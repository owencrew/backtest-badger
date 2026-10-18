"""Pure, synthetic-only minute replay; supplied projections are NOT source audits.

No loaders, paths, network, databases, quotes, or publication entry points. Native
minute observations, hypothetical fills and hourly marks have separate identities.
"""

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext
from hashlib import sha256

from backtest_badger.paper_accounting import (
    Account,
    apply_trade,
    calculate_trade,
    fund_account,
    reconcile,
    replay,
)
from backtest_badger.paper_execution import affordable_quantity
from backtest_badger.paper_historical import (
    END,
    HOUR,
    LAST_SOURCE,
    START,
    HistoricalDecision,
    HistoricalForecast,
    HourlyReference,
    SyntheticMiss,
)
from backtest_badger.paper_strategy import evaluate_strategy
from backtest_badger.paper_types import (
    INITIAL_CASH,
    STEP,
    Action,
    D,
    Portfolio,
    Side,
    Trade,
    digest,
    money_context,
    number,
    require,
    utc,
)

MINUTE = timedelta(minutes=1)
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
SYMBOLS = ("BTCUSDT", "ETHUSDT")
KIND = "synthetic_historical_minute_simulation"
PROTOCOL_VERSION = "historical-minute-execution-v1"
PROTOCOL_SHA256 = "c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b"
# Declaration only: this module never authenticates or opens the genuine release.
FROZEN_MINUTE_MANIFEST_SHA256 = (
    "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127"
)
QUANTITY_STEP = D("0.000001")


def scientific_json(value):
    """Deterministic exact strings, no floats/NaNs or recursive account histories."""

    def encode(item):
        if is_dataclass(item) and not isinstance(item, type):
            return {f.name: encode(getattr(item, f.name)) for f in fields(item)}
        if isinstance(item, Decimal):
            number(item)
            return str(item)
        if isinstance(item, datetime):
            return utc(item).isoformat()
        if isinstance(item, dict):
            require(all(isinstance(k, str) for k in item), "JSON keys must be strings.")
            return {k: encode(v) for k, v in item.items()}
        if isinstance(item, (tuple, list)):
            return [encode(v) for v in item]
        require(
            item is None or isinstance(item, (str, bool, int)),
            "Unsupported scientific JSON value (floats forbidden).",
        )
        return item

    return json.dumps(encode(value), sort_keys=True, allow_nan=False) + "\n"


def projection_sha256(references):
    """Ordered supplied-row fingerprint, NOT authentication of a full release."""
    result = sha256()
    for ref in references:
        result.update(scientific_json(ref).encode())
    return result.hexdigest()


def next_minute_at(at):
    """Strictly next native minute, including when at is exactly on a boundary."""
    return utc(at).replace(second=0, microsecond=0) + MINUTE


def reference_identity(symbol, at, interval_seconds):
    require(symbol in SYMBOLS, "Unsupported market.")
    utc(at)
    require(type(interval_seconds) is int, "Invalid native interval.")
    if interval_seconds == 60:
        return f"binance:spot:{symbol}:60:{(at - EPOCH) // timedelta(milliseconds=1)}"
    require(interval_seconds == 3600, "Unsupported native interval.")
    # Preserve the existing native-hourly identity, never relabel it as minute.
    return f"binance:spot:{symbol}:3600:{at.isoformat()}"


@dataclass(frozen=True)
class MinuteReference:
    symbol: str
    record_id: str
    at: datetime
    price: Decimal
    file_sha256: str
    source_sha256: str
    interval_seconds: int = 60
    venue: str = "binance"
    market_type: str = "spot"

    def __post_init__(self):
        utc(self.at)
        require(
            self.venue == "binance"
            and self.market_type == "spot"
            and type(self.interval_seconds) is int
            and self.interval_seconds == 60,
            "Expected native Binance Spot one-minute observation.",
        )
        require(
            START <= self.at < END and not (self.at.second or self.at.microsecond),
            "Outside 2024 native minute grid.",
        )
        require(
            self.record_id == reference_identity(self.symbol, self.at, 60),
            "Misidentified native minute observation.",
        )
        require(number(self.price) > 0, "Invalid minute opening price.")
        digest(self.file_sha256)
        digest(self.source_sha256)


@dataclass(frozen=True)
class SyntheticPriceSource:
    """Caller-supplied, independently retained fixture pins for ONE native source.

    monthly_sources contains ordered (symbol, YYYY-MM, source ZIP SHA-256) tuples.
    projected_sha256 pins only the supplied rows, including duplicates/extra rows
    for diagnostic parity reports. It makes no full archive/manifest byte claim.
    """

    interval_seconds: int
    manifest_sha256: str
    file_sha256: str
    monthly_sources: tuple[tuple[str, str, str], ...]
    projected_sha256: str
    status: str = "synthetic_test"

    def __post_init__(self):
        require(self.status == "synthetic_test", "Genuine source use is not supported.")
        require(
            type(self.interval_seconds) is int and self.interval_seconds in (60, 3600),
            "Unsupported source interval.",
        )
        for value in (self.manifest_sha256, self.file_sha256, self.projected_sha256):
            digest(value)
        require(type(self.monthly_sources) is tuple, "Immutable source pins required.")
        previous = None
        for row in self.monthly_sources:
            require(type(row) is tuple and len(row) == 3, "Malformed monthly pin.")
            symbol, month, source_hash = row
            require(
                symbol in SYMBOLS and month in {f"2024-{m:02d}" for m in range(1, 13)},
                "Invalid source market/month.",
            )
            key = symbol, month
            require(
                previous is None or key > previous, "Duplicate/reordered source pins."
            )
            digest(source_hash)
            previous = key


def price_source_sha256(source):
    """Retain this fixture metadata pin separately BEFORE passing evidence onward."""
    return sha256(scientific_json(source).encode()).hexdigest()


def validate_price_projection(
    references,
    source,
    *,
    interval_seconds,
    expected_source_sha256,
):
    """Provenance/shape checks only; callers enforce or report grid coverage."""
    require(type(source) is SyntheticPriceSource, "Expected synthetic source pins.")
    source.__post_init__()
    digest(expected_source_sha256)
    require(
        price_source_sha256(source) == expected_source_sha256,
        "Source metadata changed after its fingerprint was retained.",
    )
    require(source.interval_seconds == interval_seconds, "Mismatched source interval.")
    reference_type = MinuteReference if interval_seconds == 60 else HourlyReference
    monthly = {(s, m): h for s, m, h in source.monthly_sources}
    for ref in references:
        require(type(ref) is reference_type, "Wrong native price reference type.")
        ref.__post_init__()
        require(
            ref.record_id == reference_identity(ref.symbol, ref.at, interval_seconds),
            "Misidentified price reference.",
        )
        require(
            ref.file_sha256 == source.file_sha256
            and ref.source_sha256
            == monthly.get((ref.symbol, ref.at.strftime("%Y-%m"))),
            "Mismatched source provenance.",
        )
    require(
        projection_sha256(references) == source.projected_sha256,
        "Supplied projection changed after its fingerprint was retained.",
    )


@dataclass(frozen=True)
class MinuteFill:
    reference: MinuteReference
    trade: Trade
    decision_id: str | None
    half_spread_cost: Decimal
    slippage_cost: Decimal
    kind: str = "hypothetical_native_minute_execution"


@dataclass(frozen=True)
class MinuteMark:
    """Compact actual ledger prefix; growing trade ID histories are stored once."""

    account_id: str
    reference: MinuteReference
    ledger_seq: int
    cash: Decimal
    quantity: Decimal
    basis: Decimal
    realised: Decimal
    fees: Decimal
    equity: Decimal
    unrealised: Decimal
    kind: str = "hourly_valuation_from_native_minute_open"


@dataclass(frozen=True)
class MinuteAccount:
    label: str
    initial: Account
    final: Account
    fills: tuple[MinuteFill, ...]
    marks: tuple[MinuteMark, ...]
    status: str = "available"
    reason: str | None = None


@dataclass(frozen=True)
class MinuteResult:
    symbol: str
    end_exclusive: datetime
    source: SyntheticPriceSource
    forecast_sha256: str
    model_recipe_sha256: str
    decisions: tuple[HistoricalDecision, ...]
    accounts: tuple[MinuteAccount, ...]
    status: str
    kind: str = KIND
    protocol_version: str = PROTOCOL_VERSION
    protocol_sha256: str = PROTOCOL_SHA256
    execution_interval_seconds: int = 60
    valuation_interval_seconds: int = 3600
    authentication: str = "synthetic_projection_only_not_full_source_authentication"


def value_minute_account(account, reference, *, ledger_seq):
    reconcile(account)
    require(
        type(reference) is MinuteReference, "Expected native minute mark reference."
    )
    reference.__post_init__()
    require(
        reference.symbol == account.portfolio.symbol and reference.at.minute == 0,
        "Hourly mark market/grid mismatch.",
    )
    require(
        type(ledger_seq) is int
        and ledger_seq == account.ledger_seq > 0
        and reference.at >= account.at,
        "Wrong minute mark ledger prefix/time.",
    )
    with localcontext(money_context()):
        value = account.quantity * reference.price
        equity, unrealised = account.cash + value, value - account.basis
        require(
            account.realised + unrealised == equity - INITIAL_CASH,
            "Minute mark P&L does not reconcile.",
        )
    return MinuteMark(
        account.portfolio.key,
        reference,
        ledger_seq,
        account.cash,
        account.quantity,
        account.basis,
        account.realised,
        account.fees,
        equity,
        unrealised,
    )


def calculate_minute_fill(account, side, reference, *, identity, decision_id=None):
    """Full quantity monetary transition; caller owns causal scheduling."""
    reconcile(account)
    require(type(reference) is MinuteReference, "Expected native minute execution.")
    reference.__post_init__()
    require(isinstance(side, Side), "Invalid minute side.")
    require(
        reference.symbol == account.portfolio.symbol
        and account.ledger_seq > 0
        and reference.at >= account.at,
        "Minute execution market/time mismatch.",
    )
    with localcontext(money_context()):
        price = reference.price * (D("1.0003") if side == Side.BUY else D("0.9997"))
        if side == Side.BUY:
            require(account.quantity == 0, "Buy requires a flat account.")
            quantity = affordable_quantity(account.cash, price, QUANTITY_STEP)
        else:
            quantity = account.quantity
        require(
            quantity > 0 and quantity % QUANTITY_STEP == 0, "Infeasible full trade."
        )
        trade = calculate_trade(
            account.portfolio,
            identity,
            side,
            reference.at,
            quantity,
            price,
            ledger_seq_before=account.ledger_seq,
        )
        return MinuteFill(
            reference,
            trade,
            decision_id,
            quantity * reference.price * D("0.0001"),
            quantity * reference.price * D("0.0002"),
        )


def _plan(symbol, forecasts, misses, end, forecast_sha256):
    """Only identities, predictions and discovery times; no price dependency."""
    rows = []
    for collection, expected_type in (
        (forecasts, HistoricalForecast),
        (misses, SyntheticMiss),
    ):
        previous = None
        for item in collection:
            require(type(item) is expected_type, "Wrong forecast/miss evidence type.")
            item.__post_init__()
            require(item.symbol == symbol, "Forecast/miss market mismatch.")
            require(
                previous is None or item.source_open > previous,
                "Duplicate/reordered forecast/miss horizons.",
            )
            previous = item.source_open
            if expected_type is HistoricalForecast:
                require(
                    item.file_sha256 == forecast_sha256
                    and item.record_id
                    == (
                        f"binance:spot:{symbol}:14400:{item.source_open.isoformat()}:ridge"
                    ),
                    "Forecast source/identity mismatch.",
                )
                at, target = (
                    item.feature_available_at,
                    evaluate_strategy(item.prediction),
                )
            else:
                at, target = item.discovered_at, None
            require(
                START <= at < end and next_minute_at(at) < end,
                "Decision lacks an in-period next minute.",
            )
            rows.append((item.source_open, at, target, item))
    rows.sort(key=lambda row: row[0])
    expected = []
    opened = START - STEP
    while opened <= LAST_SOURCE and opened + STEP + MINUTE < end:
        expected.append(opened)
        opened += STEP
    require(
        [r[0] for r in rows] == expected, "Missing/duplicate required forecast grid."
    )
    require(
        all(a[1] <= b[1] for a, b in zip(rows, rows[1:], strict=False)),
        "Discovery clock reversal; later forecasts cannot be backdated.",
    )
    return rows


def _fund(symbol, label, model_recipe_sha256):
    config_hash = sha256(PROTOCOL_VERSION.encode()).hexdigest()
    portfolio = Portfolio(
        f"{KIND}:{symbol}:{label}",
        symbol,
        START,
        config_hash,
        PROTOCOL_SHA256,
        model_recipe_sha256,
        strategy_id="ridge_sign" if label == "ridge" else f"analytical_{label}",
    )
    return fund_account(Account(portfolio), START)


def replay_minute_historical(
    symbol,
    forecasts,
    references,
    *,
    source,
    expected_source_sha256,
    forecast_sha256,
    model_recipe_sha256,
    end_exclusive=END,
    synthetic_misses=(),
):
    """Three independent synthetic accounts. END selects the full-year contract.

    Short fixtures also start at START. Supply exactly the union of hourly marks
    and strictly-next-minute references for EVERY forecast/miss, including noops.
    Missing genuine evidence cannot be represented: no genuine mode exists.
    """
    require(symbol in SYMBOLS, "Unsupported minute market.")
    utc(end_exclusive)
    require(
        START < end_exclusive <= END
        and not (
            end_exclusive.minute or end_exclusive.second or end_exclusive.microsecond
        ),
        "Expected an hourly exclusive endpoint in 2024 (or END).",
    )
    digest(forecast_sha256)
    digest(model_recipe_sha256)
    plan = _plan(symbol, forecasts, synthetic_misses, end_exclusive, forecast_sha256)
    if end_exclusive == END:
        require(
            len(plan) == 2195
            and all(type(row[3]) is HistoricalForecast for row in plan),
            "Full-year mode requires exactly 2195 forecasts, without synthetic misses.",
        )
    marks_at = {START + i * HOUR for i in range((end_exclusive - START) // HOUR)}
    required = sorted(marks_at | {next_minute_at(row[1]) for row in plan})
    refs = tuple(references)
    validate_price_projection(
        refs,
        source,
        interval_seconds=60,
        expected_source_sha256=expected_source_sha256,
    )
    require(
        all(r.symbol == symbol for r in refs) and [r.at for r in refs] == required,
        "Missing/extra/duplicate/reordered required minute reference grid.",
    )
    if end_exclusive == END:
        require(
            len(plan) == 2195 and len(marks_at) == 8784, "Incomplete full-year grid."
        )
    labels = ("ridge", "cash", "buy_and_hold")
    initial = {label: _fund(symbol, label, model_recipe_sha256) for label in labels}
    accounts = dict(initial)
    fills, marks = {k: [] for k in labels}, {k: [] for k in labels}
    with localcontext(money_context()):
        available_bh = (
            affordable_quantity(
                INITIAL_CASH,
                refs[0].price * D("1.0003"),
                QUANTITY_STEP,
            )
            > 0
        )
    if available_bh:
        fill = calculate_minute_fill(
            accounts["buy_and_hold"],
            Side.BUY,
            refs[0],
            identity=accounts["buy_and_hold"].portfolio.key + ":inception",
        )
        accounts["buy_and_hold"] = apply_trade(accounts["buy_and_hold"], fill.trade)
        fills["buy_and_hold"].append(fill)
    decisions, cursor, streak, pending, last_exit = [], 0, 0, None, None
    for ref in refs:
        # Equal-time discoveries remain after this opening/mark. Their order is
        # source horizon order. Every scheduled execution is strictly later.
        while cursor < len(plan) and plan[cursor][1] < ref.at:
            opened, at, target, evidence = plan[cursor]
            cursor += 1
            miss = type(evidence) is SyntheticMiss
            streak = streak + 1 if miss else 0
            account = accounts["ridge"]
            if pending is not None:
                require(pending[1] == Side.SELL, "Overlapping minute buy intent.")
                action, reason = Action.IGNORED_EXIT_PENDING, "sticky_minute_exit"
            elif miss:
                if streak >= 2 and account.quantity > 0:
                    action, reason = Action.EXIT_REQUIRED, "risk_exit_two_misses"
                else:
                    action = (
                        Action.SIGNAL_STALE
                        if account.quantity
                        else Action.SIGNAL_MISSED
                    )
                    reason = "synthetic_missing_signal"
            elif last_exit is not None and at <= last_exit:
                action, reason = Action.CASH_NOOP, "forecast_predates_exit_satisfaction"
            elif target:
                action = Action.HOLD if account.quantity else Action.BUY_REQUIRED
                reason = "ridge_positive"
            else:
                action = Action.EXIT_REQUIRED if account.quantity else Action.CASH_NOOP
                reason = "ridge_nonpositive"
            decision = HistoricalDecision(
                f"{account.portfolio.key}:{opened.isoformat()}",
                symbol,
                opened,
                at,
                action,
                target,
                streak,
                reason,
                None if miss else evidence,
                evidence if miss else None,
            )
            decisions.append(decision)
            if action in (Action.BUY_REQUIRED, Action.EXIT_REQUIRED):
                pending = (
                    decision,
                    Side.BUY if action == Action.BUY_REQUIRED else Side.SELL,
                    next_minute_at(at),
                )
        if pending is not None and pending[2] == ref.at:
            decision, side, _ = pending
            fill = calculate_minute_fill(
                accounts["ridge"],
                side,
                ref,
                identity=decision.identity + ":trade",
                decision_id=decision.identity,
            )
            accounts["ridge"] = apply_trade(accounts["ridge"], fill.trade)
            fills["ridge"].append(fill)
            if side == Side.SELL:
                last_exit = ref.at
            pending = None
        if ref.at in marks_at:
            for label in labels:
                if label != "buy_and_hold" or available_bh:
                    account = accounts[label]
                    marks[label].append(
                        value_minute_account(
                            account,
                            ref,
                            ledger_seq=account.ledger_seq,
                        )
                    )
    require(cursor == len(plan) and pending is None, "Unprocessed minute intent.")
    outputs = []
    for label in labels:
        unavailable = label == "buy_and_hold" and not available_bh
        result = MinuteAccount(
            label,
            initial[label],
            accounts[label],
            tuple(fills[label]),
            tuple(marks[label]),
            "unavailable" if unavailable else "available",
            "inception_full_fee_affordable_buy_infeasible" if unavailable else None,
        )
        verify_minute_account(result, end_exclusive=end_exclusive)
        outputs.append(result)
    return MinuteResult(
        symbol,
        end_exclusive,
        source,
        forecast_sha256,
        model_recipe_sha256,
        tuple(decisions),
        tuple(outputs),
        "synthetic_missing_signals"
        if any(d.miss for d in decisions)
        else "synthetic_complete",
    )


def verify_minute_account(result, *, end_exclusive):
    """Replay the ledger once in time order, checking every compact mark prefix."""
    utc(end_exclusive)
    require(
        START < end_exclusive <= END
        and not (
            end_exclusive.minute or end_exclusive.second or end_exclusive.microsecond
        ),
        "Invalid account verification period.",
    )
    require(result.label in ("ridge", "cash", "buy_and_hold"), "Unknown account label.")
    account = replay(result.initial.portfolio, ())
    require(account == result.initial, "Invalid initial funding.")
    if result.status == "unavailable":
        require(
            result.label == "buy_and_hold"
            and not result.fills
            and not result.marks
            and result.final == result.initial
            and result.reason == "inception_full_fee_affordable_buy_infeasible",
            "Invalid unavailable benchmark.",
        )
        return
    require(
        result.status == "available" and result.reason is None,
        "Invalid account status.",
    )
    require(
        len(result.marks) == (end_exclusive - START) // HOUR, "Missing hourly marks."
    )
    cursor = 0
    for i, mark in enumerate(result.marks):
        at = START + i * HOUR
        while cursor < len(result.fills) and result.fills[cursor].trade.at <= at:
            fill = result.fills[cursor]
            require(
                fill
                == calculate_minute_fill(
                    account,
                    fill.trade.side,
                    fill.reference,
                    identity=fill.trade.identity,
                    decision_id=fill.decision_id,
                ),
                "Altered minute execution evidence.",
            )
            account = apply_trade(account, fill.trade)
            cursor += 1
        require(mark.reference.at == at, "Reordered hourly minute marks.")
        require(
            mark
            == value_minute_account(
                account, mark.reference, ledger_seq=account.ledger_seq
            ),
            "Minute mark differs from its actual ledger prefix.",
        )
    # Short fixtures may have a final execution after their last HH:00 mark.
    for fill in result.fills[cursor:]:
        require(fill.trade.at < end_exclusive, "Execution outside observation period.")
        require(
            fill
            == calculate_minute_fill(
                account,
                fill.trade.side,
                fill.reference,
                identity=fill.trade.identity,
                decision_id=fill.decision_id,
            ),
            "Altered final minute execution.",
        )
        account = apply_trade(account, fill.trade)
    require(
        account == result.final
        and replay(account.portfolio, (f.trade for f in result.fills)) == account,
        "Final minute ledger mismatch.",
    )
    require(result.label != "cash" or not result.fills, "Cash benchmark traded.")
    if result.label == "buy_and_hold":
        require(
            len(result.fills) == 1
            and result.fills[0].trade.side == Side.BUY
            and result.fills[0].trade.at == START
            and result.fills[0].decision_id is None,
            "Invalid inception buy-and-hold treatment.",
        )


def minute_account_summary(result, *, end_exclusive):
    """Exact money and durations; 80-digit ratios; observed hourly drawdown only."""
    verify_minute_account(result, end_exclusive=end_exclusive)
    if result.status == "unavailable":
        return {"status": "unavailable", "reason": result.reason, "performance": None}
    seconds, entered = 0, None
    for fill in result.fills:
        if fill.trade.side == Side.BUY:
            entered = fill.trade.at
        else:
            seconds += (fill.trade.at - entered) // timedelta(seconds=1)
            entered = None
    if entered is not None:
        seconds += (end_exclusive - entered) // timedelta(seconds=1)
    costs = {}
    with localcontext(money_context()):
        for side in Side:
            selected = [f for f in result.fills if f.trade.side == side]
            costs[side.value] = {
                "count": len(selected),
                "notional": sum((f.trade.notional for f in selected), D(0)),
                "fees": sum((f.trade.fee for f in selected), D(0)),
                "half_spread": sum((f.half_spread_cost for f in selected), D(0)),
                "slippage": sum((f.slippage_cost for f in selected), D(0)),
            }
        pnl = result.marks[-1].equity - INITIAL_CASH
    with localcontext(money_context(division=True)):
        peak, maximum = INITIAL_CASH, D(0)
        for mark in result.marks:
            with localcontext(money_context()):
                peak = max(peak, mark.equity)
                loss = peak - mark.equity
            maximum = max(maximum, loss / peak)
        return {
            "status": "available",
            "costs_by_side": costs,
            "last_mark_at": result.marks[-1].reference.at,
            "last_mark_pnl": pnl,
            "funding_relative_marked_return": pnl / INITIAL_CASH,
            "exposure_seconds": seconds,
            "period_seconds": (end_exclusive - START) // timedelta(seconds=1),
            "invested_hourly_mark_fraction": D(
                sum(m.quantity > 0 for m in result.marks)
            )
            / len(result.marks),
            "maximum_observed_hourly_reference_mark_drawdown": maximum,
        }


def minute_ledger_records(result):
    """One funding posting and independent signed cash/base pairs for this account."""
    records = [
        {
            "account_id": result.initial.portfolio.key,
            "sequence": 1,
            "at": START,
            "event": "funding",
            "asset": "USDT",
            "amount": INITIAL_CASH,
        }
    ]
    for fill in result.fills:
        trade = fill.trade
        for i, posting in enumerate(trade.postings, start=1):
            records.append(
                {
                    "account_id": trade.portfolio.key,
                    "sequence": trade.ledger_seq_before + i,
                    "at": trade.at,
                    "event": fill.kind,
                    "trade_id": trade.identity,
                    "asset": posting.asset,
                    "amount": posting.amount,
                }
            )
    return tuple(records)

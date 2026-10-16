"""Offline historical simulation, supplied evidence only; no artifact or live I/O.

Hourly opens are hypothetical references, never prospective Quotes. These records
assert structural integrity, not authenticity or genuine 2024 publication.
"""

import json
from dataclasses import asdict, dataclass
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
from backtest_badger.paper_strategy import evaluate_strategy
from backtest_badger.paper_types import (
    FEE_QUANTUM,
    INITIAL_CASH,
    STEP,
    Action,
    D,
    Portfolio,
    Side,
    Trade,
    digest,
    finite_decimal,
    grid,
    identifier,
    money_context,
    number,
    require,
    utc,
)

START = datetime(2024, 1, 1, tzinfo=UTC)
END = datetime(2025, 1, 1, tzinfo=UTC)
HOUR = timedelta(hours=1)
LAST_SOURCE = END - timedelta(hours=12)
KIND = "historical_simulation"


def _market(symbol, venue="binance", market_type="spot"):
    require(
        symbol in ("BTCUSDT", "ETHUSDT")
        and venue == "binance"
        and market_type == "spot",
        "Unsupported historical market.",
    )


def _hour(at):
    utc(at)
    require(not (at.minute or at.second or at.microsecond), "Off-grid hourly time.")
    return at


def next_reference_at(at):
    """Strictly next native hour; even an exact hour must wait one hour."""
    utc(at)
    return at.replace(minute=0, second=0, microsecond=0) + HOUR


def _source(at):
    grid(at)
    require(START - STEP <= at <= LAST_SOURCE, "Outside pinned forecast grid.")


@dataclass(frozen=True)
class HistoricalConfig:
    version: str = "historical-base-v1"
    sizing_version: str = "hypothetical-base-step-v1"
    quantity_step: Decimal = D("0.000001")
    fee_bps: Decimal = D("10")
    half_spread_bps: Decimal = D("1")
    slippage_bps: Decimal = D("2")
    fee_quantum: Decimal = FEE_QUANTUM

    def __post_init__(self):
        require(
            self.version == "historical-base-v1"
            and self.sizing_version == "hypothetical-base-step-v1",
            "Unsupported historical policy version.",
        )
        require(number(self.quantity_step) > 0, "Invalid synthetic quantity step.")
        for value, fixed in (
            (self.fee_bps, D(10)),
            (self.half_spread_bps, D(1)),
            (self.slippage_bps, D(2)),
            (self.fee_quantum, FEE_QUANTUM),
        ):
            require(
                number(value) == fixed, "Only the fixed base cost policy is supported."
            )


BASE_CONFIG = HistoricalConfig()


@dataclass(frozen=True)
class HistoricalForecast:
    symbol: str
    record_id: str
    source_open: datetime
    feature_available_at: datetime
    prediction: Decimal
    file_sha256: str
    model: str = "ridge"
    venue: str = "binance"
    market_type: str = "spot"

    def __post_init__(self):
        _market(self.symbol, self.venue, self.market_type)
        identifier(self.record_id)
        digest(self.file_sha256)
        _source(self.source_open)
        utc(self.feature_available_at)
        require(
            self.feature_available_at
            == self.source_open + STEP + timedelta(seconds=60),
            "Historical availability must be source opening +4h +60s.",
        )
        require(self.model == "ridge", "Expected historical Ridge forecast.")
        finite_decimal(self.prediction)


@dataclass(frozen=True)
class HourlyReference:
    symbol: str
    record_id: str
    at: datetime
    price: Decimal
    file_sha256: str
    source_sha256: str
    venue: str = "binance"
    market_type: str = "spot"

    def __post_init__(self):
        _market(self.symbol, self.venue, self.market_type)
        identifier(self.record_id)
        digest(self.file_sha256)
        digest(self.source_sha256)
        _hour(self.at)
        require(START <= self.at < END, "Outside 2024 hourly references.")
        require(number(self.price) > 0, "Invalid historical reference price.")


@dataclass(frozen=True)
class SyntheticMiss:
    """Explicit fixture gap discovered at this time, never automation evidence."""

    symbol: str
    source_open: datetime
    discovered_at: datetime
    reason: str

    def __post_init__(self):
        _market(self.symbol)
        _source(self.source_open)
        utc(self.discovered_at)
        identifier(self.reason)
        require(
            self.source_open + STEP + timedelta(minutes=16) < self.discovered_at < END,
            "Synthetic miss must be discovered AFTER cutoff within 2024.",
        )


@dataclass(frozen=True)
class HistoricalDecision:
    identity: str
    symbol: str
    source_open: datetime
    at: datetime
    action: Action
    target: int | None
    missed_streak: int
    reason: str
    forecast: HistoricalForecast | None
    miss: SyntheticMiss | None


@dataclass(frozen=True)
class HistoricalOrder:
    decision: HistoricalDecision
    side: Side
    reference_at: datetime
    ledger_seq_before: int


@dataclass(frozen=True)
class HistoricalFill:
    order: HistoricalOrder
    reference: HourlyReference
    trade: Trade
    half_spread_cost: Decimal
    slippage_cost: Decimal


@dataclass(frozen=True)
class HistoricalMark:
    reference: HourlyReference
    ledger_seq: int
    account: Account
    equity: Decimal
    unrealised: Decimal
    kind: str = KIND
    valuation_policy: str = "historical-opening-reference-v1"


@dataclass(frozen=True)
class HistoricalResult:
    symbol: str
    end_exclusive: datetime
    config: HistoricalConfig
    initial_account: Account
    final_account: Account
    decisions: tuple[HistoricalDecision, ...]
    fills: tuple[HistoricalFill, ...]
    marks: tuple[HistoricalMark, ...]
    status: str
    kind: str = KIND
    execution_constraints: str = (
        "depth_exchange_filters_fillability_not_evidenced_untested"
    )


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported historical JSON value: {type(value).__name__}")


def historical_json(result):
    """Deterministic JSON text; exact Decimals as strings, UTC ISO timestamps."""
    return (
        json.dumps(
            asdict(result), sort_keys=True, allow_nan=False, default=_json_default
        )
        + "\n"
    )


def value_historical(account, reference, *, ledger_seq):
    """Mark this exact supplied ledger prefix, never a prospective Mark event."""
    reconcile(account)
    require(isinstance(reference, HourlyReference), "Expected hourly reference.")
    require(reference.symbol == account.portfolio.symbol, "Mark market mismatch.")
    require(
        type(ledger_seq) is int
        and ledger_seq == account.ledger_seq > 0
        and reference.at >= account.at,
        "Wrong historical mark ledger prefix/time.",
    )
    with localcontext(money_context()):
        value = account.quantity * reference.price
        equity, unrealised = account.cash + value, value - account.basis
        require(
            account.realised + unrealised == equity - INITIAL_CASH,
            "Historical marked P&L does not reconcile.",
        )
    return HistoricalMark(reference, ledger_seq, account, equity, unrealised)


def calculate_historical_trade(
    account, side, reference, *, at, identity, config=BASE_CONFIG
):
    """Full mathematical transition, not signal eligibility or observed fillability.

    The runner owns the earlier decision and its strictly-next-hour schedule.
    This helper requires an exact matching reference at the processing instant.
    """
    reconcile(account)
    utc(at)
    require(isinstance(config, HistoricalConfig), "Expected historical configuration.")
    require(isinstance(side, Side), "Invalid historical side.")
    require(isinstance(reference, HourlyReference), "Expected hourly reference.")
    require(reference.symbol == account.portfolio.symbol, "Trade market mismatch.")
    require(
        account.ledger_seq > 0 and reference.at == at >= account.at,
        "Wrong historical execution reference/time.",
    )
    with localcontext(money_context()):
        adjustment = (config.half_spread_bps + config.slippage_bps) / D(10000)
        price = reference.price * (
            1 + adjustment if side == Side.BUY else 1 - adjustment
        )
        if side == Side.BUY:
            require(account.quantity == 0, "Historical buy requires flat account.")
            quantity = affordable_quantity(account.cash, price, config.quantity_step)
        else:
            quantity = account.quantity
        require(
            quantity > 0 and quantity % config.quantity_step == 0,
            "Unaffordable or off-step historical transition.",
        )
        return calculate_trade(
            account.portfolio,
            identity,
            side,
            at,
            quantity,
            price,
            ledger_seq_before=account.ledger_seq,
        )


def _plan(symbol, forecasts, misses, end):
    """Validate all source horizons and targets without accepting price inputs."""
    rows = []
    ids = set()
    for collection, expected_type in (
        (forecasts, HistoricalForecast),
        (misses, SyntheticMiss),
    ):
        previous = None
        for item in collection:
            require(isinstance(item, expected_type), "Wrong historical evidence type.")
            require(item.symbol == symbol, "Forecast/miss market mismatch.")
            require(
                previous is None or item.source_open > previous,
                "Duplicate or out-of-order source horizons.",
            )
            previous = item.source_open
            if isinstance(item, HistoricalForecast):
                require(item.record_id not in ids, "Duplicate forecast identity.")
                ids.add(item.record_id)
                at, target = (
                    item.feature_available_at,
                    evaluate_strategy(item.prediction),
                )
            else:
                at, target = item.discovered_at, None
            require(START <= at < end, "Decision outside supplied observation period.")
            require(
                next_reference_at(at) < end, "Decision lacks next in-period reference."
            )
            rows.append((item.source_open, at, target, item))
    # Separate forecast/miss collections may interleave; never repair order within one.
    rows.sort(key=lambda row: row[0])
    expected = []
    opened = START - STEP
    while opened <= LAST_SOURCE and opened + STEP + timedelta(seconds=60) < end:
        expected.append(opened)
        opened += STEP
    require(
        [row[0] for row in rows] == expected,
        "Missing/duplicate required forecast grid.",
    )
    require(
        all(a[1] <= b[1] for a, b in zip(rows, rows[1:], strict=False)),
        "Discovery/decision clock reversal; cannot backdate a later horizon.",
    )
    return rows


def replay_historical(
    symbol,
    forecasts,
    references,
    *,
    protocol_sha256,
    model_recipe_sha256,
    end_exclusive=END,
    config=BASE_CONFIG,
    synthetic_misses=(),
):
    """One independent funded account, explicit 2024 inputs, no I/O or discovery.

    Forecasts/misses must each be source-ordered; references strictly hour-ordered.
    Default requires the full pinned grid. Short fixtures start at START and must
    include the next reference of every eligible decision. Explicit synthetic
    misses make the result incomplete research evidence, even when risk exits work.
    Every reference is mandatory, including cash/HOLD hours. Invalid input raises;
    no partial economic result or later-price substitution is returned.
    """
    _market(symbol)
    _hour(end_exclusive)
    require(START < end_exclusive <= END, "Invalid historical period.")
    require(isinstance(config, HistoricalConfig), "Expected historical configuration.")
    digest(protocol_sha256)
    digest(model_recipe_sha256)
    plan = _plan(symbol, forecasts, synthetic_misses, end_exclusive)
    references = tuple(references)
    require(
        len(references) == (end_exclusive - START) // HOUR,
        "Missing/extra required hourly references.",
    )
    ids = set()
    for i, ref in enumerate(references):
        require(isinstance(ref, HourlyReference), "Expected hourly reference evidence.")
        require(ref.symbol == symbol, "Reference market mismatch.")
        require(
            ref.at == START + i * HOUR, "Duplicate/out-of-order/future hourly grid."
        )
        require(ref.record_id not in ids, "Duplicate hourly evidence identity.")
        ids.add(ref.record_id)

    config_hash = sha256(historical_json(config).encode()).hexdigest()
    portfolio = Portfolio(
        f"{KIND}:{symbol}:{config_hash}",
        symbol,
        START,
        config_hash,
        protocol_sha256,
        model_recipe_sha256,
    )
    account = initial = fund_account(Account(portfolio), START)
    decisions, fills, marks = [], [], []
    pending, streak, cursor = None, 0, 0
    with localcontext(money_context()):
        spread = config.half_spread_bps / D(10000)
        slippage = config.slippage_bps / D(10000)
        for ref in references:
            # At an hour, execute only a previously eligible intent, then mark.
            # A miss discovered AT this hour is processed AFTER that mark and
            # can trade only at the strictly next hour.
            if pending is not None and pending.reference_at == ref.at:
                require(
                    pending.ledger_seq_before == account.ledger_seq,
                    "Historical order ledger prefix mismatch.",
                )
                trade = calculate_historical_trade(
                    account,
                    pending.side,
                    ref,
                    at=ref.at,
                    identity=pending.decision.identity + ":trade",
                    config=config,
                )
                account = apply_trade(account, trade)
                fills.append(
                    HistoricalFill(
                        pending,
                        ref,
                        trade,
                        trade.quantity * ref.price * spread,
                        trade.quantity * ref.price * slippage,
                    )
                )
                pending = None
            marks.append(value_historical(account, ref, ledger_seq=account.ledger_seq))
            while cursor < len(plan) and plan[cursor][1] < ref.at + HOUR:
                opened, at, target, evidence = plan[cursor]
                cursor += 1
                require(at >= ref.at, "Decision clock reversal.")
                is_miss = isinstance(evidence, SyntheticMiss)
                streak = streak + 1 if is_miss else 0
                if pending is not None:
                    # Delayed synthetic discovery may overlap a later signal.
                    # An outstanding exit cannot be cancelled or reused to re-enter.
                    require(pending.side == Side.SELL, "Overlapping historical buy.")
                    action, reason = (
                        Action.IGNORED_EXIT_PENDING,
                        "sticky_historical_exit",
                    )
                elif is_miss:
                    if streak >= 2 and account.quantity > 0:
                        action, reason = Action.EXIT_REQUIRED, "risk_exit_two_misses"
                    else:
                        action = (
                            Action.SIGNAL_STALE
                            if account.quantity
                            else Action.SIGNAL_MISSED
                        )
                        reason = "synthetic_missing_signal"
                elif target:
                    action = Action.HOLD if account.quantity else Action.BUY_REQUIRED
                    reason = "ridge_positive"
                else:
                    action = (
                        Action.EXIT_REQUIRED if account.quantity else Action.CASH_NOOP
                    )
                    reason = "ridge_nonpositive"
                decision = HistoricalDecision(
                    f"{portfolio.key}:{opened.isoformat()}",
                    symbol,
                    opened,
                    at,
                    action,
                    target,
                    streak,
                    reason,
                    None if is_miss else evidence,
                    evidence if is_miss else None,
                )
                decisions.append(decision)
                if action in (Action.BUY_REQUIRED, Action.EXIT_REQUIRED):
                    pending = HistoricalOrder(
                        decision,
                        Side.BUY if action == Action.BUY_REQUIRED else Side.SELL,
                        next_reference_at(at),
                        account.ledger_seq,
                    )
    require(cursor == len(plan) and pending is None, "Unprocessed historical intent.")
    require(
        replay(portfolio, tuple(fill.trade for fill in fills)) == account,
        "Historical ledger replay mismatch.",
    )
    return HistoricalResult(
        symbol,
        end_exclusive,
        config,
        initial,
        account,
        tuple(decisions),
        tuple(fills),
        tuple(marks),
        "synthetic_missing_signals"
        if any(d.miss for d in decisions)
        else "complete_inputs",
    )

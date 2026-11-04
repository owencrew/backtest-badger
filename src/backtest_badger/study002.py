"""Fixed daily 30-day trend; pure signals and a narrow existing-money adapter.

No loaders, forecasts, model fitting or future-price access in the decision API.
The caller authenticates sources; this module validates the required projection.
"""

from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import localcontext

from backtest_badger import local_historical_backtest as local
from backtest_badger import paper_accounting as accounting
from backtest_badger import paper_minute_historical as minute
from backtest_badger import paper_minute_reporting as reporting
from backtest_badger.paper_types import (
    STEP,
    D,
    Portfolio,
    Side,
    digest,
    grid,
    money_context,
    number,
    require,
    utc,
)

STRATEGY = "trend_30d_daily_v1"
DAY = timedelta(days=1)
LOOKBACK = 30 * DAY
LABELS = (STRATEGY, "cash", "buy_and_hold")


@dataclass(frozen=True)
class Close:
    symbol: str
    opened: datetime
    closed: datetime
    price: D

    def __post_init__(self):
        require(self.symbol in minute.SYMBOLS, "Wrong close market.")
        grid(self.opened)
        require(self.closed == self.opened + STEP, "Wrong native close boundary.")
        utc(self.closed)
        require(number(self.price) > 0, "Invalid close price.")


@dataclass(frozen=True)
class Signal:
    symbol: str
    at: datetime
    now: Close
    past: Close
    numerator: D
    trend_return: D
    long: bool


def signal(now, past, at):
    """Only two completed candles enter this interface, never an outcome series."""
    now.__post_init__()
    past.__post_init__()
    utc(at)
    boundary = at.replace(hour=0, minute=0, second=0, microsecond=0)
    require(
        at == boundary + minute.MINUTE
        and now.closed == boundary
        and past.closed == boundary - LOOKBACK
        and now.symbol == past.symbol,
        "Expected exact daily +60s availability and 30-calendar-day lookback.",
    )
    with localcontext(money_context()):
        difference = now.price - past.price
    with localcontext(money_context(division=True)):
        ratio = difference / past.price
    return Signal(now.symbol, at, now, past, difference, ratio, difference > 0)


def close_projection(markets):
    """Discard non-study rows after the frozen loader's structural validation."""
    first = minute.START - LOOKBACK - STEP
    stop = minute.END - DAY
    return {
        symbol: tuple(
            Close(symbol, row["open_time"], row["open_time"] + STEP, row["close"])
            for row in markets[symbol]
            if first <= row["open_time"] < stop
        )
        for symbol in minute.SYMBOLS
    }


def signals(symbol, closes, *, end=minute.END):
    utc(end)
    require(
        symbol in minute.SYMBOLS
        and minute.START < end <= minute.END
        and (end - minute.START) % DAY == timedelta(0),
        "Expected whole UTC days in 2024.",
    )
    first, stop = minute.START - LOOKBACK - STEP, end - DAY
    expected = tuple(first + i * STEP for i in range((stop - first) // STEP))
    for row in closes:
        require(type(row) is Close, "Expected native close projection.")
        row.__post_init__()
    require(
        tuple(row.opened for row in closes) == expected
        and all(row.symbol == symbol for row in closes),
        "Missing/extra/duplicate/reordered warm-up or source observation.",
    )
    by_close = {row.closed: row for row in closes}
    return tuple(
        signal(by_close[d], by_close[d - LOOKBACK], d + minute.MINUTE)
        for d in (minute.START + i * DAY for i in range((end - minute.START) // DAY))
    )


def legacy_view(account):
    """Label-only facade for frozen reporting's strategy-independent checks.

    Account/portfolio/trade identities and strategy_id stay Trend. Fingerprints
    from the legacy reporter bind this facade, not the canonical serialized label.
    """
    require(account.label in LABELS, "Unknown Study 002 account.")
    return replace(account, label="ridge") if account.label == STRATEGY else account


def replay(symbol, closes, references, *, config_sha256, method_sha256, end=minute.END):
    digest(config_sha256)
    digest(method_sha256)
    plan = signals(symbol, closes, end=end)
    marks_at = {
        minute.START + i * minute.HOUR
        for i in range((end - minute.START) // minute.HOUR)
    }
    by_execution = {minute.next_minute_at(s.at): s for s in plan}
    required = sorted(marks_at | by_execution.keys())
    # Full authenticated publication can be projected by the caller. No repair here.
    require([r.at for r in references] == required, "Incomplete/reordered minute grid.")
    for ref in references:
        require(
            type(ref) is minute.MinuteReference, "Expected native minute reference."
        )
        ref.__post_init__()
        require(ref.symbol == symbol, "Minute market mismatch.")
    initial = {}
    for label in LABELS:
        portfolio = Portfolio(
            f"study-002:{symbol}:{label}",
            symbol,
            minute.START,
            config_sha256,
            method_sha256,
            config_sha256,
            strategy_id=label if label == STRATEGY else f"analytical_{label}",
        )
        initial[label] = accounting.fund_account(
            accounting.Account(portfolio), minute.START
        )
    accounts = dict(initial)
    fills, marks = {k: [] for k in LABELS}, {k: [] for k in LABELS}
    decisions = []
    with localcontext(money_context()):
        bh_available = (
            minute.affordable_quantity(
                minute.INITIAL_CASH,
                references[0].price * D("1.0003"),
                minute.QUANTITY_STEP,
            )
            > 0
        )
    for ref in references:
        intents = []
        if ref.at == minute.START and bh_available:
            intents.append(("buy_and_hold", Side.BUY, None))
        if ref.at in by_execution:
            s = by_execution[ref.at]
            held = accounts[STRATEGY].quantity > 0
            action = (
                ("HOLD" if held else "BUY_REQUIRED")
                if s.long
                else ("EXIT_REQUIRED" if held else "CASH_NOOP")
            )
            identity = f"study-002:{symbol}:{s.at.isoformat()}"
            decisions.append({"identity": identity, "signal": s, "action": action})
            if held != s.long:
                intents.append((STRATEGY, Side.BUY if s.long else Side.SELL, identity))
        for label, side, decision_id in intents:
            account = accounts[label]
            fill = minute.calculate_minute_fill(
                account,
                side,
                ref,
                identity=(decision_id or account.portfolio.key + ":inception")
                + ":trade",
                decision_id=decision_id,
            )
            accounts[label] = accounting.apply_trade(account, fill.trade)
            fills[label].append(fill)
        if ref.at in marks_at:
            for label in LABELS:
                if label != "buy_and_hold" or bh_available:
                    account = accounts[label]
                    marks[label].append(
                        minute.value_minute_account(
                            account, ref, ledger_seq=account.ledger_seq
                        )
                    )
    outputs = []
    for label in LABELS:
        unavailable = label == "buy_and_hold" and not bh_available
        account = minute.MinuteAccount(
            label,
            initial[label],
            accounts[label],
            tuple(fills[label]),
            tuple(marks[label]),
            "unavailable" if unavailable else "available",
            "inception_full_fee_affordable_buy_infeasible" if unavailable else None,
        )
        minute.verify_minute_account(legacy_view(account), end_exclusive=end)
        outputs.append(account)
    return {"symbol": symbol, "decisions": tuple(decisions), "accounts": tuple(outputs)}


def reports(result, *, end=minute.END):
    concise, detailed = [], []
    counts = Counter(d["action"] for d in result["decisions"])
    for account in result["accounts"]:
        facade = legacy_view(account)
        fingerprint = reporting.minute_reporting_fingerprint(facade, end_exclusive=end)
        summary = reporting.minute_reporting_summary(
            facade, end_exclusive=end, expected_fingerprint=fingerprint
        )
        summary["label"] = account.label
        ledger = minute.minute_ledger_records(account)
        costs = summary["costs_by_side"]
        with localcontext(money_context()):
            totals = (
                {
                    key: sum((v[key] for v in costs.values()), D(0))
                    for key in (
                        "notional",
                        "fees",
                        "hypothetical_half_spread",
                        "hypothetical_slippage",
                    )
                }
                if costs
                else None
            )
            if totals is not None:
                totals["total_attributed_costs"] = sum(
                    totals[k]
                    for k in (
                        "fees",
                        "hypothetical_half_spread",
                        "hypothetical_slippage",
                    )
                )
                totals["turnover_initial_funding"] = (
                    totals["notional"] / minute.INITIAL_CASH
                )
        daily = [
            r
            for r in summary["observations"]
            if r["period"] == "daily" and r["complete"]
        ]
        row = {
            key: summary[key]
            for key in (
                "account_id",
                "symbol",
                "label",
                "status",
                "reason",
                "initial_funding",
                "performance",
                "costs_by_side",
                "complete_day_statistics",
            )
        }
        row.update(
            {
                "legacy_reporting_fingerprint": fingerprint,
                "canonical_account_identity": local.preparation.identity(
                    local._bytes(account)
                ),
                "ledger_identity": local.preparation.identity(local._bytes(ledger)),
                "ledger_verification": "passed",
                "first_mark_equity": account.marks[0].equity if account.marks else None,
                "final_mark_equity": account.marks[-1].equity
                if account.marks
                else None,
                "final_cash": account.final.cash,
                "final_quantity": account.final.quantity,
                "final_basis": account.final.basis,
                "realised": account.final.realised,
                "unrealised": account.marks[-1].unrealised if account.marks else None,
                "totals": totals,
                "signal_evaluations": len(result["decisions"])
                if account.label == STRATEGY
                else 0,
                "position_changes": len(account.fills),
                "hold_count": counts["HOLD"] if account.label == STRATEGY else 0,
                "cash_noop_count": counts["CASH_NOOP"]
                if account.label == STRATEGY
                else 0,
                "descriptive_statistics": local._descriptive_statistics(summary),
                "best_complete_day": min(
                    (
                        r["start"]
                        for r in daily
                        if r["return"] == max(x["return"] for x in daily)
                    ),
                    default=None,
                ),
                "worst_complete_day": min(
                    (
                        r["start"]
                        for r in daily
                        if r["return"] == min(x["return"] for x in daily)
                    ),
                    default=None,
                ),
                "extreme_day_tie_policy": "earliest UTC day",
            }
        )
        concise.append(row)
        detailed.append({"summary": summary, "ledger": ledger})
    return concise, detailed

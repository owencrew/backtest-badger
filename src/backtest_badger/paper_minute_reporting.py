"""Pure native-minute reporting over retained, verified account evidence.

No source authentication, runner, I/O or authority is provided. Retain the input
fingerprint independently before handing evidence to these reporting functions;
re-fingerprinting changed evidence defeats mutation detection.
"""

import calendar
from datetime import timedelta
from decimal import localcontext
from hashlib import sha256

from backtest_badger.paper_historical import START
from backtest_badger.paper_minute_historical import (
    MinuteAccount,
    minute_account_summary,
    scientific_json,
    verify_minute_account,
)
from backtest_badger.paper_types import (
    INITIAL_CASH,
    D,
    Side,
    digest,
    money_context,
    require,
)

SCHEMA = "native-minute-economic-reporting-v1"
SECOND = timedelta(seconds=1)


def _fingerprint(result, end_exclusive):
    return sha256(
        scientific_json(
            {"schema": SCHEMA, "account": result, "end_exclusive": end_exclusive}
        ).encode()
    ).hexdigest()


def _verify(result, end_exclusive):
    require(type(result) is MinuteAccount, "Expected MinuteAccount evidence.")
    require(
        type(result.fills) is tuple and type(result.marks) is tuple,
        "Immutable fill and mark sequences required.",
    )
    verify_minute_account(result, end_exclusive=end_exclusive)
    require(result.initial.portfolio.inception_at == START, "Wrong funding boundary.")
    for fill in result.fills:
        require(fill.trade.at == fill.reference.at, "Trade/reference time mismatch.")


def minute_reporting_fingerprint(result, *, end_exclusive):
    """Verify and pin a synthetic account AND endpoint before reporting handoff.

    This is an integrity helper, not independent authentication or approval. The
    caller must retain the returned digest separately from the handed-off input.
    """
    _verify(result, end_exclusive)
    return _fingerprint(result, end_exclusive)


def _checked(result, end_exclusive, expected_fingerprint):
    _verify(result, end_exclusive)
    digest(expected_fingerprint)
    require(
        _fingerprint(result, end_exclusive) == expected_fingerprint,
        "Account or reporting boundary changed after fingerprint retention.",
    )


def _metadata(result, end_exclusive):
    return {
        "schema": SCHEMA,
        "account_id": result.initial.portfolio.key,
        "symbol": result.initial.portfolio.symbol,
        "label": result.label,
        "status": result.status,
        "reason": result.reason,
        "start_inclusive": START,
        "end_exclusive": end_exclusive,
        "execution_interval_seconds": 60,
        "valuation_interval_seconds": 3600,
        "initial_funding": INITIAL_CASH,
    }


def _costs(fills):
    costs = {}
    for side in Side:
        selected = tuple(f for f in fills if f.trade.side == side)
        with localcontext(money_context()):
            notional = sum((f.trade.notional for f in selected), D(0))
            values = {
                "count": len(selected),
                "notional": notional,
                "fees": sum((f.trade.fee for f in selected), D(0)),
                "hypothetical_half_spread": sum(
                    (f.half_spread_cost for f in selected), D(0)
                ),
                "hypothetical_slippage": sum((f.slippage_cost for f in selected), D(0)),
                "turnover_denominator": INITIAL_CASH,
            }
        with localcontext(money_context(division=True)):
            values["turnover_initial_funding"] = notional / INITIAL_CASH
        costs[side.value] = values
    return costs


def _attribution(result, end_exclusive):
    if result.status == "unavailable":
        return {"costs_by_side": None, "periods": ()}
    rows = []
    for period in ("daily", "monthly"):
        start = START
        while start < end_exclusive:
            days = 1 if period == "daily" else calendar.monthrange(2024, start.month)[1]
            boundary = start + timedelta(days=days)
            flow_end = min(boundary, end_exclusive)
            fills = tuple(f for f in result.fills if start <= f.trade.at < flow_end)
            rows.append(
                {
                    "period": period,
                    "start": start,
                    "boundary": boundary,
                    "flow_end_exclusive": flow_end,
                    "flow_complete": flow_end == boundary,
                    "fills": fills,
                    "costs_by_side": _costs(fills),
                }
            )
            start = boundary
    return {"costs_by_side": _costs(result.fills), "periods": tuple(rows)}


def minute_cost_attribution(result, *, end_exclusive, expected_fingerprint):
    """Verified side totals and half-open UTC daily/monthly actual-fill flows.

    Daily and monthly rows are alternative aggregations, never additive. Original
    MinuteFill objects retain exact timestamps, reference identities and prices.
    """
    _checked(result, end_exclusive, expected_fingerprint)
    return {**_metadata(result, end_exclusive), **_attribution(result, end_exclusive)}


def _observations(result, attribution):
    by_time = {m.reference.at: m for m in result.marks}
    rows = []
    for flow in attribution["periods"]:
        start, boundary = flow["start"], flow["boundary"]
        end = min(boundary, result.marks[-1].reference.at)
        first, final = by_time[start], by_time[end]
        with localcontext(money_context()):
            change = final.equity - first.equity
        with localcontext(money_context(division=True)):
            change_ratio = change / first.equity if end > start else None
        rows.append(
            {
                **flow,
                "end": end,
                "complete": end == boundary,
                "observed_seconds": (end - start) // SECOND,
                "missing_boundary_seconds": (boundary - end) // SECOND,
                "start_mark": first,
                "end_mark": final,
                "pnl": change,
                "return": change_ratio,
                "return_basis": "observed_hourly_mark_to_mark",
            }
        )
    return tuple(rows)


def minute_period_observations(result, *, end_exclusive, expected_fingerprint):
    """Verified UTC mark-to-mark periods, explicitly separating flow coverage.

    A zero-duration short-fixture observation has return=None. Incomplete days
    must not enter complete-day statistics. No end-boundary price is invented.
    """
    _checked(result, end_exclusive, expected_fingerprint)
    return {
        **_metadata(result, end_exclusive),
        "observations": _observations(result, _attribution(result, end_exclusive)),
    }


def minute_reporting_summary(result, *, end_exclusive, expected_fingerprint):
    """Compose the unchanged minute summary, source objects and calendar reports.

    Last observed state and final ledger state are distinct: short fixtures can
    trade after their last mark. No realised/unrealised ratio is introduced.
    """
    _checked(result, end_exclusive, expected_fingerprint)
    performance = minute_account_summary(result, end_exclusive=end_exclusive)
    attribution = _attribution(result, end_exclusive)
    observations = _observations(result, attribution)
    complete = [
        row["return"]
        for row in observations
        if row["period"] == "daily" and row["complete"]
    ]
    with localcontext(money_context()):
        total = sum(complete, D(0))
    with localcontext(money_context(division=True)):
        mean = total / len(complete) if complete else None
    return {
        **_metadata(result, end_exclusive),
        "input_fingerprint": expected_fingerprint,
        "performance": performance if result.status == "available" else None,
        "initial_account": result.initial,
        "final_account": result.final,
        "last_observed_mark": result.marks[-1] if result.marks else None,
        **attribution,
        "observations": observations,
        "complete_day_statistics": {
            "count": len(complete),
            "mean": mean,
            "min": min(complete) if complete else None,
            "max": max(complete) if complete else None,
        },
    }

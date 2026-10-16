"""Versioned Ridge policy and explicit immutable continuous-holding transitions."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from backtest_badger.paper_accounting import (
    Account,
    Mark,
    apply_trade,
    reconcile,
    value_account,
)
from backtest_badger.paper_execution import Result, Status, simulate_order
from backtest_badger.paper_types import (
    STEP,
    Action,
    D,
    Decision,
    Forecast,
    Side,
    eligible_forecast,
    finite_decimal,
    grid,
    identifier,
    require,
    utc,
)


def evaluate_strategy(prediction, *, strategy_id="ridge_sign", version="1"):
    """No price, source reader, outcome, or execution dependency in the policy."""
    require(
        (strategy_id, version) == ("ridge_sign", "1"), "Unsupported strategy version."
    )
    return int(finite_decimal(prediction) > D("1e-12"))


@dataclass(frozen=True)
class State:
    account: Account
    next_source_open: datetime
    last_at: datetime
    missed_streak: int = 0
    exit_required: Decision | None = None
    exit_satisfied_at: datetime | None = None
    decisions: tuple[Decision, ...] = ()
    attempts: tuple[Result, ...] = ()


def start_strategy(account, inception_mark):
    """Activation in memory requires a valid inception mark at the funded prefix."""
    reconcile(account)
    require(
        account.ledger_seq == 1
        and account.quantity == 0
        and account.at == account.portfolio.inception_at,
        "Expected initial funding.",
    )
    require(
        isinstance(inception_mark, Mark)
        and value_account(account, inception_mark).equity == D("10000"),
        "Valid inception mark required.",
    )
    inception = account.portfolio.inception_at
    close = inception.replace(
        hour=(inception.hour // 4) * 4, minute=0, second=0, microsecond=0
    )
    if inception >= close + timedelta(minutes=16):
        close += STEP
    return State(account, close - STEP, inception_mark.marked_at)


def _check(state, identity, at):
    reconcile(state.account)
    identifier(identity)
    utc(at)
    grid(state.next_source_open)
    require(at >= state.last_at >= state.account.at, "Strategy clock reversal.")
    require(
        identity not in {d.identity for d in state.decisions}, "Duplicate decision."
    )
    require(
        type(state.missed_streak) is int and state.missed_streak >= 0,
        "Invalid missed streak.",
    )
    require(
        type(state.decisions) is tuple and type(state.attempts) is tuple,
        "Mutable transition history.",
    )
    if state.exit_required is not None:
        require(
            state.exit_required in state.decisions
            and state.exit_required.action == Action.EXIT_REQUIRED
            and state.exit_required.portfolio == state.account.portfolio
            and state.account.quantity > 0,
            "Illegal exit obligation state.",
        )
    if state.exit_satisfied_at is not None:
        utc(state.exit_satisfied_at)
        require(state.exit_satisfied_at <= state.last_at, "Future exit satisfaction.")


def observe_forecast(state, forecast, identity, at):
    _check(state, identity, at)
    require(
        isinstance(forecast, Forecast)
        and forecast.portfolio == state.account.portfolio,
        "Forecast/account mismatch.",
    )
    require(
        forecast.source_open == state.next_source_open, "Out-of-order source horizon."
    )
    require(
        forecast.record_id
        not in {
            d.forecast.record_id for d in state.decisions if d.forecast is not None
        },
        "Duplicate forecast.",
    )
    eligible = eligible_forecast(forecast, at)
    if not eligible:
        # An ineligible observation alone is not a missed horizon at its deadline.
        decision = Decision(
            identity,
            forecast.portfolio,
            at,
            Action.SIGNAL_INELIGIBLE,
            "ineligible_forecast",
            state.missed_streak,
            forecast.source_open,
            forecast,
        )
        return replace(
            state, last_at=at, decisions=state.decisions + (decision,)
        ), decision
    target = evaluate_strategy(
        forecast.prediction,
        strategy_id=forecast.portfolio.strategy_id,
        version=forecast.portfolio.strategy_version,
    )
    obligation = state.exit_required
    if obligation is not None:
        action, reason = Action.IGNORED_EXIT_PENDING, "sticky_exit"
    elif (
        state.exit_satisfied_at is not None
        and forecast.issued_at <= state.exit_satisfied_at
    ):
        action, reason = Action.CASH_NOOP, "forecast_predates_exit_satisfaction"
    elif target:
        action = Action.HOLD if state.account.quantity > 0 else Action.BUY_REQUIRED
        reason = "ridge_positive"
    else:
        action = (
            Action.EXIT_REQUIRED if state.account.quantity > 0 else Action.CASH_NOOP
        )
        reason = "ridge_nonpositive"
    decision = Decision(
        identity,
        forecast.portfolio,
        at,
        action,
        reason,
        0,
        forecast.source_open,
        forecast,
        identity
        if action == Action.EXIT_REQUIRED
        else obligation.identity
        if obligation
        else None,
    )
    if action == Action.EXIT_REQUIRED:
        obligation = decision
    return replace(
        state,
        next_source_open=state.next_source_open + STEP,
        last_at=at,
        missed_streak=0,
        exit_required=obligation,
        decisions=state.decisions + (decision,),
    ), decision


def miss_horizon(state, source_open, identity, discovered_at):
    """Advance one expected horizon, strictly after cutoff, at actual discovery."""
    _check(state, identity, discovered_at)
    grid(source_open)
    require(source_open == state.next_source_open, "Skipped/repeated missed horizon.")
    require(
        discovered_at > source_open + STEP + timedelta(minutes=16),
        "Horizon is not missed until observed AFTER deadline.",
    )
    streak = state.missed_streak + 1
    obligation = state.exit_required
    if obligation is None and streak >= 2 and state.account.quantity > 0:
        action, reason = Action.EXIT_REQUIRED, "risk_exit_two_misses"
    else:
        action = (
            Action.SIGNAL_STALE if state.account.quantity > 0 else Action.SIGNAL_MISSED
        )
        reason = "missing_is_unknown"
    decision = Decision(
        identity,
        state.account.portfolio,
        discovered_at,
        action,
        reason,
        streak,
        source_open,
        obligation_id=(
            identity
            if action == Action.EXIT_REQUIRED
            else obligation.identity
            if obligation
            else None
        ),
    )
    if action == Action.EXIT_REQUIRED:
        obligation = decision
    return replace(
        state,
        next_source_open=source_open + STEP,
        last_at=discovered_at,
        missed_streak=streak,
        exit_required=obligation,
        decisions=state.decisions + (decision,),
    ), decision


def record_result(state, result, identity):
    """Couple a verified terminal attempt, accounting pair and exit satisfaction.

    Stage 4C must make this whole proposed transition a single DB transaction.
    Rejections/expiry preserve the obligation and financial account verbatim.
    """
    require(isinstance(result, Result), "Expected execution result.")
    _check(state, identity, result.at)
    order = result.order
    require(
        order.decision in state.decisions and order.balances == state.account.balances,
        "Unknown decision or stale account snapshot.",
    )
    require(order.submitted_at >= state.last_at, "Order predates latest transition.")
    if order.side == Side.BUY:
        require(
            state.exit_required is None and state.account.quantity == 0,
            "Buy during exit obligation/holding.",
        )
        if state.exit_satisfied_at is not None:
            require(
                order.decision.forecast.issued_at > state.exit_satisfied_at,
                "Old forecast cannot re-enter.",
            )
    else:
        require(state.exit_required == order.decision, "No matching sticky obligation.")
    # Recompute every terminal proposal, including rejections, from saved inputs.
    expected = simulate_order(
        order,
        result.quote,
        result.filters,
        result.at,
        run_id=result.run_id,
        existing=state.attempts,
    )
    require(result == expected, "Altered execution result.")
    account, obligation = state.account, state.exit_required
    satisfied = state.exit_satisfied_at
    action, reason = Action.ORDER_TERMINAL, result.reason.value
    if result.status == Status.FILLED:
        action = Action.POSITION_UPDATED
        account = apply_trade(account, result.fill.trade)
        if obligation is not None and account.quantity == 0:
            action, reason = Action.EXIT_SATISFIED, "holdings_zero"
            satisfied = result.at
            obligation = None
    transition = Decision(
        identity,
        account.portfolio,
        result.at,
        action,
        reason,
        state.missed_streak,
        obligation_id=state.exit_required.identity if state.exit_required else None,
    )
    return replace(
        state,
        account=account,
        last_at=result.at,
        exit_required=obligation,
        exit_satisfied_at=satisfied,
        attempts=state.attempts + (result,),
        decisions=state.decisions + (transition,),
    ), transition

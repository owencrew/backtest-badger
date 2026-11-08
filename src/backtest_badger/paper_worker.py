"""Single-cycle proposal planner. No financial writer or operational configuration."""

import argparse
import json
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path

import psycopg

from backtest_badger import paper_records as records
from backtest_badger.paper_accounting import Mark, reconcile, value_account
from backtest_badger.paper_clock import Clock
from backtest_badger.paper_execution import Order
from backtest_badger.paper_forward_adapter import EvidenceError
from backtest_badger.paper_market_data import (
    MarketError,
    Response,
    effective_filters,
    smoke,
)
from backtest_badger.paper_reconciliation import IntegrityIssue
from backtest_badger.paper_recovery import CUTOFF, Recovery, boundary
from backtest_badger.paper_strategy import miss_horizon, observe_forecast
from backtest_badger.paper_types import (
    STEP,
    VALUATION_POLICY,
    Action,
    Decision,
    Filters,
    eligible_forecast,
    require,
)

WINDOW = timedelta(minutes=5)


@dataclass(frozen=True)
class Plan:
    run_id: str
    result: str
    decisions: tuple = ()
    observations: tuple = ()
    marks: tuple = ()
    order: Order | None = None
    attempt: int | None = None
    filters: Filters | None = None
    filter_source: Response | None = None
    reason: str | None = None
    position: str | None = None
    pending_exit: str | None = None
    http_status: int | None = None
    retry_after: int | None = None

    def report(self):
        return dict(
            mode="dry-run",
            run_id=self.run_id,
            result=self.result,
            reason=self.reason,
            http_status=self.http_status,
            retry_after=self.retry_after,
            position=self.position,
            pending_exit=self.pending_exit,
            decisions=[
                dict(
                    action=d.action.value,
                    at=d.at.isoformat(),
                    reason=d.reason,
                    missed_streak=d.missed_streak,
                    source_open=d.source_open.isoformat(),
                )
                for d in self.decisions
            ],
            observations=[
                dict(
                    prediction_id=o.prediction_id,
                    observed_by_worker_at=o.forecast.observed_at.isoformat(),
                    issued_at=o.forecast.issued_at.isoformat(),
                    cohort=o.forecast.cohort,
                    file_sha256=o.forecast.file_sha256,
                    automation_sha256=o.forecast.automation_sha256,
                )
                for o in self.observations
            ],
            mark_plans=self.marks,
            hypothetical_order=self.order.identity if self.order else None,
            filter_sha256=self.filters.payload_sha256 if self.filters else None,
            proposed_submission_at=self.order.submitted_at.isoformat()
            if self.order
            else None,
            proposed_expiry=self.order.expires_at.isoformat() if self.order else None,
            fresh_post_intent_quote_required=bool(self.order),
            portfolio_unchanged=True,
            order_submitted=False,
            fill_recorded=False,
        )


def plan_marks(view: Recovery, at, read_quote, read_state, clock):
    slot = boundary(view.activated) + timedelta(minutes=10)
    if slot + WINDOW <= view.activated:
        slot += STEP
    result = []
    while slot <= at:
        if slot not in view.slots:
            item = {
                "slot": slot.isoformat(),
                "at": at.isoformat(),
                "status": "MARK_MISSING",
            }
            if at < slot + WINDOW:
                try:
                    q = read_quote(view.state.account.portfolio, clock)
                    require(q.run_id == clock.run_id, "Prior-run mark quote.")
                    current = read_state()
                    require(
                        current.state.account.portfolio == view.state.account.portfolio,
                        "Mark market changed.",
                    )
                    at = clock.now()
                    item["at"] = at.isoformat()
                    account = current.state.account
                    mark = Mark(
                        account.portfolio,
                        q.identity,
                        at,
                        account.ledger_seq,
                        q,
                        records.fingerprint(VALUATION_POLICY),
                        slot=slot,
                    )
                    value = value_account(account, mark)
                    if slot in current.slots:
                        item["status"] = "ALREADY_MARKED"
                    elif value.equity is not None:
                        item.update(
                            status="MARK_PROPOSED",
                            ledger_seq=account.ledger_seq,
                            quote_sha256=q.payload_sha256,
                            bid=str(q.bid),
                            received_at=q.response_received_at.isoformat(),
                        )
                    else:
                        item.update(
                            status="MARK_UNAVAILABLE", reason=value.unavailable_reason
                        )
                except MarketError as exc:
                    item.update(status="MARK_UNAVAILABLE", reason=exc.code)
                    if exc.status in (418, 429):
                        raise
                if item["status"] == "MARK_UNAVAILABLE":
                    discovery = clock.now()
                    item["at"] = discovery.isoformat()
                    if discovery >= slot + WINDOW:
                        item["status"] = "MARK_MISSING"
            result.append(item)
        slot += STEP
    return tuple(result)


def forecast_plans(view, read_forward, clock):
    state = view.state
    decisions, observed = [], []
    now = clock.now()
    while state.next_source_open + STEP + timedelta(minutes=1) <= now:
        opened = state.next_source_open
        started = now
        evidence = read_forward(state.account.portfolio, opened, clock)
        now = clock.now()
        if evidence is None and started <= opened + STEP + CUTOFF < now:
            # Recheck absence after the exclusive cutoff if the read straddled it.
            evidence = read_forward(state.account.portfolio, opened, clock)
            now = clock.now()
        if evidence:
            f = evidence.forecast
            prior = next(
                (
                    d
                    for d in state.decisions
                    if d.forecast and d.forecast.record_id == f.record_id
                ),
                None,
            )
            if prior:
                require(
                    replace(f, observed_at=prior.forecast.observed_at)
                    == prior.forecast,
                    "Conflicting duplicate forecast.",
                )
            else:
                observed.append(evidence)
                key = "forecast:" + f.record_id
                require(
                    f.portfolio == state.account.portfolio and f.source_open == opened,
                    "Observed evidence belongs to a different horizon or market.",
                )
                if f.cohort == "timely_unattributed" and now < f.deadline:
                    # Stage 3 can publish its journal after publishing the record.
                    # An immutable 0002 forecast decision would consume its unique key.
                    break
                if f.issued_at <= view.activated:
                    d = Decision(
                        key,
                        f.portfolio,
                        now,
                        Action.SIGNAL_INELIGIBLE,
                        "issued_before_activation",
                        state.missed_streak,
                        opened,
                        f,
                    )
                    state = replace(
                        state, decisions=state.decisions + (d,), last_at=now
                    )
                else:
                    state, d = observe_forecast(state, f, key, now)
                decisions.append(d)
                if state.next_source_open != opened:
                    continue
        if now <= opened + STEP + CUTOFF:
            break
        state, d = miss_horizon(state, opened, "missed:" + opened.isoformat(), now)
        decisions.append(d)
    return state, tuple(decisions), tuple(observed)


def cycle(read_state, read_forward, read_filters, read_quote, clock, sink):
    """Emit one proposal. The only sink receives a Plan, never a write transaction."""
    plan = Plan(clock.run_id, "WAITING_FOR_HORIZON")
    try:
        clock.begin_cycle()
        view = read_state()
        at = clock.now()
        require(view.state.last_at <= at, "Recovery clock reversal.")
        reconcile(view.state.account)
        plan = replace(
            plan,
            position="long" if view.state.account.quantity else "flat",
            pending_exit=view.state.exit_required.identity
            if view.state.exit_required
            else None,
        )
        if view.status != "ACTIVE":
            plan = replace(plan, result=view.status)
        else:
            plan = _active_cycle(
                view, plan, read_state, read_forward, read_filters, read_quote, clock
            )
    except EvidenceError as exc:
        plan = Plan(
            clock.run_id,
            "EVIDENCE_UNAVAILABLE"
            if exc.code == "original_unavailable"
            else "INTEGRITY_PAUSE",
            reason=str(exc),
        )
    except MarketError as exc:
        plan = Plan(
            clock.run_id,
            "MARKET_UNAVAILABLE",
            reason=exc.code,
            http_status=exc.status,
            retry_after=exc.retry_after,
        )
    except IntegrityIssue as exc:
        plan = Plan(
            clock.run_id, "INTEGRITY_PAUSE", reason=f"{exc.code}:{exc.evidence_id}"
        )
    except (ValueError, ArithmeticError) as exc:
        plan = Plan(clock.run_id, "INTEGRITY_PAUSE", reason=str(exc))
    except psycopg.Error:
        plan = Plan(clock.run_id, "STATE_UNAVAILABLE")
    sink(plan)
    return plan


def _active_cycle(
    view, plan, read_state, read_forward, read_filters, read_quote, clock
):
    require(
        view.activated is not None and view.activated <= view.state.last_at,
        "Invalid activation time.",
    )
    try:
        state, decisions, observations = forecast_plans(view, read_forward, clock)
    except EvidenceError as exc:
        if exc.code != "original_unavailable" or not (
            view.pending or view.state.exit_required
        ):
            raise
        state, decisions, observations = view.state, (), ()
        plan = replace(plan, reason="forecast_source_unavailable")
    marks = plan_marks(view, clock.now(), read_quote, read_state, clock)
    plan = replace(plan, decisions=decisions, observations=observations, marks=marks)
    now = clock.now()
    if view.pending:
        result = (
            "EXPIRE_INTERRUPTED"
            if now >= view.pending.expires_at
            else "REJECT_INTERRUPTED"
        )
        return replace(
            plan,
            result=result,
            reason="saved_quote_observation"
            if view.pending_quotes
            else "intent_without_quote",
        )
    trigger = state.exit_required
    if not trigger:
        trigger = next(
            (
                d
                for d in reversed(state.decisions)
                if d.action == Action.BUY_REQUIRED
                and state.account.quantity == 0
                and eligible_forecast(d.forecast, now)
                and (
                    state.exit_satisfied_at is None
                    or d.forecast.issued_at > state.exit_satisfied_at
                )
            ),
            None,
        )
    if not trigger:
        result = (
            decisions[-1].action.value
            if decisions
            else ("ALREADY_PROCESSED" if view.state.decisions else plan.result)
        )
        if (
            observations
            and observations[-1].forecast.cohort == "timely_unattributed"
            and (
                not decisions
                or decisions[-1].source_open != observations[-1].forecast.source_open
            )
        ):
            return replace(
                plan, result="SIGNAL_INELIGIBLE", reason="awaiting_automation_evidence"
            )
        if decisions and decisions[-1].action == Action.BUY_REQUIRED:
            result = "ENTRY_WINDOW_CLOSED"
        return replace(plan, result=result)
    prior = [a for a in view.attempts if a.decision == trigger.identity]
    if prior and trigger.action == Action.BUY_REQUIRED:
        return replace(plan, result="BUY_ALREADY_ATTEMPTED", reason=prior[-1].status)
    if prior and now < prior[-1].at + WINDOW:
        return replace(plan, result="EXIT_RETRY_WAIT", reason=prior[-1].status)
    if trigger.action == Action.BUY_REQUIRED and trigger not in decisions:
        # A decision may have committed before its intent. Rebind to original bytes
        # before planning a new buy from that interrupted operation.
        original = read_forward(state.account.portfolio, trigger.source_open, clock)
        require(
            original is not None
            and replace(original.forecast, observed_at=trigger.forecast.observed_at)
            == trigger.forecast,
            "Saved decision conflicts with original evidence.",
        )
    try:
        source = read_filters(state.account.portfolio, clock)
        if read_state() != view:
            return replace(plan, result="REPLAN_REQUIRED", reason="portfolio_changed")
        now = clock.now()
        filters = effective_filters(source, state.account.portfolio, now)
    except MarketError as exc:
        return replace(
            plan,
            result="FILTER_REJECTED",
            reason=exc.code,
            http_status=exc.status,
            retry_after=exc.retry_after,
        )
    if trigger.action == Action.BUY_REQUIRED and now >= trigger.forecast.deadline:
        return replace(plan, result="ENTRY_WINDOW_CLOSED")
    n = len(prior) + 1
    order = Order(
        f"{trigger.identity}:attempt:{n}",
        trigger,
        state.account.balances,
        clock.run_id,
        now,
        now + timedelta(seconds=30),
    )
    return replace(
        plan,
        result=trigger.action.value if not prior else "EXIT_RETRY_REQUIRED",
        order=order,
        attempt=n,
        filters=filters,
        filter_source=source,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", choices=("dry-run", "market-smoke"), nargs="?", default="dry-run"
    )
    parser.add_argument(
        "--filter-archive",
        type=Path,
        help="Existing private directory for original exchangeInfo bytes (smoke only)",
    )
    args = parser.parse_args(argv)
    if args.mode == "market-smoke":
        rows = smoke(Clock(), filter_archive=args.filter_archive)
        print(json.dumps(rows, indent=2))
        return int(any(r["validation"] != "valid" for r in rows))
    if args.filter_archive is not None:
        parser.error("--filter-archive requires market-smoke")
    from backtest_badger.paper_fixture import demonstration

    plan = demonstration()
    print(json.dumps(dict(scenario="fabricated", **plan.report()), indent=2))
    return int(plan.result != "BUY_REQUIRED")


if __name__ == "__main__":
    raise SystemExit(main())

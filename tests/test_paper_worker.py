import json
import socket
import subprocess
from dataclasses import replace
from datetime import timedelta

import psycopg
import pytest

from backtest_badger import forward_evaluation
from backtest_badger import paper_fixture as fx
from backtest_badger import paper_worker as worker
from backtest_badger.paper_accounting import (
    Account,
    apply_trade,
    calculate_trade,
    fund_account,
)
from backtest_badger.paper_forward_adapter import EvidenceError
from backtest_badger.paper_market_data import MarketError
from backtest_badger.paper_strategy import State, observe_forecast
from backtest_badger.paper_types import STEP, Action, D, Side


def forbidden(*args, **kwargs):
    pytest.fail("Fixture planner attempted external I/O, scoring or scheduling.")


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(psycopg, "connect", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(forward_evaluation, "read_target", forbidden)
    before = {p: p.read_bytes() for p in fx.ROOT.rglob("*.json")}
    yield
    assert before == {p: p.read_bytes() for p in fx.ROOT.rglob("*.json")}


def view(*, long=False, opened=fx.OPEN):
    account = fund_account(Account(fx.portfolio()), fx.INCEPTION)
    if long:
        trade = calculate_trade(
            account.portfolio,
            "fabricated-buy",
            Side.BUY,
            fx.INCEPTION,
            D(2),
            D(100),
            ledger_seq_before=1,
        )
        account = apply_trade(account, trade)
    return worker.Recovery(
        State(account, opened, fx.INCEPTION),
        "ACTIVE",
        fx.INCEPTION,
        slots=frozenset({fx.INCEPTION}),
    )


def run(v, at=fx.ISSUED, forward=fx.original, filters=fx.filter_source, quote=fx.quote):
    output = []
    plan = worker.cycle(
        lambda: v, forward, filters, quote, fx.fixed_clock(at), output.append
    )
    assert output == [plan] and not plan.report()["order_submitted"]
    assert not plan.report()["fill_recorded"] and plan.report()["portfolio_unchanged"]
    return plan


@pytest.mark.parametrize(
    "long,offset,result",
    [
        (False, 0, "BUY_REQUIRED"),
        (True, 0, "HOLD"),
        (False, 1, "CASH_NOOP"),
        (True, 1, "EXIT_REQUIRED"),
    ],
)
def test_position_and_sign(long, offset, result):
    v = view(long=long, opened=fx.OPEN + offset * STEP)
    plan = run(v, fx.ISSUED + offset * STEP)
    assert plan.result == result
    assert plan.report()["fresh_post_intent_quote_required"] == (
        result in ("BUY_REQUIRED", "EXIT_REQUIRED")
    )


def test_dry_run_cli_and_stable_operation_identity(capsys):
    for argv in ([], ["dry-run"]):
        assert worker.main(argv) == 0
        row = json.loads(capsys.readouterr().out)
        assert row["result"] == "BUY_REQUIRED" and row["fill_recorded"] is False
        assert row["order_submitted"] is False and row["mode"] == "dry-run"
    v = view()
    a, b = run(v), run(v)
    assert a.order.identity == b.order.identity and a.run_id != b.run_id


def test_outage_streak_and_actual_discovery():
    v = view(long=True)

    def missing(*args):
        return None

    deadline = fx.OPEN + STEP + worker.CUTOFF
    assert not run(v, deadline, missing).decisions
    first = run(v, deadline + timedelta(seconds=1), missing)
    assert [d.action for d in first.decisions] == [Action.SIGNAL_STALE]
    now = deadline + 2 * STEP + timedelta(seconds=1)
    batch = run(v, now, missing)
    assert [d.missed_streak for d in batch.decisions] == [1, 2, 3]
    assert [d.action for d in batch.decisions] == [
        Action.SIGNAL_STALE,
        Action.EXIT_REQUIRED,
        Action.SIGNAL_STALE,
    ]
    assert all(d.at == now and d.forecast is None for d in batch.decisions)
    assert batch.order.decision == batch.decisions[1] and batch.attempt == 1
    assert len(batch.marks) == 2 and all(
        m["status"] == "MARK_MISSING" for m in batch.marks
    )


def test_eligible_resets_streak_and_sticky_exit_overrides_positive():
    v = view(long=True)
    prior = replace(v.state, next_source_open=fx.OPEN - STEP, missed_streak=1)
    now = fx.ISSUED - timedelta(seconds=1)
    state, d = worker.miss_horizon(prior, prior.next_source_open, "earlier-exit", now)
    p = run(replace(v, state=state))
    assert p.decisions[-1].action == Action.IGNORED_EXIT_PENDING
    assert p.decisions[-1].missed_streak == 0 and p.order.decision == d


def test_stale_forecast_then_missing_horizon():
    now = fx.OPEN + STEP + worker.CUTOFF + timedelta(seconds=1)
    p = run(view(), now)
    assert [d.action for d in p.decisions] == [
        Action.SIGNAL_INELIGIBLE,
        Action.SIGNAL_MISSED,
    ]
    assert p.observations[0].forecast.observed_at == now and p.order is None


def test_no_reentry_from_signal_issued_at_exit_satisfaction():
    v = view()
    v = replace(
        v, state=replace(v.state, exit_satisfied_at=fx.ISSUED, last_at=fx.ISSUED)
    )
    plan = run(v)
    assert (
        plan.result == "CASH_NOOP"
        and plan.decisions[0].reason == "forecast_predates_exit_satisfaction"
    )


@pytest.mark.parametrize("status", ["DRAFT", "CLOSED", "PAUSED", "BLOCKED_DUST"])
def test_inactive_no_source_reads(status):
    assert run(replace(view(), status=status), forward=forbidden).result == status


def test_duplicate_changed_evidence_pauses():
    v = view()
    f = fx.original(fx.portfolio(), fx.OPEN, fx.fixed_clock(fx.ISSUED)).forecast
    state, d = observe_forecast(
        v.state,
        replace(f, cohort="timely_unattributed", automation_sha256=None),
        "prior",
        fx.ISSUED,
    )
    assert run(replace(v, state=state)).result == "INTEGRITY_PAUSE"


def test_missing_archive_is_not_a_missed_forecast():
    def unavailable(*args):
        raise EvidenceError("original_unavailable", "operations")

    assert run(view(), fx.ISSUED + STEP, unavailable).result == "EVIDENCE_UNAVAILABLE"


def test_stale_filters_are_not_a_proposed_order():
    def stale(p, clock):
        return fx.filter_source(p, fx.fixed_clock(clock.now() - timedelta(hours=2)))

    p = run(view(), filters=stale)
    assert p.result == "FILTER_REJECTED" and p.order is None


def test_active_slot_and_stale_quote():
    v = view(long=True, opened=fx.OPEN + STEP)
    now = fx.ISSUED + STEP
    good = run(v, now)
    assert (
        good.marks[0]["status"] == "MARK_PROPOSED" and good.marks[0]["ledger_seq"] == 3
    )

    def stale(p, clock):
        q = fx.quote(p, clock)
        return replace(
            q,
            request_started_at=now - timedelta(seconds=2),
            response_received_at=now - timedelta(seconds=2),
        )

    assert run(v, now, quote=stale).marks[0]["status"] == "MARK_UNAVAILABLE"
    missed = run(v, fx.INCEPTION + STEP + worker.WINDOW, quote=forbidden)
    assert missed.marks[0]["status"] == "MARK_MISSING"


def test_throttle_stops_cycle_before_other_request():
    def throttled(*args):
        raise MarketError("rate_limited", 429, 15)

    plan = run(
        view(long=True, opened=fx.OPEN + STEP),
        fx.ISSUED + STEP,
        filters=forbidden,
        quote=throttled,
    )
    assert plan.result == "MARKET_UNAVAILABLE" and plan.order is None


def test_future_observation_or_state_fails_closed():
    v = view()
    p = run(v, fx.ISSUED - timedelta(seconds=1))
    assert p.result == "INTEGRITY_PAUSE" and p.order is None
    assert (
        run(replace(v, state=replace(v.state, last_at=fx.ISSUED + STEP))).result
        == "INTEGRITY_PAUSE"
    )


def test_restart_exit_remains_actionable_during_source_unavailability():
    v = view(long=True)
    prior = replace(v.state, next_source_open=fx.OPEN - STEP, missed_streak=1)
    state, d = worker.miss_horizon(prior, prior.next_source_open, "risk-off", fx.ISSUED)

    def unavailable(*args):
        raise EvidenceError("original_unavailable", "records")

    plan = run(replace(v, state=state), forward=unavailable)
    assert plan.order.decision == d and plan.reason == "forecast_source_unavailable"

    def corrupt(*args):
        raise EvidenceError("invalid_original", "corrupt.json")

    assert run(replace(v, state=state), forward=corrupt).result == "INTEGRITY_PAUSE"


def test_changed_snapshot_requires_replan_and_clock_cannot_be_reused():
    v = view()
    clock = fx.fixed_clock(fx.ISSUED)
    views = iter([v, replace(v, status="PAUSED")])

    def next_view():
        return next(views)

    plan = worker.cycle(
        next_view, fx.original, fx.filter_source, fx.quote, clock, lambda p: None
    )
    assert plan.result == "REPLAN_REQUIRED" and plan.order is None
    plan = worker.cycle(
        forbidden, forbidden, forbidden, forbidden, clock, lambda p: None
    )
    assert plan.result == "INTEGRITY_PAUSE" and "already used" in plan.reason


def test_cutoff_crossed_during_filter_read_blocks_entry():
    now = [fx.ISSUED]
    clock = worker.Clock(
        lambda: now[0], lambda: (now[0] - fx.ISSUED) // timedelta(microseconds=1) * 1000
    )

    def slow(p, c):
        response = fx.filter_source(p, c)
        now[0] = fx.OPEN + STEP + worker.CUTOFF
        return response

    plan = worker.cycle(
        lambda: view(), fx.original, slow, fx.quote, clock, lambda p: None
    )
    assert plan.result == "ENTRY_WINDOW_CLOSED" and plan.order is None


def test_publication_before_journal_preserves_unique_durable_forecast_key():
    v = view()

    def no_journal(p, opened, clock):
        o = fx.original(p, opened, clock)
        return replace(
            o,
            forecast=replace(
                o.forecast, cohort="timely_unattributed", automation_sha256=None
            ),
            journal=None,
        )

    first = run(v, forward=no_journal)
    assert (
        first.result == "SIGNAL_INELIGIBLE"
        and first.reason == "awaiting_automation_evidence"
    )
    assert first.observations and not first.decisions and first.order is None
    later = run(v, fx.ISSUED + timedelta(seconds=1))
    assert later.result == "BUY_REQUIRED" and len(later.decisions) == 1

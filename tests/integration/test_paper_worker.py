"""Fabricated Stage 4D.1 rehearsal on an empty, loopback-only revision 0002 DB."""

from datetime import timedelta

import psycopg
import pytest

from backtest_badger import paper_fixture as fx
from backtest_badger import paper_persistence as store
from backtest_badger import paper_records as rec
from backtest_badger.paper_clock import Clock
from backtest_badger.paper_market_data import QUOTE, effective_filters, url_for
from backtest_badger.paper_recovery import recover
from backtest_badger.paper_types import STEP, D
from backtest_badger.paper_worker import cycle

from .test_paper_persistence import financial, prepared_buy

pytestmark = pytest.mark.integration


def run(c, pid, at):
    before = financial(c, pid)
    now = [at]
    clock = Clock(
        lambda: now[0], lambda: (now[0] - at) // timedelta(microseconds=1) * 1000
    )
    output = []
    plan = cycle(
        lambda: recover(c, pid),
        fx.original,
        fx.filter_source,
        fx.quote,
        clock,
        output.append,
    )
    assert financial(c, pid) == before and output == [plan]
    assert not plan.report()["order_submitted"] and not plan.report()["fill_recorded"]
    return plan, clock, now


def save(c, pid, plan):
    for d, o in zip(plan.decisions, plan.observations, strict=True):
        store.record_decision(
            c,
            pid,
            d,
            artifact_relpath=o.artifact_relpath,
            prediction_id=o.prediction_id,
        )


def submit(c, pid, plan):
    return store.submit_order(c, pid, plan.order, plan.attempt).id


def fill(c, pid, plan, oid, clock, price):
    at = clock.now()
    q = fx.quote(plan.order.balances.portfolio, clock, price)
    qid = store.record_quote(c, pid, oid, q, at).id
    f = effective_filters(plan.filter_source, fx.portfolio(), at)
    assert f == plan.filters
    return store.commit_fill(
        c, pid, oid, qid, f, run_id=clock.run_id, at=at, recorded_at=at
    )


def test_original_positive_buy_failed_exit_restart_and_final_replay(
    connection, database
):
    c = connection
    p = fx.portfolio()
    pid = store.create_portfolio(
        c,
        p,
        rec.configuration(p.symbol, fx.RECIPE, fx.COHORT),
        rec.fingerprint(fx.COHORT),
        fx.INCEPTION,
    ).id
    store.fund_portfolio(c, pid, fx.INCEPTION)
    store.record_mark(
        c,
        pid,
        fx.INCEPTION,
        fx.INCEPTION,
        inception=True,
        quote=fx.quote(p, fx.fixed_clock(fx.INCEPTION)),
    )
    assert recover(c, pid).state.account.cash == D(10000)
    buy, clock, now = run(c, pid, fx.ISSUED)
    assert buy.result == "BUY_REQUIRED" and buy.attempt == 1
    save(c, pid, buy)
    # Crash between a committed decision and its intent.
    repeated, clock, now = run(c, pid, fx.ISSUED)
    assert (
        repeated.order.identity == buy.order.identity and repeated.run_id != buy.run_id
    )
    oid = submit(c, pid, repeated)
    now[0] += timedelta(milliseconds=250)
    fill(c, pid, repeated, oid, clock, "100")
    held = recover(c, pid).state.account
    assert held.ledger_seq == 3 and held.quantity == D("99.88")
    assert run(c, pid, now[0])[0].result == "ALREADY_PROCESSED"

    at = fx.ISSUED + STEP
    sell, clock, now = run(c, pid, at)
    assert (
        sell.result == "EXIT_REQUIRED" and sell.marks[-1]["status"] == "MARK_PROPOSED"
    )
    save(c, pid, sell)
    oid = submit(c, pid, sell)
    now[0] += timedelta(seconds=2)
    store.record_quote_failure(
        c,
        pid,
        oid,
        key="fabricated-timeout",
        run_id=clock.run_id,
        source_url=url_for(QUOTE, p.symbol),
        request_started_at=at,
        discovered_at=now[0],
        reason="timeout",
    )
    store.terminate_order(c, pid, oid, status="REJECTED", reason="timeout", at=now[0])
    assert recover(c, pid).state.account == held
    assert run(c, pid, at + timedelta(minutes=4))[0].result == "EXIT_RETRY_WAIT"
    with psycopg.connect(database, autocommit=True) as restarted:
        retry, clock, now = run(restarted, pid, at + timedelta(minutes=5))
        assert retry.result == "EXIT_RETRY_REQUIRED" and retry.attempt == 2
        assert (
            retry.run_id != sell.run_id and retry.order.identity != sell.order.identity
        )
        assert retry.marks[-1]["status"] == "MARK_MISSING"
        oid = submit(restarted, pid, retry)
        now[0] += timedelta(milliseconds=250)
        fill(restarted, pid, retry, oid, clock, "110")
        final = recover(restarted, pid)
        assert final.state.account.ledger_seq == 5 and final.state.account.quantity == 0
        assert (
            final.state.exit_required is None
            and final.state.exit_satisfied_at == now[0]
        )
        assert final.state.account.basis == 0 and final.state.account.realised > 0
        assert final.state.account.cash == D(10000) + final.state.account.realised
        print(
            "fabricated reconciliation",
            held.cash,
            held.quantity,
            final.state.account.cash,
        )
        assert run(restarted, pid, now[0])[0].order is None


@pytest.mark.parametrize("with_quote", [False, True])
def test_restart_after_intent_or_quote_never_consumes_old_evidence(
    connection, with_quote
):
    from .test_paper_persistence import (
        activate,
        attempt,
        portfolio,
        save_decision,
        signal,
    )
    from .test_paper_persistence import quote as saved_quote

    c = connection
    p = portfolio()
    pid, state = activate(c, p)
    at = p.inception_at + timedelta(seconds=1)
    state, d = signal(state, at, "1")
    save_decision(c, pid, d)
    o, oid = attempt(c, pid, d, at)
    if with_quote:
        store.record_quote(c, pid, oid, saved_quote(at, "old-process"), at)
    for age, result in ((1, "REJECT_INTERRUPTED"), (30, "EXPIRE_INTERRUPTED")):
        plan, _, _ = run(c, pid, at + timedelta(seconds=age))
        assert plan.result == result and plan.run_id != o.run_id and plan.order is None
    store.terminate_order(
        c, pid, oid, status="EXPIRED", reason="restart", at=o.expires_at
    )
    plan, _, _ = run(c, pid, o.expires_at)
    assert plan.result == "BUY_ALREADY_ATTEMPTED" and plan.reason == "EXPIRED"
    assert recover(c, pid).state.account.ledger_seq == 1


def test_integrity_pause_on_corrupted_snapshot(connection):
    c = connection
    pid, *_ = prepared_buy(c)
    c.execute("ALTER TABLE paper_ledger_entry DISABLE TRIGGER USER")
    c.execute(
        "UPDATE paper_ledger_entry SET posted_at=posted_at+interval '1 second' "
        "WHERE portfolio_id=%s",
        (pid,),
    )
    c.execute("ALTER TABLE paper_ledger_entry ENABLE TRIGGER USER")
    plan, _, _ = run(c, pid, fx.ISSUED)
    assert plan.result == "INTEGRITY_PAUSE" and plan.order is None


def test_outage_risk_exit_is_reconstructed_without_postings(connection):
    from .test_paper_persistence import fill as prior_fill

    c = connection
    pid, _, _, o, oid, qid = prepared_buy(c)
    prior_fill(c, pid, o, oid, qid)
    held = recover(c, pid).state.account
    # No valid original ever existed for these January fabricated source horizons.
    at = o.submitted_at + 2 * STEP + timedelta(minutes=20)
    plan, _, _ = run(c, pid, at)
    assert [d.action.value for d in plan.decisions] == ["SIGNAL_STALE", "EXIT_REQUIRED"]
    assert all(d.at == at and d.forecast is None for d in plan.decisions)
    for d in plan.decisions:
        store.record_decision(c, pid, d)
    state = recover(c, pid).state
    assert state.account == held and state.exit_required == plan.order.decision
    again, _, _ = run(c, pid, at)
    assert not again.decisions and again.order.identity == plan.order.identity


def test_restart_refuses_blocked_dust(connection):
    from dataclasses import replace

    from .test_paper_persistence import RUN, SEC, prepared_sell, rules

    c = connection
    pid, _, _, o, oid, qid = prepared_sell(c)
    at = o.submitted_at + SEC
    store.reject_dust(
        c, pid, oid, qid, replace(rules(o.submitted_at), step=D(2)), run_id=RUN, at=at
    )
    plan, _, _ = run(c, pid, at + timedelta(minutes=5))
    assert plan.result == "BLOCKED_DUST" and plan.pending_exit == o.decision.identity
    assert plan.order is None and recover(c, pid).state.account.quantity > 0

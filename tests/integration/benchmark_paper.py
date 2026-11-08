"""Explicit opt-in PG17 benchmark. Run pytest on this file with -s (see handoff)."""

import json
import math
import resource
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from statistics import median
from threading import Barrier
from time import perf_counter, process_time, sleep

import psycopg

from backtest_badger import forward
from backtest_badger import paper_evidence as archive
from backtest_badger import paper_fixture as fx
from backtest_badger import paper_persistence as store
from backtest_badger import paper_reconciliation as audit
from backtest_badger import paper_records as rec
from backtest_badger.paper_execution import Order
from backtest_badger.paper_forward_adapter import read_forecast
from backtest_badger.paper_market_data import effective_filters
from backtest_badger.paper_operations import ClockHealth, run_checked
from backtest_badger.paper_recovery import recover
from backtest_badger.paper_strategy import observe_forecast
from backtest_badger.paper_types import STEP, Action
from backtest_badger.paper_worker import cycle

from .paper_workload import COHORT, portfolio, publish_slot
from .paper_workload import originals as setup_sources

DAYS = (30, 90, 180, 365)
MIN = timedelta(minutes=1)


def establish(c, p, root, pin):
    pid = archive.scheduled_inception(
        c,
        root,
        p,
        rec.configuration(p.symbol, p.model_recipe_sha256, COHORT),
        pin,
        fx.fixed_clock(p.inception_at),
        fx.filter_source,
        fx.quote,
    )
    return pid, recover(c, pid).state


def advance(c, pid, state, n, evidence, adverse, root):
    p = state.account.portfolio
    slot = p.inception_at + n * STEP
    at = evidence.forecast.issued_at
    if n and n % 31:
        store.record_mark(
            c,
            pid,
            slot,
            slot,
            quote=archive.archive_quote(root, fx.quote(p, fx.fixed_clock(slot))),
        )
    state, d = observe_forecast(
        state, evidence.forecast, "forecast:" + evidence.forecast.record_id, at
    )
    archive.record_archived_decision(c, pid, root, d, evidence)
    trigger = state.exit_required or (d if d.action == Action.BUY_REQUIRED else None)
    if trigger:
        prior = c.execute(
            "SELECT count(*) FROM paper_order WHERE portfolio_id=%s AND decision_id=%s",
            (pid, rec.identity(pid, "decision", trigger.identity)),
        ).fetchone()[0]
        # Multiple genuine terminal attempts leave the original sticky obligation open.
        failures = (
            3
            if adverse
            else int(n % 17 == 0 and trigger.action == Action.EXIT_REQUIRED)
        )
        for offset in range(failures + (0 if adverse else 1)):
            when = at + 5 * MIN * offset
            clock = fx.fixed_clock(when)
            number = prior + offset + 1
            o = Order(
                f"{trigger.identity}:attempt:{number}",
                trigger,
                state.account.balances,
                clock.run_id,
                when,
                when + timedelta(seconds=30),
            )
            source = fx.filter_source(p, clock)
            rules = effective_filters(source, p, when)
            oid = archive.submit_archived_order(c, pid, root, o, number, source).id
            if offset < failures:
                store.record_quote_failure(
                    c,
                    pid,
                    oid,
                    key=o.identity,
                    run_id=o.run_id,
                    source_url="https://fabricated.invalid/bookTicker",
                    request_started_at=when,
                    discovered_at=when,
                    reason="fabricated_timeout",
                )
                store.terminate_order(
                    c, pid, oid, status="REJECTED", reason="fabricated_timeout", at=when
                )
            else:
                q = archive.archive_quote(root, fx.quote(p, clock))
                qid = store.record_quote(c, pid, oid, q, when).id
                store.commit_fill(
                    c, pid, oid, qid, rules, run_id=o.run_id, at=when, recorded_at=when
                )
        # Only the database can determine the resulting financial state.
        state = recover(c, pid).state
    if n and n % 31 == 0:
        now = max(at + 15 * MIN, state.last_at)
        store.record_mark(c, pid, slot, now, reason="fabricated missed window")
    return replace(
        state, decisions=(state.exit_required,) if state.exit_required else ()
    )


class CountingCursor(psycopg.Cursor):
    def execute(self, *args, **kwargs):
        self.connection.statements += 1
        return super().execute(*args, **kwargs)


def measure(dsn, pid, root, now, repeats):
    with psycopg.connect(dsn, autocommit=True, cursor_factory=CountingCursor) as c:
        c.statements = 0

        def original(p, opened, clock):
            return read_forecast(
                p, opened, root / "records", root / "operations", clock
            )

        samples = []
        for _ in range(repeats):
            before = c.statements
            then = perf_counter()
            clock = fx.fixed_clock(now)
            plan, incident = run_checked(
                c,
                pid,
                root / "private",
                ClockHealth(True, now, MIN / 6000),
                clock,
                lambda clock=clock: cycle(
                    lambda: recover(c, pid),
                    original,
                    fx.filter_source,
                    fx.quote,
                    clock,
                    lambda plan: None,
                ),
            )
            assert incident is None
            assert plan.result == "EXIT_RETRY_REQUIRED"
            samples.append((perf_counter() - then, c.statements - before))
        p = recover(c, pid).state.account.portfolio
        start = perf_counter()
        assert original(
            p, fx.OPEN + STEP * ((now - fx.INCEPTION) // STEP), fx.fixed_clock(now)
        )
        return samples, perf_counter() - start


def timed_replay(c, pid):
    from unittest.mock import patch

    # Attribute timings inside the same complete independent audit. SQL fetch/decoding,
    # quote checks and prefix/relationship checks remain in the total.
    times = {"ledger": 0.0, "marks": 0.0}

    def timer(key, fn):
        def wrapped(*args, **kwargs):
            start = perf_counter()
            value = fn(*args, **kwargs)
            times[key] += perf_counter() - start
            return value

        return wrapped

    with (
        patch.object(audit, "simulate_order", timer("ledger", audit.simulate_order)),
        patch.object(audit, "apply_trade", timer("ledger", audit.apply_trade)),
        patch.object(audit, "value_account", timer("marks", audit.value_account)),
    ):
        start = perf_counter()
        snap = audit.reconcile_portfolio(c, pid)
        assert snap.exit_decision_id and snap.account.quantity
        times["total"] = perf_counter() - start
    return times


def remaining_journals(root, sample, start, minutes):
    journal = json.loads(sample.journal["json_utf8"])
    for minute in minutes:
        if minute == 11:
            continue
        at = start + minute * MIN
        run = rec.identity("fabricated", "collector", at.isoformat()).hex
        markets = {
            k: dict(v, status="already-recorded")
            if minute > 11
            else {"status": "not-yet-eligible"}
            for k, v in journal["markets"].items()
        }
        body = dict(
            journal,
            run_id=run,
            started_at=at.isoformat(),
            finished_at=at.isoformat(),
            markets=markets,
        )
        name = f"{at:%Y%m%dT%H%M%S%fZ}-{run}.json"
        (root / "operations" / name).write_bytes(forward.canonical(body) + b"\n")


def race_mark_and_fill(dsn, c, pid, private):
    """Measure the real locked fill path against a simultaneous scheduled mark."""
    view = recover(c, pid)
    state = view.state
    p = state.account.portfolio
    at = fx.INCEPTION + 365 * 6 * STEP
    clock = fx.fixed_clock(at)
    trigger = state.exit_required
    number = 1 + sum(a.decision == trigger.identity for a in view.attempts)
    order = Order(
        f"{trigger.identity}:attempt:{number}",
        trigger,
        state.account.balances,
        clock.run_id,
        at,
        at + timedelta(seconds=30),
    )
    source = fx.filter_source(p, clock)
    rules = effective_filters(source, p, at)
    oid = archive.submit_archived_order(c, pid, private, order, number, source).id
    qid = store.record_quote(
        c, pid, oid, archive.archive_quote(private, fx.quote(p, clock)), at
    ).id
    mark_quote = archive.archive_quote(private, fx.quote(p, fx.fixed_clock(at)))
    barrier = Barrier(2)

    def attempt(kind):
        with psycopg.connect(
            dsn, autocommit=True, application_name="d2_race_" + kind
        ) as writer:
            barrier.wait(timeout=10)
            then = perf_counter()
            if kind == "fill":
                receipt = store.commit_fill(
                    writer,
                    pid,
                    oid,
                    qid,
                    rules,
                    run_id=clock.run_id,
                    at=at,
                    recorded_at=at,
                )
            else:
                receipt = store.record_mark(writer, pid, at, at, quote=mark_quote)
            assert receipt.created
            return receipt.id, perf_counter() - then

    waits = {"fill": 0.0, "mark": 0.0}
    with ThreadPoolExecutor(2) as pool:
        jobs = {kind: pool.submit(attempt, kind) for kind in waits}
        last = perf_counter()
        while not all(job.done() for job in jobs.values()):
            waiting = c.execute(
                "SELECT application_name FROM pg_stat_activity "
                "WHERE datname=current_database() AND application_name IN "
                "('d2_race_mark','d2_race_fill') AND wait_event_type='Lock'"
            ).fetchall()
            now = perf_counter()
            for (name,) in waiting:
                waits[name.removeprefix("d2_race_")] += now - last
            last = now
            sleep(0.005)
        results = {k: v.result() for k, v in jobs.items()}
    snap = archive.verify_portfolio(c, pid, private)
    point = snap.marks[results["mark"][0]]
    assert snap.account.quantity == 0 and snap.exit_decision_id is None
    assert point.mark.asof_ledger_seq in {
        state.account.ledger_seq,
        snap.account.ledger_seq,
    }
    account = snap.prefixes[point.mark.asof_ledger_seq]
    assert point.equity == account.cash + account.quantity * mark_quote.bid
    print(
        "FABRICATED_RACE",
        json.dumps(
            dict(
                duration_s={k: v[1] for k, v in results.items()},
                sampled_lock_wait_s=waits,
                marked_sequence=point.mark.asof_ledger_seq,
                final_sequence=snap.account.ledger_seq,
            )
        ),
        flush=True,
    )


def test_fabricated_year(database, connection, tmp_path):
    c = connection
    private, pin = setup_sources(tmp_path)
    states = {
        s: establish(c, portfolio(s), private, pin) for s in ("BTCUSDT", "ETHUSDT")
    }
    adverse_slots = {day * 6 - 1 for day in DAYS}
    initial_bytes = c.execute("SELECT pg_database_size(current_database())").fetchone()[
        0
    ]
    for n in range(365 * 6):
        positive = n + 1 in adverse_slots or (n not in adverse_slots and n % 12 < 6)
        originals = publish_slot(
            tmp_path,
            fx.OPEN + n * STEP,
            dict.fromkeys(states, 0.001 if positive else -0.001),
        )
        for symbol, (pid, state) in states.items():
            states[symbol] = (
                pid,
                advance(
                    c, pid, state, n, originals[symbol], n in adverse_slots, private
                ),
            )
        exemplar = originals["BTCUSDT"]
        boundary = fx.OPEN + (n + 1) * STEP
        remaining_journals(
            tmp_path, exemplar, boundary, range(1, 27 if n in adverse_slots else 240, 5)
        )
        if n not in adverse_slots:
            continue
        now = fx.ISSUED + n * STEP + 15 * MIN
        timings = timed_replay(c, next(iter(states.values()))[0])
        start, cpu = perf_counter(), process_time()
        with ThreadPoolExecutor(2) as pool:
            jobs = [
                pool.submit(measure, database, pid, tmp_path, now, 6)
                for pid, _ in states.values()
            ]
            results = [job.result() for job in jobs]
        elapsed, cpu = perf_counter() - start, process_time() - cpu
        samples = sorted(t for rows, _ in results for t, _ in rows)
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        size, reads, hits, temp = c.execute(
            "SELECT pg_database_size(datname),blks_read,blks_hit,temp_bytes "
            "FROM pg_stat_database WHERE datname=current_database()"
        ).fetchone()
        report = dict(
            days=(n + 1) // 6,
            decisions=(n + 1) * 2,
            cycle_samples=len(samples),
            journals=len(list((tmp_path / "operations").iterdir())),
            median_s=median(samples),
            p95_s=samples[math.ceil(0.95 * len(samples)) - 1],
            worst_s=max(samples),
            queries=sorted({q for rows, _ in results for _, q in rows}),
            discovery_s=[v for _, v in results],
            audit_s=timings,
            concurrent_wall_s=elapsed,
            client_cpu_s=cpu,
            peak_rss_mib=mem / (1048576 if sys.platform == "darwin" else 1024),
            db_growth_bytes=size - initial_bytes,
            block_reads=reads,
            buffer_hits=hits,
            temp_bytes=temp,
            events=dict(
                c.execute(
                    "SELECT event_type,count(*) FROM paper_market_event GROUP BY 1"
                ).fetchall()
            ),
        )
        print("FABRICATED", json.dumps(report), flush=True)
        remaining_journals(tmp_path, exemplar, boundary, range(31, 240, 5))

    race_mark_and_fill(database, c, states["BTCUSDT"][0], private)

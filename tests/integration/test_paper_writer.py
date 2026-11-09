"""Fabricated writer tests through restricted PG17 logins and original Stage 3 bytes."""

import json
import os
import signal
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from multiprocessing import get_context
from threading import Event
from time import sleep
from uuid import uuid4

import psycopg
import pytest

from backtest_badger import paper_evidence as evidence
from backtest_badger import paper_fixture as fx
from backtest_badger.paper_market_data import FILTERS, Market, MarketError
from backtest_badger.paper_recovery import recover
from backtest_badger.paper_types import STEP

from .paper_roles import isolated_roles, upgrade
from .paper_workload import originals, portfolio, publish_slot
from .paper_writer_harness import timed_writer, transport
from .test_paper_readiness import activate

pytestmark = pytest.mark.integration
S = timedelta(seconds=1)
FIVE = timedelta(minutes=5)


@pytest.fixture
def staged(test_admin, tmp_path):
    root, manifest = originals(tmp_path)
    with isolated_roles(*test_admin, uuid4().hex) as (dsns, roles):
        upgrade(dsns, roles)
        with psycopg.connect(dsns["operator"], autocommit=True) as op:
            pid = activate(op, root, manifest, portfolio("BTCUSDT"), fx.INCEPTION)
        publish_slot(tmp_path, fx.OPEN, {"BTCUSDT": 0.001})
        yield dsns["worker"], pid, tmp_path


def snapshot(staged):
    dsn, pid, root = staged
    with psycopg.connect(dsn, autocommit=True) as c:
        evidence.verify_portfolio(c, pid, root / "private")
        return recover(c, pid)


def die_at(staged, at, point):
    def stop(name):
        if point == name:
            os.kill(os.getpid(), signal.SIGKILL)

    timed_writer(*staged, at, checkpoint=stop)


@pytest.mark.parametrize(
    "point,seq,orders,observed",
    [
        ("before_decision", 1, 0, 0),
        ("after_decision", 1, 0, 0),
        ("before_submission", 1, 0, 0),
        ("after_submission", 1, 1, 0),
        ("before_quote", 1, 1, 0),
        ("after_receipt", 1, 1, 0),
        ("after_observation", 1, 1, 1),
        ("during_fill", 1, 1, 1),
        ("after_fill_commit", 3, 1, 0),
        ("shutdown", 3, 1, 0),
        ("during_mark", 3, 1, 0),
    ],
)
def test_process_death_at_durable_boundary(staged, point, seq, orders, observed):
    at = fx.ISSUED
    if point == "during_mark":
        assert timed_writer(*staged, at)["result"] == "FILLED"
        at = fx.INCEPTION + STEP
    child = get_context("spawn").Process(target=die_at, args=(staged, at, point))
    child.start()
    child.join(25)
    assert child.exitcode == -signal.SIGKILL
    view = snapshot(staged)
    assert len(view.state.decisions) == (0 if point == "before_decision" else 1)
    assert (view.state.account.ledger_seq, len(view.attempts), view.pending_quotes) == (
        seq,
        orders,
        observed,
    )
    if point == "during_mark":
        assert at not in view.slots
    result = timed_writer(*staged, at + 2 * S)
    assert result["result"] != "STOPPED", result
    current = snapshot(staged)
    assert current.pending is None
    if orders and seq == 1:
        assert result["result"] == "REJECTED"
        assert current.state.account.cash == 10000
        assert timed_writer(*staged, at + 3 * S)["result"] == "BUY_ALREADY_ATTEMPTED"
    else:
        assert len(current.attempts) == 1 and current.state.account.ledger_seq == 3


@pytest.mark.parametrize(
    "failure",
    [
        "prior_run",
        "pre_submission",
        "stale",
        "expired",
        "depth",
        "missing",
        "filters",
        "418",
        "429",
    ],
)
def test_unsuccessful_attempt_has_no_postings(staged, failure):
    def acquire(endpoint, symbol, clock):
        response = transport(endpoint, symbol, clock, depth="0")
        if endpoint == FILTERS:
            if failure == "filters":
                rules = json.loads(response.body)
                rules["symbols"][0]["filters"].append({"filterType": "UNSUPPORTED"})
                return fx.response(FILTERS, Market(symbol), clock, rules)
            return response
        if failure in {"418", "429", "missing"}:
            raise MarketError(
                "unavailable", int(failure) if failure != "missing" else None
            )
        if failure == "prior_run":
            return replace(response, run_id=uuid4().hex)
        if failure == "pre_submission":
            return replace(response, start=replace(response.start, wall=fx.INCEPTION))
        return response

    def delay(name):
        if name == "after_observation" and failure == "stale":
            sleep(1.05)

    if failure == "expired":
        child = get_context("spawn").Process(
            target=die_at, args=(staged, fx.ISSUED, "after_submission")
        )
        child.start()
        child.join(25)
        assert child.exitcode == -signal.SIGKILL
        result = timed_writer(*staged, fx.ISSUED + 35 * S)
    else:
        result = timed_writer(*staged, fx.ISSUED, acquire=acquire, checkpoint=delay)
    assert result["result"] == (
        "FILTER_REJECTED"
        if failure == "filters"
        else "EXPIRED"
        if failure == "expired"
        else "REJECTED"
    ), result
    state = snapshot(staged)
    assert state.state.account.ledger_seq == 1 and state.state.account.cash == 10000
    if failure in {"418", "429"}:
        assert "provider_throttled" in {r["code"] for r in result["incidents"]}


def writer_lifecycle(dsns, root, archive, manifest):
    """Drive both markets through entry, hold, sticky exit, liquidation and re-entry."""
    symbols = ("BTCUSDT", "ETHUSDT")
    with psycopg.connect(dsns["operator"], autocommit=True) as op:
        pids = {
            s: activate(op, archive, manifest, portfolio(s), fx.INCEPTION)
            for s in symbols
        }

    def both(at, signals=None, **kwargs):
        if signals:
            publish_slot(root, fx.OPEN + ((at - fx.ISSUED) // STEP) * STEP, signals)
        with ThreadPoolExecutor(2) as pool:
            jobs = [
                pool.submit(timed_writer, dsns["worker"], pid, root, at, **kwargs)
                for pid in pids.values()
            ]
            results = [j.result() for j in jobs]
            assert all(r["result"] != "STOPPED" for r in results), results
            return [r["result"] for r in results]

    at = fx.ISSUED
    positive, negative = (dict.fromkeys(symbols, v) for v in (0.01, -0.01))
    assert both(at, positive) == ["FILLED"] * 2
    assert both(at + STEP, positive) == ["HOLD"] * 2

    def shallow(endpoint, symbol, clock):
        return transport(endpoint, symbol, clock, depth="0")

    assert both(at + 2 * STEP, negative, acquire=shallow) == ["REJECTED"] * 2
    assert both(at + 2 * STEP + S) == ["EXIT_RETRY_WAIT"] * 2
    assert both(at + 3 * STEP, positive, acquire=shallow) == ["REJECTED"] * 2
    assert both(at + 3 * STEP + FIVE + S) == ["FILLED"] * 2
    assert both(at + 4 * STEP, negative) == ["CASH_NOOP"] * 2
    assert both(at + 5 * STEP, positive) == ["FILLED"] * 2
    assert both(at + 6 * STEP + 2 * FIVE) == ["SIGNAL_STALE"] * 2
    assert both(at + 7 * STEP + 2 * FIVE, acquire=shallow) == ["REJECTED"] * 2
    assert both(at + 7 * STEP + 3 * FIVE + S) == ["FILLED"] * 2
    with psycopg.connect(dsns["worker"], autocommit=True) as c:
        expected = {
            pid: evidence.verify_portfolio(c, pid, archive) for pid in pids.values()
        }
        for snap in expected.values():
            assert snap.account.quantity == 0 and snap.account.ledger_seq == 9
            assert snap.exit_decision_id is None and len(snap.marks) == 8
            assert sum(m is None for m in snap.marks.values()) == 2
        return expected


@pytest.mark.parametrize(
    "case", ["lock", "slow", "dispatch", "race", "overlap", "timeout"]
)
def test_contention_at_financial_admission(staged, case):
    dsn, pid, _ = staged
    with psycopg.connect(dsn, autocommit=True) as c, ThreadPoolExecutor(1) as pool:
        ready, release = Event(), Event()

        def checkpoint(point):
            if point == "after_observation" and case in {"lock", "timeout", "race"}:
                ready.set()
                assert release.wait(10)
            if point == "before_commit" and case == "dispatch":
                sleep(1.05)
            if point == "during_fill" and case == "slow":
                # Actual PostgreSQL response delay after the ledger DML.
                c.execute("SELECT pg_sleep(1.05)")
            if point == "after_submission" and case == "overlap":
                ready.set()
                assert release.wait(10)

        run_at = fx.ISSUED
        if case == "race":
            run_at += STEP
            publish_slot(staged[2], fx.OPEN + STEP, {"BTCUSDT": 0.001})
        run = pool.submit(timed_writer, *staged, run_at, checkpoint=checkpoint)
        if case not in {"slow", "dispatch"}:
            assert ready.wait(10)
            if case == "overlap":
                assert (
                    timed_writer(*staged, fx.ISSUED + S)["incidents"][0]["code"]
                    == "cycle_overlap"
                )
                release.set()
            elif case == "race":
                from backtest_badger import paper_persistence as store

                # Commit a separate observed mark while the financial writer is waiting.
                with store._write(c, pid) as (cur, row):
                    at = cur.execute(
                        "SELECT paper_latest(%s) AS at", (pid,)
                    ).fetchone()["at"]
                    quote = evidence.archive_quote(
                        staged[2] / "private",
                        fx.quote(portfolio("BTCUSDT"), fx.fixed_clock(at)),
                    )
                    store._mark(
                        cur, pid, row, fx.INCEPTION + STEP, at, quote, None, False
                    )
                    release.set()
                    sleep(0.05)
            else:
                with c.transaction():
                    c.execute(
                        "SELECT portfolio_id FROM paper_portfolio "
                        "WHERE portfolio_id=%s FOR UPDATE",
                        (pid,),
                    )
                    release.set()
                    sleep(3.3 if case == "timeout" else 1.05)
        result = run.result()
    assert result["result"] == {
        "timeout": "STOPPED",
        "lock": "REJECTED",
        "slow": "REJECTED",
        "dispatch": "REJECTED",
    }.get(case, "FILLED"), result
    print("FABRICATED_TIMING", case, result, flush=True)
    if case == "timeout":
        assert result["incidents"][0]["code"] == "database_contention"
        assert timed_writer(*staged, fx.ISSUED + 35 * S)["result"] == "EXPIRED"
    assert snapshot(staged).state.account.ledger_seq == (
        3 if case in {"race", "overlap"} else 1
    )
    if case == "race":
        with psycopg.connect(dsn) as c:
            assert c.execute(
                "SELECT asof_ledger_seq FROM paper_market_event "
                "WHERE portfolio_id=%s AND mark_slot=%s",
                (pid, fx.INCEPTION + STEP),
            ).fetchone() == (1,)


@pytest.mark.parametrize(
    "failure", ["journal", "missing_forecast", "archive", "saved_original"]
)
def test_source_integrity_stops_and_retains_incident(staged, failure, monkeypatch):
    _, pid, root = staged
    expected_seq = 1
    if failure == "journal":
        path = next((root / "operations").iterdir())
        path.write_bytes(
            path.read_bytes().replace(b'"status":"recorded"', b'"status":"failed"')
        )
    elif failure == "missing_forecast":
        next((root / "records").iterdir()).unlink()
    elif failure == "archive":

        def unavailable(*_args):
            raise OSError("fabricated archive failure")

        monkeypatch.setattr(evidence, "retain_body", unavailable)
    else:
        assert timed_writer(*staged, fx.ISSUED)["result"] == "FILLED"
        f = snapshot(staged).state.decisions[0].forecast
        (root / "private" / (f.automation_sha256 + ".json")).unlink()
        expected_seq = 3
    for offset in [2, 3]:
        result = timed_writer(*staged, fx.ISSUED + offset * S)
        assert (
            result["result"] == "STOPPED"
            and result["incidents"][0]["severity"] == "integrity"
        )
    assert (root / "runtime" / (str(pid) + ".halt")).is_file()
    with psycopg.connect(staged[0], autocommit=True) as c:
        assert recover(c, pid).state.account.ledger_seq == expected_seq


def test_unknown_commit_acknowledgement_recovers_without_reposting(staged):
    from psycopg import sql

    class LostAck(psycopg.Cursor):
        def execute(self, query, *args, **kwargs):
            result = super().execute(query, *args, **kwargs)
            if (
                isinstance(query, sql.Composed)
                and "AS admitted FROM sample; COMMIT" in query.as_string()
            ):
                self.connection.close()
                raise psycopg.OperationalError("fabricated lost commit acknowledgement")
            return result

    from .paper_writer_harness import writer_on

    dsn, pid, root = staged
    with psycopg.connect(dsn, autocommit=True, cursor_factory=LostAck) as c:
        report = writer_on(c, pid, root, fx.ISSUED)
    assert report["result"] == "STOPPED"
    assert snapshot(staged).state.account.ledger_seq == 3
    assert timed_writer(*staged, fx.ISSUED + S)["result"] == "ALREADY_PROCESSED"
    assert len(snapshot(staged).attempts) == 1


def test_reviewed_staging_entry_point(staged, monkeypatch, capsys):
    from backtest_badger import paper_writer_cli as cli

    dsn, pid, root = staged
    runtime = root / "runtime"
    runtime.mkdir(mode=0o700)
    health = root / "clock.json"
    config = root / "writer.json"
    config.write_text(
        json.dumps(
            dict(
                mode="staging-once",
                portfolio_id=str(pid),
                symbol="BTCUSDT",
                config_sha256=portfolio("BTCUSDT").config_sha256,
                records=str(root / "records"),
                journals=str(root / "operations"),
                dsn=dsn,
                archive=str(root / "private"),
                runtime=str(runtime),
                clock_observation=str(health),
            )
        )
    )
    config.chmod(0o600)
    args = ["staging-once", "--config", str(config)]
    monkeypatch.setattr(cli, "Clock", lambda: fx.fixed_clock(fx.ISSUED))
    monkeypatch.setattr(cli, "shared_provider", lambda _: transport)
    assert cli.main(args) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["incidents"][0]["code"] == "clock_uncertain"
    assert not snapshot(staged).state.decisions
    health.write_text(
        json.dumps(
            dict(synchronised=True, sampled_at=fx.ISSUED.isoformat(), uncertainty_ms=5)
        )
    )
    # The staging test supplies a fabricated external observer in place of root.
    monkeypatch.setattr(cli, "trusted_clock_path", lambda p: p == health)
    assert cli.main(args) == 0
    assert json.loads(capsys.readouterr().out)["result"] == "FILLED"
    monkeypatch.setenv("PGHOSTADDR", "192.0.2.1")
    assert cli.main(args) == 1
    assert (
        json.loads(capsys.readouterr().out)["result"]
        == "CONFIGURATION_OR_CONNECTION_FAILED"
    )


def test_post_commit_request_and_uncontended_spread(staged):
    from decimal import Decimal

    dsn, pid, _ = staged
    observations = []

    def quoted(endpoint, symbol, clock):
        if endpoint == FILTERS:
            return transport(endpoint, symbol, clock)
        with psycopg.connect(dsn) as independent:
            order = independent.execute(
                "SELECT status,run_id FROM paper_order WHERE portfolio_id=%s", (pid,)
            ).fetchone()
        observations.append(order)
        assert order == ("SUBMITTED", clock.run_id)
        return fx.response(
            endpoint,
            Market(symbol),
            clock,
            dict(
                symbol=symbol,
                bidPrice="99",
                askPrice="101",
                bidQty="1000",
                askQty="1000",
            ),
        )

    result = timed_writer(*staged, fx.ISSUED, acquire=quoted)
    assert result["result"] == "FILLED" and len(observations) == 1
    with psycopg.connect(dsn) as c:
        assert c.execute(
            "SELECT simulated_price FROM paper_market_event WHERE "
            "portfolio_id=%s AND event_type='FILL'",
            (pid,),
        ).fetchone() == (Decimal("101.0202"),)
    assert snapshot(staged).state.account.ledger_seq == 3
    print("FABRICATED_TIMING uncontended", result, flush=True)


def test_outage_catchup_commits_progress_and_prioritises_sticky_exit(staged):
    assert timed_writer(*staged, fx.ISSUED)["result"] == "FILLED"
    returned = fx.ISSUED + 6 * STEP
    child = get_context("spawn").Process(
        target=die_at, args=(staged, returned, "after_decision")
    )
    child.start()
    child.join(25)
    assert child.exitcode == -signal.SIGKILL
    assert snapshot(staged).state.missed_streak == 1
    assert timed_writer(*staged, returned + 2 * S)["result"] == "FILLED"
    durable = snapshot(staged)
    assert durable.state.account.quantity == 0 and durable.state.missed_streak == 2
    assert len(durable.state.decisions) == 3 and durable.state.exit_required is None
    assert timed_writer(*staged, returned + 3 * S)["result"] == "SIGNAL_MISSED"
    assert snapshot(staged).state.missed_streak == 5


def test_clock_lost_before_commit_rolls_back_postings(staged):
    from backtest_badger.paper_operations import ClockHealth

    from .paper_writer_harness import writer_on

    dsn, pid, root = staged
    healthy = ClockHealth(True, fx.ISSUED, timedelta(milliseconds=1))

    def revoke(point):
        nonlocal healthy
        if point == "before_commit":
            healthy = None

    with psycopg.connect(dsn, autocommit=True) as c:
        result = writer_on(
            c, pid, root, fx.ISSUED, health=lambda: healthy, checkpoint=revoke
        )
    assert (
        result["result"] == "STOPPED"
        and result["incidents"][0]["code"] == "clock_uncertain"
    )
    state = snapshot(staged)
    assert state.state.account.ledger_seq == 1 and state.pending_quotes == 1
    assert timed_writer(*staged, fx.ISSUED + 35 * S)["result"] == "EXPIRED"

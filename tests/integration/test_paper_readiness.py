"""Fabricated, controlled-clock operational rehearsal. No provider transport."""

import json
import os
import re
import subprocess
from contextlib import closing
from dataclasses import replace
from datetime import timedelta
from time import perf_counter, sleep
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from backtest_badger import forward
from backtest_badger import paper_checkpoint as backup
from backtest_badger import paper_evidence as evidence
from backtest_badger import paper_fixture as fx
from backtest_badger import paper_persistence as store
from backtest_badger import paper_records as rec
from backtest_badger.candles import save_candle
from backtest_badger.forward_evaluation import read_target
from backtest_badger.paper_forward_adapter import read_forecast
from backtest_badger.paper_reconciliation import IntegrityIssue
from backtest_badger.paper_recovery import recover
from backtest_badger.paper_types import STEP
from backtest_badger.paper_worker import cycle

from .paper_roles import isolated_roles, restore_admin, upgrade
from .paper_workload import COHORT, originals, portfolio, publish_slot

pytestmark = pytest.mark.integration
FIVE = timedelta(minutes=5)


def activate(c, archive, pin, p, at, read=fx.quote):
    return evidence.scheduled_inception(
        c,
        archive,
        p,
        rec.configuration(p.symbol, p.model_recipe_sha256, COHORT),
        pin,
        fx.fixed_clock(at),
        fx.filter_source,
        read,
    )


def deny(c, query):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        c.execute(query)


def check_security(c, roles):
    assert c.execute(
        "SELECT current_user=session_user, rolsuper, rolbypassrls, rolcreaterole,"
        "rolcreatedb, rolinherit FROM pg_roles WHERE rolname=current_user"
    ).fetchone() == (True, False, False, False, False, False)
    for command in (
        "ALTER TABLE paper_order DISABLE TRIGGER USER",
        "SET session_replication_role=replica",
        "UPDATE paper_decision SET model_forecast=2",
        "DELETE FROM paper_decision",
        "UPDATE paper_ledger_entry SET delta_units=0",
        "TRUNCATE paper_market_event",
        "UPDATE paper_portfolio SET strategy_config='{}'",
        "DROP TABLE paper_order",
        "CREATE TEMP TABLE unexpected(i int)",
        "CREATE SCHEMA unexpected",
        "CREATE TABLE surprise(i int)",
        "SELECT lo_create(0)",
        "UPDATE market SET symbol='OTHER'",
        "SELECT * FROM candle",
        "DELETE FROM alembic_version",
        "SELECT paper_guard_portfolio()",
        sql.SQL("ALTER ROLE {} SUPERUSER").format(roles["reader"]),
        sql.SQL("SET ROLE {}").format(roles["owner"]),
    ):
        deny(c, command)
    assert not c.execute(
        "SELECT has_table_privilege(current_user,'paper_portfolio','INSERT')"
    ).fetchone()[0]


def test_role_boundaries_and_inception(test_admin, tmp_path, candle_observation):
    archive, pin = originals(tmp_path)
    p = portfolio("BTCUSDT")
    opening = fx.INCEPTION + timedelta(seconds=13)
    with isolated_roles(*test_admin, uuid4().hex) as (dsns, roles):
        with psycopg.connect(dsns["collector"], autocommit=True) as collector:
            save_candle(collector, candle_observation)
            before = collector.execute("SELECT * FROM candle").fetchall()
        upgrade(dsns, roles)
        with psycopg.connect(dsns["collector"], autocommit=True) as collector:
            assert collector.execute("SELECT * FROM candle").fetchall() == before
            revised = replace(
                candle_observation,
                close=candle_observation.close + 1,
                observed_at=candle_observation.observed_at + timedelta(seconds=10),
            )
            assert save_candle(collector, revised) == "revised"
            market, candles = forward.read_window(
                collector, "BTCUSDT", revised.open_time
            )
            assert candles[0]["close"] == revised.close and candles[0]["version"] == 2
            assert (
                read_target(
                    collector,
                    dict(market=market, target_open_time=revised.open_time.isoformat()),
                )
                == candles
            )
            deny(collector, "SELECT * FROM paper_decision")
        with (
            psycopg.connect(dsns["operator"], autocommit=True) as op,
            psycopg.connect(dsns["worker"], autocommit=True) as worker,
            psycopg.connect(dsns["reader"], autocommit=True) as reader,
            psycopg.connect(dsns["owner"], autocommit=True) as owner,
        ):
            check_security(worker, roles)
            deny(reader, "INSERT INTO paper_decision DEFAULT VALUES")
            deny(op, "INSERT INTO paper_order DEFAULT VALUES")
            with pytest.raises(ValueError, match="window"):
                activate(op, archive, pin, p, fx.INCEPTION + FIVE)

            def unavailable(p, clock):
                raise TimeoutError("fabricated provider unavailable")

            with pytest.raises(TimeoutError):
                activate(op, archive, pin, p, opening, unavailable)
            assert reader.execute(
                "SELECT count(*) FROM paper_portfolio"
            ).fetchone() == (0,)
            pid = activate(op, archive, pin, p, opening)
            assert activate(op, archive, pin, p, opening + FIVE) == pid
            state = evidence.verify_portfolio(reader, pid, archive)
            assert (
                state.state == "ACTIVE"
                and state.account.cash == 10000
                and state.account.ledger_seq == 1
            )
            assert state.account.portfolio.inception_at == opening
            assert (
                len(state.marks) == 1
                and next(iter(state.marks.values())).equity == 10000
            )
            assert owner.execute(
                "SELECT count(*) FROM pg_proc WHERE "
                "pronamespace='public'::regnamespace "
                "AND prosecdef"
            ).fetchone() == (1,)
            assert owner.execute(
                "SELECT bool_and(proconfig @> ARRAY['search_path=pg_catalog, "
                "public, pg_temp']) "
                "FROM pg_proc WHERE proname LIKE 'paper_%'"
            ).fetchone() == (True,)
            # Column UPDATE cannot authorise a state transition without a matching
            # trigger.
            with pytest.raises(psycopg.IntegrityError):
                worker.execute("UPDATE paper_portfolio SET state='PAUSED'")
            held = owner.transaction()
            with held:
                owner.execute("SELECT * FROM paper_portfolio FOR UPDATE")
                start = perf_counter()
                with pytest.raises(psycopg.errors.LockNotAvailable):
                    store.record_operational_event(
                        worker, pid, "PAUSE", "test", opening, "hold"
                    )
                waited = perf_counter() - start
                print("FABRICATED lock timeout seconds", round(waited, 3))
                assert waited >= 2.8
            assert recover(worker, pid).status == "ACTIVE"
            draft = portfolio("ETHUSDT", opening)
            draft_id = store.create_portfolio(
                op,
                draft,
                rec.configuration(draft.symbol, draft.model_recipe_sha256, COHORT),
                pin,
                opening,
            ).id
            with pytest.raises(
                psycopg.errors.InsufficientPrivilege, match="row-level security"
            ):
                store.fund_portfolio(worker, draft_id, opening)
            store.fund_portfolio(op, draft_id, opening)
            with pytest.raises(
                psycopg.errors.InsufficientPrivilege, match="row-level security"
            ):
                store.record_mark(
                    worker,
                    draft_id,
                    fx.INCEPTION,
                    opening,
                    inception=True,
                    quote=fx.quote(draft, fx.fixed_clock(opening)),
                )
            with pytest.raises(
                psycopg.errors.InsufficientPrivilege, match="row-level security"
            ):
                store.record_mark(
                    op,
                    pid,
                    fx.INCEPTION + STEP,
                    fx.INCEPTION + STEP + FIVE,
                    reason="missed",
                )


def plan(c, pid, root, clock):
    def read(p, opened, observed):
        return read_forecast(p, opened, root / "records", root / "operations", observed)

    view = recover(c, pid)
    reader = evidence.recovery_reader(root / "private", view.state, read)
    return cycle(
        lambda: recover(c, pid),
        reader,
        fx.filter_source,
        fx.quote,
        clock,
        lambda _: None,
    )


def decisions(c, pid, archive, proposal):
    observed = {o.forecast: o for o in proposal.observations}
    for d in proposal.decisions:
        evidence.record_archived_decision(c, pid, archive, d, observed.get(d.forecast))


def submit(c, pid, archive, proposal):
    return evidence.submit_archived_order(
        c, pid, archive, proposal.order, proposal.attempt, proposal.filter_source
    ).id


def complete(c, pid, archive, proposal, oid, clock):
    q = evidence.archive_quote(
        archive, fx.quote(proposal.order.balances.portfolio, clock)
    )
    at = clock.now()
    qid = store.record_quote(c, pid, oid, q, at).id
    store.commit_fill(
        c, pid, oid, qid, proposal.filters, run_id=clock.run_id, at=at, recorded_at=at
    )


def lifecycle(dsns, root, archive, pin):
    symbols = ("BTCUSDT", "ETHUSDT")
    opened = fx.OPEN
    with psycopg.connect(dsns["operator"], autocommit=True) as op:
        portfolios = {
            s: activate(op, archive, pin, portfolio(s), fx.INCEPTION) for s in symbols
        }
    assert len(set(portfolios.values())) == 2
    publish_slot(root, opened, dict.fromkeys(symbols, 0.001))
    journal = next((root / "operations").iterdir())
    final = journal.read_bytes()
    journal.unlink()
    with psycopg.connect(dsns["worker"], autocommit=True) as c:
        for pid in portfolios.values():
            proposal = plan(c, pid, root, fx.fixed_clock(fx.ISSUED))
            assert (
                proposal.reason == "awaiting_automation_evidence"
                and not proposal.decisions
            )
        running = json.loads(final)
        running.update(state="running", finished_at=None)
        journal.write_bytes(forward.canonical(running))
        for pid in portfolios.values():
            clock = fx.fixed_clock(fx.ISSUED)
            proposal = plan(c, pid, root, clock)
            assert proposal.result == "BUY_REQUIRED"
            # Collector can finish between discovery and retention. Archive precisely
            # the pinned bytes.
            journal.write_bytes(final)
            with pytest.raises(FileNotFoundError):
                decisions(c, pid, root / "unavailable", proposal)
            assert not recover(c, pid).state.decisions
            decisions(c, pid, archive, proposal)
            # Process died before submission. Its pinned journal remains authoritative.
            with psycopg.connect(dsns["worker"], autocommit=True) as restarted:
                clock = fx.fixed_clock(fx.ISSUED)
                replay = plan(restarted, pid, root, clock)
                assert replay.order.identity == proposal.order.identity
                oid = submit(restarted, pid, archive, replay)
                complete(restarted, pid, archive, replay, oid, clock)
                assert (
                    evidence.verify_portfolio(restarted, pid, archive).account.quantity
                    > 0
                )
        # Observed marks use a new quote, fetched for the scheduled slot.
        slot = fx.INCEPTION + STEP
        for pid in portfolios.values():
            p = recover(c, pid).state.account.portfolio
            q = evidence.archive_quote(archive, fx.quote(p, fx.fixed_clock(slot)))
            store.record_mark(c, pid, slot, slot, quote=q)
        publish_slot(root, opened + STEP, {"ETHUSDT": -0.001})
        eth = portfolios["ETHUSDT"]
        clock = fx.fixed_clock(fx.ISSUED + STEP)
        sell = plan(c, eth, root, clock)
        assert sell.result == "EXIT_REQUIRED"
        decisions(c, eth, archive, sell)
        submit(
            c, eth, archive, sell
        )  # Connection termination with a committed unfilled intent.
    with psycopg.connect(dsns["worker"], autocommit=True) as c:
        clock = fx.fixed_clock(fx.ISSUED + STEP + FIVE)
        interrupted = plan(c, eth, root, clock)
        assert interrupted.result == "EXPIRE_INTERRUPTED"
        pending = recover(c, eth).pending
        store.terminate_order(
            c,
            eth,
            rec.identity(eth, "order", pending.identity),
            status="EXPIRED",
            reason="restart",
            at=clock.now(),
        )
        retry = plan(c, eth, root, fx.fixed_clock(clock.now()))
        assert retry.result == "EXIT_RETRY_REQUIRED" and retry.attempt == 2
        submit(c, eth, archive, retry)
        store.terminate_order(
            c,
            eth,
            rec.identity(eth, "order", retry.order.identity),
            status="REJECTED",
            reason="fabricated_down",
            at=clock.now(),
        )
        clock = fx.fixed_clock(clock.now() + FIVE)
        sale = plan(c, eth, root, clock)
        complete(c, eth, archive, sale, submit(c, eth, archive, sale), clock)
        assert recover(c, eth).state.account.quantity == 0
        btc = portfolios["BTCUSDT"]
        for horizon in (1, 2):
            at = fx.INCEPTION + horizon * STEP + 2 * FIVE
            missed = plan(c, btc, root, fx.fixed_clock(at))
            assert missed.decisions[-1].action.value == (
                "SIGNAL_STALE" if horizon == 1 else "EXIT_REQUIRED"
            )
            decisions(c, btc, archive, missed)
        slot = fx.INCEPTION + 2 * STEP
        for pid in portfolios.values():
            store.record_mark(c, pid, slot, at, reason="worker_unavailable")
        # Preserve the unsatisfied BTC risk exit across the checkpoint.
        return {
            pid: evidence.verify_portfolio(c, pid, archive)
            for pid in portfolios.values()
        }


def database_tool(container, dsn, program, *flags, body=None, output=None):
    assert re.fullmatch(r"[0-9a-f]{64}", container)
    db = conninfo_to_dict(dsn)["dbname"]
    assert re.fullmatch(r"badger_test_[0-9a-f]{32}", db)
    command = [
        "docker",
        "--context",
        "default",
        "exec",
        "-i",
        container,
        program,
        *flags,
        "-U",
        conninfo_to_dict(dsn)["user"],
        "-d",
        db,
    ]
    result = subprocess.run(
        command,
        input=body,
        stdout=output or subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


@pytest.mark.parametrize("use_writer", [False, True], ids=["rehearsal", "writer"])
def test_separate_cluster_checkpoint(
    test_admin, tmp_path, candle_observation, use_writer
):
    target, target_dsn = restore_admin(test_admin)
    identity = uuid4().hex
    archive, pin = originals(tmp_path)
    with (
        closing(target),
        isolated_roles(*test_admin, identity) as (source, identifiers),
        isolated_roles(target, target_dsn, identity, source=False) as (restored, _),
    ):
        with psycopg.connect(source["collector"], autocommit=True) as collector:
            save_candle(collector, candle_observation)
        upgrade(source, identifiers)
        if use_writer:
            from .test_paper_writer import writer_lifecycle

            expected = writer_lifecycle(source, tmp_path, archive, pin)
        else:
            expected = lifecycle(source, tmp_path, archive, pin)
        cid = os.environ["BADGER_D2A_TEST_CONTAINER"]
        dest = os.environ["BADGER_TEST_RESTORE_CONTAINER"]
        assert cid != dest
        role_names = [conninfo_to_dict(d)["user"] for d in source.values()]

        def schema(container, dsn, snap):
            return database_tool(
                container, dsn, "pg_dump", "--schema-only", "--snapshot=" + snap
            )

        checkpoint = tmp_path / "checkpoint"
        with psycopg.connect(source["owner"], autocommit=True) as db:

            def interrupt(_, stream):
                stream.write(b"PGDMP")
                raise InterruptedError()

            with pytest.raises(InterruptedError):
                backup.capture(
                    db,
                    archive,
                    tmp_path / "partial",
                    interrupt,
                    lambda snap: schema(cid, source["owner"], snap),
                    role_names,
                )
            assert not (tmp_path / "partial/manifest.json").exists()
            pin = backup.capture(
                db,
                archive,
                checkpoint,
                lambda snap, stream: database_tool(
                    cid,
                    source["owner"],
                    "pg_dump",
                    "-Fc",
                    "--snapshot=" + snap,
                    output=stream,
                ),
                lambda snap: schema(cid, source["owner"], snap),
                role_names,
            )
        data = backup.verify_bundle(checkpoint, pin)
        dump = checkpoint / "database.dump"
        body = dump.read_bytes()
        dump.write_bytes(body[:-1])
        with pytest.raises(ValueError, match="Damaged dump"):
            backup.verify_bundle(checkpoint, pin)
        dump.write_bytes(body)
        # Replay ACL and object ownership in a fresh cluster with distinct role
        # passwords.
        restore_as_admin = make_conninfo(
            target_dsn, dbname=conninfo_to_dict(restored["owner"])["dbname"]
        )
        database_tool(
            dest,
            restore_as_admin,
            "pg_restore",
            "--exit-on-error",
            "--single-transaction",
            body=body,
        )
        with psycopg.connect(restored["owner"], autocommit=True) as db:
            assert (
                backup.verify_restored(
                    db,
                    checkpoint,
                    pin,
                    lambda snap: schema(dest, restored["owner"], snap),
                    role_names,
                )
                == expected
            )
        with psycopg.connect(restored["worker"], autocommit=True) as c:
            check_security(c, identifiers)
            pid, pin_forecast = c.execute(
                "SELECT portfolio_id,forecast_file_sha256 FROM paper_decision "
                "WHERE kind='FORECAST' LIMIT 1"
            ).fetchone()
            missing = checkpoint / "originals" / (pin_forecast + ".json")
            raw = missing.read_bytes()
            missing.unlink()
            with pytest.raises(ValueError, match="source object"):
                backup.verify_bundle(checkpoint, pin)
            with pytest.raises(IntegrityIssue):
                evidence.verify_portfolio(c, pid, checkpoint / "originals")
            evidence.retain(checkpoint / "originals", raw)
            assert backup.verify_bundle(checkpoint, pin) == data
            filter_pin = c.execute(
                "SELECT filter_raw_sha256 FROM paper_market_event WHERE "
                "portfolio_id=%s AND event_type='FILL' LIMIT 1",
                (pid,),
            ).fetchone()[0]
            artifact = checkpoint / "originals" / (filter_pin + ".json")
            body = artifact.read_bytes()
            artifact.chmod(0o600)
            artifact.write_bytes(body.replace(b"LOT_SIZE", b"NOT_SIZE", 1))
            with pytest.raises(IntegrityIssue):
                evidence.verify_portfolio(c, pid, checkpoint / "originals")
            artifact.write_bytes(body)
            artifact.chmod(0o400)
            assert (
                evidence.verify_portfolio(c, pid, checkpoint / "originals")
                == expected[pid]
            )
        print("FABRICATED restored tables", {k: v[0] for k, v in data["rows"].items()})
        for pid, snap in sorted(expected.items()):
            print(
                "FABRICATED",
                pid,
                snap.account.cash,
                snap.account.quantity,
                snap.account.realised,
                snap.account.ledger_seq,
                snap.exit_decision_id,
                len(snap.marks),
            )


def test_archive_before_commit_and_conflicting_publisher(
    test_admin, tmp_path, monkeypatch
):
    archive, pin = originals(tmp_path)
    p = portfolio("BTCUSDT")
    with isolated_roles(*test_admin, uuid4().hex) as (dsns, roles):
        upgrade(dsns, roles)
        with psycopg.connect(dsns["operator"], autocommit=True) as op:
            pid = activate(op, archive, pin, p, fx.INCEPTION)
        publish_slot(tmp_path, fx.OPEN, {p.symbol: 0.001})
        with psycopg.connect(dsns["worker"], autocommit=True) as c:
            proposal = plan(c, pid, tmp_path, fx.fixed_clock(fx.ISSUED))
            (d,), (o,) = proposal.decisions, proposal.observations
            bad = replace(o, journal=dict(o.journal, filename="misnamed.json"))
            with pytest.raises(ValueError, match="archived originals"):
                evidence.record_archived_decision(c, pid, archive, d, bad)
            with monkeypatch.context() as patch:

                def crash(*args, **kwargs):
                    raise InterruptedError("fabricated pre-commit exit")

                patch.setattr(store, "record_decision", crash)
                with pytest.raises(InterruptedError):
                    decisions(c, pid, archive, proposal)
            assert not recover(c, pid).state.decisions
            assert (
                evidence.verify_forecast(
                    archive, d, o.artifact_relpath, o.prediction_id
                )
                == o
            )
            decisions(c, pid, archive, proposal)
            journal = next((tmp_path / "operations").iterdir())
            body = json.loads(journal.read_bytes())
            body["run_id"] = "3" * 32
            journal.unlink()
            renamed = journal.with_name(
                journal.name.split("-")[0] + "-" + body["run_id"] + ".json"
            )
            renamed.write_bytes(forward.canonical(body))
            conflict = plan(c, pid, tmp_path, fx.fixed_clock(fx.ISSUED))
            assert conflict.result == "INTEGRITY_PAUSE" and conflict.order is None
            assert recover(c, pid).state.account.ledger_seq == 1


def _hold_uncommitted(dsn, pid, ready):
    """Spawned worker is killed with an open order-independent transaction."""
    from backtest_badger.paper_operations import invocation

    with (
        psycopg.connect(dsn, autocommit=True) as conn,
        invocation(conn, pid) as acquired,
    ):
        assert acquired
        with conn.transaction():
            conn.execute(
                "SELECT * FROM paper_portfolio WHERE portfolio_id=%s FOR UPDATE", (pid,)
            )
            # A genuine insert inside an interrupted transaction, rolled back on
            # disconnect.
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO paper_market_event "
                    "(event_id,portfolio_id,event_type,event_at,recorded_at,"
                    "reason_code,mark_slot,valuation_policy_sha256) "
                    "SELECT %s,portfolio_id,'MARK_MISSING',%s,%s,'fabricated "
                    "outage',%s,valuation_policy_sha256 "
                    "FROM paper_portfolio WHERE portfolio_id=%s",
                    (
                        uuid4(),
                        fx.INCEPTION + STEP + FIVE,
                        fx.INCEPTION + STEP + FIVE,
                        fx.INCEPTION + STEP,
                        pid,
                    ),
                )
            ready.send(True)
            ready.recv()


def test_five_minute_cycles_process_death_and_fail_closed(test_admin, tmp_path):
    import multiprocessing

    from backtest_badger.paper_operations import ClockHealth, run_checked

    archive, pin = originals(tmp_path)
    with isolated_roles(*test_admin, uuid4().hex) as (dsns, roles):
        upgrade(dsns, roles)
        with psycopg.connect(dsns["operator"], autocommit=True) as op:
            pid = activate(op, archive, pin, portfolio("BTCUSDT"), fx.INCEPTION)
        with psycopg.connect(dsns["worker"], autocommit=True) as c:

            def run(at, synced=True):
                clock = fx.fixed_clock(at)
                health = ClockHealth(synced, at, timedelta(milliseconds=20))
                return run_checked(
                    c,
                    pid,
                    archive,
                    health,
                    clock,
                    lambda: plan(c, pid, tmp_path, clock),
                )

            for n in range(1, 7):
                proposal, incident = run(fx.INCEPTION + n * FIVE)
                assert not incident and proposal.order is None
            # Overlapping process cannot begin even a proposal during a writer's
            # invocation.
            ctx = multiprocessing.get_context("spawn")
            parent, child = ctx.Pipe()
            process = ctx.Process(
                target=_hold_uncommitted, args=(dsns["worker"], pid, child)
            )
            process.start()
            try:
                assert parent.poll(20) and parent.recv()
                assert run(fx.INCEPTION + STEP + FIVE)[1]["code"] == "cycle_overlap"
            finally:
                process.kill()
                process.join(10)
                parent.close()
                child.close()
            assert process.exitcode is not None and process.exitcode < 0
            # Backend cleanup can follow process death across Docker NAT.
            deadline = perf_counter() + 10
            while True:
                _, incident = run(fx.INCEPTION + STEP + 2 * FIVE)
                if incident is None:
                    break
                assert incident["code"] == "cycle_overlap" and perf_counter() < deadline
                sleep(0.05)
            assert c.execute("SELECT count(*) FROM paper_market_event").fetchone() == (
                1,
            )
            assert run(fx.INCEPTION, synced=False)[1]["code"] == "clock_uncertain"
            (archive / (pin + ".json")).unlink()
            incidents = [run(fx.INCEPTION + n * FIVE)[1] for n in range(1, 4)]
            assert {i["code"] for i in incidents} == {"original_missing"}
            assert len({i["key"] for i in incidents}) == 1
            assert c.execute("SELECT count(*) FROM paper_decision").fetchone() == (0,)

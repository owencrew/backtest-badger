"""Fabricated v1 evidence only, on newly created PostgreSQL databases."""

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import Barrier
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from backtest_badger import paper_persistence as store
from backtest_badger import paper_records as rec
from backtest_badger.paper_accounting import Account, Mark, fund_account
from backtest_badger.paper_execution import Order
from backtest_badger.paper_reconciliation import (
    IntegrityIssue,
    asof_account,
    reconcile_portfolio,
)
from backtest_badger.paper_strategy import observe_forecast, start_strategy
from backtest_badger.paper_types import (
    STEP,
    VALUATION_POLICY,
    Action,
    D,
    Filters,
    Forecast,
    Portfolio,
    Quote,
)

from .conftest import migrate

pytestmark = pytest.mark.integration
T = datetime(2026, 1, 2, 0, 10, tzinfo=UTC)
SEC = timedelta(seconds=1)
HASH = rec.fingerprint("fabricated evidence")
COHORT = "fabricated-stage-4c"
RUN = "fabricated-worker-1"


def portfolio(symbol="BTCUSDT", key="fabricated-btc"):
    return Portfolio(
        key,
        symbol,
        T,
        rec.fingerprint(rec.canonical(rec.configuration(symbol, HASH, COHORT))),
        HASH,
        HASH,
    )


def quote(at, key, *, run=RUN, bid="100", symbol="BTCUSDT"):
    body = json.dumps(
        dict(symbol=symbol, bidPrice=bid, askPrice=bid, bidQty="1000", askQty="1000")
    ).encode()
    return Quote(
        key,
        run,
        symbol,
        at,
        at,
        D(bid),
        D(bid),
        D(1000),
        D(1000),
        sha256(body).hexdigest(),
        body,
        "https://fabricated.invalid/bookTicker",
        elapsed_seconds=D("0.0001"),
    )


def rules(at):
    return Filters("BTCUSDT", at, HASH, D("0.01"), D("0.01"), D(1000), D(1), None)


def draft(c, p):
    return store.create_portfolio(
        c, p, rec.configuration(p.symbol, HASH, COHORT), HASH, T - SEC
    ).id


def activate(c, p):
    pid = draft(c, p)
    store.fund_portfolio(c, pid, T)
    q = quote(T, "inception", symbol=p.symbol)
    mark = store.record_mark(c, pid, T, T, quote=q, inception=True)
    account = fund_account(Account(p), T)
    state = start_strategy(
        account,
        Mark(p, str(mark.id), T, 1, q, rec.fingerprint(VALUATION_POLICY), slot=T),
    )
    return pid, state


def signal(state, at, value):
    source = state.next_source_open
    f = Forecast(
        state.account.portfolio,
        "fabricated-" + source.isoformat(),
        source,
        at,
        at,
        D(value),
        HASH,
        HASH,
        HASH,
        HASH,
    )
    return observe_forecast(state, f, "decision-" + f.record_id, at)


def save_decision(c, pid, d):
    return store.record_decision(
        c,
        pid,
        d,
        artifact_relpath="fabricated/original.json",
        prediction_id="fabricated-ridge",
    )


def attempt(c, pid, d, at, *, key="buy", n=1, run=RUN):
    balances = reconcile_portfolio(c, pid).account.balances
    o = Order(key, d, balances, run, at, at + 30 * SEC)
    return o, store.submit_order(c, pid, o, n).id


def prepared_buy(c):
    p = portfolio()
    pid, state = activate(c, p)
    at = T + SEC
    state, d = signal(state, at, "0.1")
    did = save_decision(c, pid, d).id
    o, oid = attempt(c, pid, d, at)
    q = quote(at + SEC, "fabricated-quote-buy")
    qid = store.record_quote(c, pid, oid, q, q.response_received_at).id
    return pid, state, did, o, oid, qid


def fill(c, pid, o, oid, qid, *, run=RUN):
    return store.commit_fill(
        c,
        pid,
        oid,
        qid,
        rules(o.submitted_at),
        run_id=run,
        at=o.submitted_at + SEC,
        recorded_at=o.submitted_at + SEC,
    )


def prepared_sell(c):
    pid, state, _, o, oid, qid = prepared_buy(c)
    fill(c, pid, o, oid, qid)
    account = reconcile_portfolio(c, pid).account
    state = replace(state, account=account, last_at=account.at)
    at = T + STEP + SEC
    state, d = signal(state, at, "-0.1")
    did = save_decision(c, pid, d).id
    o, oid = attempt(c, pid, d, at, key="sell")
    q = quote(at + SEC, "fabricated-quote-sell", bid="110")
    qid = store.record_quote(c, pid, oid, q, q.response_received_at).id
    return pid, state, did, o, oid, qid


def financial(c, pid):
    return tuple(
        c.execute(query, (pid,)).fetchall()
        for query in (
            "SELECT ledger_highwater,state FROM paper_portfolio WHERE portfolio_id=%s",
            "SELECT * FROM paper_ledger_entry WHERE portfolio_id=%s ORDER BY "
            "ledger_seq",
            "SELECT * FROM paper_market_event WHERE portfolio_id=%s ORDER BY event_id",
            "SELECT * FROM paper_order WHERE portfolio_id=%s ORDER BY order_id",
            "SELECT asset,sum(delta_units) FROM paper_ledger_entry WHERE "
            "portfolio_id=%s GROUP BY asset ORDER BY asset",
        )
    )


def test_replay_marks_exit_and_idempotency(connection):
    c = connection
    pid, state, did, o, oid, qid = prepared_sell(c)
    before = reconcile_portfolio(c, pid)
    assert before.account.ledger_seq == 3 and before.exit_decision_id == did
    slot = T + STEP
    q = quote(o.submitted_at + SEC, "middle-mark", bid="110")
    mark = store.record_mark(c, pid, slot, q.response_received_at, quote=q)
    result = fill(c, pid, o, oid, qid)
    snap = reconcile_portfolio(c, pid)
    assert result.created and not fill(c, pid, o, oid, qid).created
    assert (
        snap.account.quantity == snap.account.basis == 0 and snap.account.realised > 0
    )
    assert (
        snap.account.cash == 10000 + snap.account.realised
        and snap.account.ledger_seq == 5
    )
    assert snap.pending_order is snap.exit_decision_id is None
    assert (
        snap.marks[mark.id].equity
        == before.account.cash + before.account.quantity * 110
    )
    assert asof_account(c, pid, 3) == before.account
    assert not store.record_mark(c, pid, slot, q.response_received_at, quote=q).created
    assert not store.fund_portfolio(c, pid, T).created
    assert not store.submit_order(c, pid, o, 1).created
    assert not save_decision(c, pid, o.decision).created
    with pytest.raises(store.EvidenceConflict):
        save_decision(c, pid, replace(o.decision, reason="different"))
    with pytest.raises(store.EvidenceConflict):
        store.commit_fill(
            c,
            pid,
            oid,
            qid,
            replace(rules(o.submitted_at), payload_sha256="1" * 64),
            run_id=RUN,
            at=o.submitted_at + SEC,
            recorded_at=o.submitted_at + SEC,
        )
    gap = T + 2 * STEP
    store.record_mark(c, pid, gap, gap + 300 * SEC, reason="fabricated downtime")
    with pytest.raises((ValueError, psycopg.Error)):
        store.record_mark(c, pid, gap, gap, quote=quote(gap, "late"))
    assert list(reconcile_portfolio(c, pid).marks.values()).count(None) == 1


@pytest.mark.parametrize(
    "timing,table,event,condition,deferred",
    [
        ("BEFORE", "market_event", "INSERT", "NEW.event_type='FILL'", False),
        ("AFTER", "market_event", "INSERT", "NEW.event_type='FILL'", False),
        ("AFTER", "ledger_entry", "INSERT", "NEW.asset='USDT'", False),
        ("AFTER", "ledger_entry", "INSERT", "NEW.asset='BTC'", False),
        (
            "BEFORE",
            "portfolio",
            "UPDATE",
            "NEW.ledger_highwater>OLD.ledger_highwater",
            False,
        ),
        ("BEFORE", "order", "UPDATE", "NEW.status='FILLED'", False),
        ("BEFORE", "market_event", "INSERT", "NEW.event_type='EXIT_SATISFIED'", False),
        ("AFTER", "market_event", "INSERT", "NEW.event_type='EXIT_SATISFIED'", True),
    ],
)
def test_atomic_rollback(connection, timing, table, event, condition, deferred):
    c = connection
    pid, _, did, o, oid, qid = prepared_sell(c)
    original = financial(c, pid)
    c.execute("""CREATE FUNCTION fabricated_fault() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'fabricated fault'; END $$""")
    kind = "CONSTRAINT" if deferred else ""
    mode = "DEFERRABLE INITIALLY DEFERRED" if deferred else ""
    c.execute(
        f"CREATE {kind} TRIGGER injected {timing} {event} ON paper_{table} {mode} "
        f"FOR EACH ROW WHEN ({condition}) "
        "EXECUTE FUNCTION fabricated_fault()"
    )
    with pytest.raises(psycopg.Error, match="fabricated fault"):
        fill(c, pid, o, oid, qid)
    assert financial(c, pid) == original
    assert reconcile_portfolio(c, pid).exit_decision_id == did
    c.execute(f"DROP TRIGGER injected ON paper_{table}")
    assert fill(c, pid, o, oid, qid).created


def test_crash_recovery_and_sticky_exit(connection, database):
    c = connection
    pid, state, did, o, oid, qid = prepared_sell(c)
    with psycopg.connect(database, autocommit=True) as worker:
        snap = reconcile_portfolio(worker, pid)
        assert snap.pending_order["expires_at"] == o.expires_at
        with pytest.raises(ValueError, match="INVALID_QUOTE"):
            fill(worker, pid, o, oid, qid, run="restarted")
        store.terminate_order(
            worker, pid, oid, status="EXPIRED", reason="restart", at=o.expires_at
        )
        later = o.submitted_at + STEP
        state, ignored = signal(replace(state, account=snap.account), later, "1")
        assert ignored.action == Action.IGNORED_EXIT_PENDING
        save_decision(worker, pid, ignored)
        second, sid = attempt(
            worker, pid, o.decision, later, key="retry", n=2, run="restarted"
        )
        store.record_quote_failure(
            worker,
            pid,
            sid,
            key="failure",
            run_id="restarted",
            source_url="https://fabricated.invalid/bookTicker",
            request_started_at=later,
            discovered_at=later + SEC,
            reason="timeout",
        )
        store.terminate_order(
            worker, pid, sid, status="REJECTED", reason="timeout", at=later + SEC
        )
        later += 300 * SEC
        assert reconcile_portfolio(worker, pid).exit_decision_id == did
        assert reconcile_portfolio(worker, pid).account == snap.account
        later += 300 * SEC
        third, tid = attempt(worker, pid, o.decision, later, key="fresh-attempt", n=3)
        fresh = quote(later + SEC, "new-sell")
        fid = store.record_quote(worker, pid, tid, fresh, later + SEC).id
        assert fill(worker, pid, third, tid, fid).created
        assert reconcile_portfolio(c, pid).exit_decision_id is None


def race(dsn, *operations):
    barrier = Barrier(len(operations))

    def work(operation):
        with psycopg.connect(dsn, autocommit=True, connect_timeout=3) as conn:
            barrier.wait(timeout=5)
            try:
                return operation(conn)
            except (ValueError, psycopg.Error) as exc:
                return exc

    with ThreadPoolExecutor(len(operations)) as pool:
        return list(pool.map(work, operations))


@pytest.mark.parametrize("prepare", [prepared_buy, prepared_sell])
def test_racing_same_order_cash_and_holdings(connection, database, prepare):
    pid, _, _, o, oid, qid = prepare(connection)

    def op(c):
        return fill(c, pid, o, oid, qid)

    results = race(database, op, op)
    assert sorted(r.created for r in results) == [False, True]
    assert connection.execute(
        "SELECT count(*) FROM paper_ledger_entry WHERE fill_event_id=%s",
        (results[0].id,),
    ).fetchone() == (2,)
    assert (
        reconcile_portfolio(connection, pid).account.ledger_seq
        == o.balances.ledger_seq + 2
    )


def test_competing_submissions_and_funding(connection, database):
    c = connection
    p = portfolio()
    pid = draft(c, p)

    def fund(c):
        return store.fund_portfolio(c, pid, T)

    assert sorted(r.created for r in race(database, fund, fund)) == [False, True]
    assert reconcile_portfolio(c, pid).state == "DRAFT"
    _, state = activate(c, p)
    state, d = signal(state, T + SEC, "1")
    save_decision(c, pid, d)
    o = Order("first", d, state.account.balances, RUN, d.at, d.at + 30 * SEC)
    results = race(
        database,
        lambda c: store.submit_order(c, pid, o, 1),
        lambda c: store.submit_order(c, pid, replace(o, identity="second"), 1),
    )
    assert sum(isinstance(r, store.Receipt) for r in results) == 1
    assert reconcile_portfolio(c, pid).pending_order["status"] == "SUBMITTED"


def test_mark_racing_sale(connection, database):
    pid, _, _, o, oid, qid = prepared_sell(connection)
    at = o.submitted_at + SEC
    q = quote(at, "race-mark", bid="110")
    mark, result = race(
        database,
        lambda c: store.record_mark(c, pid, T + STEP, at, quote=q),
        lambda c: fill(c, pid, o, oid, qid),
    )
    assert mark.created and result.created
    snap = reconcile_portfolio(connection, pid)
    point = snap.marks[mark.id]
    assert point.mark.asof_ledger_seq in (3, 5)
    acc = snap.prefixes[point.mark.asof_ledger_seq]
    assert point.equity == acc.cash + acc.quantity * 110


def test_raw_sql_immutability_and_foreign_keys(connection):
    c = connection
    pid, _, did, o, oid, qid = prepared_buy(c)
    other = draft(c, portfolio("ETHUSDT", "fabricated-eth"))
    for table in ("decision", "market_event", "ledger_entry"):
        for statement in (
            f"UPDATE paper_{table} SET portfolio_id=portfolio_id",
            f"DELETE FROM paper_{table}",
            f"TRUNCATE paper_{table} CASCADE",
        ):
            with pytest.raises(psycopg.Error):
                c.execute(statement)
    for statement in (
        "UPDATE paper_portfolio SET state='ACTIVE'",
        "UPDATE paper_portfolio SET ledger_highwater=999",
        "UPDATE paper_portfolio SET initial_cash=12",
        "UPDATE paper_order SET status='FILLED'",
        "UPDATE paper_order SET status='EXPIRED'",
        "UPDATE paper_order SET status='REJECTED'",
        "UPDATE paper_order SET intent='SELL_ALL_BASE'",
        "UPDATE paper_portfolio SET protocol_sha256=repeat('f',64)",
        "UPDATE market SET symbol='WRONG' WHERE symbol='BTCUSDT'",
    ):
        with pytest.raises(psycopg.Error):
            c.execute(statement)
    for column, value in (
        ("portfolio_id", other),
        ("decision_id", uuid4()),
        ("order_id", uuid4()),
    ):
        with pytest.raises(psycopg.Error):
            c.execute(
                sql.SQL(
                    "INSERT INTO paper_market_event SELECT (jsonb_populate_record("
                    "NULL::paper_market_event,to_jsonb(e)||"
                    "jsonb_build_object('event_id',%s::uuid,"
                    "{},%s::uuid,'quote_key','fabricated-other'))).* FROM "
                    "paper_market_event e "
                    "WHERE event_id=%s"
                ).format(sql.Literal(column)),
                (uuid4(), value, qid),
            )
    for amount in ("NaN", "Infinity", "-Infinity", "-1", "10000.0001"):
        with pytest.raises(psycopg.Error):
            c.execute(
                "INSERT INTO paper_ledger_entry VALUES "
                "(%s,%s,1,'INITIAL_FUNDING',NULL,'USDT',%s,%s)",
                (uuid4(), other, amount, T),
            )
    assert c.execute(
        "SELECT count(*) FROM paper_ledger_entry WHERE portfolio_id=%s", (other,)
    ).fetchone() == (0,)
    assert reconcile_portfolio(c, pid).pending_order["order_id"] == oid


def test_guarded_migration_and_failed_upgrade(empty_database, candle_observation):
    from sqlalchemy.exc import DBAPIError

    from backtest_badger.candles import save_candle

    with psycopg.connect(empty_database, autocommit=True) as c:
        migrate(empty_database, "0001")
        save_candle(c, candle_observation)
        candle = c.execute("SELECT * FROM candle").fetchone()
        markets = c.execute("SELECT * FROM market ORDER BY market_id").fetchall()
        c.execute("CREATE TABLE paper_order (unrelated int)")
        with pytest.raises(DBAPIError):
            migrate(empty_database)
        assert c.execute(
            "SELECT to_regclass('paper_portfolio'),version_num FROM alembic_version"
        ).fetchone() == (None, "0001")
        c.execute("DROP TABLE paper_order")
        migrate(empty_database)
        migrate(empty_database, "0001", downgrade=True)
        migrate(empty_database)
        draft(c, portfolio())
        with pytest.raises(DBAPIError, match="Downgrade refused"):
            migrate(empty_database, "0001", downgrade=True)
        assert (
            c.execute("SELECT * FROM market ORDER BY market_id").fetchall() == markets
        )
        assert c.execute("SELECT * FROM candle").fetchone() == candle
        assert c.execute(
            "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND "
            "tablename LIKE 'paper_%'"
        ).fetchone() == (5,)


def test_snapshot_restore_all_paper_evidence(connection, database, test_admin):
    container = os.environ.get("BADGER_D2A_TEST_CONTAINER")
    if not container:
        pytest.skip("Set BADGER_D2A_TEST_CONTAINER to the disposable PG17 container.")
    c = connection
    pid, _, _, o, oid, qid = prepared_sell(c)
    fill(c, pid, o, oid, qid)
    slot = T + 2 * STEP
    store.record_mark(c, pid, slot, slot, quote=quote(slot, "after-sale"))
    store.record_mark(
        c, pid, slot + STEP, slot + STEP + 300 * SEC, reason="fabricated outage"
    )
    original = reconcile_portfolio(c, pid)
    admin, admin_dsn = test_admin
    params = conninfo_to_dict(database)
    assert params["dbname"].startswith("badger_test_")
    target = "badger_test_" + uuid4().hex
    admin.execute(
        sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(target))
    )
    docker = ["docker", "exec", "-i", container]
    try:
        dump = subprocess.run(
            [*docker, "pg_dump", "-Fc", "-U", params["user"], "-d", params["dbname"]],
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout
        subprocess.run(
            [
                *docker,
                "pg_restore",
                "--exit-on-error",
                "--single-transaction",
                "--no-owner",
                "--no-acl",
                "-U",
                params["user"],
                "-d",
                target,
            ],
            input=dump,
            capture_output=True,
            check=True,
            timeout=30,
        )
        with psycopg.connect(
            make_conninfo(admin_dsn, dbname=target), autocommit=True
        ) as restored:
            assert reconcile_portfolio(restored, pid) == original
            for table in (
                "portfolio",
                "decision",
                "order",
                "market_event",
                "ledger_entry",
            ):
                query = sql.SQL("SELECT * FROM {} ORDER BY 1").format(
                    sql.Identifier("paper_" + table)
                )
                assert restored.execute(query).fetchall() == c.execute(query).fetchall()
            for query in (
                "SELECT conname,pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid::regclass::text LIKE 'paper_%' ORDER BY 1,2",
                "SELECT tgname,pg_get_triggerdef(oid) FROM pg_trigger "
                "WHERE NOT tgisinternal AND tgrelid::regclass::text LIKE "
                "'paper_%' ORDER BY 1,2",
            ):
                assert restored.execute(query).fetchall() == c.execute(query).fetchall()
            with pytest.raises(psycopg.IntegrityError):
                restored.execute("UPDATE paper_ledger_entry SET delta_units=1")
    finally:
        admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(target)))


def test_independent_audit_detects_corrupt_restored_posting(connection):
    c = connection
    pid, _, _, o, oid, qid = prepared_buy(c)
    fill(c, pid, o, oid, qid)
    # Owner-only corruption drill in a throwaway database. The reader must
    # detect incorrect postings even when constraints were bypassed on import.
    c.execute("ALTER TABLE paper_ledger_entry DISABLE TRIGGER paper_guard")
    c.execute("UPDATE paper_ledger_entry SET delta_units=2 WHERE ledger_seq=3")
    c.execute("ALTER TABLE paper_ledger_entry ENABLE TRIGGER paper_guard")
    with pytest.raises(IntegrityIssue) as incident:
        reconcile_portfolio(c, pid)
    assert incident.value.code == "posting"


def test_worked_wac_example_through_postgres_numeric(connection):
    from backtest_badger.paper_accounting import (
        apply_trade,
        calculate_trade,
        value_account,
    )
    from backtest_badger.paper_types import Side

    # Stage 4A section 7 uses a partial sale for the accounting example.
    # Keep its illustrative quantities outside the v1 all-or-nothing order book.
    c = connection
    c.execute(
        "CREATE TEMP TABLE fabricated_example "
        "(seq int, side text, qty numeric, quote numeric, cash_delta numeric, "
        "base_delta numeric)"
    )
    c.execute("""INSERT INTO fabricated_example VALUES
        (1,'BUY',10,100,-1001.2002,10),(3,'SELL',4,110,439.472088,-4)""")
    p = portfolio()
    account = fund_account(Account(p), T)
    for seq, side, qty, price, cash, base, fee in c.execute("""
        SELECT seq,side,qty,price,cash_delta,base_delta,paper_fee(qty*price)
        FROM (SELECT *,quote*CASE side WHEN 'BUY' THEN 1.0002 ELSE 0.9998 END AS price
              FROM fabricated_example) f ORDER BY seq"""):
        trade = calculate_trade(
            p, str(seq), Side(side), T, qty, price, ledger_seq_before=seq
        )
        assert trade.fee == fee and tuple(m.amount for m in trade.postings) == (
            cash,
            base,
        )
        account = apply_trade(account, trade)
        if side == "BUY":
            assert (account.cash, account.basis) == (D("8998.7998"), D("1001.2002"))
    point = value_account(
        account, Mark(p, "fabricated-mark", T, 5, quote(T, "example", bid="110"), HASH)
    )
    assert (account.quantity, account.basis, account.realised, account.cash) == (
        6,
        D("600.72012"),
        D("38.992008"),
        D("9438.271888"),
    )
    assert (point.equity, point.unrealised) == (D("10098.271888"), D("59.27988"))


def test_state_projection_and_safety_decision(connection):
    from backtest_badger.paper_strategy import miss_horizon

    c = connection
    pid, state, _, o, oid, qid = prepared_buy(c)
    fill(c, pid, o, oid, qid)
    acc = reconcile_portfolio(c, pid).account
    state = replace(state, account=acc, last_at=acc.at)
    for i in (1, 2):
        source = state.next_source_open
        at = source + STEP + timedelta(minutes=17)
        state, d = miss_horizon(state, source, "fabricated-missed-" + str(i), at)
        store.record_decision(c, pid, d)
    snap = reconcile_portfolio(c, pid)
    assert snap.missed_streak == 2 and snap.exit_decision_id
    store.record_operational_event(c, pid, "PAUSE", "incident", at, "fabricated review")
    assert reconcile_portfolio(c, pid).state == "PAUSED"
    with pytest.raises(psycopg.Error):
        store.record_operational_event(c, pid, "RECOVERY_NOTE", "close", at, "CLOSE")
    store.record_operational_event(
        c, pid, "RESUME", "reviewed", at, "fabricated review"
    )
    assert reconcile_portfolio(c, pid).state == "ACTIVE"


@pytest.mark.parametrize(
    "fault",
    [
        "valid_control",
        "missing_pair",
        "missing_base",
        "wrong_cash",
        "wrong_sign",
        "wrong_quantity",
        "wrong_asset",
        "wrong_sequence",
        "wrong_fee",
        "wrong_price",
        "negative_balance",
        "orphan_fill",
        "wrong_highwater",
        "cross_portfolio_posting",
        "cross_portfolio_quote",
        "non_fill_posting",
        "orphan_terminal",
    ],
)
def test_database_rejects_malformed_financial_commits(connection, fault):
    from psycopg.types.json import Jsonb

    from backtest_badger.paper_execution import simulate_order

    c = connection
    pid, _, did, o, oid, qid = prepared_buy(c)
    other = draft(c, portfolio("ETHUSDT", "fabricated-eth"))
    original = financial(c, pid)
    at = o.submitted_at + SEC
    f = rules(o.submitted_at)
    trade = simulate_order(
        o, quote(at, "fabricated-quote-buy"), f, at, run_id=RUN
    ).fill.trade
    fid = uuid4()
    outcome = (
        nullcontext() if fault == "valid_control" else pytest.raises(psycopg.Error)
    )
    with outcome, c.transaction():
        if fault == "orphan_terminal":
            c.execute(
                """INSERT INTO paper_market_event
                (event_id,portfolio_id,event_type,order_id,decision_id,
                 event_at,recorded_at,reason_code)
                VALUES (%s,%s,'ORDER_REJECTED',%s,%s,%s,%s,'fabricated rejection')""",
                (fid, pid, oid, did, at, at),
            )
        else:
            c.execute(
                """INSERT INTO paper_market_event
                (event_id,portfolio_id,event_type,order_id,decision_id,quote_event_id,event_at,recorded_at,
                run_id,simulated_qty,simulated_price,gross_notional,fee_usdt,ledger_seq_before,ledger_seq_after,
                filter_rules_json,filter_raw_sha256,filter_observed_at,policy_sha256)
                SELECT %s,%s,'FILL',order_id,decision_id,%s,%s,%s,run_id,%s,%s,%s,%s,
                snapshot_seq,snapshot_seq+2,%s,%s,%s,policy_sha256 FROM paper_order
                WHERE order_id=%s""",
                (
                    fid,
                    other if fault == "cross_portfolio_quote" else pid,
                    qid,
                    at,
                    at,
                    trade.quantity + 1
                    if fault == "negative_balance"
                    else trade.quantity,
                    trade.price + 1 if fault == "wrong_price" else trade.price,
                    trade.notional,
                    trade.fee + 1 if fault == "wrong_fee" else trade.fee,
                    Jsonb(rec.filter_fields(f)["filter_rules_json"]),
                    HASH,
                    f.observed_at,
                    oid,
                ),
            )
            for seq, m in enumerate(trade.postings, 2):
                if fault == "missing_pair" or (fault == "missing_base" and seq == 3):
                    continue
                amount = m.amount
                if (
                    fault == "wrong_cash"
                    and seq == 2
                    or fault == "wrong_quantity"
                    and seq == 3
                ):
                    amount += 1
                if fault == "wrong_sign":
                    amount = -amount
                c.execute(
                    """INSERT INTO paper_ledger_entry VALUES
                    (%s,%s,%s,'FILL',%s,%s,%s,%s)""",
                    (
                        uuid4(),
                        other if fault == "cross_portfolio_posting" else pid,
                        seq + 1 if fault == "wrong_sequence" else seq,
                        qid if fault == "non_fill_posting" else fid,
                        "ETH" if fault == "wrong_asset" else m.asset,
                        amount,
                        at,
                    ),
                )
            if fault != "wrong_highwater":
                c.execute(
                    "UPDATE paper_portfolio SET ledger_highwater=(SELECT "
                    "coalesce(max(ledger_seq),0) "
                    "FROM paper_ledger_entry WHERE portfolio_id=%s) WHERE "
                    "portfolio_id=%s",
                    (pid, pid),
                )
            if fault != "orphan_fill":
                c.execute(
                    "UPDATE paper_order SET status='FILLED' WHERE order_id=%s", (oid,)
                )
    if fault == "valid_control":
        assert reconcile_portfolio(c, pid).account.ledger_seq == 3
    else:
        assert financial(c, pid) == original


def test_original_quote_and_order_survive_restarts(connection, database):
    pid, state, _, o, oid, qid = prepared_buy(connection)
    with psycopg.connect(database, autocommit=True) as restarted:
        snap = reconcile_portfolio(restarted, pid)
        assert snap.pending_quotes[0]["event_id"] == qid
        assert (
            snap.pending_quotes[0]["raw_body"]
            == quote(o.submitted_at + SEC, "fabricated-quote-buy").raw_body
        )
        assert snap.account.cash == 10000 and snap.account.quantity == 0
        with pytest.raises(ValueError, match="INVALID_QUOTE"):
            fill(restarted, pid, o, oid, qid, run="fabricated-new-process")
        store.terminate_order(
            restarted, pid, oid, status="EXPIRED", reason="restart", at=o.expires_at
        )
        with pytest.raises(psycopg.Error):
            store.submit_order(restarted, pid, replace(o, identity="retry-old-buy"), 2)
        assert reconcile_portfolio(restarted, pid).account == snap.account

    # Restart after intent alone has likewise incurred zero expense.
    state, d = signal(state, T + STEP + SEC, "1")
    save_decision(connection, pid, d)
    submitted, second = attempt(connection, pid, d, d.at, key="new-buy")
    with psycopg.connect(database, autocommit=True) as restarted:
        snap = reconcile_portfolio(restarted, pid)
        assert snap.pending_order["order_id"] == second and snap.pending_quotes == ()
        assert snap.pending_order["expires_at"] == submitted.expires_at
        assert snap.account.ledger_seq == 1


def test_paused_resume_close_and_config_conflict(connection):
    c = connection
    p = portfolio()
    pid, state = activate(c, p)
    with pytest.raises(store.EvidenceConflict):
        store.create_portfolio(
            c, p, rec.configuration(p.symbol, HASH, COHORT), "1" * 64, T - SEC
        )
    with pytest.raises(psycopg.Error):
        store.record_operational_event(c, pid, "RESUME", "invalid", T, "fabricated")
    store.record_operational_event(c, pid, "PAUSE", "paused", T, "fabricated")
    store.record_operational_event(c, pid, "RECOVERY_NOTE", "closed", T, "CLOSE")
    assert reconcile_portfolio(c, pid).state == "CLOSED"
    with pytest.raises(psycopg.Error):
        store.record_operational_event(c, pid, "RESUME", "invalid", T, "fabricated")


def test_independent_eth_and_btc_funding(connection):
    c = connection
    btc, _, _, o, oid, qid = prepared_buy(c)
    eth, _ = activate(c, portfolio("ETHUSDT", "fabricated-eth"))
    fill(c, btc, o, oid, qid)
    assert reconcile_portfolio(c, eth).account.cash == 10000
    assert reconcile_portfolio(c, eth).account.quantity == 0
    assert reconcile_portfolio(c, btc).account.quantity > 0
    with pytest.raises(psycopg.Error):
        c.execute(
            "INSERT INTO paper_ledger_entry VALUES "
            "(%s,%s,1,'INITIAL_FUNDING',NULL,'USDT',10000,%s)",
            (uuid4(), eth, T),
        )


def test_actual_posting_time_prevents_precommit_quote_mark(connection):
    c = connection
    pid, _, _, o, oid, qid = prepared_sell(c)
    at = o.submitted_at + SEC
    recorded = at + SEC
    store.commit_fill(
        c, pid, oid, qid, rules(o.submitted_at), run_id=RUN, at=at, recorded_at=recorded
    )
    assert reconcile_portfolio(c, pid).account.at == recorded
    assert c.execute(
        "SELECT DISTINCT posted_at FROM paper_ledger_entry WHERE ledger_seq>3"
    ).fetchall() == [(recorded,)]
    old_quote = quote(at, "pre-posting-mark", bid="110")
    with pytest.raises(psycopg.Error, match="Invalid mark snapshot"):
        store.record_mark(c, pid, T + STEP, recorded, quote=old_quote)
    mark = store.record_mark(
        c, pid, T + STEP, recorded, quote=quote(recorded, "after-posting", bid="110")
    )
    assert reconcile_portfolio(c, pid).marks[mark.id].mark.asof_ledger_seq == 5


def test_failed_attempt_cannot_satisfy_exit(connection):
    c = connection
    pid, _, did, o, oid, qid = prepared_sell(c)
    at = o.expires_at
    end = store.terminate_order(
        c, pid, oid, status="EXPIRED", reason="fabricated expiry", at=at
    )
    with pytest.raises(psycopg.IntegrityError):
        c.execute(
            """INSERT INTO paper_market_event
            (event_id,portfolio_id,order_id,decision_id,event_type,event_at,recorded_at,reference_event_id,reason_code)
            VALUES (%s,%s,%s,%s,'EXIT_SATISFIED',%s,%s,%s,'fabricated false flat')""",
            (uuid4(), pid, oid, did, at, at, end.id),
        )
    assert reconcile_portfolio(c, pid).exit_decision_id == did
    assert reconcile_portfolio(c, pid).account.quantity > 0


def test_database_rejects_cross_market_decisions_and_quotes(connection):
    c = connection
    btc, _, bdid, _, boid, bqid = prepared_buy(c)
    p = portfolio("ETHUSDT", "fabricated-eth")
    eth, state = activate(c, p)
    state, d = signal(state, T + SEC, "1")
    edid = save_decision(c, eth, d).id
    _, eoid = attempt(c, eth, d, d.at, key="eth-buy")
    q = quote(d.at + SEC, "fabricated-eth", symbol=p.symbol)
    eqid = store.record_quote(c, eth, eoid, q, q.response_received_at).id
    for oid, did in ((boid, edid), (eoid, bdid)):
        with pytest.raises(psycopg.Error):
            c.execute(
                """INSERT INTO paper_market_event
                (event_id,portfolio_id,order_id,decision_id,event_type,event_at,recorded_at,reason_code)
                VALUES (%s,%s,%s,%s,'ORDER_REJECTED',%s,%s,'fabricated cross-link')""",
                (
                    uuid4(),
                    btc,
                    oid,
                    did,
                    q.response_received_at,
                    q.response_received_at,
                ),
            )
    with pytest.raises(ValueError, match="original order quote"):
        store.commit_fill(
            c,
            btc,
            boid,
            eqid,
            rules(d.at),
            run_id=RUN,
            at=d.at + SEC,
            recorded_at=d.at + SEC,
        )
    assert reconcile_portfolio(c, btc).pending_quotes[0]["event_id"] == bqid
    assert reconcile_portfolio(c, eth).pending_quotes[0]["event_id"] == eqid


def test_blocked_dust_retains_filters_cash_and_obligation(connection):
    c = connection
    pid, _, did, o, oid, qid = prepared_sell(c)
    original = reconcile_portfolio(c, pid).account
    f = replace(rules(o.submitted_at), step=D(2))
    at = o.submitted_at + SEC
    terminal = store.reject_dust(c, pid, oid, qid, f, run_id=RUN, at=at)
    assert (
        terminal.created
        and not store.reject_dust(c, pid, oid, qid, f, run_id=RUN, at=at).created
    )
    snap = reconcile_portfolio(c, pid)
    assert (
        snap.state == "PAUSED"
        and snap.exit_decision_id == did
        and snap.account == original
    )
    assert c.execute(
        "SELECT quote_event_id,filter_rules_json->>'step' FROM paper_market_event "
        "WHERE event_type='EXIT_BLOCKED_DUST'"
    ).fetchone() == (qid, "2")
    with pytest.raises(psycopg.IntegrityError):
        store.record_operational_event(c, pid, "RESUME", "automatic-retry", at, "retry")


def test_decisions_cannot_predate_committed_financial_evidence(connection):
    c = connection
    pid, state, _, order, oid, qid = prepared_buy(c)
    at = order.submitted_at + SEC
    recorded = T + STEP + 2 * SEC
    store.commit_fill(
        c,
        pid,
        oid,
        qid,
        rules(order.submitted_at),
        run_id=RUN,
        at=at,
        recorded_at=recorded,
    )
    # Even a well-formed original forecast cannot claim it was acted upon
    # before the portfolio's latest durable observation.
    account = reconcile_portfolio(c, pid).account
    state = replace(state, account=replace(account, at=at), last_at=at)
    _, d = signal(state, recorded - SEC, "-0.1")
    with pytest.raises(psycopg.IntegrityError, match="decision state, time"):
        save_decision(c, pid, d)
    assert c.execute(
        "SELECT count(*) FROM paper_decision WHERE portfolio_id=%s", (pid,)
    ).fetchone() == (1,)

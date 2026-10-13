import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
from psycopg.pq import TransactionStatus

from backtest_badger import revalidation as rv
from backtest_badger.candles import (
    BatchConflict,
    ReviewConflict,
    get_candle_history,
    get_candles,
    save_candle,
    save_candles,
)
from backtest_badger.research import export_dataset, import_evidence
from backtest_badger.rest import EPOCH, MILLISECOND, STEP, Response

from .test_candles import wait_for_lock

pytestmark = pytest.mark.integration


@pytest.fixture
def review(monkeypatch, connection, tmp_path, candle_observation, historical_payload):
    @contextmanager
    def connect(_):
        yield connection

    monkeypatch.setattr(rv, "connect_database", connect)
    state = dict(observations=[candle_observation], mutate=None, requests=[])

    def fetch(url, *, retain, attempts):
        assert connection.info.transaction_status == TransactionStatus.IDLE
        state["requests"].append(url)
        now = datetime.now(UTC)
        if url.endswith("/time"):
            response = Response(
                json.dumps({"serverTime": (now - EPOCH) // MILLISECOND}).encode(),
                url,
                now,
                200,
                {},
            )
        else:
            response = historical_payload(state["observations"], mutate=state["mutate"])
            response = replace(response, url=url)
        retain(response)
        return response

    monkeypatch.setattr(rv, "fetch", fetch)

    def run(*, start=None, end=None):
        result = {}
        status = rv.review_history(
            "BTCUSDT",
            None,
            start=start or state["observations"][0].open_time,
            end=end or state["observations"][-1].open_time + STEP,
            artifacts=tmp_path,
            result=result,
        )
        return status, result

    return run, state


def apply(plan):
    result = {}
    status = rv.apply_revalidation(
        plan["plan_path"], None, approve_changes=True, result=result
    )
    return status, result


def current(connection, a):
    return get_candles(connection, a.market_id, 14400, a.open_time, a.open_time + STEP)[
        0
    ]


def test_review_read_only_and_identical_apply_preserves_version_policy(
    review, connection, candle_observation, monkeypatch
):
    a = candle_observation
    save_candle(connection, a)
    before = current(connection, a)
    # A server-enforced read-only connection still permits the complete review.
    connection.execute("SET default_transaction_read_only=on")
    run, state = review
    status, plan = run()
    connection.execute("SET default_transaction_read_only=off")
    assert status == 0 and plan["analysis"]["counts"]["identical"] == 1
    assert current(connection, a) == before
    source = plan["source"]["responses"][0]
    assert (
        hashlib.sha256(Path(source["raw_body"]).read_bytes()).hexdigest()
        == source["sha256"]
    )
    assert (
        plan["analysis"]["entries"][0]["proposed"]["observed_at"]
        == source["observed_at"]
    )
    monkeypatch.setattr(
        rv, "fetch", lambda *a, **k: pytest.fail("Apply must not fetch")
    )
    assert apply(plan)[0] == 0
    after = current(connection, a)
    assert after.pop("last_observed_at").isoformat() == source["observed_at"]
    before.pop("last_observed_at")
    assert after == before
    assert apply(plan)[1]["outcome"] == "rolled_back"  # Watermark changed since review.
    delayed_change = replace(
        a, close=Decimal("42600"), observed_at=a.observed_at + timedelta(seconds=1)
    )
    assert save_candle(connection, delayed_change) == "stale"
    assert len(get_candle_history(connection, 1, 14400, a.open_time)) == 1
    assert len(state["requests"]) == 2


def test_revisions_a_b_a_exports_and_original_provenance(
    review, connection, candle_observation, tmp_path
):
    a = candle_observation
    save_candle(connection, a)
    old = current(connection, a)
    first = export_dataset(
        connection,
        ["BTCUSDT"],
        "4h",
        "2024-01",
        "2024-01",
        "old",
        allow_incomplete=True,
        artifacts=tmp_path,
    )
    frozen = {p: p.read_bytes() for p in (tmp_path / "exports" / "old").iterdir()}
    run, state = review
    b = replace(a, close=Decimal("42600"))
    state["observations"] = [b]
    status, plan = run()
    assert status == 0 and plan["analysis"]["counts"]["changed"] == 1
    assert apply(plan)[1]["revised"] == 1
    assert apply(plan)[1]["outcome"] == "rolled_back"  # Used snapshot is obsolete.
    new = current(connection, a)
    assert (
        new["observed_at"].isoformat() == plan["source"]["responses"][0]["observed_at"]
    )
    assert new["source_sha256"] == plan["source"]["responses"][0]["sha256"]
    second = export_dataset(
        connection,
        ["BTCUSDT"],
        "4h",
        "2024-01",
        "2024-01",
        "new",
        allow_incomplete=True,
        artifacts=tmp_path,
    )
    assert second["sha256"] != first["sha256"]
    state["observations"] = [a]
    _, again = run()
    assert apply(again)[1]["revised"] == 1
    history = get_candle_history(connection, 1, 14400, a.open_time)
    assert [r["version"] for r in history] == [1, 2, 3]
    assert [r["close"] for r in history] == [a.close, b.close, a.close]
    assert {k: v for k, v in history[0].items() if k != "superseded_at"} == old
    assert all(p.read_bytes() == body for p, body in frozen.items())


def test_missing_valid_insert_keeps_historical_evidence(
    review, connection, candle_observation, tmp_path
):
    a = candle_observation
    evidence_path = tmp_path / "manifests" / "old.json"
    evidence_path.parent.mkdir()
    evidence_path.write_text(
        json.dumps(
            dict(
                symbol="BTCUSDT",
                interval="4h",
                month="2024-01",
                run_id="old",
                inspection_complete=True,
                database_write_outcome="committed",
                missing_intervals=[a.open_time.isoformat()],
                source_missing_intervals=[],
                excluded_observations=[
                    dict(open_time=a.open_time.isoformat(), reason="irregular_close")
                ],
            )
        )
    )
    evidence = evidence_path.read_bytes()
    before = import_evidence(tmp_path, ["BTCUSDT"], "2024-01", "2024-01")
    status, plan = review[0]()
    assert status == 0 and plan["analysis"]["counts"]["missing_database"] == 1
    assert plan["historical_source_diagnostics"]
    assert apply(plan)[1]["inserted"] == 1
    assert current(connection, a)["version"] == 1
    assert evidence_path.read_bytes() == evidence
    assert import_evidence(tmp_path, ["BTCUSDT"], "2024-01", "2024-01") == before


@pytest.mark.parametrize(
    "defect",
    [
        "zero_duration",
        "duplicate",
        "out_of_range",
        "partial",
        "absent",
        "bad_ohlc",
        "bad_json",
    ],
)
def test_invalid_or_partial_source_cannot_apply(
    review, connection, candle_observation, defect, monkeypatch
):
    run, state = review
    a = candle_observation
    state["observations"] = [a, replace(a, open_time=a.open_time + STEP)]
    mutations = {
        "zero_duration": lambda r: r[0].__setitem__(6, r[0][0]),
        "duplicate": lambda r: r.append(r[0]),
        "out_of_range": lambda r: r[0].__setitem__(0, r[0][0] - 14400000),
        "partial": lambda r: r.pop(),
        "absent": lambda r: r.clear(),
        "bad_ohlc": lambda r: r[0].__setitem__(2, "1"),
    }
    if defect == "bad_json":
        original = rv.fetch

        def fetch(url, **kwargs):
            if url.endswith("/time"):
                return original(url, **kwargs)
            response = Response(b"{", url, datetime.now(UTC), 200, {})
            kwargs["retain"](response)
            return response

        monkeypatch.setattr(rv, "fetch", fetch)
    else:
        state["mutate"] = mutations[defect]
    status, plan = run()
    assert status == 1 and plan["status"] == "blocked"
    assert plan["source"]["responses"]
    if defect == "zero_duration":
        assert plan["analysis"]["counts"]["invalid"] == 1
        assert plan["analysis"]["counts"]["missing_database"] == 1
    if defect in ("partial", "absent"):
        assert plan["analysis"]["counts"]["missing_provider"] > 0
    assert apply(plan)[0] == 1
    assert connection.execute("SELECT count(*) FROM candle").fetchone()[0] == 0


@pytest.mark.parametrize(
    "mutation",
    [
        "bytes",
        "missing_bytes",
        "plan",
        "parser",
        "proposed",
        "time",
        "partial",
        "duplicate",
        "implementation",
        "state_shape",
    ],
)
def test_integrity_and_reparse_reject_edits(review, connection, mutation):
    _, plan = review[0]()
    path = Path(plan["plan_path"])
    content = json.loads(path.read_text())
    source = content["source"]["responses"][0]
    raw = Path(source["raw_body"])
    if mutation == "bytes":
        raw.write_bytes(b"[]")
    elif mutation == "missing_bytes":
        raw.unlink()
    elif mutation == "plan":
        content["symbol"] = "ETHUSDT"  # fingerprint intentionally not recomputed
    else:
        if mutation == "parser":
            content["parser_version"] = "old"
        elif mutation == "proposed":
            content["analysis"]["entries"][0]["proposed"]["close"] = "42600"
        elif mutation == "time":
            source["observed_at"] = "2000-01-01T00:00:00+00:00"
        elif mutation == "partial":
            source["complete"] = False
        elif mutation == "implementation":
            content["implementation"] = {}
        elif mutation == "state_shape":
            content["analysis"]["entries"][0]["old"] = {}
        elif mutation == "duplicate":
            rows = json.loads(raw.read_text())
            raw.write_text(json.dumps(rows + rows))
            source["sha256"] = hashlib.sha256(raw.read_bytes()).hexdigest()
        content["fingerprint"] = rv.fingerprint(content)
    path.write_text(json.dumps(content))
    assert apply(plan)[0] == 1
    assert connection.execute("SELECT count(*) FROM candle").fetchone()[0] == 0


@pytest.mark.parametrize("change", ["version", "watermark", "missing_insert"])
def test_database_changes_since_review_rejected(
    review, connection, candle_observation, change
):
    a = candle_observation
    if change != "missing_insert":
        save_candle(connection, a)
    run, state = review
    state["observations"] = [replace(a, close=Decimal("42600"))]
    _, plan = run()
    if change == "version":
        save_candle(
            connection,
            replace(
                a,
                close=Decimal("42600"),
                observed_at=a.observed_at + timedelta(seconds=1),
            ),
        )
    elif change == "watermark":
        save_candle(
            connection, replace(a, observed_at=a.observed_at + timedelta(seconds=1))
        )
    else:
        save_candle(connection, a)
    before = current(connection, a)
    status, report = apply(plan)
    assert status == 1 and report["outcome"] == "rolled_back"
    assert report["conflicting"] == 1
    assert current(connection, a) == before


def historical_save(connection, observations, expected, start, end):
    return save_candles(
        connection,
        observations,
        mode="historical-revalidation",
        reviewed_rows=expected,
        revalidation_start=start,
        revalidation_end=end,
    )


@pytest.mark.parametrize("age", [-1, 0])
def test_stale_equal_time_roll_back_revision_and_insert(
    connection, candle_observation, age
):
    a = candle_observation
    later = replace(a, open_time=a.open_time + STEP)
    save_candles(connection, [a, later])
    rows = get_candles(connection, 1, 14400, a.open_time, later.open_time + STEP)
    expected = {(1, 14400, r["open_time"]): r for r in rows}
    missing = replace(a, source_kind="rest", open_time=a.open_time - STEP)
    expected[(1, 14400, missing.open_time)] = None
    b = replace(
        a,
        source_kind="rest",
        close=Decimal("42600"),
        observed_at=a.observed_at + timedelta(seconds=1),
    )
    conflict = replace(
        later,
        source_kind="rest",
        close=Decimal("42600"),
        observed_at=a.observed_at + timedelta(seconds=age),
    )
    with pytest.raises(BatchConflict) as error:
        historical_save(
            connection,
            [conflict, b, missing],
            expected,
            missing.open_time,
            later.open_time + STEP,
        )
    assert len(error.value.stale) == (age < 0)
    assert len(error.value.conflicts) == (age == 0)
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone()[0] == 0
    assert (
        get_candles(connection, 1, 14400, missing.open_time, later.open_time + STEP)
        == rows
    )


@pytest.mark.parametrize("missing", [False, True])
def test_concurrent_writer_invalidates_locked_review(
    connection, database, candle_observation, missing
):
    a = candle_observation
    if not missing:
        save_candle(connection, a)
    expected = {(1, 14400, a.open_time): None if missing else current(connection, a)}
    b = replace(
        a,
        source_kind="rest",
        close=Decimal("42600"),
        observed_at=a.observed_at + timedelta(seconds=1),
    )
    with (
        psycopg.connect(database, autocommit=True) as writer,
        ThreadPoolExecutor(1) as pool,
    ):
        with connection.transaction():
            if missing:
                # An uncommitted competing insertion is invisible to SELECT; the
                # unique-index wait must still invalidate the reviewed absence.
                from psycopg.rows import dict_row

                from backtest_badger.candles import _save_candle

                with connection.cursor(row_factory=dict_row) as cursor:
                    _save_candle(cursor, a)
            else:
                connection.execute("SELECT * FROM candle FOR UPDATE")
            future = pool.submit(
                historical_save, writer, [b], expected, a.open_time, a.open_time + STEP
            )
            wait_for_lock(connection, writer.info.backend_pid)
            if not missing:
                connection.execute(
                    "UPDATE candle SET last_observed_at=%s", (b.observed_at,)
                )
        with pytest.raises(ReviewConflict):
            future.result(timeout=5)
    assert current(connection, a)["version"] == 1
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone()[0] == 0


def test_failure_between_history_copy_and_current_update_rolls_back(
    review, connection, candle_observation
):
    a = candle_observation
    save_candle(connection, a)
    before = current(connection, a)
    review[1]["observations"] = [replace(a, close=Decimal("42600"))]
    _, plan = review[0]()
    connection.execute("""CREATE FUNCTION fail_update() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'synthetic failure'; END; $$""")
    connection.execute(
        "CREATE TRIGGER fail_update BEFORE UPDATE ON candle "
        "FOR EACH ROW EXECUTE FUNCTION fail_update()"
    )
    status, report = apply(plan)
    assert status == 1 and report["outcome"] == "rolled_back"
    assert current(connection, a) == before
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone()[0] == 0

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import psycopg
import pytest
from psycopg.pq import TransactionStatus

from backtest_badger import recent, rest
from backtest_badger.candles import (
    BatchConflict,
    get_candle_history,
    save_candle,
    save_candles,
)

from .test_candles import wait_for_lock

pytestmark = pytest.mark.integration


def refresh(connection, observations, end, **kwargs):
    return save_candles(
        connection,
        observations,
        mode="recent-refresh",
        refresh_start=end - timedelta(days=7),
        refresh_end=end,
        **kwargs,
    )


def test_refresh_versions_provenance_and_frozen_export(
    connection, candle_observation, tmp_path
):
    from backtest_badger.research import export_dataset

    a = candle_observation
    end = a.open_time + timedelta(days=2)
    save_candle(connection, a)
    export_dataset(
        connection,
        ["BTCUSDT"],
        "4h",
        "2024-01",
        "2024-01",
        "frozen",
        allow_incomplete=True,
        artifacts=tmp_path,
    )
    frozen = {p: p.read_bytes() for p in (tmp_path / "exports" / "frozen").iterdir()}
    b = replace(
        a,
        close=Decimal("42600"),
        source_kind="rest",
        source_sha256="b" * 64,
        observed_at=a.observed_at + timedelta(seconds=1),
    )
    differences = []
    assert refresh(connection, [b], end, differences=differences)["revised"] == 1
    assert differences[0]["old"]["source_kind"] == "archive"
    again = replace(
        a, source_kind="rest", observed_at=b.observed_at + timedelta(seconds=1)
    )
    assert refresh(connection, [again], end)["revised"] == 1
    assert refresh(connection, [again], end)["unchanged"] == 1
    history = get_candle_history(connection, a.market_id, 14400, a.open_time)
    assert [r["version"] for r in history] == [1, 2, 3]
    assert history[0]["source_sha256"] == a.source_sha256
    assert history[0]["observed_at"] == a.observed_at
    assert history[1]["close"] == b.close
    assert all(p.read_bytes() == content for p, content in frozen.items())


@pytest.mark.parametrize("age,old_range", [(-1, False), (0, False), (1, True)])
def test_conflict_or_stale_rolls_back_entire_page(
    connection, candle_observation, age, old_range
):
    a = candle_observation
    save_candle(connection, a)
    b = replace(
        a,
        close=Decimal("42600"),
        source_kind="rest",
        observed_at=a.observed_at + timedelta(seconds=age),
    )
    missing = replace(b, open_time=a.open_time - rest.STEP)
    end = a.open_time + timedelta(days=10 if old_range else 2)
    with pytest.raises(BatchConflict) as error:
        refresh(connection, [missing, b], end)
    assert len(error.value.stale) == (age < 0)
    assert len(error.value.conflicts) == (age >= 0)
    assert connection.execute("SELECT count(*) FROM candle").fetchone()[0] == 1
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone()[0] == 0


def test_identical_archive_confirmation_keeps_provenance(
    connection, candle_observation
):
    a = candle_observation
    save_candle(connection, a)
    before = get_candle_history(connection, a.market_id, 14400, a.open_time)[0]
    b = replace(
        a,
        source_kind="rest",
        source_sha256="b" * 64,
        observed_at=a.observed_at + timedelta(seconds=1),
    )
    assert refresh(connection, [b], a.open_time + timedelta(days=2))["unchanged"] == 1
    after = get_candle_history(connection, a.market_id, 14400, a.open_time)[0]
    assert after.pop("last_observed_at") == b.observed_at
    before.pop("last_observed_at")
    assert after == before


def test_concurrent_refresh_uses_locked_current_row(
    connection, database, candle_observation
):
    a = candle_observation
    save_candle(connection, a)
    b = replace(
        a,
        close=Decimal("42600"),
        source_kind="rest",
        observed_at=a.observed_at + timedelta(seconds=1),
    )
    with (
        psycopg.connect(database, autocommit=True) as writer,
        ThreadPoolExecutor(1) as pool,
    ):
        with connection.transaction():
            connection.execute("SELECT * FROM candle FOR UPDATE")
            future = pool.submit(refresh, writer, [b], a.open_time + timedelta(days=2))
            wait_for_lock(connection, writer.info.backend_pid)
            connection.execute(
                "UPDATE candle SET last_observed_at=%s", (b.observed_at,)
            )
        with pytest.raises(BatchConflict):
            future.result(timeout=5)
    assert connection.execute("SELECT version FROM candle").fetchone()[0] == 1


@pytest.fixture
def sync(monkeypatch, connection, tmp_path):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=180)
    fixed = end + timedelta(seconds=60)

    class ClockMeta(type):
        def __instancecheck__(cls, instance):
            return isinstance(instance, datetime)

    class Clock(datetime, metaclass=ClockMeta):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(recent, "datetime", Clock)

    @contextmanager
    def connect(_):
        yield connection

    monkeypatch.setattr(recent, "connect_database", connect)
    requests = []
    mode = {"fail_page": None, "omit": None, "invalid": False}

    def fetch(url, *, retain, attempts):
        assert connection.info.transaction_status == TransactionStatus.IDLE
        if url.endswith("/time"):
            rows = {"serverTime": (fixed - rest.EPOCH) // rest.MILLISECOND}
        else:
            params = parse_qs(urlsplit(url).query)
            opened = rest.EPOCH + int(params["startTime"][0]) * rest.MILLISECOND
            requests.append(opened)
            if mode["fail_page"] == len(requests):
                raise rest.RestError("transport", "Synthetic timeout.")
            rows = []
            while opened < end and len(rows) < 1000:
                stamp = (opened - rest.EPOCH) // rest.MILLISECOND
                if opened != mode["omit"]:
                    rows.append(
                        [
                            stamp,
                            "100",
                            "110",
                            "90",
                            "105",
                            "123",
                            stamp + 14400000 - 1,
                            "12000",
                            1234,
                            "60",
                            "6000",
                            "0",
                        ]
                    )
                opened += rest.STEP
            if mode["invalid"]:
                rows[-1][6] += 1
        response = rest.Response(json.dumps(rows).encode(), url, fixed, 200, {})
        retain(response)
        return response

    monkeypatch.setattr(recent, "fetch", fetch)

    def run(**kwargs):
        result = {}
        status = recent.sync_recent(
            "BTCUSDT", None, artifacts=tmp_path, result=result, **kwargs
        )
        return status, result

    return run, start, end, requests, mode


def test_sync_dry_run_multi_page_exact_boundary_and_repeat(sync, connection):
    run, start, end, requests, _ = sync
    status, result = run(start=start, dry_run=True)
    assert status == 0 and result["coverage"]["missing_count"] == 1080
    assert connection.execute("SELECT count(*) FROM candle").fetchone()[0] == 0
    assert requests == [start, start + 1000 * rest.STEP]
    status, result = run(start=start)
    assert status == 0 and result["inserted"] == 1080
    assert result["coverage"]["freshness"] == "fresh"
    assert result["coverage"]["latest_stored_open"] == (end - rest.STEP).isoformat()
    status, result = run()
    assert status == 0 and result["unchanged"] == 42 and result["revised"] == 0
    assert result["start"] == (end - timedelta(days=7)).isoformat()
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone()[0] == 0


def test_failed_second_page_then_default_catchup(sync):
    run, start, end, requests, mode = sync
    mode["fail_page"] = 2
    status, result = run(start=start)
    assert status == 1 and result["inserted"] == 1000 and result["failed_pages"] == 1
    assert result["coverage"]["missing_count"] == 80
    mode["fail_page"] = None
    status, result = run()
    assert status == 0 and result["inserted"] == 80
    assert requests[-1] == start + 1000 * rest.STEP


def test_missing_grid_and_malformed_page_evidence(sync, connection):
    run, start, end, _, mode = sync
    mode["omit"] = end - 2 * rest.STEP
    status, result = run(start=end - timedelta(days=1))
    assert status == 1 and result["inserted"] == 5
    assert result["coverage"]["missing_count"] == 1
    assert result["source_missing_intervals"] == [mode["omit"].isoformat()]
    assert result["coverage"]["freshness"] == "fresh"  # fresh tail can still have gaps
    mode["invalid"] = True
    status, result = run(start=end - timedelta(days=1))
    assert status == 1 and result["error_category"] == "row"
    assert result["pages"][0]["responses"][0]["raw_body"]
    assert connection.execute("SELECT count(*) FROM candle").fetchone()[0] == 5


def test_late_conflict_rolls_back_earlier_revision(connection, candle_observation):
    a = candle_observation
    later = replace(a, open_time=a.open_time + rest.STEP)
    save_candles(connection, [a, later])
    b = replace(
        a,
        source_kind="rest",
        close=Decimal("42600"),
        observed_at=a.observed_at + timedelta(seconds=1),
    )
    conflict = replace(later, source_kind="rest", close=Decimal("42600"))
    with pytest.raises(BatchConflict):
        refresh(connection, [b, conflict], a.open_time + timedelta(days=2))
    assert connection.execute(
        "SELECT version FROM candle ORDER BY open_time"
    ).fetchall() == [(1,), (1,)]
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone()[0] == 0

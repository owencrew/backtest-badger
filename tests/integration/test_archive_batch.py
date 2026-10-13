from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import psycopg
import pytest

from backtest_badger.archives import ArchiveRequest, parse_archive
from backtest_badger.candles import (
    BatchConflict,
    get_candles,
    save_candle,
    save_candles,
)

from .test_candles import wait_for_lock

pytestmark = pytest.mark.integration
REQUEST = ArchiveRequest("BTCUSDT", "4h", "2025-01")


@pytest.fixture
def month(connection, archive_download):
    market_id = connection.execute(
        "SELECT market_id FROM market WHERE symbol='BTCUSDT'"
    ).fetchone()[0]
    return parse_archive(REQUEST, archive_download(REQUEST), market_id=market_id)


def stored(connection, month):
    return get_candles(connection, month[0].market_id, 14400, *REQUEST.bounds)


def test_month_insert_and_identical_rerun(connection, month):
    assert save_candles(connection, month) == {"inserted": 186, "unchanged": 0}
    first = stored(connection, month)
    assert len(first) == 186
    assert first[0]["open"] == month[0].open
    assert first[0]["source_sha256"] == month[0].source_sha256
    assert save_candles(connection, month) == {"inserted": 0, "unchanged": 186}
    assert stored(connection, month) == first
    later = [
        replace(o, observed_at=o.observed_at + timedelta(seconds=1)) for o in month
    ]
    assert save_candles(connection, later) == {"inserted": 0, "unchanged": 186}
    assert {r["version"] for r in stored(connection, month)} == {1}
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone() == (0,)


@pytest.mark.parametrize("age", [-1, 0, 1])
def test_conflict_and_stale_roll_back_inserts_and_watermarks(connection, month, age):
    # A successful early watermark and missing row insert must also roll back.
    for index in (0, 100):
        save_candle(connection, month[index])
    before = stored(connection, month)
    values = [
        replace(o, observed_at=o.observed_at + timedelta(seconds=1)) for o in month
    ]
    values[100] = replace(
        month[100],
        close=Decimal("106"),
        observed_at=month[100].observed_at + timedelta(seconds=age),
    )
    with pytest.raises(BatchConflict) as error:
        save_candles(connection, values)
    assert len(error.value.stale) == (1 if age < 0 else 0)
    assert len(error.value.conflicts) == (0 if age < 0 else 1)
    assert stored(connection, month) == before
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone() == (0,)


def test_invalid_whole_batch_validated_before_sql(connection, month):
    values = month[:]
    values[-1] = replace(values[-1], low=Decimal("0"))
    with pytest.raises(ValueError):
        save_candles(connection, values)
    assert stored(connection, month) == []
    with pytest.raises(ValueError, match="Duplicate"):
        save_candles(connection, [month[0], month[0]])
    assert stored(connection, month) == []


def test_partial_database_failure_rolls_back_month(connection, month):
    connection.execute("""
        CREATE FUNCTION fail_archive() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NEW.open_time >= '2025-01-15T00:00:00Z'::timestamptz THEN
            RAISE EXCEPTION 'injected late archive failure';
          END IF;
          RETURN NEW;
        END; $$""")
    connection.execute("""CREATE TRIGGER fail_archive BEFORE INSERT ON candle
        FOR EACH ROW EXECUTE FUNCTION fail_archive()""")
    with pytest.raises(psycopg.errors.RaiseException):
        save_candles(connection, month)
    assert stored(connection, month) == []
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone() == (0,)


def test_batch_conflict_checks_locked_current_row(connection, database, month):
    save_candle(connection, month[100])
    with (
        psycopg.connect(
            database, autocommit=True, options="-c statement_timeout=5000"
        ) as writer,
        ThreadPoolExecutor(max_workers=1) as executor,
    ):
        with connection.transaction():
            connection.execute(
                "UPDATE candle SET close=106 WHERE open_time=%s",
                (month[100].open_time,),
            )
            # The prior committed row is identical; only locked current data conflicts.
            future = executor.submit(save_candles, writer, month)
            wait_for_lock(connection, writer.info.backend_pid)
        with pytest.raises(BatchConflict):
            future.result(timeout=5)
    rows = stored(connection, month)
    assert len(rows) == 1 and rows[0]["close"] == Decimal(106)


def test_batch_absent_row_race_and_legacy_revisions(connection, database, month):
    with (
        psycopg.connect(
            database, autocommit=True, options="-c statement_timeout=5000"
        ) as writer,
        ThreadPoolExecutor(max_workers=1) as executor,
    ):
        with connection.transaction():
            # Direct insert only supplies the uncommitted competitor; ordinary writes
            # below continue through the existing revision-preserving public API.
            from .test_candles import insert_raw

            insert_raw(
                connection,
                replace(month[0], close=Decimal(106)),
                recorded_at=month[0].observed_at,
            )
            future = executor.submit(save_candles, writer, month)
            wait_for_lock(connection, writer.info.backend_pid)
        with pytest.raises(BatchConflict):
            future.result(timeout=5)
    assert len(stored(connection, month)) == 1
    assert (
        save_candle(
            connection,
            replace(month[0], observed_at=month[0].observed_at + timedelta(seconds=1)),
        )
        == "revised"
    )
    assert (
        save_candle(
            connection,
            replace(
                month[0],
                close=Decimal(106),
                observed_at=month[0].observed_at + timedelta(seconds=2),
            ),
        )
        == "revised"
    )
    assert stored(connection, month)[0]["version"] == 3

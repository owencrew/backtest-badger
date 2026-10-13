from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from threading import Barrier
from time import monotonic, sleep

import psycopg
import pytest
from psycopg import sql

from backtest_badger.candles import (
    ObservationConflict,
    get_candle_history,
    get_candles,
    save_candle,
)

from .conftest import migrate

pytestmark = pytest.mark.integration
D = Decimal
OPEN = datetime(2024, 1, 1, tzinfo=UTC)
OBSERVED = OPEN + timedelta(days=1)


@pytest.fixture
def observation(connection, candle_observation):
    market_id = connection.execute(
        "SELECT market_id FROM market WHERE symbol = 'BTCUSDT'"
    ).fetchone()[0]
    return replace(candle_observation, market_id=market_id)


def history(connection, observation):
    return get_candle_history(
        connection,
        observation.market_id,
        observation.interval_seconds,
        observation.open_time,
    )


def insert_raw(connection, observation, *, table="candle", **overrides):
    values = asdict(observation) | {
        "version": 1,
        "recorded_at": OBSERVED + timedelta(days=1),
        "last_observed_at": observation.observed_at,
    }
    if table == "candle_revision":
        values["superseded_at"] = OBSERVED + timedelta(days=2)
    values.update(overrides)
    connection.execute(
        sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(map(sql.Identifier, values)),
            sql.SQL(", ").join(sql.Placeholder() for _ in values),
        ),
        list(values.values()),
    )


def test_fresh_migration_downgrade_and_unrelated_data(empty_database):
    with psycopg.connect(empty_database, autocommit=True) as conn:
        conn.execute("CREATE TABLE unrelated (value text)")
        conn.execute("INSERT INTO unrelated VALUES ('preserve me')")
        original_timezone = conn.execute("SHOW timezone").fetchone()
        migrate(empty_database)
        migrate(empty_database)  # repeat upgrade is harmless, seeds once
        assert conn.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "0001",
        )
        assert conn.execute("SELECT symbol FROM market ORDER BY symbol").fetchall() == [
            ("BTCUSDT",),
            ("ETHUSDT",),
        ]
        # Only the four PK/unique indexes the query patterns require.
        assert conn.execute(
            "SELECT count(*) FROM pg_indexes "
            "WHERE tablename IN ('market', 'candle', 'candle_revision')"
        ).fetchone() == (4,)
        migrate(empty_database, "base", downgrade=True)
        assert conn.execute(
            "SELECT to_regclass('candle'), to_regclass('market'), "
            "to_regclass('candle_revision')"
        ).fetchone() == (None, None, None)
        assert conn.execute("SELECT value FROM unrelated").fetchone() == (
            "preserve me",
        )
        assert conn.execute("SHOW timezone").fetchone() == original_timezone
        migrate(empty_database)
        assert conn.execute("SELECT count(*) FROM market").fetchone() == (2,)


def test_exact_round_trip_range_and_intervals(connection, observation):
    for offset in (2, 0, 1):
        save_candle(
            connection,
            replace(observation, open_time=OPEN + timedelta(hours=4 * offset)),
        )
    save_candle(connection, replace(observation, interval_seconds=3600))
    rows = get_candles(
        connection, observation.market_id, 14400, OPEN, OPEN + timedelta(hours=8)
    )
    assert [row["open_time"] for row in rows] == [OPEN, OPEN + timedelta(hours=4)]
    for field, expected in asdict(observation).items():
        assert rows[0][field] == expected
    assert rows[0]["version"] == 1
    assert rows[0]["recorded_at"] >= OBSERVED
    assert (
        len(get_candles(connection, observation.market_id, 3600, OPEN, OBSERVED)) == 1
    )
    assert (
        history(connection, replace(observation, open_time=OPEN - timedelta(days=1)))
        == []
    )


def test_identical_and_a_b_a_preserve_full_evidence(connection, observation, database):
    assert save_candle(connection, observation) == "inserted"
    first = history(connection, observation)[0]
    assert save_candle(connection, observation) == "unchanged"
    assert history(connection, observation) == [first]
    b = replace(
        observation,
        close=D("42600"),
        observed_at=OBSERVED + timedelta(minutes=1),
        source_sha256="b" * 64,
        source_kind="rest",
        source_url="https://example.invalid/synthetic-rest",
    )
    assert save_candle(connection, b) == "revised"
    assert save_candle(connection, b) == "unchanged"
    a_again = replace(observation, observed_at=OBSERVED + timedelta(minutes=2))
    assert save_candle(connection, a_again) == "revised"
    rows = history(connection, observation)
    assert [row["version"] for row in rows] == [1, 2, 3]
    assert [row["close"] for row in rows] == [
        observation.close,
        b.close,
        observation.close,
    ]
    assert [row["source_sha256"] for row in rows] == ["a" * 64, "b" * 64, "a" * 64]
    assert rows[0] | {"superseded_at": None} == first
    for field, value in asdict(b).items():
        assert rows[1][field] == value
    assert rows[0]["superseded_at"] == rows[1]["recorded_at"]
    assert rows[1]["superseded_at"] == rows[2]["recorded_at"]
    assert rows[2]["superseded_at"] is None
    # Downgrade also succeeds with populated, immutable history.
    migrate(database, "base", downgrade=True)
    assert connection.execute("SELECT to_regclass('candle')").fetchone() == (None,)


def test_stale_equal_time_and_later_identical_watermark(connection, observation):
    save_candle(connection, observation)
    original = history(connection, observation)[0]
    later = replace(
        observation, observed_at=OBSERVED + timedelta(minutes=2), source_sha256="b" * 64
    )
    assert save_candle(connection, later) == "unchanged"
    assert history(connection, observation)[0] == original | {
        "last_observed_at": later.observed_at
    }
    delayed = replace(
        observation, close=D("42600"), observed_at=OBSERVED + timedelta(minutes=1)
    )
    assert save_candle(connection, delayed) == "stale"
    with pytest.raises(ObservationConflict):
        save_candle(connection, replace(delayed, observed_at=later.observed_at))
    assert (
        save_candle(connection, observation) == "unchanged"
    )  # no watermark regression
    assert len(history(connection, observation)) == 1
    assert (
        save_candle(
            connection, replace(delayed, observed_at=OBSERVED + timedelta(minutes=3))
        )
        == "revised"
    )
    assert history(connection, observation)[0]["last_observed_at"] == later.observed_at
    assert save_candle(connection, later) == "stale"


@pytest.mark.parametrize("failure_table", ["candle_revision", "candle"])
def test_atomic_rollback_on_history_or_current_failure(
    connection, observation, failure_table
):
    save_candle(connection, observation)
    before = history(connection, observation)
    connection.execute("""
        CREATE FUNCTION fail_write() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'injected failure'; END; $$""")
    event = "INSERT" if failure_table == "candle_revision" else "UPDATE"
    connection.execute(
        sql.SQL(
            "CREATE TRIGGER fail_write BEFORE {} ON {} "
            "FOR EACH ROW EXECUTE FUNCTION fail_write()"
        ).format(sql.SQL(event), sql.Identifier(failure_table))
    )
    changed = replace(
        observation, close=D("42600"), observed_at=OBSERVED + timedelta(minutes=1)
    )
    with pytest.raises(psycopg.errors.RaiseException):
        save_candle(connection, changed)
    assert history(connection, observation) == before
    connection.execute(
        sql.SQL("DROP TRIGGER fail_write ON {}").format(sql.Identifier(failure_table))
    )
    assert save_candle(connection, changed) == "revised"
    assert [row["version"] for row in history(connection, observation)] == [1, 2]


def test_utc_normalization_and_read_timezone_scope(connection, observation):
    offset = timezone(timedelta(hours=5, minutes=30))
    save_candle(
        connection,
        replace(
            observation,
            open_time=OPEN.astimezone(offset),
            observed_at=OBSERVED.astimezone(offset),
        ),
    )
    connection.execute("SET TIME ZONE 'America/New_York'")
    row = history(connection, observation)[0]
    assert row["open_time"] == OPEN
    for name in ("open_time", "observed_at", "recorded_at", "last_observed_at"):
        assert row[name].utcoffset() == timedelta(0)
    assert connection.execute("SHOW timezone").fetchone() == ("America/New_York",)
    with pytest.raises(ValueError, match="timezone-aware"):
        save_candle(
            connection, replace(observation, open_time=OPEN.replace(tzinfo=None))
        )
    with pytest.raises(ValueError, match="nonempty bounded"):
        get_candles(connection, observation.market_id, 14400, OPEN, OPEN)


def test_reject_future_observations_and_nested_write(connection, observation):
    future = replace(observation, observed_at=datetime.now(UTC) + timedelta(days=1))
    with pytest.raises(psycopg.errors.CheckViolation):
        save_candle(connection, future)
    save_candle(connection, observation)
    with pytest.raises((ValueError, psycopg.errors.CheckViolation)):
        save_candle(connection, future)
    with connection.transaction(), pytest.raises(ValueError, match="idle autocommit"):
        save_candle(connection, observation)
    assert history(connection, observation)[0]["last_observed_at"] == OBSERVED


def test_postgres_numeric_special_value_ordering(connection):
    assert connection.execute("""SELECT 'NaN'::numeric > 'Infinity'::numeric,
        'NaN'::numeric = 'NaN'::numeric, 'Infinity'::numeric > 0,
        '-Infinity'::numeric < 0""").fetchone() == (True, True, True, True)


@pytest.mark.parametrize("table", ["candle", "candle_revision"])
@pytest.mark.parametrize(
    "column",
    [
        "open",
        "high",
        "low",
        "close",
        "base_volume",
        "quote_volume",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ],
)
@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_numeric_special_values_rejected(connection, observation, table, column, value):
    if table == "candle_revision":
        save_candle(connection, observation)
    with pytest.raises(psycopg.errors.CheckViolation):
        insert_raw(connection, observation, table=table, **{column: D(value)})


@pytest.mark.parametrize("table", ["candle", "candle_revision"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"interval_seconds": 7200},
        {"open_time": OPEN + timedelta(microseconds=1)},
        {"open_time": OPEN + timedelta(hours=1)},
        {"open": D(0)},
        {"low": D(-1)},
        {"open": D(44000)},
        {"close": D(40000)},
        {"low": D(45000)},
        {"base_volume": D(-1)},
        {"quote_volume": D(-1)},
        {"taker_buy_base_volume": D(-1)},
        {"taker_buy_quote_volume": D(-1)},
        {"taker_buy_base_volume": D(999)},
        {"taker_buy_quote_volume": D(99999999)},
        {"trade_count": -1},
        {"version": 0},
        {"observed_at": OPEN},
        {"recorded_at": OPEN},
        {"last_observed_at": OPEN},
        {"open_time": "infinity"},
        {"observed_at": "infinity"},
        {"recorded_at": "infinity"},
        {"last_observed_at": "infinity"},
        {"source_kind": "unknown"},
        {"source_url": " "},
        {"source_sha256": "A" * 64},
    ],
)
def test_database_checks(connection, observation, table, overrides):
    if table == "candle_revision":
        save_candle(connection, observation)
    with pytest.raises(psycopg.errors.CheckViolation):
        insert_raw(connection, observation, table=table, **overrides)


def test_keys_nulls_history_times_and_immutability(connection, observation):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        insert_raw(connection, observation, market_id=32767)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        insert_raw(connection, observation, table="candle_revision")
    with pytest.raises(psycopg.errors.NotNullViolation):
        insert_raw(connection, observation, source_url=None)
    with pytest.raises(psycopg.errors.NumericValueOutOfRange):
        insert_raw(connection, observation, trade_count=2**63)
    save_candle(connection, observation)
    with pytest.raises(psycopg.errors.UniqueViolation):
        insert_raw(connection, observation)
    for superseded in (OPEN, "infinity"):
        with pytest.raises(psycopg.errors.CheckViolation):
            insert_raw(
                connection,
                observation,
                table="candle_revision",
                superseded_at=superseded,
            )
    save_candle(
        connection,
        replace(
            observation, close=D(42600), observed_at=OBSERVED + timedelta(minutes=1)
        ),
    )
    with pytest.raises(psycopg.errors.UniqueViolation):
        insert_raw(connection, observation, table="candle_revision")
    for statement in (
        "UPDATE candle_revision SET close = 42600",
        "DELETE FROM candle_revision",
    ):
        with pytest.raises(psycopg.IntegrityError):
            connection.execute(statement)
    for statement in ("DELETE FROM candle", "DELETE FROM market"):
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            connection.execute(statement)


def test_market_identity_is_unique_and_extensible(connection):
    with pytest.raises(psycopg.errors.UniqueViolation):
        connection.execute(
            "INSERT INTO market (venue, market_type, symbol, base_asset, quote_asset) "
            "VALUES ('binance', 'spot', 'BTCUSDT', 'BTC', 'USDT')"
        )
    with pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(
            "INSERT INTO market (venue, market_type, symbol, base_asset, quote_asset) "
            "VALUES (' ', 'spot', 'NEW', 'NEW', 'USD')"
        )
    connection.execute(
        "INSERT INTO market (venue, market_type, symbol, base_asset, quote_asset) "
        "VALUES ('other', 'spot', 'NEWUSD', 'NEW', 'USD')"
    )


def wait_for_lock(observer, pid):
    deadline = monotonic() + 5
    while monotonic() < deadline:
        if observer.execute(
            "SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", (pid,)
        ).fetchone() == ("Lock",):
            return
        sleep(0.01)
    raise AssertionError("Writer never reached the expected PostgreSQL lock wait.")


@pytest.mark.parametrize("winner_newer", [False, True])
def test_absent_row_insert_race(connection, observation, database, winner_newer):
    later = replace(
        observation, close=D(42600), observed_at=OBSERVED + timedelta(minutes=1)
    )
    winner, loser = (later, observation) if winner_newer else (observation, later)
    with (
        psycopg.connect(
            database, autocommit=True, options="-c statement_timeout=5000"
        ) as competing,
        ThreadPoolExecutor(max_workers=1) as executor,
    ):
        # Both writers have actually observed the row as absent.
        assert history(connection, observation) == history(competing, observation) == []
        with connection.transaction():
            insert_raw(connection, winner)
            future = executor.submit(save_candle, competing, loser)
            wait_for_lock(connection, competing.info.backend_pid)
        assert future.result(timeout=5) == ("stale" if winner_newer else "revised")
    rows = history(connection, observation)
    assert rows[-1]["close"] == later.close
    assert [row["version"] for row in rows] == ([1] if winner_newer else [1, 2])


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("identical", [False, True])
def test_two_api_writers(connection, observation, database, existing, identical):
    if existing:
        save_candle(connection, observation)
    earlier = replace(
        observation, close=D(42600), observed_at=OBSERVED + timedelta(minutes=1)
    )
    later = (
        earlier
        if identical
        else replace(
            earlier, close=D(42700), observed_at=OBSERVED + timedelta(minutes=2)
        )
    )
    barrier = Barrier(2)

    def write(conn, value):
        barrier.wait(timeout=5)
        return save_candle(conn, value)

    with (
        psycopg.connect(
            database, autocommit=True, options="-c statement_timeout=5000"
        ) as a,
        psycopg.connect(
            database, autocommit=True, options="-c statement_timeout=5000"
        ) as b,
        ThreadPoolExecutor(max_workers=2) as executor,
    ):
        if existing:
            with connection.transaction():
                connection.execute("SELECT * FROM candle FOR UPDATE")
                futures = [
                    executor.submit(write, a, earlier),
                    executor.submit(write, b, later),
                ]
                wait_for_lock(connection, a.info.backend_pid)
                wait_for_lock(connection, b.info.backend_pid)
        else:
            futures = [
                executor.submit(write, a, earlier),
                executor.submit(write, b, later),
            ]
        results = [future.result(timeout=5) for future in futures]
    rows = history(connection, observation)
    accepted = sum(result in ("inserted", "revised") for result in results)
    assert len(rows) == int(existing) + accepted
    assert [row["version"] for row in rows] == list(range(1, len(rows) + 1))
    assert rows[-1]["close"] == later.close
    assert rows[-1]["observed_at"] == later.observed_at
    if identical:
        assert sorted(results) == sorted(
            ["revised" if existing else "inserted", "unchanged"]
        )

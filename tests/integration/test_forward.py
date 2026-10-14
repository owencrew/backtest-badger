"""Real PostgreSQL snapshot/read-only guarantees on disposable databases only."""

from dataclasses import replace

import psycopg
import pytest
from psycopg.rows import dict_row
from test_forward import sample_window

from backtest_badger import forward
from backtest_badger.candles import CandleObservation, save_candles

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("symbol", forward.SYMBOLS)
def test_read_only_bounded_snapshot_and_evidence(connection, monkeypatch, symbol):
    now = forward.utc_now()
    try:
        opened = forward.current_open(now)
    except ValueError:
        pytest.skip("Current native candle is within its 60-second settling delay.")
    market, rows = sample_window(symbol)
    shift = opened - rows[-1]["open_time"]
    observations = []
    for row in rows:
        row["open_time"] += shift
        # Use previously completed data; observation must be <= database clock.
        row["observed_at"] = row["open_time"] + forward.STEP
        observations.append(
            CandleObservation(**{k: row[k] for k in forward.OBSERVATION_FIELDS})
        )
    save_candles(connection, observations)
    # The asserted query bounds independently prove t+1 is never requested.
    before = connection.execute("SELECT * FROM candle ORDER BY open_time").fetchall()
    original = forward.get_candles

    def read(conn, market_id, interval, start, end):
        assert conn.execute("SHOW transaction_read_only").fetchone() == ("on",)
        assert conn.execute("SHOW transaction_isolation").fetchone() == (
            "repeatable read",
        )
        assert (start, end) == (opened - 6 * forward.STEP, opened + forward.STEP)
        assert interval == 14400 and market_id == market["market_id"]
        # PostgreSQL itself, not just convention, disallows mutations here.
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            with conn.transaction():
                conn.execute("UPDATE candle SET version=version")
        return original(conn, market_id, interval, start, end)

    monkeypatch.setattr(forward, "get_candles", read)
    actual_market, actual = forward.read_window(connection, symbol, opened)
    assert actual_market == market
    assert len(actual) == 7
    forward.validate_window(actual_market, actual, opened, forward.utc_now())
    assert (
        connection.execute("SELECT * FROM candle ORDER BY open_time").fetchall()
        == before
    )
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone() == (0,)
    assert actual[-1]["source_sha256"] == observations[-1].source_sha256
    assert actual[-1]["close"] == observations[-1].close


def test_database_stale_and_missing_candles(connection, candle_observation):
    a = replace(candle_observation, interval_seconds=14400)
    save_candles(connection, [a])
    market, rows = forward.read_window(
        connection, "BTCUSDT", a.open_time + forward.STEP
    )
    with pytest.raises(ValueError, match="Stale data"):
        forward.validate_window(
            market, rows, a.open_time + forward.STEP, forward.utc_now()
        )


def test_missing_market(connection):
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute("DELETE FROM market WHERE symbol='ETHUSDT'")
    with pytest.raises(ValueError, match="market is absent"):
        forward.read_window(
            connection, "ETHUSDT", forward.current_open(forward.utc_now())
        )

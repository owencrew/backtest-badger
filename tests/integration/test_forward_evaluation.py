"""Target-only snapshots on the explicitly configured disposable test server."""

from datetime import timedelta

import psycopg
import pytest
from test_forward import OPENED, sample_window

from backtest_badger import forward
from backtest_badger import forward_evaluation as fe
from backtest_badger.candles import CandleObservation, save_candles

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("symbol", fe.SYMBOLS)
def test_exact_target_snapshot_and_no_mutations(connection, monkeypatch, symbol):
    # Past synthetic economics; no genuine stored data is read. The test fixture
    # owns a freshly migrated, randomly named database on a disposable server.
    market, rows = sample_window(symbol)
    target = rows[-1].copy()
    target["open_time"] = OPENED + forward.STEP
    target["observed_at"] = target["open_time"] + forward.STEP + forward.DELAY
    observations = [
        CandleObservation(**{k: row[k] for k in forward.OBSERVATION_FIELDS})
        for row in [rows[-1], target]
    ]
    # DB insertion uses its actual clock; move both synthetic candles safely into
    # the past independently of the host's current wall-clock time.
    shift = timedelta(days=1000)
    from dataclasses import replace

    observations = [
        replace(r, open_time=r.open_time - shift, observed_at=r.observed_at - shift)
        for r in observations
    ]
    save_candles(connection, observations)
    record = {
        "market": market,
        "target_open_time": observations[-1].open_time.isoformat(),
    }
    before = connection.execute("SELECT * FROM candle ORDER BY open_time").fetchall()
    original = fe.get_candles

    def read(conn, market_id, interval, start, end):
        assert conn.execute("SHOW transaction_read_only").fetchone() == ("on",)
        assert conn.execute("SHOW transaction_isolation").fetchone() == (
            "repeatable read",
        )
        assert (start, end) == (
            observations[-1].open_time,
            observations[-1].open_time + forward.STEP,
        )
        assert interval == 14400 and market_id == market["market_id"]
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            with conn.transaction():
                conn.execute("UPDATE candle SET version=version")
        return original(conn, market_id, interval, start, end)

    monkeypatch.setattr(fe, "get_candles", read)
    actual = fe.read_target(connection, record)
    assert len(actual) == 1
    assert actual[0]["close"] == observations[-1].close
    assert actual[0]["source_sha256"] == observations[-1].source_sha256
    assert (
        connection.execute("SELECT * FROM candle ORDER BY open_time").fetchall()
        == before
    )
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone() == (0,)


def test_missing_target_and_market_id_mismatch(connection):
    market, _ = sample_window()
    record = {"market": market, "target_open_time": (OPENED + forward.STEP).isoformat()}
    assert fe.read_target(connection, record) == []
    market["market_id"] = 9
    with pytest.raises(ValueError, match="identity mismatch"):
        fe.read_target(connection, record)

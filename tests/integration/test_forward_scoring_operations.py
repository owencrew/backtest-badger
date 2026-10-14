"""End-to-end cycles against synthetic targets in disposable PostgreSQL only."""

from datetime import timedelta

import psycopg
import pytest
from test_evaluation import research_source  # noqa: F401
from test_forward import recording, synthetic_fit  # noqa: F401
from test_forward_evaluation import SETTLED, forbidden, write_journal
from test_forward_scoring_operations import clone

from backtest_badger import forward
from backtest_badger import forward_evaluation as fe
from backtest_badger import forward_scoring_operations as ops
from backtest_badger.candles import CandleObservation, save_candles

pytestmark = pytest.mark.integration


def test_real_scorer_pending_target_retry_idempotency_and_read_only(
    recording,  # noqa: F811
    connection,
    database,
    tmp_path,
    monkeypatch,  # noqa: F811
):
    run, _, rows, _ = recording
    path, record = run()
    eth_path = clone({"record": record, "path": path})
    collector = tmp_path / "collector"
    for forecast in (path, eth_path):
        write_journal(forecast, collector)
    monkeypatch.setattr(forward, "fit_forward", forbidden)
    monkeypatch.setattr(forward, "record_forward", forbidden)
    monkeypatch.setattr(forward, "verify_forward", forbidden)
    outcomes = tmp_path / "outcomes"
    operations = tmp_path / "scoring"
    connect_count = []

    def connect():
        connect_count.append(1)
        return psycopg.connect(
            database,
            autocommit=True,
            options="-c timezone=UTC -c statement_timeout=5000",
        )

    def cycle(connect=connect):
        now = max(connection.execute("SELECT clock_timestamp()").fetchone()[0], SETTLED)
        return ops.run_cycle(
            records=path.parent,
            outcomes=outcomes,
            collector_operations=collector,
            operations=operations,
            clock=lambda: now + timedelta(seconds=1),
            connect=connect,
        )

    original = fe.get_candles
    reads = []

    def read(conn, market_id, interval, start, end):
        assert conn.execute("SHOW transaction_read_only").fetchone() == ("on",)
        assert conn.execute("SHOW transaction_isolation").fetchone() == (
            "repeatable read",
        )
        assert start == fe.utc_time(record["target_open_time"])
        assert end == start + forward.STEP
        reads.append(market_id)
        return original(conn, market_id, interval, start, end)

    monkeypatch.setattr(fe, "get_candles", read)
    journal, code = cycle()
    assert code == 0
    assert [r["reason"] for r in journal["results"]] == ["pending_target_missing"] * 2
    target = rows[-1].copy()
    target.update(
        open_time=fe.utc_time(record["target_open_time"]), observed_at=SETTLED
    )
    targets = []
    for symbol, market_id in (("BTCUSDT", 1), ("ETHUSDT", 2)):
        target.update(market_id=market_id)
        target["source_url"] = rows[-1]["source_url"].replace("BTCUSDT", symbol)
        targets.append(
            CandleObservation(**{k: target[k] for k in forward.OBSERVATION_FIELDS})
        )
    save_candles(connection, targets)  # Fixture setup only, outside scorer snapshots.
    before = connection.execute("SELECT * FROM candle ORDER BY market_id").fetchall()
    forecasts = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (path, eth_path)}
    journal, code = cycle()
    assert code == 0 and [r["status"] for r in journal["results"]] == ["scored"] * 2
    scores = {p: p.read_bytes() for p in outcomes.glob("*.json")}
    assert len(scores) == 2 and reads == [1, 2, 1, 2]
    journal, code = cycle(connect=forbidden)
    assert code == 0
    assert [r["status"] for r in journal["results"]] == ["already_scored"] * 2
    assert len(connect_count) == 4
    assert (
        before
        == connection.execute("SELECT * FROM candle ORDER BY market_id").fetchall()
    )
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone() == (0,)
    assert all(p.read_bytes() == body for p, body in scores.items())
    assert all(
        (p.read_bytes(), p.stat().st_mtime_ns) == old for p, old in forecasts.items()
    )

import csv
import hashlib
import json
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import psycopg
import pytest

from backtest_badger import history, ingestion, research
from backtest_badger.archives import ArchiveError, ArchiveRequest, parse_archive
from backtest_badger.candles import save_candle, save_candles

pytestmark = pytest.mark.integration


def populate(
    connection, archive_download, month="2017-08", symbols=("BTCUSDT", "ETHUSDT")
):
    observations = {}
    for symbol in symbols:
        request = ArchiveRequest(symbol, "4h", month)
        market_id = connection.execute(
            "SELECT market_id FROM market WHERE symbol=%s", (symbol,)
        ).fetchone()[0]
        observations[symbol] = parse_archive(
            request, archive_download(request), market_id=market_id
        )
        save_candles(connection, observations[symbol])
    return observations


def test_stored_coverage_initial_boundary_missing_month_and_grid(
    connection, archive_download, tmp_path
):
    populate(connection, archive_download)
    report = research.coverage_report(
        connection,
        ["ETHUSDT", "BTCUSDT"],
        "4h",
        "2017-08",
        "2017-09",
        artifacts=tmp_path,
    )
    assert not report["complete"]
    for item in report["markets"].values():
        assert item["expected_count"] == 269
        assert item["actual_count"] == 89
        assert item["missing_count"] == 180
        assert item["missing_intervals"][0] == "2017-09-01T00:00:00+00:00"
        assert item["missing_intervals"][-1] == "2017-09-30T20:00:00+00:00"
        assert item["historical_revisions"] == item["duplicate_identity_count"] == 0
    connection.execute("SET TIME ZONE 'America/New_York'")
    exact = research.coverage_report(
        connection, ["BTCUSDT"], "4h", "2017-08", "2017-08", artifacts=tmp_path
    )
    assert exact["complete"]
    assert exact["markets"]["BTCUSDT"]["current_versions"] == 89


def test_repeatable_export_exact_decimal_determinism_and_immutability(
    connection, database, archive_download, tmp_path, monkeypatch
):
    observations = populate(connection, archive_download)
    selection = (connection, ["BTCUSDT", "ETHUSDT"], "4h", "2017-08", "2017-08")
    first = research.export_dataset(*selection, "first", artifacts=tmp_path)
    second = research.export_dataset(*selection, "second", artifacts=tmp_path)
    file = tmp_path / "exports" / "first" / "candles.csv"
    original = file.read_bytes()
    assert original == (tmp_path / "exports" / "second" / "candles.csv").read_bytes()
    assert first["sha256"] == second["sha256"] == hashlib.sha256(original).hexdigest()
    rows = list(csv.DictReader(original.decode().splitlines()))
    assert len(rows) == 178
    assert rows[0]["open"] == str(observations["BTCUSDT"][0].open)
    assert rows[0]["base_volume"] == str(observations["BTCUSDT"][0].base_volume)
    assert rows[0]["observed_at"] == observations["BTCUSDT"][0].observed_at.isoformat()
    assert first["row_counts"] == {"BTCUSDT": 89, "ETHUSDT": 89}
    with pytest.raises(FileExistsError):
        research.export_dataset(*selection, "first", artifacts=tmp_path)
    original_coverage = research._coverage

    def concurrent_correction(conn, *args):
        report = original_coverage(conn, *args)
        assert conn.execute("SHOW transaction_isolation").fetchone() == (
            "repeatable read",
        )
        assert conn.execute("SHOW transaction_read_only").fetchone() == ("on",)
        with psycopg.connect(database, autocommit=True) as writer:
            for symbol in ("BTCUSDT", "ETHUSDT"):
                value = observations[symbol][0]
                assert (
                    save_candle(
                        writer,
                        replace(
                            value,
                            close=Decimal("106"),
                            observed_at=value.observed_at + timedelta(seconds=1),
                        ),
                    )
                    == "revised"
                )
        return report

    monkeypatch.setattr(research, "_coverage", concurrent_correction)
    concurrent = research.export_dataset(*selection, "concurrent", artifacts=tmp_path)
    assert concurrent["sha256"] == first["sha256"]
    monkeypatch.setattr(research, "_coverage", original_coverage)
    corrected = research.export_dataset(*selection, "corrected", artifacts=tmp_path)
    assert corrected["sha256"] != first["sha256"]
    assert file.read_bytes() == original
    assert all(
        i["historical_revisions"] == 1
        for i in corrected["coverage"]["markets"].values()
    )


def test_missing_export_refusal_acknowledged_partial_and_existing_transaction(
    connection, archive_download, tmp_path
):
    populate(connection, archive_download, symbols=("BTCUSDT",))
    args = (connection, ["BTCUSDT", "ETHUSDT"], "4h", "2017-08", "2017-08")
    with pytest.raises(ValueError, match="incomplete"):
        research.export_dataset(*args, "refused", artifacts=tmp_path)
    assert not (tmp_path / "exports" / "refused").exists()
    result = research.export_dataset(
        *args, "partial", artifacts=tmp_path, allow_incomplete=True
    )
    assert result["status"] == "incomplete"
    assert result["coverage"]["markets"]["ETHUSDT"]["missing_count"] == 89
    assert result["row_counts"] == {"BTCUSDT": 89, "ETHUSDT": 0}
    assert result["incomplete_acknowledged"]
    with connection.transaction(), pytest.raises(ValueError, match="idle"):
        research.coverage_report(*args, artifacts=tmp_path)


def test_interrupted_backfill_restart_and_provenance(
    connection, database, archive_download, monkeypatch, tmp_path
):
    months = []
    fail = True

    def download(request):
        months.append(request.month)
        if fail and request.month == "2024-01":
            raise ArchiveError("http", "Synthetic unavailable archive", http_status=404)
        return archive_download(request)

    monkeypatch.setattr(ingestion, "download_archive", download)
    monkeypatch.setattr(
        ingestion,
        "connect_database",
        lambda _: psycopg.connect(database, autocommit=True),
    )
    args = ("BTCUSDT", "4h", "2023-12", "2024-01")
    assert history.backfill_history(*args, artifacts=tmp_path) == 1
    assert months == ["2023-12", "2024-01"]
    before = connection.execute("SELECT * FROM candle ORDER BY open_time").fetchall()
    assert len(before) == 186
    fail = False
    assert history.backfill_history(*args, artifacts=tmp_path) == 0
    after = connection.execute("SELECT * FROM candle ORDER BY open_time").fetchall()
    assert after[:186] == before
    assert len(after) == 372
    report = research.coverage_report(
        connection, ["BTCUSDT"], "4h", "2023-12", "2024-01", artifacts=tmp_path
    )
    assert report["complete"]
    assert report["markets"]["BTCUSDT"]["historical_revisions"] == 0
    manifests = [
        json.loads(p.read_text()) for p in (tmp_path / "manifests").glob("*.json")
    ]
    assert sorted(m["unchanged"] for m in manifests) == [0, 0, 0, 186]


def test_unresolved_evidence_blocks_complete_export_and_failed_file_is_not_published(
    connection, archive_download, tmp_path, monkeypatch
):
    populate(connection, archive_download)
    folder = tmp_path / "manifests"
    folder.mkdir()
    attempt = folder / "unfinished.json"
    attempt.write_text(
        json.dumps(
            dict(
                symbol="BTCUSDT",
                interval="4h",
                month="2017-08",
                started_at="2026-01-01",
                database_write_outcome="in_progress",
                dry_run=False,
            )
        )
    )
    args = (connection, ["BTCUSDT", "ETHUSDT"], "4h", "2017-08", "2017-08")
    report = research.coverage_report(*args, artifacts=tmp_path)
    assert report["markets"]["BTCUSDT"]["missing_count"] == 0
    assert not report["complete"]
    with pytest.raises(ValueError, match="incomplete"):
        research.export_dataset(*args, "unresolved", artifacts=tmp_path)
    attempt.unlink()

    def broken_write(value):
        raise OSError("Synthetic disk failure")

    monkeypatch.setattr(research, "_cell", broken_write)
    with pytest.raises(OSError):
        research.export_dataset(*args, "failed", artifacts=tmp_path)
    directory = tmp_path / "exports" / "failed"
    assert (directory / "candles.csv.partial").exists()
    assert not (directory / "manifest.json").exists()
    with pytest.raises(FileExistsError):
        research.export_dataset(*args, "failed", artifacts=tmp_path)


@pytest.fixture
def gap_import(database, archive_rows, archive_download, monkeypatch, tmp_path):
    request = ArchiveRequest("BTCUSDT", "4h", "2017-09")
    rows = archive_rows(request)
    rows[33][6] = str(int(rows[33][6]) + 1)
    rows.pop(34)
    download = archive_download(request, rows)
    monkeypatch.setattr(ingestion, "download_archive", lambda _: download)
    monkeypatch.setattr(
        ingestion,
        "connect_database",
        lambda _: psycopg.connect(database, autocommit=True),
    )
    return request, download


def test_gap_import_restart_diagnostics_and_export(connection, gap_import, tmp_path):
    request, download = gap_import
    result = {}
    assert ingestion.ingest_archive(request, artifacts=tmp_path, result=result) == 1
    assert connection.execute("SELECT count(*) FROM candle").fetchone() == (0,)
    before = None
    for retry in (False, True):
        result = {}
        assert (
            ingestion.ingest_archive(
                request, artifacts=tmp_path, allow_source_gaps=True, result=result
            )
            == 0
        )
        assert result["inserted"] == (0 if retry else 178)
        assert result["unchanged"] == (178 if retry else 0)
        assert result["rejected"] == result["excluded_count"] == 1
        assert result["actual_count"] == 179
        assert result["accepted_count"] == 178
        assert result["validation_result"] == "source_gaps"
        assert result["database_write_outcome"] == "committed"
        current = connection.execute(
            "SELECT * FROM candle ORDER BY open_time"
        ).fetchall()
        if retry:
            assert current == before
        before = current
    assert connection.execute("SELECT count(*) FROM candle_revision").fetchone() == (0,)
    args = (connection, ["BTCUSDT"], "4h", "2017-09", "2017-09")
    report = research.coverage_report(*args, artifacts=tmp_path)
    market = report["markets"]["BTCUSDT"]
    assert market["actual_count"] == 178
    assert market["missing_count"] == 2
    assert market["known_source_missing_count"] == 1
    assert market["excluded_provider_observation_count"] == 1
    assert market["successfully_inspected_months"] == ["2017-09"]
    assert market["successful_archive_month_count"] == 1
    assert market["months_not_attempted"] == []
    assert market["failed_or_unresolved_imports"] == []
    assert market["source_diagnostics"][0]["source_sha256"] == download.sha256
    with pytest.raises(ValueError, match="incomplete"):
        research.export_dataset(*args, "refused-gaps", artifacts=tmp_path)
    export = research.export_dataset(
        *args, "gaps", artifacts=tmp_path, allow_incomplete=True
    )
    assert export["status"] == "incomplete"
    assert export["coverage"] == report
    # Filling the stored grid from another accepted source must not silently erase
    # the independently recorded provider anomaly from coverage or export policy.
    complete = [
        replace(o, open_time=request.grid[i])
        for i, o in zip(
            (33, 34),
            parse_archive(request, download, market_id=1, allow_source_gaps=True)[:2],
            strict=True,
        )
    ]
    save_candles(connection, complete)
    still = research.coverage_report(*args, artifacts=tmp_path)
    assert still["markets"]["BTCUSDT"]["missing_count"] == 0
    assert not still["complete"]


@pytest.mark.parametrize("failure", ["conflict", "stale", "database"])
def test_gap_batch_is_atomic_on_failures(connection, gap_import, tmp_path, failure):
    request, download = gap_import
    observations = parse_archive(request, download, market_id=1, allow_source_gaps=True)
    if failure == "database":
        connection.execute("""CREATE FUNCTION fail_gap_batch() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN
            IF NEW.open_time >= '2017-09-15Z'::timestamptz THEN
                RAISE EXCEPTION 'injected failure';
            END IF; RETURN NEW; END; $$""")
        connection.execute(
            "CREATE TRIGGER fail_gap_batch BEFORE INSERT ON candle "
            "FOR EACH ROW EXECUTE FUNCTION fail_gap_batch()"
        )
    else:
        save_candle(
            connection,
            replace(
                observations[0],
                observed_at=observations[0].observed_at - timedelta(seconds=1),
            ),
        )
        save_candle(
            connection,
            replace(
                observations[-1],
                close=Decimal("106"),
                observed_at=observations[-1].observed_at
                + timedelta(seconds=1 if failure == "stale" else 0),
            ),
        )
    before = connection.execute("SELECT * FROM candle ORDER BY open_time").fetchall()
    result = {}
    assert (
        ingestion.ingest_archive(
            request, artifacts=tmp_path, allow_source_gaps=True, result=result
        )
        == 1
    )
    assert result["database_write_outcome"] == "rolled_back"
    assert result["inserted"] == result["unchanged"] == 0
    assert result["conflicting"] == (failure == "conflict")
    assert result["stale"] == (failure == "stale")
    assert result["excluded_count"] == 1
    assert (
        connection.execute("SELECT * FROM candle ORDER BY open_time").fetchall()
        == before
    )

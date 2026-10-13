import json
from unittest.mock import MagicMock

import psycopg
import pytest

from backtest_badger import cli, ingestion
from backtest_badger.archives import ArchiveRequest
from backtest_badger.candles import BatchConflict

REQUEST = ArchiveRequest("BTCUSDT", "4h", "2025-01")


def manifest(tmp_path):
    return json.loads(next((tmp_path / "manifests").glob("*.json")).read_text())


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--symbol", "BTCUSDT"],
        ["--symbol", "OTHER", "--interval", "4h", "--month", "2025-01"],
        ["--symbol", "BTCUSDT", "--interval", "4h", "--month", "2025-13"],
        ["--symbol", "BTCUSDT", "--interval", "4h", "--month", "2025-1"],
        ["--symbol", "BTCUSDT", "--interval", "4h", "--month", "9999-12"],
    ],
)
def test_cli_validates_before_io(monkeypatch, args):
    monkeypatch.setattr(
        cli, "ingest_archive", lambda *a, **k: pytest.fail("Unexpected I/O")
    )
    with pytest.raises(SystemExit) as error:
        cli.main(["ingest-archive", *args])
    assert error.value.code == 2


def test_dry_run_artifacts_and_no_database(monkeypatch, tmp_path, archive_download):
    download = archive_download(REQUEST)
    monkeypatch.setattr(ingestion, "download_archive", lambda _: download)
    monkeypatch.setattr(
        ingestion, "connect_database", lambda _: pytest.fail("Dry run connected")
    )
    assert ingestion.ingest_archive(REQUEST, dry_run=True, artifacts=tmp_path) == 0
    result = manifest(tmp_path)
    assert result["actual_count"] == result["expected_count"] == 186
    assert result["database_write_outcome"] == "dry_run"
    assert result["source_sha256"] == download.sha256
    assert result["observed_at"] == download.observed_at.isoformat()
    assert (tmp_path / "raw" / (download.sha256 + ".zip")).read_bytes() == download.body
    assert next((tmp_path / "raw").glob("*.CHECKSUM")).read_bytes() == download.checksum


def test_cli_dry_run_needs_no_settings(monkeypatch):
    monkeypatch.setattr(
        cli, "load_settings", lambda: pytest.fail("Dry run needs no DB config")
    )
    mock = MagicMock(return_value=0)
    monkeypatch.setattr(cli, "ingest_archive", mock)
    assert (
        cli.main(
            [
                "ingest-archive",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "4h",
                "--month",
                "2025-01",
                "--dry-run",
            ]
        )
        == 0
    )
    assert mock.call_args.kwargs == {"dry_run": True}


def test_invalid_archive_retains_evidence_no_db(
    monkeypatch, tmp_path, archive_download, archive_rows
):
    rows = archive_rows(REQUEST)[1:]
    monkeypatch.setattr(
        ingestion, "download_archive", lambda _: archive_download(REQUEST, rows)
    )
    monkeypatch.setattr(
        ingestion,
        "connect_database",
        lambda _: pytest.fail("Invalid archive connected"),
    )
    assert ingestion.ingest_archive(REQUEST, artifacts=tmp_path) == 1
    result = manifest(tmp_path)
    assert result["validation_result"] == "failed"
    assert result["missing_intervals"] == [REQUEST.grid[0].isoformat()]
    assert result["rejected"] == 185
    assert result["database_write_outcome"] == "not_attempted"


@pytest.mark.parametrize("failure", ["conflict", "database", "constraint", "manifest"])
def test_write_failure_reporting(
    monkeypatch, tmp_path, archive_download, capsys, failure
):
    monkeypatch.setattr(
        ingestion, "download_archive", lambda _: archive_download(REQUEST)
    )
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.execute.return_value.fetchone.return_value = (7,)
    monkeypatch.setattr(ingestion, "connect_database", lambda _: conn)

    def save(connection, observations):
        assert all(o.market_id == 7 for o in observations)
        if failure == "conflict":
            raise BatchConflict([{"open_time": REQUEST.grid[0].isoformat()}], [])
        if failure == "database":
            raise psycopg.OperationalError("private-password")
        if failure == "constraint":
            raise psycopg.errors.CheckViolation("private-password")
        return {"inserted": 186, "unchanged": 0}

    monkeypatch.setattr(ingestion, "save_candles", save)
    original = ingestion._write_manifest

    def write(path, data):
        if data["database_write_outcome"] == "committed":
            raise OSError("private-password")
        original(path, data)

    if failure == "manifest":
        monkeypatch.setattr(ingestion, "_write_manifest", write)
    assert ingestion.ingest_archive(REQUEST, object(), artifacts=tmp_path) == 1
    output = capsys.readouterr().out
    assert "private-password" not in output
    result = manifest(tmp_path)
    if failure == "conflict":
        assert result["conflicting"] == 1
        assert result["rejected"] == 186
        assert result["database_write_outcome"] == "rolled_back"
    elif failure == "database":
        assert result["database_write_outcome"] == "failed_or_unknown"
        assert result["rejected"] is None
        assert result["failed_observations"] is None
    elif failure == "constraint":
        assert result["database_write_outcome"] == "rolled_back"
        assert result["rejected"] == 186
    else:
        assert "Database outcome: committed; inserted=186" in output
        assert result["database_write_outcome"] == "in_progress"

import json

import pytest

from backtest_badger import cli, history
from backtest_badger.archives import ArchiveError, ArchiveRequest, parse_archive
from backtest_badger.research import import_evidence


@pytest.mark.parametrize("symbol", ["BTCUSDT", "ETHUSDT"])
def test_verified_boundary_and_internal_gap(symbol, archive_download, archive_rows):
    request = ArchiveRequest(symbol, "4h", "2017-08")
    rows = archive_rows(request)
    parsed = parse_archive(request, archive_download(request, rows), market_id=1)
    assert len(parsed) == 89
    assert parsed[0].open_time.isoformat() == "2017-08-17T04:00:00+00:00"
    assert parsed[-1].open_time.isoformat() == "2017-08-31T20:00:00+00:00"
    for index in (0, 40, 88):
        with pytest.raises(ArchiveError) as error:
            parse_archive(
                request,
                archive_download(request, rows[:index] + rows[index + 1 :]),
                market_id=1,
            )
        assert error.value.details["missing_intervals"] == [
            request.grid[index].isoformat()
        ]


def test_later_partial_month_still_fails(archive_download, archive_rows):
    request = ArchiveRequest("BTCUSDT", "4h", "2017-09")
    with pytest.raises(ArchiveError, match="missing"):
        parse_archive(
            request, archive_download(request, archive_rows(request)[97:]), market_id=1
        )
    assert len(ArchiveRequest("BTCUSDT", "1h", "2017-08").grid) == 744


def test_month_order_and_stop_then_restart(monkeypatch):
    months = list(history.history_requests("BTCUSDT", "4h", "2023-12", "2024-02"))
    assert [r.month for r in months] == ["2023-12", "2024-01", "2024-02"]
    assert [len(r.grid) for r in months] == [186, 186, 174]
    called = []

    def ingest(request, *args, result, **kwargs):
        called.append(request.month)
        result.update(inserted=0, unchanged=186)
        return int(request.month == "2024-01" and called.count("2024-01") == 1)

    monkeypatch.setattr(history, "ingest_archive", ingest)
    assert history.backfill_history("BTCUSDT", "4h", "2023-12", "2024-02") == 1
    assert called == ["2023-12", "2024-01"]
    assert history.backfill_history("BTCUSDT", "4h", "2023-12", "2024-02") == 0
    assert called == ["2023-12", "2024-01", "2023-12", "2024-01", "2024-02"]


@pytest.mark.parametrize(
    "command", ["backfill-history", "coverage-report", "export-dataset"]
)
@pytest.mark.parametrize(
    "start,end",
    [("2017-07", "2017-08"), ("2024-02", "2024-01"), ("2024-01", "9999-12")],
)
def test_range_cli_validation_before_io(monkeypatch, command, start, end):
    monkeypatch.setattr(cli, "load_settings", lambda: pytest.fail("Unexpected I/O"))
    args = [
        command,
        "--symbol",
        "BTCUSDT",
        "--interval",
        "4h",
        "--start-month",
        start,
        "--end-month",
        end,
    ]
    if command == "export-dataset":
        args += ["--dataset-id", "test"]
    with pytest.raises(SystemExit) as error:
        cli.main(args)
    assert error.value.code == 2


def test_import_evidence_resolved_failures_and_unknown_attempts(tmp_path):
    folder = tmp_path / "manifests"
    folder.mkdir()
    base = dict(symbol="BTCUSDT", interval="4h", month="2024-01", dry_run=False)
    for number, fields in enumerate(
        [
            dict(http_status=404, database_write_outcome="not_attempted"),
            dict(database_write_outcome="committed"),
            dict(month="2024-02", database_write_outcome="in_progress"),
            dict(month="2024-02", database_write_outcome="dry_run", dry_run=True),
            dict(
                month="2024-03", http_status=404, database_write_outcome="not_attempted"
            ),
        ]
    ):
        (folder / f"{number}.json").write_text(
            json.dumps({**base, **fields, "started_at": str(number)})
        )
    result, errors = import_evidence(tmp_path, ["BTCUSDT"], "2024-01", "2024-03")
    assert not errors
    item = result["BTCUSDT"]
    assert item["successful_import_attempts"] == 1
    assert item["failed_or_unresolved_attempts"] == 3
    assert item["unavailable_archive_months"] == ["2024-03"]
    assert [i["month"] for i in item["failed_or_unresolved_imports"]] == [
        "2024-02",
        "2024-03",
    ]


def test_close_boundary_failure_explained_without_accepting_row(
    archive_download, archive_rows
):
    request = ArchiveRequest("BTCUSDT", "4h", "2017-09")
    rows = archive_rows(request)
    rows[33][6] = str(int(rows[33][6]) + 1)
    with pytest.raises(ArchiveError) as error:
        parse_archive(request, archive_download(request, rows), market_id=1)
    assert error.value.details["invalid_row"] == 34
    assert (
        error.value.details["invalid_reason"]
        == "Incorrect inclusive close-time boundary."
    )

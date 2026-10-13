"""Offline provider evidence and conservative gap policy regression tests."""

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backtest_badger import cli, history
from backtest_badger.archives import ArchiveError, ArchiveRequest, parse_archive

EVIDENCE = Path(__file__).parent / "fixtures" / "binance-historical-comparison.json"


def economics(row):
    return tuple(Decimal(row[i]) for i in (1, 2, 3, 4, 5, 7, 8, 9, 10))


def test_verified_official_source_comparisons():
    evidence = json.loads(EVIDENCE.read_text())
    for day in ("2017-09-06", "2018-06-26"):
        data = evidence[day]
        for interval in ("4h", "1h"):
            assert [
                [Decimal(v) for v in r[:11]] for r in data["daily_" + interval]
            ] == [[Decimal(v) for v in r[:11]] for r in data["rest_" + interval]]
        daily = {int(r[0]): r for r in data["daily_4h"]}
        for row in data["monthly_4h"]:
            assert economics(row) == economics(daily[int(row[0])])
    sept = evidence["2017-09-06"]
    assert [int(r[0]) for r in sept["monthly_4h"]] == [
        1504656000000,
        1504670400000,
        1504684800000,
        1504699200000,
        1504728000000,
    ]
    assert sept["monthly_4h"][3][6] == "1504713600000"
    assert sept["daily_4h"][3][6] == "1504713599999"
    placeholder = sept["daily_4h"][4]
    assert placeholder[0] == placeholder[6] == "1504713600000"
    assert economics(placeholder)[4:] == (0, 0, 0, 0, 0)
    # Four actual hourly parents support the 12:00 bar's economics, but no
    # replacement or aggregation is persisted by the ingestion implementation.
    parents = sept["daily_1h"][12:16]
    bar = sept["monthly_4h"][3]
    assert Decimal(bar[1]) == Decimal(parents[0][1])
    assert Decimal(bar[2]) == max(Decimal(r[2]) for r in parents)
    assert Decimal(bar[3]) == min(Decimal(r[3]) for r in parents)
    assert Decimal(bar[4]) == Decimal(parents[-1][4])
    for column in (5, 7, 8, 9, 10):
        assert Decimal(bar[column]) == sum(Decimal(r[column]) for r in parents)
    # The native 20:00 bar matches the only returned hour, 23:00. A normal
    # close boundary does not establish uninterrupted trading within a bar.
    assert economics(sept["monthly_4h"][-1]) == economics(sept["daily_1h"][-1])
    june = evidence["2018-06-26"]
    assert [int(r[0]) for r in june["monthly_4h"]] == [
        1529971200000,
        1530014400000,
        1530028800000,
        1530043200000,
    ]
    assert june["monthly_4h"][0][6] == "1529978399999"
    assert [int(r[0]) for r in june["daily_1h"][:3]] == [
        1529971200000,
        1529974800000,
        1530014400000,
    ]


@pytest.mark.parametrize(
    "month,day,accepted,missing",
    [
        ("2017-09", "2017-09-06", 178, 1),
        ("2018-06", "2018-06-26", 177, 2),
    ],
)
def test_real_defects_strict_vs_opt_in(
    archive_rows, archive_download, month, day, accepted, missing
):
    request = ArchiveRequest("BTCUSDT", "4h", month)
    evidence = json.loads(EVIDENCE.read_text())[day]["monthly_4h"]
    start = int(evidence[0][0])
    # Actual provider day inside a synthetic, otherwise complete month.
    rows = [
        r for r in archive_rows(request) if not start <= int(r[0]) < start + 86400000
    ]
    rows += evidence
    rows.sort(key=lambda r: int(r[0]))
    download = archive_download(request, rows)
    with pytest.raises(ArchiveError, match="close-time boundary"):
        parse_archive(request, download, market_id=1)
    diagnostics = {}
    observations = parse_archive(
        request, download, market_id=1, allow_source_gaps=True, diagnostics=diagnostics
    )
    assert len(observations) == accepted
    assert len(diagnostics["source_missing_intervals"]) == missing
    assert len(diagnostics["missing_intervals"]) == missing + 1
    assert diagnostics["excluded_count"] == 1
    assert not diagnostics["candle_complete"]
    assert diagnostics["inspection_complete"]
    assert (
        diagnostics["excluded_observations"][0]["action"]
        == "excluded_without_normalization"
    )
    assert all(o.source_sha256 == download.sha256 for o in observations)


@pytest.mark.parametrize(
    "kind",
    [
        "economic",
        "economic_and_close",
        "duplicate_excluded",
        "misaligned",
        "reordered",
        "outside_month",
        "inverted_close",
        "overlong_close",
        "csv",
        "checksum",
        "zip",
    ],
)
def test_gap_option_does_not_bypass_other_failures(
    archive_rows, archive_download, kind
):
    request = ArchiveRequest("BTCUSDT", "4h", "2017-09")
    rows = archive_rows(request)
    rows[0][6] = rows[0][0]  # Known shortened class, but other rules still apply.
    if kind in ("economic", "economic_and_close"):
        rows[0 if kind == "economic_and_close" else 1][5] = "-1"
    elif kind == "duplicate_excluded":
        rows[1] = rows[0][:]
    elif kind == "misaligned":
        rows[1][0] = str(int(rows[1][0]) + 1000)
    elif kind == "reordered":
        rows[0], rows[1] = rows[1], rows[0]
    elif kind == "outside_month":
        for i in (0, 6):
            rows[-1][i] = str(int(rows[-1][i]) + 14400000)
    elif kind == "inverted_close":
        rows[1][6] = str(int(rows[1][0]) - 1)
    elif kind == "overlong_close":
        rows[1][6] = str(int(rows[1][6]) + 2)
    elif kind == "csv":
        rows[1].pop()
    download = archive_download(request, rows)
    if kind == "checksum":
        download = replace(download, body=b"bad checksum")
    elif kind == "zip":
        download = archive_download(request, member="../unexpected.csv")
    with pytest.raises(ArchiveError):
        parse_archive(request, download, market_id=1, allow_source_gaps=True)


def test_missing_valid_neighbors_and_cli_opt_in(
    archive_rows, archive_download, monkeypatch
):
    request = ArchiveRequest("BTCUSDT", "4h", "2017-09")
    rows = archive_rows(request)
    rows.pop(34)
    download = archive_download(request, rows)
    with pytest.raises(ArchiveError, match="missing"):
        parse_archive(request, download, market_id=1)
    assert (
        len(parse_archive(request, download, market_id=1, allow_source_gaps=True))
        == 179
    )
    mock = MagicMock(return_value=0)
    monkeypatch.setattr(cli, "backfill_history", mock)
    assert (
        cli.main(
            [
                "backfill-history",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "4h",
                "--start-month",
                "2017-09",
                "--end-month",
                "2017-09",
                "--dry-run",
                "--allow-source-gaps",
            ]
        )
        == 0
    )
    assert mock.call_args.kwargs["allow_source_gaps"] is True


def test_range_continues_known_gaps_but_stops_new_failure(monkeypatch):
    called = []

    def ingest(request, *args, result, allow_source_gaps, **kwargs):
        assert allow_source_gaps
        called.append(request.month)
        result.update(validation_result="source_gaps", excluded_count=1)
        return int(request.month == "2017-11")

    monkeypatch.setattr(history, "ingest_archive", ingest)
    assert (
        history.backfill_history(
            "BTCUSDT", "4h", "2017-09", "2017-12", allow_source_gaps=True
        )
        == 1
    )
    assert called == ["2017-09", "2017-10", "2017-11"]


def test_empty_or_fully_excluded_month_stops_for_review(archive_download, archive_rows):
    request = ArchiveRequest("BTCUSDT", "4h", "2017-09")
    excluded = archive_rows(request)
    for row in excluded:
        row[6] = row[0]
    for rows in ([], excluded):
        with pytest.raises(ArchiveError, match="No eligible observations"):
            parse_archive(
                request,
                archive_download(request, rows),
                market_id=1,
                allow_source_gaps=True,
            )

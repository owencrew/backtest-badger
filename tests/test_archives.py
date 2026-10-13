import io
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError

import pytest

from backtest_badger import archives
from backtest_badger.archives import ArchiveError, ArchiveRequest, parse_archive

REQUEST = ArchiveRequest("BTCUSDT", "4h", "2025-01")


@pytest.mark.parametrize(
    "month,interval",
    [("2024-12", "1h"), ("2024-12", "4h"), ("2025-01", "1h"), ("2025-01", "4h")],
)
def test_complete_month_exact_values_and_provenance(archive_download, month, interval):
    request = ArchiveRequest("ETHUSDT", interval, month)
    download = archive_download(request)
    observations = parse_archive(request, download, market_id=7)
    assert len(observations) == (744 if interval == "1h" else 186)
    assert [o.open_time for o in observations] == request.grid
    assert observations[0].open == Decimal(
        "100.123456789012345678901234567890123456789"
    )
    assert observations[0].base_volume == Decimal(
        "123.000000000000000000000000000000000000001"
    )
    assert all(o.market_id == 7 and o.source_kind == "archive" for o in observations)
    assert all(
        o.observed_at == download.observed_at and o.source_sha256 == download.sha256
        for o in observations
    )
    assert (
        observations[-1].open_time + timedelta(seconds=request.seconds)
        == request.bounds[1]
    )
    # Parsing the same local file does not fabricate a new observation timestamp.
    assert parse_archive(request, download, market_id=7) == observations


@pytest.mark.parametrize(
    "column,value",
    [
        (1, "NaN"),
        (1, "1e999999"),
        (2, "1"),
        (5, "-1"),
        (8, "1.5"),
        (8, str(2**63)),
        (9, "999"),
        (6, "1735704000000000"),
        (0, "1735689600000"),
    ],
)
def test_invalid_rows_rejected(archive_rows, archive_download, column, value):
    rows = archive_rows(REQUEST)
    rows[0][column] = value
    with pytest.raises(ArchiveError, match="CSV row 1"):
        parse_archive(REQUEST, archive_download(REQUEST, rows), market_id=1)


@pytest.mark.parametrize("kind", ["columns", "unaligned", "header"])
def test_structure_alignment_header(archive_rows, archive_download, kind):
    rows = archive_rows(REQUEST)
    if kind == "columns":
        rows[0].pop()
    elif kind == "header":
        rows[0] = ["header"] * 12
    else:
        for index in (0, 6):
            rows[0][index] = str(int(rows[0][index]) + 3600 * 1_000_000)
    with pytest.raises(ArchiveError, match="CSV row 1"):
        parse_archive(REQUEST, archive_download(REQUEST, rows), market_id=1)


@pytest.mark.parametrize("kind", ["missing", "duplicate", "wrong_month", "reordered"])
def test_grid_diagnostics(archive_rows, archive_download, kind):
    rows = archive_rows(REQUEST)
    missing = REQUEST.grid[1].isoformat()
    if kind == "missing":
        rows.pop(1)
    elif kind == "duplicate":
        rows[1] = rows[0][:]
    elif kind == "wrong_month":
        for index in (0, 6):
            rows[0][index] = str(int(rows[0][index]) - 14400 * 1_000_000)
    else:
        rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(ArchiveError) as error:
        parse_archive(REQUEST, archive_download(REQUEST, rows), market_id=1)
    details = error.value.details
    if kind in ("missing", "duplicate"):
        assert details["missing_intervals"] == [missing]
    if kind == "duplicate":
        assert details["duplicate_intervals"] == [REQUEST.grid[0].isoformat()]
    if kind == "wrong_month":
        assert len(details["unexpected_intervals"]) == 1
    if kind == "reordered":
        assert not details["chronological"]


@pytest.mark.parametrize(
    "kind", ["mismatch", "malformed", "wrong_filename", "provenance"]
)
def test_checksum_failures_before_zip(archive_download, monkeypatch, kind):
    download = archive_download(REQUEST)
    if kind == "mismatch":
        download = replace(download, body=b"changed body")
    elif kind == "malformed":
        download = replace(download, checksum=b"not a checksum")
    elif kind == "wrong_filename":
        download = replace(
            download, checksum=download.checksum.replace(b"BTCUSDT", b"ETHUSDT")
        )
    else:
        download = replace(download, sha256="a" * 64)
    monkeypatch.setattr(
        archives, "ZipFile", lambda *a: pytest.fail("Checksum must precede ZIP parsing")
    )
    with pytest.raises(ArchiveError):
        parse_archive(REQUEST, download, market_id=1)


@pytest.mark.parametrize(
    "kind", ["corrupt", "member", "compressed_limit", "uncompressed_limit", "rows"]
)
def test_archive_limits_and_structure(
    archive_download, archive_rows, monkeypatch, kind
):
    download = archive_download(REQUEST)
    if kind == "corrupt":
        download = archive_download(REQUEST, body=b"not a zip")
    elif kind == "member":
        download = archive_download(REQUEST, member="../unexpected.csv")
    elif kind == "compressed_limit":
        monkeypatch.setattr(archives, "MAX_ZIP_BYTES", len(download.body) - 1)
    elif kind == "uncompressed_limit":
        monkeypatch.setattr(archives, "MAX_CSV_BYTES", 100)
    else:
        download = archive_download(REQUEST, archive_rows(REQUEST) * 5)
    with pytest.raises(ArchiveError):
        parse_archive(REQUEST, download, market_id=1)


def response(body, headers=None):
    mock = MagicMock()
    mock.status = 200
    mock.headers = headers or {}
    mock.read1.side_effect = io.BytesIO(body).read1
    mock.__enter__.return_value = mock
    return mock


def test_download_checksum_and_response_received_time(monkeypatch, archive_download):
    download = archive_download(REQUEST)
    calls = []

    def fetch(url, limit):
        calls.append(url)
        return download.checksum if url.endswith(".CHECKSUM") else download.body

    monkeypatch.setattr(archives, "_fetch", fetch)
    before = datetime.now(UTC)
    result = archives.download_archive(REQUEST)
    assert before <= result.observed_at <= datetime.now(UTC)
    assert result.sha256 == download.sha256
    assert calls == [REQUEST.url, REQUEST.url + ".CHECKSUM"]


@pytest.mark.parametrize(
    "kind,attempts", [("timeout", 3), ("url", 3), ("404", 1), ("503", 3)]
)
def test_network_errors_bounded_and_redacted(monkeypatch, kind, attempts):
    opener = MagicMock()
    error = TimeoutError("secret") if kind == "timeout" else URLError("secret")
    if kind.isdecimal():
        error = HTTPError(REQUEST.url, int(kind), "secret", {}, None)
    opener.open.side_effect = error
    monkeypatch.setattr(archives, "build_opener", lambda *a: opener)
    monkeypatch.setattr(archives.time, "sleep", lambda _: None)
    with pytest.raises(ArchiveError) as caught:
        archives._fetch(REQUEST.url, 100)
    assert "secret" not in str(caught.value)
    assert opener.open.call_count == attempts
    assert opener.open.call_args.kwargs["timeout"] == 15


@pytest.mark.parametrize("headers", [{}, {"Content-Length": "101"}])
def test_http_size_limits(monkeypatch, headers):
    opener = MagicMock()
    opener.open.return_value = response(b"x" * 101, headers)
    monkeypatch.setattr(archives, "build_opener", lambda *a: opener)
    with pytest.raises(ArchiveError, match="size limit"):
        archives._fetch(REQUEST.url, 100)
    assert opener.open.call_count == 1


def test_retry_success_and_truncated_body(monkeypatch):
    opener = MagicMock()
    opener.open.side_effect = [TimeoutError(), response(b"ok", {"Content-Length": "2"})]
    monkeypatch.setattr(archives, "build_opener", lambda *a: opener)
    monkeypatch.setattr(archives.time, "sleep", lambda _: None)
    assert archives._fetch(REQUEST.url, 100) == b"ok"
    opener.open.side_effect = None
    opener.open.return_value = response(b"short", {"Content-Length": "10"})
    with pytest.raises(ArchiveError, match="Incomplete"):
        archives._fetch(REQUEST.url, 100)

"""Fabricated source bytes only: no strategy, real archives, artifacts or DB."""

import builtins
import io
import json
import socket
import struct
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Inexact, localcontext
from pathlib import Path
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError
from zipfile import ZIP_BZIP2, ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

import psycopg
import pytest

from backtest_badger import archives, candles
from backtest_badger import minute_execution_data as minute

OBSERVED = datetime(2026, 10, 17, tzinfo=UTC)
JAN = minute.MinuteRequest("BTCUSDT", "2024-01")
PRICE = "100.123456789012345678901234567890123456789"


@pytest.fixture(autouse=True)
def forbid_external_access(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Real network/database access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(psycopg, "connect", forbidden)
    original_io, original_builtin = io.open, builtins.open

    def guarded(original):
        def open_file(file, *args, **kwargs):
            if not isinstance(file, int):
                path = Path(file).absolute()
                assert "artifacts" not in path.parts
                assert "crypto-trading-platform" not in path.parts
            return original(file, *args, **kwargs)

        return open_file

    monkeypatch.setattr(io, "open", guarded(original_io))
    monkeypatch.setattr(builtins, "open", guarded(original_builtin))


def row(stamp):
    return [
        str(stamp),
        PRICE,
        "110",
        "90",
        "105",
        "12.50",
        str(stamp + 59_999),
        "1250.00",
        "123",
        "6.25",
        "625.00",
        "0",
    ]


def packed(request, content, *, names=None, compression=ZIP_DEFLATED):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name in names or [request.stem + ".csv"]:
            info = ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
            info.compress_type = compression
            archive.writestr(info, content)
    body = buffer.getvalue()
    checksum = f"{minute._sha(body)}  {request.stem}.zip\n".encode()
    return body, checksum, OBSERVED


def synthetic_download(request, observed=OBSERVED):
    # One month at a time; no cache of all 24 raw sources or million row objects.
    start = request.start_ms
    content = io.BytesIO()
    for i in range(request.row_count):
        content.write((",".join(row(start + 60_000 * i)) + "\n").encode())
    body, checksum, _ = packed(request, content.getvalue())
    return body, checksum, observed


def verify(request, download):
    return minute.verify_minute_archive(request, *download)


def test_fixed_plan_and_hourly_isolation(candle_observation):
    requests = minute.minute_requests()
    assert len(requests) == len({r.url for r in requests}) == 24
    assert [(r.symbol, r.month) for r in requests] == [
        (s, f"2024-{m:02d}") for s in ("BTCUSDT", "ETHUSDT") for m in range(1, 13)
    ]
    for symbol in minute.SYMBOLS:
        assert sum(r.row_count for r in requests if r.symbol == symbol) == 527_040
    assert sum(r.row_count for r in requests) == 1_054_080
    assert minute.MinuteRequest("ETHUSDT", "2024-02").row_count == 41_760
    assert minute.coverage()["total_rows"] == 1_054_080
    for request in requests:
        assert request.url == (
            "https://data.binance.vision/data/spot/monthly/klines/"
            f"{request.symbol}/1m/{request.symbol}-1m-{request.month}.zip"
        )
        assert request.checksum_url == request.url + ".CHECKSUM"
        hourly = archives.ArchiveRequest(request.symbol, "1h", request.month)
        assert request.url != hourly.url and request.stem != hourly.stem
    assert (archives.MAX_ROWS, archives.MAX_ZIP_BYTES, archives.MAX_CSV_BYTES) == (
        744,
        2 * 1024**2,
        8 * 1024**2,
    )
    with pytest.raises(ValueError):
        archives.ArchiveRequest("BTCUSDT", "1m", "2024-01")
    with pytest.raises(ValueError):
        candles.validate_observation(replace(candle_observation, interval_seconds=60))


@pytest.mark.parametrize(
    "symbol,month",
    [
        ("BTCUSDT", "2025-01"),
        ("ETHUSDT", "2023-12"),
        ("BTCUSDT", "2024-13"),
        ("BTCUSDT", "2024-00"),
        ("BTCUSDT", "2024-1"),
        ("XRPUSDT", "2024-01"),
        ("../BTCUSDT", "2024-01"),
        ("BTCUSDT", None),
    ],
)
def test_outside_fixed_plan(symbol, month):
    with pytest.raises(minute.MinuteDataError):
        minute.MinuteRequest(symbol, month)


@pytest.mark.parametrize("month,count", [("01", 44640), ("02", 41760), ("12", 44640)])
def test_complete_months_and_year_boundary(month, count):
    request = minute.MinuteRequest("ETHUSDT", f"2024-{month}")
    download = synthetic_download(request)
    fragment, source = verify(request, download)
    lines = fragment.splitlines()
    assert len(lines) == count
    assert lines[0].decode() == (
        f"ETHUSDT,{request.start_ms},{PRICE},{minute._sha(download[0])}"
    )
    assert int(lines[-1].split(b",")[1]) == request.start_ms + (count - 1) * 60_000
    assert source["sha256"] == minute._sha(download[0])
    assert source["checksum_sha256"] == minute._sha(download[1])
    assert source["row_count"] == count
    assert source["observed_at"] == OBSERVED.isoformat()
    assert source["observation_kind"] == "retrospective_full_archive_acquisition"
    assert source["validation_status"] == "complete_checksum_and_native_grid"
    assert not any(k in source for k in ("bid", "ask", "fill", "available_at"))
    if month == "12":
        assert request.start_ms + count * 60_000 == 1735689600000


@pytest.mark.parametrize(
    "column,value",
    [
        (0, "1704067200000000"),
        (0, "9999999999999999999999999999999999999"),
        (0, "1704067200001"),
        (0, "1704067260000"),
        (0, "1704067140000"),
        (6, "1704067260000"),
        (6, "1704067259998"),
        (6, "1704067259999000"),
        (1, "0"),
        (1, "-1"),
        (1, "NaN"),
        (1, "Infinity"),
        (1, "1e999999999"),
        (1, "+100"),
        (1, " 100"),
        (1, "100_000"),
        (1, ".1"),
        (1, "1."),
        (1, "9" * 81),
        (2, "99"),
        (3, "106"),
        (3, "0"),
        (4, "111"),
        (4, "0"),
        (5, "-0"),
        (5, "-1"),
        (5, "NaN"),
        (7, "Infinity"),
        (8, "-1"),
        (8, "1.1"),
        (8, "1e2"),
        (8, str(2**63)),
        (9, "12.51"),
        (9, "-1"),
        (10, "1251"),
        (10, "NaN"),
        (11, "ignored"),
        (11, "-1"),
        (11, "Infinity"),
    ],
)
def test_strict_native_row_formats(column, value):
    data = row(JAN.start_ms)
    data[column] = value
    with pytest.raises(minute.MinuteDataError) as error:
        minute._parse_row(data, JAN.start_ms)
    assert value not in str(error.value) or value in ("0", "1.")


@pytest.mark.parametrize("count", [0, 11, 13])
def test_wrong_field_counts(count):
    with pytest.raises(minute.MinuteDataError):
        minute._parse_row(["0"] * count, JAN.start_ms)


def test_decimal_context_independence_and_zero_volumes():
    data = row(JAN.start_ms)
    for i in (5, 7, 8, 9, 10, 11):
        data[i] = "0"
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        assert minute._parse_row(data, JAN.start_ms) == PRICE


@pytest.mark.parametrize(
    "kind", ["duplicate", "missing", "reordered", "wrong_month", "empty", "short"]
)
def test_strict_grid_small_rejections(kind):
    stamps = [JAN.start_ms, JAN.start_ms + 60_000, JAN.start_ms + 120_000]
    if kind == "duplicate":
        stamps[1] = stamps[0]
    elif kind == "missing":
        stamps.pop(1)
    elif kind == "reordered":
        stamps[0], stamps[1] = stamps[1], stamps[0]
    elif kind == "wrong_month":
        stamps[0] -= 60_000
    elif kind == "empty":
        stamps = []
    content = "\n".join(",".join(row(s)) for s in stamps).encode()
    with pytest.raises(minute.MinuteDataError):
        verify(JAN, packed(JAN, content))


def test_extra_row_and_missing_final_row():
    request = minute.MinuteRequest("BTCUSDT", "2024-02")
    content = b"".join(
        (",".join(row(request.start_ms + i * 60_000)) + "\n").encode()
        for i in range(request.row_count + 1)
    )
    with pytest.raises(minute.MinuteDataError, match="Extra"):
        verify(request, packed(request, content))
    with pytest.raises(minute.MinuteDataError, match="Missing"):
        verify(request, packed(request, b"\n".join(content.splitlines()[:-2]) + b"\n"))


@pytest.mark.parametrize(
    "kind",
    [
        "wrong_hash",
        "wrong_name",
        "extra_line",
        "prefix_path",
        "utf8",
        "empty",
        "oversize",
    ],
)
def test_checksum_rejection_before_zip(kind, monkeypatch):
    body, checksum, observed = packed(JAN, b"invalid")
    if kind == "wrong_hash":
        checksum = b"0" * 64 + checksum[64:]
    elif kind == "wrong_name":
        checksum = checksum.replace(b"BTCUSDT", b"ETHUSDT")
    elif kind == "extra_line":
        checksum *= 2
    elif kind == "prefix_path":
        checksum = checksum.replace(b"  BTC", b"  ../BTC")
    elif kind == "utf8":
        checksum += b"\xff"
    elif kind == "empty":
        checksum = b""
    else:
        checksum = b"x" * (minute.MAX_CHECKSUM_BYTES + 1)
    monkeypatch.setattr(
        minute, "ZipFile", lambda *a: pytest.fail("Must verify hash first")
    )
    with pytest.raises(minute.MinuteDataError):
        minute.verify_minute_archive(JAN, body, checksum, observed)


@pytest.mark.parametrize("suffix", [b"", b"\n", b"\r\n"])
def test_checksum_standard_variants(suffix):
    body, checksum, observed = packed(JAN, b"invalid")
    checksum = checksum[:64].upper() + b" *" + (JAN.stem + ".zip").encode() + suffix
    # Reaching row validation proves this standard sidecar form was accepted.
    with pytest.raises(minute.MinuteDataError, match="twelve"):
        minute.verify_minute_archive(JAN, body, checksum, observed)


@pytest.mark.parametrize(
    "name",
    [
        "../escape.csv",
        "/absolute.csv",
        "nested/x.csv",
        "other.csv",
        "x.txt",
        "ETHUSDT-1m-2024-01.csv",
    ],
)
def test_unexpected_member_names(name):
    with pytest.raises(minute.MinuteDataError, match="member"):
        verify(JAN, packed(JAN, b"content", names=[name]))


def test_duplicate_entries_before_zip_allocation(monkeypatch):
    with pytest.warns(UserWarning):
        download = packed(JAN, b"content", names=[JAN.stem + ".csv"] * 2)
    monkeypatch.setattr(
        minute, "ZipFile", lambda *a: pytest.fail("Do not allocate entry list")
    )
    with pytest.raises(minute.MinuteDataError, match="directory"):
        verify(JAN, download)


@pytest.mark.parametrize(
    "kind",
    [
        "truncated",
        "not_zip",
        "trailer",
        "bzip",
        "symlink",
        "crc",
        "encrypted",
        "split",
        "zip64",
    ],
)
def test_bad_zip_structure(kind):
    body, _, observed = packed(
        JAN, (",".join(row(JAN.start_ms)) + "\n").encode(), compression=ZIP_STORED
    )
    if kind == "truncated":
        body = body[:-8]
    elif kind == "not_zip":
        body = b"not a zip"
    elif kind == "trailer":
        body += b"trailing bytes"
    elif kind == "bzip":
        body = packed(JAN, b"content", compression=ZIP_BZIP2)[0]
    else:
        body = bytearray(body)
        central = body.index(b"PK\x01\x02")
        if kind == "symlink":
            struct.pack_into("<L", body, central + 38, 0o120777 << 16)
        elif kind == "crc":
            body[30 + len(JAN.stem + ".csv")] ^= 1
        elif kind == "encrypted":
            struct.pack_into("<H", body, central + 8, 1)
        elif kind == "split":
            struct.pack_into("<H", body, len(body) - 18, 1)
        else:
            struct.pack_into("<H", body, len(body) - 12, 65535)
        body = bytes(body)
    checksum = f"{minute._sha(body)}  {JAN.stem}.zip\n".encode()
    with pytest.raises(minute.MinuteDataError):
        minute.verify_minute_archive(JAN, body, checksum, observed)


@pytest.mark.parametrize(
    "content", [b"\xff", b"\xef\xbb\xbf1,2", b'"unterminated', b"x" * 2049, b"\x00"]
)
def test_invalid_encoding_syntax_and_line_limit(content):
    with pytest.raises(minute.MinuteDataError):
        verify(JAN, packed(JAN, content))


@pytest.mark.parametrize(
    "limit", ["MAX_ZIP_BYTES", "MAX_CSV_BYTES", "MAX_RATIO", "MAX_ROWS"]
)
def test_resource_caps(limit, monkeypatch):
    download = packed(JAN, (",".join(row(JAN.start_ms)) + "\n").encode())
    monkeypatch.setattr(minute, limit, 0 if limit == "MAX_ROWS" else 1)
    with pytest.raises(minute.MinuteDataError):
        verify(JAN, download)


def test_real_expansion_bomb_rejected():
    download = packed(JAN, b"0" * 1024 * 1024)
    with pytest.raises(minute.MinuteDataError, match="ratio"):
        verify(JAN, download)


@pytest.mark.parametrize(
    "observed",
    [
        datetime(2026, 1, 1),
        datetime(2024, 1, 31, tzinfo=UTC),
        None,
        datetime.fromisoformat("2026-01-01T00:00:00+01:00"),
    ],
)
def test_bad_observation_times(observed):
    body, checksum, _ = packed(JAN, b"content")
    with pytest.raises(minute.MinuteDataError, match="Acquisition|acquisition"):
        minute.verify_minute_archive(JAN, body, checksum, observed)


@pytest.fixture(scope="module")
def published(tmp_path_factory):
    root = tmp_path_factory.mktemp("minute-synthetic")
    a, b = root / "a", root / "b"
    # Deny sockets explicitly, independent of module/function fixture order.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            socket.socket, "connect", lambda *a: pytest.fail("Network forbidden")
        )
        write = minute._write_exclusive
        replay = minute._verify_retained
        verified = set()

        def check_replay(directory, manifest):
            assert not (directory / "manifest.json").exists()
            replay(directory, manifest)
            verified.add(directory)

        def check_last(path, body):
            if path.name == "manifest.json":
                assert path.parent in verified
                assert len(list((path.parent / "raw").iterdir())) == 48
                assert (path.parent / "minute_opens.csv").is_file()
            write(path, body)

        patch.setattr(minute, "_verify_retained", check_replay)
        patch.setattr(minute, "_write_exclusive", check_last)
        failed = root / "failed-before-recovery"
        with pytest.raises(minute.MinuteDataError):
            minute.prepare_minute_execution_data(
                failed, downloader=lambda r: packed(r, b"invalid fixture")
            )
        assert not (failed / "manifest.json").exists()
        with pytest.raises(FileExistsError):
            minute.prepare_minute_execution_data(failed, downloader=synthetic_download)
        # Both successful publications recover only into distinct NEW directories.
        first = minute.prepare_minute_execution_data(a, downloader=synthetic_download)
        second = minute.prepare_minute_execution_data(
            b, downloader=lambda r: synthetic_download(r, OBSERVED + timedelta(days=1))
        )
    return a, b, first, second


def test_full_year_publication_reproduction_and_offline_verification(published):
    a, b, first, second = published
    assert first != second  # Retrospective acquisition wall clock is separate metadata.
    with (
        (a / "minute_opens.csv").open("rb") as left,
        (b / "minute_opens.csv").open("rb") as right,
    ):
        while chunk := left.read(65536):
            assert right.read(len(chunk)) == chunk
        assert not right.read(1)
    meta = minute.load_minute_execution_data(a, expected_manifest_sha256=first)
    assert meta["coverage"]["total_rows"] == 1_054_080
    assert len(meta["sources"]) == 24
    assert len(list((a / "raw").iterdir())) == 48
    for request in minute.minute_requests():
        for suffix in (".zip", ".zip.CHECKSUM"):
            assert (a / "raw" / (request.stem + suffix)).read_bytes() == (
                b / "raw" / (request.stem + suffix)
            ).read_bytes()
    bmeta = json.loads((b / "manifest.json").read_bytes())
    for source in bmeta["sources"]:
        source["observed_at"] = OBSERVED.isoformat()
    assert minute._json(bmeta) == (a / "manifest.json").read_bytes()
    assert (
        "high" not in minute.HEADER.decode() and "close" not in minute.HEADER.decode()
    )


@pytest.mark.parametrize("existing", ["empty", "file", "symlink", "published"])
def test_exclusive_destination(existing, tmp_path, published):
    destination = tmp_path / "existing"
    if existing == "empty":
        destination.mkdir()
    elif existing == "file":
        destination.write_bytes(b"unchanged")
    elif existing == "symlink":
        destination.symlink_to(published[0], target_is_directory=True)
    else:
        destination = published[0]
    with pytest.raises(FileExistsError):
        minute.prepare_minute_execution_data(
            destination, downloader=lambda *a: pytest.fail("No download")
        )


@pytest.mark.parametrize(
    "target",
    ["zip", "sidecar", "processed", "manifest", "missing", "failure", "symlink"],
)
def test_tampered_publication_rejected_and_restored(target, published):
    directory, _, pin, _ = published
    paths = {
        "zip": directory / "raw" / (JAN.stem + ".zip"),
        "sidecar": directory / "raw" / (JAN.stem + ".zip.CHECKSUM"),
        "processed": directory / "minute_opens.csv",
        "manifest": directory / "manifest.json",
        "missing": directory / "raw" / (JAN.stem + ".zip"),
        "failure": directory / "failure.json",
        "symlink": directory / "raw" / (JAN.stem + ".zip"),
    }
    path = paths[target]
    # Mutate only the first byte of the large processed file, keeping memory bounded.
    if target == "processed":
        with path.open("r+b") as stream:
            old = stream.read(1)
            stream.seek(0)
            stream.write(b"X")
        try:
            with pytest.raises(minute.MinuteDataError):
                minute.load_minute_execution_data(
                    directory, expected_manifest_sha256=pin
                )
        finally:
            with path.open("r+b") as stream:
                stream.write(old)
        return
    old = path.read_bytes() if path.exists() else None
    try:
        if target in ("missing", "symlink"):
            path.unlink()
            if target == "symlink":
                path.symlink_to(directory / "manifest.json")
        else:
            path.write_bytes(b"tampered")
        with pytest.raises(minute.MinuteDataError):
            minute.load_minute_execution_data(directory, expected_manifest_sha256=pin)
    finally:
        path.unlink(missing_ok=True)
        if old is not None:
            path.write_bytes(old)


@pytest.mark.parametrize(
    "kind",
    [
        "source_symbol",
        "source_month",
        "source_hash",
        "source_count",
        "source_time",
        "source_status",
        "coverage",
        "implementation",
        "output_hash",
        "source_order",
    ],
)
def test_rehashed_metadata_cannot_bypass_replay(kind, published):
    directory, _, _, _ = published
    path = directory / "manifest.json"
    original = path.read_bytes()
    meta = json.loads(original)
    if kind.startswith("source_") and kind != "source_order":
        field = {
            "symbol": "symbol",
            "month": "month",
            "hash": "sha256",
            "count": "row_count",
            "time": "observed_at",
            "status": "validation_status",
        }[kind[7:]]
        meta["sources"][0][field] = "tampered"
    elif kind == "source_order":
        meta["sources"][0], meta["sources"][1] = meta["sources"][1], meta["sources"][0]
    elif kind == "coverage":
        meta["coverage"]["total_rows"] -= 1
    elif kind == "implementation":
        meta["implementation_sha256"] = "0" * 64
    else:
        meta["output"]["sha256"] = "0" * 64
    body = minute._json(meta)
    try:
        path.write_bytes(body)
        with pytest.raises(minute.MinuteDataError):
            minute.load_minute_execution_data(
                directory, expected_manifest_sha256=minute._sha(body)
            )
    finally:
        path.write_bytes(original)


def test_rehashed_processed_price_still_requires_native_evidence(published):
    directory, _, _, _ = published
    path = directory / "minute_opens.csv"
    manifest_path = directory / "manifest.json"
    original_manifest = manifest_path.read_bytes()
    offset = len(minute.HEADER) + len("BTCUSDT,1704067200000,")
    with path.open("r+b") as stream:
        stream.seek(offset)
        original = stream.read(1)
        stream.seek(offset)
        stream.write(b"9")
    try:
        digest = minute.hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(65536):
                digest.update(chunk)
        meta = json.loads(original_manifest)
        meta["output"]["sha256"] = digest.hexdigest()
        body = minute._json(meta)
        manifest_path.write_bytes(body)
        with pytest.raises(minute.MinuteDataError, match="retained native"):
            minute.load_minute_execution_data(
                directory, expected_manifest_sha256=minute._sha(body)
            )
    finally:
        with path.open("r+b") as stream:
            stream.seek(offset)
            stream.write(original)
        manifest_path.write_bytes(original_manifest)


def test_failure_download_retains_evidence_and_never_resumes(tmp_path):
    calls = []

    def interrupted(request):
        calls.append(request)
        if len(calls) == 2:
            raise OSError("private error")
        return synthetic_download(request)

    destination = tmp_path / "failed"
    with pytest.raises(OSError):
        minute.prepare_minute_execution_data(destination, downloader=interrupted)
    assert len(calls) == 2
    assert not (destination / "manifest.json").exists()
    failure = json.loads((destination / "failure.json").read_bytes())
    assert len(failure["validated_sources"]) == 1
    assert failure["resume"] is False
    assert "private error" not in (destination / "failure.json").read_text()
    with pytest.raises(FileExistsError):
        minute.prepare_minute_execution_data(destination, downloader=interrupted)
    # Recovery invokes the same strict acquisition contract only at a NEW destination.
    with pytest.raises(minute.MinuteDataError):
        minute.prepare_minute_execution_data(
            tmp_path / "fresh", downloader=lambda r: packed(r, b"bad")
        )
    assert (tmp_path / "fresh" / "failure.json").is_file()


@pytest.mark.parametrize(
    "phase", ["raw", "processed", "before_manifest", "after_manifest"]
)
def test_interrupted_write_no_valid_manifest(phase, tmp_path, monkeypatch, published):
    # Full real parser/publisher success is exercised above. Fault injection reuses
    # verified synthetic bytes but avoids another full-year reconstruction per fault.
    directory, _, _, _ = published
    actual_write = minute._write_exclusive
    actual_link = minute.os.link

    def write(path, body):
        if phase == "raw" and path.suffix == ".zip":
            raise OSError("write failed")
        if path.name == "manifest.json":
            if phase == "before_manifest":
                raise KeyboardInterrupt
            actual_write(path, body)
            if phase == "after_manifest":
                raise KeyboardInterrupt
        else:
            actual_write(path, body)

    def link(source, target):
        if phase == "processed" and Path(target).name == "minute_opens.csv":
            raise OSError("write failed")
        actual_link(source, target)

    monkeypatch.setattr(minute, "_write_exclusive", write)
    monkeypatch.setattr(minute.os, "link", link)
    if phase in ("before_manifest", "after_manifest", "processed"):
        meta = json.loads((directory / "manifest.json").read_bytes())
        monkeypatch.setattr(
            minute,
            "verify_minute_archive",
            lambda r, *a: (b"fixture\n", meta["sources"][0]),
        )
        monkeypatch.setattr(minute, "_verify_retained", lambda *a: None)
    destination = tmp_path / phase
    with pytest.raises((OSError, KeyboardInterrupt)):
        minute.prepare_minute_execution_data(
            destination, downloader=lambda r: packed(r, b"fixture")
        )
    assert not (destination / "manifest.json").exists()
    assert (destination / "failure.json").is_file()


def response(body, *, headers=None, url=JAN.url, status=200):
    mock = MagicMock()
    mock.status = status
    mock.headers = headers or {}
    mock.geturl.return_value = url
    mock.read1.side_effect = io.BytesIO(body).read1
    mock.__enter__.return_value = mock
    return mock


@pytest.mark.parametrize(
    "url",
    [
        "http://data.binance.vision/x",
        JAN.url + "?token=secret",
        "https://evil.invalid/",
        JAN.url.replace("2024", "2025"),
    ],
)
def test_fetch_allowlist_before_network(url, monkeypatch):
    monkeypatch.setattr(
        minute, "build_opener", lambda *a: pytest.fail("No HTTP opener")
    )
    with pytest.raises(minute.MinuteDataError, match="fixed plan"):
        minute._fetch(url, minute.MAX_ZIP_BYTES)


@pytest.mark.parametrize(
    "kind,attempts", [("timeout", 3), ("url", 3), ("503", 3), ("404", 1), ("302", 1)]
)
def test_mock_http_bounded_retries_safe_errors(kind, attempts, monkeypatch):
    opener = MagicMock()
    if kind == "timeout":
        error = TimeoutError("private")
    elif kind == "url":
        error = URLError("private")
    else:
        error = HTTPError(JAN.url, int(kind), "private", {}, None)
    opener.open.side_effect = error
    monkeypatch.setattr(minute, "build_opener", lambda *a: opener)
    sleeps = []
    monkeypatch.setattr(minute.time, "sleep", sleeps.append)
    with pytest.raises(minute.MinuteDataError) as caught:
        minute._fetch(JAN.url, minute.MAX_ZIP_BYTES)
    assert "private" not in str(caught.value)
    assert opener.open.call_count == attempts
    assert opener.open.call_args.kwargs["timeout"] == 15
    assert sleeps == ([1, 2] if attempts == 3 else [])
    assert (
        minute._NoRedirect().redirect_request(None, None, 302, "", {}, JAN.url) is None
    )


@pytest.mark.parametrize(
    "case",
    [
        "length",
        "truncated",
        "redirect",
        "status",
        "empty",
        "bad_length",
        "stream_size",
        "deadline",
    ],
)
def test_mock_http_limits(case, monkeypatch):
    limit = minute.MAX_CHECKSUM_BYTES
    url = JAN.checksum_url
    value = response(b"ok", url=url)
    if case == "length":
        value.headers = {"Content-Length": str(limit + 1)}
    elif case == "truncated":
        value.headers = {"Content-Length": "10"}
    elif case == "redirect":
        value.geturl.return_value = "https://evil.invalid/"
    elif case == "status":
        value.status = 206
    elif case == "empty":
        value = response(b"", url=url)
    elif case == "bad_length":
        value.headers = {"Content-Length": "garbage"}
    elif case == "stream_size":
        value = response(b"a" * (limit + 1), url=url)
    elif case == "deadline":
        clock = iter([0, 61, 100, 161, 200, 261])
        monkeypatch.setattr(minute.time, "monotonic", lambda: next(clock))
    opener = MagicMock()
    opener.open.return_value = value
    monkeypatch.setattr(minute, "build_opener", lambda *a: opener)
    monkeypatch.setattr(minute.time, "sleep", lambda *a: None)
    with pytest.raises(minute.MinuteDataError):
        minute._fetch(url, limit)


def test_download_utility_only_with_mock_transport(monkeypatch):
    bodies = []
    before = datetime.now(UTC)

    def fetch(url, limit):
        bodies.append((url, limit))
        return b"sidecar" if url.endswith("CHECKSUM") else b"zip"

    monkeypatch.setattr(minute, "_fetch", fetch)
    body, checksum, observed = minute.download_minute_archive(JAN)
    assert (body, checksum) == (b"zip", b"sidecar")
    assert before <= observed <= datetime.now(UTC)
    assert bodies == [
        (JAN.url, minute.MAX_ZIP_BYTES),
        (JAN.checksum_url, minute.MAX_CHECKSUM_BYTES),
    ]


def test_no_default_downloader(tmp_path):
    with pytest.raises(TypeError):
        minute.prepare_minute_execution_data(tmp_path / "not-created")
    assert not (tmp_path / "not-created").exists()


def test_source_validation_failure_preserves_original_pair_and_timestamp(tmp_path):
    download = packed(JAN, b"malformed native row")
    destination = tmp_path / "bad-source"
    with pytest.raises(minute.MinuteDataError):
        minute.prepare_minute_execution_data(destination, downloader=lambda r: download)
    assert (destination / "raw" / (JAN.stem + ".zip")).read_bytes() == download[0]
    assert (
        destination / "raw" / (JAN.stem + ".zip.CHECKSUM")
    ).read_bytes() == download[1]
    failure = json.loads((destination / "failure.json").read_bytes())
    assert failure["current_source"] == JAN.stem
    assert failure["current_download"] == {
        "sha256": minute._sha(download[0]),
        "checksum_sha256": minute._sha(download[1]),
        "observed_at": OBSERVED.isoformat(),
    }
    assert failure["validated_sources"] == []
    assert not (destination / "manifest.json").exists()


def test_deflate_decompression_error_is_safe():
    body, _, observed = packed(JAN, b"0" * 100)
    body = bytearray(body)
    payload_offset = 30 + len(JAN.stem + ".csv")
    body[payload_offset] = 0x07  # Reserved DEFLATE block type.
    body = bytes(body)
    checksum = f"{minute._sha(body)}  {JAN.stem}.zip\n".encode()
    with pytest.raises(minute.MinuteDataError, match="Corrupt"):
        minute.verify_minute_archive(JAN, body, checksum, observed)


def test_manifest_pin_required_and_revision_not_silently_accepted(published):
    directory, _, pin, _ = published
    with pytest.raises(TypeError):
        minute.load_minute_execution_data(directory)
    with pytest.raises(minute.MinuteDataError, match="pin mismatch"):
        minute.load_minute_execution_data(directory, expected_manifest_sha256="0" * 64)
    assert pin != "0" * 64


def test_mock_http_retry_then_success_and_no_proxies(monkeypatch):
    opener = MagicMock()
    opener.open.side_effect = [
        TimeoutError(),
        response(b"ok", headers={"Content-Length": "2"}),
    ]
    handlers = []

    def build(*args):
        handlers.extend(args)
        return opener

    monkeypatch.setattr(minute, "build_opener", build)
    monkeypatch.setattr(minute.time, "sleep", lambda *a: None)
    assert minute._fetch(JAN.url, minute.MAX_ZIP_BYTES) == b"ok"
    assert opener.open.call_count == 2
    assert all(h.proxies == {} for h in handlers if isinstance(h, minute.ProxyHandler))


@pytest.mark.parametrize("field", ["row_count", "output_bytes", "coverage_interval"])
def test_rehashed_float_metadata_does_not_alias_integer_contract(field, published):
    directory, _, _, _ = published
    path = directory / "manifest.json"
    original = path.read_bytes()
    meta = json.loads(original)
    if field == "row_count":
        meta["sources"][0]["row_count"] = float(meta["sources"][0]["row_count"])
    elif field == "output_bytes":
        meta["output"]["bytes"] = float(meta["output"]["bytes"])
    else:
        meta["coverage"]["interval_seconds"] = 60.0
    body = minute._json(meta)
    try:
        path.write_bytes(body)
        with pytest.raises(minute.MinuteDataError):
            minute.load_minute_execution_data(
                directory, expected_manifest_sha256=minute._sha(body)
            )
    finally:
        path.write_bytes(original)


def test_small_zip64_member_rejected_even_with_zip32_directory():
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        with archive.open(JAN.stem + ".csv", "w", force_zip64=True) as stream:
            stream.write((",".join(row(JAN.start_ms)) + "\n").encode())
    body = buffer.getvalue()
    checksum = f"{minute._sha(body)}  {JAN.stem}.zip\n".encode()
    with pytest.raises(minute.MinuteDataError, match="unsupported ZIP member"):
        minute.verify_minute_archive(JAN, body, checksum, OBSERVED)

"""Isolated native-1m source engineering, not an approved execution scenario.

Stage 4B.2C exercises these APIs ONLY with fabricated bytes in temporary roots.
Actual acquisition requires separate owner approval; no CLI/default downloader.
"""

import calendar
import csv
import hashlib
import io
import json
import os
import re
import stat
import struct
import time
import zlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile

VERSION = "binance-1m-2024-v1"
FORMAT = "minute-opens-csv-v1"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
START = datetime(2024, 1, 1, tzinfo=UTC)
END = datetime(2025, 1, 1, tzinfo=UTC)
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
MAX_ZIP_BYTES = 16 * 1024 * 1024
MAX_CSV_BYTES = 32 * 1024 * 1024
MAX_CHECKSUM_BYTES = 1024
MAX_METADATA_BYTES = 128 * 1024
MAX_LINE_BYTES = 2048
MAX_ROWS = 44_640
MAX_RATIO = 200
HEADER = b"symbol,open_time_ms,open,source_sha256\n"


class MinuteDataError(ValueError):
    """Safe errors: never include source rows, URLs supplied by callers or secrets."""


def _require(condition, message):
    if not condition:
        raise MinuteDataError(message)


def _sha(body):
    return hashlib.sha256(body).hexdigest()


def _json(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


@dataclass(frozen=True)
class MinuteRequest:
    symbol: str
    month: str

    def __post_init__(self):
        _require(
            self.symbol in SYMBOLS
            and isinstance(self.month, str)
            and re.fullmatch(r"2024-(0[1-9]|1[0-2])", self.month),
            "Expected one of the fixed 24 native minute source identities.",
        )

    @property
    def stem(self):
        return f"{self.symbol}-1m-{self.month}"

    @property
    def url(self):
        return (
            "https://data.binance.vision/data/spot/monthly/klines/"
            f"{self.symbol}/1m/{self.stem}.zip"
        )

    @property
    def checksum_url(self):
        return self.url + ".CHECKSUM"

    @property
    def row_count(self):
        return calendar.monthrange(2024, int(self.month[-2:]))[1] * 1440

    @property
    def start_ms(self):
        return (
            datetime(2024, int(self.month[-2:]), 1, tzinfo=UTC) - EPOCH
        ) // timedelta(milliseconds=1)


def minute_requests():
    """Fixed, ordered market/month plan; no discovery or network access."""
    return tuple(
        MinuteRequest(s, f"2024-{m:02d}") for s in SYMBOLS for m in range(1, 13)
    )


def coverage():
    return {
        "start": START.isoformat(),
        "end_exclusive": END.isoformat(),
        "interval_seconds": 60,
        "row_counts": {s: 527_040 for s in SYMBOLS},
        "total_rows": 1_054_080,
        "missing": 0,
        "complete": True,
    }


def _request(request):
    _require(type(request) is MinuteRequest, "Expected a minute source request.")
    # Revalidate even if a caller bypassed the frozen dataclass guard.
    request.__post_init__()


def _observed(request, observed_at):
    _require(
        isinstance(observed_at, datetime) and observed_at.utcoffset() == timedelta(0),
        "Acquisition time must be aware UTC.",
    )
    month_end = EPOCH + timedelta(
        milliseconds=request.start_ms + request.row_count * 60_000
    )
    _require(observed_at >= month_end, "Full archive acquisition predates month end.")
    return observed_at.isoformat()


def _bounded_bytes(body, limit):
    _require(
        type(body) is bytes and 0 < len(body) <= limit, "Invalid source byte size."
    )


def _decimal(text):
    # Native fixed-point ASCII only; no exponent expansion, whitespace or NaN.
    _require(
        len(text) <= 80 and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", text),
        "Invalid native decimal format.",
    )
    return Decimal(text)


def _parse_row(row, expected_ms):
    """Validate ALL native fields; return only the original exact opening string."""
    _require(len(row) == 12, "Expected twelve native CSV fields.")
    _require(
        re.fullmatch(r"[0-9]{13}", row[0])
        and re.fullmatch(r"[0-9]{13}", row[6])
        and int(row[0]) == expected_ms
        and int(row[6]) == expected_ms + 59_999,
        "Invalid ordered UTC minute grid or inclusive millisecond close.",
    )
    opened, high, low, close = (_decimal(row[i]) for i in (1, 2, 3, 4))
    _require(
        low > 0 and low <= opened <= high and low <= close <= high,
        "Invalid positive OHLC bounds.",
    )
    base, quote, taker_base, taker_quote, _ = (
        _decimal(row[i]) for i in (5, 7, 9, 10, 11)
    )
    _require(
        taker_base <= base and taker_quote <= quote, "Invalid taker volume bounds."
    )
    _require(
        re.fullmatch(r"[0-9]{1,19}", row[8]) and int(row[8]) <= 2**63 - 1,
        "Invalid nonnegative trade count.",
    )
    return row[1]


def _zip_directory(body):
    # Inspect bounded EOCD before ZipFile allocates a potentially huge entry list.
    # Native single-member ZIP32 only; no multi-disk, ZIP64, comments or trailers.
    _require(len(body) >= 22, "Truncated ZIP archive.")
    fields = struct.unpack("<4s4H2LH", body[-22:])
    signature, disk, cd_disk, disk_count, count, size, offset, comment = fields
    _require(
        signature == b"PK\x05\x06"
        and disk == cd_disk == comment == 0
        and disk_count == count == 1
        and offset + size == len(body) - 22
        and 46 <= size <= 4096,
        "Unsupported ZIP directory or entry count.",
    )


def verify_minute_archive(request, zip_bytes, checksum_bytes, observed_at):
    """Fully validate one month; return (opening-only CSV fragment, source dict).

    The fragment has no header. No partially validated records escape this call.
    Raw evidence preserves OHLCV; the processed fragment contains only opens.
    """
    _request(request)
    observed = _observed(request, observed_at)
    _bounded_bytes(zip_bytes, MAX_ZIP_BYTES)
    _bounded_bytes(checksum_bytes, MAX_CHECKSUM_BYTES)
    match = re.fullmatch(
        rb"([0-9a-fA-F]{64}) [ *]"
        + re.escape((request.stem + ".zip").encode())
        + rb"\r?\n?",
        checksum_bytes,
    )
    _require(match is not None, "Malformed checksum or unexpected sidecar filename.")
    digest = _sha(zip_bytes)
    _require(digest == match[1].decode().lower(), "Archive SHA-256 mismatch.")
    _zip_directory(zip_bytes)
    output = io.BytesIO()
    count = total = 0
    try:
        with ZipFile(io.BytesIO(zip_bytes)) as archive:
            members = archive.infolist()
            _require(len(members) == 1, "Expected one ZIP member.")
            info = members[0]
            mode = info.external_attr >> 16
            _require(
                info.filename == request.stem + ".csv"
                and info.orig_filename == info.filename
                and info.header_offset == 0
                and info.compress_type in (ZIP_STORED, ZIP_DEFLATED)
                and info.extract_version <= 20
                and not info.flag_bits & 1
                and stat.S_IFMT(mode) in (0, stat.S_IFREG),
                "Unexpected or unsupported ZIP member.",
            )
            _require(
                0 < info.file_size <= MAX_CSV_BYTES
                and 0 < info.compress_size <= MAX_ZIP_BYTES
                and info.file_size <= info.compress_size * MAX_RATIO,
                "CSV size or expansion ratio limit exceeded.",
            )
            with archive.open(info) as stream:
                while line := stream.readline(MAX_LINE_BYTES + 1):
                    total += len(line)
                    _require(
                        len(line) <= MAX_LINE_BYTES and total <= MAX_CSV_BYTES,
                        "CSV byte or line limit exceeded.",
                    )
                    _require(
                        count < min(request.row_count, MAX_ROWS),
                        "Extra minute identity or monthly row limit exceeded.",
                    )
                    rows = list(csv.reader([line.decode("ascii")], strict=True))
                    _require(len(rows) == 1, "Invalid native CSV row.")
                    stamp = request.start_ms + count * 60_000
                    price = _parse_row(rows[0], stamp)
                    output.write(
                        f"{request.symbol},{stamp},{price},{digest}\n".encode()
                    )
                    count += 1
            _require(total == info.file_size, "Decompressed size mismatch.")
    except (BadZipFile, RuntimeError, NotImplementedError, EOFError, zlib.error):
        raise MinuteDataError("Corrupt or unsupported ZIP archive.") from None
    except (UnicodeError, csv.Error):
        raise MinuteDataError("Invalid native ASCII CSV encoding or syntax.") from None
    _require(count == request.row_count, "Missing required minute identities.")
    return output.getvalue(), {
        "symbol": request.symbol,
        "month": request.month,
        "interval": "1m",
        "url": request.url,
        "checksum_url": request.checksum_url,
        "sha256": digest,
        "checksum_sha256": _sha(checksum_bytes),
        "zip_bytes": len(zip_bytes),
        "checksum_bytes": len(checksum_bytes),
        "csv_bytes": total,
        "row_count": count,
        "observed_at": observed,
        "observation_kind": "retrospective_full_archive_acquisition",
        "validation_status": "complete_checksum_and_native_grid",
    }


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch(url, limit):
    allowed = {r.url: MAX_ZIP_BYTES for r in minute_requests()}
    allowed.update({r.checksum_url: MAX_CHECKSUM_BYTES for r in minute_requests()})
    _require(url in allowed and limit == allowed[url], "URL/limit outside fixed plan.")
    for attempt in range(3):
        try:
            deadline = time.monotonic() + 60
            # No proxies, auth handlers, cookies or redirects; fixed public HTTPS.
            opener = build_opener(ProxyHandler({}), _NoRedirect())
            with opener.open(Request(url), timeout=15) as response:
                _require(
                    response.status == 200 and response.geturl() == url,
                    "Unexpected HTTP status or response URL.",
                )
                length = response.headers.get("Content-Length")
                _require(
                    length is None
                    or (
                        re.fullmatch(r"[0-9]{1,10}", length)
                        and 0 < int(length) <= limit
                    ),
                    "Invalid HTTP content length.",
                )
                body = bytearray()
                while True:
                    if time.monotonic() > deadline:
                        raise TimeoutError
                    chunk = response.read1(min(65536, limit + 1 - len(body)))
                    if not chunk:
                        break
                    body.extend(chunk)
                    _require(len(body) <= limit, "HTTP byte limit exceeded.")
                _require(
                    body and (length is None or len(body) == int(length)),
                    "Empty or truncated HTTP body.",
                )
                return bytes(body)
        except HTTPError as error:
            error.close()
            if error.code not in (500, 502, 503, 504) or attempt == 2:
                raise MinuteDataError("Archive HTTP request failed.") from None
        except (URLError, TimeoutError, OSError, HTTPException):
            if attempt == 2:
                raise MinuteDataError(
                    "Archive download failed after three attempts."
                ) from None
        time.sleep(attempt + 1)
    raise AssertionError("Unreachable retry state")


def download_minute_archive(request):
    """FUTURE APPROVAL ONLY: bounded HTTP utility, never a default or CLI action.

    Returns (ZIP bytes, exact sidecar bytes, full-ZIP acquisition time). A caller
    must separately obtain owner acquisition approval before invoking this utility.
    """
    _request(request)
    body = _fetch(request.url, MAX_ZIP_BYTES)
    observed_at = datetime.now(UTC)
    checksum = _fetch(request.checksum_url, MAX_CHECKSUM_BYTES)
    return body, checksum, observed_at


def _write_exclusive(path, body):
    partial = path.with_name(path.name + ".partial")
    with partial.open("xb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def _read(path, limit):
    _require(
        not path.is_symlink() and path.is_file(), "Expected regular evidence file."
    )
    with path.open("rb") as stream:
        body = stream.read(limit + 1)
    _bounded_bytes(body, limit)
    return body


def _implementation():
    return _sha(Path(__file__).read_bytes())


def _manifest(sources, output_hash, output_size, implementation):
    return {
        "artifact_version": VERSION,
        "format_version": FORMAT,
        "status": "validated_source_structure_not_approved_for_evaluation",
        "source_authentication": "checksums_are_not_signed_provider_attestations",
        "coverage": coverage(),
        "archive_count": 24,
        "sources": sources,
        "output": {
            "name": "minute_opens.csv",
            "sha256": output_hash,
            "bytes": output_size,
        },
        "implementation_sha256": implementation,
    }


def _verify_retained(directory, manifest):
    """Stream an exact byte comparison against independent source reconstruction."""
    _require(type(manifest) is dict, "Invalid minute manifest.")
    _require(
        not directory.is_symlink()
        and not (directory / "raw").is_symlink()
        and not (directory / "failure.json").exists(),
        "Failed or symlinked source publication.",
    )
    _require(
        isinstance(manifest.get("sources"), list) and len(manifest["sources"]) == 24,
        "Expected exactly 24 source records.",
    )
    output = manifest.get("output")
    _require(
        isinstance(output, dict)
        and _json(manifest)
        == _json(
            _manifest(
                manifest["sources"],
                output.get("sha256"),
                output.get("bytes"),
                _implementation(),
            )
        ),
        "Manifest contract or implementation mismatch.",
    )
    path = directory / "minute_opens.csv"
    _require(not path.is_symlink() and path.is_file(), "Invalid processed file.")
    digest = hashlib.sha256(HEADER)
    size = len(HEADER)
    with path.open("rb") as processed:
        _require(processed.read(len(HEADER)) == HEADER, "Processed header mismatch.")
        for request, source in zip(minute_requests(), manifest["sources"], strict=True):
            try:
                observed = datetime.fromisoformat(source["observed_at"])
                body = _read(directory / "raw" / (request.stem + ".zip"), MAX_ZIP_BYTES)
                checksum = _read(
                    directory / "raw" / (request.stem + ".zip.CHECKSUM"),
                    MAX_CHECKSUM_BYTES,
                )
                fragment, actual = verify_minute_archive(
                    request, body, checksum, observed
                )
                _require(
                    _json(actual) == _json(source),
                    "Source identity or provenance mismatch.",
                )
                _require(
                    processed.read(len(fragment)) == fragment,
                    "Processed opens differ from retained native archives.",
                )
                digest.update(fragment)
                size += len(fragment)
                del body, checksum, fragment
            except (KeyError, TypeError, OverflowError, ValueError) as error:
                if isinstance(error, MinuteDataError):
                    raise
                raise MinuteDataError("Malformed source metadata.") from None
        _require(not processed.read(1), "Extra processed output bytes.")
    _require(
        _json(manifest)
        == _json(
            _manifest(manifest["sources"], digest.hexdigest(), size, _implementation())
        ),
        "Manifest contract, output hash or implementation mismatch.",
    )


def prepare_minute_execution_data(destination, *, downloader):
    """Reserve exclusively, retain each month, replay, publish manifest LAST.

    Stage 4B.2C: injected synthetic downloader and pytest temporary paths ONLY.
    Downloader(request) must return (zip_bytes, checksum_bytes, observed_at).
    No network fallback, resume, overwrite or automatic actual-source permission.
    Returns the external manifest SHA-256; retain it independently to pin a release.
    """
    destination = Path(destination)
    destination.mkdir()  # Parent must exist; even an empty destination is refused.
    sources = []
    current = None
    current_download = None
    try:
        implementation = _implementation()
        raw = destination / "raw"
        raw.mkdir()
        partial = destination / "minute_opens.csv.partial"
        digest = hashlib.sha256(HEADER)
        size = len(HEADER)
        with partial.open("xb") as output:
            output.write(HEADER)
            for request in minute_requests():
                current = request.stem
                current_download = None
                body, checksum, observed = downloader(request)
                _bounded_bytes(body, MAX_ZIP_BYTES)
                _bounded_bytes(checksum, MAX_CHECKSUM_BYTES)
                current_download = {
                    "sha256": _sha(body),
                    "checksum_sha256": _sha(checksum),
                    "observed_at": _observed(request, observed),
                }
                _write_exclusive(raw / (request.stem + ".zip"), body)
                _write_exclusive(raw / (request.stem + ".zip.CHECKSUM"), checksum)
                fragment, source = verify_minute_archive(
                    request, body, checksum, observed
                )
                output.write(fragment)
                digest.update(fragment)
                size += len(fragment)
                sources.append(source)
                del body, checksum, fragment
            output.flush()
            os.fsync(output.fileno())
        os.link(partial, destination / "minute_opens.csv")
        partial.unlink()
        manifest = _manifest(sources, digest.hexdigest(), size, implementation)
        _verify_retained(destination, manifest)
        body = _json(manifest)
        _write_exclusive(destination / "manifest.json", body)
        return _sha(body)
    except BaseException:
        (destination / "manifest.json").unlink(missing_ok=True)
        try:
            _write_exclusive(
                destination / "failure.json",
                _json(
                    {
                        "status": "failed",
                        "current_source": current,
                        "current_download": current_download,
                        "validated_sources": sources,
                        "recovery": "Investigate evidence; use a NEW destination.",
                        "resume": False,
                    }
                ),
            )
        except OSError:
            # Disk failure/hard kill can leave partials; no manifest fails closed.
            pass
        raise


def load_minute_execution_data(directory, *, expected_manifest_sha256):
    """Offline replay with a REQUIRED external pin; returns verified metadata only.

    Does not load a million records, access forecasts or implement trading. Future
    consumers need a separately reviewed streaming opening-reference interface.
    """
    _require(
        isinstance(expected_manifest_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256),
        "Expected an external manifest SHA-256 pin.",
    )
    directory = Path(directory)
    _require(not directory.is_symlink(), "Symlink evidence directory refused.")
    body = _read(directory / "manifest.json", MAX_METADATA_BYTES)
    _require(_sha(body) == expected_manifest_sha256, "Manifest SHA-256 pin mismatch.")
    try:
        manifest = json.loads(body)
    except (UnicodeError, ValueError):
        raise MinuteDataError("Invalid manifest JSON.") from None
    _verify_retained(directory, manifest)
    _require(_json(manifest) == body, "Noncanonical manifest encoding.")
    return manifest

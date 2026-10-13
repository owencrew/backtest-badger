"""Bounded monthly acquisition; strict grids or explicit source-gap diagnostics."""

import csv
import hashlib
import io
import re
import time
import zlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import BadZipFile, ZipFile

from backtest_badger.candles import CandleObservation, validate_observation

MAX_ZIP_BYTES = 2 * 1024 * 1024
MAX_CSV_BYTES = 8 * 1024 * 1024
MAX_CHECKSUM_BYTES = 1024
MAX_ROWS = 744
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
# Stage 1A independently checked both archives and REST startTime=0, limit=1.
# This is a verified source boundary, not proof of no earlier Binance trading.
FIRST_4H_OPEN = datetime(2017, 8, 17, 4, tzinfo=UTC)


class ArchiveError(ValueError):
    """Safe diagnostics without raw network errors or arbitrary CSV field values."""

    def __init__(self, category, message, **details):
        super().__init__(message)
        self.category = category
        self.details = details


@dataclass(frozen=True)
class ArchiveRequest:
    symbol: str
    interval: str
    month: str

    def __post_init__(self):
        if self.symbol not in ("BTCUSDT", "ETHUSDT"):
            raise ValueError("Symbol must be BTCUSDT or ETHUSDT.")
        if self.interval not in ("1h", "4h"):
            raise ValueError("Interval must be native 1h or 4h.")
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", self.month):
            raise ValueError("Month must be YYYY-MM.")
        try:
            start, end = self.bounds
        except ValueError:
            raise ValueError(
                "Month must be a valid calendar month before 9999-12."
            ) from None
        if end > datetime.now(UTC):
            raise ValueError("Archive month must have ended in UTC.")

    @property
    def bounds(self):
        year, month = map(int, self.month.split("-"))
        start = datetime(year, month, 1, tzinfo=UTC)
        end = datetime(year + month // 12, month % 12 + 1, 1, tzinfo=UTC)
        return start, end

    @property
    def seconds(self):
        return {"1h": 3600, "4h": 14400}[self.interval]

    @property
    def stem(self):
        return f"{self.symbol}-{self.interval}-{self.month}"

    @property
    def url(self):
        return (
            "https://data.binance.vision/data/spot/monthly/klines/"
            f"{self.symbol}/{self.interval}/{self.stem}.zip"
        )

    @property
    def coverage_start(self):
        if self.interval == "4h" and self.month == "2017-08":
            return FIRST_4H_OPEN
        return self.bounds[0]

    @property
    def grid(self):
        start, end = self.coverage_start, self.bounds[1]
        step = timedelta(seconds=self.seconds)
        return [start + i * step for i in range((end - start) // step)]


@dataclass(frozen=True)
class DownloadedArchive:
    body: bytes
    checksum: bytes
    sha256: str
    observed_at: datetime


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # All acquisition stays on the explicit public HTTPS archive URL.
        return None


def _fetch(url: str, limit: int) -> bytes:
    """Three attempts at most; bounded body, socket timeout and read deadline."""
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "backtest-badger/0.1"})
            with build_opener(_NoRedirect()).open(request, timeout=15) as response:
                if response.status != 200:
                    raise ArchiveError(
                        "http", "Archive request did not return HTTP 200."
                    )
                length = response.headers.get("Content-Length")
                if length is not None:
                    if len(length) > 20 or not length.isdecimal():
                        raise ArchiveError("http", "Invalid response content length.")
                    if int(length) > limit:
                        raise ArchiveError(
                            "size_limit", "HTTP response exceeds size limit."
                        )
                body = bytearray()
                deadline = time.monotonic() + 60
                while True:
                    if time.monotonic() > deadline:
                        raise TimeoutError
                    chunk = response.read1(min(65536, limit + 1 - len(body)))
                    if not chunk:
                        break
                    body.extend(chunk)
                    if len(body) > limit:
                        raise ArchiveError(
                            "size_limit", "HTTP response exceeds size limit."
                        )
                if length is not None and len(body) != int(length):
                    raise ArchiveError("download", "Incomplete HTTP response body.")
                return bytes(body)
        except HTTPError as error:
            error.close()
            if error.code not in (500, 502, 503, 504) or attempt == 2:
                raise ArchiveError(
                    "http",
                    f"Archive acquisition failed (HTTP {error.code}).",
                    http_status=error.code,
                ) from None
        except (URLError, TimeoutError, OSError, HTTPException):
            if attempt == 2:
                raise ArchiveError(
                    "download", "Archive acquisition failed after 3 attempts."
                ) from None
        time.sleep(attempt + 1)
    raise AssertionError("Unreachable retry state")


def verify_checksum(body: bytes, checksum: bytes, request: ArchiveRequest) -> str:
    if len(body) > MAX_ZIP_BYTES or len(checksum) > MAX_CHECKSUM_BYTES:
        raise ArchiveError("size_limit", "Archive or checksum exceeds size limit.")
    match = re.fullmatch(
        rb"([0-9a-fA-F]{64}) [ *]"
        + re.escape((request.stem + ".zip").encode())
        + rb"\r?\n?",
        checksum,
    )
    if not match:
        raise ArchiveError(
            "checksum", "Malformed checksum or unexpected checksum filename."
        )
    digest = hashlib.sha256(body).hexdigest()
    if digest != match[1].decode().lower():
        raise ArchiveError("checksum", "Archive SHA-256 checksum mismatch.")
    return digest


def download_archive(request: ArchiveRequest) -> DownloadedArchive:
    body = _fetch(request.url, MAX_ZIP_BYTES)
    # This is acquisition time of the complete ZIP, not parse, sidecar or DB time.
    observed_at = datetime.now(UTC)
    try:
        checksum = _fetch(request.url + ".CHECKSUM", MAX_CHECKSUM_BYTES)
        digest = verify_checksum(body, checksum, request)
    except ArchiveError as error:
        error.details.update(
            observed_at=observed_at.isoformat(),
            source_sha256=hashlib.sha256(body).hexdigest(),
        )
        raise
    return DownloadedArchive(body, checksum, digest, observed_at)


def parse_archive(
    request: ArchiveRequest,
    download: DownloadedArchive,
    *,
    market_id: int,
    allow_source_gaps=False,
    diagnostics=None,
) -> list[CandleObservation]:
    """Verify before opening; retain acquisition time when parsing/replaying bytes.

    The CSV has no symbol field: identity comes from the explicit request and exact
    member/sidecar names. Exclusive end is open_time + interval, as in persistence.
    """
    if allow_source_gaps and request.interval != "4h":
        raise ValueError("Gap-tolerant history supports native 4h only.")
    digest = verify_checksum(download.body, download.checksum, request)
    if digest != download.sha256:
        raise ArchiveError(
            "checksum", "Downloaded provenance hash does not match body."
        )
    try:
        with ZipFile(io.BytesIO(download.body)) as archive:
            members = archive.infolist()
            if len(members) != 1 or members[0].filename != request.stem + ".csv":
                raise ArchiveError(
                    "zip", "ZIP must contain only the expected CSV member."
                )
            if members[0].file_size > MAX_CSV_BYTES:
                raise ArchiveError("size_limit", "Uncompressed CSV exceeds size limit.")
            with archive.open(members[0]) as member:
                content = member.read(MAX_CSV_BYTES + 1)
                if len(content) > MAX_CSV_BYTES:
                    raise ArchiveError(
                        "size_limit", "Uncompressed CSV exceeds size limit."
                    )
    except (
        BadZipFile,
        RuntimeError,
        NotImplementedError,
        EOFError,
        UnicodeError,
        zlib.error,
    ):
        raise ArchiveError("zip", "Corrupt or unsupported ZIP archive.") from None
    try:
        rows = []
        for row in csv.reader(io.StringIO(content.decode("utf-8")), strict=True):
            if len(rows) == MAX_ROWS:
                raise ArchiveError("size_limit", "Archive exceeds monthly row limit.")
            rows.append(row)
    except (UnicodeError, csv.Error):
        raise ArchiveError("csv", "Invalid UTF-8 CSV content.") from None
    observations = []
    excluded = []
    source_opens = []
    expected = set(request.grid)
    seen, duplicates, unexpected = set(), set(), set()
    # Contract is based on the requested archive date, never on epoch digit count.
    microseconds_per_tick = 1 if request.month >= "2025-01" else 1000
    for row_number, row in enumerate(rows, 1):
        try:
            if len(row) != 12 or any(not value or len(value) > 128 for value in row):
                raise ValueError("Expected twelve nonempty bounded fields.")
            for index in (0, 6, 8):
                if not re.fullmatch(r"[0-9]+", row[index]):
                    raise ValueError(
                        "Timestamp and trade count must be unsigned integers."
                    )
            for index in (1, 2, 3, 4, 5, 7, 9, 10):
                if not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", row[index]):
                    raise ValueError("Invalid decimal field.")
            opened = EPOCH + timedelta(microseconds=int(row[0]) * microseconds_per_tick)
            exclusive_end = EPOCH + timedelta(
                microseconds=(int(row[6]) + 1) * microseconds_per_tick
            )
            observation = CandleObservation(
                market_id=market_id,
                interval_seconds=request.seconds,
                open_time=opened,
                open=Decimal(row[1]),
                high=Decimal(row[2]),
                low=Decimal(row[3]),
                close=Decimal(row[4]),
                base_volume=Decimal(row[5]),
                quote_volume=Decimal(row[7]),
                trade_count=int(row[8]),
                taker_buy_base_volume=Decimal(row[9]),
                taker_buy_quote_volume=Decimal(row[10]),
                observed_at=download.observed_at,
                source_kind="archive",
                source_url=request.url,
                source_sha256=digest,
            )
            validate_observation(observation)
            end = opened + timedelta(seconds=request.seconds)
            irregular_close = exclusive_end != end
            if irregular_close:
                # Do not normalize partial bars or infer a valid duration from OHLCV.
                # Only the investigated classes (shortened or exact-exclusive close)
                # can be quarantined. Inverted/overlong times stop for review.
                raw_close = exclusive_end - timedelta(
                    microseconds=microseconds_per_tick
                )
                if not allow_source_gaps or not opened <= raw_close <= end:
                    raise ValueError("Incorrect inclusive close-time boundary.")
        except (ValueError, OverflowError) as error:
            # All ValueErrors above contain fixed validation messages, not row values.
            reason = (
                "Timestamp is outside the supported range."
                if isinstance(error, OverflowError)
                else str(error)
            )
            raise ArchiveError(
                "row",
                f"Invalid candle at CSV row {row_number}: {reason}",
                actual_count=len(rows),
                invalid_row=row_number,
                invalid_reason=reason,
                excluded_observations=excluded,
                excluded_count=len(excluded),
                inspection_complete=False,
            ) from None
        if opened in seen:
            duplicates.add(opened)
        if opened not in expected:
            unexpected.add(opened)
        seen.add(opened)
        source_opens.append(opened)
        if irregular_close:
            excluded.append(
                {
                    "csv_row": row_number,
                    "open_time": opened.isoformat(),
                    "raw_close_time": row[6],
                    "expected_inclusive_close_time": str(
                        (end - EPOCH) // timedelta(microseconds=microseconds_per_tick)
                        - 1
                    ),
                    "reason": "irregular_close_time",
                    "close_time_class": "exclusive_boundary"
                    if raw_close == end
                    else "shortened_interval",
                    "action": "excluded_without_normalization",
                }
            )
        else:
            observations.append(observation)
    missing = expected - seen
    ordered = source_opens == sorted(source_opens)
    details = {
        "actual_count": len(rows),
        "accepted_count": len(observations),
        "inspection_complete": True,
        "source_missing_intervals": [v.isoformat() for v in sorted(missing)],
        "missing_intervals": [
            v.isoformat()
            for v in sorted(expected - {o.open_time for o in observations})
        ],
        "excluded_observations": excluded,
        "excluded_count": len(excluded),
        "duplicate_intervals": [v.isoformat() for v in sorted(duplicates)],
        "unexpected_intervals": [v.isoformat() for v in sorted(unexpected)],
        "chronological": ordered,
        "candle_complete": not (
            missing or excluded or duplicates or unexpected or not ordered
        ),
    }
    if diagnostics is not None:
        diagnostics.update(details)
    if allow_source_gaps and not observations:
        raise ArchiveError(
            "coverage", "No eligible observations; stop for review.", **details
        )
    if (missing and not allow_source_gaps) or duplicates or unexpected or not ordered:
        raise ArchiveError(
            "coverage",
            f"Archive grid invalid: {len(missing)} missing, "
            f"{len(duplicates)} duplicated, "
            f"{len(unexpected)} unexpected; chronological={ordered}.",
            **details,
        )
    return observations

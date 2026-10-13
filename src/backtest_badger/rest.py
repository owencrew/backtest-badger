"""Bounded public Binance Spot REST acquisition and strict native 4h parsing."""

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from backtest_badger.archives import EPOCH, _NoRedirect
from backtest_badger.candles import CandleObservation, validate_observation

BASE = "https://data-api.binance.vision/api/v3/"
STEP = timedelta(hours=4)
MILLISECOND = timedelta(milliseconds=1)
MAX_BODY = 2 * 1024 * 1024
PARSER_VERSION = "stage-1c1-v1"


class RestError(ValueError):
    def __init__(self, category, message, **details):
        super().__init__(message)
        self.category = category
        self.details = details


@dataclass(frozen=True)
class Response:
    body: bytes
    url: str
    observed_at: datetime
    status: int
    headers: dict
    complete: bool = True

    @property
    def sha256(self):
        return hashlib.sha256(self.body).hexdigest()


def eligible_end(run_time, settling_seconds=60):
    if run_time.utcoffset() != timedelta(0):
        raise ValueError("Run time must be aware UTC.")
    if type(settling_seconds) is not int or not 0 <= settling_seconds <= 86400:
        raise ValueError("Settling delay must be 0–86400 whole seconds.")
    elapsed = run_time - EPOCH - timedelta(seconds=settling_seconds)
    return EPOCH + (elapsed // STEP) * STEP


def sync_start(end, latest, explicit=None):
    """Bound acquisition separately from the seven-day revision authority."""
    if explicit is None:
        if latest is None:
            raise ValueError("No stored candle; supply an explicit UTC --start.")
        start = min(latest + STEP, end - timedelta(days=7))
        if end - start > timedelta(days=30):
            raise ValueError("Catch-up exceeds 30 days; use bounded --start recovery.")
    else:
        start = explicit
        if start.utcoffset() != timedelta(0) or (start - EPOCH) % STEP:
            raise ValueError("--start must be an aware UTC 4h opening boundary.")
    if not end - timedelta(days=180) <= start < end:
        raise ValueError("Recovery must start within the last 180 eligible days.")
    return start


def kline_url(symbol, start, end):
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise ValueError("Symbol must be BTCUSDT or ETHUSDT.")
    params = dict(
        symbol=symbol,
        interval="4h",
        timeZone="0",
        startTime=(start - EPOCH) // MILLISECOND,
        endTime=(end - EPOCH) // MILLISECOND - 1,
        limit=1000,
    )
    return BASE + "klines?" + urlencode(params)


def fetch(url, *, retain, attempts):
    """At most three attempts. Stop on 429/418: never retry before Retry-After.

    Record bounded bodies (including invalid/error responses) before interpreting
    them. Partial bodies are evidence only, never candle provenance.
    """
    for attempt in range(3):
        # Pace every attempt, including separate runs' first requests.
        time.sleep(1 if attempt == 0 else 2**attempt)
        try:
            request = Request(url, headers={"User-Agent": "backtest-badger/0.1"})
            try:
                response = build_opener(_NoRedirect()).open(request, timeout=15)
            except HTTPError as error:
                response = error
            with response:
                headers = {
                    k.lower(): v
                    for k, v in response.headers.items()
                    if k.lower().startswith("x-mbx-")
                    or k.lower() in ("retry-after", "date", "content-length")
                }
                status = response.code
                body = bytearray()
                complete = False
                read_error = None
                deadline = time.monotonic() + 30
                try:
                    while len(body) <= MAX_BODY:
                        if time.monotonic() > deadline:
                            raise TimeoutError
                        chunk = response.read1(min(65536, MAX_BODY + 1 - len(body)))
                        if not chunk:
                            complete = True
                            break
                        body.extend(chunk)
                except (URLError, TimeoutError, OSError, HTTPException) as error:
                    read_error = error
                acquired = datetime.now(UTC)
                downloaded = Response(
                    bytes(body), response.geturl(), acquired, status, headers, complete
                )
                retain(downloaded)
                attempts.append(
                    {
                        "status": status,
                        "headers": headers,
                        "complete": complete,
                        "observed_at": acquired.isoformat(),
                    }
                )
                if len(body) > MAX_BODY:
                    raise RestError("size_limit", "REST response exceeds 2 MiB.")
                # Even an incomplete throttle response must never be retried.
                if status in (429, 418):
                    raise RestError(
                        "rate_limit",
                        "Provider throttled/banned requests; "
                        "stop and respect Retry-After before another run.",
                        http_status=status,
                        retry_after=headers.get("retry-after"),
                    )
                if read_error is not None:
                    raise read_error
                if status in (500, 502, 503, 504) and attempt < 2:
                    continue
                if status != 200:
                    raise RestError(
                        "http",
                        f"REST acquisition failed (HTTP {status}).",
                        http_status=status,
                    )
                length = headers.get("content-length")
                if length is not None and (
                    not length.isdecimal()
                    or len(length) > 20
                    or int(length) != len(body)
                ):
                    raise RestError("download", "Incomplete or invalid Content-Length.")
                return downloaded
        except (URLError, TimeoutError, OSError, HTTPException):
            attempts.append({"error_category": "transport", "attempt": attempt + 1})
            if attempt == 2:
                raise RestError(
                    "transport", "REST acquisition failed after 3 attempts."
                ) from None
    raise AssertionError("Unreachable retry state")


def check_clock(response, started):
    try:
        data = json.loads(response.body)
        stamp = data["serverTime"]
        if type(stamp) is not int:
            raise ValueError
        server = EPOCH + stamp * MILLISECOND
    except (ValueError, TypeError, KeyError, OverflowError):
        raise RestError("clock", "Malformed provider clock response.") from None
    tolerance = timedelta(seconds=5)
    if (
        response.observed_at - started > timedelta(seconds=10)
        or not started - tolerance <= server <= response.observed_at + tolerance
    ):
        raise RestError("clock", "Provider/local clock check exceeds tolerance.")
    return server


def parse_page(response, *, market_id, start, end):
    """Reject the whole page on any anomaly; raw bytes have already been retained."""
    observations, invalid, identities = inspect_page(
        response, market_id=market_id, start=start, end=end
    )
    if invalid:
        first = invalid[0]
        raise RestError(
            "row",
            "Invalid REST candle; entire page rejected.",
            invalid_row=first["row"],
            rejected_identity=first["open_time"],
            rejected_identities=identities,
            reason=first["reason"],
        )
    if not observations:
        raise RestError("empty_page", "Empty page leaves requested range unresolved.")
    return observations


def inspect_page(response, *, market_id, start, end):
    """Inspect every row for review evidence; invalid pages are never writable.

    Shares all parsing rules with parse_page. Valid neighbours are diagnostic
    candidates only: the caller must reject the whole page if invalid is nonempty.
    """
    if not response.complete or len(response.body) > MAX_BODY:
        raise RestError("download", "Cannot parse an incomplete or oversized response.")
    try:
        rows = json.loads(response.body)
    except (ValueError, UnicodeError, RecursionError):
        raise RestError("json", "Invalid JSON response.") from None
    if not isinstance(rows, list) or len(rows) > 1000:
        raise RestError("structure", "Expected at most 1000 kline rows.")
    identities = []
    for index, row in enumerate(rows):
        opened = None
        if isinstance(row, list) and row and type(row[0]) is int:
            try:
                opened = (EPOCH + row[0] * MILLISECOND).isoformat()
            except OverflowError:
                pass
        identities.append({"row": index + 1, "open_time": opened})
    observations = []
    invalid = []
    previous = None
    digest = response.sha256
    for index, row in enumerate(rows):
        opened = None
        try:
            if not isinstance(row, list) or len(row) != 12:
                raise ValueError("Expected twelve fields.")
            if any(type(row[i]) is not int or row[i] < 0 for i in (0, 6, 8)):
                raise ValueError(
                    "Timestamps and trades must be unsigned JSON integers."
                )
            opened = EPOCH + row[0] * MILLISECOND
            if not start <= opened < end:
                raise ValueError(
                    "Unexpected or ineligible opening time; page rejected."
                )
            if previous is not None and opened <= previous:
                raise ValueError("Duplicate, non-advancing or out-of-order identity.")
            previous = opened
            if row[6] != row[0] + STEP // MILLISECOND - 1:
                raise ValueError("Incorrect inclusive millisecond close boundary.")
            for i in (1, 2, 3, 4, 5, 7, 9, 10):
                if (
                    not isinstance(row[i], str)
                    or len(row[i]) > 128
                    or not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", row[i])
                ):
                    raise ValueError("Invalid economic decimal string.")
            observation = CandleObservation(
                market_id,
                14400,
                opened,
                *(Decimal(row[i]) for i in (1, 2, 3, 4, 5, 7)),
                row[8],
                Decimal(row[9]),
                Decimal(row[10]),
                response.observed_at,
                "rest",
                response.url,
                digest,
            )
            validate_observation(observation)
        except (ValueError, OverflowError) as error:
            invalid.append(
                dict(
                    row=index + 1,
                    open_time=opened.isoformat() if opened else None,
                    reason=str(error),
                )
            )
            continue
        observations.append(observation)
        previous = opened
    return observations, invalid, identities

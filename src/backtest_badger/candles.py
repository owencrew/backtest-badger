"""Exact, version-preserving persistence of already obtained candle observations.

No provider I/O belongs here. Writers use an idle autocommit Psycopg connection
and own one short READ COMMITTED transaction per observation or batch.
"""

import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

from psycopg import Connection
from psycopg.pq import TransactionStatus
from psycopg.rows import dict_row

PRICES = ("open", "high", "low", "close")
VOLUMES = (
    "base_volume",
    "quote_volume",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
)
ECONOMIC_FIELDS = (*PRICES, *VOLUMES, "trade_count")
IDENTITY = "market_id = %(market_id)s AND interval_seconds = %(interval_seconds)s "
IDENTITY += "AND open_time = %(open_time)s"


@dataclass(frozen=True)
class CandleObservation:
    market_id: int
    interval_seconds: int
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    base_volume: Decimal
    quote_volume: Decimal
    trade_count: int
    taker_buy_base_volume: Decimal
    taker_buy_quote_volume: Decimal
    observed_at: datetime
    source_kind: str
    source_url: str
    source_sha256: str


class ObservationConflict(ValueError):
    """Different economic values have the same observation timestamp."""


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("Timestamps must be timezone-aware.")
    return value.astimezone(UTC)


def validate_observation(observation: CandleObservation) -> None:
    """Validate without rounding, converting floats or consulting a provider."""
    if (
        type(observation.market_id) is not int
        or not 1 <= observation.market_id <= 32767
    ):
        raise ValueError("market_id must be a positive smallint.")
    seconds = observation.interval_seconds
    if type(seconds) is not int or seconds not in (3600, 14400):
        raise ValueError("Only native 1h and 4h intervals are supported.")
    opened = _utc(observation.open_time)
    observed = _utc(observation.observed_at)
    if (opened - datetime(1970, 1, 1, tzinfo=UTC)) % timedelta(
        seconds=observation.interval_seconds
    ):
        raise ValueError("open_time must align exactly to the UTC interval grid.")
    if observed < opened + timedelta(seconds=observation.interval_seconds):
        raise ValueError("An observation must be of a closed candle.")
    for name in (*PRICES, *VOLUMES):
        value = getattr(observation, name)
        if not isinstance(value, Decimal) or not value.is_finite():
            raise ValueError(f"{name} must be a finite Decimal.")
        if value < 0 or (name in PRICES and value == 0):
            raise ValueError(f"{name} is outside its allowed range.")
    if not (
        observation.low <= observation.open <= observation.high
        and observation.low <= observation.close <= observation.high
    ):
        raise ValueError("OHLC bounds are inconsistent.")
    if (
        observation.taker_buy_base_volume > observation.base_volume
        or observation.taker_buy_quote_volume > observation.quote_volume
    ):
        raise ValueError("Taker-buy volumes cannot exceed total volumes.")
    if type(observation.trade_count) is not int or not (
        0 <= observation.trade_count <= 2**63 - 1
    ):
        raise ValueError("trade_count must be a non-negative bigint.")
    if observation.source_kind not in ("archive", "rest"):
        raise ValueError("source_kind must be archive or rest.")
    if (
        not isinstance(observation.source_url, str)
        or not observation.source_url.strip()
    ):
        raise ValueError("source_url must be non-blank.")
    if not isinstance(observation.source_sha256, str) or not re.fullmatch(
        "[0-9a-f]{64}", observation.source_sha256
    ):
        raise ValueError("source_sha256 must contain 64 lowercase hexadecimal digits.")


def save_candle(
    connection: Connection, observation: CandleObservation
) -> Literal["inserted", "unchanged", "revised", "stale"]:
    """Select newer observations; preserve every accepted economic change.

    Identical values keep the version, original provenance and recording time.
    Only their last_observed_at watermark may advance. Conflicting equal-time
    observations raise ObservationConflict; older changed observations return
    'stale'. Neither changes stored data. Exceptions roll back this entire write.
    """
    validate_observation(observation)
    if (
        not connection.autocommit
        or connection.info.transaction_status != TransactionStatus.IDLE
    ):
        raise ValueError("save_candle requires an idle autocommit connection.")
    with connection.transaction(), connection.cursor(row_factory=dict_row) as cursor:
        _prepare_write(cursor)
        return _save_candle(cursor, observation)


class BatchConflict(ValueError):
    """Batch rejected atomically, with conflicting and stale identities."""

    def __init__(self, conflicts, stale):
        self.conflicts = conflicts
        self.stale = stale
        super().__init__(
            f"Batch rolled back: {len(conflicts)} conflicting, {len(stale)} stale."
        )


class ReviewConflict(ValueError):
    """The locked canonical row no longer matches the reviewed snapshot."""

    def __init__(self, observation):
        self.open_time = observation.open_time.isoformat()
        super().__init__(f"Database state changed at {self.open_time}; review again.")


_UNREVIEWED = object()


def save_candles(
    connection: Connection,
    observations,
    mode="backfill",
    *,
    refresh_start=None,
    refresh_end=None,
    differences=None,
    reviewed_rows=None,
    revalidation_start=None,
    revalidation_end=None,
) -> dict[str, int]:
    """Validate first, then atomically write one batch through shared row locks.

    Backfill never revises. Explicit recent-refresh permits revisions only inside
    its seven-day authority, and reports locked old/new rows in differences.
    Historical revalidation requires a reviewed state for every selected row,
    verifies that full state under lock, and uses the same watermark policy.
    Uses the same locked selection as save_candle. Any conflict, stale changed
    observation or database error rolls back every insert and watermark update.
    Sorting identities gives overlapping batches a consistent lock order.
    """
    if mode not in ("backfill", "recent-refresh", "historical-revalidation"):
        raise ValueError("Unsupported batch mode.")
    if mode == "recent-refresh":
        refresh_start, refresh_end = _utc(refresh_start), _utc(refresh_end)
        if not timedelta(0) < refresh_end - refresh_start <= timedelta(days=7):
            raise ValueError("Recent revision authority must span at most seven days.")
    observations = list(observations)
    historical = mode == "historical-revalidation"
    if historical:
        revalidation_start = _utc(revalidation_start)
        revalidation_end = _utc(revalidation_end)
        if (
            not timedelta(0)
            < revalidation_end - revalidation_start
            <= timedelta(days=30)
            or not 1 <= len(observations) <= 180
            or len({o.market_id for o in observations}) != 1
            or not isinstance(reviewed_rows, dict)
        ):
            raise ValueError("Historical authority requires a bounded reviewed range.")
    if mode == "recent-refresh" and len(observations) > 1000:
        raise ValueError("Recent refresh batches are limited to 1000 observations.")
    identities = set()
    for observation in observations:
        validate_observation(observation)
        if historical and (
            observation.source_kind != "rest"
            or observation.interval_seconds != 14400
            or not revalidation_start <= observation.open_time < revalidation_end
        ):
            raise ValueError(
                "Historical authority requires in-range native 4h REST rows."
            )
        if mode == "recent-refresh" and (
            observation.source_kind != "rest"
            or observation.interval_seconds != 14400
            or observation.open_time >= refresh_end
        ):
            raise ValueError("Recent refresh requires eligible native 4h REST rows.")
        identity = (
            observation.market_id,
            observation.interval_seconds,
            observation.open_time,
        )
        if identity in identities:
            raise ValueError("Duplicate candle identity in batch.")
        identities.add(identity)
    if historical and set(reviewed_rows) != identities:
        raise ValueError(
            "Every selected identity must have an explicit reviewed state."
        )
    if (
        not connection.autocommit
        or connection.info.transaction_status != TransactionStatus.IDLE
    ):
        raise ValueError("save_candles requires an idle autocommit connection.")
    counts = {"inserted": 0, "unchanged": 0}
    if mode != "backfill":
        counts["revised"] = 0
    conflicts, stale = [], []
    with connection.transaction(), connection.cursor(row_factory=dict_row) as cursor:
        _prepare_write(cursor)
        for observation in sorted(
            observations, key=lambda o: (o.market_id, o.interval_seconds, o.open_time)
        ):
            try:
                result = _save_candle(
                    cursor,
                    observation,
                    backfill=mode == "backfill"
                    or (
                        mode == "recent-refresh"
                        and observation.open_time < refresh_start
                    ),
                    differences=differences,
                    expected=reviewed_rows[
                        (
                            observation.market_id,
                            observation.interval_seconds,
                            observation.open_time,
                        )
                    ]
                    if historical
                    else _UNREVIEWED,
                )
            except ObservationConflict:
                result = "conflict"
            identity = {
                "market_id": observation.market_id,
                "interval_seconds": observation.interval_seconds,
                "open_time": observation.open_time.isoformat(),
            }
            if result == "conflict":
                conflicts.append(identity)
            elif result == "stale":
                stale.append(identity)
            else:
                counts[result] += 1
        if conflicts or stale:
            raise BatchConflict(conflicts, stale)
    return counts


def _prepare_write(cursor):
    cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
    cursor.execute("SET LOCAL TIME ZONE 'UTC'")


def _save_candle(
    cursor, observation, *, backfill=False, differences=None, expected=_UNREVIEWED
):
    """Shared write logic; caller owns validation and the transaction."""
    values = asdict(observation)
    columns = ", ".join(values)
    placeholders = ", ".join(f"%({name})s" for name in values)
    # DO NOTHING serializes an absent-row race through the unique index.
    # A separate SELECT then sees the winner using a new statement snapshot.
    cursor.execute(
        f"""INSERT INTO candle ({columns}, version, recorded_at, last_observed_at)
            VALUES ({placeholders}, 1, clock_timestamp(), %(observed_at)s)
            ON CONFLICT (market_id, interval_seconds, open_time) DO NOTHING
            RETURNING version""",
        values,
    )
    if cursor.fetchone() is not None:
        if expected is not _UNREVIEWED and expected is not None:
            raise ReviewConflict(observation)
        return "inserted"
    cursor.execute(f"SELECT * FROM candle WHERE {IDENTITY} FOR UPDATE", values)
    current = cursor.fetchone()
    if current is None:
        # Concurrent administrative deletion is outside the writer protocol.
        raise RuntimeError("Candle disappeared during selection; retry the write.")
    if expected is not _UNREVIEWED and current != expected:
        raise ReviewConflict(observation)
    cursor.execute("SELECT clock_timestamp() AS now")
    recorded_at = cursor.fetchone()["now"]
    if observation.observed_at > recorded_at:
        raise ValueError("observed_at cannot be in the database clock's future.")
    if all(current[name] == values[name] for name in ECONOMIC_FIELDS):
        if observation.observed_at > current["last_observed_at"]:
            cursor.execute(
                "UPDATE candle SET last_observed_at = %(observed_at)s "
                f"WHERE {IDENTITY}",
                values,
            )
        return "unchanged"
    if differences is not None:
        differences.append({"old": current, "new": values.copy()})
    if observation.observed_at < current["last_observed_at"]:
        return "stale"
    if backfill:
        return "conflict"
    if observation.observed_at == current["last_observed_at"]:
        raise ObservationConflict("Conflicting values share an observation timestamp.")
    # One timestamp after locking, shared by the old and new versions. Never
    # use transaction_timestamp(): the transaction may have waited for a lock.
    values["recorded_at"] = recorded_at
    cursor.execute(
        f"""INSERT INTO candle_revision
            SELECT candle.*, %(recorded_at)s FROM candle WHERE {IDENTITY}""",
        values,
    )
    assignments = ", ".join(
        f"{name} = %({name})s"
        for name in values
        if name not in ("market_id", "interval_seconds", "open_time")
    )
    cursor.execute(
        f"""UPDATE candle SET {assignments}, version = version + 1,
            last_observed_at = %(observed_at)s WHERE {IDENTITY}""",
        values,
    )
    return "revised"


def get_candles(
    connection: Connection,
    market_id: int,
    interval_seconds: int,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Return current candles in ascending open order within [start, end)."""
    start, end = _utc(start), _utc(end)
    if start >= end:
        raise ValueError("A nonempty bounded time range is required.")
    with connection.transaction(), connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SET LOCAL TIME ZONE 'UTC'")
        cursor.execute(
            """SELECT * FROM candle WHERE market_id = %s AND interval_seconds = %s
               AND open_time >= %s AND open_time < %s ORDER BY open_time""",
            (market_id, interval_seconds, start, end),
        )
        return cursor.fetchall()


def get_candle_history(
    connection: Connection, market_id: int, interval_seconds: int, open_time: datetime
) -> list[dict]:
    """Return superseded and current versions, ordered, in one MVCC snapshot."""
    identity = {
        "market_id": market_id,
        "interval_seconds": interval_seconds,
        "open_time": _utc(open_time),
    }
    with connection.transaction(), connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SET LOCAL TIME ZONE 'UTC'")
        cursor.execute(
            f"""SELECT candle.*, NULL::timestamptz AS superseded_at
                FROM candle WHERE {IDENTITY}
                UNION ALL SELECT * FROM candle_revision WHERE {IDENTITY}
                ORDER BY version""",
            identity,
        )
        return cursor.fetchall()

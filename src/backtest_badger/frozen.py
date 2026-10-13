"""Offline integrity checks for the frozen Stage 1B.3 export, before research."""

import csv
import hashlib
import io
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from backtest_badger.candles import (
    PRICES,
    VOLUMES,
    CandleObservation,
    validate_observation,
)
from backtest_badger.research import COLUMNS

DATASET_ID = "binance-4h-history-v1"
CSV_SHA256 = "e6052b8cca7bca00999ca4d7429af67db019c8ef261fa2b499f0fd6774dcd13b"
MANIFEST_SHA256 = "a78d34256d3bcd789e6cc19a2807f432d1ffa1a73ecc81b5ea16b3859759a98a"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
STEP = timedelta(hours=4)


def utc_time(value):
    stamp = datetime.fromisoformat(value)
    if stamp.utcoffset() != timedelta(0):
        raise ValueError("Expected an explicit UTC timestamp.")
    return stamp.astimezone(UTC)


def grid_time(value):
    stamp = utc_time(value)
    if (stamp - datetime(1970, 1, 1, tzinfo=UTC)) % STEP:
        raise ValueError("Unexpected timestamp off the UTC 4h grid.")
    return stamp


def _identities(values):
    result = [grid_time(v) for v in values]
    if result != sorted(set(result)):
        raise ValueError("Manifest identities must be unique and chronological.")
    return set(result)


def load_frozen(
    directory,
    *,
    acknowledge_incomplete=False,
    expected_csv_sha256=CSV_SHA256,
    expected_manifest_sha256=MANIFEST_SHA256,
):
    """Hash the exact bytes that are parsed; never consult DB/provider/local gaps.

    Default pins identify the reviewed export. Explicit hash arguments support
    synthetic fixtures; the CLI does not offer a pin override.
    """
    if not acknowledge_incomplete:
        raise ValueError(
            "Explicit --acknowledge-incomplete is required for this source."
        )
    manifest_bytes = (directory / "manifest.json").read_bytes()
    csv_bytes = (directory / "candles.csv").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_sha256:
        raise ValueError("Frozen manifest SHA-256 mismatch.")
    if hashlib.sha256(csv_bytes).hexdigest() != expected_csv_sha256:
        raise ValueError("Frozen CSV SHA-256 mismatch.")
    manifest = json.loads(manifest_bytes)
    try:
        coverage = manifest["coverage"]
        if not (
            manifest["dataset_id"] == DATASET_ID
            and manifest["export_schema_version"] == 1
            and manifest["dataset_file"] == "candles.csv"
            and manifest["sha256"] == expected_csv_sha256
            and manifest["symbols"] == list(SYMBOLS)
            and manifest["interval"] == "4h"
            and manifest["status"] == coverage["status"] == "incomplete"
            and coverage["complete"] is False
            and manifest["incomplete_acknowledged"] is True
            and coverage["interval_seconds"] == 14400
            and manifest["start"] == coverage["start"]
            and manifest["end_exclusive"] == coverage["end_exclusive"]
            and set(coverage["markets"]) == set(SYMBOLS)
            and set(manifest["row_counts"]) == set(SYMBOLS)
            and not coverage["unreadable_manifests"]
        ):
            raise ValueError("Incompatible frozen export manifest.")
        start = grid_time(manifest["start"])
        end = grid_time(manifest["end_exclusive"])
        if not start < end:
            raise ValueError("Invalid source range.")
        reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"), newline=""))
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("Incompatible frozen CSV schema.")
        markets = {symbol: [] for symbol in SYMBOLS}
        previous = None
        for row in reader:
            if None in row or None in row.values():
                raise ValueError("Malformed frozen CSV row.")
            symbol = row["symbol"]
            if not (
                symbol in markets
                and row["venue"] == "binance"
                and row["market_type"] == "spot"
                and row["base_asset"] == symbol.removesuffix("USDT")
                and row["quote_asset"] == "USDT"
                and row["interval_seconds"] == "14400"
                and int(row["version"]) >= 1
            ):
                raise ValueError("Incompatible market identity or version.")
            row["open_time"] = grid_time(row["open_time"])
            row["observed_at"] = utc_time(row["observed_at"])
            identity = (symbol, row["open_time"])
            if previous is not None and identity <= previous:
                raise ValueError("Duplicate or out-of-order candle identity.")
            if not start <= row["open_time"] < end:
                raise ValueError("Candle outside manifest range.")
            previous = identity
            for name in (*PRICES, *VOLUMES):
                row[name] = Decimal(row[name])
            row["trade_count"] = int(row["trade_count"])
            row["version"] = int(row["version"])
            validate_observation(
                CandleObservation(
                    market_id=SYMBOLS.index(symbol) + 1,
                    interval_seconds=14400,
                    **{
                        name: row[name]
                        for name in CandleObservation.__dataclass_fields__
                        if name not in ("market_id", "interval_seconds")
                    },
                )
            )
            markets[symbol].append(row)
        expected_grid = {start + i * STEP for i in range((end - start) // STEP)}
        for symbol, rows in markets.items():
            item = coverage["markets"][symbol]
            present = {r["open_time"] for r in rows}
            missing = _identities(item["missing_intervals"])
            source_missing, excluded = set(), set()
            for diagnostic in item["source_diagnostics"]:
                absent = _identities(diagnostic["source_missing_intervals"])
                rejected = _identities(
                    [r["open_time"] for r in diagnostic["excluded_observations"]]
                )
                if absent & rejected or absent | rejected != _identities(
                    diagnostic["missing_intervals"]
                ):
                    raise ValueError("Inconsistent source diagnostics.")
                if any(
                    r["reason"] != "irregular_close_time"
                    or r["action"] != "excluded_without_normalization"
                    for r in diagnostic["excluded_observations"]
                ):
                    raise ValueError("Unknown source anomaly policy.")
                source_missing.update(absent)
                excluded.update(rejected)
            if not (
                rows
                and expected_grid - present == missing == source_missing | excluded
                and len(rows) == manifest["row_counts"][symbol] == item["actual_count"]
                and len(expected_grid) == item["expected_count"]
                and len(missing) == item["missing_count"]
                and len(source_missing) == item["known_source_missing_count"]
                and len(excluded) == item["excluded_provider_observation_count"]
                and rows[0]["open_time"] == grid_time(item["first_observed"])
                and rows[-1]["open_time"] == grid_time(item["last_observed"])
                and item["duplicate_identity_count"] == 0
                and item["unexpected_before_boundary"] == 0
                and not item["failed_or_unresolved_imports"]
                and not item["months_without_import_evidence"]
                and not item["months_not_attempted"]
            ):
                raise ValueError(
                    "CSV coverage disagrees with recorded source evidence."
                )
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("Malformed frozen export metadata.") from error
    return manifest, markets

"""Verify Stage 2A artifacts; expose only training and validation to modelling."""

import csv
import hashlib
import io
import json
import math
from collections import Counter
from datetime import timedelta

from backtest_badger.features import (
    EXCLUSION_REASONS,
    FEATURE_DEFINITIONS,
    KNOWN_ANOMALIES,
    OUTPUT_COLUMNS,
    SPLITS,
    TARGET_DEFINITION,
    partition,
)
from backtest_badger.frozen import STEP, SYMBOLS, grid_time, utc_time

CSV_SHA256 = "04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8"
MANIFEST_SHA256 = "a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e"
FEATURES = tuple(FEATURE_DEFINITIONS)
TARGET = "target_log_return_4h"
COUNTS = {
    "BTCUSDT": {"train": 13782, "validation": 2195, "test": 3827},
    "ETHUSDT": {"train": 13783, "validation": 2195, "test": 3827},
}
EXCLUSION_POLICY = (
    "Require every 4h candle t-6..t+1; never fill. "
    "Reject recorded gaps, excluded observations and known anomaly windows. "
    "Exclusive drop reason precedence: " + ", ".join(EXCLUSION_REASONS)
)


def sha256(body):
    return hashlib.sha256(body).hexdigest()


def select_rows(rows, manifest, *, training_only=False):
    """Inspect identities/timing, but never retrieve a test outcome or baseline.

    CSV tokenisation and whole-file hashing necessarily read holdout bytes. Test
    outcomes are never converted, returned, summarised, predicted or scored.
    With training_only, both held-out partitions skip numerical access entirely;
    identity, timing, split, gap and count checks still cover every row.
    """
    selected = {s: {"train": [], "validation": []} for s in SYMBOLS}
    counts = {s: Counter() for s in SYMBOLS}
    coverage = manifest["source_coverage"]
    start, end = grid_time(coverage["start"]), grid_time(coverage["end_exclusive"])
    forbidden = {
        s: {grid_time(t) for t in coverage["markets"][s]["missing_intervals"]}
        | {grid_time(a["open_time"]) for a in KNOWN_ANOMALIES if a["symbol"] == s}
        for s in SYMBOLS
    }
    previous = None
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Malformed research CSV row.")
        symbol = row["symbol"]
        if not (
            symbol in selected
            and row["venue"] == "binance"
            and row["market_type"] == "spot"
            and row["base_asset"] == symbol.removesuffix("USDT")
            and row["quote_asset"] == "USDT"
            and row["interval_seconds"] == "14400"
            and row["known_anomaly"] == "false"
        ):
            raise ValueError("Incompatible research market identity or anomaly flag.")
        opened = grid_time(row["open_time"])
        identity = (symbol, opened)
        if previous is not None and identity <= previous:
            raise ValueError("Duplicate or out-of-order research identity.")
        previous = identity
        available = opened + STEP + timedelta(seconds=60)
        label_available = available + STEP
        split, split_end = partition(available)
        expected_times = {
            "close_time": opened + STEP,
            "feature_available_at": available,
            "target_open_time": opened + STEP,
            "target_close_time": opened + 2 * STEP,
            "target_available_at": label_available,
        }
        if any(utc_time(row[k]) != v for k, v in expected_times.items()):
            raise ValueError("Incompatible feature/label availability timestamps.")
        if split is None or row["split"] != split or label_available >= split_end:
            raise ValueError("Incorrect chronological split or unpurged label.")
        window = {opened + i * STEP for i in range(-6, 2)}
        if min(window) < start or max(window) >= end or window & forbidden[symbol]:
            raise ValueError("Research window crosses source boundary, gap or anomaly.")
        counts[symbol][split] += 1
        # Forward inference has no use for either held-out partition's numerics.
        if training_only and split != "train":
            continue
        # Validate feature numerics without using any holdout outcome.
        features = [float(row[name]) for name in FEATURES]
        if not all(math.isfinite(v) for v in features):
            raise ValueError("Missing or nonfinite research feature.")
        if split == "test":
            continue
        target = float(row[TARGET])
        if not math.isfinite(target):
            raise ValueError("Nonfinite training/validation target.")
        selected[symbol][split].append(
            {
                "open_time": row["open_time"],
                "feature_available_at": row["feature_available_at"],
                "features": features,
                "target": target,
            }
        )
    for symbol in SYMBOLS:
        if dict(counts[symbol]) != manifest["counts"][symbol]["splits"]:
            raise ValueError("Research row counts disagree with manifest.")
    return selected


def load_model_data(
    directory,
    *,
    expected_csv_sha256=CSV_SHA256,
    expected_manifest_sha256=MANIFEST_SHA256,
    expected_counts=COUNTS,
    training_only=False,
):
    """Pins may be overridden by synthetic tests only; CLI has no overrides."""
    manifest_bytes = (directory / "manifest.json").read_bytes()
    csv_bytes = (directory / "research.csv").read_bytes()
    if sha256(manifest_bytes) != expected_manifest_sha256:
        raise ValueError("Research manifest SHA-256 mismatch.")
    if sha256(csv_bytes) != expected_csv_sha256:
        raise ValueError("Research CSV SHA-256 mismatch.")
    try:
        manifest = json.loads(manifest_bytes)
        boundaries = [
            {
                "name": name,
                "start_inclusive": start.isoformat() if start else None,
                "end_exclusive": end.isoformat(),
            }
            for name, start, end in SPLITS
        ]
        if not (
            manifest["research_schema_version"] == 1
            and manifest["implementation_version"] == "stage-2a-v1"
            and manifest["dataset_file"] == "research.csv"
            and manifest["sha256"] == expected_csv_sha256
            and manifest["feature_definitions"] == FEATURE_DEFINITIONS
            and manifest["target_definition"] == TARGET_DEFINITION
            and manifest["split_boundaries"] == boundaries
            and manifest["split_clock"]
            == "feature_available_at; require target_available_at < split end"
            and manifest["settling_seconds"] == 60
            and manifest["exclusion_policy"] == EXCLUSION_POLICY
            and manifest["known_anomalies"] == list(KNOWN_ANOMALIES)
            and manifest["source_status"] == "incomplete"
            and manifest["incomplete_acknowledged"] is True
            and manifest["source_coverage"]["complete"] is False
            and set(manifest["source_coverage"]["markets"]) == set(SYMBOLS)
            and {s: v["splits"] for s, v in manifest["counts"].items()}
            == expected_counts
            and manifest["total_eligible_rows"]
            == sum(sum(v.values()) for v in expected_counts.values())
        ):
            raise ValueError("Incompatible research manifest.")
        reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"), newline=""))
        if reader.fieldnames != list(OUTPUT_COLUMNS):
            raise ValueError("Incompatible research CSV schema or feature order.")
        selected = select_rows(reader, manifest, training_only=training_only)
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("Malformed research metadata or row.") from error
    # Return only metadata needed by evaluation, excluding source target summaries.
    metadata = {
        k: manifest[k]
        for k in (
            "feature_definitions",
            "target_definition",
            "split_boundaries",
            "split_clock",
            "settling_seconds",
            "exclusion_policy",
            "known_anomalies",
            "source_selection_policy",
            "counts",
        )
    }
    metadata["input_hashes"] = {
        "research.csv": expected_csv_sha256,
        "manifest.json": expected_manifest_sha256,
    }
    return metadata, selected

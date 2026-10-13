"""Small causal research dataset; no model fitting, execution or provider I/O."""

import csv
import hashlib
import json
import math
import platform
from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import localcontext
from pathlib import Path
from statistics import fmean, pstdev

from backtest_badger.frozen import MANIFEST_SHA256, STEP, load_frozen, utc_time

IMPLEMENTATION_VERSION = "stage-2a-v1"
LOOKBACK = 6
SPLITS = (
    ("train", None, datetime(2024, 1, 1, tzinfo=UTC)),
    ("validation", datetime(2024, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC)),
    ("test", datetime(2025, 1, 1, tzinfo=UTC), datetime(2026, 10, 1, tzinfo=UTC)),
)
FEATURE_DEFINITIONS = {
    "log_return_4h": "ln(C[t]/C[t-1]); candles t-1 through t",
    "log_return_12h": "ln(C[t]/C[t-3]); uninterrupted candles t-3 through t",
    "log_return_24h": "ln(C[t]/C[t-6]); uninterrupted candles t-6 through t",
    "realised_volatility_24h": "sqrt(sum(r[i]^2), i=t-5..t), "
    "r[i]=ln(C[i]/C[i-1]); candles t-6 through t; unannualised, not demeaned",
    "relative_base_volume": "V[t]/mean(V[t-6..t-1]); candles t-6 through t; "
    "exclude if prior mean is zero",
}
TARGET_DEFINITION = (
    "ln(C[t+1]/C[t]); candles t and t+1 must be consecutive 4h identities"
)
KNOWN_ANOMALIES = (
    {
        "symbol": "BTCUSDT",
        "open_time": "2017-09-06T20:00:00+00:00",
        "reason": "Normal boundary, but economics match sole returned hour 23:00; "
        "does not establish continuous trading. Exclude all windows using this candle.",
        "evidence": "docs/stage-01b3-full-history.md"
        "#bounded-official-source-investigation",
    },
)
EXCLUSION_REASONS = (
    "outside_split_range",
    "split_boundary_label",
    "rolling_warmup",
    "source_end_target",
    "missing_candle_window",
    "known_anomaly_window",
    "zero_volume_history",
)
OUTPUT_COLUMNS = (
    "venue",
    "market_type",
    "symbol",
    "base_asset",
    "quote_asset",
    "interval_seconds",
    "open_time",
    "close_time",
    "feature_available_at",
    "target_open_time",
    "target_close_time",
    "target_available_at",
    "close",
    "base_volume",
    "version",
    "split",
    "known_anomaly",
    *FEATURE_DEFINITIONS,
    "target_log_return_4h",
    "prediction_zero",
    "prediction_train_mean",
)


def log_return(current, previous):
    # Preserve small relative moves before the final float conversion. Precision
    # includes each operand's full fixed-point span plus 32 guard digits.
    with localcontext() as context:
        context.prec = (
            max(
                len(v.as_tuple().digits) + abs(v.as_tuple().exponent)
                for v in (current, previous)
            )
            + 32
        )
        return float((current / previous).ln())


def causal_features(window):
    """Exactly seven already completed, consecutive candles, oldest first."""
    if len(window) != LOOKBACK + 1 or any(
        b["open_time"] - a["open_time"] != STEP or b["symbol"] != a["symbol"]
        for a, b in zip(window, window[1:], strict=False)
    ):
        raise ValueError("Features require seven consecutive candles from one market.")
    prices = [r["close"] for r in window]
    returns = [log_return(b, a) for a, b in zip(prices, prices[1:], strict=False)]
    volumes = [r["base_volume"] for r in window]
    with localcontext() as context:
        context.prec = (
            max(len(v.as_tuple().digits) + abs(v.as_tuple().exponent) for v in volumes)
            + 32
        )
        total = sum(volumes[:-1])
        if not total:
            return None
        volume_ratio = float(volumes[-1] * LOOKBACK / total)
    result = {
        "log_return_4h": returns[-1],
        "log_return_12h": log_return(prices[-1], prices[-4]),
        "log_return_24h": log_return(prices[-1], prices[0]),
        "realised_volatility_24h": math.sqrt(math.fsum(r * r for r in returns)),
        "relative_base_volume": volume_ratio,
    }
    if not all(math.isfinite(v) for v in result.values()):
        raise ValueError("Feature is outside finite floating-point range.")
    return result


def partition(available_at):
    for name, start, end in SPLITS:
        if (start is None or start <= available_at) and available_at < end:
            return name, end
    return None, None


def build_rows(markets, start, end, *, settling_seconds=60):
    """Consume validated candles. Classify every source row exactly once.

    Features only read t-6..t. Labels alone read t+1. Identity lookups, never row
    adjacency, determine the window. Older split context is allowed for features.
    """
    if type(settling_seconds) is not int or not 0 <= settling_seconds < 14400:
        raise ValueError("Settling seconds must be an integer from 0 through 14399.")
    delay = timedelta(seconds=settling_seconds)
    output, report, exclusions = [], {}, []
    for symbol, candles in sorted(markets.items()):
        by_time = {r["open_time"]: r for r in candles}
        anomalies = {
            utc_time(a["open_time"]) for a in KNOWN_ANOMALIES if a["symbol"] == symbol
        }
        dropped = Counter(dict.fromkeys(EXCLUSION_REASONS, 0))
        for candle in candles:
            opened = candle["open_time"]
            available = opened + STEP + delay
            target_available = opened + 2 * STEP + delay
            split, split_end = partition(available)
            times = [opened + i * STEP for i in range(-LOOKBACK, 2)]
            # Mutually exclusive reasons; overlapping missing/anomaly flags remain
            # visible in the manifest's exclusion audit.
            reason = None
            if split is None:
                reason = "outside_split_range"
            elif target_available >= split_end:
                reason = "split_boundary_label"
            elif times[0] < start:
                reason = "rolling_warmup"
            elif times[-1] >= end:
                reason = "source_end_target"
            elif any(t not in by_time for t in times):
                reason = "missing_candle_window"
            elif any(t in anomalies for t in times):
                reason = "known_anomaly_window"
            features = None
            if reason is None:
                features = causal_features([by_time[t] for t in times[:-1]])
                if features is None:
                    reason = "zero_volume_history"
            if reason:
                dropped[reason] += 1
                exclusions.append(
                    {
                        "symbol": symbol,
                        "open_time": opened.isoformat(),
                        "reason": reason,
                        "missing_in_range": [
                            t.isoformat()
                            for t in times
                            if start <= t < end and t not in by_time
                        ],
                        "known_anomalies": [
                            t.isoformat() for t in times if t in anomalies
                        ],
                    }
                )
                continue
            target = log_return(by_time[times[-1]]["close"], candle["close"])
            row = {key: candle[key] for key in OUTPUT_COLUMNS if key in candle}
            row.update(
                interval_seconds=14400,
                close_time=opened + STEP,
                feature_available_at=available,
                target_open_time=opened + STEP,
                target_close_time=opened + 2 * STEP,
                target_available_at=target_available,
                split=split,
                known_anomaly=False,
                **features,
                target_log_return_4h=target,
                prediction_zero=0.0,
                prediction_train_mean="",
            )
            output.append(row)
        counts = Counter(r["split"] for r in output if r["symbol"] == symbol)
        report[symbol] = {
            "source_rows": len(candles),
            "eligible_rows": sum(counts.values()),
            "splits": {name: counts[name] for name, _, _ in SPLITS},
            "dropped": dict(dropped),
        }
    return output, report, exclusions


def fit_reference(rows):
    """One per-market training-label mean; no preprocessing or holdout fitting."""
    means = {}
    for symbol in sorted({r["symbol"] for r in rows}):
        targets = [
            r["target_log_return_4h"]
            for r in rows
            if r["symbol"] == symbol and r["split"] == "train"
        ]
        if not targets:
            raise ValueError(f"No eligible training labels for {symbol}.")
        means[symbol] = fmean(targets)
    return means


def target_summaries(rows):
    summaries = {}
    for symbol in sorted({r["symbol"] for r in rows}):
        summaries[symbol] = {}
        for split in ("train", "validation"):
            values = [
                r["target_log_return_4h"]
                for r in rows
                if r["symbol"] == symbol and r["split"] == split
            ]
            summaries[symbol][split] = (
                {
                    "count": len(values),
                    "mean": fmean(values),
                    "std_population": pstdev(values),
                    "min": min(values),
                    "max": max(values),
                }
                if values
                else {"count": 0}
            )
        summaries[symbol]["test"] = (
            "withheld: genuine holdout; no target summary or scoring"
        )
    return summaries


def _cell(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def prepare_dataset(
    source,
    destination,
    *,
    acknowledge_incomplete=False,
    settling_seconds=60,
    **input_hashes,
):
    """Publish deterministic rows and manifest in an exclusively new directory."""
    manifest, markets = load_frozen(
        source, acknowledge_incomplete=acknowledge_incomplete, **input_hashes
    )
    rows, counts, exclusions = build_rows(
        markets,
        utc_time(manifest["start"]),
        utc_time(manifest["end_exclusive"]),
        settling_seconds=settling_seconds,
    )
    means = fit_reference(rows)
    for row in rows:
        if row["split"] != "train":
            row["prediction_train_mean"] = means[row["symbol"]]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()  # Never overwrite a research artifact or frozen source.
    partial = destination / "research.csv.partial"
    with partial.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(OUTPUT_COLUMNS)
        writer.writerows([_cell(row[c]) for c in OUTPUT_COLUMNS] for row in rows)
    digest = hashlib.sha256(partial.read_bytes()).hexdigest()
    source_hash = input_hashes.get("expected_manifest_sha256", MANIFEST_SHA256)
    report = {
        "research_schema_version": 1,
        "implementation_version": IMPLEMENTATION_VERSION,
        "implementation_sha256": {
            name: hashlib.sha256(
                Path(__file__).with_name(name).read_bytes()
            ).hexdigest()
            for name in ("features.py", "frozen.py", "candles.py", "research.py")
        },
        "python_version": platform.python_version(),
        "source_dataset_id": manifest["dataset_id"],
        "source_csv_sha256": manifest["sha256"],
        "source_manifest_sha256": source_hash,
        "source_status": manifest["status"],
        "incomplete_acknowledged": acknowledge_incomplete,
        "source_selection_policy": manifest["selection_policy"],
        "source_coverage": manifest["coverage"],
        "integrity": "Hashes, schema, UTC identities, order, economic constraints, "
        "counts and recorded missing/excluded identities verified; no unexpected gaps.",
        "feature_definitions": FEATURE_DEFINITIONS,
        "target_definition": TARGET_DEFINITION,
        "settling_seconds": settling_seconds,
        "availability": "All features at open_time + 4h + settling delay; "
        "label at open_time + 8h + settling delay. Modelled eligibility only, "
        "not historical provider publication or executable close fills.",
        "split_clock": "feature_available_at; require target_available_at < split end",
        "split_boundaries": [
            {
                "name": name,
                "start_inclusive": start.isoformat() if start else None,
                "end_exclusive": end.isoformat(),
            }
            for name, start, end in SPLITS
        ],
        "exclusion_policy": "Require every 4h candle t-6..t+1; never fill. "
        "Reject recorded gaps, excluded observations and known anomaly windows. "
        "Exclusive drop reason precedence: " + ", ".join(EXCLUSION_REASONS),
        "known_anomalies": KNOWN_ANOMALIES,
        "preprocessing": "None. No scaling, imputation, clipping or fitted features.",
        "reference_predictions": {
            "zero": 0.0,
            "training_mean_by_market": means,
            "training_mean_applied_to": ["validation", "test"],
        },
        "counts": counts,
        "exclusion_audit": exclusions,
        "total_eligible_rows": len(rows),
        "target_summaries": target_summaries(rows),
        "dataset_file": "research.csv",
        "sha256": digest,
    }
    manifest_partial = destination / "manifest.json.partial"
    manifest_partial.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    partial.rename(destination / "research.csv")
    manifest_partial.rename(destination / "manifest.json")
    return report

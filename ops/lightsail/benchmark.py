"""Offline synthetic full-size recording/replay benchmark; never uses live evidence."""

import argparse
import csv
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

BUDGET_SECONDS = 300
WATCHDOG_SECONDS = 600
ROOT = Path(__file__).resolve().parents[2]


def synthetic_source(folder):
    import numpy as np

    from backtest_badger import features, model_data
    from backtest_badger.frozen import STEP, SYMBOLS, grid_time

    rng = np.random.default_rng(42)
    counts = model_data.COUNTS
    manifest = {
        "research_schema_version": 1,
        "implementation_version": "stage-2a-v1",
        "dataset_file": "research.csv",
        "feature_definitions": features.FEATURE_DEFINITIONS,
        "target_definition": features.TARGET_DEFINITION,
        "split_boundaries": [
            {
                "name": name,
                "start_inclusive": start.isoformat() if start else None,
                "end_exclusive": end.isoformat(),
            }
            for name, start, end in features.SPLITS
        ],
        "split_clock": "feature_available_at; require target_available_at < split end",
        "settling_seconds": 60,
        "exclusion_policy": model_data.EXCLUSION_POLICY,
        "known_anomalies": list(features.KNOWN_ANOMALIES),
        "source_status": "incomplete",
        "incomplete_acknowledged": True,
        "source_selection_policy": "SYNTHETIC deployment benchmark; no market data",
        "source_coverage": {
            "complete": False,
            "start": "2017-08-17T04:00:00+00:00",
            "end_exclusive": "2026-10-01T00:00:00+00:00",
            "markets": {s: {"missing_intervals": []} for s in SYMBOLS},
        },
        "counts": {s: {"splits": c} for s, c in counts.items()},
        "total_eligible_rows": sum(sum(c.values()) for c in counts.values()),
    }
    folder.mkdir()
    with (folder / "research.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=features.OUTPUT_COLUMNS)
        writer.writeheader()
        for symbol in SYMBOLS:
            forbidden = {
                grid_time(a["open_time"])
                for a in features.KNOWN_ANOMALIES
                if a["symbol"] == symbol
            }
            for split, start in (
                ("train", datetime(2017, 8, 20, tzinfo=UTC)),
                ("validation", datetime(2023, 12, 31, 20, tzinfo=UTC)),
                ("test", datetime(2024, 12, 31, 20, tzinfo=UTC)),
            ):
                opened = start
                written = 0
                while written < counts[symbol][split]:
                    if not ({opened + i * STEP for i in range(-6, 2)} & forbidden):
                        row = dict.fromkeys(features.OUTPUT_COLUMNS, "synthetic")
                        row.update(
                            venue="binance",
                            market_type="spot",
                            symbol=symbol,
                            base_asset=symbol[:-4],
                            quote_asset="USDT",
                            interval_seconds="14400",
                            open_time=opened.isoformat(),
                            close_time=(opened + STEP).isoformat(),
                            feature_available_at=(
                                opened + STEP + timedelta(seconds=60)
                            ).isoformat(),
                            target_open_time=(opened + STEP).isoformat(),
                            target_close_time=(opened + 2 * STEP).isoformat(),
                            target_available_at=(
                                opened + 2 * STEP + timedelta(seconds=60)
                            ).isoformat(),
                            split=split,
                            known_anomaly="false",
                        )
                        values = rng.normal(size=len(model_data.FEATURES))
                        row.update(
                            zip(model_data.FEATURES, map(str, values), strict=True)
                        )
                        row[model_data.TARGET] = str(rng.normal(scale=0.02))
                        if split != "train":
                            # Fails if either held-out partition enters fitting.
                            row.update(
                                dict.fromkeys(
                                    (*model_data.FEATURES, model_data.TARGET),
                                    "NEVER_CONVERT",
                                )
                            )
                        writer.writerow(row)
                        written += 1
                    opened += STEP
    manifest["sha256"] = model_data.sha256((folder / "research.csv").read_bytes())
    (folder / "manifest.json").write_text(json.dumps(manifest))
    return {
        "expected_csv_sha256": manifest["sha256"],
        "expected_manifest_sha256": model_data.sha256(
            (folder / "manifest.json").read_bytes()
        ),
        "expected_counts": counts,
    }


def synthetic_window(symbol, opened):
    from backtest_badger.frozen import STEP

    market = dict(
        market_id=1 if symbol == "BTCUSDT" else 2,
        venue="binance",
        market_type="spot",
        symbol=symbol,
        base_asset=symbol[:-4],
        quote_asset="USDT",
    )
    rows = []
    for i in range(7):
        start = opened + (i - 6) * STEP
        rows.append(
            dict(
                market_id=market["market_id"],
                interval_seconds=14400,
                open_time=start,
                open=Decimal(100 + i),
                high=Decimal(110 + i),
                low=Decimal(90 + i),
                close=Decimal(101 + i),
                base_volume=Decimal(10 + i),
                quote_volume=Decimal(1000),
                taker_buy_base_volume=Decimal(1),
                taker_buy_quote_volume=Decimal(100),
                trade_count=10,
                version=1,
                observed_at=start + STEP + timedelta(seconds=60),
                recorded_at=start + STEP + timedelta(seconds=61),
                last_observed_at=start + STEP + timedelta(seconds=60),
                source_kind="rest",
                source_sha256="a" * 64,
                source_url=f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=4h&timeZone=0&limit=1000",
            )
        )
    return market, rows


def child():
    started = time.monotonic()
    from backtest_badger import forward, model_data

    def deny_network(event, args):
        if event in ("socket.connect", "socket.getaddrinfo"):
            raise RuntimeError("Network access forbidden in synthetic benchmark")

    sys.addaudithook(deny_network)
    with tempfile.TemporaryDirectory(prefix="badger-synthetic-") as temporary:
        folder = Path(temporary)
        # CWD fingerprint files match the selected source, never copied evidence.
        for name in ("uv.lock", "pyproject.toml"):
            shutil.copyfile(ROOT / name, folder / name)
        os.chdir(folder)
        pins = synthetic_source(folder / "source")
        load = model_data.load_model_data

        def synthetic_load(path, *, training_only):
            assert training_only is True
            return load(path, training_only=True, **pins)

        opened = datetime(2026, 10, 14, 8, tzinfo=UTC)
        now = opened + forward.STEP + timedelta(minutes=2)
        timings = {}
        with patch.object(forward, "load_model_data", synthetic_load):
            for symbol in forward.SYMBOLS:
                tick = time.monotonic()
                with patch.object(
                    forward,
                    "read_window",
                    return_value=synthetic_window(symbol, opened),
                ):
                    record, _ = forward.record_forward(
                        None,
                        symbol,
                        source=folder / "source",
                        destination=folder / "records",
                        clock=lambda: now,
                        publication_deadline=now + timedelta(minutes=15),
                    )
                # Full verifier: hashes, loading, refitting, recipe and numerics.
                forward.verify_forward(record, source=folder / "source")
                timings[symbol] = time.monotonic() - tick
        elapsed = time.monotonic() - started
        print(
            json.dumps(
                {
                    "kind": "synthetic_deployment_benchmark_not_forward_evidence",
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                    "python": platform.python_version(),
                    "training_counts": {
                        s: c["train"] for s, c in model_data.COUNTS.items()
                    },
                    "record_and_replay_seconds": timings,
                    "total_seconds": elapsed,
                    "peak_rss_native_units": resource.getrusage(
                        resource.RUSAGE_SELF
                    ).ru_maxrss,
                    "peak_rss_units": "bytes" if sys.platform == "darwin" else "KiB",
                    "budget_seconds": BUDGET_SECONDS,
                    "passed": elapsed < BUDGET_SECONDS,
                    "limitations": "Synthetic workload; excludes provider/DB latency "
                    "and host contention. "
                    "Must repeat under target resource limits before cutover.",
                },
                indent=2,
            )
        )
        return 0 if elapsed < BUDGET_SECONDS else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        return child()
    try:
        return subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), "--child"],
            timeout=WATCHDOG_SECONDS,
            check=False,
        ).returncode
    except subprocess.TimeoutExpired:
        print(
            "Synthetic benchmark exceeded 600-second watchdog; cutover blocked.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Read only pinned validation forecasts; never open research labels or fit models."""

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from backtest_badger.execution_data import END, HOUR, START
from backtest_badger.frozen import STEP, SYMBOLS, grid_time, utc_time
from backtest_badger.model_data import CSV_SHA256 as RESEARCH_SHA256
from backtest_badger.model_data import sha256

CSV_SHA256 = "e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674"
MANIFEST_SHA256 = "af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581"
MODELS = ("zero", "training_mean", "ridge", "gradient_boosting")
COLUMNS = (
    "venue",
    "market_type",
    "symbol",
    "interval_seconds",
    "open_time",
    "feature_available_at",
    "model",
    "predicted_log_return_4h",
    "research_csv_sha256",
)
TOLERANCE = Decimal("1e-12")


@dataclass(frozen=True)
class Signal:
    symbol: str
    model: str
    open_time: datetime
    signal_time: datetime
    forecast: Decimal


def schedule(signal):
    """Eligibility uses only signal identity/timing; no execution prices or labels."""
    opened = grid_time(signal.open_time.isoformat())
    available = utc_time(signal.signal_time.isoformat())
    if (
        signal.symbol not in SYMBOLS
        or signal.model not in MODELS
        or available != opened + STEP + timedelta(seconds=60)
        or not START <= available < END
        or available + STEP >= END
    ):
        raise ValueError("Invalid validation signal identity or availability.")
    if not isinstance(signal.forecast, Decimal) or not signal.forecast.is_finite():
        raise ValueError("Forecast must be a finite Decimal.")
    entry = available.replace(minute=0, second=0, microsecond=0) + HOUR
    exit_time = opened + 2 * STEP
    if not available < entry < exit_time:
        raise ValueError(
            "Execution must follow availability and precede target endpoint."
        )
    return entry, exit_time


def should_enter(signal):
    """The entire direction rule; deliberately has no price input."""
    return signal.forecast > TOLERANCE


def load_forecasts(
    directory,
    *,
    expected_csv_sha256=CSV_SHA256,
    expected_manifest_sha256=MANIFEST_SHA256,
):
    """Alternate pins are for synthetic tests only, never CLI options."""
    manifest_body = (directory / "manifest.json").read_bytes()
    body = (directory / "validation_predictions.csv").read_bytes()
    if (
        sha256(manifest_body) != expected_manifest_sha256
        or sha256(body) != expected_csv_sha256
    ):
        raise ValueError("Forecast artifact SHA-256 mismatch.")
    accounts = {(s, m): [] for s in SYMBOLS for m in MODELS}
    try:
        manifest = json.loads(manifest_body)
        if not (
            manifest["experiment_version"] == "stage-2b-v1"
            and manifest["evaluation_partition"] == "validation"
            and manifest["fit_partition"] == "train"
            and manifest["output_sha256"]["validation_predictions.csv"] == sha256(body)
            and manifest["input"]["input_hashes"]["research.csv"] == RESEARCH_SHA256
            and manifest["input"]["settling_seconds"] == 60
        ):
            raise ValueError("Incompatible forecast manifest.")
        reader = csv.DictReader(io.StringIO(body.decode(), newline=""), strict=True)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("Incompatible forecast schema.")
        previous = None
        for row in reader:
            if None in row or None in row.values():
                raise ValueError("Malformed forecast row.")
            if (
                row["venue"] != "binance"
                or row["market_type"] != "spot"
                or row["interval_seconds"] != "14400"
                or row["research_csv_sha256"] != RESEARCH_SHA256
            ):
                raise ValueError("Inconsistent forecast source identity.")
            signal = Signal(
                row["symbol"],
                row["model"],
                grid_time(row["open_time"]),
                utc_time(row["feature_available_at"]),
                Decimal(row["predicted_log_return_4h"]),
            )
            schedule(signal)
            identity = (signal.symbol, signal.open_time, MODELS.index(signal.model))
            if previous is not None and identity <= previous:
                raise ValueError("Duplicate or nonchronological forecasts.")
            previous = identity
            if signal.model == "zero" and signal.forecast != 0:
                raise ValueError("Zero baseline must be zero.")
            if signal.model == "training_mean" and signal.forecast != Decimal(
                format(manifest["markets"][signal.symbol]["training_mean"], ".17g")
            ):
                raise ValueError("Training-mean baseline differs from frozen model.")
            accounts[signal.symbol, signal.model].append(signal)
        expected = [START - STEP + i * STEP for i in range(2195)]
        for (symbol, _), signals in accounts.items():
            if [s.open_time for s in signals] != expected or manifest["markets"][
                symbol
            ]["validation_count"] != len(signals):
                raise ValueError("Forecast validation grid or count mismatch.")
    except (KeyError, TypeError, IndexError, InvalidOperation, csv.Error) as error:
        raise ValueError("Malformed forecast metadata or row.") from error
    return {
        "manifest.json": sha256(manifest_body),
        "validation_predictions.csv": sha256(body),
    }, accounts

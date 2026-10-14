"""Manual forward observations, exclusive local publication and offline replay.

Clocks are injectable for synthetic Python tests only. The CLI always uses UTC now.
No future candle, outcome, database writer or provider request belongs here.
"""

import json
import math
import os
import platform
import tempfile
from dataclasses import fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import numpy as np
from psycopg.rows import dict_row

from backtest_badger.candles import (
    PRICES,
    VOLUMES,
    CandleObservation,
    get_candles,
    validate_observation,
)
from backtest_badger.evaluation import fit_models, predict_models
from backtest_badger.features import (
    FEATURE_DEFINITIONS,
    TARGET_DEFINITION,
    causal_features,
)
from backtest_badger.frozen import STEP, SYMBOLS, grid_time, utc_time
from backtest_badger.model_data import FEATURES, load_model_data, sha256
from backtest_badger.recent import _json
from backtest_badger.research import research_snapshot
from backtest_badger.rest import eligible_end

TRAINING = Path("artifacts/research/stage-2a-v1")
RECORDS = Path("artifacts/forward-predictions")
MODELS = ("zero", "training_mean", "ridge", "gradient_boosting")
DELAY = timedelta(seconds=60)
OBSERVATION_FIELDS = tuple(f.name for f in fields(CandleObservation))
CANDLE_FIELDS = {*OBSERVATION_FIELDS, "version", "recorded_at", "last_observed_at"}
MARKET_FIELDS = {
    "market_id",
    "venue",
    "market_type",
    "symbol",
    "base_asset",
    "quote_asset",
}
TIME_FIELDS = ("open_time", "observed_at", "recorded_at", "last_observed_at")


def utc_now():
    return datetime.now(UTC)


def checked_clock(clock):
    value = clock()
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("Clock must return aware UTC timestamps.")
    return value


def current_open(now):
    opened = eligible_end(now, 60) - STEP
    if now >= opened + 2 * STEP:
        raise ValueError("New candle is still settling; wait until close + 60 seconds.")
    return opened


def read_window(connection, symbol, opened):
    """One read-only repeatable snapshot; query exactly t-6..t, never t+1."""
    if symbol not in SYMBOLS:
        raise ValueError("Symbol must be BTCUSDT or ETHUSDT.")
    with research_snapshot(connection):
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM market WHERE venue='binance' AND market_type='spot' "
                "AND symbol=%s",
                (symbol,),
            )
            market = cursor.fetchone()
        if market is None:
            raise ValueError("Required Binance Spot market is absent.")
        candles = get_candles(
            connection, market["market_id"], 14400, opened - 6 * STEP, opened + STEP
        )
    return market, candles


def validate_window(market, candles, opened, captured_at):
    symbol = market.get("symbol")
    if set(market) != MARKET_FIELDS or not (
        symbol in SYMBOLS
        and market["venue"] == "binance"
        and market["market_type"] == "spot"
        and market["base_asset"] == symbol.removesuffix("USDT")
        and market["quote_asset"] == "USDT"
    ):
        raise ValueError("Incorrect market identity.")
    for row in candles:
        if set(row) != CANDLE_FIELDS:
            raise ValueError("Unexpected source candle schema.")
        if any(
            not isinstance(row[k], datetime) or row[k].utcoffset() != timedelta(0)
            for k in TIME_FIELDS
        ):
            raise ValueError("Source timestamps must be aware UTC.")
    if not candles or candles[-1]["open_time"] < opened:
        raise ValueError(
            f"Stale data: required {symbol} candle opening {opened.isoformat()} "
            "has not been synchronised; run sync-recent separately."
        )
    if len(candles) != 7:
        raise ValueError("Exactly seven consecutive native 4h candles are required.")
    for i, row in enumerate(candles):
        validate_observation(
            CandleObservation(**{k: row[k] for k in OBSERVATION_FIELDS})
        )
        if not (
            row["market_id"] == market["market_id"]
            and row["interval_seconds"] == 14400
            and row["open_time"] == opened + (i - 6) * STEP
            and type(row["version"]) is int
            and row["version"] > 0
            and row["observed_at"] <= row["recorded_at"] <= captured_at
            and row["observed_at"] <= row["last_observed_at"] <= captured_at
        ):
            raise ValueError("Invalid candle grid, version, identity or source timing.")
        url = urlsplit(row["source_url"])
        if row["source_kind"] == "rest":
            query = parse_qs(url.query)
            valid_source = (
                url.hostname == "data-api.binance.vision"
                and url.path == "/api/v3/klines"
                and query.get("symbol") == [symbol]
                and query.get("interval") == ["4h"]
                and query.get("timeZone") == ["0"]
            )
        else:
            valid_source = (
                url.hostname == "data.binance.vision"
                and url.path
                == f"/data/spot/monthly/klines/{symbol}/4h/"
                f"{symbol}-4h-{row['open_time']:%Y-%m}.zip"
            )
        if url.scheme != "https" or not valid_source:
            raise ValueError(
                "Source provenance does not identify native Binance Spot 4h."
            )
    if current_open(captured_at) != opened:
        raise ValueError("Source window is no longer the current eligible horizon.")
    result = causal_features([dict(r, symbol=symbol) for r in candles])
    if result is None:
        raise ValueError("Cannot calculate relative volume from zero-volume history.")
    return [result[name] for name in FEATURES]


def fit_forward(symbol, source=TRAINING):
    """Deterministically refit the fixed Stage 2B recipe on pre-2024 rows only."""
    metadata, data = load_model_data(source, training_only=True)
    rows = data[symbol]["train"]
    x = np.asarray([r["features"] for r in rows])
    y = np.asarray([r["target"] for r in rows])
    mean, models = fit_models(x, y)
    ridge = models["ridge"]
    recipe = {
        "policy": "Fixed Stage 2B estimators; separate market; pre-2024 training only",
        "symbol": symbol,
        "training_count": len(rows),
        "training_rows_sha256": sha256(canonical(rows)),
        "input_hashes": metadata["input_hashes"],
        "training_end_exclusive": "2024-01-01T00:00:00+00:00",
        "parameters": {
            "zero": {"constant": 0.0},
            "training_mean": {"constant": mean},
            "ridge": ridge.named_steps["regressor"].get_params(),
            "ridge_scaler": ridge.named_steps["scale"].get_params(),
            "gradient_boosting": models["gradient_boosting"].get_params(),
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            **{
                p: version(p)
                for p in (
                    "numpy",
                    "scikit-learn",
                    "scipy",
                    "joblib",
                    "threadpoolctl",
                    "psycopg",
                )
            },
        },
        "implementation_sha256": {
            name: sha256(Path(__file__).with_name(name).read_bytes())
            for name in (
                "forward.py",
                "features.py",
                "evaluation.py",
                "model_data.py",
                "frozen.py",
                "candles.py",
                "rest.py",
                "research.py",
                "recent.py",
                "cli.py",
                "db.py",
                "config.py",
            )
        },
        "dependency_files_sha256": {
            name: sha256(Path(name).read_bytes())
            for name in ("uv.lock", "pyproject.toml")
        },
    }
    # Fingerprint the recipe without serialising executable estimators.
    recipe["model_recipe_sha256"] = sha256(canonical(recipe))
    return mean, models, recipe


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def record_id(symbol, opened):
    return f"binance-spot-{symbol}-4h-{opened:%Y%m%dT%H%M%SZ}"


def evidence(
    market, candles, features, predictions, recipe, captured, calculated, issued
):
    opened = candles[-1]["open_time"]
    identity = record_id(market["symbol"], opened)
    return _json(
        {
            "schema_version": 1,
            "kind": "unscored_forward_observation",
            "record_id": identity,
            "market": market,
            "interval_seconds": 14400,
            "source_open_time": opened,
            "source_close_boundary": opened + STEP,
            "feature_available_at": opened + STEP + DELAY,
            "captured_at": captured,
            "calculated_at": calculated,
            "issued_at": issued,
            "target_open_time": opened + STEP,
            "target_close_boundary": opened + 2 * STEP,
            "horizon_seconds": 14400,
            "target_definition": TARGET_DEFINITION,
            "feature_names": list(FEATURES),
            "feature_definitions": FEATURE_DEFINITIONS,
            "feature_values": features,
            "source_candles": candles,
            "model": recipe,
            "predictions": [
                {
                    "prediction_id": f"{identity}:{name}",
                    "model_id": name,
                    "predicted_log_return_4h": predictions[name],
                }
                for name in MODELS
            ],
        }
    )


def check_timing(opened, captured, calculated, issued, final):
    if not opened + STEP + DELAY <= captured <= calculated <= issued <= final:
        raise ValueError(
            "Clock reversed or prediction was not calculated before issuance."
        )
    if final >= opened + 2 * STEP:
        raise ValueError("Target has already closed; forward publication refused.")
    if current_open(final) != opened:
        raise ValueError("Prediction no longer concerns the current eligible horizon.")


class PublicationDeadlineExceeded(ValueError):
    """The optional unattended publication window has elapsed."""


def publish(record, destination, clock, *, publication_deadline=None):
    """Fsync a private staging file; final clock check then exclusive atomic link.

    A crash can leave a .partial file; it is never a published record and does not
    reserve the identity. A link wins exactly once, including concurrent writers.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    record["content_sha256"] = sha256(canonical(record))
    body = canonical(record) + b"\n"
    fd, name = tempfile.mkstemp(
        prefix=".forward-", suffix=".partial", dir=destination.parent
    )
    partial = Path(name)
    linked = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fchmod(handle.fileno(), 0o444)
            os.fsync(handle.fileno())
        final = checked_clock(clock)
        if publication_deadline is not None and final >= publication_deadline:
            raise PublicationDeadlineExceeded(
                "Unattended publication deadline elapsed."
            )
        check_timing(
            grid_time(record["source_open_time"]),
            utc_time(record["captured_at"]),
            utc_time(record["calculated_at"]),
            utc_time(record["issued_at"]),
            final,
        )
        # No replace/rename: existing identities always win.
        os.link(partial, destination)
        linked = True
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as error:
        if linked:
            raise RuntimeError(
                f"Record visible at {destination}; durability is uncertain. "
                "verify the existing record before retrying."
            ) from error
        raise
    finally:
        partial.unlink(missing_ok=True)


def record_forward(
    connection,
    symbol,
    *,
    source=TRAINING,
    destination=RECORDS,
    clock=utc_now,
    publication_deadline=None,
):
    started = checked_clock(clock)
    opened = current_open(started)
    market, candles = read_window(connection, symbol, opened)
    captured = checked_clock(clock)
    if captured < started:
        raise ValueError("Clock reversed during source read.")
    features = validate_window(market, candles, opened, captured)
    path = destination / f"{record_id(symbol, opened)}.json"
    if path.exists():
        raise FileExistsError(f"Already recorded: {path}")
    mean, models, recipe = fit_forward(symbol, source)
    predictions = {
        k: float(v[0])
        for k, v in predict_models(mean, models, np.asarray([features])).items()
    }
    if set(predictions) != set(MODELS) or not all(
        map(math.isfinite, predictions.values())
    ):
        raise ValueError("Expected four finite model predictions.")
    calculated = checked_clock(clock)
    issued = checked_clock(clock)
    check_timing(opened, captured, calculated, issued, issued)
    record = evidence(
        market, candles, features, predictions, recipe, captured, calculated, issued
    )
    publish(record, path, clock, publication_deadline=publication_deadline)
    return path, record


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key in forward evidence.")
        result[key] = value
    return result


def verify_forward(path, *, source=TRAINING):
    """Offline replay from retained inputs, never canonical candles or outcomes.

    Requires the recorded implementation/runtime/lockfile and pinned training data.
    Numerical tolerance matches Stage 2B (rtol=1e-10, atol=1e-12).
    """
    try:
        record = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
        if not isinstance(record, dict):
            raise ValueError("Expected a forward record JSON object.")
        digest = record.pop("content_sha256")
        if sha256(canonical(record)) != digest:
            raise ValueError("Forward record content SHA-256 mismatch.")
        opened = grid_time(record["source_open_time"])
        captured, calculated, issued = [
            utc_time(record[k]) for k in ("captured_at", "calculated_at", "issued_at")
        ]
        check_timing(opened, captured, calculated, issued, issued)
        candles = []
        for item in record["source_candles"]:
            if set(item) != CANDLE_FIELDS or any(
                type(item[k]) is not str for k in (*PRICES, *VOLUMES)
            ):
                raise ValueError("Invalid retained candle schema/Decimal encoding.")
            row = item.copy()
            row.update({k: utc_time(row[k]) for k in TIME_FIELDS})
            row.update({k: Decimal(row[k]) for k in (*PRICES, *VOLUMES)})
            candles.append(row)
        features = validate_window(record["market"], candles, opened, captured)
        mean, models, recipe = fit_forward(record["market"]["symbol"], source)
        predictions = {
            k: float(v[0])
            for k, v in predict_models(mean, models, np.asarray([features])).items()
        }
        expected = evidence(
            record["market"],
            candles,
            features,
            predictions,
            recipe,
            captured,
            calculated,
            issued,
        )
        # Check numerical output separately; every other schema/evidence field is exact.
        if len(record["predictions"]) != len(MODELS):
            raise ValueError("Expected exactly four predictions.")
        for saved, replay in zip(
            record["predictions"], expected["predictions"], strict=True
        ):
            value = saved["predicted_log_return_4h"]
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not math.isclose(
                    value,
                    replay["predicted_log_return_4h"],
                    rel_tol=1e-10,
                    abs_tol=1e-12,
                )
            ):
                raise ValueError("Forecast does not reproduce from retained evidence.")
            replay["predicted_log_return_4h"] = value
        if canonical(expected) != canonical(record):
            raise ValueError(
                "Forward schema, features, identity or model provenance mismatch."
            )
    except (KeyError, TypeError, IndexError, AttributeError, ArithmeticError) as error:
        raise ValueError("Malformed forward record.") from error
    return {
        "record_id": record["record_id"],
        "content_sha256": digest,
        "verified": True,
        "status": "unscored observation; no outcomes accessed",
    }

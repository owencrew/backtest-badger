"""Fixed Stage 2B experiment: train-only fitting and validation-only evaluation."""

import csv
import io
import json
import platform
from importlib.metadata import version
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from backtest_badger.frozen import SYMBOLS
from backtest_badger.model_data import FEATURES, TARGET, load_model_data, sha256

SEED = 42
ZERO_TOLERANCE = 1e-12
PREDICTION_COLUMNS = (
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
METRIC_DEFINITIONS = {
    "units": "Dimensionless next-four-hour close-to-close log returns.",
    "mae": "mean(abs(prediction - target))",
    "rmse": "sqrt(mean((prediction - target)**2))",
    "relative_improvement": "1 - model error / baseline error; positive is better; "
    "null if baseline error is zero. Reported separately for MAE and RMSE.",
    "skill_vs_train_mean": "1 - model MSE / training-mean forecast MSE on validation; "
    "null if denominator is zero. Not R2 against the validation mean.",
    "pearson": "Pearson correlation; null if fewer than two rows or either "
    "standard deviation <= 1e-12 * max(1, maximum absolute value).",
    "directional_accuracy": "Fraction of nonzero forecasts with sign equal to "
    "target sign. abs(prediction) <= 1e-12 is an abstention; exact zero realised "
    "returns count as incorrect for nonzero forecasts. Null at zero coverage. "
    "A constant nonzero forecast has defined direction accuracy but no correlation.",
    "forecast_coverage": "Fraction of validation rows with abs(prediction) > 1e-12.",
}
LIMITATIONS = (
    "Correlation measures co-movement, regression errors measure numerical forecast "
    "accuracy, and directional accuracy measures sign agreement at stated coverage. "
    "None establishes executable trading profitability. Returns are noisy; market "
    "conditions change; BTC and ETH are correlated and are not independent evidence. "
    "These are retrospective provider observations and one fixed 2024 validation "
    "period. Close-to-close labels are not executable trade returns; fees, spreads, "
    "slippage and latency are unmodelled. No statistical significance is claimed: "
    "ordinary differences do not account for time dependence. Test outcomes remain "
    "withheld. No model selection, tuning, signals, backtest or deployment is done."
)


def make_models():
    return {
        "ridge": Pipeline(
            [
                ("scale", StandardScaler()),
                ("regressor", Ridge(alpha=1.0, solver="svd")),
            ]
        ),
        "gradient_boosting": GradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.03,
            n_estimators=100,
            max_depth=2,
            min_samples_leaf=100,
            subsample=1.0,
            n_iter_no_change=None,
            random_state=SEED,
        ),
    }


def fit_models(train_x, train_y):
    """No validation/test argument exists; each call creates independent estimators."""
    models = make_models()
    with threadpool_limits(limits=1):
        for model in models.values():
            model.fit(train_x, train_y)
    return float(np.mean(train_y)), models


def predict_models(mean, models, validation_x):
    with threadpool_limits(limits=1):
        return {
            "zero": np.zeros(len(validation_x)),
            "training_mean": np.full(len(validation_x), mean),
            **{name: model.predict(validation_x) for name, model in models.items()},
        }


def metrics(target, prediction, training_mean):
    target, prediction = (
        np.asarray(target, dtype=float),
        np.asarray(prediction, dtype=float),
    )
    if (
        target.ndim != 1
        or prediction.shape != target.shape
        or not len(target)
        or not np.isfinite(target).all()
        or not np.isfinite(prediction).all()
        or not np.isfinite(training_mean)
    ):
        raise ValueError("Metrics require nonempty matching finite return vectors.")
    error = prediction - target
    mae, mse = float(np.mean(np.abs(error))), float(np.mean(error**2))
    rmse = float(np.sqrt(mse))
    baseline_errors = {
        "zero": -target,
        "training_mean": training_mean - target,
    }
    relative = {}
    for name, residual in baseline_errors.items():
        bmae = float(np.mean(np.abs(residual)))
        brmse = float(np.sqrt(np.mean(residual**2)))
        relative[name] = {
            "mae": 1 - mae / bmae if bmae else None,
            "rmse": 1 - rmse / brmse if brmse else None,
        }
    denominator = float(np.mean(baseline_errors["training_mean"] ** 2))
    corr = None
    if len(target) >= 2 and all(
        np.std(v) > ZERO_TOLERANCE * max(1.0, float(np.max(np.abs(v))))
        for v in (prediction, target)
    ):
        corr = float(np.corrcoef(prediction, target)[0, 1])
    covered = np.abs(prediction) > ZERO_TOLERANCE
    return {
        "count": len(target),
        "mae": mae,
        "rmse": rmse,
        "relative_improvement": relative,
        "skill_vs_train_mean": 1 - mse / denominator if denominator else None,
        "pearson": corr,
        "pearson_undefined_reason": None
        if corr is not None
        else "Too few observations or constant/near-constant prediction or target.",
        "directional_accuracy": float(
            np.mean(np.sign(prediction[covered]) == np.sign(target[covered]))
        )
        if covered.any()
        else None,
        "directional_undefined_reason": None
        if covered.any()
        else "No nonzero forecasts.",
        "nonzero_forecast_count": int(covered.sum()),
        "forecast_coverage": float(np.mean(covered)),
        "zero_realised_count": int(np.sum(target == 0)),
    }


def _display(value, *, percent=False):
    if value is None:
        return "undefined"
    return f"{value:.3%}" if percent else f"{value:.8f}"


def summary(report):
    lines = [
        "# Stage 2B validation results",
        "",
        "Separate market fits on pre-2024 training data; evaluation only on 2024.",
        "All errors are dimensionless log returns. Positive improvements are better.",
        "",
        "| Market | Model | Train | Validation | MAE | RMSE | "
        "MAE improvement vs zero / mean | RMSE improvement vs zero / mean | "
        "Skill vs mean | Pearson | Direction | Coverage |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | "
        "---: | ---: | ---: | ---: |",
    ]
    interpretations = []
    for symbol, result in report["markets"].items():
        for name, m in result["validation_metrics"].items():
            r = m["relative_improvement"]
            fields = [
                symbol,
                name,
                str(result["training_count"]),
                str(m["count"]),
                _display(m["mae"]),
                _display(m["rmse"]),
            ]
            fields.extend(
                " / ".join(
                    _display(r[b][metric], percent=True)
                    for b in ("zero", "training_mean")
                )
                for metric in ("mae", "rmse")
            )
            fields.extend(
                [
                    _display(m["skill_vs_train_mean"]),
                    _display(m["pearson"]),
                    _display(m["directional_accuracy"], percent=True),
                    _display(m["forecast_coverage"], percent=True),
                ]
            )
            lines.append("| " + " | ".join(fields) + " |")
        for name in ("ridge", "gradient_boosting"):
            m = result["validation_metrics"][name]
            better = all(
                v is not None and v > 0
                for b in m["relative_improvement"].values()
                for v in b.values()
            )
            interpretations.append(
                f"\n{symbol} {name}: "
                + (
                    "lower MAE and RMSE than both baselines."
                    if better
                    else "does not improve both MAE and RMSE against both baselines."
                )
            )
    lines.extend(interpretations)
    lines.extend(["", "## Metric conventions", ""])
    lines.extend(f"- **{k}**: {v}" for k, v in METRIC_DEFINITIONS.items())
    lines.extend(["", LIMITATIONS, ""])
    return "\n".join(lines)


def evaluate_models(source, destination, **input_checks):
    """Publish only in a new directory, with manifest last; never overwrite."""
    if destination.exists():
        raise FileExistsError(destination)
    metadata, data = load_model_data(source, **input_checks)
    report = {
        "experiment_version": "stage-2b-v1",
        "input": metadata,
        "feature_order": list(FEATURES),
        "target": TARGET,
        "fit_partition": "train",
        "evaluation_partition": "validation",
        "test_policy": "Integrity hash and structural checks only; no numerical "
        "test targets, predictions or metrics enter evaluation.",
        "metric_definitions": METRIC_DEFINITIONS,
        "random_seed": SEED,
        "thread_limit": 1,
        "reproducibility_tolerance": {"rtol": 1e-10, "atol": 1e-12},
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            **{
                p: version(p)
                for p in ("numpy", "scikit-learn", "scipy", "joblib", "threadpoolctl")
            },
        },
        "implementation_sha256": {
            name: sha256(Path(__file__).with_name(name).read_bytes())
            for name in ("evaluation.py", "model_data.py", "features.py", "frozen.py")
        },
        "preprocessing": "Ridge: training-fitted StandardScaler in Pipeline; "
        "boosting: none. No imputation, clipping, target transform or refitting.",
        "limitations": LIMITATIONS,
        "markets": {},
    }
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(PREDICTION_COLUMNS)
    for symbol in SYMBOLS:
        train, validation = data[symbol]["train"], data[symbol]["validation"]
        train_x = np.asarray([r["features"] for r in train])
        train_y = np.asarray([r["target"] for r in train])
        validation_x = np.asarray([r["features"] for r in validation])
        validation_y = np.asarray([r["target"] for r in validation])
        mean, models = fit_models(train_x, train_y)
        predictions = predict_models(mean, models, validation_x)
        ridge = models["ridge"]
        result = {
            "training_count": len(train),
            "validation_count": len(validation),
            "training_mean": mean,
            "validation_metrics": {},
            "model_parameters": {
                "zero": {"constant": 0.0},
                "training_mean": {"constant": mean},
                "ridge": ridge.named_steps["regressor"].get_params(),
                "ridge_scaler": ridge.named_steps["scale"].get_params(),
                "gradient_boosting": models["gradient_boosting"].get_params(),
            },
            "fitted_scaler": {
                "mean": ridge.named_steps["scale"].mean_.tolist(),
                "scale": ridge.named_steps["scale"].scale_.tolist(),
                "n_samples_seen": int(ridge.named_steps["scale"].n_samples_seen_),
            },
        }
        for name, prediction in predictions.items():
            result["validation_metrics"][name] = metrics(validation_y, prediction, mean)
        for i, row in enumerate(validation):
            for name, prediction in predictions.items():
                writer.writerow(
                    [
                        "binance",
                        "spot",
                        symbol,
                        14400,
                        row["open_time"],
                        row["feature_available_at"],
                        name,
                        format(prediction[i], ".17g"),
                        metadata["input_hashes"]["research.csv"],
                    ]
                )
        report["markets"][symbol] = result
    files = {
        "validation_predictions.csv": buffer.getvalue().encode(),
        "summary.md": summary(report).encode(),
    }
    report["output_sha256"] = {name: sha256(body) for name, body in files.items()}
    files["manifest.json"] = (
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    for name, body in files.items():
        partial = destination / (name + ".partial")
        with partial.open("xb") as handle:
            handle.write(body)
        partial.rename(destination / name)
    return report

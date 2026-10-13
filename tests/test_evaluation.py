"""Synthetic fixtures only: the real test holdout is never loaded by tests."""

import copy
import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from backtest_badger import cli, evaluation, model_data
from backtest_badger.features import (
    FEATURE_DEFINITIONS,
    KNOWN_ANOMALIES,
    OUTPUT_COLUMNS,
    SPLITS,
    TARGET_DEFINITION,
)
from backtest_badger.frozen import STEP, SYMBOLS
from backtest_badger.model_data import FEATURES, TARGET, sha256


@pytest.fixture
def research_source(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    counts = {s: {"train": 240, "validation": 12, "test": 3} for s in SYMBOLS}
    manifest = {
        "research_schema_version": 1,
        "implementation_version": "stage-2a-v1",
        "dataset_file": "research.csv",
        "feature_definitions": FEATURE_DEFINITIONS,
        "target_definition": TARGET_DEFINITION,
        "split_boundaries": [
            {
                "name": name,
                "start_inclusive": start.isoformat() if start else None,
                "end_exclusive": end.isoformat(),
            }
            for name, start, end in SPLITS
        ],
        "split_clock": "feature_available_at; require target_available_at < split end",
        "settling_seconds": 60,
        "exclusion_policy": model_data.EXCLUSION_POLICY,
        "known_anomalies": list(KNOWN_ANOMALIES),
        "source_status": "incomplete",
        "incomplete_acknowledged": True,
        "source_selection_policy": "Synthetic",
        "source_coverage": {
            "complete": False,
            "start": "2023-01-01T00:00:00+00:00",
            "end_exclusive": "2026-10-01T00:00:00+00:00",
            "markets": {s: {"missing_intervals": []} for s in SYMBOLS},
        },
        "counts": {s: {"splits": c} for s, c in counts.items()},
        "total_eligible_rows": 510,
    }
    rows = []
    for market_index, symbol in enumerate(SYMBOLS):
        for split, start in (
            ("train", datetime(2023, 11, 1, tzinfo=UTC)),
            ("validation", datetime(2023, 12, 31, 20, tzinfo=UTC)),
            ("test", datetime(2024, 12, 31, 20, tzinfo=UTC)),
        ):
            for i in range(counts[symbol][split]):
                opened = start + i * STEP
                row = dict.fromkeys(OUTPUT_COLUMNS, "unused")
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
                row.update(
                    {
                        f: str((i + 1) * (j + 1) / 100 + market_index)
                        for j, f in enumerate(FEATURES)
                    }
                )
                row[TARGET] = (
                    "DO_NOT_PARSE_TEST"
                    if split == "test"
                    else str((i % 7 - 3) / 100 + market_index / 1000)
                )
                rows.append(row)

    def write(header=OUTPUT_COLUMNS):
        with (source / "research.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        manifest["sha256"] = sha256((source / "research.csv").read_bytes())
        (source / "manifest.json").write_text(json.dumps(manifest))
        return {
            "expected_csv_sha256": manifest["sha256"],
            "expected_manifest_sha256": sha256((source / "manifest.json").read_bytes()),
            "expected_counts": counts,
        }

    return source, rows, manifest, write


def test_selection_order_and_test_outcome_barrier(research_source):
    source, rows, manifest, write = research_source
    metadata, selected = model_data.load_model_data(source, **write())
    assert metadata["feature_definitions"] == FEATURE_DEFINITIONS
    for s in SYMBOLS:
        assert set(selected[s]) == {"train", "validation"}
        assert len(selected[s]["train"]) == 240
        assert len(selected[s]["validation"]) == 12
        assert selected[s]["validation"][0]["open_time"].startswith("2023-12-31T20")
    assert selected["BTCUSDT"]["train"][0]["features"] == [0.01, 0.02, 0.03, 0.04, 0.05]

    class Guard(dict):
        def __getitem__(self, key):
            if self.get("split") == "test" and key in (
                TARGET,
                "prediction_train_mean",
                "prediction_zero",
            ):
                pytest.fail("Attempted to access a holdout outcome/baseline")
            return super().__getitem__(key)

    assert model_data.select_rows(map(Guard, rows), manifest) == selected


@pytest.mark.parametrize("file", ["research.csv", "manifest.json"])
def test_hash_mismatch_before_fitting(research_source, tmp_path, monkeypatch, file):
    source, _, _, write = research_source
    checks = write()
    with (source / file).open("ab") as handle:
        handle.write(b" ")
    monkeypatch.setattr(
        evaluation, "fit_models", lambda *a: pytest.fail("Fitted bad input")
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        evaluation.evaluate_models(source, tmp_path / "out", **checks)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda m: m.update(target_definition="different"),
        lambda m: m.update(feature_definitions={}),
        lambda m: m.update(settling_seconds=0),
        lambda m: m.update(exclusion_policy="fill gaps"),
        lambda m: m.update(known_anomalies=[]),
        lambda m: m["split_boundaries"][1].update(start_inclusive="2023-01-01"),
        lambda m: m["counts"]["BTCUSDT"]["splits"].update(train=241),
        lambda m: m.pop("target_definition"),
    ],
)
def test_manifest_contract(research_source, mutation):
    source, _, manifest, write = research_source
    mutation(manifest)
    checks = write()
    # The reviewed expected count must remain independent of mutated metadata.
    checks["expected_counts"] = {
        s: {"train": 240, "validation": 12, "test": 3} for s in SYMBOLS
    }
    with pytest.raises(ValueError):
        model_data.load_model_data(source, **checks)


@pytest.mark.parametrize(
    "field,value",
    [
        (FEATURES[0], "nan"),
        (FEATURES[1], "inf"),
        (FEATURES[2], ""),
        (TARGET, "-inf"),
        ("symbol", "SOLUSDT"),
        ("venue", "other"),
        ("known_anomaly", "true"),
        ("split", "validation"),
        ("open_time", "2023-11-01T00:01:00Z"),
        ("feature_available_at", "2023-11-01T04:00:00Z"),
        ("target_available_at", "2023-11-01T04:01:00Z"),
    ],
)
def test_invalid_rows(research_source, field, value):
    source, rows, _, write = research_source
    rows[0][field] = value
    with pytest.raises(ValueError):
        model_data.load_model_data(source, **write())


@pytest.mark.parametrize("case", ["reorder", "duplicate", "missing", "gap", "purge"])
def test_chronology_counts_and_gaps(research_source, case):
    source, rows, manifest, write = research_source
    if case == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif case == "duplicate":
        rows.insert(0, copy.deepcopy(rows[0]))
    elif case == "missing":
        rows.pop(0)
    elif case == "gap":
        manifest["source_coverage"]["markets"]["BTCUSDT"]["missing_intervals"] = [
            rows[0]["open_time"]
        ]
    else:
        # Label crosses into 2024: it must be purged, not relabelled as training.
        row = rows[239]
        opened = datetime(2023, 12, 31, 16, tzinfo=UTC)
        for field, offset in (
            ("open_time", timedelta()),
            ("close_time", STEP),
            ("target_open_time", STEP),
            ("target_close_time", 2 * STEP),
            ("feature_available_at", STEP + timedelta(seconds=60)),
            ("target_available_at", 2 * STEP + timedelta(seconds=60)),
        ):
            row[field] = (opened + offset).isoformat()
    with pytest.raises(ValueError):
        model_data.load_model_data(source, **write())


@pytest.mark.parametrize("case", ["swap", "missing"])
def test_feature_schema(research_source, case):
    source, _, _, write = research_source
    header = list(OUTPUT_COLUMNS)
    if case == "swap":
        a, b = header.index(FEATURES[0]), header.index(FEATURES[1])
        header[a], header[b] = header[b], header[a]
    else:
        header.remove(FEATURES[0])
    with pytest.raises(ValueError, match="schema or feature order"):
        model_data.load_model_data(source, **write(header))


def test_train_only_scaling_fitting_and_repeatability():
    rng = np.random.default_rng(23)
    x = rng.normal(size=(250, 5))
    y = x[:, 0] / 100 + 0.002
    mean, models = evaluation.fit_models(x, y)
    assert mean == pytest.approx(y.mean())
    scale = models["ridge"].named_steps["scale"]
    np.testing.assert_allclose(scale.mean_, x.mean(axis=0))
    np.testing.assert_allclose(scale.var_, x.var(axis=0))
    assert scale.n_samples_seen_ == 250
    assert models["gradient_boosting"].n_estimators_ == 100
    assert models["gradient_boosting"].n_iter_no_change is None
    validation = x[:10] + 1000
    before = scale.mean_.copy()
    predictions = evaluation.predict_models(mean, models, validation)
    np.testing.assert_array_equal(scale.mean_, before)
    assert np.all(predictions["zero"] == 0)
    assert np.all(predictions["training_mean"] == mean)
    mean2, models2 = evaluation.fit_models(x, y)
    for name, actual in evaluation.predict_models(mean2, models2, validation).items():
        np.testing.assert_allclose(actual, predictions[name], rtol=1e-10, atol=1e-12)


def test_hand_calculated_metrics():
    m = evaluation.metrics([1, -1, 0], [2, -2, 0], 0.5)
    assert m["mae"] == pytest.approx(2 / 3)
    assert m["rmse"] == pytest.approx(np.sqrt(2 / 3))
    assert m["relative_improvement"]["zero"] == pytest.approx({"mae": 0, "rmse": 0})
    assert m["relative_improvement"]["training_mean"]["mae"] == pytest.approx(
        1 - 2 / 2.5
    )
    assert m["skill_vs_train_mean"] == pytest.approx(1 - 2 / 2.75)
    assert m["pearson"] == pytest.approx(1)
    assert m["directional_accuracy"] == 1
    assert m["forecast_coverage"] == pytest.approx(2 / 3)
    assert m["zero_realised_count"] == 1


def test_constant_near_constant_and_zero_conventions():
    zero = evaluation.metrics([-1, 0, 1], [0, 0, 0], 0)
    assert zero["pearson"] is None
    assert zero["directional_accuracy"] is None
    assert zero["forecast_coverage"] == 0
    constant = evaluation.metrics([-1, 0, 1], [0.1, 0.1, 0.1], 0.1)
    assert constant["pearson"] is None
    assert constant["directional_accuracy"] == pytest.approx(1 / 3)
    assert constant["forecast_coverage"] == 1
    near = evaluation.metrics([-1, 0, 1], [0, 1e-14, -1e-14], 0)
    assert near["pearson"] is near["directional_accuracy"] is None
    undefined = evaluation.metrics([0, 0], [0, 0], 0)
    assert undefined["skill_vs_train_mean"] is None
    assert undefined["relative_improvement"]["zero"]["rmse"] is None
    assert evaluation.metrics([1, 1], [1, 2], 1)["pearson"] is None
    assert evaluation.metrics([1], [1], 1)["pearson"] is None


@pytest.mark.parametrize(
    "y,p", [([], []), ([1], [1, 2]), ([np.nan], [1]), ([1], [np.inf])]
)
def test_invalid_metric_inputs(y, p):
    with pytest.raises(ValueError):
        evaluation.metrics(y, p, 0)


def test_artifacts_repeatability_and_label_isolation(research_source, tmp_path):
    source, rows, _, write = research_source
    checks = write()
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    first, second = tmp_path / "first", tmp_path / "second"
    report = evaluation.evaluate_models(source, first, **checks)
    assert evaluation.evaluate_models(source, second, **checks) == report
    for path in first.iterdir():
        assert path.read_bytes() == (second / path.name).read_bytes()
    for name, digest in report["output_sha256"].items():
        assert sha256((first / name).read_bytes()) == digest
    assert {p.name: p.read_bytes() for p in source.iterdir()} == before
    with pytest.raises(FileExistsError):
        evaluation.evaluate_models(source, first, **checks)
    with (first / "validation_predictions.csv").open() as handle:
        reader = csv.DictReader(handle)
        assert TARGET not in reader.fieldnames
        predictions = list(reader)
    assert len(predictions) == 12 * 2 * 4
    assert all(p["feature_available_at"].startswith("2024-") for p in predictions)
    for row in rows:
        if row["split"] == "test":
            row[TARGET] = "CHANGED_OPAQUE_TEST_OUTCOME"
    holdout = tmp_path / "holdout-changed"
    holdout_report = evaluation.evaluate_models(source, holdout, **write())
    assert holdout_report["markets"] == report["markets"]
    for row in rows:
        if row["split"] == "validation":
            row[TARGET] = str(float(row[TARGET]) + 5)
    third = tmp_path / "third"
    changed = evaluation.evaluate_models(source, third, **write())
    with (third / "validation_predictions.csv").open() as handle:
        changed_predictions = list(csv.DictReader(handle))
    assert [p["predicted_log_return_4h"] for p in predictions] == [
        p["predicted_log_return_4h"] for p in changed_predictions
    ]
    for symbol in SYMBOLS:
        a, b = report["markets"][symbol], changed["markets"][symbol]
        assert a["training_mean"] == b["training_mean"]
        assert a["fitted_scaler"] == b["fitted_scaler"]
        assert a["validation_metrics"] != b["validation_metrics"]


def test_market_fits_are_independent(research_source, tmp_path):
    source, rows, _, write = research_source
    first = evaluation.evaluate_models(source, tmp_path / "first", **write())
    for row in rows:
        if row["symbol"] == "BTCUSDT" and row["split"] == "train":
            row[TARGET] = str(float(row[TARGET]) + 1)
    second = evaluation.evaluate_models(source, tmp_path / "second", **write())
    assert first["markets"]["ETHUSDT"] == second["markets"]["ETHUSDT"]
    assert first["markets"]["BTCUSDT"] != second["markets"]["BTCUSDT"]


def test_offline_cli(monkeypatch, tmp_path, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("Offline evaluation requested configuration/database")

    monkeypatch.setattr(cli, "load_settings", forbidden)
    monkeypatch.setattr(cli, "connect_database", forbidden)
    seen = []
    monkeypatch.setattr(evaluation, "evaluate_models", lambda *a: seen.append(a))
    assert cli.main(["evaluate-models", "--output", str(tmp_path)]) == 0
    assert seen == [(Path("artifacts/research/stage-2a-v1"), tmp_path)]
    assert "Validation summary" in capsys.readouterr().out


@pytest.mark.parametrize(
    "error", [ValueError("bad hash"), FileExistsError(), OSError()]
)
def test_cli_failure(monkeypatch, tmp_path, error):
    def fail(*args):
        raise error

    monkeypatch.setattr(evaluation, "evaluate_models", fail)
    assert cli.main(["evaluate-models", "--output", str(tmp_path)]) == 1

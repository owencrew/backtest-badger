"""Synthetic projection tests; no genuine evidence, database, scoring or model fits."""

import importlib.util
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "public_forward_export",
    Path(__file__).parents[1] / "scripts/public_forward_export.py",
)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


@pytest.fixture
def synthetic():
    clock = datetime(2026, 10, 15, 13, tzinfo=UTC)
    record = {
        "record_id": "SYNTHETIC-TEST-IDENTITY",
        "market": {"symbol": "BTCUSDT"},
        "source_open_time": "2026-10-15T00:00:00+00:00",
        "target_open_time": "2026-10-15T04:00:00+00:00",
        "target_close_boundary": "2026-10-15T08:00:00+00:00",
        "issued_at": "2026-10-15T04:01:00+00:00",
        "model": {"model_recipe_sha256": "a" * 64, "private": "DO_NOT_PUBLISH"},
        "predictions": [
            {"model_id": m, "predicted_log_return_4h": 0} for m in exporter.MODELS
        ],
        "private_path": "DO_NOT_PUBLISH",
    }
    cohort = exporter.evaluator.COHORTS[0]
    score = {
        "evaluation_captured_at": "2026-10-15T08:02:00+00:00",
        "actual_log_return_4h": 0,
        "model_errors": {m: dict.fromkeys(exporter.ERRORS, 0) for m in exporter.MODELS},
        "private": "DO_NOT_PUBLISH",
    }
    report = {
        "evidence_valid": True,
        "partial_outcomes": 0,
        "protocol": {
            "version": "stage-3c-v1",
            "sha256": exporter.evaluator.PROTOCOL_SHA256,
        },
        "as_of": clock.isoformat(),
        "markets": {},
        "private": "DO_NOT_PUBLISH",
    }
    for symbol in exporter.evaluator.SYMBOLS:
        report["markets"][symbol] = {"cohorts": {}}
        for name in exporter.evaluator.COHORTS:
            n = int(symbol == "BTCUSDT" and name == cohort)
            report["markets"][symbol]["cohorts"][name] = {
                "genuine_predictions": n,
                "matched_count": n,
                "pending_not_settled": 0,
                "mature_unscored": 0,
                "missing_predictions": None,
                "matched_record_ids": [record["record_id"]] if n else [],
                "models": {
                    m: {
                        "mae": 0 if n else None,
                        "rmse": 0 if n else None,
                        "forecast_bias": 0 if n else None,
                        "directional_correct": 0,
                        "directional_denominator": 0,
                        "directional_accuracy": None,
                        "private": "DO_NOT_PUBLISH",
                    }
                    for m in exporter.MODELS
                },
            }
    return report, [{"record": record, "score": score, "cohort": cohort}], clock


def test_projection_is_allowlisted_and_browser_contract_accepts_it(synthetic, tmp_path):
    value = exporter.project(*synthetic)
    body = json.dumps(value)
    assert "DO_NOT_PUBLISH" not in body
    assert "SYNTHETIC-TEST-IDENTITY" not in body
    assert len(value["evaluations"]) == 6
    path = tmp_path / "synthetic-candidate.json"
    exporter.write_candidate(value, path)
    result = subprocess.run(
        ["node", "--import", "tsx", "scripts/validate-forward.ts", str(path)],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("fault", ["invalid", "partial", "mismatch"])
def test_projection_fails_closed(synthetic, fault):
    report, observations, clock = synthetic
    if fault == "invalid":
        report["evidence_valid"] = False
    elif fault == "partial":
        report["partial_outcomes"] = 1
    else:
        observations.clear()
    with pytest.raises(ValueError):
        exporter.project(report, observations, clock)


def test_failed_serialisation_preserves_previous_candidate(tmp_path):
    path = tmp_path / "candidate.json"
    path.write_text("previous")
    with pytest.raises(ValueError):
        exporter.write_candidate({"invalid": float("nan")}, path)
    assert path.read_text() == "previous"


def test_missing_inputs_do_not_create_empty_valid_feed(tmp_path):
    with pytest.raises(ValueError):
        exporter.prepare(tmp_path / "missing", tmp_path, tmp_path)

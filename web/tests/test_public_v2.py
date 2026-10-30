"""Synthetic retained projections and transaction faults; never publish fixtures."""

import copy
import json
import subprocess
from pathlib import Path

import pytest
from test_public_export import exporter
from test_public_export import synthetic as base_synthetic


@pytest.fixture
def synthetic():
    return base_synthetic.__wrapped__()


@pytest.fixture
def v2(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "scripts"))
    import public_forward_v2

    return public_forward_v2


def enrich(synthetic):
    report, observations, clock = synthetic
    score = observations[0]["score"]
    score["cohort"] = {"name": observations[0]["cohort"]}
    for error in score["model_errors"].values():
        error.update(actual_direction=0, directional_correct=None)
    return report, observations, clock


def summary(report, observations):
    for symbol in exporter.evaluator.SYMBOLS:
        for cohort in exporter.evaluator.COHORTS:
            rows = [
                r
                for r in observations
                if r["record"]["market"]["symbol"] == symbol and r["cohort"] == cohort
            ]
            e = report["markets"][symbol]["cohorts"][cohort]
            ids = [r["record"]["record_id"] for r in rows if r["score"]]
            e.update(
                genuine_predictions=len(rows),
                matched_count=len(ids),
                matched_record_ids=ids,
                pending_not_settled=len(rows) - len(ids),
            )
            for model in e["models"].values():
                model.update(
                    mae=0 if ids else None,
                    rmse=0 if ids else None,
                    forecast_bias=0 if ids else None,
                )


def add_row(
    observations,
    *,
    symbol="BTCUSDT",
    hour=8,
    cohort="primary_timely_automated",
    scored=True,
):
    row = copy.deepcopy(observations[0])
    row["cohort"] = cohort
    r = row["record"]
    r.update(
        record_id=f"SYNTHETIC-{symbol}-{hour}",
        market={"symbol": symbol},
        source_open_time=f"2026-10-15T{hour - 4:02}:00:00+00:00",
        target_open_time=f"2026-10-15T{hour:02}:00:00+00:00",
        target_close_boundary=f"2026-10-15T{hour + 4:02}:00:00+00:00",
        issued_at=f"2026-10-15T{hour:02}:01:00+00:00",
    )
    if scored:
        row["score"]["cohort"]["name"] = cohort
        row["score"]["evaluation_captured_at"] = f"2026-10-15T{hour + 4:02}:02:00+00:00"
    else:
        row["score"] = None
    observations.append(row)
    return row


def test_latest_scored_independent_markets_pending_and_v1_projection(
    v2, synthetic, tmp_path
):
    report, rows, clock = enrich(synthetic)
    btc = add_row(rows)
    eth = add_row(rows, symbol="ETHUSDT", hour=4)
    add_row(rows, hour=12, scored=False)
    summary(report, rows)
    result = v2.project(report, rows, clock)
    assert [r["source_close_at"] for r in result["latest_scored"]] == [
        "2026-10-15T08:00:00Z",
        "2026-10-15T04:00:00Z",
    ]
    assert result["latest"][0]["status"] == "pending_not_settled"
    assert result["latest"][0]["actual_log_return_4h"] is None
    for projected, saved in zip(result["latest_scored"], (btc, eth), strict=True):
        assert (
            projected["recipe_sha256"]
            == saved["record"]["model"]["model_recipe_sha256"]
        )
        for m in exporter.MODELS:
            assert (
                projected["models"][m]["signed_error"]
                == saved["score"]["model_errors"][m]["signed_error"]
            )
    projection = {k: v for k, v in result.items() if k != "latest_scored"}
    projection["schema_version"] = 1
    assert projection == exporter.project(report, rows, clock)
    assert "DO_NOT_PUBLISH" not in json.dumps(result)
    assert "SYNTHETIC-" not in json.dumps(result)
    path = tmp_path / "synthetic.json"
    exporter.write_candidate(result, path)
    subprocess.run(
        ["node", "--import", "tsx", "scripts/validate-forward-v2.ts", str(path)],
        cwd=Path(__file__).parents[1],
        check=True,
        capture_output=True,
    )


@pytest.mark.parametrize("cohort", ["secondary_late_manual", "timely_unattributed"])
def test_newer_other_cohort_never_substitutes(v2, synthetic, cohort):
    report, rows, clock = enrich(synthetic)
    add_row(rows, cohort=cohort)
    summary(report, rows)
    result = v2.project(report, rows, clock)
    assert result["latest"][0]["cohort"] == cohort
    assert result["latest_scored"][0]["source_close_at"] == "2026-10-15T04:00:00Z"
    rows.pop(0)
    summary(report, rows)
    assert v2.project(report, rows, clock)["latest_scored"] == []


def test_empty_scored(v2, synthetic):
    report, rows, clock = enrich(synthetic)
    rows.clear()
    summary(report, rows)
    assert v2.project(report, rows, clock)["latest_scored"] == []


@pytest.mark.parametrize(
    "fault",
    ["duplicate", "source_tie", "matched_ids", "future_score", "cohort", "direction"],
)
def test_ambiguous_or_inconsistent_evidence_fails_closed(v2, synthetic, fault):
    report, rows, clock = enrich(synthetic)
    if fault in ("duplicate", "source_tie"):
        rows.append(copy.deepcopy(rows[0]))
        if fault == "source_tie":
            rows[1]["record"]["record_id"] = "different"
        summary(report, rows)
    elif fault == "matched_ids":
        report["markets"]["BTCUSDT"]["cohorts"][rows[0]["cohort"]][
            "matched_record_ids"
        ] = ["other"]
    elif fault == "future_score":
        rows[0]["score"]["evaluation_captured_at"] = "2026-10-15T13:00:01Z"
    elif fault == "cohort":
        rows[0]["score"]["cohort"]["name"] = "timely_unattributed"
    else:
        rows[0]["score"]["model_errors"]["ridge"]["actual_direction"] = 1
    with pytest.raises(ValueError):
        v2.project(report, rows, clock)


@pytest.mark.parametrize(
    "fault", ["record", "outcome", "journal", "added", "removed", "replaced"]
)
def test_prepare_detects_byte_inventory_changes(v2, tmp_path, monkeypatch, fault):
    folders = [tmp_path / n for n in ("records", "outcomes", "operations")]
    for folder in folders:
        folder.mkdir()
        (folder / "saved.json").write_text("original")
    (folders[2] / "logs").mkdir()  # Unrelated operational logs are not evidence.

    def prepare(*args, **kwargs):
        if fault in ("record", "outcome", "journal"):
            (
                folders[("record", "outcome", "journal").index(fault)] / "saved.json"
            ).write_text("changed")
        elif fault == "added":
            (folders[0] / "new.json").write_text("added")
        elif fault == "removed":
            (folders[1] / "saved.json").unlink()
        else:
            p = folders[0] / "saved.json"
            p.unlink()
            p.write_text("original")
        return {}

    monkeypatch.setattr(v2.v1, "prepare", prepare)
    with pytest.raises(ValueError, match="changed"):
        v2.prepare(*folders)


def test_inventory_rejects_evidence_symlinks(v2, tmp_path):
    (tmp_path / "record.json").symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError):
        v2.inventory([tmp_path])


@pytest.mark.parametrize("fault", ["validator", "clock", "version", "size", "prepare"])
def test_v2_staging_failure_preserves_previous(
    v2, synthetic, tmp_path, monkeypatch, fault
):
    import stage_forward_snapshot as staging

    value = v2.project(*enrich(synthetic))
    output = tmp_path / "last-v2.json"
    exporter.write_candidate(value, output)
    previous = output.read_bytes()
    if fault == "clock":
        value["as_of"] = value["generated_at"] = "2026-10-15T12:59:00Z"
    elif fault == "version":
        old = copy.deepcopy(value)
        old["schema_version"] = 1
        exporter.write_candidate(old, output)
        previous = output.read_bytes()
    elif fault == "size":
        monkeypatch.setattr(staging, "MAX_BYTES", 1)
    elif fault == "validator":
        value["latest_scored"][0]["models"]["zero"]["directional_correct"] = True

    def prepare(*args):
        if fault == "prepare":
            raise ValueError("changed")
        return value

    monkeypatch.setattr(v2, "prepare", prepare)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        staging.stage(
            tmp_path / "records",
            tmp_path / "outcomes",
            tmp_path / "operations",
            output,
            schema_version=2,
        )
    assert output.read_bytes() == previous
    assert not list(tmp_path.glob(".forward-stage-*"))


def test_v2_staging_atomic_and_publication_disabled(
    v2, synthetic, tmp_path, monkeypatch
):
    import stage_forward_snapshot as staging

    value = v2.project(*enrich(synthetic))
    monkeypatch.setattr(v2, "prepare", lambda *args: value)
    output = tmp_path / "last-v2.json"
    sources = [tmp_path / n for n in ("records", "outcomes", "operations")]
    staging.stage(*sources, output, schema_version=2)
    assert json.loads(output.read_text()) == value
    assert output.stat().st_mode & 0o777 == 0o600
    with pytest.raises(ValueError, match="private preparation"):
        staging.stage(
            *sources,
            output,
            schema_version=2,
            r2_object="backtest-badger-forward/forward-v2.json",
        )


@pytest.mark.parametrize("fault", ["removed", "changed", "older"])
def test_v2_staging_rejects_retained_score_regression(
    v2, synthetic, tmp_path, monkeypatch, fault
):
    import stage_forward_snapshot as staging

    value = v2.project(*enrich(synthetic))
    output = tmp_path / "last-v2.json"
    exporter.write_candidate(value, output)
    previous = output.read_bytes()
    if fault == "removed":
        value["latest_scored"] = []
    elif fault == "changed":
        value["latest_scored"][0]["recipe_sha256"] = "b" * 64
    else:
        value["latest_scored"][0]["source_close_at"] = "2026-10-15T00:00:00Z"
    monkeypatch.setattr(v2, "prepare", lambda *args: value)
    # Isolate the transaction's monotonicity check after contract validation.
    monkeypatch.setattr(staging.subprocess, "run", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="regressed or changed"):
        staging.stage(
            tmp_path / "records",
            tmp_path / "outcomes",
            tmp_path / "operations",
            output,
            schema_version=2,
        )
    assert output.read_bytes() == previous


def test_selection_uses_candle_chronology_not_late_scoring_clock(v2, synthetic):
    report, rows, clock = enrich(synthetic)
    add_row(rows)
    rows[0]["score"]["evaluation_captured_at"] = "2026-10-15T12:59:00Z"
    summary(report, rows)
    result = v2.project(report, list(reversed(rows)), clock)
    assert result["latest_scored"][0]["source_close_at"] == "2026-10-15T08:00:00Z"
    assert result["latest_scored"][0]["scored_at"] == "2026-10-15T12:02:00Z"


def test_prepare_excludes_outcome_after_cutoff_without_inventing_a_score(
    v2, synthetic, tmp_path, monkeypatch
):
    from datetime import datetime

    report, rows, clock = enrich(synthetic)
    future_score = copy.deepcopy(rows[0]["score"])
    future_score["evaluation_captured_at"] = "2026-10-15T13:00:00.000001Z"
    rows[0]["score"] = None
    summary(report, rows)
    e = report["markets"]["BTCUSDT"]["cohorts"][rows[0]["cohort"]]
    e.update(pending_not_settled=0, mature_unscored=1)
    folders = [tmp_path / n for n in ("records", "outcomes", "operations")]
    for folder in folders:
        folder.mkdir()
    (folders[0] / "saved.json").write_text("synthetic loader input")
    (folders[1] / "saved.json").write_text("synthetic loader input")

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock

    monkeypatch.setattr(v2.v1, "datetime", Clock)
    monkeypatch.setattr(v2.v1.evaluator, "report", lambda **kwargs: report)
    monkeypatch.setattr(v2.v1.evaluator, "journals", lambda *args: ([], []))
    monkeypatch.setattr(
        v2.v1.evaluator, "load_prediction", lambda *args: {"record": rows[0]["record"]}
    )
    monkeypatch.setattr(v2.v1.evaluator, "load_outcome", lambda *args: future_score)
    monkeypatch.setattr(
        v2.v1.evaluator, "classify", lambda *args: {"name": rows[0]["cohort"]}
    )
    value = v2.prepare(*folders)
    assert value["latest_scored"] == []
    assert value["latest"][0]["status"] == "mature_unscored"
    assert value["latest"][0]["actual_log_return_4h"] is None

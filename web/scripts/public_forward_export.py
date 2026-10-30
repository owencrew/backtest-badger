"""Prepare a public-safe candidate from retained evidence; never connect or score.

Run from the repository root with the existing locked Python environment. Output
is a private review candidate. Hosting and scheduling need separate authorisation.
"""

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from backtest_badger import forward_evaluation as evaluator

MODELS = ("zero", "training_mean", "ridge", "gradient_boosting")
METRICS = (
    "mae",
    "rmse",
    "forecast_bias",
    "directional_correct",
    "directional_denominator",
    "directional_accuracy",
)
ERRORS = ("signed_error", "absolute_error", "squared_error")
COUNTS = (
    "genuine_predictions",
    "matched_count",
    "pending_not_settled",
    "mature_unscored",
    "missing_predictions",
)


def utc(value):
    if isinstance(value, str):
        value = evaluator.utc_time(value)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def project_forecast(item, as_of):
    """Public allowlist shared by latest-issued and latest-scored observations."""
    record, score = item["record"], item["score"]
    return {
        "symbol": record["market"]["symbol"],
        "source_close_at": utc(record["target_open_time"]),
        "issued_at": utc(record["issued_at"]),
        "target_close_at": utc(record["target_close_boundary"]),
        "recipe_sha256": record["model"]["model_recipe_sha256"],
        "cohort": item["cohort"],
        "status": "scored"
        if score
        else (
            "pending_not_settled"
            if evaluator.utc_time(as_of)
            < evaluator.utc_time(record["target_close_boundary"])
            + evaluator.forward.DELAY
            else "mature_unscored"
        ),
        "scored_at": utc(score["evaluation_captured_at"]) if score else None,
        "actual_log_return_4h": score["actual_log_return_4h"] if score else None,
        "models": {
            p["model_id"]: {
                "predicted_log_return_4h": p["predicted_log_return_4h"],
                **{
                    k: score["model_errors"][p["model_id"]][k] if score else None
                    for k in ERRORS
                },
            }
            for p in record["predictions"]
        },
    }


def project(report, observations, generated_at):
    """Allowlist projection only: all scores/metrics come from the frozen evaluator."""
    if not report["evidence_valid"] or report["partial_outcomes"]:
        raise ValueError("Invalid or partial evidence; no public export produced.")
    latest = []
    evaluations = []
    for symbol in evaluator.SYMBOLS:
        market_rows = [
            r for r in observations if r["record"]["market"]["symbol"] == symbol
        ]
        if market_rows:
            item = max(market_rows, key=lambda r: r["record"]["source_open_time"])
            latest.append(project_forecast(item, report["as_of"]))
        for cohort in evaluator.COHORTS:
            summary = report["markets"][symbol]["cohorts"][cohort]
            rows = [r for r in market_rows if r["cohort"] == cohort]
            # Ensure the projection and evaluator report refer to the same sample.
            matched = sorted(r["record"]["record_id"] for r in rows if r["score"])
            if len(rows) != summary["genuine_predictions"] or matched != sorted(
                summary["matched_record_ids"]
            ):
                raise ValueError(
                    "Evidence changed during export; retry from a stable copy."
                )
            evaluations.append(
                {
                    "symbol": symbol,
                    "cohort": cohort,
                    "first_target_close_at": min(
                        utc(r["record"]["target_close_boundary"]) for r in rows
                    )
                    if rows
                    else None,
                    **{k: summary[k] for k in COUNTS},
                    "models": {
                        m: {k: summary["models"][m][k] for k in METRICS} for m in MODELS
                    },
                }
            )
    return {
        "schema_version": 1,
        "kind": "public_forward_research",
        "data_source": "Binance Spot",
        "protocol": report["protocol"]["version"],
        "protocol_sha256": report["protocol"]["sha256"],
        "generated_at": utc(generated_at),
        "as_of": utc(report["as_of"]),
        "latest": latest,
        "evaluations": evaluations,
    }


def prepare(records, outcomes, operations, *, projector=project):
    if not all(p.is_dir() for p in (records, outcomes, operations)):
        raise ValueError("All three retained evidence directories are required.")
    as_of = datetime.now(UTC)
    arguments = dict(
        records=records, outcomes=outcomes, operations=operations, as_of=as_of
    )
    report = evaluator.report(**arguments)
    if not report["evidence_valid"] or report["partial_outcomes"]:
        raise ValueError("Invalid evidence.")
    cycles, invalid = evaluator.journals(operations)
    if invalid:
        raise ValueError("Invalid cohort evidence.")
    cycles = [(j, e) for j, e in cycles if evaluator.utc_time(j["started_at"]) <= as_of]
    observations = []
    for path in sorted(records.glob("*.json")):
        prediction = evaluator.load_prediction(path)
        record = prediction["record"]
        if evaluator.utc_time(record["issued_at"]) > as_of:
            continue
        score = None
        outcome_path = outcomes / path.name
        if os.path.lexists(outcome_path):
            candidate = evaluator.load_outcome(outcome_path, prediction)
            if evaluator.utc_time(candidate["evaluation_captured_at"]) <= as_of:
                score = candidate
        cohort = (
            score["cohort"]["name"]
            if score
            else evaluator.classify(prediction, cycles)["name"]
        )
        observations.append({"record": record, "score": score, "cohort": cohort})
    if evaluator.report(**arguments) != report:
        raise ValueError("Evidence changed during export; retry from a stable copy.")
    generated = datetime.now(UTC)
    if not 0 <= (generated - as_of).total_seconds() <= 300:
        raise ValueError("Export exceeded freshness budget.")
    return projector(report, observations, generated)


def write_candidate(value, destination):
    """Atomic local candidate replacement; output permissions remain private."""
    body = (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    fd, name = tempfile.mkstemp(prefix=".forward-public-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(name).unlink(missing_ok=True)


def check_destination(output, sources):
    """Candidates must never enter static assets or retained source evidence."""
    output = output.resolve()
    web = Path(__file__).resolve().parents[1]
    forbidden = [p.resolve() for p in sources] + [web / "public", web / "out"]
    if any(output.is_relative_to(p) for p in forbidden):
        raise ValueError("Output must be private and separate from source evidence.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("records", "outcomes", "operations", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    sources = [
        args.records.resolve(),
        args.outcomes.resolve(),
        args.operations.resolve(),
    ]
    output = args.output.resolve()
    try:
        check_destination(output, sources)
        value = prepare(*sources)
        write_candidate(value, output)
    except (OSError, ValueError, RuntimeError):
        # Do not expose evidence filenames, private paths, journals or raw exceptions.
        parser.exit(
            1, "Public export failed. Nothing published; inspect candidate privately.\n"
        )
    print("Public-safe candidate prepared for review. Nothing was published.")


if __name__ == "__main__":
    main()

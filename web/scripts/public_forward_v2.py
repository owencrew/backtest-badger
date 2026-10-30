"""Private v2 projection of retained evidence. No publication or scientific changes."""

import hashlib

import public_forward_export as v1


def project(report, observations, generated_at):
    # The existing projection checks every cohort's exact matched record IDs.
    base = v1.project(report, observations, generated_at)
    seen = set()
    identities = set()
    cutoff = v1.evaluator.utc_time(report["as_of"])
    for item in observations:
        record, score = item["record"], item["score"]
        key = (
            record["market"]["symbol"],
            v1.evaluator.utc_time(record["source_open_time"]),
        )
        if key in seen or record["record_id"] in identities:
            raise ValueError("Duplicate or ambiguous forecast evidence.")
        seen.add(key)
        identities.add(record["record_id"])
        if score and v1.evaluator.utc_time(score["evaluation_captured_at"]) > cutoff:
            raise ValueError("Score exceeds evidence cutoff.")
    selected = []
    for symbol in v1.evaluator.SYMBOLS:
        eligible = [
            r
            for r in observations
            if r["record"]["market"]["symbol"] == symbol
            and r["cohort"] == "primary_timely_automated"
            and r["score"] is not None
        ]
        if not eligible:
            continue
        item = max(
            eligible,
            key=lambda r: v1.evaluator.utc_time(r["record"]["source_open_time"]),
        )
        score = item["score"]
        if score["cohort"]["name"] != "primary_timely_automated":
            raise ValueError("Saved score cohort conflicts with selection.")
        # Reuse the exact v1 allowlist; selecting this row must not change
        # aggregate membership or any other original value.
        row = v1.project_forecast(item, report["as_of"])
        directions = {score["model_errors"][m]["actual_direction"] for m in v1.MODELS}
        if len(directions) != 1:
            raise ValueError("Conflicting saved outcome directions.")
        row["actual_direction"] = directions.pop()
        for model in v1.MODELS:
            row["models"][model]["directional_correct"] = score["model_errors"][model][
                "directional_correct"
            ]
        selected.append(row)
    return {**base, "schema_version": 2, "latest_scored": selected}


def inventory(sources):
    """Detect byte changes, replacement, additions and removals during preparation."""
    result = {}
    for folder in sources:
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Expected retained evidence directories.")
        for path in sorted({*folder.glob("*.json"), *folder.glob("*.partial")}):
            if path.is_symlink() or not path.is_file():
                raise ValueError("Expected regular retained evidence files.")
            stat = path.stat()
            result[str(path)] = (
                stat.st_ino,
                stat.st_mtime_ns,
                stat.st_ctime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
    return result


def prepare(records, outcomes, operations):
    sources = (records, outcomes, operations)
    before = inventory(sources)
    value = v1.prepare(*sources, projector=project)
    if inventory(sources) != before:
        raise ValueError("Retained evidence changed during v2 preparation.")
    return value

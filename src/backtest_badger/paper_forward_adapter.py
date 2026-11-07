"""Read a single expected Stage 3 horizon from explicitly selected evidence roots."""

import errno
import json
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from backtest_badger import forward
from backtest_badger import forward_evaluation as evaluation
from backtest_badger.paper_artifacts import directory, read_original
from backtest_badger.paper_types import Forecast, finite_decimal, grid, require, utc


class EvidenceError(ValueError):
    def __init__(self, code, filename):
        super().__init__(f"{code}: {filename}")
        self.code = code
        self.filename = filename


@dataclass(frozen=True)
class Original:
    """Stage 3's filename/read_bytes interface over a single pinned byte string."""

    name: str
    body: bytes

    def read_bytes(self):
        return self.body


@dataclass(frozen=True)
class Observation:
    forecast: Forecast
    prediction_id: str
    artifact_relpath: str
    journal: dict | None
    raw_record: bytes


def read_forecast(portfolio, opened, records, operations, clock):
    """None means an absent expected record in readable original directories."""
    name = forward.record_id(portfolio.symbol, grid(opened)) + ".json"
    source = name
    try:
        with directory(records) as fd:
            try:
                body = read_original(fd, name, 256 * 1024)
            except FileNotFoundError:
                body = None
        prediction = evaluation.load_prediction(Original(name, body)) if body else None
        require(body is None or prediction is not None, "Empty forecast.")
        cycles = []
        publishers = 0
        runs = set()
        latest_journal = opened
        with directory(operations) as fd:
            for source in sorted(os.listdir(fd)):
                if not source.endswith(".json"):
                    continue
                raw = read_original(fd, source, 128 * 1024)
                j = evaluation.parse_journal(raw)
                started = evaluation.utc_time(j["started_at"])
                require(
                    type(j["schema_version"]) is int
                    and j["run_id"] not in runs
                    and not (
                        j.keys()
                        - {
                            "schema_version",
                            "run_id",
                            "started_at",
                            "source_open_time",
                            "feature_available_at",
                            "deadline",
                            "state",
                            "finished_at",
                            "markets",
                            "error_category",
                        }
                    )
                    and source == f"{started:%Y%m%dT%H%M%S%fZ}-{j['run_id']}.json",
                    "Invalid original journal identity.",
                )
                runs.add(j["run_id"])
                if evaluation.grid_time(j["source_open_time"]) != opened:
                    continue
                finished = (
                    evaluation.utc_time(j["finished_at"])
                    if j["finished_at"]
                    else started
                )
                latest_journal = max(latest_journal, started, finished)
                item = j["markets"][portfolio.symbol]
                if item["status"] not in ("recorded", "already-recorded"):
                    require(
                        not (
                            item.keys()
                            & {"file_sha256", "content_sha256", "record_path"}
                        ),
                        "Unverified journal claim about original file.",
                    )
                    continue
                require(prediction is not None, "Journal references absent original.")
                path = Path(item["record_path"])
                require(
                    ".." not in path.parts
                    and path
                    in (
                        Path(records) / name,
                        (Path(records) / name).absolute(),
                        forward.RECORDS / name,
                    ),
                    "Journal source path mismatch.",
                )
                record = prediction["record"]
                require(
                    item["file_sha256"] == prediction["file_sha256"]
                    and item["content_sha256"] == prediction["content_sha256"]
                    and item["issued_at"] == record["issued_at"],
                    "Conflicting journal evidence.",
                )
                finished = j["finished_at"]
                require(
                    finished is None
                    or evaluation.utc_time(item["issued_at"])
                    <= evaluation.utc_time(finished),
                    "Journal predates publication.",
                )
                if item["status"] == "recorded":
                    require(
                        evaluation.matches_automation(j, prediction),
                        "Unverified automated publication.",
                    )
                    publishers += 1
                cycles.append(
                    (
                        j,
                        {
                            "filename": source,
                            "file_sha256": forward.sha256(raw),
                            "json_utf8": raw.decode("utf-8"),
                        },
                    )
                )
        require(publishers <= 1, "Multiple claimed automated publications.")
        observed = utc(clock.now())
        require(latest_journal <= observed, "Journal evidence postdates discovery.")
        if prediction is None:
            return None
        source = name
        cohort = evaluation.classify(prediction, cycles)
        evaluation.validate_cohort(cohort, prediction, observed)
        record = prediction["record"]
        require(
            record["model"]["model_recipe_sha256"] == portfolio.model_recipe_sha256,
            "Portfolio recipe fingerprint mismatch.",
        )
        # Read the canonical JSON number directly, after Stage 3 validates its bytes.
        exact = json.loads(body, parse_float=Decimal, parse_int=Decimal)
        ridge = next(p for p in exact["predictions"] if p["model_id"] == "ridge")
        journal = cohort["automation_evidence"]
        forecast = Forecast(
            portfolio,
            record["record_id"],
            opened,
            evaluation.utc_time(record["issued_at"]),
            observed,
            finite_decimal(ridge["predicted_log_return_4h"]),
            prediction["file_sha256"],
            prediction["content_sha256"],
            portfolio.model_recipe_sha256,
            journal["file_sha256"] if journal else None,
            cohort["name"],
        )
        return Observation(forecast, ridge["prediction_id"], name, journal, body)
    except OSError as error:
        code = (
            "invalid_original"
            if error.errno in (errno.ELOOP, errno.ENOTDIR, errno.EISDIR)
            else "original_unavailable"
        )
        raise EvidenceError(code, source) from error
    except (ValueError, RecursionError, *evaluation.MALFORMED) as error:
        raise EvidenceError("invalid_original", source) from error

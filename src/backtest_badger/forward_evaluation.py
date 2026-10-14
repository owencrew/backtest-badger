"""Preregistered forward scoring; no fitting, downloads, writes to DB or forecasts.

Run from the repository root with python -m backtest_badger.forward_evaluation.
Only Python tests inject clocks/connections. Production scoring uses actual UTC.
"""

import argparse
import json
import math
import os
import platform
import re
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import fmean

import psycopg
from psycopg.rows import dict_row

from backtest_badger import forward
from backtest_badger.candles import PRICES, VOLUMES, get_candles
from backtest_badger.config import load_settings
from backtest_badger.db import connect_database
from backtest_badger.features import log_return
from backtest_badger.frozen import STEP, SYMBOLS, grid_time, utc_time
from backtest_badger.recent import _json
from backtest_badger.research import research_snapshot

PROTOCOL_VERSION = "stage-3c-v1"
PROTOCOL = Path("docs/stage-03c-forward-evaluation-protocol.md")
PROTOCOL_SHA256 = "9bb655a374af27ecf41b0f31947dfad4256eb40e8973d53caf278507084d4bed"
OUTCOMES = Path("artifacts/forward-outcomes")
OPERATIONS = Path("artifacts/forward-operations")
START = datetime(2026, 10, 14, tzinfo=UTC)
PROMPTNESS = timedelta(minutes=15)
COHORTS = ("primary_timely_automated", "secondary_late_manual", "timely_unattributed")
MODELS = forward.MODELS
IMPLEMENTATION_FILES = (
    "forward_evaluation.py",
    "forward.py",
    "features.py",
    "candles.py",
    "frozen.py",
    "model_data.py",
    "recent.py",
    "research.py",
    "rest.py",
    "db.py",
    "config.py",
)
canonical, sha256 = forward.canonical, forward.sha256
LIMITATIONS = (
    "Candle-to-candle dimensionless log returns, not issued-at-to-close returns, "
    "percentages or trading results. Missingness may be selective. BTC/ETH and "
    "successive periods are correlated, not independent replications. Descriptive "
    "comparisons only: no significance, model promotion, alpha or profitability claim. "
    "100 observations is a reporting convention, not a power calculation."
)
MALFORMED = (KeyError, TypeError, IndexError, AttributeError, ArithmeticError)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest_ok(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def protocol():
    require(sha256(PROTOCOL.read_bytes()) == PROTOCOL_SHA256, "Protocol hash mismatch.")
    return {"version": PROTOCOL_VERSION, "sha256": PROTOCOL_SHA256}


def decode(body):
    result = json.loads(body, object_pairs_hook=forward._unique_object)
    require(isinstance(result, dict), "Expected JSON object.")
    # Also rejects JSON's nonstandard NaN/Infinity encodings anywhere in evidence.
    canonical(result)
    return result


def checked_file(path, checksum):
    body = path.read_bytes()
    value = decode(body)
    digest = value.pop(checksum)
    require(
        digest_ok(digest) and sha256(canonical(value)) == digest, "Checksum mismatch."
    )
    require(
        body == canonical(dict(value, **{checksum: digest})) + b"\n",
        "Exact file bytes do not match the published canonical encoding.",
    )
    return value, digest, sha256(body)


def candle_from_json(item):
    require(set(item) == forward.CANDLE_FIELDS, "Unexpected candle schema.")
    require(
        all(type(item[k]) is str for k in (*PRICES, *VOLUMES)),
        "Prices and volumes must retain exact Decimal strings.",
    )
    return {
        **item,
        **{k: utc_time(item[k]) for k in forward.TIME_FIELDS},
        **{k: Decimal(item[k]) for k in (*PRICES, *VOLUMES)},
    }


def validate_recipe(recipe, symbol, predictions):
    names = {
        "policy",
        "symbol",
        "training_count",
        "training_rows_sha256",
        "input_hashes",
        "training_end_exclusive",
        "parameters",
        "runtime",
        "implementation_sha256",
        "dependency_files_sha256",
        "model_recipe_sha256",
    }
    require(set(recipe) == names, "Unexpected model recipe schema.")
    unsigned = {k: v for k, v in recipe.items() if k != "model_recipe_sha256"}
    require(
        sha256(canonical(unsigned)) == recipe["model_recipe_sha256"],
        "Recipe checksum mismatch.",
    )
    require(
        recipe["symbol"] == symbol
        and type(recipe["training_count"]) is int
        and recipe["training_count"] > 0
        and recipe["training_end_exclusive"] == "2024-01-01T00:00:00+00:00"
        and isinstance(recipe["policy"], str)
        and bool(recipe["policy"])
        and digest_ok(recipe["training_rows_sha256"]),
        "Invalid training provenance.",
    )
    for key in ("input_hashes", "implementation_sha256", "dependency_files_sha256"):
        require(
            isinstance(recipe[key], dict)
            and bool(recipe[key])
            and all(digest_ok(v) for v in recipe[key].values()),
            "Invalid recipe fingerprints.",
        )
    require(
        set(recipe["dependency_files_sha256"]) == {"uv.lock", "pyproject.toml"}
        and isinstance(recipe["runtime"], dict)
        and bool(recipe["runtime"])
        and all(isinstance(v, str) and v for v in recipe["runtime"].values()),
        "Invalid runtime/dependency provenance.",
    )
    params = recipe["parameters"]
    require(set(params) == {*MODELS, "ridge_scaler"}, "Unexpected model parameters.")
    require(
        params["zero"] == {"constant": 0.0}
        and predictions["zero"] == 0
        and set(params["training_mean"]) == {"constant"}
        and number(params["training_mean"]["constant"])
        and predictions["training_mean"] == params["training_mean"]["constant"],
        "Saved baselines disagree with the recipe.",
    )
    fixed = {
        "ridge": {"alpha": 1.0, "solver": "svd", "fit_intercept": True},
        "ridge_scaler": {"with_mean": True, "with_std": True},
        "gradient_boosting": {
            "loss": "squared_error",
            "learning_rate": 0.03,
            "n_estimators": 100,
            "max_depth": 2,
            "min_samples_leaf": 100,
            "subsample": 1.0,
            "n_iter_no_change": None,
            "random_state": 42,
        },
    }
    for name, values in fixed.items():
        require(
            all(params[name][k] == v for k, v in values.items()),
            "Fixed model recipe mismatch.",
        )


def load_prediction(path):
    """Validate original bytes/structure/retained inputs; never refit or replay ML."""
    try:
        record, content_hash, file_hash = checked_file(path, "content_sha256")
        opened = grid_time(record["source_open_time"])
        require(
            opened >= START,
            "Pre-prospective sources are ineligible; holdout is forbidden.",
        )
        symbol = record["market"]["symbol"]
        require(
            path.name == f"{forward.record_id(symbol, opened)}.json",
            "Prediction filename mismatch.",
        )
        require(type(record["schema_version"]) is int, "Invalid schema version type.")
        captured, calculated, issued = (
            utc_time(record[k]) for k in ("captured_at", "calculated_at", "issued_at")
        )
        forward.check_timing(opened, captured, calculated, issued, issued)
        candles = [candle_from_json(row) for row in record["source_candles"]]
        features = forward.validate_window(record["market"], candles, opened, captured)
        require(
            len(record["predictions"]) == len(MODELS),
            "Expected all four model forecasts.",
        )
        predictions = {
            p["model_id"]: p["predicted_log_return_4h"] for p in record["predictions"]
        }
        require(
            set(predictions) == set(MODELS)
            and all(number(p) for p in predictions.values()),
            "Invalid forecasts.",
        )
        validate_recipe(record["model"], symbol, predictions)
        expected = forward.evidence(
            record["market"],
            candles,
            features,
            predictions,
            record["model"],
            captured,
            calculated,
            issued,
        )
        require(
            canonical(record) == canonical(expected),
            "Forward schema, timing, identity or features mismatch.",
        )
        return {
            "record": record,
            "content_sha256": content_hash,
            "file_sha256": file_hash,
        }
    except MALFORMED as error:
        raise ValueError("Malformed prediction evidence.") from error


def parse_journal(body):
    journal = decode(body)
    require(journal["schema_version"] == 1, "Invalid journal version.")
    opened = grid_time(journal["source_open_time"])
    started = utc_time(journal["started_at"])
    require(
        opened >= START
        and opened + STEP <= started < opened + 2 * STEP
        and utc_time(journal["feature_available_at"]) == opened + STEP + forward.DELAY
        and utc_time(journal["deadline"]) == opened + STEP + forward.DELAY + PROMPTNESS
        and journal["state"] in ("running", "complete", "failed", "overlap_skipped")
        and set(journal["markets"]) == set(SYMBOLS)
        and isinstance(journal["run_id"], str)
        and re.fullmatch(r"[0-9a-f]{32}", journal["run_id"]),
        "Invalid journal identity or timing.",
    )
    if journal["finished_at"] is not None:
        require(utc_time(journal["finished_at"]) >= started, "Journal clock reversed.")
    if journal["state"] == "complete":
        require(
            journal["finished_at"] is not None, "Complete journal has no finish time."
        )
    for item in journal["markets"].values():
        require(
            item["status"]
            in ("recorded", "already-recorded", "not-yet-eligible", "missed", "failed"),
            "Invalid journal status.",
        )
        if item["status"] in ("recorded", "already-recorded"):
            require(
                isinstance(item["record_path"], str)
                and digest_ok(item["content_sha256"])
                and digest_ok(item["file_sha256"])
                and grid_time(item["source_open_time"]) == opened
                and number(item["issuance_delay_seconds"])
                and item["issuance_delay_seconds"] >= 0,
                "Malformed recorded journal entry.",
            )
            issued = utc_time(item["issued_at"])
            require(
                opened + STEP + forward.DELAY <= issued < opened + 2 * STEP
                and item["issuance_delay_seconds"]
                == (issued - opened - STEP - forward.DELAY).total_seconds(),
                "Invalid recorded journal timing.",
            )
    return journal


def journals(operations):
    valid, invalid = [], []
    for path in sorted(operations.glob("*.json")):
        try:
            body = path.read_bytes()
            journal = parse_journal(body)
            valid.append(
                (
                    journal,
                    {
                        "filename": path.name,
                        "file_sha256": sha256(body),
                        "json_utf8": body.decode("utf-8"),
                    },
                )
            )
        except (OSError, ValueError, *MALFORMED):
            invalid.append(path.name)
    valid.sort(key=lambda pair: (utc_time(pair[0]["started_at"]), pair[1]["filename"]))
    return valid, invalid


def matches_automation(journal, prediction):
    record = prediction["record"]
    item = journal["markets"][record["market"]["symbol"]]
    if item["status"] != "recorded":
        return False
    issued = utc_time(record["issued_at"])
    return (
        journal["state"] in ("running", "complete", "failed")
        and journal["source_open_time"] == record["source_open_time"]
        and utc_time(journal["started_at"]) <= utc_time(record["captured_at"])
        and (
            journal["finished_at"] is None or issued <= utc_time(journal["finished_at"])
        )
        and item.get("verification") == "replayed"
        and item.get("refresh") == "complete_fresh"
        and item.get("error_category") is None
        and item.get("content_sha256") == prediction["content_sha256"]
        and item.get("file_sha256") == prediction["file_sha256"]
        and item.get("source_open_time") == record["source_open_time"]
        and item.get("issued_at") == record["issued_at"]
        and item.get("issuance_delay_seconds")
        == (issued - utc_time(record["feature_available_at"])).total_seconds()
        and Path(item.get("record_path", "")).name == f"{record['record_id']}.json"
    )


def classify(prediction, cycles):
    record = prediction["record"]
    if (
        utc_time(record["issued_at"])
        >= utc_time(record["feature_available_at"]) + PROMPTNESS
    ):
        return {"name": COHORTS[1], "automation_evidence": None}
    for journal, evidence in cycles:
        if matches_automation(journal, prediction):
            return {"name": COHORTS[0], "automation_evidence": evidence}
    return {"name": COHORTS[2], "automation_evidence": None}


def validate_cohort(cohort, prediction, captured):
    evidence = cohort["automation_evidence"]
    cycles = []
    if evidence is not None:
        require(
            set(evidence) == {"filename", "file_sha256", "json_utf8"},
            "Invalid automation evidence schema.",
        )
        body = evidence["json_utf8"].encode("utf-8")
        require(
            sha256(body) == evidence["file_sha256"],
            "Automation evidence checksum mismatch.",
        )
        journal = parse_journal(body)
        require(
            utc_time(journal["started_at"]) <= captured
            and (
                journal["finished_at"] is None
                or utc_time(journal["finished_at"]) <= captured
            ),
            "Automation evidence postdates scoring.",
        )
        cycles.append((journal, evidence))
    require(
        cohort == classify(prediction, cycles),
        "Cohort does not match retained evidence.",
    )


def read_target(connection, record):
    """Only the exact t+1 row; no source, holdout, latest-row or revision query."""
    with research_snapshot(connection):
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM market WHERE venue='binance' "
                "AND market_type='spot' AND symbol=%s",
                (record["market"]["symbol"],),
            )
            market = cursor.fetchone()
        require(market == record["market"], "Database market identity mismatch.")
        opened = grid_time(record["target_open_time"])
        return get_candles(
            connection, market["market_id"], 14400, opened, opened + STEP
        )


def validate_target(record, target, captured):
    # Validate only the captured target; never query a replacement source close.
    require(set(target) == forward.CANDLE_FIELDS, "Unexpected target schema.")
    forward.validate_observation(
        forward.CandleObservation(**{k: target[k] for k in forward.OBSERVATION_FIELDS})
    )
    require(
        all(
            isinstance(target[k], datetime) and target[k].utcoffset() == timedelta(0)
            for k in forward.TIME_FIELDS
        ),
        "Target timestamps must be UTC.",
    )
    endpoint = utc_time(record["target_close_boundary"])
    require(
        target["market_id"] == record["market"]["market_id"]
        and target["interval_seconds"] == 14400
        and target["open_time"] == grid_time(record["target_open_time"])
        and type(target["version"]) is int
        and target["version"] > 0
        and endpoint + forward.DELAY
        <= target["observed_at"]
        <= target["recorded_at"]
        <= captured
        and target["observed_at"] <= target["last_observed_at"] <= captured,
        "Invalid target identity, version, or completed-observation timing.",
    )
    # Apply the same native Binance provenance rules as Stage 3A to one target.
    url = forward.urlsplit(target["source_url"])
    symbol = record["market"]["symbol"]
    if target["source_kind"] == "rest":
        query = forward.parse_qs(url.query)
        source_ok = (
            url.hostname == "data-api.binance.vision"
            and url.path == "/api/v3/klines"
            and query.get("symbol") == [symbol]
            and query.get("interval") == ["4h"]
            and query.get("timeZone") == ["0"]
        )
    else:
        source_ok = (
            url.hostname == "data.binance.vision"
            and url.path
            == f"/data/spot/monthly/klines/{symbol}/4h/"
            f"{symbol}-4h-{target['open_time']:%Y-%m}.zip"
        )
    require(url.scheme == "https" and source_ok, "Target source provenance mismatch.")


def sign(value):
    return int(value > 0) - int(value < 0)


def model_errors(predictions, actual, direction):
    results = {}
    for item in predictions:
        predicted = item["predicted_log_return_4h"]
        error = predicted - actual
        squared = error * error
        require(
            math.isfinite(error) and math.isfinite(squared),
            "Error exceeds finite numerical range.",
        )
        predicted_direction = sign(predicted)
        results[item["model_id"]] = {
            "signed_error": error,
            "absolute_error": abs(error),
            "squared_error": squared,
            "actual_direction": direction,
            "predicted_direction": predicted_direction,
            "directional_correct": predicted_direction == direction
            if predicted_direction
            else None,
        }
    return results


def implementation():
    return {
        "sha256": {
            name: sha256(Path(__file__).with_name(name).read_bytes())
            for name in IMPLEMENTATION_FILES
        },
        "python": platform.python_version(),
    }


def make_outcome(prediction, target, captured, cohort, fingerprint):
    record = prediction["record"]
    require(
        captured >= utc_time(record["target_close_boundary"]) + forward.DELAY,
        "Target has not settled.",
    )
    validate_target(record, target, captured)
    validate_cohort(cohort, prediction, captured)
    source = Decimal(record["source_candles"][-1]["close"])
    actual = log_return(target["close"], source)
    require(math.isfinite(actual), "Nonfinite realised log return.")
    direction = int(target["close"] > source) - int(target["close"] < source)
    return _json(
        {
            "schema_version": 1,
            "kind": "scored_forward_observation",
            "prediction_record_id": record["record_id"],
            "prediction_content_sha256": prediction["content_sha256"],
            "prediction_file_sha256": prediction["file_sha256"],
            **{
                key: record[key]
                for key in (
                    "market",
                    "interval_seconds",
                    "source_open_time",
                    "target_open_time",
                    "target_close_boundary",
                    "issued_at",
                    "predictions",
                    "target_definition",
                )
            },
            "cohort": cohort,
            "original_source_close": str(source),
            "target_close": str(target["close"]),
            "target_candle": target,
            "evaluation_captured_at": captured,
            "actual_log_return_4h": actual,
            "model_errors": model_errors(record["predictions"], actual, direction),
            "protocol": {"version": PROTOCOL_VERSION, "sha256": PROTOCOL_SHA256},
            "implementation": fingerprint,
        }
    )


def load_outcome(path, prediction):
    try:
        value, digest, _ = checked_file(path, "outcome_sha256")
        require(
            path.name == f"{prediction['record']['record_id']}.json",
            "Outcome filename mismatch.",
        )
        require(
            value["prediction_record_id"] == prediction["record"]["record_id"]
            and value["prediction_content_sha256"] == prediction["content_sha256"]
            and value["prediction_file_sha256"] == prediction["file_sha256"],
            "Outcome conflicts with original prediction identity or exact bytes.",
        )
        fingerprint = value["implementation"]
        require(
            set(fingerprint) == {"sha256", "python"}
            and set(fingerprint["sha256"]) == set(IMPLEMENTATION_FILES)
            and all(digest_ok(v) for v in fingerprint["sha256"].values())
            and isinstance(fingerprint["python"], str)
            and bool(fingerprint["python"]),
            "Invalid implementation provenance.",
        )
        expected = make_outcome(
            prediction,
            candle_from_json(value["target_candle"]),
            utc_time(value["evaluation_captured_at"]),
            value["cohort"],
            fingerprint,
        )
        require(
            canonical(expected) == canonical(value),
            "Outcome evidence conflicts with forecast, protocol or metrics.",
        )
        return dict(value, outcome_sha256=digest)
    except MALFORMED as error:
        raise ValueError("Malformed outcome evidence.") from error


def publish_outcome(value, destination):
    """Atomic exclusive hard link, fsynced file and directory; never replace."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    body = canonical(dict(value, outcome_sha256=sha256(canonical(value)))) + b"\n"
    fd, name = tempfile.mkstemp(
        prefix=".outcome-", suffix=".partial", dir=destination.parent
    )
    partial = Path(name)
    linked = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fchmod(handle.fileno(), 0o444)
            os.fsync(handle.fileno())
        os.link(partial, destination)
        linked = True
        directory = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as error:
        if linked:
            raise RuntimeError(
                "Outcome is visible but directory durability is uncertain; "
                "verify on retry."
            ) from error
        raise
    finally:
        partial.unlink(missing_ok=True)


def local_connection():
    settings = load_settings()
    require(
        settings.host in ("localhost", "127.0.0.1", "::1"),
        "Only the local development database is permitted.",
    )
    return connect_database(settings)


def score(
    path,
    *,
    outcomes=OUTCOMES,
    operations=OPERATIONS,
    clock=forward.utc_now,
    connect=local_connection,
):
    protocol()
    prediction = load_prediction(path)
    record = prediction["record"]
    destination = outcomes / f"{record['record_id']}.json"
    result = {"record_id": record["record_id"], "outcome_path": str(destination)}
    if os.path.lexists(destination):
        load_outcome(destination, prediction)
        return dict(result, status="already_scored")
    started = forward.checked_clock(clock)
    if started < utc_time(record["target_close_boundary"]) + forward.DELAY:
        return dict(result, status="pending_not_settled")
    cycles, invalid = journals(operations)
    cohort = classify(prediction, cycles)
    with connect() as connection:
        targets = read_target(connection, record)
    captured = forward.checked_clock(clock)
    require(captured >= started, "Clock reversed while reading the outcome.")
    if not targets:
        return dict(result, status="pending_target_missing", invalid_journals=invalid)
    require(len(targets) == 1, "Duplicate or unexpected target candles.")
    try:
        value = make_outcome(prediction, targets[0], captured, cohort, implementation())
    except MALFORMED as error:
        raise ValueError("Malformed target evidence.") from error
    final = forward.checked_clock(clock)
    require(final >= captured, "Clock reversed before outcome publication.")
    try:
        publish_outcome(value, destination)
    except FileExistsError:
        # Another valid first capture wins, including a different provider version.
        load_outcome(destination, prediction)
        return dict(result, status="already_scored")
    return dict(
        result, status="scored", cohort=cohort["name"], invalid_journals=invalid
    )


def aggregate(outcomes):
    """A whole-record matched sample for all four models and both baselines."""
    ordered = sorted(outcomes, key=lambda r: r["prediction_record_id"])
    identities = [row["prediction_record_id"] for row in ordered]
    require(
        len(set(identities)) == len(identities),
        "Duplicate matched observation identities.",
    )
    require(
        all(set(r["model_errors"]) == set(MODELS) for r in ordered),
        "Incomplete model comparison.",
    )
    count = len(ordered)
    mean_actual = fmean(r["actual_log_return_4h"] for r in ordered) if count else None
    metrics = {}
    for name in MODELS:
        errors = [r["model_errors"][name] for r in ordered]
        directional = [
            e["directional_correct"]
            for e in errors
            if e["directional_correct"] is not None
        ]
        metrics[name] = {
            "scored_predictions": count,
            "mae": fmean(e["absolute_error"] for e in errors) if count else None,
            "rmse": math.sqrt(fmean(e["squared_error"] for e in errors))
            if count
            else None,
            "forecast_bias": fmean(e["signed_error"] for e in errors)
            if count
            else None,
            "mean_realised_log_return": mean_actual,
            "directional_correct": sum(directional),
            "directional_denominator": len(directional),
            "directional_accuracy": fmean(directional) if directional else None,
            "directional_coverage": len(directional) / count if count else None,
        }
    for name in MODELS:
        metrics[name]["relative_error_improvement"] = {
            baseline: {
                metric: 1 - metrics[name][metric] / metrics[baseline][metric]
                if metrics[baseline][metric]
                else None
                for metric in ("mae", "rmse")
            }
            for baseline in ("zero", "training_mean")
        }
    return {"matched_count": count, "matched_record_ids": identities, "models": metrics}


def period_bounds(endpoint, period):
    start = endpoint.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        start -= timedelta(days=start.weekday())
        return start, start + timedelta(days=7)
    require(period == "month", "Unknown reporting period.")
    start = start.replace(day=1)
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, end


def report(
    *,
    records=forward.RECORDS,
    outcomes=OUTCOMES,
    operations=OPERATIONS,
    as_of=None,
    period=None,
):
    """Offline inventory and descriptive scores, deterministic at a fixed cutoff."""
    policy = protocol()
    now = (
        forward.checked_clock(lambda: as_of) if as_of is not None else forward.utc_now()
    )
    require(period in (None, "week", "month"), "Unknown reporting period.")
    cycles, invalid_journals = journals(operations)
    cycles = [(j, e) for j, e in cycles if utc_time(j["started_at"]) <= now]
    first = min((grid_time(j["source_open_time"]) for j, _ in cycles), default=None)
    result = {
        "protocol": policy,
        "as_of": now.isoformat(),
        "limitations": LIMITATIONS,
        "monitoring_source_start": first.isoformat() if first else None,
        "invalid_journals": invalid_journals,
        "invalid_predictions": [],
        "invalid_outcomes": [],
        "orphan_outcomes": [],
        "partial_outcomes": len(list(outcomes.glob("*.partial"))),
        "markets": {},
    }
    valid = {}
    paths = sorted(records.glob("*.json"))
    for path in paths:
        try:
            prediction = load_prediction(path)
            if utc_time(prediction["record"]["issued_at"]) <= now:
                valid[path.stem] = prediction
        except (OSError, ValueError):
            result["invalid_predictions"].append(path.name)
    present_names = {p.stem for p in paths}
    for path in sorted(outcomes.glob("*.json")):
        if path.stem not in present_names:
            result["orphan_outcomes"].append(path.name)
    classified = {s: {c: [] for c in COHORTS} for s in SYMBOLS}
    for identity, prediction in valid.items():
        record = prediction["record"]
        cohort = classify(prediction, cycles)["name"]
        item = {
            "prediction": prediction,
            "score": None,
            "state": "pending_not_settled"
            if now < utc_time(record["target_close_boundary"]) + forward.DELAY
            else "mature_unscored",
        }
        path = outcomes / f"{identity}.json"
        if os.path.lexists(path):
            try:
                scored = load_outcome(path, prediction)
                if utc_time(scored["evaluation_captured_at"]) <= now:
                    item.update(score=scored, state="scored")
                    cohort = scored["cohort"]["name"]
            except (OSError, ValueError):
                item["state"] = "invalid_outcome"
                result["invalid_outcomes"].append(path.name)
        classified[record["market"]["symbol"]][cohort].append(item)
    for symbol in SYMBOLS:
        missing, invalid_expected, missing_primary = [], [], []
        opened = first
        while opened is not None and opened + STEP + forward.DELAY + PROMPTNESS <= now:
            identity = forward.record_id(symbol, opened)
            if identity not in present_names:
                missing.append(identity)
            elif identity not in valid:
                invalid_expected.append(identity)
            if not any(
                i["prediction"]["record"]["record_id"] == identity
                for i in classified[symbol][COHORTS[0]]
            ):
                missing_primary.append(identity)
            opened += STEP
        market = {
            "missing_prediction_count": len(missing) if first else None,
            "missing_prediction_ids": missing,
            "invalid_expected_prediction_ids": invalid_expected,
            "missing_primary_ids": missing_primary,
            "cohorts": {},
        }
        for cohort, items in classified[symbol].items():
            scores = [i["score"] for i in items if i["score"] is not None]
            counts = {
                state: sum(i["state"] == state for i in items)
                for state in (
                    "scored",
                    "pending_not_settled",
                    "mature_unscored",
                    "invalid_outcome",
                )
            }
            summary = {
                "genuine_predictions": len(items),
                **counts,
                "missing_predictions": len(missing_primary)
                if cohort == COHORTS[0] and first
                else None,
                "warning": "Preliminary: fewer than 100 scored observations."
                if len(scores) < 100
                else "Descriptive only; no statistical significance is implied.",
                **aggregate(scores),
            }
            # Counts are common to every model because incomplete outcomes fail whole.
            for model in summary["models"].values():
                model.update(
                    genuine_predictions=len(items),
                    **counts,
                    missing_predictions=summary["missing_predictions"],
                )
            if period:
                summary["periods"] = []
                endpoints = [
                    utc_time(i["prediction"]["record"]["target_close_boundary"])
                    for i in items
                ]
                if first is not None:
                    endpoints.append(first + 2 * STEP)
                if endpoints:
                    start, end = period_bounds(min(endpoints), period)
                    last = max(now, max(endpoints))
                    while start <= last:
                        subset = [
                            i
                            for i in items
                            if start
                            <= utc_time(
                                i["prediction"]["record"]["target_close_boundary"]
                            )
                            < end
                        ]
                        selected = [
                            i["score"] for i in subset if i["score"] is not None
                        ]
                        minimum = 30 if period == "week" else 100
                        summary["periods"].append(
                            {
                                "start": start.isoformat(),
                                "end_exclusive": end.isoformat(),
                                "partial_period": end > now,
                                "genuine_predictions": len(subset),
                                "scored_predictions": len(selected),
                                "warning": "Insufficient period sample."
                                if len(selected) < minimum
                                else "Preliminary descriptive comparison."
                                if len(selected) < 100
                                else "Descriptive only.",
                                "metrics": aggregate(selected)
                                if len(selected) >= minimum
                                else None,
                            }
                        )
                        start, end = period_bounds(end, period)
            market["cohorts"][cohort] = summary
        result["markets"][symbol] = market
    result["evidence_valid"] = not any(
        result[k]
        for k in (
            "invalid_journals",
            "invalid_predictions",
            "invalid_outcomes",
            "orphan_outcomes",
        )
    )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scoring = commands.add_parser(
        "score", help="Manually score one genuine forecast after protocol review."
    )
    scoring.add_argument("--record", type=Path, required=True)
    reporting = commands.add_parser(
        "report", help="Offline descriptive report; no DB or provider access."
    )
    reporting.add_argument("--records", type=Path, default=forward.RECORDS)
    reporting.add_argument("--outcomes", type=Path, default=OUTCOMES)
    reporting.add_argument("--operations", type=Path, default=OPERATIONS)
    reporting.add_argument("--as-of", type=utc_time)
    reporting.add_argument("--period", choices=("week", "month"))
    args = parser.parse_args(argv)
    try:
        if args.command == "score":
            value = score(args.record)
            code = 0 if value["status"] in ("scored", "already_scored") else 2
        else:
            value = report(
                records=args.records,
                outcomes=args.outcomes,
                operations=args.operations,
                as_of=args.as_of,
                period=args.period,
            )
            code = 0 if value["evidence_valid"] else 1
        print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))
        return code
    except (OSError, ValueError, RuntimeError, psycopg.Error):
        print(
            "Forward evaluation failed: invalid evidence, configuration, database read "
            "or publication. No evidence was replaced; details suppressed.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

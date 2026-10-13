"""Explicit historical review and replay of retained, approved REST evidence."""

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg

from backtest_badger.candles import (
    ECONOMIC_FIELDS,
    PRICES,
    VOLUMES,
    BatchConflict,
    CandleObservation,
    ReviewConflict,
    get_candles,
    save_candles,
    validate_observation,
)
from backtest_badger.db import connect_database
from backtest_badger.ingestion import _retain, _write_manifest
from backtest_badger.recent import _json, _warnings
from backtest_badger.research import import_evidence, research_snapshot
from backtest_badger.rest import (
    BASE,
    EPOCH,
    MAX_BODY,
    PARSER_VERSION,
    STEP,
    Response,
    RestError,
    check_clock,
    eligible_end,
    fetch,
    inspect_page,
    kline_url,
    parse_page,
)

PLAN_VERSION = 1


def validate_range(symbol, start, end, run_time):
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise ValueError("Select BTCUSDT or ETHUSDT.")
    if any(t.utcoffset() != timedelta(0) or (t - EPOCH) % STEP for t in (start, end)):
        raise ValueError("Both bounds must be exact aware UTC 4h boundaries.")
    if not timedelta(0) < end - start <= timedelta(days=30):
        raise ValueError("Select a nonempty historical range of at most 30 days.")
    if start < EPOCH or end > eligible_end(run_time):
        raise ValueError("The complete range must be eligible at review time.")


def implementation():
    return {
        name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ("rest.py", "candles.py", "revalidation.py")
    }


def fingerprint(plan):
    content = {k: v for k, v in plan.items() if k != "fingerprint"}
    return hashlib.sha256(
        json.dumps(_json(content), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def compare(response, market_id, start, end, current):
    observations, invalid, identities = inspect_page(
        response, market_id=market_id, start=start, end=end
    )
    proposed = {o.open_time: o for o in observations}
    invalid_times = {i["open_time"] for i in invalid}
    returned = {i["open_time"] for i in identities}
    entries, differences = [], []
    for i in range((end - start) // STEP):
        opened = start + i * STEP
        old, new = current.get(opened), proposed.get(opened)
        changed = [
            name
            for name in ECONOMIC_FIELDS
            if old and new and old[name] != getattr(new, name)
        ]
        classification = (
            "invalid"
            if opened.isoformat() in invalid_times
            else "missing_provider"
            if opened.isoformat() not in returned
            else "missing_database"
            if old is None
            else "changed"
            if changed
            else "identical"
        )
        warnings = []
        if changed:
            difference = dict(old=old, new=asdict(new))
            differences.append(difference)
            warnings.extend(_warnings([difference]))
            if new.observed_at <= old["last_observed_at"]:
                warnings.append("Stale or equal-time change: apply will reject.")
        entries.append(
            dict(
                open_time=opened,
                classification=classification,
                old=old,
                proposed=asdict(new) if new else None,
                changed_fields=changed,
                warnings=warnings,
            )
        )
    return _json(
        dict(
            inspected=len(identities),
            entries=entries,
            invalid=invalid,
            identities=identities,
            warnings=_warnings(differences),
            counts={
                name: sum(e["classification"] == name for e in entries)
                for name in (
                    "identical",
                    "changed",
                    "missing_database",
                    "missing_provider",
                    "invalid",
                )
            },
        )
    )


def _market(connection, symbol):
    row = connection.execute(
        "SELECT market_id FROM market WHERE venue='binance' "
        "AND market_type='spot' AND symbol=%s",
        (symbol,),
    ).fetchone()
    if row is None:
        raise ValueError("Selected seeded market is absent.")
    return row[0]


def _summary(plan):
    lines = [
        f"{plan['symbol']} 4h [{plan['start']}, {plan['end_exclusive']})",
        f"Review status: {plan['status']}; database writes: none.",
        "Acquisition time is not historical publication time.",
        "Approval selects every proposed observation in this complete range.",
    ]
    analysis = plan.get("analysis")
    if analysis:
        lines.append(
            f"Inspected: {analysis['inspected']}; counts: {analysis['counts']}"
        )
        for e in analysis["entries"]:
            if e["classification"] != "identical":
                lines.append(json.dumps(e, indent=2))
        lines.extend(analysis["warnings"])
        if analysis["invalid"]:
            lines.append(json.dumps(analysis["invalid"], indent=2))
    if plan.get("error"):
        lines.append(f"Failure: {plan['error']}")
    for source in plan["source"].get("responses", []):
        lines.append(
            f"Source: {source['raw_body']}; SHA-256={source['sha256']}; "
            f"observed={source['observed_at']}"
        )
    lines.append(f"Fingerprint: {plan['fingerprint']}")
    return "\n".join(lines) + "\n"


def review_history(
    symbol, settings, *, start, end, artifacts=Path("artifacts"), result=None
):
    run_time = datetime.now(UTC)
    validate_range(symbol, start, end, run_time)
    root = (artifacts / "revalidation").resolve()
    path = root / "plans" / f"{uuid4().hex}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    plan = _json(
        dict(
            schema_version=PLAN_VERSION,
            parser_version=PARSER_VERSION,
            implementation=implementation(),
            symbol=symbol,
            interval="4h",
            start=start,
            end_exclusive=end,
            fixed_run_time=run_time,
            settling_seconds=60,
            status="in_progress",
            clock={},
            source={},
        )
    )

    def publish():
        plan["fingerprint"] = fingerprint(plan)
        _write_manifest(path, plan)

    def acquire(url, item):
        item.update(request_url=url, attempts=[], responses=[])
        publish()

        def retain(response):
            raw = root / "raw" / f"{response.sha256}.json"
            raw.parent.mkdir(parents=True, exist_ok=True)
            _retain(raw, response.body)
            item["responses"].append(
                _json(
                    dict(
                        raw_body=str(raw),
                        sha256=response.sha256,
                        url=response.url,
                        observed_at=response.observed_at,
                        status=response.status,
                        complete=response.complete,
                        headers=response.headers,
                    )
                )
            )
            publish()

        response = fetch(url, retain=retain, attempts=item["attempts"])
        item["selected"] = len(item["responses"]) - 1
        publish()
        return response

    publish()
    try:
        clock_started = datetime.now(UTC)
        plan["clock_started"] = clock_started.isoformat()
        clock = acquire(BASE + "time", plan["clock"])
        check_clock(clock, clock_started)
        response = acquire(kline_url(symbol, start, end), plan["source"])
        with connect_database(settings) as connection, research_snapshot(connection):
            market_id = _market(connection, symbol)
            current = {
                row["open_time"]: row
                for row in get_candles(connection, market_id, 14400, start, end)
            }
        plan["market_id"] = market_id
        plan["analysis"] = compare(response, market_id, start, end, current)
        evidence, unreadable = import_evidence(
            artifacts,
            [symbol],
            start.strftime("%Y-%m"),
            (end - STEP).strftime("%Y-%m"),
        )
        plan["historical_source_diagnostics"] = evidence[symbol]["source_diagnostics"]
        plan["unreadable_historical_manifests"] = unreadable
        analysis = plan["analysis"]
        plan["status"] = (
            "blocked"
            if analysis["invalid"] or analysis["counts"]["missing_provider"]
            else "ready_for_approval"
        )
    except RestError as error:
        plan.update(status="blocked", error=error.category, error_details=error.details)
    except (psycopg.Error, OSError, ValueError, RuntimeError):
        plan.update(status="failed", error="Acquisition, artifact or database failure.")
    publish()
    summary = _summary(plan)
    _retain(path.with_suffix(".txt"), summary.encode())
    print(summary)
    print(f"Plan: {path}\nSummary: {path.with_suffix('.txt')}")
    if result is not None:
        result.update(plan, plan_path=str(path))
    return 0 if plan["status"] == "ready_for_approval" else 1


def _decode_row(row):
    if row is None:
        return None
    values = row.copy()
    for name in (*PRICES, *VOLUMES):
        if not isinstance(values[name], str) or len(values[name]) > 128:
            raise ValueError("Invalid reviewed decimal.")
        values[name] = Decimal(values[name])
    for name in ("open_time", "observed_at", "recorded_at", "last_observed_at"):
        values[name] = datetime.fromisoformat(values[name])
        if values[name].utcoffset() != timedelta(0):
            raise ValueError("Invalid reviewed timestamp.")
    observation = {
        k: v
        for k, v in values.items()
        if k not in ("recorded_at", "last_observed_at", "version")
    }
    validate_observation(CandleObservation(**observation))
    if type(values["version"]) is not int or values["version"] < 1:
        raise ValueError("Invalid reviewed version.")
    return values


def _read_response(item, url):
    if item["request_url"] != url:
        raise ValueError("Request URL does not match reviewed bounds.")
    selected = item["selected"]
    if type(selected) is not int or not 0 <= selected < len(item["responses"]):
        raise ValueError("Invalid response selection.")
    meta = item["responses"][selected]
    with Path(meta["raw_body"]).open("rb") as handle:
        body = handle.read(MAX_BODY + 1)
    response = Response(
        body,
        meta["url"],
        datetime.fromisoformat(meta["observed_at"]),
        meta["status"],
        meta["headers"],
        meta["complete"],
    )
    if (
        response.sha256 != meta["sha256"]
        or response.url != url
        or response.status != 200
        or response.complete is not True
        or len(body) > MAX_BODY
        or response.observed_at.utcoffset() != timedelta(0)
        or response.observed_at > datetime.now(UTC)
    ):
        raise ValueError("Retained response integrity or provenance mismatch.")
    length = response.headers.get("content-length")
    if length is not None and str(len(body)) != length:
        raise ValueError("Retained response is partial.")
    return response


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key.")
        result[key] = value
    return result


def load_plan(path):
    """Reparse original bytes and verify the entire selection before DB access."""
    try:
        with path.open("rb") as handle:
            body = handle.read(4 * MAX_BODY + 1)
        if len(body) > 4 * MAX_BODY:
            raise ValueError("Oversized review plan.")
        plan = json.loads(body, object_pairs_hook=_unique_object)
        if (
            plan["schema_version"] != PLAN_VERSION
            or plan["parser_version"] != PARSER_VERSION
            or plan["implementation"] != implementation()
            or plan["status"] != "ready_for_approval"
            or plan["interval"] != "4h"
            or plan["settling_seconds"] != 60
            or plan["fingerprint"] != fingerprint(plan)
        ):
            raise ValueError("Incompatible, altered or blocked plan.")
        start, end, run_time = (
            datetime.fromisoformat(plan[k])
            for k in ("start", "end_exclusive", "fixed_run_time")
        )
        validate_range(plan["symbol"], start, end, run_time)
        started = datetime.fromisoformat(plan["clock_started"])
        clock = _read_response(plan["clock"], BASE + "time")
        check_clock(clock, started)
        response = _read_response(plan["source"], kline_url(plan["symbol"], start, end))
        if not run_time <= started <= clock.observed_at <= response.observed_at:
            raise ValueError("Invalid acquisition chronology.")
        observations = parse_page(
            response, market_id=plan["market_id"], start=start, end=end
        )
        if [o.open_time for o in observations] != [
            start + i * STEP for i in range((end - start) // STEP)
        ]:
            raise ValueError("Partial response grid; review a complete range.")
        entries = plan["analysis"]["entries"]
        if [e["open_time"] for e in entries] != [
            o.open_time.isoformat() for o in observations
        ]:
            raise ValueError("Reviewed identity selection mismatch.")
        current = {
            datetime.fromisoformat(e["open_time"]): _decode_row(e["old"])
            for e in entries
            if e["old"] is not None
        }
        if (
            compare(response, plan["market_id"], start, end, current)
            != plan["analysis"]
        ):
            raise ValueError("Reparsed observations differ from the reviewed changes.")
        expected = {
            (o.market_id, o.interval_seconds, o.open_time): current.get(o.open_time)
            for o in observations
        }
        return plan, observations, expected, start, end
    except (
        KeyError,
        TypeError,
        ValueError,
        ArithmeticError,
        AttributeError,
        OSError,
        RecursionError,
    ):
        raise ValueError(
            "Plan/source validation failed; retain evidence and create a fresh review."
        ) from None


def apply_revalidation(path, settings, *, approve_changes=False, result=None):
    if not approve_changes:
        raise ValueError(
            "Apply requires explicit --approve-changes after reviewing the plan."
        )
    path = Path(path).resolve()
    report = dict(
        plan_path=str(path),
        outcome="not_attempted",
        inserted=0,
        unchanged=0,
        revised=0,
        conflicting=0,
        stale=0,
    )
    report_path = path.parent.parent / "applications" / f"{uuid4().hex}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        plan, observations, expected, start, end = load_plan(path)
        report.update(
            fingerprint=plan["fingerprint"],
            symbol=plan["symbol"],
            start=plan["start"],
            end_exclusive=plan["end_exclusive"],
            source=plan["source"],
            review_counts=plan["analysis"]["counts"],
            inspected=plan["analysis"]["inspected"],
            approved_at=datetime.now(UTC).isoformat(),
        )
        # Artifact failure here prevents any write. The plan itself is never changed.
        _write_manifest(report_path, report)
        with connect_database(settings) as connection:
            if _market(connection, plan["symbol"]) != plan["market_id"]:
                raise ValueError("Reviewed market mapping changed; review again.")
            report["outcome"] = "in_progress"
            _write_manifest(report_path, report)
            counts = save_candles(
                connection,
                observations,
                mode="historical-revalidation",
                reviewed_rows=expected,
                revalidation_start=start,
                revalidation_end=end,
            )
            report.update(counts, outcome="committed")
    except ReviewConflict as error:
        report.update(outcome="rolled_back", conflicting=1, error=str(error))
    except BatchConflict as error:
        report.update(
            outcome="rolled_back",
            conflicting=len(error.conflicts),
            stale=len(error.stale),
            conflicts=error.conflicts,
            stale_identities=error.stale,
        )
    except ValueError as error:
        report.update(error=str(error))
        if report["outcome"] == "in_progress":
            report["outcome"] = "rolled_back"
    except psycopg.Error as error:
        # A transport failure at COMMIT cannot prove rollback.
        report.update(error="Database/artifact failure; sensitive details suppressed.")
        if report["outcome"] == "in_progress":
            report["outcome"] = (
                "rolled_back"
                if error.sqlstate
                and (
                    error.sqlstate[:2] in ("22", "23", "40", "42")
                    or error.sqlstate == "P0001"
                )
                else "failed_or_unknown"
            )
    except (OSError, RuntimeError):
        report.update(error="Database/artifact failure; sensitive details suppressed.")
        if report["outcome"] == "in_progress":
            report["outcome"] = "failed_or_unknown"
    status = 0 if report["outcome"] == "committed" else 1
    try:
        _write_manifest(report_path, report)
    except OSError:
        status = 1
        print("Final application report unavailable; reconcile database with plan.")
    print(json.dumps({k: v for k, v in report.items() if k != "source"}, indent=2))
    print(f"Application report: {report_path}")
    if result is not None:
        result.update(report, report_path=str(report_path))
    return status

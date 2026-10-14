"""Local, bounded collection cycles. Operational journals are not forecast evidence."""

import fcntl
import json
import math
import os
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from uuid import uuid4

import psycopg

from backtest_badger import forward
from backtest_badger.config import load_settings
from backtest_badger.db import connect_database
from backtest_badger.frozen import STEP, SYMBOLS, grid_time, utc_time
from backtest_badger.recent import sync_recent
from backtest_badger.rest import eligible_end

OPERATIONS = Path("artifacts/forward-operations")
PROMPTNESS = timedelta(minutes=15)


def horizon(now):
    """Select the newly closed source even during its 60-second settling period."""
    return eligible_end(now, 0) - STEP


def record_summary(path, symbol, opened):
    """Cheap integrity/identity checks; explicitly NOT deterministic model replay.

    Older implementation fingerprints remain valid evidence. Existing records are
    never re-fitted by a scheduled retry, including after interrupted verification.
    """
    body = path.read_bytes()
    record = json.loads(body, object_pairs_hook=forward._unique_object)
    digest = record.pop("content_sha256")
    if forward.sha256(forward.canonical(record)) != digest:
        raise ValueError("Record checksum mismatch.")
    identity = forward.record_id(symbol, opened)
    if not (
        record["schema_version"] == 1
        and record["kind"] == "unscored_forward_observation"
        and record["record_id"] == identity
        and record["market"]["symbol"] == symbol
        and record["market"]["venue"] == "binance"
        and record["market"]["market_type"] == "spot"
        and record["interval_seconds"] == 14400
        and grid_time(record["source_open_time"]) == opened
        and utc_time(record["feature_available_at"]) == opened + STEP + forward.DELAY
        and utc_time(record["target_close_boundary"]) == opened + 2 * STEP
        and [p["model_id"] for p in record["predictions"]] == list(forward.MODELS)
        and all(
            p["prediction_id"] == f"{identity}:{p['model_id']}"
            and type(p["predicted_log_return_4h"]) in (int, float)
            and math.isfinite(p["predicted_log_return_4h"])
            for p in record["predictions"]
        )
    ):
        raise ValueError("Record identity mismatch.")
    captured, calculated, issued = (
        utc_time(record[k]) for k in ("captured_at", "calculated_at", "issued_at")
    )
    forward.check_timing(opened, captured, calculated, issued, issued)
    return dict(
        record_path=str(path),
        content_sha256=digest,
        file_sha256=forward.sha256(body),
        source_open_time=opened.isoformat(),
        issued_at=issued.isoformat(),
        issuance_delay_seconds=(issued - opened - STEP - forward.DELAY).total_seconds(),
        verification="integrity_only",
    )


def write_journal(path, journal):
    """Atomically replace only this run's operational snapshot, never a forecast."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".cycle-", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(forward.canonical(journal) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


def save_provider_pause(path, refresh, now):
    """Share HTTP 418/429 backoff across markets and process restarts."""
    retry = (refresh.get("error_details") or {}).get("retry_after")
    until = None
    try:
        if isinstance(retry, str) and retry.isdecimal():
            until = now + timedelta(seconds=int(retry))
        elif isinstance(retry, str):
            parsed = parsedate_to_datetime(retry)
            if parsed.utcoffset() is not None:
                until = parsed.astimezone(UTC)
        if until is not None and until <= now:
            until = None
    except (ValueError, OverflowError, TypeError):
        until = None
    write_journal(path, {"retry_at": until.isoformat() if until else None})


def collect_market(
    symbol, opened, started, *, records, source, artifacts, clock, pause_path=None
):
    available = opened + STEP + forward.DELAY
    deadline = available + PROMPTNESS
    result = dict(status="failed", refresh="not_attempted", error_category=None)
    phase = "existing_record"
    previous = started

    def timely_clock():
        nonlocal previous
        now = forward.checked_clock(clock)
        if now < previous:
            raise ValueError("Clock reversed.")
        previous = now
        if now >= deadline:
            raise forward.PublicationDeadlineExceeded()
        if now < available:
            raise ValueError("Clock precedes eligibility.")
        return now

    try:
        path = records / f"{forward.record_id(symbol, opened)}.json"
        # lexists also refuses dangling links; never replace an occupied identity.
        if os.path.lexists(path):
            result.update(
                record_summary(path, symbol, opened), status="already-recorded"
            )
            return result
        now = forward.checked_clock(clock)
        if now < started:
            raise ValueError("Clock reversed.")
        previous = now
        if now < available:
            result["status"] = "not-yet-eligible"
            return result
        timely_clock()
        phase = "provider_pause"
        if pause_path is not None and pause_path.exists():
            pause = json.loads(pause_path.read_bytes())
            if pause["retry_at"] is None or now < utc_time(pause["retry_at"]):
                result["error_category"] = phase
                return result
        phase = "configuration"
        settings = load_settings()
        if settings.host not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError("Only the local development database is permitted.")
        phase = "refresh"
        result["refresh"] = "failed"
        refresh = {}
        # Existing sync prints provider diagnostics; do not copy external strings
        # into unattended logs. Its original REST evidence stays in artifacts/rest.
        with (
            open(os.devnull, "w") as quiet,
            redirect_stdout(quiet),
            redirect_stderr(quiet),
        ):
            code = sync_recent(symbol, settings, artifacts=artifacts, result=refresh)
        if refresh.get("error_category") == "rate_limit" and pause_path is not None:
            save_provider_pause(pause_path, refresh, forward.checked_clock(clock))
        finished = forward.checked_clock(clock)
        coverage = refresh.get("coverage") or {}
        complete = (
            code == 0
            and refresh.get("status") == "complete"
            and refresh.get("source_complete") is True
            and refresh.get("failed_pages") == 0
            and refresh.get("incomplete_pages") == 0
            and coverage.get("stored_complete") is True
            and coverage.get("freshness") == "fresh"
            and utc_time(refresh["latest_eligible_open"]) == opened
            and utc_time(coverage["latest_stored_open"]) == opened
            and started
            <= utc_time(refresh["fixed_run_time"])
            <= utc_time(refresh["finished_at"])
            <= finished
        )
        result["refresh"] = "complete_fresh" if complete else "failed"
        timely_clock()
        if not complete:
            # Fixed categories only; never exception messages or provider headers.
            result["error_category"] = (
                refresh["error_category"]
                if refresh.get("error_category") in ("database", "rate_limit")
                else "refresh"
            )
            return result
        phase = "database"
        timely_clock()
        with connect_database(settings) as connection:
            phase = "prediction"
            path, _ = forward.record_forward(
                connection,
                symbol,
                source=source,
                destination=records,
                clock=timely_clock,
                publication_deadline=deadline,
            )
        result.update(record_summary(path, symbol, opened))
        phase = "verification"
        forward.verify_forward(path, source=source)
        result.update(status="recorded", verification="replayed")
    except forward.PublicationDeadlineExceeded:
        result.update(status="missed", error_category="promptness_expired")
    except psycopg.Error:
        result["error_category"] = "database"
    except Exception:
        # Market isolation includes unexpected fitting/verification failures.
        # KeyboardInterrupt/SystemExit deliberately leave an interrupted journal.
        result["error_category"] = phase
    return result


def run_cycle(
    *,
    records=forward.RECORDS,
    operations=OPERATIONS,
    source=forward.TRAINING,
    artifacts=Path("artifacts"),
    clock=forward.utc_now,
):
    started = forward.checked_clock(clock)
    opened = horizon(started)
    journal = dict(
        schema_version=1,
        run_id=uuid4().hex,
        started_at=started.isoformat(),
        source_open_time=opened.isoformat(),
        feature_available_at=(opened + STEP + forward.DELAY).isoformat(),
        deadline=(opened + STEP + forward.DELAY + PROMPTNESS).isoformat(),
        state="running",
        finished_at=None,
        markets={
            s: dict(
                status="failed",
                refresh="not_attempted",
                error_category="interrupted_or_in_progress",
            )
            for s in SYMBOLS
        },
    )
    path = operations / f"{started:%Y%m%dT%H%M%S%fZ}-{journal['run_id']}.json"
    evidence_failed = False

    def save():
        nonlocal evidence_failed
        try:
            write_journal(path, journal)
        except OSError:
            evidence_failed = True
            print("Forward operational journal write failed; details suppressed.")

    save()
    if evidence_failed:
        return 1
    try:
        records.mkdir(parents=True, exist_ok=True)
        # Stable inode: never unlink the lock file. Process exit releases flock.
        with (records / ".cycle.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                journal["state"] = "overlap_skipped"
                for item in journal["markets"].values():
                    item["error_category"] = "collection_busy"
                save()
                print("Forward cycle already running; no collection attempted.")
                return 2
            for symbol in SYMBOLS:
                journal["markets"][symbol] = collect_market(
                    symbol,
                    opened,
                    started,
                    records=records,
                    source=source,
                    artifacts=artifacts,
                    clock=clock,
                    pause_path=operations / "state" / "provider-pause.json",
                )
                save()
            journal.update(
                state="complete", finished_at=forward.checked_clock(clock).isoformat()
            )
            save()
    except Exception:
        journal["state"] = "failed"
        journal["error_category"] = "cycle_io_or_clock"
        save()
        print("Forward cycle failed; details suppressed.")
        return 1
    print(json.dumps(journal, indent=2))
    return int(
        evidence_failed
        or any(
            item["status"] in ("failed", "missed")
            for item in journal["markets"].values()
        )
    )


def status_report(
    *, records=forward.RECORDS, operations=OPERATIONS, clock=forward.utc_now
):
    """Read-only status; infer downtime gaps only since the first retained cycle."""
    now = forward.checked_clock(clock)
    cycles, unreadable_cycles = [], 0
    for path in operations.glob("*.json"):
        try:
            cycle = json.loads(path.read_bytes())
            grid_time(cycle["source_open_time"])
            utc_time(cycle["started_at"])
            if cycle["schema_version"] != 1 or cycle["state"] not in (
                "running",
                "complete",
                "failed",
                "overlap_skipped",
            ):
                raise ValueError
            if set(cycle["markets"]) != set(SYMBOLS):
                raise ValueError
            for item in cycle["markets"].values():
                if item["status"] not in (
                    "recorded",
                    "already-recorded",
                    "not-yet-eligible",
                    "missed",
                    "failed",
                ):
                    raise ValueError
            cycles.append(cycle)
        except (OSError, ValueError, KeyError, TypeError):
            unreadable_cycles += 1
    cycles.sort(key=lambda c: c["started_at"])
    first = min((grid_time(c["source_open_time"]) for c in cycles), default=None)
    report = dict(
        checked_at=now.isoformat(),
        monitoring_start=first.isoformat() if first else None,
        unreadable_cycles=unreadable_cycles,
        partial_journals=len(list(operations.glob("*.partial"))),
        incomplete_cycles=sum(c.get("state") == "running" for c in cycles),
        markets={},
    )
    for symbol in SYMBOLS:
        summaries, invalid = {}, []
        for path in records.glob(f"binance-spot-{symbol}-4h-*.json"):
            try:
                # Parse the identity from the filename, never a self-declared horizon.
                opened = datetime.strptime(path.stem[-16:], "%Y%m%dT%H%M%SZ").replace(
                    tzinfo=UTC
                )
                summaries[opened] = record_summary(path, symbol, opened)
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                invalid.append(str(path))
        missed, late = [], []
        opened = first
        while opened is not None and opened + STEP + forward.DELAY + PROMPTNESS <= now:
            if opened not in summaries:
                missed.append(opened.isoformat())
            elif (
                summaries[opened]["issuance_delay_seconds"]
                >= PROMPTNESS.total_seconds()
            ):
                late.append(opened.isoformat())
            opened += STEP
        failures = [
            {
                "started_at": c["started_at"],
                "source_open_time": c["source_open_time"],
                **c["markets"][symbol],
            }
            for c in cycles
            if c["markets"][symbol]["status"] == "failed"
        ]
        verified = [
            c["markets"][symbol]
            for c in cycles
            if c["markets"][symbol].get("verification") == "replayed"
            and c["markets"][symbol]["status"] == "recorded"
        ]
        report["markets"][symbol] = dict(
            latest_prediction=summaries[max(summaries)] if summaries else None,
            latest_replayed_prediction=verified[-1] if verified else None,
            latest_cycle=(
                {
                    "started_at": cycles[-1]["started_at"],
                    "state": cycles[-1]["state"],
                    **cycles[-1]["markets"][symbol],
                }
                if cycles
                else None
            ),
            failure_count=len(failures),
            latest_failure=failures[-1] if failures else None,
            detected_missed_horizons=missed,
            late_record_horizons=late,
            invalid_records=invalid,
        )
    return report

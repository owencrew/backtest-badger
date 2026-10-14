"""Independent Stage 3D orchestration; run from the project root on POSIX.

Only synthetic tests inject paths, connections, clocks or execution limits.
Production never changes forecasts and delegates all scientific decisions to 3C.
"""

import argparse
import fcntl
import json
import os
import signal
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import psycopg

from backtest_badger import forward
from backtest_badger import forward_evaluation as evaluation

OPERATIONS = Path("artifacts/forward-scoring-operations")
BATCH_SIZE = 100
MAX_SECONDS = 240
STATUSES = {"scored", "already_scored", "pending", "failed", "skipped", "running"}
ERRORS = {
    "database_unavailable_or_read_failed",
    "evidence_io_or_publication_failed",
    "invalid_evidence_or_configuration",
    "scoring_failed",
    "journal_write_failed",
    "cursor_write_failed",
    "invalid_cursor",
    "scoring_busy",
    "cycle_time_limit",
    "invalid_cycle_clock",
}
REASONS = ERRORS | {
    "scored",
    "already_scored",
    "pending_not_settled",
    "pending_target_missing",
    "interrupted_or_in_progress",
    "interrupted_or_time_limit",
}


class CycleTimeout(BaseException):
    """Escape even a per-record Exception handler when the cycle budget expires."""


@contextmanager
def time_limit(seconds):
    """Main-thread POSIX wall-time guard, independent of the UTC evidence clock."""

    def expired(signum, frame):
        raise CycleTimeout()

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def write_snapshot(path, value):
    """Replace only mutable operational state, with private, durable atomic writes."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    body = (
        forward.canonical(
            dict(value, content_sha256=forward.sha256(forward.canonical(value)))
        )
        + b"\n"
    )
    fd, name = tempfile.mkstemp(prefix=".scoring-", suffix=".partial", dir=path.parent)
    # Retain a failed/interrupted staging file for offline diagnostics.
    with os.fdopen(fd, "wb") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(name, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def json_paths(folder):
    """Missing initial directories are empty; unreadable inventories must fail."""
    if not os.path.lexists(folder):
        return []
    # Path.glob suppresses directory PermissionError; do not report that as empty.
    return sorted(p for p in folder.iterdir() if p.suffix == ".json")


def read_cursor(path):
    if not os.path.lexists(path):
        return ""
    value, _, _ = evaluation.checked_file(path, "content_sha256")
    evaluation.require(
        set(value) == {"schema_version", "after"}
        and value["schema_version"] == 1
        and isinstance(value["after"], str)
        and Path(value["after"]).name == value["after"]
        and value["after"].endswith(".json"),
        "Invalid queue cursor.",
    )
    return value["after"]


def error_category(error):
    if isinstance(error, psycopg.Error):
        return "database_unavailable_or_read_failed"
    if isinstance(error, OSError):
        return "evidence_io_or_publication_failed"
    if isinstance(error, (ValueError, *evaluation.MALFORMED)):
        return "invalid_evidence_or_configuration"
    return "scoring_failed"


def run_cycle(
    *,
    records=forward.RECORDS,
    outcomes=evaluation.OUTCOMES,
    collector_operations=evaluation.OPERATIONS,
    operations=OPERATIONS,
    clock=forward.utc_now,
    connect=evaluation.local_connection,
    batch_size=BATCH_SIZE,
    max_seconds=MAX_SECONDS,
):
    """Visit a rotating, bounded batch; checkpoint before work to survive crashes."""
    if type(batch_size) is not int or batch_size < 1 or max_seconds <= 0:
        raise ValueError("Invalid execution limits.")
    started = forward.checked_clock(clock)
    run_id = uuid4().hex
    journal = dict(
        schema_version=1,
        run_id=run_id,
        started_at=started.isoformat(),
        finished_at=None,
        state="running",
        discovered_count=0,
        deferred_count=0,
        results=[],
        errors=[],
    )
    operations.mkdir(mode=0o700, parents=True, exist_ok=True)
    journal_path = operations / f"{run_id}.json"

    def save():
        try:
            write_snapshot(journal_path, journal)
            return True
        except OSError:
            if "journal_write_failed" not in journal["errors"]:
                journal["errors"].append("journal_write_failed")
            return False

    last = started

    def stamp():
        nonlocal last
        now = forward.checked_clock(clock)
        evaluation.require(now >= last, "Cycle clock reversed.")
        last = now
        return now.isoformat()

    # Never unlink/replace this inode. Exit and process termination release flock.
    fd = os.open(operations / ".cycle.lock", os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "rb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            journal.update(state="busy", finished_at=stamp())
            journal["errors"].append("scoring_busy")
            return journal, 2 if save() else 1
        if not save():
            return journal, 1  # No scoring without an initial durable journal.
        try:
            with time_limit(max_seconds):
                evaluation.protocol()
                cursor_path = operations / "state" / "cursor.json"
                try:
                    after = read_cursor(cursor_path)
                except (OSError, ValueError, *evaluation.MALFORMED):
                    journal["errors"].append("invalid_cursor")
                    raise ValueError("Invalid queue state.") from None
                paths = json_paths(records)
                paths = [p for p in paths if p.name > after] + [
                    p for p in paths if p.name <= after
                ]
                journal["discovered_count"] = len(paths)
                journal["deferred_count"] = len(paths)
                for path in paths[:batch_size]:
                    item = dict(
                        record_file=path.name,
                        started_at=stamp(),
                        finished_at=None,
                        status="running",
                        reason="interrupted_or_in_progress",
                        invalid_collector_journal_count=0,
                    )
                    journal["results"].append(item)
                    journal["deferred_count"] -= 1
                    # A poisoned or interrupted record cannot monopolise the queue.
                    # This cursor is scheduling state, never proof of a score.
                    try:
                        write_snapshot(
                            cursor_path, {"schema_version": 1, "after": path.name}
                        )
                    except OSError:
                        item.update(status="skipped", reason="cursor_write_failed")
                        journal["errors"].append("cursor_write_failed")
                        item["finished_at"] = stamp()
                        break
                    save()
                    try:
                        result = evaluation.score(
                            path,
                            outcomes=outcomes,
                            operations=collector_operations,
                            clock=lambda: evaluation.utc_time(stamp()),
                            connect=connect,
                        )
                        reason = result["status"]
                        item.update(
                            status="pending"
                            if reason.startswith("pending_")
                            else reason,
                            reason=reason,
                            invalid_collector_journal_count=len(
                                result.get("invalid_journals", [])
                            ),
                        )
                    except Exception as error:
                        # Never log exception strings or traceback/configuration.
                        item.update(status="failed", reason=error_category(error))
                    item["finished_at"] = stamp()
                    save()
                journal["state"] = "complete"
        except CycleTimeout:
            journal["state"] = "timed_out"
            journal["errors"].append("cycle_time_limit")
        except Exception as error:
            journal["state"] = "failed"
            journal["errors"].append(error_category(error))
        try:
            journal["finished_at"] = stamp()
        except (ValueError, TypeError):
            journal["state"] = "failed"
            journal["errors"].append("invalid_cycle_clock")
        for item in journal["results"]:
            if item["status"] == "running":
                item.update(status="failed", reason="interrupted_or_time_limit")
                item["finished_at"] = journal["finished_at"]
        save()
    failed = (
        journal["state"] != "complete"
        or journal["errors"]
        or any(
            r["status"] in ("failed", "skipped") or r["invalid_collector_journal_count"]
            for r in journal["results"]
        )
    )
    return journal, 1 if failed else 0


def load_journal(path):
    """Validate operational shape/timing before trusting a successful-cycle claim."""
    value, _, _ = evaluation.checked_file(path, "content_sha256")
    evaluation.require(
        value["schema_version"] == 1
        and path.stem == value["run_id"]
        and len(value["run_id"]) == 32
        and value["state"] in ("running", "complete", "failed", "timed_out", "busy")
        and isinstance(value["results"], list)
        and isinstance(value["errors"], list)
        and all(isinstance(e, str) and e in ERRORS for e in value["errors"])
        and type(value["discovered_count"]) is int
        and type(value["deferred_count"]) is int
        and 0 <= value["deferred_count"] <= value["discovered_count"],
        "Invalid scoring journal.",
    )
    start = evaluation.utc_time(value["started_at"])
    end = value["finished_at"]
    if end is not None:
        end = evaluation.utc_time(end)
        evaluation.require(end >= start, "Invalid cycle timing.")
    evaluation.require(value["state"] != "complete" or end, "Unfinished cycle.")
    previous = start
    names = set()
    for item in value["results"]:
        began = evaluation.utc_time(item["started_at"])
        finished = item["finished_at"]
        evaluation.require(
            isinstance(item["record_file"], str)
            and Path(item["record_file"]).name == item["record_file"]
            and item["record_file"] not in names
            and item["status"] in STATUSES
            and isinstance(item["reason"], str)
            and item["reason"] in REASONS
            and type(item["invalid_collector_journal_count"]) is int
            and item["invalid_collector_journal_count"] >= 0
            and began >= previous
            and (end is None or began <= end),
            "Invalid record result.",
        )
        names.add(item["record_file"])
        if finished is not None:
            previous = evaluation.utc_time(finished)
            evaluation.require(
                previous >= began and (end is None or previous <= end),
                "Invalid result timing.",
            )
        evaluation.require(
            value["state"] != "complete"
            or (finished is not None and item["status"] != "running"),
            "Unfinished result.",
        )
    evaluation.require(
        len(names) + value["deferred_count"] == value["discovered_count"],
        "Invalid cycle counts.",
    )
    return value


def status_report(
    *,
    records=forward.RECORDS,
    outcomes=evaluation.OUTCOMES,
    collector_operations=evaluation.OPERATIONS,
    operations=OPERATIONS,
    clock=forward.utc_now,
):
    """Offline inventory; mature-unscored does not imply a missing database row."""
    evaluation.protocol()
    now = forward.checked_clock(clock)
    result = dict(
        as_of=now.isoformat(),
        latest_successful_cycle=None,
        latest_cycle=None,
        mature_unscored=[],
        pending_predictions=[],
        scored=[],
        invalid_predictions=[],
        invalid_outcomes=[],
        orphan_outcomes=[],
        invalid_scoring_journals=[],
        incomplete_cycles=[],
        failures=[],
        invalid_cursor=False,
        partial_files={
            label: len(list(folder.rglob("*.partial")))
            for label, folder in (
                ("predictions", records),
                ("outcomes", outcomes),
                ("scoring_operations", operations),
                ("collector_operations", collector_operations),
            )
        },
    )
    json_paths(collector_operations)  # Explicit directory readability check.
    _, result["invalid_collector_journals"] = evaluation.journals(collector_operations)
    paths = json_paths(records)
    for path in paths:
        try:
            prediction = evaluation.load_prediction(path)
            record = prediction["record"]
            evaluation.require(
                evaluation.utc_time(record["issued_at"]) <= now, "Future issuance."
            )
        except Exception:
            result["invalid_predictions"].append(path.name)
            continue
        outcome = outcomes / path.name
        if os.path.lexists(outcome):
            try:
                value = evaluation.load_outcome(outcome, prediction)
                evaluation.require(
                    evaluation.utc_time(value["evaluation_captured_at"]) <= now,
                    "Future score.",
                )
                result["scored"].append(path.name)
            except Exception:
                result["invalid_outcomes"].append(path.name)
        elif now < evaluation.utc_time(record["target_close_boundary"]) + forward.DELAY:
            result["pending_predictions"].append(path.name)
        else:
            result["mature_unscored"].append(path.name)
    names = {p.name for p in paths}
    result["orphan_outcomes"] = sorted(
        p.name for p in json_paths(outcomes) if p.name not in names
    )
    for path in json_paths(operations):
        try:
            journal = load_journal(path)
            evaluation.require(
                evaluation.utc_time(journal["started_at"]) <= now, "Future cycle."
            )
        except Exception:
            result["invalid_scoring_journals"].append(path.name)
            continue
        summary = {
            k: journal[k] for k in ("run_id", "started_at", "finished_at", "state")
        }
        summary["counts"] = {
            state: sum(r["status"] == state for r in journal["results"])
            for state in sorted(STATUSES)
        }
        summary["deferred_count"] = journal["deferred_count"]
        latest = result["latest_cycle"]
        if latest is None or summary["started_at"] > latest["started_at"]:
            result["latest_cycle"] = summary
        failed = journal["errors"] or any(
            r["status"] in ("failed", "skipped") or r["invalid_collector_journal_count"]
            for r in journal["results"]
        )
        if journal["state"] == "running":
            result["incomplete_cycles"].append(path.name)
        elif journal["state"] != "complete" or failed:
            result["failures"].append(
                {
                    **summary,
                    "errors": journal["errors"],
                    "records": [
                        r
                        for r in journal["results"]
                        if r["status"] in ("failed", "skipped")
                        or r["invalid_collector_journal_count"]
                    ],
                }
            )
        else:
            latest = result["latest_successful_cycle"]
            if latest is None or summary["finished_at"] > latest["finished_at"]:
                result["latest_successful_cycle"] = summary
    try:
        read_cursor(operations / "state" / "cursor.json")
    except Exception:
        result["invalid_cursor"] = True
    result["evidence_valid"] = not any(
        result[k]
        for k in (
            "invalid_predictions",
            "invalid_outcomes",
            "orphan_outcomes",
            "invalid_scoring_journals",
            "invalid_collector_journals",
            "invalid_cursor",
        )
    ) and not any(result["partial_files"].values())
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("cycle", "status"))
    args = parser.parse_args(argv)
    try:
        if args.command == "cycle":
            value, code = run_cycle()
        else:
            value = status_report()
            code = (
                0 if value["evidence_valid"] and not value["incomplete_cycles"] else 1
            )
        print(json.dumps(value, sort_keys=True, indent=2, allow_nan=False))
        return code
    except Exception:
        print("Forward scoring operation failed; details suppressed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

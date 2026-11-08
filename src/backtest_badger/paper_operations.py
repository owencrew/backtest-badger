"""Operational gates and credential-free diagnostic records for one portfolio cycle."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from numbers import Real
from uuid import UUID

import psycopg

from backtest_badger import paper_records as rec
from backtest_badger.paper_evidence import verify_portfolio
from backtest_badger.paper_reconciliation import IntegrityIssue
from backtest_badger.paper_types import require, utc

MISSING = {
    "forecast_missing",
    "late_forecast",
    "quote_unavailable",
    "missing_mark",
    "journal_pending",
    "exit_pending",
}
WARNING = {
    "provider_throttled",
    "filters_unavailable",
    "runtime_excessive",
    "clock_uncertain",
    "database_contention",
    "ageing_exit",
    "rejected_exits",
    "cycle_overlap",
    "repeat_failure",
}
CRITICAL = {
    "invalid_automation",
    "journal_conflict",
    "reconciliation_failed",
    "blocked_dust",
    "backup_failed",
    "original_missing",
    "restore_failed",
}


@dataclass(frozen=True)
class Incident:
    code: str
    portfolio: UUID
    subject: UUID | datetime

    def report(self, at, **metrics):
        require(
            isinstance(self.portfolio, UUID)
            and isinstance(self.subject, (UUID, datetime)),
            "Expected a portfolio and evidence identity or UTC slot.",
        )
        require(self.code in MISSING | WARNING | CRITICAL, "Unknown incident.")
        require(
            metrics.keys()
            <= {
                "attempt",
                "age_seconds",
                "elapsed_seconds",
                "http_status",
                "retry_after",
            }
            and all(
                isinstance(v, Real) and 0 <= v < float("inf") for v in metrics.values()
            ),
            "Invalid operational metric.",
        )
        ref = (
            utc(self.subject).isoformat()
            if isinstance(self.subject, datetime)
            else str(self.subject)
        )
        return dict(
            key=str(rec.identity(self.portfolio, self.code, ref)),
            code=self.code,
            severity="integrity"
            if self.code in CRITICAL
            else "warning"
            if self.code in WARNING
            else "missingness",
            portfolio=str(self.portfolio),
            subject=ref,
            observed_at=utc(at).isoformat(),
            **metrics,
        )


def diagnostics(plan, view, at, elapsed):
    p = view.state.account.portfolio
    pid = rec.identity("v1", "portfolio", p.key)
    slot = view.state.next_source_open
    rows = []

    def add(code, subject=slot, **metrics):
        rows.append(Incident(code, pid, subject).report(at, **metrics))

    for d in plan.decisions:
        if not d.forecast:
            add("forecast_missing", d.source_open)
        elif d.forecast.observed_at >= d.forecast.deadline:
            add("late_forecast", d.source_open)
    for mark in plan.marks:
        if mark["status"] in ("MARK_MISSING", "MARK_UNAVAILABLE"):
            add("missing_mark", datetime.fromisoformat(mark["slot"]))
    if elapsed >= 240:
        add("runtime_excessive", elapsed_seconds=elapsed)
    if plan.http_status in (418, 429):
        metrics = (
            {"retry_after": plan.retry_after} if plan.retry_after is not None else {}
        )
        add("provider_throttled", http_status=plan.http_status, **metrics)
    elif plan.result == "FILTER_REJECTED":
        add("filters_unavailable")
    elif plan.result == "MARKET_UNAVAILABLE":
        add("quote_unavailable")
    elif plan.reason == "awaiting_automation_evidence":
        add("journal_pending")
    elif plan.result == "INTEGRITY_PAUSE":
        reason = plan.reason or ""
        if "missing_archived_original" in reason:
            add("original_missing")
        elif "journal" in reason.lower() or "publisher" in reason.lower():
            add("journal_conflict")
        elif "invalid_original" in reason:
            add("invalid_automation")
        else:
            add("reconciliation_failed")
    exit_decision = view.state.exit_required
    if exit_decision:
        did = rec.identity(pid, "decision", exit_decision.identity)
        age = (at - exit_decision.at).total_seconds()
        add("ageing_exit" if age >= 300 else "exit_pending", did, age_seconds=age)
        failed = sum(
            a.decision == exit_decision.identity and a.status in {"REJECTED", "EXPIRED"}
            for a in view.attempts
        )
        if failed >= 2:
            add("rejected_exits", did, attempt=failed)
        if view.status == "BLOCKED_DUST":
            add("blocked_dust", did)
    return rows


def incident_counts(records):
    """Count recurring incident keys across invocations."""
    return Counter(row["key"] for row in records)


@dataclass(frozen=True)
class ClockHealth:
    synchronised: bool
    sampled_at: datetime
    uncertainty: timedelta

    def trusted(self, now):
        # Operational admission limits, separate from Stage 4A economic parameters.
        return (
            self.synchronised is True
            and timedelta(0) <= utc(now) - utc(self.sampled_at) <= timedelta(minutes=5)
            and timedelta(0) <= self.uncertainty <= timedelta(milliseconds=100)
        )


@contextmanager
def invocation(conn, pid):
    """Hold a dedicated session lock until exit or process death."""
    require(
        conn.autocommit and isinstance(pid, UUID),
        "Expected a dedicated autocommit session.",
    )
    key = int.from_bytes(pid.bytes[:8], signed=True)
    locked = conn.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone()[0]
    try:
        yield locked
    finally:
        if locked:
            conn.execute("SELECT pg_advisory_unlock(%s)", (key,))


def run_checked(conn, pid, root, health, clock, operation):
    """
    Execute a supplied one-cycle rehearsal only after health, exclusion and
    provenance gates.
    """
    at = clock.now()

    def blocked(code, subject=pid):
        return None, Incident(code, pid, subject).report(at)

    if not health or not health.trusted(at):
        return blocked("clock_uncertain")
    try:
        with invocation(conn, pid) as acquired:
            if not acquired:
                return blocked("cycle_overlap")
            verify_portfolio(conn, pid, root)
            return operation(), None
    except IntegrityIssue as exc:
        return blocked(
            "original_missing"
            if exc.code == "original_evidence_integrity"
            else "reconciliation_failed",
            exc.evidence_id,
        )
    except psycopg.errors.LockNotAvailable:
        return blocked("database_contention")

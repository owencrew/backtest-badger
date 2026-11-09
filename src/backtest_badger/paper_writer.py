"""One prospective simulated writer cycle for an explicitly selected account."""

import json
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path
from time import perf_counter
from uuid import UUID

import psycopg

from backtest_badger import paper_evidence as originals
from backtest_badger import paper_persistence as store
from backtest_badger import paper_records as records
from backtest_badger.paper_admission import (
    DeadlineElapsed,
    commit_before,
    locked_transaction,
)
from backtest_badger.paper_artifacts import directory, publish_once, read_original
from backtest_badger.paper_clock import duration
from backtest_badger.paper_execution import Reason, Status, simulate_order
from backtest_badger.paper_forward_adapter import EvidenceError, read_forecast
from backtest_badger.paper_market_data import (
    FILTERS,
    QUOTE,
    MarketError,
    parse_quote,
    url_for,
)
from backtest_badger.paper_operations import Incident, diagnostics, invocation
from backtest_badger.paper_reconciliation import IntegrityIssue, transaction
from backtest_badger.paper_recovery import CUTOFF, recover, recovery_view
from backtest_badger.paper_types import STEP, Action, require, validate_filters
from backtest_badger.paper_worker import (
    WINDOW,
    Plan,
    due_slots,
    forecast_plans,
    order_plan,
)


@dataclass(frozen=True)
class WriterConfig:
    portfolio_id: UUID
    symbol: str
    config_sha256: str
    records: Path
    journals: Path
    archive: Path
    runtime: Path


class CycleStop(Exception):
    """An operational prerequisite changed during the invocation."""


class OrderRejected(Exception):
    """The simulator found the submitted intent ineligible for a fill."""


def _noop(_):
    pass


class Writer:
    """One-use session. Transport returns a freshly sampled original Response."""

    def __init__(self, conn, config, clock, health, acquire, *, checkpoint=_noop):
        self.conn, self.config, self.clock = conn, config, clock
        self.pid = config.portfolio_id
        self.read_health = health if callable(health) else lambda: health
        self.acquire, self.checkpoint = acquire, checkpoint
        self.timings = {}
        self.incidents = {}
        self.plan = Plan(clock.run_id, "WAITING_FOR_HORIZON")
        self.order_id = None

    def now(self):
        try:
            at = self.clock.now()
        except ValueError as exc:
            raise CycleStop("clock_uncertain") from exc
        self.health = self.read_health()
        if not self.health or not self.health.trusted(at):
            raise CycleStop("clock_uncertain")
        if perf_counter() - self.started >= 240:
            raise CycleStop("runtime_excessive")
        return at

    def incident(self, code, subject=None, **metrics):
        # On reversal, log the last witnessed UTC sample without sampling again.
        at = self.clock.previous.wall if self.clock.previous else self.clock.wall()
        row = Incident(code, self.pid, subject or self.pid).report(at, **metrics)
        self.incidents[row["key"]] = row

    def audited(self):
        start = perf_counter()
        with transaction(self.conn, readonly=True) as cur:
            snap = originals.audit_sources(cur, self.pid, self.config.archive)
            view = recovery_view(cur, self.pid, snap)
        p = view.state.account.portfolio
        require(
            p.symbol == self.config.symbol
            and p.config_sha256 == self.config.config_sha256
            and records.identity("v1", "portfolio", p.key) == self.pid,
            "Configured account identity mismatch.",
        )
        self.timings["reconciliation_s"] = (
            self.timings.get("reconciliation_s", 0) + perf_counter() - start
        )
        return view

    def run(self):
        self.started = perf_counter()
        self.clock.begin_cycle()
        result = "STOPPED"
        try:
            self.now()
            with invocation(self.conn, self.pid) as locked:
                if not locked:
                    raise CycleStop("cycle_overlap")
                result = self.locked_cycle()
        except CycleStop as exc:
            self.incident(str(exc))
            result = "STOPPED"
        except (psycopg.errors.LockNotAvailable, psycopg.errors.QueryCanceled):
            self.incident("database_contention", self.order_id)
            result = "STOPPED"
        except psycopg.OperationalError:
            self.incident("worker_interrupted", self.order_id)
            result = "STOPPED"
        except (OSError, ValueError, psycopg.Error):
            self.incident("reconciliation_failed", self.order_id)
            result = "STOPPED"
        self.timings["cycle_s"] = perf_counter() - self.started
        return dict(
            run_id=self.clock.run_id,
            portfolio=str(self.pid),
            result=result,
            reason=self.plan.reason,
            order_id=str(self.order_id) if self.order_id else None,
            incidents=list(self.incidents.values()),
            timings=self.timings,
        )

    def locked_cycle(self):
        halt = str(self.pid) + ".halt"
        try:
            with directory(self.config.runtime) as fd:
                try:
                    saved = json.loads(read_original(fd, halt, 4096))
                except FileNotFoundError:
                    saved = None
            if saved is not None:
                self.incident(saved["code"], UUID(saved["subject"]))
                return "STOPPED"
            view = self.audited()
            require(view.state.last_at <= self.now(), "Recovery clock reversal.")
            self.timings["recovery_s"] = perf_counter() - self.started
            result = view.status
            if view.status == "ACTIVE":
                result = self.execute(view)
                self.marks(view)
            final = self.audited()
            for row in diagnostics(
                self.plan, final, self.now(), perf_counter() - self.started
            ):
                self.incidents[row["key"]] = row
            self.checkpoint("shutdown")
            return result
        except EvidenceError as exc:
            code = (
                "original_missing"
                if "unavailable" in exc.code
                else "invalid_automation"
            )
            if "journal" in str(exc.__cause__).lower():
                code = "journal_conflict"
            subject = self.pid
        except IntegrityIssue as exc:
            code = (
                "original_missing"
                if exc.code == "original_evidence_integrity"
                else "reconciliation_failed"
            )
            subject = exc.evidence_id
        except (ValueError, ArithmeticError, OSError, psycopg.IntegrityError):
            code = "reconciliation_failed"
            subject = self.order_id or self.pid
        self.incident(code, subject)
        publish_once(
            self.config.runtime,
            halt,
            json.dumps(
                {"code": code, "subject": str(subject), "run": self.clock.run_id}
            ).encode(),
        )
        return "STOPPED"

    def execute(self, view):
        if view.pending:
            order = view.pending
            self.order_id = records.identity(self.pid, "order", order.identity)
            self.incident("worker_interrupted", self.order_id)
            return self.terminal(
                order,
                "interrupted_observation"
                if view.pending_quotes
                else "interrupted_intent",
            )

        def discover(p, opened, clock):
            self.now()
            return read_forecast(
                p, opened, self.config.records, self.config.journals, clock
            )

        reader = originals.recovery_reader(self.config.archive, view.state, discover)
        state, decisions, observations = self.discover_decisions(view, reader)
        if decisions:
            view = recover(self.conn, self.pid)
            require(
                view.state.decisions == state.decisions, "Decision admission changed."
            )
        start = perf_counter()
        self.plan = order_plan(
            view,
            view.state,
            replace(self.plan, decisions=decisions, observations=observations),
            lambda: recover(self.conn, self.pid),
            reader,
            lambda p, clock: self.acquire(FILTERS, p.symbol, clock),
            self.clock,
        )
        self.timings["preparation_s"] = perf_counter() - start
        if not self.plan.order:
            return self.plan.result
        order = self.plan.order

        def prepare(intent):
            nonlocal order
            at = self.now()
            if intent.side == "BUY" and at >= intent.decision.forecast.deadline:
                raise CycleStop("late_forecast")
            try:
                validate_filters(
                    self.plan.filters, intent.decision.portfolio, at, acquired_by=at
                )
            except ValueError as exc:
                raise CycleStop("filters_unavailable") from exc
            order = replace(
                intent, submitted_at=at, expires_at=at + timedelta(seconds=30)
            )
            return order

        self.checkpoint("before_submission")
        start = perf_counter()
        receipt = originals.submit_archived_order(
            self.conn,
            self.pid,
            self.config.archive,
            order,
            self.plan.attempt,
            self.plan.filter_source,
            prepare=prepare,
        )
        self.timings["submission_s"] = perf_counter() - start
        require(receipt.created, "Unexpected existing intent.")
        self.order_id = receipt.id
        self.checkpoint("after_submission")
        return self.execute_quote(order)

    def discover_decisions(self, view, reader):
        state = view.state
        decisions, observations = [], []
        self.timings["discovery_s"] = 0.0
        while True:
            opened = state.next_source_open
            start = perf_counter()
            state, horizon, found = forecast_plans(
                replace(view, state=state), reader, self.clock, one_horizon=True
            )
            self.timings["discovery_s"] += perf_counter() - start
            observed = {o.forecast: o for o in found}
            for d in horizon:
                self.archive_decision(d, observed.get(d.forecast))
            decisions.extend(horizon)
            observations.extend(found)
            # Persist progress before the next expensive journal scan. An overdue
            # backlog must not starve an already established liquidation obligation.
            if state.next_source_open == opened or (
                state.exit_required
                and state.next_source_open + STEP + CUTOFF < self.now()
            ):
                break
        return state, tuple(decisions), tuple(observations)

    def archive_decision(self, decision, observation):
        def admit():
            at = self.now()
            if (
                decision.forecast
                and decision.action != Action.SIGNAL_INELIGIBLE
                and at >= decision.forecast.deadline
            ):
                raise CycleStop("late_forecast")

        self.checkpoint("before_decision")
        originals.record_archived_decision(
            self.conn, self.pid, self.config.archive, decision, observation, admit=admit
        )
        self.checkpoint("after_decision")

    def terminal(self, order, reason):
        with store._write(self.conn, self.pid) as (cur, _):
            o = store._order(cur, self.pid, self.order_id)
            at = self.now()
            expired = at >= order.expires_at
            status = Status.EXPIRED if expired else Status.REJECTED
            reason = Reason.ORDER_EXPIRED if expired else reason
            store._terminal(cur, o, status, reason, at)
        self.plan = replace(self.plan, reason=str(reason))
        self.incident("order_expired" if expired else "order_rejected", self.order_id)
        return status.value

    def execute_quote(self, order):
        self.checkpoint("before_quote")
        started = self.now()
        if started >= order.expires_at:
            return self.terminal(order, Reason.ORDER_EXPIRED)
        request = self.clock.sample()
        response = None
        try:
            response = self.acquire(QUOTE, self.config.symbol, self.clock)
            self.checkpoint("after_receipt")
            if (
                response.run_id != self.clock.run_id
                or response.start.wall < request.wall
                or response.start.before_ns < request.after_ns
            ):
                raise MarketError("quote_not_from_request")
            q = parse_quote(response, order.decision.portfolio, response.end.wall)
            self.timings["quote_http_s"] = float(q.elapsed_seconds)
        except MarketError as exc:
            if exc.code == "provider_cooldown":
                self.market_incident(exc, self.order_id)
                return self.terminal(order, exc.code)
            self.failed_quote(order, started, exc, response)
            return self.terminal(order, exc.code)

        originals.archive_quote(self.config.archive, q)
        # The immutable observation survives a process loss before settlement.
        with store._write(self.conn, self.pid) as (cur, _):
            o = store._order(cur, self.pid, self.order_id)
            latest = cur.execute(
                "SELECT paper_latest(%s) AS at", (self.pid,)
            ).fetchone()["at"]
            if latest <= q.response_received_at:
                qid = store._event(
                    cur,
                    self.pid,
                    "QUOTE_OBSERVED",
                    q.identity,
                    q.response_received_at,
                    self.now(),
                    order=o,
                    **records.quote_fields(q),
                ).id
            else:
                qid = None
        if qid is None:
            exc = MarketError("portfolio_advanced")
            self.failed_quote(order, started, exc, response)
            return self.terminal(order, exc.code)
        self.checkpoint("after_observation")
        return self.settle(order, q, qid, response.end)

    def failed_quote(self, order, started, exc, response):
        # A foreign response is evidence of rejection only. Never borrow its identity.
        response = response or exc.response
        started = exc.request_started_at or started
        body = None
        end = latency = None
        key = order.identity
        if response:
            body = response.body
            key = originals.archive_failed_response(
                self.config.archive, self.order_id, response, exc.code
            )
            if (
                response.run_id == self.clock.run_id
                and started <= response.start.wall <= response.end.wall <= self.now()
            ):
                started, end = response.start.wall, response.end.wall
                try:
                    latency = 1000 * duration(response.start, response.end)
                except ValueError:
                    # The private envelope retains the inconsistent ticks.
                    latency = None
        store.record_quote_failure(
            self.conn,
            self.pid,
            self.order_id,
            key=key,
            run_id=self.clock.run_id,
            source_url=url_for(QUOTE, self.config.symbol),
            request_started_at=started,
            discovered_at=self.now(),
            reason=exc.code,
            http_status=exc.status,
            raw_body=body,
            response_received_at=end,
            latency_ms=latency,
        )
        self.market_incident(exc, self.order_id)

    def market_incident(self, exc, subject):
        if exc.status in (418, 429):
            metrics = (
                {"retry_after": exc.retry_after} if exc.retry_after is not None else {}
            )
            self.incident(
                "provider_throttled", subject, http_status=exc.status, **metrics
            )
        else:
            self.incident("quote_unavailable", subject)

    def settle(self, order, q, qid, received):
        wait = perf_counter()
        try:
            with locked_transaction(self.conn, self.pid) as (cur, p):
                o = store._order(cur, self.pid, self.order_id)
                self.timings["settlement_lock_s"] = perf_counter() - wait
                require(
                    p["state"] == "ACTIVE"
                    and o["status"] == "SUBMITTED"
                    and o["run_id"] == self.clock.run_id
                    and o["snapshot_seq"]
                    == p["ledger_highwater"]
                    == order.balances.ledger_seq,
                    "Order or account changed after submission.",
                )
                committed, observed = store.execution_inputs(
                    cur, records.portfolio(p), o, qid
                )
                require(
                    committed == order and observed == q,
                    "Committed execution evidence changed.",
                )
                self.now()
                use = self.clock.sample()
                at = use.wall
                self.timings["receipt_to_use_s"] = float(duration(received, use))
                result = simulate_order(
                    committed, observed, self.plan.filters, at, run_id=self.clock.run_id
                )
                if result.fill:
                    store._post_fill(cur, o, qid, result, at)
                elif result.reason == Reason.EXIT_BLOCKED_DUST:
                    store._dust(cur, o, qid, self.plan.filters, self.clock.run_id, at)
                else:
                    raise OrderRejected(result.reason)
                self.checkpoint("during_fill")
                self.now()
                deadline = min(
                    q.response_received_at + timedelta(seconds=1),
                    order.expires_at,
                    self.plan.filters.observed_at + timedelta(hours=1),
                    self.health.sampled_at + WINDOW,
                )
                if order.side == "BUY":
                    deadline = min(deadline, order.decision.forecast.deadline)

                def before_commit():
                    self.checkpoint("before_commit")
                    self.now()

                self.timings["receipt_to_admission_s"] = commit_before(
                    cur,
                    self.clock,
                    received,
                    deadline,
                    before_commit=before_commit,
                )
            self.timings["receipt_to_ack_s"] = float(
                duration(received, self.clock.sample())
            )
            self.plan = replace(self.plan, reason=result.reason.value)
            self.checkpoint("after_fill_commit")
            return result.status.value
        except (OrderRejected, DeadlineElapsed) as exc:
            self.timings["receipt_to_rejection_s"] = float(
                duration(received, self.clock.sample())
            )
            reason = str(exc)
            if isinstance(exc, DeadlineElapsed):
                now = self.now()
                reason = simulate_order(
                    order, q, self.plan.filters, now, run_id=self.clock.run_id
                ).reason
                if reason in (Reason.FILLED, Reason.EXIT_BLOCKED_DUST):
                    reason = Reason.INVALID_QUOTE
            return self.terminal(order, reason)

    def mark_slot(self, p, slot):
        self.now()
        request = self.clock.sample()
        response = self.acquire(QUOTE, self.config.symbol, self.clock)
        if (
            response.run_id != self.clock.run_id
            or response.start.wall < request.wall
            or response.start.before_ns < request.after_ns
        ):
            raise MarketError("quote_not_from_request")
        q = parse_quote(response, p, self.now())
        originals.archive_quote(self.config.archive, q)
        with locked_transaction(self.conn, self.pid) as (cur, row):
            at = self.now()
            if at >= slot + WINDOW or at - q.response_received_at > timedelta(
                seconds=1
            ):
                raise MarketError("mark_elapsed")
            if _slot_recorded(cur, self.pid, slot):
                return
            last_posting = cur.execute(
                "SELECT max(posted_at) AS at FROM paper_ledger_entry "
                "WHERE portfolio_id=%s",
                (self.pid,),
            ).fetchone()["at"]
            if last_posting > q.response_received_at:
                raise MarketError("mark_prefix_changed")
            store._mark(cur, self.pid, row, slot, at, q, None, False)
            self.checkpoint("during_mark")
            commit_before(
                cur,
                self.clock,
                response.end,
                min(
                    slot + WINDOW,
                    q.response_received_at + timedelta(seconds=1),
                    self.health.sampled_at + WINDOW,
                ),
                before_commit=self.now,
            )

    def marks(self, view):
        rows = []
        for slot in due_slots(view, self.now()):
            if self.now() < slot + WINDOW:
                try:
                    self.mark_slot(view.state.account.portfolio, slot)
                    continue
                except DeadlineElapsed:
                    self.incident("missing_mark", slot)
                except MarketError as exc:
                    self.market_incident(exc, slot)
            status = "MARK_UNAVAILABLE"
            if self.now() >= slot + WINDOW:
                with store._write(self.conn, self.pid) as (cur, p):
                    if _slot_recorded(cur, self.pid, slot):
                        continue
                    store._mark(
                        cur,
                        self.pid,
                        p,
                        slot,
                        self.now(),
                        None,
                        "window_elapsed",
                        False,
                    )
                status = "MARK_MISSING"
            rows.append({"slot": slot.isoformat(), "status": status})
        self.plan = replace(self.plan, marks=tuple(rows))


def _slot_recorded(cur, pid, slot):
    return (
        cur.execute(
            "SELECT 1 FROM paper_market_event WHERE portfolio_id=%s AND mark_slot=%s",
            (pid, slot),
        ).fetchone()
        is not None
    )

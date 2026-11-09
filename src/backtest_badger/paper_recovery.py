"""Reconstruct the planner's state in one read-only Stage 4C snapshot."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from backtest_badger import paper_records as records
from backtest_badger.paper_execution import Order
from backtest_badger.paper_reconciliation import (
    IntegrityIssue,
    inspect_portfolio,
    transaction,
)
from backtest_badger.paper_strategy import State
from backtest_badger.paper_types import STEP, Action, require, utc

CUTOFF = timedelta(minutes=16)


def boundary(at):
    return utc(at).replace(hour=at.hour // 4 * 4, minute=0, second=0, microsecond=0)


@dataclass(frozen=True)
class Attempt:
    decision: str
    number: int
    status: str
    at: datetime


@dataclass(frozen=True)
class Recovery:
    state: State
    status: str
    activated: datetime | None
    attempts: tuple[Attempt, ...] = ()
    pending: Order | None = None
    pending_quotes: int = 0
    slots: frozenset = frozenset()


def recover(conn, pid):
    """Join planner context to Stage 4C's audit in the same read-only snapshot."""
    try:
        with transaction(conn, readonly=True) as cur:
            return recovery_view(cur, pid, inspect_portfolio(cur, pid))
    except IntegrityIssue:
        raise
    except (
        KeyError,
        IndexError,
        ArithmeticError,
        ValueError,
        TypeError,
        StopIteration,
    ) as exc:
        raise IntegrityIssue("invalid_portfolio_evidence", pid) from exc


def recovery_view(cur, pid, snap):
    p = snap.account.portfolio
    meta = cur.execute(
        "SELECT activated_at, paper_latest(portfolio_id) AS latest, "
        "(SELECT event_type FROM paper_market_event WHERE event_id="
        "state_event_id) AS state_event FROM paper_portfolio "
        "WHERE portfolio_id=%s",
        (pid,),
    ).fetchone()
    rows = cur.execute(
        "SELECT * FROM paper_decision WHERE portfolio_id=%s "
        "ORDER BY source_open_time, decided_at, "
        "(decision_result='SIGNAL_INELIGIBLE') DESC",
        (pid,),
    ).fetchall()
    decisions = {r["decision_id"]: records.decision(p, r) for r in rows}
    activated = meta["activated_at"]
    opened = boundary((activated or p.inception_at) - CUTOFF)
    streak = 0
    for d in decisions.values():
        require(d.source_open == opened, "Discontinuous durable horizon.")
        if d.action != Action.SIGNAL_INELIGIBLE:
            opened += STEP
            streak = 0 if d.forecast else streak + 1
        require(d.missed_streak == streak, "Inconsistent missed streak.")
    state = State(
        snap.account,
        opened,
        meta["latest"] or p.inception_at,
        streak,
        decisions.get(snap.exit_decision_id),
        snap.exit_satisfied_at,
        tuple(decisions.values()),
    )
    pending = snap.pending_order
    if pending:
        pending = records.order(
            p,
            next(r for r in rows if r["decision_id"] == pending["decision_id"]),
            pending,
        )
    attempts = tuple(
        Attempt(
            decisions[o["decision_id"]].identity,
            o["attempt_number"],
            o["status"],
            o["submitted_at"],
        )
        for o in cur.execute(
            "SELECT * FROM paper_order WHERE portfolio_id=%s ORDER BY submitted_at",
            (pid,),
        )
    )
    slots = frozenset(
        r["mark_slot"]
        for r in cur.execute(
            "SELECT mark_slot FROM paper_market_event WHERE portfolio_id=%s "
            "AND mark_slot IS NOT NULL",
            (pid,),
        )
    )
    status = (
        "BLOCKED_DUST" if meta["state_event"] == "EXIT_BLOCKED_DUST" else snap.state
    )
    return Recovery(
        state, status, activated, attempts, pending, len(snap.pending_quotes), slots
    )

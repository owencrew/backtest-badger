"""Final PG17 admission for transactions using a perishable market observation."""

from contextlib import contextmanager
from datetime import timedelta

import psycopg
from psycopg import sql
from psycopg.pq import TransactionStatus
from psycopg.rows import dict_row

from backtest_badger.paper_clock import duration
from backtest_badger.paper_persistence import _locked_portfolio
from backtest_badger.paper_reconciliation import configure_transaction
from backtest_badger.paper_types import require


class DeadlineElapsed(Exception):
    """The provisional financial or valuation transaction was rolled back."""


@contextmanager
def locked_transaction(conn, pid):
    """Only commit_before can commit. An exception or early return rolls back."""
    require(
        conn.autocommit and conn.info.transaction_status == TransactionStatus.IDLE,
        "Expected a dedicated idle writer connection.",
    )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("BEGIN ISOLATION LEVEL READ COMMITTED")
        try:
            configure_transaction(cur)
            yield cur, _locked_portfolio(cur, pid)
        finally:
            if conn.info.transaction_status in (
                TransactionStatus.INTRANS,
                TransactionStatus.INERROR,
            ):
                cur.execute("ROLLBACK")


def commit_before(cur, clock, receipt, deadline, *, before_commit):
    """Check the cutoff on the backend and COMMIT in the same protocol message.

    Anchor the remaining lifetime to a backend sample taken before the client
    samples again. This charges the return trip to the budget and works when
    the fabricated UTC epoch differs from the database's wall clock.
    """
    cur.execute("SET CONSTRAINTS ALL IMMEDIATE")
    anchor = cur.execute("SELECT clock_timestamp() AS at").fetchone()["at"]
    sample = clock.sample()
    elapsed_ns = int(duration(receipt, sample) * 1_000_000_000)
    # Round age upward to PostgreSQL's microsecond resolution.
    monotonic_remaining = timedelta(microseconds=1_000_000 - (elapsed_ns + 999) // 1000)
    remaining = min(monotonic_remaining, deadline - sample.wall)
    if remaining <= timedelta(0):
        raise DeadlineElapsed()
    before_commit()
    # A false predicate deliberately aborts the entire simple-query message,
    # including COMMIT. A lost acknowledgement is resolved from durable state.
    guard = sql.SQL(
        "WITH sample AS MATERIALIZED (SELECT clock_timestamp() AS at) "
        "SELECT at, 1 / (at >= {} AND at < {})::integer AS admitted FROM sample; COMMIT"
    ).format(sql.Literal(anchor), sql.Literal(anchor + remaining))
    try:
        cur.execute(guard, prepare=False)
    except psycopg.errors.DivisionByZero as exc:
        raise DeadlineElapsed() from exc
    admitted = cur.fetchone()["at"]
    return (elapsed_ns / 1_000_000_000) + (admitted - anchor).total_seconds()

"""Revision 0002 transactions with caller-supplied evidence and clocks."""

from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID

from psycopg import sql
from psycopg.types.json import Jsonb

from backtest_badger import paper_records as records
from backtest_badger.paper_accounting import Account, fund_account
from backtest_badger.paper_execution import Order, simulate_order
from backtest_badger.paper_reconciliation import inspect_portfolio, transaction
from backtest_badger.paper_types import (
    EXECUTION_POLICY,
    VALUATION_POLICY,
    digest,
    identifier,
    number,
    require,
    utc,
    validate_filters,
    validate_quote,
)


@dataclass(frozen=True)
class Receipt:
    id: UUID
    created: bool


class EvidenceConflict(ValueError):
    """An existing identity refers to different authoritative evidence."""


def _put(cur, table, pk, key, fields):
    """Insert or compare every supplied immutable field, including NULL and JSONB.

    The caller owns the portfolio lock (or, for creation, races on the unique PK).
    Look up first: insert triggers check current state, which can differ on a retry.
    """
    values = [Jsonb(v) if isinstance(v, dict) else v for v in fields.values()]
    table_name, id_name = sql.Identifier(table), sql.Identifier(pk)
    matches = sql.SQL(" AND ").join(
        sql.SQL("{} IS NOT DISTINCT FROM %s").format(sql.Identifier(k)) for k in fields
    )
    query = sql.SQL("SELECT ({}) AS same FROM {} WHERE {}=%s").format(
        matches, table_name, id_name
    )

    def existing():
        row = cur.execute(query, [*values, key]).fetchone()
        if row and not row["same"]:
            raise EvidenceConflict(f"Conflicting {table} evidence for {key}")
        return row is not None

    if existing():
        return Receipt(key, False)
    cols = sql.SQL(",").join(map(sql.Identifier, (pk, *fields)))
    params = sql.SQL(",").join(sql.Placeholder() for _ in range(1 + len(fields)))
    cur.execute(
        sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO NOTHING").format(
            table_name, cols, params, id_name
        ),
        [key, *values],
    )
    if cur.rowcount == 0:
        require(existing(), "Concurrent evidence missing.")
        return Receipt(key, False)
    return Receipt(key, True)


@contextmanager
def _write(conn, pid):
    require(isinstance(pid, UUID), "Expected portfolio UUID.")
    with transaction(conn) as cur:
        yield cur, _locked_portfolio(cur, pid)


def _locked_portfolio(cur, pid):
    row = cur.execute(
        "SELECT * FROM paper_portfolio WHERE portfolio_id=%s FOR UPDATE", (pid,)
    ).fetchone()
    require(row is not None, "Unknown portfolio.")
    return row


def create_portfolio(conn, p, config, implementation_sha256, created_at):
    with transaction(conn) as cur:
        return _create(cur, p, config, implementation_sha256, created_at)


def _create(cur, p, config, implementation_sha256, created_at):
    utc(created_at)
    digest(implementation_sha256)
    expected = records.configuration(
        p.symbol, p.model_recipe_sha256, config.get("cohort")
    )
    canonical = records.canonical(config)
    require(canonical == records.canonical(expected), "Unsupported v1 configuration.")
    require(
        records.fingerprint(canonical) == p.config_sha256,
        "Configuration fingerprint mismatch.",
    )
    pid = records.identity("v1", "portfolio", p.key)
    market = cur.execute(
        "SELECT market_id FROM market WHERE venue=%s AND market_type=%s AND symbol=%s",
        (p.venue, p.market_type, p.symbol),
    ).fetchone()
    require(market is not None, "Unknown spot market.")
    return _put(
        cur,
        "paper_portfolio",
        "portfolio_id",
        pid,
        dict(
            portfolio_key=p.key,
            market_id=market["market_id"],
            base_asset=p.base_asset,
            quote_asset="USDT",
            strategy_id=p.strategy_id,
            strategy_version=p.strategy_version,
            model_id="ridge",
            strategy_config=config,
            config_canonical=canonical,
            strategy_config_sha256=p.config_sha256,
            protocol_sha256=p.protocol_sha256,
            model_recipe_sha256=p.model_recipe_sha256,
            implementation_sha256=implementation_sha256,
            execution_policy_sha256=records.fingerprint(EXECUTION_POLICY),
            valuation_policy_sha256=records.fingerprint(VALUATION_POLICY),
            initial_cash=10000,
            created_at=created_at,
            inception_at=p.inception_at,
        ),
    )


def fund_portfolio(conn, pid, at):
    with _write(conn, pid) as (cur, p):
        return _fund(cur, pid, p, at)


def _fund(cur, pid, p, at):
    account = fund_account(Account(records.portfolio(p)), at)
    receipt = _put(
        cur,
        "paper_ledger_entry",
        "ledger_entry_id",
        records.identity(pid, "funding", "initial"),
        dict(
            portfolio_id=pid,
            ledger_seq=1,
            entry_type="INITIAL_FUNDING",
            asset="USDT",
            delta_units=account.cash,
            posted_at=at,
        ),
    )
    if receipt.created:
        cur.execute(
            "UPDATE paper_portfolio SET ledger_highwater=1 WHERE portfolio_id=%s",
            (pid,),
        )
    return receipt


def record_decision(conn, pid, d, *, artifact_relpath=None, prediction_id=None):
    with _write(conn, pid) as (cur, p):
        require(records.portfolio(p) == d.portfolio, "Decision portfolio mismatch.")
        return _put(
            cur,
            "paper_decision",
            "decision_id",
            records.identity(pid, "decision", d.identity),
            records.decision_fields(pid, d, artifact_relpath, prediction_id),
        )


def submit_order(conn, pid, order, attempt_number):
    require(isinstance(order, Order), "Expected immutable order intent.")
    with _write(conn, pid) as (cur, p):
        did = records.identity(pid, "decision", order.decision.identity)
        d = cur.execute(
            "SELECT * FROM paper_decision WHERE decision_id=%s AND portfolio_id=%s",
            (did, pid),
        ).fetchone()
        require(
            d and records.decision(records.portfolio(p), d) == order.decision,
            "Unknown or conflicting decision.",
        )
        return _put(
            cur,
            "paper_order",
            "order_id",
            records.identity(pid, "order", order.identity),
            dict(
                portfolio_id=pid,
                decision_id=did,
                client_order_key=order.identity,
                run_id=order.run_id,
                side=order.side.value,
                intent="SPEND_AVAILABLE_CASH"
                if order.side == "BUY"
                else "SELL_ALL_BASE",
                attempt_number=attempt_number,
                budget_cash_snapshot=order.balances.cash,
                base_qty_snapshot=order.balances.quantity,
                snapshot_seq=order.balances.ledger_seq,
                snapshot_at=order.balances.at,
                submitted_at=order.submitted_at,
                expires_at=order.expires_at,
                created_at=order.submitted_at,
                policy_sha256=p["execution_policy_sha256"],
            ),
        )


def _order(cur, pid, oid):
    require(isinstance(oid, UUID), "Expected order UUID.")
    o = cur.execute(
        "SELECT * FROM paper_order WHERE portfolio_id=%s AND order_id=%s FOR UPDATE",
        (pid, oid),
    ).fetchone()
    require(o is not None, "Unknown portfolio order.")
    return o


def _event(cur, pid, typ, key, at, recorded_at, *, order=None, **fields):
    utc(at)
    utc(recorded_at)
    if order:
        fields.update(order_id=order["order_id"], decision_id=order["decision_id"])
    return _put(
        cur,
        "paper_market_event",
        "event_id",
        records.identity(pid, typ, key),
        dict(
            portfolio_id=pid,
            event_type=typ,
            event_at=at,
            recorded_at=recorded_at,
            **fields,
        ),
    )


def record_quote(conn, pid, oid, quote, recorded_at):
    with _write(conn, pid) as (cur, p):
        validate_quote(quote, records.portfolio(p), quote.response_received_at)
        return _event(
            cur,
            pid,
            "QUOTE_OBSERVED",
            quote.identity,
            quote.response_received_at,
            recorded_at,
            order=_order(cur, pid, oid),
            **records.quote_fields(quote),
        )


def record_quote_failure(
    conn,
    pid,
    oid,
    *,
    key,
    run_id,
    source_url,
    request_started_at,
    discovered_at,
    reason,
    http_status=None,
    raw_body=None,
    response_received_at=None,
    latency_ms=None,
):
    from hashlib import sha256

    utc(request_started_at)
    require(
        raw_body is None or (type(raw_body) is bytes and len(raw_body) <= 4096),
        "Invalid failure response size.",
    )
    if latency_ms is not None:
        require(number(latency_ms) >= 0, "Invalid failure latency.")
    if response_received_at is not None:
        utc(response_received_at)
    with _write(conn, pid) as (cur, _):
        return _event(
            cur,
            pid,
            "QUOTE_FAILED",
            key,
            discovered_at,
            discovered_at,
            order=_order(cur, pid, oid),
            quote_key=key,
            run_id=run_id,
            request_started_at=request_started_at,
            source_url=source_url,
            reason_code=reason,
            http_status=http_status,
            raw_body=raw_body,
            response_received_at=response_received_at,
            latency_ms=latency_ms,
            raw_body_sha256=sha256(raw_body).hexdigest()
            if raw_body is not None
            else None,
        )


def _execution(cur, portfolio, o, quote_id, filters, at, run_id):
    q = cur.execute(
        "SELECT * FROM paper_market_event WHERE event_id=%s "
        "AND portfolio_id=%s AND "
        "order_id=%s AND event_type='QUOTE_OBSERVED'",
        (quote_id, o["portfolio_id"], o["order_id"]),
    ).fetchone()
    require(q is not None, "Unknown original order quote.")
    d = cur.execute(
        "SELECT * FROM paper_decision WHERE decision_id=%s", (o["decision_id"],)
    ).fetchone()
    order = records.order(portfolio, d, o)
    validate_filters(filters, portfolio, at, acquired_by=order.submitted_at)
    result = simulate_order(
        order, records.quote(portfolio, q), filters, at, run_id=run_id
    )
    return result


def reject_dust(conn, pid, oid, quote_id, filters, *, run_id, at):
    """Persist the effective dust evidence and pause the exposed portfolio."""
    with _write(conn, pid) as (cur, p):
        o = _order(cur, pid, oid)
        result = _execution(cur, records.portfolio(p), o, quote_id, filters, at, run_id)
        require(
            result.reason == "EXIT_BLOCKED_DUST",
            "Supplied evidence does not establish dust.",
        )
        terminal = _event(
            cur,
            pid,
            "ORDER_REJECTED",
            str(oid),
            at,
            at,
            order=o,
            reason_code="EXIT_BLOCKED_DUST",
        )
        if terminal.created:
            cur.execute(
                "UPDATE paper_order SET status='REJECTED' WHERE order_id=%s", (oid,)
            )
        _event(
            cur,
            pid,
            "EXIT_BLOCKED_DUST",
            str(oid),
            at,
            at,
            order=o,
            reason_code="EXIT_BLOCKED_DUST",
            reference_event_id=terminal.id,
            quote_event_id=quote_id,
            run_id=run_id,
            **records.filter_fields(filters),
        )
        return terminal


def terminate_order(conn, pid, oid, *, status, reason, at):
    require(
        reason != "EXIT_BLOCKED_DUST",
        "Use reject_dust with the original quote and filters.",
    )
    require(status in ("REJECTED", "EXPIRED"), "Expected unsuccessful terminal state.")
    with _write(conn, pid) as (cur, _):
        o = _order(cur, pid, oid)
        typ = "ORDER_REJECTED" if status == "REJECTED" else "ORDER_EXPIRED"
        receipt = _event(cur, pid, typ, str(oid), at, at, order=o, reason_code=reason)
        if receipt.created:
            cur.execute(
                "UPDATE paper_order SET status=%s WHERE order_id=%s", (status, oid)
            )
        return receipt


def commit_fill(conn, pid, oid, quote_id, filters, *, run_id, at, recorded_at):
    """Recompute the modelled fill and commit its complete financial transition."""
    utc(at)
    identifier(run_id)
    require(isinstance(quote_id, UUID), "Expected quote event UUID.")
    with _write(conn, pid) as (cur, p):
        o = _order(cur, pid, oid)
        snapshot = inspect_portfolio(cur, pid)
        portfolio = snapshot.account.portfolio
        result = _execution(cur, portfolio, o, quote_id, filters, at, run_id)
        order = result.order
        require(result.fill is not None, f"Fill ineligible ({result.reason}).")
        t = result.fill.trade
        receipt = _event(
            cur,
            pid,
            "FILL",
            str(oid),
            at,
            recorded_at,
            order=o,
            quote_event_id=quote_id,
            run_id=run_id,
            simulated_qty=t.quantity,
            simulated_price=t.price,
            gross_notional=t.notional,
            fee_usdt=t.fee,
            ledger_seq_before=t.ledger_seq_before,
            ledger_seq_after=t.ledger_seq_before + 2,
            policy_sha256=o["policy_sha256"],
            **records.filter_fields(filters),
        )
        if not receipt.created:
            return receipt
        require(
            snapshot.pending_order == o
            and snapshot.account.ledger_seq == t.ledger_seq_before,
            "Stale order or ledger snapshot.",
        )
        for seq, m in enumerate(t.postings, t.ledger_seq_before + 1):
            _put(
                cur,
                "paper_ledger_entry",
                "ledger_entry_id",
                records.identity(receipt.id, "posting", m.asset),
                dict(
                    portfolio_id=pid,
                    ledger_seq=seq,
                    entry_type="FILL",
                    fill_event_id=receipt.id,
                    asset=m.asset,
                    delta_units=m.amount,
                    posted_at=recorded_at,
                ),
            )
        cur.execute(
            "UPDATE paper_portfolio SET ledger_highwater=%s WHERE portfolio_id=%s",
            (t.ledger_seq_before + 2, pid),
        )
        cur.execute("UPDATE paper_order SET status='FILLED' WHERE order_id=%s", (oid,))
        if order.side == "SELL":
            require(
                snapshot.exit_decision_id == o["decision_id"],
                "Missing exit obligation.",
            )
            _event(
                cur,
                pid,
                "EXIT_SATISFIED",
                str(o["decision_id"]),
                at,
                recorded_at,
                order=o,
                reference_event_id=receipt.id,
                reason_code="holdings_zero",
            )
        inspect_portfolio(cur, pid)
        return receipt


def record_mark(conn, pid, slot, at, *, quote=None, reason=None, inception=False):
    utc(slot)
    utc(at)
    with _write(conn, pid) as (cur, p):
        return _mark(cur, pid, p, slot, at, quote, reason, inception)


def _mark(cur, pid, p, slot, at, quote, reason, inception):
    key = slot.isoformat()
    policy = p["valuation_policy_sha256"]
    if quote is None:
        require(reason and not inception, "Missing mark requires a reason.")
        return _event(
            cur,
            pid,
            "MARK_MISSING",
            key,
            at,
            at,
            reason_code=reason,
            mark_slot=slot,
            valuation_policy_sha256=policy,
        )
    require(reason is None, "Unexpected observed-mark reason.")
    validate_quote(quote, records.portfolio(p), at)
    # Retry a committed snapshot against its original prefix even after later fills.
    prior = cur.execute(
        "SELECT asof_ledger_seq FROM paper_market_event WHERE portfolio_id=%s "
        "AND mark_slot=%s "
        "AND valuation_policy_sha256=%s",
        (pid, slot, policy),
    ).fetchone()
    return _event(
        cur,
        pid,
        "MARK_OBSERVED",
        key,
        at,
        at,
        mark_slot=slot,
        valuation_policy_sha256=policy,
        reason_code="INCEPTION" if inception else None,
        asof_ledger_seq=prior["asof_ledger_seq"] if prior else p["ledger_highwater"],
        **records.quote_fields(quote),
    )


def record_operational_event(conn, pid, kind, key, at, reason):
    require(kind in ("RECOVERY_NOTE", "PAUSE", "RESUME"), "Unknown operational event.")
    with _write(conn, pid) as (cur, _):
        return _event(cur, pid, kind, key, at, at, reason_code=reason)

"""Independent read-only audit and as-of replay of durable economic evidence."""

from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from psycopg.pq import TransactionStatus
from psycopg.rows import dict_row

from backtest_badger import paper_records as records
from backtest_badger.paper_accounting import (
    Account,
    Mark,
    apply_trade,
    fund_account,
    value_account,
)
from backtest_badger.paper_execution import simulate_order
from backtest_badger.paper_types import D, Movement, require, validate_quote


@dataclass
class IntegrityIssue(ValueError):
    code: str
    evidence_id: UUID


def check(condition, code, key):
    if not condition:
        raise IntegrityIssue(code, key)


@contextmanager
def transaction(conn, *, readonly=False):
    require(
        conn.info.transaction_status == TransactionStatus.IDLE,
        "An idle connection is required.",
    )
    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        if readonly:
            cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        else:
            cur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
        configure_transaction(cur)
        yield cur


def configure_transaction(cur):
    """Use the revision 0002 session policy for one local transaction."""
    cur.execute("SET LOCAL search_path=pg_catalog,public,pg_temp")
    cur.execute("SET LOCAL timezone='UTC'")
    cur.execute("SET LOCAL lock_timeout='3s'")
    cur.execute("SET LOCAL statement_timeout='10s'")


@dataclass(frozen=True)
class Snapshot:
    state: str
    account: Account
    pending_order: dict | None
    pending_quotes: tuple[dict, ...]
    exit_decision_id: UUID | None
    marks: dict
    prefixes: dict
    missed_streak: int
    exit_satisfied_at: datetime | None


def inspect_portfolio(cur, pid):
    """Read the original evidence and rebuild every monetary pair and saved mark."""
    require(isinstance(pid, UUID), "Expected portfolio UUID.")
    r = cur.execute(
        "SELECT * FROM paper_portfolio WHERE portfolio_id=%s", (pid,)
    ).fetchone()
    require(r is not None, "Unknown portfolio.")
    p = records.portfolio(r)
    check(
        records.fingerprint(r["config_canonical"]) == p.config_sha256
        and r["config_canonical"] == records.canonical(r["strategy_config"])
        and r["strategy_config"]
        == records.configuration(
            p.symbol, p.model_recipe_sha256, r["strategy_config"].get("cohort")
        ),
        "configuration",
        pid,
    )
    market = cur.execute(
        "SELECT * FROM market WHERE market_id=%s", (r["market_id"],)
    ).fetchone()
    check(
        (
            market["symbol"],
            market["base_asset"],
            market["quote_asset"],
            market["venue"],
            market["market_type"],
        )
        == (p.symbol, p.base_asset, "USDT", p.venue, p.market_type),
        "market",
        pid,
    )
    decisions = {
        v["decision_id"]: v
        for v in cur.execute(
            "SELECT * FROM paper_decision WHERE portfolio_id=%s "
            "ORDER BY source_open_time,decided_at",
            (pid,),
        )
    }
    orders = {
        v["order_id"]: v
        for v in cur.execute("SELECT * FROM paper_order WHERE portfolio_id=%s", (pid,))
    }
    events = {
        v["event_id"]: v
        for v in cur.execute(
            "SELECT * FROM paper_market_event WHERE portfolio_id=%s", (pid,)
        )
    }
    ledger = cur.execute(
        "SELECT * FROM paper_ledger_entry WHERE portfolio_id=%s ORDER BY ledger_seq",
        (pid,),
    ).fetchall()
    account = Account(p)
    prefixes = {0: account}
    fills = sorted(
        (e for e in events.values() if e["event_type"] == "FILL"),
        key=lambda e: e["ledger_seq_before"],
    )
    check(
        len(ledger) == r["ledger_highwater"]
        and len(ledger) == (1 + 2 * len(fills) if ledger else 0),
        "ledger_length",
        pid,
    )
    if ledger:
        opening = ledger[0]
        check(
            (
                opening["entry_type"],
                opening["asset"],
                opening["delta_units"],
                opening["ledger_seq"],
                opening["fill_event_id"],
                opening["posted_at"],
            )
            == ("INITIAL_FUNDING", "USDT", 10000, 1, None, p.inception_at),
            "funding",
            pid,
        )
        account = fund_account(account, opening["posted_at"])
        prefixes[1] = account
    terminal = {}
    consumed = set()
    pending_exits = {
        d["decision_id"] for d in decisions.values() if d["is_exit_obligation"]
    }
    satisfied = {}
    for eid, e in events.items():
        typ = e["event_type"]
        if typ in ("QUOTE_OBSERVED", "MARK_OBSERVED"):
            try:
                validate_quote(records.quote(p, e), p, e["event_at"])
            except (ArithmeticError, ValueError) as exc:
                raise IntegrityIssue("quote_evidence", eid) from exc
        if typ in ("FILL", "ORDER_REJECTED", "ORDER_EXPIRED"):
            oid = e["order_id"]
            check(
                oid in orders
                and oid not in terminal
                and orders[oid]["decision_id"] == e["decision_id"],
                "terminal_identity",
                eid,
            )
            terminal[oid] = {
                "FILL": "FILLED",
                "ORDER_REJECTED": "REJECTED",
                "ORDER_EXPIRED": "EXPIRED",
            }[typ]
        if typ == "EXIT_SATISFIED":
            did = e["decision_id"]
            check(did in pending_exits and did not in satisfied, "exit_obligation", eid)
            satisfied[did] = e
    for o in orders.values():
        check(
            o["status"] == terminal.get(o["order_id"], "SUBMITTED"),
            "terminal_status",
            o["order_id"],
        )
    for e in fills:
        eid = e["event_id"]
        o = orders[e["order_id"]]
        d = decisions[o["decision_id"]]
        q = events.get(e["quote_event_id"])
        check(
            q
            and q["event_type"] == "QUOTE_OBSERVED"
            and q["order_id"] == o["order_id"]
            and q["event_id"] not in consumed
            and q["recorded_at"] <= e["event_at"],
            "fill_quote",
            eid,
        )
        consumed.add(q["event_id"])
        order = records.order(p, d, o)
        check(
            (order.balances.cash, order.balances.quantity, order.balances.ledger_seq)
            == (account.cash, account.quantity, account.ledger_seq)
            and e["policy_sha256"]
            == o["policy_sha256"]
            == r["execution_policy_sha256"],
            "order_snapshot",
            eid,
        )
        result = simulate_order(
            order,
            records.quote(p, q),
            records.filters(e),
            e["event_at"],
            run_id=e["run_id"],
        )
        check(result.fill is not None, "execution_eligibility", eid)
        t = result.fill.trade
        check(
            (
                t.quantity,
                t.price,
                t.notional,
                t.fee,
                t.ledger_seq_before,
                t.ledger_seq_before + 2,
            )
            == tuple(
                e[k]
                for k in (
                    "simulated_qty",
                    "simulated_price",
                    "gross_notional",
                    "fee_usdt",
                    "ledger_seq_before",
                    "ledger_seq_after",
                )
            ),
            "fill_economics",
            eid,
        )
        for n, movement in enumerate(t.postings, account.ledger_seq + 1):
            posting = ledger[n - 1]
            check(
                (
                    posting["entry_type"],
                    posting["fill_event_id"],
                    posting["ledger_seq"],
                    posting["posted_at"],
                    Movement(posting["asset"], posting["delta_units"]),
                )
                == ("FILL", eid, n, e["recorded_at"], movement),
                "posting",
                eid,
            )
        account = replace(apply_trade(account, t), at=e["recorded_at"])
        prefixes[account.ledger_seq] = account
        if o["side"] == "SELL":
            exit_event = satisfied.get(o["decision_id"])
            check(
                account.quantity == 0
                and exit_event
                and exit_event["reference_event_id"] == eid
                and exit_event["order_id"] == o["order_id"]
                and exit_event["event_at"] == t.at,
                "exit_satisfaction",
                eid,
            )
    check(
        all(
            v["reference_event_id"] in events
            and events[v["reference_event_id"]]["event_type"] == "FILL"
            and orders[v["order_id"]]["side"] == "SELL"
            for v in satisfied.values()
        ),
        "false_exit",
        pid,
    )
    pending_exits -= satisfied.keys()
    check(
        len(pending_exits) <= 1 and (not pending_exits or account.quantity > 0),
        "pending_exit",
        pid,
    )
    sums = {
        v["asset"]: v["balance"]
        for v in cur.execute(
            "SELECT asset,sum(delta_units) AS balance FROM paper_ledger_entry "
            "WHERE portfolio_id=%s GROUP BY asset",
            (pid,),
        )
    }
    check(
        (sums.get("USDT", D(0)), sums.get(p.base_asset, D(0)))
        == (account.cash, account.quantity),
        "balance_sum",
        pid,
    )
    marks = {}
    for eid, e in events.items():
        if e["event_type"] == "MARK_MISSING":
            marks[eid] = None
        elif e["event_type"] == "MARK_OBSERVED":
            seq = e["asof_ledger_seq"]
            check(
                seq in prefixes
                and e["valuation_policy_sha256"] == r["valuation_policy_sha256"],
                "mark_prefix",
                eid,
            )
            mark = Mark(
                p,
                str(eid),
                e["event_at"],
                seq,
                records.quote(p, e),
                e["valuation_policy_sha256"],
                slot=e["mark_slot"],
            )
            marks[eid] = value_account(prefixes[seq], mark)
            check(marks[eid].equity is not None, "invalid_observed_mark", eid)
    state_event = events.get(r["state_event_id"])
    expected_state = "DRAFT"
    if state_event:
        if state_event["event_type"] == "MARK_OBSERVED":
            check(
                state_event["reason_code"] == "INCEPTION"
                and state_event["asof_ledger_seq"] == 1,
                "inception_mark",
                pid,
            )
        expected_state = {
            "MARK_OBSERVED": "ACTIVE",
            "PAUSE": "PAUSED",
            "EXIT_BLOCKED_DUST": "PAUSED",
            "RESUME": "ACTIVE",
            "RECOVERY_NOTE": "CLOSED",
        }.get(state_event["event_type"])
    check(expected_state == r["state"], "state_projection", pid)
    for order in orders.values():
        prefix = prefixes.get(order["snapshot_seq"])
        check(
            prefix
            and (order["budget_cash_snapshot"], order["base_qty_snapshot"])
            == (prefix.cash, prefix.quantity),
            "intent_balance",
            order["order_id"],
        )
    active = [o for o in orders.values() if o["status"] == "SUBMITTED"]
    check(len(active) <= 1, "multiple_submitted", pid)
    return Snapshot(
        r["state"],
        account,
        next(iter(active), None),
        tuple(
            sorted(
                (
                    e
                    for e in events.values()
                    if active
                    and e["order_id"] == active[0]["order_id"]
                    and e["event_type"] in ("QUOTE_OBSERVED", "QUOTE_FAILED")
                ),
                key=lambda e: (e["event_at"], e["event_id"]),
            )
        ),
        next(iter(pending_exits), None),
        marks,
        prefixes,
        next(reversed(decisions.values()))["missed_streak"] if decisions else 0,
        max((e["event_at"] for e in satisfied.values()), default=None),
    )


def reconcile_portfolio(conn, pid):
    """Return a coherent recovery snapshot or raise an integrity incident."""
    with transaction(conn, readonly=True) as cur:
        try:
            return inspect_portfolio(cur, pid)
        except IntegrityIssue:
            raise
        except (KeyError, IndexError, ArithmeticError, ValueError, TypeError) as exc:
            raise IntegrityIssue("invalid_portfolio_evidence", pid) from exc


def asof_account(conn, pid, seq):
    prefixes = reconcile_portfolio(conn, pid).prefixes
    require(
        type(seq) is int and seq in prefixes,
        "Expected a complete committed ledger prefix.",
    )
    return prefixes[seq]

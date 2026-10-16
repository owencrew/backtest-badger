"""Synthetic Stage 4B.1 contracts only: no provider, artifacts, DB, or live clock."""

import json
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, Inexact, localcontext
from hashlib import sha256

import pytest

from backtest_badger.paper_accounting import (
    Account,
    Mark,
    apply_trade,
    calculate_trade,
    fee_for,
    fund_account,
    net_liquidation,
    reconcile,
    replay,
    value_account,
)
from backtest_badger.paper_execution import (
    Order,
    Reason,
    Status,
    affordable_quantity,
    simulate_order,
)
from backtest_badger.paper_strategy import (
    evaluate_strategy,
    miss_horizon,
    observe_forecast,
    record_result,
    start_strategy,
)
from backtest_badger.paper_types import (
    STEP,
    Action,
    Filters,
    Forecast,
    Movement,
    Portfolio,
    Quote,
    Side,
    money_context,
)

D = Decimal
T = datetime(2026, 10, 16, 12, tzinfo=UTC)
HASH = "a" * 64
US = timedelta(microseconds=1)


def portfolio(symbol="BTCUSDT", inception=T, key=None):
    return Portfolio(key or symbol, symbol, inception, HASH, HASH, HASH)


def quote(
    at,
    symbol="BTCUSDT",
    identity="quote",
    run="run",
    bid="100",
    ask="100",
    bid_qty="1000",
    ask_qty="1000",
    latency=timedelta(0),
):
    body = json.dumps(
        dict(symbol=symbol, bidPrice=bid, askPrice=ask, bidQty=bid_qty, askQty=ask_qty)
    ).encode()
    return Quote(
        identity,
        run,
        symbol,
        at,
        at + latency,
        D(bid),
        D(ask),
        D(bid_qty),
        D(ask_qty),
        sha256(body).hexdigest(),
        body,
        "https://example.invalid/synthetic-book-ticker",
    )


def filters(at, symbol="BTCUSDT", **changes):
    return replace(
        Filters(
            symbol, at, HASH, D("0.01"), D("0.01"), D("1000000"), D("1"), D("100000000")
        ),
        **changes,
    )


def mark(account, at, *, bid="100", **changes):
    return replace(
        Mark(
            account.portfolio,
            "mark",
            at,
            account.ledger_seq,
            quote(at, account.portfolio.symbol, bid=bid, ask=bid),
            HASH,
        ),
        **changes,
    )


def funded(p=None):
    p = p or portfolio()
    return fund_account(Account(p), p.inception_at)


def start(p=None):
    account = funded(p)
    return start_strategy(account, mark(account, account.at))


def forecast(state, value="0.1", *, issued=None, observed=None, **changes):
    opened = state.next_source_open
    issued = issued or opened + STEP + timedelta(minutes=2)
    return replace(
        Forecast(
            state.account.portfolio,
            opened.isoformat(),
            opened,
            issued,
            observed or issued,
            D(value),
            HASH,
            HASH,
            HASH,
            HASH,
        ),
        **changes,
    )


def observe(state, value="0.1", **kwargs):
    f = forecast(state, value, **kwargs)
    return observe_forecast(state, f, "decision-" + f.record_id, f.observed_at)


def order_for(state, decision, at=None, identity="order", run="run"):
    at = at or state.last_at
    return Order(
        identity, decision, state.account.balances, run, at, at + timedelta(seconds=30)
    )


def execute(state, decision, at=None, identity="order", **quote_kwargs):
    order = order_for(state, decision, at, identity)
    q = quote(
        order.submitted_at,
        state.account.portfolio.symbol,
        identity="quote-" + identity,
        **quote_kwargs,
    )
    result = simulate_order(
        order,
        q,
        filters(order.submitted_at, q.symbol),
        q.response_received_at,
        run_id="run",
        existing=state.attempts,
    )
    updated, transition = record_result(state, result, "result-" + identity)
    return updated, transition, result


def long_state():
    state, decision = observe(start())
    return execute(state, decision)[0]


def trade(account, identity, side, qty, price, at=None):
    return calculate_trade(
        account.portfolio,
        identity,
        side,
        at or account.at,
        D(qty),
        D(price),
        ledger_seq_before=account.ledger_seq,
    )


@pytest.mark.parametrize(
    "value,target",
    [("0", 0), ("-1", 0), ("1e-12", 0), ("1.0000000000000001e-12", 1), ("1", 1)],
)
def test_threshold(value, target):
    assert evaluate_strategy(D(value)) == target


@pytest.mark.parametrize(
    "value",
    [0.1, 0, True, "0.1", None, D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity")],
)
def test_invalid_predictions(value):
    with pytest.raises(ValueError):
        evaluate_strategy(value)
    with pytest.raises(ValueError):
        replace(forecast(start()), prediction=value)


def test_strategy_version_and_immutable_identity():
    with pytest.raises(ValueError, match="version"):
        evaluate_strategy(D(1), version="2")
    with pytest.raises(FrozenInstanceError):
        portfolio().symbol = "ETHUSDT"
    with pytest.raises(ValueError):
        portfolio("DOGEUSDT")


@pytest.mark.parametrize("hour", range(0, 24, 4))
@pytest.mark.parametrize(
    "offset,eligible", [(59, False), (60, True), (959.999999, True), (960, False)]
)
def test_six_native_boundaries(hour, offset, eligible):
    close = T.replace(hour=hour)
    state = start(portfolio(inception=close))
    at = close + timedelta(seconds=offset)
    f = forecast(state, issued=at)
    updated, decision = observe_forecast(state, f, "d", at)
    assert (decision.action == Action.BUY_REQUIRED) == eligible
    assert updated.missed_streak == 0


@pytest.mark.parametrize(
    "changes",
    [
        dict(automation_sha256=None),
        dict(cohort="timely_unattributed"),
        dict(cohort="secondary_late_manual"),
        dict(model_recipe_sha256="b" * 64),
    ],
)
def test_ineligible_provenance_cannot_buy_or_sell(changes):
    for state in (start(), long_state()):
        f = forecast(state, "-1", **changes)
        updated, decision = observe_forecast(state, f, "invalid", f.observed_at)
        assert decision.action == Action.SIGNAL_INELIGIBLE
        assert updated.exit_required is None
        assert updated.account == state.account
        assert updated.next_source_open == state.next_source_open


def test_continuous_positive_negative_and_cash():
    state = long_state()
    before = state.account
    state, hold = observe(state)
    assert hold.action == Action.HOLD and state.account == before
    with pytest.raises(ValueError, match="authorise"):
        order_for(state, hold)
    state, negative = observe(state, "-1")
    assert negative.action == Action.EXIT_REQUIRED
    assert state.exit_required == negative
    cash, noop = observe(start(), "-1")
    assert noop.action == Action.CASH_NOOP and cash.account.quantity == 0


def test_sticky_exit_survives_failed_expired_attempts_and_positive():
    state, negative = observe(long_state(), "-1")
    original = state.account
    order = order_for(state, negative, identity="failure")
    failed = simulate_order(order, None, None, state.last_at, run_id="run")
    state, _ = record_result(state, failed, "failed")
    assert state.account == original and state.exit_required == negative
    order = order_for(state, negative, identity="expired")
    expired = simulate_order(
        order, None, None, order.expires_at, run_id="run", existing=state.attempts
    )
    state, _ = record_result(state, expired, "expired-event")
    assert state.account == original and state.exit_required == negative
    state, ignored = observe(state)
    assert ignored.action == Action.IGNORED_EXIT_PENDING
    state, satisfied, result = execute(state, negative, identity="retry")
    assert result.status == Status.FILLED and state.account.quantity == 0
    assert satisfied.action == Action.EXIT_SATISFIED and state.exit_required is None
    state, new = observe(state)
    assert new.action == Action.BUY_REQUIRED


def test_reentry_requires_new_issuance_after_satisfaction():
    state, negative = observe(long_state(), "-1")
    next_time = state.next_source_open + STEP + timedelta(minutes=2)
    state, _, _ = execute(state, negative, next_time, "late-exit")
    f = forecast(state, issued=next_time - timedelta(seconds=1), observed=next_time)
    state, old = observe_forecast(state, f, "old-positive", next_time)
    assert old.action == Action.CASH_NOOP
    assert old.reason == "forecast_predates_exit_satisfaction"
    state, new = observe(state)
    assert new.action == Action.BUY_REQUIRED


def test_missing_horizons_discovered_after_downtime_at_actual_time():
    state = long_state()
    before = state.account
    discovered = state.next_source_open + STEP * 3 + timedelta(minutes=17)
    state, first = miss_horizon(state, state.next_source_open, "miss1", discovered)
    assert first.action == Action.SIGNAL_STALE and state.exit_required is None
    state, second = miss_horizon(state, state.next_source_open, "miss2", discovered)
    assert (
        second.action == Action.EXIT_REQUIRED
        and second.reason == "risk_exit_two_misses"
    )
    assert first.at == second.at == discovered
    assert state.account == before and state.missed_streak == 2
    state, third = miss_horizon(state, state.next_source_open, "miss3", discovered)
    assert state.exit_required == second and third.obligation_id == second.identity


def test_miss_strictly_after_deadline_and_eligible_reset():
    state = long_state()
    deadline = state.next_source_open + STEP + timedelta(minutes=16)
    for at in (deadline - US, deadline):
        with pytest.raises(ValueError, match="AFTER"):
            miss_horizon(state, state.next_source_open, "miss", at)
    state, _ = miss_horizon(state, state.next_source_open, "miss", deadline + US)
    state, hold = observe(state)
    assert state.missed_streak == 0 and hold.action == Action.HOLD
    state, _ = miss_horizon(
        state,
        state.next_source_open,
        "miss2",
        state.next_source_open + STEP + timedelta(minutes=17),
    )
    assert state.missed_streak == 1 and state.exit_required is None


def test_flat_misses_and_no_pre_inception_counting():
    state = start(portfolio(inception=T + timedelta(minutes=17)))
    assert state.next_source_open == T
    for i in range(2):
        state, decision = miss_horizon(
            state, state.next_source_open, f"miss{i}", T + STEP * 3
        )
        assert decision.action == Action.SIGNAL_MISSED
    assert state.exit_required is None


@pytest.mark.parametrize(
    "kind",
    [
        "duplicate_decision",
        "duplicate_horizon",
        "skip_horizon",
        "future_observation",
        "time_reversal",
        "market",
        "off_grid",
        "non_utc",
        "naive",
        "old_issuance",
    ],
)
def test_invalid_strategy_ordering(kind):
    state = start()
    f = forecast(state)
    at, identity = f.observed_at, "d"
    if kind == "duplicate_decision":
        state, _ = observe_forecast(state, f, identity, at)
        f = forecast(state)
        at = f.observed_at
    elif kind == "duplicate_horizon":
        state, _ = observe_forecast(state, f, identity, at)
        identity = "other"
    elif kind == "skip_horizon":
        f = replace(f, source_open=f.source_open + STEP)
    elif kind == "future_observation":
        at -= US
    elif kind == "time_reversal":
        at = T - US
    elif kind == "market":
        f = replace(f, portfolio=portfolio("ETHUSDT"))
    elif kind in ("off_grid", "non_utc", "naive"):
        opened = {
            "off_grid": T + US,
            "non_utc": T.astimezone(timezone(timedelta(hours=2))),
            "naive": T.replace(tzinfo=None),
        }[kind]
        with pytest.raises(ValueError):
            replace(f, source_open=opened)
        return
    else:
        state = start(portfolio(inception=T + timedelta(minutes=3)))
        f = forecast(
            state, issued=T + timedelta(minutes=2), observed=T + timedelta(minutes=4)
        )
        state, decision = observe_forecast(state, f, "d", f.observed_at)
        assert decision.action == Action.SIGNAL_INELIGIBLE
        return
    with pytest.raises(ValueError):
        observe_forecast(state, f, identity, at)


@pytest.fixture
def buy_order():
    state, decision = observe(start())
    return order_for(state, decision)


def simulate_buy(order, q=None, f=None, at=None, **kwargs):
    at = at or order.submitted_at
    return simulate_order(
        order,
        q or quote(at),
        f or filters(order.submitted_at),
        at,
        run_id=kwargs.pop("run_id", "run"),
        **kwargs,
    )


@pytest.mark.parametrize(
    "request_offset,receipt,fill,status",
    [
        (-1, 0, 0, Status.REJECTED),
        (0, -1, 0, Status.REJECTED),
        (0, 1, 0, Status.REJECTED),
        (0, 2, 3, Status.FILLED),
        (0, 2.000001, 3, Status.REJECTED),
        (0, 2, 3.000001, Status.REJECTED),
        (29, 29.5, 29.999999, Status.FILLED),
        (29, 29.5, 30, Status.EXPIRED),
    ],
)
def test_quote_temporal_edges(buy_order, request_offset, receipt, fill, status):
    at = buy_order.submitted_at
    q = replace(
        quote(at + timedelta(seconds=request_offset)),
        response_received_at=at + timedelta(seconds=receipt),
    )
    result = simulate_buy(buy_order, q=q, at=at + timedelta(seconds=fill))
    assert result.status == status
    assert len(result.postings) == (2 if status == Status.FILLED else 0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("bid", D(0)),
        ("bid", D(-1)),
        ("ask", D("99")),
        ("bid", D("NaN")),
        ("ask", 100.0),
        ("ask_quantity", D(-1)),
        ("bid_quantity", D("Infinity")),
        ("symbol", "ETHUSDT"),
        ("venue", "other"),
        ("market_type", "futures"),
        ("http_status", 500),
        ("payload_validated", False),
        ("run_id", "previous-run"),
        ("payload_sha256", "b" * 64),
        ("raw_body", b"{}"),
        ("raw_body", b"x" * 4097),
        ("request_started_at", T.replace(tzinfo=None)),
        ("response_received_at", T.astimezone(timezone(timedelta(hours=2)))),
        ("elapsed_seconds", D("2.000001")),
        ("elapsed_seconds", D("-1")),
    ],
)
def test_bad_quotes_have_zero_postings(buy_order, field, value):
    q = replace(quote(buy_order.submitted_at), **{field: value})
    result = simulate_buy(buy_order, q=q)
    assert result.status == Status.REJECTED and result.postings == ()


@pytest.mark.parametrize(
    "body",
    [b"{", b"[]", b"null", b"123", b"\xff", b'{"symbol":"BTCUSDT","symbol":"BTCUSDT"}'],
)
def test_malformed_quote_payload(buy_order, body):
    q = replace(
        quote(buy_order.submitted_at),
        raw_body=body,
        payload_sha256=sha256(body).hexdigest(),
    )
    assert simulate_buy(buy_order, q=q).reason == Reason.INVALID_QUOTE


def test_buy_signal_deadline_and_clock_boundaries():
    state = start()
    at = T + timedelta(minutes=16) - US
    state, decision = observe(state, issued=at)
    order = order_for(state, decision)
    assert simulate_buy(order).status == Status.FILLED
    assert simulate_buy(order, at=at + US).reason == Reason.SIGNAL_EXPIRED
    with pytest.raises(ValueError):
        replace(order, submitted_at=at + US, expires_at=at + US + timedelta(seconds=30))
    with pytest.raises(ValueError):
        replace(order, expires_at=order.expires_at + US)
    with pytest.raises(ValueError):
        simulate_buy(order, at=at - US)


@pytest.mark.parametrize(
    "changes",
    [
        dict(step=D(0)),
        dict(step=0.1),
        dict(min_quantity=D("1000")),
        dict(max_quantity=D("1")),
        dict(min_notional=D("20000")),
        dict(max_notional=D("100")),
        dict(min_quantity=D(-1)),
        dict(max_notional=D("0.1")),
        dict(version="unknown"),
        dict(supported=False),
        dict(symbol="ETHUSDT"),
        dict(payload_sha256="invalid"),
        dict(observed_at=T + timedelta(hours=1)),
    ],
)
def test_filter_rejections(buy_order, changes):
    f = filters(buy_order.submitted_at, **changes)
    result = simulate_buy(buy_order, f=f)
    assert result.status == Status.REJECTED and result.postings == ()


@pytest.mark.parametrize("age,success", [(3600, True), (3600.000001, False)])
def test_filter_age_limit_at_fill(buy_order, age, success):
    f = filters(buy_order.submitted_at - timedelta(seconds=age))
    assert (simulate_buy(buy_order, f=f).status == Status.FILLED) == success


def test_filters_must_precede_order_even_if_fresh(buy_order):
    at = buy_order.submitted_at + timedelta(seconds=1)
    assert (
        simulate_buy(buy_order, at=at, f=filters(at)).reason == Reason.INVALID_FILTERS
    )


def test_full_affordable_buy_spread_slip_fee_and_depth(buy_order):
    q = quote(buy_order.submitted_at, bid="99", ask="101", bid_qty="0", ask_qty="100")
    result = simulate_buy(buy_order, q=q)
    t = result.fill.trade
    assert t.price == D("101.0202")
    assert t.quantity == D("98.89")
    assert t.notional == D("9989.887578") and t.fee == D("9.98988758")
    assert t.postings == (
        Movement("USDT", D("-9999.87746558")),
        Movement("BTC", D("98.89")),
    )
    with localcontext(money_context()):
        assert buy_order.balances.cash + t.postings[0].amount >= 0
        next_n = (t.quantity + D(".01")) * t.price
        assert next_n + fee_for(next_n) > buy_order.balances.cash
    q = quote(
        buy_order.submitted_at, bid="99", ask="101", bid_qty="1000000", ask_qty="98.88"
    )
    rejected = simulate_buy(buy_order, q=q)
    assert rejected.reason == Reason.INSUFFICIENT_LIQUIDITY and rejected.postings == ()


def test_fee_ceiling_affordability_and_non_power_ten_steps():
    assert fee_for(D("1.000000001")) == D("0.00100001")
    # Unrounded fee fits exactly; rounded fee makes one whole unit unaffordable.
    cash, price = D("1.001000001001"), D("1.000000001")
    assert affordable_quantity(cash, price, D(1)) == 0
    assert affordable_quantity(D("10"), D("3"), D(".03")) == D("3.33")
    # Tiny steps must not cause millions of linear fee-correction iterations.
    q = affordable_quantity(cash, price, D("1e-24"))
    with localcontext(money_context()):
        assert q * price + fee_for(q * price) <= cash
        q += D("1e-24")
        assert q * price + fee_for(q * price) > cash


def test_sell_uses_bid_and_exact_owned_quantity_and_dust():
    state, exit_decision = observe(long_state(), "-1")
    order = order_for(state, exit_decision, identity="sell-order")
    q = quote(order.submitted_at, bid="110", ask="111", bid_qty="1000", ask_qty="0")
    result = simulate_order(
        order, q, filters(order.submitted_at), order.submitted_at, run_id="run"
    )
    assert result.fill.trade.price == D("109.978")
    assert result.fill.trade.quantity == state.account.quantity
    f = filters(order.submitted_at, step=D("1"))
    blocked = simulate_order(order, q, f, order.submitted_at, run_id="run")
    assert blocked.reason == Reason.EXIT_BLOCKED_DUST and not blocked.postings
    updated, _ = record_result(state, blocked, "blocked")
    assert updated.exit_required == exit_decision and updated.account == state.account
    q = quote(order.submitted_at, bid_qty="0", ask_qty="100000")
    assert simulate_order(order, q, f, order.submitted_at, run_id="run").postings == ()


def test_duplicate_execution_requires_explicit_context(buy_order):
    result = simulate_buy(buy_order)
    assert result == simulate_buy(buy_order)
    with pytest.raises(ValueError, match="already processed"):
        simulate_buy(buy_order, existing=(result,))
    with pytest.raises(ValueError, match="already attempted"):
        simulate_buy(replace(buy_order, identity="new-order"), existing=(result,))
    other = replace(
        buy_order,
        identity="other-order",
        decision=replace(buy_order.decision, identity="other-decision"),
    )
    with pytest.raises(ValueError, match="Quote already"):
        simulate_buy(other, existing=(result,))
    assert simulate_buy(other, run_id="restarted").reason == Reason.INVALID_QUOTE


def test_failed_buy_waits_for_new_forecast():
    state, decision = observe(start())
    order = order_for(state, decision)
    result = simulate_order(order, None, None, order.submitted_at, run_id="run")
    state, _ = record_result(state, result, "failed")
    with pytest.raises(ValueError, match="already attempted"):
        simulate_order(
            replace(order, identity="retry"),
            None,
            None,
            result.at,
            run_id="run",
            existing=state.attempts,
        )
    state, new = observe(state)
    assert new.action == Action.BUY_REQUIRED


def test_hand_calculated_spec_example():
    initial = funded()
    buy = trade(initial, "buy", Side.BUY, "10", "100.02", T + timedelta(minutes=2))
    bought = apply_trade(initial, buy)
    assert buy.fee == D("1.00020000")
    assert bought.cash == D("8998.7998") and bought.basis == D("1001.2002")
    assert bought.basis / bought.quantity == D("100.12002")
    sell = trade(bought, "sell", Side.SELL, "4", "109.978", T + STEP)
    sold = apply_trade(bought, sell)
    assert sell.fee == D("0.43991200") and sell.postings[0].amount == D("439.472088")
    assert bought.basis - sold.basis == D("400.48008")
    assert sold.realised == D("38.992008") and sold.cash == D("9438.271888")
    valuation = value_account(sold, mark(sold, sold.at, bid="110"))
    assert valuation.unrealised == D("59.27988")
    assert valuation.equity == D("10098.271888")
    assert valuation.realised + valuation.unrealised == valuation.equity - D(10000)


def test_multiple_buys_partial_and_full_sale_weighted_basis():
    account = funded()
    fills = []
    for identity, side, qty, price in [
        ("a", Side.BUY, "1", "100"),
        ("b", Side.BUY, "2", "200"),
        ("c", Side.SELL, "1", "180"),
        ("d", Side.SELL, "2", "180"),
    ]:
        t = trade(account, identity, side, qty, price)
        fills.append(t)
        account = apply_trade(account, t)
        reconcile(account)
        assert len(t.postings) == 2
        with localcontext(money_context()):
            assert t.postings[0].amount + t.postings[1].amount * t.price == -t.fee
    assert account.quantity == account.basis == 0
    assert account.cash == D("10038.96") and account.realised == D("38.96")
    assert account.fees == D("1.04")
    assert replay(account.portfolio, fills) == account
    assert replay(account.portfolio, fills) == replay(account.portfolio, fills)


def test_nonterminating_basis_allocation_conserves_and_full_exit():
    a = funded()
    a = apply_trade(a, trade(a, "a", Side.BUY, "3", "1"))
    a = apply_trade(a, trade(a, "b", Side.BUY, "4", "2"))
    for i in range(7):
        a = apply_trade(a, trade(a, f"s{i}", Side.SELL, "1", "2"))
        reconcile(a)
        v = value_account(a, mark(a, a.at, bid="2"))
        with localcontext(money_context()):
            assert v.realised + v.unrealised == v.equity - D(10000)
    assert a.basis == a.quantity == 0 and a.realised == D("2.975")


def test_flat_execution_price_fee_only_loss_and_prospective_slip_loss():
    a = funded()
    a = apply_trade(a, trade(a, "a", Side.BUY, "10", "100"))
    a = apply_trade(a, trade(a, "b", Side.SELL, "10", "100"))
    assert a.realised == D("-2") and a.fees == D("2")
    state, decision = observe(long_state(), "-1")
    state, _, _ = execute(state, decision, identity="sell")
    assert state.account.cash < D(10000) - state.account.fees


@pytest.mark.parametrize(
    "kind",
    [
        "duplicate",
        "reorder",
        "cash",
        "base",
        "market",
        "one_posting",
        "sign",
        "fee",
        "basis",
        "funding",
    ],
)
def test_account_invariant_failures(kind):
    a = funded()
    b = trade(a, "buy", Side.BUY, "10", "100", T + timedelta(minutes=2))
    bought = apply_trade(a, b)
    with pytest.raises(ValueError):
        if kind == "duplicate":
            apply_trade(bought, b)
        elif kind == "reorder":
            apply_trade(bought, replace(b, identity="other", at=T))
        elif kind == "cash":
            apply_trade(a, trade(a, "large", Side.BUY, "101", "100"))
        elif kind == "base":
            apply_trade(bought, trade(bought, "large", Side.SELL, "11", "100"))
        elif kind == "market":
            apply_trade(funded(portfolio("ETHUSDT")), b)
        elif kind == "one_posting":
            apply_trade(a, replace(b, postings=b.postings[:1]))
        elif kind == "sign":
            apply_trade(a, replace(b, postings=(Movement("USDT", D(1)), b.postings[1])))
        elif kind == "fee":
            apply_trade(a, replace(b, fee=D(0)))
        elif kind == "basis":
            reconcile(replace(bought, basis=D(0)))
        else:
            fund_account(a, T)


def test_exact_context_independent_of_callers_precision():
    with localcontext() as context:
        context.prec = 6
        a = funded()
        b = trade(a, "buy", Side.BUY, "10.1234567890123456789012345", "100.02")
        result = apply_trade(a, b)
    assert result == replay(a.portfolio, [b])
    with pytest.raises((ValueError, Inexact)):
        calculate_trade(
            a.portfolio,
            "huge",
            Side.BUY,
            T,
            D("9" * 150),
            D("9" * 150),
            ledger_seq_before=a.ledger_seq,
        )


def test_mark_ledger_prefix_survives_later_trades_and_net_liquidation():
    a = funded()
    buy = trade(a, "b", Side.BUY, "10", "100.02", T + timedelta(minutes=2))
    prefix = apply_trade(a, buy)
    m = mark(
        prefix, T + timedelta(minutes=10), bid="110", slot=T + timedelta(minutes=10)
    )
    original = value_account(prefix, m)
    later = trade(prefix, "s", Side.SELL, "4", "109.978", T + STEP)
    current = apply_trade(prefix, later)
    with pytest.raises(ValueError, match="prefix"):
        value_account(current, m)
    assert original == value_account(replay(a.portfolio, (buy,)), m)
    assert net_liquidation(prefix, m, filters(m.marked_at)) == D("10097.48002")
    assert original.equity == D("10098.7998")
    assert (
        net_liquidation(prefix, m, filters(m.marked_at, min_quantity=D("11"))) is None
    )
    assert (
        net_liquidation(
            prefix,
            replace(m, quote=quote(m.marked_at, bid_qty="0")),
            filters(m.marked_at),
        )
        is None
    )
    assert net_liquidation(a, mark(a, T), None) == D(10000)


@pytest.mark.parametrize("kind", ["missing", "invalid", "stale", "late_slot"])
def test_missing_invalid_marks_stay_unavailable(kind):
    a = funded()
    m = mark(a, T + timedelta(minutes=10), slot=T + timedelta(minutes=10))
    if kind == "missing":
        m = replace(m, quote=None)
    elif kind == "invalid":
        m = replace(m, quote=replace(m.quote, bid=D(-1)))
    elif kind == "stale":
        m = replace(m, marked_at=m.marked_at + timedelta(seconds=2))
    else:
        m = replace(m, marked_at=m.marked_at + timedelta(minutes=5))
    v = value_account(a, m)
    assert v.equity is None and v.unrealised is None and v.unavailable_reason
    assert net_liquidation(a, m, filters(m.marked_at)) is None


def test_deterministic_transition_sequence_and_account_isolation():
    def run(symbol):
        state = start(portfolio(symbol))
        state, d = observe(state)
        state, _, _ = execute(state, d)
        state, _ = observe(state)
        state, d = observe(state, "-1")
        state, _, _ = execute(state, d, identity="sell")
        return state

    first, second = run("BTCUSDT"), run("BTCUSDT")
    assert first == second and asdict(first) == asdict(second)
    eth = run("ETHUSDT")
    assert eth.account.cash == first.account.cash
    assert eth.account.portfolio != first.account.portfolio
    with pytest.raises(ValueError, match="mismatch"):
        apply_trade(eth.account, first.attempts[0].fill.trade)
    with pytest.raises(ValueError):
        replay(
            first.account.portfolio, [r.fill.trade for r in reversed(first.attempts)]
        )
    with pytest.raises(ValueError):
        record_result(first, first.attempts[-1], "repeat")


def test_illegal_state_jumps_and_fabricated_execution():
    state, d = observe(start())
    result = simulate_buy(order_for(state, d))
    with pytest.raises(ValueError, match="Altered"):
        record_result(state, replace(result, status=Status.REJECTED), "bad")
    with pytest.raises(ValueError, match="Unknown decision"):
        record_result(start(), result, "unknown")
    with pytest.raises(ValueError):
        observe_forecast(
            replace(state, exit_required=d),
            forecast(state),
            "bad",
            T + STEP + timedelta(minutes=2),
        )
    with pytest.raises(ValueError):
        start_strategy(funded(), replace(mark(funded(), T), quote=None))


@pytest.mark.parametrize("prediction,target", [("1e-999", 0), ("1e999", 1)])
def test_finite_prediction_comparison_has_no_monetary_precision_limit(
    prediction, target
):
    assert evaluate_strategy(D(prediction)) == target


def test_zero_cash_rejection_and_no_cross_account_snapshot(buy_order):
    order = replace(buy_order, balances=replace(buy_order.balances, cash=D(0)))
    result = simulate_buy(order)
    assert result.reason == Reason.INSUFFICIENT_CASH and result.postings == ()
    with pytest.raises(ValueError, match="mismatch"):
        replace(buy_order, balances=funded(portfolio("ETHUSDT")).balances)
    with pytest.raises(ValueError):
        replace(buy_order.balances, cash=D(-1))
    with pytest.raises(ValueError):
        replace(buy_order.balances, quantity=D(-1))


def test_filter_exact_bounds_and_no_admissible_step(buy_order):
    filled = simulate_buy(buy_order).fill.trade
    f = filters(
        buy_order.submitted_at,
        min_quantity=filled.quantity,
        max_quantity=filled.quantity,
        min_notional=filled.notional,
        max_notional=filled.notional,
    )
    assert simulate_buy(buy_order, f=f).status == Status.FILLED
    f = filters(buy_order.submitted_at, step=D(3), min_quantity=D(4), max_quantity=D(5))
    assert simulate_buy(buy_order, f=f).reason == Reason.INVALID_FILTERS


def test_sell_depth_never_uses_ask_quantity():
    state, exit_decision = observe(long_state(), "-1")
    order = order_for(state, exit_decision, identity="sell")
    q = quote(order.submitted_at, bid_qty="0", ask_qty="100000")
    result = simulate_order(
        order, q, filters(order.submitted_at), order.submitted_at, run_id="run"
    )
    assert result.reason == Reason.INSUFFICIENT_LIQUIDITY and not result.postings


def test_invalid_posting_numeric_types_cannot_compare_equal_to_decimal():
    a = funded()
    t = trade(a, "b", Side.BUY, "1", "100")
    for altered in (
        replace(t, fee=0.1),
        replace(t, notional=100.0),
        replace(t, postings=(t.postings[0], Movement("BTC", 1.0))),
    ):
        with pytest.raises(ValueError, match="Decimal"):
            apply_trade(a, altered)


def test_failed_quote_identity_cannot_be_reused(buy_order):
    q = quote(buy_order.submitted_at, ask_qty="0")
    rejected = simulate_buy(buy_order, q=q)
    other = replace(
        buy_order,
        identity="other",
        decision=replace(buy_order.decision, identity="new-decision"),
    )
    with pytest.raises(ValueError, match="Quote already"):
        simulate_buy(other, q=q, existing=(rejected,))


def test_reordered_misses_and_ineligible_at_deadline_do_not_reset_streak():
    state = long_state()
    opened = state.next_source_open
    deadline = opened + STEP + timedelta(minutes=16)
    f = forecast(state, issued=deadline)
    state, invalid = observe_forecast(state, f, "invalid", deadline)
    assert invalid.action == Action.SIGNAL_INELIGIBLE and state.missed_streak == 0
    state, _ = miss_horizon(state, opened, "missed", deadline + US)
    with pytest.raises(ValueError):
        miss_horizon(state, opened, "again", deadline + US)
    with pytest.raises(ValueError):
        miss_horizon(state, state.next_source_open + STEP, "skip", deadline + STEP * 3)
    state, valid = observe(state)
    assert valid.action == Action.HOLD and state.missed_streak == 0


def test_exact_satisfaction_timestamp_does_not_qualify_for_reentry():
    state, negative = observe(long_state(), "-1")
    now = state.next_source_open + STEP + timedelta(minutes=2)
    state, _, _ = execute(state, negative, now, "satisfy")
    state, decision = observe(state, issued=now)
    assert decision.action == Action.CASH_NOOP


def test_mark_wrong_identity_policy_time_and_sequence_fail_closed():
    a = funded()
    good = mark(a, T)
    for bad in (
        replace(good, portfolio=portfolio("ETHUSDT")),
        replace(good, marked_at=T - US),
        replace(good, asof_ledger_seq=3),
        replace(good, asof_ledger_seq=True),
        replace(good, policy="unknown"),
        replace(good, policy_sha256="invalid"),
        replace(good, slot=T + timedelta(minutes=11)),
    ):
        with pytest.raises(ValueError):
            value_account(a, bad)


def test_no_activation_on_earlier_or_missing_mark():
    a = funded()
    with pytest.raises(ValueError):
        start_strategy(a, replace(mark(a, T), marked_at=T - US))
    with pytest.raises(ValueError):
        start_strategy(a, None)


def test_independent_account_event_interleavings_preserve_results():
    btc, eth = funded(), funded(portfolio("ETHUSDT"))
    b = trade(btc, "b", Side.BUY, "2", "100.02")
    e = trade(eth, "e", Side.BUY, "3", "100.02")

    def run(events):
        accounts = {"BTCUSDT": btc, "ETHUSDT": eth}
        for event in events:
            symbol = event.portfolio.symbol
            accounts[symbol] = apply_trade(accounts[symbol], event)
        return accounts

    assert run((b, e)) == run((e, b))


def test_same_timestamp_trade_reordering_rejected_by_prefix():
    a = funded()
    first = trade(a, "first", Side.BUY, "1", "100")
    b = apply_trade(a, first)
    second = trade(b, "second", Side.BUY, "1", "100")
    with pytest.raises(ValueError, match="prefix"):
        replay(a.portfolio, (second, first))


def test_json_array_cannot_masquerade_as_quote_object(buy_order):
    q = quote(buy_order.submitted_at)
    body = json.dumps(list(json.loads(q.raw_body).items())).encode()
    q = replace(q, raw_body=body, payload_sha256=sha256(body).hexdigest())
    assert simulate_buy(buy_order, q=q).reason == Reason.INVALID_QUOTE


def test_quote_decimal_notation_is_exact_not_binary_float(buy_order):
    q = quote(buy_order.submitted_at, bid="1e2", ask="1e2")
    assert simulate_buy(buy_order, q=q).status == Status.FILLED
    for value in (100.0, "not-a-price", "NaN"):
        payload = json.loads(q.raw_body)
        payload["askPrice"] = value
        body = json.dumps(payload).encode()
        bad = replace(q, raw_body=body, payload_sha256=sha256(body).hexdigest())
        assert simulate_buy(buy_order, q=bad).reason == Reason.INVALID_QUOTE


@pytest.mark.parametrize("transaction", ["buy", "partial_sell", "full_sell"])
@pytest.mark.parametrize("receipt_offset", [-US, timedelta(0), US])
def test_valuation_receipt_cannot_predate_pinned_transaction(
    transaction, receipt_offset
):
    initial = funded()
    buy = trade(initial, "buy", Side.BUY, "10", "100", T + timedelta(seconds=10))
    trades = (buy,)
    account = replay(initial.portfolio, trades)
    if transaction != "buy":
        sale = trade(
            account,
            "sell",
            Side.SELL,
            "4" if transaction == "partial_sell" else "10",
            "110",
            account.at + timedelta(seconds=10),
        )
        trades += (sale,)
        account = replay(initial.portfolio, trades)
    receipt = account.at + receipt_offset
    m = mark(account, account.at + US, quote=quote(receipt, bid="110", ask="110"))
    valuation = value_account(account, m)
    assert valuation == value_account(replay(initial.portfolio, trades), m)
    assert valuation.mark == m
    assert valuation.realised == account.realised and valuation.fees == account.fees
    if receipt_offset < timedelta(0):
        assert valuation.equity is None and valuation.unrealised is None
        assert (
            valuation.unavailable_reason
            == "Quote observed before pinned ledger transaction."
        )
        assert net_liquidation(account, m, filters(receipt)) is None
    else:
        assert valuation.unavailable_reason is None
        assert valuation.equity == account.cash + account.quantity * D(110)
        assert valuation.realised + valuation.unrealised == valuation.equity - D(10000)


@pytest.mark.parametrize("hour", range(0, 24, 4))
@pytest.mark.parametrize(
    "request_offset,mark_offset,available",
    [
        (-US, timedelta(0), False),
        (timedelta(0), timedelta(0), True),
        (timedelta(minutes=5) - US, timedelta(minutes=5) - US, True),
        (timedelta(minutes=5) - US, timedelta(minutes=5), False),
        (timedelta(minutes=5), timedelta(minutes=5), False),
    ],
)
def test_scheduled_valuation_capture_boundaries(
    hour, request_offset, mark_offset, available
):
    slot = T.replace(hour=hour, minute=10)
    account = funded(portfolio(inception=slot - timedelta(minutes=10)))
    request = slot + request_offset
    at = slot + mark_offset
    # Receipt is inside the slot for the pre-window request regression.
    q = quote(request, latency=at - request)
    m = mark(account, at, quote=q, slot=slot)
    valuation = value_account(account, m)
    assert (valuation.equity == D(10000)) == available
    assert valuation.mark == m
    if not available:
        assert valuation.unrealised is None
        assert valuation.unavailable_reason == "Outside mark capture window."
        assert net_liquidation(account, m, None) is None


@pytest.mark.parametrize(
    "latency,processing,available",
    [
        (timedelta(seconds=2), timedelta(seconds=1), True),
        (timedelta(seconds=2) + US, timedelta(0), False),
        (timedelta(0), timedelta(seconds=1) + US, False),
    ],
)
def test_scheduled_valuation_still_requires_fresh_quotes(
    latency, processing, available
):
    account = funded()
    slot = T + timedelta(minutes=10)
    q = quote(slot, latency=latency)
    m = mark(account, q.response_received_at + processing, quote=q, slot=slot)
    valuation = value_account(account, m)
    assert (valuation.equity == D(10000)) == available
    if not available:
        assert valuation.unavailable_reason == "Stale quote."


@pytest.mark.parametrize("request_offset", [-US, timedelta(0), US])
def test_inception_request_boundary_and_actual_observation_time(request_offset):
    account = funded()
    q = quote(T + request_offset, latency=timedelta(seconds=1))
    m = mark(account, q.response_received_at, quote=q)
    valuation = value_account(account, m)
    if request_offset < timedelta(0):
        assert valuation.equity is None and valuation.unrealised is None
        assert (
            valuation.unavailable_reason == "Quote request before portfolio inception."
        )
        with pytest.raises(ValueError, match="Valid inception mark"):
            start_strategy(account, m)
    else:
        assert valuation.equity == D(10000)
        state = start_strategy(account, m)
        assert state.account == account
        assert state.last_at == m.marked_at > T
        assert state.next_source_open == start().next_source_open
        with pytest.raises(ValueError, match="clock reversal"):
            observe_forecast(state, forecast(state, issued=T + US), "early", T + US)
        state, decision = observe(state)
        assert decision.action == Action.BUY_REQUIRED
        assert execute(state, decision)[2].status == Status.FILLED

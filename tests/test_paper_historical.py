"""Fabricated in-memory 2024 evidence only; no artifact loaders or services."""

import json
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import timedelta, timezone
from decimal import ROUND_DOWN, Decimal, Inexact, localcontext

import pytest

from backtest_badger import paper_historical as historical
from backtest_badger.paper_accounting import (
    Account,
    apply_trade,
    calculate_trade,
    fee_for,
    fund_account,
    reconcile,
    replay,
)
from backtest_badger.paper_execution import affordable_quantity
from backtest_badger.paper_historical import (
    BASE_CONFIG,
    END,
    HOUR,
    LAST_SOURCE,
    START,
    HistoricalConfig,
    HistoricalForecast,
    HourlyReference,
    SyntheticMiss,
    historical_json,
    next_reference_at,
    replay_historical,
    value_historical,
)
from backtest_badger.paper_strategy import evaluate_strategy
from backtest_badger.paper_types import STEP, Action, Side, money_context

D = Decimal
HASH = "a" * 64  # Explicit fabricated fixture identity, never source authentication.
SOURCE_HASH = "b" * 64
US = timedelta(microseconds=1)


def forecast(index=0, value="1", symbol="BTCUSDT"):
    opened = START - STEP + index * STEP
    return HistoricalForecast(
        symbol,
        f"synthetic-ridge:{symbol}:{index}",
        opened,
        opened + STEP + timedelta(seconds=60),
        D(value),
        HASH,
    )


def reference(hour=0, price="100", symbol="BTCUSDT"):
    return HourlyReference(
        symbol,
        f"synthetic-open:{symbol}:{hour}",
        START + hour * HOUR,
        D(price),
        HASH,
        SOURCE_HASH,
    )


def miss(index, discovered=None):
    f = forecast(index)
    return SyntheticMiss(
        f.symbol,
        f.source_open,
        discovered or f.source_open + STEP + timedelta(minutes=17),
        "deliberately absent synthetic horizon",
    )


def run(
    values=("1",),
    *,
    symbol="BTCUSDT",
    hours=None,
    refs=None,
    forecasts=None,
    misses=(),
    config=BASE_CONFIG,
):
    hours = hours or len(values) * 4
    return replay_historical(
        symbol,
        tuple(forecast(i, v, symbol) for i, v in enumerate(values))
        if forecasts is None
        else forecasts,
        tuple(reference(i, symbol=symbol) for i in range(hours))
        if refs is None
        else refs,
        protocol_sha256=HASH,
        model_recipe_sha256=SOURCE_HASH,
        end_exclusive=START + hours * HOUR,
        synthetic_misses=misses,
        config=config,
    )


@pytest.mark.parametrize(
    "value,target",
    [
        ("-1", 0),
        ("0", 0),
        ("0.999999999e-12", 0),
        ("1e-12", 0),
        ("1.000000000000001e-12", 1),
        ("1", 1),
    ],
)
def test_strict_shared_ridge_threshold(value, target):
    result = run((value,))
    assert result.decisions[0].target == evaluate_strategy(D(value)) == target
    assert len(result.fills) == target


@pytest.mark.parametrize(
    "value",
    [None, "1", 1, 0.1, True, D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity")],
)
def test_invalid_forecast_numerics(value):
    with pytest.raises(ValueError):
        replace(forecast(), prediction=value)


@pytest.mark.parametrize(
    "opened",
    [
        START - STEP,
        START,
        START + 8 * HOUR,
        START + 20 * HOUR,
        START.replace(month=2) - STEP,
        START.replace(month=3) - STEP,
        START.replace(month=12, day=31, hour=12),
    ],
)
def test_native_grid_availability_and_next_hour_across_boundaries(opened):
    available = opened + STEP + timedelta(seconds=60)
    f = replace(forecast(), source_open=opened, feature_available_at=available)
    assert next_reference_at(f.feature_available_at) == opened + STEP + HOUR
    assert next_reference_at(f.feature_available_at) > available
    assert next_reference_at(available.replace(minute=0)) == opened + STEP + HOUR


@pytest.mark.parametrize(
    "changes",
    [
        {"source_open": START + HOUR},
        {"source_open": START + US},
        {"source_open": START.replace(tzinfo=None)},
        {"source_open": START.astimezone(timezone(timedelta(hours=2)))},
        {"feature_available_at": START + timedelta(seconds=59)},
        {"feature_available_at": START + timedelta(seconds=61)},
        {"feature_available_at": END},
        {"model": "zero"},
        {"venue": "other"},
        {"market_type": "futures"},
        {"symbol": "DOGEUSDT"},
        {"file_sha256": "bad"},
        {"record_id": ""},
    ],
)
def test_invalid_forecast_identity_timing(changes):
    with pytest.raises(ValueError):
        replace(forecast(), **changes)


def test_1201_signal_uses_1300_and_no_default_three_hour_exit():
    refs = tuple(reference(i, "1" if i == 12 else "100") for i in range(20))
    result = run(("0", "0", "0", "1", "1"), refs=refs)
    assert len(result.fills) == 1
    fill = result.fills[0]
    assert fill.order.decision.at == START + 12 * HOUR + timedelta(minutes=1)
    assert fill.trade.at == START + 13 * HOUR
    assert fill.reference.price == 100 and fill.trade.price == D("100.0300")
    assert result.decisions[-1].action == Action.HOLD
    assert result.final_account.quantity > 0
    assert result.marks[16].account.quantity == fill.trade.quantity


def test_price_access_after_price_free_target_evaluation(monkeypatch):
    evaluated = []
    original = historical.evaluate_strategy

    def evaluate(value):
        evaluated.append(value)
        return original(value)

    def guarded_references():
        # All targets are fixed before even iterating supplied hourly evidence.
        assert evaluated == [D(1), D(-1), D(1)]
        yield from (reference(i) for i in range(12))

    monkeypatch.setattr(historical, "evaluate_strategy", evaluate)
    first = run(("1", "-1", "1"), refs=guarded_references())
    second = run(("1", "-1", "1"), refs=tuple(reference(i, "999") for i in range(12)))
    assert first.decisions == second.decisions
    # Evidence and decisions contain no outcome field, future price, or quote.
    assert "price" not in asdict(first.decisions[0])
    assert "outcome" not in asdict(forecast())


def test_continuous_hold_full_exit_noop_and_new_signal_reentry():
    result = run(("1", "1", "1", "-1", "-1", "1", "-1"))
    assert [d.action for d in result.decisions] == [
        Action.BUY_REQUIRED,
        Action.HOLD,
        Action.HOLD,
        Action.EXIT_REQUIRED,
        Action.CASH_NOOP,
        Action.BUY_REQUIRED,
        Action.EXIT_REQUIRED,
    ]
    assert [f.trade.side for f in result.fills] == [Side.BUY, Side.SELL] * 2
    assert [f.trade.at for f in result.fills] == [
        START + i * HOUR for i in (1, 13, 21, 25)
    ]
    assert result.final_account.quantity == result.final_account.basis == 0
    assert len({f.order.decision.identity for f in result.fills}) == 4
    assert result.fills[2].order.decision.at > result.fills[1].trade.at
    assert all(m.account.cash >= 0 and m.account.quantity >= 0 for m in result.marks)


def test_one_miss_keeps_exposure_and_valid_signal_resets_streak():
    result = run(
        hours=20,
        forecasts=(forecast(0), forecast(2), forecast(4)),
        misses=(miss(1), miss(3)),
    )
    assert [d.missed_streak for d in result.decisions] == [0, 1, 0, 1, 0]
    assert (
        result.decisions[1].action == result.decisions[3].action == Action.SIGNAL_STALE
    )
    assert result.decisions[1].target is None
    assert len(result.fills) == 1 and result.final_account.quantity > 0
    assert result.status == "synthetic_missing_signals"


def test_two_misses_exit_at_actual_discovery_next_hour_and_no_old_reentry():
    discovered = START + 12 * HOUR + timedelta(minutes=1)
    result = run(
        hours=20,
        forecasts=(forecast(0), forecast(3), forecast(4)),
        misses=(miss(1, discovered), miss(2, discovered)),
    )
    assert result.decisions[1].at == result.decisions[2].at == discovered
    assert result.decisions[2].reason == "risk_exit_two_misses"
    assert result.decisions[3].action == Action.IGNORED_EXIT_PENDING
    assert result.decisions[3].missed_streak == 0
    assert [f.trade.at for f in result.fills] == [START + i * HOUR for i in (1, 13, 17)]
    assert result.fills[1].order.decision.miss == miss(2, discovered)
    assert result.fills[2].order.decision.forecast == forecast(4)


def test_exact_hour_discovery_waits_next_hour_and_flat_misses_never_sell():
    at = START + 9 * HOUR
    result = run(hours=12, forecasts=(forecast(0),), misses=(miss(1, at), miss(2, at)))
    assert result.fills[-1].trade.at == START + 10 * HOUR
    assert result.marks[9].account.quantity > 0
    assert result.marks[10].account.quantity == 0
    flat = run(hours=12, forecasts=(forecast(0, "0"),), misses=(miss(1), miss(2)))
    assert len(flat.fills) == 0
    assert all(d.action == Action.SIGNAL_MISSED for d in flat.decisions[1:])


@pytest.mark.parametrize("offset", [-1, 0])
def test_miss_cannot_be_discovered_before_or_at_deadline(offset):
    with pytest.raises(ValueError, match="AFTER"):
        miss(1, START + STEP + timedelta(minutes=16) + offset * US)


def test_misses_fail_if_backdated_reordered_duplicated_or_outside_fixture():
    with pytest.raises(ValueError, match="clock reversal"):
        run(
            hours=12,
            forecasts=(forecast(0), forecast(2)),
            misses=(miss(1, START + 9 * HOUR),),
        )
    with pytest.raises(ValueError, match="out-of-order"):
        run(hours=12, forecasts=(forecast(0),), misses=(miss(2), miss(1)))
    with pytest.raises(ValueError, match="grid"):
        run(hours=8, forecasts=(forecast(0), forecast(1)), misses=(miss(1),))
    with pytest.raises(ValueError, match="period"):
        run(hours=8, forecasts=(forecast(0),), misses=(miss(1, START + 9 * HOUR),))


def test_exact_costs_rounding_and_independent_financial_comparison():
    result = run(("1", "-1"))
    buy, sell = result.fills
    assert buy.trade.price == D("100.03") and sell.trade.price == D("99.97")
    assert buy.trade.quantity == affordable_quantity(
        D(10000), D("100.03"), D("0.000001")
    )
    assert buy.trade.quantity == D("99.870138")
    assert buy.trade.fee == D("9.99000991")  # rounded UP, not nearest or truncated
    assert fee_for(D("0.000000001")) == D("0.00000001")
    account = fund_account(Account(result.initial_account.portfolio), START)
    with localcontext(money_context()):
        q = buy.trade.quantity + result.config.quantity_step
        assert q * buy.trade.price + fee_for(q * buy.trade.price) > 10000
        for fill in result.fills:
            trade = fill.trade
            independently = calculate_trade(
                account.portfolio,
                trade.identity,
                trade.side,
                trade.at,
                trade.quantity,
                trade.price,
                ledger_seq_before=account.ledger_seq,
            )
            assert independently == trade
            assert trade.fee == fee_for(trade.notional)
            assert trade.postings[0].asset == "USDT"
            assert trade.postings[1].asset == "BTC"
            assert (
                trade.postings[0].amount + trade.postings[1].amount * trade.price
                == -trade.fee
            )
            account = apply_trade(account, independently)
            reconcile(account)
        assert account == result.final_account
        assert -account.realised == sum(
            (f.trade.fee + f.half_spread_cost + f.slippage_cost for f in result.fills),
            D(0),
        )
        assert buy.trade.quantity == sell.trade.quantity
        assert result.marks[1].account.basis == buy.trade.notional + buy.trade.fee


@pytest.mark.parametrize("step", ["0.000001", "0.1", "3"])
def test_explicit_synthetic_step_and_config_hash(step):
    config = HistoricalConfig(quantity_step=D(step))
    result = run(("1", "-1"), config=config)
    assert result.config == config
    assert all(f.trade.quantity % D(step) == 0 for f in result.fills)
    if step != "0.000001":
        assert (
            result.initial_account.portfolio.config_sha256
            != run().initial_account.portfolio.config_sha256
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"quantity_step": D(0)},
        {"quantity_step": D(-1)},
        {"quantity_step": D("NaN")},
        {"quantity_step": 0.01},
        {"fee_bps": D(0)},
        {"fee_bps": D(11)},
        {"half_spread_bps": D(3)},
        {"slippage_bps": D(10)},
        {"fee_quantum": D("0.01")},
        {"version": "stress"},
        {"sizing_version": "binance"},
    ],
)
def test_reject_unsupported_configuration(changes):
    with pytest.raises(ValueError):
        HistoricalConfig(**changes)


def test_unaffordable_buy_and_off_step_transition_fail_closed(monkeypatch):
    with pytest.raises(ValueError, match="Unaffordable"):
        run(config=HistoricalConfig(quantity_step=D(1000)))
    # A defective sizing provider cannot inject an invalid quantity into accounting.
    monkeypatch.setattr(historical, "affordable_quantity", lambda *args: D("0.0000001"))
    with pytest.raises(ValueError, match="off-step"):
        run()


def test_separate_accounts_funding_and_no_prospective_evidence():
    btc, eth = run(("1", "-1")), run(("0", "0"), symbol="ETHUSDT")
    assert btc.initial_account.cash == eth.initial_account.cash == 10000
    assert eth.final_account == eth.initial_account
    assert btc.final_account.portfolio != eth.final_account.portfolio
    assert btc.initial_account.ledger_seq == eth.initial_account.ledger_seq == 1
    with pytest.raises(ValueError, match="already"):
        fund_account(btc.initial_account, START)
    with pytest.raises(ValueError, match="mismatch"):
        apply_trade(eth.initial_account, btc.fills[0].trade)
    payload = json.loads(historical_json(btc))
    assert payload["kind"] == "historical_simulation"
    assert "not_evidenced_untested" in payload["execution_constraints"]
    for name in (
        "raw_body",
        "bid",
        "ask",
        "run_id",
        "automation_sha256",
        "issued_at",
        "request_started_at",
        "response_received_at",
        "filters",
    ):
        assert f'"{name}"' not in historical_json(btc)


def test_every_mark_reconciles_prefix_and_later_trade_cannot_change_history():
    result = run(("1", "1", "-1", "1"))
    with localcontext(money_context()):
        for mark in result.marks:
            prefix = tuple(
                f.trade for f in result.fills if f.trade.at <= mark.reference.at
            )
            account = replay(result.initial_account.portfolio, prefix)
            assert account == mark.account
            assert (
                value_historical(account, mark.reference, ledger_seq=mark.ledger_seq)
                == mark
            )
            assert mark.equity == account.cash + account.quantity * mark.reference.price
            assert account.realised + mark.unrealised == mark.equity - 10000
            assert account.cash == 10000 + sum(
                (t.postings[0].amount for t in prefix), D(0)
            )
            assert account.quantity == sum((t.postings[1].amount for t in prefix), D(0))
            assert account.fees == sum((t.fee for t in prefix), D(0))
    assert result.marks[0].equity == 10000
    assert result.marks[1].ledger_seq == 3  # buy precedes same-hour mark
    assert result.marks[9].ledger_seq == 5  # sell precedes same-hour mark
    assert result.marks[1].reference == result.fills[0].reference
    old = result.marks[1]
    with pytest.raises(ValueError, match="prefix/time"):
        value_historical(result.final_account, old.reference, ledger_seq=old.ledger_seq)
    with pytest.raises(ValueError, match="market"):
        value_historical(old.account, reference(1, symbol="ETHUSDT"), ledger_seq=3)
    with pytest.raises(FrozenInstanceError):
        old.equity = D(0)


@pytest.mark.parametrize(
    "kind", ["missing", "duplicate", "reversed", "identity", "market", "future"]
)
def test_invalid_forecast_collection_fails_closed(kind):
    fs = [forecast(0), forecast(1)]
    if kind == "missing":
        fs.pop()
    elif kind == "duplicate":
        fs[1] = fs[0]
    elif kind == "reversed":
        fs.reverse()
    elif kind == "identity":
        fs[1] = replace(fs[1], record_id=fs[0].record_id)
    elif kind == "market":
        fs[1] = forecast(1, symbol="ETHUSDT")
    else:
        fs[1] = forecast(2)
    with pytest.raises(ValueError):
        run(hours=8, forecasts=fs)


@pytest.mark.parametrize(
    "kind", ["missing", "duplicate", "reversed", "identity", "market", "future"]
)
@pytest.mark.parametrize("value", ["0", "1"])
def test_invalid_hourly_collection_fails_even_in_cash(kind, value):
    refs = [reference(i) for i in range(4)]
    if kind == "missing":
        refs.pop(1)
    elif kind == "duplicate":
        refs[1] = refs[0]
    elif kind == "reversed":
        refs.reverse()
    elif kind == "identity":
        refs[1] = replace(refs[1], record_id=refs[0].record_id)
    elif kind == "market":
        refs[1] = reference(1, symbol="ETHUSDT")
    else:
        refs[1] = reference(4)
    with pytest.raises(ValueError):
        run((value,), refs=refs)


@pytest.mark.parametrize(
    "changes",
    [
        {"price": D(0)},
        {"price": D(-1)},
        {"price": D("NaN")},
        {"price": D("Infinity")},
        {"price": 100.0},
        {"at": START + timedelta(minutes=1)},
        {"at": END},
        {"at": START - HOUR},
        {"at": START.replace(tzinfo=None)},
        {"source_sha256": "bad"},
        {"file_sha256": "bad"},
        {"record_id": ""},
        {"venue": "other"},
        {"market_type": "futures"},
        {"symbol": "DOGEUSDT"},
    ],
)
def test_invalid_hourly_evidence(changes):
    with pytest.raises(ValueError):
        replace(reference(), **changes)


def test_replay_rejects_duplicate_reordered_or_negative_postings():
    result = run(("1", "-1", "1"))
    p = result.initial_account.portfolio
    trades = tuple(f.trade for f in result.fills)
    with pytest.raises(ValueError):
        replay(p, trades + (trades[-1],))
    with pytest.raises(ValueError):
        replay(p, trades[::-1])
    bad = replace(result.final_account, cash=D(-1))
    with pytest.raises(ValueError, match="Negative"):
        value_historical(bad, reference(11), ledger_seq=bad.ledger_seq)


def test_decimal_context_serialization_and_reexecution_determinism():
    values = ("1", "1", "-1", "1", "-1")
    first = run(values)
    with localcontext() as caller:
        caller.prec = 4
        caller.rounding = ROUND_DOWN
        caller.traps[Inexact] = True
        second = run(values)
        assert first == second
        assert historical_json(first) == historical_json(second)
    # List versus tuple containers have no economic meaning; causal order does.
    assert (
        run(values, forecasts=[forecast(i, v) for i, v in enumerate(values)]) == first
    )
    assert json.loads(historical_json(first))["initial_account"]["cash"] == "10000"


def test_full_synthetic_year_uses_original_grid_and_no_year_end_sale():
    fs = tuple(forecast(i, "1" if i == 2194 else "0") for i in range(2195))
    result = replay_historical(
        "BTCUSDT",
        fs,
        tuple(reference(i) for i in range(8784)),
        protocol_sha256=HASH,
        model_recipe_sha256=SOURCE_HASH,
    )
    assert len(result.decisions) == 2195
    assert fs[-1].source_open == LAST_SOURCE
    assert fs[-1].feature_available_at == END - 8 * HOUR + timedelta(minutes=1)
    assert result.marks[-1].reference.at == END - HOUR
    assert len(result.fills) == 1 and result.fills[0].trade.side == Side.BUY
    assert result.final_account.quantity > 0
    assert result.final_account.realised == 0
    assert result.marks[-1].ledger_seq == 3
    with pytest.raises(ValueError, match="pinned"):
        forecast(2195)


def test_short_fixture_cannot_hide_pending_trade_or_empty_signal_grid():
    with pytest.raises(ValueError, match="next in-period"):
        run(hours=1)
    with pytest.raises(ValueError, match="forecast grid"):
        run(hours=4, forecasts=())


@pytest.mark.parametrize(
    "kind",
    [
        "future",
        "past",
        "market",
        "side",
        "unfunded",
        "negative_cash",
        "negative_base",
        "zero_sale",
        "off_step_sale",
        "rebuy",
    ],
)
def test_historical_trade_financial_boundary(kind):
    account = run().initial_account
    side, ref, at = Side.BUY, reference(1), START + HOUR
    if kind == "future":
        ref = reference(2)
    elif kind == "past":
        ref = reference(0)
    elif kind == "market":
        ref = reference(1, symbol="ETHUSDT")
    elif kind == "side":
        side = "BUY"
    elif kind == "unfunded":
        account = Account(account.portfolio)
    elif kind == "negative_cash":
        account = replace(account, cash=D(-1))
    elif kind == "negative_base":
        account = replace(account, quantity=D(-1))
    elif kind == "zero_sale":
        side = Side.SELL
    else:
        # The shared accounting primitive supports arbitrary quantities. The
        # historical adapter independently enforces its synthetic step and 0/100 rule.
        trade = calculate_trade(
            account.portfolio,
            "arithmetic-only",
            Side.BUY,
            START,
            D("1.0000001"),
            D(100),
            ledger_seq_before=1,
        )
        account = apply_trade(account, trade)
        side = Side.SELL if kind == "off_step_sale" else Side.BUY
    with pytest.raises(ValueError):
        historical.calculate_historical_trade(
            account, side, ref, at=at, identity="test"
        )


def test_historical_mark_sequence_requires_integer_and_trade_rejects_fee_overdraft():
    account = run().initial_account
    with pytest.raises(ValueError, match="prefix"):
        value_historical(account, reference(), ledger_seq=True)
    # The next step above maximal affordability includes notional plus CEILING fee.
    filled = historical.calculate_historical_trade(
        account, Side.BUY, reference(1), at=START + HOUR, identity="buy"
    )
    too_large = calculate_trade(
        account.portfolio,
        "too-large",
        Side.BUY,
        START + HOUR,
        filled.quantity + BASE_CONFIG.quantity_step,
        filled.price,
        ledger_seq_before=1,
    )
    with pytest.raises(ValueError, match="Insufficient cash"):
        apply_trade(account, too_large)


def test_independent_market_invocation_order_does_not_change_results():
    first = {s: run(("1", "-1"), symbol=s) for s in ("BTCUSDT", "ETHUSDT")}
    second = {s: run(("1", "-1"), symbol=s) for s in ("ETHUSDT", "BTCUSDT")}
    assert first == second

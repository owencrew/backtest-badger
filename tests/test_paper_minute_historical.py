"""Explicitly fabricated data only, including all full-year price/forecast grids."""

import builtins
import io
import json
import os
import socket
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, localcontext
from hashlib import sha256
from pathlib import Path

import psycopg
import pytest

from backtest_badger import (
    execution_data,
    forecast_data,
    minute_execution_data,
    model_data,
)
from backtest_badger import paper_minute_historical as minute
from backtest_badger.paper_accounting import fee_for, replay
from backtest_badger.paper_historical import (
    END,
    HOUR,
    START,
    HistoricalForecast,
    HourlyReference,
    SyntheticMiss,
    next_reference_at,
)
from backtest_badger.paper_types import STEP, Action, D, Side, money_context


@pytest.fixture(autouse=True)
def offline_boundary(monkeypatch):
    """Fail before any real artifact access, network, database or source loading."""

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Stage 4B.2D forbids source loaders, network, databases and artifacts"
        )

    for module, name in (
        (forecast_data, "load_forecasts"),
        (execution_data, "load_execution_data"),
        (minute_execution_data, "load_minute_execution_data"),
        (model_data, "load_model_data"),
        (psycopg, "connect"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
    ):
        monkeypatch.setattr(module, name, forbidden)

    def guard(original):
        def guarded(file, *args, **kwargs):
            if isinstance(file, (str, bytes, os.PathLike)):
                if "artifacts" in Path(os.fsdecode(file)).parts:
                    forbidden()
            return original(file, *args, **kwargs)

        return guarded

    for module, name in (
        (builtins, "open"),
        (io, "open"),
        (os, "open"),
        (os, "listdir"),
        (os, "scandir"),
    ):
        monkeypatch.setattr(module, name, guard(getattr(module, name)))


def digest(label):
    return sha256(("fabricated:" + label).encode()).hexdigest()


def reference(at=START, price="100", symbol="BTCUSDT", interval=60):
    args = (
        symbol,
        minute.reference_identity(symbol, at, interval),
        at,
        D(price),
        digest(f"file:{interval}"),
        digest(f"zip:{interval}:{symbol}:{at:%Y-%m}"),
    )
    return minute.MinuteReference(*args) if interval == 60 else HourlyReference(*args)


def pins(refs, interval=60):
    return minute.SyntheticPriceSource(
        interval,
        digest(f"manifest:{interval}"),
        digest(f"file:{interval}"),
        tuple(
            sorted({(r.symbol, r.at.strftime("%Y-%m"), r.source_sha256) for r in refs})
        ),
        minute.projection_sha256(refs),
    )


def forecast(index=0, value="1", symbol="BTCUSDT"):
    opened = START - STEP + index * STEP
    return HistoricalForecast(
        symbol,
        f"binance:spot:{symbol}:14400:{opened.isoformat()}:ridge",
        opened,
        opened + STEP + minute.MINUTE,
        D(value),
        digest("forecasts"),
    )


def miss(index, at=None):
    return SyntheticMiss(
        "BTCUSDT",
        START - STEP + index * STEP,
        at or START + index * STEP + timedelta(minutes=17),
        "fabricated_gap",
    )


def fixture(
    values=("1", "1", "-1", "0", "1"),
    *,
    hours=None,
    forecasts=None,
    misses=(),
    symbol="BTCUSDT",
):
    end = START + (hours if hours is not None else len(values) * 4) * HOUR
    forecasts = (
        tuple(forecast(i, v, symbol) for i, v in enumerate(values))
        if forecasts is None
        else forecasts
    )
    times = {START + i * HOUR for i in range((end - START) // HOUR)}
    times.update(minute.next_minute_at(f.feature_available_at) for f in forecasts)
    times.update(minute.next_minute_at(m.discovered_at) for m in misses)
    refs = tuple(reference(at, symbol=symbol) for at in sorted(times))
    return (
        forecasts,
        refs,
        {
            "source": pins(refs),
            "expected_source_sha256": minute.price_source_sha256(pins(refs)),
            "forecast_sha256": digest("forecasts"),
            "model_recipe_sha256": digest("model_manifest"),
            "end_exclusive": end,
            "synthetic_misses": misses,
        },
    )


def run(values=("1", "1", "-1", "0", "1"), **kwargs):
    fs, refs, options = fixture(values, **kwargs)
    return minute.replay_minute_historical(
        kwargs.get("symbol", "BTCUSDT"), fs, refs, **options
    )


def account(result, label="ridge"):
    return next(a for a in result.accounts if a.label == label)


@pytest.mark.parametrize(
    "at, expected",
    [
        (START, START + minute.MINUTE),
        (START + minute.MINUTE, START + 2 * minute.MINUTE),
        (
            START + timedelta(seconds=119, microseconds=999999),
            START + 2 * minute.MINUTE,
        ),
        (datetime(2024, 2, 28, 23, 59, tzinfo=UTC), datetime(2024, 2, 29, tzinfo=UTC)),
        (datetime(2024, 2, 29, 23, 59, tzinfo=UTC), datetime(2024, 3, 1, tzinfo=UTC)),
        (END - minute.MINUTE, END),
    ],
)
def test_strict_next_minute(at, expected):
    assert minute.next_minute_at(at) == expected
    assert next_reference_at(START) == START + HOUR  # frozen hourly function unchanged


@pytest.mark.parametrize(
    "value, target",
    [
        ("-1", 0),
        ("0", 0),
        ("1e-13", 0),
        ("1e-12", 0),
        ("1.00000000001e-12", 1),
    ],
)
def test_exact_ridge_threshold(value, target):
    result = run((value,))
    assert result.decisions[0].target == target
    assert len(account(result).fills) == target


def test_continuous_holding_full_sale_noop_reentry_and_costs():
    result = run()
    ridge = account(result)
    assert [d.action for d in result.decisions] == [
        Action.BUY_REQUIRED,
        Action.HOLD,
        Action.EXIT_REQUIRED,
        Action.CASH_NOOP,
        Action.BUY_REQUIRED,
    ]
    assert [f.trade.side for f in ridge.fills] == [Side.BUY, Side.SELL, Side.BUY]
    assert [f.trade.at for f in ridge.fills] == [
        START + i * HOUR + 2 * minute.MINUTE for i in (0, 8, 16)
    ]
    buy, sell, _ = ridge.fills
    assert buy.trade.quantity == sell.trade.quantity == D("99.870138")
    assert buy.trade.price == D("100.03")
    assert sell.trade.price == D("99.97")
    assert buy.trade.fee == D("9.99000991")
    with localcontext(money_context()):
        larger = (buy.trade.quantity + minute.QUANTITY_STEP) * buy.trade.price
        assert larger + fee_for(larger) > INITIAL
        assert buy.trade.postings[0].amount == -(buy.trade.notional + buy.trade.fee)
        assert sell.trade.postings[1].amount == -buy.trade.quantity
        flat = replay(ridge.initial.portfolio, (buy.trade, sell.trade))
        assert flat.quantity == flat.basis == 0
        assert -flat.realised == sum(
            (f.trade.fee + f.half_spread_cost + f.slippage_cost for f in (buy, sell)),
            D(0),
        )
    assert ridge.final.quantity > 0  # no forced endpoint sale
    assert account(result, "cash").fills == ()
    assert account(result, "cash").final.cash == INITIAL
    bh = account(result, "buy_and_hold")
    assert len(bh.fills) == 1 and bh.fills[0].trade.at == START
    assert bh.fills[0].decision_id is None and bh.fills[0].trade == replace(
        buy.trade,
        identity=bh.fills[0].trade.identity,
        portfolio=bh.initial.portfolio,
        at=START,
    )
    assert bh.marks[0].equity < INITIAL
    assert len({a.initial.portfolio.key for a in result.accounts}) == 3
    assert all(
        a.initial.cash == INITIAL and a.initial.ledger_seq == 1 for a in result.accounts
    )


INITIAL = D("10000")


def test_two_misses_sticky_exit_overlapping_positive_then_fresh_reentry():
    discovery = START + 12 * HOUR + minute.MINUTE
    result = run(
        hours=20,
        forecasts=(forecast(0), forecast(3), forecast(4)),
        misses=(miss(1, discovery), miss(2, discovery)),
    )
    ridge = account(result)
    assert [d.missed_streak for d in result.decisions] == [0, 1, 2, 0, 0]
    assert result.decisions[1].target is result.decisions[2].target is None
    assert result.decisions[2].at == discovery
    assert result.decisions[2].reason == "risk_exit_two_misses"
    assert result.decisions[3].action == Action.IGNORED_EXIT_PENDING
    assert [f.trade.at for f in ridge.fills] == [
        START + i * HOUR + 2 * minute.MINUTE for i in (0, 12, 16)
    ]
    assert ridge.fills[1].decision_id == result.decisions[2].identity
    assert ridge.fills[2].decision_id == result.decisions[4].identity
    assert result.status == "synthetic_missing_signals"


def test_execution_before_mark_and_discovery_at_mark_waits_next_minute():
    for discovery, exit_time, at9_invested in (
        (START + 9 * HOUR - timedelta(seconds=1), START + 9 * HOUR, False),
        (START + 9 * HOUR, START + 9 * HOUR + minute.MINUTE, True),
    ):
        result = run(
            hours=12,
            forecasts=(forecast(0),),
            misses=(miss(1, discovery), miss(2, discovery)),
        )
        ridge = account(result)
        assert ridge.fills[-1].trade.at == exit_time
        assert (ridge.marks[9].quantity > 0) == at9_invested
        assert ridge.marks[10].quantity == 0
        summary = minute.minute_account_summary(
            ridge, end_exclusive=result.end_exclusive
        )
        assert summary["exposure_seconds"] == (
            exit_time - ridge.fills[0].trade.at
        ) // timedelta(seconds=1)


def test_positive_at_exit_satisfaction_is_not_reused():
    discovery = START + 12 * HOUR + timedelta(seconds=59)
    result = run(
        hours=20,
        forecasts=(forecast(0), forecast(3), forecast(4)),
        misses=(miss(1, discovery), miss(2, discovery)),
    )
    assert result.decisions[3].action == Action.CASH_NOOP
    assert result.decisions[3].reason == "forecast_predates_exit_satisfaction"
    assert [f.trade.side for f in account(result).fills] == [
        Side.BUY,
        Side.SELL,
        Side.BUY,
    ]


def test_one_miss_stays_long_and_flat_misses_never_trade():
    result = run(
        hours=20,
        forecasts=(forecast(0), forecast(2), forecast(4)),
        misses=(miss(1), miss(3)),
    )
    assert [d.missed_streak for d in result.decisions] == [0, 1, 0, 1, 0]
    assert len(account(result).fills) == 1
    flat = run(hours=12, forecasts=(forecast(0, "0"),), misses=(miss(1), miss(2)))
    assert not account(flat).fills
    assert all(d.action == Action.SIGNAL_MISSED for d in flat.decisions[1:])


@pytest.mark.parametrize("offset", [-1, 0])
def test_misses_must_follow_cutoff(offset):
    with pytest.raises(ValueError):
        miss(1, START + STEP + timedelta(minutes=16, microseconds=offset))


def test_backdated_misses_rejected_and_omitted_forecast_never_invented():
    fs, refs, options = fixture(
        hours=12,
        forecasts=(forecast(0), forecast(2)),
        misses=(miss(1, START + 9 * HOUR),),
    )
    with pytest.raises(ValueError, match="clock reversal"):
        minute.replay_minute_historical("BTCUSDT", fs, refs, **options)
    fs, refs, options = fixture()
    with pytest.raises(ValueError, match="forecast grid"):
        minute.replay_minute_historical("BTCUSDT", fs[1:], refs, **options)


def test_infeasible_benchmark_uses_only_inception_price():
    fs, refs, options = fixture(("0", "0"))
    refs = (reference(price="100000000000"), *refs[1:])
    options["source"] = pins(refs)
    options["expected_source_sha256"] = minute.price_source_sha256(options["source"])
    result = minute.replay_minute_historical("BTCUSDT", fs, refs, **options)
    bh = account(result, "buy_and_hold")
    assert bh.status == "unavailable" and bh.final == bh.initial
    assert not bh.fills and not bh.marks
    assert (
        minute.minute_account_summary(bh, end_exclusive=result.end_exclusive)[
            "performance"
        ]
        is None
    )
    assert len(account(result, "cash").marks) == 8


def test_each_mark_reconciles_actual_signed_ledger_prefix_and_tampering_fails():
    result = run()
    for output in result.accounts:
        minute.verify_minute_account(output, end_exclusive=result.end_exclusive)
        for mark in output.marks:
            trades = [f.trade for f in output.fills if f.trade.at <= mark.reference.at]
            with localcontext(money_context()):
                assert mark.cash == INITIAL + sum(
                    (t.postings[0].amount for t in trades), D(0)
                )
                assert mark.quantity == sum(
                    (t.postings[1].amount for t in trades), D(0)
                )
                assert mark.realised + mark.unrealised == mark.equity - INITIAL
            prefix = replay(output.initial.portfolio, trades)
            assert (mark.basis, mark.fees, mark.realised) == (
                prefix.basis,
                prefix.fees,
                prefix.realised,
            )
        assert (
            replay(output.initial.portfolio, (f.trade for f in output.fills))
            == output.final
        )
    ridge = account(result)
    for field, value in (
        ("cash", D(3)),
        ("ledger_seq", 1),
        ("basis", D(9)),
        ("unrealised", D(7)),
    ):
        marks = list(ridge.marks)
        marks[1] = replace(marks[1], **{field: value})
        with pytest.raises(ValueError, match="ledger prefix"):
            minute.verify_minute_account(
                replace(ridge, marks=tuple(marks)), end_exclusive=result.end_exclusive
            )
    fill = ridge.fills[0]
    bad_fill = replace(fill, trade=replace(fill.trade, fee=D(0)))
    with pytest.raises(ValueError, match="Altered"):
        minute.verify_minute_account(
            replace(ridge, fills=(bad_fill, *ridge.fills[1:])),
            end_exclusive=result.end_exclusive,
        )


@pytest.mark.parametrize(
    "mutation",
    ["missing", "duplicate", "reorder", "extra", "other_market", "later_substitution"],
)
def test_bad_reference_grids_rejected_even_with_resealed_fixture(mutation):
    fs, refs, options = fixture(("0", "0"))
    rows = list(refs)
    if mutation == "missing":
        rows.pop(1)
    elif mutation == "duplicate":
        rows.insert(1, rows[1])
    elif mutation == "reorder":
        rows[1], rows[2] = rows[2], rows[1]
    elif mutation == "extra":
        rows.insert(1, reference(START + minute.MINUTE))
    elif mutation == "other_market":
        rows[1] = reference(rows[1].at, symbol="ETHUSDT")
    else:
        rows[1] = reference(rows[1].at + minute.MINUTE)
    options["source"] = pins(rows)
    options["expected_source_sha256"] = minute.price_source_sha256(options["source"])
    with pytest.raises(ValueError, match="reference grid"):
        minute.replay_minute_historical("BTCUSDT", fs, rows, **options)


@pytest.mark.parametrize(
    "changes",
    [
        {"price": D(0)},
        {"price": D("NaN")},
        {"price": 100.0},
        {"at": START + timedelta(seconds=1)},
        {"at": END},
        {"at": START.replace(tzinfo=None)},
        {"record_id": "hourly-disguised-as-minute"},
        {"symbol": "ETHUSDT"},
        {"interval_seconds": 3600},
        {"interval_seconds": True},
        {"venue": "other"},
        {"file_sha256": "invalid"},
        {"source_sha256": "invalid"},
    ],
)
def test_malformed_minute_reference(changes):
    with pytest.raises(ValueError):
        replace(reference(), **changes)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "reorder",
        "identity",
        "file",
        "market",
        "timing",
        "model",
        "nan",
    ],
)
def test_bad_forecasts(mutation):
    fs, refs, options = fixture()
    fs = list(fs)
    with pytest.raises(ValueError):
        if mutation == "missing":
            fs.pop(0)
        elif mutation == "duplicate":
            fs[1] = fs[0]
        elif mutation == "reorder":
            fs[1], fs[2] = fs[2], fs[1]
        else:
            changes = {
                "identity": {"record_id": "wrong"},
                "file": {"file_sha256": digest("wrong")},
                "market": {"symbol": "ETHUSDT"},
                "timing": {"feature_available_at": START},
                "model": {"model": "other"},
                "nan": {"prediction": D("NaN")},
            }
            fs[0] = replace(fs[0], **changes[mutation])
        minute.replay_minute_historical("BTCUSDT", fs, refs, **options)


@pytest.mark.parametrize(
    "mutation",
    [
        "file",
        "zip",
        "price",
        "manifest_shape",
        "status",
        "interval",
        "snapshot",
        "duplicate_pin",
    ],
)
def test_provenance_integrity(mutation):
    fs, refs, options = fixture()
    with pytest.raises(ValueError):
        if mutation in ("file", "zip", "price"):
            changes = {
                "file": {"file_sha256": digest("wrong")},
                "zip": {"source_sha256": digest("wrong")},
                "price": {"price": D(101)},
            }
            refs = (replace(refs[0], **changes[mutation]), *refs[1:])
        else:
            source = options["source"]
            changes = {
                "manifest_shape": {"manifest_sha256": "invalid"},
                "status": {"status": "genuine"},
                "interval": {"interval_seconds": 3600},
                "snapshot": {"projected_sha256": digest("wrong")},
                "duplicate_pin": {"monthly_sources": source.monthly_sources * 2},
            }
            options["source"] = replace(source, **changes[mutation])
        minute.replay_minute_historical("BTCUSDT", fs, refs, **options)


def test_price_free_policy_and_no_future_price_in_decisions(monkeypatch):
    fs, refs, options = fixture()
    evaluated = []
    original = minute.evaluate_strategy

    def policy(prediction):
        evaluated.append(prediction)
        return original(prediction)

    def supplied():
        assert len(evaluated) == len(fs)
        yield from refs

    monkeypatch.setattr(minute, "evaluate_strategy", policy)
    first = minute.replay_minute_historical("BTCUSDT", fs, supplied(), **options)
    changed = tuple(replace(r, price=D(200)) for r in refs)
    options["source"] = pins(changed)
    options["expected_source_sha256"] = minute.price_source_sha256(options["source"])
    second = minute.replay_minute_historical("BTCUSDT", fs, changed, **options)
    assert first.decisions == second.decisions
    assert not any(
        key in minute.scientific_json(first.decisions)
        for key in ('"price"', '"high"', '"low"', '"close"')
    )


def test_determinism_decimal_context_serialization_and_benchmark_drawdown():
    first = run()
    with localcontext() as context:
        context.prec, context.rounding = 6, ROUND_DOWN
        second = run()
        summary2 = minute.minute_account_summary(
            account(second, "buy_and_hold"), end_exclusive=second.end_exclusive
        )
    assert minute.scientific_json(first) == minute.scientific_json(second)
    summary = minute.minute_account_summary(
        account(first, "buy_and_hold"), end_exclusive=first.end_exclusive
    )
    assert summary == summary2
    bh = account(first, "buy_and_hold")
    assert (
        summary["maximum_observed_hourly_reference_mark_drawdown"]
        == (INITIAL - bh.marks[0].equity) / INITIAL
    )
    assert summary["exposure_seconds"] == 20 * 3600
    parsed = json.loads(minute.scientific_json(first))
    assert parsed["accounts"][0]["marks"][1]["cash"] == str(
        account(first).marks[1].cash
    )
    assert "trade_ids" not in parsed["accounts"][0]["marks"][1]
    with pytest.raises(ValueError, match="floats"):
        minute.scientific_json({"wrong": 1.2})


@pytest.mark.parametrize("symbol", minute.SYMBOLS)
def test_complete_fabricated_leap_year_and_compact_serialization(symbol):
    # Frequent transitions exercise growing shared account history without storing
    # it at every mark. All prices and forecasts are invented by this test.
    values = tuple("1" if i % 2 == 0 else "0" for i in range(2195))
    result = run(values, hours=8784, symbol=symbol)
    ridge = account(result)
    assert len(result.decisions) == 2195
    assert len(ridge.fills) == 2195
    assert result.decisions[-1].at == END - 8 * HOUR + minute.MINUTE
    assert ridge.fills[-1].trade.at == END - 8 * HOUR + 2 * minute.MINUTE
    assert all(len(a.marks) == 8784 for a in result.accounts)
    assert all(a.marks[-1].reference.at == END - HOUR for a in result.accounts)
    assert sum(m.reference.at.month == 2 for m in ridge.marks) == 696
    assert ridge.final.quantity > 0
    text = minute.scientific_json(result)
    assert text.count('"trade_ids"') == 6  # initial/final only, not 26,352 snapshots
    assert len(text) < 35_000_000
    assert (
        result.authentication
        == "synthetic_projection_only_not_full_source_authentication"
    )


def test_guards_fail_before_real_access():
    calls = (
        lambda: Path("artifacts/never-open").read_bytes(),
        lambda: builtins.open("artifacts/never-open"),
        lambda: os.listdir("artifacts"),
        lambda: os.scandir("artifacts"),
        lambda: socket.create_connection(("example.invalid", 443)),
        lambda: psycopg.connect(""),
        lambda: minute_execution_data.load_minute_execution_data("never-open"),
        lambda: forecast_data.load_forecasts("never-open"),
        lambda: execution_data.load_execution_data("never-open"),
        lambda: model_data.load_model_data("never-open"),
    )
    for call in calls:
        with pytest.raises(pytest.fail.Exception, match="forbids"):
            call()


def test_distinct_ledgers_and_unaffordable_ridge_buy_fail_closed():
    result = run()
    for output in result.accounts:
        ledger = minute.minute_ledger_records(output)
        assert len(ledger) == 1 + 2 * len(output.fills)
        assert [row["sequence"] for row in ledger] == list(range(1, len(ledger) + 1))
        assert {row["account_id"] for row in ledger} == {output.initial.portfolio.key}
        assert ledger[0]["amount"] == INITIAL
        with localcontext(money_context()):
            assert (
                sum((row["amount"] for row in ledger if row["asset"] == "USDT"), D(0))
                == output.final.cash
            )
    fs, refs, options = fixture(("1",))
    rows = tuple(replace(r, price=D("100000000000")) for r in refs)
    options["source"] = pins(rows)
    options["expected_source_sha256"] = minute.price_source_sha256(options["source"])
    with pytest.raises(ValueError, match="Infeasible"):
        minute.replay_minute_historical("BTCUSDT", fs, rows, **options)


def test_missing_last_forecast_and_off_grid_endpoints_rejected():
    fs, refs, options = fixture(("1",))
    for end in (
        START,
        END + HOUR,
        START + timedelta(minutes=30),
        START.replace(tzinfo=None),
    ):
        with pytest.raises(ValueError):
            minute.replay_minute_historical(
                "BTCUSDT", fs, refs, **{**options, "end_exclusive": end}
            )
    with pytest.raises(ValueError, match="forecast grid"):
        minute.replay_minute_historical(
            "BTCUSDT", fs, refs, **{**options, "end_exclusive": END}
        )
    with pytest.raises(ValueError):
        forecast(2195)  # forbidden December 31 20:01 availability


def test_metadata_manifest_mutation_fails_with_original_external_fingerprint():
    fs, refs, options = fixture()
    options["source"] = replace(options["source"], manifest_sha256=digest("changed"))
    with pytest.raises(ValueError, match="metadata changed"):
        minute.replay_minute_historical("BTCUSDT", fs, refs, **options)


def test_full_year_cannot_replace_required_forecasts_with_outage_fixtures():
    fs, refs, options = fixture(("1",))
    fs = tuple(forecast(i) for i in range(2195) if i != 1)
    options.update(end_exclusive=END, synthetic_misses=(miss(1),))
    with pytest.raises(ValueError, match="exactly 2195 forecasts"):
        minute.replay_minute_historical("BTCUSDT", fs, refs, **options)

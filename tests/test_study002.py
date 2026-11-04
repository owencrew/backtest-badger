"""Fabricated study data only. Genuine inputs are never opened by this suite."""

import json
import socket
from dataclasses import replace
from datetime import timedelta
from decimal import localcontext
from types import SimpleNamespace

import pytest

from backtest_badger import study002 as s
from backtest_badger import study002_runner as runner
from backtest_badger.paper_types import D, money_context

PIN = "a" * 64


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Study tests must stay offline")

    monkeypatch.setattr(socket, "socket", no_network)


def fixture(symbol="BTCUSDT", days=5, values=("101", "102", "99", "100", "110")):
    end = s.minute.START + days * s.DAY
    first = s.minute.START - s.LOOKBACK - s.STEP
    stop = end - s.DAY
    closes = []
    for i in range((stop - first) // s.STEP):
        opened = first + i * s.STEP
        index = (opened + s.STEP - s.minute.START) // s.DAY
        price = (
            values[index % len(values)] if opened + s.STEP >= s.minute.START else "100"
        )
        closes.append(s.Close(symbol, opened, opened + s.STEP, D(price)))
    times = {s.minute.START + i * s.minute.HOUR for i in range(days * 24)} | {
        s.minute.START + i * s.DAY + 2 * s.minute.MINUTE for i in range(days)
    }
    refs = tuple(
        s.minute.MinuteReference(
            symbol, s.minute.reference_identity(symbol, t, 60), t, D("100"), PIN, PIN
        )
        for t in sorted(times)
    )
    return tuple(closes), refs, end


def replay(closes=None, refs=None, days=5, symbol="BTCUSDT"):
    c, r, end = fixture(symbol, days)
    return s.replay(
        symbol,
        c if closes is None else closes,
        r if refs is None else refs,
        config_sha256=PIN,
        method_sha256=PIN,
        end=end,
    )


@pytest.mark.parametrize(
    "now,old,target",
    [
        ("101", "100", True),
        ("99", "100", False),
        ("100", "100", False),
        ("1.00000000000000000000000000000000000000001", "1", True),
    ],
)
def test_exact_decimal_sign(now, old, target):
    a = s.Close("BTCUSDT", s.minute.START - s.STEP, s.minute.START, D(now))
    b = s.Close(
        "BTCUSDT",
        s.minute.START - s.LOOKBACK - s.STEP,
        s.minute.START - s.LOOKBACK,
        D(old),
    )
    with localcontext() as ctx:
        ctx.prec = 6
        result = s.signal(a, b, s.minute.START + s.minute.MINUTE)
    assert result.long is target
    assert (result.numerator > 0) is target


@pytest.mark.parametrize(
    "delta", [timedelta(0), s.minute.MINUTE, 2 * s.minute.MINUTE, timedelta(hours=1)]
)
def test_availability_exact(delta):
    c, _, _ = fixture()
    now = next(x for x in c if x.closed == s.minute.START)
    past = c[0]
    if delta == s.minute.MINUTE:
        assert s.signal(now, past, s.minute.START + delta).at == s.minute.START + delta
    else:
        with pytest.raises(ValueError):
            s.signal(now, past, s.minute.START + delta)


@pytest.mark.parametrize("price", ["NaN", "Infinity", "-Infinity", "0", "-1"])
def test_invalid_price(price):
    with pytest.raises(ValueError):
        s.Close("BTCUSDT", s.minute.START - s.STEP, s.minute.START, D(price))


def test_boundaries_and_lookback():
    c, _, _ = fixture()
    with pytest.raises(ValueError):
        replace(c[0], closed=c[0].closed + s.minute.MINUTE)
    with pytest.raises(ValueError):
        replace(c[0], opened=c[0].opened + s.minute.MINUTE)
    now = next(x for x in c if x.closed == s.minute.START)
    with pytest.raises(ValueError):
        s.signal(now, c[6], s.minute.START + s.minute.MINUTE)
    with pytest.raises(ValueError):
        s.signal(now, replace(c[0], symbol="ETHUSDT"), s.minute.START + s.minute.MINUTE)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_warmup",
        "missing_middle",
        "missing_last",
        "duplicate",
        "reverse",
        "wrong_market",
        "extra",
    ],
)
def test_fail_closed_source_grid(mutation):
    c, r, end = fixture()
    changed = {
        "missing_warmup": c[1:],
        "missing_middle": c[:20] + c[21:],
        "missing_last": c[:-1],
        "duplicate": c[:2] + c[1:],
        "reverse": c[::-1],
        "wrong_market": (replace(c[0], symbol="ETHUSDT"),) + c[1:],
        "extra": c
        + (replace(c[-1], opened=c[-1].opened + s.STEP, closed=c[-1].closed + s.STEP),),
    }[mutation]
    with pytest.raises(ValueError):
        s.replay("BTCUSDT", changed, r, config_sha256=PIN, method_sha256=PIN, end=end)


def test_daily_only_continuous_hold_cash_and_transitions():
    result = replay()
    assert [d["action"] for d in result["decisions"]] == [
        "BUY_REQUIRED",
        "HOLD",
        "EXIT_REQUIRED",
        "CASH_NOOP",
        "BUY_REQUIRED",
    ]
    a = result["accounts"][0]
    assert [f.trade.side.value for f in a.fills] == ["BUY", "SELL", "BUY"]
    assert all(f.trade.at.hour == 0 and f.trade.at.minute == 2 for f in a.fills)
    assert a.final.quantity > 0  # no terminal sale
    assert len(a.marks) == 120
    assert a.marks[0].quantity == 0 and a.marks[1].quantity > 0
    assert a.marks[25].quantity == a.marks[1].quantity
    assert a.marks[49].quantity == 0
    assert a.initial.portfolio.strategy_id == s.STRATEGY
    assert a.label == s.STRATEGY


def test_future_price_invariance():
    c, r, end = fixture()
    plan = s.signals("BTCUSDT", c, end=end)
    future = tuple(
        replace(x, price=D("500")) if x.closed > s.minute.START + s.DAY else x
        for x in c
    )
    assert s.signals("BTCUSDT", future, end=end)[:2] == plan[:2]
    altered = tuple(replace(x, price=D("200")) for x in r)
    assert [d["signal"] for d in replay(c, altered)["decisions"]] == list(plan)
    assert s.signal.__code__.co_argcount == 3


@pytest.mark.parametrize(
    "mutation", ["missing", "reverse", "duplicate", "wrong_market"]
)
def test_minute_identity_and_coverage(mutation):
    c, r, _ = fixture()
    changed = {
        "missing": r[1:],
        "reverse": r[::-1],
        "duplicate": r[:1] + r,
        "wrong_market": tuple(
            replace(
                x,
                symbol="ETHUSDT",
                record_id=s.minute.reference_identity("ETHUSDT", x.at, 60),
            )
            for x in r
        ),
    }[mutation]
    with pytest.raises(ValueError):
        replay(c, changed)


def test_money_rounding_affordability_and_pairing():
    a = replay()["accounts"][0]
    f = a.fills[0]
    assert f.trade.price == D("100.0300")
    assert f.trade.fee == s.accounting.fee_for(f.trade.notional)
    with localcontext(money_context()):
        q = f.trade.quantity + D("0.000001")
        assert q * f.trade.price + s.accounting.fee_for(q * f.trade.price) > D(10000)
    assert len(f.trade.postings) == 2
    assert all(m.cash >= 0 and m.quantity >= 0 for m in a.marks)
    assert (
        s.accounting.replay(a.initial.portfolio, (f.trade for f in a.fills)) == a.final
    )
    assert a.fills[1].trade.price == D("99.9700")
    damaged = replace(a, final=replace(a.final, cash=a.final.cash + D(1)))
    with pytest.raises(ValueError):
        s.minute.verify_minute_account(
            s.legacy_view(damaged), end_exclusive=s.minute.START + 5 * s.DAY
        )


def test_independent_accounts_and_determinism():
    btc, eth = replay(), replay(symbol="ETHUSDT")
    assert s.local._bytes(btc) == s.local._bytes(replay())
    accounts = btc["accounts"] + eth["accounts"]
    assert len({a.initial.portfolio.key for a in accounts}) == 6
    assert all(a.initial.cash == D(10000) for a in accounts)
    assert btc["accounts"][1].final.cash == D(10000)
    assert len(btc["accounts"][2].fills) == 1
    assert btc["accounts"][2].fills[0].trade.at == s.minute.START


@pytest.fixture(scope="module")
def full_year():
    results = []
    rows = []
    details = []
    for symbol in s.minute.SYMBOLS:
        r = replay(days=366, symbol=symbol)
        a, d = s.reports(r)
        results.append(r)
        rows.extend(a)
        details.extend(d)
    summary = json.loads(s.local._bytes({"accounts": rows}))
    evidence = json.loads(s.local._bytes({"results": results, "reports": details}))
    return summary, evidence, {"accounts": summary["accounts"]}


def test_full_year_reporting_and_independent_verifier(full_year):
    summary, evidence, old = full_year
    assert runner.validate_evidence(summary, evidence, old)["status"] == "passed"
    for row in summary["accounts"]:
        assert row["complete_day_statistics"]["count"] == 365
        assert row["signal_evaluations"] == (366 if row["label"] == s.STRATEGY else 0)
        if row["label"] == "cash":
            assert (
                D(row["descriptive_statistics"]["annualised_daily_volatility"]["value"])
                == 0
            )
            assert row["descriptive_statistics"]["zero_rate_sharpe"]["value"] is None
    for r in evidence["reports"]:
        obs = r["summary"]["observations"]
        assert not obs[-1]["complete"] and obs[-1]["missing_boundary_seconds"] == 3600
        assert not obs[365]["complete"]


@pytest.mark.parametrize(
    "field", ["final_cash", "final_mark_equity", "position_changes"]
)
def test_summary_tampering_rejected(full_year, field):
    summary, evidence, old = full_year
    changed = json.loads(json.dumps(summary))
    changed["accounts"][0][field] = 999
    with pytest.raises(ValueError):
        runner.validate_evidence(changed, evidence, old)


def test_ledger_tampering_rejected(full_year):
    summary, evidence, old = full_year
    changed = json.loads(json.dumps(evidence))
    changed["reports"][0]["ledger"][1]["amount"] = "-1"
    with pytest.raises(ValueError):
        runner.validate_evidence(summary, changed, old)


def test_consent_before_inputs(tmp_path, monkeypatch):
    def forbidden(*args):
        raise AssertionError("Input read before consent")

    monkeypatch.setattr(runner, "preflight", forbidden)
    with pytest.raises(ValueError, match="execute"):
        runner.run({}, None, None, tmp_path)


def test_attempt_failure_retained_no_completion(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    def fail(*args):
        raise ValueError("input substitution")

    monkeypatch.setattr(runner, "preflight", fail)
    with pytest.raises(ValueError, match="substitution"):
        runner.run({}, None, None, tmp_path / "artifacts/runs", execute=True)
    directory = next((tmp_path / "artifacts/runs").iterdir())
    assert (directory / "attempt.json").exists() and (
        directory / "FAILED.json"
    ).exists()
    assert not (directory / "COMPLETE.json").exists()
    assert directory.stat().st_mode & 0o777 == 0o700


def test_output_hash_and_no_overwrite(tmp_path):
    p = tmp_path / "immutable"
    s.local._write(p, b"one")
    with pytest.raises(FileExistsError):
        s.local._write(p, b"two")
    assert p.read_bytes() == b"one"
    with pytest.raises(FileNotFoundError):
        runner.verify_output(tmp_path)


def test_freeze_substitution(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "DOCS", tmp_path)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    record = {
        "schema": "study-002-freeze-v1",
        "frozen_at": "2026-01-01T00:00:00+00:00",
        "files": {"config.json": {"sha256": PIN, "bytes": 1}},
    }
    (tmp_path / "config.json").write_text("changed")
    (tmp_path / "study-002-freeze.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="changed"):
        runner.check_freeze()


def test_complete_runner_lifecycle(tmp_path, monkeypatch, full_year):
    summary, _, old = full_year
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    closes, refs = {}, {}
    for symbol in s.minute.SYMBOLS:
        closes[symbol], refs[symbol], _ = fixture(symbol, 366)
    freeze = {
        "files": {
            "docs/studies/study-002-methodology.md": {"sha256": PIN},
            "docs/studies/study-002-config.json": {"sha256": PIN},
        }
    }
    monkeypatch.setattr(
        runner,
        "preflight",
        lambda *args: (
            freeze,
            SimpleNamespace(pins={"fixture": True}),
            closes,
            refs,
            old,
        ),
    )
    directory = runner.run({}, None, None, tmp_path / "artifacts/runs", execute=True)
    assert runner.verify_output(directory)["complete"] is True
    assert (
        json.loads((directory / "summary.json").read_bytes())["accounts"]
        == summary["accounts"]
    )
    (directory / "summary.json").write_text("tampered")
    with pytest.raises(ValueError, match="Output mismatch"):
        runner.verify_output(directory)


def test_unavailable_buy_hold_is_explicit():
    c, refs, end = fixture(values=("100",))
    refs = tuple(replace(r, price=D("1e20")) for r in refs)
    result = s.replay("BTCUSDT", c, refs, config_sha256=PIN, method_sha256=PIN, end=end)
    assert result["accounts"][0].final.cash == D(10000)
    account = result["accounts"][2]
    assert account.status == "unavailable" and not account.marks and not account.fills
    summary, _ = s.reports(result, end=end)
    assert summary[2]["performance"] is None
    assert summary[2]["descriptive_statistics"]["zero_rate_sharpe"]["value"] is None

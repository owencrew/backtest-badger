"""Synthetic execution tests: no database, network, training or holdout inputs."""

import csv
import io
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from backtest_badger import backtest, cli, execution_data, forecast_data
from backtest_badger.backtest import (
    ACCOUNTING,
    ACCOUNTING_TOLERANCE,
    SCENARIOS,
    Costs,
    simulate_account,
)
from backtest_badger.execution_data import START, csv_bytes, json_bytes
from backtest_badger.forecast_data import MODELS, Signal, schedule, should_enter
from backtest_badger.frozen import STEP, SYMBOLS
from backtest_badger.model_data import sha256

D = Decimal


def signal(hour=8, forecast="0.01", model="ridge", symbol="BTCUSDT"):
    opened = START + timedelta(hours=hour)
    return Signal(
        symbol, model, opened, opened + STEP + timedelta(seconds=60), D(forecast)
    )


def prices_for(signals, buy="100", sell="110"):
    return {
        key: price
        for s in signals
        for key, price in (
            ((s.symbol, schedule(s)[0]), D(buy)),
            ((s.symbol, schedule(s)[1]), D(sell)),
        )
    }


def test_timing_and_hand_calculated_frictionless():
    s = signal()
    p = prices_for([s])
    p["BTCUSDT", START + timedelta(hours=12)] = D(1)  # already passed, forbidden fill
    trades, equity, metrics = simulate_account([s], p, SCENARIOS[0])
    t = trades[0]
    assert t["signal_time"] == "2024-01-01T12:01:00+00:00"
    assert t["entry_time"] == "2024-01-01T13:00:00+00:00"
    assert t["exit_time"] == "2024-01-01T16:00:00+00:00"
    assert t["entry_price"] == D(100)
    assert t["quantity"] == D(100)
    assert t["gross_pnl"] == t["net_pnl"] == D(1000)
    assert metrics["ending_equity"] == equity[-1]["cash"] == D(11000)
    assert metrics["net_return_pct"] == 10
    assert metrics["win_rate"] == 1


@pytest.mark.parametrize(
    "forecast,expected",
    [
        ("-1", False),
        ("0", False),
        ("1e-12", False),
        ("-1e-12", False),
        ("1.0000001e-12", True),
        ("0.1", True),
    ],
)
def test_fixed_long_cash_rule(forecast, expected):
    s = signal(forecast=forecast)
    trades, _, m = simulate_account([s], prices_for([s]), SCENARIOS[1])
    assert should_enter(s) is expected
    assert len(trades) == int(expected)
    assert m["cash_signals"] == int(not expected)
    assert all(t["quantity"] > 0 and t["cash_after_entry"] >= 0 for t in trades)


def test_zero_model_all_cash():
    signals = [signal(i, "0", "zero") for i in (0, 4, 8)]
    trades, equity, m = simulate_account(signals, prices_for(signals), SCENARIOS[2])
    assert not trades
    assert all(e["cash"] == 10000 and e["asset_quantity"] == 0 for e in equity)
    assert m["win_rate"] is m["average_net_trade_return"] is None
    assert m["fraction_windows_invested"] == m["max_realised_equity_drawdown"] == 0


@pytest.mark.parametrize("costs", SCENARIOS)
def test_accounting_conservation_and_cost_directions(costs):
    s = signal()
    trades, _, m = simulate_account([s], prices_for([s]), costs)
    t = trades[0]
    with localcontext(ACCOUNTING):
        f, h, slip = (
            v / 10000
            for v in (costs.fee_bps, costs.half_spread_bps, costs.slippage_bps)
        )
        assert t["entry_price"] == 100 * (1 + h + slip)
        assert t["exit_price"] == 110 * (1 - h - slip)
        assert t["entry_fee"] == t["entry_notional"] * f
        assert t["exit_fee"] == t["exit_notional"] * f
        assert t["total_fees"] == t["entry_fee"] + t["exit_fee"]
        assert (
            t["cash_before"]
            == t["cash_after_entry"] + t["entry_notional"] + t["entry_fee"]
        )
        assert (
            t["cash_after_exit"]
            == t["cash_after_entry"] + t["exit_notional"] - t["exit_fee"]
        )
        assert t["asset_after_exit"] == 0
        assert (
            abs(
                t["net_pnl"]
                - (
                    t["gross_pnl"]
                    - t["total_fees"]
                    - t["spread_cost"]
                    - t["slippage_cost"]
                )
            )
            <= ACCOUNTING_TOLERANCE
        )
        assert t["quantity"] * t["entry_price"] * (1 + f) <= 10000
        assert (t["quantity"] + D("1e-24")) * t["entry_price"] * (1 + f) > 10000
        assert m["account_reconciliation_error"] <= ACCOUNTING_TOLERANCE


def test_known_fee_pnl():
    s = signal()
    t = simulate_account(
        [s], prices_for([s], buy="100", sell="100"), Costs("fees", D(100), D(0), D(0))
    )[0][0]
    # 1% on BOTH sides: q=10000/101, loss=q*2, no reference-price P&L.
    with localcontext(ACCOUNTING):
        assert t["gross_pnl"] == 0
        assert abs(t["net_pnl"] + t["quantity"] * 2) <= ACCOUNTING_TOLERANCE
        assert abs(t["net_pnl"] - D("-198.019801980198019801980198")) < D("1e-20")


def test_decisions_precede_every_future_price_access(monkeypatch):
    signals = [signal(i, v) for i, v in ((0, "0.1"), (4, "-0.1"), (8, "0.2"))]
    decisions = []
    original = backtest.should_enter

    def decide(s):
        decisions.append(original(s))
        return decisions[-1]

    class GuardedPrices(dict):
        def get(self, key):
            assert decisions == [True, False, True]
            return super().get(key)

        def __getitem__(self, key):
            assert decisions == [True, False, True]
            return super().__getitem__(key)

    monkeypatch.setattr(backtest, "should_enter", decide)
    p = GuardedPrices(prices_for(signals))
    first = simulate_account(signals, p, SCENARIOS[1])[0]
    decisions.clear()
    second = simulate_account(
        signals, GuardedPrices(prices_for(signals, "1000", "1")), SCENARIOS[1]
    )[0]
    assert [(t["signal_time"], t["entry_time"]) for t in first] == [
        (t["signal_time"], t["entry_time"]) for t in second
    ]


@pytest.mark.parametrize(
    "kind",
    ["naive", "offset", "early", "late", "off_grid", "test", "nan", "symbol", "model"],
)
def test_signal_rejection(kind):
    s = signal()
    if kind == "naive":
        s = replace(s, signal_time=s.signal_time.replace(tzinfo=None))
    elif kind == "offset":
        from datetime import timezone

        s = replace(
            s, signal_time=s.signal_time.astimezone(timezone(timedelta(hours=1)))
        )
    elif kind in ("early", "late"):
        s = replace(
            s,
            signal_time=s.signal_time
            + timedelta(seconds=-60 if kind == "early" else 60),
        )
    elif kind == "off_grid":
        s = signal(9)
    elif kind == "test":
        s = replace(
            s,
            open_time=datetime(2024, 12, 31, 20, tzinfo=UTC),
            signal_time=datetime(2025, 1, 1, 0, 1, tzinfo=UTC),
        )
    elif kind == "nan":
        s = replace(s, forecast=D("NaN"))
    elif kind == "symbol":
        s = replace(s, symbol="BADUSDT")
    else:
        s = replace(s, model="unknown")
    with pytest.raises(ValueError):
        schedule(s)


@pytest.mark.parametrize(
    "signals",
    [
        [signal(4), signal(0)],
        [signal(), signal()],
        [signal(), signal(12, symbol="ETHUSDT")],
        [signal(), signal(12, model="zero")],
    ],
)
def test_order_overlap_and_account_identity_rejection(signals):
    with pytest.raises(ValueError, match="overlapping|Mixed"):
        simulate_account(signals, prices_for(signals), SCENARIOS[0])


@pytest.mark.parametrize(
    "kind", ["missing", "wrong_symbol", "wrong_hour", "nan", "zero", "float"]
)
def test_execution_references_fail_even_for_cash(kind):
    s = signal(forecast="0", model="zero")
    p = prices_for([s])
    key = (s.symbol, schedule(s)[0])
    del p[key]
    if kind == "wrong_symbol":
        p["ETHUSDT", key[1]] = D(100)
    elif kind == "wrong_hour":
        p[key[0], key[1] - timedelta(hours=1)] = D(100)
    elif kind != "missing":
        p[key] = {"nan": D("NaN"), "zero": D(0), "float": 100.0}[kind]
    with pytest.raises(ValueError, match="reference"):
        simulate_account([s], p, SCENARIOS[0])


def test_drawdown_and_account_independence():
    signals = [signal(i) for i in (0, 4, 8)]
    p = prices_for(signals, "100", "90")
    p["BTCUSDT", schedule(signals[1])[1]] = D(100)
    t, e, m = simulate_account(signals, p, SCENARIOS[0])
    assert [r["cash"] for r in e] == [10000, 9000, 9000, 8100]
    assert m["max_realised_equity_drawdown"] == D("0.19")
    assert m["ending_equity"] == 8100
    for symbol in SYMBOLS:
        for model in MODELS:
            other = signal(
                symbol=symbol, model=model, forecast="0" if model == "zero" else "1"
            )
            result = simulate_account([other], prices_for([other]), SCENARIOS[0])
            assert result[2]["starting_equity"] == 10000
            assert result[2]["ending_equity"] == (10000 if model == "zero" else 11000)
    assert t[-1]["cash_after_exit"] == 8100


@pytest.mark.parametrize(
    "values",
    [("-1", "0", "0"), ("NaN", "0", "0"), ("10000", "0", "0"), ("0", "9999", "1")],
)
def test_invalid_costs(values):
    with pytest.raises(ValueError):
        Costs("invalid", *(D(v) for v in values))


@pytest.fixture
def execution(tmp_path, monkeypatch, archive_download):
    out = tmp_path / "execution"
    calls = []

    def download(request):
        calls.append(request)
        return archive_download(request)

    monkeypatch.setattr(execution_data, "download_archive", download)
    execution_data.prepare_execution_data(out)
    assert len(calls) == 24
    assert [(r.symbol, r.month) for r in calls[:2]] == [(s, "2024-01") for s in SYMBOLS]
    return out


def test_native_artifact_replay_exact_precision(execution):
    metadata, prices = execution_data.load_execution_data(execution)
    assert len(prices) == 17568
    assert (
        str(prices["BTCUSDT", START]) == "100.123456789012345678901234567890123456789"
    )
    assert metadata["coverage"]["complete"]
    with pytest.raises(FileExistsError):
        execution_data.prepare_execution_data(execution)


@pytest.mark.parametrize(
    "kind",
    [
        "zip",
        "sidecar",
        "source_identity",
        "source_hash",
        "price",
        "missing_hour",
        "manifest",
        "audit",
    ],
)
def test_altered_execution_rejected(execution, kind):
    manifest = json.loads((execution / "manifest.json").read_bytes())
    if kind in ("zip", "sidecar"):
        name = "BTCUSDT-1h-2024-01.zip" + (".CHECKSUM" if kind == "sidecar" else "")
        with (execution / "raw" / name).open("ab") as f:
            f.write(b"altered")
    elif kind in ("source_identity", "source_hash"):
        manifest["sources"][0]["symbol" if kind == "source_identity" else "sha256"] = (
            "wrong"
        )
        # Update audit too, so replay must independently reject the claim.
        audit = json_bytes({"status": "complete", "sources": manifest["sources"]})
        (execution / "acquisition.json").write_bytes(audit)
        manifest["output_sha256"]["acquisition.json"] = sha256(audit)
    elif kind in ("price", "missing_hour"):
        rows = list(
            csv.DictReader(io.StringIO((execution / "hourly_opens.csv").read_text()))
        )
        if kind == "price":
            rows[0]["open"] = "999"
        else:
            rows.pop(5)
        body = csv_bytes(execution_data.COLUMNS, rows)
        (execution / "hourly_opens.csv").write_bytes(body)
        manifest["output_sha256"]["hourly_opens.csv"] = sha256(body)
    elif kind == "audit":
        (execution / "acquisition.json").write_bytes(b"{}")
    else:
        manifest["coverage"]["complete"] = False
    (execution / "manifest.json").write_bytes(json_bytes(manifest))
    with pytest.raises(ValueError):
        execution_data.load_execution_data(execution)


def test_acquisition_stops_and_preserves_anomaly(
    tmp_path, monkeypatch, archive_download, archive_rows
):
    calls = []

    def download(request):
        calls.append(request)
        rows = archive_rows(request)
        if request.symbol == "ETHUSDT":
            rows.pop(3)
        return archive_download(request, rows)

    monkeypatch.setattr(execution_data, "download_archive", download)
    out = tmp_path / "bad"
    with pytest.raises(ValueError, match="missing"):
        execution_data.prepare_execution_data(out)
    assert len(calls) == 2
    assert not (out / "manifest.json").exists()
    audit = json.loads((out / "acquisition.json").read_bytes())
    assert audit["status"] == "failed"
    assert audit["details"]["missing_intervals"] == ["2024-01-01T03:00:00+00:00"]
    assert len(list((out / "raw").iterdir())) == 4


@pytest.fixture
def forecasts(tmp_path):
    directory = tmp_path / "forecasts"
    directory.mkdir()
    rows = []
    for symbol in SYMBOLS:
        for i in range(2195):
            opened = START - STEP + i * STEP
            for model in MODELS:
                rows.append(
                    dict(
                        zip(
                            forecast_data.COLUMNS,
                            (
                                "binance",
                                "spot",
                                symbol,
                                "14400",
                                opened.isoformat(),
                                (opened + STEP + timedelta(seconds=60)).isoformat(),
                                model,
                                "0" if model == "zero" else "0.001",
                                forecast_data.RESEARCH_SHA256,
                            ),
                            strict=True,
                        )
                    )
                )
    manifest = {
        "experiment_version": "stage-2b-v1",
        "evaluation_partition": "validation",
        "fit_partition": "train",
        "input": {
            "input_hashes": {"research.csv": forecast_data.RESEARCH_SHA256},
            "settling_seconds": 60,
        },
        "markets": {
            s: {"training_mean": 0.001, "validation_count": 2195} for s in SYMBOLS
        },
    }
    write_forecasts(directory, rows, manifest)
    return directory


def write_forecasts(directory, rows, manifest):
    body = csv_bytes(forecast_data.COLUMNS, rows)
    manifest["output_sha256"] = {"validation_predictions.csv": sha256(body)}
    (directory / "validation_predictions.csv").write_bytes(body)
    (directory / "manifest.json").write_bytes(json_bytes(manifest))


def pins(directory):
    return {
        "expected_csv_sha256": sha256(
            (directory / "validation_predictions.csv").read_bytes()
        ),
        "expected_manifest_sha256": sha256((directory / "manifest.json").read_bytes()),
    }


@pytest.mark.parametrize(
    "kind",
    [
        "hash",
        "manifest_hash",
        "schema",
        "missing",
        "duplicate",
        "order",
        "identity",
        "source",
        "time",
        "test",
        "nan",
        "zero",
        "mean",
    ],
)
def test_forecast_integrity(forecasts, kind):
    checks = pins(forecasts)
    rows = list(
        csv.DictReader(
            io.StringIO((forecasts / "validation_predictions.csv").read_text())
        )
    )
    manifest = json.loads((forecasts / "manifest.json").read_bytes())
    if kind == "manifest_hash":
        with (forecasts / "manifest.json").open("ab") as handle:
            handle.write(b" ")
    else:
        if kind == "schema":
            body = (
                (forecasts / "validation_predictions.csv")
                .read_bytes()
                .replace(b"venue,", b"exchange,", 1)
            )
            (forecasts / "validation_predictions.csv").write_bytes(body)
            manifest["output_sha256"]["validation_predictions.csv"] = sha256(body)
            (forecasts / "manifest.json").write_bytes(json_bytes(manifest))
        else:
            if kind == "missing":
                rows.pop(1)
            elif kind == "duplicate":
                rows[1] = rows[0].copy()
            elif kind == "order":
                rows[0], rows[1] = rows[1], rows[0]
            elif kind == "identity":
                rows[0]["symbol"] = "BADUSDT"
            elif kind == "source":
                rows[0]["research_csv_sha256"] = "wrong"
            elif kind == "time":
                rows[0]["feature_available_at"] = "2024-01-01T00:00:00+00:00"
            elif kind == "test":
                rows[0]["open_time"] = "2024-12-31T20:00:00+00:00"
                rows[0]["feature_available_at"] = "2025-01-01T00:01:00+00:00"
            elif kind == "nan":
                rows[0]["predicted_log_return_4h"] = "NaN"
            elif kind == "mean":
                rows[1]["predicted_log_return_4h"] = "0.02"
            else:
                rows[0]["predicted_log_return_4h"] = "0.02"
            write_forecasts(forecasts, rows, manifest)
        if kind != "hash":
            checks = pins(forecasts)
    with pytest.raises(ValueError):
        forecast_data.load_forecasts(forecasts, **checks)


def test_deterministic_offline_artifacts_preserve_inputs_and_never_open_holdout(
    forecasts,
    execution,
    tmp_path,
    monkeypatch,
):
    checks = pins(forecasts)
    original = {
        p: p.read_bytes()
        for folder in (forecasts, execution)
        for p in folder.rglob("*")
        if p.is_file()
    }
    # A sentinel Stage 2A artifact must never be opened, not even for labels/hash.
    research = tmp_path / "stage-2a"
    research.mkdir()
    (research / "research.csv").write_text("TEST LABELS MUST NEVER BE READ")
    read_bytes, read_text = Path.read_bytes, Path.read_text

    def guarded_read_bytes(path, *a, **kw):
        assert path.name != "research.csv"
        return read_bytes(path, *a, **kw)

    def guarded_read_text(path, *a, **kw):
        assert path.name != "research.csv"
        return read_text(path, *a, **kw)

    def forbidden(*a, **kw):
        pytest.fail("Offline backtest accessed network, configuration or database")

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    monkeypatch.setattr(execution_data, "download_archive", forbidden)
    monkeypatch.setattr(cli, "load_settings", forbidden)
    monkeypatch.setattr(cli, "connect_database", forbidden)
    outputs = [tmp_path / "run1", tmp_path / "run2"]
    for out in outputs:
        report = backtest.backtest_validation(forecasts, execution, out, **checks)
        assert len(report["accounts"]) == 24
        assert all(a["eligible_windows"] == 2195 for a in report["accounts"])
    for name in ("manifest.json", "summary.md", "trades.csv", "equity_curve.csv"):
        assert (outputs[0] / name).read_bytes() == (outputs[1] / name).read_bytes()
    assert all(path.read_bytes() == body for path, body in original.items())
    with pytest.raises(FileExistsError):
        backtest.backtest_validation(forecasts, execution, outputs[0], **checks)


@pytest.mark.parametrize("command", ["prepare-execution-data", "backtest-validation"])
def test_cli_offline_dispatch(command, monkeypatch, tmp_path):
    def forbidden(*a):
        pytest.fail("Stage 2C requires no application settings/database")

    monkeypatch.setattr(cli, "load_settings", forbidden)
    monkeypatch.setattr(cli, "connect_database", forbidden)
    seen = []
    if command == "prepare-execution-data":
        monkeypatch.setattr(
            execution_data, "prepare_execution_data", lambda *a: seen.append(a)
        )
        args = []
    else:
        monkeypatch.setattr(backtest, "backtest_validation", lambda *a: seen.append(a))
        args = ["--forecasts", "forecasts", "--execution", "execution"]
    assert cli.main([command, *args, "--output", str(tmp_path)]) == 0
    assert seen[0][-1] == tmp_path


@pytest.mark.parametrize(
    "error", [ValueError("Invalid reference"), FileExistsError(), OSError()]
)
@pytest.mark.parametrize("command", ["prepare-execution-data", "backtest-validation"])
def test_cli_safe_failure(command, error, monkeypatch, tmp_path):
    def fail(*a):
        raise error

    if command == "prepare-execution-data":
        monkeypatch.setattr(execution_data, "prepare_execution_data", fail)
        args = []
    else:
        monkeypatch.setattr(backtest, "backtest_validation", fail)
        args = ["--forecasts", "forecasts", "--execution", "execution"]
    assert cli.main([command, *args, "--output", str(tmp_path)]) == 1

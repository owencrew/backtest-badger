"""Synthetic fixed-schedule diagnostics; no real artifacts, network or database."""

import csv
import io
import json
from dataclasses import asdict
from datetime import timedelta
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from backtest_badger import backtest, cli, economics
from backtest_badger.backtest import ACCOUNTING, SCENARIOS, _serialise, simulate_account
from backtest_badger.execution_data import START, coverage, csv_bytes, json_bytes
from backtest_badger.forecast_data import MODELS, Signal, schedule
from backtest_badger.frozen import SYMBOLS
from backtest_badger.model_data import sha256

D = Decimal


def signals_for(hours, forecasts=None, symbol="BTCUSDT", model="ridge"):
    forecasts = forecasts or ["0.1"] * len(hours)
    return [
        Signal(
            symbol,
            model,
            START + timedelta(hours=h),
            START + timedelta(hours=h + 4, seconds=60),
            D(f),
        )
        for h, f in zip(hours, forecasts, strict=True)
    ]


def synthetic_account(
    costs, *, symbol="BTCUSDT", model="ridge", forecasts=None, sell="110"
):
    # First trade closes in January; second enters Jan 31 and exits Feb 1 00:00;
    # third closes in March. Empty months must still be retained.
    signals = signals_for([-4, 736, 1440], forecasts, symbol, model)
    prices = {
        key: value
        for s in signals
        for key, value in (
            ((symbol, schedule(s)[0]), D(100)),
            ((symbol, schedule(s)[1]), D(sell)),
        )
    }
    return simulate_account(signals, prices, costs)


@pytest.mark.parametrize("costs", SCENARIOS)
def test_cost_decomposition_months_and_compounding(costs):
    trades, equity, expected = synthetic_account(costs)
    annual, months = economics.analyse_account(trades, equity, expected, costs)
    with localcontext(ACCOUNTING):
        f, h, s = [
            v / 10000
            for v in (
                costs.fee_bps,
                costs.half_spread_bps,
                costs.slippage_bps,
            )
        ]
        # Independent closed-form expectations for these fixed synthetic prices.
        k = (1 - h - s) * (1 - f) / ((1 + h + s) * (1 + f))
        assert abs(annual["ending_equity"] - 10000 * (D("1.1") * k) ** 3) < D("1e-15")
        assert annual["total_fees"] == sum(
            t["quantity"] * f * (100 * (1 + h + s) + 110 * (1 - h - s)) for t in trades
        )
        assert annual["spread_cost"] == sum(t["quantity"] * 210 * h for t in trades)
        assert annual["slippage_cost"] == sum(t["quantity"] * 210 * s for t in trades)
        assert annual["gross_pnl"] == sum(t["quantity"] * 10 for t in trades)
        assert (
            annual["average_gross_trade_return"]
            == sum(t["quantity"] * 10 / t["cash_before"] for t in trades) / 3
        )
        assert annual["winning_trade_pct"] == 100
        assert annual["fraction_windows_invested"] == 1
        assert annual["cost_to_positive_gross"] == (
            annual["total_costs"] / annual["gross_pnl"]
        )
        assert (
            annual["two_sided_turnover_on_start"]
            == sum(t["entry_notional"] + t["exit_notional"] for t in trades) / 10000
        )
        product = D(1)
        for month in months:
            assert month["gross_pnl"] - month["total_costs"] == month["net_pnl"]
            product *= 1 + month["monthly_net_return"]
        assert abs(product - annual["ending_equity"] / 10000) < D("1e-60")
        for key in economics.TOTALS + ("trades", "eligible_windows"):
            assert abs(sum(m[key] for m in months) - annual[key]) < D("1e-60")
    assert [m["month"] for m in months] == list(economics.MONTHS)
    assert [m["trades"] for m in months] == [1, 1, 1] + [0] * 9
    assert trades[1]["entry_time"].startswith("2024-01-31")
    assert trades[1]["exit_time"] == "2024-02-01T00:00:00+00:00"
    assert months[1]["gross_pnl"] == trades[1]["gross_pnl"]
    assert months[1]["beginning_equity"] == months[0]["ending_equity"]
    assert months[-1]["monthly_net_return"] == 0


def test_scenario_gross_is_not_frictionless_gross():
    results = [
        economics.analyse_account(*synthetic_account(c), c)[0] for c in SCENARIOS
    ]
    assert results[0]["gross_pnl"] != results[1]["gross_pnl"]
    with localcontext(ACCOUNTING):
        assert (
            results[1]["gross_pnl"] - results[1]["total_costs"] == results[1]["net_pnl"]
        )
        assert (
            results[0]["gross_pnl"] - results[1]["total_costs"] != results[1]["net_pnl"]
        )
    assert (
        results[0]["frictionless_growth_factor"]
        == results[2]["frictionless_growth_factor"]
    )


@pytest.mark.parametrize(
    "ratios,status",
    [
        (["1.1", "1.2"], "nonnegative_budget"),
        (["1.1", "0.9"], "loses_without_costs"),
        (["1", "1"], "nonnegative_budget"),
        ([], "no_trades"),
    ],
)
def test_geometric_cost_budget(ratios, status):
    trades = [{"entry_reference": D(1), "exit_reference": D(r)} for r in ratios]
    result = economics.cost_budget(trades, SCENARIOS[1])
    assert result["cost_budget_status"] == status
    with localcontext(ACCOUNTING):
        growth = D(1)
        for r in ratios:
            growth *= D(r)
        assert result["frictionless_growth_factor"] == growth
        if ratios:
            geometric_bps = growth.ln() / len(ratios) * 10000
            assert abs(result["average_geometric_log_return_bps"] - geometric_bps) < D(
                "1e-60"
            )
            budget = result["max_nonnegative_round_trip_log_cost_bps"]
            if status == "nonnegative_budget":
                assert abs(budget - geometric_bps) < D("1e-60")
                # Paying precisely the log budget yields break-even growth.
                assert abs(growth * (-budget / 10000 * len(ratios)).exp() - 1) < D(
                    "1e-60"
                )
            else:
                assert budget is None
                assert result["budget_minus_actual_log_drag_bps"] is None
                assert result["frictionless_return_pct"] < 0
        else:
            assert result["average_geometric_log_return_bps"] is None
            assert result["max_nonnegative_round_trip_log_cost_bps"] is None
            assert result["analytical_ending_equity"] == 10000


def test_cost_drag_units_and_high_turnover():
    trades = [{"entry_reference": D(100), "exit_reference": D(100)}] * 1000
    base = economics.cost_budget(trades, SCENARIOS[1])
    stress = economics.cost_budget(trades, SCENARIOS[2])
    assert D("26") < base["round_trip_log_cost_drag_bps"] < D("26.001")
    assert D("25.96") < base["flat_round_trip_cost_bps"] < D("25.97")
    assert D("46") < stress["round_trip_log_cost_drag_bps"] < D("46.001")
    assert D("0.074") < base["cumulative_cost_multiplier"] < D("0.075")
    assert stress["cumulative_cost_multiplier"] < base["cumulative_cost_multiplier"]


@pytest.mark.parametrize("costs", SCENARIOS)
def test_cash_only_and_zero_trade_undefined_values(costs):
    annual, months = economics.analyse_account(
        *synthetic_account(costs, forecasts=["0"] * 3, model="zero"), costs
    )
    assert annual["ending_equity"] == 10000
    assert (
        annual["trades"] == annual["total_costs"] == annual["two_sided_notional"] == 0
    )
    assert (
        annual["fraction_windows_invested"]
        == annual["max_realised_equity_drawdown"]
        == 0
    )
    for key in (
        "average_net_trade_return",
        "average_gross_trade_return",
        "win_rate",
        "winning_trade_pct",
        "cost_per_trade",
        "cost_to_positive_gross",
        "max_nonnegative_round_trip_log_cost_bps",
    ):
        assert annual[key] is None
    assert annual["cost_budget_status"] == "no_trades"
    assert all(
        m["net_pnl"] == m["monthly_net_return"] == m["invested_windows"] == 0
        for m in months
    )


def test_independent_market_and_model_accounts():
    for symbol, model, sell, expected in (
        ("BTCUSDT", "ridge", "110", "13310"),
        ("ETHUSDT", "ridge", "90", "7290"),
        ("BTCUSDT", "gradient_boosting", "100", "10000"),
    ):
        annual, _ = economics.analyse_account(
            *synthetic_account(SCENARIOS[0], symbol=symbol, model=model, sell=sell),
            SCENARIOS[0],
        )
        assert annual["ending_equity"] == D(expected)
        assert annual["symbol"] == symbol
        assert annual["model"] == model
        if sell == "90":
            assert annual["max_realised_equity_drawdown"] == D(".271")
            assert annual["cost_budget_status"] == "loses_without_costs"


@pytest.mark.parametrize(
    "kind", ["gross", "net", "equity", "manifest", "identity", "event"]
)
def test_reconciliation_rejects_inconsistent_evidence(kind):
    trades, equity, expected = synthetic_account(SCENARIOS[0])
    if kind == "gross":
        trades[0]["gross_pnl"] += 1
    elif kind == "net":
        trades[0]["net_pnl"] += 1
    elif kind == "equity":
        equity[1]["equity"] += 1
    elif kind == "manifest":
        expected["total_fees"] += 1
    elif kind == "identity":
        trades[0]["symbol"] = "ETHUSDT"
    else:
        equity[1]["event"] = "cash_window"
    with pytest.raises(ValueError):
        economics.analyse_account(trades, equity, expected, SCENARIOS[0])


@pytest.fixture(scope="module")
def evidence(tmp_path_factory):
    directory = tmp_path_factory.mktemp("economics-evidence")
    trades, equity, accounts = [], [], []
    for symbol in SYMBOLS:
        for model in MODELS:
            signals = signals_for(
                list(range(-4, 8776, 4)),
                [
                    "0.1"
                    if model == "training_mean"
                    or (model != "zero" and i in (0, 185, 500))
                    else "0"
                    for i in range(2195)
                ],
                symbol,
                model,
            )
            prices = {
                key: value
                for s in signals
                for key, value in (
                    ((symbol, schedule(s)[0]), D(100)),
                    (
                        (symbol, schedule(s)[1]),
                        D("100.01" if symbol == "BTCUSDT" else "99.99"),
                    ),
                )
            }
            for costs in SCENARIOS:
                ts, es, account = simulate_account(signals, prices, costs)
                trades.extend(ts)
                equity.extend(es)
                accounts.append(account)
    files = {
        "trades.csv": csv_bytes(backtest.TRADE_COLUMNS, trades),
        "equity_curve.csv": csv_bytes(backtest.EQUITY_COLUMNS, equity),
        "summary.md": b"Synthetic retained historical simulation\n",
    }
    manifest = _serialise(
        {
            "backtest_version": "stage-2c-v1",
            "kind": "historical simulation",
            "partition": "2024 validation only",
            "starting_cash_usdt": D(10000),
            "scenarios": [asdict(c) for c in SCENARIOS],
            "forecast_hashes": {
                "manifest.json": economics.FORECAST_MANIFEST_SHA256,
                "validation_predictions.csv": economics.FORECAST_CSV_SHA256,
            },
            "execution": {
                "manifest_sha256": economics.EXECUTION_MANIFEST_SHA256,
                "coverage": coverage(),
            },
            "implementation_sha256": {},
            "policy": "synthetic fixed schedule",
            "accounting": "synthetic Decimal account",
            "accounts": accounts,
            "output_sha256": {name: sha256(body) for name, body in files.items()},
        }
    )
    files["manifest.json"] = json_bytes(manifest)
    for name, body in files.items():
        (directory / name).write_bytes(body)
    return directory


def pin(directory):
    return {
        "expected_manifest_sha256": sha256((directory / "manifest.json").read_bytes())
    }


@pytest.mark.parametrize(
    "kind",
    [
        "pin",
        "hash",
        "schema",
        "nan",
        "partition",
        "scenarios",
        "provenance",
        "execution",
        "missing_equity",
        "duplicate_trade",
        "trade_time",
        "scenario_schedule",
        "account_order",
        "extra_account",
        "summary_hash",
    ],
)
def test_input_integrity_and_provenance(evidence, tmp_path, kind):
    for p in evidence.iterdir():
        (tmp_path / p.name).write_bytes(p.read_bytes())
    checks = pin(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_bytes())
    if kind == "pin":
        (tmp_path / "manifest.json").write_bytes(b"{}")
    elif kind == "hash":
        with (tmp_path / "trades.csv").open("ab") as f:
            f.write(b"\n")
    elif kind == "summary_hash":
        (tmp_path / "summary.md").write_text("changed")
    else:
        if kind in (
            "schema",
            "nan",
            "duplicate_trade",
            "trade_time",
            "scenario_schedule",
        ):
            name = "trades.csv"
            rows = list(csv.DictReader(io.StringIO((tmp_path / name).read_text())))
            if kind == "nan":
                rows[0]["quantity"] = "NaN"
            elif kind == "duplicate_trade":
                rows.insert(0, rows[0].copy())
            elif kind == "trade_time":
                rows[0]["entry_time"] = "2025-01-01T01:00:00+00:00"
            elif kind == "scenario_schedule":
                rows[0]["entry_reference"] = "101"
            body = csv_bytes(backtest.TRADE_COLUMNS, rows)
            if kind == "schema":
                body = body.replace(b"symbol,", b"unknown,", 1)
            (tmp_path / name).write_bytes(body)
            manifest["output_sha256"][name] = sha256(body)
        elif kind == "missing_equity":
            name = "equity_curve.csv"
            body = (tmp_path / name).read_bytes().splitlines(keepends=True)
            body = b"".join(body[:-1])
            (tmp_path / name).write_bytes(body)
            manifest["output_sha256"][name] = sha256(body)
        elif kind == "partition":
            manifest["partition"] = "test"
        elif kind == "scenarios":
            manifest["scenarios"][1]["fee_bps"] = "0"
        elif kind == "provenance":
            manifest["forecast_hashes"]["manifest.json"] = "0" * 64
        elif kind == "execution":
            manifest["execution"]["coverage"]["start"] = "2025-01-01T00:00:00+00:00"
        elif kind == "account_order":
            manifest["accounts"].reverse()
        else:
            manifest["accounts"].append(manifest["accounts"][0])
        (tmp_path / "manifest.json").write_bytes(json_bytes(manifest))
        checks = pin(tmp_path)
    destination = tmp_path / "out"
    with pytest.raises(ValueError):
        economics.analyse_economics(tmp_path, destination, **checks)
    assert not destination.exists()


def test_deterministic_offline_artifacts(evidence, tmp_path, monkeypatch):
    original = {p: p.read_bytes() for p in evidence.iterdir()}
    read_bytes = Path.read_bytes

    def guard(path):
        assert path.name not in (
            "research.csv",
            "validation_predictions.csv",
            "hourly_opens.csv",
        )
        return read_bytes(path)

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Analysis must not simulate, fit, access network, config or database"
        )

    monkeypatch.setattr(Path, "read_bytes", guard)
    monkeypatch.setattr(backtest, "simulate_account", forbidden)
    monkeypatch.setattr(cli, "load_settings", forbidden)
    monkeypatch.setattr(cli, "connect_database", forbidden)
    import socket

    monkeypatch.setattr(socket, "create_connection", forbidden)
    reports = [
        economics.analyse_economics(evidence, tmp_path / name, **pin(evidence))
        for name in ("one", "two")
    ]
    assert reports[0] == reports[1]
    assert len(reports[0]["accounts"]) == 24
    for name in (
        "manifest.json",
        "summary.md",
        "monthly_results.csv",
        "cost_diagnostics.csv",
    ):
        body = (tmp_path / "one" / name).read_bytes()
        assert body == (tmp_path / "two" / name).read_bytes()
        if name != "manifest.json":
            assert sha256(body) == reports[0]["output_sha256"][name]
    assert (
        len(list(csv.DictReader((tmp_path / "one" / "monthly_results.csv").open())))
        == 288
    )
    assert all(p.read_bytes() == body for p, body in original.items())
    with pytest.raises(FileExistsError):
        economics.analyse_economics(evidence, tmp_path / "one", **pin(evidence))
    # The real CLI pin must reject an otherwise valid synthetic artifact.
    assert (
        cli.main(
            [
                "analyse-economics",
                "--backtest",
                str(evidence),
                "--output",
                str(tmp_path / "wrong-pin"),
            ]
        )
        == 1
    )


def test_cli_offline_dispatch(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(economics, "analyse_economics", lambda *a: seen.append(a))
    monkeypatch.setattr(cli, "load_settings", lambda: pytest.fail("settings read"))
    monkeypatch.setattr(cli, "connect_database", lambda: pytest.fail("database read"))
    assert (
        cli.main(
            ["analyse-economics", "--backtest", "input", "--output", str(tmp_path)]
        )
        == 0
    )
    assert seen == [(Path("input"), tmp_path)]


@pytest.mark.parametrize("error", [ValueError("invalid"), FileExistsError(), OSError()])
def test_cli_safe_failure(monkeypatch, tmp_path, error):
    def fail(*args):
        raise error

    monkeypatch.setattr(economics, "analyse_economics", fail)
    assert (
        cli.main(
            ["analyse-economics", "--backtest", "input", "--output", str(tmp_path)]
        )
        == 1
    )

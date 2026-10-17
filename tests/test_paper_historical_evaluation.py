"""Full fabricated 2024 grids. Mock published pins are NOT real authentication."""

import calendar
import copy
import io
import json
from dataclasses import replace
from datetime import timedelta
from decimal import ROUND_DOWN, Inexact, localcontext
from hashlib import sha256
from pathlib import Path
from unittest.mock import Mock

import pytest

from backtest_badger import execution_data, forecast_data, model_data
from backtest_badger import paper_historical_evaluation as evaluation
from backtest_badger import paper_historical_publication as publication
from backtest_badger.forecast_data import Signal
from backtest_badger.paper_accounting import apply_trade, fee_for, replay
from backtest_badger.paper_historical import (
    END,
    HOUR,
    START,
    HistoricalForecast,
    HourlyReference,
    replay_historical,
    value_historical,
)
from backtest_badger.paper_types import STEP, D, Side, money_context

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline_boundary(monkeypatch):
    """Any source loading or real artifact file access is a test failure."""

    def forbidden(*args, **kwargs):
        pytest.fail("No actual source loaders, provider or database in Stage 4B.2B")

    monkeypatch.setattr(forecast_data, "load_forecasts", forbidden)
    monkeypatch.setattr(execution_data, "load_execution_data", forbidden)
    monkeypatch.setattr(model_data, "load_model_data", forbidden)
    import socket

    import psycopg

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(psycopg, "connect", forbidden)
    original = io.open

    def guarded(file, *args, **kwargs):
        if isinstance(file, (str, Path)):
            assert not Path(file).absolute().is_relative_to(ROOT / "artifacts")
        return original(file, *args, **kwargs)

    monkeypatch.setattr(io, "open", guarded)


def reseal(forecast, execution, evidence):
    evidence["loader_snapshot_sha256"] = evaluation.loader_snapshot_sha256(
        forecast, execution, evidence["stage2b_manifest"]
    )


def fabricated_inputs():
    hashes = {
        "manifest.json": evaluation.RECIPE_SHA256,
        "validation_predictions.csv": evaluation.FORECAST_SHA256,
    }
    accounts, prices, sources, markets = {}, {}, [], {}
    for symbol, count in zip(evaluation.SYMBOLS, (13782, 13783), strict=True):
        for model in evaluation.MODELS:
            accounts[symbol, model] = [
                Signal(
                    symbol,
                    model,
                    START - STEP + i * STEP,
                    START + i * STEP + timedelta(seconds=60),
                    # Buy, HOLD, exit, cash, re-enter and hold until year end.
                    D(-1 if i in (2, 3) else 1) if model == "ridge" else D(0),
                )
                for i in range(2195)
            ]
        for i in range(8784):
            at = START + i * HOUR
            # Deliberately fabricated declining month levels; all months retained.
            prices[symbol, at] = D(
                110 - at.month if symbol == "BTCUSDT" else 210 - at.month
            )
        for month in range(1, 13):
            name = f"2024-{month:02d}"
            url = (
                "https://data.binance.vision/data/spot/monthly/klines/"
                f"{symbol}/1h/{symbol}-1h-{name}.zip"
            )
            sources.append(
                {
                    "symbol": symbol,
                    "interval": "1h",
                    "month": name,
                    "url": url,
                    "checksum_url": url + ".CHECKSUM",
                    "sha256": evaluation.MONTHLY_ZIP_SHA256[symbol, name],
                    "checksum_sha256": sha256(
                        f"mock-sidecar:{symbol}:{name}".encode()
                    ).hexdigest(),
                    "observed_at": "2026-10-14T00:00:00+00:00",
                    "row_count": calendar.monthrange(2024, month)[1] * 24,
                    "checksum_valid": True,
                    "complete": True,
                }
            )
        markets[symbol] = {
            "training_count": count,
            "validation_count": 2195,
            "model_parameters": {
                "ridge": {
                    "alpha": 1.0,
                    "copy_X": True,
                    "fit_intercept": True,
                    "max_iter": None,
                    "positive": False,
                    "random_state": None,
                    "solver": "svd",
                    "tol": 0.0001,
                },
                "ridge_scaler": {"copy": True, "with_mean": True, "with_std": True},
            },
            "fitted_scaler": {
                "mean": [0.0] * 5,
                "scale": [1.0] * 5,
                "n_samples_seen": count,
            },
        }
    metadata = {
        "manifest_sha256": evaluation.HOURLY_MANIFEST_SHA256,
        "output_sha256": {
            "hourly_opens.csv": evaluation.HOURLY_SHA256,
            "acquisition.json": evaluation.ACQUISITION_SHA256,
        },
        "coverage": execution_data.coverage(),
        "sources": sources,
    }
    evidence = {
        "status": "synthetic_test",
        "protocol_version": evaluation.PROTOCOL_VERSION,
        "protocol_sha256": evaluation.PROTOCOL_SHA256,
        "protocol_git_revision": evaluation.PROTOCOL_REVISION,
        "source_paths": dict(evaluation.SOURCE_PATHS),
        "recipe_identity_kind": "stage2b_manifest_sha256",
        "model_recipe_sha256": evaluation.RECIPE_SHA256,
        "stage2b_manifest": {
            "experiment_version": "stage-2b-v1",
            "fit_partition": "train",
            "evaluation_partition": "validation",
            "feature_order": list(evaluation.FEATURES),
            "input": {
                "settling_seconds": 60,
                "input_hashes": {
                    "research.csv": evaluation.RESEARCH_SHA256,
                    "manifest.json": evaluation.RESEARCH_MANIFEST_SHA256,
                },
            },
            "output_sha256": {"validation_predictions.csv": evaluation.FORECAST_SHA256},
            "markets": markets,
        },
    }
    forecast, execution = (hashes, accounts), (metadata, prices)
    reseal(forecast, execution, evidence)
    # Mock call result shapes, never actual artifact loaders.
    return Mock(return_value=forecast)(), Mock(return_value=execution)(), evidence


@pytest.fixture(scope="module")
def inputs():
    return fabricated_inputs()


@pytest.fixture(scope="module")
def report(inputs):
    forecast, execution, evidence = inputs
    return evaluation.evaluate_bundle(
        evaluation.adapt_inputs(forecast, execution, evidence=evidence)
    )


def test_full_synthetic_accounts_counts_lifecycle_and_exact_replay(report):
    assert len(report["orders_trades"]) == 6
    for symbol in evaluation.SYMBOLS:
        reports = report["summary"]["markets"][symbol]
        r = reports["ridge"]
        assert r["decision_count"] == 2195
        assert r["targets"] == {"long": 2193, "cash": 2}
        assert r["decisions_by_action"]["HOLD"] == 2191
        assert r["decisions_by_action"]["CASH_NOOP"] == 1
        assert r["final"]["asset_units"] > 0
        assert r["reconciliation"] == {
            "funding_events": 1,
            "fill_count": 3,
            "signed_postings": 6,
            "last_ledger_seq": 7,
            "replayed_hourly_marks": 8784,
            "reconciled": True,
        }
        for label in ("ridge", "cash", "buy_and_hold"):
            key = reports[label]["account_id"]
            data, marks = report["orders_trades"][key], report["hourly_marks"][key]
            assert data["initial"].cash == D(10000)
            assert data["initial"].portfolio.key == key
            assert len(marks) == 8784 and marks[-1].reference.at == END - HOUR
            assert replay(data["initial"].portfolio, data["trades"]) == data["final"]
            prefixes = {1: data["initial"]}
            account = data["initial"]
            for trade in data["trades"]:
                account = apply_trade(account, trade)
                prefixes[account.ledger_seq] = account
            for mark in marks:
                assert (
                    value_historical(
                        prefixes[mark.ledger_seq],
                        mark.reference,
                        ledger_seq=mark.ledger_seq,
                    )
                    == mark
                )
            assert len(report["ledger"][key]) == data["final"].ledger_seq
            assert (
                len([p for p in report["ledger"][key] if p["event"] == "funding"]) == 1
            )
        ridge_trades = report["orders_trades"][r["account_id"]]["trades"]
        assert [t.at for t in ridge_trades] == [START + n * HOUR for n in (1, 9, 17)]
        for fill in report["orders_trades"][r["account_id"]]["ridge_order_fills"]:
            assert fill.reference.at - fill.order.decision.at == timedelta(minutes=59)
            assert fill.trade.at == fill.reference.at
            assert len(fill.trade.postings) == 2
        b = reports["buy_and_hold"]
        buy = report["orders_trades"][b["account_id"]]["trades"][0]
        assert (
            buy.at == START and buy.portfolio.strategy_id == "analytical_buy_and_hold"
        )
        assert b["ending_exposed"] and b["exposure_fraction"] == 1
        assert report["decisions"][b["account_id"]] == ()
        cash = reports["cash"]
        assert cash["final"]["cash"] == 10000 and cash["total_return"] == 0
        assert cash["final"]["weighted_average_cost"] is None
        assert cash["costs_by_side"]["BUY"]["fees"] == 0


def test_cost_affordability_and_signed_postings(report):
    with localcontext(money_context()):
        for key, data in report["orders_trades"].items():
            account = data["initial"]
            references = {
                m.reference.at: m.reference for m in report["hourly_marks"][key]
            }
            for trade in data["trades"]:
                assert trade.fee == fee_for(trade.notional)
                ref = references[trade.at]
                assert trade.price == ref.price * (
                    D("1.0003") if trade.side == Side.BUY else D("0.9997")
                )
                if trade.side == Side.BUY:
                    assert trade.quantity % D("0.000001") == 0
                    assert trade.notional + trade.fee <= account.cash
                    larger = (trade.quantity + D("0.000001")) * trade.price
                    assert larger + fee_for(larger) > account.cash
                    assert trade.postings[0].amount == -(trade.notional + trade.fee)
                    assert trade.postings[1].amount == trade.quantity
                else:
                    assert trade.quantity == account.quantity
                    assert trade.postings[0].amount == trade.notional - trade.fee
                    assert trade.postings[1].amount == -trade.quantity
                account = apply_trade(account, trade)
            symbol = account.portfolio.symbol
            costs = report["summary"]["markets"][symbol][data["label"]]["costs_by_side"]
            assert sum(c["fees"] for c in costs.values()) == account.fees
            for side in Side:
                selected = [t for t in data["trades"] if t.side == side]
                assert costs[side]["hypothetical_half_spread"] == sum(
                    (
                        t.quantity * references[t.at].price * D("0.0001")
                        for t in selected
                    ),
                    D(0),
                )
                assert (
                    costs[side]["hypothetical_slippage"]
                    == 2 * costs[side]["hypothetical_half_spread"]
                )


def test_all_calendar_periods_leap_day_loss_and_final_partial(report):
    for key in report["orders_trades"]:
        rows = [r for r in report["daily_monthly"] if r["account_id"] == key]
        daily = [r for r in rows if r["period"] == "daily"]
        monthly = [r for r in rows if r["period"] == "monthly"]
        assert len(daily) == 366 and len(monthly) == 12
        assert sum(r["complete"] for r in daily) == 365
        leap = next(r for r in daily if r["start"] == START.replace(month=2, day=29))
        assert (
            leap["end"] == START.replace(month=3) and leap["observed_seconds"] == 86400
        )
        assert monthly[1]["end"] - monthly[1]["start"] == timedelta(days=29)
        assert daily[-1]["observed_seconds"] == 23 * 3600
        assert not daily[-1]["complete"] and not monthly[-1]["complete"]
        assert monthly[-1]["missing_boundary_seconds"] == 3600
        assert daily[-1]["end"] == monthly[-1]["end"] == END - HOUR
        if report["orders_trades"][key]["label"] != "cash":
            assert any(r["pnl"] < 0 for r in monthly)
        for side in ("buy", "sell"):
            for field in (
                "count",
                "notional",
                "fees",
                "hypothetical_half_spread",
                "hypothetical_slippage",
            ):
                assert sum(r[f"{side}_{field}"] for r in daily) == sum(
                    r[f"{side}_{field}"] for r in monthly
                )


def test_drawdown_duration_comparisons_and_benchmark_first_mark(report):
    with localcontext(money_context()):
        for symbol in evaluation.SYMBOLS:
            reports = report["summary"]["markets"][symbol]
            for label in ("ridge", "cash", "buy_and_hold"):
                row = reports[label]
                marks = report["hourly_marks"][row["account_id"]]
                equity = [D(10000)] + [m.equity for m in marks]
                peak, dd = D(10000), D(0)
                for value in equity:
                    peak = max(peak, value)
                    dd = max(dd, evaluation.ratio(peak - value, peak))
                assert row["maximum_observed_hourly_drawdown"] == dd
                assert (
                    row["pnl"]
                    == row["final"]["realised_pnl"] + row["final"]["unrealised_pnl"]
                )
            r, b = reports["ridge"], reports["buy_and_hold"]
            assert r["exposure_seconds"] == (8784 - 9) * 3600
            assert r["invested_hourly_marks"] == 8784 - 9
            assert b["first_hourly_mark"]["reference_marked_equity"] < 10000
            comparison = reports["comparisons"]["buy_and_hold"]
            assert (
                comparison["return_difference_initial_funding"]
                == r["total_return"] - b["total_return"]
            )
            assert (
                comparison["benchmark_endpoint_denominator"]
                == b["final"]["reference_marked_equity"]
            )
            assert comparison["common_hourly_marks"] == 8784


BAD_CASES = (
    "forecast_csv",
    "forecast_manifest",
    "hourly_csv",
    "hourly_manifest",
    "acquisition",
    "protocol",
    "protocol_version",
    "protocol_revision",
    "recipe",
    "recipe_kind",
    "real_status",
    "market",
    "model",
    "missing_horizon",
    "duplicate_horizon",
    "reordered_horizon",
    "availability",
    "missing_hour",
    "reordered_hour",
    "extra_hour",
    "cross_market_hour",
    "offgrid_hour",
    "price_mutation",
    "zero_price",
    "nan_price",
    "float_price",
    "nan_forecast",
    "source_missing",
    "source_duplicate",
    "zip_swap",
    "wrong_month",
    "source_url",
    "checksum_url",
    "checksum_hash",
    "checksum_duplicate",
    "acquisition_time",
    "source_count",
    "source_incomplete",
    "coverage",
    "features",
    "ridge_parameters",
    "scaler_parameters",
    "scaler_count",
    "scaler_scale",
    "lineage_market",
    "lineage_mutation",
    "research_pin",
    "source_path",
)


def mutate(case, forecast, execution, evidence):
    hashes, accounts = forecast
    metadata, prices = execution
    signal = accounts["BTCUSDT", "ridge"][0]
    sources = metadata["sources"]
    lineage = evidence["stage2b_manifest"]
    market = lineage["markets"]["BTCUSDT"]
    if case == "forecast_csv":
        hashes["validation_predictions.csv"] = "a" * 64
    elif case == "forecast_manifest":
        hashes["manifest.json"] = "a" * 64
    elif case == "hourly_manifest":
        metadata["manifest_sha256"] = "a" * 64
    elif case == "hourly_csv":
        metadata["output_sha256"]["hourly_opens.csv"] = "a" * 64
    elif case == "acquisition":
        metadata["output_sha256"]["acquisition.json"] = "a" * 64
    elif case == "protocol":
        evidence["protocol_sha256"] = "a" * 64
    elif case == "protocol_version":
        evidence["protocol_version"] = "other"
    elif case == "protocol_revision":
        evidence["protocol_git_revision"] = "a" * 40
    elif case == "recipe":
        evidence["model_recipe_sha256"] = "a" * 64
    elif case == "recipe_kind":
        evidence["recipe_identity_kind"] = "coefficients"
    elif case == "real_status":
        evidence["status"] = "real"
    elif case == "market":
        accounts["BTCUSDT", "ridge"][0] = replace(signal, symbol="ETHUSDT")
    elif case == "model":
        accounts["BTCUSDT", "ridge"][0] = replace(signal, model="zero")
    elif case == "missing_horizon":
        accounts["BTCUSDT", "ridge"].pop()
    elif case == "duplicate_horizon":
        accounts["BTCUSDT", "ridge"][1] = signal
    elif case == "reordered_horizon":
        accounts["BTCUSDT", "ridge"].reverse()
    elif case == "availability":
        accounts["BTCUSDT", "ridge"][0] = replace(signal, signal_time=START)
    elif case == "missing_hour":
        prices.pop(("BTCUSDT", START))
    elif case == "reordered_hour":
        prices["BTCUSDT", START] = prices.pop(("BTCUSDT", START))
    elif case == "extra_hour":
        prices["BTCUSDT", END] = D(100)
    elif case == "cross_market_hour":
        prices["BAD", START] = prices.pop(("BTCUSDT", START))
    elif case == "offgrid_hour":
        prices["BTCUSDT", START + timedelta(minutes=1)] = prices.pop(("BTCUSDT", START))
    elif case == "price_mutation":
        prices["BTCUSDT", START] = D(123)
    elif case == "zero_price":
        prices["BTCUSDT", START] = D(0)
    elif case == "nan_price":
        prices["BTCUSDT", START] = D("NaN")
    elif case == "float_price":
        prices["BTCUSDT", START] = 100.0
    elif case == "nan_forecast":
        accounts["BTCUSDT", "ridge"][0] = replace(signal, forecast=D("NaN"))
    elif case == "source_missing":
        sources.pop()
    elif case == "source_duplicate":
        sources[-1] = sources[0]
    elif case == "zip_swap":
        sources[0]["sha256"] = sources[1]["sha256"]
    elif case == "wrong_month":
        sources[0]["month"] = "2023-12"
    elif case == "source_url":
        sources[0]["url"] = sources[1]["url"]
    elif case == "checksum_url":
        sources[0]["checksum_url"] = sources[1]["checksum_url"]
    elif case == "checksum_hash":
        sources[0]["checksum_sha256"] = "broken"
    elif case == "checksum_duplicate":
        sources[0]["checksum_sha256"] = sources[1]["checksum_sha256"]
    elif case == "acquisition_time":
        sources[0]["observed_at"] = START.isoformat()
    elif case == "source_count":
        sources[0]["row_count"] = 743
    elif case == "source_incomplete":
        sources[0]["complete"] = False
    elif case == "coverage":
        metadata["coverage"]["missing"] = 1
    elif case == "features":
        lineage["feature_order"].reverse()
    elif case == "ridge_parameters":
        market["model_parameters"]["ridge"]["alpha"] = 2.0
    elif case == "scaler_parameters":
        market["model_parameters"]["ridge_scaler"]["with_mean"] = False
    elif case == "scaler_count":
        market["fitted_scaler"]["n_samples_seen"] = 2195
    elif case == "scaler_scale":
        market["fitted_scaler"]["scale"][0] = 0
    elif case == "lineage_market":
        lineage["markets"].pop("ETHUSDT")
    elif case == "lineage_mutation":
        market["fitted_scaler"]["mean"][0] = 1.0
    elif case == "research_pin":
        lineage["input"]["input_hashes"]["research.csv"] = "a" * 64
    elif case == "source_path":
        evidence["source_paths"]["predictions"] = "other"
    else:
        raise AssertionError(case)


@pytest.mark.parametrize("case", BAD_CASES)
def test_bad_evidence_has_no_successful_manifest(case, inputs, tmp_path):
    forecast, execution, evidence = copy.deepcopy(inputs)
    mutate(case, forecast, execution, evidence)
    destination = tmp_path / "failed"
    with pytest.raises(ValueError):
        publication.publish_synthetic(
            destination, forecast, execution, evidence=evidence, temporary_root=tmp_path
        )
    assert not (destination / "manifest.json").exists()
    assert json.loads((destination / "failure.json").read_bytes())["resume"] is False


def test_stable_source_identities_and_mock_lineage(inputs):
    forecast, execution, evidence = inputs
    bundle = evaluation.adapt_inputs(forecast, execution, evidence=evidence)
    for i, symbol in enumerate(evaluation.SYMBOLS):
        assert len(bundle.forecasts[i]) == 2195
        for ref in bundle.references[i]:
            assert ref.record_id == f"binance:spot:{symbol}:3600:{ref.at.isoformat()}"
            assert ref.file_sha256 == evaluation.HOURLY_SHA256
            assert (
                ref.source_sha256
                == evaluation.MONTHLY_ZIP_SHA256[symbol, ref.at.strftime("%Y-%m")]
            )
        assert bundle.forecasts[i][0].record_id.endswith(":ridge")
    retained = json.loads(bundle.source_evidence_json)
    assert (
        retained["authentication"]
        == "mocked_identifiers_not_genuine_file_authentication"
    )
    assert retained["recipe_identity_kind"] == "stage2b_manifest_sha256"
    assert len(retained["execution_metadata"]["sources"]) == 24


def short_result():
    forecasts = [
        HistoricalForecast(
            "BTCUSDT",
            f"fixture-{i}",
            START - STEP + i * STEP,
            START + i * STEP + timedelta(seconds=60),
            D(value),
            evaluation.FORECAST_SHA256,
        )
        for i, value in enumerate((1, 1, -1, -1, 1, 1))
    ]
    refs = [
        HourlyReference(
            "BTCUSDT",
            f"ref-{i}",
            START + i * HOUR,
            D(100 if i < 10 else 80),
            evaluation.HOURLY_SHA256,
            "a" * 64,
        )
        for i in range(24)
    ]
    return replay_historical(
        "BTCUSDT",
        forecasts,
        refs,
        protocol_sha256=evaluation.PROTOCOL_SHA256,
        model_recipe_sha256=evaluation.RECIPE_SHA256,
        end_exclusive=START + timedelta(days=1),
    )


def test_short_fixture_undefined_daily_and_benchmark_infeasible():
    result = short_result()
    summary, periods = evaluation.summarize_account(
        result.initial_account,
        tuple(f.trade for f in result.fills),
        result.marks,
        result.final_account,
        decisions=result.decisions,
        end=result.end_exclusive,
    )
    assert summary["complete_day_count"] == 0
    assert summary["complete_day_mean_return"] is None
    assert periods[0]["observed_seconds"] == 23 * 3600
    ref = replace(result.marks[0].reference, price=D("1e20"))
    b = evaluation.benchmark("BTCUSDT", "buy_and_hold", [ref])
    assert b.status == "unavailable" and b.trades == () and b.marks == ()
    assert b.initial == b.final and b.final.cash == 10000


def test_mark_and_ledger_tampering_detected():
    result = short_result()
    trades = tuple(f.trade for f in result.fills)
    marks = list(result.marks)
    marks[2] = replace(marks[2], equity=D(99999))
    with pytest.raises(ValueError, match="mark replay"):
        evaluation.verify_account(
            result.initial_account, trades, marks, result.final_account
        )
    with pytest.raises(ValueError):
        evaluation.verify_account(
            result.initial_account, trades[::-1], result.marks, result.final_account
        )
    marks = list(result.marks)
    marks[1] = marks[0]
    with pytest.raises(ValueError):
        evaluation.verify_account(
            result.initial_account, trades, marks, result.final_account
        )


def test_source_container_order_and_decimal_context_determinism(inputs, report):
    forecast, execution, evidence = copy.deepcopy(inputs)
    forecast = (
        dict(reversed(list(forecast[0].items()))),
        dict(reversed(list(forecast[1].items()))),
    )
    metadata, prices = execution
    metadata["sources"].reverse()
    # Reverse independent market groups, retain chronological evidence within each.
    prices = {
        key: value
        for s in reversed(evaluation.SYMBOLS)
        for key, value in prices.items()
        if key[0] == s
    }
    expected = evaluation.scientific_payloads(report)
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        actual = evaluation.scientific_payloads(
            evaluation.evaluate_bundle(
                evaluation.adapt_inputs(forecast, (metadata, prices), evidence=evidence)
            )
        )
    assert actual == expected


def test_protocol_pin_matches_unchanged_document():
    body = (ROOT / "docs/stage-04b2-historical-validation-protocol.md").read_bytes()
    assert sha256(body).hexdigest() == evaluation.PROTOCOL_SHA256


@pytest.fixture(scope="module")
def published(inputs, tmp_path_factory):
    root = tmp_path_factory.mktemp("historical-synthetic-publication")
    forecast, execution, evidence = inputs
    a, b = root / "one", root / "two"
    first = publication.publish_synthetic(
        a, forecast, execution, evidence=evidence, temporary_root=root
    )
    with localcontext() as context:
        context.prec = 4
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        second = publication.publish_synthetic(
            b, forecast, execution, evidence=evidence, temporary_root=root
        )
    return root, a, b, first, second


def test_two_publications_exact_bytes_manifest_and_replay(published):
    root, a, b, first, second = published
    assert first == second
    assert {p.name for p in a.iterdir()} == {*publication.FILES, "manifest.json"}
    for name in (*publication.FILES, "manifest.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
    manifest = publication.verify_publication(
        a, temporary_root=root, expected_manifest_sha256=first
    )
    assert manifest["status"] == "synthetic_test"
    assert manifest["coverage"]["actual_forecasts"] == {
        s: 2195 for s in evaluation.SYMBOLS
    }
    assert manifest["coverage"]["actual_hours"] == {s: 8784 for s in evaluation.SYMBOLS}
    assert set(manifest["provenance"]["source_sha256"]) == set(
        publication.IMPLEMENTATIONS
    )
    body = (a / "manifest.json").read_text()
    assert str(root) not in body
    assert "published_at" not in body


@pytest.mark.parametrize("existing", ("empty", "file", "published", "symlink"))
def test_exclusive_directory_and_no_overwrite(existing, inputs, tmp_path, published):
    root, a, _, first, _ = published
    destination = tmp_path / "existing"
    if existing == "empty":
        destination.mkdir()
    elif existing == "file":
        destination.write_bytes(b"preserve")
    elif existing == "symlink":
        destination.symlink_to(a)
    else:
        destination, tmp_path = a, root
    forecast, execution, evidence = inputs
    with pytest.raises((FileExistsError, ValueError)):
        publication.publish_synthetic(
            destination, forecast, execution, evidence=evidence, temporary_root=tmp_path
        )
    assert sha256((a / "manifest.json").read_bytes()).hexdigest() == first


@pytest.mark.parametrize("name", publication.FILES)
def test_altered_or_missing_output_fails(name, published, tmp_path):
    root, a, _, digest, _ = published
    # Hard links avoid copying large fixtures; unlink/replace only the test copy.
    import os

    target = tmp_path / "damaged"
    target.mkdir()
    for original in a.iterdir():
        os.link(original, target / original.name)
    (target / name).unlink()
    with pytest.raises(FileNotFoundError):
        publication.verify_publication(
            target, temporary_root=tmp_path, expected_manifest_sha256=digest
        )
    (target / name).write_bytes(b"altered\n")
    with pytest.raises(ValueError):
        publication.verify_publication(
            target, temporary_root=tmp_path, expected_manifest_sha256=digest
        )


@pytest.mark.parametrize("fail_at", ("ledger.json", "manifest.json"))
def test_manifest_last_write_failure_and_no_resume(
    fail_at, inputs, tmp_path, monkeypatch, report
):
    forecast, execution, evidence = inputs
    # Evaluation is tested end to end elsewhere; isolate publisher interruption.
    monkeypatch.setattr(publication, "evaluate_bundle", lambda _: report)
    write = publication._write_exclusive
    calls = []

    def interrupted(path, body):
        calls.append(path.name)
        assert not (path.parent / "manifest.json").exists()
        if path.name == fail_at:
            path.with_name(path.name + ".partial").write_bytes(body[:50])
            raise OSError("simulated interruption")
        write(path, body)

    monkeypatch.setattr(publication, "_write_exclusive", interrupted)
    destination = tmp_path / "failed"
    with pytest.raises(OSError):
        publication.publish_synthetic(
            destination, forecast, execution, evidence=evidence, temporary_root=tmp_path
        )
    assert not (destination / "manifest.json").exists()
    assert (destination / "failure.json").exists()
    assert (destination / (fail_at + ".partial")).exists()
    with pytest.raises(FileExistsError):
        publication.publish_synthetic(
            destination, forecast, execution, evidence=evidence, temporary_root=tmp_path
        )
    if fail_at == "manifest.json":
        assert calls[:-1] == [*publication.FILES, "manifest.json"]


def test_refuse_non_temporary_or_artifact_destination(inputs, tmp_path):
    forecast, execution, evidence = inputs
    for root, destination in (
        (ROOT, ROOT / "forbidden-output"),
        (tmp_path, tmp_path / "artifacts"),
    ):
        with pytest.raises(ValueError):
            publication.publish_synthetic(
                destination, forecast, execution, evidence=evidence, temporary_root=root
            )
        assert not destination.exists()


@pytest.mark.parametrize(
    "case",
    (
        "zip_swap",
        "source_url",
        "source_count",
        "features",
        "ridge_parameters",
        "scaler_count",
        "reordered_hour",
        "duplicate_horizon",
        "market",
        "model",
    ),
)
def test_structure_validation_is_not_only_snapshot_checksum(case, inputs):
    forecast, execution, evidence = copy.deepcopy(inputs)
    mutate(case, forecast, execution, evidence)
    reseal(forecast, execution, evidence)
    with pytest.raises(ValueError):
        evaluation.adapt_inputs(forecast, execution, evidence=evidence)


def test_modified_adapted_bundle_rejected(inputs):
    forecast, execution, evidence = inputs
    bundle = evaluation.adapt_inputs(forecast, execution, evidence=evidence)
    refs = list(bundle.references[0])
    refs[1] = replace(refs[1], price=D(999))
    altered = replace(bundle, references=(tuple(refs), bundle.references[1]))
    with pytest.raises(ValueError, match="changed after source"):
        evaluation.evaluate_bundle(altered)


def test_external_manifest_identity_and_symlinks(published, tmp_path):
    import os

    root, a, _, identity, _ = published
    with pytest.raises(ValueError, match="Manifest identity"):
        publication.verify_publication(
            a, temporary_root=root, expected_manifest_sha256="a" * 64
        )
    target = tmp_path / "links"
    target.mkdir()
    for original in a.iterdir():
        os.link(original, target / original.name)
    (target / "manifest.json").unlink()
    (target / "manifest.json").symlink_to(a / "manifest.json")
    with pytest.raises(ValueError, match="Symlink manifest"):
        publication.verify_publication(
            target, temporary_root=tmp_path, expected_manifest_sha256=identity
        )
    (target / "manifest.json").unlink()
    os.link(a / "manifest.json", target / "manifest.json")
    (target / "ledger.json").unlink()
    (target / "ledger.json").symlink_to(a / "ledger.json")
    with pytest.raises(ValueError, match="Symlink output"):
        publication.verify_publication(
            target, temporary_root=tmp_path, expected_manifest_sha256=identity
        )


def test_reproduction_failure_is_not_published(inputs, tmp_path, monkeypatch, report):
    forecast, execution, evidence = inputs
    monkeypatch.setattr(publication, "evaluate_bundle", lambda _: report)
    encode = publication.scientific_payloads
    calls = 0

    def changed_report(report):
        nonlocal calls
        calls += 1
        files = encode(report)
        if calls == 2:
            files["summary.json"] += b" "
        return files

    monkeypatch.setattr(publication, "scientific_payloads", changed_report)
    destination = tmp_path / "changed"
    with pytest.raises(ValueError, match="reproduction"):
        publication.publish_synthetic(
            destination, forecast, execution, evidence=evidence, temporary_root=tmp_path
        )
    assert not (destination / "manifest.json").exists()
    assert (destination / "failure.json").exists()


def test_unavailable_full_year_benchmark_remains_explicit(inputs):
    forecast, execution, evidence = copy.deepcopy(inputs)
    # Only the mandated inception purchase is infeasible; Ridge uses 01:00.
    execution[1]["BTCUSDT", START] = D("1e20")
    reseal(forecast, execution, evidence)
    report = evaluation.evaluate_bundle(
        evaluation.adapt_inputs(forecast, execution, evidence=evidence)
    )
    b = report["summary"]["markets"]["BTCUSDT"]["buy_and_hold"]
    assert b["status"] == "unavailable" and b["total_return"] is None
    assert (
        report["summary"]["markets"]["BTCUSDT"]["comparisons"]["buy_and_hold"] is None
    )
    assert report["orders_trades"][b["account_id"]]["trades"] == ()
    assert publication.verify_payloads(evaluation.scientific_payloads(report))[
        b["account_id"]
    ]["reconciled"]


def test_signed_posting_sums_independently_reproduce_every_prefix(report):
    with localcontext(money_context()):
        for key, marks in report["hourly_marks"].items():
            ledger = report["ledger"][key]
            for mark in marks:
                prefix = [p for p in ledger if p["sequence"] <= mark.ledger_seq]
                assert (
                    sum((p["amount"] for p in prefix if p["asset"] == "USDT"), D(0))
                    == mark.account.cash
                )
                assert (
                    sum((p["amount"] for p in prefix if p["asset"] != "USDT"), D(0))
                    == mark.account.quantity
                )
                assert mark.account.realised + mark.unrealised == mark.equity - D(10000)


def test_corrupt_ledger_fails_even_without_manifest_hash_check(report):
    files = evaluation.scientific_payloads(report)
    ledger = json.loads(files["ledger.json"])
    key = next(k for k, rows in ledger.items() if len(rows) > 1)
    ledger[key][1]["amount"] = "999"
    files["ledger.json"] = evaluation.json_bytes(ledger)
    with pytest.raises(ValueError, match="Signed ledger"):
        publication.verify_payloads(files)


def test_post_link_failure_removes_manifest_and_fresh_destination_recovers(
    inputs, tmp_path, monkeypatch, report
):
    forecast, execution, evidence = inputs
    monkeypatch.setattr(publication, "evaluate_bundle", lambda _: report)
    write = publication._write_exclusive

    def fail_after_link(path, body):
        write(path, body)
        if path.name == "manifest.json":
            raise OSError("simulated late manifest failure")

    monkeypatch.setattr(publication, "_write_exclusive", fail_after_link)
    with pytest.raises(OSError):
        publication.publish_synthetic(
            tmp_path / "failed",
            forecast,
            execution,
            evidence=evidence,
            temporary_root=tmp_path,
        )
    assert not (tmp_path / "failed/manifest.json").exists()
    assert (tmp_path / "failed/failure.json").exists()
    monkeypatch.setattr(publication, "_write_exclusive", write)
    identity = publication.publish_synthetic(
        tmp_path / "fresh",
        forecast,
        execution,
        evidence=evidence,
        temporary_root=tmp_path,
    )
    assert (
        publication.verify_publication(
            tmp_path / "fresh",
            temporary_root=tmp_path,
            expected_manifest_sha256=identity,
        )["status"]
        == "synthetic_test"
    )


def test_hourly_snapshots_reference_history_without_duplicating_it(report):
    files = evaluation.scientific_payloads(report)
    marks = json.loads(files["hourly_marks.json"])
    for key, rows in marks.items():
        assert len(rows) == 8784
        for row in rows:
            assert set(row["account"]) == {
                "cash",
                "quantity",
                "basis",
                "realised",
                "fees",
                "ledger_seq",
                "at",
            }
        assert (
            rows[-1]["ledger_seq"] == report["orders_trades"][key]["final"].ledger_seq
        )
    assert publication.verify_payloads(files)

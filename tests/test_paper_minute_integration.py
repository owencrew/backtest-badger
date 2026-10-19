"""Fabricated loader-shaped evidence only; no authentic artifacts or economics."""

import builtins
import copy
import io
import json
import os
import socket
from dataclasses import FrozenInstanceError, replace
from decimal import ROUND_DOWN, localcontext
from hashlib import sha256
from pathlib import Path

import psycopg
import pytest

from backtest_badger import (
    execution_data,
    forecast_data,
    genuine_minute_price_parity,
    minute_execution_data,
    model_data,
)
from backtest_badger import paper_minute_historical as replay
from backtest_badger import paper_minute_integration as integration
from backtest_badger.forecast_data import Signal
from backtest_badger.paper_accounting import fee_for
from backtest_badger.paper_historical_evaluation import FEATURES
from backtest_badger.paper_types import STEP, Action, D, money_context

START, END, HOUR = replay.START, replay.END, replay.HOUR


@pytest.fixture(autouse=True)
def offline_boundary(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Stage 4B.2D.2 forbids loaders, artifacts, sibling, network and DB"
        )

    for module, name in (
        (forecast_data, "load_forecasts"),
        (execution_data, "load_execution_data"),
        (minute_execution_data, "load_minute_execution_data"),
        (minute_execution_data, "prepare_minute_execution_data"),
        (minute_execution_data, "download_minute_archive"),
        (genuine_minute_price_parity, "audit_genuine_minute_price_parity"),
        (model_data, "load_model_data"),
        (psycopg, "connect"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket.socket, "bind"),
    ):
        monkeypatch.setattr(module, name, forbidden)

    def guard(original):
        def guarded(file, *args, **kwargs):
            if isinstance(file, (str, bytes, os.PathLike)):
                parts = Path(os.fsdecode(file)).parts
                if "artifacts" in parts or "crypto-trading-platform" in parts:
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


def fake(label):
    return sha256(("stage4b2d2-fabricated-only:" + label).encode()).hexdigest()


def seal(data, *, parity=False):
    """Test author retaining NEW fixture pins; never available in production code."""
    forecasts, manifest, metadata, projection, proof, evidence = data
    if parity:
        proof["manifest"]["report_sha256"] = integration.evidence_sha256(
            proof["report"]
        )
        evidence["pins"]["parity_report"] = integration.evidence_sha256(proof["report"])
        evidence["pins"]["parity_manifest"] = integration.evidence_sha256(
            proof["manifest"]
        )
    evidence["snapshots"] = {
        "forecasts": integration.forecast_snapshot_sha256(forecasts),
        "forecast_manifest": integration.evidence_sha256(manifest),
        "minute_metadata": integration.evidence_sha256(metadata),
        "projection": replay.projection_sha256(projection),
    }
    return integration.evidence_sha256(evidence)


def fabricated(hours=20):
    end = START + hours * HOUR
    pins = {name: fake(name) for name in integration.PIN_NAMES}
    accounts, markets = {}, {}
    count = min(2195, (hours + 3) // 4)
    values = ("1.00000000000000000000000000000000000000001", "1", "1e-12", "0", "1")
    for symbol, training in zip(replay.SYMBOLS, (13782, 13783), strict=True):
        for model in forecast_data.MODELS:
            accounts[symbol, model] = [
                Signal(
                    symbol,
                    model,
                    START - STEP + i * STEP,
                    START + i * STEP + replay.MINUTE,
                    D(values[min(i, 4)]) if model == "ridge" else D(0),
                )
                for i in range(count)
            ]
        markets[symbol] = {
            "training_count": training,
            "validation_count": 2195,
            "training_mean": 0.0,
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
                "n_samples_seen": training,
            },
        }
    manifest = {
        "experiment_version": "stage-2b-v1",
        "fit_partition": "train",
        "evaluation_partition": "validation",
        "feature_order": list(FEATURES),
        "input": {
            "settling_seconds": 60,
            "input_hashes": {
                "research.csv": pins["research_csv"],
                "manifest.json": pins["research_manifest"],
            },
        },
        "output_sha256": {"validation_predictions.csv": pins["forecast_csv"]},
        "markets": markets,
    }
    monthly, sources = [], []
    for request in minute_execution_data.minute_requests():
        zip_hash, sidecar_hash = fake(request.stem), fake(request.stem + "-sidecar")
        monthly.append([request.symbol, request.month, zip_hash, sidecar_hash])
        sources.append(
            {
                "symbol": request.symbol,
                "month": request.month,
                "interval": "1m",
                "url": request.url,
                "checksum_url": request.checksum_url,
                "sha256": zip_hash,
                "checksum_sha256": sidecar_hash,
                "zip_bytes": 100,
                "checksum_bytes": 88,
                "csv_bytes": 1000,
                "row_count": request.row_count,
                "observed_at": END.isoformat(),
                "observation_kind": "retrospective_full_archive_acquisition",
                "validation_status": "complete_checksum_and_native_grid",
            }
        )
    metadata = {
        "artifact_version": "binance-1m-2024-v1",
        "format_version": "minute-opens-csv-v1",
        "status": "validated_source_structure_not_approved_for_evaluation",
        "source_authentication": "checksums_are_not_signed_provider_attestations",
        "coverage": minute_execution_data.coverage(),
        "archive_count": 24,
        "sources": sources,
        "implementation_sha256": fake("implementation"),
        "output": {
            "name": "minute_opens.csv",
            "sha256": pins["minute_csv"],
            "bytes": 10000,
        },
    }
    times = sorted(
        {START + i * HOUR for i in range(hours)}
        | {START + i * STEP + 2 * replay.MINUTE for i in range(count)}
    )
    projection = [
        replay.MinuteReference(
            symbol,
            replay.reference_identity(symbol, at, 60),
            at,
            D("100.125"),
            pins["minute_csv"],
            fake(f"{symbol}-1m-{at:%Y-%m}"),
        )
        for symbol in replay.SYMBOLS
        for at in times
    ]
    proof = {
        "manifest": {
            "kind": "synthetic_price_parity_fixture",
            "status": "synthetic_test",
            "report_sha256": "",
        },
        "report": {
            "status": "synthetic_test",
            "direct_timing_comparison_permitted": True,
            "structural_errors": [],
            "discrepancies": [],
            "counts": {
                "expected": 17568,
                "matched": 17568,
                "equal": 17568,
                "mismatched": 0,
                "per_market": {s: 8784 for s in replay.SYMBOLS},
            },
            "hourly": {
                "version": "binance-1h-2024-v1",
                "manifest_sha256": pins["hourly_manifest"],
                "file_sha256": pins["hourly_csv"],
            },
            "minute": {
                "version": "binance-1m-2024-v1",
                "manifest_sha256": pins["minute_manifest"],
                "file_sha256": pins["minute_csv"],
            },
            "matched_hours": [
                [s, (START + i * HOUR).isoformat()]
                for s in replay.SYMBOLS
                for i in range(8784)
            ],
        },
    }
    evidence = {
        "status": "synthetic_test",
        "protocol_version": replay.PROTOCOL_VERSION,
        "protocol_sha256": replay.PROTOCOL_SHA256,
        "selected_model": "ridge",
        "recipe_identity_kind": "stage2b_manifest_sha256",
        "model_recipe_sha256": pins["forecast_manifest"],
        "pins": pins,
        "monthly_sources": monthly,
        "end_exclusive": end.isoformat(),
    }
    data = [
        (
            {
                "manifest.json": pins["forecast_manifest"],
                "validation_predictions.csv": pins["forecast_csv"],
            },
            accounts,
        ),
        manifest,
        metadata,
        projection,
        proof,
        evidence,
    ]
    seal(data, parity=True)
    return data


@pytest.fixture(scope="module")
def small_inputs():
    return fabricated()


@pytest.fixture
def data(small_inputs):
    return copy.deepcopy(small_inputs)


def adapt(data, expected=None):
    return integration.adapt_minute_inputs(
        *data[:5],
        evidence=data[5],
        expected_evidence_sha256=expected or integration.evidence_sha256(data[5]),
    )


def execute(bundle, index=0):
    pins = json.loads(bundle.source_evidence_json)["evidence"]["pins"]
    return replay.replay_minute_historical(
        replay.SYMBOLS[index],
        bundle.forecasts[index],
        bundle.references[index],
        source=bundle.sources[index],
        expected_source_sha256=replay.price_source_sha256(bundle.sources[index]),
        forecast_sha256=pins["forecast_csv"],
        model_recipe_sha256=pins["forecast_manifest"],
        end_exclusive=bundle.end_exclusive,
    )


def test_synthetic_adapter_to_unchanged_replay(data):
    before = copy.deepcopy(data)
    bundle = adapt(data)
    integration.validate_minute_integration(bundle, expected_evidence_sha256=seal(data))
    assert data == before
    assert bundle.status == "synthetic_test"
    assert bundle.authentication == integration.AUTHENTICATION
    assert len(bundle.accounts) == 8
    for i in range(2):
        result = execute(bundle, i)
        assert result.kind == "synthetic_historical_minute_simulation"
        assert "not_full_source_authentication" in result.authentication
        ridge, cash, bh = result.accounts
        assert len({a.initial.portfolio.key for a in result.accounts}) == 3
        assert all(a.initial.cash == D(10000) for a in result.accounts)
        assert [d.action for d in result.decisions] == [
            Action.BUY_REQUIRED,
            Action.HOLD,
            Action.EXIT_REQUIRED,
            Action.CASH_NOOP,
            Action.BUY_REQUIRED,
        ]
        assert ridge.fills[0].trade.at == START + 2 * replay.MINUTE
        assert bh.fills[0].trade.at == START
        assert len(ridge.fills) == 3 and len(bh.fills) == 1 and not cash.fills
        assert ridge.final.quantity > 0 and bh.final.quantity > 0
        assert cash.final.cash == D(10000)
        for account in result.accounts:
            replay.verify_minute_account(account, end_exclusive=bundle.end_exclusive)
            assert len(account.marks) == 20
        with localcontext(money_context()):
            trade = ridge.fills[0].trade
            assert trade.price == D("100.125") * D("1.0003")
            assert trade.fee == fee_for(trade.quantity * trade.price)
            assert trade.quantity % D("0.000001") == 0
        # HOLD and CASH_NOOP still require exact projected source observations.
        assert len(bundle.references[i]) == 25
        assert (
            bundle.forecasts[i][0].prediction.as_tuple()
            == data[0][1][replay.SYMBOLS[i], "ridge"][0].forecast.as_tuple()
        )


@pytest.mark.parametrize(
    "value,target",
    [
        ("-1", 0),
        ("0", 0),
        ("0.0000000000009999999999999999", 0),
        ("1e-12", 0),
        ("0.0000000000010000000000000001", 1),
    ],
)
def test_threshold_preserved_and_prices_cannot_choose_target(data, value, target):
    signals = data[0][1]["BTCUSDT", "ridge"]
    signals[0] = replace(signals[0], forecast=D(value))
    data[3][1] = replace(data[3][1], price=D("999999.1234567890123456789"))
    seal(data)
    bundle = adapt(data)
    assert bundle.forecasts[0][0].prediction.as_tuple() == D(value).as_tuple()
    assert execute(bundle).decisions[0].target == target


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "duplicate",
        "reordered",
        "model",
        "symbol",
        "availability",
        "grid",
        "float",
        "nan",
        "zero",
        "mean",
        "baseline_missing",
    ],
)
def test_invalid_forecasts(data, mutation):
    accounts = data[0][1]
    signals = accounts["BTCUSDT", "ridge"]
    if mutation == "missing":
        signals.pop()
    elif mutation == "extra":
        signals.append(signals[-1])
    elif mutation == "duplicate":
        signals[1] = signals[0]
    elif mutation == "reordered":
        signals[0], signals[1] = signals[1], signals[0]
    elif mutation == "model":
        signals[0] = replace(signals[0], model="ridge-v2")
    elif mutation == "symbol":
        signals[0] = replace(signals[0], symbol="ETHUSDT")
    elif mutation == "availability":
        signals[0] = replace(signals[0], signal_time=START)
    elif mutation == "grid":
        signals[0] = replace(signals[0], open_time=START)
    elif mutation == "float":
        signals[0] = replace(signals[0], forecast=0.1)
    elif mutation == "nan":
        signals[0] = replace(signals[0], forecast=D("NaN"))
    elif mutation == "zero":
        accounts["ETHUSDT", "zero"][0] = replace(
            accounts["ETHUSDT", "zero"][0], forecast=D(1)
        )
    elif mutation == "mean":
        accounts["ETHUSDT", "training_mean"][0] = replace(
            accounts["ETHUSDT", "training_mean"][0], forecast=D(1)
        )
    else:
        accounts["ETHUSDT", "gradient_boosting"].pop()
    # Even repinning malformed input cannot bypass semantic validation.
    with pytest.raises(ValueError):
        seal(data)
        adapt(data)


@pytest.mark.parametrize(
    "mutation", ["missing_account", "extra_account", "wrong_csv", "wrong_manifest"]
)
def test_loader_shape_and_hashes(data, mutation):
    hashes, accounts = data[0]
    if mutation == "missing_account":
        del accounts["BTCUSDT", "zero"]
    elif mutation == "extra_account":
        accounts["SOLUSDT", "ridge"] = []
    else:
        hashes[
            "validation_predictions.csv" if mutation == "wrong_csv" else "manifest.json"
        ] = fake("changed")
    with pytest.raises(ValueError):
        adapt(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "feature_order",
        "train",
        "version",
        "research",
        "output",
        "scaler_count",
        "scale",
        "scaler_params",
        "ridge",
        "count",
    ],
)
def test_lineage(data, mutation):
    manifest = data[1]
    market = manifest["markets"]["BTCUSDT"]
    if mutation == "feature_order":
        manifest["feature_order"].reverse()
    elif mutation == "train":
        manifest["fit_partition"] = "validation"
    elif mutation == "version":
        manifest["experiment_version"] = "stage-2b-v2"
    elif mutation == "research":
        manifest["input"]["input_hashes"]["research.csv"] = fake("bad")
    elif mutation == "output":
        manifest["output_sha256"]["validation_predictions.csv"] = fake("regenerated")
    elif mutation == "scaler_count":
        market["fitted_scaler"]["n_samples_seen"] = 2195
    elif mutation == "scale":
        market["fitted_scaler"]["scale"][0] = 0
    elif mutation == "scaler_params":
        market["model_parameters"]["ridge_scaler"]["with_mean"] = False
    elif mutation == "ridge":
        market["model_parameters"]["ridge"]["alpha"] = 2.0
    else:
        market["validation_count"] = 2196
    seal(data)
    with pytest.raises(ValueError):
        adapt(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "version",
        "status",
        "coverage",
        "float_count",
        "csv",
        "zip",
        "sidecar",
        "missing",
        "duplicate",
        "reordered",
        "month",
        "interval",
        "url",
        "rows",
        "observed",
    ],
)
def test_native_metadata(data, mutation):
    metadata, row = data[2], data[2]["sources"][0]
    if mutation == "version":
        metadata["artifact_version"] = "binance-1m-2025-v1"
    elif mutation == "status":
        metadata["status"] = "genuine_authenticated"
    elif mutation == "coverage":
        metadata["coverage"]["row_counts"]["BTCUSDT"] = 10979
    elif mutation == "float_count":
        metadata["coverage"]["total_rows"] = 1054080.0
    elif mutation == "csv":
        metadata["output"]["sha256"] = fake("bad")
    elif mutation == "zip":
        row["sha256"] = fake("bad")
    elif mutation == "sidecar":
        row["checksum_sha256"] = fake("bad")
    elif mutation == "missing":
        metadata["sources"].pop()
    elif mutation == "duplicate":
        metadata["sources"][1] = row
    elif mutation == "reordered":
        metadata["sources"].reverse()
    elif mutation == "month":
        row["month"] = "2025-01"
    elif mutation == "interval":
        row["interval"] = "1h"
    elif mutation == "url":
        row["url"] += "changed"
    elif mutation == "rows":
        row["row_count"] -= 1
    else:
        row["observed_at"] = START.isoformat()
    seal(data)
    with pytest.raises(ValueError):
        adapt(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "duplicate",
        "reordered",
        "timestamp",
        "negative",
        "nan",
        "float",
        "record_id",
        "zip",
        "file",
        "symbol",
        "interval",
        "future_field",
    ],
)
def test_projection_rejects_bad_rows_even_if_repinned(data, mutation):
    rows = data[3]
    if mutation == "missing":
        rows.pop(1)
    elif mutation == "extra":
        rows.append(rows[-1])
    elif mutation == "duplicate":
        rows[2] = rows[1]
    elif mutation == "reordered":
        rows[1], rows[2] = rows[2], rows[1]
    elif mutation == "future_field":
        rows[1] = {"close": D(101)}
    else:
        field, value = {
            "timestamp": ("at", START + replay.MINUTE),
            "negative": ("price", D(-1)),
            "nan": ("price", D("NaN")),
            "float": ("price", 100.0),
            "record_id": ("record_id", "binance:spot:BTCUSDT:60:1704067320001"),
            "zip": ("source_sha256", fake("wrong-month")),
            "file": ("file_sha256", fake("bad")),
            "symbol": ("symbol", "ETHUSDT"),
            "interval": ("interval_seconds", 3600),
        }[mutation]
        # Deliberately bypass frozen constructor to test boundary revalidation.
        object.__setattr__(rows[1], field, value)
    with pytest.raises(ValueError):
        seal(data)
        adapt(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "flag",
        "flag_int",
        "report_pin",
        "manifest_pin",
        "hourly",
        "minute",
        "version",
        "count",
        "missing",
        "reordered",
        "duplicate",
        "discrepancy",
        "errors",
        "status",
    ],
)
def test_parity_failure_and_forged_success(data, mutation):
    report = data[4]["report"]
    if mutation in ("report_pin", "manifest_pin"):
        data[5]["pins"][
            "parity_report" if mutation == "report_pin" else "parity_manifest"
        ] = fake("forged")
    else:
        if mutation == "flag":
            report["direct_timing_comparison_permitted"] = False
        elif mutation == "flag_int":
            report["direct_timing_comparison_permitted"] = 1
        elif mutation in ("hourly", "minute"):
            report[mutation]["manifest_sha256"] = fake("other-release")
        elif mutation == "version":
            report["minute"]["version"] = "binance-1m-2025-v1"
        elif mutation == "count":
            report["counts"]["matched"] -= 1
        elif mutation == "missing":
            report["matched_hours"].pop()
        elif mutation == "reordered":
            report["matched_hours"].reverse()
        elif mutation == "duplicate":
            report["matched_hours"][1] = report["matched_hours"][0]
        elif mutation == "discrepancy":
            report["discrepancies"] = [{"difference": "1"}]
        elif mutation == "errors":
            report["structural_errors"] = ["missing"]
        else:
            report["status"] = "genuine_success"
        seal(data, parity=True)
    with pytest.raises(ValueError):
        adapt(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "status",
        "model",
        "recipe",
        "recipe_kind",
        "protocol",
        "missing_pin",
        "genuine_pin",
    ],
)
def test_permission_and_mandatory_external_evidence(data, mutation):
    evidence = data[5]
    if mutation == "status":
        evidence["status"] = "genuine_authenticated"
    elif mutation == "model":
        evidence["selected_model"] = "gradient_boosting"
    elif mutation == "recipe":
        evidence["model_recipe_sha256"] = fake("other")
    elif mutation == "recipe_kind":
        evidence["recipe_identity_kind"] = "ridge_coefficients"
    elif mutation == "protocol":
        evidence["protocol_sha256"] = fake("other")
    elif mutation == "missing_pin":
        del evidence["pins"]["hourly_csv"]
    else:
        evidence["pins"]["minute_manifest"] = replay.FROZEN_MINUTE_MANIFEST_SHA256
    with pytest.raises(ValueError):
        adapt(data)


def test_external_pin_not_recomputed_by_adapter(data):
    external = integration.evidence_sha256(data[5])
    data[5]["pins"]["hourly_csv"] = fake("changed")
    with pytest.raises(ValueError, match="External TEST evidence pin"):
        adapt(data, external)
    with pytest.raises(TypeError):
        integration.adapt_minute_inputs(*data[:5], evidence=data[5])


@pytest.mark.parametrize("component", [0, 1, 2, 3])
def test_unrepinned_snapshot_mutation(data, component):
    if component == 0:
        signals = data[0][1]["BTCUSDT", "ridge"]
        signals[0] = replace(signals[0], forecast=D("1.23"))
    elif component == 1:
        data[1]["markets"]["BTCUSDT"]["fitted_scaler"]["mean"][0] = 1.0
    elif component == 2:
        data[2]["output"]["bytes"] += 1
    else:
        data[3][1] = replace(data[3][1], price=D(200))
    with pytest.raises(ValueError, match="snapshot"):
        adapt(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "forecast",
        "reference",
        "baseline",
        "status",
        "source",
        "evidence",
        "auth",
        "end",
    ],
)
def test_prepared_bundle_tampering(data, mutation):
    pin = integration.evidence_sha256(data[5])
    bundle = adapt(data)
    if mutation == "forecast":
        fs = bundle.forecasts
        bundle = replace(
            bundle, forecasts=((replace(fs[0][0], prediction=D(9)), *fs[0][1:]), fs[1])
        )
    elif mutation == "reference":
        rs = bundle.references
        bundle = replace(
            bundle, references=((replace(rs[0][0], price=D(9)), *rs[0][1:]), rs[1])
        )
    elif mutation == "baseline":
        accounts = list(bundle.accounts)
        accounts[0] = accounts[0][:-1]
        bundle = replace(bundle, accounts=tuple(accounts))
    elif mutation == "status":
        bundle = replace(bundle, status="genuine")
    elif mutation == "source":
        object.__setattr__(bundle.sources[0], "status", "genuine")
    elif mutation == "evidence":
        bundle = replace(bundle, source_evidence_json=b"{}")
    elif mutation == "auth":
        bundle = replace(bundle, authentication="genuine_authenticated")
    else:
        bundle = replace(bundle, end_exclusive=END)
    with pytest.raises(ValueError):
        integration.validate_minute_integration(bundle, expected_evidence_sha256=pin)


def test_immutability_decimal_context_and_no_authority(data):
    pin = integration.evidence_sha256(data[5])
    expected = adapt(data)
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = 3, ROUND_DOWN
        assert adapt(data) == expected
        assert integration.evidence_sha256(data[5]) == pin
        integration.validate_minute_integration(expected, expected_evidence_sha256=pin)
    with pytest.raises(FrozenInstanceError):
        expected.status = "genuine"
    retained = json.loads(expected.source_evidence_json)
    assert retained["genuine_execution_authorised"] is False
    assert retained["genuine_timing_comparison_authorised"] is False
    assert retained["minute_metadata"]["coverage"]["total_rows"] == 1054080
    assert expected.sources[0].projected_sha256 != expected.sources[0].file_sha256
    with pytest.raises(ValueError, match="Genuine source"):
        replace(expected.sources[0], status="genuine")
    object.__setattr__(expected.sources[0], "status", "genuine")
    with pytest.raises(ValueError, match="Genuine source"):
        execute(expected)


def test_complete_leap_year_bounded_projection():
    data = fabricated(8784)
    bundle = adapt(data)
    assert all(len(account) == 2195 for account in bundle.accounts)
    for forecasts, refs in zip(bundle.forecasts, bundle.references, strict=True):
        assert len(forecasts) == 2195 and len(refs) == 10979
        assert sum(r.at.minute == 0 for r in refs) == 8784
        assert sum(r.at.month == 2 and r.at.minute == 0 for r in refs) == 696
        assert forecasts[0].source_open == START - STEP
        assert forecasts[-1].source_open == END - 3 * STEP
        assert forecasts[-1].feature_available_at == END - 2 * STEP + replay.MINUTE
        assert refs[1].at == START + 2 * replay.MINUTE
        assert refs[-1].at == END - HOUR
        assert all(
            f.feature_available_at != END - STEP + replay.MINUTE for f in forecasts
        )
        assert all(r.source_sha256 == fake(f"{r.symbol}-1m-{r.at:%Y-%m}") for r in refs)
    # Stream serialization; no million-row price collection or duplicated ledgers.
    size = sum(
        len(replay.scientific_json(r).encode()) for rs in bundle.references for r in rs
    )
    size += sum(
        len(replay.scientific_json(s).encode()) for ss in bundle.accounts for s in ss
    )
    size += sum(
        len(replay.scientific_json(f).encode())
        for forecasts in bundle.forecasts
        for f in forecasts
    )
    size += sum(len(replay.scientific_json(s).encode()) for s in bundle.sources)
    size += len(bundle.source_evidence_json)
    assert size < 20_000_000
    integration.validate_minute_integration(
        bundle, expected_evidence_sha256=integration.evidence_sha256(data[5])
    )


@pytest.mark.parametrize(
    "operation",
    [
        "open",
        "io_open",
        "os_open",
        "listdir",
        "scandir",
        "sibling",
        "loader",
        "db",
        "network",
    ],
)
def test_offline_guards_fire_before_access(operation):
    with pytest.raises(AssertionError, match="Stage 4B.2D.2 forbids"):
        if operation == "open":
            builtins.open("artifacts/never-open", "rb")
        elif operation == "io_open":
            Path("artifacts/never-open").open("wb")
        elif operation == "os_open":
            os.open("artifacts/never-open", os.O_RDONLY)
        elif operation == "listdir":
            os.listdir("artifacts")
        elif operation == "scandir":
            os.scandir("artifacts")
        elif operation == "sibling":
            builtins.open("../crypto-trading-platform/never-open")
        elif operation == "loader":
            forecast_data.load_forecasts(None)
        elif operation == "db":
            psycopg.connect("")
        else:
            socket.create_connection(("example.invalid", 443))


def test_adapter_never_calls_strategy_or_simulation(data, monkeypatch):
    from backtest_badger import paper_strategy

    def forbidden(*args, **kwargs):
        pytest.fail("Adaptation must not calculate a strategy or account")

    monkeypatch.setattr(paper_strategy, "evaluate_strategy", forbidden)
    monkeypatch.setattr(replay, "evaluate_strategy", forbidden)
    monkeypatch.setattr(replay, "replay_minute_historical", forbidden)
    bundle = adapt(data)
    integration.validate_minute_integration(
        bundle, expected_evidence_sha256=integration.evidence_sha256(data[5])
    )


def test_genuine_permission_gate_before_payload_inspection(data):
    class ForbiddenPayload:
        def __iter__(self):
            pytest.fail("Genuine gate must precede payload inspection")

    data[5]["status"] = "genuine_authenticated"
    with pytest.raises(ValueError, match="Permission gate"):
        integration.adapt_minute_inputs(
            ForbiddenPayload(),
            None,
            None,
            None,
            None,
            evidence=data[5],
            expected_evidence_sha256="invalid",
        )


@pytest.mark.parametrize("component", [1, 2, 4])
def test_missing_metadata_evidence_fails(data, component):
    data[component] = {}
    with pytest.raises(ValueError):
        adapt(data)


def test_synthetic_success_cannot_grant_genuine_permission(data):
    bundle = adapt(data)
    retained = json.loads(bundle.source_evidence_json)
    # A caller's forged success boolean cannot change the retained provenance.
    retained["genuine_execution_authorised"] = True
    forged = replace(bundle, source_evidence_json=integration.json_bytes(retained))
    with pytest.raises(ValueError, match="Prepared records"):
        integration.validate_minute_integration(
            forged, expected_evidence_sha256=integration.evidence_sha256(data[5])
        )
    assert execute(bundle).kind.startswith("synthetic_")

"""Invented temporary bytes only; run the full suite with install_offline_audit()."""

import builtins
import copy
import csv
import io
import json
import os
import socket
import sys
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from decimal import Decimal, localcontext
from hashlib import sha256
from pathlib import Path

import psycopg
import pytest

from backtest_badger import forecast_data as forecast
from backtest_badger import genuine_minute_inputs as auth
from backtest_badger import genuine_minute_price_parity as parity
from backtest_badger import minute_execution_data as minute
from backtest_badger import paper_historical_evaluation as policy
from backtest_badger import paper_minute_historical as replay
from backtest_badger import paper_minute_integration as integration

ROOT = Path(__file__).absolute().parents[1]
SYNTHETIC_REPLAY = replay.replay_minute_historical


def forbidden(*args, **kwargs):
    raise AssertionError("Offline boundary: genuine sources/network/database forbidden")


def check_path(path):
    if isinstance(path, (str, bytes, os.PathLike)):
        absolute = Path(os.path.abspath(os.fsdecode(path)))
        if (
            absolute.is_relative_to(ROOT / "artifacts")
            or "crypto-trading-platform" in absolute.parts
        ):
            forbidden()


def install_offline_audit():
    """One-way process audit used by the documented full-suite invocation.

    Hooks run beneath monkeypatched opens. stat/lstat have no CPython audit event,
    so also guard their actual functions. No real forbidden path is probed.
    """

    def audit(event, args):
        if event in ("open", "os.listdir", "os.scandir", "os.chdir"):
            check_path(args[0])
        if event in (
            "socket.connect",
            "socket.bind",
            "socket.getaddrinfo",
            "socket.gethostbyname",
            "socket.gethostbyaddr",
            "socket.sendto",
        ):
            forbidden()

    sys.addaudithook(audit)
    for name in ("stat", "lstat"):
        original = getattr(os, name)

        def guarded(path, *args, _original=original, **kwargs):
            check_path(path)
            return _original(path, *args, **kwargs)

        setattr(os, name, guarded)
    psycopg.connect = forbidden
    os.environ.pop("BADGER_TEST_ADMIN_DSN", None)
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    for module, name in (
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket.socket, "bind"),
        (psycopg, "connect"),
        (parity, "audit_genuine_minute_price_parity"),
        (parity.hourly, "load_execution_data"),
        (replay, "replay_minute_historical"),
        (replay, "_fund"),
        (replay, "calculate_minute_fill"),
        (replay, "value_minute_account"),
        (replay, "evaluate_strategy"),
    ):
        monkeypatch.setattr(module, name, forbidden)
    for module, name in (
        (builtins, "open"),
        (io, "open"),
        (os, "open"),
        (os, "listdir"),
        (os, "scandir"),
        (os, "stat"),
        (os, "lstat"),
    ):
        original = getattr(module, name)

        def guarded(path, *args, _original=original, **kwargs):
            check_path(path)
            return _original(path, *args, **kwargs)

        monkeypatch.setattr(module, name, guarded)


def fake(label):
    return sha256(("4b2d3-fabricated:" + label).encode()).hexdigest()


def ident(body):
    return {"sha256": sha256(body).hexdigest(), "bytes": len(body)}


def recipe(pins):
    markets = {}
    for s, count in zip(minute.SYMBOLS, (13782, 13783), strict=True):
        markets[s] = {
            "training_count": count,
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
                "n_samples_seen": count,
            },
        }
    return {
        "experiment_version": "stage-2b-v1",
        "fit_partition": "train",
        "evaluation_partition": "validation",
        "feature_order": list(policy.FEATURES),
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


def forecast_bytes(pins):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(forecast.COLUMNS)
    for symbol in minute.SYMBOLS:
        for i in range(2195):
            opened = minute.START - auth.STEP + i * auth.STEP
            for model in forecast.MODELS:
                value = (
                    "0.123456789012345678901234567890123456789"
                    if model == "ridge"
                    else "0"
                )
                writer.writerow(
                    (
                        "binance",
                        "spot",
                        symbol,
                        "14400",
                        opened.isoformat(),
                        (opened + auth.STEP + replay.MINUTE).isoformat(),
                        model,
                        value,
                        pins["research_csv"],
                    )
                )
    return output.getvalue().encode()


def count_group(count):
    return {
        "expected": count,
        "matched_identities": count,
        "equal_prices": count,
        "mismatched_prices": 0,
        "positive_differences": 0,
        "negative_differences": 0,
        "absolute_difference_sum": "0.00",
        "absolute_difference_min": "0.00",
        "absolute_difference_max": "0",
        "absolute_difference_mean_exact_ratio": {
            "numerator": "0.00",
            "denominator": count,
        },
    }


def publication(pins, monthly, minute_manifest, snapshots, audit_code, hourly_monthly):
    report = {
        "schema": "native-opening-price-parity-v1",
        "status": "exact_price_parity",
        "direct_timing_comparison_permitted": True,
        "native_interval_seconds": {"hourly": 3600, "minute": 60},
        "start": minute.START.isoformat(),
        "end_exclusive": minute.END.isoformat(),
        "last_hour": (minute.END - timedelta(hours=1)).isoformat(),
        "comparison": "exact Decimal equality; no tolerance or substitution",
        "overall": count_group(17568),
        "per_symbol": {s: count_group(8784) for s in minute.SYMBOLS},
        "per_month": {
            f"2024-{m:02d}": count_group(auth.calendar.monthrange(2024, m)[1] * 48)
            for m in range(1, 13)
        },
        "per_symbol_month": {
            f"{s}:2024-{m:02d}": count_group(auth.calendar.monthrange(2024, m)[1] * 24)
            for s in minute.SYMBOLS
            for m in range(1, 13)
        },
        "discrepancies": [],
        "structural_errors": [],
        "limitations": list(parity.LIMITATIONS),
        "authentication": "genuine_pinned_releases_full_native_archive_revalidation",
    }
    hourly_sources = []
    for (symbol, month), value in monthly.items():
        url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/1h/{symbol}-1h-{month}.zip"
        hourly_sources.append(
            {
                "symbol": symbol,
                "month": month,
                "sha256": hourly_monthly[symbol, month],
                "checksum_sha256": fake(url + ".CHECKSUM"),
                "interval": "1h",
                "url": url,
                "checksum_url": url + ".CHECKSUM",
                "row_count": value["row_count"] // 60,
                "complete": True,
                "checksum_valid": True,
            }
        )
    hourly_manifest = {
        "artifact_version": "binance-1h-2024-v1",
        "coverage": parity.hourly.coverage(),
        "archive_count": 24,
        "output_sha256": {
            "hourly_opens.csv": pins["hourly_csv"],
            "acquisition.json": pins["hourly_acquisition"],
        },
        "sources": hourly_sources,
    }
    hourly_snapshot = {
        name: {"sha256": fake(name), "bytes": 123, "stat": [1, 2, 123, 4, 5]}
        for name in auth._release_names("1h")
    }
    for name, key in (
        ("manifest.json", "hourly_manifest"),
        ("hourly_opens.csv", "hourly_csv"),
        ("acquisition.json", "hourly_acquisition"),
    ):
        hourly_snapshot[name]["sha256"] = pins[key]
    for source in hourly_sources:
        for suffix, key in (("", "sha256"), (".CHECKSUM", "checksum_sha256")):
            hourly_snapshot[f"raw/{source['symbol']}-1h-{source['month']}.zip{suffix}"][
                "sha256"
            ] = source[key]
    all_snapshots = [hourly_snapshot, snapshots]
    provenance = {
        "schema": "genuine-native-parity-provenance-v1",
        "kind": "source_price_parity_only",
        "expected_external_pins": {
            "hourly": {
                "manifest.json": pins["hourly_manifest"],
                "hourly_opens.csv": pins["hourly_csv"],
                "acquisition.json": pins["hourly_acquisition"],
            },
            "minute": {
                "manifest.json": pins["minute_manifest"],
                "minute_opens.csv": pins["minute_csv"],
            },
            "documents": {
                parity.HOURLY_PROTOCOL: pins["hourly_protocol"],
                parity.MINUTE_PROTOCOL: pins["minute_protocol"],
                parity.PIN_DOCUMENT: pins["minute_pin_document"],
            },
        },
        "implementation_sha256": audit_code,
        "source_paths": {"hourly": parity.HOURLY_PATH, "minute": auth.MINUTE_PATH},
        "source_manifests": {"hourly": hourly_manifest, "minute": minute_manifest},
        "native_rows_per_symbol": {"hourly": 8784, "minute": 527040},
        "projected_rows_per_symbol": 8784,
        "integrity": {
            "method": (
                "SHA-256, size, device/inode/mtime/ctime before and after "
                "for every source file"
            ),
            "loaders": (
                "Unchanged loaders replay every ZIP/checksum and "
                "reproduce complete processed CSVs"
            ),
            "minute_projection": (
                "Additional single streaming pass: ASCII/CSV, "
                "every timestamp/price/source, EOF/hash/size; retain HH:00 only"
            ),
            "source_file_count": 101,
            "all_source_bytes_and_stats_unchanged": True,
            "sources": {
                group: {
                    name: {k: v for k, v in identity.items() if k != "stat"}
                    for name, identity in snap.items()
                }
                for group, snap in zip(("hourly", "minute"), all_snapshots, strict=True)
            },
        },
    }
    provenance["limitations"] = list(parity.LIMITATIONS)
    bodies = {
        "parity_report.json": parity._json(report),
        "provenance.json": parity._json(provenance),
        "integrity.json": parity._json(
            {"before": all_snapshots, "after": all_snapshots}
        ),
        "discrepancies.csv": (",".join(parity.COLUMNS) + "\n").encode(),
    }
    return reseal(bodies, pins)


def reseal(bodies, pins):
    """Fabricated proof author only; unavailable through production API."""
    bodies["manifest.json"] = parity._json(
        {
            "schema": "genuine-native-parity-publication-v1",
            "kind": "source_price_parity_only",
            "status": "exact_price_parity",
            "direct_timing_comparison_permitted": True,
            "files": {n: ident(b) for n, b in bodies.items() if n != "manifest.json"},
        }
    )
    pins["parity_manifest"] = ident(bodies["manifest.json"])["sha256"]
    pins["parity_report"] = ident(bodies["parity_report.json"])["sha256"]
    return bodies


@pytest.fixture(scope="module")
def fabricated(tmp_path_factory):
    root = tmp_path_factory.mktemp("fabricated-authentication").resolve()
    for name in ("forecast", "minute/raw", "parity", "code"):
        (root / name).mkdir(parents=True)
    pins = {name: fake(name) for name in auth.EXTERNAL_PINS}
    monthly, sources = {}, []
    for request in minute.minute_requests():
        raw = ("invented ZIP bytes " + request.stem).encode()
        sidecar = f"{sha256(raw).hexdigest()}  {request.stem}.zip\n".encode()
        (root / "minute/raw" / (request.stem + ".zip")).write_bytes(raw)
        (root / "minute/raw" / (request.stem + ".zip.CHECKSUM")).write_bytes(sidecar)
        value = {
            "sha256": sha256(raw).hexdigest(),
            "checksum_sha256": sha256(sidecar).hexdigest(),
            "zip_bytes": len(raw),
            "checksum_bytes": len(sidecar),
            "csv_bytes": 456,
            "row_count": request.row_count,
            "url": request.url,
            "checksum_url": request.checksum_url,
            "observed_at": minute.END.isoformat(),
        }
        monthly[request.symbol, request.month] = value
        sources.append(
            {
                **value,
                "symbol": request.symbol,
                "month": request.month,
                "interval": "1m",
                "observation_kind": "retrospective_full_archive_acquisition",
                "validation_status": "complete_checksum_and_native_grid",
            }
        )
    path = root / "minute/minute_opens.csv"
    with path.open("wb") as stream:
        stream.write(minute.HEADER)
        for request in minute.minute_requests():
            source = monthly[request.symbol, request.month]["sha256"]
            for i in range(request.row_count):
                stream.write(
                    (
                        f"{request.symbol},{request.start_ms + i * 60000},"
                        f"100.125,{source}\n"
                    ).encode()
                )
    identity = auth._identity(path)
    pins["minute_csv"] = identity["sha256"]
    code = root / "code/minute_loader.py"
    code.write_bytes(b"# fabricated reviewed code identity\n")
    code_hash = sha256(code.read_bytes()).hexdigest()
    metadata = minute._manifest(
        sources, pins["minute_csv"], identity["bytes"], code_hash
    )
    body = minute._json(metadata)
    (root / "minute/manifest.json").write_bytes(body)
    pins["minute_manifest"] = sha256(body).hexdigest()
    body = forecast_bytes(pins)
    (root / "forecast/validation_predictions.csv").write_bytes(body)
    pins["forecast_csv"] = sha256(body).hexdigest()
    manifest = recipe(pins)
    body = parity._json(manifest)
    (root / "forecast/manifest.json").write_bytes(body)
    pins["forecast_manifest"] = sha256(body).hexdigest()
    snapshots = {
        name: auth._identity(root / "minute" / name)
        for name in auth._release_names("1m")
    }
    audit_code = {
        name: fake("old-audit:" + name) for name in parity.IMPLEMENTATION_FILES
    }
    for name, key in (
        (parity.HOURLY_PROTOCOL, "hourly_protocol"),
        (parity.MINUTE_PROTOCOL, "minute_protocol"),
        (parity.PIN_DOCUMENT, "minute_pin_document"),
    ):
        audit_code[name] = pins[key]
    hourly_monthly = {key: fake("hourly:" + repr(key)) for key in monthly}
    bodies = publication(pins, monthly, metadata, snapshots, audit_code, hourly_monthly)
    for name, body in bodies.items():
        (root / "parity" / name).write_bytes(body)
    return {
        "root": root,
        "pins": pins,
        "monthly": monthly,
        "metadata": metadata,
        "manifest": manifest,
        "processed_bytes": identity["bytes"],
        "code": code,
        "code_hash": code_hash,
        "bodies": bodies,
        "audit_code": audit_code,
        "hourly_monthly": hourly_monthly,
    }


@pytest.fixture
def isolated_policy(fabricated, monkeypatch):
    """Patch TEST module constants, never translate a manifest or genuine input."""
    pins = fabricated["pins"]
    monkeypatch.setattr(forecast, "RESEARCH_SHA256", pins["research_csv"])
    for name, key in (
        ("RESEARCH_SHA256", "research_csv"),
        ("RESEARCH_MANIFEST_SHA256", "research_manifest"),
        ("FORECAST_SHA256", "forecast_csv"),
    ):
        monkeypatch.setattr(policy, name, pins[key])


def load_fixture(data):
    return forecast.load_forecasts(
        data["root"] / "forecast",
        expected_csv_sha256=data["pins"]["forecast_csv"],
        expected_manifest_sha256=data["pins"]["forecast_manifest"],
    )


def arguments(data):
    def native_loader(directory, *, expected_manifest_sha256):
        # Explicit fake: archive reconstruction is tested by the original suite.
        assert directory == data["root"] / "minute"
        assert expected_manifest_sha256 == data["pins"]["minute_manifest"]
        return copy.deepcopy(data["metadata"])

    return dict(
        fixture_root=data["root"],
        pins=data["pins"],
        monthly_sources=data["monthly"],
        processed_bytes=data["processed_bytes"],
        code_paths={"minute_loader": data["code"]},
        expected_code_sha256={"minute_loader": data["code_hash"]},
        expected_audit_code_sha256=data["audit_code"],
        hourly_monthly=data["hourly_monthly"],
        forecast_loader=lambda directory: load_fixture(data),
        minute_loader=native_loader,
        lineage_validator=policy._validate_lineage,
    )


def test_complete_fabricated_authentication(fabricated, isolated_policy):
    result = auth._authenticate_fixture_inputs(**arguments(fabricated))
    assert result.status == auth.STATUS and result.genuine_execution_authorised is False
    assert len(result.forecasts) == 8 and all(
        len(rows) == 2195 for rows in result.forecasts
    )
    assert all(len(rows) == 10979 for rows in result.references)
    ridge = result.forecasts[2]
    assert (
        ridge[0].prediction.as_tuple()
        == Decimal("0.123456789012345678901234567890123456789").as_tuple()
    )
    assert ridge[0].source_open.isoformat() == "2023-12-31T20:00:00+00:00"
    assert ridge[0].assumed_available_at == minute.START + replay.MINUTE
    assert ridge[0].hypothetical_minute_at == minute.START + 2 * replay.MINUTE
    assert ridge[-1].assumed_available_at.isoformat() == "2024-12-31T16:01:00+00:00"
    assert (
        ridge[-1].record_id
        == "binance:spot:BTCUSDT:14400:2024-12-31T12:00:00+00:00:ridge"
    )
    for refs in result.references:
        assert sum(r.at.minute == 0 for r in refs) == 8784
        assert sum(r.at.minute == 2 for r in refs) == 2195
        assert (
            sum(r.at.month == 2 and r.at.day == 29 and r.at.minute == 0 for r in refs)
            == 24
        )
        assert all(
            r.at < minute.END and r.file_sha256 == fabricated["pins"]["minute_csv"]
            for r in refs
        )
        assert all(
            r.source_sha256
            == fabricated["monthly"][r.symbol, r.at.strftime("%Y-%m")]["sha256"]
            for r in refs
        )
    evidence = json.loads(result.source_evidence_json)
    assert evidence["source_kind"] == "fabricated_temporary_fixture_bytes"
    assert evidence["recipe_sha256"] == fabricated["pins"]["forecast_manifest"]
    assert len(evidence["monthly_sources"]) == 24
    assert result.projection_sha256[0] != fabricated["pins"]["minute_csv"]
    serial = auth.authenticated_inputs_json(result)
    with localcontext() as context:
        context.prec = 3
        assert auth.authenticated_inputs_json(result) == serial
    with pytest.raises(FrozenInstanceError):
        result.status = "synthetic_test"
    with pytest.raises(ValueError):
        replace(result, status="synthetic_test")
    with pytest.raises(ValueError, match="Permission gate"):
        integration.validate_minute_integration(
            result, expected_evidence_sha256=fake("x")
        )
    with pytest.raises(ValueError, match="synthetic"):
        replay.validate_price_projection(
            result.references[0],
            result,
            interval_seconds=60,
            expected_source_sha256=fake("x"),
        )
    with pytest.raises(ValueError, match="Wrong forecast/miss evidence type"):
        SYNTHETIC_REPLAY(
            "BTCUSDT",
            result.forecasts[2],
            result.references[0],
            source=result,
            expected_source_sha256=fake("x"),
            forecast_sha256=fabricated["pins"]["forecast_csv"],
            model_recipe_sha256=fabricated["pins"]["forecast_manifest"],
        )
    assert not hasattr(auth, "replay_authenticated_minute_historical")


@pytest.mark.parametrize(
    "approval",
    [
        None,
        {},
        {"allow_genuine": True},
        {"status": "approved", "root": str(ROOT / "artifacts")},
    ],
)
def test_public_gate_never_inspects_approval(approval, monkeypatch):
    monkeypatch.setattr(auth, "_safe", forbidden)
    with pytest.raises(PermissionError):
        auth.authenticate_minute_inputs(approval=approval)


@pytest.mark.parametrize(
    "path",
    [
        ROOT / "artifacts",
        ROOT / "../crypto-trading-platform",
        Path("/etc"),
        Path("relative"),
    ],
)
def test_private_root_rejected_before_stat(fabricated, path, monkeypatch):
    args = arguments(fabricated)
    args["fixture_root"] = path
    monkeypatch.setattr(auth, "_safe", forbidden)
    with pytest.raises(ValueError, match="temporary root"):
        auth._authenticate_fixture_inputs(**args)


@pytest.mark.parametrize("operation", ["open", "stat", "lstat", "listdir", "scandir"])
def test_real_paths_blocked_without_access(operation):
    path = ROOT / "artifacts/audits/stage-04b2d1-native-parity-v1"
    with pytest.raises(AssertionError, match="Offline boundary"):
        if operation == "open":
            path.read_bytes()
        else:
            getattr(os, operation)(path)


def test_network_database_sibling_blocked():
    for call in (
        lambda: socket.getaddrinfo("example.invalid", 443),
        lambda: socket.create_connection(("127.0.0.1", 123)),
        lambda: psycopg.connect(""),
        lambda: (ROOT.parent / "crypto-trading-platform/anything").read_bytes(),
    ):
        with pytest.raises(AssertionError, match="Offline boundary"):
            call()


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_account",
        "reordered_accounts",
        "duplicate",
        "late",
        "nonfinite",
        "zero",
        "training_mean",
        "model",
        "missing_horizon",
        "float",
    ],
)
def test_forecasts_fail_closed(fabricated, isolated_policy, mutation):
    result = load_fixture(fabricated)
    hashes, accounts = result
    if mutation == "missing_account":
        del accounts[auth.ACCOUNT_KEYS[-1]]
    elif mutation == "reordered_accounts":
        accounts = dict(reversed(list(accounts.items())))
    elif mutation == "missing_horizon":
        accounts["BTCUSDT", "ridge"].pop()
    else:
        model = mutation if mutation in ("zero", "training_mean") else "ridge"
        rows = accounts["BTCUSDT", model]
        if mutation == "duplicate":
            rows[1] = rows[0]
        else:
            changes = {
                "late": {"signal_time": rows[0].signal_time + replay.MINUTE},
                "nonfinite": {"forecast": Decimal("NaN")},
                "float": {"forecast": 1.0},
                "zero": {"forecast": Decimal(1)},
                "training_mean": {"forecast": Decimal(1)},
                "model": {"model": "zero"},
            }[mutation]
            rows[0] = replace(rows[0], **changes)
    with pytest.raises(ValueError):
        auth._forecasts((hashes, accounts), fabricated["manifest"], fabricated["pins"])


@pytest.mark.parametrize(
    "mutation",
    [
        "feature_order",
        "fit_partition",
        "input_hash",
        "training_count",
        "scaler_count",
        "scale",
        "mean",
        "ridge",
        "validation_count",
    ],
)
def test_unmodified_lineage_policy(fabricated, isolated_policy, mutation):
    manifest = copy.deepcopy(fabricated["manifest"])
    market = manifest["markets"]["BTCUSDT"]
    if mutation == "feature_order":
        manifest["feature_order"].reverse()
    elif mutation == "fit_partition":
        manifest["fit_partition"] = "validation"
    elif mutation == "input_hash":
        manifest["input"]["input_hashes"]["research.csv"] = fake("wrong")
    elif mutation == "training_count":
        market["training_count"] += 1
    elif mutation == "scaler_count":
        market["fitted_scaler"]["n_samples_seen"] += 2195
    elif mutation == "scale":
        market["fitted_scaler"]["scale"][0] = 0
    elif mutation == "mean":
        market["fitted_scaler"]["mean"][0] = float("nan")
    elif mutation == "ridge":
        market["model_parameters"]["ridge"]["solver"] = "auto"
    elif mutation == "validation_count":
        market["validation_count"] += 1
    with pytest.raises(ValueError):
        policy._validate_lineage(manifest)


@pytest.mark.parametrize(
    "mutation",
    [
        "header",
        "ascii",
        "oversized",
        "missing",
        "duplicate",
        "reordered",
        "market",
        "timestamp",
        "source",
        "nan",
        "infinity",
        "negative",
        "zero",
        "exponent",
        "extra_field",
        "unterminated",
    ],
)
def test_stream_malformed_first_rows(fabricated, tmp_path, mutation):
    path = tmp_path.resolve() / "native.csv"
    fields = [
        "BTCUSDT",
        "1704067200000",
        "100",
        fabricated["monthly"]["BTCUSDT", "2024-01"]["sha256"],
    ]
    changes = {
        "ascii": (2, "é"),
        "oversized": (2, "1" * 3000),
        "reordered": (1, "1704067260000"),
        "market": (0, "ETHUSDT"),
        "timestamp": (1, "1704067200001"),
        "source": (3, fake("other-month")),
        "nan": (2, "NaN"),
        "infinity": (2, "Infinity"),
        "negative": (2, "-1"),
        "zero": (2, "0"),
        "exponent": (2, "1e2"),
    }
    if mutation in changes:
        i, value = changes[mutation]
        fields[i] = value
    if mutation == "extra_field":
        fields.append("unexpected")
    row = (",".join(fields) + "\n").encode()
    body = minute.HEADER + row
    if mutation == "header":
        body = b"wrong\n" + row
    elif mutation == "missing":
        body = minute.HEADER
    elif mutation == "duplicate":
        body += row
    elif mutation == "unterminated":
        body = body[:-1]
    path.write_bytes(body)
    with pytest.raises((ValueError, UnicodeError)):
        auth._stream_projection(
            path,
            fabricated["monthly"],
            expected_sha256=sha256(body).hexdigest(),
            expected_bytes=len(body),
        )


@pytest.mark.parametrize("mutation", ["hash", "length", "excess", "truncated"])
def test_full_stream_end_validation(fabricated, tmp_path, mutation):
    path = fabricated["root"] / "minute/minute_opens.csv"
    digest, size = fabricated["pins"]["minute_csv"], fabricated["processed_bytes"]
    if mutation in ("excess", "truncated"):
        target = tmp_path.resolve() / "altered.csv"
        with path.open("rb") as src, target.open("wb") as dst:
            remaining = size - (1 if mutation == "truncated" else 0)
            while remaining:
                chunk = src.read(min(1024 * 1024, remaining))
                dst.write(chunk)
                remaining -= len(chunk)
            if mutation == "excess":
                dst.write(b"extra\n")
        path = target
    elif mutation == "hash":
        digest = fake("wrong-file")
    elif mutation == "length":
        size += 1
    with pytest.raises(ValueError):
        auth._stream_projection(
            path, fabricated["monthly"], expected_sha256=digest, expected_bytes=size
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "status",
        "flag",
        "overall",
        "missing_month",
        "extra_symbol",
        "february",
        "discrepancy",
        "structural",
        "schema",
        "extra_field",
        "nonempty_csv",
        "wrong_output_hash",
        "missing_file",
        "source",
        "audit_code",
        "integrity",
        "incomplete_snapshot",
        "source_link",
        "manifest_kind",
        "incomplete_provenance",
        "audit_size_link",
    ],
)
def test_parity_rejects_even_resealed_fabricated_claims(fabricated, mutation):
    bodies, pins = copy.deepcopy(fabricated["bodies"]), dict(fabricated["pins"])
    report, provenance, integrity = (
        json.loads(bodies[name])
        for name in ("parity_report.json", "provenance.json", "integrity.json")
    )
    if mutation == "status":
        report["status"] = "source_price_discrepancy"
    elif mutation == "flag":
        report["direct_timing_comparison_permitted"] = 1
    elif mutation == "overall":
        report["overall"]["equal_prices"] -= 1
    elif mutation == "missing_month":
        del report["per_month"]["2024-12"]
    elif mutation == "extra_symbol":
        report["per_symbol"]["XRPUSDT"] = count_group(8784)
    elif mutation == "february":
        report["per_symbol_month"]["BTCUSDT:2024-02"] = count_group(28 * 24)
    elif mutation == "discrepancy":
        report["discrepancies"] = [{"symbol": "BTCUSDT"}]
    elif mutation == "structural":
        report["structural_errors"] = ["missing"]
    elif mutation == "schema":
        report["schema"] = "synthetic_price_parity_fixture"
    elif mutation == "extra_field":
        report["matched_hours"] = []
    elif mutation == "source":
        provenance["source_manifests"]["minute"]["sources"][0]["sha256"] = fake(
            "wrong-source"
        )
    elif mutation == "audit_code":
        provenance["implementation_sha256"][parity.MINUTE_PROTOCOL] = fake("wrong-code")
    elif mutation == "integrity":
        integrity["after"][0]["manifest.json"]["stat"][3] += 1
    elif mutation == "incomplete_snapshot":
        del integrity["before"][0]["acquisition.json"]
    elif mutation == "source_link":
        provenance["integrity"]["sources"]["hourly"]["hourly_opens.csv"]["sha256"] = (
            fake("wrong-link")
        )
    elif mutation == "incomplete_provenance":
        del provenance["integrity"]["loaders"]
    elif mutation == "audit_size_link":
        name = "raw/BTCUSDT-1m-2024-01.zip"
        for phase in ("before", "after"):
            integrity[phase][1][name]["bytes"] += 1
            integrity[phase][1][name]["stat"][2] += 1
        provenance["integrity"]["sources"]["minute"][name]["bytes"] += 1
    bodies.update(
        {
            "parity_report.json": parity._json(report),
            "provenance.json": parity._json(provenance),
            "integrity.json": parity._json(integrity),
        }
    )
    if mutation == "nonempty_csv":
        bodies["discrepancies.csv"] += b"BTCUSDT,unexpected\n"
    if mutation == "missing_file":
        del bodies["integrity.json"]
    reseal(bodies, pins)
    if mutation in ("wrong_output_hash", "manifest_kind"):
        manifest = json.loads(bodies["manifest.json"])
        if mutation == "wrong_output_hash":
            manifest["files"]["provenance.json"]["sha256"] = fake("wrong-output")
        else:
            manifest["kind"] = "economic_results"
        bodies["manifest.json"] = parity._json(manifest)
        pins["parity_manifest"] = ident(bodies["manifest.json"])["sha256"]
    with pytest.raises((ValueError, KeyError)):
        auth._parity_evidence(
            bodies,
            pins,
            fabricated["monthly"],
            fabricated["audit_code"],
            fabricated["hourly_monthly"],
            fabricated["metadata"],
        )


def test_symlink_traversal_and_replace_races(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    path = root / "original"
    path.write_bytes(b"invented")
    link = root / "link"
    link.symlink_to(path)
    for target in (link, root / ".." / root.name / "original"):
        with pytest.raises(ValueError):
            auth._identity(target)
    with pytest.raises(ValueError, match="changed"):
        with auth._open_checked(path) as stream:
            stream.read()
            path.write_bytes(b"changed!")
    actual_open = os.open
    replacement = root / "replacement"
    replacement.write_bytes(b"invented")

    def race(name, *args, **kwargs):
        replacement.replace(path)
        return actual_open(name, *args, **kwargs)

    monkeypatch.setattr(os, "open", race)
    with pytest.raises(ValueError, match="replaced"):
        auth._identity(path)


@pytest.mark.parametrize(
    "mutation",
    [
        "external_pin",
        "genuine_pin",
        "code_pin",
        "code_root",
        "changed_csv",
        "missing_manifest",
        "extra_parity_file",
        "wrong_archive",
    ],
)
def test_preflight_fails_before_loaders(fabricated, mutation):
    args = arguments(fabricated)
    args["pins"] = dict(args["pins"])
    args["forecast_loader"] = args["minute_loader"] = forbidden
    path, original = None, None
    if mutation == "external_pin":
        args["pins"]["forecast_csv"] = fake("wrong-external")
    elif mutation == "genuine_pin":
        args["pins"]["forecast_csv"] = forecast.CSV_SHA256
    elif mutation == "code_pin":
        args["expected_code_sha256"] = {"minute_loader": fake("wrong-code")}
    elif mutation == "code_root":
        args["code_paths"] = {"minute_loader": Path("/etc/passwd")}
    else:
        names = {
            "changed_csv": "forecast/validation_predictions.csv",
            "missing_manifest": "forecast/manifest.json",
            "extra_parity_file": "parity/extra.json",
            "wrong_archive": "minute/raw/BTCUSDT-1m-2024-01.zip",
        }
        path = fabricated["root"] / names[mutation]
        original = path.read_bytes() if mutation != "extra_parity_file" else None
        if mutation == "missing_manifest":
            path.unlink()
        else:
            path.write_bytes(b"fabricated mutation")
    try:
        with pytest.raises((ValueError, FileNotFoundError)):
            auth._authenticate_fixture_inputs(**args)
    finally:
        if path:
            if original is None:
                path.unlink()
            else:
                path.write_bytes(original)


def test_changed_source_after_loader_detected(fabricated, isolated_policy):
    args = arguments(fabricated)
    path = fabricated["root"] / "forecast/manifest.json"
    original = path.read_bytes()

    def loader(directory, **kwargs):
        path.write_bytes(original + b"\n")
        return fabricated["metadata"]

    args["minute_loader"] = loader
    try:
        with pytest.raises(ValueError, match="changed after"):
            auth._authenticate_fixture_inputs(**args)
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("body", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'])
def test_ambiguous_json_refused(body):
    with pytest.raises(ValueError):
        auth._json(body)


@pytest.mark.parametrize(
    "mutation",
    [
        "status",
        "coverage",
        "implementation",
        "source_url",
        "source_count",
        "source_order",
        "processed_hash",
        "processed_size",
    ],
)
def test_native_metadata_contract(fabricated, mutation):
    metadata = copy.deepcopy(fabricated["metadata"])
    if mutation == "status":
        metadata["status"] = "approved"
    elif mutation == "coverage":
        metadata["coverage"]["total_rows"] -= 1
    elif mutation == "implementation":
        metadata["implementation_sha256"] = fake("changed")
    elif mutation == "source_url":
        metadata["sources"][0]["url"] = "https://example.invalid/"
    elif mutation == "source_count":
        metadata["sources"][1]["row_count"] -= 1440
    elif mutation == "source_order":
        metadata["sources"].reverse()
    elif mutation == "processed_hash":
        metadata["output"]["sha256"] = fake("changed")
    elif mutation == "processed_size":
        metadata["output"]["bytes"] += 1
    snapshot = {
        name: auth._identity(fabricated["root"] / "minute" / name)
        for name in auth._release_names("1m")
    }
    with pytest.raises(ValueError):
        auth._minute_metadata(
            metadata,
            snapshot,
            fabricated["monthly"],
            fabricated["pins"],
            fabricated["processed_bytes"],
            fabricated["code_hash"],
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "unexpected_field",
        "duplicate_horizon",
        "reordered_horizon",
        "nonfinite",
        "missing_model",
    ],
)
def test_original_loader_rejects_fabricated_csv_mutations(
    fabricated, isolated_policy, tmp_path, mutation
):
    root = tmp_path.resolve()
    body = (fabricated["root"] / "forecast/validation_predictions.csv").read_text()
    rows = list(csv.reader(io.StringIO(body)))
    if mutation == "unexpected_field":
        rows[1].append("unexpected")
    elif mutation == "duplicate_horizon":
        rows.insert(1, rows[1])
    elif mutation == "reordered_horizon":
        rows[1], rows[5] = rows[5], rows[1]
    elif mutation == "nonfinite":
        rows[3][7] = "Infinity"
    elif mutation == "missing_model":
        rows.pop(4)
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    body = output.getvalue().encode()
    manifest = copy.deepcopy(fabricated["manifest"])
    manifest["output_sha256"]["validation_predictions.csv"] = sha256(body).hexdigest()
    encoded = parity._json(manifest)
    (root / "manifest.json").write_bytes(encoded)
    (root / "validation_predictions.csv").write_bytes(body)
    with pytest.raises(ValueError):
        forecast.load_forecasts(
            root,
            expected_csv_sha256=sha256(body).hexdigest(),
            expected_manifest_sha256=sha256(encoded).hexdigest(),
        )


def test_changed_code_after_loader_detected(fabricated, isolated_policy):
    args = arguments(fabricated)
    path = fabricated["code"]
    original = path.read_bytes()

    def loader(directory, **kwargs):
        path.write_bytes(original + b"# changed\n")
        return fabricated["metadata"]

    args["minute_loader"] = loader
    try:
        with pytest.raises(ValueError, match="Code changed"):
            auth._authenticate_fixture_inputs(**args)
    finally:
        path.write_bytes(original)


def test_all_frozen_declarations_and_source_tables():
    # Tracked documents only. No retained artifact byte identities are observed.
    doc = (ROOT / parity.PIN_DOCUMENT).read_bytes()
    assert sha256(doc).hexdigest() == auth.EXTERNAL_PINS["minute_pin_document"]
    monthly = parity._minute_pins(doc)
    assert len(monthly) == 24
    assert sum(r["row_count"] for r in monthly.values()) == 1054080
    assert sum(r["zip_bytes"] for r in monthly.values()) == 49948389
    assert sum(r["checksum_bytes"] for r in monthly.values()) == 2112
    assert auth.EXTERNAL_PINS["forecast_manifest"] == forecast.MANIFEST_SHA256
    assert auth.EXTERNAL_PINS["forecast_csv"] == forecast.CSV_SHA256
    for path, key in (
        (parity.HOURLY_PROTOCOL, "hourly_protocol"),
        (parity.MINUTE_PROTOCOL, "minute_protocol"),
    ):
        assert sha256((ROOT / path).read_bytes()).hexdigest() == auth.EXTERNAL_PINS[key]


def test_bounded_projection_retention(fabricated):
    import tracemalloc

    tracemalloc.start()
    try:
        references = auth._stream_projection(
            fabricated["root"] / "minute/minute_opens.csv",
            fabricated["monthly"],
            expected_sha256=fabricated["pins"]["minute_csv"],
            expected_bytes=fabricated["processed_bytes"],
        )
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert sum(map(len, references)) == 21958
    # Million-row materialisation would vastly exceed this bound. Prices/rows are
    # discarded while streaming; only the required projection survives.
    assert peak < 32 * 1024 * 1024
    print(f"Projection peak traced Python allocation: {peak} bytes")

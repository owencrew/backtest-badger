"""Plan/checklist tests only; native/publisher regressions stay in the old suites."""

import ast
import builtins
import dataclasses
import inspect
import io
import os
import subprocess
import sys
import types
from hashlib import sha256
from pathlib import Path

import pytest
import test_genuine_minute_inputs as fixtures
import test_genuine_minute_verification_operator as operator_tests

from backtest_badger import genuine_minute_inputs as auth
from backtest_badger import genuine_minute_verification_operator as operator
from backtest_badger import genuine_minute_verification_wiring as wiring

offline = fixtures.offline
no_economics = operator_tests.no_economics


def document():
    return (auth.ROOT / wiring.PIN_DOCUMENT).read_bytes()


def test_cold_module_execution_and_default_apis_do_not_import_operators_or_do_io(
    monkeypatch,
):
    # Execute a fresh module body after intercepting all I/O, including resolution.
    source = Path(wiring.__file__).read_text()
    module = types.ModuleType("_isolated_wiring_test")
    monkeypatch.setitem(sys.modules, module.__name__, module)
    original_import = builtins.__import__

    def importing(name, *args, **kwargs):
        assert not name.startswith("backtest_badger")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importing)
    for obj, names in (
        (builtins, ("open",)),
        (io, ("open",)),
        (os, ("open", "stat", "lstat", "listdir", "scandir", "mkdir")),
        (Path, ("resolve",)),
        (subprocess, ("Popen",)),
    ):
        for name in names:
            monkeypatch.setattr(obj, name, fixtures.forbidden)
    exec(compile(source, "<isolated-wiring>", "exec"), module.__dict__)
    plan = module.verification_plan()
    readiness = module.approval_readiness()
    assert not plan.executable
    assert readiness.access == "NO_SOURCE_ACCESS"


def test_binding_contracts_and_original_default_pins():
    plan = wiring.verification_plan()
    bindings = {b.role: b for b in plan.bindings}
    functions = {
        "forecast_loader": auth.forecast.load_forecasts,
        "lineage_validator": auth.policy._validate_lineage,
        "minute_loader": auth.minute.load_minute_execution_data,
        "projection": auth._stream_projection,
        "prior_publication": auth._parity_evidence,
    }
    for role, function in functions.items():
        binding = bindings[role]
        assert binding.target == f"{function.__module__}.{function.__name__}"
        inspect.signature(function).bind(
            *binding.arguments, **dict(binding.literal_keywords)
        )
    assert bindings["forecast_loader"].literal_keywords == ()
    defaults = inspect.signature(auth.forecast.load_forecasts).parameters
    assert (
        defaults["expected_manifest_sha256"].default
        == auth.EXTERNAL_PINS["forecast_manifest"]
    )
    assert defaults["expected_csv_sha256"].default == auth.EXTERNAL_PINS["forecast_csv"]
    assert dict(bindings["minute_loader"].literal_keywords) == {
        "expected_manifest_sha256": auth.EXTERNAL_PINS["minute_manifest"]
    }
    assert dict(bindings["projection"].literal_keywords) == {
        "expected_sha256": auth.EXTERNAL_PINS["minute_csv"],
        "expected_bytes": 107002277,
    }
    assert plan.result_type.endswith(".AuthenticatedMinuteInputs")
    assert plan.execution_authorised is plan.executable is False
    assert dict(plan.roots) == {
        "forecast": auth.FORECAST_PATH,
        "minute": auth.MINUTE_PATH,
        "parity": auth.PARITY_PATH,
    }
    assert plan.destination == operator.DESTINATION
    assert dict(plan.required_flags) == {
        "verification_only": True,
        "single_attempt": True,
        "resume": False,
        "strategy_authorised": False,
        "economic_publication_authorised": False,
    }


def test_exact_declarations_and_57_file_inventory():
    result = wiring.approval_readiness(minute_pin_document=document())
    pins = dict(result.declarations)
    assert {key: pins[key] for key in auth.EXTERNAL_PINS} == auth.EXTERNAL_PINS
    assert len(result.sources) == 57
    groups = {
        group: {r.name: r for r in result.sources if r.group == group}
        for group in ("forecast", "minute", "parity")
    }
    assert set(groups["forecast"]) == {"manifest.json", "validation_predictions.csv"}
    assert set(groups["minute"]) == auth._release_names("1m")
    assert set(groups["parity"]) == set(auth.PARITY_FILES)
    assert all(r.sha256 is not None for r in result.sources)
    assert [(r.group, r.name) for r in result.sources if r.bytes is None] == [
        ("forecast", "manifest.json"),
        ("forecast", "validation_predictions.csv"),
    ]
    assert groups["minute"]["manifest.json"].bytes == 19749
    assert groups["minute"]["minute_opens.csv"].bytes == 107002277
    # Independent retained tracked guide, never any original publication file.
    guide = (auth.ROOT / "docs/stage-04b2d1-genuine-price-parity-audit.md").read_text()
    for row in groups["parity"].values():
        assert f"| `{row.name}` | {row.bytes:,} | `{row.sha256}` |" in guide
    monthly = {(s, m): dict(row) for s, m, row in result.monthly_sources}
    assert monthly == auth.parity._minute_pins(document())
    assert list(monthly) == [(r.symbol, r.month) for r in auth.minute.minute_requests()]
    assert sum(r["row_count"] for r in monthly.values()) == 1054080
    for request in auth.minute.minute_requests():
        row = monthly[request.symbol, request.month]
        assert row["url"] == request.url
        assert row["checksum_url"] == request.checksum_url
        assert row["row_count"] == request.row_count
        for suffix, hash_key, size_key in (
            ("", "sha256", "zip_bytes"),
            (".CHECKSUM", "checksum_sha256", "checksum_bytes"),
        ):
            identity = groups["minute"][f"raw/{request.stem}.zip{suffix}"]
            assert (identity.sha256, identity.bytes) == (row[hash_key], row[size_key])


def test_readiness_never_claims_independent_approval_or_fills_unknown_evidence():
    incomplete = wiring.approval_readiness()
    declared = wiring.approval_readiness(minute_pin_document=document())
    assert len(incomplete.sources) == 57
    assert sum(r.sha256 is None for r in incomplete.sources) == 48
    for report in (incomplete, declared):
        assert (report.status, report.readiness, report.access) == (
            "NOT_APPROVED",
            "NOT_READY",
            "NO_SOURCE_ACCESS",
        )
        assert report.dependencies == operator.DEPENDENCIES
        assert len(report.missing_evidence) >= 14
        for fragment in (
            "forecast_manifest_byte_length",
            "forecast_csv_byte_length",
            "future_commit",
            "successful_ci",
            "hashes_and_lengths",
            "dependency_versions",
            "destination_absence",
            "owner_one_read_only",
            "complete_prior_auditor",
            "monthly_identities",
        ):
            assert any(fragment in item for item in report.missing_evidence)
        with pytest.raises(dataclasses.FrozenInstanceError):
            report.readiness = "READY"
        with pytest.raises(ValueError):
            dataclasses.replace(report, status="APPROVED")
    # Supplying the independently pinned tracked document resolves just its tables.
    assert set(incomplete.missing_evidence) - set(declared.missing_evidence) == {
        "hash_verified_tracked_minute_pin_document_tables"
    }
    assert declared == wiring.approval_readiness(minute_pin_document=document())


@pytest.mark.parametrize(
    "field",
    [
        *sorted(operator.APPROVAL_FIELDS),
        "owner_authorisation",
        "clean",
        "allow_genuine",
        "ready",
        "forecast_manifest_bytes",
        "forecast_csv_bytes",
        "source_path",
    ],
)
def test_template_has_no_candidate_authority_or_self_pinning_parameters(field):
    # Rejection occurs at Python argument binding, even for malicious values.
    with pytest.raises(TypeError):
        wiring.approval_readiness(**{field: operator_tests.Malicious()})


@pytest.mark.parametrize("value", [b"", b"fabricated", b"{}", b"\x00", "malicious"])
def test_document_type_and_literal_pin_checked_before_parser(value, monkeypatch):
    monkeypatch.setattr(auth.parity, "_minute_pins", fixtures.forbidden)
    if value == "malicious":
        value = operator_tests.Malicious()
    with pytest.raises((TypeError, ValueError)):
        wiring.approval_readiness(minute_pin_document=value)


def test_modified_frozen_document_cannot_be_resealed_or_reassociated(monkeypatch):
    body = document()
    for altered in (
        body + b"\n",
        body.replace(b"19749", b"19748"),
        body.replace(b"BTCUSDT-1m-2024-01", b"ETHUSDT-1m-2024-01"),
        body.replace(b"2026-10-18T05:17:44", b"2023-10-18T05:17:44"),
    ):
        with pytest.raises(ValueError, match="identity"):
            wiring.approval_readiness(minute_pin_document=altered)
    # The only parser call uses verified supplied bytes, with file I/O disabled.
    for obj, name in ((builtins, "open"), (io, "open"), (os, "stat"), (os, "lstat")):
        monkeypatch.setattr(obj, name, fixtures.forbidden)
    assert (
        len(wiring.approval_readiness(minute_pin_document=body).monthly_sources) == 24
    )


def test_both_public_gates_reject_all_plan_and_readiness_representations(monkeypatch):
    records = (
        wiring.verification_plan(),
        wiring.approval_readiness(minute_pin_document=document()),
    )
    candidates = [operator_tests.Malicious()]
    for record in records:
        candidates.extend((record, dataclasses.asdict(record)))
    monkeypatch.setattr(operator, "_validate_approval", fixtures.forbidden)
    monkeypatch.setattr(auth, "_safe", fixtures.forbidden)
    for function in (
        operator.run_genuine_minute_verification,
        auth.authenticate_minute_inputs,
    ):
        body = ast.parse(inspect.getsource(function)).body[0].body
        assert isinstance(body[1], ast.Raise)  # First statement after docstring.
        for candidate in candidates:
            with pytest.raises(PermissionError):
                function(approval=candidate)


def test_process_guard_is_effective_without_function_fixture_patches():
    # A separate process installs the same pre-collection guard, then really calls
    # the guarded APIs. No monkeypatched per-test path/network stubs are involved.
    script = """
import os, runpy, socket
from pathlib import Path
suite = runpy.run_path('tests/test_genuine_minute_inputs.py')
suite['install_offline_audit']()
root = suite['ROOT']
paths = [
    root / 'artifacts',
    root / 'artifacts/experiments/stage-2b-v1/manifest.json',
    root / 'artifacts/execution/binance-1m-2024-v1',
    root / 'artifacts/audits/stage-04b2d1-native-parity-v1',
    root / 'artifacts/audits/stage-04b2d3-minute-inputs-v1',
    root.parent / 'crypto-trading-platform',
]
checked = 0
for path in paths:
    for operation in (
        lambda: open(path, 'rb'),
        lambda: os.open(path, os.O_RDONLY),
        lambda: os.stat(path),
        lambda: os.lstat(path),
        lambda: os.listdir(path),
        lambda: os.scandir(path),
    ):
        try:
            operation()
        except AssertionError:
            checked += 1
        else:
            raise AssertionError('Process path guard did not fire')
for operation in (
    lambda: socket.getaddrinfo('example.invalid', 443),
    lambda: socket.create_connection(('127.0.0.1', 1)),
    lambda: suite['psycopg'].connect(''),
):
    try:
        operation()
    except AssertionError:
        checked += 1
    else:
        raise AssertionError('Process network/database guard did not fire')
assert checked == 39
print('39 process boundary checks blocked before access')
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=auth.ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "39 process boundary checks blocked before access"


def test_readiness_is_not_accepted_by_private_fixture_approval(tmp_path):
    for candidate in (
        wiring.approval_readiness(),
        dataclasses.asdict(wiring.approval_readiness()),
        dataclasses.asdict(wiring.verification_plan()),
    ):
        with pytest.raises(ValueError, match="Incomplete approval"):
            operator._validate_approval(candidate, tmp_path)


def test_proposed_code_inventory_covers_existing_and_transitive_imports():
    names = set(wiring.IMPLEMENTATION_FILES)
    assert set(operator.IMPLEMENTATION_FILES) <= names
    assert len(names) == len(wiring.IMPLEMENTATION_FILES)
    pending = [
        "genuine_minute_verification_operator",
        "genuine_minute_verification_wiring",
    ]
    seen = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        path = f"src/backtest_badger/{name}.py"
        assert path in names
        for node in ast.walk(ast.parse((auth.ROOT / path).read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "backtest_badger":
                    pending.extend(alias.name for alias in node.names)
                elif node.module.startswith("backtest_badger."):
                    pending.append(node.module.split(".")[1])
            elif isinstance(node, ast.Import):
                pending.extend(
                    alias.name.split(".")[1]
                    for alias in node.names
                    if alias.name.startswith("backtest_badger.")
                )
    assert {"pyproject.toml", "uv.lock", ".python-version"} <= names


def test_existing_callable_seam_with_fabricated_forecasts_and_injected_metadata(
    tmp_path, monkeypatch
):
    """Plumbing test, explicitly NOT native ZIP revalidation or publication.

    Old full-year operator tests separately use the unchanged native loader and
    all 24 fabricated ZIPs. Do not duplicate their million-row fixture here.
    """
    root = tmp_path.resolve()
    for group in ("forecast", "minute", "parity"):
        (root / group).mkdir()
    pins = {key: fixtures.fake(key) for key in auth.EXTERNAL_PINS}
    body = fixtures.forecast_bytes(pins)
    (root / "forecast/validation_predictions.csv").write_bytes(body)
    pins["forecast_csv"] = sha256(body).hexdigest()
    manifest = fixtures.recipe(pins)
    body = auth.policy.json_bytes(manifest)
    (root / "forecast/manifest.json").write_bytes(body)
    pins["forecast_manifest"] = sha256(body).hexdigest()
    metadata = {"fixture": "injected_metadata_only_not_archive_revalidation"}
    body = auth.policy.json_bytes(metadata)
    (root / "minute/manifest.json").write_bytes(body)
    pins["minute_manifest"] = sha256(body).hexdigest()
    before = {"minute": {}, "parity": {}}
    for name in auth.PARITY_FILES:
        (root / "parity" / name).write_bytes(b"{}")
        before["parity"][name] = fixtures.ident(b"{}")
    operator_tests.pin_policy(monkeypatch, {"pins": pins})
    calls = []

    def forecasts(path):
        calls.append("forecast_loader")
        assert path == root / "forecast"
        return auth.forecast.load_forecasts(
            path,
            expected_manifest_sha256=pins["forecast_manifest"],
            expected_csv_sha256=pins["forecast_csv"],
        )

    def lineage(value):
        calls.append("lineage_validator")
        assert value == manifest  # Original fabricated manifest, no translation.
        return auth.policy._validate_lineage(value)

    def native(path, *, expected_manifest_sha256):
        calls.append("minute_loader")
        assert path == root / "minute"
        assert expected_manifest_sha256 == pins["minute_manifest"]
        return metadata

    def projection(path, monthly, *, expected_sha256, expected_bytes):
        calls.append("projection")
        assert path == root / "minute/minute_opens.csv"
        assert expected_sha256 == pins["minute_csv"] and expected_bytes == 123
        assert monthly == {}
        return (), ()

    def parity(bodies, declared, monthly, audit_code, hourly, minute_metadata):
        calls.append("prior_publication")
        assert set(bodies) == set(auth.PARITY_FILES)
        assert declared == pins and minute_metadata == metadata
        return {}, {}, {}

    monkeypatch.setattr(auth, "_minute_metadata", lambda *args: None)
    monkeypatch.setattr(auth, "_stream_projection", projection)
    monkeypatch.setattr(auth, "_parity_evidence", parity)
    result = operator._verify_sources(
        root,
        {
            "pins": pins,
            "monthly_sources": [],
            "hourly_monthly": [],
            "audit_code": {},
            "input_inventory": {"minute": {"minute_opens.csv": {"bytes": 123}}},
            "implementation": {
                "src/backtest_badger/minute_execution_data.py": {
                    "sha256": fixtures.fake("code")
                }
            },
        },
        before,
        forecast_loader=forecasts,
        minute_loader=native,
        lineage_validator=lineage,
        native_loader_evidence=metadata["fixture"],
    )
    assert calls == [
        "lineage_validator",
        "forecast_loader",
        "minute_loader",
        "projection",
        "prior_publication",
    ]
    assert set(calls) == {b.role for b in wiring.verification_plan().bindings}
    assert len(result.forecasts) == 8
    assert all(len(account) == 2195 for account in result.forecasts)
    assert result.genuine_execution_authorised is False
    evidence = auth._json(result.source_evidence_json)
    assert evidence["source_kind"] == "fabricated_temporary_fixture_bytes"
    assert evidence["native_loader_evidence"] == metadata["fixture"]
    assert not (root / "output").exists()

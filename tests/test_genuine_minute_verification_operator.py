"""Strictly invented bytes. Whole-grid success; bounded publisher fault injection."""

import ast
import copy
import json
import os
import shutil
import socket
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import psycopg
import pytest
import test_genuine_minute_inputs as fixtures
import test_minute_execution_data as native

from backtest_badger import genuine_minute_inputs as auth
from backtest_badger import genuine_minute_verification_operator as operator
from backtest_badger import minute_execution_data as minute

# Reuse the executed I/O guard, without modifying or collecting the old tests twice.
offline = fixtures.offline


@pytest.fixture(autouse=True)
def no_economics(monkeypatch):
    from backtest_badger import paper_accounting, paper_execution, paper_strategy

    for module, names in (
        (auth.policy, ("evaluate_bundle", "benchmark", "summarize_account")),
        (paper_accounting, ("replay", "reconcile", "apply_trade", "fund_account")),
        (paper_execution, ("calculate_trade",)),
        (paper_strategy, ("evaluate_strategy",)),
        (minute, ("download_minute_archive", "_fetch")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, fixtures.forbidden)


def pin_policy(monkeypatch, data):
    monkeypatch.setattr(auth.forecast, "RESEARCH_SHA256", data["pins"]["research_csv"])
    for name, key in (
        ("RESEARCH_SHA256", "research_csv"),
        ("RESEARCH_MANIFEST_SHA256", "research_manifest"),
        ("FORECAST_SHA256", "forecast_csv"),
    ):
        monkeypatch.setattr(auth.policy, name, data["pins"][key])


@pytest.fixture(scope="module")
def source_fixture(tmp_path_factory):
    # The pre-existing fixture creates invented forecasts and genuine-auditor-
    # shaped evidence. Replace its fake ZIP bytes with complete fabricated ZIPs.
    data = fixtures.fabricated.__wrapped__(tmp_path_factory)
    root = data["root"]
    sources, monthly = [], {}
    with (root / "minute/minute_opens.csv").open("wb") as output:
        output.write(minute.HEADER)
        for request in minute.minute_requests():
            body, sidecar, observed = native.synthetic_download(request)
            fragment, source = minute.verify_minute_archive(
                request, body, sidecar, observed
            )
            output.write(fragment)
            for suffix, payload in ((".zip", body), (".zip.CHECKSUM", sidecar)):
                (root / "minute/raw" / (request.stem + suffix)).write_bytes(payload)
            sources.append(source)
            monthly[request.symbol, request.month] = {
                k: v
                for k, v in source.items()
                if k
                not in {
                    "symbol",
                    "month",
                    "interval",
                    "observation_kind",
                    "validation_status",
                }
            }
    data["pins"]["minute_csv"] = auth._identity(root / "minute/minute_opens.csv")[
        "sha256"
    ]
    data["processed_bytes"] = (root / "minute/minute_opens.csv").stat().st_size
    # Reviewed implementation *fixture* files have externally supplied test bytes.
    # The unchanged native loader binds its own file digest, so that one is copied.
    code = {}
    for name in operator.IMPLEMENTATION_FILES:
        body = (
            (auth.ROOT / name).read_bytes()
            if name == "src/backtest_badger/minute_execution_data.py"
            else ("# invented reviewed implementation: " + name + "\n").encode()
        )
        path = root / "code" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        code[name] = fixtures.ident(body)
    for name, key in (
        (auth.parity.HOURLY_PROTOCOL, "hourly_protocol"),
        (auth.parity.MINUTE_PROTOCOL, "minute_protocol"),
        (auth.parity.PIN_DOCUMENT, "minute_pin_document"),
    ):
        data["pins"][key] = code[name]["sha256"]
        data["audit_code"][name] = code[name]["sha256"]
    metadata = minute._manifest(
        sources,
        data["pins"]["minute_csv"],
        data["processed_bytes"],
        code["src/backtest_badger/minute_execution_data.py"]["sha256"],
    )
    body = minute._json(metadata)
    (root / "minute/manifest.json").write_bytes(body)
    data["pins"]["minute_manifest"] = sha256(body).hexdigest()
    data.update(metadata=metadata, monthly=monthly, implementation=code)
    snapshots = {
        n: auth._identity(root / "minute" / n) for n in auth._release_names("1m")
    }
    data["bodies"] = fixtures.publication(
        data["pins"],
        monthly,
        metadata,
        snapshots,
        data["audit_code"],
        data["hourly_monthly"],
    )
    for name, body in data["bodies"].items():
        (root / "parity" / name).write_bytes(body)
    data["inventory"] = {
        g: operator._without_stats(s)
        for g, s in auth._inventory(
            *(root / n for n in ("forecast", "minute", "parity"))
        ).items()
    }
    return data


def approve(data, root):
    return {
        "schema": operator.SCHEMA,
        "source_kind": operator.SOURCE_KIND,
        "commit": "d" * 40,  # Invented reviewed commit/CI, never a real CI claim.
        "ci": {
            "commit": "d" * 40,
            "run_id": "123",
            "status": "completed",
            "conclusion": "success",
        },
        "runtime": {
            "python": "3.12.TEST",
            "implementation": "CPython-TEST",
            "dependencies": {name: "TEST-1" for name in operator.DEPENDENCIES},
        },
        "implementation": data["implementation"],
        "roots": {n: str(root / n) for n in ("forecast", "minute", "parity")},
        "destination": str(root / "output"),
        "input_inventory": data["inventory"],
        "pins": data["pins"],
        "monthly_sources": [[s, m, v] for (s, m), v in data["monthly"].items()],
        "hourly_monthly": [[s, m, v] for (s, m), v in data["hourly_monthly"].items()],
        "audit_code": data["audit_code"],
        "verification_only": True,
        "strategy_authorised": False,
        "economic_publication_authorised": False,
        "single_attempt": True,
        "resume": False,
    }


def bindings(data, root):
    approval = copy.deepcopy(approve(data, root))

    def forecast_loader(directory):
        assert directory == root / "forecast"
        return auth.forecast.load_forecasts(
            directory,
            expected_csv_sha256=data["pins"]["forecast_csv"],
            expected_manifest_sha256=data["pins"]["forecast_manifest"],
        )

    return {
        "fixture_root": root,
        "approval": approval,
        "forecast_loader": forecast_loader,
        "minute_loader": minute.load_minute_execution_data,
        "lineage_validator": auth.policy._validate_lineage,
        "environment_reader": lambda _: {
            "commit": "d" * 40,
            "clean": True,
            "runtime": copy.deepcopy(approval["runtime"]),
        },
        "native_loader_evidence": (
            "unchanged_loader_full_fabricated_archive_revalidation"
        ),
    }


@pytest.fixture
def case(source_fixture, tmp_path, monkeypatch):
    root = tmp_path.resolve() / "fixture"
    root.mkdir()
    # Copies use hard links only to save disk. Mutations below replace a link first.
    for name in ("forecast", "minute", "parity", "code"):
        shutil.copytree(
            source_fixture["root"] / name, root / name, copy_function=os.link
        )
    pin_policy(monkeypatch, source_fixture)
    return bindings(source_fixture, root)


def replace_bytes(path, body):
    path.unlink()
    path.write_bytes(body)


@pytest.fixture(scope="module")
def verified(source_fixture):
    """Exactly one full native-loader + bounded projector + publisher success."""
    with pytest.MonkeyPatch.context() as patch:
        pin_policy(patch, source_fixture)
        # Fixture setup precedes function fixtures; explicitly install real guards.
        guard = fixtures.offline.__wrapped__(patch)
        assert guard is None
        args = bindings(source_fixture, source_fixture["root"])
        events = []

        def checkpoint(phase):
            events.append(phase)
            if phase == "before_manifest":
                assert not (source_fixture["root"] / "output/manifest.json").exists()
                assert set(os.listdir(source_fixture["root"] / "output")) == {
                    "authenticated_inputs.json",
                    "integrity.json",
                }

        patch.setattr(operator, "_checkpoint", checkpoint)
        result = operator._run_fixture_verification(**args)
        return result, events


def test_full_native_success_and_manifest_last(source_fixture, verified):
    result, events = verified
    root = source_fixture["root"] / "output"
    manifest = json.loads((root / "manifest.json").read_bytes())
    science = (root / "authenticated_inputs.json").read_bytes()
    assert manifest["kind"] == "source_authentication_only"
    assert manifest["complete"] is True
    assert manifest["genuine_execution_authorised"] is False
    assert manifest["economic_results"] is False
    assert manifest["source_kind"] == operator.SOURCE_KIND
    assert set(os.listdir(root)) == {"manifest.json", *manifest["files"]}
    for name, identity in manifest["files"].items():
        assert fixtures.ident((root / name).read_bytes()) == identity
    assert science == auth.authenticated_inputs_json(result)
    assert auth.scientific_json(auth._json(science)).encode("ascii") == science
    assert result.genuine_execution_authorised is False
    assert len(result.forecasts) == 8
    assert all(len(rows) == 2195 for rows in result.forecasts)
    assert all(len(rows) == 10979 for rows in result.references)
    assert (
        sum(
            r.at.month == 2 and r.at.day == 29 and r.at.minute == 0
            for rows in result.references
            for r in rows
        )
        == 48
    )
    evidence = auth._json(result.source_evidence_json)
    assert evidence["counts"]["native_rows"] == 1054080
    assert evidence["native_loader_evidence"] == (
        "unchanged_loader_full_fabricated_archive_revalidation"
    )
    assert evidence["parity_report"]["overall"]["equal_prices"] == 17568
    assert events.index("after_output_readback") < events.index("before_manifest")
    assert events[-1] == "after_manifest"
    with pytest.raises(ValueError):
        fixtures.SYNTHETIC_REPLAY(
            "BTCUSDT",
            result.forecasts[2],
            result.references[0],
            source=result,
            expected_source_sha256=fixtures.fake("x"),
            forecast_sha256=source_fixture["pins"]["forecast_csv"],
            model_recipe_sha256=source_fixture["pins"]["forecast_manifest"],
        )


def test_reproduction_on_copied_sources(case, source_fixture, verified):
    # A second full real verification path, on copies with different inode/stats.
    result = operator._run_fixture_verification(**case)
    first = source_fixture["root"] / "output"
    second = case["fixture_root"] / "output"
    assert result == verified[0]
    assert (first / "authenticated_inputs.json").read_bytes() == (
        second / "authenticated_inputs.json"
    ).read_bytes()
    assert (first / "integrity.json").read_bytes() != (
        second / "integrity.json"
    ).read_bytes()


class Malicious:
    def __getattribute__(self, name):
        fixtures.forbidden()

    def __bool__(self):
        fixtures.forbidden()

    def __fspath__(self):
        fixtures.forbidden()

    def __str__(self):
        fixtures.forbidden()


@pytest.mark.parametrize(
    "function",
    [operator.run_genuine_minute_verification, auth.authenticate_minute_inputs],
)
@pytest.mark.parametrize("approval", [None, True, "approved", "malicious", {}])
def test_closed_gates(function, approval, monkeypatch):
    if type(approval) is str and approval == "malicious":
        approval = Malicious()
    monkeypatch.setattr(auth, "_safe", fixtures.forbidden)
    monkeypatch.setattr(operator, "_validate_approval", fixtures.forbidden)
    with pytest.raises(PermissionError):
        function(approval=approval)


def test_apparently_complete_approval_still_refused(case, monkeypatch):
    monkeypatch.setattr(auth, "_safe", fixtures.forbidden)
    for function in (
        operator.run_genuine_minute_verification,
        auth.authenticate_minute_inputs,
    ):
        with pytest.raises(PermissionError):
            function(approval=case["approval"])


@pytest.mark.parametrize("field", sorted(operator.APPROVAL_FIELDS))
def test_every_approval_field_required(case, field):
    del case["approval"][field]
    with pytest.raises(ValueError):
        operator._run_fixture_verification(**case)
    assert not (case["fixture_root"] / "output").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "commit",
        "ci_commit",
        "ci_failed",
        "ci_missing",
        "authority",
        "resume",
        "source_kind",
        "missing_pin",
        "genuine_pin",
        "document_link",
        "source_inventory",
        "implementation_inventory",
        "implementation_hash",
        "implementation_size",
        "runtime",
        "monthly_order",
        "hourly_order",
        "audit_code",
        "destination",
        "traversal",
        "wrong_root",
        "dirty",
        "nonboolean_clean",
        "changed_head",
        "changed_runtime",
    ],
)
def test_preflight_rejections_without_sources_or_reservation(
    case, monkeypatch, mutation
):
    a = case["approval"]
    if mutation == "commit":
        a["commit"] = "short"
    elif mutation == "ci_commit":
        a["ci"]["commit"] = "e" * 40
    elif mutation == "ci_failed":
        a["ci"]["conclusion"] = "failure"
    elif mutation == "ci_missing":
        del a["ci"]["run_id"]
    elif mutation == "authority":
        a["strategy_authorised"] = True
    elif mutation == "resume":
        a["resume"] = True
    elif mutation == "source_kind":
        a["source_kind"] = "genuine"
    elif mutation == "missing_pin":
        del a["pins"]["research_csv"]
    elif mutation == "genuine_pin":
        a["pins"]["research_csv"] = auth.EXTERNAL_PINS["research_csv"]
    elif mutation == "document_link":
        a["pins"]["minute_pin_document"] = fixtures.fake("unlinked document")
    elif mutation == "source_inventory":
        a["input_inventory"]["forecast"]["labels.csv"] = fixtures.ident(b"forbidden")
    elif mutation == "implementation_inventory":
        a["implementation"].pop("uv.lock")
    elif mutation in ("implementation_hash", "implementation_size"):
        a["implementation"]["uv.lock"][
            "sha256" if mutation.endswith("hash") else "bytes"
        ] = fixtures.fake("changed") if mutation.endswith("hash") else 1
    elif mutation == "runtime":
        del a["runtime"]["dependencies"]["numpy"]
    elif mutation in ("monthly_order", "hourly_order"):
        a[
            "monthly_sources" if mutation == "monthly_order" else "hourly_monthly"
        ].reverse()
    elif mutation == "audit_code":
        a["audit_code"].pop("uv.lock")
    elif mutation == "destination":
        a["destination"] += "-alternative"
    elif mutation == "traversal":
        case["fixture_root"] = case["fixture_root"] / ".." / "fixture"
    elif mutation == "wrong_root":
        a["roots"]["forecast"] = str(auth.ROOT / auth.FORECAST_PATH)
    else:
        current = case["environment_reader"](None)
        if mutation in ("dirty", "nonboolean_clean"):
            current["clean"] = False if mutation == "dirty" else 1
        elif mutation == "changed_head":
            current["commit"] = "f" * 40
        else:
            current["runtime"]["python"] = "changed"
        case["environment_reader"] = lambda _: current
    monkeypatch.setattr(operator, "_source_snapshot", fixtures.forbidden)
    with pytest.raises((ValueError, KeyError)):
        operator._run_fixture_verification(**case)
    assert not (Path(a["destination"]).parent / "output").exists()


@pytest.mark.parametrize("kind", ["directory", "file", "broken_symlink", "symlink"])
def test_existing_output_never_mutated(case, kind, monkeypatch):
    output = case["fixture_root"] / "output"
    if kind == "directory":
        output.mkdir()
        (output / "sentinel").write_bytes(b"preserve")
    elif kind == "file":
        output.write_bytes(b"preserve")
    else:
        output.symlink_to(
            case["fixture_root"] / ("missing" if kind == "broken_symlink" else "code")
        )
    before = output.lstat()
    monkeypatch.setattr(operator, "_source_snapshot", fixtures.forbidden)
    with pytest.raises(FileExistsError):
        operator._run_fixture_verification(**case)
    assert output.lstat() == before


@pytest.mark.parametrize("name", ["forecast", "minute", "parity", "code"])
def test_symlink_ancestor_preflight(case, name):
    root = case["fixture_root"]
    (root / name).rename(root / (name + "-original"))
    (root / name).symlink_to(root / (name + "-original"))
    with pytest.raises(ValueError, match="Symlink"):
        operator._run_fixture_verification(**case)
    assert not (root / "output").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "deleted",
        "extra_minute",
        "extra_raw",
        "extra_parity",
        "changed_forecast",
        "changed_manifest",
        "zip",
        "sidecar",
        "source_symlink",
    ],
)
def test_exact_source_inventory_and_external_bytes(case, mutation, monkeypatch):
    root = case["fixture_root"]
    names = {
        "deleted": "parity/integrity.json",
        "changed_forecast": "forecast/validation_predictions.csv",
        "changed_manifest": "forecast/manifest.json",
        "zip": "minute/raw/BTCUSDT-1m-2024-01.zip",
        "sidecar": "minute/raw/BTCUSDT-1m-2024-01.zip.CHECKSUM",
        "source_symlink": "parity/provenance.json",
    }
    if mutation.startswith("extra"):
        directory = {
            "extra_minute": "minute",
            "extra_raw": "minute/raw",
            "extra_parity": "parity",
        }[mutation]
        (root / directory / "unexpected").write_bytes(b"unexpected")
    else:
        path = root / names[mutation]
        if mutation == "deleted":
            path.unlink()
        elif mutation == "source_symlink":
            path.unlink()
            path.symlink_to(root / "forecast/manifest.json")
        else:
            replace_bytes(path, b"altered bytes")
    monkeypatch.setattr(operator, "_verify_sources", fixtures.forbidden)
    with pytest.raises((ValueError, FileNotFoundError)):
        operator._run_fixture_verification(**case)
    assert not (root / "output/manifest.json").exists()
    assert json.loads((root / "output/failure.json").read_bytes())["complete"] is False


@pytest.fixture
def publisher_case(case, verified, monkeypatch):
    # Explicit publisher-only boundary: reuse an actually verified immutable record.
    # These fault tests do NOT claim to rerun native authentication for each phase.
    monkeypatch.setattr(operator, "_verify_sources", lambda *a, **k: verified[0])
    return case


PHASES = [
    "after_reservation",
    "source_verification",
    "after_verification",
    *[
        f"{event}:{name}"
        for name in ("authenticated_inputs.json", "integrity.json", "manifest.json")
        for event in ("create", "partial", "link", "linked")
    ],
    "output_readback",
    "after_output_readback",
    "before_manifest",
    "after_manifest",
]


@pytest.mark.parametrize("phase", ["before_reservation", *PHASES])
def test_failure_at_every_publication_phase(publisher_case, monkeypatch, phase):
    case = publisher_case
    output = case["fixture_root"] / "output"

    def fail(value):
        if value == phase:
            raise RuntimeError("secret content and /private/secret/path")

    monkeypatch.setattr(operator, "_checkpoint", fail)
    with pytest.raises(RuntimeError):
        operator._run_fixture_verification(**case)
    if phase == "before_reservation":
        assert not output.exists()
        return
    assert not (output / "manifest.json").exists()
    failure_body = (output / "failure.json").read_bytes()
    assert json.loads(failure_body) == {
        "schema": "minute-input-incomplete-attempt-v1",
        "phase": phase,
        "exception_type": "Exception",
        "complete": False,
        "resume": False,
    }
    assert b"secret" not in failure_body
    snapshot = {p.name: auth._identity(p) for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        operator._run_fixture_verification(**case)
    assert {p.name: auth._identity(p) for p in output.iterdir()} == snapshot


@pytest.mark.parametrize(
    "phase",
    [
        "after_verification",
        "after_output_readback",
        "before_manifest",
        "after_manifest",
    ],
)
@pytest.mark.parametrize(
    "mutation", ["bytes", "inode", "code", "unexpected", "deleted", "environment"]
)
def test_preservation_across_all_boundaries(
    publisher_case, monkeypatch, phase, mutation
):
    case = publisher_case
    root = case["fixture_root"]
    environment = case["environment_reader"](None)
    case["environment_reader"] = lambda _: environment

    def change(value):
        if value != phase:
            return
        path = root / (
            "code/uv.lock" if mutation == "code" else "forecast/manifest.json"
        )
        if mutation in ("inode", "code"):
            replace_bytes(path, path.read_bytes())
        elif mutation == "bytes":
            replace_bytes(path, b"changed")
        elif mutation == "unexpected":
            (root / "minute/extra").write_bytes(b"changed")
        elif mutation == "deleted":
            path.unlink()
        else:
            environment["clean"] = False

    monkeypatch.setattr(operator, "_checkpoint", change)
    with pytest.raises((ValueError, FileNotFoundError)):
        operator._run_fixture_verification(**case)
    assert not (root / "output/manifest.json").exists()
    assert (root / "output/failure.json").exists()


def test_forecast_not_listed_and_no_source_writes(publisher_case, monkeypatch):
    case = publisher_case
    listing = os.listdir
    opening = os.open
    root = case["fixture_root"]

    def listdir(path):
        assert Path(path) != root / "forecast"
        return listing(path)

    def open_file(path, flags, *args, **kwargs):
        if isinstance(path, Path) and path.is_relative_to(root):
            assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        return opening(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "listdir", listdir)
    monkeypatch.setattr(os, "open", open_file)
    (root / "forecast/labels-never-open").write_bytes(b"unrelated")
    operator._run_fixture_verification(**case)


@pytest.mark.parametrize(
    "name", ["authenticated_inputs.json", "integrity.json", "manifest.json"]
)
def test_corrupt_output_readback_invalidates(publisher_case, monkeypatch, name):
    root = publisher_case["fixture_root"]

    def corrupt(phase):
        if phase == (
            "after_manifest" if name == "manifest.json" else "output_readback"
        ):
            # Preserve owned inode so cleanup can safely remove its success marker.
            (root / "output" / name).write_bytes(b'{"forged":true}\n')

    monkeypatch.setattr(operator, "_checkpoint", corrupt)
    with pytest.raises(ValueError):
        operator._run_fixture_verification(**publisher_case)
    assert not (root / "output/manifest.json").exists()


@pytest.mark.parametrize(
    "name", ["authenticated_inputs.json", "integrity.json", "manifest.json"]
)
def test_exclusive_collision_never_overwrites(publisher_case, monkeypatch, name):
    root = publisher_case["fixture_root"]

    def collide(phase):
        if phase == "link:" + name:
            (root / "output" / name).write_bytes(b"external collision")

    monkeypatch.setattr(operator, "_checkpoint", collide)
    with pytest.raises(FileExistsError):
        operator._run_fixture_verification(**publisher_case)
    assert (root / "output" / name).read_bytes() == b"external collision"
    assert (root / "output/failure.json").exists()


def test_fsync_failure_keeps_partial(publisher_case, monkeypatch):
    monkeypatch.setattr(
        os, "fsync", lambda _: (_ for _ in ()).throw(OSError("private"))
    )
    with pytest.raises(OSError):
        operator._run_fixture_verification(**publisher_case)
    root = publisher_case["fixture_root"] / "output"
    assert (root / "authenticated_inputs.json.partial").exists()
    assert not (root / "manifest.json").exists()


def test_atomic_reservation_race_not_retried(case, monkeypatch):
    output = case["fixture_root"] / "output"

    def race(phase):
        if phase == "before_reservation":
            output.mkdir()
            (output / "sentinel").write_bytes(b"other attempt")

    monkeypatch.setattr(operator, "_checkpoint", race)
    with pytest.raises(FileExistsError):
        operator._run_fixture_verification(**case)
    assert set(os.listdir(output)) == {"sentinel"}


def test_moved_output_anchored_writes(publisher_case, monkeypatch):
    root = publisher_case["fixture_root"]
    outside = root / "outside"
    outside.mkdir()

    def move(phase):
        if phase == "partial:authenticated_inputs.json":
            (root / "output").rename(root / "moved")
            (root / "output").symlink_to(outside)

    monkeypatch.setattr(operator, "_checkpoint", move)
    with pytest.raises(ValueError):
        operator._run_fixture_verification(**publisher_case)
    assert not list(outside.iterdir())
    assert (root / "moved/failure.json").exists()


def test_real_io_blocks_are_executed():
    for operation in (
        lambda: (auth.ROOT / auth.FORECAST_PATH).stat(),
        lambda: os.listdir(auth.ROOT / "artifacts"),
        lambda: (auth.ROOT.parent / "crypto-trading-platform/test").read_bytes(),
        lambda: socket.create_connection(("127.0.0.1", 1)),
        lambda: psycopg.connect(""),
    ):
        with pytest.raises(AssertionError):
            operation()


def test_transitive_project_import_inventory():
    pending, seen = ["genuine_minute_verification_operator"], set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        path = f"src/backtest_badger/{name}.py"
        assert path in operator.IMPLEMENTATION_FILES
        for node in ast.walk(ast.parse((auth.ROOT / path).read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "backtest_badger":
                    pending.extend(alias.name for alias in node.names)
                elif node.module.startswith("backtest_badger."):
                    pending.append(node.module.split(".")[1])


def test_provenance_crosscheck_cannot_bless_changed_record(
    publisher_case, verified, monkeypatch
):
    record = verified[0]
    evidence = auth._json(record.source_evidence_json)
    evidence["pins"]["forecast_csv"] = fixtures.fake("forged")
    monkeypatch.setattr(
        operator,
        "_verify_sources",
        lambda *a, **k: replace(record, source_evidence_json=operator._json(evidence)),
    )
    with pytest.raises(ValueError, match="disagrees"):
        operator._run_fixture_verification(**publisher_case)
    assert not (publisher_case["fixture_root"] / "output/manifest.json").exists()


@pytest.mark.parametrize(
    "name", ["authenticated_inputs.json", "integrity.json", "manifest.json"]
)
def test_existing_partial_is_never_resumed(publisher_case, monkeypatch, name):
    output = publisher_case["fixture_root"] / "output"

    def collide(phase):
        if phase == "create:" + name:
            (output / (name + ".partial")).write_bytes(b"prior partial")

    monkeypatch.setattr(operator, "_checkpoint", collide)
    with pytest.raises(FileExistsError):
        operator._run_fixture_verification(**publisher_case)
    assert (output / (name + ".partial")).read_bytes() == b"prior partial"
    assert not (output / "manifest.json").exists()


def test_interruption_after_manifest_link(publisher_case, monkeypatch):
    def interrupt(phase):
        if phase == "linked:manifest.json":
            raise KeyboardInterrupt

    monkeypatch.setattr(operator, "_checkpoint", interrupt)
    with pytest.raises(KeyboardInterrupt):
        operator._run_fixture_verification(**publisher_case)
    output = publisher_case["fixture_root"] / "output"
    assert not (output / "manifest.json").exists()
    assert (output / "manifest.json.partial").exists()
    assert (
        auth._json((output / "failure.json").read_bytes())["exception_type"]
        == "KeyboardInterrupt"
    )


def test_git_runtime_observation_is_read_only_and_exact(tmp_path, monkeypatch):
    calls = []

    def command(args, *, cwd, env):
        calls.append(args)
        assert cwd == tmp_path
        assert env["GIT_OPTIONAL_LOCKS"] == "0"
        return b"d" * 40 + b"\n" if args[1] == "rev-parse" else b""

    monkeypatch.setattr(operator.subprocess, "check_output", command)
    monkeypatch.setattr(operator.platform, "python_version", lambda: "3.12.TEST")
    monkeypatch.setattr(operator.platform, "python_implementation", lambda: "CPython")
    monkeypatch.setattr(operator.importlib.metadata, "version", lambda _: "TEST")
    result = operator._read_environment(tmp_path)
    assert result["commit"] == "d" * 40
    assert result["clean"] is True
    assert set(result["runtime"]["dependencies"]) == set(operator.DEPENDENCIES)
    assert calls == [
        ["git", "rev-parse", "HEAD"],
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
    ]

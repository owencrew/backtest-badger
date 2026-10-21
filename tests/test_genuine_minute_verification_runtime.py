"""Fabricated signatures/sources only; no owner-signed approval or genuine run."""

import builtins
import copy
import io
import json
import os
import shutil
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest
import test_genuine_minute_inputs as fixtures
import test_genuine_minute_signed_approval as signatures
import test_genuine_minute_verification_operator as legacy

from backtest_badger import genuine_minute_verification_runtime as runtime

signed = runtime.signed
operator = runtime.operator
auth = runtime.auth
wiring = runtime.wiring
offline = fixtures.offline
no_economics = legacy.no_economics
keys = signatures.keys
# One full-year native fixture per module; every case hard-links these bytes.
source_fixture = legacy.source_fixture


def original_shaped_payload():
    """Known declarations + explicitly INVENTED missing lengths/identities; no I/O."""
    payload = signatures.complete_payload()
    payload["pins"] = dict(wiring.DECLARATIONS)
    # Reading a frozen tracked document is permitted; never an original artifact.
    declared = wiring.approval_readiness(
        minute_pin_document=(auth.ROOT / wiring.PIN_DOCUMENT).read_bytes()
    )
    for row in declared.sources:
        payload["input_inventory"][row.group][row.name] = {
            "sha256": row.sha256,
            "bytes": row.bytes if row.bytes is not None else 123,
        }
    payload["monthly_sources"] = [
        [s, m, dict(v)] for s, m, v in declared.monthly_sources
    ]
    payload["hourly_monthly"] = [
        [s, m, v] for (s, m), v in sorted(auth.policy.MONTHLY_ZIP_SHA256.items())
    ]
    for name, key in (
        (auth.parity.HOURLY_PROTOCOL, "hourly_protocol"),
        (auth.parity.MINUTE_PROTOCOL, "minute_protocol"),
        (wiring.PIN_DOCUMENT, "minute_pin_document"),
    ):
        payload["implementation"][name]["sha256"] = payload["pins"][key]
        payload["audit_code"][name] = payload["pins"][key]
    payload["audit_code"]["src/backtest_badger/genuine_minute_price_parity.py"] = (
        "d4b3fb3f9f06b553fce0f1303a61bc4483feb2d90840573c9c33ac9e5523d092"
    )
    return payload


def document(keys, payload):
    return signatures.wire(signatures.envelope(keys, payload))


def install_test_trust(monkeypatch, keys):
    monkeypatch.setattr(signed, "TRUSTED_OWNER_PUBLIC_KEY", keys[1])
    monkeypatch.setattr(signed, "TRUSTED_OWNER_KEY_ID", keys[2])


def all_io_forbidden(patch):
    for module, names in (
        (builtins, ("open",)),
        (io, ("open",)),
        (os, ("open", "stat", "lstat", "listdir", "scandir", "mkdir")),
        (subprocess, ("Popen",)),
    ):
        for name in names:
            patch.setattr(module, name, fixtures.forbidden)


def test_unenrolled_runtime_refuses_every_claim_before_inspection(keys, monkeypatch):
    assert signed.TRUSTED_OWNER_PUBLIC_KEY != keys[1]
    assert signed.TRUSTED_OWNER_KEY_ID != keys[2]
    good = document(keys, original_shaped_payload())
    for key, key_id in ((None, None), (None, keys[2]), (keys[1], None)):
        monkeypatch.setattr(signed, "TRUSTED_OWNER_PUBLIC_KEY", key)
        monkeypatch.setattr(signed, "TRUSTED_OWNER_KEY_ID", key_id)
        with monkeypatch.context() as patch:
            all_io_forbidden(patch)
            patch.setattr(signed, "_verify_envelope", fixtures.forbidden)
            patch.setattr(runtime, "_prepare_and_operate", fixtures.forbidden)
            for value in (
                signatures.Malicious(),
                good,
                {},
                True,
                {"trusted_digest": sha256(good).hexdigest()},
                wiring.verification_plan(),
                wiring.approval_readiness(),
            ):
                with pytest.raises(PermissionError):
                    runtime.run_genuine_minute_verification(approval=value)


def test_enrolled_preflight_is_pure_detached_and_not_ci_attestation(keys, monkeypatch):
    payload = original_shaped_payload()
    candidate = document(keys, payload)
    install_test_trust(monkeypatch, keys)
    with monkeypatch.context() as patch:
        all_io_forbidden(patch)
        detached = signed.preflight_owner_approval(approval=candidate)
    assert detached == signatures.wire(payload)
    payload["ci"]["run_id"] = "999999"  # Another owner declaration, not fetched CI.
    assert (
        json.loads(signed.preflight_owner_approval(approval=document(keys, payload)))[
            "ci"
        ]["run_id"]
        == "999999"
    )
    assert json.loads(detached)["ci"]["run_id"] == signatures.RUN


@pytest.mark.parametrize("path,value", signatures.MUTATIONS)
def test_public_signature_covers_every_authority_field(keys, monkeypatch, path, value):
    candidate = signatures.envelope(keys, original_shaped_payload())
    target = candidate
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    body = signatures.wire(candidate)
    install_test_trust(monkeypatch, keys)
    with monkeypatch.context() as patch:
        all_io_forbidden(patch)
        with pytest.raises(ValueError):
            signed.preflight_owner_approval(approval=body)


@pytest.mark.parametrize(
    "kind",
    [
        "missing_length",
        "extra_file",
        "runtime",
        "code",
        "ci",
        "hourly",
        "auditor",
        "flags",
        "wrong_key",
        "noncanonical",
        "oversized",
        "malicious",
    ],
)
def test_signed_bad_authority_refuses_before_runtime(keys, monkeypatch, kind):
    payload = original_shaped_payload()
    if kind == "missing_length":
        del payload["input_inventory"]["forecast"]["manifest.json"]["bytes"]
    elif kind == "extra_file":
        payload["input_inventory"]["forecast"]["labels.csv"] = fixtures.ident(b"no")
    elif kind == "runtime":
        payload["runtime"]["dependencies"].pop("cffi")
    elif kind == "code":
        payload["implementation"].pop("uv.lock")
    elif kind == "ci":
        payload["ci"]["commit"] = "b" * 40
    elif kind == "hourly":
        payload["hourly_monthly"][0][2] = signatures.invented("wrong hourly")
    elif kind == "auditor":
        payload["audit_code"]["src/backtest_badger/genuine_minute_price_parity.py"] = (
            signatures.invented("wrong auditor")
        )
    elif kind == "flags":
        payload["strategy_authorised"] = True
    body = document(keys, payload)
    if kind == "noncanonical":
        body += b"\n"
    elif kind == "oversized":
        body = b" " * (signed.MAX_DOCUMENT_BYTES + 1)
    elif kind == "malicious":
        body = signatures.Malicious()
    install_test_trust(monkeypatch, keys)
    if kind == "wrong_key":
        monkeypatch.setattr(signed, "TRUSTED_OWNER_KEY_ID", "sha256:" + "0" * 64)
    with monkeypatch.context() as patch:
        all_io_forbidden(patch)
        patch.setattr(runtime, "_prepare_and_operate", fixtures.forbidden)
        with pytest.raises(ValueError):
            runtime.run_genuine_minute_verification(approval=body)


def test_public_route_binds_original_functions_without_overrides(keys, monkeypatch):
    install_test_trust(monkeypatch, keys)
    candidate = document(keys, original_shaped_payload())
    observed = []

    def inspect(approved, **bindings):
        observed.append(bindings)
        assert approved["pins"] == dict(wiring.DECLARATIONS)
        assert bindings == {
            "checkout": auth.ROOT,
            "source_kind": operator._SourceKind.GENUINE,
            "environment_reader": runtime._read_environment,
            "declaration_reader": runtime._declared_sources,
            "forecast_loader": auth.forecast.load_forecasts,
            "lineage_validator": auth.policy._validate_lineage,
        }
        raise RuntimeError("test stops before any production observation")

    monkeypatch.setattr(runtime, "_prepare_and_operate", inspect)
    with pytest.raises(RuntimeError):
        runtime.run_genuine_minute_verification(approval=candidate)
    assert len(observed) == 1
    for name in (
        "public_key",
        "key_id",
        "environment_reader",
        "checkout",
        "source_kind",
        "forecast_loader",
        "allow_genuine",
    ):
        with pytest.raises(TypeError):
            runtime.run_genuine_minute_verification(approval=candidate, **{name: None})


def make_case(source_fixture, tmp_path, monkeypatch, keys):
    checkout = tmp_path.resolve() / "synthetic-test-checkout"
    checkout.mkdir()
    payload = signatures.complete_payload()
    payload.update(
        copy.deepcopy(legacy.approve(source_fixture, source_fixture["root"]))
    )
    payload["schema"] = signed.PAYLOAD_SCHEMA
    payload["source_kind"] = operator._SourceKind.GENUINE.value
    payload["runtime"] = signatures.complete_payload()["runtime"]
    payload["roots"] = {n: str(checkout / p) for n, p in wiring.ROOTS}
    payload["destination"] = str(checkout / wiring.DESTINATION)
    for group, relative in wiring.ROOTS:
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            source_fixture["root"] / group, destination, copy_function=os.link
        )
    for name in signed.IMPLEMENTATION_FILES:
        source = source_fixture["root"] / "code" / name
        target = checkout / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if name in source_fixture["implementation"]:
            os.link(source, target)
        else:
            target.write_bytes(
                ("# synthetic_test code/document: " + name + "\n").encode()
            )
        payload["implementation"][name] = operator._without_stats(
            {name: auth._identity(target)}
        )[name]
    for name, key in (
        ("provenance.json", "parity_provenance"),
        ("integrity.json", "parity_integrity"),
        ("discrepancies.csv", "parity_discrepancies"),
    ):
        payload["pins"][key] = payload["input_inventory"]["parity"][name]["sha256"]
    external = copy.deepcopy(payload)
    declarations = wiring.Readiness(
        tuple(
            wiring.SourceDeclaration(g, n, v["sha256"], v["bytes"], "synthetic_test")
            for g, items in external["input_inventory"].items()
            for n, v in items.items()
        ),
        tuple((s, m, tuple(v.items())) for s, m, v in external["monthly_sources"]),
        ("synthetic_test_not_owner_evidence",),
        declarations=tuple(external["pins"].items()),
    )
    legacy.pin_policy(monkeypatch, source_fixture)

    def forecasts(path):
        assert path == Path(external["roots"]["forecast"])
        return auth.forecast.load_forecasts(
            path,
            expected_csv_sha256=external["pins"]["forecast_csv"],
            expected_manifest_sha256=external["pins"]["forecast_manifest"],
        )

    return {
        "payload": payload,
        "keys": keys,
        "bindings": {
            "checkout": checkout,
            "source_kind": operator._SourceKind.SYNTHETIC_TEST,
            "environment_reader": lambda _: {
                "commit": external["commit"],
                "clean": True,
                "runtime": copy.deepcopy(external["runtime"]),
            },
            "declaration_reader": lambda _: declarations,
            "forecast_loader": forecasts,
            "lineage_validator": auth.policy._validate_lineage,
        },
    }


@pytest.fixture
def case(source_fixture, tmp_path, monkeypatch, keys):
    return make_case(source_fixture, tmp_path, monkeypatch, keys)


def run_test(case):
    # Real Ed25519 verification under ephemeral private TEST trust; never production
    # constants, public invocation, or a fabricated record relabelled as genuine.
    detached = signed._verify_envelope(
        document=document(case["keys"], case["payload"]),
        public_key=case["keys"][1],
        key_id=case["keys"][2],
    )
    return runtime._prepare_and_operate(json.loads(detached), **case["bindings"])


@pytest.fixture(scope="module")
def verified(source_fixture, tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        fixtures.offline.__wrapped__(patch)
        legacy.no_economics.__wrapped__(patch)
        case = make_case(
            source_fixture,
            tmp_path_factory.mktemp("signed-native"),
            patch,
            signatures.keys.__wrapped__(),
        )
        return verify_full_native(case, patch)


def verify_full_native(case, monkeypatch):
    payload = case["payload"]
    output = Path(payload["destination"])
    original_open = os.open
    original_list = os.listdir
    phases = []

    def opening(path, flags, *args, **kwargs):
        if isinstance(path, Path) and any(
            path.is_relative_to(Path(root)) for root in payload["roots"].values()
        ):
            assert output.is_dir(), "Source opened before destination reservation"
            assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        return original_open(path, flags, *args, **kwargs)

    def listing(path):
        assert Path(path) != Path(payload["roots"]["forecast"])
        return original_list(path)

    monkeypatch.setattr(os, "open", opening)
    monkeypatch.setattr(os, "listdir", listing)
    monkeypatch.setattr(operator, "_checkpoint", phases.append)
    result = run_test(case)
    return result, payload, phases


def test_full_native_signed_test_route(verified):
    result, payload, phases = verified
    output = Path(payload["destination"])
    evidence = json.loads(result.source_evidence_json)
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert (
        evidence["source_kind"]
        == manifest["source_kind"]
        == operator._SourceKind.SYNTHETIC_TEST.value
    )
    assert (
        evidence["native_loader_evidence"]
        == "synthetic_test_unchanged_loader_full_fabricated_archive_revalidation"
    )
    assert len(result.forecasts) == 8 and all(len(a) == 2195 for a in result.forecasts)
    assert sum(map(len, result.references)) == 21958
    assert evidence["counts"]["native_rows"] == 1054080
    assert evidence["parity_report"]["overall"]["equal_prices"] == 17568
    assert manifest["kind"] == "source_authentication_only"
    assert (
        manifest["economic_results"]
        is manifest["genuine_execution_authorised"]
        is False
    )
    assert set(os.listdir(output)) == {
        "manifest.json",
        "integrity.json",
        "authenticated_inputs.json",
    }
    for name, identity in manifest["files"].items():
        assert fixtures.ident((output / name).read_bytes()) == identity
    assert phases[-1] == "after_manifest"
    assert phases.index("after_output_readback") < phases.index("create:manifest.json")
    assert signed.TRUSTED_OWNER_PUBLIC_KEY is not None
    assert signed.TRUSTED_OWNER_KEY_ID is not None
    with pytest.raises(ValueError):
        fixtures.SYNTHETIC_REPLAY(
            "BTCUSDT",
            result.forecasts[2],
            result.references[0],
            source=result,
            expected_source_sha256=fixtures.fake("no"),
            forecast_sha256=payload["pins"]["forecast_csv"],
            model_recipe_sha256=payload["pins"]["forecast_manifest"],
        )


@pytest.mark.parametrize(
    "kind",
    [
        "git",
        "dirty",
        "runtime",
        "package",
        "code_hash",
        "code_size",
        "source_hash",
        "source_size",
        "monthly",
        "destination",
        "source_kind",
        "forecast_length",
        "auditor",
    ],
)
def test_pre_source_checks_on_valid_test_signatures(case, kind, monkeypatch):
    payload = case["payload"]
    if kind in ("git", "dirty", "runtime", "package"):
        env = case["bindings"]["environment_reader"](None)
        if kind == "git":
            env["commit"] = "f" * 40
        elif kind == "dirty":
            env["clean"] = False
        elif kind == "runtime":
            env["runtime"]["python"] = "3.12.99"
        else:
            env["runtime"]["dependencies"]["cryptography"] = "99.0.0"
        case["bindings"]["environment_reader"] = lambda _: env
    elif kind in ("code_hash", "code_size"):
        payload["implementation"]["uv.lock"][
            "sha256" if kind == "code_hash" else "bytes"
        ] = signatures.invented("code") if kind == "code_hash" else 1
    elif kind == "source_hash":
        payload["pins"]["forecast_csv"] = signatures.invented("forecast")
        payload["input_inventory"]["forecast"]["validation_predictions.csv"][
            "sha256"
        ] = payload["pins"]["forecast_csv"]
    elif kind == "source_size":
        payload["input_inventory"]["forecast"]["manifest.json"]["bytes"] += 1
    elif kind == "monthly":
        payload["monthly_sources"][0][2]["observed_at"] = "2026-01-01T00:00:00+00:00"
    elif kind == "destination":
        payload["destination"] += "-other"
    elif kind == "source_kind":
        payload["source_kind"] = operator.SOURCE_KIND
    elif kind == "forecast_length":
        del payload["input_inventory"]["forecast"]["manifest.json"]["bytes"]
    else:
        payload["audit_code"].pop("uv.lock")
    monkeypatch.setattr(runtime, "_check_source_paths", fixtures.forbidden)
    monkeypatch.setattr(operator, "_publish", fixtures.forbidden)
    with pytest.raises((ValueError, KeyError)):
        run_test(case)


@pytest.mark.parametrize(
    "kind", ["symlink", "collision", "extra_minute", "extra_parity", "missing_file"]
)
def test_paths_refuse_before_original_open(case, monkeypatch, kind):
    roots = case["payload"]["roots"]
    output = Path(case["payload"]["destination"])
    if kind == "symlink":
        path = Path(roots["minute"])
        path.rename(path.with_name("moved"))
        path.symlink_to(path.with_name("moved"))
    elif kind == "collision":
        output.mkdir()
    elif kind.startswith("extra"):
        Path(
            roots["minute" if kind == "extra_minute" else "parity"], "extra"
        ).write_bytes(b"bad")
    else:
        Path(roots["parity"], "integrity.json").unlink()
    monkeypatch.setattr(runtime, "_source_snapshot", fixtures.forbidden)
    with pytest.raises((ValueError, FileExistsError, FileNotFoundError)):
        run_test(case)
    assert not (output / "manifest.json").exists()


def test_real_runtime_observer_has_no_ci_or_source_discovery(monkeypatch):
    calls = []

    def git(checkout, *args):
        calls.append(args)
        assert checkout == auth.ROOT
        if args == ("rev-parse", "--show-toplevel"):
            return str(auth.ROOT) + "\n"
        if args == ("rev-parse", "HEAD"):
            return "a" * 40 + "\n"
        if args == ("ls-files", "--stage", "-z"):
            return "100644 " + "a" * 40 + " 0\tuv.lock\0"
        if args == ("ls-files", "-v", "-z"):
            return "H uv.lock\0"
        assert args == (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            ".",
            ":(exclude)artifacts",
        )
        return ""

    monkeypatch.setattr(runtime, "_git", git)
    result = runtime._read_environment(auth.ROOT)
    assert result["clean"] is True
    assert set(result["runtime"]["dependencies"]) == signed.DEPENDENCIES
    assert result["runtime"]["dependencies"]["cryptography"].startswith("46.")
    assert len(calls) == 5
    assert "ci" not in result


@pytest.mark.parametrize(
    "stage", ["tracked_artifact", "skip_worktree", "assume_unchanged"]
)
def test_git_rejects_hidden_or_source_entries_before_status(monkeypatch, stage):
    def git(checkout, *args):
        if args == ("rev-parse", "--show-toplevel"):
            return str(checkout)
        if args == ("ls-files", "--stage", "-z"):
            return (
                "100644 "
                + "a" * 40
                + " 0\t"
                + ("artifacts/protected" if stage == "tracked_artifact" else "uv.lock")
                + "\0"
            )
        if args == ("ls-files", "-v", "-z"):
            return ("S" if stage == "skip_worktree" else "h") + " uv.lock\0"
        pytest.fail("Unexpected Git observation")

    monkeypatch.setattr(runtime, "_git", git)
    with pytest.raises(ValueError):
        runtime._read_environment(auth.ROOT)


@pytest.fixture
def publication_case(case, verified, monkeypatch):
    # Publisher fault injection reuses a truly full-native TEST record. This is
    # never described as repeated native revalidation at every failure point.
    monkeypatch.setattr(operator, "_verify_source_roots", lambda *a, **k: verified[0])
    return case


@pytest.mark.parametrize("phase", ["before_reservation", *legacy.PHASES])
def test_signed_route_publication_failure_phases(publication_case, monkeypatch, phase):
    output = Path(publication_case["payload"]["destination"])

    def fail(value):
        if value == phase:
            raise RuntimeError("secret /private/secret source row")

    monkeypatch.setattr(operator, "_checkpoint", fail)
    with pytest.raises(RuntimeError):
        run_test(publication_case)
    if phase == "before_reservation":
        assert not output.exists()
        return
    assert not (output / "manifest.json").exists()
    body = (output / "failure.json").read_bytes()
    assert b"secret" not in body and json.loads(body)["complete"] is False
    before = {p.name: auth._identity(p) for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        run_test(publication_case)
    assert before == {p.name: auth._identity(p) for p in output.iterdir()}


@pytest.mark.parametrize(
    "phase",
    [
        "after_verification",
        "after_output_readback",
        "before_manifest",
        "after_manifest",
    ],
)
@pytest.mark.parametrize("target", ["source", "code", "runtime"])
def test_signed_route_pre_post_preservation(
    publication_case, monkeypatch, phase, target
):
    case = publication_case
    output = Path(case["payload"]["destination"])
    environment = case["bindings"]["environment_reader"](None)
    case["bindings"]["environment_reader"] = lambda _: environment

    def mutate(value):
        if value != phase:
            return
        if target == "runtime":
            environment["runtime"]["dependencies"]["cryptography"] = "99.0.0"
            return
        path = (
            case["bindings"]["checkout"] / "uv.lock"
            if target == "code"
            else Path(case["payload"]["roots"]["forecast"]) / "manifest.json"
        )
        legacy.replace_bytes(path, path.read_bytes())

    monkeypatch.setattr(operator, "_checkpoint", mutate)
    with pytest.raises(ValueError):
        run_test(case)
    assert not (output / "manifest.json").exists()
    assert (output / "failure.json").exists()


@pytest.mark.parametrize(
    "kind", [operator._SourceKind.FIXTURE, operator._SourceKind.GENUINE]
)
def test_other_route_record_cannot_be_published(
    publication_case, verified, monkeypatch, kind
):
    from dataclasses import replace

    record = verified[0]
    evidence = json.loads(record.source_evidence_json)
    evidence["source_kind"] = kind.value
    wrong = replace(record, source_evidence_json=operator._json(evidence))
    monkeypatch.setattr(operator, "_verify_source_roots", lambda *a, **k: wrong)
    with pytest.raises(ValueError, match="disagrees"):
        run_test(publication_case)
    output = Path(publication_case["payload"]["destination"])
    assert not (output / "manifest.json").exists()


def test_fabricated_route_cannot_accept_real_pins_or_checkout(case, monkeypatch):
    monkeypatch.setattr(runtime, "_code_snapshot", fixtures.forbidden)
    case["bindings"]["checkout"] = auth.ROOT
    case["payload"]["roots"] = {n: str(auth.ROOT / p) for n, p in wiring.ROOTS}
    case["payload"]["destination"] = str(auth.ROOT / wiring.DESTINATION)
    with pytest.raises(ValueError, match="Isolated"):
        run_test(case)


def test_process_guard_and_temporary_io(tmp_path):
    for operation in (
        lambda: os.stat(auth.ROOT / auth.FORECAST_PATH),
        lambda: os.lstat(auth.ROOT / wiring.DESTINATION),
        lambda: os.open(auth.ROOT / auth.MINUTE_PATH, os.O_RDONLY),
        lambda: os.listdir(auth.ROOT / auth.PARITY_PATH),
        lambda: os.stat(auth.ROOT.parent / "crypto-trading-platform"),
    ):
        with pytest.raises(AssertionError):
            operation()
    path = tmp_path / "fabricated.txt"
    path.write_bytes(b"fabricated")
    assert path.read_bytes() == b"fabricated" and path.stat().st_size == 10


def test_cold_runtime_import_has_guard_before_project_imports(tmp_path):
    import sys

    script = r"""
import ast, os, sys
from pathlib import Path
import psycopg
root = Path.cwd()
assert not any(n.startswith('backtest_badger') for n in sys.modules)
tree = ast.parse((root / 'tests/test_genuine_minute_inputs.py').read_text())
keep = {'forbidden', 'check_path', 'install_offline_audit'}
guard = ast.Module(body=[n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name in keep], type_ignores=[])
namespace = dict(os=os, sys=sys, Path=Path, psycopg=psycopg, ROOT=root)
exec(compile(guard, '<preimport guard>', 'exec'), namespace)
namespace['install_offline_audit']()
from backtest_badger import genuine_minute_verification_runtime as runtime
class Untrusted:
    def __getattribute__(self, name): raise AssertionError('argument inspected')
try: runtime.run_genuine_minute_verification(approval=Untrusted())
except ValueError: pass
else: raise AssertionError('invalid approval accepted')
for path in (root / 'artifacts', root.parent / 'crypto-trading-platform'):
    for operation in (lambda: path.stat(), lambda: path.lstat(),
                      lambda: os.listdir(path), lambda: os.open(path, os.O_RDONLY)):
        try: operation()
        except AssertionError: pass
        else: raise AssertionError('protected path touched')
safe = Path(sys.argv[1]) / 'synthetic.txt'
safe.write_bytes(b'synthetic')
assert safe.read_bytes() == b'synthetic'
print('guarded cold runtime and temporary I/O passed')
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=auth.ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "guarded cold runtime and temporary I/O passed"


def test_enrolled_owner_public_key_identity():
    expected = bytes.fromhex(
        "9b22dba87d87cd5d4fa5c6db7948eb3d117ae3ad17b7956a3b0b71d5ba4c18a9"
    )
    expected_id = (
        "sha256:503ebad4f2d36152e2fdc8d71a9b8cbaf2cede3804e6293d7a939f65578abe43"
    )
    assert type(signed.TRUSTED_OWNER_PUBLIC_KEY) is bytes
    assert signed.TRUSTED_OWNER_PUBLIC_KEY == expected
    assert len(expected) == 32
    assert signed.TRUSTED_OWNER_KEY_ID == expected_id
    assert "sha256:" + sha256(expected).hexdigest() == expected_id


@pytest.mark.parametrize(
    "kind",
    [
        "ephemeral_key",
        "forged_owner_id",
        "altered_signature",
        "missing_signature",
        "malformed_signature",
        "fake_key_id",
        "public_key",
        "key_fingerprint",
        "trusted_digest",
        "trust_store",
        "missing_manifest_length",
        "missing_forecast_length",
        "unsigned_payload",
        "incomplete_payload",
        "noncanonical",
        "malicious",
        "missing",
    ],
)
def test_enrolled_public_apis_reject_without_any_io(keys, monkeypatch, kind):
    # All signed bytes come from unrelated ephemeral TEST keys. Even a valid
    # test signature over the published owner ID cannot authenticate as the owner.
    candidate = signatures.envelope(keys)
    assert signatures.verify(keys, signatures.wire(candidate))
    assert keys[1] != signed.TRUSTED_OWNER_PUBLIC_KEY
    if kind != "ephemeral_key":
        candidate["key_id"] = signed.TRUSTED_OWNER_KEY_ID
        authenticated = {n: candidate[n] for n in ("schema", "key_id", "payload")}
        candidate["signature"] = (
            keys[0].sign(signed.DOMAIN + signatures.wire(authenticated)).hex()
        )
    if kind == "altered_signature":
        candidate["signature"] = "00" * 64
    elif kind == "missing_signature":
        del candidate["signature"]
    elif kind == "malformed_signature":
        candidate["signature"] = "invalid"
    elif kind == "fake_key_id":
        candidate["key_id"] = "sha256:" + "0" * 64
    elif kind in ("public_key", "key_fingerprint", "trusted_digest", "trust_store"):
        candidate[kind] = keys[1].hex()
    elif kind in ("missing_manifest_length", "missing_forecast_length"):
        name = (
            "manifest.json"
            if kind == "missing_manifest_length"
            else "validation_predictions.csv"
        )
        del candidate["payload"]["input_inventory"]["forecast"][name]["bytes"]
    elif kind == "incomplete_payload":
        candidate["payload"] = {}
    body = signatures.wire(candidate)
    if kind == "unsigned_payload":
        body = signatures.wire(candidate["payload"])
    elif kind == "noncanonical":
        body += b"\n"
    elif kind == "malicious":
        body = signatures.Malicious()
    elif kind == "missing":
        body = None
    with monkeypatch.context() as patch:
        all_io_forbidden(patch)
        for module, name in (
            (runtime, "_prepare_and_operate"),
            (runtime, "_read_environment"),
            (operator, "_publish"),
            (auth.forecast, "load_forecasts"),
            (auth.minute, "load_minute_execution_data"),
        ):
            patch.setattr(module, name, fixtures.forbidden)
        for gate in (
            signed.preflight_owner_approval,
            runtime.run_genuine_minute_verification,
        ):
            with pytest.raises(ValueError, match="^Invalid offline approval.$"):
                gate(approval=body)
            for name in ("public_key", "key_id", "trust_store", "trusted_digest"):
                with pytest.raises(TypeError):
                    gate(approval=body, **{name: keys[1]})
        # Prove the interceptors raise before the real operation, including stat,
        # listing, reservation and dispatch, without probing any original path.
        for operation in (
            lambda: builtins.open("/fabricated-guard-probe"),
            lambda: io.open("/fabricated-guard-probe"),  # noqa: UP020 - test io guard
            lambda: os.open("/fabricated-guard-probe", os.O_RDONLY),
            lambda: os.stat("/fabricated-guard-probe"),
            lambda: os.lstat("/fabricated-guard-probe"),
            lambda: os.listdir("/fabricated-guard-probe"),
            lambda: os.scandir("/fabricated-guard-probe"),
            lambda: os.mkdir("/fabricated-guard-probe"),
            lambda: runtime._prepare_and_operate(None),
            lambda: operator._publish(None),
            lambda: auth.forecast.load_forecasts(None),
            lambda: auth.minute.load_minute_execution_data(None),
        ):
            with pytest.raises(AssertionError, match="Offline boundary"):
                operation()


def test_enrolled_module_body_has_no_io_or_implicit_invocation(monkeypatch):
    import types

    # Ordinary imports necessarily load Python files. Execute the unchanged module
    # body with dependencies already imported to isolate any enrolment side effect;
    # the separate cold-process tests cover normal import under the path guard.
    code = compile(Path(signed.__file__).read_bytes(), signed.__file__, "exec")
    module = types.ModuleType("enrolment_import_test")
    with monkeypatch.context() as patch:
        all_io_forbidden(patch)
        patch.setattr(runtime, "run_genuine_minute_verification", fixtures.forbidden)
        patch.setattr(runtime, "_prepare_and_operate", fixtures.forbidden)
        exec(code, module.__dict__)
    assert module.TRUSTED_OWNER_PUBLIC_KEY == signed.TRUSTED_OWNER_PUBLIC_KEY
    assert module.TRUSTED_OWNER_KEY_ID == signed.TRUSTED_OWNER_KEY_ID

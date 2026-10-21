"""Ephemeral in-memory Ed25519 keys and invented identities; no real approval."""

import ast
import builtins
import copy
import dataclasses
import io
import json
import os
import socket
import subprocess
import sys
import tomllib
from hashlib import sha256
from pathlib import Path

import psycopg
import pytest
import test_genuine_minute_inputs as fixtures
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backtest_badger import genuine_minute_signed_approval as signed

offline = fixtures.offline
operator = signed.fixture_contract
auth = operator.auth
wiring = signed.wiring
COMMIT = "a" * 40
RUN = "123456"
GATES = (
    signed.preflight_owner_approval,
    operator.run_genuine_minute_verification,
    auth.authenticate_minute_inputs,
)


def wire(value):
    # Independent test serializer; the known-answer test below fixes exact bytes.
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def invented(label):
    return sha256(("fabricated-signature-test:" + label).encode()).hexdigest()


def complete_payload():
    pins = {name: invented(name) for name, _ in wiring.DECLARATIONS}
    inventory = {
        group: {name: {"sha256": invented(name), "bytes": 123} for name in names}
        for group, names in (
            ("forecast", ("manifest.json", "validation_predictions.csv")),
            ("minute", auth._release_names("1m")),
            ("parity", auth.PARITY_FILES),
        )
    }
    for group, mapping in (
        (
            "forecast",
            {
                "manifest.json": "forecast_manifest",
                "validation_predictions.csv": "forecast_csv",
            },
        ),
        (
            "minute",
            {"manifest.json": "minute_manifest", "minute_opens.csv": "minute_csv"},
        ),
        (
            "parity",
            dict(
                zip(
                    auth.PARITY_FILES,
                    (
                        "parity_manifest",
                        "parity_report",
                        "parity_provenance",
                        "parity_integrity",
                        "parity_discrepancies",
                    ),
                    strict=True,
                )
            ),
        ),
    ):
        for name, key in mapping.items():
            inventory[group][name]["sha256"] = pins[key]
    implementation = {
        name: {"sha256": invented(name), "bytes": 456}
        for name in signed.IMPLEMENTATION_FILES
    }
    for path, key in (
        (auth.parity.HOURLY_PROTOCOL, "hourly_protocol"),
        (auth.parity.MINUTE_PROTOCOL, "minute_protocol"),
        (wiring.PIN_DOCUMENT, "minute_pin_document"),
    ):
        implementation[path]["sha256"] = pins[key]
    monthly = []
    for symbol in ("BTCUSDT", "ETHUSDT"):
        for month in range(1, 13):
            label = f"2024-{month:02d}"
            stem = f"{symbol}-1m-{label}.zip"
            url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/1m/{stem}"
            monthly.append(
                [
                    symbol,
                    label,
                    {
                        "sha256": inventory["minute"][f"raw/{stem}"]["sha256"],
                        "checksum_sha256": inventory["minute"][f"raw/{stem}.CHECKSUM"][
                            "sha256"
                        ],
                        "zip_bytes": 123,
                        "checksum_bytes": 123,
                        "csv_bytes": 789,
                        "row_count": signed.calendar.monthrange(2024, month)[1] * 1440,
                        "url": url,
                        "checksum_url": url + ".CHECKSUM",
                        "observed_at": "2025-01-02T00:00:00+00:00",
                    },
                ]
            )
    return {
        "schema": signed.PAYLOAD_SCHEMA,
        "source_kind": wiring.verification_plan().future_source_kind,
        "commit": COMMIT,
        "ci": {
            "commit": COMMIT,
            "run_id": RUN,
            "status": "completed",
            "conclusion": "success",
        },
        "runtime": {
            "python": "3.12.1",
            "implementation": "CPython",
            "platform": "linux",
            "dependencies": {name: "1.2.3" for name in signed.DEPENDENCIES},
        },
        "implementation": implementation,
        "roots": {name: "/fabricated-review/" + path for name, path in wiring.ROOTS},
        "destination": "/fabricated-review/" + wiring.DESTINATION,
        "input_inventory": inventory,
        "pins": pins,
        "monthly_sources": monthly,
        "hourly_monthly": [[s, m, invented(s + m)] for s, m, _ in monthly],
        "audit_code": {
            name: invented("historical:" + name)
            for name in auth.parity.IMPLEMENTATION_FILES
        },
        **dict(wiring.verification_plan().required_flags),
    }


@pytest.fixture
def keys():
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return private, public, "sha256:" + sha256(public).hexdigest()


def envelope(keys, payload=None, *, domain=signed.DOMAIN):
    private, _, key_id = keys
    result = {
        "schema": signed.SCHEMA,
        "key_id": key_id,
        "payload": complete_payload() if payload is None else payload,
    }
    result["signature"] = private.sign(domain + wire(result)).hex()
    return result


def verify(keys, document, **overrides):
    options = dict(
        document=document,
        public_key=keys[1],
        key_id=keys[2],
        reviewed_commit=COMMIT,
        ci_run_id=RUN,
    )
    return signed._verify_envelope(**(options | overrides))


def test_canonical_known_answer_and_real_repeatable_signatures(keys):
    assert (
        signed.canonical_approval_bytes({"é": "badger", "z": [True, 1, -1], "a": '"\\'})
        == b'{"a":"\\"\\\\","z":[true,1,-1],"\xc3\xa9":"badger"}'
    )
    candidate = envelope(keys)
    assert len(candidate["signature"]) == 128
    assert envelope(keys) == candidate  # Ed25519 deterministic for the same key.
    reordered = dict(reversed(list(candidate.items())))
    reordered["payload"] = dict(reversed(list(candidate["payload"].items())))
    assert signed.canonical_approval_bytes(reordered) == wire(candidate)
    for _ in range(2):
        assert verify(keys, wire(reordered)) == wire(candidate["payload"])
    assert sum(map(len, candidate["payload"]["input_inventory"].values())) == 57
    assert not set(candidate["payload"]["pins"].values()) & set(
        dict(wiring.DECLARATIONS).values()
    )


MUTATIONS = [
    (("schema",), "unknown-v2"),
    (("key_id",), "sha256:" + "0" * 64),
    (("payload", "schema"), operator.SCHEMA),
    (("payload", "commit"), "b" * 40),
    (("payload", "ci", "commit"), "b" * 40),
    (("payload", "ci", "run_id"), "123457"),
    (("payload", "runtime", "python"), "3.12.2"),
    (("payload", "runtime", "dependencies", "cryptography"), "1.2.4"),
    (("payload", "implementation", "uv.lock", "bytes"), 457),
    (("payload", "input_inventory", "forecast", "manifest.json", "sha256"), "0" * 64),
    (
        (
            "payload",
            "input_inventory",
            "forecast",
            "validation_predictions.csv",
            "bytes",
        ),
        122,
    ),
    (("payload", "destination"), "/another/" + wiring.DESTINATION),
    (("payload", "roots", "minute"), "/another/minute"),
    (("payload", "verification_only"), False),
    (("payload", "single_attempt"), False),
    (("payload", "resume"), True),
    (("payload", "strategy_authorised"), True),
    (("payload", "economic_publication_authorised"), True),
    (("payload", "source_kind"), operator.SOURCE_KIND),
    (("payload", "pins", "minute_protocol"), "1" * 64),
    (("payload", "monthly_sources", 0, 2, "csv_bytes"), 788),
    (("payload", "monthly_sources", 0, 2, "observed_at"), "2025-01-03T00:00:00+00:00"),
    (("payload", "hourly_monthly", 0, 2), "2" * 64),
    (("payload", "audit_code", "uv.lock"), "3" * 64),
]


@pytest.mark.parametrize("path,value", MUTATIONS)
def test_authenticated_field_mutations_fail(keys, path, value):
    candidate = envelope(keys)
    target = candidate
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ValueError, match="^Invalid offline approval.$"):
        verify(keys, wire(candidate))


def test_each_signature_byte_bit_flip_and_domain_separation(keys):
    candidate = envelope(keys)
    signature = bytes.fromhex(candidate["signature"])
    for i in range(64):
        changed = bytearray(signature)
        changed[i] ^= 1
        candidate["signature"] = changed.hex()
        with pytest.raises(ValueError):
            verify(keys, wire(candidate))
    for domain in (b"", signed.DOMAIN[:-1], signed.DOMAIN.replace(b"V1", b"V2")):
        with pytest.raises(ValueError):
            verify(keys, wire(envelope(keys, domain=domain)))


def test_microsecond_receipts_preserved_and_unicode_paths_bound(keys):
    payload = complete_payload()
    payload["monthly_sources"][0][2]["observed_at"] = "2025-01-02T00:00:00.123456+00:00"
    payload["destination"] = "/fabricatéd-review/" + wiring.DESTINATION
    payload["roots"] = {
        name: "/fabricatéd-review/" + path for name, path in wiring.ROOTS
    }
    candidate = envelope(keys, payload)
    assert verify(keys, wire(candidate)) == wire(payload)
    for replacement in (b"fabricat\\u00e9d", "fabricate\u0301d".encode()):
        with pytest.raises(ValueError):
            verify(keys, wire(candidate).replace("fabricatéd".encode(), replacement))


def test_one_bit_changes_to_each_selected_payload_field(keys):
    candidate = envelope(keys)
    for path, _ in MUTATIONS:
        modified = copy.deepcopy(candidate)
        target = modified
        for part in path[:-1]:
            target = target[part]
        value = target[path[-1]]
        if type(value) is bool:
            target[path[-1]] = not value
        elif type(value) is int:
            target[path[-1]] = value ^ 1
        else:
            target[path[-1]] = chr(ord(value[0]) ^ 1) + value[1:]
        with pytest.raises(ValueError):
            verify(keys, wire(modified))


@pytest.mark.parametrize(
    "signature",
    [
        "",
        "00" * 63,
        "00" * 65,
        "AB" * 64,
        "gg" * 64,
        "0x" + "00" * 64,
        "00 " * 64,
        "A" * 88,
        0,
        None,
    ],
)
def test_invalid_signature_encoding(keys, signature):
    candidate = envelope(keys)
    candidate["signature"] = signature
    with pytest.raises(ValueError):
        verify(keys, wire(candidate))


@pytest.mark.parametrize(
    "public", [b"", b"x" * 31, b"x" * 33, "x" * 32, bytearray(32), None]
)
def test_invalid_key_bytes(keys, public):
    with pytest.raises(ValueError):
        verify(keys, wire(envelope(keys)), public_key=public)


def test_wrong_key_self_anchor_and_stale_independent_review(keys):
    candidate = envelope(keys)
    public = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    other_id = "sha256:" + sha256(public).hexdigest()
    candidate["key_id"] = other_id
    with pytest.raises(ValueError):
        verify(keys, wire(candidate), public_key=public, key_id=other_id)
    for overrides in (
        {"key_id": "sha256:" + "0" * 64},
        {"reviewed_commit": "b" * 40},
        {"ci_run_id": "999999"},
    ):
        with pytest.raises(ValueError):
            verify(keys, wire(envelope(keys)), **overrides)
    for field in (
        "public_key",
        "key_fingerprint",
        "trusted_digest",
        "anchor",
        "trust_store",
    ):
        candidate = envelope(keys)
        candidate[field] = sha256(wire(candidate)).hexdigest()
        with pytest.raises(ValueError):
            verify(keys, wire(candidate))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b + b"\n",
        lambda b: b + b"{}",
        lambda b: b"\xef\xbb\xbf" + b,
        lambda b: b.decode().encode("utf-16"),
        lambda b: b.replace(b":", b": ", 1),
        lambda b: b.replace(b'"schema":', b'"schema":"duplicate","schema":', 1),
        lambda b: b.replace(b'"bytes":123', b'"bytes":123,"bytes":123', 1),
        lambda b: b.replace(b'"bytes":123', b'"bytes":123.0', 1),
        lambda b: b.replace(b'"bytes":123', b'"bytes":1e2', 1),
        lambda b: b.replace(b'"bytes":123', b'"bytes":NaN', 1),
        lambda b: b.replace(b'"bytes":123', b'"bytes":Infinity', 1),
        lambda b: b.replace(b'"bytes":123', b'"bytes":-Infinity', 1),
        lambda b: b.replace(b'"bytes":123', b'"bytes":-0', 1),
        lambda b: b.replace(b"fabricated-review", b"fabricat\\u0065d-review", 1),
        lambda b: b.replace(b"fabricated-review", "fabricatéd-review".encode(), 1),
        lambda b: b.replace(b"fabricated-review", b"fabricat\xffd-review", 1),
        lambda b: json.dumps(json.loads(b), sort_keys=False, indent=2).encode(),
    ],
)
def test_noncanonical_or_invalid_wire_refused(keys, mutate):
    with pytest.raises(ValueError, match="^Invalid offline approval.$"):
        verify(keys, mutate(wire(envelope(keys))))


@pytest.mark.parametrize(
    "path,value",
    [
        (("verification_only",), 1),
        (("resume",), 0),
        (("input_inventory", "forecast", "manifest.json", "bytes"), True),
        (("input_inventory", "forecast", "manifest.json", "bytes"), None),
        (("input_inventory", "forecast", "manifest.json", "bytes"), 0),
        (("input_inventory", "forecast", "manifest.json", "bytes"), 2**63),
        (("input_inventory", "forecast"), {}),
        (("input_inventory", "minute"), {}),
        (("input_inventory", "parity"), {}),
        (("audit_code",), {}),
        (("implementation",), {}),
        (("pins",), {}),
        (("monthly_sources",), []),
        (("hourly_monthly",), []),
        (("ci", "run_id"), 123456),
        (("ci", "conclusion"), "failure"),
        (("schema",), operator.SCHEMA),
        (("source_kind",), operator.SOURCE_KIND),
        (("destination",), "/wrong"),
        (("runtime", "dependencies"), {}),
        (("runtime", "python"), "any"),
        (("monthly_sources", 1, 2, "row_count"), 40320),
        (("monthly_sources", 0, 2, "observed_at"), "2024-01-01T00:00:00+00:00"),
        (("monthly_sources", 0, 2, "url"), "https://example.invalid/archive.zip"),
        (("monthly_sources", 0, 2, "checksum_bytes"), 124),
        (("pins", "minute_protocol"), "0" * 64),
    ],
)
def test_valid_signature_cannot_make_incomplete_payload_valid(keys, path, value):
    payload = complete_payload()
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ValueError):
        verify(keys, wire(envelope(keys, payload)))


def test_signed_missing_extra_fields_and_month_order(keys):
    original = complete_payload()
    for field in original:
        payload = copy.deepcopy(original)
        del payload[field]
        with pytest.raises(ValueError):
            verify(keys, wire(envelope(keys, payload)))
    for path in (
        (),
        ("ci",),
        ("runtime",),
        ("input_inventory",),
        ("input_inventory", "forecast"),
        ("input_inventory", "forecast", "manifest.json"),
        ("monthly_sources", 0, 2),
    ):
        payload = copy.deepcopy(original)
        target = payload
        for part in path:
            target = target[part]
        target["unexpected"] = "injected"
        with pytest.raises(ValueError):
            verify(keys, wire(envelope(keys, payload)))
    for name in ("monthly_sources", "hourly_monthly"):
        payload = copy.deepcopy(original)
        payload[name].reverse()
        with pytest.raises(ValueError):
            verify(keys, wire(envelope(keys, payload)))


class Malicious:
    def __getattribute__(self, name):
        raise AssertionError("Argument inspected")

    __bool__ = __str__ = __repr__ = __iter__ = __fspath__ = __getattribute__


def test_no_object_adaptation_or_non_json_types(keys):
    for value in (
        Malicious(),
        {"nested": Malicious()},
        dataclasses.asdict(wiring.approval_readiness()),
        wiring.verification_plan(),
        (1,),
        {1: "bad"},
        float("nan"),
        float("inf"),
        1.5,
        None,
        "e\u0301",
        "\ud800",
        "\x00",
    ):
        with pytest.raises(ValueError):
            signed.canonical_approval_bytes(value)
    for value in (
        Malicious(),
        {},
        bytearray(wire(envelope(keys))),
        wiring.approval_readiness(),
        dataclasses.asdict(wiring.verification_plan()),
    ):
        with pytest.raises(ValueError):
            verify(keys, value)
    cycle = []
    cycle.append(cycle)
    with pytest.raises(ValueError):
        signed.canonical_approval_bytes(cycle)
    with pytest.raises(ValueError):
        verify(keys, b" " * (signed.MAX_DOCUMENT_BYTES + 1))


@pytest.mark.parametrize("gate", GATES)
def test_gates_reject_fabricated_claims_before_all_io(
    keys, gate, monkeypatch, tmp_path
):
    good = wire(envelope(keys))
    verified = verify(keys, good)
    assert signed.TRUSTED_OWNER_PUBLIC_KEY != keys[1]
    assert signed.TRUSTED_OWNER_KEY_ID != keys[2]
    attempts = []

    def unexpected(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("Closed gate attempted work")

    candidates = (
        Malicious(),
        good,
        verified,
        {"public_key": keys[1], "approved_digest": sha256(good).hexdigest()},
        dataclasses.asdict(wiring.approval_readiness()),
    )
    with monkeypatch.context() as patch:
        for module, names in (
            (builtins, ("open",)),
            (io, ("open",)),
            (os, ("open", "stat", "lstat", "listdir", "scandir", "mkdir")),
            (subprocess, ("Popen",)),
            (socket, ("getaddrinfo", "create_connection")),
            (psycopg, ("connect",)),
            (operator, ("_run_fixture_verification", "_publish", "_source_snapshot")),
            (auth.forecast, ("load_forecasts",)),
            (auth.minute, ("load_minute_execution_data",)),
        ):
            for name in names:
                patch.setattr(module, name, unexpected)
        if gate is not signed.preflight_owner_approval:
            patch.setattr(signed, "_verify_envelope", unexpected)
        for value in candidates:
            with pytest.raises(
                ValueError
                if gate is signed.preflight_owner_approval
                else PermissionError
            ):
                gate(approval=value)
    assert attempts == []
    assert list(tmp_path.iterdir()) == []
    for field in (
        "public_key",
        "key_id",
        "trusted_digest",
        "environment_reader",
        "allow_genuine",
    ):
        with pytest.raises(TypeError):
            gate(approval=good, **{field: keys[1]})
    # Even test trust cannot authorise invented pins or open the legacy gates.
    monkeypatch.setattr(signed, "TRUSTED_OWNER_PUBLIC_KEY", keys[1])
    monkeypatch.setattr(signed, "TRUSTED_OWNER_KEY_ID", keys[2])
    with pytest.raises(PermissionError):
        gate(approval=good)


def test_signed_intent_is_not_fixture_authority(keys, tmp_path):
    payload = json.loads(verify(keys, wire(envelope(keys))))
    with pytest.raises(ValueError):
        operator._validate_approval(payload, tmp_path)
    readiness = wiring.approval_readiness()
    assert (readiness.status, readiness.readiness, readiness.access) == (
        "NOT_APPROVED",
        "NOT_READY",
        "NO_SOURCE_ACCESS",
    )


def test_invalid_signature_has_no_filesystem_effect(keys, tmp_path, monkeypatch):
    candidate = envelope(keys)
    candidate["signature"] = "00" * 64
    with monkeypatch.context() as patch:
        for module, names in (
            (builtins, ("open",)),
            (io, ("open",)),
            (os, ("stat", "lstat", "open", "mkdir", "listdir", "scandir")),
            (subprocess, ("Popen",)),
        ):
            for name in names:
                patch.setattr(module, name, fixtures.forbidden)
        with pytest.raises(ValueError):
            verify(keys, wire(candidate))
    assert list(tmp_path.iterdir()) == []


def test_import_and_runtime_closure_is_explicit():
    root = Path(__file__).absolute().parents[1]
    covered = set(signed.IMPLEMENTATION_FILES)
    for name in covered:
        if name.endswith(".py"):
            tree = ast.parse((root / name).read_text())
            for node in ast.walk(tree):
                imports = []
                if isinstance(node, ast.Import):
                    imports = [
                        a.name
                        for a in node.names
                        if a.name.startswith("backtest_badger.")
                    ]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module == "backtest_badger":
                        imports = ["backtest_badger." + a.name for a in node.names]
                    elif node.module.startswith("backtest_badger."):
                        imports = [node.module]
                for module in imports:
                    assert "src/" + module.replace(".", "/") + ".py" in covered
    lock = tomllib.loads((root / "uv.lock").read_text())
    packages = {p["name"]: p for p in lock["package"]}
    pending = [d["name"] for d in packages["backtest-badger"]["dependencies"]]
    found = set()
    while pending:
        name = pending.pop()
        if name in found:
            continue
        found.add(name)
        package = packages[name]
        pending.extend(d["name"] for d in package.get("dependencies", ()))
        if name == "psycopg":
            pending.extend(
                d["name"] for d in package["optional-dependencies"]["binary"]
            )
    assert found == signed.DEPENDENCIES | {"tzdata"}


def test_cold_import_with_independent_precollection_guard(tmp_path):
    script = r"""
import ast, os, socket, sys
from pathlib import Path
import psycopg
root = Path.cwd()
assert not any(n.startswith('backtest_badger') for n in sys.modules)
tree = ast.parse((root / 'tests/test_genuine_minute_inputs.py').read_text())
names = {'forbidden', 'check_path', 'install_offline_audit'}
guard = ast.Module(body=[n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
namespace = dict(os=os, sys=sys, Path=Path, psycopg=psycopg, ROOT=root)
exec(compile(guard, '<unchanged process guard>', 'exec'), namespace)
namespace['install_offline_audit']()
blocked = 0
paths = [root / 'artifacts' / s for s in (
    'experiments/stage-2b-v1', 'execution/binance-1m-2024-v1',
    'audits/stage-04b2d1-native-parity-v1', 'audits/stage-04b2d3-minute-inputs-v1'
)] + [root.parent / 'crypto-trading-platform']
for path in paths:
    for op in (lambda: path.stat(), lambda: path.lstat(),
               lambda: os.open(path, os.O_RDONLY), lambda: os.listdir(path)):
        try: op()
        except AssertionError: blocked += 1
        else: raise AssertionError('Forbidden path access')
for op in (lambda: socket.getaddrinfo('example.invalid', 443),
           lambda: socket.create_connection(('127.0.0.1', 1)),
           lambda: psycopg.connect('')):
    try: op()
    except AssertionError: blocked += 1
    else: raise AssertionError('Forbidden network/database')
assert blocked == 23
from backtest_badger import genuine_minute_signed_approval as signed
class Untrusted:
    def __getattribute__(self, name): raise AssertionError('Argument inspected')
for gate, error in ((signed.preflight_owner_approval, ValueError),
             (signed.fixture_contract.run_genuine_minute_verification, PermissionError),
             (signed.fixture_contract.auth.authenticate_minute_inputs,
              PermissionError)):
    try: gate(approval=Untrusted())
    except error: pass
    else: raise AssertionError('Gate opened')
assert list(Path(sys.argv[1]).iterdir()) == []
print('23 guarded operations; cold imports and three refusing gates passed')
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=Path(__file__).absolute().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        result.stdout.strip()
        == "23 guarded operations; cold imports and three refusing gates passed"
    )

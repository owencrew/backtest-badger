"""Activation is blocked on an owner-selected independent approval mechanism.

These are refusal regressions, not tests of an implemented genuine validator.
Full native fabricated success/fault tests remain in the unchanged operator suite.
"""

import builtins
import dataclasses
import io
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest
import test_genuine_minute_inputs as fixtures

from backtest_badger import genuine_minute_inputs as auth
from backtest_badger import genuine_minute_verification_operator as operator
from backtest_badger import genuine_minute_verification_wiring as wiring

offline = fixtures.offline
GATES = (operator.run_genuine_minute_verification, auth.authenticate_minute_inputs)


class Untrusted:
    def __getattribute__(self, name):
        raise AssertionError("Approval object inspected before independent authority")

    __bool__ = __str__ = __repr__ = __iter__ = __fspath__ = __getattribute__


def candidates():
    """Incomplete invented claims; never a genuine approval constructor."""
    plan, readiness = wiring.verification_plan(), wiring.approval_readiness()
    candidate = {"owner_authorised": True, "commit": "a" * 40}
    self_digest = sha256(operator._json(candidate)).hexdigest()
    return [
        pytest.param(None, id="absent"),
        pytest.param(Untrusted(), id="malicious-object"),
        pytest.param({"nested": Untrusted()}, id="nested-malicious-object"),
        pytest.param(plan, id="plan"),
        pytest.param(dataclasses.asdict(plan), id="plan-dict"),
        pytest.param(readiness, id="readiness"),
        pytest.param(dataclasses.asdict(readiness), id="readiness-dict"),
        pytest.param(candidate, id="owner-boolean-without-anchor"),
        pytest.param({**candidate, "approved_digest": self_digest}, id="self-anchor"),
        pytest.param({"anchor": "caller-selected"}, id="unreviewed-anchor"),
        pytest.param({"source_kind": operator.SOURCE_KIND}, id="fixture-kind"),
        pytest.param({"source_kind": plan.future_source_kind}, id="genuine-kind-claim"),
        pytest.param({"forecast_bytes": None}, id="unknown-lengths"),
        pytest.param({"input_inventory": {}}, id="missing-files"),
        pytest.param({"input_inventory": {"labels.csv": {}}}, id="extra-files"),
        pytest.param({"commit": "short"}, id="wrong-commit"),
        pytest.param({"ci": {"conclusion": "success"}}, id="unverified-ci"),
        pytest.param({"runtime": {"python": "TEST"}}, id="wrong-runtime"),
        pytest.param({"implementation": {"unknown.py": "0" * 64}}, id="wrong-code"),
        pytest.param({"pins": {"minute_pin_document": "0" * 64}}, id="wrong-doc"),
        pytest.param({"pins": {"forecast_csv": "0" * 64}}, id="wrong-source"),
        pytest.param({"verification_only": 1}, id="nonboolean-flag"),
    ]


@pytest.mark.parametrize("function", GATES)
@pytest.mark.parametrize("approval", candidates())
def test_no_unanchored_claim_can_reach_any_io(function, approval, monkeypatch):
    attempts = []

    def unexpected(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("Unanchored public call attempted I/O or fixture dispatch")

    # Block ALL path probes, including the destination, without probing one first.
    # Restore before pytest can do its own result reporting/temporary cleanup.
    with monkeypatch.context() as patch:
        for module, names in (
            (builtins, ("open",)),
            (io, ("open",)),
            (os, ("open", "stat", "lstat", "listdir", "scandir", "mkdir")),
            (subprocess, ("Popen",)),
            (operator, ("_validate_approval", "_run_fixture_verification")),
            (auth, ("_safe",)),
        ):
            for name in names:
                patch.setattr(module, name, unexpected)
        with pytest.raises(PermissionError):
            function(approval=approval)
    assert attempts == []


@pytest.mark.parametrize("function", GATES)
def test_omitted_approval_and_runtime_overrides_are_not_interfaces(function):
    with pytest.raises(TypeError):
        function()
    for keyword in (
        "allow_genuine",
        "force",
        "unsafe",
        "test_mode",
        "dry_run_override",
        "fixture_root",
        "environment_reader",
        "approved_digest",
    ):
        with pytest.raises(TypeError):
            function(approval=None, **{keyword: True})


def test_cold_import_and_process_guards_before_project_imports(tmp_path):
    # Independent child: install the existing process guard before any project
    # import by extracting only its stdlib/psycopg guard definitions with AST.
    # This avoids run_path importing the authentication module before the guard.
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
exec(compile(guard, '<existing offline guard>', 'exec'), namespace)
namespace['install_offline_audit']()
paths = [root / 'artifacts' / p for p in (
    'experiments/stage-2b-v1', 'execution/binance-1m-2024-v1',
    'audits/stage-04b2d1-native-parity-v1',
    'audits/stage-04b2d3-minute-inputs-v1',
)] + [root.parent / 'crypto-trading-platform']
blocked = 0
for path in paths:
    for operation in (
        lambda: path.stat(), lambda: path.lstat(),
        lambda: os.open(path, os.O_RDONLY), lambda: os.listdir(path),
    ):
        try:
            operation()
        except AssertionError:
            blocked += 1
        else:
            raise AssertionError('Forbidden path reached filesystem')
for operation in (
    lambda: socket.getaddrinfo('example.invalid', 443),
    lambda: socket.create_connection(('127.0.0.1', 1)),
    lambda: psycopg.connect(''),
):
    try:
        operation()
    except AssertionError:
        blocked += 1
    else:
        raise AssertionError('Network or database guard failed')
assert blocked == 23
from backtest_badger import genuine_minute_verification_operator as operator
from backtest_badger import genuine_minute_inputs as auth
for gate in (operator.run_genuine_minute_verification, auth.authenticate_minute_inputs):
    try:
        gate(approval=None)
    except PermissionError:
        pass
    else:
        raise AssertionError('Cold gate opened')
safe = Path(sys.argv[1]) / 'fabricated.txt'
safe.write_bytes(b'fabricated temporary bytes')
assert safe.read_bytes() == b'fabricated temporary bytes'
assert safe.stat().st_size == 26
print('cold imports guarded; 23 forbidden operations blocked; temporary I/O allowed')
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=Path(__file__).absolute().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == (
        "cold imports guarded; 23 forbidden operations blocked; temporary I/O allowed"
    )

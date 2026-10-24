"""Disposable models only; no installed runtime, account or privileged probes."""

import importlib.util
import json
import os
import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from backtest_badger import genuine_backtest_custody as custody
from backtest_badger import genuine_backtest_operator as operator

spec = importlib.util.spec_from_file_location(
    "rehearsal",
    str(Path(__file__).absolute().parents[1] / "ops/e5d_rehearsal_preflight.py"),
)
rehearsal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rehearsal)


@pytest.fixture
def scratch():
    import __main__

    return Path(
        tempfile.mkdtemp(prefix="preparation-", dir=getattr(__main__, "E5D_TEMP", None))
    ).resolve()


@pytest.fixture
def model_tree(scratch, monkeypatch):
    # POSIX tree algorithm under disposable same-UID scratch. Deliberately replace
    # ancestor policy here; separate tests verify that real /tmp is rejected.
    @contextmanager
    def model_directory(path, owner_uid):
        with custody.directory(path) as fd:
            yield fd

    monkeypatch.setattr(rehearsal, "protected_directory", model_directory)
    (scratch / "empty-package.py").write_bytes(b"")
    (scratch / "code.py").write_bytes(b"fabricated code")
    (scratch / "empty-directory").mkdir()
    return scratch


def snapshot(root):
    return rehearsal.snapshot_tree(root, owner_uid=os.getuid())


def test_snapshot_is_deterministic_and_supports_empty_entries(model_tree):
    first = snapshot(model_tree)
    assert first == snapshot(model_tree)
    assert first["files"]["empty-package.py"]["bytes"] == 0
    assert "empty-directory/" in first["directories"]
    assert rehearsal.canonical(first) == rehearsal.canonical(
        json.loads(rehearsal.canonical(first))
    )


@pytest.mark.parametrize(
    "change", ["missing", "extra", "empty_directory", "bytes", "mode"]
)
def test_snapshot_exact_sets_and_bytes(model_tree, change):
    before = snapshot(model_tree)
    if change == "missing":
        (model_tree / "code.py").unlink()
    if change == "extra":
        (model_tree / "extra.py").write_bytes(b"invented")
    if change == "empty_directory":
        (model_tree / "extra").mkdir()
    if change == "bytes":
        (model_tree / "code.py").write_bytes(b"changed")
    if change == "mode":
        (model_tree / "code.py").chmod(0o400)
    assert snapshot(model_tree) != before


@pytest.mark.parametrize(
    "change", ["symlink", "hardlink", "fifo", "writable", "private"]
)
def test_snapshot_refuses_unsafe_entries(model_tree, change):
    target = model_tree / "unsafe"
    if change == "symlink":
        target.symlink_to(model_tree / "code.py")
    if change == "hardlink":
        os.link(model_tree / "code.py", target)
    if change == "fifo":
        os.mkfifo(target)
    if change == "writable":
        (model_tree / "code.py").chmod(0o666)
    if change == "private":
        (model_tree / ".env").write_bytes(b"fabricated forbidden fixture")
    with pytest.raises((ValueError, OSError)):
        snapshot(model_tree)


def test_snapshot_detects_change_during_read(model_tree, monkeypatch):
    original = os.read
    changed = False

    def read(fd, size):
        nonlocal changed
        body = original(fd, size)
        if body and not changed:
            changed = True
            (model_tree / "code.py").write_bytes(b"changed during read")
        return body

    monkeypatch.setattr(os, "read", read)
    with pytest.raises(ValueError, match="changed"):
        snapshot(model_tree)


def test_real_writable_ancestor_is_rejected(scratch):
    with pytest.raises(ValueError, match="writable"):
        snapshot(scratch)
    with pytest.raises(ValueError, match="ancestor"):
        with custody.directory(scratch, trusted_uid=os.getuid()):
            pytest.fail("Writable /tmp ancestor accepted")


@pytest.mark.parametrize(
    "uid,mode", [(999999, 0o755), (0, 0o777), (123, 0o775), (123, 0o757)]
)
def test_untrusted_ancestor_metadata(uid, mode):
    with pytest.raises(ValueError):
        custody.check_ancestor(
            SimpleNamespace(st_uid=uid, st_mode=stat.S_IFDIR | mode), 123
        )


def test_unlisted_empty_runtime_directory_is_rejected(scratch):
    (scratch / "code.py").write_bytes(b"invented")
    inventory = {
        "roles": {r: str(scratch) for r in custody.CLOSURE_ROLES},
        "roots": {str(scratch): {"code.py": custody.identity(b"invented")}},
    }
    custody.verify_closure(inventory, supervisor_uid=os.getuid(), mocked=True)
    (scratch / "unknown").mkdir()
    with pytest.raises(ValueError, match="Unreviewed runtime directory"):
        custody.verify_closure(inventory, supervisor_uid=os.getuid(), mocked=True)


def test_worker_has_no_inherited_stderr_or_supplementary_groups(monkeypatch):
    captured = {}

    class Stream:
        def fileno(self):
            return 123

    def popen(command, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(stdin=Stream(), stdout=Stream())

    monkeypatch.setattr(operator.subprocess, "Popen", popen)
    monkeypatch.setattr(os, "set_blocking", lambda *args: None)
    operator.PipeWorker(
        ["fabricated-never-executed"],
        uid=os.getuid() + 1,
        gid=os.getgid(),
        seconds=1,
        maximum=1024,
    )
    assert captured["stderr"] == operator.subprocess.DEVNULL
    assert captured["close_fds"] is True and captured["extra_groups"] == []
    assert captured["user"] != os.getuid()
    assert "pass_fds" not in captured
    assert set(captured["env"]) == {
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONNOUSERSITE",
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
    }


@pytest.mark.parametrize(
    "argument",
    ["--run", "--install", "--approval=/invented", "--worker=/invented", "--genuine"],
)
def test_no_run_or_authority_override_interface(monkeypatch, argument):
    monkeypatch.setattr(sys, "argv", ["preflight", argument])
    with pytest.raises(SystemExit, match="execution unavailable"):
        rehearsal.main()


def test_default_is_print_only_ignores_environment(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["preflight"])
    monkeypatch.setenv("E5D_RUNTIME", "/invented/untrusted")
    monkeypatch.setattr(rehearsal, "preflight", lambda: pytest.fail("Read attempted"))
    assert rehearsal.main() == 2
    value = json.loads(capsys.readouterr().out)
    assert value["status"] == "BLOCKED"
    assert value["genuine_execution_authorised"] is False
    assert value["fixed_installation"] == str(rehearsal.INSTALL)


def test_successful_snapshot_never_passes_isolation_gate(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["preflight", "--preflight"])
    monkeypatch.setattr(rehearsal, "preflight", lambda: {"invented_snapshot": True})
    assert rehearsal.main() == 2
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"


def test_missing_installation_never_creates_state(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["preflight", "--preflight"])

    def missing():
        raise FileNotFoundError("fabricated missing installation")

    monkeypatch.setattr(rehearsal, "preflight", missing)
    assert rehearsal.main() == 2
    assert (
        json.loads(capsys.readouterr().out)["preflight_refusal"] == "FileNotFoundError"
    )

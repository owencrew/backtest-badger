import json
import signal
from configparser import RawConfigParser
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import uuid4

import pytest

from backtest_badger import paper_production as prod
from backtest_badger.paper_operations import ClockHealth

OPS = Path(__file__).resolve().parents[1] / "ops/paper"
spec = spec_from_file_location("clock_observer", OPS / "clock_observer.py")
observer = module_from_spec(spec)
spec.loader.exec_module(observer)


def approvals(**changes):
    data = dict(
        mode="production-once",
        symbol="BTCUSDT",
        portfolio_id=str(uuid4()),
        config_sha256="a" * 64,
        implementation_sha256="b" * 64,
        release="c" * 40,
        deployment_sha256="f" * 64,
        machine="d" * 32,
        host="127.0.0.1",
        port=5432,
        role="paper_worker",
        database="paper",
        cluster="123",
        database_oid=456,
        security_sha256="e" * 64,
        archive_identity=[1, 29],
        records_identity=[1, 42],
        journals_identity=[1, 86],
    )
    data.update(changes)
    install = json.dumps(data).encode()
    activate = json.dumps(
        dict(
            action="activate-one-portfolio",
            installation_sha256=sha256(install).hexdigest(),
        )
    ).encode()
    return install, activate


def check(pair):
    return prod.approval(*pair, "BTCUSDT", "c" * 40, "d" * 32)


def test_separate_exact_activation():
    pair = approvals()
    assert check(pair)["database"] == "paper"
    with pytest.raises(ValueError):
        check((pair[0], approvals()[1]))
    with pytest.raises(ValueError):
        check((pair[0], b"{}"))


@pytest.mark.parametrize(
    "bad",
    [
        {"symbol": "ETHUSDT"},
        {"release": ""},
        {"release": "a" * 40},
        {"machine": "1" * 32},
        {"portfolio_id": "local"},
        {"config_sha256": "?"},
        {"host": "database.example"},
        {"database": "x user=postgres"},
        {"database": "postgres"},
        {"port": True},
        {"role": "postgres"},
        {"dsn": "host=other"},
        {"records": "/tmp"},
        {"mode": "staging-once"},
        {"password": "fabricated"},
    ],
)
def test_reject_unsafe_approval(bad):
    with pytest.raises(ValueError):
        check(approvals(**bad))


def test_development_cannot_connect(monkeypatch, tmp_path):
    monkeypatch.setattr(prod.psycopg, "connect", lambda **_: pytest.fail("connected"))
    assert (
        prod.main(["production-once", "--market", "BTCUSDT", "--release", "a" * 40])
        == 1
    )
    p = tmp_path / "untrusted"
    p.write_text("{}")
    with pytest.raises(ValueError):
        prod.protected_bytes(p)


def test_shutdown_unwinds_without_connection(monkeypatch):
    def interrupt(*_):
        signal.raise_signal(signal.SIGTERM)

    monkeypatch.setattr(prod, "installed", interrupt)
    assert (
        prod.main(["production-once", "--market", "BTCUSDT", "--release", "a" * 40])
        == 2
    )


def test_unit_contract():
    service = RawConfigParser(interpolation=None, strict=False)
    service.read(OPS / "backtest-badger-paper@.service.in")
    unit = service["Service"]
    assert unit["User"] == unit["Group"] == "badger-paper"
    assert unit["Type"] == "oneshot" and unit["TimeoutStartSec"] == "240"
    assert unit["ProtectSystem"] == "strict" and unit["NoNewPrivileges"] == "true"
    assert unit["CapabilityBoundingSet"] == ""
    assert unit["ExecStart"].startswith("/usr/bin/env -i ")
    assert "production-once --release @RELEASE@ --market %i" in unit["ExecStart"]
    assert "EnvironmentFile" not in unit and "Install" not in service
    assert unit["LoadCredential"].split(":")[0] == "db-password"
    assert unit["ReadWritePaths"] == str(prod.STATE / "runtime")
    assert set(unit["BindReadOnlyPaths"].split()) == {
        str(prod.SOURCES / "records"),
        str(prod.SOURCES / "journals"),
        str(prod.STATE / "archive"),
    }
    timer = RawConfigParser()
    timer.read(OPS / "backtest-badger-paper@.timer")
    assert timer["Timer"]["Persistent"] == "false"
    assert timer["Timer"]["OnCalendar"] == "*-*-* *:00/5:00 UTC"


def test_observer_uses_external_sample_and_bounds():
    line = "C0000201,192.0.2.1,3,1720000000.1,0.001,0,0,0,0,1,0.02,0.003,16,Normal"
    sample = observer.observation(line, "192.0.2.1")
    measured = datetime.fromtimestamp(1720000000.1, UTC)
    assert sample["sampled_at"] == measured.isoformat()
    assert 18 <= sample["uncertainty_ms"] <= 19
    gate = ClockHealth(True, measured, timedelta(milliseconds=sample["uncertainty_ms"]))
    assert gate.trusted(measured) and not gate.trusted(
        measured + timedelta(seconds=301)
    )
    for invalid in (
        line.replace("Normal", "Not synchronised"),
        line.replace("0.003", "nan"),
        line.replace("192.0.2.1", "192.0.2.2"),
        line.replace("0.003", "-1"),
    ):
        with pytest.raises(ValueError):
            observer.observation(invalid, "192.0.2.1")


def test_release_pin_checks_actual_installed_bytes(tmp_path, monkeypatch):
    for name in ("src/backtest_badger", "docs"):
        (tmp_path / name).mkdir(parents=True)
    files = {}
    for name in (
        "src/backtest_badger/paper_production.py",
        "pyproject.toml",
        "uv.lock",
        "docs/stage-04a-prospective-evaluation-protocol.md",
        "docs/stage-04a-paper-trading-spec.md",
    ):
        (tmp_path / name).write_bytes(b"fabricated")
        files[name] = sha256(b"fabricated").hexdigest()
    content = json.dumps(dict(git_commit="a" * 40, files_sha256=files)).encode()
    (tmp_path / "deployment.json").write_bytes(content)
    monkeypatch.setattr(prod, "trusted_clock_path", lambda _: True)
    pin = sha256(content).hexdigest()
    prod.verify_release(tmp_path, "a" * 40, pin)
    for release, wrong in (("a" * 40, "b" * 64), ("b" * 40, pin)):
        with pytest.raises(ValueError):
            prod.verify_release(tmp_path, release, wrong)
    (tmp_path / "uv.lock").write_bytes(b"changed")
    with pytest.raises(ValueError, match="byte mismatch"):
        prod.verify_release(tmp_path, "a" * 40, pin)


def test_credential_requires_readonly_private_regular_file(tmp_path, monkeypatch):
    from types import SimpleNamespace

    root = tmp_path / "credentials"
    root.mkdir()
    secret = root / "db-password"
    secret.write_text("fabricated")
    secret.chmod(0o400)
    with pytest.raises(ValueError):
        prod.service_password(root)
    monkeypatch.setattr(
        prod.os, "fstatvfs", lambda _: SimpleNamespace(f_flag=prod.os.ST_RDONLY)
    )
    assert prod.service_password(root) == "fabricated"
    secret.chmod(0o440)
    with pytest.raises(ValueError):
        prod.service_password(root)
    secret.rename(root / "other")
    secret.symlink_to(root / "other")
    with pytest.raises(ValueError):
        prod.service_password(root)


def test_archive_service_retries_and_rejects_rewrites(tmp_path, monkeypatch):
    import socket
    from concurrent.futures import ThreadPoolExecutor

    from backtest_badger.paper_archive_service import accept_object
    from backtest_badger.paper_artifacts import ArchiveView, publish_once

    monkeypatch.chdir(tmp_path)
    endpoint = "socket"
    name = str(uuid4()) + ".ref"
    body = b"fabricated original"
    pin = sha256(body).hexdigest()
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener,
        ThreadPoolExecutor(1) as pool,
    ):
        listener.bind(endpoint)
        listener.listen()
        view = ArchiveView(tmp_path, endpoint)

        def serve():
            conn, _ = listener.accept()
            with conn:
                accept_object(conn, tmp_path)

        for filename, data, allowed in (
            (pin + ".json", body, True),
            (pin + ".json", body, True),
            (name, pin.encode(), True),
            (pin + ".json", b"changed", False),
            (name, b"f" * 64, False),
            ("../new.json", body, False),
        ):
            job = pool.submit(serve)
            if allowed:
                publish_once(view, filename, data)
                job.result(timeout=5)
            else:
                with pytest.raises(ValueError):
                    publish_once(view, filename, data)
                with pytest.raises((OSError, ValueError)):
                    job.result(timeout=5)
        assert (tmp_path / name).read_bytes() == pin.encode()
        assert (tmp_path / (pin + ".json")).read_bytes() == body


def test_shipped_installation_template_is_inert():
    template = (OPS / "installation.json.in").read_bytes()
    fabricated, _ = approvals()
    assert json.loads(template).keys() == json.loads(fabricated).keys()
    with pytest.raises(ValueError):
        check((template, b"{}"))

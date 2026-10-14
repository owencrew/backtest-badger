"""Deployment contracts only; no server access, live forecasts or real credentials."""

import configparser
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops/lightsail"


def load(name):
    spec = importlib.util.spec_from_file_location(name, OPS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = load("validate")
benchmark = load("benchmark")


def unit(name):
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read(OPS / "systemd" / name)
    return config


@pytest.mark.parametrize("worker", ["collection", "scoring"])
def test_independent_workers_with_bounded_failure_and_restricted_writes(worker):
    name = f"backtest-badger-{worker}"
    service = unit(name + ".service")
    timer = unit(name + ".timer")
    other = "scoring" if worker == "collection" else "collection"
    assert other not in service["Unit"]["After"]
    assert service["Unit"]["Requires"] == "docker.service"
    assert "time-sync.target" in service["Unit"]["After"]
    assert service["Service"]["User"] == "ubuntu"
    assert service["Service"]["Restart"] == "no"
    assert service["Service"]["Type"] == "oneshot"
    assert service["Service"]["KillMode"] == "control-group"
    assert service["Service"]["TimeoutStartSec"] == (
        "900" if worker == "collection" else "270"
    )
    assert service["Service"]["WorkingDirectory"] == "/opt/backtest-badger/current"
    assert service["Service"]["EnvironmentFile"] == "/etc/backtest-badger/worker.env"
    assert service["Service"]["ProtectSystem"] == "strict"
    assert service["Service"]["UMask"] == "0077"
    assert set(service["Service"]["ReadWritePaths"].split()) == {
        str(validate.ARTIFACTS / path) for path in validate.WRITABLE[worker]
    }
    assert "research" not in service["Service"]["ReadWritePaths"]
    assert timer["Timer"]["Unit"] == name + ".service"
    assert timer["Timer"]["Persistent"] == "false"
    assert timer["Timer"]["AccuracySec"] == "1s"
    assert timer["Timer"]["RandomizedDelaySec"] == "0"
    assert timer["Timer"]["OnCalendar"] == (
        "*-*-* *:01/5:00 UTC" if worker == "collection" else "*-*-* *:02/5:00 UTC"
    )
    for config in (timer, service):
        assert (
            config["Unit"]["ConditionPathExists"]
            == "/etc/backtest-badger/workers-approved"
        )
    assert "Install" not in service  # Cannot accidentally enable the worker at boot.


def test_template_compose_native_validation():
    # Docker Compose config does not need a daemon or initialise any volume.
    validate.templates()


@pytest.fixture
def resolved_compose():
    return {
        "services": {
            "postgres": {
                "ports": [
                    {"host_ip": "127.0.0.1", "published": "5432", "target": 5432}
                ],
                "image": "postgres:17@sha256:" + "0" * 64,
                "restart": "unless-stopped",
                "pull_policy": "never",
                "mem_limit": 1073741824,
                "memswap_limit": 1073741824,
                "cpus": "1.0",
                "healthcheck": {"test": ["CMD-SHELL", "pg_isready"]},
                "volumes": [
                    {"source": "postgres_data", "target": "/var/lib/postgresql/data"}
                ],
            }
        },
        "volumes": {
            "postgres_data": {"name": "backtest-badger-pg17", "external": True}
        },
    }


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "", "192.0.2.1"])
def test_reject_public_database_binding(resolved_compose, host):
    resolved_compose["services"]["postgres"]["ports"][0]["host_ip"] = host
    with pytest.raises(ValueError, match="127.0.0.1"):
        validate.check_compose(resolved_compose)


def test_reject_floating_image_and_implicit_volume(resolved_compose):
    validate.check_compose(resolved_compose)
    resolved_compose["services"]["postgres"]["image"] = "postgres:17"
    with pytest.raises(ValueError, match="digest"):
        validate.check_compose(resolved_compose)
    resolved_compose["services"]["postgres"]["image"] = "postgres:17@sha256:" + "0" * 64
    resolved_compose["volumes"]["postgres_data"]["external"] = False
    with pytest.raises(ValueError, match="volume"):
        validate.check_compose(resolved_compose)


def test_private_file_permissions_ownership_and_no_symlinks(tmp_path):
    path = tmp_path / "private"
    path.write_text("synthetic")
    path.chmod(0o640)
    args = dict(uid=os.getuid(), gid=os.getgid(), mode=0o640)
    validate.private_file(path, **args)
    for mode in (0o644, 0o666, 0o777):
        path.chmod(mode)
        with pytest.raises(ValueError, match="owner/group/mode"):
            validate.private_file(path, **args)
    path.chmod(0o640)
    with pytest.raises(ValueError):
        validate.private_file(path, uid=os.getuid() + 1, gid=os.getgid(), mode=0o640)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="regular"):
        validate.private_file(link, **args)


def test_environment_contract_and_secret_redaction(tmp_path):
    path = tmp_path / "worker.env"
    template = (OPS / "worker.env.example").read_text()
    path.write_text(template.replace("REPLACE_WITH_RANDOM_HEX_SECRET", "a" * 64))
    values = validate.read_environment(path)
    validate.check_worker_environment(values)
    values["POSTGRES_HOST"] = "external.invalid"
    with pytest.raises(ValueError, match="127.0.0.1"):
        validate.check_worker_environment(values)
    path.write_text("POSTGRES_PASSWORD=supersecret$()\n")
    with pytest.raises(ValueError) as error:
        validate.read_environment(path)
    assert "supersecret" not in str(error.value)
    path.write_text(template)
    with pytest.raises(ValueError, match="placeholder"):
        validate.read_environment(path)


def test_missing_dependencies_fail_clearly(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", lambda _: None)
    with pytest.raises(ValueError, match="Missing dependency: docker"):
        validate.templates()
    with pytest.raises(ValueError, match="Missing dependency: systemd-analyze"):
        validate.run(["systemd-analyze", "verify"])


def test_release_preparation_refuses_wrong_directory_and_never_starts_workers(tmp_path):
    result = subprocess.run(
        ["bash", str(OPS / "prepare-release.sh"), "a" * 40],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "matching new release" in result.stderr
    assert not list(tmp_path.iterdir())
    script = (OPS / "prepare-release.sh").read_text()
    assert "--locked --no-dev --no-install-project --no-build" in script
    assert "--no-python-downloads" in script
    assert "systemctl" not in script and "docker compose" not in script


def test_release_symlink_preserves_relative_artifact_paths(tmp_path, monkeypatch):
    from backtest_badger import forward, forward_evaluation, forward_operations
    from backtest_badger import forward_scoring_operations as scoring

    persistent = tmp_path / "persistent"
    persistent.mkdir()
    for revision in ("old", "new"):
        release = tmp_path / revision
        release.mkdir()
        (release / "artifacts").symlink_to(persistent, target_is_directory=True)
        monkeypatch.chdir(release)
        assert forward.TRAINING.resolve() == persistent / "research/stage-2a-v1"
        assert forward.RECORDS.resolve() == persistent / "forward-predictions"
        assert forward_evaluation.OUTCOMES.resolve() == persistent / "forward-outcomes"
        assert (
            forward_operations.OPERATIONS.resolve() == persistent / "forward-operations"
        )
        assert scoring.OPERATIONS.resolve() == persistent / "forward-scoring-operations"


def test_status_commands_are_offline_and_do_not_write(tmp_path, monkeypatch, capsys):
    from backtest_badger import cli, forward_operations, forward_scoring_operations

    protocol = forward_scoring_operations.evaluation.PROTOCOL
    (tmp_path / "docs").mkdir()
    (tmp_path / protocol).write_bytes((ROOT / protocol).read_bytes())
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    monkeypatch.chdir(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("Status attempted a database connection or model calculation")

    monkeypatch.setattr(forward_operations, "connect_database", forbidden)
    monkeypatch.setattr(
        forward_scoring_operations.evaluation, "connect_database", forbidden
    )
    monkeypatch.setattr(forward_operations.forward, "fit_forward", forbidden)
    assert cli.main(["forward-status"]) == 0
    assert forward_scoring_operations.main(["status"]) == 0
    assert {
        str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    } == before
    capsys.readouterr()
    script = (OPS / "status.sh").read_text()
    assert "forward-status" in script
    assert "forward_scoring_operations status" in script
    assert "env-file" not in script and "cycle" not in script


def test_full_size_synthetic_fixture_keeps_all_checks_and_holdout_barrier(tmp_path):
    from backtest_badger import model_data

    source = tmp_path / "synthetic"
    pins = benchmark.synthetic_source(source)
    metadata, rows = model_data.load_model_data(source, training_only=True, **pins)
    assert {s: len(v["train"]) for s, v in rows.items()} == {
        "BTCUSDT": 13782,
        "ETHUSDT": 13783,
    }
    assert all(not v["validation"] for v in rows.values())
    assert metadata["counts"]["BTCUSDT"]["splits"] == model_data.COUNTS["BTCUSDT"]
    with (source / "research.csv").open("a") as handle:
        handle.write("corruption")
    with pytest.raises(ValueError, match="SHA-256"):
        model_data.load_model_data(source, training_only=True, **pins)


def test_benchmark_watchdog_is_a_failure(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["benchmark.py"])

    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 600
        raise subprocess.TimeoutExpired("synthetic", 600)

    monkeypatch.setattr(benchmark.subprocess, "run", timeout)
    assert benchmark.main() == 1


def test_runtime_missing_file_is_reported_without_traceback(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["validate.py", "runtime", "--worker", "scoring"])

    def missing(_):
        raise FileNotFoundError("private-credential-value")

    monkeypatch.setattr(validate, "runtime", missing)
    assert validate.main() == 1
    error = capsys.readouterr().err
    assert "missing/unreadable" in error and "private-credential-value" not in error


def test_no_production_changes_in_templates():
    for path in (OPS / "systemd").iterdir():
        body = path.read_text()
        assert "POSTGRES_PASSWORD=" not in body
        assert "uv run" not in body
    # Prompt is archived as supplied, including the D1 stop boundary.
    prompt = (ROOT / "prompts/deployment/001-lightsail-foundation.md").read_text()
    assert "Do not stop the existing Mac LaunchAgents." in prompt


@pytest.fixture
def deployed(tmp_path, monkeypatch):
    """Isolated path/config model; ownership rules are tested separately above."""
    from types import SimpleNamespace

    releases = tmp_path / "releases"
    release = releases / ("a" * 40)
    release.mkdir(parents=True)
    current = tmp_path / "current"
    current.symlink_to(release)
    artifacts = tmp_path / "persistent/artifacts"
    artifacts.mkdir(parents=True)
    artifacts.parent.chmod(0o700)
    artifacts.chmod(0o700)
    for directory in {p for values in validate.WRITABLE.values() for p in values}:
        (artifacts / directory).mkdir(mode=0o700)
    (release / "artifacts").symlink_to(artifacts)
    config = tmp_path / "config"
    config.mkdir()
    (config / "worker.env").write_text(
        (OPS / "worker.env.example")
        .read_text()
        .replace("REPLACE_WITH_RANDOM_HEX_SECRET", "a" * 64)
    )
    values = validate.read_environment(config / "worker.env")
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    (release / "docs").mkdir()
    (release / "docs/stage-03c-forward-evaluation-protocol.md").write_text("synthetic")
    (release / "uv.lock").write_text("synthetic lock")
    (release / "deployment.json").write_text(
        json.dumps(
            {
                "git_commit": release.name,
                "python": "3.12.15",
                "machine": "x86_64",
                "files_sha256": {
                    "uv.lock": validate.hashlib.sha256(b"synthetic lock").hexdigest()
                },
                "packages": {"numpy": "synthetic-version"},
            }
        )
    )
    monkeypatch.setattr(validate, "CURRENT", current)
    monkeypatch.setattr(validate, "RELEASES", releases)
    monkeypatch.setattr(validate, "ARTIFACTS", artifacts)
    monkeypatch.setattr(validate, "CONFIG", config)
    monkeypatch.setattr(
        validate.pwd,
        "getpwnam",
        lambda _: SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid()),
    )
    monkeypatch.setattr(validate, "private_file", lambda *a, **kw: None)
    monkeypatch.setattr(validate.platform, "python_version", lambda: "3.12.15")
    monkeypatch.setattr(validate.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(validate.platform, "system", lambda: "Linux")
    monkeypatch.setattr(validate, "version", lambda _: "synthetic-version")
    monkeypatch.chdir(release)
    return release, artifacts


def test_runtime_scoring_does_not_require_training_and_is_read_only(deployed):
    release, artifacts = deployed
    before = {str(p): p.read_bytes() for p in release.rglob("*") if p.is_file()}
    validate.runtime("scoring")
    with pytest.raises(ValueError, match="Missing frozen training"):
        validate.runtime("collection")
    training = artifacts / "research/stage-2a-v1"
    training.mkdir(parents=True)
    for name in ("research.csv", "manifest.json"):
        (training / name).write_text("synthetic")
    validate.runtime("collection")
    assert {str(p): p.read_bytes() for p in release.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize(
    "failure", ["link", "directory_mode", "lockfile", "environment", "dependency"]
)
def test_runtime_rejects_drift(deployed, monkeypatch, failure):
    release, artifacts = deployed
    if failure == "link":
        (release / "artifacts").unlink()
        (release / "artifacts").symlink_to(release)
    elif failure == "directory_mode":
        artifacts.chmod(0o755)
    elif failure == "lockfile":
        (release / "uv.lock").write_text("modified")
    elif failure == "environment":
        monkeypatch.setenv("POSTGRES_HOST", "192.0.2.1")
    else:
        monkeypatch.setattr(validate, "version", lambda _: "changed")
    with pytest.raises(ValueError):
        validate.runtime("scoring")

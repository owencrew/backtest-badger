"""D2A failure boundaries use synthetic trees and mocked Docker/systemd only."""

import importlib
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

OPS = Path(__file__).resolve().parents[1] / "ops/lightsail"
sys.path.insert(0, str(OPS))
r = importlib.import_module("rehearsal")
f = importlib.import_module("rehearsal_files")
db = importlib.import_module("rehearsal_db")
IDENT = "r20261014t220000z-1234abcd"


@pytest.fixture
def tree(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    for name in (
        "raw/data.bin",
        "forward-predictions/.cycle.lock",
        "ops/.x.partial",
        "backtests/test.csv",
        "forward-outcomes/original.json",
    ):
        path = source / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"exact\x00bytes\n" + name.encode())
        path.chmod(0o400)
        os.utime(path, ns=(1792012345123456789, 1792012345123456789))
    (source / "empty").mkdir()
    return source


def test_archive_complete_roundtrip_preserves_bytes_modes_nanoseconds(tree, tmp_path):
    original = f.inventory(tree)
    archive = tmp_path / "copy.tar"
    f.archive(tree, archive)
    captured = f.archive_inventory(archive)
    f.assert_inventory(original, captured)
    restored = tmp_path / "restored"
    f.extract(archive, restored, captured)
    f.assert_inventory(original, f.inventory(restored))
    assert (restored / "forward-predictions/.cycle.lock").exists()
    assert (restored / "ops/.x.partial").exists()
    with pytest.raises(FileExistsError):
        f.extract(archive, restored, captured)


@pytest.mark.parametrize(
    "name", ["../escape", "/absolute", "a/../../escape", "a//b", "./file", "."]
)
def test_reject_archive_traversal(name, tmp_path):
    archive = tmp_path / "evil.tar"
    with tarfile.open(archive, "w") as t:
        item = tarfile.TarInfo(name)
        t.addfile(item, io.BytesIO(b""))
    with pytest.raises(ValueError, match="Unsafe"):
        f.archive_inventory(archive)


@pytest.mark.parametrize("kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE])
def test_archive_special_files_refused(kind, tmp_path):
    archive = tmp_path / "evil.tar"
    with tarfile.open(archive, "w") as t:
        item = tarfile.TarInfo("file")
        item.type = kind
        item.linkname = "/etc/passwd"
        t.addfile(item)
    with pytest.raises(ValueError, match="links/special"):
        f.archive_inventory(archive)


def test_source_symlink_is_issue_not_followed(tree, tmp_path):
    (tree / "linked").symlink_to(tmp_path)
    result = f.inventory(tree)
    assert result["issues"] == [{"path": "linked", "issue": "symlink-or-special-file"}]
    with pytest.raises(ValueError, match="links/special"):
        f.archive(tree, tmp_path / "failed.tar")
    assert (tmp_path / "failed.tar").exists()


def test_changes_and_missing_files_are_retained(tree):
    before = f.inventory(tree)
    path = tree / "new-journal.json"
    path.write_text("running")
    after = f.inventory(tree)
    assert f.differences(before, after)["extra"] == ["new-journal.json"]
    with pytest.raises(ValueError, match="Inventory mismatch"):
        f.assert_inventory(before, after)


@pytest.fixture
def bundle(tree, tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    for stem in ("source", "artifacts"):
        f.archive(tree, bundle / f"{stem}.tar")
        f.write_json(
            bundle / f"{stem}.archive.json", f.archive_inventory(bundle / f"{stem}.tar")
        )
    return bundle, f.seal(bundle)


def test_bundle_verification_and_no_overwrite(bundle):
    root, sha = bundle
    f.verify_bundle(root, sha)
    with pytest.raises(FileExistsError):
        f.seal(root)


@pytest.mark.parametrize(
    "damage", ["missing", "corrupt", "extra", "manifest", "partial"]
)
def test_corrupt_checksum_partial_transfer_refusal(bundle, damage):
    root, sha = bundle
    path = root / "artifacts.tar"
    if damage == "missing":
        path.unlink()
    elif damage == "corrupt":
        path.write_bytes(b"not a tar archive")
    elif damage == "extra":
        (root / "unexpected").write_text("x")
    elif damage == "manifest":
        (root / "bundle.json").write_text("{}")
    else:
        path.write_bytes(path.read_bytes()[:100])
    with pytest.raises(ValueError):
        f.verify_bundle(root, sha)


def test_corrupt_archive_rejected_before_extract(tmp_path):
    bad = tmp_path / "bad.tar"
    bad.write_bytes(b"corrupt")
    with pytest.raises(tarfile.ReadError):
        f.extract(bad, tmp_path / "output", {"entries": {}})
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "path",
    [
        "/var/lib/backtest-badger/artifacts",
        "/opt/backtest-badger/current",
        "/etc/backtest-badger/postgres.env",
        "relative/path",
    ],
)
def test_production_paths_refused(path):
    with pytest.raises(ValueError):
        r.safe_destination(Path(path))


def test_symlink_destination_refused(tmp_path):
    (tmp_path / "alias").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        r.safe_destination(tmp_path / "alias/out")


def test_wrong_host_fails_before_docker(monkeypatch):
    monkeypatch.setattr(r.socket, "gethostname", lambda: "mac")
    monkeypatch.setattr(r, "docker", lambda *a: pytest.fail("Docker must not run"))
    with pytest.raises(ValueError, match="Wrong host"):
        r.target(SimpleNamespace(expect_host="server", id=IDENT))


@pytest.mark.parametrize("value", ["production", "../escape", "", "r20261014t220000z"])
def test_bad_identifier(value):
    with pytest.raises(ValueError):
        r.names(value)


def test_nonempty_database_refused(monkeypatch):
    monkeypatch.setattr(r, "query_container", lambda *a: "1")
    with pytest.raises(ValueError, match="empty database"):
        r.require_empty("synthetic")


def test_empty_database_query_includes_sessions_and_other_schemas(monkeypatch):
    def query(container, text):
        assert (
            "pg_stat_activity" in text and "pg_extension" in text and "pg_proc" in text
        )
        return "0"

    monkeypatch.setattr(r, "query_container", query)
    r.require_empty("synthetic")


@pytest.fixture
def target_config(tmp_path, monkeypatch):
    root = tmp_path / IDENT
    root.mkdir(mode=0o700)
    project, volume, database = r.names(IDENT)
    plan = dict(
        id=IDENT,
        host="server",
        project=project,
        volume=volume,
        database=database,
        port=r.PORT,
        image={
            "reference": "postgres:17@sha256:" + "1" * 64,
            "image_id": "sha256:synthetic",
        },
    )
    values = dict(
        POSTGRES_IMAGE=plan["image"]["reference"],
        POSTGRES_DB=database,
        POSTGRES_PASSWORD="2" * 64,
        REHEARSAL_ID=IDENT,
        REHEARSAL_VOLUME=volume,
    )
    f.write_json(root / "plan.json", plan)
    (root / "postgres.env").write_text("\n".join(f"{k}={v}" for k, v in values.items()))
    (root / "readonly.env").write_text(
        f"POSTGRES_HOST=127.0.0.1\nPOSTGRES_PORT={r.PORT}\nPOSTGRES_DB={database}\n"
        f"POSTGRES_USER=d2a_admin\nPOSTGRES_PASSWORD={values['POSTGRES_PASSWORD']}\n"
    )
    (root / "worker.env").write_text(
        f"POSTGRES_HOST=127.0.0.1\nPOSTGRES_PORT={r.PORT}\nPOSTGRES_DB={database}\n"
        f"POSTGRES_USER=d2a_worker\nPOSTGRES_PASSWORD={'3' * 64}\n"
    )
    (root / "compose.yaml").write_bytes((OPS / "compose.rehearsal.yaml").read_bytes())
    for path in root.iterdir():
        path.chmod(0o600)
    args = SimpleNamespace(
        id=IDENT,
        expect_host="server",
        bundle_sha256="a" * 64,
        confirm=volume,
        pg_version="17.9",
        required_free_bytes=1,
    )
    monkeypatch.setattr(r, "target", lambda _: root)
    return root, plan, values, args


def test_wrong_database_configuration_refused(target_config):
    root, plan, values, args = target_config
    assert r.configuration(root, args)[0] == plan
    values["POSTGRES_DB"] = "backtest_badger"
    (root / "postgres.env").write_text("\n".join(f"{k}={v}" for k, v in values.items()))
    with pytest.raises(ValueError, match="configuration mismatch"):
        r.configuration(root, args)


def test_preexisting_volume_refused_without_mutation(target_config, monkeypatch):
    root, plan, values, args = target_config
    monkeypatch.setattr(r, "verify_bundle", lambda *a: None)
    calls = []

    def docker(*args):
        calls.append(args)
        assert args == ("volume", "ls", "--format", "{{.Name}}")
        return plan["volume"].encode()

    monkeypatch.setattr(r, "docker", docker)
    with pytest.raises(ValueError, match="Pre-existing rehearsal volume"):
        r.init(args)
    assert len(calls) == 1 and not (root / "INIT-ATTEMPT.json").exists()


def test_restore_requires_exact_confirmation(target_config, monkeypatch):
    root, plan, values, args = target_config
    args.confirm = "backtest_badger"
    monkeypatch.setattr(
        r, "docker", lambda *a: pytest.fail("must refuse before Docker")
    )
    with pytest.raises(ValueError, match="Confirm exact rehearsal database"):
        r.restore(args)


def test_configuration_does_not_accept_compose_drift(target_config):
    root, _, _, args = target_config
    (root / "compose.yaml").write_text("production: unsafe")
    with pytest.raises(ValueError, match="template changed"):
        r.configuration(root, args)


def test_subprocess_errors_do_not_print_secrets(monkeypatch, capsys):
    monkeypatch.setattr(
        r, "target", lambda _: (_ for _ in ()).throw(RuntimeError("secret"))
    )
    assert r.main(["preflight", "--id", IDENT, "--expect-host", "server"]) == 1
    assert "secret" not in capsys.readouterr().err


def test_pg_dump_schema_normalization_only_transport_headers():
    a = (
        b"-- Dumped from database version 17.1\n\\restrict abc\n"
        b"CREATE TABLE t(a numeric);\n\\unrestrict abc\n"
    )
    b = (
        b"-- Dumped from database version 17.9\n\\restrict xyz\n"
        b"CREATE TABLE t(a numeric);\n\\unrestrict xyz\n"
    )
    assert db.schema_digest(a) == db.schema_digest(b)
    assert db.schema_digest(a) != db.schema_digest(b.replace(b"numeric", b"float"))


def test_compose_loopback_external_unique_volume_no_pull(tmp_path):
    env = dict(
        os.environ,
        POSTGRES_IMAGE="postgres:17@sha256:" + "1" * 64,
        POSTGRES_DB=r.names(IDENT)[2],
        POSTGRES_PASSWORD="synthetic",
        REHEARSAL_ID=IDENT,
        REHEARSAL_VOLUME=r.names(IDENT)[1],
    )
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            os.devnull,
            "-f",
            str(OPS / "compose.rehearsal.yaml"),
            "config",
            "--format",
            "json",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    service = data["services"]["postgres"]
    assert service["ports"] == [
        {
            "mode": "ingress",
            "host_ip": "127.0.0.1",
            "target": 5432,
            "published": "55437",
            "protocol": "tcp",
        }
    ]
    assert service["pull_policy"] == "never" and service["restart"] == "no"
    assert service["platform"] == "linux/amd64"
    assert data["volumes"]["rehearsal_data"] == {
        "name": r.names(IDENT)[1],
        "external": True,
    }


@pytest.mark.parametrize("change", ["image", "database", "mount", "binding", "project"])
def test_actual_container_isolation_is_checked(target_config, monkeypatch, change):
    root, plan, values, _ = target_config
    cid = "c" * 64
    data = {
        "Config": {
            "Labels": {
                "badger.d2a": IDENT,
                "com.docker.compose.project": plan["project"],
            },
            "Env": [f"POSTGRES_DB={plan['database']}", "POSTGRES_USER=d2a_admin"],
        },
        "Image": plan["image"]["image_id"],
        "NetworkSettings": {
            "Ports": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "55437"}]}
        },
        "Mounts": [{"Name": plan["volume"], "Destination": "/var/lib/postgresql/data"}],
    }
    if change == "image":
        data["Image"] = "another-image"
    elif change == "database":
        data["Config"]["Env"][0] = "POSTGRES_DB=backtest_badger"
    elif change == "mount":
        data["Mounts"][0]["Name"] = "backtest-badger-pg17"
    elif change == "binding":
        data["NetworkSettings"]["Ports"]["5432/tcp"][0]["HostIp"] = "0.0.0.0"
    else:
        data["Config"]["Labels"]["com.docker.compose.project"] = (
            "backtest-badger-lightsail"
        )
    monkeypatch.setattr(r, "compose", lambda *a: cid.encode())
    monkeypatch.setattr(r, "docker", lambda *a: json.dumps([data]).encode())
    with pytest.raises(ValueError, match="isolation mismatch"):
        r.live_container(root, plan)


def test_remote_target_override_removed(monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "tcp://production:2375")
    monkeypatch.setenv("DOCKER_CONTEXT", "production")

    def run(command, **kwargs):
        assert command[:3] == ["docker", "--context", "default"]
        assert "DOCKER_HOST" not in kwargs["env"]
        assert "DOCKER_CONTEXT" not in kwargs["env"]
        return b"ok"

    monkeypatch.setattr(db, "run", run)
    assert db.docker("version") == b"ok"


def test_source_inventory_records_mid_read_change(tree, monkeypatch):
    original = f.hashlib.file_digest
    changed = False
    path = tree / "raw/data.bin"

    def mutate(handle, algorithm):
        nonlocal changed
        result = original(handle, algorithm)
        if not changed:
            changed = True
            path.chmod(0o600)
            with path.open("ab") as out:
                out.write(b"concurrent append")
        return result

    # Ensure mutation happens while the selected file is being hashed.
    for item in tree.rglob("*"):
        if item.is_file() and item != path:
            item.unlink()
    monkeypatch.setattr(f.hashlib, "file_digest", mutate)
    result = f.inventory(tree)
    assert any(i["issue"] == "changed-during-read" for i in result["issues"])


def test_duplicate_archive_member_is_refused(tmp_path):
    archive = tmp_path / "duplicate.tar"
    with tarfile.open(archive, "w") as tar:
        for _ in range(2):
            tar.addfile(tarfile.TarInfo("file"), io.BytesIO(b""))
    with pytest.raises(ValueError, match="Duplicate"):
        f.archive_inventory(archive)


def test_readonly_connection_config_cannot_address_production(target_config):
    root, _, _, args = target_config
    body = (
        (root / "readonly.env")
        .read_text()
        .replace("POSTGRES_PORT=55437", "POSTGRES_PORT=5432")
    )
    (root / "readonly.env").write_text(body)
    with pytest.raises(ValueError, match="Inspection connection"):
        r.configuration(root, args)


def test_image_selection_refuses_floating_and_wrong_architecture(monkeypatch):
    with pytest.raises(ValueError, match="immutable digest"):
        r.image_check("postgres:17", "17.9")
    monkeypatch.setattr(
        r,
        "docker",
        lambda *a: json.dumps([{"Architecture": "arm64", "Os": "linux"}]).encode(),
    )
    with pytest.raises(ValueError, match="platform"):
        r.image_check("postgres:17@sha256:" + "a" * 64, "17.9")


def test_report_differentiates_incomplete_and_not_run(target_config, monkeypatch):
    root, _, _, args = target_config
    monkeypatch.setattr(r, "verify_bundle", lambda *a: None)
    (root / "inbox").mkdir()
    f.write_json(root / "inbox/online-changes.json", {"changed": ["journal"]})
    f.write_json(root / "RESTORE-ATTEMPT.json", {"at": "synthetic"})
    r.report(args)
    report = f.read_json(root / "rehearsal-report.json")
    assert report["d2b_ready"] is False
    assert report["checks"]["database-comparison.json"]["status"] == "INCOMPLETE"
    assert report["checks"]["evidence-validation/result.json"]["status"] == "NOT_RUN"
    assert report["online_changes"] == {"changed": ["journal"]}
    with pytest.raises(FileExistsError):
        r.report(args)

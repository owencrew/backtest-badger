#!/usr/bin/env python3
"""Operator-only D2A rehearsal. No scheduler, production restore or cleanup commands."""

import argparse
import importlib.metadata
import json
import os
import platform
import re
import secrets
import shutil
import socket
import stat
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from rehearsal_db import docker, query_container, run, snapshot
from rehearsal_files import (
    archive,
    archive_inventory,
    assert_inventory,
    differences,
    digest,
    extract,
    inventory,
    read_json,
    require,
    seal,
    verify_bundle,
    write_json,
)

HERE = Path(__file__).resolve().parent
BASE = Path("/var/lib/backtest-badger-rehearsals")
PRODUCTION = (
    Path("/var/lib/backtest-badger"),
    Path("/opt/backtest-badger"),
    Path("/etc/backtest-badger"),
)
PORT = 55437


def now():
    return datetime.now(UTC).isoformat()


def host(expected, system):
    require(
        socket.gethostname() == expected and platform.system() == system,
        "Wrong host/OS; no operation performed.",
    )


def identifier(value):
    require(
        re.fullmatch(r"r\d{8}t\d{6}z-[0-9a-f]{8}", value),
        "Require unique rYYYYMMDDtHHMMSSz-8hex rehearsal ID.",
    )
    return value


def safe_destination(path):
    path = Path(path)
    require(
        path.is_absolute() and path == path.resolve(),
        "Require canonical absolute path without symlinks.",
    )
    require(
        not any(path == p or path.is_relative_to(p) for p in PRODUCTION),
        "Production path refused.",
    )
    return path


def private(path, directory=False):
    info = path.lstat()
    require(
        (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
        and info.st_uid == os.getuid()
        and stat.S_IMODE(info.st_mode) == (0o700 if directory else 0o600),
        "Require current-user ownership and private 0700/0600 permissions.",
    )


def source_copy(repo, output):
    def git(*args):
        return run(["git", "-C", str(repo), *args])

    tracked = git("ls-files", "-z").decode().split("\0")[:-1]
    untracked = (
        git("ls-files", "--others", "--exclude-standard", "-z")
        .decode()
        .split("\0")[:-1]
    )
    names = sorted(set(tracked + untracked))
    for name in names:
        parts = Path(name).parts
        require(
            not any(
                p in (".env", ".venv", ".git", ".ssh", ".aws", "artifacts")
                or p.endswith((".pem", ".key"))
                for p in parts
            ),
            "Sensitive/unexpected source path; review before archiving.",
        )
        require(
            (repo / name).is_file() and not (repo / name).is_symlink(),
            "Deleted/linked source path; review before archiving.",
        )
    write_json(
        output / "source-state.json",
        {
            "commit": git("rev-parse", "HEAD").decode().strip(),
            "status": git("status", "--porcelain").decode(),
            "untracked_included": untracked,
            "files_sha256": {name: digest(repo / name) for name in names},
            "runtime": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "machine": platform.machine(),
            },
            "packages": {
                d.metadata["Name"]: d.version
                for d in importlib.metadata.distributions()
                if d.metadata["Name"]
            },
        },
    )
    git("bundle", "create", str(output / "source.bundle"), "HEAD")
    git("bundle", "verify", str(output / "source.bundle"))
    (output / "source-working-tree.patch").write_bytes(git("diff", "--binary", "HEAD"))
    with tempfile.TemporaryDirectory(prefix="badger-d2a-source-") as tmp:
        root = Path(tmp)
        for name in names:
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / name, dest)
        archive(root, output / "source.tar")
    archived = archive_inventory(output / "source.tar")
    write_json(output / "source.archive.json", archived)
    expected = read_json(output / "source-state.json")["files_sha256"]
    require(
        all(
            archived["entries"][n]["sha256"] == sha == digest(repo / n)
            for n, sha in expected.items()
        ),
        "Source changed during archive.",
    )


def backup(args):
    host(args.expect_host, "Darwin")
    repo = Path.cwd().resolve()
    require(
        (repo / "AGENTS.md").is_file() and (repo / "src/backtest_badger").is_dir(),
        "Run from the Backtest Badger repository.",
    )
    dest = safe_destination(Path(args.output))
    require(not dest.is_relative_to(repo), "Backup must be outside source repository.")
    private(dest.parent, directory=True)
    from backtest_badger.config import load_settings

    settings = load_settings()
    require(
        settings.host == "127.0.0.1"
        and settings.database == args.expect_database
        and settings.port == args.expect_port,
        "Source host/database/port mismatch.",
    )
    require(
        re.fullmatch(r"[0-9a-f]{64}", args.container),
        "Full source container ID required.",
    )
    labels = json.loads(
        docker("inspect", "--format", "{{json .Config.Labels}}", args.container)
    )
    require(
        labels.get("com.docker.compose.project") == "backtest-badger"
        and labels.get("com.docker.compose.service") == "postgres",
        "Source container is not the Backtest Badger development DB.",
    )
    dest.mkdir(mode=0o700)
    write_json(
        dest / "snapshot-kind.json",
        {
            "kind": "NONAUTHORITATIVE_ONLINE_D2A_REHEARSAL",
            "started_at": now(),
            "host": args.expect_host,
            "coherent_cross_system_checkpoint": False,
            "schedulers": "left running; no lifecycle commands issued",
        },
    )
    # Failure leaves all files in place; no COMPLETE/bundle manifest is emitted.
    try:
        source_copy(repo, dest)
        snapshot(settings, args.container, dest, dump=True)
        before = inventory(repo / "artifacts")
        write_json(dest / "artifacts.before.json", before)
        require(
            not before["issues"],
            "Unstable/unreadable initial inventory; retain and retry.",
        )
        archive(repo / "artifacts", dest / "artifacts.tar")
        captured = archive_inventory(dest / "artifacts.tar")
        after = inventory(repo / "artifacts")
        write_json(dest / "artifacts.archive.json", captured)
        write_json(dest / "artifacts.after.json", after)
        write_json(
            dest / "online-changes.json",
            {
                "before_to_archive": differences(before, captured),
                "archive_to_after": differences(captured, after),
                "finished_at": now(),
                "limitation": (
                    "May miss changes between scans; never a coherent checkpoint."
                ),
            },
        )
        print("Bundle manifest SHA-256 (retain separately): " + seal(dest))
    except Exception:
        write_json(
            dest / "FAILED.json",
            {
                "at": now(),
                "status": "incomplete; do not restore",
                "details": "suppressed to protect credentials",
            },
        )
        raise


def target(args):
    host(args.expect_host, "Linux")
    require(platform.machine() == "x86_64", "Require Linux x86_64 target.")
    ident = identifier(args.id)
    private(BASE, directory=True)
    root = safe_destination(BASE / ident)
    require(
        not os.path.lexists("/etc/backtest-badger/workers-approved"),
        "Production worker approval gate must be absent.",
    )
    volumes = docker("volume", "ls", "--format", "{{.Name}}").decode().splitlines()
    require("backtest-badger-pg17" not in volumes, "Production database volume exists.")
    for worker in ("collection", "scoring"):
        for suffix in ("service", "timer"):
            unit = f"backtest-badger-{worker}.{suffix}"
            values = run(
                [
                    "systemctl",
                    "show",
                    unit,
                    "--property=LoadState,ActiveState,UnitFileState",
                ]
            )
            props = dict(line.split("=", 1) for line in values.decode().splitlines())
            require(
                props.get("LoadState") == "loaded"
                and props.get("ActiveState") == "inactive"
                and props.get("UnitFileState") in ("disabled", "static"),
                "Production units must be installed, inactive and disabled/static.",
            )
    return root


def names(ident):
    project = "badger-d2a-" + identifier(ident)
    return project, project + "-pg17", "d2a_" + ident.replace("-", "_")


def image_check(image, version):
    require(
        re.fullmatch(r"postgres:17@sha256:[0-9a-f]{64}", image),
        "Require reviewed official postgres:17 immutable digest.",
    )
    require(re.fullmatch(r"17\.\d+", version), "Require reviewed major.minor version.")
    inspected = json.loads(docker("image", "inspect", image))[0]
    require(
        inspected["Architecture"] == "amd64" and inspected["Os"] == "linux",
        "Wrong PostgreSQL image platform.",
    )
    require(
        any(r.endswith(image.split("@")[1]) for r in inspected["RepoDigests"]),
        "Image digest not present locally; pull reviewed digest explicitly.",
    )
    # --entrypoint bypasses initdb; no volume/network is attached.
    actual = (
        docker(
            "run",
            "--rm",
            "--pull=never",
            "--network=none",
            "--entrypoint",
            "postgres",
            image,
            "--version",
        )
        .decode()
        .strip()
    )
    require(
        re.search(r"\b" + re.escape(version) + r"\b", actual), "Image version mismatch."
    )
    return {
        "reference": image,
        "image_id": inspected["Id"],
        "version": actual,
        "architecture": inspected["Architecture"],
        "repo_digests": inspected["RepoDigests"],
    }


def prepare(args):
    root = target(args)
    require(not root.exists(), "Rehearsal directory already exists; use a new ID.")
    reviewed = image_check(args.image, args.pg_version)
    root.mkdir(mode=0o700)
    project, volume, database = names(args.id)
    write_json(
        root / "plan.json",
        {
            "id": args.id,
            "host": args.expect_host,
            "image": reviewed,
            "project": project,
            "volume": volume,
            "database": database,
            "port": PORT,
            "created_at": now(),
        },
    )
    password = secrets.token_hex(32)
    (root / "postgres.env").write_text(
        f"POSTGRES_IMAGE={args.image}\nPOSTGRES_DB={database}\n"
        f"POSTGRES_PASSWORD={password}\nREHEARSAL_ID={args.id}\nREHEARSAL_VOLUME={volume}\n"
    )
    (root / "readonly.env").write_text(
        f"POSTGRES_HOST=127.0.0.1\nPOSTGRES_PORT={PORT}\nPOSTGRES_DB={database}\n"
        f"POSTGRES_USER=d2a_admin\nPOSTGRES_PASSWORD={password}\n"
    )
    (root / "worker.env").write_text(
        f"POSTGRES_HOST=127.0.0.1\nPOSTGRES_PORT={PORT}\nPOSTGRES_DB={database}\n"
        f"POSTGRES_USER=d2a_worker\nPOSTGRES_PASSWORD={secrets.token_hex(32)}\n"
    )
    shutil.copyfile(HERE / "compose.rehearsal.yaml", root / "compose.yaml")
    print("Private isolated rehearsal prepared; database not started.")


def configuration(root, args):
    private(root, directory=True)
    for name in (
        "plan.json",
        "postgres.env",
        "readonly.env",
        "worker.env",
        "compose.yaml",
    ):
        private(root / name)
    plan = read_json(root / "plan.json")
    project, volume, database = names(args.id)
    require(
        plan["host"] == args.expect_host
        and plan["id"] == args.id
        and (plan["project"], plan["volume"], plan["database"], plan["port"])
        == (project, volume, database, PORT),
        "Rehearsal plan identity mismatch.",
    )
    require(
        (root / "compose.yaml").read_bytes()
        == (HERE / "compose.rehearsal.yaml").read_bytes(),
        "Rehearsal Compose template changed.",
    )
    values = dict(
        line.split("=", 1) for line in (root / "postgres.env").read_text().splitlines()
    )
    require(
        set(values)
        == {
            "POSTGRES_IMAGE",
            "POSTGRES_DB",
            "POSTGRES_PASSWORD",
            "REHEARSAL_ID",
            "REHEARSAL_VOLUME",
        }
        and values["POSTGRES_IMAGE"] == plan["image"]["reference"]
        and values["POSTGRES_DB"] == database
        and values["REHEARSAL_ID"] == args.id
        and values["REHEARSAL_VOLUME"] == volume
        and re.fullmatch(r"[0-9a-f]{64}", values["POSTGRES_PASSWORD"]),
        "Private rehearsal configuration mismatch; values suppressed.",
    )
    connection_values = dict(
        line.split("=", 1) for line in (root / "readonly.env").read_text().splitlines()
    )
    require(
        connection_values
        == {
            "POSTGRES_HOST": "127.0.0.1",
            "POSTGRES_PORT": str(PORT),
            "POSTGRES_DB": database,
            "POSTGRES_USER": "d2a_admin",
            "POSTGRES_PASSWORD": values["POSTGRES_PASSWORD"],
        },
        "Inspection connection must match the exact rehearsal target.",
    )
    worker = dict(
        line.split("=", 1) for line in (root / "worker.env").read_text().splitlines()
    )
    require(
        set(worker) == set(connection_values)
        and all(
            worker[k] == connection_values[k]
            for k in ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB")
        )
        and worker["POSTGRES_USER"] == "d2a_worker"
        and re.fullmatch(r"[0-9a-f]{64}", worker["POSTGRES_PASSWORD"])
        and worker["POSTGRES_PASSWORD"] != values["POSTGRES_PASSWORD"],
        "Worker configuration must be private, separate and rehearsal-only.",
    )
    return plan, values


def compose(root, plan, *args):
    # Strip interpolation overrides as well as remote Docker target overrides.
    saved = {
        k: os.environ.pop(k)
        for k in list(os.environ)
        if k.startswith(("POSTGRES_", "REHEARSAL_"))
    }
    try:
        return docker(
            "compose",
            "--project-name",
            plan["project"],
            "--env-file",
            str(root / "postgres.env"),
            "-f",
            str(root / "compose.yaml"),
            *args,
        )
    finally:
        os.environ.update(saved)


def live_container(root, plan):
    container = compose(root, plan, "ps", "-q", "postgres").decode().strip()
    require(
        re.fullmatch(r"[0-9a-f]{64}", container),
        "Exactly one rehearsal container required.",
    )
    data = json.loads(docker("inspect", container))[0]
    env = dict(v.split("=", 1) for v in data["Config"]["Env"] if "=" in v)
    require(
        data["Config"]["Labels"].get("badger.d2a") == plan["id"]
        and data["Config"]["Labels"].get("com.docker.compose.project")
        == plan["project"]
        and env["POSTGRES_DB"] == plan["database"]
        and env["POSTGRES_USER"] == "d2a_admin"
        and data["Image"] == plan["image"]["image_id"]
        and data["NetworkSettings"]["Ports"]
        == {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(PORT)}]}
        and len(data["Mounts"]) == 1
        and data["Mounts"][0].get("Name") == plan["volume"]
        and data["Mounts"][0]["Destination"] == "/var/lib/postgresql/data",
        "Container image/database/volume/network isolation mismatch.",
    )
    vol = json.loads(docker("volume", "inspect", plan["volume"]))[0]
    require(
        vol.get("Labels", {}).get("badger.d2a") == plan["id"], "Volume label mismatch."
    )
    return container


def init(args):
    root = target(args)
    plan, _ = configuration(root, args)
    verify_bundle(root / "inbox", args.bundle_sha256)
    require(
        args.confirm == plan["volume"], "Confirm exact disposable rehearsal volume."
    )
    volumes = docker("volume", "ls", "--format", "{{.Name}}").decode().splitlines()
    require(plan["volume"] not in volumes, "Pre-existing rehearsal volume refused.")
    require(
        not docker(
            "ps",
            "-aq",
            "--filter",
            "label=com.docker.compose.project=" + plan["project"],
        ).strip(),
        "Pre-existing rehearsal container refused.",
    )
    image_check(plan["image"]["reference"], args.pg_version)
    required = args.required_free_bytes
    require(
        required > 0 and shutil.disk_usage(root).free >= required,
        "Insufficient reviewed disk capacity.",
    )
    write_json(
        root / "INIT-ATTEMPT.json",
        {"at": now(), "volume": plan["volume"], "reviewed_free_bytes": required},
    )
    docker("volume", "create", "--label", "badger.d2a=" + args.id, plan["volume"])
    compose(root, plan, "up", "-d", "--wait")
    container = live_container(root, plan)
    write_json(
        root / "initialized.json",
        {"at": now(), "container": container, "volume": plan["volume"]},
    )


def settings_for(plan, values):
    from backtest_badger.config import Settings

    return Settings(
        "127.0.0.1",
        PORT,
        plan["database"],
        "d2a_admin",
        values["POSTGRES_PASSWORD"],
        "INFO",
    )


def require_empty(container):
    # No app relations/functions/extensions/extra schemas or other sessions.
    answer = query_container(
        container,
        """
        SELECT (SELECT count(*) FROM pg_class c
                 JOIN pg_namespace n ON n.oid=c.relnamespace
                 WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema')
             + (SELECT count(*) FROM pg_proc p
                 JOIN pg_namespace n ON n.oid=p.pronamespace
                 WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema')
             + (SELECT count(*) FROM pg_namespace WHERE nspname NOT LIKE 'pg_%'
                 AND nspname NOT IN ('public','information_schema'))
             + (SELECT count(*) FROM pg_extension WHERE extname <> 'plpgsql')
             + (SELECT count(*) FROM pg_stat_activity WHERE datname=current_database()
                 AND pid <> pg_backend_pid());
    """,
    )
    require(answer == "0", "Restore requires empty database and no other sessions.")


def restore(args):
    root = target(args)
    plan, values = configuration(root, args)
    require(args.confirm == plan["database"], "Confirm exact rehearsal database.")
    verify_bundle(root / "inbox", args.bundle_sha256)
    require(not (root / "inbox/FAILED.json").exists(), "Failed source backup refused.")
    container = live_container(root, plan)
    dump = root / "inbox/database.dump"
    with dump.open("rb") as handle:
        listing = docker("exec", "-i", container, "pg_restore", "--list", stdin=handle)
    require(b"TABLE DATA" in listing, "Dump contains no table data.")
    require_empty(container)
    # Exclusive attempt marker means even a failed restore is never silently retried.
    write_json(
        root / "RESTORE-ATTEMPT.json",
        {
            "at": now(),
            "database": plan["database"],
            "bundle_sha256": args.bundle_sha256,
        },
    )
    with dump.open("rb") as handle:
        docker(
            "exec",
            "-i",
            container,
            "sh",
            "-ec",
            "exec pg_restore --exit-on-error --single-transaction --no-owner --no-acl "
            '-U "$POSTGRES_USER" -d "$POSTGRES_DB"',
            stdin=handle,
        )
    out = root / "restored-database"
    out.mkdir(mode=0o700)
    snapshot(settings_for(plan, values), container, out)
    source, restored = (
        read_json(root / "inbox/database.json"),
        read_json(out / "database.json"),
    )
    equal = source["logical"] == restored["logical"]
    isolated = (
        source["identity"]["system_identifier"]
        != restored["identity"]["system_identifier"]
    )
    write_json(
        root / "database-comparison.json",
        {
            "at": now(),
            "logical_equal": equal,
            "different_cluster": isolated,
            "source": source["identity"],
            "restored": restored["identity"],
            "passed": equal and isolated,
            "scope": (
                "all table rows, schemas, constraints, triggers, sequences, Alembic"
            ),
        },
    )
    require(
        equal and isolated, "Database comparison failed; retain logs and investigate."
    )
    # Privilege setup is a separate explicit operator step after exact comparison.


def unpack(args):
    root = target(args)
    configuration(root, args)
    bundle = root / "inbox"
    verify_bundle(bundle, args.bundle_sha256)
    require(not (bundle / "FAILED.json").exists(), "Failed source backup refused.")
    work = root / "work"
    extract(bundle / "source.tar", work, read_json(bundle / "source.archive.json"))
    extract(
        bundle / "artifacts.tar",
        work / "artifacts",
        read_json(bundle / "artifacts.archive.json"),
    )
    write_json(
        root / "extraction.json",
        {
            "at": now(),
            "uid": os.getuid(),
            "gid": os.getgid(),
            "bundle_sha256": args.bundle_sha256,
        },
    )


def evidence(args):
    root = target(args)
    configuration(root, args)
    work = root / "work"
    require(
        Path.cwd().resolve() == work and not work.is_symlink(),
        "Run evidence checks from the isolated work directory.",
    )
    require(
        Path(sys.executable).absolute().is_relative_to(work / ".venv"),
        "Use the rehearsal checkout's own Python environment.",
    )
    import backtest_badger

    require(
        Path(backtest_badger.__file__).resolve().is_relative_to(work / "src"),
        "Application import must resolve to isolated source.",
    )
    bundle = root / "inbox"
    verify_bundle(bundle, args.bundle_sha256)
    for name, sha in read_json(bundle / "source-state.json")["files_sha256"].items():
        require(
            digest(work / name) == sha, "Copied source/lock/protocol checksum mismatch."
        )
    expected = read_json(bundle / "artifacts.archive.json")
    assert_inventory(expected, inventory(work / "artifacts"))
    output = root / "evidence-validation"
    output.mkdir(mode=0o700)
    from backtest_badger import forward_evaluation, frozen, model_data

    forward_evaluation.protocol()
    frozen.load_frozen(
        work / "artifacts/exports/binance-4h-history-v1", acknowledge_incomplete=True
    )
    model_data.load_model_data(
        work / "artifacts/research/stage-2a-v1", training_only=True
    )
    commands = [
        [
            "-c",
            "from backtest_badger.cli import main; raise SystemExit(main())",
            "forward-status",
        ],
        ["-m", "backtest_badger.forward_scoring_operations", "status"],
        ["-m", "backtest_badger.forward_evaluation", "report"],
    ]
    statuses = []
    import subprocess

    env = {k: v for k, v in os.environ.items() if not k.startswith(("POSTGRES_", "PG"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for index, command in enumerate(commands):
        result = subprocess.run(
            [sys.executable, *command], env=env, capture_output=True, timeout=300
        )
        (output / f"{index}.json").write_bytes(result.stdout)
        # Offline commands have no credentials; still keep stderr out of console.
        (output / f"{index}.stderr").write_bytes(result.stderr)
        statuses.append(result.returncode)
    after = inventory(work / "artifacts")
    write_json(output / "after.json", after)
    unchanged = not any(differences(expected, after).values())
    write_json(
        output / "result.json",
        {
            "at": now(),
            "exit_codes": statuses,
            "unchanged": unchanged,
            "passed": unchanged and statuses == [0, 0, 0],
            "original_mac_replay": "not established by Linux structural validation",
            "linux_reproduction": "not run; separate diagnostics required",
        },
    )
    require(
        unchanged and statuses == [0, 0, 0],
        "Evidence check incomplete/failed; inspect retained reports without repair.",
    )


def report(args):
    root = target(args)
    configuration(root, args)
    verify_bundle(root / "inbox", args.bundle_sha256)
    result = {
        "at": now(),
        "kind": "D2A_ONLY_NOT_CUTOVER_APPROVAL",
        "checks": {},
        "d2b_ready": False,
        "outstanding": [
            "quiescent final checkpoint",
            "two independent encrypted backups",
            "Mac original-runtime replay coverage",
            "Linux reproduction diagnostics",
            "clock/provider/actual concurrent-load and disk/CPU-credit review",
            "least-privilege role acceptance",
            "explicit D2B authorisation",
        ],
    }
    for name, marker in (
        ("initialized.json", "INIT-ATTEMPT.json"),
        ("database-comparison.json", "RESTORE-ATTEMPT.json"),
        ("evidence-validation/result.json", "evidence-validation"),
        ("extraction.json", "work"),
    ):
        path = root / name
        result["checks"][name] = (
            read_json(path)
            if path.exists()
            else {"status": "INCOMPLETE" if (root / marker).exists() else "NOT_RUN"}
        )
    result["online_changes"] = read_json(root / "inbox/online-changes.json")
    write_json(root / "rehearsal-report.json", result)
    print("Rehearsal report retained. D2B remains unapproved.")


def main(argv=None):
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("backup")
    p.add_argument("--expect-host", required=True)
    p.add_argument("--expect-database", required=True)
    p.add_argument("--expect-port", required=True, type=int)
    p.add_argument("--container", required=True)
    p.add_argument("--output", required=True)
    for cmd in (
        "prepare",
        "init",
        "restore",
        "unpack",
        "evidence",
        "report",
        "preflight",
    ):
        p = subs.add_parser(cmd)
        p.add_argument("--expect-host", required=True)
        p.add_argument("--id", required=True)
        if cmd in ("init", "restore", "unpack", "evidence", "report"):
            p.add_argument("--bundle-sha256", required=True)
        if cmd in ("prepare", "init"):
            p.add_argument("--pg-version", required=True)
        if cmd == "prepare":
            p.add_argument("--image", required=True)
        if cmd in ("init", "restore"):
            p.add_argument("--confirm", required=True)
        if cmd == "init":
            p.add_argument("--required-free-bytes", type=int, required=True)
    p = subs.add_parser("verify")
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--bundle-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            verify_bundle(args.bundle, args.bundle_sha256)
        elif args.command == "preflight":
            root = target(args)
            configuration(root, args)
            print("Host, production inactivity and isolated configuration checked.")
        else:
            globals()[args.command](args)
    except ValueError as error:
        print("D2A refused: " + str(error), file=sys.stderr)
        return 1
    except Exception as error:
        # Database, Docker and parser diagnostics can contain connection secrets.
        print(
            "D2A failed; details suppressed; retain partial output. "
            f"Category: {type(error).__name__}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only deployment checks; never starts containers, workers or migrations."""

import argparse
import hashlib
import json
import os
import platform
import pwd
import re
import shutil
import stat
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

HERE = Path(__file__).resolve().parent
CURRENT = Path("/opt/backtest-badger/current")
RELEASES = Path("/opt/backtest-badger/releases")
ARTIFACTS = Path("/var/lib/backtest-badger/artifacts")
CONFIG = Path("/etc/backtest-badger")
WRITABLE = {
    "collection": ("forward-predictions", "forward-operations", "rest"),
    "scoring": ("forward-outcomes", "forward-scoring-operations"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def private_file(path, *, uid, gid, mode):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode), f"Expected a regular private file: {path}")
    require(
        (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode)) == (uid, gid, mode),
        f"Incorrect owner/group/mode: {path}",
    )


def read_environment(path):
    """Deliberately narrow shared subset of systemd/Compose env-file syntax."""
    values = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        require(
            separator and re.fullmatch(r"[A-Z_]+", key) and key not in values,
            "Invalid or duplicate environment key; values suppressed.",
        )
        require(
            re.fullmatch(r"[A-Za-z0-9_./:@-]+", value) and "REPLACE" not in value,
            "Invalid literal environment value or unfilled placeholder; suppressed.",
        )
        values[key] = value
    return values


def check_worker_environment(values):
    require(values.get("POSTGRES_HOST") == "127.0.0.1", "DB must use 127.0.0.1.")
    require(values.get("POSTGRES_PORT") == "5432", "DB must use port 5432.")
    require(values.get("POSTGRES_USER") == "badger_worker", "Use the worker role.")
    require(values.get("POSTGRES_DB") == "backtest_badger", "Unexpected database.")
    require(
        re.fullmatch(r"[a-fA-F0-9]{64}", values.get("POSTGRES_PASSWORD", "")),
        "Worker password must be 32 random bytes encoded as 64 hex characters.",
    )
    require(values.get("LOG_LEVEL") == "INFO", "Use INFO logging.")
    require(
        set(values)
        == {
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_USER",
            "POSTGRES_DB",
            "POSTGRES_PASSWORD",
            "LOG_LEVEL",
        },
        "Unexpected worker environment keys.",
    )


def configuration():
    """Privileged read-only check; does not print resolved configuration."""
    account = pwd.getpwnam("ubuntu")
    info = CONFIG.lstat()
    require(
        stat.S_ISDIR(info.st_mode)
        and (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode))
        == (0, account.pw_gid, 0o750),
        "Configuration directory must be root:ubuntu 0750.",
    )
    private_file(CONFIG / "postgres.env", uid=0, gid=0, mode=0o600)
    private_file(CONFIG / "worker.env", uid=0, gid=account.pw_gid, mode=0o640)
    admin = read_environment(CONFIG / "postgres.env")
    worker = read_environment(CONFIG / "worker.env")
    check_worker_environment(worker)
    require(
        set(admin)
        == {"POSTGRES_IMAGE", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"}
        and admin["POSTGRES_DB"] == "backtest_badger"
        and admin["POSTGRES_USER"] == "badger_admin"
        and re.fullmatch(r"postgres:17@sha256:[0-9a-f]{64}", admin["POSTGRES_IMAGE"])
        and re.fullmatch(r"[a-fA-F0-9]{64}", admin["POSTGRES_PASSWORD"])
        and admin["POSTGRES_PASSWORD"] != worker["POSTGRES_PASSWORD"],
        "Invalid admin configuration/digest or reused password; values suppressed.",
    )
    print("Private configuration ownership, permissions and values validated.")


def run(arguments):
    require(shutil.which(arguments[0]), f"Missing dependency: {arguments[0]}")
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=60)
    require(result.returncode == 0, f"Validation command failed: {arguments[0]}")
    return result.stdout


def check_compose(config):
    require(set(config["services"]) == {"postgres"}, "Unexpected Compose service.")
    db = config["services"]["postgres"]
    ports = db["ports"]
    require(
        len(ports) == 1
        and ports[0]["host_ip"] == "127.0.0.1"
        and str(ports[0]["published"]) == "5432"
        and ports[0]["target"] == 5432,
        "PostgreSQL must publish only 127.0.0.1:5432.",
    )
    require(
        re.fullmatch(r"postgres:17@sha256:[0-9a-f]{64}", db["image"]),
        "Pin an immutable PostgreSQL 17 digest.",
    )
    require(db["restart"] == "unless-stopped", "Incorrect DB restart policy.")
    require(db["pull_policy"] == "never", "Runtime image pulls must be disabled.")
    require(int(db["mem_limit"]) == 1073741824, "Expected 1 GiB DB limit.")
    require(db["memswap_limit"] == db["mem_limit"], "DB swap must be disabled.")
    require(float(db["cpus"]) == 1, "Expected one CPU DB limit.")
    require(db["healthcheck"]["test"][0] == "CMD-SHELL", "Missing DB health check.")
    require(
        db["volumes"][0]["target"] == "/var/lib/postgresql/data"
        and db["volumes"][0]["source"] == "postgres_data"
        and config["volumes"]["postgres_data"]["external"]
        and config["volumes"]["postgres_data"]["name"] == "backtest-badger-pg17",
        "Expected dedicated external PostgreSQL data volume.",
    )


def templates(native_systemd=False):
    # Fake values only: resolved Compose JSON is kept in memory, never printed.
    env = dict(os.environ)
    env.update(
        POSTGRES_IMAGE="postgres:17@sha256:" + "0" * 64,
        POSTGRES_DB="synthetic",
        POSTGRES_USER="synthetic",
        POSTGRES_PASSWORD="synthetic-validation-only",
    )
    require(
        shutil.which("docker"), "Missing dependency: docker (Compose plugin required)"
    )
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            os.devnull,
            "-f",
            str(HERE / "compose.yaml"),
            "config",
            "--format",
            "json",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    require(result.returncode == 0, "Docker Compose config failed; install Compose.")
    check_compose(json.loads(result.stdout))
    if native_systemd:
        run(
            [
                "systemd-analyze",
                "verify",
                "--man=no",
                *map(str, sorted((HERE / "systemd").glob("backtest-badger-*.*"))),
            ]
        )
    else:
        print(
            "NOT CHECKED: native systemd syntax; "
            "run templates --native-systemd on Linux."
        )
    print(
        "Compose configuration validated using synthetic credentials; nothing started."
    )


def runtime(worker):
    account = pwd.getpwnam("ubuntu")
    private_file(CONFIG / "worker.env", uid=0, gid=account.pw_gid, mode=0o640)
    values = read_environment(CONFIG / "worker.env")
    check_worker_environment(values)
    require(
        all(os.environ.get(key) == value for key, value in values.items()),
        "Process configuration differs from the private worker file.",
    )
    release = CURRENT.resolve(strict=True)
    metadata = json.loads((release / "deployment.json").read_text())
    require(
        release == RELEASES / metadata["git_commit"]
        and Path.cwd().resolve() == release,
        "Incorrect release path or working directory.",
    )
    require(
        metadata["python"] == platform.python_version() == "3.12.15"
        and metadata["machine"] == platform.machine() == "x86_64"
        and platform.system() == "Linux",
        "Unexpected Python/runtime; prepare a reviewed release.",
    )
    for name, digest in metadata["files_sha256"].items():
        require(
            hashlib.sha256((release / name).read_bytes()).hexdigest() == digest,
            f"Deployment input changed: {name}",
        )
    for name, expected in metadata["packages"].items():
        require(version(name) == expected, f"Dependency version changed: {name}")
    require((release / "artifacts").is_symlink(), "Missing persistent artifact link.")
    require(
        (release / "artifacts").resolve(strict=True) == ARTIFACTS,
        "Artifact link targets the wrong directory.",
    )
    for path in (
        ARTIFACTS.parent,
        ARTIFACTS,
        *(ARTIFACTS / p for p in WRITABLE[worker]),
    ):
        info = path.lstat()
        require(
            stat.S_ISDIR(info.st_mode)
            and info.st_uid == account.pw_uid
            and stat.S_IMODE(info.st_mode) == 0o700,
            f"Expected ubuntu-owned private directory: {path}",
        )
    if worker == "collection":
        for name in ("research.csv", "manifest.json"):
            require(
                (ARTIFACTS / "research/stage-2a-v1" / name).is_file(),
                "Missing frozen training inputs; migration is not complete.",
            )
    require(
        (release / "docs/stage-03c-forward-evaluation-protocol.md").is_file(),
        "Missing frozen scoring protocol.",
    )
    print(
        "Private configuration, release, dependencies and persistent paths validated."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    template = sub.add_parser("templates")
    template.add_argument("--native-systemd", action="store_true")
    live = sub.add_parser("runtime")
    live.add_argument("--worker", choices=WRITABLE, required=True)
    sub.add_parser("configuration")
    args = parser.parse_args()
    try:
        if args.command == "templates":
            templates(args.native_systemd)
        elif args.command == "configuration":
            configuration()
        else:
            runtime(args.worker)
    except ValueError as error:
        print(f"Deployment validation failed: {error}", file=sys.stderr)
        return 1
    except (OSError, KeyError, ImportError, subprocess.SubprocessError):
        print(
            "Deployment validation failed: missing/unreadable dependency or metadata; "
            "details suppressed.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

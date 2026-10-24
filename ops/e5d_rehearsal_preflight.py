"""Read-only E.5d preparation; NOT an installed bootstrap or host attestation.

No arguments prints the blocked plan. --preflight is a separate manual action
against ONE future administrator-staged fabricated installation. No run, install,
sign, enrol, consume, probe, cleanup or path/config override interface exists.
"""

import hashlib
import json
import os
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

INSTALL = Path("/Library/Application Support/BacktestBadger/E5dRehearsal/v1")
RUNTIME = INSTALL / "runtime"
REVIEW = INSTALL / "review/runtime-snapshot.json"
ROLES = ("python", "stdlib", "packages", "native", "project", "launcher", "config")
MAX_FILE = 512 << 20
MAX_TOTAL = 4 << 30
MAX_ENTRIES = 50_000
FORBIDDEN = {
    "artifacts",
    "BacktestBadgerEvidence",
    "crypto-trading-platform",
    ".ssh",
    ".aws",
    ".env",
    ".codex",
    "credentials",
    "private-keys",
}
BLOCKERS = (
    "No reviewed installed MAC/network/process policy or two-principal proof.",
    "No fixed executable supervisor/worker bootstrap is enabled.",
    "OS dyld/shared-cache, loaded images, ACLs, mounts and startup trust need review.",
    "A matching file snapshot is reproducibility evidence, not host attestation.",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def metadata(s):
    return [
        s.st_dev,
        s.st_ino,
        s.st_size,
        s.st_mtime_ns,
        s.st_ctime_ns,
        s.st_uid,
        s.st_gid,
        stat.S_IMODE(s.st_mode),
        s.st_nlink,
        getattr(s, "st_flags", 0),
    ]


def protected(s, owner_uid):
    require(
        s.st_uid in (0, owner_uid) and not s.st_mode & 0o022,
        "Unknown owner or writable path; ACLs still require separate review.",
    )


@contextmanager
def protected_directory(path, owner_uid):
    # No resolve(): symlinks, including ancestors, must fail rather than disappear.
    parts = str(path).split("/")
    require(
        parts[0] == "" and all(p not in ("", ".", "..") for p in parts[1:]),
        "Canonical absolute path required.",
    )
    require(not FORBIDDEN.intersection(parts), "Private/original path forbidden.")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        protected(os.fstat(fd), owner_uid)
        for part in parts[1:]:
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            os.close(fd)
            fd = child
            protected(os.fstat(fd), owner_uid)
        yield fd
    finally:
        os.close(fd)


def snapshot_tree(root, *, owner_uid):
    """Deterministic exact files AND directories, streaming hashes, no link follows.

    Only call on deliberately staged runtime code/config, never evidence or home
    directories. This API is an inventory utility, not execution authority. Native
    images not present in this tree and the executing process are NOT attested.
    """
    files, directories, total = {}, {}, 0

    def walk(fd, prefix):
        nonlocal total
        before = os.fstat(fd)
        protected(before, owner_uid)
        directories[prefix] = {
            "uid": before.st_uid,
            "gid": before.st_gid,
            "mode": stat.S_IMODE(before.st_mode),
            "flags": getattr(before, "st_flags", 0),
        }
        names = sorted(os.listdir(fd))
        for name in names:
            require(
                name not in FORBIDDEN and not name.startswith(".env"),
                "Private/original name forbidden before open.",
            )
            relative = prefix + name
            require(len(files) + len(directories) < MAX_ENTRIES, "Inventory bound.")
            item = os.stat(name, dir_fd=fd, follow_symlinks=False)
            protected(item, owner_uid)
            if stat.S_ISDIR(item.st_mode):
                child = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                )
                try:
                    require(
                        metadata(os.fstat(child)) == metadata(item),
                        "Directory changed before open.",
                    )
                    walk(child, relative + "/")
                finally:
                    os.close(child)
            else:
                require(
                    stat.S_ISREG(item.st_mode)
                    and item.st_nlink == 1
                    and item.st_size <= MAX_FILE,
                    "Unaliased regular file required.",
                )
                child = os.open(
                    name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd
                )
                try:
                    require(
                        metadata(os.fstat(child)) == metadata(item),
                        "File changed before open.",
                    )
                    digest, size = hashlib.sha256(), 0
                    while chunk := os.read(child, 1 << 20):
                        size += len(chunk)
                        total += len(chunk)
                        require(
                            size <= MAX_FILE and total <= MAX_TOTAL,
                            "Inventory byte bound.",
                        )
                        digest.update(chunk)
                    require(
                        metadata(item)
                        == metadata(os.fstat(child))
                        == metadata(os.stat(name, dir_fd=fd, follow_symlinks=False))
                        and size == item.st_size,
                        "File changed during inventory.",
                    )
                finally:
                    os.close(child)
                files[relative] = {
                    "sha256": digest.hexdigest(),
                    "bytes": size,
                    "uid": item.st_uid,
                    "gid": item.st_gid,
                    "mode": stat.S_IMODE(item.st_mode),
                    "flags": getattr(item, "st_flags", 0),
                }
            require(
                metadata(item)
                == metadata(os.stat(name, dir_fd=fd, follow_symlinks=False)),
                "Entry changed during inventory.",
            )
        require(
            names == sorted(os.listdir(fd))
            and metadata(before) == metadata(os.fstat(fd)),
            "Directory changed during inventory.",
        )

    with protected_directory(root, owner_uid) as fd:
        walk(fd, "")
    return {
        "schema": "e5d-fabricated-runtime-snapshot-v1",
        "files": files,
        "directories": directories,
    }


def context():
    """Current process facts only; no environment values, private FDs or home scans."""
    host = os.uname()
    return {
        "uid": os.getuid(),
        "euid": os.geteuid(),
        "gid": os.getgid(),
        "egid": os.getegid(),
        "groups": os.getgroups(),
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "system": host.sysname,
        "kernel": host.release,
        "architecture": host.machine,
        "python_version_build": sys.version,
        "executable": sys.executable,
        "isolated": sys.flags.isolated,
        "no_site": sys.flags.no_site,
        "import_paths": list(sys.path),
        "loaded_python_files": sorted(
            {
                str(m.__file__)
                for m in sys.modules.values()
                if getattr(m, "__file__", None)
            }
        ),
        "loaded_native_images": "UNVERIFIED: includes OS-managed dyld shared cache",
        "inherited_fds": "UNVERIFIED: separate administrator-observed rehearsal",
    }


def preflight():
    require(
        sys.platform == "darwin" and sys.version_info[:2] == (3, 12),
        "macOS and CPython 3.12 required; exact patch/build remains review-bound.",
    )
    require(
        sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
        "Invoke using -I -S -B.",
    )
    # Fixed location, no CLI/env or worker-provided expected snapshot. Review is
    # root controlled; this file is never an approval and cannot activate a run.
    with protected_directory(REVIEW.parent, 0) as fd:
        review_fd = os.open(
            REVIEW.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd
        )
        try:
            s = os.fstat(review_fd)
            protected(s, 0)
            require(
                stat.S_ISREG(s.st_mode)
                and s.st_nlink == 1
                and 0 < s.st_size <= 32 << 20,
                "Bounded review file required.",
            )
            with os.fdopen(os.dup(review_fd), "rb") as stream:
                body = stream.read((32 << 20) + 1)
            require(
                metadata(s)
                == metadata(os.fstat(review_fd))
                == metadata(os.stat(REVIEW.name, dir_fd=fd, follow_symlinks=False))
                and len(body) == s.st_size,
                "Review changed.",
            )
        finally:
            os.close(review_fd)
    expected = json.loads(body)
    require(canonical(expected) == body, "Canonical snapshot required.")
    first = snapshot_tree(RUNTIME, owner_uid=0)
    require(
        all(role + "/" in first["directories"] for role in ROLES),
        "Every staged runtime role required; completeness still needs review.",
    )
    require(first == expected, "Missing/extra/changed runtime entries.")
    # Second observation is a preflight race check, NOT atomic consumption or a
    # promise the runtime cannot change afterwards. No consumption exists here.
    require(
        snapshot_tree(RUNTIME, owner_uid=0) == first, "Runtime changed in preflight."
    )
    paths = [
        Path("/"),
        *reversed(INSTALL.parents[:-1]),
        INSTALL,
        RUNTIME,
        REVIEW.parent,
        REVIEW,
    ]
    acl = []
    for path in paths:
        result = subprocess.run(
            ["/bin/ls", "-lde", str(path)],
            check=True,
            capture_output=True,
            text=True,
            cwd="/",
            env={"LC_ALL": "C"},
        )
        acl.append({"path": str(path), "ls_lde": result.stdout})
    return {
        "snapshot_sha256": hashlib.sha256(canonical(first)).hexdigest(),
        "context": context(),
        "ancestor_acl_observations": acl,
        "acl_enforcement_verified": False,
    }


def main():
    if sys.argv[1:] not in ([], ["--preflight"]):
        raise SystemExit(
            "Only print-only default or --preflight; execution unavailable."
        )
    result = {
        "status": "BLOCKED",
        "fabricated_only": True,
        "genuine_execution_authorised": False,
        "blockers": BLOCKERS,
        "fixed_installation": str(INSTALL),
        "manual_preflight": (
            "python3.12 -I -S -B ops/e5d_rehearsal_preflight.py --preflight"
        ),
    }
    if sys.argv[1:]:
        try:
            result["observations"] = preflight()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            result["preflight_refusal"] = type(error).__name__
    print(json.dumps(result, sort_keys=True, indent=2))
    return 2  # Never emit a successful installation/isolation/execution gate.


if __name__ == "__main__":
    raise SystemExit(main())

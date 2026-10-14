"""Private, exclusive D2A inventories and PAX archives; no application writes."""

import hashlib
import json
import os
import stat
import tarfile
from decimal import Decimal
from pathlib import Path, PurePosixPath


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_json(path):
    return json.loads(Path(path).read_bytes())


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def safe_relative(name):
    path = PurePosixPath(name)
    require(
        bool(name)
        and bool(path.parts)
        and not path.is_absolute()
        and str(path) == name
        and not any(p in ("..", ".") for p in path.parts),
        "Unsafe archive/manifest path.",
    )
    return path


def metadata(info):
    return dict(
        size=info.st_size, mtime_ns=info.st_mtime_ns, mode=stat.S_IMODE(info.st_mode)
    )


def inventory(root):
    """Include empty directories, hidden/partial/lock files; never follow links.

    Inaccessible, disappearing and changing entries are retained as issues. Any
    symlink/special file blocks a complete backup rather than silently omitting it.
    Reading may update atime; source bytes, modes and mtime are never written.
    """
    root = Path(root)
    require(
        root.is_dir() and not root.is_symlink(), "Require a real inventory directory."
    )
    entries, issues = {}, []

    def visit(folder):
        for path in sorted(folder.iterdir()):
            name = path.relative_to(root).as_posix()
            try:
                info = path.lstat()
                item = metadata(info)
                if stat.S_ISDIR(info.st_mode):
                    entries[name] = dict(item, kind="directory", size=0)
                    visit(path)
                elif stat.S_ISREG(info.st_mode):
                    # O_NOFOLLOW catches a file replaced by a link during the scan.
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                    with os.fdopen(fd, "rb") as handle:
                        before = os.fstat(handle.fileno())
                        sha = hashlib.file_digest(handle, "sha256").hexdigest()
                        after = os.fstat(handle.fileno())
                    entries[name] = dict(item, kind="file", sha256=sha)
                    if info != before or before != after or path.lstat() != after:
                        # atime is allowed to change when we read: compare below.
                        def key(s):
                            return (
                                s.st_ino,
                                s.st_dev,
                                s.st_size,
                                s.st_mtime_ns,
                                s.st_ctime_ns,
                                s.st_mode,
                            )

                        if (
                            len({key(s) for s in (info, before, after, path.lstat())})
                            != 1
                        ):
                            issues.append(dict(path=name, issue="changed-during-read"))
                else:
                    entries[name] = dict(item, kind="unsupported")
                    issues.append(dict(path=name, issue="symlink-or-special-file"))
            except OSError:
                issues.append(dict(path=name, issue="unreadable-or-disappeared"))

    visit(root)
    return dict(format="badger-files-v1", entries=entries, issues=issues)


def differences(left, right):
    a, b = left["entries"], right["entries"]
    return {
        "missing": sorted(a.keys() - b.keys()),
        "extra": sorted(b.keys() - a.keys()),
        "changed": sorted(k for k in a.keys() & b.keys() if a[k] != b[k]),
        "issues": left.get("issues", []) + right.get("issues", []),
    }


def assert_inventory(expected, actual):
    delta = differences(expected, actual)
    require(not any(delta.values()), "Inventory mismatch; retain both manifests.")


def archive(root, output):
    """A complete independent pass. PAX preserves integer nanosecond mtimes."""
    root = Path(root)
    with tarfile.open(output, "x", format=tarfile.PAX_FORMAT, dereference=True) as tar:

        def add(path):
            name = path.relative_to(root).as_posix()
            info = path.lstat()
            require(
                stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode),
                "Archive refuses links/special files; retain failed backup.",
            )
            member = tarfile.TarInfo(name)
            member.mode = stat.S_IMODE(info.st_mode)
            require(member.mode & ~0o777 == 0, "Unsafe file permissions.")
            member.pax_headers = {"mtime": str(Decimal(info.st_mtime_ns) / 10**9)}
            member.uid, member.gid = info.st_uid, info.st_gid
            if path.is_dir():
                member.type = tarfile.DIRTYPE
                tar.addfile(member)
                for child in sorted(path.iterdir()):
                    add(child)
            else:
                member.size = info.st_size
                with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as h:
                    tar.addfile(member, h)

        for path in sorted(root.iterdir()):
            add(path)


def archive_inventory(path):
    entries = {}
    with tarfile.open(path, "r:") as tar:
        for member in tar:
            name = member.name
            safe_relative(name)
            require(name not in entries, "Duplicate archive path.")
            require(
                member.isfile() or member.isdir(),
                "Archive links/special files refused.",
            )
            require(member.mode & ~0o777 == 0, "Unsafe archive permissions.")
            item = dict(
                kind="file" if member.isfile() else "directory",
                size=member.size if member.isfile() else 0,
                mode=member.mode,
                mtime_ns=int(
                    Decimal(member.pax_headers.get("mtime", str(member.mtime))) * 10**9
                ),
            )
            if member.isfile():
                with tar.extractfile(member) as h:
                    item["sha256"] = hashlib.file_digest(h, "sha256").hexdigest()
            entries[name] = item
    return dict(format="badger-files-v1", entries=entries, issues=[])


def extract(path, target, expected):
    """Only a NEW directory, explicit current-user ownership, no tar extractall."""
    assert_inventory(expected, archive_inventory(path))
    target = Path(target)
    target.mkdir(mode=0o700)  # refuse any existing directory, even empty
    directories = []
    with tarfile.open(path, "r:") as tar:
        for member in tar:
            dest = target / str(safe_relative(member.name))
            dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if member.isdir():
                dest.mkdir(mode=0o700, exist_ok=True)
                directories.append((dest, expected["entries"][member.name]))
            else:
                with dest.open("xb") as out, tar.extractfile(member) as source:
                    while chunk := source.read(1024 * 1024):
                        out.write(chunk)
                apply_metadata(dest, expected["entries"][member.name])
    for dest, item in reversed(directories):
        apply_metadata(dest, item)
    assert_inventory(expected, inventory(target))


def apply_metadata(path, item):
    path.chmod(item["mode"])
    os.utime(path, ns=(item["mtime_ns"], item["mtime_ns"]))


def seal(bundle):
    manifest = inventory(bundle)
    require(not manifest["issues"], "Unstable bundle cannot be sealed.")
    write_json(bundle / "bundle.json", manifest)
    return digest(bundle / "bundle.json")


def verify_bundle(bundle, expected_sha256):
    require(
        digest(bundle / "bundle.json") == expected_sha256,
        "Bundle manifest differs from separately retained SHA-256.",
    )
    expected = read_json(bundle / "bundle.json")
    actual = inventory(bundle)
    actual["entries"].pop("bundle.json", None)
    assert_inventory(expected, actual)
    for stem in ("artifacts", "source"):
        assert_inventory(
            read_json(bundle / f"{stem}.archive.json"),
            archive_inventory(bundle / f"{stem}.tar"),
        )

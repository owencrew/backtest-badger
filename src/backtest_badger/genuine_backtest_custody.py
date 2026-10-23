"""E.5d local custody primitives. No genuine execution entry point is enabled.

Filesystem protection requires a separately installed supervisor principal. Unit
fixtures model that boundary; chmod or a same-UID process is NOT independent custody.
"""

import fcntl
import json
import os
import re
import stat
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from backtest_badger import genuine_backtest_preparation as preparation
from backtest_badger import genuine_minute_signed_approval as signing
from backtest_badger.paper_types import require

DOMAIN = b"BACKTEST_BADGER_ONE_SHOT_HISTORICAL_EXECUTION_V1\n"
ENVELOPE = "stage-04b2e5d-one-shot-owner-signature-v1"
SCHEMA = "stage-04b2e5d-fabricated-supervisor-intent-v1"
INPUT_LIMITS = dict(
    zip(preparation.PIN_NAMES, (4096, 32 << 20, 1 << 20, 1 << 20), strict=True)
)
CLOSURE_ROLES = {"code", "python", "stdlib", "packages", "native", "config", "launcher"}


def run_genuine_historical_operator(**kwargs):
    """Closed before arguments, approval, paths or any private material are read."""
    raise PermissionError(
        "E.5d permits fabricated rehearsal only; genuine route closed."
    )


def identity(body):
    return {"sha256": sha256(body).hexdigest(), "bytes": len(body)}


def canonical(value):
    return signing.canonical_approval_bytes(value)


def fields(value, names):
    require(
        type(value) is dict and value.keys() == set(names), "Closed schema required."
    )


def pin(value):
    fields(value, {"sha256", "bytes"})
    signing._hex(value["sha256"])
    signing._positive(value["bytes"])


def path_parts(path):
    require(type(path) is str and path.startswith("/"), "Absolute path required.")
    parts = path.split("/")[1:]
    require(
        bool(parts) and all(p not in ("", ".", "..") for p in parts),
        "Canonical absolute path required.",
    )
    return parts


def verify_approval(document, *, now, expected, public_key=None):
    """Pure TEST intent verifier. Default anchor is the enrolled owner public key.

    Explicit key substitution is available ONLY for this fabricated schema. No
    genuine schema is accepted. CI/closure completeness are protected reviewer
    declarations, not remote attestations or automatic dependency discovery.
    """
    try:
        require(type(document) is bytes and len(document) <= 1 << 20, "Approval bound.")
        value = json.loads(document)
        require(canonical(value) == document, "Canonical approval required.")
        fields(value, {"schema", "key_id", "payload", "signature"})
        key = signing.TRUSTED_OWNER_PUBLIC_KEY if public_key is None else public_key
        require(value["schema"] == ENVELOPE, "Execution signature schema required.")
        require(value["key_id"] == "sha256:" + sha256(key).hexdigest(), "Wrong signer.")
        signing._hex(value["signature"], 128)
        Ed25519PublicKey.from_public_bytes(key).verify(
            bytes.fromhex(value["signature"]),
            DOMAIN + canonical({k: value[k] for k in ("schema", "key_id", "payload")}),
        )
        p = value["payload"]
        fields(
            p,
            {
                "schema",
                "fabricated_only",
                "attempt_id",
                "not_before",
                "expires_at",
                "maximum_attempts",
                "resume",
                "method",
                "protocol",
                "inputs",
                "output",
                "implementation",
                "custody",
                "limits",
                "publication_schema",
                "output_schema_identity",
            },
        )
        require(p["schema"] == SCHEMA and p["fabricated_only"] is True, "TEST only.")
        require(re.fullmatch(r"[a-z0-9-]{1,80}", p["attempt_id"]), "Attempt ID.")
        require(type(now) is int, "Integer UTC seconds required.")
        require(
            type(p["not_before"]) is int
            and type(p["expires_at"]) is int
            and p["not_before"] <= now < p["expires_at"],
            "Stale approval.",
        )
        require(
            type(p["maximum_attempts"]) is int
            and p["maximum_attempts"] == 1
            and p["resume"] is False,
            "One attempt only.",
        )
        require(
            canonical(p["method"]) == canonical(preparation.METHOD)
            and p["protocol"] == preparation.PROTOCOL,
            "Frozen method required.",
        )
        fields(p["inputs"], INPUT_LIMITS)
        paths = []
        for name, item in p["inputs"].items():
            fields(item, {"path", "identity"})
            path_parts(item["path"])
            pin(item["identity"])
            require(item["identity"]["bytes"] <= INPUT_LIMITS[name], "Input bound.")
            require(
                item["identity"]["sha256"]
                not in {v["sha256"] for v in preparation.HISTORICAL_PINS.values()},
                "Original identities forbidden.",
            )
            paths.append(item["path"])
        require(len(set(paths)) == 4, "Four distinct inputs required.")
        path_parts(p["output"])
        impl = p["implementation"]
        fields(impl, {"commit", "ci", "closure"})
        signing._hex(impl["commit"], 40)
        fields(impl["ci"], {"commit", "run_id", "status", "conclusion"})
        require(
            impl["ci"]["commit"] == impl["commit"]
            and impl["ci"]["status"] == "completed"
            and impl["ci"]["conclusion"] == "success"
            and re.fullmatch(r"[1-9][0-9]*", impl["ci"]["run_id"]),
            "CI binding.",
        )
        pin(impl["closure"])
        fields(p["custody"], {"store", "installation", "supervisor_uid", "worker_uid"})
        path_parts(p["custody"]["store"])
        signing._hex(p["custody"]["installation"])
        for name in ("supervisor_uid", "worker_uid"):
            require(
                type(p["custody"][name]) is int and p["custody"][name] >= 0,
                "Principal IDs required.",
            )
        require(
            p["custody"]["supervisor_uid"] != p["custody"]["worker_uid"],
            "Distinct principals required.",
        )
        fields(p["limits"], {"frame_bytes", "total_output_bytes", "wall_seconds"})
        for limit in p["limits"].values():
            signing._positive(limit)
        require(p["limits"]["frame_bytes"] <= 128 << 20, "Frame ceiling.")
        require(
            p["publication_schema"] == "stage-04b2e5d-fabricated-publication-v1",
            "Unreviewed output schema.",
        )
        pin(p["output_schema_identity"])
        # Protected review is compared byte-for-byte, not supplied by the worker.
        require(canonical(p) == canonical(expected), "Protected review mismatch.")
        return p
    except (ValueError, TypeError, KeyError, RecursionError, InvalidSignature):
        raise ValueError("Invalid execution approval.") from None


@contextmanager
def directory(path):
    """Walk every component by descriptor; never traverse symlinks."""
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path_parts(str(path)):
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def snapshot(s):
    return [
        s.st_dev,
        s.st_ino,
        s.st_size,
        s.st_mtime_ns,
        s.st_ctime_ns,
        s.st_uid,
        stat.S_IMODE(s.st_mode),
        s.st_nlink,
    ]


def read_file(parent, name, maximum):
    require("/" not in name and name not in (".", ".."), "Single component required.")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        before = os.fstat(fd)
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 < before.st_size <= maximum,
            "Bounded unaliased regular file.",
        )
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(fd, min(remaining, 1 << 20))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        body = b"".join(chunks)
        after = os.fstat(fd)
        named = os.stat(name, dir_fd=parent, follow_symlinks=False)
        require(
            snapshot(before) == snapshot(after) == snapshot(named)
            and len(body) == before.st_size <= maximum,
            "Input changed during read.",
        )
        return body, snapshot(before)
    finally:
        os.close(fd)


def read_inputs(approved):
    bodies, retained, inodes = {}, {}, set()
    for name, maximum in INPUT_LIMITS.items():
        item = approved["inputs"][name]
        path = Path(item["path"])
        with directory(path.parent) as parent:
            body, metadata = read_file(parent, path.name, maximum)
        require(identity(body) == item["identity"], "Input pin mismatch.")
        require(tuple(metadata[:2]) not in inodes, "Aliased inputs.")
        inodes.add(tuple(metadata[:2]))
        bodies[name] = body
        retained[name] = {"identity": identity(body), "stat": metadata}
    return bodies, retained


def sync(fd):
    os.fsync(fd)
    # macOS asks the drive to flush caches too. Failure is terminal, never fallback.
    if hasattr(fcntl, "F_FULLFSYNC") and stat.S_ISREG(os.fstat(fd).st_mode):
        fcntl.fcntl(fd, fcntl.F_FULLFSYNC)


def write_once(parent, name, body, fault=lambda _: None):
    """Any exception after exclusive creation leaves a terminal occupied name."""
    fd = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent
    )
    try:
        fault(name + ":created")
        view = memoryview(body)
        while view:
            n = os.write(fd, view)
            require(n > 0, "Short write.")
            view = view[n:]
        fault(name + ":written")
        sync(fd)
        fault(name + ":file_synced")
    finally:
        os.close(fd)
    sync(parent)
    fault(name + ":directory_synced")


def check_private(fd, uid):
    s = os.fstat(fd)
    require(
        s.st_uid == uid and stat.S_IMODE(s.st_mode) == 0o700,
        "Supervisor-only private directory required.",
    )


def verify_closure(inventory, *, supervisor_uid, mocked=False):
    """Verify every byte in an explicitly reviewed exact closure inventory.

    This detects inventory changes, not omitted external runtime dependencies.
    The OS installation review must establish closure completeness, loaded image
    paths (including dyld shared cache), ACLs and immutable ancestor ownership.
    TEST inventories intentionally do not attest the executing host's full runtime.
    """
    fields(inventory, {"roles", "roots"})
    fields(inventory["roles"], CLOSURE_ROLES)
    require(type(inventory["roots"]) is dict and inventory["roots"], "Closure roots.")
    require(
        all(p in inventory["roots"] for p in inventory["roles"].values()),
        "Missing runtime role.",
    )
    for root, expected in inventory["roots"].items():
        path_parts(root)
        require(type(expected) is dict and expected, "Exact closure files required.")
        observed = {}
        with directory(root) as fd:

            def walk(parent, prefix, expected=expected, observed=observed):
                s = os.fstat(parent)
                require(
                    mocked or (s.st_uid == supervisor_uid and not s.st_mode & 0o022),
                    "Worker-writable runtime directory.",
                )
                for name in sorted(os.listdir(parent)):
                    relative = prefix + name
                    item = os.stat(name, dir_fd=parent, follow_symlinks=False)
                    if stat.S_ISDIR(item.st_mode):
                        child = os.open(
                            name,
                            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=parent,
                        )
                        try:
                            walk(child, relative + "/")
                        finally:
                            os.close(child)
                    else:
                        require(relative in expected, "Unreviewed runtime file.")
                        pin(expected[relative])
                        require(
                            mocked
                            or (
                                item.st_uid == supervisor_uid
                                and not item.st_mode & 0o022
                            ),
                            "Worker-writable runtime file.",
                        )
                        body, _ = read_file(parent, name, expected[relative]["bytes"])
                        observed[relative] = identity(body)

            walk(fd, "")
        require(observed == expected, "Runtime closure changed.")
    return identity(canonical(inventory))


def attempt_key(approved):
    return identity(canonical(approved))["sha256"] + "-" + approved["attempt_id"]


def consume(store, approved, *, fault=lambda _: None):
    """Only pre-enrolled slots can be consumed; absence is never unused authority.

    The installer creates installation.json and the exact slot/eligible.json under
    separately protected ownership. Runtime has no enrol/reset/delete operation.
    """
    installation, _ = read_file(store, "installation.json", 4096)
    require(
        installation
        == canonical({"installation": approved["custody"]["installation"]}),
        "Lost or different custody installation.",
    )
    slot = os.open(
        attempt_key(approved),
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        dir_fd=store,
    )
    try:
        check_private(slot, os.getuid())
        eligible, _ = read_file(slot, "eligible.json", 4096)
        require(
            eligible
            == canonical(
                {
                    "approval": identity(canonical(approved)),
                    "attempt_id": approved["attempt_id"],
                }
            ),
            "Unenrolled or damaged attempt.",
        )
        # No read of a worker-supplied 'unspent' flag. O_EXCL arbitrates concurrent
        # processes; even an empty/partial record forbids every subsequent attempt.
        write_once(slot, "consumed.json", eligible, fault)
        return slot
    except BaseException:
        os.close(slot)
        raise

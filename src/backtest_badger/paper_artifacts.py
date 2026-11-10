"""Descriptor-relative access to explicitly selected local evidence directories."""

import os
import socket
import stat
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from backtest_badger.paper_types import digest, require

ARCHIVE_LIMIT = 1024 * 1024


class ArchiveView:
    """Read retained bytes from the read-only view and publish through the broker."""

    def __init__(self, path, endpoint):
        self.path = path
        self.endpoint = endpoint

    def __fspath__(self):
        return os.fspath(self.path)

    def publish(self, name, body):
        require(len(body) <= ARCHIVE_LIMIT, "Oversized archive object.")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(3)
            conn.connect(self.endpoint)
            conn.sendall(name.encode("ascii") + b"\n" + body)
            conn.shutdown(socket.SHUT_WR)
            require(conn.recv(1) == b"1", "Archive publication failed.")
        # Acknowledgement and this independent read must refer to the same vault.
        with directory(self.path) as fd:
            require(
                read_original(fd, name, len(body)) == body, "Archive view mismatch."
            )


@contextmanager
def directory(path):
    path = Path(path).absolute()
    require(".." not in path.parts, "Unsafe evidence root.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open("/", flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def read_original(fd, name, limit):
    require(Path(name).name == name and name not in (".", ".."), "Unsafe filename.")
    file = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        info = os.fstat(file)
        require(
            stat.S_ISREG(info.st_mode) and info.st_size <= limit,
            "Expected bounded regular evidence file.",
        )
        with os.fdopen(file, "rb", closefd=False) as stream:
            body = stream.read(limit + 1)
        require(len(body) == info.st_size, "Incomplete or oversized original.")
        return body
    finally:
        os.close(file)


def retain_body(root, body, fingerprint):
    """Publish once in an existing private directory. Equal bytes are idempotent."""
    digest(fingerprint)
    require(sha256(body).hexdigest() == fingerprint, "Source body hash mismatch.")
    publish_once(root, fingerprint + ".json", body)


def publish_once(root, name, body):
    """Atomically create a private object or verify an identical prior publication."""
    if isinstance(root, ArchiveView):
        return root.publish(name, body)
    require(
        Path(name).name == name and name not in ("", ".", ".."), "Unsafe archive name."
    )
    with directory(root) as fd:
        info = os.fstat(fd)
        require(
            info.st_uid == os.getuid() and not info.st_mode & 0o077,
            "Expected an owner-only archive directory.",
        )
        staging = "." + uuid4().hex + ".partial"
        file = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400, dir_fd=fd)
        try:
            with os.fdopen(file, "wb") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(
                    staging, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False
                )
            except FileExistsError:
                require(read_original(fd, name, len(body)) == body, "Archive conflict.")
            os.fsync(fd)
        finally:
            os.unlink(staging, dir_fd=fd)

"""Local append-only archive publisher, socket-activated under a separate UID."""

import os
import pwd
import re
import socket
import struct
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from backtest_badger.paper_artifacts import (
    ARCHIVE_LIMIT,
    directory,
    publish_once,
    read_original,
)
from backtest_badger.paper_types import require

VAULT = Path("/var/lib/badger-paper-vault/originals")
SOCKET = "/run/badger-paper-archive.sock"


def accept_object(conn, vault):
    with conn.makefile("rb") as stream:
        line = stream.readline(72)
        require(line.endswith(b"\n"), "Invalid archive name.")
        name = line[:-1].decode("ascii")
        body = stream.read(ARCHIVE_LIMIT + 1)
        require(len(body) <= ARCHIVE_LIMIT, "Oversized archive object.")
        if name.endswith(".ref"):
            require(
                str(UUID(name[:-4])) + ".ref" == name, "Invalid reference identity."
            )
            require(re.fullmatch(b"[0-9a-f]{64}", body), "Invalid reference.")
            with directory(vault) as fd:
                original = read_original(fd, body.decode() + ".json", ARCHIVE_LIMIT)
            require(sha256(original).hexdigest().encode() == body, "Unknown object.")
        else:
            require(sha256(body).hexdigest() + ".json" == name, "Invalid content name.")
        publish_once(vault, name, body)
    conn.sendall(b"1")


def main():
    require(
        os.geteuid() == pwd.getpwnam("badger-archive").pw_uid != 0,
        "Expected the archive identity.",
    )
    worker = pwd.getpwnam("badger-paper").pw_uid
    with socket.socket(fileno=3) as listener:
        require(
            listener.family == socket.AF_UNIX and listener.getsockname() == SOCKET,
            "Expected the installed archive socket.",
        )
        while True:
            conn, _ = listener.accept()
            with conn:
                try:
                    conn.settimeout(3)
                    _, uid, _ = struct.unpack(
                        "3i",
                        conn.getsockopt(
                            socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")
                        ),
                    )
                    require(uid == worker, "Wrong archive client.")
                    accept_object(conn, VAULT)
                except (OSError, ValueError):
                    # Closing without an acknowledgement fails the requesting cycle.
                    continue


if __name__ == "__main__":
    main()

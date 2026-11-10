"""Independent chrony observer. Run from reviewed root-owned code and configuration."""

import ipaddress
import json
import math
import os
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

DIRECTORY = Path("/run/badger-paper-clock")
SERVER = Path("/etc/backtest-badger/paper/ntp-source")


def observation(report, approved_ip):
    # chronyc -c tracking includes both hex refid and numeric source address.
    (
        ref,
        address,
        stratum,
        timestamp,
        offset,
        _,
        _,
        _,
        residual,
        skew,
        delay,
        disp,
        _,
        leap,
    ) = report.strip().split(",")
    source = ipaddress.ip_address(address)
    if (
        source != ipaddress.ip_address(approved_ip)
        or source.is_loopback
        or source.is_unspecified
        or source.is_multicast
        or ref in {"00000000", "7F7F0101"}
        or leap != "Normal"
        or not 1 <= int(stratum) <= 15
    ):
        raise ValueError("Untrusted time source")
    offset, residual, skew, delay, disp = map(
        float, (offset, residual, skew, delay, disp)
    )
    if (
        not all(map(math.isfinite, (offset, residual, skew, delay, disp)))
        or min(skew, delay, disp) < 0
    ):
        raise ValueError("Invalid uncertainty")
    # Charge frequency uncertainty across the entire allowed sample lifetime.
    bound = abs(offset) + delay / 2 + disp + 300 * (abs(residual) + skew + 15) / 1e6
    return dict(
        synchronised=True,
        sampled_at=datetime.fromtimestamp(float(timestamp), UTC).isoformat(),
        uncertainty_ms=math.ceil(bound * 1e6) / 1000,
    )


def protected(path):
    for item in (*path.parents, path):
        info = item.lstat()
        if info.st_uid != 0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):
            raise PermissionError("Unsafe observer path")


def main():
    if os.geteuid() != 0:
        raise PermissionError("Requires independent observer identity")
    protected(DIRECTORY)
    dest = DIRECTORY / "observation.json"
    try:
        protected(SERVER)
        report = subprocess.check_output(
            ["/usr/bin/chronyc", "-h", "/run/chrony/chronyd.sock", "-c", "tracking"],
            timeout=2,
            text=True,
            env={"LC_ALL": "C"},
        )
        result = observation(report, SERVER.read_text().strip())
    except (OSError, ValueError, OverflowError, subprocess.SubprocessError):
        dest.unlink(missing_ok=True)
        return 1
    with NamedTemporaryFile(dir=DIRECTORY, delete=False, mode="w") as stream:
        json.dump(result, stream)
        os.fchmod(stream.fileno(), 0o644)
    os.replace(stream.name, dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate a private forward candidate for later approved publication.

Private preparation by default; no database, scoring or model fitting. The optional
R2 upload MUST have separate owner approval before execution. It sends validated
bytes without reserializing or retiming them.
"""

import argparse
import fcntl
import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path

from public_forward_export import check_destination, prepare, write_candidate

WEB = Path(__file__).resolve().parents[1]
MAX_BYTES = 64 * 1024


def deadline(_signum, _frame):
    raise TimeoutError("Snapshot preparation deadline exceeded.")


def stage(records, outcomes, operations, output, node="node", r2_object=None):
    """Keep the previous candidate intact unless both validation layers succeed."""
    check_destination(output, (records, outcomes, operations))
    if r2_object is not None and not re.fullmatch(
        r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]/forward-v1\.json", r2_object
    ):
        raise ValueError("Only an explicit R2 bucket/forward-v1.json is permitted.")
    # Keep this inode; unlinking an advisory lock can allow overlapping writers.
    fd = os.open(output.with_suffix(".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tempfile.TemporaryDirectory(
            prefix=".forward-stage-", dir=output.parent
        ) as d:
            candidate = Path(d) / "candidate.json"
            value = prepare(records, outcomes, operations)
            write_candidate(value, candidate)
            if candidate.stat().st_size > MAX_BYTES:
                raise ValueError("Snapshot exceeds the public size budget.")
            subprocess.run(
                [
                    node,
                    "--import",
                    "tsx",
                    "scripts/validate-forward.ts",
                    str(candidate),
                ],
                cwd=WEB,
                check=True,
                timeout=30,
                capture_output=True,
            )
            # Compare clocks before replacing a previously validated candidate.
            if output.exists():
                import json

                from backtest_badger.forward_evaluation import utc_time

                previous = json.loads(output.read_text())
                if any(
                    utc_time(value[k]) < utc_time(previous[k])
                    for k in ("as_of", "generated_at")
                ):
                    raise ValueError("Snapshot clocks regressed.")
            if r2_object is not None:
                # One object PUT, under the same lock as staging. No bucket creation,
                # directory upload, site deployment or public-access configuration.
                subprocess.run(
                    [
                        "pnpm",
                        "exec",
                        "wrangler",
                        "r2",
                        "object",
                        "put",
                        r2_object,
                        "--remote",
                        "--file",
                        str(candidate),
                        "--content-type",
                        "application/json",
                        "--cache-control",
                        "public, max-age=60, must-revalidate",
                    ],
                    cwd=WEB,
                    check=True,
                    timeout=30,
                    capture_output=True,
                )
            write_candidate(value, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("records", "outcomes", "operations", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--node", default="node")
    parser.add_argument(
        "--publish-r2-object",
        help="EXTERNAL WRITE: requires separate approval; BUCKET/forward-v1.json",
    )
    args = parser.parse_args()
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(120)
    try:
        stage(
            args.records.resolve(),
            args.outcomes.resolve(),
            args.operations.resolve(),
            args.output.resolve(),
            args.node,
            args.publish_r2_object,
        )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        parser.exit(1, "Snapshot preparation/publication failed; inspect privately.\n")
    finally:
        signal.alarm(0)
    print(
        "Validated snapshot uploaded; verify the HTTPS endpoint separately."
        if args.publish_r2_object
        else "Private snapshot passed both validators. No public upload attempted."
    )


if __name__ == "__main__":
    main()

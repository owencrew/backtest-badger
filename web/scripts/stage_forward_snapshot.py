"""Validate a private forward candidate for later approved publication.

Private preparation by default; no database, scoring or model fitting. The optional
R2 upload MUST have separate owner approval before execution. It sends validated
bytes without reserializing or retiming them.
"""

import argparse
import fcntl
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from public_forward_export import check_destination, prepare, write_candidate

WEB = Path(__file__).resolve().parents[1]
MAX_BYTES = 64 * 1024


def deadline(_signum, _frame):
    raise TimeoutError("Snapshot preparation deadline exceeded.")


def stage(
    records,
    outcomes,
    operations,
    output,
    node="node",
    r2_object=None,
    validator=None,
    *,
    schema_version=1,
):
    """Keep the previous candidate intact unless both validation layers succeed."""
    check_destination(output, (records, outcomes, operations))
    if schema_version not in (1, 2):
        raise ValueError("Unsupported snapshot version.")
    if schema_version == 2 and r2_object is not None:
        raise ValueError("V2 is private preparation only; publication needs review.")
    if r2_object not in (None, "backtest-badger-forward/forward-v1.json"):
        raise ValueError("Only the dedicated approved bucket and key are permitted.")
    # Keep this inode; unlinking an advisory lock can allow overlapping writers.
    fd = os.open(output.with_suffix(".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tempfile.TemporaryDirectory(
            prefix=".forward-stage-", dir=output.parent
        ) as d:
            candidate = Path(d) / "candidate.json"
            if schema_version == 2:
                from public_forward_v2 import prepare as prepare_v2

                value = prepare_v2(records, outcomes, operations)
            else:
                value = prepare(records, outcomes, operations)
            write_candidate(value, candidate)
            if candidate.stat().st_size > MAX_BYTES:
                raise ValueError("Snapshot exceeds the public size budget.")
            subprocess.run(
                [node, str(validator), str(candidate)]
                if validator
                else [
                    node,
                    "--import",
                    "tsx",
                    "scripts/validate-forward-v2.ts"
                    if schema_version == 2
                    else "scripts/validate-forward.ts",
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
                if previous["schema_version"] != schema_version:
                    raise ValueError("Use separate candidate paths for each version.")
                if any(
                    utc_time(value[k]) < utc_time(previous[k])
                    for k in ("as_of", "generated_at")
                ):
                    raise ValueError("Snapshot clocks regressed.")
                if schema_version == 2:
                    current = {r["symbol"]: r for r in value["latest_scored"]}
                    for old in previous["latest_scored"]:
                        row = current.get(old["symbol"])
                        if (
                            row is None
                            or utc_time(row["source_close_at"])
                            < utc_time(old["source_close_at"])
                            or (
                                utc_time(row["source_close_at"])
                                == utc_time(old["source_close_at"])
                                and row != old
                            )
                        ):
                            raise ValueError(
                                "Latest scored evidence regressed or changed."
                            )
            if r2_object is not None:
                if {row["symbol"] for row in value["latest"]} != {"BTCUSDT", "ETHUSDT"}:
                    raise ValueError("Publication requires both approved markets.")
                # Preserve the previous approved bytes privately before attempting
                # a PUT: a lost acknowledgement can leave remote success uncertain.
                if output.exists():
                    write_candidate(previous, output.with_name("previous-success.json"))
                subprocess.run(
                    [
                        sys.executable,
                        str(WEB / "scripts/publish_forward_r2.py"),
                        str(candidate),
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
    parser.add_argument("--schema-version", type=int, choices=(1, 2), default=1)
    parser.add_argument("--validator", type=Path, help="Bundled existing TS validator")
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
            args.validator,
            schema_version=args.schema_version,
        )
    except subprocess.CalledProcessError as error:
        phase = (
            "publication_or_readback_failed"
            if any("publish_forward_r2.py" in str(part) for part in error.cmd)
            else "public_contract_rejected"
        )
        parser.exit(1, f"Public feed failure category={phase}; inspect privately.\n")
    except ValueError:
        parser.exit(1, "Public feed failure category=invalid_candidate.\n")
    except (OSError, RuntimeError, subprocess.SubprocessError):
        parser.exit(1, "Public feed failure category=source_lock_or_deadline.\n")
    finally:
        signal.alarm(0)
    print(
        "Validated snapshot uploaded; verify the HTTPS endpoint separately."
        if args.publish_r2_object
        else "Private snapshot passed both validators. No public upload attempted."
    )


if __name__ == "__main__":
    main()

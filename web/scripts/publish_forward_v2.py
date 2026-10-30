"""Prepare retained evidence and publish v2 only; execution needs owner approval.

There is deliberately no CLI accepting an arbitrary candidate JSON file. Genuine
provenance is checked by the frozen evidence loader before the public projection.
A structurally valid JSON file alone cannot prove that predictions are genuine.
"""

import argparse
import fcntl
import hashlib
import json
import os
import signal
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from public_forward_export import check_destination
from publish_forward_r2 import CACHE_CONTROL, MAX_BYTES, client
from stage_forward_snapshot import deadline, stage

DESTINATION = "backtest-badger-forward/forward-v2.json"
STATE_NAME = "last-success-v2.json"


def check_freshness(value, now):
    from backtest_badger.forward_evaluation import utc_time

    if not timedelta(0) <= now - utc_time(value["as_of"]) <= timedelta(minutes=20):
        raise ValueError("Publication cutoff is stale or in the future.")
    boundary = now.replace(hour=now.hour // 4 * 4, minute=0, second=0, microsecond=0)
    required = (
        boundary
        if now >= boundary + timedelta(minutes=16)
        else boundary - timedelta(hours=4)
    )
    if any(utc_time(r["source_close_at"]) < required for r in value["latest"]):
        raise ValueError("Latest forecast issuance is stale.")


def atomic_bytes(path, body):
    """Preserve exact validated bytes, with durable private atomic replacement."""
    fd, name = tempfile.mkstemp(prefix=".forward-v2-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        Path(name).unlink(missing_ok=True)


def check_progress(previous, current):
    """Reject removed coverage, count regression and rewritten issued forecasts."""
    from backtest_badger.forward_evaluation import utc_time

    for old in previous["latest"]:
        row = next((r for r in current["latest"] if r["symbol"] == old["symbol"]), None)
        if row is None or utc_time(row["source_close_at"]) < utc_time(
            old["source_close_at"]
        ):
            raise ValueError("Latest issuance regressed.")
        if utc_time(row["source_close_at"]) == utc_time(old["source_close_at"]):
            immutable = ("issued_at", "target_close_at", "recipe_sha256", "cohort")
            if any(row[k] != old[k] for k in immutable) or any(
                row["models"][m]["predicted_log_return_4h"]
                != old["models"][m]["predicted_log_return_4h"]
                for m in old["models"]
            ):
                raise ValueError("Original prediction changed.")
            if old["status"] == "scored" and row != old:
                raise ValueError("Saved scored observation changed.")
    for old in previous["evaluations"]:
        row = next(
            r
            for r in current["evaluations"]
            if (r["symbol"], r["cohort"]) == (old["symbol"], old["cohort"])
        )
        if any(row[k] < old[k] for k in ("genuine_predictions", "matched_count")):
            raise ValueError("Retained evidence counts regressed.")


def upload_verified(body, s3, destination):
    """Internal transport: caller must prepare/validate under the publisher lock."""
    if destination != DESTINATION:
        raise ValueError("Only the approved v2 destination is permitted.")
    if not 0 < len(body) <= MAX_BYTES:
        raise ValueError("Invalid snapshot size.")
    bucket, key = DESTINATION.split("/")
    acknowledgement = s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
        CacheControl=CACHE_CONTROL,
        StorageClass="STANDARD",
    )
    if acknowledgement.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200:
        raise ValueError("R2 PUT acknowledgement uncertain.")
    response = s3.get_object(Bucket=bucket, Key=key)
    with response["Body"] as stream:
        stored = stream.read(MAX_BYTES + 1)
    digest = hashlib.sha256(body).hexdigest()
    if (
        response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200
        or stored != body
        or hashlib.sha256(stored).hexdigest() != digest
        or response.get("ContentType") != "application/json"
        or response.get("CacheControl") != CACHE_CONTROL
    ):
        raise ValueError("R2 readback mismatch.")
    return digest


def publish(
    records,
    outcomes,
    operations,
    output,
    *,
    node="node",
    validator=None,
    destination=DESTINATION,
):
    if destination != DESTINATION:
        raise ValueError("Only the approved v2 destination is permitted.")
    output = output.resolve()
    if output.name != STATE_NAME or output.is_relative_to(
        Path("/var/lib/backtest-badger-public-feed")
    ):
        raise ValueError("Use isolated v2 state, never the v1 state directory.")
    sources = (records, outcomes, operations)
    check_destination(output, sources)
    fd = os.open(output.with_suffix(".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tempfile.TemporaryDirectory(prefix=".publish-v2-", dir=output.parent) as d:
            candidate = Path(d) / STATE_NAME
            previous = output.read_bytes() if output.exists() else None
            if previous is not None:
                atomic_bytes(candidate, previous)
            # Existing private v2 preparation checks provenance, concurrent source
            # mutation, strict TS schema, clocks and latest-scored regression.
            stage(*sources, candidate, node=node, validator=validator, schema_version=2)
            body = candidate.read_bytes()
            current = json.loads(body)
            if {r["symbol"] for r in current["latest"]} != {"BTCUSDT", "ETHUSDT"}:
                raise ValueError("Publication requires both approved markets.")
            check_freshness(current, datetime.now(UTC))
            if previous is not None:
                check_progress(json.loads(previous), current)
                atomic_bytes(output.with_name("previous-success-v2.json"), previous)
            # No SDK client (or credential lookup) until preparation succeeds.
            digest = upload_verified(body, client(), destination)
            atomic_bytes(output, body)
            return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("records", "outcomes", "operations", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--node", default="node")
    parser.add_argument("--validator", type=Path)
    parser.add_argument("--publish-r2-object", required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(120)
    try:
        digest = publish(
            args.records.resolve(),
            args.outcomes.resolve(),
            args.operations.resolve(),
            args.output,
            node=args.node,
            validator=args.validator,
            destination=args.publish_r2_object,
        )
    except Exception:
        # Neither SDK errors nor private evidence/paths belong in the journal.
        parser.exit(
            1, "V2 publication failed; last-success not advanced; inspect privately.\n"
        )
    finally:
        signal.alarm(0)
    print(
        f"V2 R2 exact-byte readback verified sha256={digest}; check HTTPS separately."
    )


if __name__ == "__main__":
    main()

"""One explicitly requested archive per run; local evidence and atomic backfill."""

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psycopg

from backtest_badger.archives import (
    ArchiveError,
    ArchiveRequest,
    download_archive,
    parse_archive,
)
from backtest_badger.candles import BatchConflict, save_candles
from backtest_badger.db import connect_database


def _write_manifest(path: Path, manifest: dict) -> None:
    temporary = path.with_suffix(".tmp")
    try:
        temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _retain(path: Path, body: bytes) -> None:
    """Content-addressed evidence; never silently replace a different local body."""
    if path.exists():
        if path.read_bytes() != body:
            raise ArchiveError("artifact", "Existing raw artifact has different bytes.")
        return
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        temporary.write_bytes(body)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def ingest_archive(
    request: ArchiveRequest,
    settings=None,
    *,
    dry_run=False,
    allow_source_gaps=False,
    artifacts=Path("artifacts"),
    result=None,
) -> int:
    """Return CLI status; optionally copy the final evidence into result.

    Safe diagnostics exclude raw network/driver exceptions. The range caller uses
    the same manifest counts, never a second implementation of monthly ingestion.
    """
    run_id = uuid4().hex
    manifest_path = artifacts / "manifests" / f"{run_id}.json"
    manifest = {
        "run_id": run_id,
        "parser_version": "stage-1b3-gaps-v2",
        "allow_source_gaps": allow_source_gaps,
        "inspection_complete": False,
        "candle_complete": False,
        "accepted_count": 0,
        "excluded_count": 0,
        "excluded_observations": [],
        "source_missing_intervals": [],
        "coverage_start": request.coverage_start.isoformat(),
        "coverage_end_exclusive": request.bounds[1].isoformat(),
        "listing_boundary_evidence": (
            "docs/stage-01a-market-data-design.md: REST/archive first-open agreement"
            if request.coverage_start != request.bounds[0]
            else None
        ),
        "mode": "backfill",
        "started_at": datetime.now(UTC).isoformat(),
        "source_url": request.url,
        "source_sha256": None,
        "symbol": request.symbol,
        "interval": request.interval,
        "month": request.month,
        "timestamp_unit": "microseconds"
        if request.month >= "2025-01"
        else "milliseconds",
        "observed_at": None,
        "dry_run": dry_run,
        "validation_result": "not_started",
        "expected_count": len(request.grid),
        "actual_count": None,
        "inserted": 0,
        "unchanged": 0,
        "conflicting": 0,
        "stale": 0,
        "rejected": 0,
        "missing_intervals": [],
        "duplicate_intervals": [],
        "conflicting_identities": [],
        "stale_identities": [],
        "database_write_outcome": "not_attempted",
        "error_category": None,
    }
    status = 0
    phase = "artifact"
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        raw = artifacts / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        _write_manifest(manifest_path, manifest)
        print(
            f"Fetching {request.symbol} {request.interval} {request.month} "
            "archive and checksum."
        )
        phase = "download"
        download = download_archive(request)
        manifest.update(
            source_sha256=download.sha256, observed_at=download.observed_at.isoformat()
        )
        phase = "artifact"
        raw_path = raw / f"{download.sha256}.zip"
        # Run-specific evidence preserves the sidecar's exact bytes on each acquisition.
        checksum_path = raw / f"{download.sha256}-{run_id}.CHECKSUM"
        _retain(raw_path, download.body)
        _retain(checksum_path, download.checksum)
        manifest.update(raw_archive=str(raw_path), checksum_artifact=str(checksum_path))
        _write_manifest(manifest_path, manifest)
        phase = "validation"
        manifest["validation_result"] = "in_progress"
        # Placeholder is for validation only; never written. Resolve the real market
        # identity after acquisition/parsing, and rebind every observation below.
        observations = parse_archive(
            request,
            download,
            market_id=1,
            allow_source_gaps=allow_source_gaps,
            diagnostics=manifest,
        )
        manifest.update(
            validation_result="passed"
            if manifest["candle_complete"]
            else "source_gaps",
            rejected=manifest["excluded_count"],
        )
        print(
            f"Checksum verified; eligible={len(observations)}/{len(request.grid)}; "
            f"source missing={len(manifest['source_missing_intervals'])}, "
            f"excluded={manifest['excluded_count']}; "
            f"candle_complete={manifest['candle_complete']}."
        )
        _write_manifest(manifest_path, manifest)
        if dry_run:
            manifest["database_write_outcome"] = "dry_run"
        else:
            phase = "database"
            with connect_database(settings) as connection:
                market = connection.execute(
                    "SELECT market_id FROM market "
                    "WHERE venue=%s AND market_type=%s AND symbol=%s",
                    ("binance", "spot", request.symbol),
                ).fetchone()
                if market is None:
                    raise ArchiveError(
                        "market", "Requested seeded market is absent from the database."
                    )
                observations = [replace(o, market_id=market[0]) for o in observations]
                manifest["database_write_outcome"] = "in_progress"
                _write_manifest(manifest_path, manifest)
                counts = save_candles(connection, observations)
                manifest.update(counts)
                manifest["database_write_outcome"] = "committed"
    except BatchConflict as error:
        status = 1
        manifest.update(
            error_category="backfill_conflict",
            database_write_outcome="rolled_back",
            conflicting=len(error.conflicts),
            stale=len(error.stale),
            conflicting_identities=error.conflicts,
            stale_identities=error.stale,
            rejected=manifest["actual_count"],
        )
        print(str(error))
        for kind, identities in (("Conflict", error.conflicts), ("Stale", error.stale)):
            for identity in identities:
                print(
                    f"{kind}: {request.symbol} {request.interval} "
                    f"{identity['open_time']}"
                )
    except ArchiveError as error:
        status = 1
        manifest.update(error_category=error.category, **error.details)
        if phase == "validation":
            manifest["validation_result"] = "failed"
            manifest["rejected"] = manifest["actual_count"]
        print(f"Ingestion failed [{error.category}]: {error}")
        for key in ("missing_intervals", "duplicate_intervals", "unexpected_intervals"):
            for identity in manifest.get(key, []):
                print(f"{key}: {request.symbol} {request.interval} {identity}")
    except psycopg.Error as error:
        status = 1
        manifest["error_category"] = "database"
        if manifest["database_write_outcome"] == "in_progress":
            # Server-reported errors roll back. A transport loss during COMMIT
            # cannot establish whether the transaction committed.
            confirmed_rollback = bool(
                error.sqlstate
                and (
                    error.sqlstate[:2] in ("22", "23", "40", "42")
                    or error.sqlstate == "P0001"
                )
            )
            manifest["database_write_outcome"] = (
                "rolled_back" if confirmed_rollback else "failed_or_unknown"
            )
            manifest["rejected"] = (
                manifest["actual_count"] if confirmed_rollback else None
            )
        print("Ingestion failed during database access; sensitive details suppressed.")
    except (OSError, ValueError, RuntimeError):
        status = 1
        manifest["error_category"] = "artifact" if phase != "database" else "database"
        if manifest["database_write_outcome"] == "in_progress":
            manifest["database_write_outcome"] = "rolled_back"
            manifest["rejected"] = manifest["actual_count"]
        print(f"Ingestion failed during {phase}; sensitive error details suppressed.")
    manifest["finished_at"] = datetime.now(UTC).isoformat()
    manifest["failed_observations"] = manifest["actual_count"] if status else 0
    if manifest["database_write_outcome"] == "failed_or_unknown":
        manifest["failed_observations"] = None
    if result is not None:
        result.update(manifest, manifest_path=str(manifest_path))
    try:
        _write_manifest(manifest_path, manifest)
    except OSError:
        print(
            "Final manifest could not be saved. "
            f"Database outcome: {manifest['database_write_outcome']}; "
            f"inserted={manifest['inserted']}, unchanged={manifest['unchanged']}. "
            "Inspect the database and prior manifest; repeating backfill is safe."
        )
        return 1
    print(
        f"Outcome: {manifest['database_write_outcome']}; "
        f"inserted={manifest['inserted']}, "
        f"unchanged={manifest['unchanged']}, conflicting={manifest['conflicting']}, "
        f"stale={manifest['stale']}, rejected={manifest['rejected']}. "
        f"Manifest: {manifest_path}"
    )
    return status

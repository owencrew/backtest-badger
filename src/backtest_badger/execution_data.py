"""Frozen native hourly references; bounded acquisition and offline source replay."""

import csv
import io
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from backtest_badger.archives import (
    ArchiveError,
    ArchiveRequest,
    DownloadedArchive,
    download_archive,
    parse_archive,
)
from backtest_badger.frozen import SYMBOLS, utc_time
from backtest_badger.ingestion import _retain, _write_manifest
from backtest_badger.model_data import sha256

START = datetime(2024, 1, 1, tzinfo=UTC)
END = datetime(2025, 1, 1, tzinfo=UTC)
HOUR = timedelta(hours=1)
COLUMNS = (
    "venue",
    "market_type",
    "symbol",
    "interval_seconds",
    "open_time",
    "open",
    "source_url",
    "source_sha256",
    "observed_at",
)


def requests():
    # January for BOTH markets must pass before any remaining month is acquired.
    return [
        ArchiveRequest(symbol, "1h", f"2024-{month:02d}")
        for month in range(1, 13)
        for symbol in SYMBOLS
    ]


def json_bytes(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def csv_bytes(columns, rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def reference_rows(request, download):
    observations = parse_archive(
        request, download, market_id=SYMBOLS.index(request.symbol) + 1
    )
    return [
        dict(
            zip(
                COLUMNS,
                (
                    "binance",
                    "spot",
                    request.symbol,
                    3600,
                    o.open_time.isoformat(),
                    str(o.open),
                    request.url,
                    download.sha256,
                    download.observed_at.isoformat(),
                ),
                strict=True,
            )
        )
        for o in observations
    ]


def source_record(request, download, count):
    return {
        "symbol": request.symbol,
        "interval": "1h",
        "month": request.month,
        "url": request.url,
        "checksum_url": request.url + ".CHECKSUM",
        "sha256": download.sha256,
        "checksum_sha256": sha256(download.checksum),
        "observed_at": download.observed_at.isoformat(),
        "row_count": count,
        "checksum_valid": True,
        "complete": True,
    }


def coverage():
    return {
        "start": START.isoformat(),
        "end_exclusive": END.isoformat(),
        "interval_seconds": 3600,
        "row_counts": {s: 8784 for s in SYMBOLS},
        "missing": 0,
        "rejected": 0,
        "complete": True,
    }


def prepare_execution_data(destination):
    """Reserve a new directory; retain evidence on failure; publish manifest last."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    raw = destination / "raw"
    raw.mkdir()
    sources, rows = [], []
    audit = {"status": "acquiring", "sources": sources}
    try:
        for request in requests():
            print(f"Validating {request.stem} (ZIP and official checksum).", flush=True)
            audit["current_source"] = request.url
            _write_manifest(destination / "acquisition.json", audit)
            download = download_archive(request)
            _retain(raw / (request.stem + ".zip"), download.body)
            _retain(raw / (request.stem + ".zip.CHECKSUM"), download.checksum)
            # Retain acquisition evidence BEFORE parsing, including on anomalies.
            audit["current_download"] = {
                "sha256": download.sha256,
                "observed_at": download.observed_at.isoformat(),
            }
            _write_manifest(destination / "acquisition.json", audit)
            accepted = reference_rows(request, download)
            sources.append(source_record(request, download, len(accepted)))
            rows.extend(accepted)
            print(f"Verified {len(accepted)} complete hourly identities.", flush=True)
        rows.sort(key=lambda r: (r["symbol"], r["open_time"]))
        body = csv_bytes(COLUMNS, rows)
        _retain(destination / "hourly_opens.csv", body)
        audit = {"status": "complete", "sources": sources}
        _write_manifest(destination / "acquisition.json", audit)
        manifest = {
            "artifact_version": "binance-1h-2024-v1",
            "coverage": coverage(),
            "sources": sources,
            "archive_count": len(sources),
            "output_sha256": {
                "hourly_opens.csv": sha256(body),
                "acquisition.json": sha256(
                    (destination / "acquisition.json").read_bytes()
                ),
            },
            "implementation_sha256": {
                name: sha256(Path(__file__).with_name(name).read_bytes())
                for name in ("execution_data.py", "archives.py", "candles.py")
            },
            "policy": "Independent native 1h monthly archives; strict full 2024 grid; "
            "no interpolation, substitution or canonical database writes.",
        }
        _retain(destination / "manifest.json", json_bytes(manifest))
        return manifest
    except (ValueError, OSError) as error:
        audit["status"] = "failed"
        audit["error"] = (
            str(error) if isinstance(error, ValueError) else "File access failed."
        )
        if isinstance(error, ArchiveError):
            audit["category"] = error.category
            audit["details"] = error.details
        _write_manifest(destination / "acquisition.json", audit)
        raise


def load_execution_data(directory):
    """Verify every retained source offline and reproduce the exact reference CSV."""
    manifest_body = (directory / "manifest.json").read_bytes()
    body = (directory / "hourly_opens.csv").read_bytes()
    try:
        manifest = json.loads(manifest_body)
        if not (
            manifest["artifact_version"] == "binance-1h-2024-v1"
            and manifest["coverage"] == coverage()
            and manifest["archive_count"] == 24
            and len(manifest["sources"]) == 24
            and manifest["output_sha256"]["hourly_opens.csv"] == sha256(body)
        ):
            raise ValueError("Execution manifest, coverage or CSV SHA-256 mismatch.")
        audit_body = (directory / "acquisition.json").read_bytes()
        if sha256(audit_body) != manifest["output_sha256"][
            "acquisition.json"
        ] or json.loads(audit_body) != {
            "status": "complete",
            "sources": manifest["sources"],
        }:
            raise ValueError("Execution acquisition evidence mismatch.")
        rows = []
        for request, source in zip(requests(), manifest["sources"], strict=True):
            raw = directory / "raw"
            download = DownloadedArchive(
                (raw / (request.stem + ".zip")).read_bytes(),
                (raw / (request.stem + ".zip.CHECKSUM")).read_bytes(),
                source["sha256"],
                utc_time(source["observed_at"]),
            )
            accepted = reference_rows(request, download)
            if source != source_record(request, download, len(accepted)):
                raise ValueError("Execution source identity or provenance mismatch.")
            rows.extend(accepted)
        rows.sort(key=lambda r: (r["symbol"], r["open_time"]))
        if csv_bytes(COLUMNS, rows) != body:
            raise ValueError(
                "Execution CSV differs from verified native archive prices."
            )
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("Malformed execution metadata.") from error
    # CSV equality above includes exact decimal strings, ordering and identities.
    from decimal import Decimal

    prices = {(r["symbol"], utc_time(r["open_time"])): Decimal(r["open"]) for r in rows}
    return {
        "manifest_sha256": sha256(manifest_body),
        "output_sha256": manifest["output_sha256"],
        "coverage": manifest["coverage"],
        "sources": manifest["sources"],
    }, prices

"""Stored-grid coverage and frozen exact CSVs from one read-only MVCC snapshot."""

import csv
import hashlib
import json
import os
import re
import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from psycopg.pq import TransactionStatus
from psycopg.rows import dict_row

from backtest_badger.archives import FIRST_4H_OPEN
from backtest_badger.history import history_requests

COLUMNS = (
    "venue",
    "market_type",
    "symbol",
    "base_asset",
    "quote_asset",
    "interval_seconds",
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "base_volume",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "version",
    "observed_at",
    "source_kind",
    "source_url",
    "source_sha256",
)


def selections(symbols, interval, start_month, end_month):
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("Select one or more distinct markets.")
    for symbol in symbols:
        history_requests(symbol, interval, start_month, end_month)
    return sorted(symbols)


@contextmanager
def research_snapshot(connection):
    if (
        not connection.autocommit
        or connection.info.transaction_status != TransactionStatus.IDLE
    ):
        raise ValueError("Research reads require an idle autocommit connection.")
    with connection.transaction():
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        connection.execute("SET LOCAL TIME ZONE 'UTC'")
        yield


def import_evidence(artifacts, symbols, start_month, end_month):
    """Local attempt evidence, separate from authoritative stored continuity.

    A later successful commit resolves earlier failed writes for that month.
    Source anomalies remain visible independently of a successful partial commit.
    Dry runs cannot resolve imports. Missing manifests cannot prove acquisition.
    """
    attempts = {symbol: [] for symbol in symbols}
    unreadable = []
    for path in sorted((artifacts / "manifests").glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(item, dict):
                raise ValueError
            symbol = item.get("symbol")
            if (
                symbol in attempts
                and item.get("interval") == "4h"
                and start_month <= item.get("month", "") <= end_month
            ):
                item["manifest"] = str(path)
                attempts[symbol].append(item)
        except (OSError, ValueError, TypeError):
            unreadable.append(str(path))
    result = {}
    for symbol, all_items in attempts.items():
        items = [i for i in all_items if not i.get("dry_run")]
        latest = {}
        for item in sorted(
            items, key=lambda i: (i.get("started_at", ""), i.get("run_id", ""))
        ):
            latest[item["month"]] = item
        unresolved = [
            {
                "month": month,
                "manifest": item["manifest"],
                "outcome": item.get("database_write_outcome"),
                "error_category": item.get("error_category"),
                "invalid_row": item.get("invalid_row"),
                "invalid_reason": item.get("invalid_reason"),
                "source_sha256": item.get("source_sha256"),
            }
            for month, item in sorted(latest.items())
            if item.get("database_write_outcome") != "committed"
        ]
        unavailable = sorted(
            month for month, i in latest.items() if i.get("http_status") == 404
        )
        inspected = {}
        for item in sorted(
            items, key=lambda i: (i.get("started_at", ""), i.get("run_id", ""))
        ):
            if (
                item.get("inspection_complete")
                or item.get("validation_result") == "passed"
            ):
                inspected[item["month"]] = item
        diagnostics = [
            {
                "month": month,
                "manifest": item["manifest"],
                "source_url": item.get("source_url"),
                "source_sha256": item.get("source_sha256"),
                "raw_archive": item.get("raw_archive"),
                "observed_at": item.get("observed_at"),
                "source_missing_intervals": item.get("source_missing_intervals", []),
                "missing_intervals": item.get("missing_intervals", []),
                "excluded_observations": item.get("excluded_observations", []),
                "candle_complete": item.get("candle_complete", False),
            }
            for month, item in sorted(inspected.items())
            if item.get("missing_intervals") or item.get("excluded_observations")
        ]
        result[symbol] = {
            "months_not_attempted": [
                r.month
                for r in history_requests(symbol, "4h", start_month, end_month)
                if r.month not in {i["month"] for i in all_items}
            ],
            "successfully_inspected_months": sorted(inspected),
            "successfully_inspected_month_count": len(inspected),
            "source_diagnostics": diagnostics,
            "known_source_missing_count": sum(
                len(i["source_missing_intervals"]) for i in diagnostics
            ),
            "excluded_provider_observation_count": sum(
                len(i["excluded_observations"]) for i in diagnostics
            ),
            "months_without_import_evidence": [
                r.month
                for r in history_requests(symbol, "4h", start_month, end_month)
                if r.month not in latest
            ],
            "successful_archive_month_count": sum(
                i.get("database_write_outcome") == "committed" for i in latest.values()
            ),
            "unavailable_archive_month_count": len(unavailable),
            "successful_import_attempts": sum(
                i.get("database_write_outcome") == "committed" for i in items
            ),
            "failed_or_unresolved_attempts": sum(
                i.get("database_write_outcome") != "committed" for i in items
            ),
            "unavailable_archive_months": unavailable,
            "failed_or_unresolved_imports": unresolved,
        }
    return result, unreadable


def _coverage(connection, symbols, start_month, end_month, artifacts):
    # Caller owns a snapshot shared with every export query.
    requests = list(history_requests(symbols[0], "4h", start_month, end_month))
    start, end = requests[0].coverage_start, requests[-1].bounds[1]
    evidence, unreadable = import_evidence(artifacts, symbols, start_month, end_month)
    report = {
        "interval_seconds": 14400,
        "start": start.isoformat(),
        "end_exclusive": end.isoformat(),
        "requested_start_month": start_month,
        "requested_end_month": end_month,
        "verified_source_first_open": FIRST_4H_OPEN.isoformat(),
        "boundary_evidence": "docs/stage-01a-market-data-design.md (archive and REST)",
        "outside_declared_range": "unverified; no claim of earlier trading absence",
        "research_window_policy": "Reject or explicitly handle windows crossing "
        "missing intervals or provider anomalies. Adjacent stored rows need not be "
        "consecutive periods; normal native boundaries do not prove uninterrupted "
        "trading within an interval.",
        "unreadable_manifests": unreadable,
        "markets": {},
    }
    with connection.cursor(row_factory=dict_row) as cursor:
        for symbol in symbols:
            cursor.execute(
                "SELECT market_id FROM market WHERE venue='binance' "
                "AND market_type='spot' AND symbol=%s",
                (symbol,),
            )
            market = cursor.fetchone()
            if market is None:
                raise ValueError("Selected seeded market is absent from the database.")
            params = (market["market_id"], start, end)
            cursor.execute(
                """SELECT count(*) AS actual_count, min(open_time) AS first_observed,
                max(open_time) AS last_observed,
                count(*) - count(DISTINCT open_time) AS duplicate_identity_count,
                count(*) AS current_versions,
                count(*) FILTER (WHERE version > 1) AS revised_current_candles
                FROM candle WHERE market_id=%s AND interval_seconds=14400
                AND open_time >= %s AND open_time < %s""",
                params,
            )
            item = cursor.fetchone()
            for name in ("first_observed", "last_observed"):
                if item[name] is not None:
                    item[name] = item[name].isoformat()
            cursor.execute(
                """SELECT count(*) AS revisions FROM candle_revision
                WHERE market_id=%s AND interval_seconds=14400
                AND open_time >= %s AND open_time < %s""",
                params,
            )
            item["historical_revisions"] = cursor.fetchone()["revisions"]
            cursor.execute(
                """SELECT g.t FROM generate_series(
                    %s::timestamptz, %s::timestamptz - interval '4 hours',
                    interval '4 hours') AS g(t)
                WHERE NOT EXISTS (SELECT 1 FROM candle c WHERE c.market_id=%s
                    AND c.interval_seconds=14400 AND c.open_time=g.t)
                ORDER BY g.t""",
                (start, end, market["market_id"]),
            )
            item["missing_intervals"] = [row["t"].isoformat() for row in cursor]
            item["missing_count"] = len(item["missing_intervals"])
            item["expected_count"] = sum(len(r.grid) for r in requests)
            # Don't hide rows before the verified August boundary if present.
            cursor.execute(
                "SELECT count(*) AS n FROM candle WHERE market_id=%s "
                "AND interval_seconds=14400 AND open_time >= %s AND open_time < %s",
                (market["market_id"], requests[0].bounds[0], start),
            )
            item["unexpected_before_boundary"] = cursor.fetchone()["n"]
            item.update(evidence[symbol])
            item["complete"] = not (
                item["missing_count"]
                or item["duplicate_identity_count"]
                or item["unexpected_before_boundary"]
                or item["failed_or_unresolved_imports"]
                or item["source_diagnostics"]
                or unreadable
            )
            report["markets"][symbol] = item
    report["complete"] = all(i["complete"] for i in report["markets"].values())
    report["status"] = "complete" if report["complete"] else "incomplete"
    return report


def coverage_report(
    connection,
    symbols,
    interval,
    start_month,
    end_month,
    *,
    artifacts=Path("artifacts"),
):
    symbols = selections(symbols, interval, start_month, end_month)
    with research_snapshot(connection):
        return _coverage(connection, symbols, start_month, end_month, artifacts)


def _implementation():
    root = Path(__file__).resolve().parents[2]
    info = {}
    try:
        for key, args in (
            ("git_commit", ["rev-parse", "HEAD"]),
            ("git_status", ["status", "--porcelain"]),
        ):
            result = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            info[key] = result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        info["git_revision_unavailable"] = True
    info["module_sha256"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(__file__).parent.glob("*.py"))
    }
    return info


def _cell(value):
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def export_dataset(
    connection,
    symbols,
    interval,
    start_month,
    end_month,
    dataset_id,
    *,
    allow_incomplete=False,
    artifacts=Path("artifacts"),
):
    """Retain bytes plus a manifest; reserve a new directory without overwriting.

    A failed write leaves an explicit .partial file/directory for inspection.
    Only a final manifest denotes a finished export. No provider I/O occurs.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", dataset_id):
        raise ValueError(
            "Dataset ID must be 1-100 letters, digits, hyphens or underscores."
        )
    symbols = selections(symbols, interval, start_month, end_month)
    directory = artifacts / "exports" / dataset_id
    with research_snapshot(connection):
        report = _coverage(connection, symbols, start_month, end_month, artifacts)
        if not report["complete"] and not allow_incomplete:
            raise ValueError(
                "Coverage is incomplete. Run coverage-report for gaps; "
                "--allow-incomplete explicitly acknowledges a partial export."
            )
        directory.parent.mkdir(parents=True, exist_ok=True)
        directory.mkdir()  # Exclusive reservation also prevents concurrent overwrite.
        partial = directory / "candles.csv.partial"
        row_counts = dict.fromkeys(symbols, 0)
        with partial.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(COLUMNS)
            with connection.cursor(
                name="research_export", row_factory=dict_row
            ) as cursor:
                cursor.itersize = 1000
                cursor.execute(
                    """SELECT m.venue, m.market_type, m.symbol, m.base_asset,
                    m.quote_asset, c.* FROM candle c JOIN market m USING (market_id)
                    WHERE m.venue='binance' AND m.market_type='spot'
                    AND m.symbol=ANY(%s) AND c.interval_seconds=14400
                    AND c.open_time >= %s AND c.open_time < %s
                    ORDER BY m.symbol COLLATE "C", c.open_time""",
                    (
                        symbols,
                        datetime.fromisoformat(report["start"]),
                        datetime.fromisoformat(report["end_exclusive"]),
                    ),
                )
                for row in cursor:
                    writer.writerow([_cell(row[name]) for name in COLUMNS])
                    row_counts[row["symbol"]] += 1
            handle.flush()
            os.fsync(handle.fileno())
        if row_counts != {s: report["markets"][s]["actual_count"] for s in symbols}:
            raise RuntimeError("Snapshot row counts disagree with coverage.")
    with partial.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    manifest = {
        "dataset_id": dataset_id,
        "created_at": datetime.now(UTC).isoformat(),
        "export_schema_version": 1,
        "symbols": symbols,
        "interval": interval,
        "start": report["start"],
        "end_exclusive": report["end_exclusive"],
        "row_counts": row_counts,
        "coverage": report,
        "status": report["status"],
        "incomplete_acknowledged": allow_incomplete,
        "selection_policy": "Current accepted canonical versions in one read-only "
        "REPEATABLE READ snapshot; original observation provenance. "
        "Not point-in-time historical provider availability.",
        "dataset_file": "candles.csv",
        "sha256": digest,
        "implementation": _implementation(),
    }
    manifest_partial = directory / "manifest.json.partial"
    with manifest_partial.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    partial.rename(directory / "candles.csv")
    manifest_partial.rename(directory / "manifest.json")
    return manifest

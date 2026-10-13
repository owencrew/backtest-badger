"""Recent REST sync: fixed grids, retained evidence and atomic page writes."""

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
from uuid import uuid4

import psycopg

from backtest_badger.candles import (
    ECONOMIC_FIELDS,
    PRICES,
    BatchConflict,
    get_candles,
    save_candles,
)
from backtest_badger.db import connect_database
from backtest_badger.ingestion import _retain, _write_manifest
from backtest_badger.research import research_snapshot
from backtest_badger.rest import (
    BASE,
    STEP,
    RestError,
    check_clock,
    eligible_end,
    fetch,
    kline_url,
    parse_page,
    sync_start,
)


def _json(value):
    """Exact Decimal strings and aware timestamps in existing JSON manifests."""

    def cell(item):
        if isinstance(item, datetime):
            return item.isoformat()
        if isinstance(item, Decimal):
            return str(item)
        raise TypeError

    return json.loads(json.dumps(value, default=cell))


def _latest(connection, market_id):
    return connection.execute(
        "SELECT max(open_time) FROM candle WHERE market_id=%s "
        "AND interval_seconds=14400",
        (market_id,),
    ).fetchone()[0]


def recent_coverage(connection, market_id, start, end):
    with research_snapshot(connection):
        latest = _latest(connection, market_id)
        missing = connection.execute(
            """SELECT t FROM generate_series(%s::timestamptz,
                %s::timestamptz - interval '4 hours', interval '4 hours') AS g(t)
            WHERE NOT EXISTS (SELECT 1 FROM candle WHERE market_id=%s
                AND interval_seconds=14400 AND open_time=t) ORDER BY t""",
            (start, end, market_id),
        ).fetchall()
    return dict(
        latest_stored_open=latest,
        missing_intervals=[r[0] for r in missing],
        expected_count=(end - start) // STEP,
        missing_count=len(missing),
        stored_complete=not missing,
        freshness="fresh"
        if latest == end - STEP
        else "ahead_of_cutoff"
        if latest and latest > end - STEP
        else "stale",
    )


def _warnings(differences):
    warnings = []
    if len(differences) >= 5:
        warnings.append("Widespread disagreement: at least five changed identities.")
    for difference in differences:
        old, new = difference["old"], difference["new"]
        if old["source_kind"] == "archive":
            warnings.append(f"Archive/REST disagreement at {new['open_time']}.")
        if any(abs(new[p] - old[p]) >= old[p] * Decimal("0.05") for p in PRICES):
            warnings.append(f"Price revision of at least 5% at {new['open_time']}.")
    return warnings


def sync_recent(
    symbol,
    settings,
    *,
    start=None,
    settling_seconds=60,
    dry_run=False,
    artifacts=Path("artifacts"),
    result=None,
):
    """Run synchronously; each HTTP call happens on an idle DB connection.

    Dry runs read the database to plan and reconcile coverage, but never invoke a
    writer. Their comparisons are advisory; real comparisons use locked rows.
    """
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise ValueError("Symbol must be BTCUSDT or ETHUSDT.")
    run_time = datetime.now(UTC)
    end = eligible_end(run_time, settling_seconds)
    refresh_start = end - timedelta(days=7)
    run_id = uuid4().hex
    path = artifacts / "rest" / "manifests" / f"{run_id}.json"
    manifest = dict(
        run_id=run_id,
        parser_version="stage-1c1-v1",
        symbol=symbol,
        interval="4h",
        fixed_run_time=run_time,
        dry_run=dry_run,
        end_exclusive=end,
        latest_eligible_open=end - STEP,
        settling_seconds=settling_seconds,
        refresh_start=refresh_start,
        inserted=0,
        unchanged=0,
        revised=0,
        stale=0,
        conflicting=0,
        pages=[],
        status="in_progress",
        failed_pages=0,
        coverage=None,
        error_category=None,
    )
    received = set()
    page = None
    phase = "artifact"
    status = 0

    def publish():
        _write_manifest(path, _json(manifest))

    def acquire(url, item):
        item.update(
            request_url=url,
            parameters=dict(parse_qsl(urlsplit(url).query)),
            request_headers={"User-Agent": "backtest-badger/0.1"},
            timestamp_unit="milliseconds",
            attempts=[],
            responses=[],
        )
        publish()

        def retain(response):
            raw = artifacts / "rest" / "raw" / f"{response.sha256}.json"
            raw.parent.mkdir(parents=True, exist_ok=True)
            _retain(raw, response.body)
            item["responses"].append(
                dict(
                    actual_url=response.url,
                    observed_at=response.observed_at,
                    sha256=response.sha256,
                    raw_body=str(raw),
                    status=response.status,
                    headers=response.headers,
                    complete=response.complete,
                )
            )
            publish()

        response = fetch(url, retain=retain, attempts=item["attempts"])
        publish()
        print(f"Received HTTP {response.status}; rate diagnostics: {response.headers}")
        return response

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        publish()
        phase = "database"
        with connect_database(settings) as connection:
            market = connection.execute(
                "SELECT market_id FROM market WHERE venue='binance' "
                "AND market_type='spot' AND symbol=%s",
                (symbol,),
            ).fetchone()
            if market is None:
                raise ValueError("Selected seeded market is absent.")
            market_id = market[0]
            phase = "planning"
            start = sync_start(end, _latest(connection, market_id), start)
            manifest["start"] = start
            manifest["market_id"] = market_id
            manifest["coverage_before"] = recent_coverage(
                connection, market_id, start, end
            )
            print(
                f"{symbol}: fixed run={run_time.isoformat()}; "
                f"range=[{start.isoformat()}, {end.isoformat()}); "
                f"revision authority starts {refresh_start.isoformat()}."
            )
            try:
                phase = "clock"
                manifest["clock_check"] = {}
                clock_started = datetime.now(UTC)
                clock = acquire(BASE + "time", manifest["clock_check"])
                manifest["clock_check"]["server_time"] = check_clock(
                    clock, clock_started
                )
                cursor = start
                while cursor < end:
                    if len(manifest["pages"]) == 16:
                        page = None
                        raise RestError(
                            "page_limit", "Stopped at the 16-page run bound."
                        )
                    page = dict(
                        start=cursor,
                        end_exclusive=end,
                        accepted_identities=[],
                        rejected_identities=[],
                        differences=[],
                        database_write_outcome="not_attempted",
                    )
                    manifest["pages"].append(page)
                    phase = "download"
                    response = acquire(kline_url(symbol, cursor, end), page)
                    phase = "validation"
                    observations = parse_page(
                        response, market_id=market_id, start=cursor, end=end
                    )
                    identities = [o.open_time for o in observations]
                    page["accepted_identities"] = identities
                    received.update(identities)
                    # Exact last returned opening time, never page size or local time.
                    next_open = observations[-1].open_time + STEP
                    expected = {
                        cursor + i * STEP for i in range((next_open - cursor) // STEP)
                    }
                    page["source_missing_intervals"] = sorted(
                        expected - set(identities)
                    )
                    publish()
                    phase = "database"
                    if dry_run:
                        old = {
                            r["open_time"]: r
                            for r in get_candles(
                                connection, market_id, 14400, cursor, next_open
                            )
                        }
                        for observation in observations:
                            prior = old.get(observation.open_time)
                            if prior and any(
                                prior[k] != getattr(observation, k)
                                for k in ECONOMIC_FIELDS
                            ):
                                page["differences"].append(
                                    dict(old=prior, new=asdict(observation))
                                )
                        page["database_write_outcome"] = "dry_run"
                    else:
                        page["database_write_outcome"] = "in_progress"
                        publish()
                        counts = save_candles(
                            connection,
                            observations,
                            mode="recent-refresh",
                            refresh_start=refresh_start,
                            refresh_end=end,
                            differences=page["differences"],
                        )
                        page["counts"] = counts
                        page["database_write_outcome"] = "committed"
                        for key, count in counts.items():
                            manifest[key] += count
                    page["warnings"] = _warnings(page["differences"])
                    for warning in page["warnings"]:
                        print(
                            f"WARNING: {warning} "
                            "Old/new values and sources are in the manifest."
                        )
                    publish()
                    print(
                        f"Page {len(manifest['pages'])}: "
                        f"validated={len(observations)}, "
                        f"source gaps={len(page['source_missing_intervals'])}, "
                        f"outcome={page['database_write_outcome']}."
                    )
                    cursor = next_open
            finally:
                # Read stored coverage even after a rejected or partially committed run.
                try:
                    manifest["coverage"] = recent_coverage(
                        connection, market_id, start, end
                    )
                except psycopg.Error:
                    manifest["coverage_error"] = "database"
                    status = 1
    except BatchConflict as error:
        status = 1
        manifest.update(
            error_category="observation_conflict",
            conflicting=len(error.conflicts),
            stale=len(error.stale),
        )
        page.update(
            database_write_outcome="rolled_back",
            conflicting_identities=error.conflicts,
            stale_identities=error.stale,
            rejected_identities=page["accepted_identities"],
        )
        print(
            f"Page rolled back: conflicting={len(error.conflicts)}, "
            f"stale={len(error.stale)}."
        )
    except RestError as error:
        status = 1
        manifest.update(error_category=error.category, error_details=error.details)
        if page is not None:
            page.update(error_category=error.category, error_details=error.details)
            page["rejected_identities"] = error.details.get("rejected_identities", [])
        print(f"Sync failed [{error.category}]: {error}")
    except ValueError as error:
        status = 1
        manifest.update(error_category=phase, error_message=str(error))
        if page and page["database_write_outcome"] == "in_progress":
            page["database_write_outcome"] = "rolled_back"
        print(f"Sync failed during {phase}: {error}")
    except (psycopg.Error, OSError, RuntimeError):
        status = 1
        manifest["error_category"] = phase
        if page and page["database_write_outcome"] == "in_progress":
            page["database_write_outcome"] = "failed_or_unknown"
        print(f"Sync failed during {phase}; sensitive details suppressed.")
    if "start" in manifest:
        expected = {start + i * STEP for i in range((end - start) // STEP)}
        manifest["unresolved_response_intervals"] = sorted(expected - received)
        manifest["source_missing_intervals"] = sorted(
            {
                t
                for p in manifest["pages"]
                for t in p.get("source_missing_intervals", [])
            }
        )
        manifest["source_complete"] = not manifest["unresolved_response_intervals"]
        if not manifest["source_complete"]:
            status = 1
        if not dry_run and (
            not manifest["coverage"] or not manifest["coverage"]["stored_complete"]
        ):
            status = 1
    manifest["failed_pages"] = int(
        bool(manifest["error_category"]) and page is not None
    )
    manifest["incomplete_pages"] = sum(
        bool(p.get("source_missing_intervals")) for p in manifest["pages"]
    )
    manifest["status"] = (
        "failed_or_partial" if status else "dry_run_passed" if dry_run else "complete"
    )
    manifest["finished_at"] = datetime.now(UTC)
    try:
        publish()
    except OSError:
        status = 1
        manifest["status"] = "failed_or_partial"
        print("Final manifest write failed; inspect stored data and earlier manifest.")
    summary = _json(
        {
            k: v
            for k, v in manifest.items()
            if k not in ("pages", "clock_check", "coverage_before")
        }
    )
    print(json.dumps(summary, indent=2))
    print(f"Manifest: {path}")
    if result is not None:
        result.update(_json(manifest), manifest_path=str(path))
    return status

"""Explicit chronological 4h backfills, reusing the single-month importer."""

from pathlib import Path

from backtest_badger.archives import ArchiveRequest
from backtest_badger.ingestion import ingest_archive


def history_requests(symbol, interval, start_month, end_month):
    """Validate both boundaries before any I/O; return a bounded month iterator."""
    if interval != "4h":
        raise ValueError("Historical ranges support native 4h only.")
    first = ArchiveRequest(symbol, interval, start_month)
    last = ArchiveRequest(symbol, interval, end_month)
    if start_month < "2017-08" or first.bounds[0] > last.bounds[0]:
        raise ValueError("Range must start at/after 2017-08 and end at/after start.")

    def months():
        request = first
        while True:
            yield request
            if request.month == end_month:
                break
            request = ArchiveRequest(
                symbol, interval, request.bounds[1].strftime("%Y-%m")
            )

    return months()


def backfill_history(
    symbol,
    interval,
    start_month,
    end_month,
    settings=None,
    *,
    dry_run=False,
    allow_source_gaps=False,
    artifacts=Path("artifacts"),
):
    totals = dict.fromkeys(("inserted", "unchanged", "conflicting", "stale"), 0)
    succeeded = 0
    incomplete = missing = excluded = 0
    for request in history_requests(symbol, interval, start_month, end_month):
        result = {}
        status = ingest_archive(
            request,
            settings,
            dry_run=dry_run,
            allow_source_gaps=allow_source_gaps,
            artifacts=artifacts,
            result=result,
        )
        for key in totals:
            totals[key] += result.get(key, 0)
        if status:
            print(
                f"Backfill stopped at {request.month}: successful_months={succeeded}, "
                f"failed_months=1; totals={totals}; "
                f"failed_observations={result.get('failed_observations')}. "
                "Unknown counts are null; remaining months were not attempted. "
                "Inspect the manifest, then retry the same explicit range safely."
            )
            return 1
        succeeded += 1
        incomplete += result.get("validation_result") == "source_gaps"
        missing += len(result.get("source_missing_intervals", []))
        excluded += result.get("excluded_count", 0)
    print(
        f"Backfill finished: successful_months={succeeded}, failed_months=0; "
        f"months_with_source_gaps={incomplete}; source_missing_intervals={missing}; "
        f"excluded_observations={excluded}; "
        f"totals={totals}; failed_observations=0. "
        "Acquisition success does not establish continuous candle coverage."
    )
    return 0

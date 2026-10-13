"""Health checks and explicitly bounded archive ingestion."""

import argparse
import json
import logging

import psycopg

from backtest_badger.archives import ArchiveRequest
from backtest_badger.config import load_settings
from backtest_badger.db import check_database, connect_database
from backtest_badger.history import backfill_history, history_requests
from backtest_badger.ingestion import ingest_archive
from backtest_badger.research import coverage_report, export_dataset, selections

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="badger", description="A little badger. A lot of backtests."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("health", help="Validate application configuration")
    commands.add_parser("db-health", help="Check PostgreSQL connectivity")
    archive = commands.add_parser(
        "ingest-archive", help="Validate and backfill one monthly archive"
    )
    archive.add_argument("--symbol", required=True, choices=("BTCUSDT", "ETHUSDT"))
    archive.add_argument("--interval", required=True, choices=("1h", "4h"))
    archive.add_argument("--month", required=True)
    archive.add_argument("--dry-run", action="store_true")
    for name in ("backfill-history", "coverage-report", "export-dataset"):
        command = commands.add_parser(name)
        command.add_argument(
            "--symbol",
            required=True,
            choices=("BTCUSDT", "ETHUSDT"),
            **({"nargs": "+"} if name != "backfill-history" else {}),
        )
        command.add_argument("--interval", required=True, choices=("4h",))
        command.add_argument("--start-month", required=True)
        command.add_argument("--end-month", required=True)
        if name == "backfill-history":
            command.add_argument("--dry-run", action="store_true")
            command.add_argument(
                "--allow-source-gaps",
                action="store_true",
                help="Import valid rows and retain source-gap diagnostics",
            )
        if name == "export-dataset":
            command.add_argument("--dataset-id", required=True)
            command.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    if args.command == "ingest-archive":
        try:
            request = ArchiveRequest(args.symbol, args.interval, args.month)
        except ValueError as error:
            parser.error(str(error))
        if args.dry_run:
            return ingest_archive(request, dry_run=True)

    if args.command in ("backfill-history", "coverage-report", "export-dataset"):
        try:
            if args.command == "backfill-history":
                history_requests(
                    args.symbol, args.interval, args.start_month, args.end_month
                )
            else:
                selections(args.symbol, args.interval, args.start_month, args.end_month)
        except ValueError as error:
            parser.error(str(error))
        if args.command == "backfill-history" and args.dry_run:
            return backfill_history(
                args.symbol,
                args.interval,
                args.start_month,
                args.end_month,
                dry_run=True,
                allow_source_gaps=args.allow_source_gaps,
            )

    try:
        settings = load_settings()
    except ValueError as error:
        logger.error("Configuration error: %s", error)
        return 2

    logging.getLogger().setLevel(settings.log_level)
    if args.command == "ingest-archive":
        return ingest_archive(request, settings)
    if args.command == "backfill-history":
        return backfill_history(
            args.symbol,
            args.interval,
            args.start_month,
            args.end_month,
            settings,
            allow_source_gaps=args.allow_source_gaps,
        )
    if args.command in ("coverage-report", "export-dataset"):
        try:
            with connect_database(settings) as connection:
                selection = (
                    connection,
                    args.symbol,
                    args.interval,
                    args.start_month,
                    args.end_month,
                )
                if args.command == "coverage-report":
                    report = coverage_report(*selection)
                    print(json.dumps(report, indent=2))
                    return 0 if report["complete"] else 1
                report = export_dataset(
                    *selection, args.dataset_id, allow_incomplete=args.allow_incomplete
                )
                print(f"Export: artifacts/exports/{args.dataset_id}/manifest.json")
                print(
                    f"Status: {report['status']}; rows={report['row_counts']}; "
                    f"SHA-256={report['sha256']}"
                )
                return 0
        except ValueError as error:
            logger.error("Research operation failed: %s", error)
        except FileExistsError:
            logger.error("Export already exists; select a new dataset ID.")
        except (psycopg.Error, OSError, RuntimeError):
            logger.error("Research operation failed; database/file details suppressed.")
        return 1
    if args.command == "health":
        print("Application configuration OK.")
        return 0

    try:
        check_database(settings)
    except (psycopg.Error, ValueError):
        # Driver errors can include credentials or connection details. Never print them.
        logger.error(
            "Database health check failed. Check PostgreSQL is running and "
            "POSTGRES_* settings are correct."
        )
        return 1

    print("PostgreSQL connectivity OK.")
    return 0

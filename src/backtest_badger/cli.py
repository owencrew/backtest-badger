"""Health checks and explicitly bounded archive ingestion."""

import argparse
import logging

import psycopg

from backtest_badger.archives import ArchiveRequest
from backtest_badger.config import load_settings
from backtest_badger.db import check_database
from backtest_badger.ingestion import ingest_archive

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
    args = parser.parse_args(argv)
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    if args.command == "ingest-archive":
        try:
            request = ArchiveRequest(args.symbol, args.interval, args.month)
        except ValueError as error:
            parser.error(str(error))
        if args.dry_run:
            return ingest_archive(request, dry_run=True)

    try:
        settings = load_settings()
    except ValueError as error:
        logger.error("Configuration error: %s", error)
        return 2

    logging.getLogger().setLevel(settings.log_level)
    if args.command == "ingest-archive":
        return ingest_archive(request, settings)
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

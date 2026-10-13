"""Stage 0 command-line health checks."""

import argparse
import logging

import psycopg

from backtest_badger.config import load_settings
from backtest_badger.db import check_database

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="badger", description="A little badger. A lot of backtests."
    )
    parser.add_argument("command", choices=("health", "db-health"))
    args = parser.parse_args(argv)
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    try:
        settings = load_settings()
    except ValueError as error:
        logger.error("Configuration error: %s", error)
        return 2

    logging.getLogger().setLevel(settings.log_level)
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

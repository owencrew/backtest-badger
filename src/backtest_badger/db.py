"""Bounded PostgreSQL connections and a read-only connectivity check."""

import psycopg

from backtest_badger.config import Settings


def connect_database(settings: Settings) -> psycopg.Connection:
    """Open an idle autocommit connection with bounded connection/server waits."""
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
        connect_timeout=5,
        options="-c statement_timeout=5000",
        autocommit=True,
    )


def check_database(settings: Settings) -> None:
    """Connect, execute a read-only probe and close, with bounded server waits."""
    with connect_database(settings) as connection:
        with connection.execute("SELECT 1") as cursor:
            if cursor.fetchone() != (1,):
                raise psycopg.DatabaseError("Unexpected health check result.")

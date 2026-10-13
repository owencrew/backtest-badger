"""A single PostgreSQL connectivity check; no schema or persistent connection pool."""

import psycopg

from backtest_badger.config import Settings


def check_database(settings: Settings) -> None:
    """Connect, execute a read-only probe and close, with bounded server waits."""
    with psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
        connect_timeout=5,
        options="-c statement_timeout=5000",
        autocommit=True,
    ) as connection:
        with connection.execute("SELECT 1") as cursor:
            if cursor.fetchone() != (1,):
                raise psycopg.DatabaseError("Unexpected health check result.")

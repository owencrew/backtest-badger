"""Migrations use the same environment settings as the Stage 0 CLI."""

from alembic import context
from sqlalchemy import URL, create_engine, pool

from backtest_badger.config import load_settings


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url="postgresql+psycopg://", literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
elif context.config.attributes.get("connection") is not None:
    # Tests supply a connection to a database they created themselves.
    run_migrations(context.config.attributes["connection"])
else:
    settings = load_settings()
    engine = create_engine(
        URL.create(
            "postgresql+psycopg",
            username=settings.user,
            password=settings.password,
            host=settings.host,
            port=settings.port,
            database=settings.database,
        ),
        poolclass=pool.NullPool,
        connect_args={
            "connect_timeout": 5,
            "options": "-c timezone=UTC -c statement_timeout=30000",
        },
    )
    try:
        with engine.connect() as connection:
            run_migrations(connection)
    finally:
        engine.dispose()

# Architecture

## Implemented in Stage 0

- **Python 3.12** and a conventional `src/backtest_badger` package keep development
  familiar and provide access to the scientific Python ecosystem in later stages.
- **uv** manages the virtual environment and locked dependencies. `pyproject.toml`
  defines the installable package and `badger` entry point; `uv.lock` gives local
  development and CI the same dependency resolution.
- **Configuration** is loaded on command execution from environment variables into
  an immutable settings record. Required values, port range and logging level are
  validated without echoing values. Importing the package does not read configuration
  or open connections. uv loads local `.env` files explicitly.
- **CLI** uses standard-library `argparse` and logging. `health` validates settings;
  `db-health` opens a short-lived Psycopg connection, executes `SELECT 1` and closes
  it. Connection and statement timeouts limit waits. Raw driver exceptions are not
  printed. SQLAlchemy is unnecessary for this single query.
- **PostgreSQL 17** runs locally through Docker Compose, bound to localhost and
  persisted in a named volume. PostgreSQL provides relational constraints and SQL
  for future market-data work. The major-version image receives patch updates;
  it is not pinned to an immutable digest. There is no application schema yet.
- **pytest and Ruff** cover configuration, CLI success/failure, safe error reporting
  and connection lifecycle. GitHub Actions uses the lockfile and no production secrets.

The application runs on the host; only PostgreSQL runs in a container. The path is
`badger → validated settings → optional PostgreSQL probe`. There are no services,
repositories, schedulers, connection pools or feature placeholder packages.

## Intended direction (not implemented)

Add modules only when a development stage needs them. Stage 1 will introduce the
market-data schema, Alembic migrations, provider ingestion and data-quality checks.
Later stages add causal features, chronological ML evaluation, realistic backtests,
forward predictions and separately accounted paper trading.

The eventual public dashboard must use read-only database access and clearly label
research, forward predictions and simulated trading. AWS Lightsail on Ubuntu is a
future deployment target; Stage 0 has no production access or deployment setup.
The historical `crypto-trading-platform` repository is outside this project's
implementation boundary and is not required by any component.

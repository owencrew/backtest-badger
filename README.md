# Backtest Badger

**A little badger. A lot of backtests.**

Backtest Badger is an open-source quantitative research platform for market-data
engineering, machine learning, backtesting and paper-trading analytics.
It begins with cryptocurrency spot markets and is intended to support other asset
classes as research develops. [backtestbadger.com](https://backtestbadger.com)

The principle is **minimum complexity, maximum correctness**: readable Python,
few dependencies, reproducible research, causal features, chronological evaluation
and realistic transaction costs. Economic viability is a question to investigate,
not a promise of profitability. Simulated results will remain distinct from live
predictions and paper trading.

## Status

Stage 0 provides the Python package, environment configuration, CLI health checks,
local PostgreSQL service, tests and lint workflow. Stage 1B.1 adds Alembic migrations
and tested persistence of exact, versioned market candles. Validation and future
acceptance criteria are in the [roadmap](docs/roadmap.md).

Market ingestion, features, ML, backtesting, live predictions, paper trading and the
public dashboard are **planned, not implemented**. The future product sections are
The Burrow (dashboard), The Dig (research) and Field Notes (experiment history).

## Local setup

Prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/getting-started/installation/)
and Docker with Compose (Docker Desktop on macOS). Run from the repository root:

```sh
uv python install 3.12  # only needed if Python 3.12 is not installed
uv sync --locked
cp .env.example .env
docker compose up -d --wait
uv run --locked --env-file .env badger health
uv run --locked --env-file .env badger db-health
```

`uv.lock` pins dependencies for development and CI and should be tracked in Git.
The CLI reads process environment variables; `uv --env-file` loads `.env`
explicitly, while Compose reads `.env` automatically. Existing shell environment
variables take precedence. `POSTGRES_DB`, `POSTGRES_USER` and `POSTGRES_PASSWORD`
are required; host defaults to `127.0.0.1`, port to `5432`, and log level to `INFO`.
`LOG_LEVEL` accepts DEBUG, INFO, WARNING, ERROR and CRITICAL.

The example credentials are **for local development only**. `.env` is ignored.
PostgreSQL binds only to `127.0.0.1` and stores data in a named Docker volume.
If port 5432 is occupied, change `POSTGRES_PORT` in `.env` before starting Compose.
Credentials initialise a new volume; changing `.env` does not change the credentials
of an existing database. Compose does not create application tables. Apply the
schema and seed the two initial market identities explicitly:

```sh
uv run --locked --env-file .env alembic upgrade head
uv run --locked --env-file .env alembic current
```

See the [persistence guide](docs/stage-01b1-persistence.md) for the Python API,
revision policy, SQL inspection and isolated PostgreSQL testing.

`badger health` validates configuration without connecting to PostgreSQL.
`badger db-health` also connects and executes `SELECT 1`, with a five-second
connection timeout and five-second statement timeout. Exit codes are 0 for success,
1 for database failure and 2 for invalid configuration or command usage. Errors go
to stderr without printing credentials or driver diagnostics.

```sh
docker compose down  # stops local PostgreSQL; retains its data volume
```

## Development

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
uv build
```

Unit tests need no database or secrets. PostgreSQL integration tests skip unless
`BADGER_TEST_ADMIN_DSN` explicitly names an isolated local PostgreSQL server's
`postgres` maintenance database. The fixtures create fresh random test databases;
they never migrate, truncate or drop the development database. Follow the
[test instructions](docs/stage-01b1-persistence.md#isolated-integration-tests).
GitHub Actions runs the full suite against an isolated PostgreSQL 17 service,
plus lint and formatting checks. There is no deployment automation.

See [architecture](docs/architecture.md), [roadmap](docs/roadmap.md),
[agent guidelines](AGENTS.md) and the [prompt archive](prompts/README.md).

## License

The new project's code is licensed under the [MIT License](LICENSE),
Copyright (c) 2026 Owen Crew. Third-party code and assets retain their own licenses.

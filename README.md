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

Historical archive ingestion, incomplete frozen research exports and
[recent REST synchronization](docs/stage-01c1-rest-tail-and-refresh.md) and
[controlled historical revalidation](docs/stage-01c2-historical-revalidation.md)
are implemented. [Stage 2A](docs/stage-02a-research-dataset.md) adds verified frozen
inputs, causal features, a 4h research target and chronological splits.
[Stage 2B](docs/stage-02b-predictive-baselines.md) adds fixed Ridge and gradient
boosting experiments with train-only fitting and validation-only baseline comparisons.
[Stage 2C](docs/stage-02c-execution-backtesting.md) implements historical validation
backtesting with independent hourly references and explicit transaction costs.
[Stage 2D](docs/stage-02d-economic-diagnostics.md) adds a reproducible economic
postmortem of those fixed simulations, including monthly results and cost budgets.
[Stage 3A](docs/stage-03a-forward-predictions.md) adds manual forward prediction
recording with strict freshness/timing checks, immutable input evidence and offline
verification. [Stage 3B](docs/stage-03b-automated-forward-collection.md) adds
reliable collection cycles, operational history and an opt-in macOS scheduler.
Predictions remain unscored observations; no model has demonstrated economic
viability. Paper trading and the public dashboard remain **planned, not implemented**. The future product sections are
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

## Offline research preparation

Use the existing frozen export, without database configuration or network access:

```sh
uv run --locked badger prepare-research \
  --output artifacts/research/stage-2a-v1 \
  --acknowledge-incomplete
```

Each run requires a new output directory. The source is explicitly incomplete;
gap-spanning windows are excluded. Feature availability includes a 60-second
settling delay, and the close-to-close target is not an executable trading return.
See the [Stage 2A guide](docs/stage-02a-research-dataset.md) for definitions,
reproduction, split counts and holdout policy.

Evaluate the fixed models on 2024 validation data, preserving the test holdout:

```sh
uv run --locked badger evaluate-models \
  --source artifacts/research/stage-2a-v1 \
  --output artifacts/experiments/stage-2b-v1
```

Use a new output directory each time. The [Stage 2B guide](docs/stage-02b-predictive-baselines.md)
records actual results, metrics, hashes and limitations. Small forecast error
reductions do not establish trading profitability.

## Manual forward observations

Refresh local data separately, then record all four fixed model predictions for
the current eligible horizon:

```sh
uv run --locked --env-file .env badger sync-recent --symbol BTCUSDT --interval 4h
uv run --locked --env-file .env badger record-forward --symbol BTCUSDT
# Use ETHUSDT in both commands for Ether.
uv run --locked badger verify-forward --record artifacts/forward-predictions/RECORD.json
```

Replace `RECORD.json` with the printed path. Recording fails on stale or incomplete
data, expired horizons and duplicates; it never refreshes data automatically.
The [Stage 3A guide](docs/stage-03a-forward-predictions.md) documents retained
provenance, deterministic training-only refits, local-clock limitations and the
actual stale-database check. These observations are not trading recommendations.

## Automated forward collection

Stage 3B adds an idempotent two-market collection cycle and offline status report:

```sh
uv run --locked --env-file .env badger forward-cycle
uv run --locked badger forward-status
```

New forecasts require complete, fresh observations and publication within 15 minutes
of candle-close-plus-60-seconds. Existing records are skipped; expired windows are
reported as missed. The [Stage 3B guide](docs/stage-03b-automated-forward-collection.md)
covers failure evidence, backups and the opt-in five-minute macOS LaunchAgent.
The scheduler is not installed automatically, and a development Mac does not provide
24/7 availability. Predictions remain unscored observations, separate from trading.

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

[Field Notes](docs/field-notes/README.md) is the curated technical research journal,
with draft stories intended for the future website's Field Notes section.

## License

The new project's code is licensed under the [MIT License](LICENSE),
Copyright (c) 2026 Owen Crew. Third-party code and assets retain their own licenses.

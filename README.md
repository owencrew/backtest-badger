# Backtest Badger

**A little badger. A lot of backtests.**

Backtest Badger is an open-source quantitative research platform for market-data
engineering, machine learning, backtesting and paper-trading analytics. It starts
with Binance Spot BTCUSDT and ETHUSDT, with other asset classes left for future
research. [backtestbadger.com](https://backtestbadger.com)

The principle is **minimum complexity, maximum correctness**: readable Python,
exact financial accounting, versioned SQL data, causal features, chronological
evaluation and reproducible evidence. Profitability is a question to investigate.

## Latest research: a working pipeline, a losing strategy

The first genuine **2024 native-minute historical backtest** completed on
24 October 2026. Six independently funded portfolios passed ledger verification.
Each began with 10,000 USDT; returns below include the frozen transaction costs.

| Market | Ridge strategy | Cash | Buy & Hold |
| --- | ---: | ---: | ---: |
| BTCUSDT | −60.69% | 0.00% | +120.81% |
| ETHUSDT | −57.96% | 0.00% | +46.18% |

Ridge substantially underperformed both benchmarks. Frequent position changes
incurred approximately 9,932.12 USDT of costs for BTC and 9,239.49 USDT for ETH.
The useful result is an inspectable account of an unsuccessful strategy, not a
claim of trading skill.

These are exploratory simulations on previously inspected history. Final values
are marked at 2024-12-31 23:00 UTC; Buy & Hold retains unsold assets without an
invented exit cost. Archive opening prices and assumed costs do not prove actual
fillability. The different holding rules mean this is **not** a controlled
execution-frequency comparison with the earlier Stage 2C study.
Read the [full research report](docs/stage-04b2e5g-first-genuine-historical-backtest.md)
or [The Price of Changing Your Mind](docs/field-notes/003-the-price-of-changing-your-mind.md).

## What works today

- **Market-data engineering:** checksum-verified archives, recent REST refresh,
  version-preserving PostgreSQL storage, disclosed gaps and immutable exports.
- **Historical research:** causal features, train-only model fitting, chronological
  evaluation, authenticated native-minute references and verified independent
  strategy/benchmark accounting.
- **Live forward evidence:** actual forecast issuance, automated collection,
  immutable outcome scoring and prospective accuracy reports. Forecast errors
  are not trading returns.
- **Paper-trading foundations:** deterministic strategy, execution and accounting
  primitives, exercised synthetically and reused for historical replay. A complete
  prospective paper-trading service is **not implemented**.

Historical backtests simulate past decisions. Live forward predictions record
forecasts before their outcomes. Prospective paper trading will simulate orders
and portfolios as new evidence arrives. Real trading places actual orders and is
outside the current scope. No model has demonstrated economic viability.

The **Stage 5A local website prototype** now lives in [`web/`](web/README.md):
The Burrow (forward research preview), The Dig (verified historical comparisons),
Field Notes, The Field Guide and About/Methodology. Run `pnpm dev` from `web/` to
review the design and editorial drafts. Production builds exclude unapproved
articles. Public launch and the public API remain planned. See the
[design and validation report](docs/stage-05a-website-design.md).

## Local development

Prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/getting-started/installation/)
and Docker with Compose. Run from the repository root:

```sh
uv python install 3.12  # only if needed
uv sync --locked
cp .env.example .env
docker compose up -d --wait
uv run --locked --env-file .env badger health
uv run --locked --env-file .env badger db-health
uv run --locked --env-file .env alembic upgrade head
```

The example credentials are for local development only; `.env` is ignored.
PostgreSQL binds to loopback and persists in a named volume. The CLI reads process
environment variables; `uv --env-file` loads `.env` explicitly. Existing shell
variables take precedence. See the [persistence guide](docs/stage-01b1-persistence.md)
for configuration, migrations and isolated database tests.

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
uv build
```

PostgreSQL integration tests skip without an explicit isolated
`BADGER_TEST_ADMIN_DSN`. GitHub Actions supplies PostgreSQL 17 and runs lint,
formatting and test suites, including guarded historical-runner checks. There is
no deployment automation.

## Research and operations guides

- [Architecture](docs/architecture.md) and [development handoff](docs/development-handoff.md)
  describe current components, evidence boundaries and next work.
- [Research preparation](docs/stage-02a-research-dataset.md),
  [predictive baselines](docs/stage-02b-predictive-baselines.md) and
  [earlier execution study](docs/stage-02c-execution-backtesting.md) retain the
  original methodology and results.
- [Local historical runner](docs/stage-04b2e5e-simple-local-historical-runner.md):
  one process, four explicit pinned inputs, preflight, explicit execution and
  verified outputs in fresh directories. The [local execution decision](docs/stage-04b2e5e-local-execution-decision.md)
  supersedes E.5d's supervisor, custody and protected-installation prerequisites
  for this route; frozen research assumptions remain unchanged.
- [Forward collection](docs/stage-03b-automated-forward-collection.md) and
  [outcome scoring](docs/stage-03d-automated-outcome-scoring.md) explain prospective
  evidence, missed horizons and operational limits.
- [Production runbook](docs/deployment/production-infrastructure.md): the verified
  **16 October 2026 snapshot** records Lightsail PostgreSQL, active collection and
  scoring, backups, restore drills and monitoring. It is not a live inventory or
  evidence that the latest research code is deployed. Unattended verification
  items remain recorded there; no host recheck was performed for this update.
- [Field Notes](docs/field-notes/README.md), [agent guidelines](AGENTS.md) and the
  [prompt archive](prompts/README.md) explain the research and development process.

## License

The new project's code is licensed under the [MIT License](LICENSE),
Copyright (c) 2026 Owen Crew. Third-party code and assets retain their own licenses.

# Roadmap

Each stage is scoped independently. Planned capabilities are not current features.

| Stage | Status | Acceptance criteria |
| --- | --- | --- |
| **0 — Foundation** | Complete | Python 3.12 package installs from the uv lockfile; configuration and both CLI checks work; local PostgreSQL connectivity is demonstrated when Docker is available; pytest and Ruff pass; CI, license and concise documentation exist. |
| **1A — Market Data Feasibility and Design** | Complete; schema decisions refined in 1B.1 | Official Binance documentation reviewed; bounded public API/archive tests completed; timeframe, revision policy and minimal schema proposed in the [Stage 1A design](stage-01a-market-data-design.md). Provider ingestion remains unimplemented; schema implemented in 1B.1. |
| **1B.1 — Schema and Persistence** | Implemented; awaiting review | Three application tables and market seeds; Alembic upgrade/downgrade; exact Decimal persistence; version-preserving writes; stale-write handling and PostgreSQL concurrency/rollback tests. No ingestion. |
| **1B.2 — Bounded Archive Ingestion** | Planned; follows 1B.1 review | Explicit-range native 4h BTCUSDT/ETHUSDT archive parsing and checksum validation; one-month backfill; manifests, raw artifacts and explicit gap reports. |
| **1B.3 — Full Historical Coverage and Research Dataset** | Planned | Expand in bounded resumable increments to full available history for selected markets, not a permanent 2024 cutoff; verify completeness and export reproducible versioned datasets. |
| **1C — Incremental Ingestion and Revisions** | Planned | Public REST tail, closed-candle eligibility, recent overlap refresh and explicit historical revalidation; valid corrections replace canonical values atomically without rewriting frozen datasets; focused quality and failure tests. |
| **2 — Quantitative Research, ML and Backtesting** | Planned | Causal features, chronological train/validation/test splits and train-only preprocessing; reproducible baseline experiments; tested execution timing, fees and slippage; honest out-of-sample reporting. |
| **3 — Live Predictions** | Planned | Forward predictions saved with timestamps and model/data provenance; reproducible inference and freshness checks; clear separation from backtest results. |
| **4 — Paper Trading and Performance** | Planned | Simulated orders, fills, costs and portfolio accounting are tested and auditable; performance is clearly labelled paper trading and separate from backtests and predictions. |
| **5 — Polished Website and Public Launch** | Planned | The Burrow, The Dig and Field Notes present understandable analytics; public database access is read-only; simulation disclosures, security and deployment checks pass before authorised launch. |
| **6 — Research and Asset-Class Expansion** | Planned | New research and asset classes are supported by documented evidence, appropriate data/execution assumptions and reproducible validation without compromising existing results. |

Real-money trading is outside this roadmap and requires explicit approval.

## Stage 1A findings and proposed direction

On 2026-10-13, public Binance access from the Mac succeeded after the sandbox's
initial DNS failure. Ten ZIP checksums and 998 archive rows passed validation;
60 overlapping archive/REST candles matched exactly after timestamp normalization.
Both markets' first returned 1h/4h candle was 2017-08-17 04:00 UTC. These bounded
samples do not establish complete historical continuity. The October 12 daily
archive was still unavailable at 00:44 UTC on October 13, so REST must cover the
tail without assuming midnight archive publication.

The selected design uses native UTC 4h candles, independent native 1h only when
needed, and three tables (`market`, `candle`, `candle_revision`). A 60-second
settling delay and seven-day overlap are initial project defaults, not provider
finality guarantees. Stage 1B/1C scopes, acceptance criteria and unresolved risks
are in the [design document](stage-01a-market-data-design.md). Stage 1B.1 implements
the schema and persistence; later increments await implementation review.

## Stage 5 — Planned website design

**Animated backtesting mascot**

When a user initiates a backtest, a small animated badger could follow the historical
price chart backwards, representing the platform investigating past market data.
This is a future product-design idea, not a Stage 0 requirement.

The animation should eventually:

- Follow the shape of a historical price line from right to left.
- Be visually engaging but subtle and professional.
- Reflect backtest progress where technically feasible, rather than displaying
  misleading artificial progress.
- Avoid interfering with chart readability or performance.
- Respect reduced-motion accessibility preferences.
- Work appropriately on desktop and mobile.

## Stage 0 validation

Stage 0 was verified locally on 2026-10-13 with Python 3.12.13: 26 pytest tests
passed, Ruff lint and formatting passed, source/wheel builds and isolated wheel
installation succeeded, and both CLI checks passed against local PostgreSQL.
CLI error exit codes and credential redaction were also checked. The GitHub
Actions workflow is configured but has not run remotely; no commit or push was made.

## Stage 1B.1 implementation

The [persistence guide](stage-01b1-persistence.md) documents the schema, API,
revision policy, migrations, inspection queries and isolated test setup. Runtime
uses Psycopg; SQLAlchemy is limited to Alembic. Only three application tables and
required PK/unique indexes exist. Concurrent writes use short transactions and
row locks, with no advisory locks around network requests. Immutable superseded
versions retain original provenance; identical confirmations advance only a
last-observed watermark to reject delayed conflicting writes.

Raw data and manifests can initially use ignored local `artifacts/`; durable
retention follows as research and deployment progress. Stage 1C retains the
60-second settling-delay and seven-day refresh-overlap defaults. No downloading,
archive parsing, REST updates, scheduling, research or dashboard work is included.
Local migration verification uses only disposable databases. Review this increment
before starting Stage 1B.2. No commit, push or deployment is part of this stage.

Local verification on 2026-10-13: **169 pytest tests passed**, including **118 real
PostgreSQL integration cases** on PostgreSQL **17.11** and all 26 Stage 0 tests.
Without a test DSN, 51 unit tests pass and 118 integration cases skip explicitly.
Ruff lint and formatting pass. Fresh/repeated upgrades, populated downgrade,
re-upgrade, offline SQL and the normal environment-configured migration CLI were
verified. An unrelated table and database timezone survived migration cycling.
The prompt archive matches the supplied prompt byte for byte. GitHub Actions is
configured for the full suite but has not been run remotely.

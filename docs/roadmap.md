# Roadmap

Each stage is scoped independently. Planned capabilities are not current features.

| Stage | Status | Acceptance criteria |
| --- | --- | --- |
| **0 — Foundation** | Complete | Python 3.12 package installs from the uv lockfile; configuration and both CLI checks work; local PostgreSQL connectivity is demonstrated when Docker is available; pytest and Ruff pass; CI, license and concise documentation exist. |
| **1A — Market Data Feasibility and Design** | Complete; awaiting design review | Official Binance documentation reviewed; bounded public API/archive tests completed; timeframe, revision policy and minimal schema proposed in the [Stage 1A design](stage-01a-market-data-design.md). No ingestion engine or schema implemented. |
| **1B — Schema and Historical Ingestion** | Planned; follows 1A review | Three application tables and first Alembic migration; verified native 4h BTCUSDT/ETHUSDT archive backfill in bounded increments; idempotent version-preserving writes; explicit gap report and reproducible dataset export. |
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

The proposed design uses native UTC 4h candles, independent native 1h only when
needed, and three tables (`market`, `candle`, `candle_revision`). A 60-second
settling delay and seven-day overlap are initial project defaults, not provider
finality guarantees. Stage 1B/1C scopes, acceptance criteria and unresolved risks
are in the [design document](stage-01a-market-data-design.md). Existing 26 tests
and Ruff checks still pass; Stage 1 implementation awaits review.

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

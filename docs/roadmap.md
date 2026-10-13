# Roadmap

Each stage is scoped independently. Planned capabilities are not current features.

| Stage | Status | Acceptance criteria |
| --- | --- | --- |
| **0 — Foundation** | Complete | Python 3.12 package installs from the uv lockfile; configuration and both CLI checks work; local PostgreSQL connectivity is demonstrated when Docker is available; pytest and Ruff pass; CI, license and concise documentation exist. |
| **1 — Market Data Engine** | Planned | First real PostgreSQL schema and Alembic migrations; reproducible spot-market ingestion; idempotent writes; explicit timestamp, missing-data and provider-revision handling; meaningful data-quality tests. |
| **2 — Quantitative Research, ML and Backtesting** | Planned | Causal features, chronological train/validation/test splits and train-only preprocessing; reproducible baseline experiments; tested execution timing, fees and slippage; honest out-of-sample reporting. |
| **3 — Live Predictions** | Planned | Forward predictions saved with timestamps and model/data provenance; reproducible inference and freshness checks; clear separation from backtest results. |
| **4 — Paper Trading and Performance** | Planned | Simulated orders, fills, costs and portfolio accounting are tested and auditable; performance is clearly labelled paper trading and separate from backtests and predictions. |
| **5 — Polished Website and Public Launch** | Planned | The Burrow, The Dig and Field Notes present understandable analytics; public database access is read-only; simulation disclosures, security and deployment checks pass before authorised launch. |
| **6 — Research and Asset-Class Expansion** | Planned | New research and asset classes are supported by documented evidence, appropriate data/execution assumptions and reproducible validation without compromising existing results. |

Real-money trading is outside this roadmap and requires explicit approval.

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

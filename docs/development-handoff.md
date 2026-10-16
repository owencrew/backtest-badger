# Development handoff — Backtest Badger

**Last updated:** 2026-10-16 (UTC)
**Repository:** https://github.com/owencrew/backtest-badger
**Product:** https://backtestbadger.com — *A little badger. A lot of backtests.*
**Next priority:** Stage 4, a realistic, independently auditable **paper-trading engine**; then Stage 5, the public website.

> **Purpose:** This is a concise continuity record for a new developer, coding agent or ChatGPT conversation. It is not a substitute for reading the current source code, tests, Git history or actual host status. Update it after each substantial milestone. Never infer that proposed work is deployed.

## 1. Resume here

Read, in order:

1. [AGENTS.md](../AGENTS.md) — engineering conventions, scientific boundaries, security and permission gates.
2. [README.md](../README.md), [architecture](architecture.md) and [roadmap](roadmap.md) — repository architecture and staged research history.
3. [Production infrastructure runbook](deployment/production-infrastructure.md) — **authoritative 2026-10-16 snapshot of the live Lightsail environment**.
4. Stage [3A](stage-03a-forward-predictions.md), [3B](stage-03b-automated-forward-collection.md), [3C](stage-03c-forward-evaluation.md) and [3D](stage-03d-automated-outcome-scoring.md) documentation, plus associated implementation and tests.
5. Stage [2C backtesting](stage-02c-execution-backtesting.md) and [2D economic diagnostics](stage-02d-economic-diagnostics.md) before reusing any simulation/execution logic.
6. Recent Git commits and the actual production release SHA. **Do not assume GitHub `main` is identical to the release deployed at `/opt/backtest-badger/current`.**

**Context drift warning:** Older README/roadmap/deployment text still says the Mac is the active scheduler and D2B cutover is planned. Those statements describe the earlier project stage and have **not** all been reconciled in Git. The newer production runbook describes the subsequent operator-verified Lightsail deployment. Inspect live state before operational changes. Updating the stale summary docs is a future documentation task, not permission to alter production.

## 2. Project and working style

Backtest Badger is an open-source Python/SQL quantitative research platform starting with **Binance Spot BTCUSDT and ETHUSDT**. It supports historical data engineering, reproducible causal research, machine-learning forecasts, historical simulation and forward prediction/outcome evidence. It is **not** a live-money trading system. Paper trading and the public dashboard are still to be built.

Core philosophy: **minimum complexity, maximum correctness**. Prefer small, readable Python modules and plain functions, pinned dependencies, PostgreSQL constraints where appropriate, explicit UTC timestamps and Decimal precision for money. Avoid speculative abstraction, uncontrolled dependencies or infrastructure expansion.

Scientific invariants:

- No look-ahead bias, retrospective forecast issuance or data leakage.
- Train-only model fitting/preprocessing; chronological validation and untouched holdouts.
- Account for execution timing, fees, slippage and market-data gaps honestly.
- Preserve immutable source observations, forecast records, outcome evidence and reproducibility provenance; do not rewrite them to make a new design work.
- Distinguish **historical backtests**, **real forward predictions**, **paper-trading orders/fills**, and **actual brokerage trades** in code, data and UI.
- Do not claim any trading edge: Stage 2C/2D historical long/cash accounts were economically negative under the tested base/stress assumptions.

Preferred collaboration workflow: inspect first; propose narrowly scoped changes and acceptance criteria; write focused tests; run the relevant test/lint suite; report precise implemented/tested/committed/deployed statuses. Make changes to production only with explicit permission. Respect the repo's Conventional Commit guidance.

## 3. Implemented capabilities — verify in code

| Area | Current understanding |
| --- | --- |
| Foundation | Python 3.12 `src/backtest_badger` package, `uv.lock`, pytest, Ruff, GitHub Actions and `badger` CLI |
| Database | PostgreSQL 17, Alembic, version-preserving market/candle storage and immutable historical `candle_revision` |
| Collection | Binance archive checksums, native 4-hour candle history, recent REST refresh, bounded revalidation and visible source gaps |
| Research | Immutable incomplete historical export, causal features and frozen Stage 2A datasets |
| Models | Train-only baselines, Ridge and gradient boosting; deterministic evaluation and recorded limitations |
| Backtesting | Stage 2C long/cash backtests with delayed execution and explicit fees; Stage 2D cost/performance diagnosis |
| Forward evidence | Stage 3A genuine immutable live predictions; Stage 3B idempotent collection operations |
| Scoring | Stage 3C prospective outcomes and Stage 3D automated scoring with separate evidence |
| Hosting | Operator-verified Lightsail PostgreSQL and collection/scoring systemd workers plus reliable backup/monitoring stack |

There is **no verified implementation yet** of a complete order/fill/portfolio paper-trading engine, public application API or launched dashboard. Do not claim otherwise merely because the README describes the product vision.

The initial data universe is only two crypto spot markets. Forward predictions use genuine issuance timestamps and native 4h horizons; outcome scoring happens when the target is eligible. Avoid using information unavailable at simulated decision time.

## 4. Production snapshot (16 October 2026)

See [production-infrastructure.md](deployment/production-infrastructure.md) for all commands, files and safety rules. Summary:

- AWS Lightsail Ubuntu 24.04, roughly 4 GiB RAM, 77 GB root filesystem (~9% used on last check).
- PostgreSQL 17 Docker container `backtest-badger-lightsail-postgres-1`, database `backtest_badger`, persistent named volume `backtest-badger-pg17`.
- Current release path `/opt/backtest-badger/current`; historically observed source revision `e0d622d51e1edc120fb4f1b5229e46907ed6219d`, **not guaranteed current**.
- Six active scheduled timers at last verification: collection and scoring every five minutes; encrypted S3 backup daily 02:40 UTC; isolated restore drill Sundays 06:00 UTC; storage monitoring every six hours; local checkpoint retention daily 05:30 UTC.
- Backup snapshots via encrypted restic in versioned S3 (`eu-west-2`), including consistent `pg_dump`/four-table SHA-256 fingerprints and `bundle.sha256`. Snapshot IDs and actual row counts can change over time.
- Independently demonstrated an end-to-end S3 restore and exact source/recovered fingerprints for **40,096 candles** on 16 October, followed by a successful supervised systemd restore drill.
- AWS budget **USD $35/month** with four notifications; local disk/backup warnings via SNS; S3 lifecycle expiration only for noncurrent `restic/locks/` after 30 days and `monitoring/` after 90 days.
- Three newest local checkpoints retained; one guarded local deletion tested successfully; daily retention scheduler enabled. **Remote restic pruning remains disabled**; budget alerts are not a spending cap.
- Backup/restore validation is automatic, **production restoration is not**. Never restore over the live database without explicit approval and an isolated rehearsal.

Do not commit private environment files, restic password, cloud credentials, complete operational logs or live data. Do not remove Docker volumes or recovery resources because `docker system df` labels them reclaimable. Do not change scientific code or worker activation during unrelated development.

## 5. Pending infrastructure verification — not a blocker to local Stage 4 design

As of this handoff, **the first unattended runs using the final configurations have not yet been observed**:

- 2026-10-17 02:40 UTC: daily shared-snapshot S3 backup; 04:00 UTC independent freshness monitor; 05:30 UTC automatic four-checkpoint local cleanup.
- 2026-10-18 06:00 UTC: first unattended fingerprint-aware isolated recovery drill.
- Automatic retention wrapper was tested in a **no-deletion** service run, while the guarded one-checkpoint deletion was tested manually. Its unattended deleting path still needs validation.
- The wrapper intentionally refuses when there are other than exactly four local checkpoints; prolonged misses can leave local files accumulating. The separate disk monitor should warn, but no hard bound is enforced.
- Remote restic keep-last/daily/weekly/monthly retention was reviewed in **dry run only**, not deployed. Current S3 backup data has no lifecycle expiration rule.
- Legacy S3 checkpoints without fingerprint audit can pass restore structural checks with a warning. Missing Lambda-invocation alert and independent monitor-execution failure alerts are not yet verified as present.
- Old architecture/roadmap/README statements about Mac-only scheduling and pending cutover need updating to reflect the operator-verified deployed state.

Record observed unattended results as they arrive, distinguishing success from mere timer activation.

## 6. Immediate task: design Stage 4 paper trading

**Do not implement from this document alone. First inspect actual modules, tests, schema/migrations, APIs/CLI and immutable forward records.** Then propose a bounded Stage 4A that can be tested offline and introduced without breaking existing worker timing.

Suggested staged direction (design proposals, **not accepted implementation decisions**):

1. **4A — Trading/accounting contract:** specify a spot long/cash paper strategy, decision events, portfolio currency, eligible forecast time, capital, target exposures, idempotency keys, transaction-cost parameters and fixed evaluation protocol. Determine which existing backtest accounting functions can be reused safely.
2. **4B — Deterministic simulation core:** separately test orders, price/quantity precision, fills, fees, cash, holdings, realised/unrealised P&L, equity, drawdown and rejected/skipped orders; define conservative execution when data is missing. No actual order submission.
3. **4C — Persistent immutable events:** design migrations and audit trails for paper signals, orders, fills, portfolio/account state and reconciliation; safe replay and unique identity constraints.
4. **4D — Prospective service integration:** schedule only future eligible decisions with explicit UTC observation/decision/execution timestamps; avoid hindsight executions or retroactive fills. Choose any additional timer only after a small rehearsal.
5. **4E — Read-only reporting/API:** positions, realised/unrealised returns, fees, performance attribution, trade history and model/portfolio comparison. No publicly exposed database administrator access.

Questions to resolve from the actual code and product requirements: what constitutes a tradable signal from the current forecasts; whether to start with BTC/ETH spot long/cash or include shorting; base quote currency and starting paper capital; forecast-to-order timing and price source; whether reference hourly prices are permissible **prospectively**; conservative fees/slippage; position sizing; handling delayed or missed cycles; accounting lots; failed fills and market outages; evaluation versus cash and buy-and-hold.

**Acceptance baseline:** no real-money credentials or exchange orders, no look-ahead, no mutation of existing forecast/outcome artifacts, deterministic and auditable accounting, cost-inclusive reporting, tests for idempotency and failure, and explicit separation of simulated and real outcomes.

## 7. Website (Stage 5, after a reliable paper-trading contract)

Brand: **Backtest Badger** — *A little badger. A lot of backtests.*

Proposed information architecture (existing product intent): **The Burrow** (dashboard and paper portfolios), **The Dig** (backtests/research), **Field Notes** (technical research/experiment history). Website address `backtestbadger.com` is owned, but **a publicly running application is not yet confirmed**.

Develop a simple read-only public API and dashboard on clearly labelled source categories: historical validation, genuine forward results and simulated paper trades. Protect sensitive configuration and DB; do not add real-money execution without separate authorisation. Choose frontend stack/deployment based on requirements, not assumed infrastructure.

## 8. New conversation restart instructions

Copy/paste this short prompt into a new chat, or simply ask the assistant to read this file:

> We are continuing **Backtest Badger** (https://github.com/owencrew/backtest-badger). Please read `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/development-handoff.md` and `docs/deployment/production-infrastructure.md` first, and inspect the real code and latest commits. The README/roadmap contain stale deployment-stage statements; distinguish historical plans from the actual current infrastructure runbook. Do not assume GitHub HEAD is deployed. Our priority is **Stage 4 paper trading, then Stage 5 website**. Preserve immutable prediction/scoring evidence, avoid look-ahead and unapproved production changes, distinguish planned/tested/deployed status, and continue from the current codebase rather than restarting. First summarize the current implementation, identify the smallest sensible next milestone and propose testable acceptance criteria.

## 9. Maintaining this file

After each meaningful milestone, refresh:

- **Date, branch, Git SHA, deployment SHA** (if checked), and links to relevant PRs/commits.
- **What changed**, with paths and migration names, and which tests were actually executed.
- **Operational impact**, if any: new timers, costs, secrets/permissions, storage, alerts and rollback instructions.
- **Next exact task** and open blockers/decisions; remove obsolete claims rather than accumulating contradictory history.

Maintain this as a **short current-state handoff**, not a transcript of hundreds of development steps. Git commits, code, tests and runbooks remain the underlying source of truth.

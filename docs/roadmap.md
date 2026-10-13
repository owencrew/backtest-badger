# Roadmap

Each stage is scoped independently. Planned capabilities are not current features.

| Stage | Status | Acceptance criteria |
| --- | --- | --- |
| **0 — Foundation** | Complete | Python 3.12 package installs from the uv lockfile; configuration and both CLI checks work; local PostgreSQL connectivity is demonstrated when Docker is available; pytest and Ruff pass; CI, license and concise documentation exist. |
| **1A — Market Data Feasibility and Design** | Complete; schema decisions refined in 1B.1 | Official Binance documentation reviewed; bounded public API/archive tests completed; timeframe, revision policy and minimal schema proposed in the [Stage 1A design](stage-01a-market-data-design.md). Schema implemented in 1B.1; bounded monthly archives implemented in 1B.2. |
| **1B.1 — Schema and Persistence** | Implemented; awaiting review | Three application tables and market seeds; Alembic upgrade/downgrade; exact Decimal persistence; version-preserving writes; stale-write handling and PostgreSQL concurrency/rollback tests; ingestion added separately in 1B.2. |
| **1B.2 — Bounded Archive Ingestion** | Implemented; awaiting review | Explicit monthly native 1h/4h CLI; bounded checksum/parser validation; atomic conflict-rejecting backfill; local raw evidence and manifests. January 2025 live 4h import: 186 candles per market, zero gaps/revisions. |
| **1B.3 — Full Historical Coverage and Research Dataset** | Implemented; acquired with known gaps | All 220 market-months through September 2026 inspected and committed; 19,955 candles and 36 disclosed gaps per market. Frozen 39,910-row export is explicitly incomplete. See [results](stage-01b3-full-history.md). |
| **1C.1 — REST Tail and Recent Refresh** | Implemented; awaiting review | Fixed eligible cutoff, strict native 4h REST, seven-day refresh, bounded catch-up, atomic page revisions and stored-grid diagnostics. Live: 75 new candles per market, 20,030 total each; zero recent gaps/revisions, historical gaps and frozen export preserved. See [guide](stage-01c1-rest-tail-and-refresh.md). |
| **1C.2 — Historical Revalidation** | Planned | Deliberate bounded source/range selection, older revision review and provenance reporting; frozen datasets remain unchanged. |
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

**Field Notes journal**

The repository's [Field Notes](field-notes/README.md) journal holds curated
engineering and research articles for this future website section. Entries begin
as drafts and require editorial review before publication; they are not automatic
development logs. Website presentation and publishing remain Stage 5 work.

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
60-second settling-delay and seven-day refresh-overlap defaults. That persistence
increment included no downloading, archive parsing, REST updates, scheduling,
research or dashboard work.
Local migration verification uses only disposable databases. Stage 1B.2 is
documented separately below. No commit, push or deployment is part of this stage.

Local verification on 2026-10-13: **169 pytest tests passed**, including **118 real
PostgreSQL integration cases** on PostgreSQL **17.11** and all 26 Stage 0 tests.
Without a test DSN, 51 unit tests pass and 118 integration cases skip explicitly.
Ruff lint and formatting pass. Fresh/repeated upgrades, populated downgrade,
re-upgrade, offline SQL and the normal environment-configured migration CLI were
verified. An unrelated table and database timezone survived migration cycling.
The prompt archive matches the supplied prompt byte for byte. GitHub Actions is
configured for the full suite but has not been run remotely.

## Stage 1B.2 implementation

The [archive ingestion guide](stage-01b2-archive-ingestion.md) documents explicit
single-month commands, full-grid validation, atomic backfill conflict handling,
provenance and ignored local artifacts. Standard-library acquisition adds no
dependencies or schema migration. Live January 2025 native 4h ingestion yielded
372 candles, zero gaps and zero revisions across BTCUSDT and ETHUSDT. Stage 1B.3
coverage expansion and exports remain deferred until review; no automatic extra
months, REST ingestion, scheduling or historical revalidation were added.

Local final verification: 227 tests passed (101 unit, 126 PostgreSQL integration),
plus Ruff lint and formatting. Each repeated live import returned 186 unchanged
candles and no inserts or revisions; exact values and original provenance remained
unchanged. Only confirmation watermarks advanced. The temporary test container was
separate from the existing development database, which remained at revision 0001.

## Stage 1B.3 implementation

The [full-history guide](stage-01b3-full-history.md) records commands, restart
semantics, initial-boundary evidence, actual backfill results and snapshot exports.
The two-market source start is 2017-08-17 04:00 UTC; the requested exclusive end is
2026-10-01 00:00 UTC. Completeness is checked against stored identities, with no
interpolation or silent exclusion of gaps. Unchanged imports preserve accepted
versions and provenance. Existing monthly ingestion and persistence are reused;
no new schema or dependencies are introduced. Stage 1C remains unimplemented and
requires review before work begins.

Initial Stage 1B.3 verification: 247 tests passed (116 unit, 131 isolated PostgreSQL
integration), with Ruff lint/format passing. Eight bounded imports passed, then
full BTC backfill stopped at September 2017's invalid close boundary and missing
16:00 UTC candle on September 6. Each market has 641 stored candles; January
observations and provenance are preserved, with zero revisions. The declared
full range remains incomplete and its export was refused. No validation was
weakened, no later full-range imports were attempted after the blocker, and no
partial live export was implicitly approved.


### Stage 1B.3 historical-anomalies follow-up

Implemented opt-in `backfill-history --allow-source-gaps`, preserving strict
monthly defaults, economic/identity/checksum validation and atomic conflict
rejection. Missing intervals and excluded irregular-close rows remain visible
in coverage and export manifests; no timestamp normalization or replacement
candles were added. Official September 2017 and June 2018 comparisons are retained
as offline regression fixtures; interruption-sensitive research windows must
explicitly handle gaps and cannot assume uninterrupted trading within native bars.

Both full histories through September 2026 were acquired: **110 months and 19,955
stored native 4h candles per market**, with **17 absent monthly-source intervals
and 19 excluded rows per market** (36 stored gaps each). All 1,282 pre-existing
rows were preserved; there were zero conflicts, stale changes, failures or
revisions. Complete export remains correctly refused. Final checks: **268 tests
passed (133 unit, 135 isolated PostgreSQL integration)**, plus Ruff lint/format.
See the [full-history guide](stage-01b3-full-history.md) for exact identities,
investigation, source disagreement, totals and remaining limits. Stage 1C remains
unimplemented; stop here for review.

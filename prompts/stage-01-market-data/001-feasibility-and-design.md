# Backtest Badger — Stage 1A: Binance Data Feasibility & Architecture

You are acting as a senior Python data engineer and quantitative research architect.

We are beginning Stage 1A of Backtest Badger.

**This is a read-only feasibility and design exercise. Do not implement the production ingestion engine or database schema yet.**

## 1. Project context

Backtest Badger is an open-source quantitative research platform.

- Repository: `~/Code/backtest-badger`
- Website: https://backtestbadger.com
- Official tagline: A little badger. A lot of backtests.
- Development: macOS
- Future deployment: AWS Lightsail on Ubuntu
- Primary objectives: excellent engineering, scientifically credible research, public analytics, and eventually investigating economic viability.

Stage 0 is complete.

Before proceeding:

1. Read `AGENTS.md`.
2. Read `docs/architecture.md` and `docs/roadmap.md`.
3. Inspect the existing Python configuration, CLI and database connection implementation.
4. Preserve all Stage 0 functionality.

The original `../crypto-trading-platform` repository is not needed for this stage. Do not access or modify it.

**Overriding design principle: minimum complexity, maximum correctness.**

## 2. Initial market selection

We have provisionally selected Binance Spot as the first data source.

Markets:

- `BTCUSDT` — BTC/USDT
- `ETHUSDT` — ETH/USDT

We intend to use:

- Binance Vision archives for historical OHLCV data.
- Binance's public market-data-only REST API for recent candles and incremental updates.
- PostgreSQL for durable storage.
- UTC timestamps.
- Four-hour candles for initial quantitative research.
- Potentially one-hour candles for execution-price modelling and additional validation.

Future support for other exchanges and asset classes is desirable, but must not create unnecessary Stage 1 complexity.

Do not implement generic multi-provider abstractions.

## 3. Task A — Verify Binance data access

Consult current official Binance documentation.

Primary references:

- https://github.com/binance/binance-public-data
- https://github.com/binance/binance-spot-api-docs
- https://data.binance.vision
- https://data-api.binance.vision

Verify:

1. Availability of BTCUSDT and ETHUSDT spot candles.
2. Availability of native `1h` and `4h` intervals.
3. Historical data coverage for each market.
4. Monthly and daily archive organisation.
5. ZIP file format and accompanying checksums.
6. Public REST API access without authentication.
7. REST API pagination and request limits.
8. Timestamp units and UTC interpretation.
9. Current archive publication cadence.
10. Known archive corrections or revision behaviour.

Clearly distinguish documented provider behaviour from observations verified locally.

### Bounded live tests

If outbound network access is permitted, run a small number of read-only public requests from the Mac.

Use a maximum of approximately 15 MB total downloads, with sensible request timeouts.

Suggested tests:

- Public API connectivity and exchange information for BTCUSDT and ETHUSDT.
- A small sample of recent closed 1h and 4h candles.
- One older daily archive from before 2025.
- One daily archive from after 1 January 2025.
- One recent daily archive with an overlapping REST API range.
- Corresponding checksum verification.

Select concrete dates where files are available. Record the actual dates used.

Do not download entire historical datasets.

Do not scrape unofficial providers.

Do not require exchange credentials.

If connectivity is unavailable, document the limitation instead of claiming that tests passed.

Use temporary or ignored files for downloaded samples. Do not commit market-data archives.

## 4. Task B — Validate candle semantics and data quality

Inspect the observed data and confirm:

- Exact archive columns and data types.
- Open-time and close-time semantics.
- Millisecond versus microsecond timestamp differences.
- Timestamp alignment for hourly and four-hour candles.
- OHLC consistency.
- Positive prices and non-negative volumes.
- Missing intervals and duplicate observations.
- How an incomplete current candle is identified and excluded.
- Differences between archival and API observations, where comparable.

For comparisons, use exact market, timeframe and UTC open-time identity.

Do not assume archive and API observations are identical without checking.

Avoid float-based price comparisons that create artificial discrepancies.

Document how we should distinguish:

- An incomplete candle.
- A missing candle.
- An invalid candle.
- A valid provider revision.
- An anomalous provider observation.

Do not interpolate missing market data.

## 5. Task C — Decide the initial timeframe architecture

Compare two alternatives.

### Option A — Native 4h candles

Download Binance's native four-hour candles directly.

Potential advantages:

- Simpler ingestion.
- No derived-parent persistence.
- No four-parent invalidation machinery.
- Direct alignment with our initial research timeframe.

### Option B — Hourly candles with deterministic 4h resampling

Download one-hour candles and derive four-hour candles locally.

Potential advantages:

- Greater granularity.
- Independent control of aggregation.
- Potential reuse for execution-price modelling.
- Transparent relationships between hourly and four-hour observations.

Evaluate complexity, scientific correctness, data consistency, future execution requirements and maintainability.

Also consider a minimal third option: native 4h candles for features, with native 1h candles retained separately when needed for execution or validation.

**Make one clear recommendation for Stage 1.**

Do not introduce derived-candle tables or lineage machinery without a demonstrated need.

## 6. Task D — Design minimal revision handling

Our previous project encountered a failure where a historical hourly candle changed after initial ingestion.

The first observation was retained indefinitely, later differing observations were treated as unresolved conflicts, and an old defective parent prevented unrelated future inference.

Backtest Badger must avoid repeating this architecture.

Propose a simple policy that:

1. Accepts structurally valid provider observations.
2. Preserves evidence of genuine corrections.
3. Keeps current canonical data clearly identifiable.
4. Does not create unnecessary duplicate records for identical repeat requests.
5. Allows a legitimate corrected value to replace the current selection.
6. Supports reproducible historical research.
7. Preserves the distinction between market time and observation availability time.
8. Never silently rewrites already-issued forward predictions.
9. Ensures old irrelevant revisions do not block current inference.

Consider an explicit short post-close settling delay, recent-candle overlap refresh and a bounded revision window.

Explain how revisions outside that window should be handled when encountered during deliberate historical revalidation.

Use a small number of database constraints and clear application logic.

Do not introduce a voting system, complex event-sourcing framework or candidate-style immutable lifecycle machinery.

## 7. Task E — Design the first PostgreSQL schema

Review the current Stage 0 database setup.

Propose the minimum relational schema necessary for historical and incremental candle ingestion.

Consider:

- Market identity.
- Candle observations or revisions.
- Current selected candles.
- Ingestion-run diagnostics, if necessary.

Do not automatically create a table for every concept.

Compare a simple canonical-candle-plus-revision-history design against a separate immutable-observations-and-current-selection design.

Choose the simpler design that meets the genuine correctness requirements.

Specify:

- Tables and columns.
- Primary keys.
- Natural and unique keys.
- Relevant foreign keys.
- UTC timestamp representation.
- Numeric precision.
- Important check constraints.
- Indexes required by actual planned queries.
- Idempotent upsert behaviour.
- Transaction boundaries for revised observations.
- How data snapshots will eventually be reproducible.

Distinguish these timestamps explicitly:

- Market timestamp.
- Provider observation or ingestion timestamp.
- Research or prediction recording timestamp.

Only Stage 1 tables should be designed.

Do not create model, prediction, backtest, portfolio or website tables.

Do not implement the schema or create Alembic migrations yet.

## 8. Task F — Plan Stage 1 implementation

Divide the remaining Stage 1 work into small, independently verifiable increments.

Suggested structure:

### Stage 1B — Schema and historical ingestion

Implement the first migrations and bounded historical backfill.

### Stage 1C — Incremental ingestion and revisions

Implement current-candle updates, idempotency, revision handling and data-quality reporting.

Include 1h/4h validation or aggregation only where justified by the selected timeframe architecture.

For each increment, provide:

- Exact scope.
- Deliverables.
- Important invariants.
- Targeted tests.
- Objective acceptance criteria.
- Dependencies and risks.

Prioritise reaching a usable research dataset over introducing extensive infrastructure.

## 9. Explicit restrictions

Do not:

- Implement production ingestion modules.
- Create or modify application tables.
- Apply migrations.
- Download complete historical datasets.
- Build technical indicators or ML models.
- Implement backtesting.
- Implement scheduled prediction jobs.
- Create dashboard or website functionality.
- Access the original repository.
- Access production infrastructure.
- Modify the existing Lightsail deployment.
- Add unnecessary dependencies.
- Introduce speculative multi-exchange abstractions.
- Commit or push changes.

This stage is design and bounded provider verification only.

## 10. Documentation and prompt archive

Create one concise design document:

`docs/stage-01a-market-data-design.md`

It should contain:

1. Executive recommendation.
2. Verified Binance API/archive findings.
3. Actual feasibility-test results and limitations.
4. Native 4h versus derived 4h decision.
5. Proposed revision policy.
6. Minimal PostgreSQL schema.
7. Historical and incremental ingestion approach.
8. Stage 1B/1C implementation plan.
9. Unresolved decisions and risks.

Keep it practical and implementation-oriented.

Update `docs/roadmap.md` to reflect Stage 1A's findings and current status.

Update `docs/architecture.md` only if the planned architecture materially changes. Clearly label unimplemented design decisions as planned.

Maintain `AGENTS.md` only if an enduring project-wide engineering principle needs to change.

Preserve this exact substantive Codex prompt under:

`prompts/stage-01-market-data/001-feasibility-and-design.md`

Do not modify existing historical prompts.

## 11. Final report

At completion, report:

- Official documentation consulted.
- Public endpoints and archive samples actually tested.
- Test successes and failures.
- Recommended historical and incremental data sources.
- Recommended timeframes.
- Recommended revision-handling policy.
- Proposed schema and number of tables.
- Files created or modified.
- Stage 1B implementation readiness.
- Questions or risks that remain unresolved.

Distinguish tested facts from assumptions.

Review the proposal for unnecessary complexity before finishing.

**Do not implement Stage 1B or Stage 1C. Do not commit or push. Stop after Stage 1A and await review.**
# Backtest Badger — Stage 1B.1: Market Data Schema & Persistence

You are acting as a senior Python data engineer with expertise in PostgreSQL, data integrity and quantitative research systems.

Implement Stage 1B.1 of Backtest Badger: the minimal PostgreSQL schema and tested persistence logic for versioned market candles.

**Do not implement market-data downloading or ingestion from Binance yet.**

## 1. Context

Repository: `~/Code/backtest-badger`

Before beginning, read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-01a-market-data-design.md`

Stage 0 is complete and Stage 1A established our market-data architecture.

We have selected:

- Binance Spot as the first provider.
- BTCUSDT and ETHUSDT as the initial markets.
- Native 4h candles as the initial research dataset.
- Native 1h candles only when justified by future execution or validation requirements.
- PostgreSQL 17 for storage.
- Immutable historical candle versions alongside a mutable current selection.

**Overriding principle: minimum complexity, maximum correctness.**

Preserve all working Stage 0 functionality.

## 2. Scope

Implement the schema and persistence mechanisms only.

Introduce Alembic for database migrations.

Use the existing Psycopg connectivity approach for runtime database operations, unless there is a compelling demonstrated reason to change it.

SQLAlchemy may be used for Alembic migration infrastructure. Do not introduce an unnecessary ORM or generic repository abstraction.

## 3. Database schema

Implement the three tables proposed in Stage 1A:

### market

Stores exchange-market identity.

Fields include:

- market_id
- venue
- market_type
- symbol
- base_asset
- quote_asset

Enforce unique venue/market-type/symbol identity.

Support BTCUSDT and ETHUSDT initially without hard-coding the entire application around only two symbols.

### candle

Stores the current accepted version of each candle.

Identity:

`(market_id, interval_seconds, open_time)`

Include:

- OHLC prices.
- Base and quote volumes.
- Trade count.
- Taker-buy base and quote volumes.
- Version number.
- Observation timestamp.
- Recording timestamp.
- Source kind, source URL and source content hash.

Use PostgreSQL numeric types suitable for exact decimal preservation.

Store timestamp-aware UTC values.

Support 1h and 4h candle intervals.

### candle_revision

Stores superseded versions of accepted candle observations.

Preserve all previous economic values, source details and original timestamps.

The historical version must remain retrievable even after subsequent corrections.

A candle may progress through:

A → B → A

Each actual accepted change must remain distinguishable as a separate version.

Do not deduplicate history solely by OHLCV content hash.

### Constraints

Implement meaningful database constraints for:

- Candle identity and interval alignment.
- Positive finite prices.
- Valid OHLC relationships.
- Non-negative finite volumes.
- Valid trade counts.
- Taker volume bounds.
- Positive version numbers.
- Valid timestamp relationships.
- Foreign-key integrity.

Verify PostgreSQL numeric NaN/Infinity behaviour when designing checks rather than assuming ordinary numeric comparisons exclude these values.

Do not add unrelated tables or indexes without a demonstrated requirement.

## 4. Persistence behaviour

Implement a small, clear persistence API.

It must support:

- Inserting a new valid candle.
- Detecting identical observations without creating duplicates.
- Accepting valid revised observations.
- Preserving the previous version before changing the current row.
- Retrieving current candles over a bounded time range.
- Retrieving the complete version history of an individual candle.

An accepted update must be atomic.

If the history insertion or canonical update fails, the entire transaction must roll back.

Retried identical writes must be idempotent.

Do not use unconditional conflict updates that overwrite evidence.

### Concurrency

Do not hold database locks across external HTTP requests.

Use short transactions, PostgreSQL row-level locking and conflict-safe insertion where appropriate.

Ensure concurrent writers cannot silently lose a version or overwrite newer observations with older ones.

Use observation timestamps and explicit stale-write handling where necessary.

Test the insertion race where two writers initially observe an absent candle, as well as two writers attempting revisions.

Introduce advisory locks only if simpler database mechanisms cannot satisfy a demonstrated concurrency invariant.

## 5. Revision policy

The current candle contains the latest accepted observation under the documented selection policy.

An identical observation is a no-op.

A changed, valid observation creates a new version and retains the previous version.

An older delayed observation must not silently replace a newer accepted observation.

Keep data validation and version-selection decisions understandable.

Do not build a general event-sourcing system.

Do not add provider reconciliation frameworks.

No network requests are required for this stage; use synthetic test observations.

## 6. Migrations

Introduce a minimal Alembic configuration.

Create the first application migration for the three tables and their required constraints.

The migration must:

- Apply cleanly to an empty development database.
- Not destroy existing Stage 0 database settings or unrelated data.
- Support a safe, tested downgrade in a disposable database.
- Use conventional migration organisation.
- Avoid unnecessary migration helper frameworks.

Do not delete existing database volumes or databases.

Seed the two initial market identities in a simple, reproducible manner.

## 7. Testing

Create focused pytest tests covering:

- Fresh database migration.
- Candle insertion and retrieval.
- Exact Decimal round trips.
- Duplicate/idempotent writes.
- A → B → A revision history.
- Transaction rollback on failure.
- Validation and database constraints.
- UTC timestamp handling.
- Out-of-order observations.
- Concurrent insertion/revision attempts.
- Historical-version retrieval.

Use a disposable PostgreSQL test database for integration tests.

Do not allow tests to truncate, drop or overwrite the normal development database.

Ensure the tests exercise actual PostgreSQL transaction behaviour rather than relying exclusively on mocks.

Keep existing Stage 0 tests working.

If needed, extend GitHub Actions minimally to run the PostgreSQL integration tests using an isolated service database.

Run pytest, Ruff and relevant migration checks.

## 8. Documentation updates

Update `docs/architecture.md` with the implemented market-data schema.

Update `docs/roadmap.md` to reflect Stage 1B.1 progress.

Refine `docs/stage-01a-market-data-design.md` where necessary to record the final implementation decisions.

In particular:

- Full available historical coverage is the eventual Stage 1B.3 objective; 2024 onward is not a permanent restriction.
- Retain 60 seconds as the initial settling-delay default and seven days as the initial refresh-overlap default for Stage 1C.
- Prefer short database transactions over advisory locks held during network requests.
- Raw data artifacts and manifests can initially be stored in ignored local directories, with durable retention addressed as research and deployment progress.

Maintain `AGENTS.md` only if a lasting engineering principle changes.

Preserve this exact prompt in the stage-based prompt archive.

## 9. Explicit exclusions

Do not:

- Download market data.
- Call Binance APIs.
- Implement ZIP/CSV archive ingestion.
- Implement incremental REST updates.
- Implement technical indicators.
- Implement ML or backtesting.
- Implement derived candle aggregation.
- Implement scheduling.
- Implement the dashboard or website.
- Access the original crypto-trading-platform repository.
- Access or change AWS infrastructure.
- Add unnecessary dependencies or abstractions.
- Commit or push changes.

## 10. Completion report

After implementation, provide:

1. Files created and modified.
2. Final database schema and constraints.
3. Description of candle revision behaviour.
4. Explanation of transaction and concurrency guarantees.
5. Test results, including PostgreSQL integration tests.
6. Migration verification results.
7. Any unresolved risks.
8. Instructions for running migrations and inspecting stored candles locally.

Review the code for unnecessary complexity before finishing.

**Stop after Stage 1B.1. Do not begin historical ingestion until the implementation has been reviewed.**
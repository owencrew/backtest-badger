# Backtest Badger — Stage 1B.2: Historical Binance Archive Ingestion

You are acting as a senior Python data engineer specialising in market-data pipelines, PostgreSQL and reproducible quantitative research.

Implement **Stage 1B.2: bounded historical Binance Spot archive ingestion**.

The objective is to download, validate and persist genuine historical candles using the Stage 1B.1 persistence layer.

Do not implement a full historical backfill, incremental REST ingestion, ML or backtesting yet.

## 1. Review the existing implementation

Repository: `~/Code/backtest-badger`

Read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-01a-market-data-design.md`
- `docs/stage-01b1-persistence.md`
- `src/backtest_badger/candles.py`
- `src/backtest_badger/cli.py`
- Existing migrations and tests.

The development PostgreSQL database has already been migrated to Alembic revision `0001 (head)`.

Do not recreate the schema or apply unnecessary migrations.

Preserve existing commands, tests and project conventions.

Engineering principle: **minimum complexity, maximum correctness**.

## 2. Initial ingestion scope

Provider: Binance Spot.

Markets:

- BTCUSDT
- ETHUSDT

Primary timeframe: native 4h candles.

Initial live validation period: **January 2025**, separately for both markets.

Expected result for a complete month:

- BTCUSDT: 186 candles.
- ETHUSDT: 186 candles.
- Total: 372 candles.

These are expected counts, not figures to force into the database. If actual coverage differs, investigate and report it.

Use Binance Vision monthly archives:

`https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-YYYY-MM.zip`

Download the companion `.CHECKSUM` file.

Use only publicly accessible, unauthenticated market-data endpoints.

Support an explicitly selected month, symbol and native interval. The initial real import must remain limited to January 2025.

Do not automatically download additional months.

## 3. Command-line interface

Extend the existing argparse CLI with a command such as:

`badger ingest-archive --symbol BTCUSDT --interval 4h --month 2025-01`

Also support:

`badger ingest-archive --symbol BTCUSDT --interval 4h --month 2025-01 --dry-run`

The dry-run mode must fetch, validate and report the archive without writing candle data.

Requirements:

- Preserve `badger health` and `badger db-health`.
- Require explicit symbol, interval and month arguments.
- Validate arguments before network access.
- Initially restrict symbols to the two seeded Binance Spot markets.
- Permit native 1h and 4h intervals using shared parsing logic, but validate live ingestion with 4h only.
- Print useful progress and final counts.
- Use nonzero exit codes for failed ingestion.
- Never expose database credentials or sensitive environment values in errors.

Avoid introducing a new CLI framework.

## 4. Download and checksum validation

Implement a small Binance archive downloader.

Requirements:

1. Use HTTPS and the documented Binance Vision archive paths.
2. Fetch both the ZIP and its CHECKSUM sidecar.
3. Calculate SHA-256 over the exact ZIP bytes.
4. Verify the checksum before parsing or persisting.
5. Handle missing files, timeouts, non-success HTTP responses and corrupt downloads.
6. Use reasonable request timeouts, bounded retries and response-size limits.
7. Do not retry indefinitely.
8. Avoid unnecessary external dependencies; the Python standard library is acceptable.
9. Do not make trading API calls or require API keys.

Treat a missing archive file as an acquisition failure, not evidence that the exchange had no trading activity.

Do not confuse a matching file checksum with proof that the market prices are economically correct.

## 5. CSV parsing and timestamp handling

Binance Spot kline archives contain 12 columns, without a CSV header.

Parse and validate the documented column order:

1. Open time.
2. Open price.
3. High price.
4. Low price.
5. Close price.
6. Base volume.
7. Close time.
8. Quote volume.
9. Trade count.
10. Taker-buy base volume.
11. Taker-buy quote volume.
12. Ignored provider field.

Requirements:

- Parse prices and volumes directly into `Decimal`.
- Never use floating-point numbers for economic values.
- Parse trade counts as integers.
- Use timezone-aware UTC timestamps.
- Handle Binance Spot archive milliseconds before 2025 and microseconds from 1 January 2025.
- Determine timestamp units using the documented archive contract, not merely the number of digits.
- Validate the provider's inclusive close-time boundary and normalise internally to an exclusive interval end.
- Validate interval alignment and requested month boundaries.
- Validate all economic fields against the existing `CandleObservation` rules.
- Do not assume the ignored final column is zero.
- Reject malformed or unexpected CSV rows.

Read the expected CSV member directly from the ZIP. Do not extract arbitrary archive paths into the filesystem.

Apply sensible limits to archive size, uncompressed content and row counts.

## 6. Completeness and data-quality validation

For a requested monthly archive, construct the expected UTC candle grid.

Verify:

- Every candle belongs to the requested symbol, interval and month.
- Timestamps are correctly aligned.
- Candle identities are unique.
- Rows are chronologically consistent.
- OHLCV constraints hold.
- No unexpected timestamps appear.
- No internal candle intervals are missing.

Report missing or duplicated candle identities explicitly.

Do not fabricate candles, forward-fill missing prices or interpolate gaps.

For this Stage 1B.2 proof of ingestion, a materially incomplete or invalid archive should fail validation before any database writes.

Keep the validation rules practical; do not build a general-purpose data-quality framework.

## 7. Atomic batch persistence

The existing `save_candle()` function manages its own transaction per observation.

That is insufficient for an all-or-nothing monthly archive import.

Extend the persistence layer to support a simple batch operation, for example:

`save_candles(connection, observations, mode="backfill")`

Requirements:

- Reuse the existing validation and version-selection logic.
- Avoid duplicating complex SQL across single-record and batch functions.
- Validate the entire archive before writing.
- Persist a complete archive within one short database transaction.
- Roll back the entire archive if any database write fails.
- Preserve the established atomic revision-history behaviour.
- Do not hold database locks during HTTP requests or ZIP parsing.
- Preserve concurrency safety and stale-observation detection.

Refactor `save_candle()` internally if necessary, but preserve its public behaviour and existing tests.

### Routine historical backfill policy

This stage implements ordinary historical backfill, **not historical revalidation**.

- Missing candle: insert it.
- Identical existing candle: leave its economic version unchanged.
- Changed existing candle: report an explicit conflict and fail the archive transaction without overwriting existing accepted data.
- Invalid observation: reject the archive without writing partial data.
- Stale observation: report explicitly; do not silently count it as successful.

Conflict detection must take place against the current database row under appropriate transaction locking, not solely through a preliminary unlocked query.

Historical revalidation that deliberately accepts changed provider values belongs to Stage 1C.

Do not compromise the A → B → A revision capabilities already implemented in Stage 1B.1.

## 8. Observation timestamps and provenance

Preserve accurate data provenance.

- `open_time` is market time.
- `observed_at` is the local time the complete provider response was received.
- `recorded_at` remains the database-side recording time.
- `source_kind` is `archive`.
- `source_url` identifies the original Binance archive.
- `source_sha256` identifies the exact downloaded ZIP body.

All observations from one downloaded archive may share the same response-received timestamp because they were acquired together.

Do not claim that historical candles downloaded today were available to Backtest Badger at their original market times.

An archived local file replay must not be treated as a new provider observation merely because it is parsed again.

Preserve existing version and observation-ordering semantics.

## 9. Raw artifacts and ingestion manifests

Introduce minimal local artifact storage under:

`artifacts/`

Suggested organisation:

- `artifacts/raw/`
- `artifacts/manifests/`

Use content-addressed filenames where useful so a revised download cannot silently overwrite earlier raw evidence.

Retain:

- Verified raw archive bytes.
- Associated checksum evidence.
- A small structured JSON ingestion manifest.

The manifest should record:

- Run identifier.
- Source URL and checksum.
- Market, interval and month.
- Download/observation time.
- Validation result.
- Expected and actual candle counts.
- Inserted, unchanged, conflicting and rejected counts.
- Any missing intervals.
- Database write outcome.
- Error category, when applicable.

No secrets or credentials should appear in artifacts.

Ensure artifacts are gitignored.

Do not implement cloud storage, a manifest database, an elaborate artifact manager or backup orchestration.

If the database commit succeeds but writing the final manifest fails, report the problem honestly. A rerun must remain safe.

## 10. Testing

Write focused tests covering:

### Archive parsing

- Valid pre-2025 millisecond timestamps.
- Valid post-2025 microsecond timestamps.
- Exact Decimal preservation.
- Correct 1h and 4h alignment.
- Valid close-time boundaries.
- Incorrect column counts.
- Invalid numeric values.
- Duplicate candles.
- Missing intervals.
- Wrong month or unexpected timestamps.
- Nonzero ignored provider fields.

### Download integrity

- Correct SHA-256 verification.
- Mismatched checksum.
- Malformed checksum.
- Corrupt ZIP.
- Unexpected archive member.
- Download timeout or HTTP error.
- Response and decompression size limits.

Mock or fixture external requests in automated tests. CI must not depend on Binance network availability.

### PostgreSQL integration

Use the existing disposable PostgreSQL integration-test infrastructure.

Verify:

- Entire month inserts atomically.
- Identical rerun creates no new candle versions.
- A failed import leaves the database unchanged.
- Conflicting existing observations are detected without overwrite.
- Partial transaction failure rolls back all archive rows.
- Existing Stage 1B.1 revision functionality still works.
- Database constraints remain intact.

Ensure tests never drop, truncate or reset the normal development database.

Do not inflate test counts with redundant cases.

## 11. Real-world validation

After passing local tests, perform a bounded end-to-end ingestion.

Run January 2025 native 4h ingestion for:

1. BTCUSDT.
2. ETHUSDT.

Prefer dry-run validation before actual persistence.

Verify:

- Checksums pass.
- Expected candle identities are present.
- Persisted row counts match validated input.
- Values retain exact Decimal precision.
- Source provenance is present.
- Re-running the same commands is idempotent.
- The final dataset contains no unexplained gaps.
- No unintended revisions were created.

Use only the local development PostgreSQL database configured in `.env`.

Never use the disposable integration-test database for permanent project data, and never use a production database.

Do not delete existing database data, volumes or schemas.

If networking is unavailable, report that limitation and complete the fixture-based tests instead. Do not invent successful live results.

Do not automatically expand beyond the specified month.

## 12. Documentation

Add one concise operational guide:

`docs/stage-01b2-archive-ingestion.md`

Include:

- How ingestion works.
- Exact CLI commands.
- How to perform a dry run.
- Database write behaviour.
- How completeness is checked.
- Where downloaded artifacts are stored.
- How failures and conflicting observations are handled.
- How to inspect ingested data.
- Actual live-test results and limitations.

Update `docs/architecture.md` and `docs/roadmap.md` to distinguish implemented ingestion functionality from what remains planned.

Preserve the existing Stage 1A design and Stage 1B.1 guide. Update them only when needed to document genuine implementation changes.

Archive this exact prompt under:

`prompts/stage-01-market-data/003-historical-archive-ingestion.md`

Do not alter previous prompts.

## 13. Explicit exclusions

Do not implement:

- Full historical backfill from 2017.
- Automatic multi-month download orchestration.
- Binance REST candle ingestion.
- Incremental refresh or scheduling.
- Historical revalidation workflows.
- Derived 4h candle aggregation.
- Technical indicators.
- ML models.
- Backtesting.
- Paper trading.
- Dashboards or website development.
- AWS deployment.
- Generalised multi-exchange frameworks.

Do not access the original `crypto-trading-platform` repository.

Do not commit or push changes.

## 14. Completion report

At completion, report:

1. Files created and modified.
2. CLI usage examples.
3. Dependencies introduced and their justification.
4. Archive validation behaviour.
5. Batch transaction and conflict-handling behaviour.
6. Unit and PostgreSQL integration-test results.
7. Actual January 2025 BTCUSDT and ETHUSDT ingestion results.
8. Final stored candle counts and gap counts.
9. Repeat-ingestion/idempotency results.
10. Remaining risks and anything deferred to Stage 1B.3.

Run pytest, Ruff lint and formatting checks.

Review the implementation for unnecessary complexity.

**Stop after Stage 1B.2. Do not begin the complete historical backfill until reviewed.**
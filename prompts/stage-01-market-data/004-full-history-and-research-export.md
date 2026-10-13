# Backtest Badger — Stage 1B.3: Complete Historical Coverage & Research Dataset

You are acting as a senior quantitative data engineer specialising in reproducible market-data pipelines, PostgreSQL and data integrity.

Implement **Stage 1B.3 — Full Historical Coverage and Research Dataset**.

The objective is to extend our proven single-month Binance ingestion into a complete, validated and reproducible historical dataset for quantitative research.

**Minimum complexity. Maximum correctness.**

## 1. Read existing project

Repository: `~/Code/backtest-badger`

Read and understand:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-01a-market-data-design.md`
- `docs/stage-01b1-persistence.md`
- `docs/stage-01b2-archive-ingestion.md`
- `src/backtest_badger/archives.py`
- `src/backtest_badger/ingestion.py`
- `src/backtest_badger/candles.py`
- Existing CLI and integration tests.

Stage 1B.2 has been committed and validated against actual Binance data.

The existing database contains January 2025 native 4h observations for BTCUSDT and ETHUSDT.

Preserve those observations and their provenance.

Do not modify the historical `crypto-trading-platform` repository.

## 2. Scope and historical coverage

Primary provider: Binance Spot.

Markets:

- BTCUSDT
- ETHUSDT

Timeframe:

- Native 4h candles only for the full backfill.

Our objective is to acquire the **complete available historical 4h archive dataset** for both markets.

Stage 1A observed that both markets' first accessible candle opened at:

`2017-08-17 04:00 UTC`

The initial intended historical range is:

- Start month: `2017-08`
- End month: `2026-09` inclusive

Verify that the September 2026 monthly archives are available before attempting them.

If newer complete monthly archives are available, do not silently expand the specified backfill range. Additional months should require explicit selection.

Do not include incomplete October 2026 data in this stage.

Stage 1C will handle the recent tail through daily archives and REST.

## 3. Handle the initial partial month correctly

The current monthly validator expects the entire calendar month to be populated.

This is appropriate for ordinary months but rejects the verified initial trading month.

Implement a minimal initial-listing-boundary policy.

Requirements:

1. Explicitly recognise August 2017 as the special first archive month for these markets.
2. Verify that the first observation agrees with independent Stage 1A evidence and, where practical, the Binance public REST historical starting point.
3. Require all subsequent 4h intervals through the end of that month to be present.
4. Record the verified first open time in coverage metadata.
5. Do not invent missing candles before the market began trading.
6. Do not assume this proves Binance had no earlier trading data outside the verified source.
7. Continue requiring full calendar-month coverage for all later months.
8. Do not allow arbitrary partial months to pass validation.

Keep the special-case policy small and explicit rather than creating a general market-listing framework.

## 4. Bounded multi-month ingestion

Extend the existing archive ingestion functionality to support a range of months.

Provide a CLI command with explicit boundaries, such as:

`badger backfill-history --symbol BTCUSDT --interval 4h --start-month 2017-08 --end-month 2026-09`

Requirements:

- Process archives chronologically.
- Process one month at a time.
- Reuse the existing downloader, checksum verification, parser and persistence logic.
- Do not duplicate monthly ingestion implementations.
- Preserve the existing `badger ingest-archive` command.
- Keep memory usage bounded.
- Persist each validated archive as one atomic transaction.
- Do not use one enormous transaction for the full historical range.
- Avoid asynchronous workers, job queues and general orchestration frameworks.
- Provide clear progress reporting by month.
- Report inserted, unchanged, conflicting, stale and failed observations.
- Support a safe restart after an interrupted run.
- Do not interpret 404 responses as evidence of missing candles.

Allow small test ranges before processing the full history.

A failed month should cause a clear failure result. By default, stop and allow the user to retry after investigation rather than silently proceeding and reporting incomplete history as success.

## 5. Idempotency and historical conflicts

Preserve the established Stage 1B.2 backfill policy.

For every monthly archive:

- New valid observations are inserted.
- Identical existing observations remain unchanged.
- Valid but different existing observations are reported as conflicts.
- Stale changed observations are reported explicitly.
- A conflicting archive rolls back its entire month's writes.
- Existing candle versions and provenance are never silently overwritten.

Do not automatically accept historical revisions in this stage.

The deliberate historical revalidation process belongs to Stage 1C.

Repeated full-history imports must not create new revisions when provider economic values are unchanged.

Reusing existing downloaded raw files is permissible only when their provenance and acquisition semantics are preserved. A cached file must not be misrepresented as a newly observed provider response.

Do not introduce a new database schema unless a concrete blocker makes it necessary.

## 6. Historical completeness reporting

Implement a clear coverage report covering the selected markets and historical range.

For each market, report:

- First observed candle.
- Last observed candle.
- Expected candles within verified coverage.
- Actual stored candles.
- Missing candle count.
- Duplicate identity count, if applicable.
- Number of current versions.
- Number of historical revisions.
- Unavailable archive months.
- Failed or unresolved imports.

Treat the verified initial partial month correctly.

Use explicit UTC boundaries.

Continuity must be checked against the stored data, not merely inferred from successful archive downloads.

Do not interpolate prices, invent zero-volume candles or silently exclude gaps.

The final report must distinguish:

- Complete historical coverage for the declared verified range.
- Incomplete coverage.
- Unverified periods outside the declared range.

## 7. Reproducible dataset export

Implement a minimal mechanism to export a frozen historical research dataset from PostgreSQL.

The initial format should be a straightforward CSV containing exact string representations of Decimal prices and volumes.

Avoid pandas, PyArrow or Parquet dependencies at this stage unless there is a compelling demonstrated requirement.

Include:

- Market identity.
- Candle interval.
- UTC candle open time.
- OHLC values.
- Volume and trade fields.
- Accepted candle version.
- Original observation timestamp.
- Source kind.
- Source URL and source SHA-256.

Export BTCUSDT and ETHUSDT from a **single consistent database snapshot** using a read-only REPEATABLE READ transaction.

Do not read the markets in separate transactions if that would allow a correction between exports to produce inconsistent snapshot state.

Order rows deterministically.

Produce a small JSON metadata manifest containing:

- Dataset identifier.
- Export creation time.
- Market and interval selections.
- Start and exclusive end timestamps.
- First and last observed timestamps.
- Row counts per market.
- Completeness results.
- Selected source/version policy.
- Export schema version.
- A SHA-256 hash of the actual exported dataset bytes.
- Relevant implementation revision information when available.

The CSV contents and hash must be deterministic for unchanged database inputs, regardless of when the export command runs. Keep run timestamps in the separate manifest.

Write exports safely to ignored local artifacts and never silently overwrite an existing immutable export.

### Incomplete datasets

By default, a research export should fail if there are unexplained gaps in the requested coverage.

Permit an explicitly acknowledged partial export only if clearly labelled as incomplete and accompanied by the missing-interval report.

### Historical reproducibility

The frozen export must remain unchanged if the canonical database is later updated.

Do not rely solely on recording a database timestamp or content hash without retaining the actual dataset bytes.

Do not claim that today's backfilled dataset reproduces exactly what Binance published at every historical moment.

## 8. Local artifact storage

Continue using the existing ignored `artifacts/` directory.

Reuse existing raw and manifest storage conventions.

Add exports under:

`artifacts/exports/`

Do not create cloud storage, S3 infrastructure, a backup service or a new artifacts database.

Retain verified archive evidence and avoid overwriting older evidence.

Document that these locally stored artifacts are not yet durable off-machine backups.

## 9. Testing

Extend the existing tests with focused coverage of the new functionality.

Important cases:

- Correct acceptance of the verified initial partial month.
- Rejection of an arbitrary later partial month.
- Missing intervals within the first trading month.
- Missing full months in a requested range.
- Correct chronological month iteration across year boundaries.
- Idempotent re-running of an already imported month.
- Interrupted backfill followed by safe restart.
- Conflicting existing data without overwriting.
- Aggregated completeness reporting.
- UTC interval-grid correctness.
- Consistent multi-market dataset snapshots.
- Exact Decimal export values.
- Deterministic CSV contents and hashes.
- Export refusal when required data is missing.
- Explicitly acknowledged incomplete exports.
- Export immutability after a database correction.

Use fixture-based or mocked network tests.

Continue using isolated PostgreSQL integration tests for database behaviour.

Do not make CI depend on live Binance availability.

Avoid introducing large numbers of trivial or redundant tests.

## 10. Controlled live validation

Before downloading the full historical range, perform bounded checks.

First validate:

1. August 2017 BTCUSDT and ETHUSDT native 4h archives.
2. A complete month from before 2025.
3. January 2025, already stored.
4. One recent completed month.

Verify archive checksums, timestamps and database persistence.

Confirm that previously stored January 2025 data remains unchanged.

If those checks pass, execute the requested full historical backfill for BTCUSDT and ETHUSDT within the explicit date range.

Use the existing local development PostgreSQL configured in `.env`.

Do not reset the database, delete Docker volumes or touch production resources.

If provider availability, database conflicts or unverified listing boundaries prevent completion, stop safely and report the precise blocker. Do not weaken validation simply to achieve a complete dataset.

After a successful backfill:

- Run an independent PostgreSQL completeness check.
- Confirm the count of current candle rows for each market.
- Confirm no unintended historical revisions.
- Create a frozen dataset export covering the verified range.
- Verify the export's row counts and hash.

Do not download native 1h history during this stage.

## 11. Documentation

Create:

`docs/stage-01b3-full-history.md`

Document:

- Historical start and end boundaries.
- Initial partial-month treatment.
- CLI commands and examples.
- Restart and recovery behaviour.
- Archive and database completeness checks.
- Data export format and reproducibility.
- Actual live backfill results.
- Known limitations.

Update:

- `docs/roadmap.md`
- `docs/architecture.md`
- Relevant operational documentation only where necessary.

Preserve previous historical Codex prompts.

Archive this exact prompt at:

`prompts/stage-01-market-data/004-full-history-and-research-export.md`

Avoid additional documentation that duplicates existing guides.

## 12. Explicit exclusions

Do not implement:

- Binance REST ingestion.
- Daily archive ingestion.
- Incremental updates.
- Historical provider revalidation.
- Automatic scheduling.
- Native 1h full-history downloading.
- Derived 4h resampling.
- Technical indicators.
- Machine learning.
- Backtesting.
- Paper trading.
- Dashboards or website work.
- AWS deployment.
- Unnecessary exchange/provider abstractions.

Do not access the original `crypto-trading-platform` repository.

Do not commit or push changes.

## 13. Completion report

Provide:

1. Files created and modified.
2. CLI usage examples.
3. Historical first/last candle timestamps.
4. Per-market candle counts.
5. Missing and unavailable interval counts.
6. Archive success/failure counts.
7. Idempotency and revision results.
8. Export filenames, row counts and SHA-256 hashes.
9. Unit and PostgreSQL integration-test results.
10. Remaining issues or limits.

Clearly distinguish observed results from assumptions.

**Stop after Stage 1B.3. Do not begin Stage 1C without review.**
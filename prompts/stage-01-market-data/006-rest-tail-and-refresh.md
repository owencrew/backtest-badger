# Backtest Badger — Stage 1C.1: Incremental REST Ingestion & Recent Candle Refresh

Act as a senior quantitative data engineer specialising in Python, PostgreSQL, financial market data and reproducible research.

Implement **Stage 1C.1 — Incremental Binance REST Ingestion and Recent Candle Refresh**.

The goal is to extend the existing historical data platform so that it can safely acquire newly closed candles, catch up after periods without ingestion, refresh recent observations and preserve legitimate provider revisions.

**Engineering principle: Minimum complexity. Maximum correctness.**

Do not proceed to Stage 1C.2 or Stage 2.

## 1. Inspect the existing implementation

Repository: `~/Code/backtest-badger`

Read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-01a-market-data-design.md`
- `docs/stage-01b1-persistence.md`
- `docs/stage-01b2-archive-ingestion.md`
- `docs/stage-01b3-full-history.md`
- `src/backtest_badger/candles.py`
- `src/backtest_badger/archives.py`
- `src/backtest_badger/ingestion.py`
- `src/backtest_badger/history.py`
- `src/backtest_badger/research.py`
- `src/backtest_badger/cli.py`
- Existing migrations and tests.

Preserve existing behaviour and public APIs wherever practical.

Stage 1B.3 has been completed and committed.

The development database contains:

- 19,955 native 4h BTCUSDT candles.
- 19,955 native 4h ETHUSDT candles.
- Complete acquisition evidence through September 2026.
- 36 known missing or excluded identities per market.
- No accepted historical revisions.

The original anomalous observations and their evidence must remain preserved.

A frozen historical research export has also been created under:

`artifacts/exports/binance-4h-history-v1/`

It contains 39,910 rows, is explicitly labelled incomplete, and has SHA-256:

`e6052b8cca7bca00999ca4d7429af67db019c8ef261fa2b499f0fd6774dcd13b`

Do not modify this frozen export or its manifest.

## 2. Source and market scope

Use Binance Spot's public market-data-only REST API:

`https://data-api.binance.vision/api/v3/klines`

Supported markets:

- BTCUSDT
- ETHUSDT

Primary interval:

- Native 4h only for this increment.

Use public, unauthenticated market-data requests.

Do not require API keys or trading permissions.

Consult the current Binance Spot REST documentation before implementation.

Relevant properties:

- `symbol` and `interval` identify the requested series.
- `startTime` and `endTime` are UTC timestamps.
- `timeZone=0` selects UTC candle boundaries.
- Default API response timestamps use milliseconds.
- Maximum response size is 1,000 klines.
- Each kline has twelve documented fields.

Do not use `uiKlines`, futures endpoints, WebSocket streams or derived candles.

## 3. CLI command

Add a simple command such as:

`badger sync-recent --symbol BTCUSDT --interval 4h`

Support both markets by running the command separately, or allow a small explicit multi-symbol option if that is materially simpler.

Provide:

- Default recent synchronisation.
- `--dry-run` for validation without database writes.
- An optional explicit UTC start time for bounded catch-up and recovery.
- Clear progress, coverage and error reporting.

Preserve all existing CLI commands.

Do not implement automatic scheduling, daemons or background jobs.

## 4. Closed-candle eligibility

Never persist a still-forming candle.

Use a configurable/default **60-second settling delay**.

A candle is eligible only when:

`open_time + interval_duration + settling_delay <= fixed_run_time`

Capture one fixed UTC run time before acquiring pages.

Derive the eligible exclusive range boundary from it, using integer timestamp arithmetic.

Requirements:

- Exclude current incomplete candles even if Binance returns them.
- Respect exact UTC 4h boundaries.
- Avoid floating-point timestamp calculations.
- Test behaviour exactly before, at and after the closing/settling threshold.
- Do not assume Binance guarantees finality after 60 seconds.

The settling delay is our provisional research policy, not a provider guarantee.

## 5. Catch-up and refresh-window policy

A normal sync must do two things:

1. Fetch newly eligible candles since the latest stored observation.
2. Revisit a rolling seven-day overlap to detect recent corrections and fill recent gaps.

Calculate the default start as the earlier of:

- The next expected opening time after the latest stored candle.
- The start of the seven-day refresh window.

This ensures a system left offline for more than seven days attempts to catch up rather than silently skipping missing history.

However:

- Put a sensible explicit bound on automatic catch-up.
- If the required catch-up exceeds that bound, report it and require an explicit bounded recovery command.
- Do not automatically scan all history back to 2017.
- If there is no stored candle for a selected market, require a clearly defined starting boundary rather than guessing.
- Keep the existing 2017–2021 provider-gap investigation outside the normal refresh operation.

An explicit start-time override should permit controlled recent backfills.

Do not silently use the latest stored timestamp as evidence that all earlier candles exist.

## 6. REST acquisition and pagination

Implement a minimal REST kline acquisition module, reusing existing HTTP conventions where appropriate.

Requirements:

- Fixed requested time window.
- Explicit `symbol`, `interval`, `timeZone=0`, `startTime`, `endTime` and `limit`.
- At most 1,000 rows per page.
- Bounded network timeouts and HTTP response sizes.
- Retry transient transport/server failures with bounded backoff.
- Handle HTTP 429 and 418 conservatively, respecting `Retry-After` when supplied.
- Do not retry indefinitely or aggressively poll the API.
- Observe and report rate-limit diagnostics when available.
- Use a conservative request pace.

Pagination must advance using:

`last_returned_open_time + interval_duration`

Never advance using local wall-clock time, an assumed close timestamp or the requested page size.

Reject or report:

- Duplicate identities.
- Non-advancing pages.
- Out-of-order response rows.
- Malformed responses.
- Unexpected timestamps.
- Empty pages before a requested range is adequately resolved.

An empty page is not proof that no trading occurred.

The final requested interval must always be compared with the expected UTC candle grid.

## 7. REST parsing and validation

Implement strict conversion of native REST klines into the existing `CandleObservation` representation.

Requirements:

- Validate the expected twelve-element structure.
- Preserve economic fields as exact `Decimal` values from provider strings.
- Parse trade counts as integers.
- Use aware UTC timestamps.
- Validate inclusive millisecond close boundaries.
- Validate alignment and OHLCV consistency.
- Do not accept malformed economic fields.
- Do not interpolate or forward-fill absent observations.
- Do not treat the ignored final field as an economic field.

The regular recent-data workflow should not silently accept malformed historical-style candle closes.

If a new anomaly class appears in recent responses, retain evidence and report it for investigation.

Do not manufacture replacement candles.

## 8. Observation provenance and raw evidence

Preserve the distinction between:

- Market opening time.
- Provider-response acquisition time.
- Database recording time.

For REST observations:

- `source_kind = "rest"`
- `source_url` records the exact public kline request.
- `source_sha256` is SHA-256 of the exact received response body.
- `observed_at` is the locally recorded complete-response acquisition time.

All observations from one response page may share an acquisition timestamp.

Do not claim that the REST response time is Binance's original candle publication time.

Store bounded raw REST response evidence and structured run/page manifests under the existing ignored `artifacts/` directory.

Retain:

- Request parameters.
- Actual response URL.
- Response acquisition timestamp.
- SHA-256.
- Accepted and rejected identities.
- Coverage diagnostics.
- Persistence outcomes.
- Error categories.

Reuse existing manifest and artifact utilities where practical. Avoid a separate generic storage system.

## 9. Safe persistence of recent revisions

The existing `save_candle()` API already supports:

- New insertions.
- Identical confirmations.
- Atomic revisions.
- Historical-version preservation.
- Stale-observation rejection.
- Equal-observation-time conflict detection.

Reuse its established SQL and locking behaviour.

For practical REST page writes, extend the batch API to support an explicit recent-refresh mode if appropriate.

Requirements:

- Preserve `save_candles(..., mode="backfill")` behaviour.
- Validate all observations in a page before writing.
- Use one bounded database transaction per page or small batch.
- No database transaction may span an HTTP request.
- Insert missing valid candles.
- Keep identical versions and original provenance unchanged.
- Accept legitimate newer changed observations in the authorised recent-refresh range.
- Copy superseded values and provenance to `candle_revision`.
- Increment the current version correctly.
- Reject stale changed observations without overwriting newer accepted data.
- Treat equal-time changed observations as explicit conflicts.
- Preserve the A → B → A revision history behaviour.
- Avoid partial writes from a failed page transaction.

Do not automatically revise observations outside the authorised recent-refresh range.

Do not turn the complete historical database into an automatically mutable dataset.

If a response contains a significant archive-versus-REST disagreement, record old and new values and the source evidence. Do not hide the disagreement simply because the newer acquisition timestamp permits a database revision.

Consider appropriate safeguards for unusually large or widespread changes, but avoid an elaborate approval system.

## 10. Explicit separation from historical revalidation

Stage 1C.1 is a routine operational refresh of recent market data.

It must not automatically:

- Revisit old September 2017 source anomalies.
- Fill old historical maintenance gaps using synthetic values.
- Rewrite years of accepted archive data.
- Treat a newer REST acquisition timestamp as proof of economic truth.

Stage 1C.2 will implement deliberate bounded historical revalidation.

Keep that distinction obvious in the CLI, documentation and persistence calls.

## 11. Gap detection and freshness

After each sync, produce an understandable summary per market:

- Fixed run time.
- Requested start and exclusive end.
- Latest eligible candle opening time.
- Latest stored candle opening time.
- Inserted candles.
- Unchanged candles.
- Revised candles.
- Stale/conflicting observations.
- Missing eligible candle identities in the requested range.
- Failed or incomplete pages.
- Freshness/staleness status.

Use actual database coverage checks, not just response counts.

Do not describe a requested range as complete if there are unexplained missing intervals.

Keep historical known gaps visible in the existing historical coverage reports without causing every recent sync to fail because of issues from 2017.

A network failure must not erase previously accepted data.

A failed or partial sync must be reported honestly, even if earlier pages committed successfully.

## 12. Testing

Write focused unit and disposable PostgreSQL integration tests.

Cover:

- UTC boundary calculations.
- Settling delay.
- Current candle exclusion.
- One-page and multi-page requests.
- Exact pagination boundary.
- Non-advancing and empty pages.
- Incorrect response order.
- Wrong number of JSON fields.
- Decimal precision.
- Malformed close timestamps.
- HTTP timeouts.
- Retry limits.
- 429/418 rate-limit handling.
- Recent catch-up after an interruption.
- Seven-day overlap behaviour.
- Explicit bounded recovery.
- Missing candle diagnosis.
- First insertion.
- Identical repeat.
- A → B → A revisions.
- Stale and equal-time conflicts.
- Atomic rollback.
- Concurrent writers.
- Preservation of earlier archive provenance.
- Immutable frozen dataset exports.
- No regression to strict/gap-tolerant historical archive ingestion.

Use mocked HTTP responses for automated tests.

CI must not require live Binance access.

Use the existing isolated PostgreSQL integration-test infrastructure.

Do not introduce redundant test cases merely to increase the count.

## 13. Controlled live validation

After automated tests pass, perform bounded live validation using the local development PostgreSQL configured in `.env`.

Use the first new range after September 2026 historical coverage through the current eligible UTC cutoff.

Validate BTCUSDT and ETHUSDT separately.

First perform dry runs.

Then perform real syncs.

Verify:

1. New recent candles are stored.
2. Current incomplete candles are excluded.
3. Recent stored coverage is reconciled against the expected grid.
4. Previously imported historical candles are not deleted.
5. Ordinary identical repeats create no unnecessary revisions.
6. Existing historical source-gap diagnostics remain unchanged.
7. The frozen Stage 1B.3 export is unchanged, including its SHA-256.

Do not manufacture a genuine economic revision merely to demonstrate that versioning works.

Test revision scenarios using isolated PostgreSQL fixtures.

If real Binance data differs from existing recent observations, record and investigate the actual discrepancy.

If live provider access is unavailable, report the blocker rather than inventing successful results.

## 14. Documentation

Create:

`docs/stage-01c1-rest-tail-and-refresh.md`

Document:

- API selection.
- Exact CLI commands.
- UTC cutoff policy.
- Pagination rules.
- Catch-up and overlap.
- Correction/version-selection policy.
- Gap and freshness diagnostics.
- Raw evidence and manifests.
- Actual live validation results.
- Known limitations.

Update the roadmap and architecture to reflect only implemented functionality.

Update the existing design where genuinely required, without rewriting past decisions.

Archive this exact substantive prompt as:

`prompts/stage-01-market-data/006-rest-tail-and-refresh.md`

Do not automatically create a Field Note. Create one only if the work produces a genuinely interesting new engineering or research discovery.

## 15. Explicit exclusions

Do not implement:

- Stage 1C.2 historical revalidation workflows.
- Automatic daily archive processing.
- WebSocket streaming.
- Automatic scheduling or background services.
- Kubernetes, AWS or cloud deployment.
- Additional assets or exchanges.
- Native 1h full-history imports.
- Derived candle aggregation.
- Technical indicators.
- ML training.
- Backtesting.
- Forward predictions.
- Paper trading.
- Website/frontend functionality.

Do not access or modify the old `crypto-trading-platform` project.

Do not commit or push changes.

## 16. Completion report

Report:

1. Files created and changed.
2. CLI commands.
3. Source/API validation decisions.
4. Catch-up and refresh behaviour.
5. Final recent candle counts and timestamps.
6. Missing interval and freshness diagnostics.
7. Inserted, unchanged, revised, stale and conflicting counts.
8. Provenance and revision-history evidence.
9. Regression/unit/integration test results.
10. Any provider anomalies, unresolved issues or deferred functionality.

Run pytest, Ruff lint and Ruff formatting checks.

Review the implementation for unnecessary complexity.

**Stop after Stage 1C.1. Do not start historical revalidation or quantitative modelling without review.**
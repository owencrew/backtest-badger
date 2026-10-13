# Backtest Badger — Stage 1C.2: Controlled Historical Revalidation

Act as a senior quantitative data engineer specialising in auditable market-data pipelines, PostgreSQL, concurrency and reproducible research.

Implement **Stage 1C.2 — Controlled Historical Revalidation**.

Our objective is to explicitly re-examine historical Binance candles, identify changes against accepted database values, and safely apply reviewed corrections while preserving all previous versions and research artifacts.

**Principle: Minimum complexity. Maximum correctness.**

Do not implement quantitative modelling or begin Stage 2.

## 1. Inspect existing code

Repository: `~/Code/backtest-badger`

Read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-01a-market-data-design.md`
- `docs/stage-01b1-persistence.md`
- `docs/stage-01b2-archive-ingestion.md`
- `docs/stage-01b3-full-history.md`
- `docs/stage-01c1-rest-tail-and-refresh.md`
- `src/backtest_badger/candles.py`
- `src/backtest_badger/rest.py`
- `src/backtest_badger/recent.py`
- `src/backtest_badger/research.py`
- The existing CLI, migrations and tests.

The repository has been committed and pushed after Stage 1C.1.

Current observed data state at the end of Stage 1C.1:

- BTCUSDT: 20,030 stored native 4h candles.
- ETHUSDT: 20,030 stored native 4h candles.
- Historical source gaps: 36 per market.
- Recent October coverage: complete to the recorded eligibility cutoff.
- No genuine economic revisions observed so far.
- 306 tests passed in the previous stage.

The frozen historical export exists under:

`artifacts/exports/binance-4h-history-v1/`

Its CSV SHA-256 is:

`e6052b8cca7bca00999ca4d7429af67db019c8ef261fa2b499f0fd6774dcd13b`

Do not modify it.

## 2. Scope

Support:

- Binance Spot BTCUSDT and ETHUSDT.
- Native 4h observations.
- Explicit UTC-aligned historical start and exclusive end timestamps.
- A bounded maximum of 30 days per revalidation operation.

Use the existing public market-data-only REST endpoint and parser, with necessary small refactoring to reuse acquisition logic.

Do not automatically scan nine years of history.

Do not add a scheduler, provider abstraction, database migration or new dependencies unless a concrete requirement makes them unavoidable.

## 3. CLI workflow

Implement a clear two-phase operation.

### Phase A — Review

Example:

`badger revalidate-history --symbol BTCUSDT --interval 4h --start 2026-09-01T00:00:00Z --end 2026-09-03T00:00:00Z`

Review must be read-only.

The command should:

1. Fetch the explicit historical range.
2. Validate responses using existing REST rules.
3. Compare every returned observation with current canonical PostgreSQL values.
4. Identify missing, unchanged, changed and invalid observations.
5. Preserve raw response bytes and provenance.
6. Create a human-readable summary and machine-readable review plan.
7. Exit without modifying any candle or observation watermark.

The default must always be review-only.

### Phase B — Apply

Provide an explicit command or flag to apply a previously produced review plan.

Suggested interface:

`badger apply-revalidation --plan artifacts/revalidation/plans/<plan-id>.json --approve-changes`

The exact CLI structure can differ if a simpler design is more maintainable.

Requirements:

- Explicit user action is required.
- Apply precisely the previously reviewed provider responses.
- Do not fetch fresh data and silently substitute new observations.
- Validate the retained raw bytes and SHA-256 against the review plan.
- Reparse the original payload using the intended parser version.
- Preserve the acquisition timestamp originally recorded during review.
- Confirm the current database values and versions still match the state reviewed.
- If relevant values changed after review, reject the application and require a fresh review.
- Validate all selected observations before the transaction begins.

Do not build an elaborate multi-user approvals system.

## 4. Comparison behaviour

For each expected historical identity, distinguish:

- Missing from the provider response.
- Missing from PostgreSQL but valid in the provider response.
- Present and economically identical.
- Present with different economic values.
- Structurally invalid provider observation.
- Changed database state since an earlier review.

Economic equality must continue to use all nine existing economic fields.

Use exact Decimal comparisons.

Produce a concise difference report with:

- Market and candle opening timestamp.
- Old and proposed economic values.
- Changed fields.
- Current and proposed source provenance.
- Existing version.
- Old and new observation timestamps.
- Source hashes.
- Any validation warnings.

Do not describe a newly acquired historical observation as proof that Binance originally published the same value at the candle's market time.

## 5. Historical revision persistence

Reuse the existing version-preserving SQL.

Introduce the smallest necessary explicitly authorised historical-revalidation mode.

Keep the existing modes unchanged:

- `backfill`: no revisions.
- `recent-refresh`: revisions restricted to the recent seven-day authority.

Historical revalidation must never be triggered by ordinary `sync-recent` or `backfill-history`.

When an approved historical observation differs from the current accepted version:

1. Lock and verify the existing candle.
2. Verify the review plan's expected version and economic state.
3. Insert the superseded current row into `candle_revision`.
4. Update current economic values and provenance.
5. Increment the current version.
6. Commit atomically.

Preserve A → B → A version history.

A failed application must not leave a partial revision.

Use a bounded transaction for the reviewed range and ensure deterministic row-lock ordering.

Do not hold database locks during HTTP requests.

Handle stale or equal-time conflicts explicitly rather than overriding the existing version-selection policy.

## 6. Missing historical candles

An absent database identity is not necessarily an invitation to fill it.

Recall the Stage 1B.3 investigation:

- Some early historical Binance records have abnormal closing timestamps.
- Some provider observations are zero-duration or otherwise incomplete.
- Regularly aligned candles can still contain trading interruptions.
- Historical source diagnostics must remain visible.

A missing candle may be inserted only if the proposed observation passes all established eligibility, timestamp, OHLCV and provenance checks and is explicitly included in an approved plan.

Do not:

- Fabricate zero-volume candles.
- Treat a zero-duration placeholder as a full 4h observation.
- Normalize malformed timestamps automatically.
- Resample 1h data into a replacement 4h candle.
- Clear historical anomaly records merely because another source returns an identity.

Retain or update historical investigation notes when a source discrepancy is resolved, keeping the original evidence.

## 7. Reviewed plan integrity

Use a lightweight plan stored under ignored local artifacts.

For example:

`artifacts/revalidation/plans/`

The plan should identify:

- Selected symbol and UTC bounds.
- Acquisition timestamp.
- Parser/implementation version.
- Original request URLs.
- Raw response paths and SHA-256 values.
- Observations and exact proposed changes.
- Database values and versions at review time.
- Missing/invalid observations.
- Review status.
- A fingerprint of the reviewed content.

The apply operation must reject:

- Altered or missing response bytes.
- Invalid or incompatible review plans.
- A mismatch between reviewed and current database values.
- Expired or inappropriate revision authority, where applicable.
- Duplicate or out-of-range candle identities.
- Partial or malformed provider pages.

Avoid treating an editable JSON file alone as cryptographic authorisation. It is local review evidence; explicit CLI approval and revalidation of source bytes/current database state are required.

No new approval-service infrastructure.

## 8. Interaction with frozen research datasets

This is scientifically important.

An accepted correction changes the canonical candle, but it must never rewrite an existing frozen research export.

Verify:

- Previous dataset CSV bytes remain unchanged.
- Existing export hashes remain unchanged.
- Older candle versions remain queryable.
- A newly created dataset export can reflect updated canonical values.
- Both datasets remain distinguishable by their content hashes and manifests.

Do not update the original Stage 1B.3 frozen export.

Historical revalidation does not imply that previous research can be silently rewritten with new inputs.

## 9. Diagnostics and failure handling

Produce an understandable final report including:

- Selected range.
- Provider observations inspected.
- Identical candles.
- Proposed revisions.
- Approved revisions applied.
- Missing observations inserted.
- Invalid or absent source identities.
- Conflicts/stale attempts.
- Rollback or commit outcome.
- Source and plan artifact paths.

Preserve the previous values and their original provenance.

Use clear nonzero exit codes for unsafe or unsuccessful applications.

Do not emit credentials or raw database connection details.

## 10. Testing

Add focused tests covering:

- Review mode never modifying the database.
- Exact Decimal difference detection.
- Missing-versus-revised identity classification.
- Correct source hashes and provenance.
- Original observation time preserved between review and apply.
- A changed source response not being silently substituted.
- Changed canonical data between review and apply.
- A → B → A revision history.
- Identical observations not creating revisions.
- Stale and equal-time conflicts.
- Atomic rollback.
- Existing row concurrency safety.
- Missing valid historical identity insertion.
- Invalid historical provider observations not being inserted.
- Preservation of prior anomaly evidence.
- Frozen export immutability.
- Existing recent-refresh authority remaining restricted to seven days.
- Historical backfill remaining conflict-rejecting.

Use mocked provider responses and the existing disposable PostgreSQL integration-test infrastructure.

Do not make CI depend on Binance network availability.

Avoid redundant tests.

## 11. Controlled live verification

Do not manufacture a real provider correction.

First use a clean, small historical range, for example two days in September 2026.

Run review mode against the actual existing development database and confirm that identical observations are identified without writing changes.

Then inspect an early historically anomalous period such as 2017-09-06 in review-only mode.

Record what the current REST endpoint actually returns.

If it contains a malformed or zero-duration provider observation, reject that observation and retain its evidence. Do not force the plan to succeed or write a replacement.

Verify actual application mechanics using the disposable integration-test database and controlled synthetic observations.

A harmless live apply of a reviewed identical range is acceptable only if the operation is demonstrably safe; no live historical economic revision is required for acceptance.

Confirm:

- Historical stored rows have not been unexpectedly modified.
- No unapproved revisions have occurred.
- Existing source diagnostics remain available.
- The frozen Stage 1B.3 export and hash remain unchanged.

## 12. Documentation

Create:

`docs/stage-01c2-historical-revalidation.md`

Document:

- Review and apply commands.
- Exact approval semantics.
- Revision/versioning rules.
- Source comparison limitations.
- Atomic transaction behaviour.
- Missing and invalid historical candle policy.
- Recovery after failures.
- Actual live review results.
- Known limitations.

Update `docs/architecture.md` and `docs/roadmap.md` to reflect actual implementation status.

Archive the exact substantive prompt at:

`prompts/stage-01-market-data/007-historical-revalidation.md`

Create a Field Note only if the work uncovers a genuinely new, evidence-backed research or engineering lesson.

## 13. Explicit exclusions

Do not implement:

- Automated historical revalidation.
- Scheduled ingestion.
- Full-history rescans.
- Additional exchanges.
- 1h resampling or synthetic 4h replacements.
- A separate observation database.
- Database migrations unless essential.
- ML, trading signals or backtesting.
- Paper trading or live trading.
- Website/backend deployment.
- An approval UI or multi-user review system.

Do not access the original `crypto-trading-platform` repository.

Do not commit or push changes.

## 14. Completion report

Report:

1. Files created and modified.
2. Review and apply CLI examples.
3. Comparison and revision policies.
4. Review-plan integrity checks.
5. Live historical observations inspected.
6. Genuine changes found, if any.
7. Test results.
8. Preservation of existing canonical data and frozen exports.
9. Remaining limitations and potential simplifications.

Run pytest, Ruff lint, Ruff formatting and `git diff --check`.

**Stop after Stage 1C.2. Do not begin Stage 2 without review.**
# Backtest Badger — Stage 1B.3 Follow-up: Historical Data Anomalies and Backfill Recovery

Act as a senior quantitative data engineer. Review and resolve the historical-data ingestion blocker discovered during Stage 1B.3.

The objective is to acquire as much genuine Binance history as possible **without fabricating observations, weakening economic validation, or allowing isolated historical defects to block unrelated data acquisition**.

Principle: Minimum complexity. Maximum correctness.

## 1. Review the project

Read:

- `AGENTS.md`
- `docs/stage-01a-market-data-design.md`
- `docs/stage-01b2-archive-ingestion.md`
- `docs/stage-01b3-full-history.md`
- `src/backtest_badger/archives.py`
- `src/backtest_badger/ingestion.py`
- `src/backtest_badger/history.py`
- `src/backtest_badger/candles.py`
- Existing coverage/export functionality and tests.

Stage 1B.3 is implemented but its full historical backfill stopped at BTCUSDT September 2017.

Do not modify existing accepted observations or reset the database.

## 2. Known problem

For BTCUSDT September 2017 native 4h candles:

- ZIP checksum passes.
- Archive has 179 observations instead of the expected 180.
- Row 34 opens at 2017-09-06 12:00 UTC.
- Its raw close timestamp is `1504713600000`.
- Expected inclusive close is `1504713599999`.
- The 2017-09-06 16:00 UTC candle is missing.

This discrepancy must not be silently corrected.

Similar historical anomalies have been reported in Binance's public-data repository, including:

- https://github.com/binance/binance-public-data/issues/77
- https://github.com/binance/binance-public-data/issues/374

A Binance repository contributor has noted that some historical missing candles reflect exchange maintenance periods.

Do not assume every absent interval represents data corruption or that every malformed close timestamp represents a full valid candle.

## 3. Investigate before modifying validation

Perform a bounded read-only investigation of the affected September 2017 interval.

Compare, where available:

1. The retained monthly 4h archive.
2. Binance's daily 4h archive.
3. The historical public REST `klines` response.
4. Native 1h observations around the affected period.

Record:

- The exact returned candle identities.
- Whether the missing 4h candle exists in any official source.
- Whether the abnormal close timestamp is consistent across sources.
- Whether observed OHLCV and trade-count values agree.
- Whether there is evidence consistent with a trading interruption.
- What remains unverified.

Use only official public Binance data.

Do not persist alternative-timeframe data or fabricate a replacement 4h candle.

## 4. Separate archive validity from interval completeness

Review the current validation policy and make the minimum changes needed to distinguish:

- Invalid ZIP or checksum.
- Invalid CSV structure.
- Invalid OHLCV values.
- Duplicate or misaligned identities.
- Irregular provider close timestamps.
- Valid stored candles with missing neighbouring intervals.
- Genuine but unverified historical trading gaps.

A missing interval must be reported, not interpolated.

Do not globally disable timestamp or completeness validation.

For a close-time discrepancy, accept an explicit, narrowly justified normalization only if supported by provider evidence. Preserve the exact original ZIP and report the normalization. Otherwise exclude or quarantine the affected row and record why.

Do not silently treat a partial trading interval as an ordinary complete 4h candle.

## 5. Support historical gaps without corrupting research data

Extend the historical backfill to support an explicit, opt-in gap-tolerant mode if justified.

Suggested CLI option:

`--allow-source-gaps`

Requirements:

- Preserve the existing strict monthly ingestion behaviour by default.
- Only import individually valid, eligible observations.
- Preserve atomic writes for each validated accepted batch.
- Explicitly record excluded rows, missing intervals and reasons.
- Never create synthetic zero-volume or forward-filled candles.
- Never report a month with gaps as fully candle-complete.
- Preserve content hashes, raw archives and diagnostic manifests.
- Keep database conflicts and stale changed observations as explicit failures.
- Do not treat a failed checksum or unsafe archive as acceptable merely because the gap option is enabled.

If a month contains an unresolved data anomaly, its diagnostic status must remain visible even when the valid portion has been ingested.

Avoid new database tables unless the existing manifests and coverage reports genuinely cannot represent the information.

## 6. Research-safety requirements

The resulting dataset must not imply that missing intervals contain known prices.

Ensure coverage reports distinguish:

- Months successfully inspected.
- Valid observations persisted.
- Missing market intervals.
- Rejected or anomalous provider observations.
- Months that could not be acquired.
- Months not yet attempted.

Preserve the default rule that complete dataset exports fail when gaps remain.

Explicit incomplete exports may remain available but must contain the full gap manifest and be clearly labelled incomplete.

Document that future feature engineering and backtests must reject or explicitly handle windows crossing gaps. Rolling indicators must not silently treat candles separated by missing intervals as consecutive periods.

No ML or backtesting implementation belongs in this task.

## 7. Verify and resume

First verify the fix using September 2017 BTCUSDT.

Then test another bounded selection containing previously reported historical gaps, such as an affected month in 2018.

Do not hard-code a special rule for September 2017 if the same underlying problem occurs elsewhere.

If the validation policy is demonstrably safe, resume the full native 4h backfill for BTCUSDT and ETHUSDT from August 2017 through September 2026.

Reuse existing stored observations and existing ingestion infrastructure.

Keep each month's writes transactional and the process resumable.

Do not automatically attempt source repairs with alternative exchanges or synthesised candles.

If the backfill discovers other meaningful classes of anomalies, stop for review rather than progressively weakening validation until everything imports.

Report exact counts for successfully acquired months, accepted candles, known gaps, excluded observations, conflicts and failures.

A backfill with known gaps must not be described as a completely continuous dataset.

## 8. Testing

Add focused tests for:

- The September 2017 anomaly.
- Verified alternative-source comparisons.
- Missing intervals with valid surrounding candles.
- Irregular close-time handling.
- Explicit gap-tolerant versus strict mode.
- Atomic persistence of accepted rows.
- Rejected economic values.
- Conflicting existing observations.
- Restart and idempotency.
- Coverage reporting and export restrictions.

Automated tests must not require live Binance connectivity.

Use the existing disposable PostgreSQL integration environment.

Do not inflate the test suite unnecessarily.

Run pytest, Ruff lint and formatting.

## 9. Documentation and scope

Update `docs/stage-01b3-full-history.md` with the investigation, exact decisions, live results and remaining limitations.

Update the architecture/roadmap only where the implemented design changes.

Archive this substantive follow-up prompt chronologically under `prompts/stage-01-market-data/`.

Do not:

- Implement REST ingestion or recurring refresh.
- Add scheduling.
- Implement ML, backtesting or dashboards.
- Modify the original repository.
- Change production infrastructure.
- Commit or push changes.

## 10. Completion report

Explain:

1. Whether the 2017-09-06 gap exists in the alternative official sources.
2. The likely reason for the abnormal closing timestamp, clearly separating evidence from inference.
3. What validation rules were changed and why.
4. Which candles were excluded, accepted or normalized.
5. Whether the full historical acquisition completed.
6. Per-market stored counts and remaining gaps.
7. Whether a complete export was possible.
8. Test results and unresolved risks.

**Stop after this Stage 1B.3 follow-up. Do not begin Stage 1C.**
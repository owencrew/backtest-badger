# Backtest Badger — Stage 3D: Automated Forward Outcome Scoring

Implement reliable, unattended scoring of genuine forward predictions using the frozen Stage 3C evaluation protocol.

Stage 3C is implemented and verified. Genuine scoring succeeded for the first four BTCUSDT/ETHUSDT predictions, including two timely automated records. The Stage 3B prediction collector is running through a macOS LaunchAgent.

The goal is to automate outcome evaluation without modifying any existing forecast or score evidence.

## 1. Inspect before implementing

Read AGENTS.md, the architecture and roadmap, and the Stage 3A, 3B and 3C guides.

Inspect `forward_evaluation.py` and its `score()` API, current immutable outcome records, operational journals, and existing LaunchAgent conventions.

Reuse the existing scorer directly rather than rebuilding target validation, cohort classification, metric calculations or publication.

## 2. Add an automated scoring-cycle command

Implement a standalone module, for example:

`python -m backtest_badger.forward_scoring_operations cycle`

It must:

- Discover existing genuine forward prediction records for both markets.
- Determine which observations have matured under the frozen Stage 3C protocol.
- Skip unexpired targets without accessing the database.
- Skip already-scored records, validating existing evidence where appropriate.
- Invoke the existing Stage 3C scorer for eligible, unscored records.
- Retain pending observations for later retries.
- Continue processing other records after a per-record failure.
- Record clear operational diagnostics.

Use actual UTC timestamps. Never spoof issuance or scoring dates.

The scoring process must never create predictions or alter original forecast files.

Handle older mature-but-unscored records after downtime. Scoring an originally genuine prediction after its target matures is permitted; inventing a prediction retrospectively is not.

Make batch processing bounded without permanently abandoning older eligible work.

## 3. Preserve existing scientific evidence

Do not modify:

- `forward.py`
- `forward_operations.py`
- `forward_evaluation.py`
- `cli.py`
- Fixed model, feature or training definitions.
- Stage 3C's frozen evaluation protocol.
- Existing prediction or outcome JSON files.
- The installed Stage 3B LaunchAgent.

Avoid edits to any code whose fingerprints are embedded in existing records, including shared validators and model dependencies.

Keep Stage 3D as an independent orchestration layer.

Do not change the existing outcome-record schema.

## 4. Idempotency and failure handling

Use a single-machine process lock for overlapping scoring cycles.

Preserve the existing scorer's atomic exclusive outcome publication.

Handle database unavailability, missing target candles, corrupted predictions, invalid outcomes, partial operational writes and interrupted processes.

Failures must remain visible and must not prevent processing unrelated valid predictions.

Do not silently delete, overwrite or repair immutable evidence.

No provider requests or database writes are permitted.

Avoid unnecessary database connections for pending or already-scored observations.

## 5. Scheduling

Provide a separate opt-in macOS LaunchAgent with a five-minute interval.

It should be independent of the prediction collector and use the existing local development configuration.

The evaluator must tolerate running before the collector has refreshed a target candle: report pending, then retry on a subsequent cycle.

Do not assume execution order between the two LaunchAgents.

Use explicit paths, bounded execution, non-overlapping runs, local logs and safe permissions.

Do not automatically install or enable the new LaunchAgent.

The existing collection scheduler must remain operational.

## 6. Operational evidence and status

Use a separate gitignored directory:

`artifacts/forward-scoring-operations/`

Retain per-cycle timestamps and per-record results, including scored, already-scored, pending, failed and skipped.

Keep raw exception messages, secrets and configuration values out of logs.

Provide an offline status command showing the latest successful scoring cycle, outstanding mature predictions, pending predictions, failures and invalid evidence.

Do not duplicate immutable scored outcome evidence unnecessarily.

## 7. Testing

Test synthetic UTC clocks, target-maturity boundaries, multiple pending records, database failures, idempotency, concurrency, interrupted cycles, recovery, existing valid scores, invalid records and long downtime backlogs.

Include an integration test invoking the real Stage 3C scorer on synthetic PostgreSQL target data.

Ensure the existing 817 tests still pass.

Run Ruff, formatting, whitespace checks and LaunchAgent plist validation.

Do not access live Binance during automated tests.

## 8. Documentation

Create:

`docs/stage-03d-automated-outcome-scoring.md`

Archive the substantive prompt in:

`prompts/stage-03-forward/004-automated-outcome-scoring.md`

Update README, architecture and roadmap where appropriate.

Document installation, inspection, stopping, recovery and backup procedures.

Ensure future backups include `artifacts/forward-outcomes/` and the new scoring-operation evidence.

## 9. Boundaries

Do not implement live trading, paper trading, additional ML models, strategy optimisation, cloud hosting, a website, external notifications, new evaluation metrics or a new full quantitative audit.

Do not rescore existing outcomes.

Do not modify the historical holdout.

Do not commit, push, deploy or enable the new scheduler.

## 10. Completion report

Report implementation changes, new commands, idempotency safeguards, operational limitations, test results and any effects on existing evidence.

Confirm explicitly whether the original live prediction collector remained unchanged.

Stop after Stage 3D.
# Backtest Badger — Stage 3B: Reliable Automated Forward Collection

Implement Stage 3B: a small, reliable and idempotent automation workflow for the existing forward prediction system.

Stage 3A has been completed, committed and pushed. Its first genuine BTCUSDT and ETHUSDT forward records, issued on 2026-10-14, both passed offline verification.

The objective is to collect future forward predictions automatically, promptly and with clear failure evidence.

**Keep the existing scientific safeguards. Minimise new architecture.**

## 1. Inspect existing implementation

Read `AGENTS.md`, architecture, roadmap, Stage 1C.1 and Stage 3A guides.

Inspect `recent.py`, `forward.py`, `rest.py`, `cli.py`, existing tests and the Stage 3A record schema.

Reuse existing ingestion, eligibility, model inference, recording and verification functions.

Do not replace or redesign them.

## 2. Implement a single collection-cycle command

Add a command such as:

`badger forward-cycle`

It should:

1. Check the actual current UTC time.
2. Determine whether a new four-hour prediction horizon is eligible.
3. Check whether each market already has a record for that horizon.
4. If recorded, skip that market without re-fitting models or contacting Binance.
5. If recording is due, run the existing bounded recent-data refresh.
6. Require successful, complete and fresh source observations.
7. Call the existing forward-recording implementation.
8. Verify the newly published forward record.
9. Record an operational result for each market.
10. Exit with a meaningful status when any required action fails.

Handle BTCUSDT and ETHUSDT independently. A failure in one market must not prevent an attempt for the other.

Never create duplicate or backdated forward records.

Use the existing development PostgreSQL database only. Do not access production systems.

## 3. Time and freshness policy

Preserve native UTC four-hour candle boundaries at 00:00, 04:00, 08:00, 12:00, 16:00 and 20:00.

The earliest signal eligibility is candle close plus 60 seconds.

Aim to record each prediction within 15 minutes of its feature eligibility time.

For unattended operation, if the permitted promptness window has already elapsed, mark that horizon as missed rather than silently publishing a late prediction. A minimal targeted deadline guard at final publication may be added if necessary, with appropriate synthetic tests.

Do not alter the existing manual recording semantics unnecessarily.

A missed prediction must never be reconstructed and described as a genuine on-time forward observation.

Record actual issuance latency for successful predictions.

Use UTC internally throughout. Avoid scheduling assumptions based on London daylight-saving time.

## 4. Scheduling on macOS

Provide an opt-in macOS `launchd` LaunchAgent example using a five-minute interval.

It must:

- Use explicit paths to the project and uv executable.
- Set the correct project working directory.
- Use the existing `.env` configuration without copying secrets into the plist.
- Avoid overlapping collection processes.
- Resume safely after ordinary process failures.
- Produce locally retained, non-sensitive operational logs.
- Work without a continuously open terminal.

Do not automatically install or enable the LaunchAgent.

Document commands for installing, starting, stopping and inspecting it.

Explain that macOS sleep, shutdown, network outages and user logout may prevent timely execution. Missed windows must be reported, never backfilled as forward observations.

This is a development-machine solution, not a guarantee of 24/7 collection.

## 5. Reliability and idempotency

Implement safe handling of:

- Duplicate scheduled invocations.
- Simultaneous process attempts.
- Missing or stale source candles.
- Binance connectivity failures.
- PostgreSQL unavailability.
- An expired prediction horizon.
- Prediction or model fitting failures.
- Partially published operational evidence.
- Existing valid records.
- Unexpected process interruption.

Reuse Stage 3A's exclusive atomic prediction publication.

Avoid unnecessary repeated provider requests and model fitting.

Failures must not corrupt previously recorded predictions.

Retries may only operate while the same forward horizon is genuinely eligible and within the defined promptness window.

## 6. Operational history

Record lightweight per-cycle diagnostics under a separate gitignored directory, such as:

`artifacts/forward-operations/`

Include:

- UTC run timestamp.
- Eligible candle identity.
- Per-market status: recorded, already-recorded, not-yet-eligible, missed or failed.
- Source refresh outcome.
- Prediction record path and checksum, if successful.
- Actual issuance delay.
- Sanitised error category, if unsuccessful.

Do not copy complete forward evidence into operational logs.

Add a simple status command or report showing the latest successful prediction, most recent cycle, failures and detected missed horizons per market.

Do not interpret a missing prediction as a forecast with zero return.

## 7. Backups

Document a straightforward way to back up the forward-prediction directory and its operational evidence off-machine.

Preserve original bytes, timestamps and content hashes where practical.

Do not automatically connect cloud storage, introduce credentials or configure external backup services without explicit operator approval.

Document how backup copies can be verified.

## 8. Scientific integrity

Preserve the existing:

- Pre-2024 fixed model training sample.
- Five Stage 2A features.
- Four Stage 2B prediction models.
- No validation/test-label refitting.
- No forward-outcome scoring.
- No automatic trading.
- Immutable prediction records.
- Strict future-outcome timing checks.

Do not change strategy rules because Stage 2D found negative economic performance.

Scheduling and operational logs must remain separate from actual forecast evidence.

## 9. Tests

Use synthetic clocks and mocked provider responses.

Test:

- All six daily UTC four-hour boundaries.
- Eligibility before and after the 60-second delay.
- Promptness-window expiry.
- Exactly-once record publication.
- Duplicate and concurrent invocations.
- Independent BTC/ETH failures.
- Provider and database errors.
- Missed horizon reporting.
- Safe retry behaviour.
- No accidental overwrite.
- No forecast generation when no new candle is eligible.
- Recording and verification from real Stage 3A functions using synthetic fixtures.
- Idempotent repeated cycles.
- Correct operational logging and secret redaction.

Do not rely on live Binance access in automated tests.

Run pytest, Ruff and whitespace checks.

## 10. Controlled validation

Test the collection-cycle command using synthetic data and an injectable clock.

If the current actual UTC window is eligible and the local development database is fresh, an explicitly bounded genuine live test is permitted.

Never fabricate an earlier issue timestamp or overwrite the first verified records.

Do not install or enable the macOS scheduled job.

## 11. Documentation

Create:

`docs/stage-03b-automated-forward-collection.md`

Update README, architecture and roadmap.

Archive this exact substantive prompt at:

`prompts/stage-03-forward/002-automated-forward-collection.md`

Document operational installation instructions, limitations and how to check status.

Do not add a new audit or Field Note.

## 12. Exclusions

Do not implement:

- AWS/cloud hosting.
- Docker deployment or Kubernetes.
- Web dashboard.
- Live trading or paper trading.
- Prediction outcome scoring.
- Model optimisation or refitting on newer labels.
- Evaluation of the historical holdout.
- A generic distributed job framework.
- An external notification service.
- New PostgreSQL schema unless absolutely necessary.

Do not modify previous frozen artifacts, historical prediction records or earlier audit evidence.

Do not commit, push, deploy or enable unattended scheduled execution.

## 13. Completion report

Report:

1. Implementation summary.
2. Scheduler installation instructions.
3. Idempotency and timing safeguards.
4. Operational logging and failure handling.
5. Verification and test results.
6. Any actual forward records produced.
7. Known macOS reliability limitations.
8. Files added and modified.

Stop after Stage 3B. Do not proceed to forward evaluation or paper trading.
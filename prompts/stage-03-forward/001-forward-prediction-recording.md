# Backtest Badger — Stage 3A: Forward Prediction Recording

Act as a senior quantitative researcher and Python data engineer.

Implement Stage 3A: a minimal, reproducible system for generating and recording genuine forward predictions using the existing Backtest Badger research pipeline.

The objective is to build a trustworthy collection of timestamped forecasts issued **before the predicted market outcome is known**.

This is an engineering and scientific observation exercise, not a trading strategy.

## 1. Project context

Repository: `~/Code/backtest-badger`

Read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-01c1-rest-tail-and-refresh.md`
- `docs/stage-02a-research-dataset.md`
- `docs/stage-02b-predictive-baselines.md`
- `docs/stage-02c-execution-backtesting.md`
- `docs/stage-02d-economic-diagnostics.md`
- `docs/audits/001-integrated-quantitative-review.md`

Inspect the actual existing Python modules and artifact schemas before designing the implementation.

The prior integrated audit passed with limitations.

Stage 2D established that all existing trading policies lose money under base and stress transaction-cost assumptions. No model has demonstrated economic viability.

Do not interpret forward predictions as actionable trading recommendations.

## 2. Scope

Implement a manually invoked command that:

1. Reads the latest eligible historical candles from the existing local PostgreSQL database.
2. Validates their completeness, freshness and source provenance.
3. Calculates the existing causal features.
4. Applies the existing fixed predictive models.
5. Records the predictions, timestamps and exact input evidence.
6. Prevents duplicate or retroactively fabricated forward observations.

Start with BTCUSDT and ETHUSDT native four-hour candles.

Do not implement scheduling, a persistent background service, automatic execution or a web interface.

## 3. Existing models

Use the fixed Stage 2B model definitions:

- Zero-return baseline.
- Training-mean baseline.
- Ridge regression.
- Shallow gradient boosting.

Keep the original five Stage 2A features in exactly the original order.

Do not add new features, tune hyperparameters, change model architecture or choose a model based on the negative Stage 2C results.

Preserve the original training boundary: training observations before 2024.

Refit the fixed estimators deterministically from the pinned Stage 2A training dataset if necessary, reusing existing model construction and fitting helpers.

Do not use validation labels for refitting, and do not access the untouched 2025–2026 test targets.

Document the model-fitting policy and record the relevant implementation, input, dependency and model-configuration fingerprints.

If persistence of fitted estimators is genuinely useful, evaluate the simplest safe approach. Avoid introducing an ML model registry or unsafe loading of untrusted pickle/joblib files.

## 4. Forward-data eligibility

Use the existing PostgreSQL candle store as the source of recent observations.

Reuse the Stage 1C.1 recent-data infrastructure where appropriate.

For each prediction, require:

- Exactly seven consecutive native 4h candles for the fixed six-period feature lookback.
- The correct market identity.
- Valid UTC timestamps.
- Valid prices and volumes.
- No missing or invalid observations in the feature window.
- The latest candle to have completed and passed its 60-second settling delay.
- No source observation or revision recorded later than the forecast's actual issuance time.

Select the latest eligible candle based on the actual current UTC clock.

Crucially, the prediction must be for the **current, newly eligible horizon**, not whichever old candle happens to be most recent in a stale database.

If the latest required candle has not been synchronised, fail with a clear stale-data message.

If the source is incomplete, fail rather than forward-filling prices.

Do not automatically invoke data ingestion from the prediction command.

The existing `sync-recent` command can be run separately by the operator to refresh the local database.

## 5. Strict forward timing

For a candle opening at 08:00 UTC:

- Its close boundary is 12:00.
- Its features become eligible at 12:01.
- The prediction concerns the next candle ending at 16:00.

A genuine recorded forward prediction must satisfy:

`feature_available_at <= issued_at < target_close_boundary`

Also verify that the prediction was actually calculated before being recorded, and use a final issuance-time check immediately before durable publication.

Do not permit backdating, timestamp overrides or historical replay through the production recording command.

Do not generate a supposedly forward prediction for an outcome whose candle has already closed.

Inject clocks in synthetic tests without exposing a production CLI option that permits fabricated timestamps.

Use aware UTC timestamps throughout.

A local timestamp is evidence of local recording, not independent cryptographic proof of historical publication. State this limitation clearly.

## 6. Feature generation

Reuse Stage 2A's feature definitions and calculation helpers.

Required features:

- `log_return_4h`
- `log_return_12h`
- `log_return_24h`
- `realised_volatility_24h`
- `relative_base_volume`

Ensure the production forward path never requires the future target candle.

Keep prices and volumes as Decimal values until the existing feature calculations require numerical conversion.

Do not silently change historical research definitions.

## 7. Prediction records

For every recorded market/time/model prediction, preserve:

- Unique prediction identity.
- Venue, market and interval.
- Source candle opening and closing timestamps.
- Feature eligibility timestamp.
- Actual prediction issuance timestamp.
- Predicted horizon and target endpoint.
- Model identifier.
- Predicted next-four-hour log return.
- Optional equivalent percentage for presentation.
- Exact ordered feature values.
- Source candle versions and economic input values.
- Source observation timestamps and provenance references.
- Deterministic model/training fingerprints.
- Relevant software/runtime versions.
- A content hash covering the prediction evidence.

Store enough information to reconstruct why a prediction was made without querying later, potentially revised canonical database rows.

Do not store realised future prices, outcomes, hypothetical P&L or accuracy scores in forward-prediction records.

## 8. Append-only storage

Use simple local artifact storage under:

`artifacts/forward-predictions/`

Each eligible market/candle observation should have a stable, uniquely identified record.

Choose a straightforward immutable record format such as JSON.

Requirements:

- Atomic or exclusive publication.
- No silent overwrites.
- Duplicate market/candle/model records are rejected or explicitly identified as already recorded.
- Original predictions are never revised when provider prices change later.
- Failed attempts do not create apparently successful records.
- Checksums allow later verification of stored prediction contents.
- A failed or partial recording can be diagnosed and safely retried.

Avoid introducing a new database schema, generic event bus, message queue or experiment registry.

Local files are not cryptographically tamper-proof; document that limitation rather than claiming stronger guarantees.

## 9. CLI

Add a small command such as:

`badger record-forward --symbol BTCUSDT`

It should:

- Use the existing local development configuration.
- Read PostgreSQL without mutating candle tables.
- Compute all four model predictions for the latest eligible candle.
- Record a coherent set of predictions with shared input provenance.
- Print a concise completion summary with the record path and forecast identities.

Provide equivalent support for ETHUSDT.

The command must not submit orders, simulate trades or trigger unattended market-data synchronisation.

## 10. Verification and reproducibility

Build an independent command or small helper that verifies an existing forward record from retained evidence.

It should check:

- Stored record hash.
- Expected record schema.
- Feature inputs and definitions.
- Model identity and reproducible numerical output.
- UTC timing.
- Forecast issued before the target endpoint.
- No post-issuance source observations included.

Verification may use original pinned training artifacts, but must not silently substitute subsequently updated source candles.

Do not overwrite a record merely because the current canonical database differs.

A later provider revision is a separate observation, not a reason to rewrite historical prediction evidence.

## 11. Tests

Use synthetic data, an injectable clock and the existing isolated database test patterns where appropriate.

Cover:

- Correct causal features.
- Model reuse and deterministic fitting.
- UTC timestamp validation.
- Exactly seven consecutive candles.
- Missing or malformed candle rejection.
- Stale source-data rejection.
- Settling-delay boundaries.
- Correct target endpoint.
- Prediction recorded before outcome closes.
- Rejection after the target closes.
- No future candle or target access.
- No validation/test-label fitting.
- Source provenance preservation.
- Duplicate record protection.
- Atomic publication and failure handling.
- Provider-revision preservation.
- Independent BTC/ETH handling.
- No database writes.
- Deterministic forecast verification.

Do not require live Binance connectivity in automated tests.

Run the relevant tests, Ruff and whitespace checks.

Report PostgreSQL integration tests as passed or skipped accurately.

## 12. Controlled live validation

After implementing and testing:

- Inspect whether the existing local database has a freshly eligible, complete seven-candle window.
- If it does, perform at most one genuine manual forward-recording smoke test for each market.
- If the database is stale, report this and provide the existing `sync-recent` commands needed for a separate operator-controlled refresh.
- Never generate a retrospective record and label it as genuinely forward.
- Never modify provider data to force an example.

A successful live example is useful, but not required if eligibility conditions are not met.

## 13. Documentation

Create:

`docs/stage-03a-forward-predictions.md`

Document:

- How to refresh the existing market-data store manually.
- How to record forward predictions.
- Exact feature and model dependencies.
- Timestamp and eligibility definitions.
- Record identity and provenance.
- How immutable records are verified.
- How later provider revisions are handled.
- Scientific limitations.
- What was actually verified locally.

Update README, architecture and roadmap.

Archive this exact prompt at:

`prompts/stage-03-forward/001-forward-prediction-recording.md`

Do not automatically create a new Field Note.

## 14. Explicit exclusions

Do not implement:

- Scheduled prediction jobs.
- Live trading or exchange order submission.
- Paper trading.
- Automatic strategy decisions.
- Model optimisation or retraining on validation/test data.
- Evaluation of the historical test holdout.
- Forward-outcome scoring.
- P&L tracking.
- New data providers.
- Website or dashboard development.
- Production deployment.
- New PostgreSQL migrations unless an essential requirement demonstrably cannot be met with local artifacts.

Do not modify previous frozen datasets, experiments, backtests, audits or Field Notes.

Do not commit or push.

## 15. Completion report

Report:

1. Files added or modified.
2. Fixed model and feature provenance.
3. Forward timing and freshness safeguards.
4. Record schema and persistence rules.
5. Live smoke-test result, if eligible.
6. Exact predictions recorded, if any, labelled as unscored observations.
7. Test results.
8. Reproduction and verification evidence.
9. Known scientific and operational limitations.

Stop after Stage 3A.

**Do not begin automated prediction scheduling, outcome evaluation or paper trading.**
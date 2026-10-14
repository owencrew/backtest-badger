# Backtest Badger — Stage 3C: Prospective Forecast Evaluation

Act as a senior quantitative researcher and Python data engineer.

Implement Stage 3C: a scientifically defensible evaluation system for genuinely forward-recorded cryptocurrency predictions.

The existing Stage 3B collector is now operating on a Mac using an installed macOS LaunchAgent. Its first automated BTCUSDT and ETHUSDT prediction records were issued on 2026-10-14 shortly after 16:01 UTC and passed deterministic model replay.

Forward evidence and operations history are stored locally, with an initial off-machine backup uploaded to Google Drive.

The goal is to measure prediction accuracy once the corresponding future market outcomes become available.

**Preserve the original predictions, live collector, fixed models and untouched historical holdout.**

Do not implement trading, strategy optimisation or website components.

## 1. Inspect the existing project

Read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-02a-research-dataset.md`
- `docs/stage-02b-predictive-baselines.md`
- `docs/stage-02d-economic-diagnostics.md`
- `docs/stage-03a-forward-predictions.md`
- `docs/stage-03b-automated-forward-collection.md`

Inspect:

- `src/backtest_badger/forward.py`
- `src/backtest_badger/forward_operations.py`
- `src/backtest_badger/features.py`
- `src/backtest_badger/evaluation.py`
- `src/backtest_badger/candles.py`
- `src/backtest_badger/recent.py`
- Existing PostgreSQL read-only snapshot helpers.
- Existing record, manifest and test conventions.

Inspect the forward-record schema and operational-status definitions.

Do not read any realised forward outcome or calculate actual forward performance until the evaluation protocol in section 2 has been written and frozen for this implementation.

## 2. Predefine the evaluation protocol first

Create:

`docs/stage-03c-forward-evaluation-protocol.md`

Do this before processing actual forward outcomes.

The protocol must specify:

- Eligible prediction records.
- Primary and secondary observation cohorts.
- Forecast/target alignment.
- Target data requirements.
- Evaluation metrics.
- Treatment of zero and missing returns.
- Benchmark definitions.
- Missing and late-record handling.
- Duplicate and revised data policies.
- Reporting periods.
- Minimum sample-size warnings.
- Scientific limitations.

Record a SHA-256 fingerprint of the protocol in subsequent scoring artifacts.

Do not change metric definitions after viewing actual results.

If a material protocol change is later necessary, document it as a new version without rewriting existing scored evidence.

## 3. Primary and secondary cohorts

Define the primary evaluation cohort as **timely automated forward observations**.

A timely record must have an actual `issued_at` timestamp in:

`[feature_available_at, feature_available_at + 15 minutes)`

It must also have been issued before the target candle's closing boundary.

The primary cohort should represent the predictions produced under Stage 3B's unattended promptness policy.

Define a separate secondary cohort for genuine but late manual predictions.

The two original manually issued BTCUSDT and ETHUSDT records from 2026-10-14, with source opening 08:00 UTC, belong to this secondary cohort.

Do not silently pool them with timely automated observations.

A missing prediction must remain missing. Never substitute a forecast generated after the outcome is known.

Do not manufacture historical records, infer missing predictions or backfill missed horizons.

## 4. Exact target definition

Preserve the original Stage 2A target:

`actual_log_return_4h = ln(C[t+1] / C[t])`

Where:

- `C[t]` is the close price of the source candle retained inside the immutable forward-prediction record.
- `C[t+1]` is the close price of the immediately following native Binance Spot four-hour candle.

For example:

- Source candle opens 12:00 UTC and closes at 16:00.
- A prediction issued at 16:04 targets the candle opening at 16:00.
- The outcome candle closes at 20:00.
- The outcome is not eligible for scoring before 20:01 UTC.

The target is a four-hour candle-to-candle return.

It is not the market return between `issued_at` and target close.

This distinction must remain visible in reports.

Use the original retained source close rather than a revised canonical source close. Otherwise a later source revision could silently change the prediction's target definition.

## 5. Outcome eligibility and provenance

Retrieve future outcome candles from the existing local development PostgreSQL database.

Use the existing read-only, repeatable-read snapshot pattern.

Require:

- Actual current UTC time at or after target close plus 60 seconds.
- Exact market identity.
- Native 4h interval.
- Exactly the expected `target_open_time`.
- Valid complete source economics.
- Valid source/provenance fields.
- A recorded observation of the completed target candle.
- No malformed or missing target data.
- No unacknowledged source identity mismatch.

The scoring command must not trigger Binance downloads or synchronisation.

If the required outcome has not arrived, return a clear pending status rather than manufacturing a return.

The collector will continue refreshing data independently.

Retain the exact outcome candle values, version, provenance, observation timestamp, database-recording timestamp and evaluation capture timestamp.

Never silently replace a scored target with a subsequently revised canonical observation.

Provider revisions can be investigated separately, without altering the original forecast or outcome evidence.

## 6. Preserve the live prediction system

This is an important compatibility constraint.

Stage 3A includes hashes of existing implementation modules, including `forward.py`, `cli.py`, and model-fitting dependencies, in every recorded model recipe.

Editing those files may cause previously recorded forecasts to fail replay under the new checkout.

Therefore:

- Implement evaluation in a separate new module.
- Do not edit `forward.py`.
- Do not edit `forward_operations.py`.
- Do not edit `cli.py`.
- Do not edit feature, model-fitting, database, REST or candle-processing modules.
- Do not change `pyproject.toml` or `uv.lock`.
- Do not modify the existing LaunchAgent plist.
- Do not interrupt or restart the installed collector.
- Do not modify already recorded forecast files or operation journals.

Expose Stage 3C through a standalone Python module entry point, avoiding changes to the existing `badger` CLI.

For example:

`uv run --locked python -m backtest_badger.forward_evaluation score --record PATH`

and

`uv run --locked python -m backtest_badger.forward_evaluation report`

Adjust the final command names if there is a demonstrably simpler approach that preserves these compatibility requirements.

Do not create a new package, script entry point or dependency merely for CLI aesthetics.

## 7. Scoring individual predictions

Each forward JSON contains four fixed model forecasts:

- zero
- training_mean
- ridge
- gradient_boosting

Validate the original record's exact bytes, hash, identity, schema and time ordering.

Use the saved forecast values exactly as originally published.

Do not refit models as part of calculating evaluation metrics.

Full historical model replay is a separate verification step; scoring should not fail merely because the active checkout differs from the source revision that created a valid original record.

For each model compute:

- Signed forecast error: prediction minus actual log return.
- Absolute error.
- Squared error.
- Actual direction.
- Predicted direction.
- Directional correctness when a directional prediction exists.

Define the treatment of exact zero forecasts and zero actual returns explicitly.

For example, the zero baseline should abstain from directional accuracy rather than being credited with a correct upward/downward prediction.

Avoid arbitrary tolerances that redefine economic direction unless a tolerance is explicitly part of the preregistered protocol.

Preserve raw numerical precision and distinguish log returns from percentages.

## 8. Immutable outcome records

Create a separate directory:

`artifacts/forward-outcomes/`

Use one immutable outcome/evaluation record per source prediction record.

Each result must retain:

- Original prediction record ID.
- Original prediction content SHA-256 and exact-file SHA-256.
- Market and source/target candle identities.
- Original issuance timestamp.
- Cohort classification.
- Original source close.
- Target close and full target candle evidence.
- Outcome observation and capture timestamps.
- Actual target log return.
- All four original predictions.
- Individual model errors and directional outcomes.
- Evaluation protocol version and hash.
- Implementation fingerprint.
- Outcome-record checksum.

Use atomic, exclusive publication, with no silent overwrite.

Idempotent retries should recognise a valid existing outcome record and return an explicit already-scored result.

Corrupt or conflicting existing records must fail visibly rather than being replaced.

No database writes.

No forecast revisions.

A missing or pending outcome must not create a successful score record.

## 9. Aggregate evaluation

Implement an offline report command that reads the immutable forecast and outcome evidence.

It should not connect to PostgreSQL or Binance.

For each market/model/cohort, report:

- Number of genuine predictions.
- Number of scored predictions.
- Missing, pending and invalid counts where distinguishable.
- MAE.
- RMSE.
- Directional accuracy, with its denominator.
- Forecast bias.
- Mean realised log return.
- Error relative to the zero baseline.
- Error relative to the training-mean baseline.

For comparisons between models, use matched observation identities.

Do not compare scores calculated over different subsets of timestamps.

If a denominator is zero or a comparison is undefined, report it as undefined rather than zero.

Keep BTCUSDT and ETHUSDT separate.

Provide optional calendar-week or calendar-month summaries using fixed UTC boundaries, when the sample is sufficient. Define grouping by target endpoint.

Avoid pooling correlated observations and calling them independent replications.

## 10. Reporting small samples

Initially only a few genuine forward records exist.

The system should work correctly with one scored observation, zero scored observations or hundreds.

However, tiny samples must not produce misleading performance claims.

Include clear sample counts and warnings.

For example:

- Under 100 scored timely observations per market: explicitly preliminary.
- Larger samples: descriptive comparisons, not automatic statistical significance.
- No automatic model winner or promotion.
- No claim of persistent alpha or executable profitability.

The 100-observation threshold is a reporting convention, not a statistical power calculation.

Do not add complicated significance tests or bootstrapping machinery at this stage.

## 11. Research integrity

Never:

- Change the fixed Stage 2B models.
- Alter features or training windows.
- Evaluate or inspect 2025–September 2026 historical holdout targets.
- Optimise trading decisions from the observed outcomes.
- Change model-selection criteria after viewing results.
- Exclude losing predictions.
- Select favourable markets, months or confidence thresholds.
- Convert forecast scores into claimed trading returns.

A negative result is a valid research result.

Forward scoring should be clearly separated from the Stage 2C trading simulation and Stage 2D transaction-cost diagnostics.

## 12. Tests

Use synthetic records, clocks and target candles to test:

- Exact 4h target alignment.
- The 60-second target settling boundary.
- Scoring rejected before the outcome becomes available.
- Correct source-close/target-close log return.
- Retained original source price despite later revisions.
- Primary timely versus secondary late classification.
- Immutable publication.
- Existing-record idempotency.
- Malformed and altered prediction hashes.
- Invalid, missing and stale target observations.
- Provider revisions after scoring.
- Matched sample comparisons.
- MAE and RMSE calculations.
- Zero-prediction directional abstention.
- Exact-zero outcomes.
- Undefined metric denominators.
- UTC period grouping.
- Zero observations.
- Independent BTC/ETH records.
- No database writes.
- No forecast file modifications.
- Deterministic offline aggregate reports.

Use isolated PostgreSQL fixtures where useful.

Do not access live Binance in automated tests.

Run pytest, Ruff and whitespace checks.

Clearly report passed and skipped tests.

## 13. Controlled validation

Use synthetic evidence to exercise the full recording-to-scoring workflow.

The installed forward collector must remain operational and unchanged.

Do not perform real-outcome scoring yet.

Specifically, do not examine the realised outcomes of the first four forward-record files as part of implementing this stage.

After implementation, the user will review the preregistered protocol and test results before explicitly running genuine scoring.

Do not alter the evaluation protocol based on observed real performance.

No new scheduler for scoring is authorised in this stage.

## 14. Outputs and documentation

Create:

- `src/backtest_badger/forward_evaluation.py`
- `tests/test_forward_evaluation.py`
- `docs/stage-03c-forward-evaluation-protocol.md`
- `docs/stage-03c-forward-evaluation.md`

Update the roadmap and README as needed.

Archive this prompt at:

`prompts/stage-03-forward/003-forward-evaluation.md`

Do not modify fingerprinted live-prediction implementation files or historical Stage 3A/3B documentation simply for consistency.

Do not add another full audit or Field Note automatically.

## 15. Explicit exclusions

Do not implement:

- Automated outcome-scoring schedules.
- Live trading.
- Paper trading.
- New ML models.
- New features.
- Signal optimisation.
- Transaction-cost changes.
- Historical test-holdout assessment.
- Website dashboards.
- Production deployment.
- New external services.
- New database migrations.
- Generic experiment frameworks.

Do not commit, push or enable new unattended jobs.

## 16. Completion report

Provide:

1. Protocol definitions and fingerprint.
2. Evaluation cohort and target rules.
3. Implemented commands.
4. Outcome provenance and immutability safeguards.
5. Metrics and benchmark conventions.
6. Synthetic test results.
7. Regression test results.
8. Confirmation that no actual forward outcomes were scored.
9. Confirmation that the existing live collector and records remained unchanged.
10. Files added and modified.
11. Exact manual commands for future genuine scoring, without executing them.

Stop after Stage 3C implementation.

**Do not begin Stage 4 paper trading.**
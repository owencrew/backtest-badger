# Backtest Badger — Stage 2A: Reproducible Research Dataset & Causal Features

Act as a senior quantitative researcher and Python data engineer.

Implement Stage 2A: the minimum trustworthy research foundation needed before predictive modelling and backtesting.

Principle: **Scientific correctness first. Minimum complexity. No feature creep.**

## 1. Review the project

Read `AGENTS.md`, `docs/architecture.md`, `docs/roadmap.md`, the Stage 1B.3 and 1C guides, the existing research export code and the first Field Note.

Inspect the actual frozen dataset manifest and CSV before implementing.

Do not modify the market-data database or existing frozen artifacts.

## 2. Data source

Use the existing frozen Stage 1B.3 research export:

`artifacts/exports/binance-4h-history-v1/`

Verify its recorded CSV SHA-256, schema and manifest.

The export is explicitly incomplete, with documented historical gaps. Require an explicit acknowledgement of this status.

Do not fetch new Binance data during research preparation.

Start with BTCUSDT and ETHUSDT native 4h candles.

## 3. Research data preparation

Implement a minimal, readable research data pipeline.

Requirements:

- Parse economic values without unnecessary precision loss.
- Keep market identity and UTC timestamps.
- Verify chronological order and unique candle identities.
- Respect recorded source gaps and excluded observations.
- Never forward-fill missing prices.
- Never treat adjacent CSV rows as consecutive 4h periods without verifying their timestamps.
- Reject features or targets spanning missing candle intervals.
- Clearly flag known historical source anomalies.
- Separate the source-data integrity checks from feature generation.

Use pandas and NumPy if appropriate; avoid a larger framework.

## 4. Causal features

Implement a small set of interpretable, backward-looking features:

- Previous 4h log return.
- Previous 12h and 24h returns.
- Rolling realised volatility.
- Rolling volume relative to recent history.
- Optional hour-of-day feature using UTC.

Avoid dozens of technical indicators.

For each feature, document exactly which candles are required and when the feature becomes knowable.

No feature may reference future candles.

Test feature values on small hand-constructed datasets.

## 5. Prediction target

Begin with one simple research target:

**Next 4h close-to-close log return.**

Treat this as a predictive research target, not automatically as an executable trading return.

Clearly document that the latest completed candle's features are only available after the configured settling delay. Stage 2C must model execution timing independently and must not assume fills at prices already unavailable when a signal is generated.

Require uninterrupted candle identities for target computation.

Do not introduce multiple prediction horizons yet.

## 6. Chronological evaluation

Create a clearly documented chronological train, validation and test split.

Suggested initial fixed boundaries:

- Training: available eligible history before 2024.
- Validation: 2024.
- Test: January 2025 through September 2026.

Use the same calendar boundaries for both markets.

Prevent labels from crossing split boundaries. Never fit preprocessing statistics on validation or test data.

Do not shuffle time-series observations.

The test partition must be preserved as a genuine holdout for later modelling.

Do not tune anything against test results.

## 7. Initial sanity checks

Report:

- Total eligible feature/target observations.
- Dropped observations due to rolling warm-up.
- Dropped observations due to missing candles or known anomalies.
- Training, validation and test counts by market.
- Target distribution summaries.
- Any unexpected timestamps or discontinuities.

Implement simple no-skill reference predictions, such as a training-set mean return, for future comparisons.

Do not train an ML model or optimise a trading strategy in this increment.

## 8. Reproducibility

Produce a deterministic research artifact containing the resulting feature/target rows.

Record:

- Original frozen dataset ID and hash.
- Feature definitions.
- Target definition.
- Gap and anomaly exclusion policy.
- Split boundaries.
- Implementation version.
- Output content hash.
- Row counts and exclusions.

Keep artifacts under gitignored local storage.

Do not introduce a new database or experiment-tracking platform.

## 9. Testing

Cover:

- No future-data access.
- No forward-filling.
- Missing-candle boundaries.
- Rolling-window correctness.
- Return and volatility calculations.
- Target alignment.
- Chronological splits.
- Split-boundary label leakage.
- No preprocessing leakage.
- Deterministic reproduction.
- Rejection of incompatible or altered frozen inputs.

Use synthetic fixtures for tests.

Run the full pytest suite and Ruff.

## 10. Documentation

Create:

`docs/stage-02a-research-dataset.md`

Update the architecture and roadmap.

Archive this substantive prompt at:

`prompts/stage-02-research/001-research-dataset-and-features.md`

Create a Field Note only if a genuinely new, evidence-backed discovery emerges.

## 11. Explicit exclusions

Do not implement:

- Complex machine learning.
- Hyperparameter optimisation.
- Trading strategies or position sizing.
- Transaction-cost or execution simulations.
- Paper trading.
- Live predictions.
- Scheduled ingestion.
- Website features.
- New data providers.
- Production deployment.

Do not commit or push.

## 12. Completion report

Provide:

1. Files added and modified.
2. Input dataset verification results.
3. Feature and target definitions.
4. Exact temporal alignment and leakage controls.
5. Train/validation/test counts.
6. Gap and anomaly exclusions.
7. Generated artifact hash.
8. Test results.
9. Remaining scientific limitations.

**Stop after Stage 2A for review.**
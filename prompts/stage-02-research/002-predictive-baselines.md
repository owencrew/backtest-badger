# Backtest Badger — Stage 2B: Predictive Baselines and Chronological Evaluation

Act as a quantitative researcher and Python machine-learning engineer.

Implement Stage 2B: a small, reproducible predictive experiment comparing simple machine-learning models with honest no-skill baselines.

**Principle: Minimum complexity. Maximum scientific correctness.**

This stage measures statistical predictability, not trading profitability.

## 1. Review existing work

Repository: `~/Code/backtest-badger`

Read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-02a-research-dataset.md`
- `src/backtest_badger/features.py`
- `src/backtest_badger/frozen.py`
- Existing CLI and tests.

Inspect the actual Stage 2A research manifest.

The existing research dataset is:

`artifacts/research/stage-2a-v1/`

Expected CSV SHA-256:

`04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8`

Expected manifest SHA-256:

`a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e`

The dataset contains 39,609 eligible feature/target rows across BTCUSDT and ETHUSDT.

Do not recreate or modify Stage 2A artifacts.

## 2. Research question

Evaluate:

**Do simple features describing recent returns, realised volatility and trading volume predict the next four-hour close-to-close log return better than naive forecasts?**

Use the existing five features unchanged:

1. `log_return_4h`
2. `log_return_12h`
3. `log_return_24h`
4. `realised_volatility_24h`
5. `relative_base_volume`

Target: `target_log_return_4h`.

Do not engineer new features or change the target after seeing results.

## 3. Experimental scope

Train separate models for BTCUSDT and ETHUSDT.

Compare:

- Zero-return prediction.
- Training-mean prediction.
- Ridge regression.
- A small, deliberately regularised gradient-boosted tree regressor.

Prefer scikit-learn and NumPy. Add them through uv with compatible pinned lockfile resolution.

Do not add TensorFlow, PyTorch, MLflow, Optuna or experiment-orchestration frameworks.

Use fixed, documented model configurations.

For Ridge, use train-fitted standardisation in a scikit-learn Pipeline.

For gradient boosting, use a conservative shallow model, disable random validation-based early stopping and set a deterministic random seed where supported.

No hyperparameter searches in this stage.

## 4. Chronological data discipline

Preserve Stage 2A splits exactly:

- Train: eligible observations before 2024.
- Validation: 2024.
- Test: January 2025 to September 2026.

Fit all models and preprocessing using **training data only**.

Evaluate models on validation data only.

Do not:

- Shuffle rows into random train/test partitions.
- Fit scalers or transformations on validation data.
- Use validation labels when calculating training baselines.
- Access test labels for model selection, scoring or exploratory plots.
- Generate, inspect or publish test-set prediction metrics.
- Change split boundaries based on outcomes.

The test holdout must remain untouched for later locked evaluation.

Keep both market models independent; do not treat correlated BTC and ETH observations as independent evidence of significance.

## 5. Input validation

Validate the Stage 2A CSV and manifest before model fitting.

Check:

- Actual input hashes.
- Expected feature names and order.
- Target definition.
- Market identities.
- Train/validation/test boundaries.
- Chronological ordering.
- Finite numeric values.
- Unique market/open-time identities.
- Feature/label availability timestamps.
- Recorded gap and anomaly-exclusion policy.
- Expected train and validation row counts.

Use the existing source manifest rather than duplicating the whole Stage 2A implementation.

If the dataset is incompatible or altered, fail explicitly.

Research preparation and modelling should be separate responsibilities.

## 6. Validation metrics

For each market/model, report:

- Mean absolute error (MAE).
- Root mean squared error (RMSE).
- Relative improvement or deterioration against the zero and training-mean baselines.
- Out-of-sample R² or clearly labelled skill score against the training-mean forecast.
- Prediction versus realised-return Pearson correlation, where mathematically defined.
- Directional accuracy for nonzero forecasts, with forecast coverage and explicit zero-return conventions.

Keep units clear: predictions and targets are dimensionless log returns.

Constant or near-constant predictions may make correlation or directional accuracy undefined. Report this rather than fabricating a statistic.

A model with slightly better RMSE does not automatically have useful trading value.

Do not report profit, Sharpe ratio, alpha, strategy returns or economic significance.

Do not claim statistical significance from ordinary accuracy differences without accounting for time dependence.

## 7. Evaluation protocol

Train once using fixed initial configurations.

Evaluate on the 2024 validation partition.

Compare models with both simple baselines.

Provide a compact comparison by market.

Optionally include one predefined quarterly breakdown of validation performance to expose instability across market regimes.

Avoid repeatedly changing features, models and parameters to obtain better validation results.

Do not conduct a broad model search.

If the models do not outperform the baselines, report that plainly.

## 8. Reproducible outputs

Add a command such as:

`badger evaluate-models --source artifacts/research/stage-2a-v1 --output artifacts/experiments/stage-2b-v1`

Generate:

- A validation prediction CSV.
- An experiment manifest containing configurations and validation metrics.
- A concise human-readable results summary.

The prediction CSV should include:

- Market identity.
- Source candle opening time.
- Feature availability time.
- Model identifier.
- Predicted next-four-hour log return.
- Referenced research dataset hash.

Do not put realised future target values into the prediction CSV. Evaluation metrics may use validation targets internally.

Keep model output distinct from trading signals and orders.

Record:

- Input artifact hashes.
- Feature names and ordering.
- Target and split definitions.
- Training row counts.
- Model parameters.
- Preprocessing rules.
- Library/runtime versions.
- Random seeds.
- Validation metrics.
- Output file SHA-256.

Use gitignored immutable experiment directories. Repeated runs with unchanged inputs and configuration should reproduce predictions and metrics within a defined numerical tolerance.

Avoid a separate experiment database or ML platform.

## 9. Scientific interpretation

Explain the differences between:

- Predictive correlation.
- Regression error.
- Directional prediction.
- Actual executable trading profitability.

If results appear promising, identify relevant limitations:

- Financial returns are noisy.
- Market conditions change.
- BTC and ETH are correlated.
- The dataset uses retrospective provider observations.
- Results are specific to a fixed 2024 validation period.
- Close-to-close targets are not executable trade returns.
- Fees, spreads, slippage and execution latency are not yet modelled.

Do not conclude that a model is profitable.

Avoid creating an elaborate model-selection framework.

## 10. Tests

Write focused tests for:

- Correct feature ordering.
- Exact chronological selection.
- Train-only scaling and fitting.
- No validation-label or test-label leakage.
- Correct baseline values.
- Reproducible model fitting.
- Correct metric calculations.
- Constant-prediction edge cases.
- Missing/nonfinite feature rejection.
- Input schema and hash validation.
- Deterministic output creation.
- No accidental access to test outcomes.

Use small synthetic examples for numerical validation.

No tests should require live Binance connectivity.

Run pytest, Ruff lint, formatting and `git diff --check`.

## 11. Documentation

Create:

`docs/stage-02b-predictive-baselines.md`

Document:

- Research question.
- Model choices.
- Train/validation/test protocol.
- Validation metrics.
- Real experimental results.
- Interpretation and limitations.
- Artifact locations and hashes.

Update the architecture and roadmap to reflect the implementation.

Archive this substantive prompt at:

`prompts/stage-02-research/002-predictive-baselines.md`

A Field Note is warranted only if the experiment yields a meaningful, evidence-backed lesson. Do not automatically publish one.

## 12. Explicit exclusions

Do not implement:

- Additional feature engineering.
- Automated feature selection.
- Hyperparameter optimisation.
- Deep learning.
- Test-set evaluation.
- Trading signals or threshold optimisation.
- Backtesting.
- Fees, slippage or execution simulations.
- Model deployment or live predictions.
- Paper trading.
- Website development.

Do not alter frozen datasets, ingestion infrastructure or the development PostgreSQL database.

Do not commit or push changes.

## 13. Completion report

Report:

1. Models and dependencies added.
2. Training and validation counts.
3. Per-market validation metric comparison.
4. Any baseline improvements or deterioration.
5. Reproducibility verification.
6. Test results.
7. Scientific limitations.
8. Artifacts generated and files changed.

Critically interpret the results without searching for excuses if performance is poor.

**Stop after Stage 2B. Do not begin Stage 2C.**
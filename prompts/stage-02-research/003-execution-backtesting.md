# Backtest Badger — Stage 2C: Realistic Execution Backtesting

Act as a senior quantitative developer specialising in backtesting, market microstructure, execution simulation and reproducible Python research.

Implement **Stage 2C — Execution-Aware Backtesting**.

We have completed:

- Stage 2A: deterministic, gap-safe research features and chronological splits.
- Stage 2B: validation-only predictive baselines for BTCUSDT and ETHUSDT.

Our objective is to test whether those existing forecasts produce economically useful simulated trading results **without inventing fills at prices unavailable when the signal was generated**.

**Principle: Minimum complexity. Maximum scientific correctness.**

Do not tune models or strategies to improve results.

## 1. Inspect the existing project

Repository: `~/Code/backtest-badger`

Read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-01a-market-data-design.md`
- `docs/stage-02a-research-dataset.md`
- `docs/stage-02b-predictive-baselines.md`
- Existing archive, validation, feature and evaluation modules.
- Existing CLI, tests and manifest conventions.

Inspect the existing research and forecast artifacts.

Stage 2B forecast artifact:

`artifacts/experiments/stage-2b-v1/`

Expected hashes:

- `validation_predictions.csv`: `e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674`
- `manifest.json`: `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581`

These contain 17,560 validation forecast rows, representing four models across 4,390 market-time observations.

Verify the actual bytes and schema before use.

Do not alter Stage 2A or Stage 2B artifacts.

## 2. Fundamental execution timing

The Stage 2A signal becomes available at:

`signal_time = four_hour_candle_open + 4 hours + 60 seconds`

The Stage 2B prediction targets the return between the end of that candle and the end of the following four-hour candle.

A signal at 12:01 cannot execute at the already-passed 12:00 closing price.

For this initial backtest, deliberately choose a conservative, independently sourced **native 1h execution-price model**.

For a signal available at 12:01 UTC:

- Entry reference: 13:00 UTC native 1h opening price.
- Exit reference: 16:00 UTC native 1h opening price.
- Simulated holding period: three hours.

At the next signal, 16:01 UTC, a new entry can occur at 17:00.

The execution rule must be fixed before looking at backtest results.

Important qualifications:

- This is a hypothetical hourly-boundary execution policy.
- We are not claiming that an actual market order placed at 12:01 would wait until 13:00.
- Opening prices are historical references, not guaranteed fill prices.
- Explicit slippage and spread assumptions must be applied.
- This deliberately delayed model is not a precise simulation of immediate execution after the signal.
- The model's predictive target and the simulated holding-period return are different quantities. Never conflate them.

Do not use future prices for trading decisions. Future prices may only be used to calculate hypothetical fills and realised P&L after the trade has been selected.

## 3. Independently sourced execution prices

Acquire native Binance Spot **1h monthly archives for January–December 2024**, for BTCUSDT and ETHUSDT.

This means at most 24 monthly archive downloads.

Reuse existing checksum verification, parsing, UTC validation, safe HTTP handling and artifact retention.

Requirements:

- Source native 1h observations independently of the 4h research dataset.
- Verify official archive ZIP checksums.
- Preserve exact provider price strings as Decimals.
- Validate timestamps and native hourly candle boundaries.
- Retain source URLs, hashes and acquisition evidence.
- Require an explicit complete hourly identity grid for the selected validation range.
- Do not interpolate absent hourly prices.
- Do not silently substitute a four-hour price if an hourly reference is unavailable.
- Reject malformed or incomplete execution input, rather than trading around unverified gaps.

Create an immutable, locally stored execution-reference artifact containing the required hourly opening prices and their provenance.

Suggested path:

`artifacts/execution/binance-1h-2024-v1/`

Use a manifest with source/archive hashes, row counts, coverage and output SHA-256.

Downloading and preparing execution data must be separate from the actual backtest.

Do not insert this hourly dataset into the canonical market-data PostgreSQL tables.

Do not build a general multi-timeframe ingestion framework.

## 4. CLI

Add two small commands or equivalent interfaces:

### Prepare execution data

`badger prepare-execution-data --output artifacts/execution/binance-1h-2024-v1`

This performs bounded source acquisition and publishes the frozen execution-reference artifact.

### Run validation backtest

`badger backtest-validation --forecasts artifacts/experiments/stage-2b-v1 --execution artifacts/execution/binance-1h-2024-v1 --output artifacts/backtests/stage-2c-v1`

This command must run offline using only verified, frozen input artifacts.

Do not overwrite existing artifact directories.

Both commands should produce clear diagnostics.

## 5. Strategies

Simulate all four existing predictors independently:

- `zero`
- `training_mean`
- `ridge`
- `gradient_boosting`

For each market and model, use a separate simulated account.

Starting capital: **10,000 USDT**.

Use this fixed rule:

- Forecast greater than `1e-12`: enter long.
- Otherwise: remain in cash.
- At the target endpoint: exit any open position.

The tolerance is fixed for consistency with Stage 2B's near-zero forecast convention, not tuned against trading performance.

No short selling, borrowing, leverage, margin, derivatives or funding.

No concurrent positions in one simulated account.

Do not allow cash balances or trades to leak between models or markets.

Trading decisions may use only the model identifier, forecast value, signal timestamp and previously available state.

No price trend filters, volatility filters, stop losses, take-profit optimisation, forecast ranking or tuned thresholds.

## 6. Execution and transaction costs

For each scheduled entry and exit, use the matching hourly opening-price reference.

Apply explicit configurable, deterministic costs.

Use three **fixed scenarios**, all specified before viewing results:

| Scenario | Taker fee per side | Assumed half-spread per side | Slippage per side |
| --- | --- | --- | --- |
| Frictionless diagnostic | 0 bps | 0 bps | 0 bps |
| Base | 10 bps | 1 bp | 2 bps |
| Stress | 10 bps | 3 bps | 10 bps |

These are modelling assumptions, not verified historical bid/ask spreads, actual 2024 account fees or guaranteed execution conditions.

For buys, apply spread and slippage adversely to the reference price.

For sells, apply them adversely in the opposite direction.

Charge fees on executed notional on both sides.

Ensure the purchase quantity is affordable after fees.

Use coherent, reproducible USDT cash and asset-quantity accounting. Prefer Decimal for prices, cash and trade quantities.

No negative cash, hidden leverage, free transaction costs or implicit financing.

Report gross and net P&L separately.

Do not double-count fees or treat the fee rate as a one-time round-trip charge.

## 7. Backtesting engine

Implement the smallest clear event-based or sequential simulation needed.

For each market/model/scenario:

1. Read each eligible 2024 validation forecast chronologically.
2. Determine the signal availability timestamp.
3. Determine its first eligible hourly entry boundary.
4. Confirm that the entry precedes the fixed exit boundary.
5. Apply the predefined long/cash rule.
6. If long, simulate entry using the execution-price model.
7. Hold until the predetermined exit boundary.
8. Simulate exit.
9. Deduct transaction costs.
10. Update cash and equity.
11. Record the complete trade and accounting evidence.

Do not allow overlapping positions in the same account.

A trade may not use a prediction produced after its entry timestamp.

An execution reference must belong to the correct symbol and timestamp.

Use no later data for determining entry eligibility or direction.

No fills during source gaps.

The engine should be easy to test using a handful of synthetic signals and prices.

Prefer ordinary Python functions and small data structures over a complex broker/order-management abstraction.

## 8. Results and metrics

For each market/model/cost scenario report:

- Starting and ending equity.
- Gross and net P&L.
- Net percentage return.
- Total fees, spread costs and slippage costs.
- Number of executed trades.
- Number of signals that remained in cash.
- Win rate.
- Average net trade return.
- Maximum drawdown, with its observation convention explicitly stated.
- Time in market or fraction of eligible windows invested.
- Missing or rejected execution references.

Keep cash-only and always-positive forecast baselines visible.

If equity is measured only after positions close, label drawdown as a realised-equity measure rather than pretending to observe all intratrade drawdowns.

Do not invent intrabar mark-to-market prices.

Do not calculate an annualised Sharpe ratio unless the sampling, return clock and flat-period accounting are explicitly sound. Omitting Sharpe is preferable to publishing a misleading statistic.

Do not report trading results as actual or paper-traded performance. Label everything historical simulation.

## 9. Holdout discipline

Use **only the 2024 validation forecasts**.

The 2025–September 2026 test partition remains untouched.

Do not train or refit models.

Do not regenerate predictions.

Do not access test labels or generate test forecasts.

Do not modify strategies, cost parameters or thresholds in response to the backtest's performance.

No strategy optimisation, model promotion or selection for live use in this stage.

A negative result is acceptable and should be reported honestly.

## 10. Reproducibility and artifacts

Generate a deterministic directory containing, as appropriate:

- `trades.csv`: executed trades, entry/exit timestamps and prices, quantity, gross/net P&L and detailed costs.
- `equity_curve.csv`: consistent timestamped simulated equity and cash.
- `manifest.json`: source hashes, execution assumptions, models, scenarios, counts, metrics and output hashes.
- `summary.md`: compact results and limitations.

Include signal time and execution time in the trade records so timing can be independently inspected.

Keep BTC and ETH simulation accounting separate.

Use immutable, gitignored output directories.

Re-running with the same artifacts and assumptions should reproduce the outputs within defined tolerances.

Do not create a trading database, scheduler, API service or web dashboard.

## 11. Tests

Write focused synthetic tests covering:

- A signal at 12:01 cannot fill at 12:00.
- The 12:01 signal uses 13:00 entry and 16:00 exit references.
- Exact UTC timing and chronological ordering.
- No future-price access in signal decisions.
- No execution before feature availability.
- Correct long/cash classification.
- The zero model executes no trades.
- No short selling or leverage.
- No overlapping trades.
- Correct buy and sell spread/slippage direction.
- Fees deducted on both sides.
- Correct affordable quantity.
- Cash and asset conservation.
- Known hand-calculated P&L.
- Missing hourly execution data.
- Rejected or inconsistent source identities.
- Correct independent market/model accounts.
- Correct gross-versus-net reconciliation.
- Deterministic output artifacts.
- Altered source hash rejection.
- Immutable Stage 2A and 2B inputs.
- No test-holdout access.

Use synthetic fixtures for backtesting tests.

No automated test should need live Binance connectivity.

Run the existing pytest suite and Ruff checks.

If the isolated PostgreSQL test environment is unavailable, explicitly distinguish passing unit tests from skipped integration tests; do not claim that skipped tests passed.

## 12. Controlled live execution-data validation

Acquire only the selected 2024 native 1h archives.

First validate a single month per market before acquiring the rest.

Verify checksum validity, expected timestamps and consistency between the execution artifact and the acquired source files.

If genuine provider gaps or anomalies occur, stop, record the evidence and report them; do not loosen validation to force a backtest result.

Only run the actual backtest after the execution-reference artifact is complete and frozen.

Preserve all prior research exports and predictions.

## 13. Scientific interpretation

Explain:

- Why regression improvement does not guarantee trading profitability.
- Why execution costs can overwhelm weak signals.
- Why the one-hour delayed entry changes the economic exposure being evaluated.
- Why a 1h opening price is not an exact historical trade fill.
- Why a profitable validation backtest would not yet establish a robust strategy.
- Why correlated BTC and ETH results are not independent confirmation.
- Why our fixed 2024 results cannot establish performance in other regimes.
- Why existing retrospective market data cannot fully reconstruct historical order-book conditions.

Distinguish gross from net results prominently.

Avoid exaggerating small or positive outcomes.

## 14. Documentation

Create:

`docs/stage-02c-execution-backtesting.md`

Update `docs/architecture.md` and `docs/roadmap.md`.

Archive this exact substantive prompt at:

`prompts/stage-02-research/003-execution-backtesting.md`

Do not automatically create a Field Note. Only add one if the results reveal a meaningful, evidence-backed insight worth sharing publicly.

## 15. Explicit exclusions

Do not implement:

- Stage 2D strategy optimisation or robustness research.
- Test-holdout evaluation.
- Model retraining or feature changes.
- Live or paper trading.
- Exchange order submission.
- WebSocket streaming.
- A generic broker abstraction.
- Position leverage or short selling.
- Order-book reconstruction.
- Minute-by-minute execution simulation.
- AWS or website deployment.

Do not modify the old `crypto-trading-platform` repository.

Do not commit or push changes.

## 16. Completion report

Report:

1. Execution-data acquisition counts and hashes.
2. Source integrity and coverage findings.
3. Actual forecast-to-entry/exit timing policy.
4. Trading and cost assumptions.
5. Gross/net results by model and market.
6. Trade counts, costs and cash-accounting checks.
7. Reproducibility results.
8. Test results.
9. Files created or modified.
10. Scientific limitations and unresolved issues.

Review the implementation for unnecessary complexity.

**Stop after Stage 2C for review. Do not begin Stage 2D or use test-holdout data.**
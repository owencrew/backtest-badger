# Backtest Badger — Integrated Quantitative Audit 001

Act as an independent senior quantitative researcher and trading-systems auditor.

Conduct a **single, focused, adversarial audit** of the completed Backtest Badger research pipeline through Stage 2C.

Your role is to determine whether the reported research and backtesting results can be trusted, not to improve strategy performance or redesign the platform.

**Core principle: Find material errors. Avoid speculative improvements and audit-driven overengineering.**

This is a read-only audit of implementation and evidence. Do not modify application code.

## 1. Scope

Repository: `~/Code/backtest-badger`

Read `AGENTS.md`, the architecture and relevant stage guides.

Inspect the integrated pipeline:

- Stage 1: frozen market-data exports and source integrity.
- Stage 2A: `frozen.py`, `features.py`.
- Stage 2B: `model_data.py`, `evaluation.py`.
- Stage 2C: `execution_data.py`, `forecast_data.py`, `backtest.py`.

Inspect relevant tests and the actual frozen artifact manifests.

Inspect the existing 2024 validation results and retained accounting evidence.

Do not access 2025–2026 holdout labels, generate holdout forecasts or evaluate test-period performance.

Do not redownload market data or run new experiments unless needed to verify a concrete potential defect.

## 2. Audit feature and target causality

Independently trace at least one complete example from historical candle through features, target, model forecast and execution.

Verify:

- Every rolling feature uses only completed candles.
- Missing timestamps cannot silently shorten lookback horizons.
- Known anomaly exclusions propagate correctly.
- The next-four-hour target uses the correct future candle.
- Labels cannot cross the defined train/validation boundaries.
- Training preprocessing uses training observations only.
- Validation labels are never used to fit models.
- The test holdout is never used for performance evaluation or tuning.
- Feature availability and target availability are calculated consistently.

Distinguish genuine leakage from legitimate use of older historical observations.

## 3. Audit predictive evaluation

Check:

- Model and feature ordering.
- Market separation.
- Baseline construction.
- Train-only standardisation.
- Deterministic fitting.
- MAE/RMSE and skill calculations.
- Correlation and directional accuracy conventions.
- Handling of constant predictions.
- Comparison against zero and training-mean forecasts.

Identify any misleading claims about predictive performance or statistical significance.

Do not tune models or select a different model based on backtesting results.

## 4. Audit execution timing

Verify the exact intended sequence:

- A native 4h source candle opens at 08:00.
- It finishes at 12:00.
- Its features become eligible at 12:01.
- The simulated entry reference is 13:00.
- The exit reference is 16:00.

Confirm that a strategy cannot enter before its forecast is available.

Verify that independent native 1h references belong to the correct symbol, date and hour.

Ensure execution never falls back to an already-passed 4h close.

Check for duplicate trades, overlapping positions, incorrectly aligned signals, future-data access in trading decisions or silent gaps in execution data.

Recognise that hourly opening prices are retrospective reference prices and do not prove actual fill availability.

## 5. Independently verify accounting

Use an independent calculation—not merely the same implementation's reconciliation function—to verify representative synthetic trades and a selection of retained real simulated trades.

Check:

- Buy and sell price adjustments.
- Fee calculations on both sides.
- All-in affordability.
- Asset quantities.
- Residual cash.
- Gross P&L.
- Spread and slippage cost decomposition.
- Net P&L.
- Ending equity.
- Compounding over repeated trades.
- Cash-only windows.
- Drawdown conventions.
- Independent account isolation.

Pay particular attention to whether scenario-specific gross P&L is being compared correctly with scenario-specific costs.

Check whether any reported numerical precision or accounting tolerance is misleading.

## 6. Verify the reported results

Reconcile the existing Stage 2C summary and manifest against the retained trades and equity curve.

Confirm the reported results are consistent with:

- 10,000 USDT starting equity per account.
- The fixed long/cash decision rule.
- The three predefined transaction-cost scenarios.
- The reported number of trades.
- No borrowing, leverage or short selling.
- The stated capital and equity conventions.

The key example is BTC Ridge:

- Frictionless: approximately +98.53%.
- Base-cost scenario: approximately −88.12%.
- 1,083 trades.

Explain whether the observed deterioration is consistent with turnover and compounding costs.

Do not infer that frictionless profitability establishes alpha: directional market drift, exposure and benchmark choice also matter.

Pay attention to the missing exchange minimum-notional/lot-size assumptions as simulated balances approach zero. Distinguish their effect on precise reported outcomes from their effect on the broader negative conclusion.

## 7. Independent methodological assessment

Identify any material limitations affecting the interpretation of the results.

In particular:

- The model predicts a 4h close-to-close return, but execution captures approximately 3h.
- 2024 is the only evaluated validation period.
- BTC and ETH are correlated.
- Historical bid/ask spreads and liquidity are not reconstructed.
- Fees and slippage are assumptions.
- The accounts repeatedly invest their full available capital.
- The strategy is fixed, long-only and trades frequently.
- Realised-equity drawdown excludes intratrade excursions.
- Retrospective provider data do not prove exact historical information availability.

Determine whether any limitation invalidates an advertised result, or merely restricts its interpretation.

Do not invent additional experiments, claims or findings.

## 8. Audit severity and reporting

Categorise findings strictly:

**Critical:** Results are materially invalid, unreproducible or contaminated by future information.

**Major:** A real correctness defect or important methodological misrepresentation that should be fixed before further research.

**Minor:** A demonstrated issue that does not materially change the results.

**Known limitation:** An existing, correctly disclosed modelling restriction.

**Optional improvement:** Nonessential future work. Keep this category short.

Every actual defect must include:

- Exact file and function.
- Reproducible evidence.
- Why it matters.
- Likely effect on results.
- Smallest viable correction.

Do not report speculative bugs without evidence.

Do not manufacture findings to justify the audit.

## 9. Avoid audit spirals

This audit must not trigger general refactoring.

Do not:

- Introduce generic frameworks or new architecture.
- Add technical indicators.
- Optimise model hyperparameters.
- Change trading thresholds.
- Change cost assumptions.
- Add new assets, intervals or exchanges.
- Modify production code.
- Automatically implement suggested fixes.
- Start Stage 2D.
- Repeatedly audit existing audits.

Only recommend immediate corrective work when there is a demonstrated critical or major issue.

If no such issues exist, explicitly recommend proceeding to Stage 2D.

## 10. Tests and evidence

Run relevant existing tests and lightweight independent checks where useful.

Do not create a disposable PostgreSQL environment solely to repeat unrelated integration tests unless a suspected issue requires it.

Distinguish passing, skipped and unexecuted tests accurately.

Check artifact hashes and preservation without modifying frozen inputs.

Document any verification that cannot be performed because local evidence is unavailable.

## 11. Deliverable

Create one concise report:

`docs/audits/001-integrated-quantitative-review.md`

Include:

1. Executive verdict: PASS, PASS WITH LIMITATIONS or BLOCKED.
2. Scope and evidence inspected.
3. Findings by severity, supported by evidence.
4. Independent timing checks.
5. Independent accounting checks.
6. Research methodology assessment.
7. What the negative backtest results establish.
8. Required fixes, if any.
9. Deferred suggestions, limited to genuinely useful ones.
10. A clear go/no-go recommendation for Stage 2D.

Archive this prompt at:

`prompts/audits/001-integrated-quantitative-review.md`

Do not edit application code, modify frozen artifacts, commit or push.

**Stop after this one audit.**
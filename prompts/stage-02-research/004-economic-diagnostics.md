# Backtest Badger — Stage 2D: Economic Diagnostics and Robustness

Act as a senior quantitative researcher and Python data engineer.

Implement Stage 2D: a reproducible economic postmortem of the fixed Stage 2C historical simulations.

The integrated quantitative audit has completed with **PASS WITH LIMITATIONS**, finding no critical or major issues.

The objective is to understand why the existing strategies fail economically and how confidently the results can be interpreted.

**Do not optimise strategies, change trading rules or repeat the integrated audit.**

## 1. Review existing implementation

Read:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/stage-02b-predictive-baselines.md`
- `docs/stage-02c-execution-backtesting.md`
- `docs/audits/001-integrated-quantitative-review.md`
- Existing forecast, execution and backtesting modules.
- Existing artifact manifests and test conventions.

Use the existing frozen Stage 2C artifacts:

`artifacts/backtests/stage-2c-v1/`

Expected Stage 2C manifest SHA-256:

`72a2bd94966a07a726d3d2876fbabd249211ecda2994f930258edb8c5007ada0`

Existing independent hourly execution data:

`artifacts/execution/binance-1h-2024-v1/`

Do not modify either artifact.

Do not open test-holdout labels or generate test-period predictions.

## 2. Research questions

Investigate these fixed questions:

1. How much economic return do the existing forecasts capture before costs?
2. How much return is consumed by fees, spread and slippage?
3. How does high trading frequency compound those costs?
4. How consistent are gross and net outcomes across calendar months?
5. Do the ML strategies outperform meaningful naive alternatives under the same execution assumptions?
6. What conclusions are and are not supported by one year of validation data?

No new trading hypothesis should be optimised during this stage.

## 3. Validate existing evidence

Build a lightweight read-only analysis of the retained:

- `trades.csv`
- `equity_curve.csv`
- `manifest.json`
- Existing native hourly reference artifact, only where needed for benchmark calculations.

Verify hashes and expected schemas.

Check that the requested inputs correspond to the fixed 2024 validation period and the previously audited simulation.

If input evidence is incompatible, fail explicitly.

Reuse existing validation helpers where appropriate. Do not duplicate or replace the audited backtesting engine.

## 4. Transaction-cost decomposition

For each existing market, model and scenario, report:

- Trade count.
- Starting and ending equity.
- Gross and net P&L.
- Total fees, spread and slippage.
- Average gross return per trade.
- Average net return per trade.
- Winning-trade percentage.
- Fraction of eligible windows invested.
- Realised-equity maximum drawdown.
- Relevant cost and turnover ratios.

Clearly distinguish **scenario-specific gross P&L** from a separately compounded frictionless account.

Never subtract the costs of one scenario from another scenario's gross P&L.

Reconcile all totals with the existing Stage 2C manifest.

## 5. Break-even cost analysis

Compute a transparent analytical cost-budget diagnostic for each fixed strategy.

Use the actual historical entry/exit reference-price ratios from its existing, unchanged trade schedule.

For a long round trip, the fixed proportional cost multiplier is:

`k = (1 - h - s)(1 - f) / ((1 + h + s)(1 + f))`

where `f`, `h` and `s` are per-side fee, half-spread and slippage rates.

Ignoring explicitly documented negligible quantity-rounding effects, cumulative account growth equals the product of the individual reference-price ratios multiplied by `k` once per executed trade.

For each fixed market/model trade sequence:

- Compute cumulative frictionless growth.
- Compute average geometric log return per executed round trip.
- Calculate the theoretical maximum effective round-trip log cost drag compatible with breaking even.
- Compare this with the actual base and stress cost drag.
- Express cost budgets in clearly labelled basis points.
- Identify strategies that lose even without costs and therefore have no nonnegative cost budget.

This analysis is descriptive, not an instruction to change fees, thresholds or strategies.

Do not search for an optimal fee, trade frequency or selection threshold.

## 6. Monthly economic breakdown

Provide a calendar-month breakdown of the existing 2024 simulation results.

For each market/model/scenario include:

- Executed trade count.
- Gross P&L attributable to that month's trades, using actual quantities.
- Total transaction costs.
- Net P&L.
- Beginning and ending account equity.
- Monthly net return.
- Invested window count.

Define month membership consistently by execution timestamp.

Ensure monthly totals reconcile to annual results.

For capital-compounded returns, use appropriate multiplicative reconciliation rather than summing monthly percentages.

Briefly describe variation across months without attributing performance to market regimes or specific events without evidence.

Do not choose favourable months or exclude unfavourable periods.

## 7. Benchmark context

Retain the existing fixed zero and training-mean baselines.

Compare the ML models against the always-positive training-mean policy, recognising differences in market exposure and turnover.

Optionally implement one conventional, fixed buy-and-hold benchmark using the existing verified hourly references:

- One purchase at the 2024-01-01 01:00 UTC reference.
- One sale at the 2024-12-31 20:00 UTC reference.
- Starting capital 10,000 USDT.
- Apply the same predefined cost scenarios.

This is a conventional reference benchmark, not an optimised strategy.

Its holding period and exposure differ from the three-hour trading windows. Label that difference explicitly and do not interpret simple return differences as risk-adjusted alpha.

Do not implement additional benchmarks.

## 8. Research interpretation

Discuss:

- How turnover compounds transaction costs.
- Why modest predictive improvements may be economically insignificant.
- Why positive frictionless returns may reflect market exposure rather than alpha.
- Why low transaction costs alone do not guarantee a viable signal.
- Why 2024 validation performance cannot establish robustness across market regimes.
- Why BTC/ETH correlation weakens claims of independent replication.
- Why a model's 4h target differs from the simulated three-hour trading exposure.
- Why retrospective hourly reference prices and assumed spreads do not establish actual executable returns.
- Why exchange lot sizes and minimum-notional requirements could change precise late-stage results.

The analysis should describe the current fixed system, not propose performance claims unsupported by evidence.

Do not perform statistical-significance testing without an explicitly appropriate time-series methodology. Do not add bootstrap machinery merely to produce confidence intervals.

## 9. Implementation

Prefer a single small analysis module:

`src/backtest_badger/economics.py`

Add a CLI command such as:

`badger analyse-economics --backtest artifacts/backtests/stage-2c-v1 --output artifacts/economics/stage-2d-v1`

Use British spelling consistently with the existing project if convenient.

The command should run offline.

Use only standard-library functionality and existing dependencies where possible.

Do not create a new database, experiment framework, scheduler or reporting service.

Do not refit existing ML models or resimulate trades with altered decisions.

## 10. Artifacts

Generate a new immutable, gitignored analysis directory containing:

- `monthly_results.csv`
- `cost_diagnostics.csv`
- `manifest.json`
- `summary.md`

Record:

- Source artifact identities and hashes.
- Fixed economic assumptions.
- Calculation definitions.
- Models and markets.
- Reconciled totals.
- Benchmark conventions, if implemented.
- Analysis implementation hash.
- Output file hashes.
- Scientific limitations.

Require deterministic reproduction using the same environment and inputs.

Never overwrite previous outputs.

## 11. Tests

Write focused synthetic tests covering:

- Cost decomposition.
- Geometric compounding.
- Break-even cost calculations.
- Strategies that lose frictionlessly.
- Cash-only accounts.
- Monthly P&L reconciliation.
- Month-boundary assignment.
- Independent markets and accounts.
- Correct handling of zero trades.
- Benchmark fee calculations, if implemented.
- Input integrity and provenance.
- Deterministic artifacts.

Run the relevant existing test suite and Ruff.

There is no need to rerun the entire independent quantitative audit.

Do not provision PostgreSQL solely for unrelated integration tests. Clearly report skipped tests if the isolated test configuration is unavailable.

## 12. Documentation and maintenance

Create:

`docs/stage-02d-economic-diagnostics.md`

Update:

- `docs/architecture.md`
- `docs/roadmap.md`

Correct the single minor documentation finding from Audit 001:

- Update the stale README implementation status to recognise that Stage 2C backtesting is implemented.

Archive this exact prompt at:

`prompts/stage-02-research/004-economic-diagnostics.md`

Do not add another audit.

Do not automatically add a third Field Note. Field Note 002 already discusses the central transaction-cost finding.

## 13. Explicit exclusions

Do not:

- Add or modify features.
- Retrain models.
- Tune thresholds.
- Reduce trading frequency by selecting favourable subsets.
- Optimise strategies against validation results.
- Change execution timing.
- Change fee, spread or slippage assumptions.
- Evaluate the 2025–2026 test holdout.
- Introduce new market data.
- Add live predictions or paper trading.
- Build website components.
- Refactor the existing research architecture.

Do not modify existing frozen artifacts, the development database or the old crypto-trading-platform repository.

Do not commit or push.

## 14. Completion report

Provide:

1. Evidence and hashes verified.
2. Annual and monthly economic results.
3. Cost decomposition and break-even diagnostics.
4. Benchmark comparison.
5. Important economic interpretations.
6. Scientific limitations.
7. Test and reproducibility results.
8. Files created or modified.
9. Recommendation for the next development stage.

**Stop after Stage 2D. Do not begin Stage 3.**
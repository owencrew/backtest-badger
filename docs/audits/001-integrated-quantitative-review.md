# Integrated Quantitative Review 001

**Date:** 2026-10-14

**Verdict: PASS WITH LIMITATIONS**

**Stage 2D recommendation: GO.** No critical or major defect was demonstrated.
The retained results are trustworthy as the specified retrospective simulations,
not as executable returns, evidence of alpha or live trading performance.

## 1. Scope and evidence

One read-only audit through Stage 2C, at commit
`b0b4fcd0403ee39a3cc6542d6873df073b046479` (initial worktree clean).
Inspected `AGENTS.md`, architecture, relevant Stage 1/2 guides, README, Field Note
002, the eight requested pipeline modules, Stage 1 export/archive handling,
CLI dispatch, relevant tests, actual manifests, and retained forecasts, trades,
equity curves, summaries and reproduction copies.

Local artifact roots under `artifacts/` were:

- `exports/binance-4h-history-v1/`
- `research/stage-2a-v1/`
- `experiments/stage-2b-v1/`
- `execution/binance-1h-2024-v1/`
- `backtests/stage-2c-v1/`

Independent checks used separate temporary Python calculations, not the
application's feature, metric or accounting reconciliation functions. Synthetic
accounting expectations used exact rational arithmetic; retained-account replay
used 120-digit Decimal arithmetic and rational quantity flooring. No new strategy
experiment, market-data download, database access or real-data pipeline run was
performed. The independent Ridge normal-equation calculation verified existing
forecasts with unchanged inputs and alpha; it was not model selection or tuning.

**Holdout boundary:** whole-file SHA-256 checks treated bytes opaquely. Research
lines were filtered using the split prefix **before decoding their feature/label
suffix**; all test lines were skipped. Only training/validation targets entered
calculations. Post-2024 source candles received identity/grid checks, not economic
replay. No 2025–2026 labels were inspected, forecasts generated or performance
scored. Inspected code and retained evidence show no holdout evaluation; they
cannot establish a history of activity outside this repository.

## 2. Findings by severity

**Critical: none. Major: none.** No demonstrated leakage, timing, identity,
affordability, accounting or reported-performance defect.

**Minor M1 — README implementation status is stale.**

- Location: [README.md](../../README.md), lines 30–31, `Status` section
  (documentation; no function).
- Reproduce: `sed -n '28,31p' README.md` says backtesting remains unimplemented;
  [backtest.py](../../src/backtest_badger/backtest.py),
  `backtest_validation`, lines 321–383, and the retained Stage 2C manifest/trades
  demonstrate implementation and completed simulation.
- Effect: misstates project scope to readers; no numerical or scientific effect.
- Smallest correction: link the completed Stage 2C guide and remove backtesting
  from the list of unimplemented capabilities during routine documentation work.
  This does not block further research and was not changed by this audit.

**Known limitations:** the disclosed restrictions in section 7 below.
No other defect is inferred from a hypothetical future use case.

## 3. Source integrity and preservation

All five current manifest hashes matched the documented releases:

| Manifest directory under `artifacts/` | SHA-256 |
| --- | --- |
| `exports/binance-4h-history-v1` | `a78d34256d3bcd789e6cc19a2807f432d1ffa1a73ecc81b5ea16b3859759a98a` |
| `research/stage-2a-v1` | `a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e` |
| `experiments/stage-2b-v1` | `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581` |
| `execution/binance-1h-2024-v1` | `1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d` |
| `backtests/stage-2c-v1` | `72a2bd94966a07a726d3d2876fbabd249211ecda2994f930258edb8c5007ada0` |

CSV hashes, manifest input/output links, acquisition hashes and all recorded Stage
2 implementation fingerprints also matched. Existing Stage 2A/2B/2C reproduction
copies match every corresponding output byte. This is verification of retained
copies, not a claim that this audit reran those experiments.

The source grid contains 39,910 unique candles, 19,955 per market. Each market's
36 gaps exactly equal 17 source absences plus 19 irregular-close exclusions.
Independently compared all **32,254 pre-2025 candles** against **178 retained
monthly ZIPs**: economic fields, proper close boundaries and archive provenance
agree; ZIP hashes and retained official checksum sidecars match. Independently
replayed all **24 native 1h ZIPs** against the execution CSV: **17,568 hours**,
8,784 per symbol, with no duplicate, missing or mismatched hourly reference.

Before/after SHA-256, size and modification-time checks preserved all **914
pre-existing artifact/source/test files** inventoried, excluding bytecode.
Original provider publication times, historical revisions as seen by traders,
actual fills and off-machine backup availability cannot be verified from this
local evidence. No production or sibling repository was accessed.

## 4. Causality, prediction and independent timing checks

[features.py](../../src/backtest_badger/features.py), `causal_features` and
`build_rows`, use exact four-hour timestamp lookups. Seven completed candles
`t−6 … t` determine features; only the label reads `t+1`. Missing identities
cannot shorten the horizon. The full required window excludes gaps and known
anomalies. In particular, BTC's flagged 2017-09-06 20:00 candle excludes the
otherwise complete window ending 2017-09-07 20:00; the exclusion manifest records
this additional row. Earlier affected windows already cross gaps.

Independently rebuilt eligibility, five features and next-candle targets for all
**31,955 training/validation rows**. Maximum absolute numerical difference was
`3.56e-15`. Counts agree: BTC/ETH training 13,782/13,783; validation 2,195 each.
Labels are available at `open + 8h + 60s` and must precede the partition end.
The December 31 16:00 rows are correctly purged at both the 2023/2024 and 2024/2025
boundaries. December 31 20:00 belongs to the following availability-based
partition; its older feature history is legitimate past information.

[model_data.py](../../src/backtest_badger/model_data.py), `select_rows`, excludes
test targets before conversion. [evaluation.py](../../src/backtest_badger/evaluation.py),
`fit_models` and `evaluate_models`, create separate market fits, fit Ridge scaling
and coefficients using training only, and keep validation labels in scoring.
Feature order is fixed; boosting has seed 42, full subsampling and no early
stopping; Ridge uses SVD and numerical execution has a one-thread limit.

Independent training means/scaler checks and the Ridge equation
`β = (ZᵀZ + I)⁻¹ Zᵀ(y − mean_train)` reproduce all retained Ridge validation
forecasts within `1.12e-16`. Independently recomputed all eight model/market metric
sets: maximum difference `2.23e-16`. MAE, RMSE, both baseline improvements and
training-mean-relative MSE skill are correct. Skill is not ordinary validation R².
Zero predictions abstain; constant predictions have undefined correlation;
positive training means have defined direction accuracy. Exact zero targets count
as incorrect for nonzero forecasts. Tests cover near-constant and zero-denominator
cases. No inspected report claims statistical significance or reliable alpha.

### Complete retained example: BTC Ridge, 2024-01-02

The seven native 4h closes from January 1 08:00 through January 2 08:00 are
`42690.20, 42783.05, 43517.99, 44179.55, 45402.38, 45455.53, 45433.99`.
Current volume is `10027.39458`; the six prior volumes sum to `46000.92649`.
These produce, in the fixed feature order:

```text
[-0.000473982047727018, 0.027998491005768129, 0.062291117644698787,
  0.035629761050027180, 1.3078946897532369]
```

The 08:00 candle completes at **12:00**; features become eligible at **12:01**.
The next candle opens at 12:00 and closes at 16:00 at `45184.82`, giving the target
`ln(45184.82 / 45433.99) = −0.0054993136184189875`, available at **16:01**.
The retained Ridge forecast is `+0.00058102395957460365`; the independent
calculation gives `+0.0005810239595746044`, so the fixed rule enters long.

Entry uses the native **13:00 open, 45302.00**; exit uses the native **16:00 open,
45184.83**. The one-cent difference from the target's close is preserved.
[forecast_data.py](../../src/backtest_badger/forecast_data.py), `schedule` and
`should_enter`, determine timing/direction without execution prices.
`simulate_account` plans decisions before accessing future references.

All 17,560 forecasts have the correct market/time/model identity. Each account has
2,195 ordered windows; its entries follow availability by 59 minutes and precede
exits by three hours. First signal: January 1 00:01; last: December 31 16:01;
last exit: December 31 20:00. No duplicate trade, overlapping position, price-driven
decision or fallback to the already-passed 4h close was found. Missing execution
references fail even for cash windows. Hourly opens remain retrospective price
references, not proof that the order could have filled.

## 5. Independent accounting checks

For cash `C`, references `P0/P1`, fee `f`, half-spread `h` and slippage `s`, checked:

```text
B = P0(1+h+s); S = P1(1-h-s)
q = floor(10^24 C / [B(1+f)]) / 10^24
residual = C − qB(1+f)
ending cash = residual + qS(1−f)
gross = q(P1−P0)
fees = qf(B+S); spread = qh(P0+P1); slippage = qs(P0+P1)
net = ending cash − C = gross − fees − spread − slippage
```

The independent floor uses an exact rational quotient. Every quantity is positive,
affordable, and maximal at the numerical increment; residual cash is retained.
All **27,936 round trips**, **52,704 equity observations** and **24 isolated accounts**
reconcile. Each account starts with 10,000 USDT, and every recorded endpoint is
flat cash. Trade membership equals `forecast > 1e-12` in every scenario.
Cash windows preserve balances; win rates, exposure, mean trade returns and
initial/endpoint peak-to-trough drawdowns match the manifest. All 24 rounded
result rows match both the retained summary and Stage 2C guide.

Nine synthetic comparisons covered falling, flat and rising references under
all three scenarios. From 10,000 USDT with entry reference 100:

| Scenario | Exit 90: ending cash | Exit 100 | Exit 110 |
| --- | ---: | ---: | ---: |
| Frictionless | 9000.000000 | 10000.000000 | 11000.000000 |
| Base | 8976.630388 | 9974.033764 | 10971.437140 |
| Stress | 8958.695055 | 9954.105617 | 10949.516178 |

A separate long/cash/long example gives `10000 → 11000 → 11000 → 9900` and 10%
realised maximum drawdown, verifying compounding, a cash-only window and the
running-peak convention independently.

For the January 2 trace, base-adjusted buy/sell prices are
`45315.590600` / `45171.274551`; quantity is `0.220462677313833213046523 BTC`.
Cash before is `10000.386824161307`; residual is approximately `1.0260e-20` USDT.
Buy/sell fees are `9.990396427734` / `9.958580125192`; gross is `−25.831611900862`,
spread `1.994896880344`, slippage `3.989793760688`, net `−51.765279094820`, and
ending cash `9948.621545066488`. These displayed values are rounded.

Additional retained BTC Ridge base examples, selected across the year:

| Trade number | Entry UTC | Cash before | Net P&L | Cash after |
| --- | --- | ---: | ---: | ---: |
| 1 | 2024-01-01 01:00 | 10000.000000 | −59.951736 | 9940.048264 |
| 542 | 2024-07-02 01:00 | 3485.896881 | +2.663594 | 3488.560475 |
| 1083 | 2024-12-31 05:00 | 1186.129975 | +2.201997 | 1188.331972 |

Money reconciliation is exact for retained finite-decimal quantities. Differences
in independently recomputed ratio metrics are below `5e-81`; the maximum ending
cash difference from an unrounded-quantity multiplicative calculation is
`4.774e-20` USDT. The application's `1e-60` tolerance and 80-digit arithmetic are
internal numerical checks, not economically attainable accuracy or exchange
precision. No material precision misrepresentation was found in the disclosures.

## 6. Reported deterioration and what the negative results establish

Fixed per-side assumptions are frictionless `(0,0,0)`, base `(10,1,2)` and stress
`(10,3,10)` bps for fee, half-spread and slippage respectively. No borrowing,
leverage or shorts occur. BTC Ridge makes **1,083 trades** in each:

| Scenario | Ending equity USDT | Net return |
| --- | ---: | ---: |
| Frictionless | 19852.925195 | +98.529252% |
| Base | 1188.331972 | −88.116680% |
| Stress | 136.224510 | −98.637755% |

Ignoring negligible quantity-rounding residuals, each invested window multiplies
cash by `(P1/P0) × k`, where
`k = (1−h−s)(1−f) / [(1+h+s)(1+f)]`.
Base `k = 0.9974033763896805`, approximately 25.966 bps lost on a flat round trip.
Thus `19852.925195 × k^1083 ≈ 1188.331972`, since `k^1083 ≈ 0.05985677`.
The deterioration is quantitatively consistent with turnover and compounding.

The base account's own totals reconcile:
`3438.967312 − 9423.565408 − 942.356644 − 1884.713288 = −8811.668028` USDT
(gross minus fees, spread and slippage; rounded here). Subtracting these costs
from the frictionless gross `9852.925195` would mix different quantities and
capital paths and is invalid. The reported treatment is correct.

All trading base accounts lose 87.36%–99.63%; all trading stress accounts lose
money; zero-model cash accounts retain 10,000. This establishes poor results for
these fixed 2024 policies under the stated assumptions. It does not establish
that every strategy is unprofitable. Nor does frictionless profitability establish
alpha: BTC's always-positive training mean earns +98.74% frictionlessly without
selective ML timing. Market drift, exposure and benchmark choice matter; no
risk/exposure-adjusted alpha comparison is supplied or claimed.

## 7. Known methodological limitations

The [Stage 2C guide](../stage-02c-execution-backtesting.md) and retained summary
correctly disclose these interpretation limits:

- Four-hour close-to-close prediction and delayed three-hour trading exposure are
  different outcomes. Predictive error improvements do not establish trading edge.
- Only 2024 validation is evaluated; correlated BTC/ETH results are not independent
  replications. No statistical-significance or out-of-sample profitability claim
  follows, and further work must preserve holdout discipline.
- Retrospective single-provider candles do not reconstruct historical information
  availability, bid/ask spreads, order books, liquidity, market impact or fills.
  Fees, spread and slippage are explicit assumptions.
- Repeated full-capital long/cash positions create substantial turnover. Separate
  10,000-USDT accounts are comparisons, not one shared funded portfolio.
- Drawdown uses realised flat equity and omits intratrade excursions. Window
  exposure is not continuous-time exposure; unreported Sharpe is not inferred.
- Exchange minimum-notional/lot-size filters are absent. The stress ETH
  training-mean account ends at **0.460921 USDT**, not exact bankruptcy despite
  a rounded −100.00% display. Actual filters could prevent later orders and change
  precise trade counts, terminal balances and cost totals. They do not invalidate
  the arithmetic of this disclosed unconstrained simulation or turn its losses
  into evidence of viability. Exchange-compliant outcomes have not been measured.

These restrictions limit interpretation; none invalidates the advertised
conditional simulation result. Local artifact retention also lacks verified
durable backup.

## 8. Tests and verification limits

Executed from the existing virtual environment, without loading `.env`:

```sh
env -u BADGER_TEST_ADMIN_DSN .venv/bin/pytest -q -p no:cacheprovider
.venv/bin/ruff check . --no-cache
.venv/bin/ruff format --check . --no-cache
git diff --check
```

**343 passed, 173 skipped** in 10.51 seconds. The skipped PostgreSQL integration
cases were not executed; no disposable database was created. Ruff passed;
71 files were already formatted. Whitespace checks passed. Relevant existing
synthetic tests cover future-value perturbation, missing timestamps/anomalies,
label purging, train-only scaling and fitting, validation-label perturbation,
market isolation, guarded holdout access, deterministic fitting, constant
predictions, timing, decision-before-price access, source replay, affordability,
account isolation and deterministic output. No remote CI run is claimed.

Independent checks above verified retained evidence beyond those tests. They do
not reconstruct historical broker fills or re-execute database transactions.

## 9. Required fixes and deferred suggestions

**Required fixes before Stage 2D: none.** No refactoring, model/threshold/cost
changes or new experiments are recommended by this audit.

Deferred: correct M1 in routine documentation maintenance; preserve the frozen
artifacts in a durable off-machine backup. Neither suggestion requires expanding
this audit or repeating it.

## 10. Go/no-go

**Proceed to Stage 2D**, retaining the stated limits and untouched holdout.
This recommendation concerns scoped research, not promotion to trading.
This audit stops here: only this report and the
[verbatim prompt archive](../../prompts/audits/001-integrated-quantitative-review.md)
were added. Application code and frozen evidence were preserved; nothing was
committed, pushed or deployed.

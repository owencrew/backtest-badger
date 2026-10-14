# Stage 2D — Economic diagnostics and robustness limits

Implemented for review on 2026-10-14. This is a reproducible **economic postmortem
of the unchanged Stage 2C historical simulations**, following Audit 001's
**PASS WITH LIMITATIONS**. It does not repeat that audit or optimise a strategy.

Every trading account loses under base and stress assumptions, in **every calendar
month**. Positive frictionless returns are insufficient evidence of useful ML:
both ML models trail the always-positive training-mean policy frictionlessly in
both markets. ETH boosting loses even at zero costs. Costly ML accounts lose less
than the training-mean accounts, but their lower exposure and turnover prevent
that comparison from establishing alpha. Cash retains its starting balance.

## Run and reproduce

```sh
uv run --locked badger analyse-economics \
  --backtest artifacts/backtests/stage-2c-v1 \
  --output artifacts/economics/stage-2d-v1

uv run --locked badger analyse-economics \
  --backtest artifacts/backtests/stage-2c-v1 \
  --output artifacts/economics/stage-2d-v1-reproduction
```

These two directories now exist locally; use a fresh destination for further
runs. The command is offline, requires no environment/database configuration and
never overwrites a destination. The four outputs are `monthly_results.csv`,
`cost_diagnostics.csv`, `manifest.json` and `summary.md`, under gitignored
`artifacts/`. The manifest is written last with existing retention helpers.
A write failure may leave an incomplete directory; investigate and choose a new
one. Immutability means refusal to overwrite, not a filesystem lock or backup.

## Evidence and preservation

The exact bytes parsed must match the audited Stage 2C manifest pin. Its output
hashes authenticate all retained trades, equity observations and the summary:

| Verified Stage 2C file | SHA-256 |
| --- | --- |
| `equity_curve.csv` | `f0293cf1e9872f07aaf39457388254e3bfedfc576eb59955506c74cfa5054b39` |
| `manifest.json` | `72a2bd94966a07a726d3d2876fbabd249211ecda2994f930258edb8c5007ada0` |
| `summary.md` | `b51f1851f1831edbc1dfa74d6803e52893983b79d5a0d884684ed1e40ddce6c1` |
| `trades.csv` | `bd2055ef06baab59ffa301583080734f2ef8c683634328cdf14a6529d6c4f37b` |

Checks enforce the exact CSV schemas, finite numbers, two market/four model/three
scenario identities, canonical ordering, complete 2,195-window 2024 equity grids,
valid signal/entry/exit timing, unique trades and matching schedules/reference
prices across scenarios. The zero policy stays cash; training mean trades every
window. Retained trade cash changes, scenario gross/fees/net, equity endpoints,
counts, win rates, mean net returns, exposure and realised drawdowns reconcile to
the Stage 2C manifest using its 80-digit Decimal context and 1e-60 tolerance.
This is an aggregation/reconciliation check, not a new execution-engine audit.

The pinned manifest links the original forecasts and independent hourly evidence:

- Forecast manifest: `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581`.
- Validation predictions: `e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674`.
- Hourly manifest: `1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d`.
- Hourly CSV: `39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a`.

The command records these upstream identities as provenance from the pinned
manifest; it does not independently reopen/replay those upstream sources. The
retained zero/mean comparisons need no new benchmark prices. No optional
buy-and-hold benchmark was added. A separate before/after preservation inventory
verified identical hashes, sizes and modification times for all 55 files in the
Stage 2C and hourly artifact directories. No research CSV, test-holdout labels or
prediction generation was involved; no database or production access occurred.

## Annual results and cost budgets

Every account starts at **10,000 USDT**. The table shows all scenarios, including
the six zero-model cash accounts. Gross means the sum of actual scenario quantities
multiplied by exit-minus-entry reference prices. Costs and gross are always taken
from the same scenario. Tables round; full precision remains in CSV/JSON.

| Market | Model | Scenario | Trades | Ending equity | Gross P&L | Fees | Spread | Slippage | Net P&L | Net % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | zero | frictionless | 0 | 10000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| BTCUSDT | zero | base | 0 | 10000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| BTCUSDT | zero | stress | 0 | 10000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| BTCUSDT | training_mean | frictionless | 2195 | 19873.9084 | 9873.9084 | 0.0000 | 0.0000 | 0.0000 | 9873.9084 | 98.7391 |
| BTCUSDT | training_mean | base | 2195 | 66.0335 | 2582.5482 | 9628.0881 | 962.8089 | 1925.6178 | -9933.9665 | -99.3397 |
| BTCUSDT | training_mean | stress | 2195 | 0.8189 | 1871.2475 | 5161.0545 | 1548.3171 | 5161.0570 | -9999.1811 | -99.9918 |
| BTCUSDT | ridge | frictionless | 1083 | 19852.9252 | 9852.9252 | 0.0000 | 0.0000 | 0.0000 | 9852.9252 | 98.5293 |
| BTCUSDT | ridge | base | 1083 | 1188.3320 | 3438.9673 | 9423.5654 | 942.3566 | 1884.7133 | -8811.6680 | -88.1167 |
| BTCUSDT | ridge | stress | 1083 | 136.2245 | 2355.6810 | 5312.8055 | 1593.8426 | 5312.8085 | -9863.7755 | -98.6378 |
| BTCUSDT | gradient_boosting | frictionless | 1941 | 16276.5263 | 6276.5263 | 0.0000 | 0.0000 | 0.0000 | 6276.5263 | 62.7653 |
| BTCUSDT | gradient_boosting | base | 1941 | 104.6768 | 1914.1383 | 9084.2010 | 908.4202 | 1816.8403 | -9895.3232 | -98.9532 |
| BTCUSDT | gradient_boosting | stress | 1941 | 2.1573 | 1553.1058 | 5022.1504 | 1506.6457 | 5022.1524 | -9997.8427 | -99.9784 |
| ETHUSDT | zero | frictionless | 0 | 10000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ETHUSDT | zero | base | 0 | 10000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ETHUSDT | zero | stress | 0 | 10000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ETHUSDT | training_mean | frictionless | 2195 | 11186.6520 | 1186.6520 | 0.0000 | 0.0000 | 0.0000 | 1186.6520 | 11.8665 |
| ETHUSDT | training_mean | base | 2195 | 37.1690 | 1996.1582 | 9199.2223 | 919.9223 | 1839.8446 | -9962.8310 | -99.6283 |
| ETHUSDT | training_mean | stress | 2195 | 0.4609 | 1601.8504 | 5044.0812 | 1513.2250 | 5044.0833 | -9999.5391 | -99.9954 |
| ETHUSDT | ridge | frictionless | 832 | 10998.4007 | 998.4007 | 0.0000 | 0.0000 | 0.0000 | 998.4007 | 9.9840 |
| ETHUSDT | ridge | base | 832 | 1264.3388 | 1240.3473 | 7673.8526 | 767.3853 | 1534.7706 | -8735.6612 | -87.3566 |
| ETHUSDT | ridge | stress | 832 | 239.4401 | 1196.6518 | 4764.0042 | 1429.2017 | 4764.0058 | -9760.5599 | -97.6056 |
| ETHUSDT | gradient_boosting | frictionless | 1066 | 9190.2728 | -809.7272 | 0.0000 | 0.0000 | 0.0000 | -809.7272 | -8.0973 |
| ETHUSDT | gradient_boosting | base | 1066 | 574.9598 | 1361.3869 | 8297.2515 | 829.7252 | 1659.4504 | -9425.0402 | -94.2504 |
| ETHUSDT | gradient_boosting | stress | 1066 | 68.1900 | 1591.1881 | 5009.9980 | 1503.0000 | 5010.0001 | -9931.8100 | -99.3181 |

## Fixed-sequence cost budgets

Effective round-trip **log-cost** basis points, not per-side fees. Undefined budgets distinguish cash accounts and frictionless losses.

| Market | Model | Frictionless % | Mean log return bps | Budget bps | Status | Base drag bps | Stress drag bps |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| BTCUSDT | zero | 0.0000 | undefined | undefined | no_trades | 26.0000 | 46.0000 |
| BTCUSDT | training_mean | 98.7391 | 3.1290 | 3.1290 | nonnegative_budget | 26.0000 | 46.0000 |
| BTCUSDT | ridge | 98.5293 | 6.3321 | 6.3321 | nonnegative_budget | 26.0000 | 46.0000 |
| BTCUSDT | gradient_boosting | 62.7653 | 2.5097 | 2.5097 | nonnegative_budget | 26.0000 | 46.0000 |
| ETHUSDT | zero | 0.0000 | undefined | undefined | no_trades | 26.0000 | 46.0000 |
| ETHUSDT | training_mean | 11.8665 | 0.5109 | 0.5109 | nonnegative_budget | 26.0000 | 46.0000 |
| ETHUSDT | ridge | 9.9840 | 1.1438 | 1.1438 | nonnegative_budget | 26.0000 | 46.0000 |
| ETHUSDT | gradient_boosting | -8.0973 | -0.7921 | undefined | loses_without_costs | 26.0000 | 46.0000 |


For the unchanged sequence of N round trips:

```text
R = product(P_exit / P_entry)
g = sum(ln(P_exit / P_entry)) / N
k = (1-h-s)(1-f) / ((1+h+s)(1+f))
analytical ending equity = 10,000 × R × k^N
round-trip log-cost drag in bps = -ln(k) × 10,000
maximum nonnegative log-cost budget in bps = g × 10,000, only if g >= 0
```

The rates f, h and s are per-side fee, half-spread and slippage, obtained by
dividing the fixed bps assumptions by 10,000. Frictionless is (0,0,0); base is
(10,1,2); stress is (10,3,10). Nothing was fitted or searched. A negative g means
**no nonnegative budget exists**, represented as null/blank with an explicit
`loses_without_costs` status, not a misleading zero budget. With no trades, R=1
and per-trade averages/budgets are undefined (`no_trades`). A traded flat-price
sequence has an actual zero budget.

Log-cost bps differ from flat-price round-trip loss: base is approximately
26.000007 log bps versus 25.966236 simple bps; stress is 46.000021 log bps versus
45.894383 simple bps. Neither is a per-side fee quote. The budget is descriptive
and does not recommend changing fees, thresholds or trade frequency.

Analytical growth omits only the existing numerical quantity floor at 1e-24 asset
units and residual cash. Its maximum absolute endpoint difference from the
retained accounts is **4.77348e-20 USDT**, below the explicitly recorded 1e-15-USDT
check. These are numerical reconciliation figures, not executable precision.

For BTC Ridge, base k^1083 is approximately 0.05985677: the separately compounded
frictionless balance of 19,852.925195 USDT becomes approximately 1,188.331972 USDT
under base costs. Its **own** base accounting is:

```text
3,438.967312 gross
− 9,423.565408 fees − 942.356644 spread − 1,884.713288 slippage
= −8,811.668028 net P&L (rounded)
```

Subtracting those costs from the frictionless gross of 9,852.925195 would mix
capital paths and quantities. ETH boosting illustrates why this matters: its
base scenario gross is positive despite its compounded frictionless loss.
Earlier/later returns receive different monetary weights as costly capital shrinks.

## Turnover, exposure and existing benchmarks

Training mean is positive in each market and enters all 2,195 windows; zero
enters none. Each model has an independent 10,000-USDT account. These are not
components of a pooled funded portfolio. Invested-window fraction is not the
fraction of continuous calendar time spent holding an asset.

| Market | Model | Trades | Invested windows % | Base two-sided turnover / starting equity | Base costs / positive gross |
| --- | --- | ---: | ---: | ---: | ---: |
| BTCUSDT | zero | 0 | 0.00 | 0.00 | undefined |
| BTCUSDT | training_mean | 2195 | 100.00 | 962.81 | 4.85 |
| BTCUSDT | ridge | 1083 | 49.34 | 942.36 | 3.56 |
| BTCUSDT | gradient_boosting | 1941 | 88.43 | 908.42 | 6.17 |
| ETHUSDT | zero | 0 | 0.00 | 0.00 | undefined |
| ETHUSDT | training_mean | 2195 | 100.00 | 919.92 | 5.99 |
| ETHUSDT | ridge | 832 | 37.90 | 767.39 | 8.04 |
| ETHUSDT | gradient_boosting | 1066 | 48.56 | 829.73 | 7.92 |

Two-sided turnover is the sum of actual entry and exit notionals divided by
starting equity. The CSV also reports cumulative entry notional divided by each
trade's current pre-entry equity, so shrinking cash does not hide repeated
full-capital exposure. Cost/start-equity ratios can exceed one: capital may be
reused and earn gross gains while paying costs throughout the year.

BTC Ridge earns 98.53% frictionlessly versus the training mean's 98.74%, using
1,083 rather than 2,195 trades. BTC boosting earns 62.77% with 1,941 trades.
ETH Ridge earns 9.98% versus the mean's 11.87%, while ETH boosting loses 8.10%.
ML base/stress outcomes exceed the training-mean returns but remain severe losses;
zero cash outperforms every costly trading account. This establishes neither
risk-adjusted alpha nor predictive superiority. Lower exposure and turnover are
material differences, not controlled-away explanations.

The annual CSV includes arithmetic mean gross/net returns per trade (each P&L
divided by its own pre-entry equity), strictly positive net winning-trade
percentage, realised-equity maximum drawdown, cost/turnover ratios and the full
budget diagnostic for each scenario. Empty-trade averages and zero/nonpositive
gross cost ratios are explicitly undefined.

## All twelve calendar months

**UTC exit execution time** assigns the whole round trip, both sides' fees and
other costs, and the invested window. An entry at January 31 21:00 exiting at
February 1 00:00 belongs entirely to February. A cash window belongs to its
endpoint month. Monthly beginning/ending equity carries the last recognised
realised balance; this is not mark-to-market NAV at a calendar boundary while
a trade remains open. It aligns the recorded flat endpoints with realised P&L.

`monthly_results.csv` contains **288 rows**: all twelve months for all 24 accounts,
including cash-only accounts. Every row includes trades, invested and eligible
windows, actual-quantity gross P&L, fees/spread/slippage, total costs, net P&L,
beginning/ending equity and monthly net return. The generated `summary.md` prints
every month/account's money figures. No months were selected or excluded.

For every account, monthly money and counts sum to annual totals. Monthly returns
compound: `product(1 + monthly_net_return) = ending / starting equity`; percentages
must not be added. These checks run before output publication.

All base trading accounts' monthly net returns (%):

| Month | BTC mean | BTC Ridge | BTC boosting | ETH mean | ETH Ridge | ETH boosting |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-01 | -29.97 | -9.05 | -25.89 | -32.85 | -9.30 | -10.26 |
| 2024-02 | -16.29 | -4.95 | -22.56 | -16.67 | -6.37 | -11.49 |
| 2024-03 | -39.07 | -20.61 | -33.49 | -40.14 | -16.69 | -23.75 |
| 2024-04 | -44.78 | -29.81 | -42.17 | -46.26 | -25.27 | -26.38 |
| 2024-05 | -30.78 | -11.39 | -28.59 | -24.33 | -0.68 | -13.09 |
| 2024-06 | -41.46 | -17.89 | -34.22 | -41.24 | -15.37 | -23.50 |
| 2024-07 | -36.35 | -20.98 | -38.95 | -44.67 | -24.44 | -26.34 |
| 2024-08 | -47.47 | -20.67 | -46.51 | -55.72 | -30.26 | -29.66 |
| 2024-09 | -30.43 | -11.83 | -30.90 | -32.12 | -9.93 | -27.38 |
| 2024-10 | -28.41 | -13.54 | -23.82 | -34.85 | -13.69 | -21.00 |
| 2024-11 | -23.84 | -12.66 | -16.07 | -27.30 | -11.55 | -13.42 |
| 2024-12 | -34.84 | -18.76 | -30.04 | -41.06 | -21.48 | -24.63 |

Gross and net consistency across **all** scenarios follows. Each cell is the count
of strictly positive gross months / strictly positive net months, out of twelve:

| Market | Model | Frictionless | Base | Stress |
| --- | --- | ---: | ---: | ---: |
| BTCUSDT | zero | 0 / 0 | 0 / 0 | 0 / 0 |
| BTCUSDT | training_mean | 8 / 8 | 8 / 0 | 8 / 0 |
| BTCUSDT | ridge | 10 / 10 | 10 / 0 | 10 / 0 |
| BTCUSDT | gradient_boosting | 8 / 8 | 8 / 0 | 8 / 0 |
| ETHUSDT | zero | 0 / 0 | 0 / 0 | 0 / 0 |
| ETHUSDT | training_mean | 6 / 6 | 6 / 0 | 6 / 0 |
| ETHUSDT | ridge | 7 / 7 | 7 / 0 | 7 / 0 |
| ETHUSDT | gradient_boosting | 4 / 4 | 4 / 0 | 4 / 0 |

Gross outcomes vary in sign across months, whereas every base and stress trading
month loses net. Base Ridge ranges from −29.81% to −4.95% for BTC and −30.26% to
−0.68% for ETH. Zero has twelve exactly flat months. These are descriptive
calendar differences; no market regime, specific event or causal explanation is
inferred from the month labels. Even positive gross months do not establish an
edge after recurring costs.

## Interpretation and scientific limitations

- High turnover compounds proportional costs through `k^N`; adding per-side bps
  or subtracting another scenario's dollar costs misstates the economic path.
- Modest 4h forecast error improvements do not establish profitable sign decisions.
  The delayed three-hour opening-reference exposure is a different target from
  the fitted four-hour close-to-close label.
- Long-only frictionless gains can reflect market exposure rather than alpha.
  The meaningful existing training-mean comparison is positive without selective
  ML timing, and raw differences do not adjust for risk or exposure.
- Low costs cannot rescue a sequence that loses frictionlessly; ETH boosting
  demonstrates this within the fixed system, without generalising to all signals.
- One fixed 2024 validation year cannot establish robustness across market regimes.
  Twelve monthly observations are descriptive, not independent replications.
  BTC/ETH correlation also weakens claims of independent confirmation. No
  statistical-significance tests, bootstrap intervals or probability-of-success
  claims are made. The 2025–2026 test holdout remains unexamined.
- Retrospective single-provider hourly opening references and assumed constant
  spreads/slippage do not prove actual executable returns, historical information
  availability, liquidity, market impact or broker fills.
- Drawdown observes only initial and flat endpoint realised equity; it misses
  intratrade excursions. No Sharpe ratio or risk-adjusted alpha is manufactured.
- Numerical quantity flooring does not model exchange lot sizes or minimum
  notionals. Late-stage depleted balances could prevent real orders and change
  precise counts, costs and balances. ETH training-mean stress ends near
  **0.460921 USDT**, not exact bankruptcy despite a rounded −100.00% display.
- Local hash verification preserves evidence integrity within the reviewed trust
  boundary; it is not a signed source attestation or durable off-machine backup.

## Tests, reproduction and output identities

Executed with the existing environment, without `.env` or a test database:

```sh
env -u BADGER_TEST_ADMIN_DSN .venv/bin/pytest -q -p no:cacheprovider
.venv/bin/ruff check . --no-cache
.venv/bin/ruff format --check . --no-cache
git diff --check
```

**382 passed, 173 skipped**. The 39 new synthetic tests cover cost decomposition,
geometric compounding, positive/zero/negative budgets, cash-only accounts,
month-boundary attribution and additive/multiplicative reconciliation, separate
markets/models, input schema/hash/provenance failures, immutable deterministic
artifacts and offline CLI success/failure. Existing relevant tests also passed.
Skipped PostgreSQL integration cases require an explicitly configured isolated
server; none was provisioned and no development database was accessed. Ruff lint
and formatting pass. No remote CI execution is claimed.

Both actual offline CLI runs produced byte-identical copies of all four files.
The manifest records runtime, fixed assumptions, definitions, all reconciled
annual diagnostics, source identities and implementation/output hashes. It does
not embed run timestamps or destination paths. The manifest's own hash is listed
below rather than recursively embedded in itself.

| Stage 2D output | SHA-256 |
| --- | --- |
| `cost_diagnostics.csv` | `4e970ec235b63be36ffc745ada684b3a49173c6b609aa94c0d07fbda1d3fbb21` |
| `manifest.json` | `e0fc31db58e2340f6c3da1c6700f0949950e05451bc8837fd3bc9108f31fa2ca` |
| `monthly_results.csv` | `c29ae49409fa52217f0a032db8d1490e7736140211c39b81113a6d44327eeaa9` |
| `summary.md` | `f7e64c31c8775943e492b517eaaa140896274d5a02e04ff3a4968509fa745948` |

Analysis implementation SHA-256 (`economics.py`):
`4c460a3302a4a511ad186fc7ab653c144b1d7adafed0726aba79b568b0f2702a`.

## Files and next-stage recommendation

Created `src/backtest_badger/economics.py`, `tests/test_economics.py`, this guide,
the exact prompt archive at `prompts/stage-02-research/004-economic-diagnostics.md`
and the ignored analysis/reproduction directories. Updated CLI dispatch,
architecture and roadmap. README now recognises implemented Stage 2C backtesting,
correcting Audit 001's sole minor documentation finding, and links Stage 2D.
No third Field Note or another audit was added.

Review and accept this postmortem before separately scoping **Stage 3 forward
prediction recording as an engineering/observation exercise**. These results do
not justify promoting a profitable trading strategy. Preserve the frozen evidence
and untouched holdout, keep forward predictions distinct from backtests, and
predefine any later research/evaluation protocol before examining new outcomes.
Do not use these diagnostics to tune the existing validation strategy.

This work stops after Stage 2D. No Stage 3 work, feature/model/trading-rule changes,
new market data, holdout evaluation, live/paper trading, deployment, commit or push
was performed.

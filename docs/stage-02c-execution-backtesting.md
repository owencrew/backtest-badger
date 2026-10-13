# Stage 2C — Execution-aware historical backtesting

Implemented for review on 2026-10-14. **Historical simulation only**: no actual or
paper trades. The fixed long/cash policy loses money in every base and stress
account that trades. No strategy, forecast, threshold or cost assumption was
changed after results were viewed. Stage 2D and the test holdout remain untouched.

## Commands and local artifacts

```sh
# Bounded acquisition: 24 monthly ZIPs plus their official checksum sidecars.
uv run --locked badger prepare-execution-data \
  --output artifacts/execution/binance-1h-2024-v1

# Offline: no settings, provider requests, database connections or model fitting.
uv run --locked badger backtest-validation \
  --forecasts artifacts/experiments/stage-2b-v1 \
  --execution artifacts/execution/binance-1h-2024-v1 \
  --output artifacts/backtests/stage-2c-v1

# Identical inputs, separate destination, no fresh downloads.
uv run --locked badger backtest-validation \
  --forecasts artifacts/experiments/stage-2b-v1 \
  --execution artifacts/execution/binance-1h-2024-v1 \
  --output artifacts/backtests/stage-2c-v1-reproduction
```

These directories already exist locally. Both commands refuse existing output
directories. All generated data are gitignored. The acquisition directory contains
`raw/*.zip`, `raw/*.zip.CHECKSUM`, `acquisition.json`, `hourly_opens.csv` and
`manifest.json`. The backtest directory contains `trades.csv`, `equity_curve.csv`,
`summary.md` and `manifest.json`. Manifests are published last. A failed acquisition
retains its diagnostics and available evidence, but publishes no usable manifest;
inspect it and use a new destination. Source anomalies stop the whole acquisition.

Immutable here means commands never overwrite a published directory; it is not a
filesystem permission lock or an off-machine backup. Acquisition times describe
when retrospective archives were received, not historical price availability.
Reacquiring data has new observation evidence and can encounter provider revisions;
reproduction uses the same frozen artifacts.

## Forecast integrity and holdout discipline

Both supplied Stage 2B SHA-256 pins match the actual bytes:

```text
validation_predictions.csv
e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674
manifest.json
af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581
```

The loader verifies the exact nine-column schema, Binance Spot identities, native
4h source openings, finite Decimal forecasts, UTC availability, unique canonical
ordering, both baseline constants, the research fingerprint and the explicit full
validation grid. There are **17,560 rows: four predictors × 2,195 windows × two
markets**, representing 4,390 market-time observations. The first signal is
2024-01-01 00:01 UTC and the last is 2024-12-31 16:01 UTC. The final exit is
2024-12-31 20:00 UTC. The boundary-purged 20:01 signal is not invented.

The backtest reads only validation predictions and frozen execution data. It
neither opens the Stage 2A research CSV nor accesses any labels, trains/refits a
model or generates a forecast. The Stage 2A manifest hash and file sizes/mtime_ns
were checked unchanged, without reading research CSV bytes. Stage 2B's two pinned
hashes were verified unchanged after both runs. This is a deliberate distinction
between preservation evidence and a new whole-file hash of withheld research data.

## Independent native hourly acquisition

January BTC and January ETH were each acquired, checksummed and parsed before any
February–December acquisition. All **24 ZIPs and 24 checksum sidecars** were
retained, totalling **1,003,416 ZIP bytes**. All official ZIP hashes match. Strict
parsing reuses `archives.py`: exact member and sidecar filenames, twelve-column
CSV validation, milliseconds for 2024, UTC native boundaries, proper inclusive
close times, exact Decimal economics, ordered identities and complete monthly
grids. No validation exception or source-gap mode was used.

Coverage is **2024-01-01 00:00 UTC inclusive to 2025-01-01 00:00 UTC exclusive**:
8,784 hourly observations per market, 17,568 total. Missing, duplicated, unexpected
and rejected identities: **zero**. February correctly has 696 hours. Every hour
is required, including hours not used as fills. There is no interpolation,
substitution from 4h research prices or canonical PostgreSQL insertion.

Offline loading hashes the CSV and acquisition evidence, verifies each retained
ZIP against its official sidecar again, reparses all 24 archives and reproduces
the exact reference CSV bytes. Thus changing a reference price and recomputing its
CSV hash still fails source replay. URLs, market/month identity, archive/sidecar
hashes, row counts and observed times must also agree. SHA-256 checks provide
integrity, not a signed attestation of historical economics: coordinated changes
to all local evidence are outside this trust model. The reviewed hashes below
identify this exact release.

| Execution file | SHA-256 |
| --- | --- |
| `acquisition.json` | `926697a89eb7c018ca5913f1e3c4c1170715db5639d444a58a78012e92aec055` |
| `hourly_opens.csv` | `39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a` |
| `manifest.json` | `1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d` |

Official monthly archive hashes follow. Each filename is
`{symbol}-1h-{month}.zip`, under
`https://data.binance.vision/data/spot/monthly/klines/{symbol}/1h/`.
Full source/checksum URLs and acquisition timestamps are retained in the manifest.

| Market | Month | Rows | Official ZIP SHA-256 |
| --- | --- | ---: | --- |
| BTCUSDT | 2024-01 | 744 | `cf873a185bd5b24b8e00034e49583fcb49928e0c3a45c6fc27a632a683655417` |
| ETHUSDT | 2024-01 | 744 | `1fdb3a8fa6b77ef30ef17ed4b71b184172ef1f812d83bd0f50bbd08e71a92057` |
| BTCUSDT | 2024-02 | 696 | `b83aa7319ef1d4baa7b923c0fe802b88dfaf241c7456af295f1f656a24379b33` |
| ETHUSDT | 2024-02 | 696 | `f080ff288b2f7e85e78c5370a8a3258b93f85531ff96b4131c1b7889649a8ba4` |
| BTCUSDT | 2024-03 | 744 | `b0851daf609d6ab82fdf8f1d1c4fbd974bc1b4e6530a832067516ac1c2be63a6` |
| ETHUSDT | 2024-03 | 744 | `4eb16ab0c5db15e5e0d77827f5c19c215c7ce601a5501d9563b75bda7602f46e` |
| BTCUSDT | 2024-04 | 720 | `e266707ad2ea3cd4680bf1ac5025f0c1bfeb38e703374a91f8dc193d1ec8d48f` |
| ETHUSDT | 2024-04 | 720 | `8b710fad720ae0bc75eaded37b3add95ca49122ae398f3f6e33e57e864da781e` |
| BTCUSDT | 2024-05 | 744 | `077c71eec71a8ecf2edb6e3a3927b600b8f358fd37066ce120c19fb5302a9ab8` |
| ETHUSDT | 2024-05 | 744 | `0307d64f0d9ae6ff4001442a014d7b02dcbc5a003dcc36ba139f1c9695996b51` |
| BTCUSDT | 2024-06 | 720 | `2e1f968fa34b9feabfb19cc6eec47a146e20d64a706f4b17d0babf4d2f475c39` |
| ETHUSDT | 2024-06 | 720 | `59ee6920bd72d93d1130c89711c93ea192bbfd5f82b548dcb0448f66450f6a06` |
| BTCUSDT | 2024-07 | 744 | `41fd58a70ae40bebb74682555cc5054709f8dde0f5c8193ae2103dac95274e5f` |
| ETHUSDT | 2024-07 | 744 | `83181cfcc1f1e32a542e2c220cbd58acd1c550cc64ad1e2c414e47088266aa7c` |
| BTCUSDT | 2024-08 | 744 | `88521a975ee7bfdd21f891d81f4243a01b90b977cf525d11747e27c66e3bad60` |
| ETHUSDT | 2024-08 | 744 | `d908255a48978f6acb769c4b856a3307c58a8c19dbf2b3b7f10067245d5e8b89` |
| BTCUSDT | 2024-09 | 720 | `123f402c6dbf19b9b72b4af7ad4d5325c73ba4833148cc398b803d7a34ac5c5f` |
| ETHUSDT | 2024-09 | 720 | `bfbdda97d03abac469199120ec3c2f1305e2d5947e9155ff84dbeafe33cd4a67` |
| BTCUSDT | 2024-10 | 744 | `393b18ad2634f0cd3b2fd54321c8286ea143419cf3129b4cc44e089681912b03` |
| ETHUSDT | 2024-10 | 744 | `cbb13664485b6c9a6365da7ae23299b722ab5926a6aed516add486ef501883bc` |
| BTCUSDT | 2024-11 | 720 | `7a51fe8811c754ff43a2be0ba10e53a6d4218521e27ac765fbc9a1ca0fc15bac` |
| ETHUSDT | 2024-11 | 720 | `29cd30419b86d5dff5467a7a81d43e492aaaeb3669db216ab8badaad5fe610ec` |
| BTCUSDT | 2024-12 | 744 | `dfec812f73a84257b195cbdaed34d020fa77e845625c061c13bd6a60e7ef9372` |
| ETHUSDT | 2024-12 | 744 | `84312b7dc2b5c903853c78d94f587ef1d24b7960d7bd95f5bfe3afc3db006203` |

## Fixed execution and accounting policy

For a native 4h candle opening at 08:00 UTC, feature availability is 12:01 UTC.
Entry uses the **13:00 native 1h opening reference**, with exit at **16:00**. This
holds for three hours; the next 16:01 signal can enter at 17:00. Entry is 59
minutes after availability and one hour after the source candle endpoint. It
never uses the already-passed 12:00 price. This is a hypothetical boundary policy,
not a claim that an actual market order waits until the next hour. Forecasts
predict a four-hour close-to-close log return; trading earns a different, shorter
opening-reference return. The two quantities are never substituted for each other.

Every market/model/scenario has a separate account starting at **10,000 USDT**.
Only forecasts strictly greater than **1e-12** enter long; all others remain in
cash. The tolerance is inherited from Stage 2B and was not optimised. Selected
trades use all affordable cash, exit completely at their fixed endpoint, and
cannot overlap. No borrowing, leverage, shorts, filters or stops are implemented.
The decision function has no price argument; all directions and schedules are
fixed before future references are looked up for accounting. Input integrity
failure aborts the run even if the affected signal would have stayed in cash.

| Scenario | Taker fee / side | Assumed half-spread / side | Slippage / side |
| --- | ---: | ---: | ---: |
| Frictionless diagnostic | 0 bps | 0 bps | 0 bps |
| Base | 10 bps | 1 bp | 2 bps |
| Stress | 10 bps | 3 bps | 10 bps |

These are modelling assumptions, not verified historical spreads, account fees or
execution conditions. The CLI always runs these three fixed scenarios; the small
`Costs` record permits explicit deterministic assumptions in synthetic unit tests.

Let entry/exit references be `P0`, `P1`, fee rate `f`, half-spread `h`, slippage `s`,
and pre-entry cash `C`. Rates divide the bps values by 10,000:

```text
buy_price  = P0 × (1 + h + s)
sell_price = P1 × (1 - h - s)
quantity   = floor_to_1e-24(C / (buy_price × (1 + f)))
buy_fee    = quantity × buy_price × f
cash_left  = C - quantity × buy_price - buy_fee
sell_fee   = quantity × sell_price × f
cash_after = cash_left + quantity × sell_price - sell_fee

gross_pnl  = quantity × (P1 - P0)
spread     = quantity × (P0 + P1) × h
slippage   = quantity × (P0 + P1) × s
net_pnl    = gross_pnl - spread - slippage - buy_fee - sell_fee
           = cash_after - C
```

Prices, quantities, cash and costs use Decimal with an explicit 80-significant-digit
ROUND_HALF_EVEN context. Quantity alone rounds down at 1e-24 asset units to retain
affordable residual cash; this is numerical precision, **not an exchange lot-size
rule**. No exchange minimum notional, tick/lot filters, liquidity cap or partial
fills are claimed. These omissions particularly limit interpretation as accounts
shrink to very small balances. Source ZIPs preserve the original provider strings;
the opening-reference CSV retains their Decimal precision.

Gross P&L uses each scenario's actual quantities. Costly accounts shrink, changing
later quantities, so their gross sums can differ from the frictionless account,
and can even have a different sign. Do not subtract a cost total from a different
scenario's gross result. Within each account, gross minus all costs reconciles to
net equity change. The realised stress ETH training-mean balance is positive
(about 0.46 USDT); a rounded −100.00% display does not mean exact bankruptcy.

## Results: gross, net and costs

All numbers below are USDT except net percentage return. Each account starts at
10,000 USDT. The zero model is always cash. Both training-mean forecasts are
positive and trade every eligible window. Decimal precision remains in CSV/JSON;
tables round for readability.

| Market | Model | Scenario | Trades | Gross P&L USDT | Net P&L USDT | Net % | Fees | Spread | Slippage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | zero | frictionless | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| BTCUSDT | zero | base | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| BTCUSDT | zero | stress | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| BTCUSDT | training_mean | frictionless | 2195 | 9873.91 | 9873.91 | 98.74 | 0.00 | 0.00 | 0.00 |
| BTCUSDT | training_mean | base | 2195 | 2582.55 | -9933.97 | -99.34 | 9628.09 | 962.81 | 1925.62 |
| BTCUSDT | training_mean | stress | 2195 | 1871.25 | -9999.18 | -99.99 | 5161.05 | 1548.32 | 5161.06 |
| BTCUSDT | ridge | frictionless | 1083 | 9852.93 | 9852.93 | 98.53 | 0.00 | 0.00 | 0.00 |
| BTCUSDT | ridge | base | 1083 | 3438.97 | -8811.67 | -88.12 | 9423.57 | 942.36 | 1884.71 |
| BTCUSDT | ridge | stress | 1083 | 2355.68 | -9863.78 | -98.64 | 5312.81 | 1593.84 | 5312.81 |
| BTCUSDT | gradient_boosting | frictionless | 1941 | 6276.53 | 6276.53 | 62.77 | 0.00 | 0.00 | 0.00 |
| BTCUSDT | gradient_boosting | base | 1941 | 1914.14 | -9895.32 | -98.95 | 9084.20 | 908.42 | 1816.84 |
| BTCUSDT | gradient_boosting | stress | 1941 | 1553.11 | -9997.84 | -99.98 | 5022.15 | 1506.65 | 5022.15 |
| ETHUSDT | zero | frictionless | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ETHUSDT | zero | base | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ETHUSDT | zero | stress | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ETHUSDT | training_mean | frictionless | 2195 | 1186.65 | 1186.65 | 11.87 | 0.00 | 0.00 | 0.00 |
| ETHUSDT | training_mean | base | 2195 | 1996.16 | -9962.83 | -99.63 | 9199.22 | 919.92 | 1839.84 |
| ETHUSDT | training_mean | stress | 2195 | 1601.85 | -9999.54 | -100.00 | 5044.08 | 1513.22 | 5044.08 |
| ETHUSDT | ridge | frictionless | 832 | 998.40 | 998.40 | 9.98 | 0.00 | 0.00 | 0.00 |
| ETHUSDT | ridge | base | 832 | 1240.35 | -8735.66 | -87.36 | 7673.85 | 767.39 | 1534.77 |
| ETHUSDT | ridge | stress | 832 | 1196.65 | -9760.56 | -97.61 | 4764.00 | 1429.20 | 4764.01 |
| ETHUSDT | gradient_boosting | frictionless | 1066 | -809.73 | -809.73 | -8.10 | 0.00 | 0.00 | 0.00 |
| ETHUSDT | gradient_boosting | base | 1066 | 1361.39 | -9425.04 | -94.25 | 8297.25 | 829.73 | 1659.45 |
| ETHUSDT | gradient_boosting | stress | 1066 | 1591.19 | -9931.81 | -99.32 | 5010.00 | 1503.00 | 5010.00 |

Base account diagnostics:

| Market | Model | Ending equity | Cash signals | Net win rate | Mean net trade return | Realised max drawdown | Eligible windows invested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | zero | 10000.00 | 2195 | undefined | undefined | 0.000% | 0.000% |
| BTCUSDT | training_mean | 66.03 | 0 | 35.444% | -0.223% | 99.358% | 100.000% |
| BTCUSDT | ridge | 1188.33 | 1112 | 37.211% | -0.191% | 88.687% | 49.339% |
| BTCUSDT | gradient_boosting | 104.68 | 254 | 34.827% | -0.230% | 98.982% | 88.428% |
| ETHUSDT | zero | 10000.00 | 2195 | undefined | undefined | 0.000% | 0.000% |
| ETHUSDT | training_mean | 37.17 | 0 | 37.403% | -0.248% | 99.634% | 100.000% |
| ETHUSDT | ridge | 1264.34 | 1363 | 41.707% | -0.240% | 87.664% | 37.904% |
| ETHUSDT | gradient_boosting | 574.96 | 1129 | 34.615% | -0.261% | 94.626% | 48.565% |

All 24 accounts' full metrics, including other scenarios, are in `manifest.json`.
There are **27,936 executed round trips** across scenarios and **52,704 equity
observations** (initial plus 2,195 window endpoints for each of 24 accounts).
These are repeated simulations, not independent samples. All ending assets are
zero; no purchase overdraws cash. Actual maximum per-trade and account gross/net
reconciliation errors are **zero** against the declared 1e-60 USDT tolerance.
Missing/rejected execution references are zero in all completed accounts; failed
input validation would produce an error rather than a performance result.

Win rate counts strictly positive net trade P&L. Mean net trade return uses
pre-entry account equity as denominator. Both are undefined with no trades.
Exposure is the fraction of eligible windows invested, not a continuous-time
annual exposure estimate. Each invested window holds three hours.
Drawdown uses initial equity and each eligible window's exit boundary, including
cash-only windows. It is explicitly **realised-equity drawdown**, not all intratrade
losses. No invented intrabar marks or annualised Sharpe ratio are reported.

## Interpretation and limitations

The base policy loses between **87.36% and 99.63%** in accounts that trade. Repeated
turnover is decisive: a flat reference price loses roughly 26 bps per round trip
under base assumptions and 46 bps under stress assumptions. Compounding those
costs through hundreds or thousands of fully invested trades overwhelms these
weak forecasts. The zero model's unchanged cash is a necessary visible comparator.

Regression improvement measures numerical forecast error on a different target;
it does not guarantee useful sign decisions, sufficient return per trade or
positive net P&L. BTC's positive frictionless results do not survive the specified
costs. ETH boosting loses even frictionlessly. These observations reject economic
usefulness of this particular fixed validation policy under the specified costs;
they do not prove all possible strategies or execution policies are unprofitable.
No threshold or strategy search was performed in response.

The delayed entry changes exposure by omitting the first hour after the forecast's
reference close and creating flat gaps between positions. An hourly opening price
is a retrospective historical reference; it is not a guaranteed attainable fill
for the simulated quantity. Candles cannot reconstruct historical order books,
bid/ask quotes, liquidity, market impact, publication delays or revision history
as observed by a trader in 2024. Fees and execution frictions are assumptions.

Even profitable validation outcomes would not establish a robust strategy or
justify promotion. BTC and ETH share market conditions and are not independent
confirmation. One fixed 2024 sample cannot establish results in other regimes;
chronological holdout and robustness research remain separate future work. No
statistical significance or live-performance claim is made. No Field Note was
added automatically; this guide retains the complete evidence for review.

## Reproducibility, tests and review

Two actual offline runs reproduced **all four output files byte for byte**:

| Backtest file | SHA-256 |
| --- | --- |
| `equity_curve.csv` | `f0293cf1e9872f07aaf39457388254e3bfedfc576eb59955506c74cfa5054b39` |
| `manifest.json` | `72a2bd94966a07a726d3d2876fbabd249211ecda2994f930258edb8c5007ada0` |
| `summary.md` | `b51f1851f1831edbc1dfa74d6803e52893983b79d5a0d884684ed1e40ddce6c1` |
| `trades.csv` | `bd2055ef06baab59ffa301583080734f2ef8c683634328cdf14a6529d6c4f37b` |

An independent cash-flow audit recomputed every buy/sell notional and both fees,
verified affordability and ending cash, and compared ending equity with the
unrounded all-in multiplicative formula. Maximum difference caused by retaining
quantity-rounding residuals was **4.774e-20 USDT**, below 1e-12 USDT. The manifest
records source hashes, implementation fingerprints, fixed scenarios, precision,
metrics and output hashes. Full verification evidence is retained at
`artifacts/backtests/stage-2c-verification.json`; input preservation evidence is at
`artifacts/stage-2c-input-audit.json`. No new provider acquisition was needed for
reproduction.

Executed validation: **343 pytest tests passed**, including **69 new synthetic
Stage 2C tests**. **173 PostgreSQL integration tests were skipped**, not passed,
because `BADGER_TEST_ADMIN_DSN` was not configured. No database code/schema changed.
`ruff check .`, `ruff format --check .` and `git diff --check` passed.

New tests cover exact UTC availability/entry/exit timing; rejection of early,
late, off-grid, non-UTC and test-partition signals; fixed threshold and zero-model
cash behaviour; decisions before future-price access; chronology/overlap and
independent accounts; adverse costs, two-sided fees and affordable quantities;
conservation and hand-calculated P&L; realised drawdown; complete hourly grids;
source replay, altered hashes/identities/prices, failure evidence and bounded
January-first acquisition; immutable inputs/outputs, offline dispatch and byte
reproduction. Network acquisition is mocked in all automated tests.

Implementation review retained three ordinary-function modules with two small
immutable records (`Signal`, `Costs`). It reuses the existing HTTP/checksum/parser,
UTC helpers and artifact retention, with no dependency, database, broker, scheduler,
service or multi-timeframe ingestion framework added.

Created:

- `src/backtest_badger/execution_data.py`: fixed acquisition and offline source replay.
- `src/backtest_badger/forecast_data.py`: pinned validation-only input and timing rules.
- `src/backtest_badger/backtest.py`: sequential independent Decimal accounts and reports.
- `tests/test_backtest.py`: synthetic tests.
- This guide and the exact substantive prompt at
  `prompts/stage-02-research/003-execution-backtesting.md` (byte equality checked).

Modified: `src/backtest_badger/cli.py`, `docs/architecture.md`, `docs/roadmap.md`.
Local gitignored artifacts are listed above. No Stage 2A/2B artifact, historical
repository, production system or deployment was modified. No commit or push.
Stop after Stage 2C for review; do not begin Stage 2D or evaluate the holdout.

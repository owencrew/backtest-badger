# Stage 4B.2E.5g — first genuine 2024 historical backtest

2026-10-24, Europe/London. **GENUINE BACKTEST COMPLETED.** Exactly one genuine
economic replay was invoked. All six accounts are available; all six ledgers
passed the unchanged runner's verification. Independent `verify-output` completed
with exit status **0**, confirming the completion marker and all four output
identities. Ridge substantially underperformed both Cash and Buy & Hold in both
markets after the frozen transaction costs. This is a negative exploratory
research result, not evidence of a trading edge.

## Execution and reproducibility

- Reviewed E.5e implementation: `c39f572c046253b196c12b476c9170d71b0468bb`.
- Execution HEAD: `8900aa900f385dab7a8b4c9d744f3c898e205974`; starting tree clean.
  Its only changes since E.5e are the E.5f record, archived prompt and prompt index.
  Scientific source, tests, dependency files and frozen declarations are unchanged.
  All **31** loaded-project-source identities in `run.json` were compared against
  both E.5e Git blobs and the current files: exact matches.
- Runner: `stage-04b2e5e-local-historical-v1`, invoked through the existing
  `.venv/bin/python -m backtest_badger.local_historical_backtest run --execute`.
- CPython **3.12.13**, Clang **21.0.0**, macOS/Darwin **25.5.0**, **arm64**.
  Installed imports matched `uv.lock`: Alembic 1.20.0, cryptography 46.0.7,
  NumPy 2.5.4, psycopg 3.3.6, scikit-learn 1.9.1, pytest 9.1.1, Ruff 0.17.0.
  No dependency installation occurred. Owner-reported E.5e CI `40084535405`
  was not queried; this task used no network.
- Readiness: exact four E.5f locations were regular files without symlink path
  components. The requested output parent is Git-ignored, has no tracked entries,
  and resides on local APFS. Approximately **450 GiB** of disk space was free;
  `memory_pressure -Q` reported **24 GiB** physical RAM and **55%** memory free.
- Repeated standalone preflight: **exit 0**; four sizes/hashes, publication
  associations, independent sign-off and frozen methodology passed. The run's
  built-in preflight also passed. No source authentication was rerun.

- Run ID: `20261024T143549527999Z-85d1960cda514032ba3e4ac5f59b21d2`.
- Runner started: **2026-10-24T14:35:49.527999+00:00**; completed: **2026-10-24T14:36:02.933757+00:00**.

The runner printed its run directory only after writing `COMPLETE.json` and
passing its own `verify_output`. Its normal CLI path then returns 0. The outer
`/usr/bin/time -l` diagnostic wrapper reported **exit 1** because the sandbox denied
`sysctl kern.clockrate` during resource-statistic collection; it recorded 17.50
seconds wall time but could not provide complete resource statistics. This is a
wrapper diagnostic failure, not a failed/incomplete economic replay. The separate
CLI `verify-output` subsequently exited **0**. No retry or second replay occurred.
The exact wrapper output is retained in the ignored output parent's
`stage-04b2e5g-execution.log`; standalone preflight output is retained alongside it.

## Input and methodology identities

The original publication is identified as `stage-04b2d3-minute-inputs-v1`, with
independent D.14 sign-off. All original bytes were accessed read-only; private
absolute input paths and original artifact contents are omitted.

| Input | Bytes | SHA-256 |
| --- | --- | --- |
| authenticated_inputs | 15272413 | `2581482b4b8a60fa1a53f7710ed080be7de25d50a76fcae35c8aaf64f2cb2168` |
| integrity | 74200 | `23c3d17b2e5b67de701d9a0dd22d6135a907057b9acaeb16bcbdb4cb9c613a8b` |
| manifest | 560 | `3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea` |
| signoff | 2020 | `21b04470e861a039750bf7b665b993d332bf998fcc5b9fea47dc2c8b80f334b4` |

Protocol: `historical-minute-execution-v1`, SHA-256
`c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b`.
Frozen METHOD declaration SHA-256:
`d38ff4eb51cfbec757c4592fb4ee08c38f43d04ebbb23f264a875d0ae24b1754`.
Retained forecast identity:
`e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674`;
Stage 2B manifest/model-recipe identity:
`af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581`.
These identities and the publication pins reconcile across metadata and results.

The frozen Ridge sign threshold is `1e-12`; forecast availability is assumed at
source open +4h+60s, with execution at the strictly next native minute opening.
The run retains 2,195 decisions per market and 8,784 hourly marks per account.
Each portfolio has its own 10,000 USDT funding posting and account/ledger identity;
BTC and ETH never share cash or holdings. Costs remain 10 bps fee, 1 bp half-spread
and 2 bps adverse slippage per side, with the approved rounding and quantity step.
No model fitting, forecast regeneration, tuning or scientific change occurred.

## Six-account results

All amounts are USDT unless a base-asset quantity is specified. Funding, marked
values, cumulative returns, holdings and summed costs/turnover below are exact,
with insignificant trailing zeros omitted. Long descriptive ratios and calendar
returns are displayed to **six decimal places**; their authoritative full-precision
Decimal strings remain in `summary.json` and `private/evidence.json`.

All accounts are **available** and have **passed** ledger verification. Initial
funding is distinct from the first hourly mark: Buy & Hold pays inception costs
before its first mark. Final values are at **2024-12-31 23:00 UTC**.

| Account | Initial funding | First marked value | Final marked value | Cumulative return |
| --- | --- | --- | --- | --- |
| BTCUSDT Ridge | 10000 | 10000 | 3930.855650228768 | -60.69144349771232% |
| BTCUSDT Cash | 10000 | 10000 | 10000 | 0% |
| BTCUSDT Buy & Hold | 10000 | 9987.013902536866 | 22081.233105286866 | 120.81233105286866% |
| ETHUSDT Ridge | 10000 | 10000 | 4204.394238239753 | -57.95605761760247% |
| ETHUSDT Cash | 10000 | 10000 | 10000 | 0% |
| ETHUSDT Buy & Hold | 10000 | 9987.013887627081 | 14617.584036417081 | 46.17584036417081% |

| Account | Annualised return | Maximum hourly drawdown | Annualised daily volatility | Zero-rate Sharpe |
| --- | --- | --- | --- | --- |
| BTCUSDT Ridge | -60.595211% | 65.410518% | 34.424241% | -2.533268 |
| BTCUSDT Cash | 0.000000% | 0.000000% | 0.000000% | Undefined (zero variance) |
| BTCUSDT Buy & Hold | 120.354757% | 32.310653% | 53.146893% | 1.742899 |
| ETHUSDT Ridge | -57.860552% | 65.787102% | 38.184018% | -2.066832 |
| ETHUSDT Cash | 0.000000% | 0.000000% | 0.000000% | Undefined (zero variance) |
| ETHUSDT Buy & Hold | 46.030590% | 46.655060% | 64.925900% | 0.916039 |

Annualised return uses the actual elapsed time through the last mark and 365-day
scaling. Volatility is the sample standard deviation of 365 complete UTC daily
returns times sqrt(365); Sharpe uses their mean and a zero reference rate. Cash's
zero volatility is valid; its Sharpe is **undefined**, not zero. Drawdown includes
funding and observed hourly marks, not an unobserved intraminute equity path.

## Trading activity, costs and final holdings

Turnover below is the sum of BUY and SELL execution notionals divided by the
original 10,000 USDT; it is not halved or measured against average equity. Total
cost is fees plus the existing hypothetical half-spread and slippage attribution.
Spread/slippage are embedded in execution prices, not additional cash fees.

| Account | Buys / sells | Traded notional | Turnover (× funding) | Total costs |
| --- | --- | --- | --- | --- |
| BTCUSDT Ridge | 570 / 570 | 7640090.531145331794 | 764.0090531145331794 | 9932.118043791232 |
| BTCUSDT Cash | 0 / 0 | 0 | 0 | 0 |
| BTCUSDT Buy & Hold | 1 / 0 | 9989.997144093134 | 0.9989997144093134 | 12.986097463134 |
| ETHUSDT Ridge | 499 / 499 | 7107303.185600881653 | 710.7303185600881653 | 9239.494456250247 |
| ETHUSDT Cash | 0 / 0 | 0 | 0 | 0 |
| ETHUSDT Buy & Hold | 1 / 0 | 9990.008613482919 | 0.9990008613482919 | 12.986112372919 |

| Account | Fees | Half-spread | Slippage | Final cash | Final base holdings |
| --- | --- | --- | --- | --- | --- |
| BTCUSDT Ridge | 7640.09053678 | 764.009169003744 | 1528.018338007488 | 3930.855650228768 | 0 |
| BTCUSDT Cash | 0 | 0 | 0 | 10000 | 0 |
| BTCUSDT Buy & Hold | 9.98999715 | 0.998700104378 | 1.997400208756 | 0.012858756866 | 0.236191 |
| ETHUSDT Ridge | 7107.30319062 | 710.730421876749 | 1421.460843753498 | 4204.394238239753 | 0 |
| ETHUSDT Cash | 0 | 0 | 0 | 10000 | 0 |
| ETHUSDT Buy & Hold | 9.99000862 | 0.998701250973 | 1.997402501946 | 0.001377897081 | 4.376679 |

BTC Buy & Hold retains **0.236191 BTC** with cost basis **9999.987141243134**;
ETH Buy & Hold retains **4.376679 ETH** with cost basis **9999.998622102919**.
Both Ridge accounts end in cash with zero base holdings and zero cost basis.
No terminal liquidation or liquidation cost was invented for Buy & Hold.

## Daily and monthly patterns

Complete-day counts exclude December 31's 23-hour partial observation. Best/worst
dates below denote the start of the UTC return period; percentages are mark-to-mark.

| Account | Positive / flat / negative days | Mean daily return | Best complete day | Worst complete day |
| --- | --- | --- | --- | --- |
| BTCUSDT Ridge | 147 / 2 / 216 | -0.238920% | 7.475094% (2024-08-08) | -8.082685% (2024-01-12) |
| BTCUSDT Cash | 0 / 365 / 0 | 0.000000% | 0.000000% (all days) | 0.000000% (all days) |
| BTCUSDT Buy & Hold | 191 / 0 / 174 | 0.253780% | 11.884249% (2024-08-08) | -8.390157% (2024-03-19) |
| ETHUSDT Ridge | 155 / 27 / 183 | -0.216219% | 8.629362% (2024-03-06) | -8.151067% (2024-04-13) |
| ETHUSDT Cash | 0 / 365 / 0 | 0.000000% | 0.000000% (all days) | 0.000000% (all days) |
| ETHUSDT Buy & Hold | 191 / 0 / 174 | 0.162944% | 19.229941% (2024-05-20) | -10.277604% (2024-03-19) |

Cash returns are exactly 0 in every month for both independent accounts.

| Month | BTCUSDT Ridge | BTCUSDT Buy & Hold | ETHUSDT Ridge | ETHUSDT Buy & Hold |
| --- | --- | --- | --- | --- |
| 2024-01 | -9.825124% | 0.701028% | -5.482420% | 0.056094% |
| 2024-02 | 10.466677% | 43.567323% | 1.729394% | 46.293492% |
| 2024-03 | -2.476912% | 16.602056% | 4.652553% | 9.137151% |
| 2024-04 | -26.143695% | -14.882129% | -20.312390% | -17.316865% |
| 2024-05 | 1.247558% | 11.319872% | 7.568044% | 24.825481% |
| 2024-06 | -10.569057% | -7.059514% | -8.982368% | -8.615231% |
| 2024-07 | -15.623625% | 2.956729% | -20.571118% | -5.974707% |
| 2024-08 | -7.842686% | -8.748537% | -19.366764% | -22.264083% |
| 2024-09 | -3.512634% | 7.382229% | -6.467908% | 3.551134% |
| 2024-10 | -8.975433% | 10.997423% | -10.751322% | -3.213769% |
| 2024-11 | 0.689977% | 37.153525% | 18.606023% | 47.048962% |
| 2024-12 (partial) | -12.009279% | -3.027922% | -15.543471% | -9.820471% |

BTC Ridge has only **3 positive months** and ETH Ridge **4**. April is BTC Ridge's
worst month; July is ETH Ridge's worst. Both have persistent losses from June
through October, followed by a positive November and another negative December.
BTC Buy & Hold captures large February and November gains that Ridge mostly misses;
ETH Ridge also captures much less of those months' gains than ETH Buy & Hold.
Both Ridge accounts outperform their own Buy & Hold in August, while still losing
money that month. These isolated relative improvements do not offset annual losses.

December ends at December 31 23:00, one hour short; the final daily and monthly
observations remain explicitly partial. Calendar returns start at observed marks,
so Buy & Hold's inception cost precedes January's mark-to-mark return. Its
funding-relative annual return and drawdown include that cost. Daily and monthly
cost buckets use actual hypothetical fill timestamps and are alternative
aggregations, not additive evidence.

## Economic interpretation and limitations

| Market | Benchmark | Ridge minus benchmark cumulative return |
| --- | --- | --- |
| BTCUSDT | cash | -60.69144349771232 pp |
| BTCUSDT | buy_and_hold | -181.50377455058098 pp |
| ETHUSDT | cash | -57.95605761760247 pp |
| ETHUSDT | buy_and_hold | -104.13189798177328 pp |

**Neither Ridge account beats either benchmark after costs.** Cash preserves all
10,000 USDT and is preferable to Ridge on both terminal simulated value and
observed drawdown. Buy & Hold produces the largest terminal value in each market,
although its own drawdowns remain substantial. Ridge's lower daily volatility
than Buy & Hold does not rescue its sharply negative return or roughly 65% maximum
hourly drawdown; both descriptive Sharpe ratios are negative.

Turnover is economically material: BTC Ridge trades more than 7.64 million USDT
and ETH Ridge more than 7.10 million against only 10,000 USDT initial funding each.
Their aggregate attributed costs are **9932.118043791232** and
**9239.494456250247** USDT, respectively, versus roughly 12.99 USDT for each
Buy & Hold inception purchase. Capital is repeatedly recycled, so cumulative costs
can approach initial funding while positive trade-price movements offset part of
them. The retained evidence shows a severe cost burden. Adding these costs back
to terminal equity would not establish a valid frictionless strategy result:
changed costs would change affordability, quantities and the subsequent capital
path. No zero-cost replay or cost-sensitivity experiment was performed.

ETH Ridge loses **2.73538588010985 percentage points** less than BTC Ridge, trades
142 fewer times and pays less aggregate cost. Nevertheless, ETH Ridge has slightly
worse maximum drawdown and higher daily volatility. BTC Buy & Hold's much larger
return makes BTC Ridge's benchmark shortfall materially worse. These are separate
market outcomes, not a diversified portfolio or two independent replications.

Execution depends on assumed forecast availability, strictly next-minute archive
open references and fixed costs. There is no measured latency, historical order
book/depth, quantity-specific liquidity, market impact or proof of fillability.
Buy & Hold begins at 00:00; Ridge's earliest eligible execution is 00:02. The
native-minute release and previous source authentication are retained evidence,
not proof of contemporaneous availability or immunity to provider revisions.

**2024 was already inspected.** This is exploratory historical simulation, not
untouched out-of-sample testing, live trading profits, proven alpha or prospective
paper-trading performance. One year and two correlated markets cannot establish
future reliability. The 365-day annualisation and zero-rate Sharpe are descriptive
conventions. Cash is the frozen constant-USDT benchmark, not an interest-bearing
or purchasing-power-adjusted alternative. Final Buy & Hold values include unsold
assets and no hypothetical exit costs. No parameter tuning or strategy variations
were introduced after seeing these results.

There are no unresolved output-integrity or account-availability issues. The
resource-statistic wrapper restriction remains a diagnostic limitation only.
Useful future research questions are why the frozen signals reverse position so
frequently, which existing decision sequences account for the cost burden, and
whether a separately preregistered evaluation on genuinely uninspected data or
prospective paper trading offers different evidence. Those are future scoped
tasks; this run does not justify promotion or real-money trading.

## Retention and validation

Private local results are retained, unchanged, under this repository-relative
Git-ignored directory (no sensitive absolute input paths are exposed):

`artifacts/paper-historical/stage-04b2e5e-local-runs/20261024T143549527999Z-85d1960cda514032ba3e4ac5f59b21d2/`

| Completed output | Bytes | Verified SHA-256 |
| --- | --- | --- |
| private/evidence.json | 66840604 | `d23caae7d49bad50a254495b5f1a5b973ba72f714ce6be83bce0368a95bc0368` |
| run.json | 6985 | `9ccb356d538b3a3198fbc670b0adc5f42ea215f3eee3e4c84df1e3d766f75790` |
| summary.json | 16433 | `5d0536ea8e1b7f80274fddd6b0f0840901231838f17877632b936d5c01905a9b` |
| summary.md | 1614 | `47ff388881d6cbf1c05b9f18b762a205ae73894292e8620b9cd00c0d6ac4c5eb` |

`COMPLETE.json` binds exactly those four files and the run ID. The independent CLI
verification checked their hashes and sizes. Read-only analysis also reconciled
all six exported ledger identities and account fingerprints, distinct funding
postings, market identities, initial balances, report/native performance and final
marked equity. The existing runner had already executed the scientific ledger
verifiers; this analysis did not replay economics or modify generated evidence.

Documentation validation: `git diff --check`, Ruff lint and formatting checks,
and byte-for-byte prompt comparison passed. No pytest or expensive synthetic suite
was rerun because implementation did not change. Source/dependency/frozen-method
comparison against E.5e passed. No network, production, database modification,
website publication, commit, push, deployment or real-money trading occurred.

Only this new report, the following verbatim prompt archive, and `prompts/README.md`
were changed outside the ignored output parent:
[`stage-04b2e5g-first-genuine-historical-backtest.md`](../prompts/stage-04-paper/stage-04b2e5g-first-genuine-historical-backtest.md).

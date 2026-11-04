# Study 002 — Can a Slower Trend Beat the Noise?

Method version: `study-002-methodology-v1`. Strategy: `trend_30d_daily_v1`.
Status: predeclared exploratory retrospective historical simulation; unpublished.
Starting revision: `8e22d263b8a8bf548d9e014a121e68c522b6ee82` (clean).
The external freeze record binds this file, the configuration and implementation
before the first genuine economic evaluation; it supplies the exact UTC time.

## Question and hypotheses

Does a slower daily rule reduce turnover and attributed transaction costs versus
the previously verified Ridge Sign study? Does its net return or drawdown improve?
H1: fewer executions and lower turnover. H2: lower attributed costs. H3: net
returns may improve relative to Ridge, without guarantee. H4: the strategy may
still underperform Cash or Buy & Hold. Report every market and all twelve months,
including losses, regardless of whether these hypotheses are supported.

Study 001 established a substantial cost burden, not that frequency alone caused
underperformance. This experiment changes signal construction as well as cadence.
2024 was already inspected: predeclaration for this study does not mean the rule
was chosen before the market history was known. No untouched out-of-sample claim,
parameter sweep, alternative threshold, extra year, market-specific selection,
Ridge refit, or held-out 2025–2026 target analysis is permitted.

## Data, causal rule and completeness

Use the pinned native Binance Spot four-hour Stage 1B.3 export:

- `candles.csv`: `e6052b8cca7bca00999ca4d7429af67db019c8ef261fa2b499f0fd6774dcd13b`.
- `manifest.json`: `a78d34256d3bcd789e6cc19a2807f432d1ffa1a73ecc81b5ea16b3859759a98a`.

`frozen.load_frozen` validates whole-file hashes, market identity, UTC grid, ordering,
economics, recorded source gaps and provenance. Whole-source structural parsing
includes later candles; the strategy receives only the required pre-2025 close
projection, never target labels or later prices. The globally incomplete source
is acknowledged explicitly. Require the complete contiguous native grid from
2023-12-01 20:00 through 2024-12-30 20:00 (2,371 observations per market).
No missing observation, duplicated/reordered identity or invalid price is repaired.
This is stricter than requiring just the two daily endpoint closes.

For each UTC midnight D in [2024-01-01, 2025-01-01), use exactly the native close
at D and the native close at D minus 30 calendar days. The corresponding candle
opens are D minus four hours and D minus 30 days minus four hours. Evaluate once
at D+60 seconds: 366 evaluations per market. Trend is `(P_now/P_30d)-1`.
The trading sign uses exact Decimal comparison `P_now > P_30d`, algebraically
equivalent for validated positive prices, so ratio rounding cannot erase a tiny
positive signal. Retain both exact operands and the numerator; the descriptive
ratio uses the existing 80-digit division context. No deadband or risk overlay.

Positive means LONG; zero/negative means CASH. LONG while invested is HOLD;
CASH while flat is CASH_NOOP. Otherwise buy the full fee-affordable step quantity
or sell all holdings. Preserve continuous holdings. No intermediate weights,
forced daily/year-end liquidation, leverage, shorts, borrowing or shared capital.

## Execution and independent benchmarks

Reuse the authenticated native-minute publication, its original external pins
and independent sign-off, through the unchanged E.5e preflight. Its retained
projection already includes every daily 00:02 opening and all hourly marks.
The four publication/sign-off SHA-256s are:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| manifest | 560 | `3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea` |
| authenticated_inputs | 15272413 | `2581482b4b8a60fa1a53f7710ed080be7de25d50a76fcae35c8aaf64f2cb2168` |
| integrity | 74200 | `23c3d17b2e5b67de701d9a0dd22d6135a907057b9acaeb16bcbdb4cb9c613a8b` |
| signoff | 2020 | `21b04470e861a039750bf7b665b993d332bf998fcc5b9fea47dc2c8b80f334b4` |

Three independently identified/funded 10,000 USDT accounts per market: Trend,
Cash (no interest/trades) and Buy & Hold (one purchase at January 1 00:00).
Ridge is the fixed historical reference from the [original E.5g report](../stage-04b2e5g-first-genuine-historical-backtest.md),
with its pinned retained summary and evidence. Never regenerate its model.
A regression may recompute the identical pinned replay in memory solely to compare
byte identities; do not replace or publish new Study 001 results.

Signal availability at 00:01 means strictly-next-minute execution at 00:02,
including exact-minute signals. Never use 00:00/00:01 for Trend. B&H's inception
purchase precedes the earliest Trend execution by two minutes, as in Study 001.
Fee: 10 bps of adjusted notional, rounded UP to 0.00000001 USDT. Half-spread: 1 bp;
adverse slippage: 2 bps. Buy price = native opening ×1.0003; sell ×0.9997.
Quantity step: 0.000001 base units. Use existing fee-aware affordability and
160-digit exact money context, 80-digit division conventions. Spread/slippage
are embedded in price and attributed, never charged again as cash fees.
Mathematically infeasible Trend trades fail the run; infeasible inception B&H is
reported unavailable with its existing reason, never assigned a later purchase.

Use the existing monetary fill, paired-posting accounting, hourly mark, ledger
verification and economic reporting functions. The frozen Ridge planner/loop is
unchanged. A small daily scheduler supplies already-causal signals to these
primitives. Because legacy reporting admits only `ridge`, `cash`, `buy_and_hold`
labels, a temporary in-memory label facade permits its strategy-independent
account checks for Trend. It never changes portfolio identity or strategy ID,
never invokes Ridge planning, and is not retained as a Ridge result. The adapted
report restores the Trend label and declares the legacy fingerprint convention.
No monetary algorithm is duplicated or overridden.

## Valuation, metrics and interpretation

8,784 native-minute HH:00 marks per available account. Last observation:
2024-12-31 23:00 UTC. No 2025 price or terminal sale. Exposure duration can use
2025-01-01 solely as a duration boundary, separately from hourly invested fraction.

Report funding, first/final equity, funding-relative return, descriptive annual
return, observed-hourly maximum drawdown (including initial funding), complete-day
sample volatility ×sqrt(365), zero-rate daily Sharpe, buys/sells, signal and
position-change counts, HOLD/CASH_NOOP counts, total buy+sell notional, turnover
relative to funding (not halved), fees/spread/slippage/total costs, exposure,
final cash/base/basis, realised/unrealised P&L, monthly returns/trading and best/worst
complete days. Undefined statistics use null with reasons, never invented zeros.
Benchmarks have zero trend evaluations; B&H has one inception position change.

Annual return uses `(final_equity/10000) ** (365*86400/elapsed_seconds)-1`, with
elapsed time ending at the last observed mark. Daily/monthly mark returns begin
at observed marks; B&H inception costs precede its first mark and January return.
There are 365 complete days; December 31 and December are partial. Costs/trades
use actual hypothetical fill timestamps in half-open calendar buckets. Monthly
chaining reconciles first-to-last equity; funding-relative return also includes
any inception cost. Preserve exact Decimal strings; display rounding is separate.

Compare all four strategies without claiming a controlled frequency-only effect.
Discuss exposure during large gains and lag around reversals using retained
marks/positions, without hindsight trades or a zero-cost replay. Adding costs
back to final equity is not a valid counterfactual: sizing and the capital path
would change. One year, two correlated markets, retrospective provider revisions,
unobserved intrahour drawdown and assumed +60-second availability limit inference.
Fixed costs and next-open references do not establish actual fees, quotes,
liquidity, fills, exchange-side availability or an investable edge.

## Validation, freeze and one-run procedure

Before genuine economics: verify local input hashes/sign-off and complete warm-up;
implement and pass synthetic causality, exact-sign, transition, missing-data,
identity, timing, affordability, ledger and reporting tests; run relevant existing
regressions; record methodology/config/source SHA-256s and freeze UTC time.
Check Study 001 outputs against their externally retained hashes and regress its
unchanged pinned replay against original summary/evidence bytes. Failure blocks
Study 002. No acquisition, production/database access or input repair is authorised.

The owner authorises one local genuine Study 002 attempt after those gates.
Create a fresh exclusive mode-0700 directory under Git-ignored
`artifacts/studies/study-002/`; record the attempt before loading/replaying.
Retain failures and diagnostics, with no silent retry. Record source/runtime,
all input/config/method identities, signals, fills, accounts, hourly marks, paired
ledgers and full reports. Recheck source identities after execution. Independently
sum ledger postings, fees, costs, exposure, equity and period returns; compare the
new Cash/B&H values with original benchmarks. Write a hash-bound completion marker
only after all checks pass, then independently verify output readback.

Generate equity, drawdown, exposure, monthly activity, attributed-cost comparison
and monthly-return charts from verified retained evidence, carrying units and
source hashes. Prepare source-linked exact data and accessible draft copy outside
`web/app`, `web/public` and the production content loader. No public route, sitemap,
approval-hash change, deployment, commit or push. Publication needs owner review.

The full task is archived in [the Stage 6 request](../../prompts/stage-06-research/001-study-002-slower-trend.md).

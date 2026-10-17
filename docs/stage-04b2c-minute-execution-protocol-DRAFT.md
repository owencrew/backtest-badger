# DRAFT / NOT APPROVED FOR GENUINE DATA ACQUISITION OR ECONOMIC EVALUATION

## Stage 4B.2C — Proposed one-minute historical execution scenario

Provisional version: **`historical-minute-execution-draft-v1`**.
Written 2026-10-17 for owner review. This is a separate proposed scenario, not an
amendment to frozen `historical-validation-v1`, Stage 4A, or any hourly experiment.
Stage 4B.2B synthetic engineering is accepted; that acceptance does not approve
real hourly evaluation or this minute methodology. No minute replay is implemented
or authorised, no genuine minute source release is authenticated or frozen, and
no minute economic result has been calculated.

## Proposed fixed research inputs and decisions

Binance Spot BTCUSDT and ETHUSDT, independently, over
`[2024-01-01T00:00:00+00:00, 2025-01-01T00:00:00+00:00)`.
Use the same fixed **2,195 Stage 2B Ridge validation forecasts per market**, from
native four-hour source openings 2023-12-31 20:00 through 2024-12-31 12:00 UTC.
Keep the original per-market train-only standardised Ridge model, five-feature
recipe and whole-Stage-2B-manifest lineage identity. No fitting, new features,
threshold search, forecast regeneration, model selection or withheld labels.

The unchanged source declarations are:

| Stage 2B file | Declared SHA-256, not reverified here |
| --- | --- |
| `validation_predictions.csv` | `e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674` |
| `manifest.json` | `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581` |

Strictly `prediction > Decimal('1e-12')` targets long; equality, negative values
and positive values at/below the threshold target cash. Decisions accept only
forecast identity, assumed availability and prediction, never future prices or
any minute candle's full OHLCV. Nonfinite or malformed evidence fails closed.
No source file above is opened by Stage 4B.2C.

Assume availability at the previous native four-hour candle open **+4h+60s**.
At 12:01 assumed availability, the first hypothetical execution reference is the
**strictly next native one-minute opening, 12:02**. The 12:01 opening has already
passed and is forbidden. Even a decision exactly on a minute boundary waits to
the next minute. The first possible Ridge reference is January 1 00:02; the last
eligible signal is December 31 16:01, with a 16:02 reference. Do not invent the
boundary-purged 20:01 signal.

A retrospectively archived opening is a hypothetical opening reference, not a
guaranteed contemporaneously executable price. Validation may inspect all source
fields offline; a future strategy decision interface must never receive future
high/low/close/volume or use source validation as historical availability evidence.

Preserve continuous HOLD while long and sign remains positive, full sale on a
cash target, CASH_NOOP while flat, reentry only on a new eligible signal after a
completed exit, and sticky risk-off exit intent. Pending risk exits cannot be
cancelled by intervening positive forecasts or reused for reentry. Missing real
forecasts/references abort the scenario, not create synthetic outage histories.
Future synthetic risk-off tests must explicitly record discovery times and use
the strictly next minute. These principles are **proposed only**, not simulated
or implemented here.

## Proposed fixed economics and contextual accounts

Each market's Ridge account starts with **10,000 USDT once** at inception.
Independent cash and buy-and-hold accounts also start with 10,000 USDT each.
No shared funds, leverage, shorts, midyear external reinvestment/top-ups, or forced
year-end sale. Retain unsold holdings and basis at year end. A new Ridge signal
may invest its existing available cash following an earlier exit.

Only the initial timing comparison's **10-bps fee, 1-bp hypothetical half-spread,
2-bps adverse slippage per side** is proposed. Buy reference ×1.0003; sell
reference ×0.9997. Preserve Stage 4B.1's exact fee rounding: 10 bps of adjusted
notional, rounded UP to 0.00000001 USDT; shared isolated monetary context, exact
paired ledger postings and fee-aware affordability. Use a synthetic base quantity
step of **0.000001 for both markets**; full affordable buys and complete sells.
No frictionless/stress alternative is authorised by this draft.

These assumptions are not observations of 2024 fees, spreads, depth, liquidity,
market impact, tick/lot-size or other Binance filters. No quote, order submission,
actual fill, or historical exchange-filter evidence may be invented.

Cash remains constant with no trades or costs. Buy-and-hold makes one hypothetical
full fee-affordable buy at **January 1 00:00**, using that market's native minute
opening and identical costs/step, then holds. This analytical counterfactual
precedes the earliest Ridge trade by two minutes. If inception acquisition is
mathematically infeasible, report the benchmark unavailable, without substituting
a later opening. Benchmark accounts remain independent from Ridge and each other.

## Proposed valuation, parity audit and reporting

Retain **hourly portfolio marks at HH:00**, sourced exclusively from the new
native **1m HH:00 opening**: 8,784 marks per market per available account, ending
December 31 23:00. The minute source grid still requires **all 527,040 minutes
per market**, including minutes with no trade. This keeps execution timing
minute-specific without over a million account snapshots.

A minute HH:00 opening may differ from the separately acquired 1h opening for
that hour because provider archives can be revised independently. Before claiming
directly comparable valuations, prospectively specify and execute a **fail-closed
parity/discrepancy audit** on both pinned releases: compare all 17,568 market/hour
identities and exact Decimal opens; retain both source hashes, counts, missing
identities, all discrepancies and magnitudes. Missing evidence or any mismatch
blocks a direct timing-only valuation comparison pending explicit owner review.
No post-results tolerance selection, silent source substitution, overwriting or
reinterpretation of the existing hourly results. A separately labelled comparison
on revised valuation assumptions requires a new approval. This audit is future
work requiring authorisation to open the old artifacts; it was not run here.

At any shared timestamp, execute only previously eligible scheduled intent, then
mark its resulting ledger prefix. A newly discovered signal at that timestamp
cannot use that opening. B&H inception costs precede its first 00:00 mark: include
them in funding-relative return/drawdown and disclose that they precede its first
mark-to-mark return. No assertion of actual intrasecond event order is implied.

Keep the prior UTC daily/monthly convention: consecutive exact midnight marks for
complete days; December 31 **00:00→23:00 is a partial 23-hour observation**, excluded
from complete-day statistics; December ends one hour short at 23:00 and is partial.
Use all months and preserve all adverse periods. No invented 2025 endpoint price.
Trade counts, turnover and costs belong to their **actual hypothetical minute-fill
timestamps**, using calendar `[start, next boundary)` buckets even when different
from marked-return endpoints. Return calculations keep exact authoritative money
values; display rounding cannot replace evidence.

Time-based exposure uses actual hypothetical entry/exit timestamps and END only
as a duration boundary for an open final holding, never an END valuation price.
Report the fraction of hourly marks invested separately. Maximum drawdown is
**observed-hourly-reference-mark drawdown**, not minute, intrabar or continuous-time
drawdown. No minute-level equity path is reconstructed from unobserved marks.

## Limitations and interpretation

One-minute next-open still assumes the forecast is usable exactly at +60 seconds,
with no actual compute, network, submission or order latency. The first trade in
a minute need not be executable at precisely its nominal 00-second opening.
There are no historical quotes/order-book depths, quantity-specific fillability
or market-impact observations. Retrospective full-archive acquisition timestamps
are not price publication times, actual forecast issuance, or evidence of timely
historical access. Provider corrections, backfills and revisions remain possible.

**2024 has already been inspected in earlier research.** These comparisons are
exploratory and **not independent out-of-sample validation**, causal alpha or
profitability evidence. BTC/ETH are correlated; a single retrospective year does
not justify model promotion. Do not reinterpret simulations as real trades or
prospective paper-trading evidence.

## Separate identities and freeze/approval sequence

Reserve dataset contract `binance-1m-2024-v1` and prospective directory
`artifacts/execution/binance-1m-2024-v1/`; do not create or access it in this stage.
Use new minute-specific source IDs (`binance:spot:{symbol}:60:{open_time_ms}`),
manifest/schema version, native ZIP/sidecar pins and `minute_opens.csv` hash.
Hourly source paths, the approved hourly protocol hash and prior experiment
identifiers remain unchanged.

A future accepted protocol must have a newly approved version/hash. Reserve
provisional experiment label `stage-4b2-minute-base-v1` and a separate proposed
`artifacts/paper-historical/stage-4b2-minute-base-v1/` destination. Minute policy,
source evidence, decisions, fills, ledger, hourly marks and reports need separate
versioned manifests and filenames/paths within that destination. Record execution
interval 60 and valuation interval 3600 explicitly. Never overwrite, reclassify,
or opportunistically select among Stage 2C/2D or hourly Stage 4B.2 results.

Required future sequence, each step preserving earlier evidence:

1. Owner finalises and explicitly approves/freezes this separate protocol,
   including timing, costs, benchmarks, marks, parity-failure treatment and limits.
2. Review/validate the isolated acquisition implementation, synthetic tests,
   size/format limits, source identities and exclusive publication contract.
3. **Separately authorise actual acquisition** of exactly the 24 monthly Spot
   ZIP/sidecar pairs into a named fresh destination, using the reviewed code
   revision. Confirm source accessibility; no fallback source or loosened parsing.
   This authorises neither old artifact access nor calculations.
4. After successful independent offline replay, review and freeze the exact
   source ZIP and checksum-body SHA-256s, manifest, processed-file hash and code
   identity. Store the external manifest pin independently. No such pins exist yet.
5. Separately approve minute-replay implementation and causal/accounting/reporting
   tests, plus the scope of a future parity audit and original forecast loading.
6. Only then explicitly authorise real evaluations against those frozen sources
   and approved implementations into new destinations, with reproduction/review.

Neither this task nor the approved hourly protocol authorises those future steps.
Stage 4B.2C stops at draft design and synthetic source engineering. No Stage 4B.2D,
holdout access, genuine Stage 3 evidence, database or production work is included.

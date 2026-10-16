# Backtest Badger — Stage 4A Prospective Paper-Trading Evaluation Protocol

**Status:** APPROVED — STAGE 4A PROSPECTIVE PROTOCOL; NO IMPLEMENTATION OR DEPLOYMENT AUTHORISED  
**Protocol version:** `stage-4a-prospective-v1`  
**Date:** 16 October 2026  
**Companion specification:** [`stage-04a-paper-trading-spec.md`](stage-04a-paper-trading-spec.md)  
**Codebase baseline:** GitHub `owencrew/backtest-badger`, `4bd5b8773fb420f87353616ec644a4f9e5f29425`

## 1. Scientific objective and what results mean

The preregistered goal is to observe **prospectively** whether a fixed, simple Ridge-sign-based, continuous-holding trading policy can maintain a correctly accounted hypothetical portfolio, and how its modelled economic performance behaves after prospectively observed spreads, fees, slippage and operational failures. **No edge, profitability or exchange execution is assumed.**

This experiment observes genuinely issued forward signals and contemporaneously captured public quotations, then produces **simulated**, not actual, fills. It is not a brokerage account or proof of attainable real-market execution. Forecast accuracy is evaluated by the separate unchanged Stage 3C protocol; this protocol concerns a **trading policy's modelled performance**. Historical Stage 2C/2D results and any new continuous-holding historical validation remain separately labelled retrospective simulations.

This approved protocol must have its exact content hash pinned in experiment evidence **before the first experiment-eligible order or valuation**. Approval/commit does not activate a portfolio or authorise Stage 4B–4E implementation or Lightsail deployment. Later changes require a new named protocol/portfolio/cohort. Do not rewrite, erase or reclassify previous observations to improve results.

## 2. Primary experiments and eligibility

Two initially active, independently funded accounts:

| Portfolio | Venue / market | Policy | Starting cash |
|---|---|---|---|
| `ridge_sign_v1_btc` | Binance Spot BTCUSDT | Ridge Sign v1, long/cash | 10,000 USDT |
| `ridge_sign_v1_eth` | Binance Spot ETHUSDT | Ridge Sign v1, long/cash | 10,000 USDT |

Their original source evidence is Stage 3A schema-v1 published JSON, attributed to qualifying **timely automated** Stage 3B collection with immutable journal provenance. Validate original record identity, original file/content hashes, exact market and model recipe, `issued_at`, 15-minute window, actual current observation time and selected model. Only the `ridge` value directs trading: **forecast > 1e-12 => target long; otherwise target cash**. Positive following positive => hold; no forced sale at 4h interval. Ineligible, late manual and unattributed forecasts cannot generate v1 entries or normal strategy exits and are reported independently as ineligible; they may coexist with the unchanged separate forecast-scoring cohorts.

**At activation:** Capture a valid, immutable common first valuation mark after a deliberately approved portfolio activation gate; do not enable Ridge orders until that inception mark is committed. Record actual experiment inception timestamp, quote response, policy/config hash, funded ledger sequence and enabled worker evidence. This initial mark also establishes the counterfactual buy-and-hold entry quotation. If the expected initial mark is missed, postpone activation rather than choose an earlier unavailable quotation or fabricate a purchase; the new proposed start and reason must be recorded. The next timely eligible forecast observed after inception may be used; never replay forecasts issued or already missed before activation.

Portfolios with different start instants are **separate market experiments**, not two replications with a common market return. Do not pool BTC and ETH sample counts or claim independence: crypto returns are correlated.

## 3. Fixed operational policy

### 3.1 Signal horizon and missedness

Each market's native 4h close boundaries are 00:00, 04:00, 08:00, 12:00, 16:00 and 20:00 UTC. Forecast feature eligibility is close +60 sec; automated Stage 3B forecast must be issued before close +16 min, exclusive. A new buy must be decided and filled while the forecast's window is still eligible, using a fresh independently requested quote **after** its submitted order. A timely negative signal creates a sticky exit requirement that survives the original forecast deadline.

If no qualifying forecast exists after a publication deadline, record that source horizon as **missed**, detected at the actual discovery time. Missing is **neither zero nor negative**. One consecutive miss leaves current exposure unchanged and flagged stale; **two consecutive missed source horizons** trigger a current-time risk-off exit if exposed. The streak resets on a qualifying eligible forecast. Missing periods during downtime are counted from the grid only **when discovered**, with no invented retrospective decisions/fills. Report number and length of stale-exposure episodes.

### 3.2 Sticky exit, recovery and re-entry

When negative Ridge or the risk-off condition creates an `EXIT_REQUIRED` decision, it creates a **sticky obligation** until base holdings are genuinely zero and `EXIT_SATISFIED` is atomically recorded. A single order is valid for **30 seconds**. Expiry/rejection/network failure leaves the position intact and obligation open. The worker may retry at most one new prospective exit attempt per 5-minute cycle with fresh quote acquisition and a distinct order identity, until liquidation or an explicit blocked-dust/integrity pause. No order may be filled using quotes obtained before its submission, previous runs, later historical candles or reconstructed clock times. A later positive forecast while exit pending is observed/ignored but cannot cancel it. Re-entry requires a **new eligible forecast issued after exit satisfaction**; prior signals are not re-used.

A successful sell fill plus **both** USDT/base ledger postings and final `EXIT_SATISFIED` evidence (if flat) must commit atomically. Failed/rejected/expired attempts have **no ledger postings**. A worker crash after committing a fill cannot generate a second fill for that order; a crash after quote receipt but before fill commit cannot reuse that quote as fresh fill evidence after restarting. A failed buy is not continuously retried from the same old decision; a later genuinely eligible forecast is required.

### 3.3 Execution pricing and trading rules

Prospectively request Binance Spot public `bookTicker` bid/ask and displayed bid/ask sizes. Record exact raw response bytes or bounded body, source URI, SHA-256, market identity, HTTP result, request/receipt UTC times, monotonic duration when available and actual fill time. The endpoint contains **no exchange-side quote timestamp**; the quote freshness limit is *client-observed request/receipt latency*, not proof of exchange quote age or executable fill.

Default model: `fee=10 bps` per side, **USDT**, and `adverse slippage=2 bps` each side. Buy = observed ask × 1.0002; sell = observed bid × 0.9998. The spread is already incorporated in observed best bid/ask: no additional 1 bp historical half-spread in prospective execution. Fee rounds **up to 0.00000001 USDT**; quantity rounds **down** to captured applicable market lot step; after fee rounding the chosen buy size cannot exceed cash. Reject rather than partially fill if full quantity exceeds displayed same-side top-of-book size or applicable supported filter bounds. The filter evidence is captured/versioned; initial max filter-cache age 1 hour.

The proposed request-to-receipt limit is **2 seconds**, receipt-to-fill limit **1 second**, order lifetime **30 seconds**. Reject stale/invalid responses, clock reversal, invalid market identity, zero/negative quotes, bid>ask, insufficient holdings/funds or unsupported filters. Market orders are never actually placed; these rules approximate feasibility but do not replicate depth, queue, market impact, volatile spread changes or Binance's internal notional reference calculations.

## 4. Valuation schedule and canonical performance observations

Attempt independent prospective portfolio marks at **00:10/04:10/08:10/12:10/16:10/20:10 UTC**, within the next five minutes. A valid mark persists the **original quote bid/ask/size evidence**, request/receipt/mark timestamps, exact hash, market/policy version and **atomic snapshot ledger sequence**; use the **bid** to mark long holdings. A slot without valid timely mark yields `MARK_MISSING` recorded at actual discovery time, not a later backfilled quotation. There is no forward filling, imputation, fabricated intrabar mark or interpolation represented as observed.

Define at each mark `E_t = cash_at_pinned_ledger_seq + base_qty_at_pinned_ledger_seq × observed_bid_t`. Include the starting 10,000-USDT equity point at inception. `Unrealised_t = base_qty × bid − remaining_weighted_average_basis`; `Realised_t = accumulated sale net proceeds − basis released`; `Realised + Unrealised = E_t − 10,000`, with no subsequent funding. The separate hypothetical net liquidation estimate deducts modelled sell slippage and fee and is undefined when filters or dust make full liquidation ineligible. Realised and unrealised values must reconstruct exactly from saved paired postings and fill evidence; never retrieve a newer price when reproducing an earlier mark.

For each market account, predeclare outputs: cumulative total return, monetary gain/loss, marked equity curve, maximum **observed-mark** drawdown, time spent invested, exposure at valid marks, side-specific turnover, executed/rejected/expired order counts, quote-failure rates, fees, cost attribution, realised/unrealised P&L, number/age of unresolved exits, missing signal/mark counts, worker downtime and modelled net liquidation equity where defined.

**Drawdown:** peak-to-trough only among inception and **valid observed marks**; gaps explicitly shown. This is not a tick-by-tick or exchange-realised loss path. Do not make continuous-trading Sharpe/volatility claims without sufficient fixed-frequency complete observations; see maturity rules.

## 5. Preregistered benchmarks and fair comparisons

**Cash benchmark:** 10,000 USDT constant with zero trading costs, over the same actual inception/mark schedule. It is a virtual analytical control, not a funded brokerage trade.

**Buy-and-hold analytical benchmark:** at the **same initial eligible observed quote mark** as the Ridge portfolio inception, simulate **one** full affordable buy using original ask and the **same 10 bps fee / 2 bps adverse slippage / precision/lot/notional rules**, then hold the resulting base units and residual USDT. Thereafter mark to each contemporaneous valid bid using the same observed quote event, without any hypothetical later purchases or sales. Clearly label this an **analytical prospective quote-based counterfactual**, not a separately persisted `paper_order` or exchange execution. If the first-quote liquidity/filters cannot support the all-or-nothing 10,000-USDT benchmark buy, record `benchmark_unavailable` at inception instead of silently assuming an obtainable position or beginning later at a favourable price.

**Fairness:** Ridge and benchmark must use the same venue, market, quote stream, initial capital and actual inception. At each comparison timestamp, benchmark and Ridge values derive from that **same retained mark**, with no substitution of current prices. Keep exposure/turnover differences explicit; a cash-relative gain does not demonstrate timing alpha and BTC/ETH are correlated. Results across different parameter/cohort versions are separate, not pooled as though identical experiments.

**Historical reference:** The 2024 continuous-holding replay (Stage 4B.2) uses archived independent hourly opens and synthetic spread assumptions, not genuine quote snapshots. Its purpose is implementation verification and descriptive economic sensitivity; it is **not an execution-price parity test**, not a prospective benchmark and not comparable tick-for-tick with Stage 4 quotes. Existing three-hour Stage 2C trades remain a different strategy with separate evidence. Holdout 2025–2026 research labels are not accessed.

## 6. Defined reporting periods and descriptive evaluation

- **From-inception series:** full retained marked equity and every valid/missing scheduled mark from inception; no cherry-picked starting points.
- **Checkpoint summaries:** day 30, 90 and 180 after actual activation for each market, plus cumulative all-time and weekly UTC calendar summaries. Map each cutoff `inception_at + N × 24h` deterministically to the **first predefined four-hour valuation slot whose scheduled UTC time is not earlier than that cutoff** (at most four hours later). Only that slot defines the checkpoint value. If its mark is missing, label the checkpoint unavailable and separately show most recent valid observation/time; never slide to another favourable quotation.
- **Daily returns:** only from exactly aligned consecutive days' predefined **00:10 UTC** valid marks; missing a mark makes the relevant daily return undefined. Do not compound unequal-gap observed marks and call the result a full daily series.
- **Maximum drawdown:** mark-based on all valid marks, clearly noting missing intervals that may conceal deeper drawdowns.
- **Comparative returns:** use observed marks available to the evaluated Ridge and counterfactual benchmark, disclose sample count and missingness; report unpaired observations separately, not as outperform/underperform estimates.
- **Maturity labels:** below **30 calendar days** or fewer than **100 qualifying timely forecasts per market**, label trading assessment `early/insufficient sample`. At 30 days, show descriptive results rather than significance claims. Do not calculate or interpret Sharpe-like daily risk metrics with fewer than **30 valid consecutive-day return observations**; even after that threshold, label such metrics exploratory because of changing exposure, crypto regimes and missingness. At 90/180 days, update fixed prespecified descriptive summaries without promoting a winning model.
- **Scientific status:** no inferential p-values, confidence claims, proof of profitability or model-ranking/promotion in v1. Any later formal hypothesis test requires a separately preregistered protocol specifying sample size, autocorrelation treatment, multiple testing and selection bias.

Do not retrospectively select the best model, reset a losing portfolio, change its initial cash or quietly suppress outages. The 2024 Ridge Sign choice is **post-hoc relative to the already-inspected Stage 2C results**, and that selection is disclosed; its future performance is assessed only from inception onward.

## 7. Required evidence, retention and integrity

Every active portfolio references: canonical strategy/config JSON hash and version; original forecast file path and hashes; original `issued_at` and local discovery timestamp; current-time decision and outstanding obligation; unique internal submitted order; quote request/receipt/original body hash; adjusted fill quantity/price/fee (or failure reason); market filter evidence/version; exactly paired atomic USDT/base ledger entries; ledger high-water and cost basis replay; original scheduled valuation events and missing slot evidence; deployment/release and approved protocol fingerprints.

A scheduled job being active is not proof it successfully executed. An order request or observed quote is not proof of a simulated fill. A `FILL` is valid only when committed with its paired postings and the order's terminal state; without commit, it has not happened. Missing source artifacts or corrupted checksums make affected decisions/marks **unverifiable**; the system must report failure and avoid inventing repairs.

File and DB evidence must be included in coherent encrypted backup/checkpoint coverage. Before production activation, the existing consistent PostgreSQL fingerprint/restore drill must be extended to **all five paper tables** and demonstrated through a real **isolated** restore with ledger+valuation replay. The original Stage 3 forecast/outcome artifacts remain untouched. Retention of newly generated events must not be pruned without a separately approved preservation/recovery policy.

## 8. Operational cohort definitions

Classify observations **before seeing profit/loss**:

- `primary_timely_paper`: portfolio activated; strategy/protocol exact version; original eligible Stage 3B automated forecast, genuine current-time decision and properly retained live quote evidence, with either successful atomic modelled fill or explicit no-order action. Failed attempts count in this cohort's operational history; do **not** select only successfully filled trades.
- `missed_signal`: a 4h horizon with no qualifying timely automated forecast, discovered at actual time; never reconstructed as an old forecast.
- `rejected_execution`: a valid decision/order but no modelled fill owing to invalid/late quote, insufficient liquidity, filters, funds or recorded failure; no financial posting.
- `exit_recovery`: an ongoing sticky obligation, including rejected/expired repeated **prospective** exit attempts and eventual fill, counted as part of the original portfolio experience.
- `missing_valuation`: scheduled mark failed; retain gap and never insert a later historical valuation to replace it.
- `invalid_evidence`: bad hash, broken identity, inconsistent posting, time reversal or failed reproducibility; flagged and excluded **with its count and cause** from valid marked statistics, never silently removed.

These categories are not alternate hidden portfolios. Model performance results must not be conditioned solely on successful trades; report rejected orders, delays, unresolved exposure and downtime beside the money metrics.

## 9. Protocol-preserving changes and incidents

- **No silent optimisation:** after activation, Ridge threshold, fee/slippage assumptions, cash, strategy version, missing-signal trigger, exit behavior, mark schedule or quote limits are frozen for this account. Any material change creates **new version/cohort** with independent inception. The original keeps all prior gains/losses and incident evidence.
- **Bug fix:** document date, affected observations, exact source/release hashes, why behaviour was incorrect, old/new report versions and whether earlier results are invalid. Never edit original fill or source evidence; if a correction requires a financial entry, it must be a separately approved explicit compensating mechanism in a later schema/protocol, not a silent ledger edit. No emergency profit-restoring rewrite.
- **Market outage:** show missed signals, failed quotes, missed marks, sticky exit age, remaining exposure and the first successful *current* quote after recovery. No backdating or fabricated flat portfolio.
- **Irrecoverable dust or ledger mismatch:** fail closed, mark paused/blocking, retain all evidence, require explicit owner-reviewed remediation. Do not describe an unresolved exit as completed.
- **Infrastructure and deployment:** independent approval required to enable worker or modify production DB, monitoring, backups, timers, deployment or retention. Operating cost and service reliability are reported alongside investment simulation results.

## 10. Acceptance test plan for the protocol itself

1. Activation starts only with true observed initial mark; no earlier signal or price is reused.
2. Original Stage 3B provenance and deadline govern eligible signals; Stage 3C outcome files are provably not read by the strategy.
3. Positive and nonpositive Ridge values create correct long/cash targets; continuous positive signals do not churn the position.
4. Two missed horizons trigger a **current** risk-off decision, not a backdated one.
5. An exit survives failed network quotes, an expired 30-second order, an app crash and an intervening positive forecast; fresh quote after restart, no reuse.
6. Each `FILL` has exactly two validated ledger postings, and exactly one successful fill per order and quote; failed terminal attempts leave balances unchanged.
7. Fees, original spread, adverse slippage, quantity rounding and partial/full weighted-average basis reconcile exactly, including worked hand-calculated examples.
8. First eligible quote and matched mark define deterministic buy-and-hold counterfactual; no look-ahead or recreated benchmark position.
9. Later ledger movements cannot change earlier mark equity: replay through saved as-of sequence produces byte-for-byte/Decimal-equivalent results.
10. Missed valuation produces a permanent gap, not a later filled price; daily returns around missing 00:10 mark are undefined.
11. 30/90/180-day reporting respects actual inception and observation coverage; no artificial daily Sharpe due to gaps.
12. Historical 2024 validation calls identical strategy/accounting primitives, never the future labels or holdout, and explicitly reports historical hourly-reference versus prospective bid/ask non-parity.
13. Original Stage 2C/Stage 3 evidence files unchanged; new outputs carry source/policy/code hashes and timestamps.
14. Simulated status and all risk, missingness, outages and benchmark limitations are visible in the read-only report/API.
15. An isolated PostgreSQL restored snapshot reproduces all five tables, fill/posting constraints, source fingerprints, marks, account balances and documented curve metrics.

## 11. Signoff before freezing

**Provisionally accepted design:** Ridge Sign reference, independent 10,000-USDT market portfolios, continuous exposure, prospectively captured bid/ask, 10 bps USDT fees, 2 bps adverse slippage, all-or-nothing modelled fills, weighted-average cost basis, five-table append-only evidence/ledger with `paper_market_event`, sticky exit obligations, atomic fill/postings and versioned historical valuation evidence.

**Require explicit product-owner confirmation of operational numerical defaults before freeze:** two missed horizons as safety trigger; quote RTT 2 sec and receipt-to-use 1 sec; 30-second simulated order lifetime; five-minute exit retry cadence; no buy retry on stale signal; initial valuation slot and five-minute window; one-hour filter TTL; fee rounding to 1e-8 USDT; immediate all-or-nothing top-of-book rejection; benchmark inception and missingness presentation. If market/API tests invalidate feasibility, revise the **draft** and reapprove before activation, not silently in a running experiment.

On approval, separately version the final protocol as `docs/stage-04a-prospective-evaluation-protocol.md` and pin its SHA-256 from the outside (e.g., final specification manifest/handoff); do not put the file's own SHA inside itself. Preserve this exact version once prospective economic data are visible. **No Stage 4B.1 Codex implementation prompt is authorised by this draft alone.**
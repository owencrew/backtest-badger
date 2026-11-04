# Backtest Badger — Stage 6A.1: Study 002 — Can a Slower Trend Beat the Noise?

## Objective

Develop the second genuine historical trading strategy study for Backtest Badger:

**Study 002 — Can a Slower Trend Beat the Noise?**

The first study investigated a machine-learning Ridge-sign strategy and found that frequent trading generated substantial costs and poor economic performance.

Study 002 investigates a natural follow-up:

**Can a simpler, slower-moving trend-following strategy reduce trading costs and improve economic performance?**

Implement one predeclared 30-day trend-following strategy, validate it using the existing research infrastructure, and perform one reproducible genuine historical backtest against independently funded benchmarks.

Prepare the resulting research for eventual inclusion in **The Dig**, but do not publish it without owner review.

The principal aim is credible, transparent research — not finding a profitable strategy at any cost.

---

## 1. Starting context

Repository:

`~/Code/backtest-badger`

GitHub:

`owencrew/backtest-badger`

Start by checking:

- Current HEAD and working tree
- Repository instructions in `AGENTS.md`
- Most recent GitHub CI results
- Existing historical research methods and data provenance
- Existing minute-level replay infrastructure
- Current website research presentation
- Relevant tests and documentation

Read at least:

- `README.md`
- `docs/roadmap.md`
- `docs/architecture.md`
- `docs/development-handoff.md`
- `docs/stage-02a-research-dataset.md`
- `docs/stage-02b-predictive-baselines.md`
- `docs/stage-04b2c-minute-execution-protocol.md`
- `docs/stage-04b2e5e-local-execution-decision.md`
- `docs/stage-04b2e5e-simple-local-historical-runner.md`
- `docs/stage-04b2e5g-first-genuine-historical-backtest.md`
- `src/backtest_badger/local_historical_backtest.py`
- `src/backtest_badger/paper_minute_historical.py`
- `src/backtest_badger/paper_minute_integration.py`
- `src/backtest_badger/paper_minute_reporting.py`
- `src/backtest_badger/paper_accounting.py`
- `src/backtest_badger/paper_execution.py`
- `web/app/dig/page.tsx`
- `web/components/dig-explorer.tsx`
- `web/lib/research.ts`
- Existing minute-data and accounting tests

Read the existing authenticated input publication, integrity and sign-off documentation.

Determine which existing inputs and execution components can safely be reused, rather than implementing an entirely separate backtesting engine.

Preserve all existing frozen scientific protocols and historical outputs.

---

## 2. Background: Study 001

The first genuine 2024 historical backtest completed on 24 October 2026.

It compared the Ridge-sign strategy against Cash and Buy & Hold using independent BTCUSDT and ETHUSDT portfolios.

All accounts began with 10,000 USDT.

### Existing verified results

| Strategy | BTCUSDT return | ETHUSDT return |
|---|---:|---:|
| Ridge Sign | −60.69% | −57.96% |
| Cash | 0.00% | 0.00% |
| Buy & Hold | +120.81% | +46.18% |

Trading activity and attributed costs:

| Market | Ridge buys | Ridge sells | Total attributed costs |
|---|---:|---:|---:|
| BTCUSDT | 570 | 570 | 9,932.12 USDT |
| ETHUSDT | 499 | 499 | 9,239.49 USDT |

These historical results are already known.

The new study must not treat 2024 as a previously unseen test period.

The first study demonstrated a severe cost burden, but it did **not** isolate trading frequency as the sole cause of underperformance.

Study 002 should investigate a different decision rule under comparable execution assumptions.

Do not rewrite or reinterpret Study 001.

---

## 3. Research question and hypotheses

### Primary research question

Does a deliberately slower, rules-based trend-following strategy reduce turnover and trading costs relative to the previously evaluated Ridge-sign strategy?

### Secondary research question

Does that reduction in trading activity translate into improved net portfolio returns or drawdowns?

### Hypotheses

**H1 — Trading activity**

A daily 30-day trend signal will result in fewer executions and lower turnover than the existing Ridge strategy.

**H2 — Trading costs**

Lower turnover will reduce attributed transaction costs.

**H3 — Economic performance**

Reduced trading costs may improve the strategy's net returns relative to Ridge, but this is not guaranteed.

**H4 — Benchmark performance**

Even if the new strategy outperforms Ridge, it may still underperform Buy & Hold or Cash.

Treat all four as hypotheses, not assumptions or expected findings.

Report the results regardless of whether they support the hypotheses.

Do not select a different strategy after inspecting the outcomes.

---

## 4. Predeclared strategy: 30-Day Trend v1

Implement one fixed strategy:

**`trend_30d_daily_v1`**

This is a simple, long/cash time-series momentum strategy.

It does not use machine learning.

It does not attempt to forecast the exact magnitude of a future return.

### Trading universe

- Binance Spot BTCUSDT
- Binance Spot ETHUSDT

Each market receives its own independent portfolio.

No combined allocation or shared cash.

### Signal frequency

Evaluate the strategy once per day at:

`00:01 UTC`

Use only price observations from completed candles available by that decision time.

The strategy must not evaluate new signals every four hours, every hour or every minute.

### Trend calculation

At each UTC midnight boundary D, obtain:

- `P_now`: the closing price of the latest completed native four-hour candle, whose close boundary is D.
- `P_30d`: the closing price of the native four-hour candle whose close boundary is exactly 30 calendar days before D.

Define:

`trend_return = (P_now / P_30d) - 1`

Use exact Decimal arithmetic for the trading decision.

Decision rule:

- If `trend_return > 0`, target **LONG**.
- If `trend_return <= 0`, target **CASH**.

There is no deadband, volatility filter, stop-loss, profit target or hysteresis in v1.

The lookback is fixed at **30 days**.

The evaluation frequency is fixed at **once per day**.

Both decisions are frozen before genuine performance evaluation.

### Position behaviour

- LONG means invest available cash in the selected spot asset, subject to the execution engine's affordability and quantity rules.
- CASH means hold USDT.
- If already long and the signal remains long, HOLD.
- If already in cash and the signal remains cash, CASH_NOOP.
- If the target changes from long to cash, sell the existing holdings.
- If the target changes from cash to long, buy using available cash.
- Retain continuous holdings between decisions.
- No forced daily liquidation.
- No leverage.
- No short selling.
- No borrowing.
- No portfolio rebalancing to intermediate weights.

Do not add secondary thresholds or risk rules to improve historical performance.

### Why this rule?

A 30-day directional trend is easy to explain, reproducible, and meaningfully slower than a signal potentially changing every four hours.

Evaluating it only once daily further constrains trading frequency.

This is an exploratory research choice, not a parameter proven optimal for crypto.

Do not conduct a 7/14/21/30/60/90-day parameter sweep.

Do not optimise the signal threshold.

Do not choose the better-performing signal separately for BTC and ETH.

---

## 5. Chronological integrity and warm-up

The historical evaluation interval is:

`2024-01-01T00:00:00Z`

through

`2025-01-01T00:00:00Z` exclusive.

Use a consistent signal schedule across both markets.

### Required warm-up history

The first 2024 signal requires a 30-day trailing observation, including historical data before 1 January 2024.

Inspect whether the existing authenticated/native four-hour history contains the required warm-up observations.

Reusing a previously validated historical source is preferable to acquiring another dataset.

Do not silently substitute prices from an unverified source.

Do not approximate the first signal using fewer than 30 days.

Do not fill missing observations.

If the full validated warm-up cannot be established, report the blocker and stop before the genuine run.

### Prevent look-ahead

At each decision:

1. Identify the latest genuinely completed four-hour candle.
2. Read only its completed close and the completed close exactly 30 days earlier.
3. Compute the trend signal from those two values.
4. Record assumed signal availability at midnight plus 60 seconds.
5. Execute, if necessary, at the strictly next native one-minute opening.

For a 00:01 UTC signal, the first hypothetical execution reference is:

`00:02 UTC`

Do not execute at 00:00 or 00:01.

Do not use current-day future high, low, close or volume.

Do not use future target returns, Ridge forecasts, eventual strategy profitability or scored outcomes to calculate the trend signal.

Source candles must be validated for exact identity, order, UTC boundaries and completeness.

Any required missing source observation must fail closed.

Document that historical +60-second candle availability and next-minute execution are modelling assumptions, not proof of actual 2024 exchange-side availability.

---

## 6. Reuse the existing execution methodology

The new strategy should be compared fairly with the existing 2024 study.

Reuse the authenticated native-minute execution data and existing economic/accounting primitives where technically compatible.

Preserve the following assumptions:

| Parameter | Requirement |
|---|---|
| Initial funding | 10,000 USDT per account |
| Execution reference | Strictly next native 1-minute opening after signal availability |
| Fee | 10 bps per side |
| Half-spread assumption | 1 bp per side |
| Adverse slippage | 2 bps per side |
| Buy execution adjustment | Minute opening × 1.0003 |
| Sell execution adjustment | Minute opening × 0.9997 |
| Base quantity step | 0.000001 |
| Accounting | Exact Decimal with existing rounding conventions |
| Holdings | Continuous long/cash |
| Valuation | Native minute HH:00 opening, hourly |
| End of observation | 31 December 2024, 23:00 UTC |

Do not invent actual historical bid/ask quotes, fill confirmations or observed liquidity.

Preserve the distinction between hypothetical execution prices and actually executable orders.

Retain independent funding and ledger identities.

### Reuse versus modification

The existing historical runner is tied to the frozen Ridge forecast schedule.

Do not modify that frozen protocol to accept arbitrary daily signals.

Instead, inspect the replay architecture and identify the smallest safe way to support another strategy.

Prefer extracting a reusable strategy-independent execution core if it can be done without changing existing Ridge behaviour.

Otherwise, implement a narrowly scoped adapter using existing trading/accounting primitives.

Avoid duplicating hundreds of lines of execution and ledger logic.

Preserve exact results and byte identities of Study 001.

Regression tests must prove that the existing Ridge study still produces its original results when supplied the same pinned inputs.

If the engine cannot safely support the new study without substantial architectural changes, document the issue and propose the smallest compatible refactor before proceeding.

---

## 7. Benchmarks and comparisons

Include the following independent portfolios for each market.

### A. 30-Day Trend v1

The new strategy.

### B. Cash

10,000 USDT, no trading and no interest.

### C. Buy & Hold

The existing independently funded buy-and-hold benchmark, using the same authenticated minute-level opening reference and the same fee, spread, slippage and quantity conventions.

One hypothetical initial purchase, with no forced liquidation at year-end.

### D. Ridge Sign — historical reference

Use the previously verified Stage 4B.2E.5g result as a fixed historical reference.

Do not regenerate the Ridge model or change its forecasts.

Verify all historical reference figures against the authoritative original report.

The new study's primary accounts must be independently verified.

If cost, timing, source, mark or accounting differences prevent direct comparison with the existing Ridge results, report those differences explicitly.

Do not call the results a controlled frequency-only experiment: the strategies also differ in their signal construction.

### Comparison metrics

At minimum, calculate for each strategy and market:

- Initial funding
- Final marked portfolio value
- Cumulative net return
- Annualised descriptive return
- Maximum drawdown from observed hourly marks
- Annualised daily volatility, where defined
- Daily-return Sharpe ratio using the existing stated convention, where defined
- Number of buys
- Number of sells
- Number of signal evaluations
- Number of position changes
- HOLD/CASH_NOOP counts
- Total turnover
- Turnover relative to initial funding
- Total fees
- Total attributed half-spread
- Total attributed slippage
- Total attributed costs
- Time invested
- Fraction of hourly marks invested
- Final cash
- Final base-asset holdings
- Realised and unrealised accounting values where supported
- Monthly returns
- Monthly trading activity
- Best and worst complete observed days

Explicitly report undefined metrics rather than inventing zero values.

Distinguish funding-relative return from mark-to-mark period return.

Preserve the previous study's convention for the incomplete final day and December period.

Do not invent a 2025 endpoint valuation or terminal sale.

---

## 8. Research integrity and execution sequencing

This is an important requirement.

### Phase A — Inspect and design

Before executing the new strategy against genuine 2024 outcome data:

1. Inspect the existing data contracts and replay architecture.
2. Confirm availability of the required 30-day warm-up history.
3. Confirm that the existing minute source can be reused.
4. Write the complete Study 002 methodology.
5. Specify the exact strategy, costs, timing, benchmark treatment and validation.
6. Implement synthetic tests.
7. Freeze the research configuration and record its SHA-256.

Create:

`docs/studies/study-002-methodology.md`

Choose the exact final filename after checking repository conventions.

The methodology must be fixed before the first genuine Study 002 economic run.

Record the source revision, exact configuration identity and time at which the methodology was frozen.

Do not choose parameters after viewing results.

### Phase B — Synthetic implementation verification

Run deterministic tests using fabricated prices.

Cover positive, negative and zero trends, chronology, held positions, transitions, transaction costs, missing data, input identity, Decimal precision and ledger correctness.

Verify independently that the strategy cannot see future prices.

Do not use synthetic profitability as evidence of market behaviour.

### Phase C — Genuine historical evaluation

This prompt authorises **one local, read-only genuine 2024 historical Study 002 run**, provided that:

- All required authentic input files are available locally.
- Original evidence hashes and sign-off checks pass.
- The warm-up history has verified provenance.
- The methodology is frozen and recorded.
- Synthetic tests and regressions pass.
- The implementation does not alter frozen Study 001 files.

Use the existing local research artifacts.

Do not download replacement market data, access Lightsail, or query production databases to repair missing inputs without separate authorisation.

The genuine run must write into a fresh, private, Git-ignored results directory.

Never overwrite an earlier run.

Record all actual attempts, including failures.

After execution:

- Verify source and output SHA-256 identities.
- Verify each portfolio ledger independently.
- Reconcile holdings, cash, costs and marked equity.
- Independently validate the final summary against account evidence.
- Retain the complete result manifest.
- Produce a clear completion marker only after all checks pass.

If the genuine run fails, do not silently retry with modified settings.

Report the failure and retain its diagnostic evidence.

### Phase D — Interpretation

Analyse the results without optimising them.

Address:

1. Was turnover actually lower?
2. Were trading costs lower?
3. Did net returns improve relative to Ridge?
4. Did drawdown improve or deteriorate?
5. Did the strategy beat Cash?
6. Did it beat Buy & Hold?
7. Was the strategy invested during major market gains?
8. Did slower signals lag important market reversals?
9. How much of the result appears associated with exposure differences versus trading costs?
10. What remains impossible to infer from this study?

Do not present descriptive associations as causal proof.

Do not claim that lower turnover necessarily caused better performance.

A lower-cost strategy can still lose substantial money.

Report negative findings with the same prominence as positive ones.

---

## 9. Avoiding hindsight bias

2024 has already been examined in Study 001.

Therefore:

**Study 002 is exploratory retrospective research, not a new untouched out-of-sample test.**

The parameter choice must be documented as predeclared for Study 002, without claiming it was chosen before anyone knew the 2024 market history.

Do not evaluate multiple candidate lookbacks and publish only the winner.

Do not silently evaluate additional historical years and select the most favourable period.

Do not inspect or use the existing held-out 2025–2026 target outcomes to select strategy parameters.

Any subsequent genuinely unseen or prospective evaluation requires a separately frozen protocol, appropriate source eligibility and its own research classification.

A single profitable historical year would not establish a durable trading edge.

BTC and ETH should remain separate and should not be presented as independent confirmations of profitability.

---

## 10. Reporting and visualisation

Produce a complete scientific report and a concise human-readable research summary.

Suggested files:

`docs/studies/study-002-slower-trend-results.md`

`docs/studies/study-002-methodology.md`

The research report should contain:

- Executive summary
- Research question and hypotheses
- Strategy definition
- Data and source identities
- Execution assumptions
- Reproducibility details
- Genuine run identity
- Main account results
- Comparison with Ridge
- Cost and turnover analysis
- Risk metrics
- Monthly observations
- Interpretation
- Limitations
- Future research opportunities

Include appropriately generated charts from verified results:

- Portfolio equity over time
- Drawdown over time
- Position exposure / long-versus-cash history
- Trading activity
- Attributed cost comparison
- Monthly performance

Use the actual retained account evidence, not manually invented return series.

Every chart must carry its source identity and relevant units.

Use consistent market colours and labels where the website already has an established convention.

Clearly identify historical simulations.

Do not visually imply real trading or future returns.

### Publication-ready summary

Prepare a concise public-facing draft explaining:

- Why Study 001 motivated the experiment
- The new simple trend rule
- What happened after costs
- How it compared with Ridge and Buy & Hold
- What the findings mean
- What they do not establish

Use accessible language without sacrificing scientific accuracy.

If results are unavailable, produce an explicitly labelled methodology draft rather than inventing outcomes.

---

## 11. Prepare the study for The Dig

The current public Dig contains the original Ridge study.

Ultimately, The Dig should become a research library with several independently versioned studies.

The intended future navigation is:

**The Dig**
- Study 001 — The 2024 Ridge Sign Study
- Study 002 — Can a Slower Trend Beat the Noise?
- Later studies covering mean reversion, volatility management and other strategies

For this stage:

1. Inspect the existing page and components.
2. Propose a scalable study-card or study-selector structure.
3. Preserve the current Study 001 experience.
4. Prepare the verified Study 002 results in a website-friendly, source-linked format.
5. Draft the layout and copy for a dedicated Study 002 view.
6. Consider reusable visualisations for comparing equity, drawdown, trades and costs.
7. Document the smallest safe website integration.

Do not automatically make Study 002 public.

Do not add an exported public route that exposes unapproved research.

Do not place Study 002 in the production sitemap until publication approval.

Do not replace existing Study 001 numerical constants or approved research evidence.

If building a local preview is practical, it must remain unavailable from the production static export until explicitly approved.

Avoid introducing a generic experiment framework just for two studies.

### Field Notes

If the research produces a substantive and defensible finding, prepare an optional new Field Notes draft.

It must remain unpublished until separately reviewed and approved.

Do not change the seven existing editorial approval hashes.

No auto-publication.

---

## 12. Testing

Run all applicable existing tests and add new focused regressions.

### Strategy tests

- Exact 30-day lookback
- UTC daily signal schedule
- Positive trend
- Negative trend
- Exactly zero trend
- Decimal precision
- Missing warm-up data
- Missing source observation
- Non-finite or invalid price
- Out-of-order candles
- Duplicate candle identities
- Incorrect candle boundaries
- Future-price leakage
- No intra-day strategy reevaluation
- Continuous HOLD behaviour
- CASH_NOOP behaviour
- Long-to-cash transition
- Cash-to-long transition

### Execution tests

- +60-second signal availability
- Strictly next-minute execution
- Fees, spread and slippage
- Quantity rounding
- Fee-aware affordability
- No negative cash or holdings
- Atomic paired ledger accounting
- Independent BTC and ETH accounts
- Correct position and P&L reconciliation
- Correct hourly mark ordering
- Correct final holdings
- No invented terminal liquidation

### Provenance and reporting tests

- Correct authenticated input identities
- Frozen methodology hash
- Input substitution rejection
- Incomplete input rejection
- No overwrite of previous runs
- Deterministic replay
- Complete output manifest
- Output hash verification
- Reconciliation of summary and underlying ledger
- Monthly and annual consistency
- Correct treatment of partial days
- Explicit undefined metrics
- Preservation of Study 001 results and identities

Run:

- Appropriate Python pytest suites
- Ruff lint
- Ruff formatting
- Existing research regressions
- Relevant PostgreSQL integration tests when an isolated test database is available
- Documentation/link checks
- Any relevant frontend tests if website code changes

Do not change scientific assertions to make the new results appear favourable.

---

## 13. Resource and operational boundaries

Study 002 is local historical research.

It must not affect the live research or public website.

Do not:

- Access production Lightsail infrastructure
- Change live forward collectors or scorers
- Modify existing R2 objects
- Change Cloudflare settings
- Deploy the website
- Modify GitHub Actions release behaviour
- Retrain the Ridge model
- Regenerate existing frozen forecasts
- Modify Study 001 evidence
- Change approved historical protocols
- Modify existing editorial approval hashes
- Run real-money orders
- Create exchange API trading credentials
- Enable prospective paper trading
- Use hidden future information
- Download additional market data without approval
- Perform parameter optimisation on 2024
- Publish synthetic research as genuine evidence

One genuine local 2024 Study 002 economic run is authorised only under the conditions in Section 8.

Do not commit or push in this stage.

Stop for owner review before publication or deployment.

---

## 14. Documentation and handoff

Create or update as appropriate:

- `docs/studies/study-002-methodology.md`
- `docs/studies/study-002-slower-trend-results.md`
- Relevant research architecture documentation
- `docs/roadmap.md`
- `docs/development-handoff.md`

Keep the existing historical reports unchanged.

Archive this complete request at:

`prompts/stage-06-research/001-study-002-slower-trend.md`

Create the new prompt directory if necessary.

Update:

`prompts/README.md`

Document any change to the originally proposed design, including its timing and justification.

Do not silently change the 30-day lookback, decision rule or costs.

---

## 15. Final completion report

Provide:

1. Exact starting Git commit.
2. Summary of the new trend strategy.
3. Verified research-input identities.
4. Frozen methodology version and SHA-256.
5. Existing engine components reused.
6. New modules and interfaces.
7. Synthetic test results.
8. Regression results for Study 001.
9. Genuine run status and output identity.
10. BTC and ETH economic results, if successfully produced.
11. Direct comparison against Ridge, Cash and Buy & Hold.
12. Turnover and transaction-cost differences.
13. Risk and drawdown findings.
14. Scientific limitations and potential confounders.
15. Reproducibility instructions.
16. Complete changed-file inventory.
17. Publication-ready Dig summary and proposed page structure.
18. Any remaining source or implementation blockers.
19. Recommended Conventional Commit message.
20. Proposed next step for owner review and website integration.

Suggested commit message:

`feat(research): add study 002 daily trend backtest`

### Definition of success

Study 002 succeeds when it has:

- One predeclared, reproducible strategy.
- Genuine authenticated historical inputs.
- Correct causal signal construction.
- Reused and verified execution/accounting assumptions.
- A fully reconciled independent ledger.
- Transparent comparison with existing benchmarks.
- A scientifically honest report.
- Source-linked, publication-ready research material.
- No changes to production systems or existing approved evidence.

**A losing strategy is a valid research result.**

Do not optimise away an unfavourable outcome. The objective is to learn whether a slower trend changes turnover, costs and economic behaviour — not to manufacture a winning backtest.
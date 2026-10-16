# Backtest Badger — Stage 4B.2A: Historical Continuous-Holding Replay Engine

Act as a senior quantitative software engineer specialising in causal backtesting, exact financial accounting, reproducible market-data evidence and scientific research integrity.

Implement **only Stage 4B.2A: a deterministic, offline historical replay engine with synthetic tests**. We will separately review and approve the runner before Stage 4B.2B is permitted to inspect the actual 2024 validation predictions, execute the full real historical backtest or report economic performance.

**Principle: Minimum complexity. Maximum correctness.** Do not optimise the strategy, disguise historical execution references as prospective quotes, or alter any frozen research evidence.

## 1. Confirm repository state and inspect before writing

Repository: `owencrew/backtest-badger`. Expected reference HEAD when this prompt was prepared: `8e094f94e4c831d62690d9487b2f85dbbaeeae9a` (`fix(paper): enforce valuation quote timing and snapshot integrity`). Inspect and report the *actual* checkout commit; do not reset or overwrite newer changes merely to match this SHA.

Read:

- `AGENTS.md` and `prompts/README.md`.
- `docs/architecture.md`, `docs/roadmap.md`, `docs/development-handoff.md`.
- **Approved** `docs/stage-04a-paper-trading-spec.md`, especially Sections 3–4, 5, 7, 8 and 9, and its acceptance criteria.
- **Approved** `docs/stage-04a-prospective-evaluation-protocol.md`, especially the historical-reference/evidence distinctions.
- `docs/stage-04b1-deterministic-paper-primitives.md`, including the valuation timing correction.
- `docs/stage-02b-predictive-baselines.md`, `docs/stage-02c-execution-backtesting.md` and `docs/stage-02d-economic-diagnostics.md`.
- `src/backtest_badger/paper_types.py`, `paper_strategy.py`, `paper_execution.py`, `paper_accounting.py` and `tests/test_paper_primitives.py`.
- `src/backtest_badger/forecast_data.py`, `execution_data.py`, `backtest.py`, and relevant source-validation and synthetic-test conventions.

Before implementing, briefly identify the exact existing API functions to reuse and any incompatibilities between the historical and prospective evidence models. Preserve existing Stage 2C/2D and Stage 3 implementations unchanged.

## 2. Objective and non-objectives

Implement a **pure, deterministic historical replay calculation** taking already supplied historical Ridge forecasts and native hourly opening-reference prices as *in-memory inputs*. It should reproduce a continuous-holding 0%/100% long/cash account with independent 10,000-USDT starting capital for each market.

This stage is the **simulation mechanics and synthetic-test gate**, not the real 2024 economic evaluation. Implement callable functions, not a command that automatically runs the actual historical dataset. Do not open real `artifacts/experiments/stage-2b-v1/`, `artifacts/execution/binance-1h-2024-v1/`, actual Stage 2C/2D outputs or any historical holdout during this task. You may read their documentation and source-code loader contracts. Do not open genuine Stage 3 forecast, outcome or operations artifacts.

There is no database, network, broker, scheduler, AWS, website, production, migration or genuine-market-data acquisition work in 4B.2A.

## 3. Historical evidence is not prospective evidence

- The historical adapter uses pre-existing, frozen **2024 validation** forecast identities and independent **native hourly opening-price** identities.
- The prospective Stage 4 `Forecast` requires real automated issuance provenance and `Quote` requires actual REST request/receipt evidence. **Do not fabricate, repurpose or monkeypatch those records, timestamps, automation hashes, quote responses, `run_id`s, market depth or exchange filters to make historical data pass a prospective validator.**
- Reuse `paper_strategy.evaluate_strategy()` directly for Ridge Sign v1 (`prediction > Decimal('1e-12')`), and the existing exact `paper_accounting` financial primitives wherever they apply: `fund_account`, `calculate_trade`, `apply_trade`, `reconcile`, `replay`, `affordable_quantity`, and the existing fee calculation.
- Historical source validation/timing and historical mark-to-price evidence may need a **small separate typed adapter**. Avoid duplicating the financial ledger, replacing prospective invariants or modifying `paper_strategy.observe_forecast()` to accept unauthenticated evidence.
- If clean reuse of a purely financial valuation calculation warrants extracting a tiny shared helper, do so only with explicit preserved-prospective tests. Otherwise compute the simple historical cash-plus-units-times-reference mark using the same Decimal context, with exact reconciliation tests and no claim that `paper_accounting.value_account()` accepted a genuine prospective `Mark`.
- A small, explicit historical position/exit transition model is acceptable because historical availability and execution differ; explain which rules are genuinely shared versus independently adapted. Do not falsely assert full live-execution or outage parity.

## 4. Frozen baseline historical timing policy

Use the already specified **2024 validation period**: `[2024-01-01T00:00:00Z, 2025-01-01T00:00:00Z)`. For the future full experiment, the original pinned forecast grid has 2,195 four-hour source horizons per market; it begins with the source opening on 2023-12-31 20:00 whose signal becomes available on 2024-01-01 00:01, and its last eligible historical forecast is available on 2024-12-31 16:01. Preserve this original identity grid; do not retrain or regenerate forecasts.

For each valid synthetic historical Ridge signal:

1. Its source opening must be an exact UTC four-hour boundary, and its `feature_available_at` must equal source opening + four hours + 60 seconds. This is an **historical feature-availability assumption**, not a claim the archived forecast was genuinely published in 2024.
2. Determine desired target exposure solely from the forecast using the existing Ridge evaluator. The signal never sees a price or target label.
3. The **earliest hypothetical trade reference** is the first native 1h opening strictly after feature availability. Example: available 12:01 → permitted reference 13:00, **never 12:00**. Execution at a historical reference is hypothetical, not a literal order placed on an exchange.
4. If flat and target is long, buy using that permitted reference. If long and target remains long, HOLD without a sell/rebuy. If long and target becomes cash, sell at its next permitted reference. If flat and target is cash, CASH_NOOP. No default forced exit three hours after purchase.
5. There may be **one actual position transition per four-hour signal**, absent a separately declared missing-data/risk rule. Preserve prior exposure during intervening hourly marks.
6. A trade or valuation cannot use an unavailable, future, mismatched, invalid or substituted hourly price. Never choose a later price for an earlier scheduled trade because it looks favourable.
7. Historical signal completeness is **an input-integrity requirement** for the eventual full 2024 experiment. If a required forecast or hourly opening reference is absent/corrupt, fail clearly or retain a clearly unavailable synthetic result; do not silently impute or skip losing opportunities. Stage 4B.2B must require the pinned full grid before publishing completed results.
8. In tests with deliberately missing signal horizons, distinguish a missing signal from a negative forecast, and test the same logical *two consecutive misses → risk-off exit* principle using the actual synthetic discovery/processing point. Do not create synthetic Stage 3 automation evidence or claim to test the prospective network-recovery worker.

Define deterministic order when a hypothetical trade and an hourly valuation share a reference timestamp: **process the eligible trade first, then mark the resulting ledger prefix** using the same archived hourly opening reference. Clearly label this as a historical reporting convention, not a claim about intrasecond quote order.

## 5. Fixed historical baseline cost and sizing policy

Implement the **base scenario only** in 4B.2A:

- 10 bps **USDT fee per side**, rounded up to `0.00000001` USDT using existing Stage 4B.1 accounting functions.
- **Hypothetical 1 bp half-spread** per side relative to the archived hourly opening reference.
- **Hypothetical 2 bps adverse slippage** per side.
- Thus, with reference price `P`, hypothetical buy execution price = `P × (1 + 0.0001 + 0.0002)` and sell execution price = `P × (1 − 0.0001 − 0.0002)`. The reference is **not a historical observed bid or ask**.
- Full available-cash purchase (after exact fee and step rounding), and full held-quantity sale, subject to the deliberately **synthetic** sizing assumption. Default proposal for this historical research adapter: `Decimal('0.000001')` base-asset quantity step for both markets, clearly labelled as a hypothetical research convention, *not* asserted Binance filters. Make this explicit/versioned in a pure configuration record rather than hiding it in the code.
- Do not invent historical top-of-book depth, `exchangeInfo` filter snapshots, provider timestamps or real fillability. Record them as **not evidenced/untested**; a mathematical fill is contingent on these simplified assumptions. Do not call `paper_execution.simulate_order()` using invented REST evidence.
- Reject buys that cannot fund both notional and rounded fee, invalid or off-step sales, zero/negative prices/quantities, negative cash/base and nonfinite Decimal inputs.
- Preserve full balances, weighted-average acquisition basis, realised/unrealised P&L, and exact ledger-posting reconciliation using existing accounting primitives.

**Scenario caveat:** Stage 2C's frozen comparators are `frictionless` (0/0/0), `base` (10/1/2) and `stress` (10/3/10), expressed as (fee/half-spread/slippage) bps. The new Stage 4B.1 accounting functions intentionally enforce the 10-bps fee policy. Therefore **do not fake a zero-fee or alternative-fee account by changing the historical reference price while still charging Stage 4B.1 fees.** B.2A implements only the correctly shared base case. Record in the draft historical protocol that genuinely separate cost scenarios are a future, separately reviewed B.2B extension if approved. Do not modify the approved prospective fee policy to make those alternatives work now.

## 6. Account inception, marks and year-end

- Independently fund BTCUSDT and ETHUSDT at `2024-01-01 00:00 UTC` with exactly 10,000 USDT each; these are research accounts, **not** the prospective paper-trading portfolios.
- Retain historical valuation observations with explicit market, hour, original hourly price evidence identity, reference price, resulting account `ledger_seq`, and base/cash/basis/P&L snapshot. Never claim these are Stage 4 `MARK_OBSERVED` REST bid/ask events.
- Define historical marked equity = `cash + quantity × archived opening-reference price` and unrealised P&L = `quantity × reference price − cost_basis`. These are **reference-price marks**, not liquidation-at-bid marks. Reconcile realised + unrealised = equity − 10,000 for each valid mark.
- A deterministic 1h observation grid is preferable for the synthetic runner, with optional smaller fixture horizons. The intended eventual reporting start is 2024-01-01 00:00 and final available 2024 reference is **2024-12-31 23:00 UTC**; no 2025-01-01 00:00 price is invented. The initial funding point is explicitly 10,000 USDT.
- **Do not force-liquidate an open position at year-end.** Report marked holdings/equity and, only if separately modelled under explicit hypothetical exit costs and valid evidence, a distinct counterfactual net liquidation figure. Do not use a hypothetical future liquidation as an actual ledger sale.
- Missing/invalid historical references must produce an explicit failure or gap, never forward-filled observed equity or an economically convenient execution.

## 7. Module/API layout and validation boundaries

Prefer one focused module such as `src/backtest_badger/paper_historical.py` with frozen, simple historical evidence/result dataclasses if useful, plus `tests/test_paper_historical.py`.

Implement a clearly named **offline pure entry point** accepting already validated/in-memory or explicitly passed synthetic forecast/reference collections; it must not autonomously discover artifact directories, access the network or execute a real backtest. A separate future Stage 4B.2B adapter may invoke the existing **read-only** pinned loaders `forecast_data.load_forecasts()` and `execution_data.load_execution_data()` after approval. Do not duplicate those full immutable-artifact loaders.

Make the result data sufficient for independent future verification: ordered decisions, hypothetical orders/trades, original historical reference identities, paired financial movements, hourly marks with ledger-prefix identity, rejected/missing evidence status, and summary-ready totals. Keep source evidence and calculated economic results conceptually separate. All outputs should be deterministic, serialisable and explicitly labelled `historical_simulation` rather than `prospective_paper_trade`.

Do not introduce a framework, a new database schema, a new CLI command, dependency changes or large refactors. If a minor existing-function change is unavoidable, explain and regressively test its unchanged prospective behaviour.

## 8. Synthetic tests and acceptance criteria

Use fabricated in-memory synthetic 2024 UTC forecast values and hourly prices only. Cover at least:

1. Ridge values below/equal/above the strict `1e-12` threshold; reject invalid numerical inputs.
2. Native four-hour source-grid and +60-second availability; 12:01 → 13:00, never 12:00; midnight, UTC day/month/year boundaries.
3. Decision cannot access an hourly reference or outcome not yet available at the decision time.
4. Consecutive positives produce one buy followed by HOLDs, not repeated transactions; a negative sells once; subsequent negatives remain flat.
5. Positive after a genuine completed exit requires a new signal; no reuse of an old signal or invented past decision.
6. Two missed synthetic horizons versus one missed horizon, missed-signal reset and risk-off; no historical extrapolation of genuine Stage 3 outage/quote recovery behaviour.
7. 10/1/2-bps historical pricing, exact 10-bps fee quantum, affordable quantity flooring and explicit synthetic quantity-step settings.
8. Reference price versus presumed bid/ask distinction; no invented raw bookTicker bodies, network timings, live market depth or exchange filters.
9. Independent BTC and ETH accounts, 10,000-USDT funding once, no shared balances or duplicate trades.
10. Full buy, HOLD, full sell, multiple eligible cycles and no negative balances.
11. Paired signed USDT/base ledger movements and exact realised/unrealised/total equity reconciliation; deterministic replay.
12. Hourly mark source identity, deterministic trade-before-mark ordering, correct ledger prefix and a historical mark unchanged by later trades.
13. Missing, duplicate, out-of-order, off-grid, future, zero, NaN or market-mismatched forecast/reference inputs fail closed without backfilling.
14. Open holding at end of fixture remains open; last known mark is not a fabricated sale.
15. Determinism under a changed caller Decimal context and re-execution with identical inputs; explain permitted non-relevant input ordering versus causal reordering.
16. An explicit comparison test that the shared Ridge evaluator and accounting arithmetic yield the same values independently of historical orchestration, without claiming historical/prospective execution-price parity.
17. Existing Stage 4B.1 synthetic tests still pass unchanged; all protected Stage 2–3 implementation files remain unchanged.

Tests must not open real research artifacts, connect to PostgreSQL or Binance, or access the existing holdout. If a deterministic source-artifact loader integration would require opening real pinned files, **defer that to 4B.2B**. Remote CI need not be configured or run.

## 9. Draft the historical evaluation protocol, but do not execute it

Create `docs/stage-04b2-historical-validation-protocol-DRAFT.md` documenting, **before anyone views this new continuous-holding result**:

- Historical data boundaries and exact approved Stage 2B/independent 1h input identities/hashes **as declared in existing code/docs**, without reopening actual research artifacts yet.
- Entry/exit times, continuous holdings, missing-input policy, trade-before-mark ordering, BTC/ETH separation and end-of-2024 open positions.
- Reference-price execution assumptions and their limits relative to prospective bid/ask; fixed 10/1/2-bps baseline and hypothetical step.
- That stress/frictionless cost scenarios require a separately approved, economically consistent implementation, rather than silently altering the current 10-bps fee contract.
- Planned historical account reconciliation, turnover, exposure, transaction costs, equity, realised/unrealised P&L, observed-mark drawdown, daily/monthly reporting conventions and potential cash/buy-and-hold context.
- Exact immutable output/artifact manifest intentions for later Stage 4B.2B, with inputs, code/policy hashes, market/time provenance and exclusive no-overwrite publication.
- Scientific limitations: no claim of observed execution liquidity, order-price parity, genuine 2024 forward publication, independently tested alpha, or untouched 2025–2026 holdout performance.
- Fixed acceptance tests required before B.2B may access actual pinned input artifacts.

Mark this document **DRAFT / NOT YET APPROVED FOR 2024 EXECUTION**. Do not modify or imply reapproval of the two frozen Stage 4A documents.

## 10. Documentation and prompt archiving

Create/update only the appropriate narrowly scoped items:

- `src/backtest_badger/paper_historical.py` (or justified similarly scoped module).
- `tests/test_paper_historical.py`.
- `docs/stage-04b2-historical-validation-protocol-DRAFT.md`.
- `docs/stage-04b2a-historical-replay-engine.md` containing exact API, synthetic test evidence, scientific limitations and how B.2B will call the already pinned loaders **after separate approval**.
- Minimal `docs/architecture.md`, `docs/roadmap.md` and `docs/development-handoff.md` status updates if warranted; preserve the existing approved-spec links and production-state warnings.

Archive **this exact substantive prompt**, after reviewing it for secrets, at:

`prompts/stage-04-paper/003-historical-continuous-holding-replay-engine.md`

Do not overwrite prompts 001–002, reword the archived copy or add full Codex conversation logs.

## 11. Verification

Run relevant synthetic and existing tests and report exact outcomes:

```sh
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked ruff check .
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked ruff format --check .
env -u BADGER_TEST_ADMIN_DSN UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked pytest -q
git diff --check
```

If the environment needs the existing offline uv-cache workaround, use `--offline` and report it. PostgreSQL fixtures may skip without an explicitly configured isolated test server; do not point tests at production or fetch credentials. Do not imply a passing test if it was not actually run.

Check preservation of approved Stage 4A protocols, source hashes, immutable Stage 2–3 modules and existing research artifacts. You must not read genuine Stage 3 outcomes or the 2025–2026 holdout for preservation checks. Report source-file and artifact metadata limitations accurately.

## 12. Strict boundaries

**Do not**:

- Run the full actual 2024 backtest or view the new continuous-holding economic performance.
- Open real 2024 forecast/hourly artifacts or real Stage 2C/2D output datasets during this synthetic-only stage.
- Inspect, score, train on or otherwise access 2025–2026 test/holdout labels.
- Modify the Ridge threshold, predictive model recipe, original data or frozen Stage 2C/2D results.
- Fabricate Stage 3 forward records, exchange-side timestamps, original REST quotes, fills or prospective evidence.
- Implement market-data collection, paper-trading workers, PostgreSQL migrations, actual orders, AWS services, APIs or the website.
- Commit, push, merge, deploy, edit production environments, enable timers or start 4B.2B.

If an approved specification is ambiguous or inconsistent with the historical mechanics, document the precise issue and your conservative choice. Do not silently change frozen protocols.

## 13. Completion report and stop condition

Report:

1. Checkout commit, inspected contracts and files created/modified.
2. Exact historical eligibility/reference-price/continuous-holding rule and source-versus-execution evidence distinction.
3. Which original Stage 4B.1 pure functions are reused and where historical-specific mechanics necessarily differ.
4. Synthetic sizing, spread/slippage/fee handling and any intentionally unsupported historical constraints.
5. Ledger/valuation reconciliation tests and deterministic replay evidence.
6. Full pytest/Ruff/format/whitespace results and skips, with actual executed commands.
7. Verified preservation of existing code/protocol/evidence, with limitations.
8. Draft historical protocol contents and remaining approval choices for 4B.2B, including scenario fee-policy limitations.
9. Exact prompt archive path and unresolved issues.

**Stop after Stage 4B.2A. Do not run real 2024 performance, commit, push or proceed to Stage 4B.2B without a separate instruction.**

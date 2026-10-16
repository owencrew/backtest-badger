# Backtest Badger — Stage 4B.1: Deterministic Paper-Trading Primitives

Act as a senior Python data engineer and quantitative software engineer. Implement **only Stage 4B.1**, a small, deterministic, **pure-Python** foundation for future paper trading. Use the approved Stage 4A technical specification and prospective evaluation protocol as the authority for behaviour.

This is the first implementation milestone following Stage 4A approval. Its purpose is to prove the strategy state transitions, simulated fill arithmetic and portfolio accounting **with synthetic inputs**. It is not permission to connect the engine to real predictions, Binance, PostgreSQL, the Lightsail server or a scheduler.

**Working baseline:** `owencrew/backtest-badger`, `main` as inspected at task start (the Stage 4A approval follow-up was commit `0c9766a5be54d38692eebe9f299462adc3361f7f`). Verify the actual current HEAD before changing files; do not assume it has not advanced.

## 1. Inspect first, then implement

Read, in this order:

- `AGENTS.md`, `README.md`, `docs/development-handoff.md`, `docs/architecture.md`, `docs/roadmap.md`.
- **Approved** `docs/stage-04a-paper-trading-spec.md` and `docs/stage-04a-prospective-evaluation-protocol.md` in full. Their approved requirements take precedence over this prompt if you identify a discrepancy; report the discrepancy rather than silently reinterpreting the documents.
- `docs/stage-02c-execution-backtesting.md`, `docs/stage-02d-economic-diagnostics.md`, `docs/stage-03a-forward-predictions.md`, `docs/stage-03b-automated-forward-collection.md`, and `docs/stage-03c-forward-evaluation-protocol.md`.
- Relevant source and tests: `backtest.py`, `forecast_data.py`, `forward.py`, `forward_operations.py`, `forward_evaluation.py`, `tests/test_backtest.py`, `tests/test_forward.py`, and existing synthetic test conventions.
- `prompts/README.md` and representative archived prompts such as `prompts/stage-03-forward/004-automated-outcome-scoring.md` and `prompts/stage-02-research/004-economic-diagnostics.md`.

Briefly identify functions and accounting patterns that can be reused **without modifying or breaking frozen Stage 2/3 behaviour**. Do not transplant `backtest.simulate_account()` unchanged: its historical, always-flat three-hour round trips are a different strategy.

## 2. Scope and implementation structure

Implement a small set of new functions and immutable value objects for:

1. **Versioned strategy evaluation and pure state transitions** (initial `ridge_sign` v1, future policies possible without changing the execution engine).
2. **Simulated order/quote validation and one-shot all-or-nothing execution calculations** from caller-supplied evidence.
3. **Deterministic account accounting, paired proposed monetary postings, weighted-average cost basis, reconciliation and valuation**.

Prefer plain functions and frozen dataclasses in a small number of new `src/backtest_badger/` modules (for example `paper_strategy.py`, `paper_execution.py`, `paper_accounting.py`), or an even simpler clearly justified layout. Avoid an abstract strategy framework, service/repository layer, event bus, mutable global state, unnecessary classes, dependencies or overgeneralisation.

**No new database objects, migrations, network clients, REST calls, filesystem artifact readers/writers, CLI commands, scheduling, production config or website code.** The function inputs must be explicit, so tests require no `.env`, provider, database or current live clock. Use injected aware UTC timestamps for deterministic tests; do not allow arbitrary clock overrides in a future live command as a side effect of this stage.

## 3. Strategy and missing-signal rules

- Initial market identities: Binance Spot BTCUSDT and ETHUSDT, independent 10,000-USDT hypothetical portfolios; no leverage, shorts, borrowing, external funding or pooled capital.
- Ridge Sign v1: read a caller-supplied, already-verified Ridge predicted **four-hour log return** as an exact finite `Decimal`. Target long (1) only when prediction `> Decimal('1e-12')`; equality, zero and negative mean cash (0). Do not refit models or inspect forecast outcome labels. Do not silently coerce malformed floats, NaN or infinities into valid forecasts.
- The initial historical/forward reader owns validation of actual source JSON and Stage 3B automation attribution. Stage 4B.1 should model the **necessary eligibility/provenance fields in its input contract**, and validate logical time order and policy boundaries, without reaching into original JSON artifacts or implementing a second competing Stage 3 verifier.
- The original native four-hour close grid, +60-second feature availability, and **exclusive** +16-minute automated issuance/entry deadline must be represented correctly. No prospective new buy from a late, unattributed, stale or missing forecast. A source horizon is considered missed only **when observed after its promptness deadline**, not retrospectively at the deadline.
- A repeated positive forecast while already long produces a recorded conceptual HOLD, not another buy. A negative forecast when long creates one sticky `EXIT_REQUIRED` obligation; negative when flat yields a cash no-op.
- Missing forecast is **unknown**, not a negative forecast. One consecutive missed horizon preserves current position and records stale exposure; **two consecutive misses** create a current-time risk-off exit obligation if long. The streak resets on a qualifying eligible forecast. Consecutive missed horizons discovered after a downtime must be represented with actual discovery time; no backdated decisions.
- While a sticky exit remains outstanding, ignore later positive signals for trading. An order expiry or failed quote does **not** satisfy or cancel the obligation. Once holdings genuinely reach zero and exit satisfaction is recorded in the **pure state transition**, a buy requires a **new qualifying forecast issued after satisfaction**; do not reactivate an old signal.
- Define a small explicit state-transition representation that can later be persisted in Stage 4C. Pure transitions must reject illegal jumps, conflicting portfolio/market identities, duplicate decision identities and obvious time reversals. Do not invent persistence or true concurrent locking in this stage.

## 4. Orders, quote evidence and all-or-nothing simulated fills

The engine does not place real orders. It receives a pre-submitted **internal** order intent and a separately supplied prospective bid/ask observation. Model the following temporal invariants:

`decision_at <= order.submitted_at <= quote.request_started_at <= quote.response_received_at <= fill_at < order.expires_at`.

For new buys, the decision and modelled fill must also occur within the originating forecast's valid window. For sticky exit retries, the current order still has its own 30-second validity, but the original exit obligation survives beyond its initiating signal window. Quote observations from before submission, from an earlier worker run, or after expiry are not usable for a new fill.

**Frozen initial defaults:**

- 30-second individual order expiry.
- Maximum request-to-receipt interval 2 seconds; maximum response-to-fill processing interval 1 second; reject sampled UTC clock reversal. The first limit measures local round-trip time; it is not an exchange-side quote-age guarantee.
- Buyer uses observed ask; seller uses observed bid. **Buy simulated price** `ask * (1 + 0.0002)`; **sell simulated price** `bid * (1 - 0.0002)`.
- **Fee:** 10 bps each side, charged in USDT and rounded **up** to 0.00000001 USDT per fill. Do not double-count the spread with an extra assumed historical half-spread.
- Require finite positive bid/ask with `ask >= bid`; valid nonnegative displayed best-level quantities; exact correct market, symbol, and validated evidence timestamps.
- Model effective market lot-step, minimum/maximum quantity and applicable notional filters as caller-supplied, explicitly versioned filter evidence. Reject unsupported, inconsistent or more-than-one-hour-old filter evidence. Do not fetch `exchangeInfo` yet.
- **All-or-nothing:** calculate the full affordable quantity for a buy, rounding **down** to the applicable step and checking cash *after fee rounding*. A sale uses the required owned quantity under the allowed step. Reject invalid size, insufficient cash/base, ineligible notional and insufficient relevant best-level displayed liquidity. Do not partially fill, silently shrink a target because depth is insufficient, use opposite-side liquidity or pretend the REST price guarantees an executable market order.
- A rejected/expired/failed attempt yields a typed outcome and **zero proposed financial postings**. An eligible modelled fill yields explicit immutable-style evidence suitable for Stage 4C and exactly two proposed signed financial movements (USDT and the portfolio base asset).
- Treat a repeated processed order/fill identity as an error or idempotent no-op **only when the caller supplies an explicit existing-result context**. Demonstrate deterministic replay/duplicate detection with a pure in-memory sequence; database uniqueness and crash consistency belong to Stage 4C.

## 5. Financial accounting — exact rules

Use `Decimal` for **all** prices, quantities, balances, notional, fees, cost basis and P&L, with consistent explicit precision and rounding. Follow the approved equations:

- **Buy:** `N = q * P_exec`; `fee = ceil_to_quantum(N * 0.001, 1e-8 USDT)`; cash delta `-(N + fee)`; base delta `+q`; acquisition cost basis increases by `N + fee`.
- **Sell:** `N = q * P_exec`; fee as above; cash delta `N - fee`; base delta `-q`; realised P&L increment `N - fee - q * (cost_basis_before / units_before)`; remaining cost basis reduces by allocated weighted-average basis. On full liquidation units and remaining basis become exactly zero without hiding unexplained losses.
- Independent accounts begin with exactly 10,000 USDT cash and zero asset units; represent once-only initial funding in the pure state model without implementing the future DB ledger.
- The accounting primitive should correctly process **partial sales** even though the v1 strategy normally requests full liquidation. This is needed for general accounting correctness and future extensions.
- Reject negative cash/asset balances, sale of unowned quantity, invalid signs or market mismatch. Reject a fill applied twice. A fill cannot result in only one proposed posting.
- The returned state must reconcile cash, asset quantity, cost basis, cumulative realised P&L, fees and mark-to-market equity. For a supplied valid bid mark, `equity = cash + qty * bid`, `unrealised = qty * bid - remaining_basis`, and `realised + unrealised = equity - 10000` under the no-extra-funding convention.
- Provide a separate **modelled net-liquidation estimate** only when an all-or-nothing eligible liquidation is well-defined; its hypothetical fees/slippage must not be deducted from ordinary marked equity. If mark evidence is missing/invalid, mark is unavailable, not filled forward or fabricated.
- Valuation functions take a caller-supplied immutable-style mark with **actual time, price evidence, valuation-policy fingerprint and `asof_ledger_seq`**, and explicit already-replayed account state at that sequence. Demonstrate that replaying the same mark/ledger prefix yields identical historical equity after later hypothetical trades. No quote download or standalone valuation storage here.

## 6. Synthetic tests and worked examples

Create focused unit tests in the existing style. At minimum test:

1. Ridge threshold strictly greater than `1e-12`, equality, negative, invalid numerical inputs, independent BTC/ETH state.
2. Consecutive positive HOLD, long-to-exit on negative, negative while cash, sticky exit suppressing later positive, fresh-only re-entry after satisfaction.
3. One missed horizon vs two, reset on qualifying forecast, missed horizons discovered after downtime without fabricated historical timestamps.
4. All exact 4h UTC boundary rules, +60-second eligibility and **exclusive** +16-minute deadline, current-time decision ordering.
5. Pre-submission quotes, request/receipt/fill ordering, 2s and 1s edges, 30s exclusive expiry, invalid/reversed/non-UTC timestamps and attempted quote reuse.
6. Quote validity (bid/ask, symbols, sizes), actual observed spread not charged twice, buy/sell 2bps adverse pricing and 10bps per-side fees.
7. Market quantity step, rounding down, minimum and maximum notional/quantity, 1-hour filter evidence limit, no partial fill, insufficient displayed liquidity/cash/base and dust exit refusal.
8. Fee rounded **up** to 1e-8 USDT and an affordability boundary where fee rounding would otherwise overdraw cash.
9. Paired USDT/base postings, exact money conservation, multiple buys/weighted-average basis, partial sale, full liquidation, repeated fill rejection and rejected order making no financial changes.
10. Hand-calculated example from Stage 4A specification (buy 10 units at reference ask 100, sell 4 at bid 110; exact fees, basis, P&L and equity), plus flat-price fee loss.
11. Deterministic replay with identical chronologically ordered synthetic events; reject duplicate/reordered events and show no cross-account spending.
12. Valuation using exact stored bid and account high-water, reproducible after subsequent trades, missing mark as unavailable, and separate hypothetical net liquidation.

Use synthetic input evidence only. Do not access Binance, live forecasts, genuine scored outcomes, historical holdout labels, production infrastructure or any non-test database.

## 7. Preserve existing implementation and scientific evidence

Do **not** edit the existing frozen ML, forecast or scoring modules merely for code reuse: `forward.py`, `forward_operations.py`, `forward_evaluation.py`, `forward_scoring_operations.py`, `features.py`, `evaluation.py`, `model_data.py`, `forecast_data.py`, `backtest.py`, and the existing `cli.py` unless an unexpected, essential issue is separately explained and approved **before** modification.

Do not alter `docs/stage-04a-paper-trading-spec.md`, `docs/stage-04a-prospective-evaluation-protocol.md` or the Stage 3C frozen protocol; no experiment parameter changes. Do not create, rewrite or delete any `artifacts/` historical or forward evidence. No third-party dependency, new CLI entry point, schema migration, new scheduler, real-money order access or Docker change.

Respect the existing `AGENTS.md`, Ruff, pytest, type and naming conventions. Avoid creating a general purpose strategy plugin infrastructure or significant refactoring outside the new modules.

## 8. Run validation and document exact results

Run from the repository root, as feasible:

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
git diff --check
```

If integration tests need an isolated PostgreSQL server, they may skip as designed. **Do not configure one against the application or production database** just to increase passed-test counts. Report exact passed/skipped/failed tests and any unavailable commands; do not claim CI passed unless observed.

If you implement a pure replay helper, test the same input sequence twice and compare all resulting canonical monetary values and transitions. Include tests for malformed payloads and invariant failures, not only success cases. Prefer strict failures to silent corrections.

## 9. Documentation and prompt archive

Create a concise implementation guide:

`docs/stage-04b1-deterministic-paper-primitives.md`

Explain the pure-function API, contracts, cost/rounding policy, state transitions, test limitations, and what remains for Stage 4B.2, Stage 4C and Stage 4D. Update `docs/architecture.md`, `docs/roadmap.md` and `docs/development-handoff.md` **only as needed** to reflect what was actually implemented and tested. Preserve the approved Stage 4A texts.

**Archive this exact substantive Codex prompt verbatim** (rather than a summary or a response transcript) at:

`prompts/stage-04-paper/001-deterministic-paper-trading-primitives.md`

Follow `prompts/README.md` conventions. Review the archived text for secrets and sensitive values. The prompt file is documentation of the implementation instruction, not a substitute for the approved Stage 4A specification.

## 10. Explicit exclusions and stop condition

**Do not** implement Stage 4B.2 historical replay, access 2024 validation artifacts for economic results, tune strategy thresholds, inspect test-holdout outcomes, implement database persistence/Alembic migrations, connect forward-prediction artifact readers, implement a live quote adapter or real-time collector, run portfolio workers, create an API, deploy, change backups or touch production systems.

Do not commit, push, open or merge a PR, activate a worker or deploy without an explicit subsequent instruction. Changes should remain reviewable locally/in your Codex workspace until authorised.

## 11. Completion report

Report, concisely but concretely:

1. Files created/modified and why; note every deviation from the proposed module layout.
2. Exact public pure-function/data contracts and any deliberate limitations.
3. Strategy/missing-signal/sticky-exit behaviour proved by tests.
4. Quote/ordering/filter/fee/rounding rules and accounting/reconciliation invariants.
5. The hand-calculated numerical example compared to actual test results.
6. Test/lint/format/whitespace commands run, including pass/fail/skip counts.
7. Verification that existing fixed forecast/outcome evidence and frozen Stage 4A docs are unchanged.
8. Any unresolved ambiguity or engineering risk, especially one affecting Stage 4C's eventual atomic database constraints.
9. The smallest proposed follow-on task, **Stage 4B.2 historical continuous-holding validation**; do not start it.

**Stop after Stage 4B.1 and present your work for review.**

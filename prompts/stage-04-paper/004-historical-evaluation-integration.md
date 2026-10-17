Backtest Badger — Stage 4B.2B: Historical Evaluation Integration and Synthetic Publication

Act as a senior quantitative researcher and Python data engineer. Implement Stage 4B.2B — the offline integration, benchmark, reporting and immutable-publication layer for historical continuous-holding evaluation, but do not run the real 2024 experiment.

Principle: minimum complexity, maximum scientific correctness. This is a bounded engineering task. Stage 4B.2A's pure replay engine has been reviewed and approved. Its historical evaluation protocol is now approved and frozen in docs/stage-04b2-historical-validation-protocol.md, version historical-validation-v1.

This prompt permits synthetic end-to-end fixtures only. It does NOT authorise opening, hashing, loading, analysing, replaying or publishing any genuine 2024 artifact or economic result. An explicit owner-approved subsequent real-run gate is mandatory.

A separate, future one-minute historical execution scenario has been proposed to test near-immediate signal response. It is not approved for implementation or data acquisition in this task, and the approved hourly baseline must remain unchanged.

1. Inspect and verify the repository first

Repository: ~/Code/backtest-badger (owencrew/backtest-badger). The documentation baseline immediately before this task is commit f1df2ecaa426957a09d3577125d1095a2d5dc69b. Inspect the actual checkout HEAD, status and parent history; do not assume GitHub and the local worktree are identical, reset/rebase or overwrite local work automatically. Report any discrepancy.

Read AGENTS.md, prompts/README.md, README, docs/architecture.md, docs/roadmap.md, docs/development-handoff.md, and especially:

docs/stage-04a-paper-trading-spec.md and docs/stage-04a-prospective-evaluation-protocol.md — approved prospective rules; unchanged.

docs/stage-04b2-historical-validation-protocol.md — the frozen, authoritative historical protocol. The old -DRAFT.md filename was retired; do not consult or restore the obsolete draft as authority.

docs/stage-04b2a-historical-replay-engine.md and docs/stage-04b1-deterministic-paper-primitives.md.

docs/stage-02b-predictive-baselines.md, docs/stage-02c-execution-backtesting.md, and docs/stage-02d-economic-diagnostics.md for fixed source schemas and scientific limitations.

Inspect existing src/backtest_badger/paper_historical.py, paper_types.py, paper_strategy.py, paper_execution.py, paper_accounting.py, forecast_data.py, execution_data.py, evaluation.py, ingestion.py, and relevant existing deterministic artifact/publication conventions and tests.

Inspect code/documentation only. Do not open files under the real artifacts/ tree (including manifests), do not ask existing loaders to read them, and do not inspect withheld labels or Stage 3 artifacts.

Compute and retain the SHA-256 of the current frozen protocol file bytes and its Git revision for use in synthetic publication tests and the future run manifest. Do not insert the protocol's hash into that file.

2. Scope and module design

Build the smallest offline composition layer around paper_historical.replay_historical(...), preferably one narrow module such as src/backtest_badger/paper_historical_evaluation.py with a second publication module only if separation materially improves clarity.

Implement straightforward, testable functions with injected in-memory inputs or fake loader results for:

Validating a complete, pinned, two-market historical input bundle and mapping the existing loader-return schemas into HistoricalForecast and HourlyReference records.

Running the approved base-cost Ridge simulation only on supplied synthetic data.

Building constant-cash and independently funded buy-and-hold analytical accounts using shared Stage 4B.1 financial primitives.

Producing fixed descriptive summaries, exact per-event ledger evidence, hourly marks, daily/monthly observations and scientifically qualified comparisons.

Publishing those structured outputs exclusively to a supplied synthetic temporary destination, verifying deterministic reproduction and manifest-last/no-overwrite semantics.

The integration layer should be ready to use genuine already verified loader outputs in a later, separately approved run.

Do not wire or expose an executable CLI/entrypoint that can read actual artifact paths or invoke the real data loaders in this stage. An explicit subsequent real-run wrapper/authorisation is still required. No package installation, new dependency, scheduler or database is needed.

Future execution-frequency compatibility (design only)

A separately versioned one-minute historical reference/execution scenario may follow this work, with trades close to signal availability rather than at the next hourly opening.

Keep performance summaries, benchmark accounting and deterministic publication reasonably separable from the hourly input adapter and next-hour execution policy where this follows naturally from the existing code.

Prefer small clear functions to a new generic backtesting framework.

Do not add frequency switches, additional input schemas, one-minute execution scheduling, or placeholder integrations now.

If a calculation or file format intrinsically assumes hourly data, preserve the approved hourly contract and document that assumption precisely.

3. Strict source-adapter contract

Prefer reuse of the unchanged forecast_data.load_forecasts() and execution_data.load_execution_data() return types, but do not call these on genuine files now. Use mocked/injected exact-shape results and synthetic records. Do not rewrite either loader, duplicate their original research validation or access model_data.load_model_data().

At the adapter boundary, validate and retain the frozen protocol's declarations:

Stage 2B validation predictions: e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674.

Stage 2B manifest / manifest-anchored Ridge recipe identity: af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581.

Stage 2C hourly openings CSV: 39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a.

Stage 2C hourly manifest: 1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d.

Stage 2C acquisition manifest: 926697a89eb7c018ca5913f1e3c4c1170715db5639d444a58a78012e92aec055.

For the future actual loader integration, forecast_data.load_forecasts() returns (hashes, accounts) with (market, model) signals; select exactly the ridge model for each market.

execution_data.load_execution_data() returns (metadata, hourly_price_mapping); verify its manifest and output hashes against all reviewed pins (not just the hourly loader's internal self-consistency).

Retain 24 distinct monthly source ZIP/checksum identities, source hashes, origins and retrospective acquisition times.

The adapter must validate the 2,195-per-market ordered 4h signals and 8,784-per-market ordered hourly opens, reconstruct explicit stable per-row/month identities and pass data to the existing pure replay engine, not fit models.

Input validation must reject missing, duplicate, inconsistent, cross-market, wrong-month, out-of-order, unpinned and malformed evidence.

For model lineage, use model_recipe_sha256 equal to the original Stage 2B manifest SHA-256, and explicitly label it recipe_identity_kind=stage2b_manifest_sha256 — this does not claim to be a standalone digest of coefficients or to imply identical BTC/ETH fitted models.

Pin the original market-specific Ridge/scaler configuration and feature order from the verified Stage 2B manifest metadata in the future source evidence; validate synthetic metadata now.

Preserve historic signal availability as an assumed timestamp, not an actual issuance timestamp. Do not convert hourly opens into synthetic REST Quotes.

When constructing mock evidence, it is acceptable to use the published frozen expected digest strings as mocked identifiers.

Be explicit that synthetic tests cannot establish authenticity of real files; that can only be verified at the later real-run gate.

4. Fixed simulations and contextual accounts

Exactly two independently funded (10,000-USDT) Ridge portfolios: BTCUSDT and ETHUSDT, from 2024-01-01 00:00 UTC through the exclusive 2025-01-01 00:00 UTC endpoint.

Ridge forecasts at +4h+60s hypothetically execute at the strictly next hourly opening (12:01 → 13:00).

Consecutive positive forecasts HOLD, nonpositive signals liquidate once, re-entry requires a new signal.

Retain open holdings at the 2024-12-31 23:00 final mark without inventing a sale or 2025 price.

Only the approved historical-base-v1:

Fee: 10 bps per side, USDT quantum 1e-8, ROUND_UP.

Hypothetical half-spread: 1 bp.

Adverse slippage: 2 bps per side.

Synthetic base quantity step: 0.000001 for both markets.

Reuse replay_historical unchanged unless a proven critical defect makes a separate, explicitly reported stop unavoidable.

Do not implement or silently approximate frictionless/stress scenarios in this task.

Include two separately labelled historical analytical benchmarks, per market:

Cash: fixed 10,000 USDT, no fees or trading, marked at the same hourly identities.

Buy and hold: an independent 10,000-USDT hypothetical account purchases its maximum fee-affordable synthetic quantity at the 2024-01-01 00:00 original hourly opening price ×1.0003, with the same approved base quantity step and 10-bps fee. It makes no further trades or forced year-end sale. Use the shared affordable_quantity, calculate_trade, apply_trade, reconcile, replay rather than duplicating financial formulae. If the whole initial benchmark buy is infeasible under the fixed rules, return an explicit unavailable result rather than moving its entry time.

Value every strategy and benchmark at matched original hourly opening references; keep accounts and funds separate and never call a benchmark trade a Ridge-generated signal/order.

Make clear B&H's 00:00 inception purchase happens earlier than Ridge's earliest 01:00 hypothetical trade and yields different exposure timing.

This comparison is contextual, not causal proof of alpha.

Do not alter either benchmark to simulate a future one-minute scenario or change its inception reference; that requires its own preregistration.

5. Deterministic reporting: all periods, all costs, no selection

For each market and the two controls, calculate and retain where meaningful:

Initial/final cash, asset units, weighted-average cost basis, realised/unrealised P&L and reference-marked equity; exact total return and monetary P&L.

All eligible decision counts by type, executed mathematical buys/sells, matched full hourly marks, starting-funding and each paired signed ledger posting, last ledger sequence and complete replay reconciliation.

Bought/sold notional and turnover relative to 10,000-USDT initial funding, summed actual modelled fees and separately identified hypothetical half-spread/slippage costs by side; no double counting or comparing costs from different account paths.

Exposure duration from actual hypothetical transition times and ending exposure to END for duration only; fraction of hourly observed marks invested; max drawdown computed from inception and observed hourly marked-equity sequence, not intrabar/trade-only drawdown.

Calendar daily returns strictly from consecutive 00:00 UTC marks: only actual complete 24-hour periods enter the complete-day series. The 2024-12-31 00:00 → 23:00 change is labelled a partial 23-hour interval and excluded from complete-day statistics. Monthly returns use calendar-month opening 00:00 boundaries; December 2024 is labelled partial by one hour, ending with its 23:00 mark. Report all months, including poor ones.

Separate full-period cash-relative and buy-and-hold comparisons at common marks, with exposure/time/cost caveats and correct denominators. No Sharpe claims, automated model winner, significance tests or strategy promotion.

All authoritative monetary data are exact Decimal strings; display rounding must not replace scientific values.

Make missing/undefined metrics null/explicit undefined, not a fabricated zero.

Explicitly identify the output as kind=historical_simulation using archived hourly opening references, without provider-side quote timestamps, actual order-book liquidity or warranted fillability.

A positive result is not independent research validation; Ridge was chosen after previous 2024 analysis.

Future frequency compatibility

The daily/monthly time-boundary and duration algorithms may eventually be reusable for denser marks, but this implementation must retain exactly the frozen hourly definitions and counts.

Avoid silently equating "one observation" with "one hour" in a generic account/cost-summary function where an explicit timestamp difference is just as simple.

Keep the existing hourly-specific output names and the 00:00 boundary definitions.

Do not introduce one-minute output, assumptions, tests requiring real one-minute files or performance figures.

6. Immutable publication contract — synthetic fixtures only

Use an explicit injected output path pointing at a test-owned temporary directory; refuse if the destination already exists, including apparently empty directories.

Publish immutable, reviewable outputs in the frozen protocol's approved shape:

policy.json — exact frozen strategy, config, timing, evaluation definitions, limitations and externally computed protocol hash.

source_evidence.json — supplied/mock complete hash evidence, original identities and recipe lineage, transparently marked synthetic in tests.

decisions.json, orders_trades.json, ledger.json, hourly_marks.json — ordered per-market records and exact accounting evidence; include analytical controls with unambiguous account IDs.

summary.json, daily_monthly.csv, summary.md — both markets, all periods, controls, coverage and transparent scientific limitations.

manifest.json — written last, with schema/version/kind, original market and time boundaries, protocol/hash, dependency/runtime/source-implementation fingerprints, Git revision/dirty-tree provenance where available, byte lengths and SHA-256s for every other output, counts/reconciliation and explicit status=synthetic_test for fixture publications. The manifest must never claim genuine 2024 source authentication from fixture hashes.

Keep scientific payload ordering/serialization deterministic and independent of wall-clock time, output directory name, locale, ambient Decimal precision and machine-specific paths.

Separate nondeterministic operational timestamps if needed; never contaminate scientific hashes.

Do not hard-wire generic serialisation and manifest-hashing utilities to one-hour timestamps where avoidable, but do not change the approved schema or invent a schema for future one-minute outputs.

Re-running with identical injected synthetic evidence and code into two fresh temporary destinations must generate byte-identical scientific payloads and consistent manifest identities.

Check outputs against their manifest hashes and replay all account/mark states.

Use established _retain, _write_manifest and exclusive-publication conventions when suitable.

Never overwrite existing directories or previous artifacts.

On simulated write failure, do not publish a valid manifest.json; retain clear failure evidence, never silently resume/rewrite previous science.

No writes to the existing artifacts/ tree in this stage, even new versioned directories, and no S3/backup/deployment interaction.

The eventual approved real output destination will be artifacts/paper-historical/stage-4b2-base-v1/ but must not be created now.

7. Synthetic tests and acceptance criteria

Add tests/test_paper_historical_evaluation.py (or similarly focused test file).

Use only fabricated full/short 2024 grids, mocked source-loader responses and tmp_path.

Tests must not open any real research, prediction, hourly, Stage 2C/2D, Stage 3 or holdout payloads.

Require tests for:

End-to-end two-market synthetic fixture; exact Ridge source/target counts, independent accounts, forecast-to-next-hour execution and continuous HOLD lifecycle.

Rejection of wrong SHA pins, wrong market/model, broken monthly source/ZIP associations, missing/duplicate/reordered hours/horizons, price mutations and source-protocol mismatch; no successful manifest.

Cross-check every strategy/benchmark mark and final balance with shared accounting replay; exactly two signed postings per hypothetical fill and one opening funding event per account.

Exact B&H initial 00:00 buy, 01:00 earliest Ridge buy, base-cost fee rounding, synthetic-step affordability, separate cash benchmark, final open B&H and Ridge holdings.

Daily boundaries on leap day, month transitions and year end; 2024-12-31 partial 23-hour day and partial December; all losses included; correct exposure and mark drawdown.

Determinism across input/container order, repeated calls, Decimal contexts, synthetic fixture publication to distinct directories, JSON byte-for-byte stability and output manifest verification.

Exclusive-directory failure, manifest-last partial-write interruption/recovery behaviour, safe failure when an output is missing/altered, and no overwrite of published results.

No actual loaders called, no network or DB, no wall clock leaking into scientific artifacts, no code path opening real artifacts, no frozen source/Stage 4A/protocol modifications.

The approved hourly timestamps, counts, reference IDs, named output files and performance definitions remain unchanged despite any internal separation of reporting/accounting utilities; there is no one-minute mode or accidental alternative baseline.

Run locked Ruff lint, formatter, focused synthetic tests, complete available pytest suite and git diff --check.

The earlier environment had 1,056 passing tests and 183 isolated PostgreSQL skips; report actual new totals without treating skipped integration cases as passing.

Report if CI/isolated PostgreSQL was not run. Do not claim unperformed evidence audits.

8. Documentation and prompt archive

Create docs/stage-04b2b-historical-evaluation-integration.md documenting exact APIs, mocked-versus-real boundaries, source adapters, benchmark assumptions, reporting definitions, evidence/publication format, reproducing synthetic-only tests and the explicit remaining real-run gate.

Add a short future one-minute scenario compatibility subsection identifying exactly:

Which modules/functions currently assume hourly inputs.

Which reusable summary/accounting/publication components can remain unchanged.

What separate source validation, execution timing, cost assumptions, benchmarks, scientific protocol version and tests would be needed.

Describe this as a future proposal, not an approved or implemented research scenario.

Update architecture, roadmap and handoff narrowly to reflect implementation awaiting review, not approved real-run execution.

Archive this exact substantive prompt at:

prompts/stage-04-paper/004-historical-evaluation-integration.md

Preserve the wording, three-digit numbering and historical prompt archive. Review archived text for secrets.

Do not edit docs/stage-04b2-historical-validation-protocol.md, approved Stage 4A documents, existing frozen Stage 2/3 artifacts or fingerprinted implementation files.

If you identify a protocol contradiction, report it and stop rather than silently revising the frozen rules.

9. Explicit exclusions and stop condition

Do NOT run genuine 2024 historical calculations, invoke loaders against genuine local artifacts, create a real output directory, calculate/publish actual P&L, open any 2025–2026 research/holdout data or Stage 3 genuine prediction/outcome data, add live or prospective trading, change policies/models/parameters, implement frictionless/stress cases, install dependencies, modify PostgreSQL or its migrations, contact Binance, touch Lightsail, schedule workers, or build website components.

Do NOT acquire, load, inspect or replay one-minute market data; implement a one-minute strategy/adapter/frequency flag; change the frozen hourly protocol; or claim near-immediate historical execution was tested.

Do not commit, push or deploy.

Stop after the complete synthetic 4B.2B engineering implementation; request a separate explicit user approval before any real 2024 input loading or economic result publication.

10. Completion report

Provide:

Verified starting HEAD and changed files.

Adapter/API shape.

Mock pins and lineage validation.

Cash/B&H methodology and independent shared-ledger checks.

Exact synthetic reports/manifests.

Deterministic/no-overwrite and failure-injection evidence.

Focused/full test and Ruff results.

Unchanged protected file/protocol checks.

Unresolved issues.

A concise inventory of hourly-specific code and future one-minute compatibility.

The exact commands/changes that would be required in a future separately authorised real-run task.

Do not execute those real-run commands now.

Stop after Stage 4B.2B synthetic implementation.
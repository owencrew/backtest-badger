Backtest Badger — Stage 4B.2D.2
Authenticated forecast/minute integration design and synthetic tests ONLY
Owner authorisation: The owner has explicitly approved Stage 4B.2D.2 implementation and synthetic testing only. This instruction does not authorise opening or hashing genuine Stage 2B forecast artifacts, any genuine artifacts/ directory, the original hourly release, the acquired minute release, or the completed parity-audit output. It does not authorise genuine strategy calculation, historical economic reporting, actual evaluation, publishing research results, running providers, accessing holdouts/Stage 3, databases, production infrastructure or deployment. No genuine data access, even “read-only,” is included in this gate.

Primary objective: Build and rigorously test the integration boundary that, following a later separate approval, could authenticate and adapt the frozen Stage 2B Ridge forecast records and independently frozen 2024 one-minute opening references for the Stage 4B.2D replay/evaluation workflow. In this stage, consume fabricated, in-memory, loader-shaped evidence only. Prepare a future genuine-source authentication/execution plan without invoking it now. Do not produce any results derived from genuine 2024 prices or forecasts.

Expected checkout: clean main at eae27377c121fa42f40102ba0cb28151a0d41a38 (the green-CI Stage 4B.2D.1 commit). Its successful GitHub Actions run is 39217332089. If the checkout differs, check Git history and stop for owner review rather than resetting, rebasing or silently adapting the stage. Do not commit, push or deploy. Preserve an exact SHA-256 snapshot of protected tracked files before changes and verify it afterward.
1. Read the authoritative repository contracts first
Review AGENTS.md and at minimum:
- docs/stage-04b2c-minute-execution-protocol.md — approved/frozen historical-minute-execution-v1 scientific policy.
- docs/stage-04b2c-minute-source-pins.md — the frozen minute release table.
- docs/stage-04b2d-minute-replay-engine.md — synthetic-only execution/reconciliation API.
- docs/stage-04b2d1-genuine-hourly-minute-parity-audit.md and docs/stage-04b2d1-genuine-price-parity-audit.md — exactly what was actually authorised, authenticated, compared and published. Read the tracked guides, not the ignored audit files.
- docs/stage-04b2-historical-validation-protocol.md and docs/stage-04b2b-historical-evaluation-integration.md — original hourly baseline and lineage/loader integration.
- src/backtest_badger/forecast_data.py, src/backtest_badger/paper_historical_evaluation.py, src/backtest_badger/paper_historical.py, src/backtest_badger/paper_minute_historical.py, src/backtest_badger/minute_execution_data.py, src/backtest_badger/genuine_minute_price_parity.py, src/backtest_badger/minute_price_parity.py, and shared accounting/strategy/execution modules and corresponding tests.
Important existing APIs and semantics (confirm against live source before relying on them):
forecast_data.load_forecasts(directory) -> (hashes, accounts)
# accounts indexed by (symbol, model) with forecast_data.Signal objects;
# both symbols x all four models are present; 2,195 validation rows per account.

minute_execution_data.load_minute_execution_data(
    directory, *, expected_manifest_sha256
) -> dict  # verifies complete retained native source; returns metadata ONLY

paper_minute_historical.replay_minute_historical(
    symbol, forecasts, references, *, source, expected_source_sha256,
    forecast_sha256, model_recipe_sha256, end_exclusive=END,
    synthetic_misses=(),
) -> MinuteResult
# IMPORTANT: currently accepts SyntheticPriceSource with status='synthetic_test'
# only. This is not genuine-source authentication or authority to calculate
# economic results from real source data.
2. Immutable external identities (declarations only in this stage)
The real immutable identities already documented and approved are:
Evidence	SHA-256
Approved minute methodology	c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b
Frozen original hourly methodology	b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b
Original Stage 2B validation_predictions.csv	e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674
Original Stage 2B manifest.json / whole model recipe lineage	af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581
Original hourly dataset manifest	1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d
Original hourly opening CSV	39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a
Frozen minute dataset manifest	673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127
Frozen minute opening CSV	37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233
Prior genuine parity audit manifest	53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d
Prior genuine parity report	0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb


The separately authorised genuine parity audit found 17,568 / 17,568 exact HH:00 matches across BTCUSDT and ETHUSDT, with zero discrepancies, for these precise releases. This is a previously recorded outcome, not permission to reopen the parity output or any dataset now, and is not permission for genuine economic evaluation. Treat the pin identities as declarations from tracked docs and code, never derive a new “approved” pin from a tampered local file.
3. Scope of Stage 4B.2D.2 implementation
Implement a small, offline, testable, fail-closed adapter for supplied loader-shaped evidence, for example:

src/backtest_badger/paper_minute_integration.py

Choose final API names based on existing conventions. Candidate pure interfaces:
adapt_minute_inputs(
    forecast_result,       # fabricated (hashes, accounts) matching frozen loader shape
    forecast_manifest,     # fabricated parsed Stage 2B manifest-like lineage
    minute_metadata,       # fabricated complete native-minute manifest-like metadata
    minute_projection,     # fabricated required native one-minute openings only
    parity_evidence,       # fabricated externally-pinned parity proof-shaped record
    *, evidence,           # explicit independently-supplied TEST provenance/pins
) -> PreparedMinuteBundle

validate_minute_integration(bundle, *, expected_evidence_sha256) -> None
API names/signatures are illustrative, not required. Keep modules pure and independent of artifacts/; no CLI, directory discovery, loader invocation, network, database, real-data mode, downloader, publisher, background worker, external service or scheduled process. The adapter may import existing types/functions and must not re-fit models or invent forecasts.

Design for a genuine future source boundary, but run none of it in this stage: clearly distinguish (a) a future separately authorised genuine loader/authentication layer, (b) this pure supplied-evidence adaptation/validation seam, and (c) the eventual genuinely authorised trading simulation and publication. It must be possible for a later reviewer to understand where original bytes, released metadata, internal projected data and independent external pins are authenticated, and where economic evaluation starts. Do not falsely label synthetic tests as genuine authentication.
Original forecast contract
- Fixed Binance Spot BTCUSDT/ETHUSDT, 2024 validation only.
- Original 2,195 four-hour Ridge validation forecasts per market, source-opening grid 2023-12-31 20:00 UTC through 2024-12-31 12:00 UTC, every 4h; availability = source open +4h+60s.
- Exact forecast_data.load_forecasts return shape: (hashes, accounts), with all eight (symbol, model) keys (zero, training_mean, ridge, gradient_boosting) from the same original whole-manifest lineage. Validate baseline accounts' identity, chronological grid and 2,195 counts, even though only Ridge predictions feed the strategy. Preserve source row order, and reject wrong model/version, duplicates, missing, extra, wrong-symbol and out-of-order records.
- For Ridge, preserve original exact Decimal predictions, file_sha256, source opening/available clock, canonical record ID binance:spot:{symbol}:14400:{source_open.isoformat()}:ridge, and whole-Stage-2B-manifest model identity. Prediction threshold remains strictly > Decimal('1e-12') and is applied in the engine, not via future-price-dependent adaptation.
- Validate train-only Ridge/StandardScaler and five-feature recipe lineage from authenticated manifest-shaped metadata; reuse existing validation logic, where safe, rather than duplicating it. Ensure no training, refitting, feature refresh, parameter change, withheld target read or look-ahead.
- The existing forecast_data.schedule describes the original hourly experiment timing; do not accidentally adopt its hourly entry/exit schedule or short-horizon liquidation. The approved minute scenario uses continuing holdings and strictly next-minute entry/exit.
- A fixture or in-memory snapshot fingerprint alone cannot authenticate a genuine original CSV or manifest. Document exactly what the future external byte pin and unchanged loader need to prove.
Native minute and forecast/price projection contract
- Full frozen 2024 minute release: 24 exact monthly ZIP/sidecar pairs, 527,040 native minutes per market, 1,054,080 total. The existing minute loader authenticates the complete source, but returns metadata only, not a 1,054,080-object price collection.
- The genuine future adapter must use the already verified complete native source as authority, preserve the exact manifest/processed CSV and monthly ZIP provenance, and project only the required native opening references. Never confuse the projections' own fingerprint with full-source authentication.
- For a standard year: 8,784 hourly HH:00 valuation references plus 2,195 strictly-next-minute forecast-reference times = normally 10,979 distinct minute references per market (if no overlap). Include price evidence even for HOLD and CASH_NOOP decisions, and the 00:00 B&H inception opening (already part of HH:00 marks).
- Validate the full required projection: correct market/date bounds/order, unique/exact timestamp, strictly next-minute 12:01→12:02, exact minute open_time_ms identity, positive finite Decimal opening, original monthly ZIP SHA-256 and processed-file SHA-256 provenance. No later-price substitution, interpolation, fallback, rounding, duplicate timestamps, synthetic gap repair or prices from OHLCV future fields.
- Genuine source status must never be passed as SyntheticPriceSource(status='synthetic_test') or “re-sealed” with an ad hoc fixture pin to bypass genuine authentication. paper_minute_historical currently enforces this as an intentional scientific guard. Preserve that check. If a future genuine execution path requires sharing pure replay mechanics, propose/implement the minimal separate typed trusted-boundary design, with synthetic-only tests proving the two modes cannot be confused. Do not activate or invoke a genuine simulation path under this authorisation. Avoid a broad refactor; if changing previously approved replay modules is necessary, stop and report the proposal instead of weakening a guard in this stage.
- Do not create another 1,054,080-row fixture eagerly just to test the seam. Use small fabricated fixtures and a bounded complete-year synthetic test where justified; apply deterministic bounded streaming/projection concepts for future full-release adapter, not a giant memory-resident price-object list.
Prior parity evidence and timing-comparison gate
- Fix the previously frozen genuine parity manifest/report identities as external declarations. The future integration must verify a real, previously committed/externally retained successful parity audit independently of the source inputs. Never let a caller construct a self-consistent fake parity manifest or direct_timing_comparison_permitted=True flag to grant genuine permission.
- For tests, use explicit synthetic parity fixtures including mismatched pins, direct_timing_comparison_permitted=False, mismatched source manifests/versions, missing or reordered hours and a forged success flag. Refuse all invalid combinations; do not touch genuine audit files now.
- Do not rerun the genuine price-parity audit. The existing published parity report already establishes zero price mismatches for those exact releases. Neither it nor this stage authorises a trading comparison.
What the adapter may and may not output
- Produce deterministic, immutable in-memory, synthetic-labelled prepared inputs and a scientific input-provenance/validation record. Preserve provenance distinguishing an original forecast manifest, hourly source/parity authority, minute native source, projected observation, hypothetical future execution reference and prospective quote.
- A prepared input bundle must not claim the genuine source has been freshly authenticated. No genuine economic status, buy/sell fills, real-data account output, backtest P&L, strategy comparison, returns, drawdown, profitability or performance metrics in the adapter.
- It is acceptable to run a clearly synthetic replay in tests only using the existing pure replay engine and fabricated SyntheticPriceSource to prove correct wiring, forecasts, timestamps, budgets and benchmark independence. Preserve the unchanged Ridge/cash/B&H mechanics, 10,000 USDT funding each, 10/1/2-bps cost convention, 0.000001 step and HH:00 accounting without duplicating the engine.
- Ensure any attempt to call the real/genuine entry point, if one exists in this code stage, raises a clear permission-gate error before file I/O or strategy calculation. Do not add a runtime boolean or environment-variable override permitting unauthorised genuine execution. Instead, document the future separately reviewed authorisation and wrapper entry point.
4. Synthetic tests and fail-closed threat model
Add tests, e.g. tests/test_paper_minute_integration.py. Fabricate all loader returns, Stage 2B manifest metadata, monthly native source identities, minute projections, and prior parity report/manifest evidence. Use known random/test-only SHA strings as fixture hashes; never read genuine files merely to fill a fixture.

At minimum test:
1. Two markets, all eight original forecast accounts; exactly 2,195 Ridge forecasts per market for full-year fixtures; proper first and final signal times; no extra 20:01 forecast.
2. Exact four-hour forecast ID, grid, +60s eligibility and strictly-next-minute projected reference identity.
3. Correct model-manifest/feature order/train-only Ridge/scaler identity and original-source validation hashes. Baselines are validated but not traded.
4. Forecast predictions kept as precise Decimal, with strict threshold boundary/equality and no future minute fields entering signal choice.
5. A projection containing both hourly marks and all scheduled reference points, including HOLD/CASH_NOOP references, correctly preserves monthly ZIP identity and full-release vs projection provenance distinction.
6. Missing/duplicated/reordered/misaligned/price-negative/misidentified sources and forecasts fail without inventing replacement data.
7. Stage 2B lineage mismatch, feature-order swap, regenerated forecast/changed CSV digest, wrong 2024 dataset version or selected model, wrong recipe identity fail.
8. Fake parity success flag with wrong parity report/manifest hash, wrong hourly/minute source identities, mismatched counts or missing evidence fails; parity failure blocks any direct timing-only comparison.
9. The synthetic-only replay source guard remains intact; attempting to feed real-labelled evidence through synthetic playback fails. No genuine execution route is accidentally exposed.
10. Synthetic end-to-end adapter → replay experiment in pytest with independent Ridge/cash/B&H ledgers, first trade at 00:02, minute costs/fees and no forced liquidation. The simulation result is explicitly synthetic, not genuine.
11. Complete-year leap-year synthetic adapter verification with 2,195 forecasts, 8,784 marks per market and compact memory/serialization, using bounded resources. Do not redundantly run expensive multiple full-year scenarios without value.
12. Deterministic serialization/fingerprint independent of ambient Decimal context, no floating-point monetaries, finite numeric checks and unchanged authoritative input/pin values.
13. Tests prohibit network, database, production access and artifacts/ reads/listings/writes, with clear guards covering filesystem and relevant loader functions. No /Users/.../crypto-trading-platform access.
14. Counterexamples where a “successful” synthetic result cannot be mistaken for a genuine authenticated evaluation, including attempts to override source status or bypass mandatory external pins.
Use no new dependencies unless absolutely unavoidable. Minimise duplication and protect the established source parser, source-pin document, genuine parity auditor and monetary engine.
5. Documentation, preservation and checks
Create docs/stage-04b2d2-minute-forecast-integration.md describing:
- The exact implemented function signatures, injected-evidence contract and proof obligations.
- What is really authenticated versus merely mocked or self-consistent.
- How all original Stage 2B accounts, Ridge lineage and minute projection map into typed source references.
- The separation between the original hourly evaluation, minute synthetic replay, prior real price-parity audit, future real forecast loader, future real simulation and publication.
- Causal timing and parity gate, all missing-evidence failure modes, performance/memory bounds and security limitations.
- A detailed but unexecuted future operator plan for a separately approved read-only full-source verification + original forecast loading + authenticated projection stage, followed by still separately approved real simulation/reproduction/publication. The planned operator must pin the exact revision, bytes, input roots and fresh output path before opening data; no permission is conferred now.
Archive this prompt faithfully as prompts/stage-04-paper/008-minute-forecast-integration.md (excluding any unrelated session/auth tails from pasted input). Update docs/architecture.md, docs/roadmap.md, and docs/development-handoff.md narrowly, marking Stage 4B.2D.2 synthetic integration awaiting review, not genuine evaluation.

Protected and unmodified: all previously approved protocols, docs/stage-04b2c-minute-source-pins.md, all genuine audit guides and pins, genuine_minute_price_parity.py, forecast_data.py, minute_execution_data.py, original hourly implementation/evaluation/publication and old tests; preserve uv.lock, pyproject.toml, and .gitignore. Prefer to leave paper_minute_historical.py byte-identical. If an essential change to it would be required for future genuine evaluation, document the exact proposed seam instead of making a misleading synthetic-labelled backdoor.

Run focused pytest, locked full pytest where practical, Ruff lint/format, git diff --check, any new-file whitespace checks, SHA-256 preservation, and git status. Report local PostgreSQL skips as skips; CI is not run locally unless you actually trigger it. Use fabricated fixture data only, with source/DB/network/artifact guardrails active. Report tests accurately.
6. Completion report and explicit stop
Provide:
- Starting Git branch/HEAD, final working-tree status and every changed/added file.
- API signatures and a concise trust-boundary diagram/description.
- How the original Stage 2B model/forecast/manifest lineage is protected.
- Exact synthetic reference counts and signal/execution clock contract.
- Focused and full-suite pass/fail/skip counts; Ruff/whitespace evidence.
- SHA-256 preservation evidence for protected frozen protocols, source pins, loader/replay/monetary modules and genuine parity code.
- Clear confirmation that no artifacts/ files, genuine Stage 2B forecasts, real minute/hourly prices or genuine audit files were opened or listed.
- What additional code review, exact data-access authorisation, fresh destination and immutable publication gates remain before real performance can ever be calculated.
Do not commit, push or deploy. Stop after implementing and synthetically validating Stage 4B.2D.2. Return the report for owner review.

Suggested later commit message (after user review):

feat(research): add synthetic forecast-minute integration adapter

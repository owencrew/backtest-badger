Backtest Badger — Stage 4B.2D.3
Authorised implementation and synthetic testing of the genuine minute-input authentication adapter
Owner authorisation in this conversation: implement, document, and test Stage 4B.2D.3 using fabricated fixtures only. This authorisation does not grant permission to open, list, stat, hash, validate, or otherwise access genuine retained historical artifacts; it does not authorise an operator run, live forecast loading, real replay, any economic calculation, publication of real results, deployment, or a follow-on stage.

Start: owencrew/backtest-badger, main, expected HEAD fb7ec9d1bc5530b88c2f9c35216418c4d8d9484b (feat(research): add synthetic forecast-minute integration adapter). Expected CI: run 39323850146, success (1,760 passed, 1 skipped). Confirm clean git status --porcelain=v1 --untracked-files=all, branch, commit, and CI before any editing. If different, stop and report rather than guessing a new baseline.

Read AGENTS.md and inspect the code/tests/contracts before implementation, including:
- src/backtest_badger/forecast_data.py (original pinned load_forecasts, eight account shape), src/backtest_badger/minute_execution_data.py (pinned native minute loader returning metadata, not a price mapping);
- src/backtest_badger/paper_historical_evaluation.py (real Stage 2B/hourly/research constants, _validate_lineage), src/backtest_badger/paper_minute_integration.py (synthetic only), src/backtest_badger/paper_minute_historical.py (synthetic only);
- src/backtest_badger/genuine_minute_price_parity.py and its tests (read-only genuine price-only parity; do not rerun its real audit);
- docs/stage-04b2d2-minute-forecast-integration.md, docs/stage-04b2d1-genuine-price-parity-audit.md, docs/stage-04b2c-minute-source-pins.md, both frozen Stage 4B.2 historical validation/minute execution protocols, and existing tests.
1. Exact scope and permission boundary
Implement a separate, narrowly scoped, read-only authentication and input-projection adapter for a future approved genuine 2024 minute replay. Write genuine-path-aware code only where needed; all tests must operate on fabricated temporary fixture directories and fabricated source bytes. Do not execute the adapter on actual historical artifacts. Do not create an executable real-data CLI/operator script or an easy environment-variable/flag bypass. The future exact-root, exact-code-pin, fresh-output and operator authorisation gate remains unapproved.

Recommended new module:

src/backtest_badger/genuine_minute_inputs.py

Recommended new test module:

tests/test_genuine_minute_inputs.py

Implement a distinct frozen input/evidence type, e.g. AuthenticatedMinuteInputs, to capture only verified forecast identities, original source provenance, price-independent decision timestamps, projected native-minute references, independent original-byte pins, and verification status. Its status must unambiguously mean source authentication completed, historical replay NOT authorised. It should contain no trades, portfolio balances, returns, drawdowns or trading result objects.

No genuine execution/replay entry point in this stage. AuthenticatedMinuteInputs must not be convertible by relabelling to PreparedMinuteBundle or SyntheticPriceSource. Do not change the existing synthetic_test checks or introduce allow_genuine=True, --real, or a broad status override. A later reviewed replay boundary will explicitly consume this separate authenticated type after separate authorisation.

A dataclass or hash is a provenance/validation record, not a security sandbox against malicious Python callers. Do not overclaim a tamper-proof capability token.
2. Frozen external declarations — never discover or repin based on local files
Identity	Authoritative SHA-256
Stage 2B forecast manifest	af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581
Stage 2B validation forecasts CSV	e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674
Original research manifest declaration (no opening)	a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e
Original research CSV declaration (no opening)	04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8
Hourly manifest declaration (no opening this stage)	1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d
Hourly CSV declaration (no opening this stage)	39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a
Minute release manifest	673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127
Processed native-minute CSV (107,002,277 bytes)	37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233
Prior parity audit manifest	53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d
Prior parity report	0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb
Frozen hourly protocol	b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b
Frozen minute protocol	c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b


Also retain the tracked 24-minute ZIP/sidecar pin pairs and their source URLs, sizes and counts from docs/stage-04b2c-minute-source-pins.md; do not substitute newly observed hashes. Prior genuine parity audit was reported as exact_price_parity, 17,568/17,568 exact equal comparisons, direct_timing_comparison_permitted=true; these claims must be authenticated against the original pinned audit bytes before any genuine future result is accepted, not simply copied from the guide.

The retained paths in the current repository are:
- Original Stage 2B predictions: artifacts/experiments/stage-2b-v1/ — only manifest.json and validation_predictions.csv are permitted for a separately authorised future run.
- Native-minute source: artifacts/execution/binance-1m-2024-v1/ — original 24 ZIPs, 24 checksum bodies, minute_opens.csv, manifest.json.
- Prior price-parity evidence: artifacts/audits/stage-04b2d1-native-parity-v1/ — five published files, not the source hourly directory.
These paths are declarations to develop against, not permission to access them now. The genuine hourly directory, research source, labels, holdouts, Stage 3, database, providers, sibling repo and production must not be accessed. The old parity authorisation must not be reused as a new forecast-access authorisation.
3. Authenticated forecast adapter contract
Design a future read-only entry point that fails closed unless explicitly supplied an exact approved scope and independent external source/code pins. No default to arbitrary directories, no source discovery, no alternate provider or hash override for an actual run. Keep test helper injection private and clearly synthetic.

For future execution, use the unchanged forecast_data.load_forecasts on the exact approved root with its original default pins (not altered fixture pins). Independently verify original manifest and CSV SHA-256 and exact file identities before trusting parsed results, with before/after preservation checks. Parse the approved original Stage 2B manifest for the same whole-manifest recipe lineage; check original input_hashes, frozen feature order, training-only Ridge/scaler parameters, chronological train/validation partitions, original counts, and the unmodified _validate_lineage policy. Do not run the test-only manifest-hash translation in paper_minute_integration._lineage on genuine inputs. Do not read original research.csv or labels to revalidate the recipe.

Require exactly all eight (symbol, model) accounts: BTCUSDT and ETHUSDT × zero, training_mean, ridge, gradient_boosting. Check 2,195 ordered records each (17,560 forecasts total); no missing/duplicated/reordered horizons, no prediction regeneration, refit, model selection or threshold search. Validate baseline semantics and all five-feature lineage. Preserve Ridge's exact finite Decimal predictions, canonical record IDs, four-hour source opens and source-open +4h+60s availability. Do not call forecast_data.schedule as the new minute execution rule (the unchanged loader may use it for its own original validation), and do not substitute the old HH:00 execution clock.

The 2024 Ridge source opens are from 2023-12-31 20:00 UTC through 2024-12-31 12:00 UTC (2,195 per market). First assumed availability is 2024-01-01 00:01, with first hypothetical eligible minute 00:02; last availability 2024-12-31 16:01, hypothetical minute 16:02. No invented December 31 20:01 signal, missing real signals or backdated events. All decisions remain unexecuted in this stage.
4. Minute archive verification and minimal projection
For the future approved wrapper, first independently match the full original release byte identities and 24 ZIP/sidecar pairs against external frozen pins and source inventory. Call the unchanged minute_execution_data.load_minute_execution_data(directory, expected_manifest_sha256=<literal fixed manifest SHA-256>) for full revalidation; it returns metadata only, not price rows. Require exact binance-1m-2024-v1 format/coverage, original processed SHA-256 and byte length, authentic ZIP/sidecar associations, status and implementation provenance. No replacement source, archive repair, checksum waiver or regenerated manifest.

Then make a separate, bounded, single streaming pass of the verified minute_opens.csv with the exact native header symbol,open_time_ms,open,source_sha256, complete original UTC millisecond grid, ordered BTCUSDT then ETHUSDT, monthly source ZIP pins, finite positive exact Decimal opens, bounded physical rows, original processed byte SHA-256/size and EOF. Fail closed on any discrepancy. Build and retain only the union of:
- 8,784 HH:00 valuation openings for each market (2024 leap-year hours);
- 2,195 price-independent strictly-next-minute forecast execution timestamps for each market, including HOLD/CASH_NOOP horizons;
- 10,979 distinct native-minute references per market / 21,958 total.
Never turn all 1,054,080 source records into portfolio snapshots or invent OHLCV. Preserve MinuteReference native identities (binance:spot:{symbol}:60:{open_time_ms}), original processed-file hash and market-month ZIP association on each projected record. Keep projected-subset fingerprint distinct from full native-source authentication evidence; do not use it to replace a pinned original-byte digest.
5. Prior parity evidence validation (do not rerun audit)
Validate the original five-file price-only audit publication using exact known original bytes: externally pinned manifest.json SHA-256 and parity_report.json SHA-256, manifest-listed bytes/hashes for remaining files (provenance.json, integrity.json, discrepancies.csv), complete expected inventory and verified links. Parse the actual genuine auditor schema documented in genuine_minute_price_parity.py, not the incompatible paper_minute_integration synthetic fixture schema.

Require manifest kind=source_price_parity_only, status exact_price_parity, direct_timing_comparison_permitted=true, zero CSV/JSON discrepancies, empty structural errors, and exactly 17,568 equal HH:00 pairs with the correct two-market, month and leap-day distribution. Cross-check audited hourly/minute release pins and protocol/code evidence in the pinned provenance. Do not re-run the old genuine parity comparison, and do not silently interpret a mismatch or ambiguous evidence as success. Parity means price equivalence only; it does not grant strategy-execution authority or prove fillability.
6. Pure authentication output and future run gate
Produce AuthenticatedMinuteInputs only after all original-file, loader, full-grid, lineage, parity and immutable-projection validations succeed, plus post-verification source/code/document preservation rechecks. Include an explicit record of original source SHA-256s, all 24 minute source associations, prior parity publication identity, original forecast/recipe identity, code/protocol pins, projection fingerprints, verification status, exact output counts, and limitations. Freeze tuple fields and use canonical deterministic scientific serialization; do not invent historical publication/issuance timestamps.

For a future separately authorised operator invocation, propose an exact one-use approval record specifying clean Git SHA, reviewed wrapper/code SHA-256, approved input paths/files, the exact frozen external pins, explicit read-only permission, and one previously absent ignored verification-only output destination. Implement exclusive fail-closed publication if it can be meaningfully synthetic-tested; otherwise keep it as a fully specified reviewed design. No success manifest until independent readback of outputs and complete post-read preservation; preserve failure evidence when possible and never resume, overwrite, use an alternate destination or mutate original files.

Not authorised in this stage: operator execution, any actual reads of artifacts/, real input projection, any replay_minute_historical invocation on authenticated inputs, replay_authenticated_minute_historical, real accounts, trades, P&L, comparisons, analytics, production or publication of economic results. The authenticated record must say verification only / genuine_execution_authorised=false regardless of the prior parity flag. The status must not be named synthetic_test and genuine data must never be wrapped as a SyntheticPriceSource.

If robustly implementing an executable real-source wrapper requires granting genuine access or altering a frozen component, stop at an implementation plan/interface with synthetic helpers and identify the precise next approval required. Never work around the limit by accessing artifacts during this stage.
7. Synthetic verification and failure cases
Write all focused tests using fabricated temporary source files with invented SHA-256 values, not copies of genuine market/forecast data, and test private I/O boundaries with safe monkeypatching/fakes. The public future-genuine path must be uninvoked on actual repository artifact roots. Network, DNS/socket, databases, sibling repository and genuine artifact opens/listing/hashing must be blocked with focused fixtures and an offline full-suite audit hook. Do not touch the real saved parity output even to check its existence.

Required tests include:
1. Correct eight-account validation; Ridge prediction and identity preservation; train-only scaler/five-feature recipe; original source-linked metadata.
2. Full 2024 leap-year grids: 2,195 forecasts, 8,784 hourly marks, 10,979 projected price rows per market; no 2025 price or last 20:01 signal; exact 00:01→00:02 timing.
3. Stream validation: wrong header, non-ASCII/oversized lines, missing/excess/duplicate/reordered timestamps, wrong market, malformed price, wrong monthly ZIP, altered CSV hash/length, truncated source, symlink/race and changed source after first read.
4. Tampered/missing forecast CSV/manifest, original lineage and baseline values, missing/reordered accounts, duplicate/late source horizons, non-finite Decimal and unexpected fields.
5. Wrong parity status, forged success flag, wrong file manifest/output digests, missing/excess rows, discrepancy CSV nonempty, wrong per-month/market count, changed original source association, record schema mismatch and incomplete audit evidence.
6. Exact external pin and code identity enforcement; symlink/path traversal and unexpected roots; no source mutation or implicit repinning.
7. No strategy/replay/account calls even on successful fabricated authentication; authenticated data rejected by existing synthetic replay and synthetic integration adapter; any future real replay interface remains absent.
8. Deterministic serialization/provenance, unchanged original loaders/protocols, no new dependencies, no significant memory blow-up; distinct source and projection hashes.
9. Negative tests proving genuine repository artifact access, network, PostgreSQL, sibling repo and other unapproved paths are forbidden.
Do not write tests that need original retained historical data or call original source loaders on real artifact paths. The tests may invoke original loader code against fabricated fixtures under isolated temporary directories if properly bounded, mocked and permitted.
8. Scope of edits, documentation, and validation
Preferred added files:
- src/backtest_badger/genuine_minute_inputs.py
- tests/test_genuine_minute_inputs.py
- docs/stage-04b2d3-genuine-minute-input-authentication.md
- prompts/stage-04-paper/009-genuine-minute-input-authentication.md (archive this substantive prompt; omit unrelated pasted session/browser context)
You may narrowly update docs/architecture.md, docs/roadmap.md, and docs/development-handoff.md. Do not change frozen protocols, original source loaders, paper_historical.py, paper_historical_evaluation.py, paper_minute_historical.py, paper_minute_integration.py, the genuine parity auditor, their old tests, uv.lock, project dependencies, .gitignore, or any original artifacts. Keep changes minimal and stop if protected code seems to require alterations for a safe design.

Run focused synthetic tests, existing replay/integration/parity regression suites, locked full suite if feasible, whole-repo Ruff check and format, tracked/staged and new-file whitespace checks. Record PostgreSQL integration skips honestly; do not count them as passes. Do not relax safeguards because of a test runner environment issue. Verify original tracked protected-file SHA-256s against the clean baseline and report any discrepancy. No manual source-data verification during this stage.

Deliver a completion report containing: starting/final HEAD, changed files, exact new API signatures, explicit permission boundary, evidence/lineage contract, fixture tests including fail-closed cases, preservation results, all test/CI results actually observed, whether any real source was accessed (must be no), what remains necessary for the genuine verification-only operator approval, and the later distinct real replay/economic publication gates.

Stop after implementation and synthetic-only testing for owner review. Do not commit, push, run genuine authentication, run a backtest, perform any genuine economic calculation, or proceed to a further stage.

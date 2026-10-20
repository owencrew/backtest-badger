Backtest Badger — Stage 4B.2D.4: One-Use Genuine-Input Verification Operator (Implementation and Fabricated Tests Only)
AUTHORISATION: Implement and test Stage 4B.2D.4 with fabricated evidence ONLY. The owner has not authorised opening, listing, statting, hashing or executing against real Stage 2B forecasts, minute data, parity audit outputs, or any other original artifacts. The owner has not authorised a genuine verification invocation, the activation of a public operator, a historical trading simulation, a performance calculation, or publication of economic findings. Stop at owner/code review.
0. Baseline, repository instructions, and protected authority
Expected clean main HEAD: 925f9abe2ec21fffc937df86e9283ad63e09aac4.

The baseline GitHub Actions run 39379366971 completed successfully. Confirm local revision and a clean working tree before editing; do not proceed automatically on a different revision or dirty checkout.

Read, in this order:
- AGENTS.md
- docs/stage-04b2d3-genuine-minute-input-authentication.md
- docs/stage-04b2d2-minute-forecast-integration.md
- docs/stage-04b2d1-genuine-price-parity-audit.md
- docs/stage-04b2d1-genuine-hourly-minute-parity-audit.md
- docs/stage-04b2c-minute-source-pins.md
- docs/stage-04b2c-minute-execution-protocol.md
- docs/stage-04b2d-minute-replay-engine.md
- src/backtest_badger/genuine_minute_inputs.py and its tests
- src/backtest_badger/genuine_minute_price_parity.py
- The unchanged forecast/minute source loaders, historical lineage validator, synthetic minute integration, synthetic replay, publication conventions, and relevant tests.
Protect byte-for-byte: all existing source modules, old tests, frozen protocols, source pins, previous audit results/guides, lockfile, dependencies and .gitignore. In particular preserve the current public authenticate_minute_inputs(*, approval) refusal, which raises PermissionError before examining its argument or touching a path. Never change its permission gate to accept a boolean, environment switch, magic string, local approval file or permissive callback. Do not modify the synthetic replay to accept genuine inputs, and do not cast/label genuine inputs as SyntheticPriceSource.

Record a baseline SHA-256 inventory of protected tracked source/document files (not the original artifacts). Only narrowly update docs/architecture.md, docs/roadmap.md, and docs/development-handoff.md among pre-existing files. Stop and request review if a protected file must change.
1. Deliverable and permission boundary
Implement a separate, closed one-use verification operator and an exclusive, manifest-last publication path, fully exercised with fabricated data.

Suggested names (adjust only if an existing naming convention clearly warrants it):
- src/backtest_badger/genuine_minute_verification_operator.py — implementation
- tests/test_genuine_minute_verification_operator.py — fabricated end-to-end and failure tests
- docs/stage-04b2d4-genuine-verification-operator.md — implementation, threat/permission boundary, test evidence and proposed future operator invocation
- prompts/stage-04-paper/010-genuine-minute-verification-operator.md — archive only this substantive request, without unrelated user/session material.
The public genuine operator must remain unusable in this stage: a public function with a clear name such as run_genuine_minute_verification(*, approval) must always refuse before reading the approval payload, inspecting any genuine path or opening a source. Keep the existing genuine_minute_inputs.authenticate_minute_inputs closed as well. No callable CLI, __main__ invocation, --allow-real flag, environment override or approved-by-default fallback.

Implement the actual verification/publication mechanics in a separate private core that can be exercised under pytest with strictly isolated fabricated temporary roots and explicitly invented fixture identities. A single later reviewed source change and separately specified authorisation will be required to expose a real, exact-root entry point. Document precisely what remains inactive; do not claim a live-capable operator is already approved.

It is acceptable to reuse existing private validation helpers from genuine_minute_inputs.py rather than duplicate source/lineage/parity policies. However, never repurpose _authenticate_fixture_inputs to accept genuine pins or paths, and do not make a helper that can silently convert synthetic evidence into AuthenticatedMinuteInputs claiming real authentication. Tests and evidence must retain source_kind=fabricated_temporary_fixture_bytes or equally explicit fixture provenance.
2. Predeclared eventual real operator contract — do NOT execute
This section defines what the closed implementation must be designed to enforce in a future separately authorised run. It is not permission to inspect these paths now.

The only future scientific source roots, to be explicitly approved later, are:
1. artifacts/experiments/stage-2b-v1/ — read only manifest.json and validation_predictions.csv, never enumerate that directory or access other Stage 2B files.
2. artifacts/execution/binance-1m-2024-v1/ — exact manifest, processed minute CSV, and 24 pinned monthly ZIP + 24 checksum sidecars (50 files total).
3. artifacts/audits/stage-04b2d1-native-parity-v1/ — exactly the existing manifest.json, parity_report.json, provenance.json, integrity.json, discrepancies.csv.
Proposed future exclusively reserved ignored output, subject to an explicit later approval and absence check:

artifacts/audits/stage-04b2d3-minute-inputs-v1/

Do not create, inspect, list, stat or reserve it during this stage. Do not use the previous parity-output location for new publication. There must be no discovery or access to the original hourly archive directory, research CSV or labels, 2025–2026 holdout, Stage 3, sibling repository, any database, exchange API or production.

Original byte pins are fixed externally, never inferred from the candidate source bytes:
Identity	SHA-256
Stage 2B forecast manifest	af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581
Stage 2B validation predictions CSV	e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674
Original research manifest — declaration, do not open	a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e
Original research CSV — declaration, do not open	04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8
Original native-hourly manifest — prior-audit declaration, do not open	1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d
Original native-hourly CSV — prior-audit declaration, do not open	39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a
Minute manifest	673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127
Minute CSV (107,002,277 bytes)	37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233
Completed parity manifest	53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d
Completed parity report	0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb
Minute protocol	c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b
Hourly protocol	b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b
Tracked minute source-pin document	967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c


Read the other authoritative identities and all monthly SHA/size/URL/count tables from the unchanged, previously frozen tracked documents only, after validating their already-declared document pins. Future code/dependency/operational pins must be separately frozen and reviewed after implementation, before any real source access; do not auto-approve hashes read from a mutable checkout.
3. Exact one-use approval and preflight design
Define a clear, non-optional operator approval schema for future use, but do not accept any such approval through the closed genuine entry point now. It must bind:
- A full, clean Git commit SHA and successful CI run for the reviewed implementation.
- Exact SHA-256 identities for the operator, all transitively relevant code, documents, pyproject.toml, uv.lock and critical dependency/runtime versions. Pins must originate outside the currently inspected artifacts, not be dynamically blessed.
- Exact permitted input file inventory and roots above, full original external SHA-256 pins and the one future destination.
- Verification-only status, no strategy or publication authority, and the single-attempt/one-use rule.
- A previously absent destination verified without following symlinks, before any source opening.
A reservation must be atomic (mkdir without exist_ok), must happen once, and must consume the approved attempt even if it fails. Never silently retry, overwrite, repair, resume, delete evidence, rename to an alternate destination or regenerate an approval. Read-only file access to original inputs; output writes only inside the single reserved directory. Reject a dirty checkout, changed code/pins, symlink in any path component, missing/unexpected files, changed inode/stat/hash across checks, wrong source version or incomplete evidence before a successful manifest can be published.

Preflight checks with failures before reservation should leave no directory; failures after reservation should leave clearly incomplete, forensic failure evidence without a success manifest.
4. Verification-only core and non-execution proof
Under the test-only fabricated wrapper, implement the later real path faithfully with independently supplied TEST pins. Avoid code paths that are partly stubbed yet reported as successful authentication.
- Validate the two named forecast files by exact original-byte hash/size and the unchanged forecast_data.load_forecasts parser. Validate original manifest lineage without synthetic hash translation in the intended real path; mock/test with invented identities only via controlled dependency injection. Require all eight accounts, 2,195 fixed forecasts each, Ridge prediction Decimals, frozen model/scaler lineage, canonical source opening and +4h+60s assumed availability. Do not refit, regenerate or read a label.
- Validate the minute release as the complete 50-file native source. Require the unchanged minute_execution_data.load_minute_execution_data with the literal frozen original manifest pin in a future real invocation, plus month-by-month source ZIP/checksum identities. Distinguish fabricated fixture loader returns from actual full archive revalidation in synthetic tests; don't misreport tests that inject mock metadata.
- Reuse the Stage 4B.2D.3 bounded 1,054,080-row projection contract, checking every source row, the exact minute CSV hash, strict UTC/open-price/source associations and EOF. Retain 8,784 HH:00 marks and 2,195 next-minute references per market (10,979 each, 21,958 total); no million-row object retention.
- Independently verify the complete existing five-file parity audit publication and its original pins/linked source identities. Reuse the actual genuine auditor schema, not the synthetic fixture schema. Require all 17,568 equal HH:00 prices, zero structural problems/discrepancies and its original source_price_parity_only status. Do not rerun the parity audit or change parity methodology.
- Recheck all originally permitted file hashes/sizes/stats and reviewed implementation identities after verification and after output readback. Fail closed on observed changes; do not relabel any source or repair mismatches.
- Output the already-defined AuthenticatedMinuteInputs structure as a verification-only record. Its genuine_execution_authorised must remain False. An authenticated result is not a simulation-capable portfolio or a capability token. The old synthetic replay must continue to reject this type, and no replay_authenticated_minute_historical may be added now.
- Absolutely no strategies, buys/sells, accounts, fills, ledgers, P&L, returns, Sharpe, drawdowns or backtest performance calculated from genuine inputs. Use no provider/network/database or production. No research-data label reads.
5. Exclusive, reproducible verification publication
Implement a narrowly scoped publisher only for the test-only private execution core; keep genuine invocation closed. Define a clean deterministic schema for:
1. authenticated_inputs.json: exact verification-only scientific record, provenance, immutable forecast/minute references, source hashes and scientific limitations; not a trading result. Scientific bytes should not depend on output location, creation clock, inode/mtime, or external session data.
2. integrity.json: separate operational before/after code/source byte/hash/size and filesystem stat evidence, plus declared versioning; it may vary on reproduced filesystem copies.
3. manifest.json: final success marker written last, specifying the complete output inventory, lengths, SHA-256 hashes, kind=source_authentication_only, no economic results, and genuine_execution_authorised=false.
4. failure.json: incomplete-attempt evidence on post-reservation failure (phase, safe exception type, complete=false, resume=false); no success manifest. Never leak data, exception messages containing sensitive file content, or secret paths.
Use exclusive .partial file creation, flush/fsync, atomic exclusive publication (e.g. hard-link/unlink where supported) and independent readback/hash/length/schema cross-checks. Verify the science and integrity documents agree with the independently retained pins and source inventory. Recheck source/code preservation after output verification and before final manifest. In case of exception, remove/invalidate only a just-published success marker from this attempt, never wipe an existing attempt or the original data. A hard kill can leave partial artifacts; such a directory must never be considered a completed successful run or automatically resumed.

The test harness may create and inspect fresh temporary directories. No actual path under repo artifacts/ may be created, listed or opened in this stage. Do not commit any generated evidence files.
6. Mandatory fabricated test coverage
Write comprehensive focused tests that use fabricated data and the same actual production publication/verification mechanics, injected only at explicit test boundaries:
- The public real operator and existing authenticate_minute_inputs always refuse before inspecting approval payloads or opening files, even for apparently valid approval records; malicious objects and coercion side effects must not be evaluated.
- Exact directory allowlists; no silent source discovery; named forecast files only (no forecast-directory listing); fail on symlinks, path traversal, wrong inventory, already existing output, unexpected or deleted file, changed code or moved inode.
- Frozen external identity mismatches, original ZIP/sidecar association failures and source changes during/after loading.
- Forecast manifest/CSV, all eight account identities and full original ridge/model/scaler/timing lineage; rejected tampering, reordering and altered predictions.
- Full native 1m grid, source hashes, leap February, 1,054,080-row bounded scan, 21,958-reference projection and source-preservation check. Memory bounds should remain reasonable; avoid repeating the expensive full-year fixture unnecessarily.
- Valid and corrupted five-file parity publication, forged success flags, wrong original manifest/report hashes, missing/extra files, altered provenance/retained integrity, nonempty discrepancies and wrong 17,568-market/hour counts.
- Exclusive success case with canonical scientific JSON, manifest-last status and on-disk readback. Reproducible scientific-byte hashes when the same invented fixtures are published to different fresh temporary roots.
- Failure-injection at every phase: before reservation (no new output), after reservation, during file creation, after creating .partial, after output readback, before manifest, during manifest publication and immediately after; never produce a completed manifest for failed attempts. A second run on an already reserved destination must fail without mutation.
- Explicit negative tests proving no forecast side effects, trading calculations, replay/funding/cost/valuation calls, network/provider access, PostgreSQL, other artifacts, sibling repository or production.
- Existing native loader, synthetic replay/integration and genuine parity tests continue passing unchanged.
Block forbidden I/O in actual tests, not only via comments/mocks that do not execute. Use the installed locked/offline environment and a fresh user-owned pytest temporary base (prior sessions established that macOS /tmp group ownership causes an unrelated permissions test failure). No network downloads or dependency installations.
7. Documentation, validation and stop conditions
Create the implementation guide with:
- Precise public closed gate and implemented private test entry points/signatures.
- The single-attempt future approval contract and exact proposed roots/destination, clearly marked not yet authorised.
- Detailed provenance/pin schema, end-to-end operator event order, exclusive-publication invariants and security limitations.
- External pin origins, exact count/grid requirements, reproducibility interpretation and separation from genuine simulation.
- Test coverage, full-suite results, failures resolved during development, local skip reasons, and original protected-source SHA-256 preservation.
- Explicit next permissions required to (a) approve a reviewed production wiring and one read-only genuine verification run, (b) implement and authorise the genuine replay boundary, and (c) publish/reproduce economics.
Update docs/architecture.md, docs/roadmap.md and docs/development-handoff.md narrowly, including replacing obsolete handoff priority text; do not rewrite historical protocol or provenance records.

Run and report focused tests, the locked offline full suite (where possible), Ruff check and format, tracked/staged whitespace checks, explicit whitespace checks on untracked files, and baseline-versus-final protected byte inventory. Treat PostgreSQL skips as skips. Do not equate test assertions reaching 100% with full success if pytest cleanup or exit status fails. Never report GitHub CI as passing for uncommitted changes.

Completion response must state: initial/final HEAD; changed files; new API signatures; which public interfaces remain closed; exactly what fixture orchestration and publisher were actually exercised; focused/full tests and skips; protected-file preservation; proposed approval payload/pins; any incomplete edge cases; next explicit authorisation gates. No genuine artifact may have been opened or even inventoried.

STOP. Do not commit, push, deploy, access any genuine artifact, activate the public operator, invoke the genuine wrapper, create an actual ignored audit output, run a genuine strategy, or proceed to Stage 4B.2E. Await owner review.
Suggested commit message (after independent review, not part of this task)
feat(research): add gated minute-input verification operator and publisher

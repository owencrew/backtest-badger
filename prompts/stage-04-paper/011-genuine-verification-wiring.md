Backtest Badger — Stage 4B.2D.5: Genuine Verification Wiring & Approval Preparation
Owner authorisation: IMPLEMENTATION AND FABRICATED-DATA TESTING ONLY. This authorisation does not permit opening, listing, statting, hashing, loading, or executing on the original retained 2024 data, including the original Stage 2B forecasts, 1m/1h source archives, previous parity-audit output, research/holdout artifacts or any other genuine artifact. It does not authorise a genuine verification attempt, backtest, strategy replay, economic results, publication from genuine data, deployment, network access, databases, or production work. Preserve the closed genuine entry points. Stop for owner review.
0. Start condition and instructions
Read AGENTS.md, this entire request, and the exact contracts in:
- src/backtest_badger/genuine_minute_verification_operator.py
- src/backtest_badger/genuine_minute_inputs.py
- src/backtest_badger/forecast_data.py
- src/backtest_badger/minute_execution_data.py
- src/backtest_badger/genuine_minute_price_parity.py
- src/backtest_badger/paper_minute_integration.py
- src/backtest_badger/paper_minute_historical.py
- docs/stage-04b2d4-genuine-verification-operator.md
- docs/stage-04b2d3-genuine-minute-input-authentication.md
- docs/stage-04b2d2-minute-forecast-integration.md
- docs/stage-04b2d1-genuine-price-parity-audit.md
- docs/stage-04b2c-minute-source-pins.md
- docs/stage-04b2c-minute-execution-protocol.md
- docs/stage-04b2-historical-validation-protocol.md
- docs/architecture.md, docs/roadmap.md, docs/development-handoff.md
- the existing tests for genuine input verification, source loaders, parity, integration and minute replay.
Expected clean baseline main at full Git commit:

550d457aef42b08a2933a701136266d31da082b5

Baseline GitHub Actions run 39473129809 completed successfully for that commit (1,999 passed; 1 skipped). Independently check the local commit/working-tree state. Stop and explain any mismatch or pre-existing modifications; do not reset, discard, amend or silently reconcile a different checkout. No need to fetch/download code or packages. If GitHub is inaccessible, say so; do not invent independently verified CI evidence.

Read repository policy first; do not access or modify sibling crypto-trading-platform, any cloud service, provider, network, local database, production Lightsail, deployment or other repositories. The original ignored artifacts/ tree is off limits during this stage: do not even list or stat it. All integration success cases must use exclusively fabricated files created under a fresh temporary test root. Do not try to infer missing real-artifact lengths or runtime pins by opening original artifacts.

Before modifications, take a reproducible SHA-256 inventory of all protected pre-existing tracked files without traversing artifacts/; exclude only explicitly authorised high-level documentation to be edited. Record the protected count, canonical mapping hash and exact baseline. Preserve the frozen protocols, source-pin records, prior parity auditor/guide, previous implementations/tests, original source loaders and replay/accounting modules byte-for-byte unless an essential narrowly scoped change is first reported as a blocker for owner review. No dependency additions, configuration/lockfile modifications or test weakening.
1. Objective and scientific boundary
Stage 4B.2D.4 delivered a private fabricated-fixture verification operator and exclusive manifest-last publisher, but the public function remains unconditionally disabled:
run_genuine_minute_verification(*, approval) -> AuthenticatedMinuteInputs
The earlier genuine_minute_inputs.authenticate_minute_inputs(*, approval) also unconditionally refuses. This is intentional. Stage 4B.2D.5 must prepare reviewable genuine-production bindings and an exact one-attempt approval preparation workflow, while keeping actual source access and both public functions disabled. Do not turn the fixture runner into an unprotected genuine loader, do not set allow_genuine=True, do not relabel fabricated_temporary_fixture_bytes as genuine, and do not have any public convenience function that can indirectly call the real-data verification path.

Deliver the smallest maintainable wiring implementation that makes a later, separately authorised source change and one genuine read-only attempt straightforward and auditable. Reuse the existing approved preflight, authentication primitives, native loader, parity checks, private one-use publisher and failure behavior; avoid copying the 915-line authentication module or 665-line operator into a second implementation. Do not invoke the synthetic-only execution engine on genuine inputs.

A good design is a pure, non-executing, reviewable verification plan/binding descriptor plus internal callable-boundary plumbing safely exercised against fabricated roots, and an approval-readiness checker/template that reports unresolved required evidence. Use judgment about exact module names/APIs, but meet every safety and verification acceptance criterion below and document the concrete seam. Any changes to existing operator code must be minimal, clearly scoped and compatible with existing tests. The old public genuine gate must remain an unconditional PermissionError at function entry before evaluating the approval argument.

This is a wiring/preparation stage, not a disguised real authentication run. The implementation must not issue a production approval token or make approval attainable solely from local candidate bytes.
2. Exact original identities: declarations only, never source reads
These existing frozen identities are known from reviewed tracked code/documents. Treat them as independent immutable declarations, not as instructions to open data:
Identity	Frozen SHA-256
Stage 2B validation forecast manifest.json	af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581
Stage 2B validation_predictions.csv	e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674
Research manifest.json (declaration only)	a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e
Research research.csv (declaration only)	04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8
1h manifest (from prior parity evidence; not an input root now)	1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d
1h processed CSV (declaration only)	39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a
1h acquisition (declaration only)	926697a89eb7c018ca5913f1e3c4c1170715db5639d444a58a78012e92aec055
Native minute manifest	673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127
Native minute processed minute_opens.csv	37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233
Prior completed parity manifest.json	53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d
Prior parity parity_report.json	0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb
Prior parity provenance.json	fb44c49bf468ca976706567f7997ff61cdfe3f5157eca387c796b73fba0556eb
Prior parity integrity.json	5594e11f44cbc0e820595501a508b47f6f7b55508de3c2895c7b6ae6e64ab395
Prior parity discrepancies.csv	0afb86f6389a1ab6a6931f0a96bd3ef0484bbd172f8bcd8b2fc7b8e9dea4a755
Minute source-pin document	967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c
Frozen hourly protocol	b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b
Frozen minute protocol	c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b


Known original file sizes: minute CSV 107,002,277 bytes; parity report 18,452, parity provenance 60,610, parity integrity 61,684, parity discrepancy CSV 162, parity manifest 740. The existing frozen minute-pin document gives 24 monthly ZIP/sidecar identities/sizes/counts. Do not invent the sizes of the two original forecast files or other missing sizes. If approval requires other externally pinned original lengths that are not in reviewed tracked records, list them as unresolved evidence. Do not issue a valid-looking ready-to-run approval with placeholders, fabricated sizes, or values computed from unapproved local originals.

Any genuine-run approval would have exactly 57 source files: two named Stage 2B forecast files; 50 minute-release files (manifest, processed CSV, 24 monthly ZIPs, 24 checksum sidecars); five original parity-publication files. The research and native 1h data are not additional input roots: their hashes are declarations or provenance already authenticated by the prior audit.

Exact future roots (declare only; never exists, stat, lstat, resolve, open or enumerate in this stage):
artifacts/experiments/stage-2b-v1/
artifacts/execution/binance-1m-2024-v1/
artifacts/audits/stage-04b2d1-native-parity-v1/
Exact proposed future fresh output (declare only; do not inspect or create):
artifacts/audits/stage-04b2d3-minute-inputs-v1/
The output's existence and ignore status are not yet established; they must be checked only under a future expressly approved source/output preflight. Do not reuse or overwrite the parity output. Do not publish a manifest.json from original data.
3. Production wiring contracts to prepare now, WITHOUT execution
Design and implement narrow production binding declarations with no operational side effects. Explicitly establish how a future approved wrapper will invoke the unchanged APIs:
forecast_data.load_forecasts(approved_forecast_root)
paper_historical_evaluation._validate_lineage(original_forecast_manifest)
minute_execution_data.load_minute_execution_data(
    approved_minute_root,
    expected_manifest_sha256=(
        "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127"
    ),
)
Do not override the genuine forecast loader's original default pins. Do not use the synthetic integration module's TEST-hash lineage translation. Do not regenerate the model or touch research labels/holdouts. The native minute loader returns metadata only, not a native-price mapping. The existing bounded projector (genuine_minute_inputs._stream_projection) must validate every one of the 1,054,080 minute rows and retain only 21,958 required references (per market 8,784 hourly marks + 2,195 strictly next-minute forecast observations = 10,979). Source openings 2023-12-31 20:00 to 2024-12-31 12:00; forecast availability +4h+60s; execution reference strictly next minute, e.g. 12:01 -> 12:02. The prior five-file parity publication uses the actual auditor schema, not Stage 4B.2D.2 synthetic fixture parity schema; validate the pinned original evidence without rerunning the audit. The parity permission flag only establishes native-opening-price comparability, not an evaluation/trading permission.

The new wiring must make these binding identities and contracts inspectable/testable without importing or executing a genuine-source operator. Importing any new module must be side-effect-free: no source queries, no Path.resolve() against genuine paths, no Git/network/DB access, no CI query, no scanning of artifacts/, no destination reservation. No CLI, background task, environment switch, magic file, config flag or callable public genuine-data bypass.

If a shared internal engine refactor is truly necessary to eliminate duplicated operator code, retain the existing fixture-only entry point's strict temporary-root and synthetic-pin restrictions, keep real entry points refusing, preserve publication's one-use fail-closed semantics, and add regression tests proving the old gates cannot be bypassed. Prefer not to modify frozen source modules at all. If the requested wiring appears to require creating a callable non-fixture real-data function now, stop and report the design tradeoff rather than silently implementing a path that bypasses the owner gate.

The future correctly typed result remains AuthenticatedMinuteInputs with genuine_execution_authorised=False. It is not a PreparedMinuteBundle or SyntheticPriceSource, and there is no replay_authenticated_minute_historical or real trading calculation in this stage.
4. Approval readiness and external evidence plan
Implement a pure, fail-closed approval-readiness validator/template (or similarly small read-only component), distinct from the existing TEST approval schema, that can report required evidence and unresolved fields without constructing an executable authority. Prefer a structured result clearly marked NOT_APPROVED, NOT_READY, NO_SOURCE_ACCESS (or equally unequivocal values); do not mint fake CI, SHA-256, runtime, owner signature, or a real approval record. Its purpose is to make future review deterministic, not to grant authority.

The documented eventual one-attempt schema must include at least:
1. Clean full reviewed Git commit SHA, matching GitHub CI run ID with completed/success result independently checked for that exact commit. The existing baseline SHA/CI are not approval for future changed wiring code. No new code SHA or workflow result may be guessed in advance.
2. Full transitive implementation code/document/configuration allowlist, independently retained SHA-256 and byte length for every file, including production wiring, operator, old authentication primitives, imports, protocols, pyproject.toml and uv.lock (and import closure validation).
3. Exact Python version/implementation and relevant installed dependency versions (alembic, numpy, psycopg, psycopg-binary, scikit-learn, scipy, SQLAlchemy, joblib, threadpoolctl). These are observations to freeze at the future run boundary, not credentials or loose compatibility ranges.
4. Three exact original input roots and their exact 57-file allowlist, external per-file SHA-256 and length. All 24 ordered minute market/month ZIP and checksum hashes, sizes, URLs, monthly grid/expanded byte counts, retrospective receipts. Independently retained hourly monthly ZIP pins and prior-auditor implementation identities.
5. The frozen methodology/source document pins and original genuine_minute_inputs.EXTERNAL_PINS; no hash substitution, dynamic fallback or input-derived self-pinning.
6. An exact absolute previously absent approved destination, strict verification_only=True, single_attempt=True, resume=False, strategy_authorised=False, economic_publication_authorised=False, source-kind explicitly identifying the genuine retained releases.
7. Clear evidence of owner authorisation for one read-only source verification invocation, given after reviewing/committing the genuine-enabled wiring code and green CI; no standing authorisation and no automatic retries.
Supply a human-readable checklist of which identities exist in tracked declarations vs. which still require independently retained evidence. Keep a missing-evidence list, especially the original forecast file lengths and future reviewed code/CI/run-specific runtime identities. A helper may parse only tracked frozen documents, never the ignored artifact tree. If it can build candidate records, they must be intentionally non-executable and rejected by both public gates, and tests must demonstrate that.

Avoid unnecessary machinery: do not build a generalized permission server, persistent authorization database, signing PKI, downloader, token service or network CI integration. Simple reviewable structures and exact validation are preferred.
5. One-use verification publisher and safety acceptance
Retain the existing Stage 4B.2D.4 semantics. For the future approved invocation, the design must preserve this exact ordering:
- Validate and detach a complete externally pinned approval before source access; reject incorrect commit, CI, runtime, code/document/source inventories, source-kinds or non-verification flags.
- Confirm no symlinks and no existing destination; atomically reserve the sole named destination, consuming the attempt before opening genuine source files. No retry, resume, alternate directory, repair, downloads or overwrite.
- Hash named permitted forecast files only; never enumerate that forecast root. Verify the exact complete minute/parity inventories and external digests/lengths before trusting bytes.
- Run unchanged forecast/lineage/minute loaders, full native projection and previous publication verification. Recheck original bytes/stats, code/document identities and environment after verification and after publication readback.
- Produce authenticated_inputs.json (deterministic scientific evidence), integrity.json (operational approval, before/after filesystem stats), then manifest.json last, with exact verified hashes/lengths, kind=source_authentication_only, economic_results=false, genuine_execution_authorised=false. Files are exclusive/fsynced/read-back and no unknown files or .partial files can remain on success.
- On failure preserve incomplete forensic evidence and refuse to represent it as success. Invalidate only a manifest inode owned by this attempt. Do not remove someone else's destination/files, or silently recover/resume. Record safe failure class/phase only; no arbitrary exception messages, secrets, source rows or leaked private paths.
- A hard kill, disk failure or coordinated hostile filesystem mutation can defeat cleanup; document operational limits and do not claim transactionality/fillability/provider signatures.
The current fixture's source_kind=fabricated_temporary_fixture_bytes must remain explicit in all synthetic outputs. Never represent fabricated tests as successful authentication of the actual Binance or Stage 2B artifacts.
6. Synthetic-only testing: real safety checks, zero genuine access
Write focused tests for each new wiring/readiness function, and extend existing fixture tests only if needed. Test against fabricated temporary roots only. Require a process-level offline I/O guard installed before pytest collection: forbid opens, listing, stat/lstat of genuine repository artifacts and sibling crypto-trading-platform, and forbid sockets/DNS, provider/database connection and genuine audit/replay/economics. Actually exercise forbidden paths to prove the guard works. Run pytest from an explicitly allowed tests path with fresh user-owned temporary base to avoid previous macOS fixture-group and pytest-cleanup failures. Do not relax guards to make the suite pass. Unconfigured PostgreSQL cases are skips, not passes.

At minimum cover:
- Public run_genuine_minute_verification and authenticate_minute_inputs always raise before inspecting malicious approval objects; none of the new wiring/readiness APIs can trigger genuine source I/O or an invocation.
- Reuse of the unchanged forecast/lineage/minute loader contracts with fabricated files; distinguish injected fake metadata from actual fabricated ZIP/sidecar native revalidation. No TEST hash override exposed on a genuine execution path.
- Complete 2024 grids, eight model accounts, 2,195 forecasts per account, exact Decimals, train-only scaler/whole-manifest lineage, 1,054,080 minute rows/21,958 projected references, leap February, every required next-minute timestamp including HOLD/CASH_NOOP horizons, end-of-year boundaries.
- Pinned prior parity publication and provenance, all month/market counts, exactly 17,568 equality pairs, zero discrepancies; reject modified/resealed mismatched claims and absent/unknown linked files.
- Strict approval missing field, wrong file length/hash, changed code/doc hash, altered original source associations, stale CI/revision/runtime, dirty checkout, missing externally retained monthly identities, extra/unknown files, wrong source-kind, bad destination, symlink, traversal, receipt/source ambiguity, float/nonfinite forecast/price, duplicate/reordered timestamps, etc.
- Readiness must fail, not produce approval, with unknown genuine forecast lengths, future wiring hashes, CI evidence or destination state; it cannot self-heal by calculating missing pins from candidate real files.
- Deterministic scientific serialized bytes under copied fabricated roots; operational stats may differ. Verify canonical parsing/readback and full three-file successful inventory. Failure injection at all reservation, mutation, partial-create, fsync/link, readback, manifest-last and post-manifest phases must prevent a valid success publication. Preserve an alien collision inode, never retry or overwrite.
- The full native projection stays memory bounded (prior tracemalloc bound 32 MiB), preferably relying on existing regression rather than duplicating expensive full-year cases unnecessarily.
- No strategy, funding, trade, ledger, mark, P&L, Sharpe, economic report or genuine authentication invocation occurs.
New tests should preferentially exercise the existing full-year fabricated fixtures rather than create a second expensive independent million-row dataset. Keep the test suite reasonably fast and avoid broad refactoring.

Run:
1. Focused new/affected test suites with complete offline guards and confirmed exit 0.
2. Full uv run --locked --offline --no-sync pytest suite with the same guards, fresh user-owned temp base, no downloads/install/network/DB; record pass/skip/fail and actual process exit. If the full run is interrupted, not concluded or pytest cleanup fails, do not claim a pass; rerun appropriately.
3. Ruff lint + format checks on explicit tracked/new Python inventory (avoid automatic discovery of ignored artifacts).
4. git diff --check, git diff --cached --check and explicit whitespace/final-newline checks for new untracked files.
5. Pre/post SHA-256 and baseline Git-blob confirmation of all protected tracked files. Do not infer source preservation from changes in ignored data; do not inspect originals at all.
Do not falsely claim PostgreSQL integration tests passed if skipped. No production deployment or GitHub CI run is included in the local task. New CI will occur only after an owner-reviewed commit/push.
7. Deliverables and documentation
Keep the diff focused. Suggested new guide:

docs/stage-04b2d5-genuine-verification-wiring.md

Suggested archived prompt:

prompts/stage-04-paper/011-genuine-verification-wiring.md

Add the smallest useful new module/test, e.g. src/backtest_badger/genuine_minute_verification_wiring.py and tests/test_genuine_minute_verification_wiring.py, or another clear implementation with no duplication. Changes to the existing operator should only be made when necessary to provide a safely testable pure internal seam; preserve all existing fail-closed behavior. Update only docs/architecture.md, docs/roadmap.md, docs/development-handoff.md among existing overview documents unless you report a blocker. Do not modify the approved frozen methodology, acquisition records or source pins, existing loaders, audits, replay engines, accounting or earlier tests to make new tests pass. Do not modify package dependencies or generate files in repository artifacts/.

The implementation guide must include:
- Exact clean starting SHA and baseline CI evidence.
- The precise API, its non-executing contract and whether public gates remain closed.
- Production-loader bindings and how they're isolated from fabricated injected tests.
- A non-executable evidence-readiness checklist with unknown values clearly listed; no apparently approved genuine invocation payload.
- Full known independent hashes and 57-file source-inventory rules; proposed exact named destination with uninspected status.
- Provenance and publication guarantees and limitations, including why source equality is not fillability or economic validation.
- Exact executed focused/full test counts and exits, Ruff and preservation results, failure cases and skipped DB cases.
- List of changed/new files and the precise next owner approval gates.
- A safe future operator procedure as a proposed design only, not a runnable genuine command under current authorisation.
Archive this substantive prompt in the suggested prompts/stage-04-paper/011-genuine-verification-wiring.md and exclude any unrelated pasted browser/session metadata. Keep it complete and reviewable; don't append tool logs, private environment values or secrets.
8. Hard stop and completion response
No commit, push, deployment or genuine-source access under this authorisation. Do not call the disabled public genuine functions except in tests asserting immediate refusal. Do not create or inspect artifacts/audits/stage-04b2d3-minute-inputs-v1/ or any other genuine artifact. Do not run any historical trading/economic simulation. Do not automatically advance to a genuine verification run, a genuine replay boundary, or economic result publication.

Stop and ask for owner review if you discover a need to weaken a frozen guard, modify an already frozen loader/protocol, use original artifacts to discover missing identities, or change the reviewed research assumptions. Explicit owner approval for one future read-only genuine verification run is a separate decision, taken only after review, a clean commit and green CI for the genuine-ready implementation and complete independent approval evidence. Authorisation for genuine strategy execution and economic publication remains a later separate gate.

In your final report: give actual Git status/HEAD, exact changed files, public/private API, the closed-gate proof, complete known-vs-missing approval evidence, actual focused/full test counts, Ruff, protected inventory, any failures, resource limits, and the next separate approval requirements. If incomplete, identify the exact blocker rather than filling gaps. Stop before committing or pushing.

Suggested conventional commit message after owner review:

feat(research): prepare genuine minute verification wiring

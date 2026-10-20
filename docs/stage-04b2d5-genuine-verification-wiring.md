# Stage 4B.2D.5 — Verification bindings and approval preparation

**NOT_APPROVED / NOT_READY / NO_SOURCE_ACCESS.** Implementation and fabricated
testing only, prepared on 2026-10-20 (Europe/London), with final validation and
owner-review completion on 2026-10-21. Both public genuine entry
points remain unconditional refusals before argument inspection. No production
approval, enabled wrapper, invocation command, CLI or dispatch function is added.
Stop for owner review.

Starting checkout: clean `main`,
`550d457aef42b08a2933a701136266d31da082b5`. Local HEAD, branch, tracked status,
nonignored untracked paths and baseline blob contents were independently checked
without traversing `artifacts/`. The owner reports GitHub Actions run
`39473129809` completed successfully for that SHA (1,999 passed; 1 skipped).
GitHub was unavailable to this task under its explicit no-network scope; that
CI statement was **not independently verified** here. It cannot approve changed
wiring or a future invocation. No CI was queried or triggered.

## API and concrete existing seam

New module: `src/backtest_badger/genuine_minute_verification_wiring.py`.

```python
verification_plan() -> VerificationPlan
approval_readiness(*, minute_pin_document: bytes | None = None) -> Readiness
```

`verification_plan()` returns immutable symbolic bindings, the three relative
root declarations, sole proposed destination, exact proposed implementation
allowlist, required verification flags, result type and ordered publication
phases. All call targets and arguments are strings, never resolved callables.
There is no callable production runner, environment switch or `allow_genuine`.
The module imports only standard-library dataclasses/hashlib at import time.
The default APIs need no project imports, filesystem queries, Git, CI or runtime
observations. Paths are declarations, never resolved or inspected.

`approval_readiness()` is the explicitly permitted **template**, not a validator
or issuer of executable approvals. It accepts no candidate inventory, runtime,
CI claim, owner signature, destination or source path. It always reports
`NOT_APPROVED`, `NOT_READY`, `NO_SOURCE_ACCESS`; the statuses are non-init frozen
fields. Missing required evidence remains explicit even when all tracked
declarations are available. Changing a Python record is not an authorisation.

Optionally supply already-read **tracked minute pin document bytes**. The helper
checks their SHA-256 against the literal frozen declaration before importing and
reusing the existing pure `genuine_minute_price_parity._minute_pins` table parser.
It does not import the verification operator. It never opens a path. The supplied
document yields the existing ordered 24 ZIP/sidecar hash/size/count/URL/receipt
rows and 48 source-file identities. Without it, those entries retain explicit
unknown values and a reference to their authoritative document row. No arbitrary
replacement document, parser callback or caller-supplied hash is accepted.
This read of tracked documentation is not authentication of archive bytes.

The unchanged internal callable boundary remains
`genuine_minute_verification_operator._verify_sources`, reached in operation only
through the existing guarded `_run_fixture_verification` test seam. No new
private execution API is needed. The new tests verify the declared targets and
signatures against that seam, exercise its callbacks with fabricated forecasts
and explicitly injected minute metadata, and retain the old full-native tests.
The old operator and authentication modules remain byte-for-byte unchanged.

Future, separately reviewed source code must bind precisely:

```python
forecast_data.load_forecasts(approved_forecast_root)
paper_historical_evaluation._validate_lineage(original_forecast_manifest)
minute_execution_data.load_minute_execution_data(
    approved_minute_root,
    expected_manifest_sha256=(
        "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127"
    ),
)
```

These are declarations, not a runnable invocation procedure. No forecast default
pin override and no Stage 4B.2D.2 TEST lineage translation belongs in that future
path. The minute loader returns metadata only. Then the existing
`genuine_minute_inputs._stream_projection` must check all 1,054,080 native rows
against the original processed hash and 107,002,277-byte length and retain only
21,958 references. `_parity_evidence` must validate the original five-file
publication in the actual auditor schema; never rerun the audit.

The future result remains `AuthenticatedMinuteInputs` with
`genuine_execution_authorised=False`. It is not a `PreparedMinuteBundle` or
`SyntheticPriceSource`. No genuine replay boundary or economic calculation is
implemented.

### What still needs a separately reviewed source change

The existing `_validate_approval`, `_code_snapshot`, `_source_snapshot`,
`_verify_sources`, `_operate_fixture` and publisher collectively demonstrate the
required operations, but their current paths/schema/source kind are intentionally
fixture-specific. This plan does **not** make them a genuine runner.
The later source change must add exact approved-root binding and externally pinned
genuine preflight, carry the original source kind through scientific/operational
crosschecks, and reuse the existing authentication/publication operations.
If that requires extracting a shared private core, review that narrow change
separately while preserving the fixture restriction and testing both boundaries.
Do not merely remove temporary-root checks or relabel fixture outputs.
There is no production-enable commit or CI identity to freeze today.

## Known declarations and exact future inventory

All hashes below are independent declarations from the request and tracked frozen
records. They were not obtained by opening, hashing or inspecting originals.

| Declaration | Frozen SHA-256 |
| --- | --- |
| `forecast_manifest` | `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581` |
| `forecast_csv` | `e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674` |
| `research_manifest` | `a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e` |
| `research_csv` | `04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8` |
| `hourly_manifest` | `1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d` |
| `hourly_csv` | `39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a` |
| `hourly_acquisition` | `926697a89eb7c018ca5913f1e3c4c1170715db5639d444a58a78012e92aec055` |
| `minute_manifest` | `673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127` |
| `minute_csv` | `37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233` |
| `parity_manifest` | `53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d` |
| `parity_report` | `0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb` |
| `parity_provenance` | `fb44c49bf468ca976706567f7997ff61cdfe3f5157eca387c796b73fba0556eb` |
| `parity_integrity` | `5594e11f44cbc0e820595501a508b47f6f7b55508de3c2895c7b6ae6e64ab395` |
| `parity_discrepancies` | `0afb86f6389a1ab6a6931f0a96bd3ef0484bbd172f8bcd8b2fc7b8e9dea4a755` |
| `minute_pin_document` | `967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c` |
| `hourly_protocol` | `b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b` |
| `minute_protocol` | `c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b` |

The 14 keys shared with `genuine_minute_inputs.EXTERNAL_PINS` remain identical.
The three additional prior-publication hashes bind provenance, integrity and
discrepancy bytes independently as required by this stage.

Exactly 57 future source files, no discovery or wildcard authority:

| Group and relative root | Exact allowed files | Known lengths |
| --- | --- | --- |
| `forecast`: `artifacts/experiments/stage-2b-v1/` | `manifest.json`, `validation_predictions.csv`; named reads only, never enumerate this root | Both **unknown** |
| `minute`: `artifacts/execution/binance-1m-2024-v1/` | `manifest.json`, `minute_opens.csv`, `raw/{BTCUSDT,ETHUSDT}-1m-2024-{01..12}.zip` and each `.zip.CHECKSUM` | 19,749; 107,002,277; each ZIP/sidecar length in frozen table |
| `parity`: `artifacts/audits/stage-04b2d1-native-parity-v1/` | `manifest.json`, `parity_report.json`, `provenance.json`, `integrity.json`, `discrepancies.csv` | 740; 18,452; 60,610; 61,684; 162 |

The month notation describes an exact enumerated set, not a runtime glob:
BTCUSDT January–December, then ETHUSDT January–December. The immutable checklist
enumerates every name. All 48 full hashes and lengths, 24 expanded native CSV
lengths and row counts, URLs and retrospective receipts are already declared in
the unchanged [minute source-pin document](stage-04b2c-minute-source-pins.md).
Its two exact tables are authoritative; no copy or new parser is maintained.
ZIP sizes sum to 49,948,389 bytes; sidecars sum to 2,112 bytes. Leap February has
41,760 rows per market. The source-pin document also supplies the previously
known 19,749-byte minute manifest length. No forecast length is guessed.

The independently declared 24 hourly ZIP hashes remain in
`paper_historical_evaluation.MONTHLY_ZIP_SHA256`. Retain them externally together
with the **complete original auditor implementation mapping**. Some prior code
identities are recorded in the [parity guide](stage-04b2d1-genuine-price-parity-audit.md),
including auditor SHA-256
`d4b3fb3f9f06b553fce0f1303a61bc4483feb2d90840573c9c33ac9e5523d092`.
Do not substitute freshly computed current code hashes for missing historical
audit evidence. Research and hourly releases are declarations/provenance, **not
additional input roots**. No research, labels, holdouts or hourly sources may be
opened under the proposed 57-file scope.

The sole proposed future output is
`artifacts/audits/stage-04b2d3-minute-inputs-v1/`. Its existence, absence, symlink
state and ignore status are **uninspected**. Nothing there has been reserved or
created. A future approval must identify its exact absolute path within the
approved checkout; expressly authorised preflight must then check it.
The prior parity output cannot be reused or overwritten.

## Missing evidence and eventual one-attempt schema

This is a human review checklist, not a valid-looking invocation payload.
Neither the template nor local candidate bytes can resolve the following gates.

| Required eventual field/evidence | Known now / still required |
| --- | --- |
| `commit`, clean checkout | Baseline known; full clean reviewed **genuine-enabled future** SHA unknown |
| `ci` | Independently check exact matching SHA, run ID, `completed` / `success`; retain evidence after future code review/commit |
| `implementation` | Exact proposed allowlist is `IMPLEMENTATION_FILES`; independently retain SHA-256 **and byte length** for every code/document/config file at the reviewed future revision |
| Import closure | New AST regression covers all transitive project imports including lazy parser import and package initialisation; revalidate closure when future wiring changes |
| `runtime` | Freeze exact Python version/implementation and installed alembic, numpy, psycopg, psycopg-binary, scikit-learn, scipy, SQLAlchemy, joblib, threadpoolctl versions at the future run boundary; no ranges or invented current pins |
| `roots`, `input_inventory` | Three exact absolute roots and all 57 independent hashes/lengths; two forecast lengths unresolved; externally retain the complete inventory before source access |
| `monthly_sources` | Independently retain ordered ZIP/sidecar hashes, lengths, URLs, monthly/expanded byte counts, complete UTC grids and retrospective receipts from the pinned document |
| `hourly_monthly`, `audit_code` | Independently retain all 24 original hourly ZIP hashes and complete prior-auditor code identities, matching prior provenance |
| `pins` | Original `EXTERNAL_PINS`, frozen protocol/source-document hashes and extra parity hashes above; no substitutions or fallback |
| `source_kind` | Proposed `genuine_retained_stage2b_native_minute_prior_parity`; never fixture status |
| `destination` | Exact absolute approved previously absent destination; ignore/no-symlink state requires later expressly approved preflight |
| Strict flags | `verification_only=True`, `single_attempt=True`; `resume=False`, `strategy_authorised=False`, `economic_publication_authorised=False` |
| Owner authorisation | Clear externally retained permission for **one** read-only invocation, granted after review/commit and green CI for enabled code; no standing approval or retries |

The proposed code allowlist includes the new wiring/guide, old operator,
authentication primitives, every transitive project import, frozen documents,
`AGENTS.md`, `.python-version`, CI configuration, `pyproject.toml` and `uv.lock`.
Current local preservation hashes are review evidence only, not run authority.
The future complete approval must be validated and detached before source access;
missing/extra fields/files, hash/length mismatches, changed code/documents,
dirty/stale revision/CI/runtime, source associations, ambiguous receipts,
wrong kind/flags, traversal and symlinks must fail closed.

## Proposed future procedure and retained publication guarantees

Only after the separate gates above:

1. Validate/detach complete external approval. Check code/config/document and
   runtime identities, clean exact revision, CI evidence and owner scope.
2. Check all approved path components and exact destination absence without
   following symlinks. Atomically reserve the **sole** destination, consuming the
   attempt **before source file opens**. No retry/resume/alternate output.
3. Hash only the two named forecast files; never enumerate that root. Require
   exact complete minute/parity inventories and all external hashes/lengths before
   trusting bytes. Do not discover missing pins from these candidate files.
4. Run original forecast/lineage/minute bindings, full bounded projection and
   original publication validation. Preserve whole-manifest/train-only lineage,
   all eight accounts × 2,195 forecasts, exact Decimals and all required horizons.
5. Recheck source bytes/stats, code/document identities and environment. Exclusively
   write/fsync/read back `authenticated_inputs.json` then `integrity.json`.
   Scientific bytes are deterministic; operational stats/approval remain separate.
6. Recheck preservation after readback and before publishing `manifest.json` last.
   Require exact hashes/lengths and three-file success inventory, no unknown files
   or `.partial` files, `kind=source_authentication_only`, `economic_results=false`
   and `genuine_execution_authorised=false`. Independently read back the manifest
   and repeat final source/code/environment preservation.
7. On failure retain forensic partial evidence; invalidate only the manifest
   inode owned by this attempt. Preserve alien collisions. Safe failure evidence
   records controlled phase/class only, no exception text, paths, secrets or rows.
   Never remove somebody else's directory or silently repair/resume.

Availability remains source opening +4h+60s, with strictly next-minute references
(`12:01 -> 12:02`), including potential HOLD/CASH_NOOP horizons. Source openings
span 2023-12-31 20:00 to 2024-12-31 12:00; last availability/reference is 16:01/16:02.
Per market retain 8,784 hourly marks + 2,195 forecast references = 10,979.
No December 31 20:01 signal, 2025 price or strategy decision is manufactured.
The prior actual-schema evidence must establish exactly 17,568 equality pairs,
all market/month counts, zero discrepancies and complete linked provenance.
Its timing flag grants no strategy/evaluation permission.

Archived open equality is not contemporaneous availability, quote depth,
fillability, economic validation or independent out-of-sample evidence. Checksums
are unsigned; receipts are retrospective. Before/after preservation detects
observed mutations, not coordinated hostile replace/restore races. Frozen Python
records are not capabilities against hostile code. Hard kills, storage failures
and filesystem races can defeat cleanup or failure recording; no transactionality
or guaranteed success-marker invalidation is claimed.

## Local validation and preservation

The process guard is installed before pytest collection. It blocks underlying
opens/listing and stat/lstat of genuine artifacts and the sibling repository,
sockets/DNS and PostgreSQL. Existing test fixtures additionally block genuine
audit/replay/economics/provider boundaries, while existing synthetic mechanics
tests retain their fabricated inputs. Forbidden operations are actually exercised
against the guards. No guard was weakened. Collection is explicitly `tests/`,
with a fresh user-owned temporary base and locked/offline/no-sync dependencies.
Unconfigured PostgreSQL tests are skips, never passes.

The new seam test uses actual fabricated forecast bytes and the unchanged
forecast/lineage validators, but **injected metadata/projection/parity**; it does
not claim archive authentication. Existing operator tests separately exercise
all 24 fabricated ZIP/sidecar native reconstructions, full-year projection,
actual auditor schema, deterministic science across copies, exclusive publisher
and all reservation/mutation/fsync/link/readback/manifest fault phases.
Existing authentication tests cover the full projector's 32-MiB tracemalloc bound.
No second million-row dataset was added by the new tests.

Actual local results (all reported commands completed with exit **0**):

| Check | Result |
| --- | --- |
| Initial new tests, before the final two safety cases | 38 passed in 0.31s |
| Earlier combined focused selection | 173 passed in 85.39s |
| Final combined focused selection, including all 40 new cases | **175 passed in 84.07s** |
| Final locked offline full suite | **1,857 passed, 183 skipped in 382.10s (0:06:22)**; no failures |
| Ruff lint and formatting, reconfirmed at completion | Both passed for the explicit **90-file** Python inventory |
| Protected tracked files | All **181** match both the retained pre-edit SHA-256 inventory and baseline Git blobs |
| Whitespace | `git diff --check`, `git diff --cached --check`, and explicit whitespace/final-newline checks for all four new files passed |
| Substantive prompt archive | Exact byte-for-byte match to the supplied substantive request; existing archive confirmed before any resumed edits |

The final full-suite process was already running when the previous session ended.
On 2026-10-21 its captured execution-session log (session **18350**) was recovered:
it contains the summary above, `PYTEST_EXIT=0`, and the completed process returned
exit **0**, with no pytest cleanup errors. This confirms normal pytest cleanup
and process shutdown; it does not claim every temporary fixture was deleted.
There was no separately redirected log file. The verified full suite was not
rerun. All 183 skips were unconfigured PostgreSQL integration cases requiring
`BADGER_TEST_ADMIN_DSN`; no database integration pass is claimed.
Only this guide's validation record changed during completion; tested Python
implementation and tests were preserved. No test or lint failure occurred.

Final permission-boundary review found no source discovery, callable dispatch,
approval bypass or acceptance of incomplete evidence in the new APIs. The tests
cover cold-module/default-API I/O refusal, frozen-document hash checking before
parsing, malicious approval objects, rejection of readiness/plan records and
their dictionary representations, and 39 process-level forbidden operations
blocked before access. Both existing public entry points still immediately raise
`PermissionError`; neither approval payload inspection nor filesystem work
precedes that refusal. Existing private fixture seams remain unchanged.

Readiness remains **NOT_APPROVED / NOT_READY / NO_SOURCE_ACCESS** in both modes.
Without tracked pin-document bytes, 48 monthly hashes and lengths remain unknown
and 15 missing-evidence obligations are listed. With the exact frozen tracked
document, the declarations contain all 57 source hashes and 55 lengths, plus
24 monthly associations, but still list 14 obligations. The two original forecast
lengths remain `None`. These declarations do not independently authenticate any
source, satisfy runtime/code/CI/owner evidence, or enable an invocation.

The final focused selection is the new wiring test module plus the unchanged
operator test module. The full selection is explicitly `tests`. Executed runner:

```sh
env PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  uv --cache-dir /private/tmp/badger-4b2d5-uv-cache \
  run --locked --offline --no-sync python -u - <<'PY'
import runpy, sys, tempfile
from pathlib import Path

runpy.run_path('tests/test_genuine_minute_inputs.py')['install_offline_audit']()
import pytest

base = Path(tempfile.mkdtemp(prefix='badger-4b2d5-full-')).resolve() / 'suite'
result = pytest.main([
    '-q', '--rootdir=tests', '--confcutdir=tests', f'--basetemp={base}',
    'tests', '-p', 'no:cacheprovider',
])
print(f'PYTEST_EXIT={result}', flush=True)
sys.exit(result)
PY
```

Focused runs use the same runner with fresh named temporary bases and replace
`'tests'` with `'tests/test_genuine_minute_verification_wiring.py'` and
`'tests/test_genuine_minute_verification_operator.py'`. Ruff `check --no-cache`
and `format --check --no-cache` receive the explicit Git-tracked Python filename
list plus the two new Python files, never automatic repository discovery.
Whitespace validation runs both Git diff checks and explicit new-file trailing
whitespace/final-newline checks. The substantive prompt is compared byte-for-byte
against the attachment prefix through the suggested commit message.

Pre-edit inventory: **181** protected tracked files, excluding only the three
permitted overview documents. Canonical mapping SHA-256:
`4985b559d4c07a79a680cf8da347a76adaa41380f8c7a0bef423de994427edfe`.
Reproduce it from the starting Git blobs as a sorted compact JSON mapping of
repository-relative filenames to SHA-256 strings, followed by one newline,
excluding `docs/architecture.md`, `docs/roadmap.md`, `docs/development-handoff.md`
and any `artifacts/` names. No artifact is traversed or inventoried.

New files:

- `src/backtest_badger/genuine_minute_verification_wiring.py`
- `tests/test_genuine_minute_verification_wiring.py`
- `docs/stage-04b2d5-genuine-verification-wiring.md`
- `prompts/stage-04-paper/011-genuine-verification-wiring.md`

Modified existing files: only `docs/architecture.md`, `docs/roadmap.md`,
`docs/development-handoff.md`. All previous code/tests/protocols/pins,
dependencies/configuration and earlier guides remain unchanged.
The prompt archive contains the complete substantive request through the
suggested commit message; unrelated browser/session metadata is excluded.
Final Git state is `main` at the unchanged starting SHA, with three modified
tracked overview documents and four new untracked files, nothing staged.
The earlier six-file visible summary omitted the already-present prompt archive;
the actual seven-file change inventory above includes it.

## Next owner gates

Review this uncommitted plan/template and fabricated test evidence first.
Separately authorise the narrow genuine-enabled source change described above,
review/commit it and obtain green CI for that exact SHA. Complete independent
evidence retention, including original forecast lengths and run-specific identities.
Only then consider one explicit read-only verification invocation and its exact
fresh output. Nothing in this stage grants that invocation.

A later genuine replay boundary, actual historical strategy execution and
economic reproduction/publication require further distinct approvals.
No commit, push, deployment, genuine verification, genuine backtest or source
access occurred here. Stop at owner review.

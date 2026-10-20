# Stage 4B.2D.4 — Closed one-use verification operator

Implementation and fabricated tests only, awaiting owner/code review.
Initial clean `main` and final HEAD:
`925f9abe2ec21fffc937df86e9283ad63e09aac4`.
Baseline CI run `39379366971` is owner-supplied context; it is not CI evidence
for these uncommitted changes. No commit, push, deployment or Stage 4B.2E work.
No original artifact was opened, listed, statted, hashed or inventoried.

The [archived request](../prompts/stage-04-paper/010-genuine-minute-verification-operator.md)
contains only the substantive instruction through the suggested commit message.
The attachment's unrelated browser/session tail is excluded.

## Interfaces and inactive authority

New module:
[genuine_minute_verification_operator.py](../src/backtest_badger/genuine_minute_verification_operator.py).

```python
run_genuine_minute_verification(*, approval) -> AuthenticatedMinuteInputs

_run_fixture_verification(
    *, fixture_root, approval, forecast_loader, minute_loader,
    lineage_validator, environment_reader, native_loader_evidence,
) -> AuthenticatedMinuteInputs
```

The public function **always raises PermissionError before inspecting approval**,
including malicious objects and apparently complete records. The old
`genuine_minute_inputs.authenticate_minute_inputs(*, approval)` remains unchanged
and equally closed. No CLI, `__main__`, switch, environment override, approval
file, permissive callback or default loader binding can activate either function.

The private entry point accepts only isolated temporary roots, invented external
source pins and explicit test bindings. Its roots are exactly `forecast/`,
`minute/`, `parity/`, `code/` and a previously absent `output/`. The private
`_operate_fixture` orchestrates verification and publication; `_verify_sources`
uses the unchanged validation helpers, and `_publish` implements exclusive writes.
Neither the old fixture harness nor any old source module was changed.

The resulting frozen `AuthenticatedMinuteInputs` has false execution authority.
It is a verification record, not a portfolio or capability token. All newly
created evidence retains `source_kind=fabricated_temporary_fixture_bytes`.
The embedded parity report uses the real auditor's schema, including its original
authentication field; that is a **fabricated prior-audit claim**, explicitly
enclosed in fixture provenance, not a new genuine audit.

Production wiring remains inactive and unapproved. A later reviewed source
change must bind the real roots, externally frozen operational pins and literal
loader calls; this is not achievable by supplying approval to today's public
function. The temporary entry point must never be repurposed to accept genuine
paths or convert synthetic evidence into a genuine claim. Python code can replace
private functions or construct records; this module is not a hostile-code sandbox.

## Required future approval — declaration only

There is no accepted genuine approval payload in this stage. The strict TEST
approval schema (`minute-input-verification-approval-v1`) demonstrates mandatory
fields for the future independently reviewed payload:

| Field | Required declaration |
| --- | --- |
| `commit` | Full 40-character clean reviewed Git SHA |
| `ci` | Matching SHA, exact run ID, completed status and success conclusion, retained independently |
| `runtime` | Exact Python version/implementation and every critical dependency version |
| `implementation` | Exact relative file inventory, external SHA-256 and byte length for each file |
| `roots`, `destination` | Exact absolute roots and sole destination, never discovered |
| `input_inventory` | Exactly 2 named forecast, 50 minute and 5 parity files, each with external SHA-256/length |
| `pins` | Complete original external pin mapping, including unopened research/hourly declarations |
| `monthly_sources` | Ordered 24 market/month ZIP/sidecar hashes, sizes, URLs, expanded sizes, counts and receipts |
| `hourly_monthly`, `audit_code` | Independently retained prior-audit monthly and implementation identities |
| `verification_only`, `single_attempt` | Strict booleans, both true |
| `strategy_authorised`, `economic_publication_authorised`, `resume` | Strict booleans, all false |
| `source_kind`, `schema` | Explicit provenance and version; TEST fixture status is never a genuine approval |

The code allowlist includes this operator, authentication primitives, transitive
project imports (including package initialization), frozen documents,
`pyproject.toml` and `uv.lock`. An AST test checks project-import closure.
Runtime fields explicitly cover Python and Alembic, NumPy, psycopg/binary,
scikit-learn, SciPy, SQLAlchemy, joblib and threadpoolctl. They are not silently
filled from currently observed files. `_read_environment(checkout)` can inspect
local Git/runtime state; the fixture tests inject invented commit/CI/version
observations. A success string alone is not independently fetched CI evidence:
the future owner must freeze and verify that evidence before authorising access.

The only proposed future roots are:

1. `artifacts/experiments/stage-2b-v1/`: only `manifest.json` and
   `validation_predictions.csv`; never enumerate the directory.
2. `artifacts/execution/binance-1m-2024-v1/`: manifest, processed CSV and
   the exact 24 ZIPs plus 24 checksum sidecars.
3. `artifacts/audits/stage-04b2d1-native-parity-v1/`: exactly `manifest.json`,
   `parity_report.json`, `provenance.json`, `integrity.json`, `discrepancies.csv`.

The only proposed future output is
`artifacts/audits/stage-04b2d3-minute-inputs-v1/`. Its existence, absence and ignored
status have **not** been inspected; it has not been created or reserved.
The previous parity destination must never be reused for this publication.

Source pins originate from the owner request, the unchanged
`genuine_minute_inputs.EXTERNAL_PINS`, the
[minute pin document](stage-04b2c-minute-source-pins.md), and the
[completed parity guide](stage-04b2d1-genuine-price-parity-audit.md).
The minute pin document's already-declared SHA-256 was verified before reading
its monthly tables:
`967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c`.
Both protocol document pins also matched. The full original minute CSV identity
remains 107,002,277 bytes,
`37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233`.
No declarations were learned from original source bytes.

Future operator/code/configuration/runtime identities must be frozen externally
after implementation review and CI. Unknown original file lengths must be supplied
from separately approved retained records, never filled by blessing the candidate
files. The current test hashes and invented CI record are not production approval.
The future wiring must use precisely:

```python
forecast_data.load_forecasts(approved_forecast_root)
paper_historical_evaluation._validate_lineage(original_manifest)
minute_execution_data.load_minute_execution_data(
    approved_minute_root,
    expected_manifest_sha256=(
        "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127"
    ),
)
```

This is an unexecuted binding specification, not an operator command.
The proposed future invocation is
`run_genuine_minute_verification(approval=externally_reviewed_one_use_payload)`,
only after that source change and a separately granted exact one-attempt approval.
That call is guaranteed to refuse in the present implementation. No approval
payload has been issued and no invocation script or CLI has been created.
Hourly source archives, research files/labels, holdouts, Stage 3, other artifacts,
the sibling repository, network/providers, databases and production stay excluded.

## Event order and one-use publication

1. Lexically reject non-temporary roots, traversal and genuine external identities
   in the test seam. Validate and detach the complete supplied approval.
2. Check root/directory components for symlinks; require an absent destination
   with `lstat`, including refusal of broken symlinks. Verify reviewed Git/runtime
   state and independently pinned code/document hashes and lengths. No source
   file opens occur during this preflight.
3. Open the checked parent directory; atomically `mkdir` the sole destination
   without `exist_ok`. That reservation consumes the attempt. A race losing to an
   existing directory fails without mutation. No alternate destination or retry.
4. Require exact minute and parity inventories; hash all 57 allowed source files,
   recording bytes/device/inode/mtime/ctime. Forecast access is named-file-only.
   Compare against the independent complete inventory before parsing.
5. Validate original forecast and minute manifests; run unchanged lineage policy
   without synthetic hash translation; parse forecasts with the unchanged loader.
   Run the bound native loader, stream the complete projection, validate the
   separately pinned five-file prior parity publication without rerunning it.
6. Recheck every allowed source/code identity, stats and clean runtime/revision.
   Build the immutable scientific record and separate operational integrity.
7. Publish `authenticated_inputs.json` then `integrity.json` exclusively. Each
   uses `O_EXCL|O_NOFOLLOW` `.partial` creation, flush/fsync, an exclusive hard
   link, partial unlink and directory fsync. Writes are anchored to the reserved
   directory descriptor. Check the reserved path's device/inode at every phase.
8. Independently read back bytes with safe opens, reparse canonical JSON, verify
   exact lengths/hashes/inventory and cross-check science/integrity against the
   detached approval, original source inventory and code evidence.
9. Recheck all sources/code/environment after readback and immediately before
   publishing the manifest. Write `manifest.json` last with the exact two-file
   inventory, lengths/hashes, `kind=source_authentication_only`,
   `economic_results=false`, `genuine_execution_authorised=false`. Independently
   read back the entire publication and recheck preservation once more.
10. On any caught post-reservation exception, invalidate only this attempt's
    owned manifest inode and retain best-effort `failure.json`. It records a
    controlled phase, safe exception category, `complete=false`, `resume=false`;
    no exception message, file contents, private paths or arbitrary class names.
    Other files/partials remain for forensics. Never overwrite an existing attempt.

Success requires the exact final three-file inventory, no failure/partial files,
valid canonical bytes and all manifest links. A filename or a `complete` flag
alone is insufficient. Collision files belonging to another writer are preserved;
the failed directory is not successful evidence. Directory ownership/permissions,
read-only originals and frozen other writers remain operational prerequisites.

Disk errors, process death or descriptor exhaustion can prevent failure recording
or final invalidation; failures remain errors, never automatic repair/resume.
A hard kill can leave a partial/link combination. No incomplete directory can be
considered a successful publication. The manifest is the commit marker only after
the required validation has completed. This is not a transactional guarantee
against hostile mutation of the filesystem or coordinated replace/restore races.
The unchanged source loaders use their existing path APIs; additional before/after
checks detect observed changes but do not turn those loaders into an OS sandbox.

## Scientific invariants and reproducibility

All eight model/account identities retain 2,195 chronologically fixed forecasts.
Ridge predictions remain exact Decimals, preserving original record IDs, full
manifest recipe/scaler lineage, canonical source opens and +4h+60s availability.
These are collections of forecast identities, not funded trading accounts.
No refitting, forecast regeneration, label reads or strategy decisions occur.

The bounded projector checks all 1,054,080 native rows, including leap February,
their exact UTC/source association, positive fixed-point open, CSV identity and
EOF. It retains 8,784 HH:00 and 2,195 next-minute references per market:
10,979 each, 21,958 total. The unchanged existing allocation test enforces a
32-MiB peak for the projector. Source identity is distinct from projection hashes.

Prior parity uses the actual genuine auditor schema, all 17,568 equal HH:00 pairs,
all market/month counts, zero discrepancies/structural errors, linked original
source identities and complete retained before/after integrity. Price parity is
not trading authority, contemporaneous availability or fillability evidence.

Scientific JSON includes immutable forecasts/references, full source provenance,
hashes and limitations. It excludes this run's destination, wall clock, filesystem
stats, session data and approval identity. The old scientific serializer's canonical
spacing is preserved. The prior parity publication is retained byte-identically;
its hash is an input identity, not recomputed for a new filesystem copy.
Operational integrity includes the exact approval and source/code stat snapshots.
Identical scientific input bytes on different temporary roots produce identical
scientific output; operational and final-manifest hashes may differ.

## Fabricated validation and preservation

Tests use fresh user-owned pytest roots, the locked installed offline environment
and no downloads or dependency installations. Process audit hooks block genuine
artifact opens/listing, sibling paths, sockets/DNS and PostgreSQL; actual stat/lstat
wrappers cover operations without CPython audit events. Function tests block
audit reruns, replay, strategy, funding, trades and valuation. Forbidden operations
are executed against the guards, so the boundary is tested rather than asserted.

Two end-to-end successes exercise the unchanged forecast parser, unchanged lineage
policy with invented module constants, **actual native loader revalidation of all
24 fabricated ZIP/checksum pairs**, the full-year bounded projection, genuine-auditor
schema validation, preservation and the production publication mechanics.
The second uses copied sources under a different root and compares scientific bytes.
Invented code/CI/runtime fixtures test the approval contract; they do not authenticate
the executing process as a reviewed production build.

Publisher fault tests explicitly inject the previously verified immutable fixture
record at `_verify_sources`. They exercise actual reservation, source/code rechecks,
exclusive writes, readback, manifest and failure handling without repeatedly scanning
the million-row grid. They are publisher tests, not additional native authentications.
The earlier authentication/native-loader/parity/replay/integration suites remain
unchanged and cover detailed lineage, malformed CSV, stream and parity tampering.

Development failures are recorded here; executed validation counts follow below.
The first collection failed because pytest introspected the malicious object before
the test; construction was moved inside the test. The first native success attempt
correctly failed readback because it used compact JSON to check the existing spaced
scientific serializer; readback now applies the appropriate canonical serializer.
A test guard initially named `apply_trade` in the wrong module; the guard was fixed.

Before editing, 177 protected tracked non-artifact files were SHA-256 inventoried.
Only the three allowed existing architecture/roadmap/handoff files are excluded.
The final preservation check compares both that inventory and the initial Git blobs.
No source artifact inventory forms part of that check.

The canonical protected-inventory SHA-256 is
`f95f07fe44d8c8a476f94bf5538526c4e0931390fd37293e688c65f39d2e126f`.
It hashes the sorted compact JSON mapping of relative filenames to SHA-256 strings,
plus a final newline, reconstructible from the initial Git revision excluding the
three permitted existing documentation edits and any `artifacts/` paths.

Current implementation SHA-256:
`c693d5e11648619719402a62ab2fe94d69c547e04463877c0dfd9a8b3442f70e`.
Current test SHA-256:
`a5ec4cc076416e6aa2fbbabe7cdb092037ab75995efc68c57cba404fade304a4`.
These identify the local review candidates; they do not approve production wiring
or replace the future externally frozen complete implementation pin inventory.

## Validation commands

The final focused command selects
`tests/test_genuine_minute_verification_operator.py`; the full command selects
`tests`. Both use the same pre-collection process guard and fresh user-owned base:

```sh
env PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  uv --cache-dir /private/tmp/badger-4b2d4-uv-cache \
  run --locked --offline --no-sync python -u - <<'PYTEST'
import runpy
import sys
import tempfile
from pathlib import Path

runpy.run_path('tests/test_genuine_minute_inputs.py')['install_offline_audit']()
import pytest

base = Path(tempfile.mkdtemp(prefix='badger-4b2d4-validation-')).resolve() / 'suite'
sys.exit(pytest.main([
    '-q', '--rootdir=tests', '--confcutdir=tests', f'--basetemp={base}',
    'tests', '-p', 'no:cacheprovider',
]))
PYTEST
```

Ruff check and format-check use an explicit inventory of all tracked Python files
plus the two new Python files, avoiding discovery under ignored artifact roots.
Tracked/staged `git diff --check` is supplemented with explicit trailing-whitespace
and final-newline checks on all four new files. Source preservation compares all
177 protected hashes to the saved pre-edit mapping and the initial Git blobs.
The prompt archive is compared to the attachment only through its substantive
suggested commit message, without rereading the unrelated trailing material.

## Final executed results and owner-review handoff

Final validation completed on 2026-10-20 (Europe/London). The resumed handoff
recovered the existing final full-suite process output and **actual exit status 0**;
it did not rerun the expensive fabricated-source tests. The usage interruption
delayed reporting, not completion of that test process.

| Check | Observed result |
| --- | --- |
| Initial collection | Failed during pytest introspection of the malicious approval fixture; corrected |
| First end-to-end attempt | Failed canonical readback; retained incomplete evidence, no success manifest; corrected serializer check |
| Next test setup | Failed on an incorrectly located `apply_trade` guard; corrected |
| Earlier focused suite | 128 passed in 80.68s, exit 0 |
| Earlier full suite | 1,816 passed, 183 skipped in 385.08s, exit 0; preceded the final document-pin linkage check |
| Final focused suite | **135 passed in 89.29s, exit 0** |
| Final locked offline full suite | **1,817 passed, 183 skipped in 385.11s, exit 0** |
| Ruff, reconfirmed during handoff | Check passed; all **88** tracked/new Python files formatted |
| Protected-file preservation, reconfirmed | All **177** files match both the saved pre-edit SHA-256 inventory and baseline Git blobs |
| Whitespace | Tracked/staged checks and explicit new-file checks passed |
| Published validation command | Shell syntax checked with `sh -n`; embedded Python parsed successfully; original offline guard and locked/no-sync options retained |
| Archived request | Exact substantive-prefix comparison passed; unrelated attachment tail excluded |

All 183 skips require `BADGER_TEST_ADMIN_DSN` for a disposable local PostgreSQL
server. The process guard removes that setting and forbids connections. These
tests were **not executed**, and no database was accessed. The final full suite
includes the unchanged native-loader, authentication, parity, synthetic integration
and replay tests. No GitHub CI run was performed for these uncommitted changes.

Final source review checked both unconditional public refusals, temporary-root
restrictions, strict approval/file inventories, transitive code coverage, external
document-pin linkage, source/code mutation checks, exclusive reservation and
publication, manifest readback/invalidation and collision preservation. No further
source change was required during handoff. This is local review, not independent
owner approval or evidence that production wiring is active.

The limitations above remain material: injected fixture Git/CI/runtime observations
do not authenticate a production process; private Python functions are not a
security boundary against hostile callers; filesystem checks do not eliminate
coordinated races; and OS/storage failure or abrupt termination can prevent failure
recording or marker invalidation. Publication acceptance must require the complete
verified inventory, not merely the presence of a manifest. There is no automatic
recovery, retry, resume or approval regeneration.

Changed files are the new operator, its tests, this guide and substantive prompt
archive, plus only `docs/architecture.md`, `docs/roadmap.md` and
`docs/development-handoff.md` among existing files. Initial and final HEAD remain
`925f9abe2ec21fffc937df86e9283ad63e09aac4`. Nothing was committed, pushed or deployed;
no actual ignored audit output or economic result was created. Genuine artifacts
were not opened, listed, statted, hashed or inventoried.

## Next explicit gates

1. Owner/code review of this implementation, then a separately reviewed production
   wiring source change, clean committed SHA, successful CI and externally retained
   code/document/dependency/runtime pins. Separately authorise **one** read-only
   genuine verification attempt with exact input inventory and the named fresh
   destination. No invocation is approved by this stage.
2. Separately approve implementation/review of a genuine replay boundary accepting
   the distinct authenticated type, then authorise its exact historical execution.
   No `replay_authenticated_minute_historical` was added; synthetic guards remain.
3. Separately authorise reproduction and immutable publication of economic results,
   with approved destinations and scientific interpretation. Verification alone
   grants none of these permissions.

Stop at owner review.

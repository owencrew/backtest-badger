# Stage 4B.2D.8 — Owner-key enrolment boundary and verification integration

Prepared 2026-10-21 (Europe/London). **Implementation and fabricated tests only.**
The separate signed genuine verification route is implemented but inactive:
`TRUSTED_OWNER_PUBLIC_KEY = None` and `TRUSTED_OWNER_KEY_ID = None`.
No actual owner key was generated, requested, inspected, stored or enrolled.
No genuine source/destination was opened, statted, listed, hashed or reserved.
No genuine verification, audit rerun, strategy calculation, economic publication,
database, provider, production or sibling-project access occurred.

Starting clean `main` and final uncommitted HEAD:
`c3ee6b8ebf51911349ceab36b773eafd48585c74`. The owner reports baseline Actions run
`39576540599` completed successfully (2,183 passed, 1 skipped) for this SHA.
This is supplied baseline context, not independently queried CI and not CI for
these changes. No commit, push, deployment or remote CI execution occurred.
The [archived substantive request](../prompts/stage-04-paper/014-owner-key-enrolment-verification-integration.md)
excludes the attachment's browser/session material.

## Implemented APIs and route separation

Public interfaces:

```python
# genuine_minute_signed_approval.py
preflight_owner_approval(*, approval)  # detached canonical payload bytes

# genuine_minute_verification_runtime.py — NEW separate production entry point
run_genuine_minute_verification(*, approval) -> AuthenticatedMinuteInputs
```

Both check the independently enrolled key/ID before inspecting the candidate.
With either constant `None`, every candidate raises `PermissionError` without
object adaptation, path access, subprocess execution, callbacks or publication.
No public parameter accepts a key, runtime observer, loader, checkout override,
source kind, trust store, environment switch or permission boolean. There is no
CLI, self-service approval generator or automatic signing/enrolment procedure.

The **legacy** `genuine_minute_verification_operator.run_genuine_minute_verification`
and `genuine_minute_inputs.authenticate_minute_inputs` retain their unconditional
refusals. The new entry point has its own module; it does not weaken a fixture
entry point or rebrand its result. The symbolic `verification_plan()` and
`approval_readiness()` remain unchanged and non-executing, always reporting
`NOT_APPROVED / NOT_READY / NO_SOURCE_ACCESS`. They are not authority inputs.

Private interfaces added or narrowly extracted:

```python
# signed approval: existing seam, optional TEST assertions retained
_verify_envelope(*, document, public_key, key_id,
                 reviewed_commit=None, ci_run_id=None)

# runtime: production binds these arguments internally; TEST injection is private
_prepare_and_operate(approved, *, checkout, source_kind, environment_reader,
                     declaration_reader, forecast_loader, lineage_validator)
_read_environment(checkout)
_code_snapshot(checkout, approved)
_declared_sources(checkout)
_check_declarations(approved, declarations)
_source_snapshot(roots, approved)
_check_source_paths(roots)
_git(checkout, *args)

# operator: shared scientific and publishing cores
_verify_source_roots(roots, approved, before, *, forecast_loader, minute_loader,
                     lineage_validator, native_loader_evidence, source_kind)
_operate_verified(destination, approved, *, source_kind, source_snapshot,
                  code_snapshot, environment_reader, verify_sources,
                  directory_before)
_crosscheck(payloads, approved, before, code_before,
            *, source_kind=_SourceKind.FIXTURE)
```

`_SourceRoots` is a frozen record of three paths. `_SourceKind` distinguishes
legacy fabricated fixtures, genuine retained evidence and the new synthetic test
route. The test route accepts only isolated temporary checkouts and rejects the
original source pins; it publishes
`synthetic_test_fabricated_signed_genuine_path`. The deterministic header-only
parity discrepancy file may share its fixed format hash with the original;
that hash never authenticates a forecast, archive or prior publication.
Crosschecks require the expected route kind in scientific evidence. A result
from the legacy fixture route cannot become a genuine result by dispatching it
through the new publisher. Private functions and Python enums are not security
capabilities against hostile Python code or monkeypatching.

Only the operator's internal scientific/publishing orchestration is extracted.
Its fixture approval parser, temporary-root restrictions, default route, loaders,
publisher algorithm and failure semantics remain. `_publish` and `_readback`
are unchanged. No helper extraction from protected authentication, readiness,
loaders, parity, replay, accounting or evaluation modules was needed.

## Authority and pre-source checks

The Stage 4B.2D.7 V1 envelope contract is reused: exact canonical UTF-8/NFC JSON,
strict builtin types/fields, no duplicates/floats/nulls, sorted keys and compact
separators, no trailing newline, depth at most 32 and at most 1,048,576 bytes.
The envelope fields are exactly `schema`, `key_id`, `payload`, `signature`.
The Ed25519 message is the existing domain
`BACKTEST_BADGER_MINUTE_INPUT_VERIFICATION_APPROVAL_V1` followed by LF and the
canonical three-field object excluding `signature`. The signature remains
64 bytes encoded as 128 lowercase hexadecimal characters. `key_id` remains
`sha256:` plus the SHA-256 of the independently pinned 32 raw public-key bytes.
No alternate cryptography, signature encoding or key discovery was added.

The enrolled owner key is the approval anchor. Hashes of current code are only
observations compared against the owner's signed external identities; the running
module does not approve itself by hashing itself. The verifier returns detached
canonical payload bytes only after signature and complete intent validation.
Production preflight additionally requires the original frozen pin map, ordered
original hourly archive identities, historical protocol links and the previously
recorded original auditor implementation hash. The full historical auditor map
must still be supplied independently, not reconstructed from today's checkout.

**Commit and CI fields are owner-approved declarations, not GitHub attestation.**
The owner must independently review the exact successful CI run before signing.
The program checks the CI claim's complete schema, matching commit, numeric run ID,
completed status and success conclusion. It does not contact GitHub and cannot
prove that the declared run actually happened. Changing a field in an existing
signed record invalidates its signature; a newly owner-signed different valid CI
claim is a different declaration, not something an offline CI observer rejects.
The optional expected commit/run arguments exist only for the older private tests;
production supplies no caller assertion masquerading as independent CI evidence.

Before any source or destination path observation, the runtime requires:

1. The complete signed V1 intent, exact original source kind and strict flags:
   verification-only/single-attempt true; resume/strategy/economic authority false.
2. Exact absolute approved roots and sole destination within the actual running
   checkout, with no traversal, alternate locations or implicit path discovery.
3. Exactly 57 source identities: two named original forecast files, fifty minute
   files and five prior parity publication files. Every hash and positive byte
   length is mandatory, including **both forecast lengths**. Every implementation
   entry needs a hash and length; runtime/dependency maps must be complete.
4. A clean local Git checkout at the exact signed SHA and matching installed
   CPython 3.12 version, platform and full locked dependency closure. Local Git
   checks reject tracked artifacts, unsupported index entries and assume-unchanged
   or skip-worktree entries. Git status excludes artifact trees and covers other
   tracked/untracked files, so it cannot use status to discover source contents.
   Git environment overrides are removed and fsmonitor/untracked cache disabled.
   Loaded project modules must originate in the reviewed checkout.
5. Exact SHA-256/length observations for every declared implementation/config/doc
   path. The signed allowlist includes the new runtime and guide, `.gitignore`,
   all transitive project imports, previous guides, frozen protocols/source table,
   `AGENTS.md`, Python configuration, CI configuration, `pyproject.toml`, `uv.lock`.
6. The tracked minute pin document authenticated against its independent frozen
   hash **before** its existing parser is used. All 55 already-known source sizes,
   all 57 hashes and all 24 minute-month ZIP/sidecar/URL/grid/receipt associations
   must agree. Unknown forecast lengths are never filled from candidate sources.

Runtime package checks include cryptography, cffi, pycparser and the other lock
closure packages. The existing closure regression checks transitive project imports
and lock dependencies, now including the new runtime. No dependency or lockfile
changed. Installed package version equality is not a cryptographic attestation of
all installed third-party distribution bytes.

## Original verification and exclusive publication

Only after the above checks can a later separately authorised invocation inspect
symlink-free root components, exact minute/parity inventories and regular named
files, and the sole previously absent destination. The forecast directory is
**never enumerated**. Atomic destination reservation consumes the attempt before
any original file open. No alternate destination, overwrite, retry, reset, repair
or resume is implemented. Existing output and partial/collision evidence remain.

The production binding uses the unchanged original functions:

```python
forecast_data.load_forecasts(approved_forecast_root)  # original default pins
paper_historical_evaluation._validate_lineage(original_forecast_manifest)
minute_execution_data.load_minute_execution_data(
    approved_minute_root,
    expected_manifest_sha256=(
        "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127"
    ),
)
```

The shared core passes the signed minute manifest pin, whose equality to this
literal is required before source access. There is no TEST-hash translation,
retrospective forecast issuance, model fitting or substituted source policy.
Original all-eight-account forecast validation and Ridge/scaler lineage remain.
The unchanged native loader reparses all ZIP/sidecars; `_stream_projection` checks
all 1,054,080 rows, monthly UTC/source associations, positive exact prices,
original hash/size and EOF, retaining 21,958 references. Its existing separate
32-MiB tracemalloc regression remains. Five-file `_parity_evidence` authenticates
the prior publication with 17,568 exact HH:00 matches and linked historical
hourly/auditor provenance; it never reopens hourly archives or reruns the audit.
Research labels, holdouts, new 2025 data, funding, trades and economics are absent.

The result stays the frozen `AuthenticatedMinuteInputs` source record, with
`genuine_execution_authorised=false`, no strategy authority and no portfolios.
Genuine evidence has its distinct genuine kind; test evidence has its distinct
synthetic-test kind in both scientific bytes and publication manifest.

The single shared publisher retains descriptor-anchored exclusive `.partial`
writes, file/directory fsync, no-replace linking, canonical independent readback,
source/code/runtime pre/post checks, route crosschecks and manifest-last output.
Complete success requires exactly `authenticated_inputs.json`, `integrity.json`
and `manifest.json`, with all lengths/hashes valid, no stray/partial/failure files,
`kind=source_authentication_only`, `economic_results=false` and false execution
authority. Operational integrity retains the detached signed intent and local
observations. The owner must retain the original signed envelope separately;
the publication does not replace that approval record.

Failure invalidates only the attempt-owned manifest inode and retains safe
partial/failure evidence. Failure JSON uses controlled phases and exception
categories, not arbitrary exception messages, secrets or source rows. Foreign
collisions remain untouched. Storage failure, hard kills and hostile coordinated
replace/restore races can defeat cleanup or observation. The original loaders
retain their path APIs; this is not a filesystem sandbox or transactional guarantee.
A manifest's mere presence is insufficient evidence of successful verification.
The file publication mechanics require a suitable POSIX filesystem.

## Owner-only enrolment and missing evidence — NOT executed

1. The owner independently creates an Ed25519 signing key using a separately
   reviewed local tool in secure storage **outside the repository**, safeguards
   the private material and maintains a secure backup. Do not paste/send a private
   key to Codex/ChatGPT, commit it, put it in CI secrets for this workflow or ask
   an agent to generate/sign on the owner's behalf.
2. Export only the 32 raw public-key bytes and SHA-256 fingerprint through an
   independently confirmed channel. Separately review and explicitly authorise
   a narrow code change pinning that public key and `sha256:` ID. Commit the
   reviewed change and require green CI. Never enrol a fabricated test key or
   infer a trusted key from an incoming envelope. No fallback or override exists.
3. Separately authorise a **read-only evidence-acquisition step** for the two
   original Stage 2B byte lengths and complete historical auditor identities.
   The original manifest/forecast lengths remain unknown today. The historical
   map must come from independent retained audit evidence, not current-file
   hashes. No original file was statted, hashed, listed or opened to close these
   gaps. Until independently retained, these remain hard blockers to an actual
   complete genuine approval; invented test values do not satisfy them.
4. After the implementation/enrolment SHA and matching green CI are fixed,
   independently review the runtime, complete code/document/config identities,
   all 57 source identities, monthly/history evidence, exact roots, sole output
   and flags. Separately authorise one verification-only invocation and sign that
   exact complete manifest. Do not sign a manifest with guessed/missing fields.
5. The later real invocation must run in that exact clean checkout and runtime.
   Reservation consumes the sole attempt even on failure. A failed attempt needs
   owner review; this code offers no retry/resume/reset mechanism. Rotation or
   revocation needs another reviewed key change. Signatures do not prevent a
   hostile operator from deleting a reservation directory or replacing local code.

This stage authorises none of those manual operational actions. Genuine replay
implementation, actual strategy execution and economic publication remain further
separate approvals. Stop for owner review of this uncommitted implementation.

## Validation and preservation

The runner `/private/tmp/badger-stage8-offline-tests.py` extracts only the unchanged
`forbidden`, `check_path` and `install_offline_audit` guard definitions with AST,
then installs them before pytest collection or project imports. Active process
hooks and stat/lstat guards block all repository artifacts, sibling-project paths,
network/DNS and DB access. New integration tests additionally block provider,
parity rerun, replay, funding/trade, valuation and strategy functions. Dedicated
tests actually exercise forbidden operations and permitted temporary I/O. The new
cold-import test covers the runtime gate in a fresh guarded process.

The new suite uses ephemeral Ed25519 keys entirely in test memory and invented
code/runtime/CI/root contents. It reuses the existing native fixture generator
once per module and hard-links its files into isolated cases instead of rebuilding
full-year sources for every fault. One complete new-route run uses the unchanged
forecast parser, lineage validator, native loader, full projector and prior-parity
validator. The test forecast wrapper supplies invented source pins; production
uses original defaults. Publisher fault cases reuse that verified test record and
are explicitly not repeated native authentication. Existing fixture/native/
projection/parity/replay regression modules remain byte-identical.

Commands use this prefix, with a fresh user-owned pytest base on every invocation,
explicit test collection, `--rootdir=tests --confcutdir=tests` and
`-p no:cacheprovider`:

```sh
env PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  UV_CACHE_DIR=/private/tmp/badger-stage8-cache \
  uv run --locked --offline --no-sync python \
  /private/tmp/badger-stage8-offline-tests.py
```

The temporary runner contains:

```python
import ast
import os
import sys
import tempfile
from pathlib import Path

import psycopg

root = Path.cwd()
tree = ast.parse((root / "tests/test_genuine_minute_inputs.py").read_text())
names = {"forbidden", "check_path", "install_offline_audit"}
guard = ast.Module(
    body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names],
    type_ignores=[],
)
namespace = dict(os=os, sys=sys, Path=Path, psycopg=psycopg, ROOT=root)
exec(compile(guard, "<unchanged precollection guard>", "exec"), namespace)
namespace["install_offline_audit"]()
import pytest

base = Path(tempfile.mkdtemp(prefix="badger-stage8-")).resolve() / "suite"
result = pytest.main(
    [
        "-q",
        "--rootdir=tests",
        "--confcutdir=tests",
        f"--basetemp={base}",
        "-p",
        "no:cacheprovider",
        *sys.argv[1:],
    ]
)
print(f"PYTEST_EXIT={result}", flush=True)
sys.exit(result)
```

The focused selection is the new runtime test module plus the unchanged operator,
signed-approval, wiring and activation test modules. The full selection is `tests`.
The guard removes database DSNs; disposable-PostgreSQL cases are skips, not passes.
Ruff check and format-check use all 95 explicit tracked/new Python paths, avoiding
artifact-directory discovery. Whitespace checks include both Git diffs and all
four new files. Local logs are `/private/tmp/badger-stage8-{early,new,new2,focused,cold,full}.log`.

| Executed check | Actual result |
| --- | --- |
| Earlier unchanged signature/wiring/activation regression selection | 184 passed, `PYTEST_EXIT=0`; initial orchestration returned only its output, so this is a captured runner result |
| First new runtime suite | 59 passed, 3 failed, exit 1: hourly declaration ordering (two tests) and shared discrepancy-header hash rejected by the test-only pin guard |
| Corrected new runtime suite | 62 passed in 23.92s, exit 0 |
| Combined focused regressions after added route/failure tests | 417 passed in 141.11s, exit 0, no cleanup errors |
| Additional final cold-import test | 1 passed, 98 deselected in 0.20s, exit 0 |
| Whole-repository Ruff | 95 explicit Python files; lint and format-check exit 0 |
| Full offline suite | **2,100 passed, 183 skipped in 437.16s (0:07:17)**, `PYTEST_EXIT=0` and enclosing process exit 0; no cleanup errors |

The initial Ruff pass reported formatting/import/line-length issues, corrected
before the successful checks above. The first new-suite failures were corrected
in code/test declarations and rerun. No old test assertion or guard was weakened.
The focused selection preceded only the final cold-import test, separately checked
above and included in the full suite. Expected full-suite collection was 2,283 cases: the previous local 2,001 passes
+ 183 skips, plus 99 new cases. The actual result matches exactly: 2,100 passes
and 183 skips. All skips require `BADGER_TEST_ADMIN_DSN` for a disposable local
PostgreSQL server; no database integration pass is claimed. Full-suite process
completion confirms normal pytest teardown/shutdown without cleanup errors;
it does not claim removal of every retained temporary fixture. The full run
includes the final Python implementation and tests. Subsequent edits only finish
this documentation; no Python code changed after validation.

All **195** original tracked files were SHA-256/length inventoried before edits.
Every inventory record matches both starting HEAD and index blob bytes. The **190
protected working files** exclude only the two explicitly allowed source modules
and the three overview documents. All 190 match their original bytes; frozen
protocols/source pins, authentication/readiness, original loaders/auditor,
replay/accounting/evaluation, old tests, dependency files and configuration remain
unchanged. Genuine artifacts were excluded from inspection altogether.

Complete pre-edit inventory `/private/tmp/badger-stage8-baseline.json` SHA-256:
`b66049e5007c590479fdefb68e2baabddac2da6f9a6fce5d39d2e82a5538be08`.
Protected canonical mapping SHA-256:
`23d0f10e26231d8ac0d51220aa2e6d79a065169b7831fd20bf3417bff5767192`.
The latter hashes sorted compact JSON mapping each protected path to its SHA-256,
plus LF; reproduce it from the baseline Git blobs with the five exclusions above.
No source pin was resealed from observed candidate data. Both Git whitespace
checks and all four untracked-file whitespace/inventory checks passed. The prompt
archive matches the isolated substantive request exactly; SHA-256:
`3ca70e4996c4bae1044a25fc150fccc32c9d5ca879807cfe07b2426ad0745910`.

Local reviewed source/test identities (not approval anchors):

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `src/backtest_badger/genuine_minute_signed_approval.py` | `be5495c6a6873158438ce7ef99672dc47406c12d040d424068099dff76cdbf31` | 13596 |
| `src/backtest_badger/genuine_minute_verification_operator.py` | `7d2895ae097c91fea37fe591e71598eef6345910708a46ab58c795ea45c58609` | 24812 |
| `src/backtest_badger/genuine_minute_verification_runtime.py` | `a94fa4dce2c732ff0d1a55f47c9530344f87bc4557f165c7ac5e493dd0f29c88` | 10159 |
| `tests/test_genuine_minute_verification_runtime.py` | `8c575cfbcc7b10d38ab682929af006eb088685073b07e042faf8fda5aa4115cd` | 26325 |


## Complete change inventory and stop state

Modified existing files:

- `src/backtest_badger/genuine_minute_signed_approval.py`
- `src/backtest_badger/genuine_minute_verification_operator.py`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`

New files:

- `src/backtest_badger/genuine_minute_verification_runtime.py`
- `tests/test_genuine_minute_verification_runtime.py`
- `docs/stage-04b2d8-owner-key-enrolment-verification-integration.md`
- `prompts/stage-04-paper/014-owner-key-enrolment-verification-integration.md`

Final Git status: five modified tracked files, four new untracked files, nothing
staged, same starting SHA on `main`. No genuine source verification result or
publication exists from this stage. The code path is implemented; owner trust,
complete independent evidence and actual invocation remain disabled/unapproved.
Review these nine files and the test evidence before separately authorising any
commit, key enrolment, evidence acquisition or real invocation.

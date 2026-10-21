# Stage 4B.2D.9 — Owner public-key enrolment

Prepared 2026-10-21 (Europe/London). Implementation and fabricated tests only.
Starting clean `main`: `72469f674a4d60c2ef97c6f77f2f85672ddc4bbd`.
The owner supplied baseline Actions run `39622070431` (2,282 passed / one skipped);
this was not independently queried and does not validate the future enrolment
commit. No commit, push, deployment or new GitHub CI run occurred.

## Implemented

The independently supplied public values are pinned in
`src/backtest_badger/genuine_minute_signed_approval.py`:

```text
PUBLIC_KEY_HEX = 9b22dba87d87cd5d4fa5c6db7948eb3d117ae3ad17b7956a3b0b71d5ba4c18a9
KEY_ID = sha256:503ebad4f2d36152e2fdc8d71a9b8cbaf2cede3804e6293d7a939f65578abe43
```

Pure computation from the literal hex independently confirmed exactly 32 bytes
and the stated SHA-256 of those raw bytes. This is not an OpenSSH CLI fingerprint
or a hash of a public-key file. No key file or signing-key directory was accessed.
The key was not generated, regenerated, copied or moved in this stage.

Production source changes are only the two trust constants and the module's
opening descriptive sentence. An AST comparison confirms all imports, functions,
schemas, limits and other constants are unchanged. The key is immutable `bytes.fromhex` of the fixed
literal; the key ID is a separate fixed literal. All verifier/runtime functions,
source declarations, dependency/lock files and CI configuration remain unchanged.
There is no loader, fallback, trust-store lookup, environment switch, public key
override, signing API or rotation feature.

The separate `genuine_minute_verification_runtime.run_genuine_minute_verification`
can now in principle accept a future valid, complete owner-signed approval.
**No owner-signed approval or genuine invocation is supplied or authorised here.**
Both legacy public gates still refuse unconditionally. Earlier Stage 4B.2D.7/8
statements about unenrolled trust describe those historical stages; the unchanged
runtime module's introductory enrolment condition has now been satisfied.

## Reviewed ordering and preserved boundaries

The unchanged public preflight checks exact bytes, canonical V1 envelope/domain,
independently pinned key ID, Ed25519 signature and the complete intent schema.
It then checks frozen original declarations, ordered hourly identities and
historical auditor/protocol links. Missing/invalid signatures, malicious objects,
wrong source kinds/flags, incomplete inventory/forecast lengths/auditor maps,
and incomplete commit/CI/runtime/code evidence cannot reach source/destination I/O.

The runtime next checks exact checkout/root declarations, the clean signed Git
commit, installed runtime/dependency versions, complete code/config/document
identities and the tracked frozen source declarations. Only after these checks
can source/destination metadata be inspected. A signature authenticates an owner
claim about CI; it does not prove that GitHub ran it. The owner must independently
review the exact commit and successful workflow before signing later.

The 57-file inventory, original forecast/minute/parity validators, manifest-last
one-use publisher, no retry/resume semantics and fixture/synthetic/genuine type
separation are preserved. `AuthenticatedMinuteInputs.genuine_execution_authorised`
remains false. Publications remain source-only with `economic_results=false` and
no strategy/replay authority. No original source or proposed original destination
was opened, statted, listed, hashed or reserved. No signing-key directory, sibling
repository, production infrastructure, database or network was accessed by tests.

## Test changes and actual validation

Two existing test modules were edited; all other regression modules are unchanged.
Assertions that required `None` now check enrolment or unrelated test keys.
Public preflight failures now expect `ValueError` for invalid candidates; legacy
refusals still require `PermissionError`, with their no-verifier-dispatch guards.
The missing-key fail-closed cases still explicitly test absent/partial trust.

Nineteen new cases cover the exact key/ID, import-body side effects and seventeen
invalid-candidate variants through both enrolled public APIs. They cover ephemeral
keys, signatures made with a test key over the owner ID, altered/missing/malformed
signatures, fake IDs, candidate-selected keys/fingerprints/trust, each missing
forecast length, unsigned/incomplete records, noncanonical bytes and malicious or
missing objects. File open/stat/list/reservation/dispatch interceptors are explicitly
exercised to prove they fail before underlying operations. Public key overrides
raise `TypeError`. Existing cold-process import guards remain active. Ordinary
imports load Python code; the added module-body test isolates enrolment effects
under a blanket filesystem guard after dependencies have loaded.

Real cryptographic success uses only unrelated ephemeral in-memory test keys via
existing test seams. Complete synthetic execution retains isolated temporary
roots and independent TEST pins. Existing production-binding inspection stops at
an interception before any real observation. No fabricated authority executes
against original roots. Native archive/projector and publication fault-injection
regressions remain in the suite; no expensive native test module was edited.

The temporary runner `/private/tmp/badger-stage9-offline-tests.py` AST-extracts
`forbidden`, `check_path`, `install_offline_audit` from the unchanged
`tests/test_genuine_minute_inputs.py` and installs the guard before pytest
collection or project imports. It blocks repository artifacts/sibling paths,
network/DNS and PostgreSQL, including stat/lstat. It removes DB DSNs. Each run
creates a fresh user-owned temporary base and uses `--rootdir=tests`,
`--confcutdir=tests`, `-p no:cacheprovider` and an explicit test selection.

```sh
env PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  UV_CACHE_DIR=/private/tmp/badger-stage9-cache \
  uv run --locked --offline --no-sync python \
  /private/tmp/badger-stage9-offline-tests.py tests
```

The focused selection comprises signed-approval, runtime, operator, wiring and
activation modules. Logs: `/private/tmp/badger-stage9-focused.log` and
`/private/tmp/badger-stage9-full.log`.

| Executed check | Actual result |
| --- | --- |
| Focused guarded suite | **437 passed in 142.48s**, `PYTEST_EXIT=0`, process exit 0 |
| Full guarded suite | **2,119 passed, 183 skipped in 440.83s (0:07:20)**, `PYTEST_EXIT=0`, process exit 0 |
| `uv run --locked --offline --no-sync ruff check .` | Exit 0 after correcting two test-only lint findings |
| `uv run --locked --offline --no-sync ruff format --check .` | **178 files already formatted**, exit 0; whole repository including Markdown |
| `git diff --check` | Exit 0 |
| Protected-file SHA-256 / HEAD / index comparisons | All 193 protected files match |

The first lint check exited 1 for a long embedded test-script line and an
intentional `io.open` guard probe. The line was wrapped; the probe retains a
specific `UP020` exemption so it still tests that separate interceptor. The
focused suite started before these two non-behavioural lint corrections; the
complete suite uses the final Python source/tests. No test was removed or silently
bypassed. All 183 skips require `BADGER_TEST_ADMIN_DSN` for an isolated local
PostgreSQL server; they are not successful database tests. All 2,302 collected
cases are accounted for (the baseline 2,283 plus 19 new cases). Both processes
completed normal teardown without cleanup errors. Final report edits only update
documentation; no Python changed after full-suite validation.

## Preservation and reviewed identities

Before edits, all 199 tracked files matched their initial SHA-256/length records,
HEAD blobs and index blobs. No ignored artifact tree was inventoried. The baseline
inventory `/private/tmp/badger-stage9-baseline.json` SHA-256 is
`55d86f9c8a34b3b6fb7195611e7e5df1d9188bf080e2aabb5348d93c12295a95`.

The protected set is all 199 baseline files except the six modified files listed
below: **193 protected files**. SHA-256 plus HEAD/index byte comparisons pass.
This includes frozen source pins/protocols, original loaders/auditor,
replay/portfolio/accounting/economics, runtime/operator, other tests, lockfile and
configuration. The protected canonical mapping SHA-256 is
`3ee4e2016301b808fdf18aaa0449244af5799c7bfd47ae0568399e614720956b`:
sorted compact JSON mapping each protected path to its original SHA-256, plus LF.

Locally reviewed identities are observations, not future signed approval anchors:

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `src/backtest_badger/genuine_minute_signed_approval.py` | `1beba3a207c30052717d8d148a7bcdfd7eb74b78948a5c38efafc491aaf7e01b` | 13752 |
| `src/backtest_badger/genuine_minute_verification_runtime.py` | `a94fa4dce2c732ff0d1a55f47c9530344f87bc4557f165c7ac5e493dd0f29c88` | 10159 |
| `src/backtest_badger/genuine_minute_verification_operator.py` | `7d2895ae097c91fea37fe591e71598eef6345910708a46ab58c795ea45c58609` | 24812 |
| `tests/test_genuine_minute_signed_approval.py` | `cd983426c7db6b27900b97a2683ffd41378a96e11f76268fed516d93db3b4eec` | 24582 |
| `tests/test_genuine_minute_verification_runtime.py` | `f51f1df7196373471c206d89956bb3ccb41a42f0c075efd3641ad1223bfe7b41` | 31990 |

The [archived substantive request](../prompts/stage-04-paper/015-owner-public-key-enrolment.md)
excludes unrelated browser/session material from the attachment and matches the
isolated request byte-for-byte. Its SHA-256 is
`35d06dc72acc6184c2befab17826abaa238803c51b0e56e247807646ad911d2c`.

Exact changed-file inventory (nothing staged):

- Modified: `src/backtest_badger/genuine_minute_signed_approval.py`.
- Modified: `tests/test_genuine_minute_signed_approval.py`.
- Modified: `tests/test_genuine_minute_verification_runtime.py`.
- Modified: `docs/architecture.md`.
- Modified: `docs/roadmap.md`.
- Modified: `docs/development-handoff.md`.
- New: `docs/stage-04b2d9-owner-public-key-enrolment.md`.
- New: `prompts/stage-04-paper/015-owner-public-key-enrolment.md`.

## Outstanding evidence and next owner decision

Implemented: reviewed owner public-key enrolment in local source, awaiting owner
review of the uncommitted diff. Not yet independently verified: green GitHub CI
for the future enrolment commit, the exact future complete signed intent, and all
future reviewed runtime/code/document identities. The supplied baseline SHA/CI
and local hash observations do not substitute for that future approval.

Outstanding independent historical evidence: **both original Stage 2B forecast
file byte lengths**, the **complete historical auditor implementation map**, and
all other obligations in the [Stage 4B.2D.8 guide](stage-04b2d8-owner-key-enrolment-verification-integration.md).
No values were invented for genuine evidence, auto-learned from originals or
substituted from current auditor code. Fabricated test values close no evidence gap.

Not authorised: genuine data/source/destination access, genuine verification,
signing, historical replay, economic calculation/publication, production
deployment, retries or resumes. No owner-signed record is stored in the repository.

Next owner decision: review these eight files and the local test evidence, then
separately decide whether to authorise commit/push and require green CI for that
exact enrolment commit. Evidence acquisition needs its own explicit read-only
scope. Only after all evidence and identities are independently reviewed may the
owner separately sign a complete intent and authorise one genuine verification
attempt. Stop here for review; no commit, push or deployment is authorised.

# Stage 4B.2E.3 — Independent sign-off contract reconciliation

Prepared 2026-10-23 (Europe/London). Fabricated records only; uncommitted owner
review deliverable. Baseline HEAD is
`27a4d4e6967fa8a986678f1622e4509cffa16b4b`, verified locally before implementation.
The owner reports baseline GitHub Actions run `39833360153` succeeded with
2,485 passed and one skipped. That is supplied review context, not a CI result
for this diff; no network query, commit, push or CI dispatch occurred.

The [original substantive request](../prompts/stage-04-paper/018-independent-signoff-contract.md)
is archived separately from session context. The resumed request preserves the
implementation and prohibits economic calculation. Accordingly, local validation
runs parsing and rejection tests only, with the minute replay core disabled.
The existing fabricated economic parity test and full suite remain for separately
authorised CI; neither was run here.

## Pure contract and accepted evidence

Only `src/backtest_badger/genuine_minute_publication.py` and its matching test
module change existing Python code. The added private seam is:

```python
_validate_independent_signoff(
    *, signoff, expected_signoff, publication, expected
) -> _ReconciledSignoff
```

- `signoff` must be exact immutable in-memory `bytes`.
- `expected_signoff` must be a separately retained `_Fingerprint` with an exact
  SHA-256 string and positive integer length bounded at 1 MiB. Booleans and floats
  are not integer lengths. The exact body length and SHA-256 must match before
  any JSON is parsed. This fingerprint must also equal `expected.signoff`.
- `publication` must be `_VerifiedPublication` carrying exactly three immutable
  byte bodies. `expected` must be independently supplied `_PublicationPins`.
  The existing E.2 parser reparses those bodies against the external pins and
  refuses changed records. All subsequent reconciliation uses its newly parsed
  evidence, not the caller's converted records.
- The result retains the exact sign-off bytes and revalidated publication in a
  frozen `_ReconciledSignoff`. It contains no execution permission switch.

No existing parser or replay signature changes. In particular,
`_parse_verified_publication(..., signoff_claim=...)` still checks fingerprint
continuity only. It does not imply that this new content validator was called.
The private E.2 replay remains unchanged and separately unauthorised; the new
validator never calls it or `_replay_minute_core`.

This implements the schema-reconciliation step left outstanding in the E.2
guide, using the supplied writer declaration. It does not complete that guide's
separately authorised original-file acceptance or future execution steps.

The validator has no loader, path argument, callback, writer, environment flag,
network operation or public CLI. The publication identifier is compared as a
literal string; no filesystem operation is performed on it. It does not reopen
native archives, validate a signature again, refresh CI, or calculate trades.

## Exact D.14 writer schema

The sole schema source is the owner-supplied D.14 writer declaration archived
with the request. None of the four original files was read or reconstructed.
Tests independently serialize invented identities using the declared
`json.dumps(..., sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"`
UTF-8 encoding. The existing strict JSON reader and canonical serializer enforce
that encoding, duplicate-key rejection, and nonfinite/overflow rejection.

The full expected record is compared through canonical encoded JSON, preserving
bool/int/float distinctions and exact key sets at every level:

| Field | Required agreement |
| --- | --- |
| `schema`, `status` | `stage-04b2d14-publication-signoff-v1`, `PASS` |
| `original_execution_commit`, `reviewed_ci_run_id` | Original `integrity.json` approval's `commit` and `ci.run_id` |
| `publication` | Exactly `artifacts/audits/stage-04b2d3-minute-inputs-v1` |
| `independent_manifest_sha256` | External manifest fingerprint |
| `published_file_identities` | Exactly manifest, authenticated inputs and integrity; each exact byte length and SHA-256 equals its external pin |
| `publication_kind`, `source_kind` | Revalidated manifest's `source_authentication_only` and `genuine_retained_stage2b_native_minute_prior_parity` |
| `verification_flags` | Exactly original approval's verification-only/single-attempt true and resume/strategy/economic-publication false |
| `genuine_execution_authorised`, `economic_results` | Revalidated manifest's exact false values |
| `scientific_counts` | 8 forecast accounts, 17,560 forecasts, 2 reference markets, 21,958 references, 1,054,080 authenticated native-minute rows |
| `checks`, `limitations` | All six entries each, verbatim and in writer order, as archived in the request |

Scientific counts come from revalidated typed rows and retained scientific
metadata already constrained to the fixed E.2 counts. Manifest companion
identities are compared to the external pins as well as the sign-off. The
manifest declares its two companions; its own identity is established by the
externally pinned exact manifest body, not an impossible self-referential hash.

The original verification commit/CI are distinct from the current implementation
and any future simulation commit/CI. The parser obtains the former solely from
the externally bound historical integrity body. It neither replaces those claims
with HEAD nor hardcodes genuine identities into fabricated fixtures. Tests use
`a` repeated 40 times and CI `123456`, with unrelated invented publication pins.

The six checks and six limitations are descriptive statements from the historical
writer. Validating their text does not perform or authorise the described actions.
Historical retained parity and preservation evidence is not a new audit of source
bytes; the missing original parity-integrity bytes are not reconstructed.

## Authority and limitations

A caller able to invent both candidate bytes and every purported external pin can
construct an internally consistent fabricated record. No pure bytes parser can
prove that supplied pins were independently retained. The future owner-controlled
boundary must supply them independently. Tests distinguish structural validation
from that external trust requirement: self-hashed altered records fail against
retained pins, and even test-only repinning cannot reconcile a substituted new
commit/CI with the historical publication.

Frozen Python records and private names are not security capabilities. A matching
fingerprint alone is not validated sign-off content. Neither successful content
validation nor direct construction of a record grants strategy permission.
`replay_genuine_minute_historical(*, approval)` remains unconditionally closed
with `PermissionError` before inspecting even a hostile argument. The validated
wrapper is also refused by the existing synthetic source/evaluation boundaries.

Original source authenticity, fresh CI, fresh signatures, file preservation and
profitability are not established by this step. No original identity in the
request was recomputed or represented as observed here.

## Tests, offline procedure and review

The added tests cover a valid complete canonical roundtrip; every required field
altered, omitted and mistyped; extra object keys; all individual attestation list
entries omitted, substituted or reordered; duplicate/reordered JSON keys;
missing newline, whitespace, BOM, invalid UTF-8, trailing data and excess nesting;
NaN, infinities and numeric overflow; bool/float length and count confusion;
external hash/length failures before JSON; changed external publication pins;
self-hashed new commit/CI claims; injected publication records; and upstream
manifest identity/authority, integrity authority and scientific count disagreement.
The complete-schema success test disables both private replay entry points and
checks that the public gate refuses the result without inspecting its argument.

Guarded execution uses the existing temporary root
`/private/tmp/badger-4b2e3-9X85Sc` and its `guarded.py` launcher. Before project
imports it blocks original/private path opens/listings/stats and network calls,
removes database configuration without reading its values, disables bytecode,
and confines test file writes to that temporary root. It then installs the E.2
`install_offline_audit()` fixture guard before pytest collection. Per-test no-I/O
guards additionally forbid filesystem operations, genuine verification, loaders
and publishers. The launcher disables the minute economic core for these runs.
These are procedural/Python guards, not a claim of OS-enforced isolation. Ruff
runs on only the two named files with `--no-cache`; Python hooks do not sandbox
the native Ruff subprocess.

Exact command prefix used for all final lint/test invocations:

```sh
PYTHONDONTWRITEBYTECODE=1 \
UV_CACHE_DIR=/private/tmp/badger-4b2e3-9X85Sc/uv-cache \
RUFF_CACHE_DIR=/private/tmp/badger-4b2e3-9X85Sc/ruff-cache \
uv run --locked --offline --no-sync python \
/private/tmp/badger-4b2e3-9X85Sc/guarded.py
```

Arguments appended to that prefix:

```sh
lint check --no-cache src/backtest_badger/genuine_minute_publication.py tests/test_genuine_minute_publication.py
lint format --check --no-cache src/backtest_badger/genuine_minute_publication.py tests/test_genuine_minute_publication.py
focused tests/test_genuine_minute_publication.py -k signoff
regression tests/test_genuine_minute_publication.py -k 'not signoff and not full_year_shared_core_parity_with_unchanged_fixture'
```

Ruff lint passed; Ruff format reported both files already formatted. The focused
run passed **185 tests**, with **112 deselected**, in **300.52 seconds**, exit zero:
all **184 new cases** plus the pre-existing sign-off fingerprint-continuity test.
The subsequent regression run passed **111 tests**, with **186 deselected**, in
**40.91 seconds**, exit zero. These selections are disjoint: **296 distinct tests
passed**, with no failures or skips. The sole unexecuted test in this module is
`test_full_year_shared_core_parity_with_unchanged_fixture`, which calculates
fabricated economics. It is unchanged and was not run under the resumed request.
The broader suite, including economic parity and database cases, remains for
separately authorised GitHub CI. No CI result for this uncommitted diff exists.

Local self-review found no outstanding implementation issue after the lint fixes.
This is not independent external code review. The review checked the pure call
boundary, the complete supplied writer declaration, original commit/CI separation,
strict scalar comparison, external identity binding and unconditional public gate.
Actual original-file acceptance remains deliberately untested.

The launcher adds `-q --rootdir=tests --confcutdir=tests
-p no:cacheprovider -p no:logging --capture=sys` and a bounded `--basetemp` under
the same temporary root. No dependencies are installed or synchronised.

Initial Ruff reported formatting/long-line issues and one unused import; these
were fixed. The initial pytest launch exited before collection because the strict
write guard refused pytest's default logging sink outside the temporary root.
Disabling the logging plugin and using Python-level capture resolved this without
relaxing path/network/write guards. No test failure or pass count is attributed
to that aborted launch.

## Preservation and owner-controlled next steps

The intended diff consists of the Python module, its test module, this report and
the archived request. Existing parsing/replay implementation and tests are
preserved; all additions concern sign-off reconciliation. No other source module,
dependency, frozen methodology, source pin, accounting cost/timing/strategy,
public gate or deployment configuration is changed.

Only exact named source/test reads and scoped Git checks were used. No generic
repository discovery, unrestricted status, environment inspection or original
artifact metadata check was performed. No procedural access deviation is known.
Preservation checks concern tracked allowed paths and unchanged existing code;
original artifacts were deliberately not statted, hashed or compared, so their
byte preservation is not independently certified here.

Static AST comparison against HEAD confirmed all **18 existing function/class
definitions** in the implementation and all **24 existing function/class
definitions** in its test module are unchanged. Scoped `git diff --exit-code
HEAD --` returned zero for the allowed unchanged paths: `AGENTS.md`, genuine
replay, inputs, signed-approval and verification-operator modules, minute
historical accounting, existing input/replay/signed-approval tests, E.1/E.2 guides,
architecture, roadmap, handoff, `pyproject.toml` and `uv.lock`. This is a scoped
preservation check, not an inventory or audit of uninspected repository paths.

Whitespace checks use `git diff --check HEAD --` with exactly the two changed
Python paths, and `git diff --no-index --check -- /dev/null` separately for each
new Markdown path. No whitespace diagnostics were reported. The no-index checks
return one because these files differ from `/dev/null`; that is not a whitespace
failure. Final `git rev-parse HEAD` still reports
`27a4d4e6967fa8a986678f1622e4509cffa16b4b`. All four deliverables remain uncommitted.

Before any original read or 2024 economics, the owner must separately review and
authorise the implementation/CI pinning and the next operation. A future boundary
must bind independently retained fingerprints, exact permitted original paths,
no-follow bounded reads and preservation checks. Acceptance of the actual original
sign-off and publication is untested here. Unexpected content must stop that
future operation; it must not trigger fallback, repinning or verification reruns.
Genuine execution and any economic output publication require their own explicit
owner authority. This deliverable includes no runner, operational command or
publication destination.

FABRICATED TESTS ONLY · ORIGINAL SIGN-OFF/PUBLICATION UNREAD · GENUINE REPLAY NOT
EXECUTED · ECONOMIC PUBLICATION NOT AUTHORISED.

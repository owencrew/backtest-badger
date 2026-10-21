# Stage 4B.2D.7 — Offline Ed25519 approval envelope

Prepared 2026-10-21 (Europe/London). Implementation and fabricated tests only.
Real cryptographic verification is implemented; production trust is **not
enrolled**, and genuine invocation remains **unconditionally closed**.

Starting clean `main`: `1378d15939dad63651a73c9ea0bebada7f819886`.
Git HEAD, branch, index and working-file bytes matched the required baseline.
Actions run `39519276647` and its 2,086 passed / 1 skipped result are
owner-supplied baseline evidence, not newly queried CI. No new CI was triggered.
The [substantive request](../prompts/stage-04-paper/013-offline-signed-verification-approval.md)
excludes unrelated browser/session material from the supplied attachment.

## Delivered interfaces and boundaries

[genuine_minute_signed_approval.py](../src/backtest_badger/genuine_minute_signed_approval.py)
provides three deliberately distinct operations:

- `canonical_approval_bytes(value)` serializes supported plain data. This creates
  neither a signature nor permission. It does not read paths or adapt objects.
- `_verify_envelope(*, document, public_key, key_id, reviewed_commit, ci_run_id)`
  is an **internal fabricated-key seam**. It checks canonical wire bytes, real
  Ed25519 verification and the complete inert intent schema, then returns detached
  canonical payload bytes. Its injected key/review identities are test inputs.
- `preflight_owner_approval(*, approval)` always raises `PermissionError` before
  inspecting approval, even if key constants are monkeypatched. It accepts no key,
  digest, trust-store, CI observer, path or enable override.

`TRUSTED_OWNER_PUBLIC_KEY` and `TRUSTED_OWNER_KEY_ID` are both `None`. No private
key, production public key, trusted digest, signing command or invocation CLI
exists. Only tests generate ephemeral keys in memory using the vetted library.
No private-key bytes are serialized or saved. The internal verifier's successful
bytes are not an `AuthenticatedMinuteInputs`, fixture approval or capability.

Both existing public entry points remain byte-identical unconditional refusals:
`run_genuine_minute_verification(*, approval)` and
`authenticate_minute_inputs(*, approval)`. Neither calls the new verifier.
Readiness still reports **NOT_APPROVED / NOT_READY / NO_SOURCE_ACCESS**.
The Stage 4B.2D.6 historical design-choice blocker is resolved by the owner's
selection of offline Ed25519; enrolment, evidence and invocation remain separate.

## Exact V1 wire and signature contract

The envelope has exactly four fields: `schema`, `key_id`, `payload`, `signature`.
`schema` is exactly `minute-input-owner-signature-v1`. Unknown versions and extra
fields at any validated object level are refused.

Canonical serialization is deliberately distinct from scientific evidence JSON:

1. Only exact builtin dictionaries, lists, strings, booleans and signed 64-bit
   integers are supported. Dictionary keys must be exact strings. Null, tuples,
   floats (including finite values), NaN, infinities, subclasses and custom
   objects are rejected. No `str`, property, iterator, dataclass adapter or
   `dataclasses.asdict` conversion is applied to supplied objects.
2. Strings must already be Unicode NFC. No normalization is silently applied.
   U+0000–U+001F and surrogate code points are forbidden. Other valid Unicode
   scalar values are encoded directly in strict UTF-8, without BOM.
3. Object keys sort lexicographically by Unicode code point; arrays retain order.
   Use Python JSON escaping with `ensure_ascii=False`, `allow_nan=False`,
   `sort_keys=True`, separators `(',', ':')`. Quotes/backslashes are escaped;
   non-ASCII characters are not escaped. Integers use ordinary decimal spelling,
   booleans use `true`/`false`. No insignificant whitespace or final newline.
4. The maximum document is 1,048,576 bytes and maximum structural depth is 32
   (root depth zero). Reject duplicate keys at every depth during parsing,
   floating-point tokens, nonfinite constants, trailing data and non-UTF-8 input.
   Re-encode and compare the **entire envelope bytes** with the supplied bytes.
   Alternate key order, escaped Unicode, `-0`, spacing and newline spellings fail
   even when they would decode to equivalent values.

The bytes signed by Ed25519 are exactly:

```text
b"BACKTEST_BADGER_MINUTE_INPUT_VERIFICATION_APPROVAL_V1\n"
    + canonical_approval_bytes({schema, key_id, payload})
```

The braces above denote the three complete named fields and their values, not
Python set syntax or a shortened payload. Nothing else is excluded from signed
coverage. The domain's terminating LF is mandatory; the JSON has no trailing LF.
No prehash or signing of a self-supplied digest is used.

`key_id` consists of the seven ASCII bytes `sha256:` followed by 64 lowercase
hexadecimal characters: SHA-256 of exactly the 32 raw Ed25519 public-key bytes.
It is not the hash of PEM text or of the candidate approval. Both the separately
provided expected ID and envelope ID must match that raw key. This consistency
check establishes no production authority when the key is test-injected.

`signature` is exactly 128 lowercase hexadecimal ASCII characters representing
64 Ed25519 signature bytes. Reject uppercase, prefixes, spaces, base64, wrong
lengths or alternate encodings. Verification uses
`cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey.verify`.
Errors expose only `Invalid offline approval.`, suppress decoder/crypto exception
context in ordinary tracebacks, and do not log supplied content.

## Complete inert payload

`payload.schema` is `minute-input-verification-intent-v1`. This is intentionally
distinct from the existing executable **fixture-only** approval schema. Its exact
top-level field inventory reuses `operator.APPROVAL_FIELDS` without changing that
operator. A valid signature does not convert a fixture into genuine evidence.

| Field | Validated contract |
| --- | --- |
| `source_kind` | Proposed `genuine_retained_stage2b_native_minute_prior_parity`; an inert declaration only |
| `commit`, `ci` | Lowercase full 40-character SHA; CI exactly `commit`, positive decimal-string `run_id`, `status=completed`, `conclusion=success`; both match separately provided internal test review expectations |
| `runtime` | Exactly Python `3.12.x`, `implementation=CPython`, `platform` (`darwin`, `linux`, `win32`), complete dependency-version map; no ranges/defaults |
| `implementation` | Exact wiring allowlist plus new verifier and Stage 4B.2D.6/7 guides; every entry has exactly lowercase SHA-256 and positive integer byte count |
| `roots`, `destination` | Three exact lexical source suffixes and sole proposed destination suffix under one absolute checkout prefix; no empty, dot, parent, backslash or trailing-slash destination components; no filesystem resolution |
| `input_inventory` | Exactly 2 named forecast files, 50 minute files and 5 parity files, each with SHA-256 and positive integer byte length |
| `pins` | All 17 wiring declarations, including original research/hourly declarations, protocol/source-document hashes and five original parity identities; source and document crosslinks must agree |
| `monthly_sources` | Exactly 24 ordered `[symbol, month, record]` entries, BTCUSDT then ETHUSDT, January–December 2024; exact nine-field records described below |
| `hourly_monthly` | Same 24 ordered symbol/month identities, each with its original declared hourly ZIP hash |
| `audit_code` | Exact original `parity.IMPLEMENTATION_FILES` hash map, retained from the historical auditor, not substituted from current code |
| flags | Strict booleans: `verification_only=true`, `single_attempt=true`; `resume=false`, `strategy_authorised=false`, `economic_publication_authorised=false` |

Monthly records contain exactly `sha256`, `checksum_sha256`, `zip_bytes`,
`checksum_bytes`, `csv_bytes`, `row_count`, `url`, `checksum_url`, `observed_at`.
ZIP/sidecar hashes and sizes crosslink to the exact 48 raw-file identities.
URLs match the original symbol/1m/month ZIP and `.CHECKSUM` associations.
Expanded CSV size is mandatory; the original pin contract does not supply an
independent expanded CSV hash, so none is invented. Row counts bind the full
calendar month, including 41,760 minutes in leap February. The month identity
implies the complete UTC minute grid; archive/grid authentication remains the
unchanged future loader's responsibility. Retrospective receipts must be valid
UTC ISO timestamps ending `+00:00`, with either seconds or six microsecond digits,
exactly round-tripping through `datetime.isoformat`, and no earlier than month end.
Original microsecond receipt precision is preserved.

The runtime map contains the 17 non-Windows CPython runtime distributions in the
current lock: alembic, cffi, cloudpickle, cryptography, joblib, mako, markupsafe,
narwhals, numpy, psycopg, psycopg-binary, pycparser, scikit-learn, scipy, sqlalchemy,
threadpoolctl, typing-extensions; Windows also requires tzdata. Keys use normalized
lowercase distribution names; versions are explicit numeric dotted strings.
Development-only pytest/Ruff dependencies are not invocation runtime evidence.
An AST import-closure test covers transitive project imports; a lock-graph test
covers the runtime dependency inventory. A future dependency/platform change
requires review of this schema and closure.

The internal verifier checks completeness, internal consistency and signature
integrity. It deliberately permits **invented hashes, sizes, runtime versions and
checkout prefixes in tests**. It does not authenticate real evidence, inspect Git,
fetch CI, compare runtime observations or enforce current production declarations.
No external identity is defaulted from local sources. The future genuine
validator must separately bind the enrolled owner's original declarations,
reviewed source contract and actual permitted runtime/code observations. It must
not use the injected test key or test review expectations as an authority reader.

## Future manual owner enrolment and one-use workflow — not executed

1. The owner generates and secures a real Ed25519 private key offline, outside
   the repository, using an independently reviewed local tool or secure storage.
   Codex must not create that key, request it, transmit it or sign on the owner's
   behalf. No executable key-generation/signing command is supplied in this stage.
2. The owner independently communicates the 32 raw public-key bytes and SHA-256
   fingerprint over a confirmed out-of-band channel. Do not extract the anchor
   from a candidate envelope. A separate approved code change pins the public
   key and expected `sha256:` ID in reviewed source with matching green CI.
   Filling the constants alone does not open today's preflight or public gates.
3. Separately review the genuine contract/activation implementation, preserving
   fixture restrictions, all existing loaders and exclusive publication rules.
   Freeze its clean full SHA, exact successful CI run, code/config/document
   hashes/lengths and exact runtime. No environment override or caller trust store.
4. Independently retain the complete original 57-file evidence, both forecast
   lengths, monthly provenance and original auditor identity map. The owner
   inspects every field of the completed canonical intent and separately signs
   precisely the domain-separated authenticated fields after code review and CI.
   Retain the exact signed envelope and independently confirmed public-key ID.
5. Obtain separate explicit manual permission for **one read-only attempt** at
   the exact roots and sole output. The future production preflight must reject
   missing/unapproved keys, invalid signatures, incomplete evidence, stale
   commit/CI/runtime/code identities and wrong flags before source/destination I/O.
6. The future operator consumes the attempt by exclusive destination reservation
   before opening sources, even if verification later fails. No retry, alternate
   destination, resume, repair or overwrite. Publish source-only evidence with
   `economic_results=false`, `genuine_execution_authorised=false`, and the success
   manifest last only after all preservation/readback checks.

Signatures alone enforce neither single use nor revocation. Rotation/revocation
requires a separately reviewed public-key change; no accepted fallback set may
retain a revoked key. These controls do not protect against replacement of local
code or compromise of the owner's private key. A valid signature is owner consent
only when the key really was independently enrolled and the owner signed that
exact manifest. Test keys or self-generated anchors never supply that evidence.

## Preserved genuine constraints and unresolved evidence

The frozen declarations in the unchanged
[wiring guide](stage-04b2d5-genuine-verification-wiring.md#known-declarations-and-exact-future-inventory)
and [minute pin document](stage-04b2c-minute-source-pins.md) remain authoritative.
The forecast manifest length and `validation_predictions.csv` length are still
**unknown**. No original source or destination was statted, listed, opened or
hashed to obtain them. The complete independently retained original auditor map,
future enabled-code/CI/runtime identities, approved absolute checkout paths and
one-attempt permission remain unresolved. A well-shaped fabricated envelope
resolves none of those obligations.

Later source verification must reuse unchanged default-pinned
`forecast_data.load_forecasts`, `_validate_lineage`, and
`minute_execution_data.load_minute_execution_data` with the literal original
minute manifest pin. It must scan the full 1,054,080-row bounded projection,
retain exactly 21,958 references and validate the already published genuine
five-file parity evidence without rerunning its audit. Only the two named
forecast files may be opened; never enumerate their directory. Research/hourly
releases remain declarations, not additional input roots. Economic restrictions,
causal timing, frozen protocols and separation of synthetic/genuine types remain.

The sole future output remains `artifacts/audits/stage-04b2d3-minute-inputs-v1/`.
Its presence/absence, metadata, ignore state and symlink state remain uninspected.
No reservation, source audit, genuine verification, historical replay or economic
publication has occurred. No database, provider, production or sibling-repository
access occurred. No commit, push or deployment is part of this stage.

## Dependency resolution and validation

Added bounded direct dependency `cryptography>=46,<47` through ordinary `uv add`.
The lock resolves cryptography **46.0.7**, cffi **2.1.1**, pycparser **3.11**, with
registry distribution hashes/sizes. Existing package records/versions are
unchanged. Initial offline resolution in a new isolated cache failed because
metadata was absent; default-cache sandbox access also initially refused. The
authorised cache/registry resolution then succeeded (exit 0) and installed the
three distributions. No hand-written lockfile or cryptographic implementation.
All tests and lint subsequently use locked/offline/no-sync execution.

No new CI status is claimed for this uncommitted change.

### Guarded validation procedure

The local runner `/private/tmp/badger-4b2d7-offline-tests.py` AST-extracts only
`forbidden`, `check_path` and `install_offline_audit` from the unchanged
`tests/test_genuine_minute_inputs.py`, installs them **before pytest collection
or any project import**, then runs explicit `tests/` selections. It blocks
artifact/sibling opens, listings and stat/lstat, sockets/DNS and PostgreSQL.
Database DSN environment variables are removed by the unchanged guard. No guard
or pre-existing test assertion was weakened. Each invocation uses a fresh
user-owned temporary base and disables pytest's cache provider.

The new independent child process installs that guard before the new module's
cold import, exercises 23 forbidden operations without reaching their underlying
access, and confirms all three public gates refuse malicious objects. In-process
tests additionally intercept all opens/stat/list/mkdir, subprocess, network, DB,
loader and publisher dispatch, including before candidate inspection. Successful
test signatures and monkeypatched key constants still cannot open public gates.

New tests exercise real ephemeral-key signing/verification, known canonical
bytes, insertion order, repeatability, every selected authenticated field's
one-bit mutation, all 64 signature-byte bit flips, domain changes, bad keys and
IDs, wrong lengths/encodings, malformed/noncanonical JSON, duplicate/unknown
fields, integer/boolean substitutions, floats/nonfinite values, Unicode, missing
file sizes/inventories, historical auditor map, stale independent SHA/CI,
runtime/closure completeness, monthly consistency and malicious objects.
Correct signatures on incomplete payloads fail. There is no second million-row
fixture in the new tests. Existing full-native loaders, bounded projections,
parity validation and publisher fault regressions run unchanged.

All test commands share this prefix:

```sh
env PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  UV_CACHE_DIR=/private/tmp/badger-4b2d7-uv-cache \
  uv run --locked --offline --no-sync python \
  /private/tmp/badger-4b2d7-offline-tests.py
```

The focused selection is `tests/test_genuine_minute_signed_approval.py`,
`tests/test_genuine_minute_verification_activation.py`,
`tests/test_genuine_minute_verification_operator.py`,
`tests/test_genuine_minute_verification_wiring.py`,
`tests/test_genuine_minute_inputs.py`, `tests/test_paper_minute_integration.py`,
`tests/test_genuine_minute_price_parity.py`, `tests/test_minute_price_parity.py`.
The full-suite selection is `tests`. Logs are retained under
`/private/tmp/badger-4b2d7-{new-final,focused,full}.log`; these local temporary
records are neither CI nor approval authority.

During development, an initial test/runner syntax error was corrected, then the
first collected run returned exit 1 (94 passed, one new assertion used incorrect
readiness attribute names). That assertion was corrected to the unchanged
`status`, `readiness`, `access` interface. Two further coverage cases fixed the
receipt-precision contract and tested one-bit mutations. Initial Ruff findings
were formatting/line lengths; those were fixed before final regression runs.
No old tests or guards changed. An initial preservation-report command used a
system Python without `tomllib`; rerunning it with the locked Python succeeded.

Final executed results (all commands completed, including pytest shutdown):

| Check | Result |
| --- | --- |
| New signed-approval tests | **97 passed in 0.81s**, exit 0 |
| Combined relevant regressions | **630 passed in 211.27s**, exit 0 |
| Whole locked offline suite | **2,001 passed, 183 skipped in 385.97s**, exit 0 |
| Ruff lint and format | **93** explicit tracked/new Python files; both exit 0 |
| Protected files | **186/186** SHA-256/length, HEAD and index comparisons passed |
| Whitespace and prompt archive | Both Git diff checks, all four new-file checks and exact archive comparison passed |

All 183 skips require an explicitly configured disposable PostgreSQL server via
`BADGER_TEST_ADMIN_DSN`; no database tests are counted as passes. Both combined
logs end with `PYTEST_EXIT=0` and their enclosing processes returned exit 0,
without cleanup errors. There were no focused/full regression failures. No
Python implementation or test changed after the final 97-test run; subsequent
changes were documentation only. The tested new module SHA-256 is
`800e29ce5ac1bd848844d0f64efaab7cf0fbdbe699acff4f611d66ceead12bec`,
and the tested new test-module SHA-256 is
`0709a17dfaa097b286954b241c24a5a1eec6a066529ad3ec96d0f975f409a098`.
These are review identities, not production approval anchors.

### Protected baseline

Before implementation, all **191** tracked files were compared with both HEAD
and index bytes and snapshotted without traversing ignored artifacts.
The complete snapshot `/private/tmp/badger-4b2d7-baseline.json` has SHA-256
`29660646ada6652542216a47d0bd728b659cfebbd94ba0e0a942aafe8d004f73`.
The **186** protected files exclude only the three permitted overview documents,
`pyproject.toml` and `uv.lock`. All earlier source, tests, protocol/pin documents,
prior stage guides, replay/accounting code and configuration remain protected.

Reproducible protected identity: sorted compact JSON mapping each protected
tracked path to its baseline SHA-256 string, with one terminal newline. Hash:
`5734cf2ecee6947844a43114880cc4508ebe17f2e14fcc823159dab91ee6f3f7`.
The local mapping is `/private/tmp/badger-4b2d7-protected.json`; reconstruct it
from the baseline Git blobs using the five exclusions above. No artifact paths
are included in the tracked inventory.

| Protected implementation | Unchanged SHA-256 | Bytes |
| --- | --- | ---: |
| `genuine_minute_verification_operator.py` | `c693d5e11648619719402a62ab2fe94d69c547e04463877c0dfd9a8b3442f70e` | 22,704 |
| `genuine_minute_inputs.py` | `415c5e381dadc176a35c32f373fb4c25668e8c46b28fd2ce4d79952534a856e0` | 34,385 |
| `genuine_minute_verification_wiring.py` | `6bbb1cefef585a6dd5f4ee2fb01170cb2c5d8a72007020d9d0019be6e3bfffb6` | 13,705 |
| `forecast_data.py` | `d9ba8b84e4846d1d12dc208e4de9164e58ef418fc5381a27eef10322b9b180aa` | 5,650 |
| `minute_execution_data.py` | `84cb5f7a8c3fcfcc6b7b488cdaf22bd6e3fb8c369fdf8cf12c1435fc2da256c2` | 20,797 |
| `paper_historical_evaluation.py` | `df46fd26f857e834bd0559caa25ee525868b8de08ccbe3abb7388e9c6db193aa` | 41,830 |
| `genuine_minute_price_parity.py` | `d4b3fb3f9f06b553fce0f1303a61bc4483feb2d90840573c9c33ac9e5523d092` | 27,734 |

The substantive prompt archive matches the isolated supplied request byte for
byte; SHA-256 `62ff6936fb933c87335e001e55023596e16c1c29d2bf4299665915015f087501`.

### Change inventory

Four new files: the signed-approval module, its test module, this guide, and
`prompts/stage-04-paper/013-offline-signed-verification-approval.md`.
Five narrowly modified existing files: `docs/architecture.md`, `docs/roadmap.md`,
`docs/development-handoff.md`, `pyproject.toml`, `uv.lock`.
No production activation or broad refactoring was needed. Stop for owner review.

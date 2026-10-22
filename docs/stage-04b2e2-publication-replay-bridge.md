# Stage 4B.2E.2 — Authenticated publication-to-replay bridge

Prepared 2026-10-22 (Europe/London). **Fabricated tests only; awaiting owner review.**
Baseline HEAD: `e060bfd8cdc510a242bd06b9ef8caf8620eed99c`.
The owner supplies successful CI run `39739736818` (2,372 passed, one skipped)
for that baseline. It was not queried here and does not validate this uncommitted
change. The original verification at `94584dc4b08f06441cff3bcd7983bba1ca0afe8d`
remains a separate completed single-use operation; it was not rerun.

The substantive [request](../prompts/stage-04-paper/017-authenticated-publication-to-replay-bridge.md)
is archived without the unrelated browser/session trailer in the attachment.
No genuine publication, sign-off, signing key, signed approval, database, provider
or production infrastructure was accessed. No commit, push, activation, signing,
deployment, genuine replay or economic publication occurred.

## Private parser contract

`src/backtest_badger/genuine_minute_publication.py` adds only private pure interfaces:

```python
_Fingerprint(sha256, bytes)
_PublicationPins(manifest, authenticated_inputs, integrity, signoff)
_parse_verified_publication(
    *, manifest, authenticated_inputs, integrity, expected, signoff_claim
) -> _VerifiedPublication
_replay_verified_publication(publication, *, expected, signoff_claim)
```

The three candidate files must be explicitly supplied immutable in-memory `bytes`.
There are no paths, readers, writers, callbacks, environment overrides, CLI or
operational runner. External expected fingerprints are a separate, immutable,
required parameter. The parser never derives expected identities from candidates.
Limits are 4 KiB for manifest, 32 MiB for authenticated inputs and 1 MiB for
integrity; source-evidence JSON and the sign-off fingerprint length are bounded
at 1 MiB. Exact supplied lengths and SHA-256s are checked before JSON decoding.

**Caller-created matching bytes and fingerprints are not independently
authenticated.** A later owner-controlled runner must bind the externally retained
identities independently of the candidate payloads. Python frozen dataclasses and
private function names are not security capabilities or execution permission.

The reader rejects duplicate fields, NaN/Infinity, float overflow, noncanonical
encodings, wrong publication/science/integrity/evidence field sets, unexpected
manifest associations, or altered original false execution/economic flags. It
preserves the original compact metadata encoding and the distinct spaced scientific
encoding, including terminal newlines. Embedded canonical evidence permits valid
finite recipe floats; monetary values remain bounded exact Decimal strings.

Checks include original verification-only intent schema and flags, commit/CI
agreement, runtime, complete source/code inventories, before/after stat claims,
forecast/minute/parity and research pins, all 22 retained auditor links, monthly
associations, scientific counts, fixed train-only Ridge/scaler lineage, native
metadata and original projection digests. Retained forecast/minute/parity metadata
is re-encoded using its tracked original publisher's format and matched against
retained source identities. No original source is reopened. The unchanged pure
signed-intent schema validator is reused; no signature verification, signing or
owner-preflight invocation occurs. The retained intent is bound by the external
integrity fingerprint, not treated as a newly verified signature or current CI
attestation.

The three-file publication retains parity report/provenance and the original
parity-integrity identity, but not all original parity-integrity bytes. This reader
checks those retained links; it does not reconstruct missing original bytes or
claim a fresh source audit. The preserved original authentication is the upstream
trust boundary, anchored by separately trusted publication fingerprints.

`signoff_claim` is deliberately only `_Fingerprint`. It must equal the external
expected fingerprint. This checks claim continuity, **not sign-off contents or
approval**. No fields of the unavailable sign-off JSON schema have been invented.
There is no sign-off-authorised boolean, default successful sign-off or authority
transfer from verification consent.

## Typed conversion and shared monetary core

The parsed record retains the exact three bodies, external pins and a typed
`AuthenticatedMinuteInputs`. It requires all eight ordered forecast accounts,
2,195 rows each, and both ordered 10,979-reference streams. It reuses the existing
pure forecast converter, checks zero and train-mean baselines, canonical UTC/Decimal
representations, identity/model/source pins and a byte-identical typed roundtrip.
Missing, duplicated or reordered rows are refused rather than repaired.

Each reference stream is exactly the native hourly/forecast-minute union:
8,784 hourly marks plus 2,195 strictly next-minute references. The first source
open is 2023-12-31 20:00 UTC. Availability remains source-open +4h+60s; a 12:01
signal uses 12:02, including HOLD/noop rows. Both full-year projections and all
24 market/month source associations are retained and checked.

Before replay, the private seam reparses the original bytes against the separately
supplied pins and rejects a changed record. Calculations use the newly parsed
values, never caller-injected converted forecasts or prices. It creates distinct
`_PublicationMinuteSource` and `_PublicationReplayResult` types and the portfolio
prefix `genuine_publication_hypothetical_minute_replay` before calculation. It
never constructs a `SyntheticPriceSource`, invokes the fixture adapter, or relabels
a fixture/synthetic result. Tests use invented genuine-shaped publication bytes
and unrelated data/code identities; the resulting numbers are only test assertions.
The result explicitly states that this private seam grants no authority.

The existing price-free planner and `_replay_minute_core` supply all economics:
separate 10,000-USDT Ridge Sign, cash and inception buy-and-hold accounts per
market; 10-bps fees, 1-bp half-spread, 2-bps adverse slippage; 0.000001 quantity
step; precise Decimal arithmetic; sticky exits; ledger-prefix validation;
trade-before-mark ordering; retained ending holdings. Only Ridge is simulated.
There is no retuning, scenario selection, forecast regeneration or second engine.

The original E.1 fixture route, synthetic public APIs and monetary core are
byte-for-byte unchanged in the tracked diff. In particular:

```python
replay_genuine_minute_historical(*, approval)
# Always raises PermissionError before inspecting approval or performing I/O.
```

Pure conversion is implemented and exercised on fabricated full-year records.
Acceptance of the genuine publication is **not verified in this stage** because
its bytes remain unread. A shape/encoding discrepancy in the later authorised
read must stop the runner for review; no fallback, reshaping, rehashing or rerun
of the original verification is permitted.

## Future owner-controlled runner contract — documentation only

No executable runner or genuine-run command is delivered. Before one is approved:

1. Review this implementation and tests; separately authorise commit/push and
   independently confirm CI on the exact resulting checkout. Pin the reviewed
   runner, parser, replay and accounting implementation closure, frozen protocol,
   dependency lock and exact runtime. Check the actual checkout/implementation/
   runtime against those declarations before any authorised original read. The
   historical verification commit/runtime and future execution commit/runtime are
   distinct identities; preserve both, never overwrite historical claims.
2. Obtain explicit owner permission for read-only access to **only** the three
   original publication files in
   `artifacts/audits/stage-04b2d3-minute-inputs-v1/` and
   `~/Documents/BacktestBadgerEvidence/stage-04b2d14-publication-signoff-94584dc.json`.
   Bind their exact absolute paths in the owner-reviewed runner. Do not discover
   directories or follow symlinks; require regular files, bounded reads and
   before/after identity checks. Never read the original Stage 2B CSV, minute
   ZIP/CSV, parity sources, private signing key or verification signed approval.
3. Validate exact original bytes against these externally retained owner claims,
   supplied independently of candidate files (all remain unverified here):

   | File | Bytes | SHA-256 |
   | --- | ---: | --- |
   | manifest.json | 560 | `3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea` |
   | authenticated_inputs.json | 15,272,413 | `2581482b4b8a60fa1a53f7710ed080be7de25d50a76fcae35c8aaf64f2cb2168` |
   | integrity.json | 74,200 | `23c3d17b2e5b67de701d9a0dd22d6135a907057b9acaeb16bcbdb4cb9c613a8b` |
   | independent sign-off | 2,020 | `21b04470e861a039750bf7b665b993d332bf998fcc5b9fea47dc2c8b80f334b4` |

4. After that separately authorised sign-off read, review its actual original
   schema and authoritative fields. Implement/test their exact reconciliation
   with publication identity and original verification context. Do not treat
   fingerprint equality alone as sign-off validation. An unknown/contradictory
   field or identity blocks progression. This is an outstanding integration step,
   not implicitly supplied by the present parser.
5. Require separate explicit owner authority for **exactly one** genuine strategy
   evaluation with the frozen method and independently pinned publication. The
   prior verification signature, false economic/execution flags and successful
   sign-off do not grant this authority. Do not silently retry or broaden scope.
6. If immutable economic publication is wanted, obtain a separately approved
   fresh output directory and reviewed exclusive, no-overwrite publication plan.
   No proposed output directory was inspected here. Retain original publication,
   sign-off, execution approval and implementation identities in any later results.

All later outputs must remain hypothetical, exploratory, previously inspected
2024 validation. Retrospective archive opens are not contemporaneous quotes,
depth or fills; nothing is live trading or untouched out-of-sample performance.

## Changes, preservation and validation

Added:

- `src/backtest_badger/genuine_minute_publication.py`
- `tests/test_genuine_minute_publication.py`
- `docs/stage-04b2e2-publication-replay-bridge.md`
- `prompts/stage-04-paper/017-authenticated-publication-to-replay-bridge.md`

Documentation updates:

- `docs/stage-04b2e1-genuine-replay-integration.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`

The final guarded full suite passed **2,303 tests**, with **183 skipped**, in
555.08 seconds (9m15s), exit code zero and no warnings. All 183 skips require
`BADGER_TEST_ADMIN_DSN` for a disposable PostgreSQL server; those cases were not
executed. The run includes all **113 new bridge tests** and all final source/test
changes. Only documentation changed afterward.

The first focused run passed 88 tests in 37.61s. The intermediate scoped regression
passed 682 tests with no skips in 233.97s, covering the bridge, unchanged E.1 fixture
route, minute integration/replay, hourly replay/evaluation and verification runtime.
Its pytest iterator-parametrization warning was fixed before the final full run.
Two final manifest type-rejection cases and stricter integer/float and preservation
comparisons were included in the full run. All **99 tracked/new Python files**
passed Ruff lint and format checks with caching disabled. All eight changed/new
files passed whitespace checks, including the archived substantive prompt.

Local self-review checked the pure call boundary and fixed Python equality's
integer/float ambiguity for manifest lengths and before/after preservation claims.
Static review confirmed no direct I/O, verifier invocation, dynamic execution,
fixture adapter/replay call or synthetic-source construction in the new module.
The private seam uses the existing monetary core. This is not independent external
code review; owner review remains pending. No new CI run was triggered or observed.
The baseline CI success above remains an owner-supplied claim.

Tracked preservation checks against HEAD passed for all existing source code,
tests, `pyproject.toml`, `uv.lock`, `.github`, `AGENTS.md`, and the frozen minute
protocol/source-pin documents. HEAD remains
`e060bfd8cdc510a242bd06b9ef8caf8620eed99c`; no commit/push occurred.

The test runner
installs path and network denial before any project imports, then installs the
established offline test audit before pytest collection. It removes database
configuration, disables bytecode/cache writes, uses fresh temporary test roots,
and limits collection to `tests/`. Per-test guards additionally forbid opens,
stats, listings, source loaders, genuine verification and publication calls.
These are procedural/Python guards, not a claim of OS-enforced isolation.

Reproduce the guarded full-suite run from the checkout root (no original inputs):

```sh
UV_CACHE_DIR=/private/tmp/badger-stage4b2e2-uv-cache uv run --locked --offline python - tests <<'PYTHON'
import os
import sys
import tempfile
from pathlib import Path
ROOT = Path.cwd()
sys.dont_write_bytecode = True

def deny_path(path):
    if isinstance(path, (str, bytes, os.PathLike)):
        absolute = Path(os.path.abspath(os.fsdecode(path)))
        if absolute.is_relative_to(ROOT / 'artifacts') or any(p in absolute.parts for p in ('BacktestBadgerEvidence', 'crypto-trading-platform', '.ssh')):
            raise AssertionError('Original/private path forbidden before imports')

def audit(event, args):
    if event in ('open', 'os.listdir', 'os.scandir', 'os.chdir'):
        deny_path(args[0])
    if event.startswith('socket.') and event != 'socket.__new__':
        raise AssertionError('Network forbidden')

sys.addaudithook(audit)
for name in ('stat', 'lstat'):
    original = getattr(os, name)
    def guarded(path, *args, _original=original, **kwargs):
        deny_path(path)
        return _original(path, *args, **kwargs)
    setattr(os, name, guarded)
os.environ.pop('BADGER_TEST_ADMIN_DSN', None)
os.environ.pop('DATABASE_URL', None)
sys.path.insert(0, str(ROOT / 'tests'))
import test_genuine_minute_inputs as fixtures
fixtures.install_offline_audit()
import pytest
base = Path(tempfile.mkdtemp(prefix='badger-4b2e2-suite-')) / 'suite'
sys.exit(pytest.main(['-q', '--rootdir=tests', '--confcutdir=tests', '-p', 'no:cacheprovider', f'--basetemp={base}', *sys.argv[1:]]))
PYTHON
```

Preservation is assessed through exact tracked Git diffs, not observation or
rehashing of ignored original outputs. Their byte equality is not independently
certified here. Existing research, source declarations, protocols, verification,
replay, dependencies, lockfile, CI and pre-existing tests must remain unchanged.

**Procedural deviation:** the initial tool call read the attachment and then ran
`rg --files` before its restrictions had been processed. It returned repository
filenames. No original publication or private evidence content was opened, but
zero incidental metadata observation cannot be claimed. This was disclosed
immediately. Subsequent repository inspection used exact named paths and scoped
Git operations. The attachment's unrelated browser/session trailer appeared in
the initial tool output; it was not saved in the repository or used for this task.
Initial Ruff invocations used its default cache setting, so incidental ignored
cache writes outside the requested tracked/temp outputs cannot be excluded.
Subsequent lint/format checks explicitly disable caching; no cache tree was
inspected or removed. No original artifact directory was intentionally touched.

FABRICATED TESTS ONLY · ORIGINAL PUBLICATION UNREAD · GENUINE REPLAY NOT EXECUTED · ECONOMIC PUBLICATION NOT AUTHORISED.

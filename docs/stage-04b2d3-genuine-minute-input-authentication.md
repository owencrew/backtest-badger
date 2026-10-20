# Stage 4B.2D.3 — Minute input authentication primitives

Implementation and fabricated testing only; awaiting owner review. No genuine
source was opened, listed, statted, hashed, projected or authenticated. No replay,
strategy calculation, economic result, publication, database, provider, sibling
repository or production access occurred. Existing synthetic regression tests
exercise only their own fabricated simulations.

Starting checkout: clean `main`,
`fb7ec9d1bc5530b88c2f9c35216418c4d8d9484b`.
[Baseline CI run 39323850146](https://github.com/owencrew/backtest-badger/actions/runs/39323850146)
was independently observed as completed/success for that exact SHA. The owner's
1,760 passed / 1 skipped baseline count is supplied context, not a count extracted
from the CI logs. No new CI run, commit or push is part of this stage.

The [archived request](../prompts/stage-04-paper/009-genuine-minute-input-authentication.md)
contains only the substantive task, excluding the unrelated browser/session tail.

## Changed files and revision

Starting and final HEAD are both
`fb7ec9d1bc5530b88c2f9c35216418c4d8d9484b` on `main`; no commit was created.

| File | Change |
| --- | --- |
| [genuine_minute_inputs.py](../src/backtest_badger/genuine_minute_inputs.py) | New separate verification records, validators, bounded projector and private fixture orchestration; closed public operator interface |
| [test_genuine_minute_inputs.py](../tests/test_genuine_minute_inputs.py) | New fabricated-byte tests and offline process audit hook |
| This guide | Contract, validation, preservation and future exact one-use approval/publication design |
| [009-genuine-minute-input-authentication.md](../prompts/stage-04-paper/009-genuine-minute-input-authentication.md) | Substantive request archive only |
| [architecture.md](architecture.md) | Narrow stage/boundary update |
| [roadmap.md](roadmap.md) | Narrow stage/next-approval update |
| [development-handoff.md](development-handoff.md) | Current review priority and implementation limits |

## Implemented interface and deliberately closed operator boundary

```python
authenticate_minute_inputs(*, approval) -> AuthenticatedMinuteInputs
authenticated_inputs_json(inputs: AuthenticatedMinuteInputs) -> bytes
```

`authenticate_minute_inputs` is a reserved interface. **Every invocation raises
PermissionError before inspecting its argument or accessing any path.** There is
no accepted approval value, environment switch, CLI, real-data script or genuine
execution function. The exact-root, exact-code-pin, one-use approval and exclusive
verification publication wrapper remains a specified design below. This stage
implements the verification primitives and their private synthetic orchestration;
it does not claim that a usable genuine operator wrapper has been delivered.

Private orchestration, used only by tests:

```python
_authenticate_fixture_inputs(
    *, fixture_root, pins, monthly_sources, processed_bytes,
    code_paths, expected_code_sha256, expected_audit_code_sha256,
    hourly_monthly, forecast_loader, minute_loader, lineage_validator,
) -> AuthenticatedMinuteInputs
```

This seam rejects genuine declared hashes and roots outside an isolated temporary
directory before source I/O. It rejects repository roots, `artifacts`/sibling path
components, traversal and symlinks. Inputs live under precisely `forecast/`,
`minute/` and `parity/`; fixture code paths must stay beneath that temporary root.
All substitutions are private test dependencies. This is not an alternate genuine
source mode or an implementation of owner approval.

`AuthenticatedMinuteInputs` is a separate frozen dataclass containing immutable
nested tuples of `VerifiedForecast` and `MinuteReference`, canonical evidence
bytes, and two ordered projection fingerprints. `VerifiedForecast` retains
symbol, model, canonical original record ID, source open, assumed availability,
hypothetical strictly-next-minute timestamp, exact Decimal prediction and
original forecast CSV identity. All eight model collections remain represented.
There are no account objects, trades, balances, fees, returns or drawdowns.

Its fixed, non-constructor status is
`source_authentication_complete_verification_only_replay_not_authorised` and
`genuine_execution_authorised` is always false. Fixture evidence explicitly says
`source_kind=fabricated_temporary_fixture_bytes`. Successful tests authenticate
only invented fixture bytes. They do not authenticate the retained historical
release. Existing synthetic replay/integration type gates remain unchanged;
relabelling this record cannot make it a `PreparedMinuteBundle` or
`SyntheticPriceSource`. Python callers can fabricate objects or replace code;
this is a provenance record, not a tamper-proof capability or security sandbox.

## Verification contract

1. Require independent external fixture pins and independently supplied code
   identities before loaders. The future wrapper must instead require the exact
   frozen genuine declarations. Recheck code/documents and all named source files
   after verification; compare hashes, sizes and device/inode/mtime/ctime. Safe
   reads reject every symlink component, non-regular files, traversal and file
   replacement between path checking and descriptor opening. SHA-256 reads use
   bounded chunks, metadata reads have a two-MiB ceiling, and source opens are
   read-only. Before/after checks detect observed mutations, not hostile coordinated
   replacement/restoration between checks.
2. Open only forecast `manifest.json` and `validation_predictions.csv`; do not
   enumerate the forecast directory or inspect its other outputs. Independently
   authenticate the original bytes before trusting the loader. Preserve the
   whole-manifest recipe identity. Invoke the unchanged lineage policy without
   the synthetic integration module's hash translation. In tests, monkeypatch
   only the policy's constant declarations to invented hashes, leaving both
   function code and input metadata unchanged. The unchanged forecast loader
   actually parses fabricated CSV bytes using private test pins.
3. Check exact eight-account insertion order (the original loader constructs it),
   all 2,195 horizons in each, finite exact Decimal predictions and zero/training
   mean baseline semantics. Check five-feature order, train/validation partition
   declarations, original counts 13,782/13,783 and 2,195, train-only five-dimensional
   scaler, and frozen Ridge/scaler parameters. Original genuine manifest bytes
   would bind the complete recipe. No research CSV, labels, model fitting or
   forecast regeneration is needed. Forecast loader scheduling is solely its
   original validation; the new projection does not use its hourly entry clock.
4. Require all 50 minute files and exact top-level/raw inventories. Check every
   ZIP/sidecar byte digest and size, source URL/association, expanded size, monthly
   count, retrospective receipt, source status, implementation and complete
   metadata contract. A separately approved wrapper must call the unchanged
   native loader for complete ZIP/checksum/native reconstruction. The focused
   orchestration fixture injects a fake metadata-returning loader over clearly
   invented non-ZIP bytes; it does not pretend those fake archives passed the
   native loader. Existing native-loader regressions cover actual fabricated ZIP
   reconstruction independently.
5. Perform one additional bounded streaming pass over all 1,054,080 native rows.
   Check the literal header, ASCII, bounded physical lines, exactly four fields,
   BTCUSDT then ETHUSDT ordering, exact monthly UTC millisecond grids, fixed-point
   positive finite Decimal prices, monthly ZIP association, EOF, full CSV hash
   and byte length. Retain only the union of hourly opens and every scheduled
   forecast minute, regardless of the forecast's sign. Native processed-file
   authentication is distinct from each projected-subset fingerprint.
6. Read the five-file parity publication, never rerun the audit. Check separately
   pinned original manifest/report bytes and manifest-listed hashes/lengths for
   provenance, integrity and discrepancies. Require the actual auditor schemas,
   `source_price_parity_only`, `exact_price_parity`, strict boolean true timing
   flag, empty discrepancies/structural errors and header-only discrepancy CSV.
   Validate all overall, market, month and market-month counts and zero exact
   differences. February has 696 hours per market, so its full-grid count includes
   leap day; the genuine auditor has no separate daily report table. Check original
   hourly/minute identities, all archive associations, code/protocol evidence,
   both complete before/after inventories and provenance links. Hourly data stays
   unopened: its source manifests and identities come from pinned audit evidence.
7. Return the immutable record only after full post-read source/code preservation.
   Evidence retains original pins, all 24 monthly associations, recipe, minute
   metadata, prior publication/report/provenance, output counts, limitations and
   distinct projection fingerprints. Scientific serialization uses exact Decimal
   strings and deterministic field ordering; operational filesystem stats are
   excluded from its scientific identity. Recipe floats stay inside canonical
   metadata JSON, never prices or predictions. No issuance time is invented.

| Per market | Exact contract |
| --- | --- |
| Original model horizons | 2,195 per each of four models |
| Ridge source opens | 2023-12-31 20:00 to 2024-12-31 12:00 UTC |
| Assumed availability | Source open +4h+60s; first 00:01, last 16:01 |
| Hypothetical native minute | Strictly next minute: first 00:02, last 16:02 |
| Hourly valuation references | 8,784; last December 31 23:00 |
| Forecast references | 2,195, including potential HOLD/CASH_NOOP horizons |
| Union retained | 10,979; 21,958 total |
| Full native grid checked | 527,040; 1,054,080 total |
| Prior equal price pairs | 8,784; 17,568 total |

There is no December 31 20:01 signal, 2025 price, OHLCV reconstruction, portfolio
snapshot per source minute, trade decision or calculation of fillability.

## Frozen declarations and preservation

The module's `EXTERNAL_PINS` retains the owner's forecast, research, hourly,
minute, parity and protocol declarations, plus the existing hourly acquisition
and source-pin-document identities needed to validate the auditor's real schema.
The research and hourly declarations confer no permission to open those sources.

All 24 ZIP/sidecar pairs, URLs, sizes, expanded sizes, counts and receipt metadata
remain authoritative in the unchanged
[minute source-pin document](stage-04b2c-minute-source-pins.md), SHA-256
`967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c`.
The future wrapper must verify this document against that literal pin before
using the existing pure `genuine_minute_price_parity._minute_pins` parser. Never
observe local archive bytes and replace the declarations with their hashes.
The full native CSV declaration remains 107,002,277 bytes and
`37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233`.

A pre-edit inventory recorded SHA-256s for all 176 tracked non-artifact files.
Protected source loaders, replay/integration/evaluation code, genuine auditor,
old tests, protocols, frozen source declarations, dependencies, lockfile and
`.gitignore` must remain byte-identical. No original artifact inventory was taken.

## Future one-use approval and publication design — not executable

The next approval must authorise implementation/review of the closed operator
wrapper and then one specific verification-only invocation. Supply a human
approval record containing **all** of the following, without wildcard roots or
runtime bypasses:

- A clean full Git SHA and successful CI evidence for the reviewed implementation.
- Independent SHA-256s for the wrapper and every transitive imported project
  module, dependency/configuration file and protocol/document consumed; explicit
  independently retained prior-auditor code identities for provenance validation.
  Reject missing/extra code pins and mismatches, with pre/post rechecks. Do not
  calculate current code hashes and silently accept them as the approval pins.
- The three exact absolute roots under this checkout and their explicit files:
  `artifacts/experiments/stage-2b-v1/{manifest.json,validation_predictions.csv}`;
  `artifacts/execution/binance-1m-2024-v1/{manifest.json,minute_opens.csv,raw/...}`
  with exactly the 48 frozen ZIP/sidecars; and exactly the five files at
  `artifacts/audits/stage-04b2d1-native-parity-v1/`.
- The complete exact external pin map, source table/document identity and
  107,002,277-byte processed identity above. No alternate roots, providers,
  manifest revisions, discovery, repair, cache substitution or hash overrides.
- Explicit read-only permission for those files alone; exclusion of research,
  hourly source directory, labels, holdouts, Stage 3, providers, DB, sibling,
  production, strategy/replay and economic publication.
- One exact previously absent ignored destination. Proposed declaration only:
  `artifacts/audits/stage-04b2d3-minute-inputs-v1/`. Its existence and ignored
  status have **not** been inspected. The owner must approve that exact destination
  and one attempt; an existing destination aborts before source loading.

Required loader bindings for that future reviewed wrapper are exactly:

```python
forecast_data.load_forecasts(approved_forecast_root)  # unchanged default pins
paper_historical_evaluation._validate_lineage(original_manifest)  # no translation
minute_execution_data.load_minute_execution_data(
    approved_minute_root,
    expected_manifest_sha256=(
        "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127"
    ),
)
```

Future exclusive publication must reserve the sole approved destination using
exclusive directory creation, after scope/code checks and before the attempt's
source reads. That reservation consumes the one-use approval, including failures.
Write only `authenticated_inputs.json` (scientific verification record) and
`integrity.json` (separate operational preservation record), using exclusive files,
flush/fsync and independent readback/reparse/hash/size verification. Recheck every
approved source and code/document after output readback, before creating
`manifest.json` last. The manifest must state verification only, false execution
authority, exact file inventory and hashes/lengths. Independently read it back.
No successful manifest may remain after failed verification/readback; implement
exclusive temporary manifest publication and failure invalidation in the reviewed
wrapper, with synthetic interruption tests at every phase. Retain `failure.json`
when possible, containing phase, exception type, incomplete status and no resume;
never overwrite sources, resume, delete an attempt directory or choose another
output destination. Operational errors must not contain secrets or source data.

No publisher is implemented now because the concrete one-use operator contract
and output destination are explicitly unapproved. This design does not grant
permission to run the private fixture harness on real inputs or merely remove
its fixture restrictions. The future wrapper requires reviewed code and separate
owner approval; changing a flag is insufficient.

After verification-only approval and successful verification, a **distinct** owner
approval and reviewed genuine replay boundary must consume this separate type.
Another explicit approval covers reproduction and publication of real historical
economic results. Neither source validation nor the old price-parity flag grants
those permissions. Stop here for owner review.

## Validation record

Final local validation, completed 2026-10-20 (Europe/London):

| Check | Observed result |
| --- | --- |
| Initial new tests | 85 passed, 1 failed: incorrect test expectation for `dataclasses.replace`; corrected to `ValueError` |
| First process-audited collection | Aborted before tests: pytest attempted an ignored-artifact probe, blocked by the guard |
| Subsequent process-audited attempt | Test assertions completed, but cleanup of an older numbered temporary directory was blocked; not counted as a successful run |
| Clean focused run with dedicated temporary base | 375 passed in 137.55s, including new authentication plus existing minute replay, integration and both parity suites |
| Final additional changes | Added audited source-size linkage and two corresponding incomplete-evidence cases; included in the full-suite run below |
| Final locked offline full suite | 1,682 passed, 183 skipped in 296.74s; recovered process exit status 0 confirms successful cleanup, not merely 100% assertion progress |
| Final affected focused rerun | 22 passed, 82 deselected in 5.95s, exit 0; complete fabricated authentication and all parity rejection cases, including the final source-size edits |
| Whole-repository Ruff | Check passed; all 86 tracked/new Python files already formatted |
| Whitespace | Tracked/staged `git diff --check` and explicit new-file checks passed |
| Protected-file preservation | All 173 protected tracked non-artifact files match both the saved baseline SHA-256s and Git baseline blob bytes at `fb7ec9d1bc5530b88c2f9c35216418c4d8d9484b` |

All 183 full-suite skips require the disposable local PostgreSQL
`BADGER_TEST_ADMIN_DSN`, deliberately removed by the offline runner. These cases
were not executed. The final full suite included every source/test edit; the
resumed review changed documentation only. The earlier 375-test focused run
preceded the last source-size edits, which the final full suite and affected
focused rerun both cover.

Reviewed source SHA-256:
`415c5e381dadc176a35c32f373fb4c25668e8c46b28fd2ce4d79952534a856e0`.
Reviewed test SHA-256:
`e67108d631111f2a597bd21dcce016644d44dfbec6a80044f44a1bcb5ea630c5`.
The review found no further implementation defect requiring a change.
The public entry point remains fail-closed before argument inspection or I/O;
original-byte pins, parity provenance and the full minute grid are exercised
only with fabricated fixtures. The genuine wrapper and publisher remain
unimplemented. Genuine artifacts were neither accessed nor modified; their
contents were not rehashed because that access is prohibited.

The full-year projector test measured Python allocations with `tracemalloc` and
passed its 32-MiB peak bound. The source has 1,054,080 fabricated rows, but only
21,958 references are retained. New tests include eight-account/lineage/baseline
and CSV-shape failures; full-year clock boundaries; malformed/truncated/excess
streams and bad hashes/sizes; symlinks, traversal and open/after-read races;
changed code; wrong inventories, pins, archive associations and parity schemas;
resealed forged parity claims, incomplete preservation links and nonempty
discrepancies; strict JSON; deterministic serialization; synthetic-engine type
rejection; and actual guards against forbidden paths/network/DB access.

The initial default uv cache location was not writable in the sandbox. All
executed validation commands used an isolated writable uv cache, locked installed
dependencies and offline mode; no dependency or safeguard change was needed.

Run the offline process audit before pytest collection, and restrict collection
to `tests/` so pytest itself cannot probe ignored artifact directories:

```sh
UV_CACHE_DIR=/private/tmp/badger-uv-cache uv run --locked --offline python - <<'PY'
import runpy
import sys
import tempfile
from pathlib import Path
suite = runpy.run_path('tests/test_genuine_minute_inputs.py')
suite['install_offline_audit']()
import pytest
base = Path(tempfile.mkdtemp(prefix='badger-4b2d3-full-')).resolve() / 'suite'
sys.exit(pytest.main([
    '-q', '--rootdir=tests', '--confcutdir=tests', f'--basetemp={base}', 'tests',
]))
PY
```

The process hook blocks underlying file opens/listing under genuine artifacts and
the sibling repository, network/DNS events, and PostgreSQL connections. Separate
stat/lstat guards cover operations without a CPython audit event. Focused tests
also intercept I/O, network, DB, old audit, replay, funding and fill/valuation
boundaries. The test runner removes the disposable PostgreSQL DSN from its own
process; integration cases requiring it are reported as skips, never passes.

# Stage 4B.2E.1 — Verified-record replay integration

Prepared 2026-10-22 (Europe/London). **Fabricated tests only; awaiting owner review.**
Starting and final HEAD: `94584dc4b08f06441cff3bcd7983bba1ca0afe8d`.
The owner's baseline CI declaration is run `39668530849`, success, 2,301 passed
and one skipped. It was not queried and does not validate this uncommitted diff.
No commit, push, signing, deployment or genuine strategy execution occurred.

The owner reports successful Stage 4B.2D.13 verification and Stage 4B.2D.14
independent exact-publication readback. Those are retained private evidence,
not fixtures or execution authority. The exact three-file publication and private
sign-off declarations are archived in the [request](../prompts/stage-04-paper/016-genuine-historical-replay-integration.md).
Neither success was reverified. Their false execution/economic flags remain
unchanged. The request archive excludes unrelated browser/session content.

## API and closed authority boundary

Public API in `src/backtest_badger/genuine_minute_replay.py`:

```python
replay_genuine_minute_historical(*, approval)
```

Every call raises `PermissionError` **before inspecting approval or doing I/O**.
There is no CLI, publication reader, signing function, loader, writer, environment
switch, source-kind argument or `allow_genuine` parameter. A verification record,
manifest, synthetic source, changed status or old verification approval cannot
open this route. Authentication and strategy authority remain distinct.

Private, in-memory test interfaces:

```python
_FixtureDeclarations(
    inputs_sha256, forecast_sha256, model_recipe_sha256,
    minute_manifest_sha256, minute_file_sha256, monthly_sources,
    projection_sha256, protocol_version, protocol_sha256,
)
_adapt_fixture_inputs(inputs, *, declarations) -> _FixtureReplayInputs
_convert_verified_forecasts(accounts, forecast_sha256)
_replay_fixture_inputs(inputs, *, declarations) -> tuple[_FixtureReplayResult, ...]

# paper_minute_historical.py, used by both wrappers:
_replay_minute_core(plan, refs, marks_at, initial, *, end_exclusive)
```

`inputs` must be exactly `AuthenticatedMinuteInputs`, with its original status
and `genuine_execution_authorised is False`. Private declarations must be exactly
`_FixtureDeclarations`. Data pins matching known genuine external declarations are
refused; the frozen protocol pin intentionally remains the genuine methodology
pin. Only the two existing fabricated verification evidence kinds are accepted.
There are no path arguments or shortened-window overrides in this new seam.

The independent whole-record SHA-256 binds `authenticated_inputs_json(inputs)`,
including all forecast records, reference rows and original evidence bytes.
Separately supplied prediction/recipe/minute manifest/minute CSV pins, two
projection fingerprints, 24 ordered monthly ZIP associations and protocol
version/hash must agree with the evidence. Counts must be exact integers.
Recomputing received hashes is not authentication. New tests invent records and
use ephemeral identities; they do not invoke the genuine verifier or manufacture
a genuine manifest. Source-kind labels and dataclasses cannot establish that a
loader was used. Python privacy/frozen records are not a security sandbox against
arbitrary code, monkeypatching or a caller fabricating data and every matching pin.

The adapter retains the original verification record, including all eight accounts,
without rewriting it. It produces two Ridge forecast tuples and separate
`_FixtureMinuteSource` descriptors. Replay returns separate `_FixtureReplayResult`
objects, never synthetic `MinuteResult` objects. Source/result kind and portfolio
key prefix are `fabricated_verified_input_minute_replay`; status is
`fabricated_records_only_not_genuine_results`. Authentication explicitly says
`fabricated_records_not_source_authentication`. `genuine_execution_authorised`
and `economic_results` are false: calculated fixture balances are test assertions,
not a genuine economic publication. No genuine result/source type is activated.
A later reviewed genuine wrapper must supply distinct genuine provenance and
portfolio identities, without relabelling either existing test route.

## Scientific contract and shared algorithm

All eight ordered BTCUSDT/ETHUSDT × zero/training_mean/ridge/gradient_boosting
accounts must contain exactly 2,195 immutable `VerifiedForecast` records each.
Every record rechecks market, model, canonical identity, finite bounded Decimal,
CSV pin and UTC source grid. Zero baseline values must remain zero. Original
train-only recipe and other baseline semantics remain upstream verification
responsibilities, bound by the independent record/recipe declarations; this stage
does not rerun lineage validation, fit models or authenticate original CSV values.

Only Ridge converts to `HistoricalForecast`; prediction Decimal representation,
identity, source time and CSV pin are preserved. Availability is source open
+4h+60s; hypothetical execution is strictly the next minute (12:01 → 12:02).
First source open is 2023-12-31 20:00, last is 2024-12-31 12:00 UTC. No historical
publication latency is proven and no December 31 20:01 signal is invented.

Each market retains exactly 10,979 strictly ordered native one-minute references:
8,784 hourly marks union 2,195 forecast-related minutes, including HOLD/noop
references. No sorting, gap filling or deduplication of input is allowed. Every
row rechecks native identity, UTC timestamp, positive Decimal price, processed
CSV pin and market/month ZIP pin. Ordered projection digests are rechecked against
independent declarations. Full source authenticity, depth and fillability are
not inferred from these checks or from prior price parity.

The only protected replay change extracts the existing accounting loop as a
private pure function. Its loop AST is identical to the baseline. Synthetic
public checks, source type/status, planning order, short fixtures, missing-signal
semantics and complete-year behavior are retained. The new wrapper reuses the
same price-free planner, strategy evaluator, monetary loop and account validator.
It creates separate portfolios with the new test identity before replay; it does
not edit identities after calculating trades.

Both markets independently retain 10,000-USDT Ridge, cash and fee-aware B&H
accounts, quantity step 0.000001, 10-bps fees, 1-bp half-spread and 2-bps adverse
slippage. B&H buys at inception; Ridge first trades at 00:02. Ledger prefixes,
trade-before-mark ordering and open ending holdings are unchanged. No retuning,
threshold selection, outcome override or economic scenario was added.

## File inventory and preservation

Modified:

- `src/backtest_badger/paper_minute_historical.py`: private shared loop extraction.
- `docs/architecture.md`, `docs/roadmap.md`, `docs/development-handoff.md`: stage
  status, supplied verification context and next gate.

Added:

- `src/backtest_badger/genuine_minute_replay.py`: closed public API, private
  structural conversion, fixture declarations and replay wrapper.
- `tests/test_genuine_minute_replay.py`: fabricated-record positive/negative tests.
- This guide.
- `prompts/stage-04-paper/016-genuine-historical-replay-integration.md`: substantive
  request only, included in whitespace checks.

Existing verification/signature/publication modules, source pins, frozen protocols,
scientific methods, old tests, synthetic integration/hourly evaluation, dependency
files and CLI are unchanged. Preservation is assessed through tracked Git diffs
and the shared-loop AST comparison. Original ignored files and private evidence
were not rehashed: their byte equality is not independently certified here.

**Procedural deviation:** before reading the attached restrictions, the first
tool call included `rg --files` and `git status --short`. These were prohibited
by this request. No genuine file contents were deliberately opened, but those
commands cannot support a claim of zero incidental metadata observation. This
was disclosed immediately. Subsequent orientation used explicit Git/named-file
reads; no genuine publication/sign-off inspection, verifier, audit or replay ran.
No OS-enforced isolation is claimed. No original output/source directory was
intentionally written or modified.

## Validation

The final focused run passed **71 tests** in 38.93s. The scoped regression run
passed **500 tests** in 136.32s: minute replay/integration, historical replay and
evaluation, and genuine-verification runtime tests. Both had zero skips.
Ruff lint and format checks passed for all **97 tracked/new Python files**.
Tracked/staged and all four added-file whitespace checks passed, including the
archived prompt. The final offline full suite exited successfully with **2,190
passed, 183 skipped in 489.18s**. Every skip requires `BADGER_TEST_ADMIN_DSN`
for a disposable PostgreSQL server, deliberately disabled in this stage. Those
183 database cases were not executed. The full suite includes all final source
and test changes; only documentation was updated afterward.

The first focused attempt failed during collection because pytest inspected the
hostile approval object; moving its construction inside the test fixed the test.
The next run passed 68 tests; three further guard/isolation tests brought the final
focused run to 71. Ruff initially found one long docstring, now corrected. The
first new-file whitespace wrapper misinterpreted Git's normal no-index difference
exit code; the corrected check accepted difference-only exit codes and required
empty diagnostic output for every file.

The runner installs the existing offline audit before pytest collection, adds
private evidence/SSH path guards, removes database environment settings, disables
pytest cache writes and uses a dedicated temporary root. Collection is restricted
to `tests/`. New tests also block opens, stats, listing, publication, loaders and
verifier calls during their execution. No network/provider/database service is
contacted. Reproduce the full-suite invocation from the checkout root:

```sh
UV_CACHE_DIR=/private/tmp/badger-stage4b2e-uv-cache uv run --locked --offline python - <<'PYTHON'
import os
import runpy
import sys
import tempfile
from pathlib import Path
suite = runpy.run_path('tests/test_genuine_minute_inputs.py')
original = suite['check_path']
def check_path(path):
    original(path)
    if isinstance(path, (str, bytes, os.PathLike)):
        parts = Path(os.path.abspath(os.fsdecode(path))).parts
        if 'BacktestBadgerEvidence' in parts or '.ssh' in parts:
            suite['forbidden']()
suite['install_offline_audit'].__globals__['check_path'] = check_path
suite['install_offline_audit']()
import pytest
base = Path(tempfile.mkdtemp(prefix='badger-stage4b2e-tests-')).resolve() / 'suite'
sys.exit(pytest.main([
    '-q', '--rootdir=tests', '--confcutdir=tests', '-p', 'no:cacheprovider',
    f'--basetemp={base}', 'tests',
]))
PYTHON
```

## Limitations and next owner gate

This implements the reusable conversion and single accounting seam, tested with
invented full-year records. **Exact-publication ingestion and genuine execution
remain closed and unimplemented.** It does not authenticate the declared genuine
publication, independent sign-off or original sources. It is not a genuine 2024
backtest, economic finding, untouched out-of-sample validation or live profit claim.
Any later 2024 research must be labelled exploratory, previously inspected
validation, with assumed availability and hypothetical execution limitations.

Next decision: review this uncommitted eight-file diff and the procedural deviation.
Only after acceptance may the owner separately authorise commit/push and CI.
A subsequent scope must review the exact-publication reader: independently pinned
manifest/authenticated-input/integrity byte lengths and SHA-256s, exact manifest
associations, independent sign-off, original false flags, code/runtime identities,
and approved read-only paths. Do not derive authority from edited metadata or
reuse the earlier verification consent. Separately authorise any genuine strategy
execution and, separately, any economic publication. No such permission is granted
by this stage, and no later access/run command is provided here.

SYNTHETIC TESTS ONLY · GENUINE BACKTEST NOT EXECUTED · AWAITING OWNER REVIEW.

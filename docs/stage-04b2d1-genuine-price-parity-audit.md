# Stage 4B.2D.1 — Authenticated opening-price parity

**Completed 2026-10-19 (Europe/Ljubljana): genuine exact-price parity passed.**
The authorised operator invocation ran once, after all Phase A gates passed.
Both complete pinned releases authenticated; all 17,568 HH:00 prices were equal.
No forecasts or economic calculations were accessed or run.
The [authorisation gate](stage-04b2d1-genuine-hourly-minute-parity-audit.md) fixes
scope, stop conditions and the clean starting revision.

## Separate API and protected components

`src/backtest_badger/genuine_minute_price_parity.py` adds one public entry point:

```python
audit_genuine_minute_price_parity(
    *, hourly_directory, minute_directory, destination,
    expected_pins, expected_implementation_sha256,
)
```

Every argument is mandatory. The public adapter requires the two exact approved
paths, exact known external pins, full-year grids and sole fresh destination.
There is no CLI, automatic source discovery, download, cache or runtime fixture
mode. Fabricated wrapper tests monkeypatch boundaries only in pytest; the genuine
operator path has no override for alternative releases or abbreviated grids.

The existing `minute_price_parity.audit_minute_price_parity` remains synthetic
only. Its status check, both upstream source loaders, both replay engines, account
and evaluation modules, existing tests, dependencies and lockfile are unchanged.
The new module imports existing hourly pins/constants without invoking forecasts
or evaluation. Both approved protocols and Stage 4B.2C engineering/pin documents
remain byte-identical. A pre-edit SHA-256 inventory covers all 167 tracked files.

## Authoritative identities

Pins originate from the owner, reviewed hourly constants and the Git-tracked
minute source-freeze record, never from newly opened source bytes.

| Evidence | SHA-256 |
| --- | --- |
| Hourly manifest | `1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d` |
| Hourly CSV | `39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a` |
| Hourly acquisition | `926697a89eb7c018ca5913f1e3c4c1170715db5639d444a58a78012e92aec055` |
| Minute manifest | `673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127` |
| Minute CSV, 107,002,277 bytes | `37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233` |
| Hourly protocol | `b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b` |
| Minute protocol | `c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b` |
| Minute source-pin document | `967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c` |
| Unchanged hourly loader | `29f6d0ac446a1fe58030bee0d6502854d462eb388b1e27eb060cba3d6b969d7a` |
| Unchanged minute loader | `84cb5f7a8c3fcfcc6b7b488cdaf22bd6e3fb8c369fdf8cf12c1435fc2da256c2` |
| Unchanged uv.lock | `81ca2ffed631698425fc5921cfdf8b5c2160a3e8f4afbec249a164fa5984c118` |

All 24 hourly ZIP pins are imported unchanged from
`paper_historical_evaluation.MONTHLY_ZIP_SHA256`. The minute document's exact
24-row hash/size/count table and 24-row URL/receipt table are parsed only after
its fixed document hash passes. ZIP and checksum-body hashes, lengths, expanded
CSV lengths, source associations and counts must match those declarations.
Different native releases retain different manifests and source ZIP hashes.

## Authentication and bounded source I/O

1. Reject unapproved path arguments, all symlink components (including ancestors
   and broken links), an existing destination, wrong external/code/document pins.
2. Require exact original inventories: 51 hourly and 50 minute files. Hash every
   regular file with bounded reads; retain byte size and device/inode/mtime/ctime.
   Reject missing, unexpected or partial evidence without following its contents.
3. Check original manifest/processed/acquisition pins before trusting metadata or
   invoking loaders. Check minute CSV size. Validate source revision, coverage,
   monthly source/URL/interval association and independent raw-source hashes.
4. Call unchanged `load_execution_data(Path(hourly_directory))`, which verifies
   all 24 ZIP/sidecar pairs and reproduces the exact original hourly CSV. Verify
   returned metadata against the independently pinned original manifest.
5. Call unchanged `load_minute_execution_data(minute_directory,
   expected_manifest_sha256=MINUTE_MANIFEST_SHA256)`. It verifies every native
   archive field/grid/checksum/CRC, reconstructs the complete CSV byte-for-byte,
   checks canonical metadata and returns verified metadata only.
6. Make one additional streaming projection pass over the minute CSV. Check the
   exact ASCII header, four CSV fields, strict BTCUSDT then ETHUSDT/month order,
   every exact millisecond timestamp and monthly source hash, bounded native
   fixed-point positive Decimal prices, final EOF, full-file hash and byte count.
   Require 527,040 rows per symbol; retain only 8,784 HH:00 observations per symbol.
7. Reject any missing, duplicate, reordered, off-hour, wrong-market or endpoint
   hourly projection. Both projections must contain exactly 17,568 identities.
8. Rehash all 101 files and compare every stat after comparison, then repeat this
   check after on-disk output verification immediately before final publication.
   Check the fixed code/document allowlist at both boundaries. No source writes.

The projector does not materialise a million price records. Full source loading
is mandatory even when the projection would match. The original loaders also
check original sidecar bodies and filename/checksum associations. They are
existing validators, not newly independent native archive parsers.

Before/after SHA-256s are authoritative; stats are additional mutation checks.
This contract detects observed changes, not adversarial coordinated replacement
and restoration between checks. Freeze other writers during the run. There are
no changes to the protected loaders' filesystem APIs.

## Predeclared comparison and report schema

Compare exact Decimal native 1h opens with native 1m opens at every matching
HH:00 from 2024-01-01 00:00 through 2024-12-31 23:00 UTC. No tolerance, rounding,
`isclose`, substitution or aggregated reconstruction. Numerically equal Decimal
strings with different precision compare equal. Subtraction/sums use the existing
isolated 160-digit context with inexact arithmetic trapped; unsupported precision
fails instead of rounding.

`parity_report.json` has full overall, per-symbol, per-month and per-symbol/month
buckets. Each contains expected and matched-identity counts, equal/mismatched
price counts, positive/negative differences, absolute-difference sum/min/max and
an exact mean as numerator/denominator. Min/max and mean cover **all** matched
observations, including zero differences. No floating-point or rounded summary
is authoritative. All 12 months and both symbols remain represented.

Every discrepancy has symbol, UTC hour, exact hourly/minute prices, signed
minute-minus-hourly difference, absolute difference and both ZIP/manifest hashes.
The report includes all discrepancies without truncation. Native intervals remain
3600 and 60. Structural failures raise rather than returning partial valid grids.
A complete report has an empty structural-errors list because all grids verified.

`direct_timing_comparison_permitted` is true only for authenticated complete grids
and zero exact mismatches. Otherwise a completed comparison is
`source_price_discrepancy`, with a false flag. This flag does not grant authority
to load forecasts or run a trading comparison.

## Exclusive publication and reproduction

| File | Contract |
| --- | --- |
| `provenance.json` | Both original manifests, expected external pins, code/document/lock hashes, original release identities and sources, counts, all source file hashes/sizes, methods and limitations |
| `parity_report.json` | Deterministic scientific result, all buckets and every discrepancy; exact Decimal strings |
| `discrepancies.csv` | Same complete discrepancy list with fixed columns and a header even when empty |
| `integrity.json` | Separate operational before/after file hashes and filesystem stats; excluded from scientific-byte determinism claims |
| `manifest.json` | Canonical JSON, written last after on-disk verification; exact output lengths and hashes, parity status/flag, `kind=source_price_parity_only` |
| `failure.json` | Best-effort incomplete-attempt evidence after reservation; no successful final manifest |

Every write uses exclusive `.partial` creation, fsync and exclusive hard-link
publication. Existing destinations are refused, including empty directories and
symlinks. Read back all outputs, compare against computed payload bytes, and
cross-check CSV against JSON discrepancy/count/flag evidence before the manifest.
An exception after linking the manifest removes that success marker and rethrows;
a hard kill can leave partial files, which are not completed evidence. A failed
attempt is never resumed or silently assigned another directory.

Scientific JSON and CSV contain no clock, output-directory or filesystem-stat
fields. Repeated identical inputs/code produce identical scientific bytes.
Operational stats can legitimately differ on copies; the final manifest binds
that particular integrity envelope as well. Retain its SHA-256 externally.

Source equality proves no contemporaneous access, publication order, quote,
liquidity, latency, exchange filter or actual fillability. Sidecars are unsigned;
local consistency is not a signed provider attestation. The source release status
is preserved, and this audit is not a completed trade-evaluation artifact.

## Validation and operator record

All Phase A gates passed before the first genuine source open. No source or
preflight failure may be repaired or retried under this authorisation.

### Exact operator command

The operator script is outside the repository and includes an audit hook that
blocks other artifacts, source writes and network/database sockets. It freezes
all tracked and new nonignored worktree files before/after the single call.
The code pins are recorded separately after Phase A; they are never derived
from market-data files. Its exact contents follow.

```python
"""Single explicitly authorised local invocation; run only after Phase A passes."""

import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/owencrew/Code/backtest-badger")
HEAD = "38a27902542f94d47c620e3516cfff53b32be058"
SOURCE_PATHS = (
    ROOT / "artifacts/execution/binance-1h-2024-v1",
    ROOT / "artifacts/execution/binance-1m-2024-v1",
)
DESTINATION = ROOT / "artifacts/audits/stage-04b2d1-native-parity-v1"


def boundary(event, args):
    if event in (
        "socket.connect",
        "socket.connect_ex",
        "socket.getaddrinfo",
        "socket.bind",
    ):
        raise RuntimeError("Authorised audit forbids network/database access")
    if event in ("open", "os.listdir", "os.scandir") and args:
        path = args[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(path)).absolute()
            if "crypto-trading-platform" in path.parts:
                raise RuntimeError("Historical sibling access forbidden")
            if path.is_relative_to(ROOT / "artifacts"):
                if not any(
                    path.is_relative_to(p) for p in (*SOURCE_PATHS, DESTINATION)
                ):
                    raise RuntimeError("Artifact access outside exact authorisation")
                if event == "open":
                    mode, flags = args[1], args[2]
                    writing = (
                        isinstance(mode, str) and any(c in mode for c in "wax+")
                    ) or (
                        isinstance(flags, int)
                        and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
                    )
                    if writing and not path.is_relative_to(DESTINATION):
                        raise RuntimeError("Source write forbidden")


sys.addaudithook(boundary)
# Standard module imports are side-effect free; only the two approved loaders run.
from backtest_badger import genuine_minute_price_parity as audit


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def freeze():
    names = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
        )
        .decode()
        .split("\0")
    )
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in names
        if name and (ROOT / name).is_file()
    }


assert git("rev-parse", "HEAD") == HEAD
assert git("branch", "--show-current") == "main"
for relative in (audit.HOURLY_PATH, audit.MINUTE_PATH, audit.OUTPUT_PATH):
    assert git("check-ignore", relative) == relative
expected_code = json.loads(Path("/tmp/badger-4b2d1-approved-code.json").read_text())
assert audit._implementation(expected_code) == expected_code
before = freeze()
status_before = git("status", "--porcelain=v1", "--untracked-files=all")
print("Phase B: invoking authenticated read-only audit exactly once.", flush=True)
try:
    result = audit.audit_genuine_minute_price_parity(
        hourly_directory=SOURCE_PATHS[0],
        minute_directory=SOURCE_PATHS[1],
        destination=DESTINATION,
        expected_pins=json.loads(json.dumps(audit.EXTERNAL_PINS)),
        expected_implementation_sha256=expected_code,
    )
finally:
    assert freeze() == before, "Worktree changed during genuine audit"
    assert git("status", "--porcelain=v1", "--untracked-files=all") == status_before
    assert git("rev-parse", "HEAD") == HEAD
    assert audit._implementation(expected_code) == expected_code
print(
    json.dumps(
        {
            "result": result,
            "worktree_unchanged_during_run": True,
            "auditor_sha256": expected_code[
                "src/backtest_badger/genuine_minute_price_parity.py"
            ],
            "operator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        indent=2,
        sort_keys=True,
    ),
    flush=True,
)
```

Invocation, only after all Phase A gates pass:

```sh
env -u BADGER_TEST_ADMIN_DSN PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  uv --cache-dir /tmp/badger-4b2d1-uv-cache run --locked --offline --no-sync \
  python -u /tmp/badger-4b2d1-operator.py
```

### Protected-file preservation before genuine access

All 164 protected pre-existing tracked files match the clean starting snapshot.
Only the three authorised architecture/roadmap/handoff documents differ. The
following SHA-256s are identical **before and after implementation**; Phase B
will recheck its fixed code/document allowlist and freeze the entire worktree.

| Protected file | Before = after SHA-256 |
| --- | --- |
| `docs/stage-04b2-historical-validation-protocol.md` | `b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b` |
| `docs/stage-04b2c-minute-execution-protocol.md` | `c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b` |
| `docs/stage-04b2c-minute-data-engineering.md` | `4799eb4eb7df9abae156d0851a75f0da1ec1bc30abd8d5267fdcbbfc22e0363c` |
| `docs/stage-04b2c-minute-source-pins.md` | `967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c` |
| `src/backtest_badger/execution_data.py` | `29f6d0ac446a1fe58030bee0d6502854d462eb388b1e27eb060cba3d6b969d7a` |
| `src/backtest_badger/minute_execution_data.py` | `84cb5f7a8c3fcfcc6b7b488cdaf22bd6e3fb8c369fdf8cf12c1435fc2da256c2` |
| `src/backtest_badger/minute_price_parity.py` | `660e4eb4e276778e08319e7d343746c6a01311272f8c239845f3da99481820c8` |
| `src/backtest_badger/paper_historical.py` | `910f8d8107c6360fac565dce463f686f82478b8e459d4b6768ebb679c515ae43` |
| `src/backtest_badger/paper_minute_historical.py` | `b0ff96d747136373a4a562f3fb8f7fe77b705ed5208c2c12cd25ad266936bf25` |
| `src/backtest_badger/paper_historical_evaluation.py` | `df46fd26f857e834bd0559caa25ee525868b8de08ccbe3abb7388e9c6db193aa` |
| `src/backtest_badger/paper_historical_publication.py` | `c019b55ffde53486137586c1e3f97838fcd7d07d57f36aac011a1a50c893b16d` |
| `src/backtest_badger/paper_accounting.py` | `532ffd69e785dc7429403bb67da87bf82d563d60a5c9cfc3f36a69577eae34b6` |
| `src/backtest_badger/paper_execution.py` | `ed054f523d7a7c29978635c3426345186ea94dd11fb2c480543353b97861959b` |
| `src/backtest_badger/paper_types.py` | `39a7a46b2631f4d3416df34fa866e4ba8e42c51e7e1b4775ab19b9ecfd371067` |
| `uv.lock` | `81ca2ffed631698425fc5921cfdf8b5c2160a3e8f4afbec249a164fa5984c118` |
| `pyproject.toml` | `65185e707b97ac92a120cd868c1d1a431e3393068c0886e055fb20da8d90d9ea` |
| `.gitignore` | `9e12ce0dbd7f13bddd46ab0077114e47ff5f5749775f02ca1e6a4f5182f0b983` |

Complete protected-inventory SHA-256: `471d12624bf2fbebc14c012c30081f2b34cbfdbe4f1773062dc95de7d32985e8`.
This fingerprints the sorted compact JSON mapping of the 164 repository-relative
paths to their SHA-256s, with a final newline. The clean baseline commit retains
every original byte, so this inventory can be reconstructed without source-data
access. Old tests and all other implementation modules are included.

### Executed Phase A checks

- Final focused synthetic tests: **72 passed in 47.18 seconds**. The earlier
  70-test run also passed before two additional publication tests were added.
- Whole-repository Ruff lint passed; formatting check passed for 149 files.
- Tracked/staged diff whitespace and all five new files checked separately.
- All 164 protected original files remain byte-identical; substantive prompt
  matches the request through the suggested commit message.
- Installed environment: Python 3.12.13, uv 0.13.0; locked/offline/no-sync,
  no dependency installation. No GitHub CI run for these local changes.
- Full locked offline suite: **1,465 passed, 183 skipped in 310.56 seconds**.
  All 183 skips require an explicitly configured isolated PostgreSQL server.
  No database was accessed; these skips are not passes.

Commands:

```sh
env -u BADGER_TEST_ADMIN_DSN PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  PYTHONPATH=/tmp/badger-4b2d1-offline \
  uv --cache-dir /tmp/badger-4b2d1-uv-cache run --locked --offline --no-sync \
  pytest -q tests/test_genuine_minute_price_parity.py -p no:cacheprovider
env -u BADGER_TEST_ADMIN_DSN PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  PYTHONPATH=/tmp/badger-4b2d1-offline \
  uv --cache-dir /tmp/badger-4b2d1-uv-cache run --locked --offline --no-sync \
  pytest -q -p no:cacheprovider
uv --cache-dir /tmp/badger-4b2d1-uv-cache run --locked --offline --no-sync \
  ruff check . --no-cache
uv --cache-dir /tmp/badger-4b2d1-uv-cache run --locked --offline --no-sync \
  ruff format --check . --no-cache
git diff --check
git diff --cached --check
```

The session-only `sitecustomize.py` on the test PYTHONPATH uses Python audit
events to reject opens/listing under genuine repository artifacts and socket
connections/binds/name resolution. Focused tests also forbid real loader calls,
network and psycopg entry points; wrapper loaders are explicitly fabricated
boundaries. This guard is a local validation aid, not a dependency or CI change.

### Frozen pre-run implementation identities

- `src/backtest_badger/genuine_minute_price_parity.py`: `d4b3fb3f9f06b553fce0f1303a61bc4483feb2d90840573c9c33ac9e5523d092`.
- `tests/test_genuine_minute_price_parity.py`: `2baa3f377023b10addb332af77eb6506ad7452d8df7c114660ab4557795690c8`.
- Operator script: `c62dcfa84d8ff5c203dd2ee39374d33101bad42b224cfa80a6b57b8ff3835f40`.

The exact code-pin preparation command, executed after all tests passed and
before genuine source access, was:

```python
from pathlib import Path
import hashlib, json
from backtest_badger import genuine_minute_price_parity as audit

pins = {
    name: hashlib.sha256((audit.ROOT / name).read_bytes()).hexdigest()
    for name in audit.IMPLEMENTATION_FILES
}
Path("/tmp/badger-4b2d1-approved-code.json").write_text(
    json.dumps(pins, sort_keys=True, indent=2) + "\n"
)
audit._implementation(pins)
```

Manual review checked the restricted I/O path, external pins, complete-grid
validation, exact arithmetic and failure/publication gates. No unresolved issue
remained. This is local review, not independent reviewer or new GitHub CI evidence.

## Genuine audit outcome and completion record

The documented operator command was invoked **once** and exited successfully.
The auditor SHA-256 remained
`d4b3fb3f9f06b553fce0f1303a61bc4483feb2d90840573c9c33ac9e5523d092`
before and after the run. The operator SHA-256 was
`c62dcfa84d8ff5c203dd2ee39374d33101bad42b224cfa80a6b57b8ff3835f40`.
All tracked and new nonignored worktree file bytes, Git status and HEAD remained
unchanged throughout the run. Only documentation was updated afterwards.

| Market | Authenticated native 1h rows | Authenticated native 1m rows | HH:00 pairs | Exact mismatches |
| --- | ---: | ---: | ---: | ---: |
| BTCUSDT | 8,784 | 527,040 | 8,784 | 0 |
| ETHUSDT | 8,784 | 527,040 | 8,784 | 0 |
| Combined | 17,568 | 1,054,080 | 17,568 | 0 |

Status: **`exact_price_parity`**.
`direct_timing_comparison_permitted=true`. Missing, duplicated, extra, reordered,
wrong-market and off-grid observations: **zero**. Positive and negative price
differences: **zero**. Every monthly bucket also has zero discrepancies; leap
February contains 696 matched hours per market. Exact absolute-difference sum
is `0E-8`, min `0E-8`, max `0`; the mean is retained as `0E-8 / 17568`.
These are exact Decimal representations of zero, with no rounding or tolerance.

Only the two authorised 2024 execution source directories were opened as
scientific inputs. No other artifacts, original forecasts, private datasets,
2025–2026 holdouts, providers, databases or production infrastructure were
inspected. The new audit output directory was separately read back for
verification. No strategy, trade, account, ledger, P&L, return, Sharpe, drawdown
or economic result was calculated from genuine data.

All **101 source files** passed complete SHA-256/size/device/inode/mtime/ctime
comparison after source validation/comparison and again immediately before the
final manifest. All 164 protected pre-existing tracked files, including every
old test and frozen protocol/source record, still match their original hashes.
The protected hash table above therefore applies **before and after Phase B**
as well. Source directories were never written or repaired. No source changes,
preflight failures, partial output, failure record or retry occurred.

### Published evidence

Output: `artifacts/audits/stage-04b2d1-native-parity-v1/` (ignored by Git).

| File | Exact bytes | SHA-256 |
| --- | ---: | --- |
| `discrepancies.csv` | 162 | `0afb86f6389a1ab6a6931f0a96bd3ef0484bbd172f8bcd8b2fc7b8e9dea4a755` |
| `integrity.json` | 61,684 | `5594e11f44cbc0e820595501a508b47f6f7b55508de3c2895c7b6ae6e64ab395` |
| `parity_report.json` | 18,452 | `0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb` |
| `provenance.json` | 60,610 | `fb44c49bf468ca976706567f7997ff61cdfe3f5157eca387c796b73fba0556eb` |
| `manifest.json` | 740 | `53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d` |

The manifest hash above is retained externally here for later owner pinning.
A separate final inspection of the five published files verified their inventory,
lengths and hashes against that external identity, the zero-discrepancy report,
and before/after integrity equality. It read only audit outputs and did not rerun
the genuine comparison or reopen either source release.

### Changed files and strict next gate

Added the separate auditor, its 72 focused tests, this implementation/report
guide, the authorisation-gate guide and the substantive prompt archive. Updated
only `docs/architecture.md`, `docs/roadmap.md` and `docs/development-handoff.md`
among existing files. No commit, push, deployment or GitHub CI run occurred.
Starting/final HEAD is `38a27902542f94d47c620e3516cfff53b32be058` on `main`.

Genuine archived opening-price parity is **scientifically clear for these exact
retained releases**. It establishes no historical execution availability or
fillability and is not an economic finding. Stop here for owner review.
The next gate requires separate explicit owner approval to **design and test**
a genuine forecast/minute replay adapter. Actual strategy calculation and
immutable economic publication require later explicit authorisation. This
passing parity result grants neither permission.

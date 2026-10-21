# Stage 4B.2D.10 — Read-only historical evidence

Completed 2026-10-21 (Europe/London), within the owner's explicit three-file
read-only scope. Starting and final reviewed `main`:
`d82a9a042efe8ae7a6348c3f4deb5138de07fa92`.
The owner/reviewer supplied successful Actions run `39660572895`
(2,301 passed, 1 skipped); no network query or new CI run was performed here.
Git confirmed the expected root, branch and clean tracked baseline before access.

## Forecast metadata only

| Original evidence name | Measured bytes | Earlier declared SHA-256 (not freshly verified) |
| --- | ---: | --- |
| `forecast/manifest.json` | 16,757 | `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581` |
| `forecast/validation_predictions.csv` | 3,031,672 | `e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674` |

Original paths are the two named files under
`artifacts/experiments/stage-2b-v1/`. Only no-follow file metadata was measured;
neither forecast file was opened, read, hashed, streamed, mapped or copied.
**These sizes do not establish that current bytes match the earlier hashes.**
Later separately authorised verification must authenticate actual contents.

## Authenticated historical provenance

Only `artifacts/audits/stage-04b2d1-native-parity-v1/provenance.json` was opened,
once, read-only with `O_NOFOLLOW`. Its complete original **60,610 bytes** matched
the independently retained Stage 4B.2D.1 reference SHA-256:
`fb44c49bf468ca976706567f7997ff61cdfe3f5157eca387c796b73fba0556eb`.
The reference came from the tracked completion report, not current source hashes.

Exact ancestor components were checked without enumeration and anchored using
no-follow directory descriptors. Both forecasts required positive regular-file
sizes. Provenance required matching regular-file `fstat`, exact size, a bounded
read and one extra-byte EOF check. Its SHA-256 passed **before** UTF-8/JSON parsing;
duplicate keys, nonfinite constants and noncanonical bytes were rejected.
Source and ancestor metadata matched before/after acquisition. These checks do
not exclude coordinated replacement and restoration between observations.

Schema: `genuine-native-parity-provenance-v1`;
kind: `source_price_parity_only`. `expected_external_pins` matched the tracked
auditor's complete hourly/minute/document pin structure and values, which also
matched the Stage 4B.2D.1 report. The map had exactly the 22 names declared by
`IMPLEMENTATION_FILES`, each with a lowercase 64-digit digest. The independently
frozen auditor and three protocol/source-pin-document claims also matched.
Tracked contracts were inspected as text/AST, without importing application code.

All hashes below are **historical claims recovered from authenticated original
provenance**, not hashes freshly calculated from today's checkout.

| Original auditor-listed file | Historical SHA-256 |
| --- | --- |
| `docs/stage-04b2-historical-validation-protocol.md` | `b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b` |
| `docs/stage-04b2c-minute-data-engineering.md` | `4799eb4eb7df9abae156d0851a75f0da1ec1bc30abd8d5267fdcbbfc22e0363c` |
| `docs/stage-04b2c-minute-execution-protocol.md` | `c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b` |
| `docs/stage-04b2c-minute-source-pins.md` | `967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c` |
| `pyproject.toml` | `65185e707b97ac92a120cd868c1d1a431e3393068c0886e055fb20da8d90d9ea` |
| `src/backtest_badger/archives.py` | `59e57bc50f8328f6fc8ecd280c5e32777a41bfb2ffc822c7f8cfed9dbb9a616f` |
| `src/backtest_badger/candles.py` | `c07cde054ae5284e96672fc7e436a669466361b47d8cee66544d83e889c76203` |
| `src/backtest_badger/execution_data.py` | `29f6d0ac446a1fe58030bee0d6502854d462eb388b1e27eb060cba3d6b969d7a` |
| `src/backtest_badger/frozen.py` | `09c6ff1c4fb71f923e7e3876b3613d8e8c4b494f2916b39a297f4419d81fcd66` |
| `src/backtest_badger/genuine_minute_price_parity.py` | `d4b3fb3f9f06b553fce0f1303a61bc4483feb2d90840573c9c33ac9e5523d092` |
| `src/backtest_badger/ingestion.py` | `025436994b355ee168e49654cf3188be22b46492748fe70adaa9b90b8f4aa8a3` |
| `src/backtest_badger/minute_execution_data.py` | `84cb5f7a8c3fcfcc6b7b488cdaf22bd6e3fb8c369fdf8cf12c1435fc2da256c2` |
| `src/backtest_badger/minute_price_parity.py` | `660e4eb4e276778e08319e7d343746c6a01311272f8c239845f3da99481820c8` |
| `src/backtest_badger/model_data.py` | `4ce532d0972866cd5e12396a51a79b7c28912c88debfdd7f61a4d1c4dd302a3b` |
| `src/backtest_badger/paper_accounting.py` | `532ffd69e785dc7429403bb67da87bf82d563d60a5c9cfc3f36a69577eae34b6` |
| `src/backtest_badger/paper_execution.py` | `ed054f523d7a7c29978635c3426345186ea94dd11fb2c480543353b97861959b` |
| `src/backtest_badger/paper_historical.py` | `910f8d8107c6360fac565dce463f686f82478b8e459d4b6768ebb679c515ae43` |
| `src/backtest_badger/paper_historical_evaluation.py` | `df46fd26f857e834bd0559caa25ee525868b8de08ccbe3abb7388e9c6db193aa` |
| `src/backtest_badger/paper_minute_historical.py` | `b0ff96d747136373a4a562f3fb8f7fe77b705ed5208c2c12cd25ad266936bf25` |
| `src/backtest_badger/paper_strategy.py` | `55df7d0aadad660c849f7785ebcfe6e81d7bcc18cd610fd4233de8e7aca37eac` |
| `src/backtest_badger/paper_types.py` | `39a7a46b2631f4d3416df34fa866e4ba8e42c51e7e1b4775ab19b9ecfd371067` |
| `uv.lock` | `81ca2ffed631698425fc5921cfdf8b5c2160a3e8f4afbec249a164fa5984c118` |

## Detached retention and boundary

The deterministic, sorted, two-space-indented UTF-8 JSON with final LF uses
schema `stage-04b2d10-historical-evidence-v1` and is **4,981 bytes**.
Owner-relative retained location:
`Documents/BacktestBadgerEvidence/stage-04b2d10-historical-evidence-d82a9a0.json`.
The owner-owned dedicated folder is mode **0700**, the exclusively created file
is mode **0600**, and fsync plus exact readback verification passed.
The stable external copy is separate from the temporary acquisition output.

Detached evidence-record SHA-256:
`9813c3f12521d1167d5e6d7a635516d61df30260f5e22a4bd8bac499128819cf`.

Only the requested forecast evidence, provenance reference, 22-entry historical
map and method/limitations were retained. Full provenance and unrelated release
manifests were not printed or saved. No other audit publication file, minute or
hourly source, signing-key directory, genuine-verification destination, sibling
repository, database, network or production deployment was accessed.

`verification_executed=false`, `replay_executed=false`, `owner_signed=false`.
No parity rerun, runtime/loader dispatch, signing, approval generation, strategy
or economic computation occurred. This unsigned evidence grants no later
execution authority. No commit, push or deployment was performed.

## Review and validation

Only this new Markdown report was added; existing tracked files and the index
remain unchanged. No application code, tests, dependencies or frozen mappings
were edited. Acquisition completed once with exit 0; no original-source failure
or retry occurred. The initial script syntax-check command encountered a Python
bytecode-cache permission error before any source access; an in-memory syntax
check then passed, without executing acquisition code.

| Executed check | Result |
| --- | --- |
| Repository-wide `uv run --locked ruff check .` | Exit 0; all checks passed |
| Repository-wide `uv run --locked ruff format --check .` | Exit 0; 179 files already formatted |
| `git diff --check` and `git diff --cached --check` | Both exit 0 |
| New-report `git diff --no-index --check /dev/null <report>` | Exit 1 with no diagnostics: expected new-file difference, no whitespace errors |
| Explicit Markdown/evidence/sanitisation review | Exit 0; both forecasts and all 22 map entries match retained JSON |
| Git HEAD/index/tracked preservation | Exit 0; expected HEAD and all 201 existing tracked files unchanged |

Both Ruff invocations used `UV_OFFLINE=1`, `UV_NO_SYNC=1`,
`UV_PYTHON_DOWNLOADS=never`, a temporary external UV cache, and
`--no-cache --force-exclude --extend-exclude artifacts`. No dependencies were
installed and ignored source directories were excluded. Ruff's `--show-files`
output contains no Markdown; the report was separately checked for whitespace,
final LF, table values, absence of private paths and scope accuracy. Ruff success
is therefore not represented as Markdown lint/format coverage.

No full test suite or native-million-row regression was rerun for this
Markdown-only addition. No outstanding acquisition or retention blocker remains.
Stop here for owner review; later signing and genuine verification require
separate authorisation.

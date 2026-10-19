# Stage 4B.2D.2 — Synthetic forecast/minute integration

**Implemented with fabricated inputs only; awaiting owner/code review.**
Date: 2026-10-19 (Europe/London). Starting checkout: clean `main` at
`eae27377c121fa42f40102ba0cb28151a0d41a38`. The owner supplied baseline CI run
`39217332089`; this work did not query or trigger CI. No genuine artifacts,
source directories or completed audit output were opened, listed or hashed.
No genuine strategy calculation, publication, provider, database, production,
holdout or Stage 3 access is authorised by this stage.

The [archived request](../prompts/stage-04-paper/008-minute-forecast-integration.md)
contains the substantive attachment through its suggested commit message. The
unrelated session/browser tail is excluded. All pre-existing implementation,
tests, protocols, source pins, audit guides and dependency/configuration files
remain unchanged. Only architecture, roadmap and handoff are updated.

## Implemented API and trust boundaries

`src/backtest_badger/paper_minute_integration.py` supplies:

```python
evidence_sha256(value) -> str
forecast_snapshot_sha256(forecast_result) -> str
adapt_minute_inputs(
    forecast_result, forecast_manifest, minute_metadata, minute_projection,
    parity_evidence, *, evidence, expected_evidence_sha256,
) -> PreparedMinuteBundle
validate_minute_integration(bundle, *, expected_evidence_sha256) -> None
```

```text
Fabricated in-memory loader results + independently retained TEST evidence pin
    -> pure adaptation: lineage / grids / provenance / fixture parity checks
    -> immutable synthetic PreparedMinuteBundle (no accounts calculated)
    -> pytest ONLY: unchanged synthetic minute replay and independent ledgers

Future explicit source-access approval + externally frozen original byte pins
    -> NOT IMPLEMENTED: genuine loader/authentication and streaming projection
    -> proposed distinct AuthenticatedMinuteInputs (never SyntheticPriceSource)
    -> separate simulation approval + reviewed genuine execution boundary
    -> separate reproduction/publication approval and fresh destinations
```

The adapter has no CLI, path argument, source discovery, loader invocation,
network/database client, service, strategy call or genuine entry point. An input
status other than `synthetic_test` raises a permission-gate error before examining
payloads or even hashing evidence. There is no boolean/environment override.
The unchanged replay still rejects a genuine-labelled `SyntheticPriceSource`.
No new genuine execution function exists to invoke accidentally.

The seam proves supplied-fixture integrity and policy consistency. It does not
prove that any claimed digest describes original files, that supplied prices
came from native archives, or that a caller actually used a loader. A coordinated
caller can fabricate values and matching TEST pins; successful output remains
explicitly synthetic and cannot authorise real evaluation. Known genuine source,
research and parity declarations are rejected as TEST pin values to reduce
accidental reuse. This is not a security sandbox against hostile Python code
that can replace modules or rewrite every object and external pin.

## Injected contract

`forecast_result` is exactly the loader's `(hashes, accounts)` shape. `hashes`
contains `manifest.json` and `validation_predictions.csv`. `accounts` has exactly
all eight `(symbol, model)` keys, with original `forecast_data.Signal` instances
for BTCUSDT/ETHUSDT × zero/training_mean/ridge/gradient_boosting. Mapping insertion
order is irrelevant; each signal sequence's order is authoritative. No sorting,
deduplication, gap repair, refitting or invented record is permitted.

`forecast_manifest` is parsed Stage-2B-shaped metadata; `minute_metadata` is the
complete metadata-only shape returned by the native minute loader, without an
invented returned price mapping or manifest-hash field. The adapter checks the
original release status `validated_source_structure_not_approved_for_evaluation`;
that field is a source contract, not permission to evaluate. A synthetic envelope
and TEST pins identify the fabricated metadata as such.

`minute_projection` is a bounded list/tuple of existing `MinuteReference` objects,
ordered first by BTCUSDT then ETHUSDT, and by exact timestamp within each market.
The sequence must already contain only required openings. Iterators are refused
so a native million-row stream cannot be eagerly materialised by this API. The
adapter validates, but does not read or create, this projection from a CSV.

`parity_evidence` has `manifest` and `report` mappings. It is an explicit TEST
proof-shaped schema, **not a parser for the genuine auditor's JSON**. Its report
contains synthetic status, both source versions/manifest/CSV declarations,
`direct_timing_comparison_permitted`, empty structural-errors/discrepancies,
exact overall/per-market counts, and all ordered `(symbol, ISO UTC hour)` lists.
The fixture manifest has kind `synthetic_price_parity_fixture`, synthetic status
and the report hash. Both canonical fixture hashes must match separate pins.
A forged success flag, integer in place of the boolean, wrong source version,
missing/reordered/duplicate hours, incorrect counts, discrepancies or missing
proof aborts. The prior audit is never rerun. The flag only expresses fixture
parity consistency; retained genuine execution and timing-comparison authority
are always false.

`evidence` is an explicit mapping containing:

- `status="synthetic_test"`, the exact minute `protocol_version`/`protocol_sha256`,
  `selected_model="ridge"`, `recipe_identity_kind="stage2b_manifest_sha256"`, and
  `model_recipe_sha256` equal to its TEST forecast-manifest pin.
- `end_exclusive`, an ISO aware UTC hourly boundary after inception and at/before
  END. Use END for the complete contract. Shortened windows are synthetic prefixes
  only; they never alter the declared full native release or recipe counts.
- `pins`, exactly ten separately supplied TEST SHA-256 strings: `forecast_manifest`,
  `forecast_csv`, `research_manifest`, `research_csv`, `hourly_manifest`,
  `hourly_csv`, `minute_manifest`, `minute_csv`, `parity_manifest`, `parity_report`.
- `monthly_sources`, exactly 24 ordered `[symbol, YYYY-MM, ZIP hash, sidecar hash]`
  records, twelve distinct ZIP/sidecar pairs for each market.
- `snapshots`: `forecasts` from `forecast_snapshot_sha256`, `forecast_manifest`
  and `minute_metadata` from `evidence_sha256`, and `projection` from the unchanged
  `projection_sha256`. Take these before passing fixtures across the boundary.

The caller must separately retain `expected_evidence_sha256` from the original
TEST evidence mapping. Both public validation functions require it without a
default. The adapter does not replace it with a hash of the evidence it receives.
An in-memory snapshot is not an original CSV/manifest byte hash. Recomputing all
pins after mutation constructs another fixture, never authentic source evidence.

The frozen bundle retains immutable tuples for all eight baseline/Ridge signal
sequences, two Ridge forecast sequences, two minute reference sequences and two
synthetic source descriptors, plus the endpoint and canonical evidence bytes.
The bytes retain original supplied manifest metadata, native metadata, parity
proof and TEST pins, with an explicit authentication limitation. Revalidation
rebuilds the bundle using its retained inputs and the independent expected pin,
then checks exact equality, including all output labels and source descriptors.
Keeping baseline signals permits rechecking every original account; they never
feed the strategy. There is no fill, account balance, return, drawdown or other
performance field in the bundle.

## Lineage, timing and native provenance

Every account requires the exact source grid and finite Decimal forecasts. Zero
and training-mean baselines also match their loader semantics; the latter uses
the unchanged loader's `.17g` manifest-number conversion. Only Ridge is adapted
to `HistoricalForecast`, preserving the exact Decimal tuple, source open,
assumed availability, TEST original-file hash and canonical ID:
`binance:spot:{symbol}:14400:{source_open.isoformat()}:ridge`.
The whole Stage 2B manifest identifies the recipe, not a coefficient-only hash.

The adapter reuses the unchanged `_validate_lineage` policy validator for the
ordered five features, train/validation partitions, original training counts
13,782/13,783, 2,195 validation records, fixed Ridge (`alpha=1.0`, `solver="svd"`
and remaining frozen parameters), StandardScaler configuration and train-only
five-element finite means/positive scales. Because that validator embeds real
research/prediction declarations, a detached copy translates **only previously
checked TEST research/output pins** to those existing constants before the policy
check. Original supplied metadata and retained pins remain unmodified. This
translation is a fixture policy check, never authentication or a future genuine
loader mechanism. Original parameter floats are metadata; prices and forecasts
must be finite bounded Decimals and cannot be floats.

The adapter never calls `forecast_data.schedule`, whose hourly entry/exit timing
belongs to a different experiment. It also never calls `evaluate_strategy`.
Thresholding remains strictly `prediction > Decimal('1e-12')` inside replay.
Neither minute prices nor future OHLCV fields can enter the signal interface.

| Per market, full leap-year fixture | Required count / clock |
| --- | --- |
| Each original model account | 2,195 source horizons |
| Ridge source openings | 2023-12-31 20:00 through 2024-12-31 12:00 UTC, every 4h |
| Assumed availability | source open +4h+60s; first 00:01, last December 31 16:01 |
| Hypothetical execution reference | strictly next native minute: 00:02 / 12:02 / last 16:02 |
| Hourly native-minute valuation references | 8,784; January 1 00:00 through December 31 23:00 |
| Scheduled forecast references | 2,195, including every HOLD and CASH_NOOP |
| Distinct required projected minutes | 10,979; 21,958 across both markets |
| Full source authority (metadata claim only here) | 527,040 minutes each; 1,054,080 total |
| Prior full parity proof fixture | 8,784 hours each; 17,568 total |

There is no December 31 20:01 signal, invented 2025 price, interpolated reference
or forced closing trade. The 00:00 B&H reference is already in the hourly set.
Every minute record revalidates Binance Spot identity, native interval 60, exact
UTC timestamp/epoch-millisecond ID, positive finite Decimal open, processed-file
hash and original market/month ZIP hash. No later reference can substitute for
00:02. Source rows and monthly metadata cannot be silently reordered.

Full native metadata retains the original processed output identity/byte count,
24 ordered official ZIP/sidecar URLs and digests, interval, expected monthly row
counts (including 41,760 for February), byte sizes, validation status and aware
retrospective receipt time after month-end. Its source provenance remains
separate from the projection fingerprint. The test-only source descriptor binds
the projection but does not authenticate those 1,054,080 native records.

A native observation remains distinct from a hypothetical execution reference,
which remains distinct from a prospective quote or actual exchange fill. This
stage creates no quote/order-book/issuance evidence. Synthetic replay tests reuse
the existing independent 10,000-USDT Ridge/cash/B&H accounts, exact 10/1/2-bps
costs and 0.000001 quantity step. They verify minute timing, signed ledger replay,
benchmark independence and continuing final holdings, without duplicating engine
mechanics or presenting fabricated economics as historical results.

## Resources and failure behaviour

Work is linear in supplied forecasts, projected references and parity hours;
projection hashes stream row by row. The adapter stores eight original signal
sequences, two Ridge projections and 21,958 minute references at most. It never
creates 1,054,080 price objects, account histories or minute equity paths. A single
complete-year adapter test checks all counts, leap-February provenance and a
serialized bundle-content budget below 20 MB. Short fixtures exercise failures
and synthetic replay; new tests do not redundantly simulate a complete year.
Existing engine full-year regression tests remain unchanged.

Every missing/wrong pin, changed snapshot, lineage/grid/count mismatch, malformed
source association, nonfinite/float monetary value, missing/reordered projection
or invalid parity proof aborts with an exception. No partial success bundle,
repair, provider retry, alternative source or late-price fallback is returned.
Canonical retained JSON and row fingerprints are independent of ambient Decimal
context; financial values are exact strings. Recipe JSON preserves numeric
metadata from the original-shaped manifest. External evidence is an integrity
contract for cooperative Python callers, not cryptographic proof of loader use.

## Unexecuted future operator plan and typed execution proposal

No command below has been executed; this section confers no access permission.
Do not pass genuine data through this synthetic adapter or manufacture replacement
TEST pins to make a genuine source acceptable.

1. Obtain code review and CI for this stage. Agree a separately reviewed genuine
   authentication wrapper and tests. Pin its exact commit and implementation,
   frozen protocols, dependency/runtime identities, permitted input roots and
   fresh verification-only destination **before any source open or listing**.
   Do not inherit the old parity task's access approval or destination. Obtain
   specific owner read-only approval for the original Stage 2B validation CSV
   and manifest, the retained minute release, and the independently retained
   parity evidence files. Hourly manifest/CSV/acquisition/raw source access, if
   needed for revalidation, needs an explicitly enumerated separate allowance.
   Research CSV, labels, holdouts, Stage 3, providers, DB and production remain
   excluded. Refuse unexpected paths, symlinks, changed code and existing output.
2. Take source integrity snapshots only within those approved roots and freeze
   other writers. Before interpreting payloads, compare exact bytes against
   **external declarations already frozen in tracked records**, not hashes
   learned from whatever local file happens to exist. The declarations are:

   | Original byte identity | SHA-256 |
   | --- | --- |
   | Minute methodology | `c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b` |
   | Hourly methodology | `b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b` |
   | Stage 2B predictions | `e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674` |
   | Stage 2B whole manifest | `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581` |
   | Hourly manifest | `1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d` |
   | Hourly CSV | `39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a` |
   | Minute manifest | `673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127` |
   | Minute CSV | `37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233` |
   | Prior parity manifest | `53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d` |
   | Prior parity report | `0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb` |

3. Verify the independent prior parity manifest/report raw-byte pins and output
   associations, successful source-price-only kind/status, both source release
   identities, all total/market/month counts, empty errors/discrepancies and true
   flag. Parse the **actual** auditor schema under its pinned bytes; the synthetic
   fixture schema in this stage is not wire-compatible. Its genuine report uses
   aggregate buckets, not this fixture's matched-hour list. Establish full-grid
   coverage from the authenticated report/provenance and the unchanged auditor's
   pinned contract. Validate every linked evidence file needed by the approved
   scope. Never generate a replacement success manifest or rerun the genuine
   price comparison. If parity cannot be independently established, stop.
4. Call unchanged `forecast_data.load_forecasts` on the exact authorised Stage 2B
   root with its original default pins, without overrides. Independently pin and
   parse the same manifest bytes for lineage. Check loader hashes against the
   external declarations and manifest output linkage, all eight chronological
   2,195-record accounts and research-lineage declarations without opening labels.
   This original byte pin, loader parsing and lineage check together protect the
   model/forecast identity; a snapshot of fabricated Signal objects cannot.
5. Call unchanged `minute_execution_data.load_minute_execution_data` on the exact
   approved minute root with the literal external manifest pin. It verifies all
   24 native ZIP/sidecar pairs and complete processed-file reconstruction and
   returns metadata only. Compare the metadata/implementation and every retained
   source association against the frozen pin table. Do not weaken the native
   parser or substitute the projection's fingerprint for this complete check.
6. Implement/review a bounded additional streaming pass over the already verified
   processed CSV: validate the header, all 1,054,080 identities in original order,
   exact millisecond timestamps, positive exact Decimal opens, month ZIP hashes,
   raw-byte SHA-256/length and EOF. Keep only the precomputed union of 8,784 hourly
   marks and 2,195 price-independent next-minute times per market. Preserve source
   manifest, original processed hash and ZIP/sidecar lineage alongside each
   projection digest. Bound line length and parser work using the existing native
   contract. Reject missing data without repair, OHLCV substitution or refitting.
7. Recheck original byte hashes/stat evidence and code/document pins before
   retaining the verification record. Fail on mutation, unexplained inventories
   or provider revisions; preserve failed evidence and request owner review.
   Record authenticated input provenance only. No strategy or performance call
   belongs in this authentication-only stage. Before/after checks detect observed
   changes, not a hostile coordinated replacement-and-restoration race.
8. A later simulation approval requires a minimal **separate typed boundary**:
   proposed `AuthenticatedMinuteInputs` produced only by the reviewed genuine
   wrapper, and `replay_authenticated_minute_historical` requiring that type and
   independently retained verification pins. It must reject `PreparedMinuteBundle`
   and `SyntheticPriceSource`. To avoid copying monetary/replay mechanics, propose
   factoring the existing runner's validated plan/reference loop into a private
   pure core, with distinct synthetic and genuine validation front doors. Keep
   the synthetic source/status guard intact and test mutual type rejection.
   **This factoring and genuine function are not implemented here** because they
   would change a protected replay module. Review/approve that precise seam first;
   no runtime `allow_genuine` option or status relabelling is acceptable.
9. Separately authorise actual strategy execution for exact authenticated inputs,
   frozen costs/timing and a named fresh simulation destination. Then separately
   gate deterministic reproduction and immutable manifest-last publication, with
   a distinct fresh reproduction destination, exact ledger/mark reconciliation,
   preserved source/code hashes and review of scientific interpretation. Refuse
   all existing destinations and incomplete prior attempts; never overwrite the
   original hourly results or choose costs/thresholds after inspecting economics.
   Preserve partial-day/month definitions, actual-minute cost attribution and
   observed-hourly drawdown semantics from the frozen protocol.

The existing hourly experiment, synthetic minute replay, completed genuine
**price-only** parity audit, future forecast/source authentication, future genuine
simulation and publication remain separate. Prior parity found 17,568 exact
matches according to its tracked guide; it was not reverified here. Equal archive
opens establish no historical issuance, quote, liquidity or fillability. Any
future 2024 economic result remains exploratory previously inspected validation,
not real trading or independent out-of-sample profitability evidence.

## Local verification record

Tests use the installed locked environment without dependency sync/install or
Python downloads. The focused test module blocks all source loaders, the genuine
auditor, acquisition, psycopg connections, sockets and artifact/sibling
opens/listings. Guard tests exercise those blocks before real access. The full
suite also uses a session-only `sitecustomize.py` audit hook from
`/tmp/badger-4b2d2-offline`, rejecting genuine repository artifact/sibling access
and socket connection/bind/name resolution; `BADGER_TEST_ADMIN_DSN` is removed.
Existing loader tests may use their own fabricated temporary source files.
This hook is a local validation aid, not a new dependency or a CI change.

Executed commands:

```sh
env -u BADGER_TEST_ADMIN_DSN PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  PYTHONPATH=/tmp/badger-4b2d2-offline \
  uv --cache-dir /tmp/badger-4b2d2-uv-cache run --locked --offline --no-sync \
  pytest -q tests/test_paper_minute_integration.py \
  tests/test_paper_minute_historical.py tests/test_minute_price_parity.py \
  -p no:cacheprovider
env -u BADGER_TEST_ADMIN_DSN PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  PYTHONPATH=/tmp/badger-4b2d2-offline \
  uv --cache-dir /tmp/badger-4b2d2-uv-cache run --locked --offline --no-sync \
  pytest -q -p no:cacheprovider \
  --basetemp=/private/var/folders/7w/wfyb65513236nhbh8m_xr90c0000gn/T/badger-4b2d2-pytest-final
uv --cache-dir /tmp/badger-4b2d2-uv-cache run --locked --offline --no-sync \
  ruff check . --no-cache
uv --cache-dir /tmp/badger-4b2d2-uv-cache run --locked --offline --no-sync \
  ruff format --check . --no-cache
git diff --check
```

Focused combined suite: **201 passed, 0 failed, 0 skipped in 27.31 seconds**
(113 new integration cases and 88 unchanged replay/parity cases). The initial
integration-only run passed 107 tests before six additional boundary cases were
added. Whole-repository Ruff lint passed and all 153 Python files passed the
formatter check. Git whitespace and explicit checks of all four new files
passed. The substantive prompt matches the attachment byte for byte; the archive
and new files contain none of the unrelated session tail.

The first full run reached 100% without test failures, but pytest session cleanup
raised when the audit hook interpreted a relative `os.open(..., dir_fd=...)`
inside an older temporary fixture as repository artifact access. It exited 1
before printing a final summary and is **not counted as a passing full run**.
A second full run used a dedicated `/tmp` root and completed with **1 failed,
1,577 passed, 183 skipped in 214.17 seconds**. The sole failure was the unchanged
`test_private_file_permissions_ownership_and_no_symlinks`: this macOS temporary
root gives created files a group different from `os.getgid()`. A single-test
probe reproduced that failure under `/tmp` (1 failed), and passed under the
user-owned temporary directory (1 passed). No implementation/test change was
needed. The final run uses a dedicated previously absent `--basetemp` under the
user temporary directory to avoid both group inheritance and unrelated numbered
directory cleanup. The audit hook remains unchanged for every run.

Final locked full suite: **1,578 passed, 0 failed, 183 skipped in 215.59 seconds**
(exit 0). All 183 skips require an explicitly configured isolated PostgreSQL
server; no database was accessed and skips are not passes. The final log is
retained locally at `/tmp/badger-4b2d2-full-pytest-verified.log`. No GitHub Actions
run was triggered or claimed for these changes. The final protected-file and
tracked/new-file whitespace checks also passed after the documentation update.

### Protected-file snapshot

A pre-edit SHA-256 inventory covers **169 protected pre-existing tracked files**
(all tracked files except the three authorised summary documents). No genuine
artifact is part of this inventory. All 169 matched after implementation. The
original snapshot is retained locally at
`/tmp/backtest-badger-4b2d2-protected.json`; the clean baseline commit also retains
every protected original byte. SHA-256 of the sorted compact JSON mapping with
a final newline is
`e7a5379885c28c9a8500deceb1e4687c4728e463a2e425e7a90edfbf99249a3e`.

| Protected file | Before = after SHA-256 |
| --- | --- |
| `docs/stage-04b2-historical-validation-protocol.md` | `b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b` |
| `docs/stage-04b2c-minute-execution-protocol.md` | `c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b` |
| `docs/stage-04b2c-minute-source-pins.md` | `967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c` |
| `docs/stage-04b2d1-genuine-hourly-minute-parity-audit.md` | `877275430448b621296d017162c5b067383c44d20096f8581c38b64b899ccaa6` |
| `docs/stage-04b2d1-genuine-price-parity-audit.md` | `b4c94c3cdaa4882be184376ba810f6cbda6c2720e9d9fad93e2377e3ce8d2022` |
| `src/backtest_badger/forecast_data.py` | `d9ba8b84e4846d1d12dc208e4de9164e58ef418fc5381a27eef10322b9b180aa` |
| `src/backtest_badger/execution_data.py` | `29f6d0ac446a1fe58030bee0d6502854d462eb388b1e27eb060cba3d6b969d7a` |
| `src/backtest_badger/minute_execution_data.py` | `84cb5f7a8c3fcfcc6b7b488cdaf22bd6e3fb8c369fdf8cf12c1435fc2da256c2` |
| `src/backtest_badger/genuine_minute_price_parity.py` | `d4b3fb3f9f06b553fce0f1303a61bc4483feb2d90840573c9c33ac9e5523d092` |
| `src/backtest_badger/minute_price_parity.py` | `660e4eb4e276778e08319e7d343746c6a01311272f8c239845f3da99481820c8` |
| `src/backtest_badger/paper_historical.py` | `910f8d8107c6360fac565dce463f686f82478b8e459d4b6768ebb679c515ae43` |
| `src/backtest_badger/paper_minute_historical.py` | `b0ff96d747136373a4a562f3fb8f7fe77b705ed5208c2c12cd25ad266936bf25` |
| `src/backtest_badger/paper_historical_evaluation.py` | `df46fd26f857e834bd0559caa25ee525868b8de08ccbe3abb7388e9c6db193aa` |
| `src/backtest_badger/paper_historical_publication.py` | `c019b55ffde53486137586c1e3f97838fcd7d07d57f36aac011a1a50c893b16d` |
| `src/backtest_badger/paper_accounting.py` | `532ffd69e785dc7429403bb67da87bf82d563d60a5c9cfc3f36a69577eae34b6` |
| `src/backtest_badger/paper_execution.py` | `ed054f523d7a7c29978635c3426345186ea94dd11fb2c480543353b97861959b` |
| `src/backtest_badger/paper_strategy.py` | `55df7d0aadad660c849f7785ebcfe6e81d7bcc18cd610fd4233de8e7aca37eac` |
| `src/backtest_badger/paper_types.py` | `39a7a46b2631f4d3416df34fa866e4ba8e42c51e7e1b4775ab19b9ecfd371067` |
| `uv.lock` | `81ca2ffed631698425fc5921cfdf8b5c2160a3e8f4afbec249a164fa5984c118` |
| `pyproject.toml` | `65185e707b97ac92a120cd868c1d1a431e3393068c0886e055fb20da8d90d9ea` |
| `.gitignore` | `9e12ce0dbd7f13bddd46ab0077114e47ff5f5749775f02ca1e6a4f5182f0b983` |

Every old test and all other original source files are included in the complete
inventory, not just this table. This is code/document preservation evidence, not
a fresh hash audit of datasets or genuine audit outputs.

### Changed files and stop gate

Added:

- `src/backtest_badger/paper_minute_integration.py`
- `tests/test_paper_minute_integration.py`
- `docs/stage-04b2d2-minute-forecast-integration.md`
- `prompts/stage-04-paper/008-minute-forecast-integration.md`

Modified only `docs/architecture.md`, `docs/roadmap.md` and
`docs/development-handoff.md` among existing files. Final HEAD remains the starting
commit on `main`; the seven files above are uncommitted changes. No commit, push,
deployment or CI trigger occurred. Stop after synthetic validation for owner
review. The future source roots, wrapper revision, fresh verification destination,
separate genuine execution seam and simulation/reproduction/publication approvals
are still required before any real performance can be calculated.

# Stage 4B.2B — Historical evaluation integration and synthetic publication

Implemented locally on 2026-10-17, **awaiting review**. Synthetic engineering only:
no genuine 2024 artifact was opened, hashed, loaded, replayed or published. No
real continuous-holding economic result exists from this work. No CLI, dependency,
installation, database, scheduler, provider request or deployment was added.

## Starting checkout and frozen authority

Starting `main` was clean at `f1df2ecaa426957a09d3577125d1095a2d5dc69b`, matching
the requested baseline and the locally cached `origin/main`. Its parent is
`9af7a4573169b16bd049be34ed130c41c17a9d45` (protocol approval), preceded by
`daa3d458cba4eb73f6d50495911503d84e144359` (replay implementation). No remote
fetch, GitHub-current-state assertion, reset, rebase, commit or push was made.

The authoritative [frozen protocol](stage-04b2-historical-validation-protocol.md)
is `historical-validation-v1`. Its exact bytes hash to:

```text
b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b
```

Its last-change Git revision is
`9af7a4573169b16bd049be34ed130c41c17a9d45`. These identities are retained outside
the protocol, in the new implementation and publications. The retired draft was
not used. The protocol, approved Stage 4A documents, shared replay/primitives,
existing source loaders and every pre-existing Python implementation are unchanged.

## APIs and trust boundary

Two modules separate in-memory science from temporary publication:

```python
# paper_historical_evaluation.py
loader_snapshot_sha256(forecast_result, execution_result, lineage) -> str
adapt_inputs(forecast_result, execution_result, *, evidence) -> HistoricalBundle
evaluate_bundle(bundle) -> dict
benchmark(symbol, label, references) -> AnalyticalAccount
summarize_account(initial, trades, marks, final, *, decisions=(), end=END)
    # -> (summary, daily_monthly_rows)
period_observations(account_id, marks, trades) -> list[dict]
cost_summary(trades, references) -> dict
verify_account(initial, trades, marks, final) -> dict
scientific_payloads(report) -> dict[str, bytes]

# paper_historical_publication.py
implementation_provenance() -> dict
publish_synthetic(destination, forecast_result, execution_result,
                  *, evidence, temporary_root) -> str  # external manifest SHA-256
verify_publication(directory, *, temporary_root, expected_manifest_sha256) -> dict
verify_payloads(files) -> dict  # all six accounts' reconciliation evidence
```

No function invokes either real loader. The adapter accepts the exact existing
return shapes: forecast `(hashes, accounts)` with `(symbol, model)` keys and
`forecast_data.Signal` rows; execution `(metadata, prices)` with
`(symbol, datetime)` keys and Decimal opening prices. Both complete market grids
are mandatory. All eight original forecast account identities are checked;
**only Ridge** is selected for simulation. Other models are neither evaluated nor
used for comparison. A mapping cannot retain duplicate identical keys: original
CSV duplicate validation remains the unchanged loader's responsibility. The
adapter additionally checks counts, each ordered identity and per-market hours.

`evidence` requires:

- `status="synthetic_test"`, frozen protocol version/hash/last-change revision.
- `source_paths`, the five exact original repository-relative paths as declarations
  only; no source path is opened or resolved by the adapter.
- `model_recipe_sha256` equal to the original Stage 2B manifest digest and
  `recipe_identity_kind="stage2b_manifest_sha256"`.
- `stage2b_manifest`, supplied original-shaped metadata: experiment, partitions,
  ordered five features, research CSV/manifest lineage declarations, settling
  delay, prediction-output hash and independent market configuration/scalers.
- `loader_snapshot_sha256`, taken immediately from trusted loader results plus
  supplied lineage, before they can be mutated. Tests take this snapshot from
  fabricated objects. It is **not** a second artifact verifier or authenticity
  assertion. Recomputing it after changing values would defeat this boundary.

The five release declarations are checked exactly, including **all three**
hourly manifest/CSV/acquisition pins. All 24 monthly source/official ZIP identities
are checked against the Stage 2C documentation table, with exact market/month URLs,
checksum URLs, distinct checksum digests, complete row counts and retrospective
aware-UTC acquisition times. Twelve months per market are mandatory. February
has 696 hours. The retained source metadata is canonicalised by market/month.
The adapter never reparses archives or duplicates original research validation.

The original Ridge configuration is `alpha=1.0`, `solver="svd"`, intercept enabled,
`copy_X=True`, `positive=False`, `max_iter=None`, `random_state=None`, `tol=0.0001`.
Scaler parameters are `copy=True`, `with_mean=True`, `with_std=True`; five finite
means, five positive scales and market-specific training sample counts
13,782/13,783 are retained. Feature order is exactly `log_return_4h`,
`log_return_12h`, `log_return_24h`, `realised_volatility_24h`,
`relative_base_volume`. The manifest fingerprint anchors the recipe: it is not a
standalone coefficient digest or a claim of identical BTC and ETH fitted weights.
No coefficients are fitted, forecasts generated or research labels accessed.

The output bundle contains immutable tuples and retained evidence bytes. A digest
of adapted records rejects subsequent mutation. Original row identities are
`binance:spot:{symbol}:14400:{source_open.isoformat()}:ridge` and
`binance:spot:{symbol}:3600:{hour.isoformat()}`. Decisions and marks retain every
identity, original CSV hash and applicable monthly ZIP hash; source evidence
explicitly points to those records rather than duplicating their arrays.
Forecast availability remains assumed +4h+60s, never actual issuance. No REST
Quote is manufactured.

Published digest strings in tests are mocked identifiers. Structural checks and
snapshot checks cannot prove authentic 2024 files, original scaler values, native
archive economics or authentic acquisition timestamps. The later real-run wrapper
must establish these facts through the unchanged pinned loaders and original
manifest bytes. There is no path in this stage that does so.

## Accounts and accounting

The unchanged `paper_historical.replay_historical` runs once per market with the
full frozen 2,195-source / 8,784-hour grids and `BASE_CONFIG`. Strictly positive
above-1e-12 forecasts buy or HOLD; other forecasts liquidate or remain cash.
The first assumed availability is 00:01 and first possible fill is 01:00.
A 12:01 forecast can execute only at 13:00. Open year-end holdings remain open.
There are no synthetic miss records, alternative steps or stress/frictionless runs.

Each market also has separately named analytical cash and buy-and-hold accounts,
funded independently with 10,000 USDT. Cash never trades. B&H buys its maximal
fee-affordable 0.000001-step quantity at the original inception 00:00 opening
multiplied by 1.0003, then holds. All buys/sells use the shared historical trade
helper, which calls `affordable_quantity` and `calculate_trade`; `apply_trade`,
`reconcile` (through shared calls) and `replay` enforce the same monetary contract.
Fees are 10 bps, rounded up to 1e-8 USDT. An infeasible whole inception purchase
returns unavailable with null performance and no marks/trades; it never moves to
01:00 or pretends to be a cash benchmark. Its funding record remains reviewable.

Every account has one funding event and exactly two signed sequence-numbered
postings per fill. Hourly JSON retains all exact financial snapshot fields; the
enclosing account key identifies its portfolio and the ledger prefix identifies
its trade history. Those identities are retained once in `orders_trades.json`
and `ledger.json`, avoiding repeated growing trade-ID lists at every mark.
Prefix replay reconstructs those identities and checks every original hourly mark; full replay
checks final cash, units, fee-inclusive basis, realised P&L and fees. Tests also
sum signed currency postings independently at every mark. Benchmark trades carry
analytical account identities and no Ridge decision/order. Matched reference
identities are checked across available accounts.

## Reporting definitions

Authoritative amounts are exact Decimal strings, using the shared isolated
160-digit context with inexact money arithmetic trapped. Total return divides
exact monetary P&L by initial 10,000 USDT. Nonterminating ratios and weighted
average basis use the shared 80-significant-digit HALF_EVEN division convention;
exact monetary operands, units, counts and durations remain retained. These
quotients are explicitly numerical representations, not infinitely exact decimal
expansions. Display formatting does not replace money evidence. Undefined ratios
and unavailable benchmark performance are null, not fabricated zeros.

Each available account retains initial funding, first hourly mark and final
cash/units/basis/weighted-average cost/realised/unrealised P&L/equity; all action
and target counts; buy/sell notional, turnover, fees, hypothetical spread/slippage
by side; final sequence and complete reconciliation. Costs use that account's
actual quantities and original references. Spread/slippage are already included
in fill prices and are not subtracted again.

Exposure duration uses actual transition timestamps, with an open final interval
ending at END **only for duration**. Its denominator is 31,622,400 seconds. The
fraction of observed hourly marks invested is separate. Maximum drawdown uses
initial funding plus the chronological observed hourly marked-equity sequence,
including B&H's initial cost loss; it is not an intrabar drawdown.

Daily rows use consecutive 00:00 UTC marks: 365 complete days, including leap-day
and month-boundary observations, plus the partial December 31 00:00→23:00 row.
Complete-day count/mean/min/max exclude that final 23-hour interval. Monthly rows
use month-opening boundaries and include all twelve months; December ends at
23:00 and is explicitly incomplete by one hour. With six available accounts there
are 2,268 daily/monthly rows: 2,196 daily and 72 monthly. Costs/counts are assigned
to actual fill dates using `[start, next calendar boundary)`. All poor periods
remain in CSV, and every available month appears in Markdown.

Marks are post-trade. B&H's inception costs precede its first 00:00 mark and hence
its first mark-to-mark daily/monthly return. They remain fully included in its
funding-relative full-period return and inception-to-observed drawdown. Reports
retain both funding and first marked equity to make this distinction explicit.
This implements the mandated benchmark inception and hourly boundaries without
inventing another mark or modifying the frozen protocol.

Comparisons show matched-hour coverage, endpoint equity difference, difference
in funding-relative returns (10,000 denominator for each account), and relative
endpoint difference (benchmark final equity denominator). Controls have different
exposure/cost timing; B&H enters one hour before Ridge can. These are contextual
comparisons, not causal alpha, formal significance or independent confirmation.
Ridge was selected after earlier 2024 analysis. Every report discloses retrospective
availability, provider revision, quote/depth/filter/fillability and single-year
limitations. No winner, Sharpe, significance test or promotion is produced.

## Publication and verification

The destination must be a new direct child of an existing explicitly supplied
test temporary root under the system temporary directory or `/tmp`. Existing
files, directories (even empty ones), symlink destinations, non-temporary roots
and `artifacts` path components are refused. There is no genuine publisher mode.

All named scientific outputs are fixed:

| File | Evidence |
| --- | --- |
| `policy.json` | Frozen configuration, strategy, timing, grids, definitions, limitations, external protocol/config fingerprints |
| `source_evidence.json` | Mock status, five release hashes, source declarations, all monthly ZIP/checksum/origin/acquisition metadata, market-specific recipe lineage and snapshot/adapted-record hashes |
| `decisions.json` | Ordered original Ridge decisions/forecast identities, empty analytical decision histories |
| `orders_trades.json` | Distinct labelled accounts, initial/final snapshots, exact trades and Ridge-specific order/fill provenance |
| `ledger.json` | One initial funding and each paired signed posting, sequence and trade identity |
| `hourly_marks.json` | Complete original hourly references and exact account prefixes/equity/unrealised P&L |
| `summary.json` | Both markets, all controls, coverage, descriptive metrics, comparisons and limitations |
| `daily_monthly.csv` | Every available daily/monthly observation, completeness, exact operands, returns and date-attributed costs |
| `summary.md` | Clearly synthetic summary, every available month and scientific limitations |
| `manifest.json` | Written last: schema/version/kind, synthetic status, identities, provenance, coverage/reconciliation and every other file's byte length/SHA-256 |

The publisher evaluates twice and requires byte-identical payloads before writing.
It exclusively reserves the directory, writes/fsyncs `.partial` files and publishes
them by exclusive atomic hard link, reads every output back, verifies bytes and
replays all six ledgers and every mark, then publishes the manifest last. The
external manifest SHA-256 is returned to the caller; it is never embedded
recursively. Verification requires that external identity, exact named outputs,
all byte sizes/hashes and shared accounting replay. Missing/altered files and
manifest/output symlinks fail closed. There are no scientific wall-clock stamps,
absolute machine paths, locale-dependent ordering or output-directory identities.

The manifest fingerprints the new modules, unchanged historical/shared paper
modules, source loaders and their relevant implementation dependencies, lockfile,
project configuration, runtime/package versions, Git HEAD/dirty status and
protocol revision. Provenance reads only a fixed code/document/lock allowlist.
Unavailable Git fields are null. Implementation/provenance must stay unchanged
through publication. Reproduction assumes the same supplied evidence, code,
runtime and Git provenance; account payloads are independent of directory names.

The existing `_retain`/`_write_manifest` helpers can replace existing files, or
accept existing identical bytes. This stricter publisher instead follows the
repository's exclusive hard-link convention without importing ingestion/DB code.
A failure retains partial evidence and attempts a deterministic `failure.json`,
with no successful manifest. A hard kill may leave only partial files. Never
resume/rewrite an old attempt: investigate it and choose a fresh temporary
destination. Exclusive publication is not coordinated-forgery protection,
filesystem power-loss certification or a backup system.

## Synthetic verification and preservation

Run from the checkout, with installed locked tools and no installation/sync:

```sh
uv --cache-dir /tmp/badger-4b2b-uv-cache run --locked --offline --no-sync ruff check . --no-cache
uv --cache-dir /tmp/badger-4b2b-uv-cache run --locked --offline --no-sync ruff format --check . --no-cache
env -u BADGER_TEST_ADMIN_DSN uv --cache-dir /tmp/badger-4b2b-uv-cache run --locked --offline --no-sync pytest -q tests/test_paper_historical_evaluation.py -p no:cacheprovider
env -u BADGER_TEST_ADMIN_DSN uv --cache-dir /tmp/badger-4b2b-uv-cache run --locked --offline --no-sync pytest -q -p no:cacheprovider
git diff --check
```

**Final executed checks:** focused suite **92 passed** (47.66 s); complete
available suite **1,148 passed, 183 skipped** (80.60 s). Locked offline Ruff lint
and formatter checks passed; `git diff --check` and separate whitespace checks
on all five new files passed. The 183 PostgreSQL skips are not integration
evidence. No remote CI was run. Tests use fabricated
full/short grids and `tmp_path`/`tmp_path_factory`, with genuine loaders, provider
connections, DB connections and real artifact opens forbidden in the focused
suite. Mutation tests cover release pins, metadata, source association, chronology,
prices, lineage and protocol; checks remain effective independently of the
snapshot digest. Tests cover all marks, exact ledger sums, continuous holding,
00:00/01:00 entry differences, affordability, costs, unavailable B&H, leap day,
partial year end, all months, exposure/drawdown, Decimal/container-order stability,
byte-identical publications, missing/altered outputs, exclusive directories,
reproduction mismatch, interruption before/during/after manifest linking and
fresh-destination recovery.

Before/after SHA-256 comparison covers every pre-existing Python implementation,
`uv.lock`, `pyproject.toml`, both approved Stage 4A documents and the historical
protocol. No real artifact inventory or preservation hash audit was performed,
because opening those files was explicitly prohibited. Prompt archive wording
is preserved byte for byte and reviewed for secrets. No secrets were found.
No remote CI or isolated PostgreSQL service is run; skipped cases are not passes.

## Retained synthetic fixture identities

The full fabricated two-market fixture published to two distinct pytest-owned
temporary directories with byte-identical files and the same external manifest
identity. This is mock engineering evidence, not genuine 2024 performance or
authentication. Temporary files are disposable; reproduce with the focused tests.
The manifest identity below pins this implementation/runtime/Git-dirty provenance.

| Synthetic output | Bytes | SHA-256 |
| --- | ---: | --- |
| `daily_monthly.csv` | 579,136 | `b86e8da81e907bacf2684db2cca3b0a2e1611b3fecb77c372c02ed3ee19d3b04` |
| `decisions.json` | 2,915,716 | `26fede8557c2b41a8adec5148bb250834c204033f288523365f6952bdad51ee4` |
| `hourly_marks.json` | 34,671,990 | `ceaae444626145357a7eb11cfe8fc40038c7eae34b3a9c98ac666ec498b1b839` |
| `ledger.json` | 5,360 | `27b223de04f967d6000422215830dd3d796fe4d06949ff2426df55b91e723297` |
| `orders_trades.json` | 31,260 | `ce14e6ea0dc302b4b998383aaad0ed24031552ad6a3d57f3ace2b0ba301b43fb` |
| `policy.json` | 3,519 | `4e3d4935e90bd9d4098bc7067fecde079a72f5dbc4b2365be46c24cc70924f1b` |
| `source_evidence.json` | 15,816 | `27d1369df9d32db13615bfdff048a0943bcacd6d2f7e117e1ec0aac2bef7cb65` |
| `summary.json` | 16,675 | `5c0ca78797f90deaa9fc3c7ff5596f4a217b5576a8e65ac7a7e85c636b5a47ec` |
| `summary.md` | 16,200 | `9a164ba520cfd02c0914e7801c6ec6bcff7824eaddbb6e68a283bc65a299a016` |
| `manifest.json` | 20,968 | `f1a704c4117459be80ce7b67ed0eacc9dcf0cd8568d1c591230fb57066573d80` |

Each synthetic Ridge account has 2,195 decisions: two BUY_REQUIRED, 2,191 HOLD,
one EXIT_REQUIRED and one CASH_NOOP; 2,193 long targets and two cash targets.
There are three fills, six signed fill postings, one funding event and ledger
sequence seven. Each cash account has only sequence one; each B&H account has
one buy, two fill postings and sequence three. All six retain 8,784 matched
marks (52,704 total), with no forced final sales. These fixture counts are
engineering expectations, not observations from real forecasts.

## Future one-minute proposal — not approved or implemented

Hourly-specific components are `adapt_inputs` (hour grid, counts, monthly native
1h sources and record identities), `benchmark` (fixed original 00:00 entry),
`verify_account`/`verify_payloads` (hourly completeness), `period_observations`
(frozen midnight/23:00 endpoint definitions), `policy`, and the unchanged
`paper_historical` records, `next_reference_at` and `replay_historical` scheduling.
`evaluate_bundle` and manifest coverage intentionally require the frozen counts.

Shared financial primitives, signed ledger construction, exact cost decomposition,
ratio arithmetic, timestamp-based exposure duration, canonical serialization,
output hashing and exclusive manifest-last publication mechanics can remain.
The existing output names stay hourly-specific. No frequency option or alternative
schema exists. A future scenario needs independently approved source acquisition
and validation, source pins/identities/counts, signal-to-minute execution ordering,
latency/availability assumptions, spread/slippage/liquidity policy, benchmark entry
and boundary-flow definitions, a separate scientific protocol/config/output
version, and new causality/grid/period/reconciliation tests. Near-immediate
execution has not been tested by this work.

## Separate real-run gate and exact remaining changes

Stop after synthetic Stage 4B.2B review. **Explicit owner approval is mandatory
before any genuine 2024 input loading, calculation or economic publication.**
There is no executable real-run command to run in this checkout.

A subsequently authorised task must implement/review a narrow real-run wrapper
and genuine evidence/publication gate without weakening `publish_synthetic`:

1. Confirm the approved code revision, unchanged protocol bytes and all five
   reviewed pins. Restrict source access to the Stage 2B validation artifact and
   Stage 2C hourly artifact, including the latter's 24 native ZIP/sidecar pairs.
2. Only then call the unchanged APIs with no pin override:
   `forecast_data.load_forecasts(Path("artifacts/experiments/stage-2b-v1"))` and
   `execution_data.load_execution_data(Path("artifacts/execution/binance-1h-2024-v1"))`.
   Independently verify the Stage 2B manifest bytes against `RECIPE_SHA256`, parse
   its original metadata for lineage, and retain the source hashes before using
   the returned data. Do not call `model_data.load_model_data` or fit anything.
3. Construct the same adapter evidence from those verified outputs, replacing the
   currently synthetic-only gate with a separately reviewed genuine-verification
   contract; take the in-memory snapshot immediately. Preserve original actual
   source acquisition metadata and all row/month identities.
4. Invoke the unchanged base evaluation/accounting/report definitions, reproduce
   all payloads twice, and replay every ledger/mark. Add a separately approved
   exclusive real publisher for the fixed destination
   `artifacts/paper-historical/stage-4b2-base-v1/`, with genuine status and correct
   authentication disclosure, plus separately fresh reproduction destination.
   Keep the temporary fixture publisher's synthetic restriction intact.
5. Review preservation, reproducibility and interpretation evidence before any
   further economic publication or promotion. Do not access Stage 3 artifacts,
   research CSV/holdout labels, providers, databases or production infrastructure.

Those API calls and output paths are documentary instructions for the future
authorised wrapper, **not commands executed here**. Real source authenticity,
real-runtime/evidence reconciliation and actual economic results remain untested.

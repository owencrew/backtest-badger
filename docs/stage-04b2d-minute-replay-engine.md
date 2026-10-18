# Stage 4B.2D — Synthetic minute replay and price parity

Implemented locally on 2026-10-18, awaiting review. This stage uses fabricated
inputs only. It does not load, inventory, hash or evaluate genuine artifacts,
query a database, download sources, publish economic results or deploy anything.
The unchanged native-hourly experiment and prospective paper trading remain
separate scientific identities.

## Baseline and preserved authority

Starting and final Git HEAD: `0329b12643e9668d9eae1cfedc459ca4d08b0f46`.
The checkout was clean before implementation. GitHub's API confirmed successful
baseline [CI run 39101709169](https://github.com/owencrew/backtest-badger/actions/runs/39101709169),
completed on 2026-10-18. The local changes have not been committed, pushed or run
through GitHub CI.

| Frozen declaration | SHA-256 |
| --- | --- |
| `historical-minute-execution-v1` protocol, rehashed code/document bytes | `c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b` |
| Minute dataset manifest, declaration only; **not opened or reverified** | `673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127` |
| `historical-validation-v1` hourly protocol, rehashed document bytes | `b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b` |
| Unchanged minute source implementation | `84cb5f7a8c3fcfcc6b7b488cdaf22bd6e3fb8c369fdf8cf12c1435fc2da256c2` |

The [frozen source-pin metadata](stage-04b2c-minute-source-pins.md) is unchanged.
Its release verification belongs to the previous separately authorised task.
This implementation does not repeat that verification or authenticate its data.
All pre-existing source modules, tests, lock/configuration files and frozen
protocols remain byte-identical to the starting checkout.

## Public APIs

All APIs are offline supplied-input functions. No CLI, loader adapter, real-data
mode or publisher is added.

```python
# paper_minute_historical.py
next_minute_at(at) -> datetime
reference_identity(symbol, at, interval_seconds) -> str
projection_sha256(references) -> str
price_source_sha256(source) -> str
validate_price_projection(references, source, *, interval_seconds,
                          expected_source_sha256) -> None
replay_minute_historical(
    symbol, forecasts, references, *, source, expected_source_sha256,
    forecast_sha256, model_recipe_sha256,
    end_exclusive=END, synthetic_misses=(),
) -> MinuteResult
calculate_minute_fill(account, side, reference, *, identity,
                      decision_id=None) -> MinuteFill
value_minute_account(account, reference, *, ledger_seq) -> MinuteMark
verify_minute_account(result, *, end_exclusive) -> None
minute_account_summary(result, *, end_exclusive) -> dict
minute_ledger_records(result) -> tuple[dict, ...]
scientific_json(value) -> str

# minute_price_parity.py
# Both markets are required, even for short fixtures.
audit_minute_price_parity(
    hourly_references, minute_references, *, hourly_source, minute_source,
    expected_hourly_source_sha256, expected_minute_source_sha256,
    end_exclusive=END,
) -> ParityReport
```

`calculate_minute_fill` is a monetary helper; the runner owns decision eligibility
and strictly-next-minute scheduling. `verify_minute_account` proves supplied fill
amounts, balances and hourly prefixes, not the authenticity of source bytes or
forecasts. `minute_ledger_records` projects a successfully verified account into
one funding row and two signed rows per fill; it is not a persistence transaction.

## Supplied evidence contracts

`HistoricalForecast` and `SyntheticMiss` are reused because they describe native
four-hour signal identity and discovery, without assuming an execution interval.
Forecast IDs must be
`binance:spot:{symbol}:14400:{source_open.isoformat()}:ridge`; their file digest
must match the explicit supplied forecast pin. The model recipe parameter is the
whole-manifest lineage identity. Tests use invented hashes and values. No model
is fitted, prediction regenerated or target label read.

`MinuteReference` requires aware UTC 2024 minute boundaries, positive finite
Decimal opening prices, Binance Spot BTCUSDT/ETHUSDT identity, native interval 60,
and ID `binance:spot:{symbol}:60:{open_time_ms}`. It retains the supplied processed
file and monthly source ZIP digests. There are no high/low/close/volume fields.
`HourlyReference` remains the old native-hourly type, with its existing ISO-time
identity format. It is used only as the auditor's separately supplied hourly side.

`SyntheticPriceSource` requires:

- Native interval 60 or 3600, manifest and processed-file SHA-256 declarations.
- Immutable, strictly ordered `(symbol, YYYY-MM, source_zip_sha256)` tuples.
- `projected_sha256`, a streaming fingerprint of the ordered supplied records.
- Exactly `status="synthetic_test"`; genuine mode is rejected.

Retain `price_source_sha256(source)` separately before passing fixture evidence
onward. The APIs require that external fingerprint and check all metadata, each
record's file/month association, identity, interval and projection fingerprint.
Changing a price or provenance without changing the independently retained pin
fails. Deliberately constructing and pinning a new fixture is supported; resealing
changed evidence cannot prove authenticity. Coordinated source/pin replacement
is outside this integrity contract.

A supplied projection is **not full-source authentication**. The complete native
release has 527,040 minutes per market, 1,054,080 observations total. Its original
archives, checksums, manifest, processed bytes and complete coverage must be
verified upstream under separate authorisation. This engine requires only the
union of all hourly mark times and the strictly-next-minute time of every supplied
forecast/miss, including HOLD and CASH_NOOP decisions. An ordinary full-year
projection therefore has 10,979 references per market, not 527,040 snapshots.
Extra, missing, duplicated, reordered or misidentified replay references fail.

Short fixtures start at January 1 00:00 and end at an explicit hourly exclusive
boundary. Default `END` requires exactly 2,195 forecast horizons and 8,784 hourly
marks per market, with no synthetic miss substitutions. In short fixtures only,
explicit synthetic misses may replace required horizons and produce
`synthetic_missing_signals`, never completed genuine evidence. Missing forecasts
without such explicit fixture records always fail. Forecast and miss
collections each remain source-ordered; combining them cannot repair bad ordering
within either collection or backdate later forecasts before a delayed discovery.

## Causal ordering and sticky exits

The shared `evaluate_strategy` receives only the prediction. Its exact threshold
is `prediction > Decimal('1e-12')`. Availability is source opening +4h+60s.
Execution is at the strictly next minute even for an exact-boundary discovery:
12:01 means 12:02. The first Ridge execution can be January 1 00:02; the last
eligible availability is December 31 16:01, executable at 16:02. The purged 20:01
signal is rejected.

Flat/positive buys the full affordable quantity; long/positive HOLDs;
long/nonpositive sells all; flat/nonpositive is CASH_NOOP. Only a new eligible
forecast after exit satisfaction may re-enter. A pending sale cannot be cancelled
or reused for entry by a later positive forecast, including at the same discovery
time. A forecast available at the exit timestamp cannot re-enter.

Synthetic misses retain the actual discovery timestamp and explicit reason.
Discovery must be strictly after source close +16 minutes, preserving the existing
miss contract. One miss retains the position. Two consecutive misses while long
schedule a risk-off sale at the strictly next minute. Positive forecasts reset
the miss streak but cannot cancel that pending exit. Missing execution evidence
aborts; there is no later-price retry or invented outage history.

The runner validates the price-free signal plan before consuming prices. At a
shared timestamp it executes previously scheduled intent, then marks the resulting
ledger prefix. A discovery at that timestamp is processed afterwards and must wait
to the next minute. This is a hypothetical ordering convention, not an observation
of exchange intrasecond order or actual contemporaneous availability.

## Accounts, accounting and marks

Ridge, static cash and buy-and-hold each receive 10,000 USDT once in distinct
portfolios. They have separate trades, signed postings, balances and marks. Cash
never trades. Buy-and-hold makes its only purchase at January 1 00:00 using the
native minute opening, before its first mark and two minutes before Ridge's first
possible execution. A mathematically infeasible initial purchase makes that
benchmark unavailable, with retained funding, no fills/marks and null performance;
there is no substitute later purchase. Neither long account is liquidated at year
end.

The implementation reuses unchanged `fund_account`, `calculate_trade`,
`apply_trade`, `replay`, `reconcile` and `affordable_quantity`. Prices are adjusted
once: buy `P * 1.0003`, sell `P * 0.9997`. Fees are 10 bps of adjusted notional,
rounded UP to 0.00000001 USDT. The quantity step is fixed at 0.000001 for both
markets. Costs separately expose the hypothetical 1-bp half-spread and 2-bp
slippage already embedded in execution prices; they are not deducted again.
Shared `Trade.policy` identifies the unchanged monetary contract, while
`MinuteFill.kind` identifies hypothetical minute execution, never a prospective
quote fill.

Every HH:00 mark uses that native minute opening and reconciles:

```text
cash = 10000 + sum(USDT postings through ledger_seq)
quantity = sum(base postings through ledger_seq)
equity = cash + quantity * minute_open
unrealised = quantity * minute_open - remaining_basis
realised + unrealised = equity - 10000
```

Verification advances through the ordered ledger once, reconstructs each mark's
actual prefix, compares cash, quantity, fee-inclusive basis, realised/unrealised
P&L, fees and equity, and replays the final account through shared accounting.
Marks store compact scalar state and a sequence, not growing account histories.
The final full-year mark is December 31 23:00. END is only a duration boundary for
open exposure; no January 2025 reference or valuation is manufactured.

`minute_account_summary` retains exact cost amounts, funding-relative last-mark
return, actual minute-based exposure seconds, invested hourly-mark fraction and
maximum **observed-hourly-reference-mark drawdown**, including initial B&H costs.
Money uses the shared isolated exact 160-digit context; ratios use its 80-digit
HALF_EVEN division convention. Short fixtures may execute after their last HH:00
mark; last-mark performance is explicitly timestamped and is not a later final
account valuation. No daily/monthly publisher is introduced in this engine stage.
Any future report must retain the frozen midnight boundaries, partial December 31
23-hour observation/December endpoint, and actual-minute calendar cost attribution.

Scientific JSON uses exact Decimal strings, UTC timestamps, deterministic keys
and a final newline. It rejects floats and nonfinite values. Projected fingerprints
are streamed row by row. Serialization retains initial/final account histories
only once per account and avoids quadratic mark-history expansion. Shared immutable
accounting still validates growing trade-ID tuples during trades; this is retained
rather than replacing the approved monetary implementation.

## Exact price parity

The auditor expects `(symbol, hour)` order across both supplied source grids. In
full-year mode it checks all 17,568 identities using exact Decimal equality.
Native source manifests, processed-file hashes and ZIP hashes remain distinct;
price equality does not require equal source hashes.

The deterministic report retains both source contracts, expected/input counts,
matched identities, missing identities on each side, all extra/duplicated rows,
reordered indices, and exact discrepancy records with both original references,
signed minute-minus-hourly difference and absolute magnitude. Duplicate identities
are never considered a unique match. Conflicting duplicate price pairs also
remain in discrepancy evidence. Missingness, extras, duplicates, reordering or any
price discrepancy sets `direct_timing_comparison_permitted=False`. Malformed,
off-hour or tampered provenance raises instead of producing a usable report.
There is no tolerance, interpolation, substitution, overwrite or silent repair.
The permission flag refers only to the supplied synthetic fixture.

## Validation and future gates

Focused tests block source loaders, network connections, databases and artifact
reads/listing. All forecasts, prices and source hashes are fabricated, including
the complete leap-year grids. The full locked suite additionally runs with a
session-only Python audit hook blocking genuine repository artifacts and real
network connections, with `BADGER_TEST_ADMIN_DSN` removed. Existing source-loader
tests may still validate their own fabricated temporary files.

Final local results are recorded below after completion. PostgreSQL integration
skips are not passes; baseline CI success is not CI evidence for these local edits.

Before genuine parity or historical evaluation, obtain separate owner approval
for the exact reviewed code, original hourly/forecast source access, pinned minute
release and scope. Then separately implement/review a narrow genuine adapter that
uses unchanged upstream loaders and externally frozen pins, proves full minute
source coverage, preserves original Ridge/manifest lineage, and refuses missing
real signals rather than constructing `SyntheticMiss` records. Run the separately
authorised real parity audit across all 17,568 identities before claiming a direct
timing comparison. Any discrepancy requires owner review, never a tolerance or
source change chosen after viewing results. Genuine evaluation, reproduction and
exclusive publication require their own approved integration/output contract.

Retrospective archive openings are not quotes, fills or quantity-specific
fillability evidence. Spread, slippage, latency and lot step remain assumptions.
2024 was already inspected; no independent out-of-sample, causal alpha or
profitability claim follows. The holdout, Stage 3 evidence, databases, production
and prospective execution remain outside scope. Stop at Stage 4B.2D review.

### Local validation commands

The installed locked environment was used without sync, installation or Python
downloads. The session-only audit hook was injected through `PYTHONPATH` for the
test runs; it is an additional local guard, not a new project dependency. The
persistent focused tests contain their own explicit forbidden-I/O fixture.

```sh
env -u BADGER_TEST_ADMIN_DSN PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  uv --cache-dir /tmp/badger-4b2d-uv-cache run --locked --offline --no-sync \
  pytest -q tests/test_paper_minute_historical.py tests/test_minute_price_parity.py \
  -p no:cacheprovider
env -u BADGER_TEST_ADMIN_DSN PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never \
  uv --cache-dir /tmp/badger-4b2d-uv-cache run --locked --offline --no-sync \
  pytest -q -p no:cacheprovider
uv --cache-dir /tmp/badger-4b2d-uv-cache run --locked --offline --no-sync \
  ruff check . --no-cache
uv --cache-dir /tmp/badger-4b2d-uv-cache run --locked --offline --no-sync \
  ruff format --check . --no-cache
git diff --check
git diff --cached --check
```

Whitespace was also checked explicitly in all six new files, which ordinary
`git diff --check` does not include before staging. The archived substantive
prompt was compared byte for byte with the attachment. A SHA-256 snapshot of
tracked code, tests, documents, prompts, lockfile and project configuration
confirmed 129 pre-existing files unchanged; only the three intended existing
architecture/roadmap/handoff documents changed. No artifact preservation inventory
or hashes were taken. No commit, push or deployment occurred.

### Final executed results

- Final focused synthetic suite: **88 passed in 29.00 seconds**.
- Final complete locked suite: **1,393 passed, 183 skipped in 261.46 seconds**.
  All skips are PostgreSQL integration cases requiring an explicitly configured
  disposable local test server. No database was accessed and these are not passes.
- Whole-repository Ruff lint passed; formatter check passed for all 144 files.
- Git tracked/staged whitespace checks and explicit new-file whitespace checks
  passed. Frozen document/code preservation and prompt byte equality passed.
- The first full run also passed (1,392 passed, 183 skipped); the full suite was
  rerun after the final full-year no-miss guard/test so the totals above apply to
  the final implementation. No local test failures occurred.
- Baseline GitHub CI was verified before implementation. These uncommitted local
  changes have **not** run through GitHub CI. Starting/final HEAD remains
  `0329b12643e9668d9eae1cfedc459ca4d08b0f46`.

# Stage 4B.2A — Historical continuous-holding replay engine

Implemented locally for review on 2026-10-16. **Synthetic mechanics only; no real
2024 continuous-holding result has been calculated or inspected.** Stop here.
The companion [historical validation protocol](stage-04b2-historical-validation-protocol.md)
was **DRAFT when Stage 4B.2A was implemented; approved and frozen on 2026-10-16. Real 2024 execution remains gated**.

## Checkout, inspected contracts and scope

Actual starting checkout was clean at
`8e094f94e4c831d62690d9487b2f85dbbaeeae9a`
(`fix(paper): enforce valuation quote timing and snapshot integrity`), matching the
request's expected reference. Nothing was reset. No commit, push or deployment.

Inspected `AGENTS.md`, `prompts/README.md`, architecture/roadmap/handoff, both
approved Stage 4A documents, Stage 4B.1 guide including its valuation correction,
Stage 2B/2C/2D guides, all four existing `paper_*.py` modules and their synthetic
tests, `forecast_data.py`, `execution_data.py`, `backtest.py` and existing test
fixtures/source-validation conventions. No genuine artifact payload was needed.

Added one standard-library module, `src/backtest_badger/paper_historical.py`, and
`tests/test_paper_historical.py`, this guide, the draft protocol and the exact
prompt archive. Architecture, roadmap and handoff receive narrow status/link
updates. No existing Python implementation/test, dependency, CLI, schema, worker
or frozen protocol is changed.

## Exact callable API

```python
replay_historical(
    symbol,
    forecasts,
    references,
    *,
    protocol_sha256,
    model_recipe_sha256,
    end_exclusive=END,
    config=BASE_CONFIG,
    synthetic_misses=(),
) -> HistoricalResult

calculate_historical_trade(
    account, side, reference, *, at, identity, config=BASE_CONFIG
) -> Trade

value_historical(account, reference, *, ledger_seq) -> HistoricalMark
next_reference_at(at) -> datetime
historical_json(result) -> str
```

`replay_historical` is a pure one-account calculation. Invoke separately for
BTCUSDT and ETHUSDT; invocation order cannot affect balances. It accepts supplied
in-memory records, never paths, settings, a clock or a destination. It does not
locate inputs, call loaders, access the network or launch a command. The default
period is the full fixed 2024 grid, but this stage invokes it only with fabricated
values, including one fabricated full-year boundary test. Supplying actual data
remains a separately authorised Stage 4B.2B action.

| Record | Fields and meaning |
| --- | --- |
| `HistoricalConfig` | Frozen `historical-base-v1`, `hypothetical-base-step-v1`, positive Decimal step, fixed 10/1/2 bps and fee quantum. Default `BASE_CONFIG` uses 0.000001 base units for either market. |
| `HistoricalForecast` | Symbol, original row `record_id`, native `source_open`, assumed `feature_available_at`, finite Decimal `prediction`, original CSV SHA-256; fixed Ridge/Binance/spot identity. No issuance/automation evidence. |
| `HourlyReference` | Symbol, original row `record_id`, native hourly `at`, positive Decimal `price`, original CSV SHA-256 and monthly source SHA-256; Binance/spot identity. No bid/ask or receipt timestamps. |
| `SyntheticMiss` | Symbol, expected source opening, actual synthetic discovery time and explicit fixture reason. Never genuine Stage 3 operational evidence. |
| `HistoricalDecision` | Deterministic identity, symbol/source/decision time, action, target or `None`, missed streak, reason, and original forecast or explicit miss. No price or outcome. |
| `HistoricalOrder` | Earlier decision, side, exact required reference time and pre-trade ledger sequence. Mathematical intent, not submitted exchange order. |
| `HistoricalFill` | Order, original hourly reference, unchanged financial `Trade` with paired postings, separate assumed spread/slippage amounts. |
| `HistoricalMark` | Original hourly reference (including symbol/hour/hash/price), exact ledger sequence, immutable `Account` snapshot, equity/unrealised values and historical kind/valuation policy. Account retains cash, units, remaining weighted-average basis, realised P&L and cumulative fees. |
| `HistoricalResult` | Market, exclusive end, config, initial/final accounts, ordered decisions/fills/marks, input status, `kind=historical_simulation`, explicit unevidenced/untested execution constraints. |

All records are frozen; output histories are tuples. Financial fields remain
Decimal. `historical_json` serialises the dataclass tree with sorted keys, exact
Decimal strings, aware UTC ISO timestamps and a trailing newline; it also provides
the config representation used for SHA-256. No wall clock enters result identities
or JSON. Caller-supplied protocol/model-recipe hashes are required provenance
identifiers, not proof of approval, source authenticity or genuine issuance.

The shared `Portfolio` is a monetary account identity whose key begins
`historical_simulation`; its configuration fingerprint derives from the historical
config and its protocol/recipe hashes are supplied explicitly. It does not create
a prospective portfolio. Nested `Trade.policy` retains the unmodified Stage 4B.1
monetary contract because `apply_trade` authenticates that arithmetic contract;
execution provenance lives in `HistoricalFill` and the historical config/result.
Never detach the proposal and present it as a quote-validated prospective Fill.

## Timing, completeness and conservative adaptation

Funding is exactly 10,000 USDT at 2024-01-01 00:00 per market. Source openings begin
2023-12-31 20:00, then every four hours through 2024-12-31 12:00 (2,195 rows).
Availability must equal source opening +4h +60s. The last signal is therefore
2024-12-31 16:01. The boundary-purged 20:01 signal is not a missing horizon.

The price-free shared Ridge evaluator fixes target exposure. Hypothetical execution
uses the strictly next native hourly opening, e.g. 12:01→13:00. Flat/positive buys,
long/positive HOLDs, long/nonpositive sells, flat/nonpositive CASH_NOOPs. There is
no three-hour forced exit and no repeated transaction while exposure agrees.
A completed full exit needs a new signal to re-enter. The original three-hour
Stage 2C strategy is unchanged.

References must form the exact hourly grid from inception to `end_exclusive`,
exclusive. Default final mark is 2024-12-31 23:00. A shorter fixture still starts
at inception and must include the next reference of every included decision;
truncating a pending intent fails explicitly. All expected forecasts must exist,
including cash signals, and all hourly references must exist, including nontrade
hours. Unsupported, duplicated, unordered, missing, off-grid, out-of-period,
nonfinite or market-mismatched data raise `ValueError`; monetary precision failures
may raise Decimal arithmetic errors. No partial result, skip, backfill or retry
using a later economically favourable reference is returned.

At a reference timestamp the runner first executes the previously scheduled intent,
then records the resulting ledger prefix against that same reference. At an exact
hour, newly discovered misses occur after this mark and wait to the next hour.
This is an explicit historical reporting convention, not intrasecond quote order.
The result remains open if still long at its last mark: no fabricated sale,
2025 price or net-liquidation value is inserted.

Forecasts and synthetic misses must each be strictly source-ordered; references
must be strictly hour-ordered. Their separate source streams merge by identity,
but a supplied stream is never silently repaired by sorting. Effective decision/
discovery times must be nondecreasing. List/tuple choice, independent market call
order and separation of forecast/miss collections are non-economic ordering;
source/trade reordering and duplicate identities are integrity errors.

Explicit `SyntheticMiss` replaces an expected horizon only in deliberately
incomplete fixtures. It requires discovery **strictly after** close +16 minutes,
never an invented earlier decision. Missing has no forecast/target. One miss
preserves exposure; two consecutive misses while long create risk-off at discovery,
then sell at the next hourly reference. Qualifying forecasts reset the streak.
Several misses can share a delayed discovery time. A pending exit takes precedence
over intervening positives; successful full sale satisfies it, with no reuse of
ignored signals. These outputs have `status=synthetic_missing_signals`; normal
structurally complete inputs have `status=complete_inputs`, which is not source
authentication or economic approval. Missing real forecasts must never be turned
into synthetic misses to publish a completed 4B.2B result.

## Shared functions and historical-only mechanics

Reused directly, without modifying their implementation:

- `paper_strategy.evaluate_strategy`: strict Ridge Sign v1 threshold, no prices.
- `paper_execution.affordable_quantity`: maximum step multiple that funds exact
  adjusted notional plus ceiling fee.
- `paper_accounting.fund_account`, `calculate_trade`, `apply_trade`, `reconcile`,
  `replay`: once-only funding, exact paired postings, fee-inclusive weighted-average
  basis, realised P&L, no negative holdings and deterministic ledger verification.
- `fee_for` is invoked by existing sizing/trade functions; it remains the exact
  10-bps USDT fee rounded UP to 1e-8. Shared `money_context` isolates all financial
  arithmetic from caller precision/rounding/traps.

Historical transition logic adapts the same long/cash/HOLD/miss/exit principles,
but does not call `observe_forecast`, `miss_horizon`, `start_strategy`,
`simulate_order` or `value_account` with invented prospective evidence. Historical
availability is assumed at +60s; genuine prospective issuance, 16-minute new-buy
windows, 30-second submitted orders and REST acquisition/receipt chronology do not
apply to next-hour archived-reference execution. Risk discovery uses the same
logical two-miss trigger and strict cutoff as a synthetic fixture convention.
There is no prospective network recovery, filters, latency, retry worker or
persistence parity claim.

`calculate_historical_trade` checks a funded reconciled account, genuine `Side`
enum, market and exact reference/processing-time match. It permits a full cash buy
only when flat and a full held-quantity sale only on the explicit synthetic step.
It returns an arithmetic proposal; the runner establishes signal eligibility and
then applies it. `value_historical` checks the requested integer ledger prefix,
market and time; it computes cash + units × opening reference with the shared
exact Decimal context. It does not call prospective mark validation.

Cost assumptions are fixed: buy reference ×1.0003, sell ×0.9997, plus 10-bps fees.
Full affordable size floors to the versioned synthetic step. No real depth,
exchangeInfo, min/max notional, lot filters, original quote body or exchange-side
timestamp is invented. These constraints are explicitly **not evidenced/untested**.
Alternate positive quantity steps exist for synthetic tests; other cost scenarios
are rejected. A zero-fee price adjustment would violate the financial contract.
Genuine stress/frictionless implementation is deferred for separate approval.

## Synthetic accounting and causality evidence

The new tests cover strict below/equal/above threshold and invalid numerics; all
UTC grid/availability cases including day/month/leap-day/year boundaries; 12:01
versus 12:00/13:00; price-free target evaluation; HOLD, full exits, no-ops and fresh
re-entry; one/two/delayed/exact-hour misses, resets and sticky exits; independent
accounts; full 10/1/2-bps pricing; ceiling fee affordability and synthetic steps;
invalid references/signals even in cash; no invented prospective evidence;
trade-before-mark ledger prefixes; unchanged old marks; and end-of-year holdings.

A hand-checked fabricated 100-USDT reference buys 99.870138 units at 100.03 with
fee 9.99000991 USDT. One more default step exceeds available cash including fee.
A subsequent sell uses 99.97. At constant reference prices, the account's loss
reconciles exactly to actual fees plus assumed spread/slippage for both sides.
These are synthetic arithmetic assertions, not a 2024 economic result.

Every fixture mark is compared with an independent replay of its saved trade
prefix; cash/base equal summed signed movements, basis/realised/fees match, and
realised + unrealised equals equity −10,000 exactly. Independent calls to the
shared evaluator, sizing and accounting produce equal values. Duplicate/reordered
trades, market mismatches, negative balances, zero/off-step sales, repeated buys
while long, wrong-time references and fee overdrafts reject. Prior marks remain
unchanged after later sales; using a later account for an old mark fails.

Re-execution under caller precision 4, ROUND_DOWN and Inexact trapping produces
identical dataclasses and JSON. Pure computations have no durability/concurrency
claim. The runner independently replays its complete ledger before returning.
The full-year synthetic fixture checks precisely 2,195 forecasts and 8,784 marks,
the final 16:01 signal/23:00 mark and an unsold final holding. It uses fabricated
constant prices and forecasts only.

## Verification and preservation

Focused checks executed with the offline cache option:

```sh
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --offline --locked ruff check src/backtest_badger/paper_historical.py tests/test_paper_historical.py
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --offline --locked ruff format src/backtest_badger/paper_historical.py tests/test_paper_historical.py
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --offline --locked pytest -q tests/test_paper_historical.py tests/test_paper_primitives.py
```

**308 passed**: 111 new historical cases and all 197 unchanged Stage 4B.1 cases.
Initial lint findings were corrected before the final clean checks. No dependency
change was needed; the existing `/tmp/badger-uv-cache` worked. Final whole-repository
commands use the requested form without needing `--offline`:

```sh
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked ruff check .
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked ruff format --check .
env -u BADGER_TEST_ADMIN_DSN UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked pytest -q
git diff --check
```

Final results: **1,056 passed, 183 skipped, zero failed** in 30.79 seconds.
All skips are existing integration cases requiring an explicitly configured
isolated PostgreSQL server; `BADGER_TEST_ADMIN_DSN` was unset. No such server was
configured or accessed. Ruff lint passed; **126 Python files** passed formatting;
`git diff --check` passed. New untracked files were also checked for whitespace
with `git diff --no-index --check /dev/null PATH`. Remote CI was not run.

A before/after SHA-256 inventory covered 116 pre-existing tracked source, test,
document, prompt and dependency files. Only the three authorised status documents
changed; **113 hashes remain identical**, including all existing Python source and
tests, approved Stage 4A documents, frozen Stage 3C protocol, prior prompt archives
and dependency files. Git status shows only the five requested new files and
three status-document updates. The approved protocol hashes remain:

- Technical specification:
  `25412bf4f0e83f848adb09d42d16f39e0c46a55a339d525fd576f1fa85dff399`.
- Prospective protocol:
  `f4561da8db29a180b9abc7b131a6455cefca3c6c44318b268ad5428769273cd9`.

All **1,092 existing artifact entries** retain identical paths, sizes, nanosecond
modification times and modes. This inventory uses directory listings and stat
metadata only: **no payload was opened or rehashed**, including genuine Stage 3
records, actual 2024 inputs/Stage 2C–2D outputs and research holdout files.
Metadata equality is not a new byte-level evidence audit and cannot establish
that a prior artifact was authentic. Source pins quoted in the draft are existing
code/document declarations, not newly verified actual input bytes.

The prompt was reviewed for secrets (none identified), archived verbatim at
[`prompts/stage-04-paper/003-historical-continuous-holding-replay-engine.md`](../prompts/stage-04-paper/003-historical-continuous-holding-replay-engine.md),
and compared byte-for-byte with the supplied attachment. Prompts 001–002 and the
frozen protocols remain unchanged. No new actual research artifact, data access,
production change, provider request, migration, commit or push was performed.

## Future loader boundary and unresolved approval choices

No real source-loader integration was executed. After explicit 4B.2B approval,
a small separate adapter can call unchanged `forecast_data.load_forecasts()` and
`execution_data.load_execution_data()`, verify exact declared release pins, select
Ridge and attach canonical row/month identities to these historical records.
The engine will require both full grids; publication additionally requires both
markets and absence of synthetic misses. No source loader is duplicated here.
The [approved historical protocol](stage-04b2-historical-validation-protocol.md) specifies
hashes, reporting, no-overwrite publication intentions and the pre-access gates.

Remaining choices are owner review of this engine and draft, baseline synthetic
step, daily/monthly partial-endpoint labels, optional cash/buy-and-hold context,
recipe fingerprint representation and future immutable manifest/publisher design.
Stress/frictionless costs and counterfactual liquidation are separately reviewed
extensions, not hidden options. Real source verification and output publication
remain unimplemented. No full historical economic evaluation is authorised.

Conservative specification interpretation: Stage 4A's shared transition language
means the same threshold/financial arithmetic and stated position principles;
it cannot mean feeding unauthenticated historical forecasts into prospective
issuance validation or calling hourly opens REST quotes. Stage 4A's optional cost
comparators are deferred because this task explicitly limits mechanics to base.
The previously documented prospective section-11 provisional wording and inception
versus scheduled-mark schema ambiguity remain unchanged and outside this task.

## Subsequent review and approval — 2026-10-16

Following this implementation report, the product owner approved Stage 4B.2A and froze [`historical-validation-v1`](stage-04b2-historical-validation-protocol.md). The approved choices fix the 0.000001 synthetic base-unit step, whole-Stage-2B-manifest-anchored Ridge lineage identity, cash and inception buy-and-hold controls, clearly labelled partial period returns, and exclusive hash-verified research publication. This is a subsequent documentary decision and does not imply a real 2024 replay was performed during Stage 4B.2A. Stage 4B.2B implementation may use synthetic fixtures, but actual 2024 economic calculation is not yet authorised.

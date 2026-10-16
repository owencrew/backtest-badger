# Stage 4B.1 — Deterministic paper-trading primitives

Implemented locally for review on 2026-10-16, from clean `main` at
`50add18c17c8f6e6074bdeb1f636a78e73bb9caf` (newer than the prompt's reference
`0c9766a5be54d38692eebe9f299462adc3361f7f`). Behaviour follows the unchanged
[approved specification](stage-04a-paper-trading-spec.md) and
[prospective protocol](stage-04a-prospective-evaluation-protocol.md).
This is synthetic implementation verification, not an activated experiment or
economic result. No historical replay, genuine forecasts, outcome payloads,
provider, database, scheduler, CLI, deployment or website is involved.

## Layout and reusable patterns

- `paper_types.py`: frozen evidence/value records, enums and shared strict
  Decimal/UTC/identity/quote/filter validation. This fourth module is the only
  deviation from the suggested three-module layout; shared contracts prevent
  circular imports and duplicate validation.
- `paper_strategy.py`: versioned threshold evaluator and pure state transitions.
- `paper_execution.py`: one-shot submitted internal order simulation.
- `paper_accounting.py`: paired monetary proposals, funding, weighted-average
  accounting, replay, reconciliation and immutable-mark valuation.
- `tests/test_paper_primitives.py`: synthetic fixtures and regression tests.

Stage 2C's explicit Decimal contexts, affordability flooring and conservation
checks are useful patterns; `forecast_data.should_enter` supplies the same strict
threshold convention. Stage 3's UTC grid and provenance separation are preserved.
No frozen module is imported or edited. `backtest.simulate_account` is not reused:
its forced three-hour round trips, assumed spread and fee precision differ.

## Public pure-function API

All records are frozen dataclasses; histories and financial pairs are tuples.
No function samples a clock or accesses environment, filesystem, network or DB.
Timestamps are caller-supplied aware UTC; nonzero UTC offsets are rejected rather
than silently normalised. These APIs are not live-command clock overrides.

| Function | Contract / result |
| --- | --- |
| `evaluate_strategy(prediction, *, strategy_id='ridge_sign', version='1')` | Finite exact Decimal four-hour log return → integer target 0/1. Unknown version, floats, NaN and infinity fail. No prices/outcomes enter this function. |
| `fund_account(Account(portfolio), at)` | Exactly 10,000 USDT at the portfolio inception, zero base/basis, ledger sequence 1. A second funding fails. |
| `start_strategy(account, inception_mark)` | Requires the funded prefix and a valid initial observation captured at or after inception; returns immutable `State` with `last_at=marked_at`. Does not approve or activate a live experiment. |
| `observe_forecast(state, forecast, identity, at)` | Returns `(new_state, Decision)`, preserving eligibility/provenance and actual decision time. |
| `miss_horizon(state, source_open, identity, discovered_at)` | Advances exactly one expected source horizon, strictly after its deadline, at the actual discovery time. |
| `simulate_order(order, quote, filters, fill_at, *, run_id, existing=())` | Returns terminal `Result`: `FILLED`, `REJECTED` or `EXPIRED`, typed `Reason`, retained inputs, and either a `Fill` with two postings or no postings. |
| `record_result(state, result, identity)` | Recomputes the proposal, checks the current decision/account snapshot, and returns `(new_state, transition)`. Successful accounting and final exit satisfaction are one pure transition. |
| `affordable_quantity(cash, price, step)` | Greatest positive step-multiple affordable after rounded fee, or zero. Does not consider depth or downsize for exchange-style bounds. |
| `fee_for(notional)` | Exact 10-bps fee rounded upward to 1e-8 USDT. |
| `calculate_trade(portfolio, identity, side, at, quantity, price, *, ledger_seq_before)` | Monetary proposal only, with two signed `Movement`s. Caller supplies an already selected execution price and explicit quantity. Does not certify strategy/quote eligibility. |
| `apply_trade(account, trade)` | Validates every amount, sign, asset, policy, sequence and identity before returning a new account. Supports partial sales and multiple acquisitions. |
| `replay(portfolio, trades)` | One funding plus the caller-ordered sequence; rejects duplicates, reversed times and incorrect ledger prefixes, including reordered equal-time trades. |
| `reconcile(account)` | Checks nonnegative balances/basis/fees, funded sequence/unique identities and exact cash/basis/realised identity. Full history/fee verification uses `replay` and comparison with the supplied account. |
| `value_account(account, mark)` | Uses the exact supplied replayed prefix and saved bid; returns immutable `Valuation`, with unavailable values for missing/invalid price evidence. Wrong account, sequence or policy is an integrity error. |
| `net_liquidation(account, mark, filters)` | Separate hypothetical full-sale equity or `None` if unavailable/ineligible; never changes marked equity. |

`Portfolio` fixes key, Binance Spot BTCUSDT/ETHUSDT identity, inception,
strategy ID/version, model-recipe fingerprint and configuration/protocol hashes.
Keys should include market, policy/version and cohort. Accounts never share cash.
`Balances` pins portfolio, cash, base units, ledger sequence and snapshot time.
`Account` additionally retains basis, realised P&L, cumulative fees and processed
trade identities. Funding occupies sequence 1; every complete fill advances by 2.

`Forecast` retains record identity, source opening, issuance/observation times,
exact prediction, file/content/model-recipe/automation fingerprints, cohort,
selected model and four-hour horizon. The **future reader** must verify original
Stage 3 JSON and qualifying journal attribution before constructing it; these
functions cannot authenticate supplied provenance hashes. They do not refit,
read original artifacts, infer automation from timing, or implement a second
Stage 3 verifier. Only the declared primary timely automated cohort qualifies.

`Order` contains one pre-submitted intent, its decision, balance snapshot, worker
run identity, submission/expiry times and execution-policy version. `Fill` retains
the complete order, quote, effective filters and monetary `Trade`. `Result`
retains attempted quote/filter evidence even on rejection. Caller-supplied
`existing` results detect already processed orders, attempted quotes and reused
buy decisions; the strategy state supplies this context automatically.
Recomputing without that context deliberately reproduces the same proposal;
it does not prove idempotent persistence.

## Strategy and chronology

Ridge Sign v1 buys only above `Decimal('1e-12')`. Equality and lower values target
cash. Positive while long records `HOLD`; nonpositive while flat records
`CASH_NOOP`. An eligible nonpositive forecast while long creates one immutable
`EXIT_REQUIRED` decision. Later signals record `IGNORED_EXIT_PENDING` until the
obligation is satisfied, even when positive. Eligible signals still reset missed
streaks while an exit is pending.

Source openings use the native four-hour UTC grid. Availability is source close
+60 seconds; issuance, observation, decision and a new buy fill must precede the
exclusive close +16-minute deadline. Ineligible observations record
`SIGNAL_INELIGIBLE`, cannot trade or reset the streak, and do not prematurely count
as misses. All expected earlier horizons must be handled before a later one.

The first expected horizon is the current source-close cycle if its deadline
still follows inception; otherwise it is the next cycle. Only forecasts issued
strictly after inception can qualify. Pre-inception expired horizons are never
counted. This explicit rule permits the remaining part of an inception cycle's
window without replaying a previously issued signal.

One discovered miss keeps holdings unchanged and records `SIGNAL_STALE` while
exposed (`SIGNAL_MISSED` in cash). The second consecutive miss creates a current-time
risk exit while exposed. Discovery must be **strictly after** the deadline.
Several missed horizons discovered after downtime are supplied consecutively with
the same actual discovery time; no past decision timestamps are fabricated.

Rejected, failed and expired orders record `ORDER_TERMINAL` and leave the financial
account and exit obligation unchanged. A full sell records `EXIT_SATISFIED` at
its fill time in the same returned state as accounting. Re-entry requires a new
qualifying forecast **issued strictly after** that time. An expired/rejected buy
cannot be retried from its old decision. Dust keeps the exit outstanding.

## Execution and precision

`decision_at <= submitted_at <= request_started_at <= response_received_at <=
fill_at < expires_at`; expiry is exactly submission +30 seconds. Quote RTT is
at most 2 seconds and processing delay at most 1 second, inclusive. Optional
monotonic elapsed seconds must also be finite Decimal in [0,2]. Run identities
must match; prior-run and pre-submission quotes fail. Exit retries use a fresh
order/quote and may outlive the initiating forecast window.

`Quote` preserves venue/type/symbol, bid/ask and respective sizes, request/receipt
times, run/quote identities, source URL, HTTP status, original bytes/hash and
optional monotonic duration. The pure validator checks a five-field bookTicker
JSON object, unique keys, exact Decimal strings, matching parsed values and SHA-256.
The approved design did not give a byte count: this implementation chooses an
explicit **4,096-byte** cap. Unsupported payload shapes fail; no endpoint is called.
The future adapter remains responsible for source authenticity, actual clock
capture and genuine worker identity.

Buy price is ask ×1.0002; sell price is bid ×0.9998. Observed spread is already
included. Fees are USDT notional ×0.001, rounded **up** to 0.00000001. No extra
half-spread or price-tick quantisation is applied.

`Filters` is versioned **effective** market-filter evidence: market identity,
observation time/hash, effective step and min/max quantity, min notional and an
optional applicable maximum notional. The caller must resolve the intersection
of applicable LOT_SIZE/MARKET_LOT_SIZE/notional rules and flag unsupported rules;
this stage does not parse exchangeInfo or assert actual Binance admission.
Evidence must precede submission and be at most one hour old **at fill**. Invalid
bounds, impossible step ranges, unsupported versions and stale evidence reject.

Buy sizing floors the full cash-affordable step multiple. Integer ratios and a
bounded binary search find the maximum size after fee rounding, including tiny
steps where linear decrements would be impractical. Then the entire size must
pass quantity/notional filters and relevant best-level depth. No depth-based
shrinking, partial fills or opposite-side substitution occurs. Sales request all
owned base; off-step or below-minimum residuals are `EXIT_BLOCKED_DUST`.

Financial arithmetic uses a fresh explicit 160-digit ROUND_HALF_EVEN context with
`Inexact` trapped; overflow/unsupported precision fails closed. Financial inputs
are bounded to 160 coefficient digits and decimal exponents [-160,80]. Forecast
comparison only requires finiteness and does not impose monetary bounds.
The sole currency quantisation is upward fee rounding. Nonterminating partial-sale
basis allocation `(basis * sold_qty) / units_before` rounds at 80 significant digits;
the numerator is exact, and the same allocated amount is subtracted from basis
and realised proceeds using exact arithmetic. Full liquidation releases the exact
remaining basis, producing exactly zero units/basis with no hidden writeoff.
Changing the caller's Decimal context does not change results.

Paired postings are USDT `-(N+fee)` / base `+q` for a buy and USDT `N-fee` /
base `-q` for a sale. Conservation is `cash_delta + base_delta * price = -fee`;
these are two assets, not same-currency postings summing to zero.
Accounting-only `calculate_trade` intentionally permits a fixed 10-unit buy or
partial sale for arithmetic examples. Prospective `simulate_order` always uses
full affordable cash or full owned base and separately validates execution.

## Worked example and valuation

The mandatory Stage 4A example passes with these exact test assertions:

| Quantity | Expected and actual USDT |
| --- | ---: |
| Buy 10 at simulated 100.02: fee | 1.00020000 |
| Cash after buy / acquisition basis | 8998.7998 / 1001.2002 |
| Sell 4 at simulated 109.978: fee / net proceeds | 0.43991200 / 439.472088 |
| Basis released / realised P&L | 400.48008 / 38.992008 |
| Remaining 6 units: unrealised at bid 110 | 59.27988 |
| Cash / marked equity | 9438.271888 / 10098.271888 |

Realised + unrealised = 98.271888 = equity −10000 exactly. Separate tests show
fee-only loss at flat execution prices and additional slippage loss with flat
prospective bid/ask references; no profitability inference is made.

`Mark` pins portfolio/identity, actual `marked_at`, `asof_ledger_seq`, the complete
original quote, valuation-policy version/fingerprint and optional scheduled slot.
A supplied scheduled slot must be a native boundary +10 minutes. Both the quote
request and actual mark time must lie in `[slot, slot + 5 minutes)`; the opening
boundary is inclusive and the closing boundary exclusive. A request before the
slot cannot qualify merely because its receipt or mark time falls inside it.
An unscheduled mark supports inception/arithmetic observations. No scheduling or
mark storage is implemented. Missing/stale/invalid quotes yield unavailable
equity/P&L, even in cash; nothing is filled forward.

Every valuation request must begin at or after the portfolio's actual inception.
The initial observation may complete after funding: `inception_at <= request <=
receipt <= marked_at`, with the unchanged maximum 2-second request latency and
1-second receipt-to-mark delay. `start_strategy` retains the original inception,
funded account and expected-horizon grid, but starts its transition clock at the
actual initial mark time, preventing decisions before that observation.

Quote receipt must be **at or after `Account.at`**, the latest financial event
included in the pinned replayed prefix. Thus a still-fresh pre-trade quotation
cannot value post-trade holdings, including partially or fully sold positions.
The existing mark-time/prefix integrity checks still raise `ValueError`; invalid
quote timing returns an unavailable `Valuation` retaining the supplied mark,
realised P&L and fees. `net_liquidation` also returns `None` for these marks.
No quote is replaced, timestamp moved or past mark reconstructed.

These checks establish local timestamp bounds, not full transactional snapshot
consistency. Equal receipt/transaction timestamps remain accepted by the pure
API; they cannot establish which event happened first. Stage 4C persistence must
enforce equal-timestamp event ordering and coherent quote/ledger snapshots under
the portfolio lock, including concurrent fills. Receipt is a client observation
time, not an independently witnessed exchange-side timestamp.

The caller must pass the already-replayed account **at that exact sequence**.
Value is cash + units ×saved bid; unrealised is units ×bid −basis. Replay tests
retain an earlier mark and reconstruct identical equity after later trades; using
the later account directly fails. Hypothetical net liquidation additionally checks
full-sale quantity/notional/depth/filters and applies sell slippage/fee separately.
There is no observed drawdown series, benchmark runner or performance report yet.

## Validation, preservation and remaining gates

Original Stage 4B.1 verification from the repository root:

```sh
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked ruff check .
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked ruff format --check .
env -u BADGER_TEST_ADMIN_DSN UV_CACHE_DIR=/tmp/badger-uv-cache uv run --locked pytest -q
git diff --check
```

**900 passed, 183 skipped, zero failed** in 28.61 seconds, including **152 new
synthetic cases**. All skips are existing isolated-PostgreSQL integration cases.
Ruff lint, formatting and whitespace checks passed. Remote CI was not run.
Initial fixture/collection mistakes were corrected before these final results.
Tests cover all six UTC boundaries, threshold/invalid numerics, independent accounts, HOLD/sticky exits,
miss discovery/reset, fresh-only re-entry, quote/clock/filter/depth failures,
fee-ceiling affordability, exact paired accounting, weighted-average partial/full
sales, duplicates/reordering, deterministic transitions/replay and historical marks.

The original default-cache `uv run --locked ruff ...` invocations failed because
the sandbox could not access `~/.cache/uv/sdists-v10/.git`. Validation uses
`UV_CACHE_DIR=/tmp/badger-uv-cache`; dependencies and lockfile are unchanged.
`BADGER_TEST_ADMIN_DSN` is unset for pytest so existing integration fixtures skip;
no application/production or substitute PostgreSQL server is configured.

Preservation checks found identical SHA-256 values for all ten protected Python
modules and three frozen protocol documents. The approved Stage 4A hashes are:

- Technical specification: `76e7e80c3aa0eb171281fc4dcd244309a18d752df980d223c40d919669deffba`.
- Prospective protocol: `f4561da8db29a180b9abc7b131a6455cefca3c6c44318b268ad5428769273cd9`.

All **1,092 existing artifact files** retain identical paths, sizes and nanosecond
modification times. Their payloads were not opened or rehashed, preserving the
no-outcome/holdout-access boundary; this is metadata preservation evidence, not a
new byte-level artifact audit. No artifact was created, changed or deleted by this
implementation. Git changes are limited to the four new modules, synthetic tests,
this guide, verbatim prompt archive and architecture/roadmap/handoff updates.

No new dependency, database object, migration, I/O adapter or runtime command was
added. The exact substantive prompt is archived at
`prompts/stage-04-paper/001-deterministic-paper-trading-primitives.md`, reviewed
for secrets and verified byte-for-byte against the supplied attachment.

No unresolved behaviour discrepancy with the approved Stage 4A requirements was
identified. Implementation choices needing retention in eventual configuration
include the numerical precision envelope, 4,096-byte quote cap, explicit initial
grid rule and supported effective-filter schema. Hashes identify caller-supplied
evidence; they do not prove external publication or authentic local clocks.
REST timing is local RTT, not exchange-side quote age or guaranteed execution.

Stage 4C must supply serialisation/locks and DB constraints: exactly one active
submitted order per portfolio, unique decisions/order/fill/quote/funding identities,
immutable events, exact two-row signed postings, terminal status consistency,
ledger-prefix locking, and atomic final-sale/exit-satisfaction commit. The pure
model offers no concurrent lock, crash durability, true commit, automatic recovery,
or five-minute retry scheduler. Never apply a naked monetary proposal to a live
account without execution validation and this atomic persistence boundary.

Next: **Stage 4B.2 historical continuous-holding validation**, separately authorised,
using the same threshold/financial mechanics with explicitly historical next-hour
references and synthetic depth/filter assumptions. Do not represent historical
references as prospective quotations or change the frozen Stage 2C results.

## Valuation timing correction review — 2026-10-16

Correction baseline: clean HEAD `27ae92a697f2dc057f326c398353fc4988c7e5ca`.
Changes are confined to valuation timing, initial-observation transition time,
synthetic regressions, this guide and the verbatim prompt archive
`prompts/stage-04-paper/002-valuation-timing-corrections.md` (reviewed for secrets).
Decimal equations, replay, Ridge decisions, execution, filters, costs, balances
and sticky exits are unchanged.

Added 45 synthetic cases: quote receipt immediately before/at/after buys,
partial sales and full sales; all six scheduled slots at exact opening/closing
boundaries and one microsecond either side where relevant; pre-window requests
with in-window receipts; exact and excessive quote freshness bounds; pre-inception
requests and valid observations completing after inception. Tests also verify
unavailable liquidation, retained evidence, replay equality, activation chronology
and successful subsequent orders.

Correction verification (all commands completed successfully):

```sh
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --offline --locked pytest -q tests/test_paper_primitives.py
env -u BADGER_TEST_ADMIN_DSN UV_CACHE_DIR=/tmp/badger-uv-cache uv run --offline --locked pytest -q
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --offline --locked ruff check .
UV_CACHE_DIR=/tmp/badger-uv-cache uv run --offline --locked ruff format --check .
git diff --check
```

Paper primitives: **197 passed**. Complete suite: **945 passed, 183 skipped,
zero failed** in 30.26 seconds. Skips require an isolated PostgreSQL server;
none was configured or accessed. Ruff lint passed, all **122 Python files** passed
format checking, and whitespace checks passed. No network access, commit, push,
deployment or Stage 4B.2 work was performed.

Documentation inconsistencies found, reported without editing approved Stage 4A:
the prospective protocol's section 11 retains provisional/draft and pending-signoff
wording despite its approved header and the technical specification's approval;
the technical schema's section 6.4 requires `mark_slot` for every `MARK_OBSERVED`,
while the prospective protocol separately requires an actual inception mark that
need not fall on the scheduled grid. Stage 4C must distinguish inception from
scheduled marks in its persistence contract. Neither issue authorises changing
the frozen protocol in this correction.

The original verification section above records the earlier implementation's
technical-specification hash. At this correction's baseline, the specification
hash is `25412bf4f0e83f848adb09d42d16f39e0c46a55a339d525fd576f1fa85dff399`;
both the working file and `HEAD` have that value. The prospective protocol still
matches `f4561da8db29a180b9abc7b131a6455cefca3c6c44318b268ad5428769273cd9`.
Both approved documents are unchanged by this correction.
Stage 4C persistence and Stage 4D forecast/quote adapters, worker integration,
clock-health checks, backup extension and deployment remain subsequent gated work.

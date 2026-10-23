# Stage 4B.2E.5b — native-minute economic reporting

Prepared for owner review on 2026-10-23 against checkout
`727b3172a6ed238bf74bf010311dcdbad1fef7a7`. All exercised accounts, forecasts,
prices and source fingerprints are fabricated. No original evidence was opened,
no genuine evaluation was executed and no economic files were published.

The adapter fills the reporting gap between the existing shared minute monetary
core and a future, separately authorised runner. It does not implement that runner,
owner authorisation, attempt consumption, signing, source acquisition or publication.
The public genuine gate and the E.5 TEST evidence transport remain unchanged.

## Pure API and integrity boundary

`src/backtest_badger/paper_minute_reporting.py` exposes four functions:

| Function | Required keyword arguments | Result |
| --- | --- | --- |
| `minute_reporting_fingerprint(account, ...)` | `end_exclusive` | SHA-256 string to retain independently before reporting handoff |
| `minute_cost_attribution(account, ...)` | `end_exclusive`, `expected_fingerprint` | Metadata, account side totals and daily/monthly cost-flow buckets |
| `minute_period_observations(account, ...)` | `end_exclusive`, `expected_fingerprint` | Metadata and daily/monthly observed mark-to-mark periods with their cost flows |
| `minute_reporting_summary(account, ...)` | `end_exclusive`, `expected_fingerprint` | Metadata, unchanged account performance, authoritative account/mark objects, flows, periods and complete-day statistics |

Every entry verifies the `MinuteAccount` using the unchanged
`verify_minute_account(account, end_exclusive=...)`. Reporting additionally checks
the separately supplied fingerprint; there is no unverified mode or default pin.
The summary composes the unchanged `minute_account_summary` without replacing its
accounting, cost assumptions, exposure or drawdown calculations. Fill/reference
timestamps must match exactly. Funding must start at the frozen START, and fill
and mark sequences must be tuples.

The required fingerprint is an owner-approved addition to the initial reporting
contract. The original verifier establishes ledger/mark consistency, but cannot
detect all changes to caller-supplied evidence. For example, replacing a valid
source hash or changing a cash account's mark price can leave accounting unchanged.
Tests demonstrate that these cases pass the core verifier and are then rejected
against the retained reporting fingerprint.

The fingerprint is SHA-256 over UTF-8 bytes of the existing `scientific_json` of:

```python
{
    "schema": "native-minute-economic-reporting-v1",
    "account": account,
    "end_exclusive": end_exclusive,
}
```

The entire account dataclass is encoded, not just financial totals: label, status,
reason, initial/final accounts and portfolio metadata, full trades and signed
postings, trade identities, decision identities, fill kinds, original reference
identities/prices/source hashes, raw fill costs, and every ordered compact mark
and ledger prefix. The endpoint is bound even for an unavailable account without
marks. Shared canonical encoding sorts dictionary keys, preserves sequence order,
encodes Decimal operands as exact strings and UTC datetimes as ISO strings with
`+00:00`, and includes a trailing newline. It rejects floats/nonfinite money.

The fixture owner retains the digest before handing the account onward. A caller
who changes an account and supplies a newly computed digest defeats that guarantee.
The helper does **not** authenticate market data, prove independent retention,
certify strategy decisions, or grant execution authority. The account fingerprint
does not include the containing replay result's full forecast/projection history,
source envelope or original publication bytes. Those remain upstream obligations.

All functions return in-memory Python values. Original frozen `MinuteFill`,
`MinuteMark` and `Account` objects are retained in the output; no parallel financial
record types are introduced. `scientific_json(payload)` can encode a returned
payload deterministically in memory. This stage provides no reader, writer, CLI,
publication manifest or new genuine export path.

## Metric schema and interpretation

Common metadata contains `schema`, `account_id`, `symbol`, `label`, `status`,
`reason`, `start_inclusive`, `end_exclusive`, `initial_funding`,
`execution_interval_seconds=60` and `valuation_interval_seconds=3600`.
BTCUSDT and ETHUSDT are independent; each Ridge, cash and inception B&H account
is separately funded with Decimal `10000` USDT. The adapter never pools them.

Each `costs_by_side` mapping contains BUY and SELL entries:

| Field | Meaning |
| --- | --- |
| `count` | Number of actual hypothetical fills on that side |
| `notional` | Sum of exact `fill.trade.notional`: execution-price-adjusted quantity × price after the core's fee-aware sizing; fees remain a separate amount |
| `fees` | Sum of recorded `fill.trade.fee`, including the core's fee ceiling |
| `hypothetical_half_spread` | Sum of recorded `fill.half_spread_cost` |
| `hypothetical_slippage` | Sum of recorded `fill.slippage_cost` |
| `turnover_denominator` | Initial Decimal `10000` USDT funding |
| `turnover_initial_funding` | Side notional divided by that denominator, using the frozen 80-digit division policy |

No costs are recomputed from hourly prices or rounded to display precision.
Evidence in each bucket's `fills` tuple preserves the actual reference timestamp,
trade timestamp and source identity. Daily and monthly buckets are alternative
aggregations of the same fills: never sum the daily and monthly views together.
Within either view, each fill appears exactly once.

Cost-flow rows contain `period` (`daily` or `monthly`), `start`, the next UTC
calendar `boundary`, `flow_end_exclusive`, `flow_complete`, `fills` and
`costs_by_side`. A bucket selects `start <= fill.trade.at < flow_end_exclusive`,
where `flow_end_exclusive=min(boundary, end_exclusive)`. Thus a 00:00 fill belongs
only to the new period; a 00:02 fill retains its own price and timestamp.
`flow_complete` describes coverage of the scenario's calendar interval, not
availability of the next boundary valuation.

Observation rows additionally contain:

| Field | Meaning |
| --- | --- |
| `end` | Next calendar boundary if observed, otherwise the last observed HH:00 |
| `complete` | Whether the closing calendar-boundary mark exists |
| `observed_seconds` | Actual mark-to-mark duration |
| `missing_boundary_seconds` | Calendar boundary minus observed end |
| `start_mark`, `end_mark` | Original authoritative marks, including reference identities and ledger prefixes |
| `pnl` | Exact end equity minus start equity |
| `return` | P&L divided by start equity at 80 digits; `None` for zero observed duration |
| `return_basis` | `observed_hourly_mark_to_mark` |

Complete days use consecutive UTC midnight marks. Months use first-of-month
midnight marks. Under the full-year contract there are 366 daily observations
(365 complete) and 12 monthly observations (11 complete). February has 29 days.
December 31 runs 00:00–23:00, so `observed_seconds=82800`,
`missing_boundary_seconds=3600` and `complete=False`. December likewise ends one
hour short. Their cost-flow intervals are complete through END, independently of
the absent valuation. END is only an exclusive scenario/flow or exposure-duration
boundary: no 2025-01-01 price or liquidation is constructed.

The summary's `complete_day_statistics` contains `count`, `mean`, `min` and `max`
of **complete daily returns only**. Empty statistics have count zero and all three
values `None`. Partial final days never enter these statistics. All monetary
sums/differences use the existing 160-digit exact context with Inexact trapped;
ratios and the mean use its 80-digit HALF_EVEN division context. Ambient Decimal
precision and rounding do not alter reports. Display rounding is a consumer concern.

For available accounts, `performance` is exactly the unchanged minute summary:
`status`, `costs_by_side` (its original field names), `last_mark_at`,
`last_mark_pnl`, `funding_relative_marked_return`, `exposure_seconds`,
`period_seconds`, `invested_hourly_mark_fraction` and
`maximum_observed_hourly_reference_mark_drawdown`. This nested cost view retains
the core's `half_spread`/`slippage` names; the reporting cost view above adds the
explicit turnover denominator and uses the longer hypothetical-cost names.
There are no Sharpe, annualisation or new realised/unrealised return ratios.

The drawdown starts from initial funding and uses observed hourly-reference marks,
including inception costs. It is not intrabar, per-minute or continuous drawdown.
B&H's inception fill at START is included once in January/January 1 flows and in
funding-relative performance. Its first mark is already post-trade. Its first
mark-to-mark return does not charge that inception cost again.

`initial_account`, `final_account` and `last_observed_mark` preserve authoritative
state. The mark includes cash, units (`quantity`), basis, realised/unrealised P&L,
fees, equity and ledger prefix. A short synthetic fixture can trade after its
last HH:00: its final ledger then differs from its last observed mark. The adapter
reports both and does not attach an invented valuation to the final ledger.

Unavailable B&H has `status="unavailable"`, the exact core reason
`inception_full_fee_affordable_buy_infeasible`, `performance=None`,
`last_observed_mark=None`, `costs_by_side=None`, and empty flows/observations.
Initial/final funded accounts remain available, with no invented fills or marks.
The core verifies unavailable-account structure; the account alone lacks the
inception reference needed to independently re-prove infeasibility. That fact must
come from the upstream replay. Cash remains available with zero fills and costs.

## Synthetic validation

The new test module uses `replay_minute_historical`, which calls the shared monetary
core, for short fixtures and both markets' full fabricated leap years. No genuine
result parser or replay entry point is invoked. Coverage includes:

- Off-hour HH:02 costs with deliberately different HH:00 prices and long exact
  Decimal prices; fee-aware notional, fees, spread, slippage and turnover.
- Separate Ridge/cash/B&H funding, inception costs, explicit unavailable B&H,
  zero-trade cash, zero-duration periods and trades after a short fixture's last mark.
- Exact midnight exits at day-end, January month-end and leap-day month-end;
  half-open attribution, post-trade boundary marks and no double-counting.
- Full-year daily/monthly returns and flow conservation, February 29, partial final
  day/December, complete-day-only statistics and no END valuation/liquidation.
- Timestamp mismatch, duplicate/missing/reordered fills and marks, wrong market,
  account, label or endpoint, changed funding/final state, trade identities,
  reference hashes/prices, fees/spread/slippage and all financial mark fields.
- Core-consistent source/mark/portfolio metadata mutation rejected by the retained
  pin; mandatory core verification, exact fingerprint schema and serialization.
- Unchanged core summary composition and stability under low ambient precision.

Direct execution installs the offline guard before pytest or project imports.
It disables site initialisation, bytecode writes, plugin autoload, conftest,
pytest cache/logging and filesystem capture. Its exact-file collector retains
pytest fixtures and parametrization while avoiding ancestor-directory scanning.
Only the selected test files, approved source dependencies and installed runtime
are readable; protected evidence paths, other data reads, writes, network/process
operations and source symlink reads are denied. Repository directory enumeration
is restricted to import directories. The ordinary pytest route also installs a
per-test protected-path/network guard. These are procedural Python guards, not an
OS security boundary against hostile native code.

The regression mode runs the complete existing minute-accounting and synthetic
minute-integration modules plus ten explicitly selected pure hourly reporting
tests. It excludes hourly publication/writer tests and the protocol-file test,
which would need additional document access. No test invokes a writer.
The separate existing E.5 launcher remains unchanged and is run independently.

Final targeted validation passed on Python **3.12.13**, using installed project
dependencies without a dependency fetch or sync:

```sh
python3.12 -I -S -B tests/test_paper_minute_reporting.py --regressions
python3.12 -I -S -B tests/run_e5_guarded.py
```

| Command | Executed result |
| --- | --- |
| Reporting launcher with `--regressions` | **303 passed**, zero skips: 114 new reporting cases and 189 existing regression cases; 42.86 seconds |
| Unchanged E.5 guarded launcher | **87 passed**, zero skips; 36.077 seconds |

The independent E.5 step was executed once and was unaffected by subsequent edits
to the new reporting tests. Its 87 cases remain deliberately skipped by ordinary
pytest; that is not a failure of the separately executed guarded suite.

During development, the reporting-only command
`python3.12 -I -S -B tests/test_paper_minute_reporting.py` passed 78 cases, then
112 after strengthening evidence checks. Two additional month-boundary cases
bring the final reporting count to 114, all executed in the final 303-case run.
An earlier combined run passed 267 cases. Initial launches stopped before tests
when dependency lookup, capture/logging writes or ancestor-directory collection
hit the guard. These launches are not reported as successful tests. Capture,
logging and filesystem collection were removed from the test path; protected
evidence, write and network denials were retained.

Final scoped lint and formatting commands use the project environment's installed
**Ruff 0.17.0** (initial formatting also used system Ruff 0.12.0):

```sh
.venv/bin/ruff check --isolated --no-cache --no-respect-gitignore --select E,F,I,UP,B --target-version py312 src/backtest_badger/paper_minute_reporting.py tests/test_paper_minute_reporting.py
.venv/bin/ruff format --check --isolated --no-cache --no-respect-gitignore --target-version py312 src/backtest_badger/paper_minute_reporting.py tests/test_paper_minute_reporting.py
```

Both checks pass. New-file whitespace is checked with
`git diff --no-index --check /dev/null PATH` for each of the four deliverable paths,
so untracked content is included. These comparisons return exit 1 because the
files are additions; absence of whitespace diagnostics is the successful check.
The archived request's trailing blank line was removed to satisfy this check.
Preservation uses this scoped tracked comparison:

```sh
git diff --no-ext-diff --exit-code HEAD -- AGENTS.md src/backtest_badger/paper_minute_historical.py src/backtest_badger/paper_historical_evaluation.py src/backtest_badger/paper_accounting.py src/backtest_badger/paper_types.py src/backtest_badger/paper_historical.py src/backtest_badger/paper_execution.py src/backtest_badger/paper_strategy.py src/backtest_badger/genuine_minute_publication.py src/backtest_badger/genuine_minute_replay.py src/backtest_badger/genuine_backtest_preparation.py tests/test_paper_minute_historical.py tests/test_paper_historical_evaluation.py tests/test_paper_minute_integration.py tests/test_genuine_backtest_preparation.py tests/run_e5_guarded.py docs/stage-04b2c-minute-execution-protocol.md docs/stage-04b2e5-one-shot-backtest-preparation.md docs/stage-04b2e5-run-contract.json .github/workflows/ci.yml pyproject.toml uv.lock
```

That comparison is empty (exit zero). The scoped status lists exactly the four
new deliverables; no existing file was edited. The archived prompt preserves the
substantive request (with one terminal newline), without attachment/session metadata.
The owner subsequently
approved necessary dependency reads/imports and the retained-fingerprint contract;
those approvals are documented here, not inserted into the original request archive.
No unrestricted status or repository-wide lint/test discovery is needed for these
checks. Unnamed files and original evidence were not audited. Full-suite and
locked-environment CI on a future owner-created commit remain outstanding.

## Remaining E.5 integration and review gates

No mapping to `genuine_backtest_preparation`'s TEST evidence schema is introduced.
A future authorised producer could hand off each existing `MinuteAccount`, its
reviewed endpoint and an independently retained digest to these functions. Before
any genuine use, owner review must establish the producer/retention boundary,
authenticate and bind the outer result's original provenance and decisions,
approve a concrete reporting/export schema, and verify its mapping to original
source and ledger identities. The existing TEST transport is not certified economics.
Owner authorisation, a bounded runner, durable one-attempt/crash handling, output
destination policy and publication verification remain separate unfinished stages.

Owner review checklist:

- Review the required independent fingerprint and its limited integrity guarantee.
- Review actual-fill flow attribution versus post-trade mark-to-mark returns,
  partial-period flags, zero-duration fixtures and unavailable-account treatment.
- Confirm the preserved core, protocol, public gate, E.5 transport and CI workflow.
- Require green CI for the eventual owner-created commit, including the separate
  mandatory 87-test E.5 step; local targeted results do not replace full CI.
- Keep genuine evidence access and historical evaluation separately unauthorised.

2024 is previously inspected exploratory validation, not untouched out-of-sample
performance or evidence of tradable alpha. These tests establish consistency of
fabricated hypothetical accounting/reporting, not financial viability or actual
trading results. No commit, push, deployment or economic publication is part of E.5b.

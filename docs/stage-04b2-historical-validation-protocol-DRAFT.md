# Stage 4B.2 — Historical continuous-holding validation protocol

**DRAFT / NOT YET APPROVED FOR 2024 EXECUTION**

Version: `historical-validation-draft-v1`

Prepared: 2026-10-16, before viewing any new continuous-holding economic result.

Implementation gate: Stage 4B.2A, supplied synthetic inputs only. Stage 4B.2B
requires separate review and explicit authorisation before opening actual inputs.

## Scope and scientific status

The intended experiment describes a deterministic 2024 historical simulation of
Ridge Sign v1 with continuous long/cash holdings. It is neither a prospective
paper-trading portfolio nor evidence of actual exchange fills. Existing Stage 2C
three-hour round trips and Stage 2D diagnostics remain separate and frozen.
The Ridge choice follows previously inspected validation research; it is not an
independently tested alpha hypothesis. No thresholds, models or parameters are
selected using this experiment. No 2025–2026 research/holdout labels, genuine
Stage 3 forecast/outcome/operations artifacts, database or provider are required.

The approved [Stage 4A specification](stage-04a-paper-trading-spec.md) and
[prospective protocol](stage-04a-prospective-evaluation-protocol.md) are unchanged.
This draft does not reapprove or revise them. Its historical timing and reference
prices cannot pass their genuine issuance and REST observation requirements.

## Frozen input declarations, not newly verified artifact bytes

These identities are transcribed from `forecast_data.py` and the existing
[Stage 2B](stage-02b-predictive-baselines.md),
[Stage 2C](stage-02c-execution-backtesting.md) and
[Stage 2D](stage-02d-economic-diagnostics.md) documentation. Stage 4B.2A has **not**
opened or rehashed the corresponding actual artifact payloads.

| Input | Declared SHA-256 |
| --- | --- |
| `artifacts/experiments/stage-2b-v1/validation_predictions.csv` | `e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674` |
| `artifacts/experiments/stage-2b-v1/manifest.json` | `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581` |
| `artifacts/execution/binance-1h-2024-v1/hourly_opens.csv` | `39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a` |
| `artifacts/execution/binance-1h-2024-v1/manifest.json` | `1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d` |
| `artifacts/execution/binance-1h-2024-v1/acquisition.json` | `926697a89eb7c018ca5913f1e3c4c1170715db5639d444a58a78012e92aec055` |

Stage 2B declares the original research CSV fingerprint
`04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8`
and research manifest fingerprint
`a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e`.
These are lineage declarations only: this replay must not open that research CSV.
The original per-market train-only five-feature standardised Ridge recipe
(`alpha=1.0`, `solver="svd"`) is retained, never regenerated or refitted.

The independent hourly release comprises exactly 24 native monthly ZIPs and
24 official checksum sidecars, 12 months for each Binance Spot market. The exact
monthly identities, row counts and ZIP hashes are declared in the
[Stage 2C source table](stage-02c-execution-backtesting.md#independent-native-hourly-acquisition).
The future manifest must retain all of that loader-verified source metadata,
including original URLs, hashes and actual retrospective acquisition timestamps.
Acquisition timestamps are not 2024 availability or exchange quote timestamps.

After separate approval, Stage 4B.2B will call `forecast_data.load_forecasts()`
with its unchanged default pins and `execution_data.load_execution_data()`.
The latter reproduces the CSV from source archives but does not itself hard-code
the reviewed release manifest hash: the future adapter must additionally compare
its returned manifest/output hashes with the declarations above. Do not accept
an internally consistent but different release. No duplicate artifact loader,
new acquisition or hash override for genuine data is permitted.

Select only `(symbol, "ridge")` from the forecast loader. Construct row identities
from venue/type/symbol/native interval/source opening/model and retain the pinned
CSV hash. Construct hourly identities from venue/type/symbol/3600/opening, retaining
the CSV hash and the corresponding monthly source ZIP hash. The loader metadata
provides that month-to-source association. The future adapter must pin a canonical
fingerprint of the **existing** declared Ridge recipe, without re-fitting it, and
record its precise canonicalisation in the run manifest. The pure engine accepts
caller-supplied protocol/recipe hashes; it does not authenticate them.

## Period, grid, availability and account transitions

- Period: `[2024-01-01T00:00:00Z, 2025-01-01T00:00:00Z)`.
- Each market has exactly 2,195 source horizons: 2023-12-31 20:00 through
  2024-12-31 12:00, inclusive, every four hours. Feature availability equals
  source opening +4h +60s. Last eligible availability is 2024-12-31 16:01.
  Do not invent the boundary-purged 20:01 signal.
- Each market requires all 8,784 hourly openings: inception 00:00 through
  2024-12-31 23:00 inclusive. No 2025-01-01 00:00 price is used or invented.
- BTCUSDT and ETHUSDT each receive exactly 10,000 USDT once at inception. No
  transfers, shared cash, borrowing, leverage, shorts or later funding.
- Evaluate `paper_strategy.evaluate_strategy(prediction)` with no price/outcome
  input. Strictly `prediction > Decimal('1e-12')` targets long; equality targets cash.
- First permissible hypothetical reference is the native hour strictly after
  feature availability: 12:01 means 13:00, never 12:00. Decisions retain the assumed
  availability timestamp, explicitly **not** an original publication timestamp.
- Flat/long buys once; long/long HOLDs; long/cash sells all; flat/cash CASH_NOOPs.
  One position transition per signal, with no three-hour forced sale. Preserve
  exposure between signals. Re-entry requires a new eligible source horizon after
  a completed exit; no previously ignored positive signal is replayed.

Every hourly event executes an already eligible scheduled trade **first**, then
marks the resulting ledger prefix with that exact hourly opening. This is a
historical reporting convention, not evidence of intrasecond trade/quote order.
A discovery exactly on an hour occurs after that hour's trade/mark and can trade
only at the strictly next hour. No future reference participates in a decision.

## Missingness, failures and synthetic risk-off tests

Required missing, duplicate, unordered, off-grid, nonfinite, nonpositive-price,
market-mismatched or out-of-period evidence aborts the calculation. This includes
cash/HOLD hours, not just profitable or traded horizons. No substitution, later
favourable price selection, imputation, forward filling or partial-success report.
Malformed inputs fail before a completed result is returned. A 4B.2B publication
must require the full pinned grids, both markets and no synthetic miss records.

For mechanics tests only, `SyntheticMiss` explicitly replaces a source horizon,
with a reason and actual synthetic discovery time strictly after close +16min.
Missing has `target=None`, never zero/negative. One miss leaves exposure unchanged;
two consecutive misses while long create one risk-off exit at discovery, executed
at its strictly next hourly reference. A valid signal resets the streak.
Several misses may be discovered at the same later time, in source order. A later
signal cannot be backdated before discovery. Pending exits suppress intervening
positive signals; the successful full sale satisfies the obligation, and only a
new signal can buy again. If required reference evidence is missing the entire
fixture fails, rather than retrying at a later price.

These fixtures are labelled `synthetic_missing_signals` and cannot represent
completed validation research. They test a shared safety principle, not a Stage 3
network worker, real outage chronology, retry cadence or prospective recovery.
Synthetic misses are not an escape hatch for missing real forecasts.

## Fixed base economics and unsupported execution constraints

Only `HistoricalConfig(version="historical-base-v1")` is supported:

| Assumption | Fixed policy |
| --- | --- |
| Fee per side | 10 bps of adjusted notional, USDT, rounded UP to 0.00000001 |
| Hypothetical half-spread | 1 bp per side relative to opening reference |
| Hypothetical adverse slippage | 2 bps per side |
| Buy / sell price | `P * 1.0003` / `P * 0.9997` |
| Sizing | Full fee-affordable cash purchase, full held quantity sale |
| Default base quantity step | `Decimal('0.000001')` for both markets |
| Sizing convention | `hypothetical-base-step-v1`, explicitly synthetic |

The step is a versioned configuration field, included in its fingerprint. Alternate
positive steps are supported for synthetic edge tests; the intended historical
baseline fixes the default before any real results are viewed. It is not a Binance
filter. A step change requires separately labelled configuration/results.

Reuse exact Stage 4B.1 affordability, fee, paired postings and weighted-average
accounting. Financial calculations use its isolated 160-digit context with inexact
arithmetic trapped; unsupported precision fails rather than silently rounds.
Prices are not additionally tick-rounded. Notional plus ceiling fee must fit cash;
zero/negative/off-step quantities and negative balances fail. Full exits release
all remaining acquisition basis, including buy fees, without dust writeoffs.

Historical opens are not observed bid/ask. Real best-level depth, exchange filter
snapshots, market impact, minimum/maximum notionals, timestamp freshness and real
fillability are **not evidenced/untested**. No invented bookTicker body, run ID,
automation hash, timestamp or exchangeInfo record is constructed. Mathematical
fills are contingent on simplified assumptions. `simulate_order()` is not called.
The reused `Trade.policy` identifies the unchanged Stage 4B.1 monetary contract;
the surrounding `historical_simulation` result, historical config and opening
reference define execution provenance. A naked `Trade` is never a prospective fill.

Frozen Stage 2C scenarios are frictionless (0/0/0), base (10/1/2) and stress
(10/3/10) bps (fee/half-spread/slippage). Stage 4B.1 intentionally fixes a 10-bps fee.
Stage 4B.2A implements **only base**. Frictionless and stress require separate
approval and an economically consistent scenario implementation in a future
4B.2B extension. Never hide zero/alternative fees by adjusting the reference price,
or weaken the approved prospective fee contract. Stress still has 10-bps fees,
but its different price assumptions are unsupported by this base-only adapter.

## Marks, reconciliation and planned reporting

Funding is an explicit 10,000-USDT point, ledger sequence 1. Every hypothetical
fill has exactly two signed postings and advances the sequence by two. Each mark
retains its market/hour, original hourly identity and hashes, reference price,
account snapshot and ledger sequence. These are `historical-opening-reference-v1`
observations, never prospective `MARK_OBSERVED` events.

At each valid mark:

```text
equity = cash + base_quantity * archived_open
unrealised = base_quantity * archived_open - remaining_cost_basis
realised + unrealised = equity - 10000
cash = 10000 + sum(USDT postings through the pinned prefix)
base_quantity = sum(base postings through the pinned prefix)
```

Replaying the exact prefix must reproduce cash, quantity, fee-inclusive basis,
realised P&L and cumulative fees exactly. An earlier mark must reproduce unchanged
after later trades. Replaying all trades must equal the final account. Separate
execution-side spread/slippage amounts use actual quantity times original reference
times the respective rates; fee totals come from actual postings, not another
scenario's capital path. No alternate liquidation value is implemented in 4B.2A.
At year-end retain cash, base, basis and reference-marked P&L. **No forced sale.**
A separately approved future counterfactual liquidation would need explicit costs
and valid evidence and must never become an actual ledger sale.

Planned 4B.2B outputs per market, before examining results:

- All decisions and counts by action, mathematical orders/fills, missing/rejected
  evidence counts/status, exact final holdings/cash/basis/realised/unrealised P&L.
- Starting/final reference equity and total return; all hourly marks with coverage.
- Buy/sell notional totals and each divided by 10,000; fees, hypothetical spread
  and slippage costs by side. Keep quantities and paths scenario-specific.
- Time invested from actual transition intervals over the declared period, with
  a final open interval ending at END solely for duration (no invented END price).
  Separately report fraction of valid hourly marks invested and mark exposure.
- Maximum **observed-hourly-reference-mark** drawdown from inception and retained
  marks, never continuous-time or intrabar drawdown. Missing observations are not
  interpolated; incomplete real input prevents completed publication.
- UTC daily returns only between consecutive exact 00:00 reference marks.
  December 31 lacks the next 00:00 mark: any 00:00→23:00 change must be explicitly
  labelled a partial 23-hour observation, excluded from complete daily statistics.
  Monthly returns use first-of-month 00:00 boundaries; December ends at the last
  available 23:00 mark and is labelled partial by one hour. Include all months;
  no best-month selection. Display rounding never replaces authoritative Decimals.
- Flow counts/costs belong to their actual UTC fill dates. Mark-to-mark P&L retains
  unrealised changes, unlike Stage 2D's exit-month round-trip attribution. The full
  baseline's permitted fills never occur at midnight, avoiding a boundary-flow
  ambiguity; new timing policies must explicitly resolve any such ambiguity.
- Potential context, subject to protocol signoff: constant 10,000-USDT cash;
  one hypothetical buy-and-hold purchase at inception's original 00:00 reference,
  using the same base costs/step and all subsequent shared marks. This contextual
  account must disclose its earlier entry/exposure than Ridge's first 01:00 trade.
  No counterfactual is silently added to the current engine or called observed.

No formal significance, independently confirmed alpha, tick-for-tick execution
parity or holdout performance is inferred. BTC/ETH are correlated. One retrospective
year with provider revision and availability limitations cannot establish general
profitability. Current-hour opens represent a fixed modelling assumption, not
proof of contemporaneous availability of a finalized archived candle.

## Intended immutable publication contract — future work

Stage 4B.2B must reserve a new exclusive directory, proposed
`artifacts/paper-historical/stage-4b2-base-v1/`, refusing every existing destination.
Never write into Stage 2/3 evidence directories. Publish the final manifest only
after all validations/reconciliations and deterministic reproduction succeed;
retain incomplete attempts as failures, without silently overwriting them.
No such directory or publisher is created by Stage 4B.2A.

Proposed authoritative files, fixed before execution:

- `policy.json`: full config, exact strategy/step/fee/precision, period/grids,
  timing/order/missingness/mark conventions, limitations and approved protocol hash.
- `source_evidence.json`: exact input paths and five pinned hashes, all 24 source
  identities/checksums/URLs/acquisition times, recipe provenance and row identities;
  no source forecast publication time fabricated from availability.
- `decisions.json`, `orders_trades.json`, `ledger.json`, `hourly_marks.json`:
  ordered per-market records, paired sequence-numbered postings and initial
  funding, original source references, full exact Decimal strings and UTC times.
- `summary.json`, `daily_monthly.csv`, `summary.md`: both market summaries and all
  defined observations with period completeness, denominators and limitations.
- `manifest.json`: schema/experiment version, `kind=historical_simulation`, full
  input identities, code SHA-256s (historical module plus all shared paper modules
  and pinned loaders), lockfile/runtime identity, Git revision and dirty-tree
  status, approved protocol and config hashes, market/time bounds, expected/actual
  row counts, status, output sizes/SHA-256s and exact reconciliation results.
  Record the manifest's own hash externally, not recursively inside itself.

All ordered scientific outputs must reproduce byte-for-byte from identical
approved inputs/code/policies. Run wall-clock/publishing metadata belongs in a
separate operational envelope if needed, not nondeterministic scientific payloads.
Exclusive creation protects against accidental overwrite, not coordinated local
source forgery or loss of backups. Persistence and publication are not implemented
or tested against real artifacts in 4B.2A.

## Fixed gates before Stage 4B.2B input access

Review the [engine guide](stage-04b2a-historical-replay-engine.md) and code; retain
passing synthetic tests for threshold/invalid numerics; UTC four-hour and hourly
grids; next-hour causality; continuous HOLD/full exit/new-only re-entry; explicit
miss/reset/discovery risk-off; full fee-aware sizing/off-step rejection; isolated
accounts; original reference identities; paired conservation, prefix marks and
ledger replay; deterministic JSON under changed Decimal contexts; full synthetic
year cutoff/open-position handling; and unchanged prospective regressions.

Require Ruff lint/format, the existing complete synthetic suite, whitespace checks
and protected source/protocol preservation checks. Skipped isolated PostgreSQL
fixtures are explicitly reported, never counted as passing integration evidence.
Do not open genuine artifacts merely to satisfy a loader integration test here.

Owner approval must resolve this draft, baseline step, reporting/benchmark
conventions, recipe-fingerprint canonicalisation and the future publication
contract **before** actual input inspection. Scenario expansion, real source-loader
integration and any optional liquidation calculation require their own reviewed
implementation/tests. Approving synthetic mechanics alone does not authorise
opening the 2024 predictions, executing the real replay, publishing economic
results, accessing the holdout or beginning prospective deployment.

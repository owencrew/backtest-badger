# Backtest Badger — Stage 4A Paper-Trading Technical Specification

**Status:** APPROVED — STAGE 4A TECHNICAL DESIGN; IMPLEMENTATION AND DEPLOYMENT REQUIRE SEPARATE AUTHORISATION  
**Specification version:** `stage-4a-v1`  
**Date:** 16 October 2026  
**Repository baseline:** `owencrew/backtest-badger`, GitHub `main` at `4bd5b8773fb420f87353616ec644a4f9e5f29425`  
**Companion:** [`stage-04a-prospective-evaluation-protocol.md`](stage-04a-prospective-evaluation-protocol.md)  
**Approval:** Product owner approved this Stage 4A design and its default policies on 16 October 2026. Approval authorises publication of these specification documents only; subsequent implementation tasks, commits and production activity retain their separate approval gates.

## 1. Purpose, boundaries and approval status

Build a **strategy-independent, spot-only, long/cash prospective paper-trading engine** consuming original, genuine Stage 3 forward-prediction artifacts. Orders and fills are **modelled**, never sent to Binance. Provide event-level auditability, exact financial accounting, conservative outage recovery, repeatable equity curves and honest comparisons to separately labelled historical experiments.

**Approved Stage 4A direction:** Ridge Sign v1 reference strategy; BTCUSDT and ETHUSDT in separate portfolios; 10,000 USDT initial funding **per portfolio per market**; continuous holdings; publicly observed prospective bid/ask; 10 bps fee per side; 2 bps adverse slippage; all-or-nothing simulated market fills; weighted-average cost basis; five PostgreSQL tables; append-only monetary ledger; persistent sticky exit obligations; versioned immutable valuation observations.

Not in scope: live-money API keys/orders, leverage, shorts, margin, borrowing, transfers, deposits after inception, partial fills, intra-order order-book simulation, generic brokerage frameworks, portfolio-optimisation research, production changes, or public website development.

### 1.1 Existing repository invariants

- `forward.py` creates immutable JSON records containing exactly four forecasts, source candles, feature and model fingerprints, actual `issued_at`, target boundaries and original publication identity.
- `forward_operations.py` permits timely **automated** forecasts only during `[source_close + 60 seconds, source_close + 16 minutes)` and logs missed horizons. Existing Stage 3 evidence and output never get rewritten.
- `forward_evaluation.py` evaluates the **future target** separately. Stage 4 must never read scored outcome files or future candles when deciding or filling orders.
- `forecast_data.py` and `backtest.py` implement **historical**, independently priced, three-hour round trips, not persistent long exposure. Reuse arithmetic/invariants where sound, not the existing `simulate_account()` lifecycle unchanged.
- The active PostgreSQL application schema has `market`, `candle`, `candle_revision`; Alembic's next new revision will be separate and locally tested.
- Production infrastructure currently has scheduled collection/scoring and backups. Its snapshot fingerprint currently covers the existing market-data tables and Alembic metadata, **not future paper tables**. GitHub HEAD is not verified as deployed.

### 1.2 Design priorities

1. Chronological integrity: no past-time decision, quote, fill or valuation invented after recovery.
2. Monetary integrity: reproducible balances, never negative USDT/assets, atomic fill and ledger postings.
3. Evidence integrity: original forecast hash, quotes and policy versions verifiable; immutable economic history.
4. Reliability: idempotent decisions/orders, sticky exit recovery, clear missing-data reporting.
5. Minimum complexity: plain Python functions, Psycopg and PostgreSQL; no message broker or event-framework abstraction.

## 2. Logical components and contracts

- **Forecast reader:** validates *original* retained Stage 3A/B JSON, filename/identity, checksum, timestamps and automation evidence. It does not fit models or read Stage 3C outcomes.
- **Strategy evaluator:** pure function accepting a verified, eligible forecast and current portfolio state; outputs desired long (1) or cash (0) plus provenance. Initial `ridge_sign` is one small versioned strategy, not a branching execution engine.
- **Decision/orchestration:** maintains expected 4h horizons, idempotency, outstanding exit priority, and current-time-only order intent.
- **Prospective quote adapter:** reads public Binance Spot best bid/ask and displayed best-level sizes, stamps actual UTC request/receipt times, retains exact response bytes/hashes, validates input and network freshness. No secret or private API access.
- **Execution/accounting core:** pure deterministic functions accepting order intent, observed quote, effective trading filters, balances and versioned fee/slippage policies; returns either a proposed full fill and paired currency movements or explicit rejection. No network or database dependency.
- **Persistence:** PostgreSQL transactions and constraints, event-level provenance and deterministic ledger replay.
- **Valuation/reporting:** captures contemporaneous immutable bid/ask marks and exact ledger high-water marks, then computes reproducible equity and statistics without querying future prices.

Implementation modules/interfaces will be fixed during Stage 4B.1 design review; no new generic strategy framework is required. Explicitly distinguish **signal target** (strategy) from **execution attempt** (simulation) from **financial state** (ledger).

## 3. Portfolios, strategy and versioning

### 3.1 Portfolio isolation

Create two initial funded experiments, one each for BTCUSDT and ETHUSDT, with independent **10,000 USDT** opening entries. No shared cash, internal transfers or correlated-risk allocation in v1. `portfolio_key` uniquely identifies `{market, strategy_id, strategy_version, inception_cohort}`. BTC and ETH accounts are separate experiments; aggregate nominal starting balances must not be presented as real investment.

Portfolio configuration is canonical JSON with SHA-256, immutable once activated, containing market identity, strategy, model recipe identifier, target weights, timing, execution, filters, monetary precision, valuation and missing-signal policy. A changed parameter requires a **new version and/or independent portfolio**, never silent retroactive modification. Preserve original code/protocol hashes, schema version, effective timestamp and source forecast references.

### 3.2 Ridge Sign v1 (engineering reference; not demonstrated alpha)

Input: exact retained `ridge` predicted 4h log return from a *timely automated* Stage 3B forecast. Convert from JSON decimal notation to `Decimal` without accidental binary-float threshold changes. Output `target=1` when `forecast > Decimal('1e-12')`, otherwise `target=0` (including negative and equality). No shorting, leverage, threshold optimisation or forced 4h liquidation. If already at desired state, record `HOLD`/`CASH_NOOP` without an order. Positive consecutive forecasts continue holding without churn. Strategy selection is based on an engineering reference, not evidence of economic viability; disclose that the 2024 validation results were already available when choosing Ridge.

Historical validation is a separate, fixed protocol, using the same strategy evaluator and accounting primitives but **not** pretending historical hourly opens were live bid/ask observations.

### 3.3 Priority and no re-entry during outstanding exit

An unresolved **exit obligation** has priority over every later forecast. A valid negative forecast while long, or a missing-signal safety rule while long, creates one immutable `EXIT_REQUIRED` decision. It remains sticky until a fully flat position is verified. A later positive forecast may be recorded as `IGNORED_EXIT_PENDING` but **cannot cancel the obligation or cause a buy**. On successful liquidation, append `EXIT_SATISFIED` evidence in the same transaction as the final sale and ledger postings. A new buy requires a **different, timely eligible forecast actually issued after the exit-satisfaction time**; a previously seen positive forecast is not reactivated.

If the account was already flat when a sell/risk-off decision occurs, persist `CASH_NOOP` (and any required terminal satisfaction event) without a modelled sale. If remaining base units cannot meet exchange-style filters, report `EXIT_BLOCKED_DUST`, retain the obligation, prohibit new buys and require a separately approved policy/administrative resolution; never silently delete the residual units.

## 4. Temporal rules and evidence availability

All recorded instants are timezone-aware UTC (`timestamptz`), with independently captured local clock values. A source 4h candle opening `t` closes at `t+4h`; feature availability is `t+4h+60s`; the Stage 3B timely automated publication deadline is `t+4h+16min` **exclusive**. The forecast targets the immediately following four-hour candle and is not the execution price.

- At time `decision_at`, the forecast must already exist, validate, be attributed to qualifying Stage 3B automation and satisfy `issued_at <= observed_by_worker_at <= decision_at < publication_deadline` for **new entries**. Receipt of a forecast after this deadline must not trigger a late purchase. Record it as missed/ineligible, with actual discovery time.
- For a timely negative forecast, persist its exit obligation while genuinely eligible; once created, the obligation can be acted on later at present-time quotes even after that forecast's horizon ends. Safety exits triggered by missing horizons are likewise current-time exit decisions, not backfilled forecast decisions.
- Record and commit order intent **before beginning the quote HTTP request**. `submitted_at <= request_started_at <= response_received_at <= fill_at` and `fill_at < order.expires_at`. `order.expires_at=submitted_at+30s` (fixed v1).
- Proposed quote validity: request-to-response latency at most **2 seconds** and response-to-fill elapsed time at most **1 second**; measured using monotonic duration where available, plus UTC audit stamps. Reject any sampled backwards UTC time. A client-observed low-latency REST response does **not** establish exchange-side quote age because bookTicker does not provide an exchange timestamp. Keep this limitation explicit.
- New buy fills must also complete **before** the corresponding forecast's timely deadline and target candle close. Persistent exits can execute beyond those times, but only at newly requested current quotations.
- An order has at most **one** successful fill. Every fresh quote attempt has its own identity; an attempted request is not proof of a fill. No recorded quote from a prior crashed process can be replayed as fresh execution evidence.
- No price is ever carried forward to a missed fill or historical valuation. Clock skew, suspended host, invalid response, query timeout or stale filters => no fill; reason is persisted.

### 4.1 Missing horizons and risk-off policy

At each expected 4h source-close cycle, accept only a validated qualifying timely automated forecast. After the 16-minute publication deadline, a missing/ineligible forecast is a **missed horizon**, detected and recorded **at the actual check time**, not falsely at the missed deadline. Two **consecutive** missed horizons constitute the approved v1 safety trigger, even if discovered upon recovery. A qualifying eligible forecast resets the missed-horizon streak. When safety condition is detected and the portfolio holds base units, create one `RISK_EXIT` decision **now**, and maintain its sticky obligation. When flat, stay in cash. An outage during which the system cannot check must not be represented as decisions taken in the past.

A single missing horizon: no new buy or model-derived sell; retain the current exposure but mark `SIGNAL_STALE`. Two consecutive misses: create `RISK_EXIT` if exposed. Missing signals do not count as negative Ridge forecasts. The exact expected-grid/account activation rules prevent counting periods before portfolio inception.

### 4.2 Exit and order state machine

Order state is `SUBMITTED` initially, then exactly one terminal `FILLED`, `REJECTED`, or `EXPIRED`. `SUBMITTED` holds a single outstanding request for one portfolio. A quote-observation event is not terminal and changes no financial balance. Terminal changes are coupled with an append-only market event. Order intent and all terminal transition audit data are immutable; `paper_order.status` is an updateable **projection** strictly mirroring the event history.

- On normal exit: create persistent exit decision and a `SELL_ALL` order. Validate current balance under a portfolio row lock; capture fresh quote; simulate all-or-nothing sell; atomically record fill and two postings. If base balance becomes exactly zero, record `EXIT_SATISFIED` atomically.
- On quote/network outage: record `QUOTE_FAILED` or `ORDER_REJECTED`, terminalise the attempt, **leave balances untouched**, and retain sticky exit. On every scheduled recovery opportunity, if the position remains nonzero, create the next `EXIT_RETRY` order with a new order ID, submit a **new** quote request and check current filters. No historical execution time or price is reused.
- On order expiry: append `ORDER_EXPIRED` and mark terminal; **do not cancel sticky exit**. Fresh exit attempts are allowed during later genuine checks. Maximum one active order per portfolio and at most one new exit attempt per worker cycle; no unbounded tight retry loop.
- On a crash after order commit but before response: recover the pending order, never fill using an absent/uncommitted quote. Prefer expire/terminalise the interrupted attempt and create a new prospective exit order; for a buy, do **not** retry an expired prior buy merely because it was once eligible. A buy can be attempted again only via a new eligible signal as defined by the fixed policy.
- On a crash after quote evidence but before fill commit: original quote persists as observation, but may **not** be reused by a restarted worker to claim a fill. Terminalise the unfilled attempt; exits keep their obligation, buys wait for a new timely signal.
- On a crash after fill/ledger commit: query state by deterministic order identity, verify paired postings and do not insert a second fill or post again.
- On competing workers: serialise per portfolio via `SELECT ... FOR UPDATE`, plus uniqueness constraints. A simultaneous process cannot open another `SUBMITTED` order, spend the same cash, or sell the same base units.

Explicit `EXIT_REQUIRED` and `EXIT_SATISFIED` records in decisions/events establish obligation lifecycle without a sixth table or manually editable boolean. An unresolved obligation is derived from a required exit decision lacking satisfaction evidence. If an exit was already satisfied, a subsequent negative signal in a flat account is a no-op.

## 5. Market quote, filter and execution assumptions

**Source:** Proposed public `GET /api/v3/ticker/bookTicker?symbol=BTCUSDT|ETHUSDT`. Record the exact UTF-8 response body (with size bound), SHA-256, HTTP endpoint, response status, locally measured request/receipt timestamps, elapsed duration and parsed bid/ask prices and best-level sizes. These are observed market data, **not exchange-acknowledged execution quotes**, and the response contains no exchange-side timestamp. Use no signed order endpoint or trading credentials.

A valid quote must have matching market/symbol, finite positive bid/ask, `ask >= bid`, finite nonnegative quantities, sufficient relevant-side best-level displayed quantity, response within timing limits, and source provenance. No cross-side liquidity substitution. Preserve both original bid/ask and adjusted simulated price. A documented liquidity caveat remains: displayed best-level quantity can change before actual execution, and a REST snapshot cannot establish fill certainty.

**Versioned assumptions:** `fee_bps=10` on each fill side, `adverse_slippage_bps=2`; observed bid/ask already embodies spread—**never add Stage 2C assumed half-spread to prospective quotes**. Modelled buy price = `ask*(1+0.0002)`; sell price = `bid*(1-0.0002)` before any conservative precision rounding. Fees are paid in USDT. Reject missing/unknown fee asset handling rather than silently assuming BNB discounts.

Capture relevant current `exchangeInfo` symbol filters, retained as versioned evidence/hash and acquired before the order, with a **proposed maximum 1h local age**. Validate market-quantity increments and min/max quantity under applicable `MARKET_LOT_SIZE`, `LOT_SIZE` where it applies, and minimum/maximum notional filters as they apply to market orders; reject if source filters are stale or unsupported. These checks **approximate** exchange admission rules; for actual market orders Binance may use a different reference price for notional checks, so modelled checks must not be described as exact exchange acceptance. Preserve price tick metadata for display and possible conservative model-price quantisation; no assumption that Binance market fills are actually quantised to a limit-order price tick is needed.

**All-or-nothing:** determine quantity from current available cash (buy) or currently owned base quantity (sell), then validate entire requested quantity against filters and displayed best-side liquidity. If insufficient, reject; do not manufacture partial fills or quietly downsize the target exposure because visible liquidity is low. A buy rounds affordable quantity **down to the active market quantity step**. A sell must respect the same step; any ineligible dust is an explicit blocked exit, not a zero balance.

### 5.1 Numerical policy

Use `Decimal`/PostgreSQL unrestricted `numeric`; reject NaN, infinities and negative amounts. No binary float for prices, quantities, costs, financial updates or position cost. Initial monetary policy proposal:

- USDT fee calculation: `ROUND_UP` to a **0.00000001 USDT** fee quantum, explicitly stored in config. (Simulation convention, not assertion of actual Binance fee settlement.)
- Retain unrounded observed prices as Decimal; modelled price may carry additional decimal digits from slippage. No unjustified price tick rounding for a simulated market fill.
- Quantity rounds down to applicable market step. For buys, compute a provisional affordable quantity and decrement by step if the **rounded-up fee** would exceed available cash.
- Gross notional and cash posting use exact Decimal product; fee rounding is the only additional monetary quantisation specified above. Reports may display fewer decimals but authoritative records must preserve full precision.
- Reject any order for which `cash_after<0`, `base_after<0`, min/max/step validation or conservation checks fail.

## 6. Proposed five-table PostgreSQL schema (logical column-level contract)

The following are the **approved conceptual columns and constraints**, to be translated by Codex into a reviewed Alembic migration only under separately authorised Stage 4C work. `uuid` is a deterministic generated identity where appropriate; `timestamptz` always aware UTC; `numeric` exact; hashes are 64 lowercase hex. Prefer enumerated `text CHECK` values over new PostgreSQL enum types. All economic event rows are append-only with database UPDATE/DELETE prohibitions; **only explicitly identified operational projections are mutable**.

### 6.1 `paper_portfolio` — authoritative identity/configuration, mutable operational projections

| Column | Type / rule |
|---|---|
| `portfolio_id` | UUID PK |
| `portfolio_key` | nonblank TEXT UNIQUE |
| `market_id` | FK `market.market_id`; BTCUSDT or ETHUSDT spot for v1 |
| `base_asset`, `quote_asset` | TEXT, consistent with market, quote `USDT` |
| `strategy_id`, `strategy_version`, `model_id` | TEXT, initially `ridge_sign`, `1`, `ridge` |
| `strategy_config` | JSONB complete canonical parameters; immutable after activation |
| `strategy_config_sha256`, `protocol_sha256`, `implementation_sha256` | hashes of frozen definitions/approved source; implementation SHA may be set at activation |
| `initial_cash` | NUMERIC > 0, exactly 10000 initially |
| `inception_at`, `created_at`, `activated_at` | TIMESTAMPTZ; activation no earlier than creation |
| `state` | `DRAFT`, `ACTIVE`, `PAUSED`, `CLOSED`; changes audited by market event |
| `ledger_highwater` | BIGINT >=0, cached committed per-portfolio sequence, updated atomically with ledger writes |

A portfolio is created and funded **once** with an `INITIAL_FUNDING` ledger entry; no arbitrary later deposits. Immutable configuration + distinct inception cohorts prevent illicit changing of an ongoing strategy. The mutable `state` and `ledger_highwater` are reconstructible/auditable projections, not a secondary source of financial truth.

### 6.2 `paper_decision` — immutable forecast decisions and prospective safety decisions

| Column | Type / rule |
|---|---|
| `decision_id` | UUID PK |
| `portfolio_id` | FK portfolio |
| `decision_key` | TEXT, UNIQUE per portfolio; deterministic idempotency key |
| `kind` | `FORECAST`, `MISSED_SIGNAL`, `RISK_EXIT` |
| `source_open_time`, `target_close_boundary` | TIMESTAMPTZ nullable only where not applicable; exact 4h identity |
| `forecast_record_id`, `prediction_id`, `artifact_relpath` | TEXT nullable for missing/risk decisions; safe relative path, no path traversal |
| `forecast_file_sha256`, `forecast_content_sha256` | hashes; nullable only without an original forecast |
| `forecast_issued_at`, `forecast_observed_at` | TIMESTAMPTZ; both before/equal `decided_at` |
| `model_forecast` | NUMERIC finite; null unless actual verified forecast |
| `target_exposure` | NUMERIC CHECK IN (0,1) or NULL for missing information |
| `decision_result` | e.g. `BUY_REQUIRED`, `EXIT_REQUIRED`, `HOLD`, `CASH_NOOP`, `IGNORED_EXIT_PENDING`, `SIGNAL_MISSED` |
| `is_exit_obligation` | BOOLEAN, true only for effective sell/risk-off decision while exposed |
| `missed_streak`, `reason_code` | integer/nonblank reason; snapshot state for safety audit |
| `strategy_config_sha256`, `decided_at`, `created_at` | pinned hash and actual timestamps |

Uniqueness: `(portfolio_id, decision_key)`, plus partial uniqueness of genuine `FORECAST` decision per `(portfolio_id,source_open_time)`; input must reference one original file and one `ridge` prediction. `MISSED_SIGNAL` rows may document old absent horizons **at the time discovered** (never claim their `decided_at` was the old deadline). `RISK_EXIT` uses a new actual-time decision with a stable trigger key. A duplicate does not alter source evidence or recompute a trade.

### 6.3 `paper_order` — immutable order intent plus audited mutable status projection

| Column | Type / rule |
|---|---|
| `order_id` | UUID PK |
| `portfolio_id`, `decision_id` | FKs; decision must belong to portfolio |
| `client_order_key` | deterministic TEXT UNIQUE per portfolio |
| `side` | `BUY` or `SELL` |
| `intent` | `SPEND_AVAILABLE_CASH` or `SELL_ALL_BASE` |
| `attempt_number` | INTEGER >=1, unique for decision and side |
| `budget_cash_snapshot`, `base_qty_snapshot` | NUMERIC >=0; order intent and upper limits observed before quote |
| `submitted_at`, `expires_at` | timestamps with `expires_at=submitted_at+30 seconds` policy |
| `status` | `SUBMITTED`, `FILLED`, `REJECTED`, `EXPIRED`; only legal status transitions, paired with terminal event |
| `policy_sha256`, `created_at` | versioned execution policy and actual creation time |

One active order **per portfolio**, enforced by partial unique index `UNIQUE(portfolio_id) WHERE status='SUBMITTED'`. Status transition from `SUBMITTED` to terminal is permitted once, under row lock, **in the same transaction** as the terminal `paper_market_event`; all other order fields immutable. An exit retry uses the original outstanding exit decision with a strictly increasing attempt number and fresh order ID. A buy does not restart from an expired old decision.

### 6.4 `paper_market_event` — immutable quote, fill, valuation and operational evidence

| Column | Type / rule |
|---|---|
| `event_id` | UUID PK |
| `portfolio_id` | FK portfolio |
| `order_id`, `decision_id` | nullable FKs, same portfolio as event |
| `event_type` | `QUOTE_OBSERVED`, `QUOTE_FAILED`, `FILL`, `ORDER_REJECTED`, `ORDER_EXPIRED`, `MARK_OBSERVED`, `MARK_MISSING`, `EXIT_SATISFIED`, `PAUSE`, `RESUME`, `RECOVERY_NOTE`, `EXIT_BLOCKED_DUST` |
| `event_at`, `recorded_at` | actual UTC occurrence/publication timestamps; nondecreasing within an event chain |
| `quote_event_id` | self-FK to earlier valid `QUOTE_OBSERVED`, required for `FILL` |
| `request_started_at`, `response_received_at`, `latency_ms` | nullable only for non-HTTP events; use monotonic duration check |
| `source_url`, `http_status`, `raw_body`, `raw_body_sha256` | bounded original quote evidence; secrets excluded |
| `bid_price`, `ask_price`, `bid_qty`, `ask_qty` | NUMERIC; required, finite and positive/nonnegative for valid quote/mark |
| `simulated_qty`, `simulated_price`, `gross_notional`, `fee_usdt` | NUMERIC; required only for `FILL` |
| `ledger_seq_before`, `ledger_seq_after` | required for `FILL`; exactly 2 increments; no financial movement for other types |
| `mark_slot`, `asof_ledger_seq`, `valuation_policy_sha256` | UTC scheduled slot and pinned portfolio state/policy, required for `MARK_OBSERVED`; `mark_slot` also required for `MARK_MISSING` |
| `filter_rules_json`, `filter_raw_sha256`, `filter_observed_at` | effective applicable symbol filters (JSONB), source response hash and actual capture time; required for `FILL` |
| `reference_event_id`, `reason_code`, `policy_sha256` | optional related event and versioned structured reason |

`MARK_OBSERVED` must retain observed bid/ask plus original raw quote and a portfolio ledger high-water snapshot, not merely a computed equity number. `MARK_MISSING` includes scheduled mark identity and actual failure time but **no invented market price**. Require unique `(portfolio_id,mark_slot,valuation_policy_sha256)` for scheduled marks; duplicate slot may not overwrite. A late observation cannot fill an earlier missing slot. Quote evidence may be retained in a `QUOTE_OBSERVED` row first; a fill references that exact event and cannot reference a `MARK_OBSERVED` event.

Unique partial indexes: **one `FILL` per order**, **one `FILL` per quote event**, **one `EXIT_SATISFIED` per exit decision**, **one terminal event per order**, and one market mark per portfolio/scheduled slot. Check type-specific nullability, matching market/portfolio, immutable original quote and policy identifiers, chronology and bounded payload sizes. `QUOTE_FAILED`, `ORDER_REJECTED`, `ORDER_EXPIRED`, missing marks and safety notes **must never** carry simulated fill quantities or point to ledger postings. An `EXIT_BLOCKED_DUST` observation accompanies an `ORDER_REJECTED` terminal event if an order already exists; it does not independently terminalise an order.

### 6.5 `paper_ledger_entry` — authoritative financial postings

| Column | Type / rule |
|---|---|
| `ledger_entry_id` | UUID PK |
| `portfolio_id` | FK portfolio |
| `ledger_seq` | BIGINT positive, unique `(portfolio_id,ledger_seq)`, serialised under portfolio lock |
| `entry_type` | `INITIAL_FUNDING` or `FILL` |
| `fill_event_id` | nullable FK `paper_market_event`; required for FILL, absent for funding |
| `asset` | `USDT` or this portfolio's base asset |
| `delta_units` | finite NUMERIC nonzero, signed |
| `posted_at` | timestamp tied to actual committed fill/funding event |

Exactly one opening `INITIAL_FUNDING` posting (+10,000 USDT) per portfolio, uniquely constrained. Each `FILL` has exactly two postings: USDT delta and base-asset delta. Unique `(fill_event_id,asset)` prohibits duplicate per-asset postings. No other posting type can alter a balance; no UPDATE/DELETE. These are paired multi-asset movements, **not** a same-currency double-entry ledger; cross-currency value conservation is checked using the fill price, not by requiring deltas to sum to zero.

### 6.6 Commit-level financial integrity — mandatory

A PostgreSQL transaction that successfully fills an order must, **atomically**:

1. Lock the portfolio and submitted order; ensure no existing successful fill and no unresolved consistency error.
2. Validate timely `QUOTE_OBSERVED`, filters, funds, holdings, matching policy hash and allowable all-or-nothing quantity.
3. Allocate the next two per-portfolio ledger sequences and insert one immutable `FILL` market event linking order and quote.
4. Insert the **two** correctly signed financial postings linked to that fill; update `paper_portfolio.ledger_highwater` to the second posting and `paper_order.status='FILLED'`.
5. If this sell leaves base balance **exactly zero** and a sticky exit is active, also insert `EXIT_SATISFIED` in that transaction.
6. Commit only if reconciliation and deferred PostgreSQL integrity checks pass; on any exception roll back **everything** and preserve no apparent success.

Required DB-enforced invariants (not just Python asserts): unique fill/order and fill/quote, per-portfolio FKs and same-portfolio checks, no orphan fill ledger entries, a **deferred constraint trigger** (or equivalent concrete audited PostgreSQL constraint design) that validates **exactly** the expected USDT and base postings for every `FILL` at commit, matching amount/fee/quantity and order `FILLED` status; reject a terminal order state without its matching terminal event. Postings to a non-FILL event must be rejected. The application must additionally recalculate balances under a lock and reject negatives. A deferred trigger should validate actual values, **not merely count two rows**. A funding invariant similarly ensures the exact once-only opening amount.

For a rejection or expiry, persist a terminal `paper_market_event` and update order status in **one transaction**, with **zero** ledger inserts and no `ledger_highwater` change. A quote may have been observed earlier and remain valid audit evidence despite a later rejected fill. A failed DB commit after a retained quote must be recorded as a subsequent no-financial-impact failure when possible; never fabricate a committed fill.

### 6.7 Reconciliation and replay

Portfolio cash and units are **always replayable** as `SUM(delta_units)` grouped by asset for all ledger entries through a selected `ledger_seq`. `ledger_highwater` is a checked projection, not authoritative balance. Replay must also reconstruct weighted-average cost basis and realised P&L from chronological fill events and the associated fee/quantity evidence. Reconciliation verifies nonnegative balances, chronological event sequence, exactly one funding entry, paired postings, order terminal status/event agreement and absence of an orphaned fill. Any mismatch => fail closed, pause economic operations and surface an explicit integrity incident.

## 7. Accounting and valuation definitions

Let `P_ref` be observed ask for a buy or bid for a sell; `s=0.0002`, `f=0.001`, units `q` rounded down to an eligible step.

- **Buy:** `P_exec=P_ask*(1+s)`; `N=q*P_exec`; `fee=ceil_to_quantum(N*f)`; `ΔUSDT=-(N+fee)`; `ΔBASE=+q`. Acquisition total cost basis increases by `N+fee`.
- **Sell:** `P_exec=P_bid*(1-s)`; `N=q*P_exec`; `fee=ceil_to_quantum(N*f)`; `ΔUSDT=N-fee`; `ΔBASE=-q`. Weighted-average cost before sale is `A=B/Q`; realised P&L increment = `N-fee-q*A`; remaining basis `B'=B-q*A` (force `B'=0` on an exact full liquidation, without an unexplained rounding writeoff).
- **After new buy:** `Q'=Q+q`, `B'=B+N+fee`; new average = `B'/Q'`. Buy has no realised P&L.
- **Unrealised P&L at mark:** `Q*bid_mark-B` (for one-asset portfolio). Marked equity = `cash + Q*bid_mark`; realised P&L + unrealised P&L = marked equity − initial capital, provided only initial funding and no later transfers.
- **Estimated net-liquidation equity:** `cash + [Q*bid_mark*(1-s) - ceil_to_quantum(Q*bid_mark*(1-s)*f)]` **only if** hypothetical liquidation of full Q would be eligible under the saved assumptions. If filters/dust make it ineligible, present liquidation estimate as `undefined`, not as zero.
- **Cumulative portfolio return:** `equity/10000 - 1`; no further contributions. Mark-to-market max drawdown is `max_t[(peak_t−equity_t)/peak_t]`, peak from initial equity and valid chronological observed marks; report mark coverage and gaps. Do not label this continuous-time or intrabar maximum drawdown.
- **Fees/spread/slippage:** store fee actually charged in the model and both unadjusted quote and execution price; report cost decomposition without double-counting bid/ask spread. When summarising against midpoint, observed half-spread and adverse slippage must be explicitly distinguished.

**Illustrative arithmetic (not a price prediction, and intentionally disregards real BTC market-level sizing):** start with 10,000 USDT; ask 100.00; buy 10 units at 100.02; fee 1.0002; cash = 8,998.7998; basis = 1,001.2002; weighted average = 100.12002/unit. Later bid 110.00, sell 4 units at 109.978; fee 0.439912; net proceeds 439.472088; basis released 400.48008; realised gain 38.992008. Remaining 6 units at marked bid 110: unrealised gain 59.27988, cash 9,438.271888, equity 10,098.271888. Reconciliation: 38.992008 + 59.27988 = 98.271888 = equity − 10,000. A numerical test of this example is mandatory.

## 8. Immutable valuation history without a sixth table

### 8.1 Valuation events and schedule

For v1, attempt **one scheduled mark every native 4h UTC boundary plus 10 minutes** (00:10, 04:10, 08:10, 12:10, 16:10, 20:10). Use a bounded **five-minute capture window** beginning at the slot time; if no valid current quote is recorded by its end, append `MARK_MISSING` when next running, at the actual detection timestamp. No retroactive mark using later prices. This scheduled mark is independent of whether Stage 3 successfully published a forecast or any trade occurred.

A valid `MARK_OBSERVED` event includes: immutable `mark_slot`, actual request/receipt and `marked_at` timestamps, raw bid/ask/size evidence and payload hash, selected bid, venue/symbol, valuation policy and implementation fingerprints, fee/slippage assumptions for optional liquidation estimate, and `asof_ledger_seq` selected **under the portfolio lock**. The mark's **recorded valuation time** is the actual persisted observation/snapshot time, not the scheduled slot label. Require the quote to remain within the approved freshness bound at `marked_at`. The lock captures a coherent ledger high-water; a fill committed before that boundary is included, a later fill is not.

`MARK_OBSERVED` is a retained evidence event, **not** an authoritative mutable equity balance. The equity curve is rebuilt by replaying ledger entries through `asof_ledger_seq` and marking their resulting holdings to this event's recorded bid, using the versioned policy. A pre-fill market quote and post-fill balance cannot be misrepresented as the earlier precise market snapshot: both quote receipt and ledger snapshot times must be displayed, with a bounded permitted interval. Quote publication without independently witnessed exchange-side time is explicitly disclosed.

### 8.2 Reproducibility invariant

A historical equity point **must never** be calculated from a current quote or a revised candle. Inputs to the reconstruction are (i) immutable ledger events up to the pinned sequence, (ii) exact original retained mark event, and (iii) pinned valuation code/policy. Reproduction on an isolated restored database must produce the same Decimal equity, unrealised P&L, drawdown sequence and evidence fingerprints, or explicitly fail due to missing evidence. Missing marks stay gaps. Do not interpolate or forward-fill and report interpolated values as observed.

For benchmarks, compare returns only on the **common valid mark schedule** where both price and account evidence exist; also show individual missingness and any exposure difference. Distinguish native scheduled slots from actual capture times; report maximum mismatches/timing differences.

## 9. Historical parity-validation design (Stage 4B.2)

The immutable 2024 validation forecasts (`forecast_data.py`) and independently acquired native hourly reference prices (`execution_data.py`) provide fixed evidence for causal strategy/accounting tests. The historical runner must call the **same Ridge Sign evaluator, sizing policy, weighted-average accounting primitives and long/cash transition logic** as Stage 4 prospective logic. For an eligible historical forecast available at `HH:01`, use the *next* hourly opening-reference timestamp (e.g., 12:01 → 13:00) for an entry/exit transition; maintain the resulting position across consecutive positive forecasts. No future hourly reference may influence an earlier decision. The original Stage 2C three-hour round-trip files remain **untouched and separately labelled**.

Historical execution reference: independent hourly opening price with predetermined **hypothetical** half-spread of 1 bp and adverse slippage 2 bps and 10 bps per-side fees, following Stage 2C's base convention; compare optional fixed stress/frictionless scenarios with no parameter search. Do not describe hourly references as prospective bid/ask observations, do not assert quote freshness, network latency, live depth or order-fill parity, and do not claim exact matching P&L across historical/prospective periods. The parity claim is **shared logical and financial mechanics**, not market-execution equivalence.

Because archived hourly opens have **no historical best-level bid/ask sizes or contemporaneous symbol-filter snapshots**, the historical adapter must use explicitly fixed synthetic depth/filter assumptions or report such constraints as untested; it must never describe a synthetic depth pass as actual exchange liquidity evidence. Historic validation should verify position-transition counts, no redundant buy/sell, complete asset/cash ledgers at each event, scenario-specific compounding, affordability, conservation, drawdown computed only from retained marks, and gap/invalid-horizon treatment. Retain input hashes and a new separate historical report; do not inspect the 2025–2026 untouched research holdout. Don't tune Ridge thresholds, missed-streak or costs after viewing results; implementation defect corrections require logged before/after differences.

## 10. Prospective scientific integrity and reporting

The companion **prospective evaluation protocol** is mandatory and should be frozen before the **first** paper order or market valuation is captured as part of the scored experiment. Paper trading begins only after a deliberate activation event and recorded UTC inception, not from historical existing predictions. No backdated portfolio creation, initial purchase, benchmark fill or missed-period reconstruction.

At minimum publish/retain: strategy/config and protocol version, forecast cohort, orders (including failures), immutable quote evidence, modelled fills, cash/base balances, fees and cost decomposition, timestamped marked equity, missing marks and delayed exits, exposure, turnover, realised/unrealised P&L, risk/drawdown and benchmark methodologies. Every page/API response must visibly distinguish historical backtests, genuine forward forecasting, prospective **simulated** trades, and any future actual real-money trades (not implemented).

## 11. Verification matrix / acceptance tests

**Stage 4A documentary gate:** approved complete specification and protocol, canonical policy/config, schema/constraint mapping, state transition table, numerical worked examples, test matrix, production safety gate and clear unresolved decisions; no code change implied.

**Stage 4B.1 pure-function tests (synthetic only):**

1. Threshold: `> 1e-12` long; equal/below cash; invalid/NaN inputs rejected.
2. Repeated positive forecasts keep one position without rebuy; negative generates exit; repeated negatives when flat are no-ops.
3. Sticky negative/risk-off exit suppresses later positive forecasts until flat; no re-entry using an already-seen forecast.
4. Missing horizon detection only after actual promptness cutoff; two consecutive misses produce one risk-off exit at actual detection time; valid eligible horizon resets streak.
5. Quote request precedes reception; order precedes request; fill follows response; future/stale/reversed clocks and expired buy deadline reject.
6. Quote bid/ask positivity/order, quantities, invalid symbol, malformed payload, size limit, HTTP failure, missing exchange timestamp limitation.
7. Buy adjusted from ask, sell adjusted from bid, 2 bps adverse slippage, 10 bps fee, no double-counted spread.
8. All-or-nothing best-level depth rejection, no partial synthetic fill, stale or unsupported symbol filters rejection.
9. Quantity step flooring, minimum/maximum sizes, price positivity, rounded-up fee affordability and insufficient funds.
10. Exact USDT/base movement; fee-included weighted-average acquisition; partial sale basis release; full sale resets basis; no negative balances.
11. Numeric hand-worked example above and fee-only flat-price loss; cumulative money reconciliation.
12. Deterministic replay under permutations that preserve causal order; reject reordered events or duplicate fills.
13. Missing quote must not generate equity/profit/fill; absent marks remain gaps.
14. One funding per portfolio; no cross-portfolio spending or market-price confusion.

**Stage 4B.2 historical tests:** frozen 2024 forecast/hash replay; next-hour entry policy; continuous holding; no target-label or withheld holdout access; base/stress cost sensitivity; old Stage 2C files byte unchanged; repeatable outputs; explicit non-parity disclosures.

**Stage 4C isolated PostgreSQL tests:**

15. Transactional insert of successful fill + exactly two postings and status; `ledger_highwater` matches.
16. Reject commit with fill missing either posting; wrong sign, quantity, fee, asset or order status; reject orphan posting.
17. Unique fill per order, per quote; unique initial funding; unique decision keys and terminal events.
18. Concurrent fill attempts via separate transactions yield one winner; no overspend or double sell.
19. Inject exceptions between each fill transaction step: full rollback, balances unchanged, no phantom fill.
20. Rejected/expired/network-failed attempt persists event/status but inserts **zero** financial postings.
21. Crash after submitted order, after quote observation, and after committed fill: recovery follows exact rules and never reuses an old quote.
22. Sticky exit retried using newly timestamped quote after interruption; old expired order remains terminal; re-entry blocked.
23. Attempted UPDATE/DELETE on immutable decision/event/ledger rows rejected, including direct SQL.
24. Mark persists raw quote/hash and ledger watermark; deterministic exact as-of equity reconstruction after subsequent trades and isolated restore.
25. Concurrent mark and trade produce coherent high-water sequence; stale mark or future quotation cannot rewrite prior point.
26. Missing scheduled mark is recorded as missing and is never retroactively marked with newer data.
27. Reconcile ledger with order/fill/events; tampering or missing artifact halts account and alerts.
28. Validate new migration upgrade and guarded downgrade on **disposable databases only**; do not run against production.

**Stage 4D/4E gated tests:** bounded read-only quote acquisition in isolation; observed latency/failure evidence; clock health, outage/missing-signal operations; explicit order-expiry tests; signed-off backup extension; restored database reproduces complete paper ledger and marks; staging rehearsal with workers isolated; report/API checks of portfolio independence, returns, fees, marks, gaps, reproducibility, benchmark labelling and read-only permissions.

## 12. Operational and production safety gates

Before deploying or activating Stage 4:

1. Product owner has approved this Stage 4A technical specification and prospective protocol; this does not itself authorise Stage 4B–4E implementation or production changes.
2. Codex implements bounded Stage 4B.1 then 4B.2, 4C, 4D, 4E with explicit review between stages; run Ruff, pytest and isolated PG integration tests and report results accurately.
3. Inspect actual Lightsail checkout SHA, worker scheduling and current DB migration version; GitHub main must not be assumed deployed.
4. Prepare and review new Alembic migration on disposable PostgreSQL; no production DB migration yet.
5. Expand consistent-snapshot backup/database fingerprints and weekly isolated restore drills to include **all five paper tables**, immutable trigger definitions, rows, ledger and marks. Preserve previous recovery process; verify a genuine isolated full restore with equal fingerprints and ledger/valuation replay before authorising production write activation.
6. Add independent systemd paper worker with service-specific scoped filesystem write paths, non-overlapping bounded cycles, logs, alerts and recovery behaviour; never change collection/scoring timers casually. Account for memory/CPU/resource contention with model-refitting collector and backup pauses.
7. Configure monitoring for missing marks, unresolved exit backlog, failed fills/quotes, DB consistency, unexpected timestamps and stale system clock. Review expected API call frequency, disk/S3 retention and AWS budget alerts; neither budgets nor timers guarantee success.
8. Require explicit, separate product-owner approval for deployment, migrations, worker activation, backup/retention changes and any destructive action. No real-money credentials or actual exchange order endpoint may be used.

## 13. Decisions resolved, implementation choices to verify, and version freeze

**Approved by product owner (16 October 2026):** Ridge Sign v1; two independent 10,000-USDT portfolios; long/cash persistent holdings; observed bid/ask; 10 bps fees and 2 bps adverse slippage; all-or-nothing fills; weighted-average cost; five tables with `paper_market_event`; sticky exit; financial atomicity; immutable quote/valuation evidence; historical logic parity but not execution-price parity.

**Approved Stage 4A defaults (verify mechanically before activation):** two consecutive missed horizons trigger safety exit; five-minute paper worker cadence; 30-second order expiry; 2-second quote RTT / 1-second processing freshness; 1-hour filter cache age; quote-size-cap policy; 1e-8 USDT fee rounding up; four-hour scheduled marks at +10 minutes within 5-minute window; stop/retry semantics for failed buy versus outstanding sell; above exact terminal types, constraints and temporal windows; restriction of accepted trade signals to qualifying timely automated Stage 3B records. Source REST endpoint reachability and real response characteristics remain a pre-deployment validation gate.

Approved source documents: `docs/stage-04a-paper-trading-spec.md` and `docs/stage-04a-prospective-evaluation-protocol.md`. Their exact SHA-256 content fingerprints must be recorded in a non-self-referential evidence manifest before activation. **Do not modify these frozen protocols after prospective results are seen; introduce a new version and new experiment instead.**

## 14. References (repository as reviewed)

- `AGENTS.md`, `README.md`, `docs/development-handoff.md`, `docs/architecture.md`, `docs/roadmap.md`.
- `docs/stage-02c-execution-backtesting.md`, `docs/stage-02d-economic-diagnostics.md`.
- `docs/stage-03a-forward-predictions.md`, `docs/stage-03b-automated-forward-collection.md`, `docs/stage-03c-forward-evaluation-protocol.md`, `docs/stage-03d-automated-outcome-scoring.md`.
- `docs/deployment/production-infrastructure.md`, `src/backtest_badger/{forward.py,forward_operations.py,forward_evaluation.py,forecast_data.py,backtest.py}`, `migrations/versions/0001_market_candles.py`.
- Binance Spot public API and symbol filters: <https://developers.binance.com/en/docs/products/spot/rest-api>, <https://github.com/binance/binance-spot-api-docs/blob/master/filters.md>. Endpoint and filters must be reverified before production activation.
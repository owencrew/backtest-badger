# Backtest Badger — Stage 4D.1: Prospective Forecast and Market-Data Integration

## Objective

Implement Stage 4D.1 of Backtest Badger: a verified, recovery-aware integration layer connecting genuine Stage 3 forward-prediction evidence, public Binance Spot market observations and the Stage 4C paper-trading persistence architecture.

The goal is to create a **safe, testable single-cycle dry-run worker** that can eventually become the prospective paper-trading engine.

This stage must establish that the platform can:

1. Authenticate original forward-prediction records and their automation provenance.
2. Distinguish eligible, ineligible, missing and stale forecasts.
3. Acquire and validate current public Binance bid/ask quotations.
4. Acquire and validate effective symbol trading filters.
5. Apply the approved Ridge Sign v1 policy.
6. Reconstruct and respect existing portfolio state and sticky exit obligations.
7. Plan simulated order attempts with correct timing and provenance.
8. Handle outages, expired intents, duplicate observations and process restarts.
9. Run deterministic dry-run scenarios without modifying production systems.

**No prospective paper trading is to be activated during Stage 4D.1.**

The approved economic rules must remain unchanged. Implementation should prioritise correctness, traceability and maintainability over adding functionality beyond this stage.

---

## 1. Repository and starting context

Repository:

`~/Code/backtest-badger`

GitHub:

`owencrew/backtest-badger`

Expected latest implementation commit:

`6ddaf54631b163f29812f44897be7188ec31b271`

Commit message:

`feat(paper): implement durable paper trading persistence`

Verify current Git HEAD, working-tree cleanliness and GitHub CI status before editing.

If HEAD has advanced, inspect those changes rather than resetting the repository.

Read the repository instructions and current handoff:

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`

### Approved specifications

Read completely:

- `docs/stage-04a-paper-trading-spec.md`
- `docs/stage-04a-prospective-evaluation-protocol.md`
- `docs/stage-04b1-deterministic-paper-primitives.md`
- `docs/stage-04c-paper-trading-persistence.md`

These define the approved scientific, accounting and operational contracts.

### Existing implementation

Inspect:

- `src/backtest_badger/forward.py`
- `src/backtest_badger/forward_operations.py`
- `src/backtest_badger/forward_evaluation.py`
- `src/backtest_badger/forward_scoring_operations.py`
- `src/backtest_badger/paper_types.py`
- `src/backtest_badger/paper_strategy.py`
- `src/backtest_badger/paper_execution.py`
- `src/backtest_badger/paper_accounting.py`
- `src/backtest_badger/paper_records.py`
- `src/backtest_badger/paper_persistence.py`
- `src/backtest_badger/paper_reconciliation.py`

Also inspect existing forward, paper-primitives and PostgreSQL integration tests.

The existing public website and forward feed must remain unaffected.

---

## 2. Stage boundaries

Stage 4D has been divided into three milestones:

**4D.1 — Integration and dry-run worker**

This task. Implement authentic evidence adapters, clock validation, bounded public market-data clients and recovery-aware orchestration. Validate locally.

**4D.2 — Production readiness and isolated operational rehearsal**

Later. Least-privilege database roles, resource benchmarks, production migration planning, backup/restore coverage, staged worker installation and monitoring.

**4D.3 — Controlled prospective activation**

Later, requiring separate owner approval. Initialise genuinely observed BTC/ETH simulated portfolios and begin their prospective economic histories.

Do not undertake 4D.2 or 4D.3 within this task.

---

## 3. Authentic forward-prediction reader

Build a narrowly scoped adapter that reads **original Stage 3 forward-prediction records**.

Suggested module:

`src/backtest_badger/paper_forward_adapter.py`

Reuse the existing Stage 3 validation and cohort classification implementations wherever possible.

In particular, inspect:

- `forward_evaluation.load_prediction`
- `forward_evaluation.parse_journal`
- `forward_evaluation.journals`
- `forward_evaluation.matches_automation`
- `forward_evaluation.classify`
- `forward_evaluation.validate_cohort`

Do not implement an independent, weaker forecast-authentication system.

### Required verification

For every candidate forecast, verify:

- Original file bytes and SHA-256.
- Content checksum.
- JSON structure and exact record identity.
- Filename and market identity.
- Source four-hour candle boundaries.
- Actual original issuance time.
- Model recipe and prediction provenance.
- Original Ridge prediction identity and value.
- Associated automated collection journal.
- Journal source hash and original timestamps.
- Evidence that the record belongs to a qualifying automated cohort.
- Exact deadline and eligibility.

Use original timestamps. Never replace them with current read time.

Use a separate `observed_by_worker_at` timestamp indicating when this new worker actually discovered the evidence.

### Eligibility

Only the approved `primary_timely_automated` source cohort may authorise a prospective Ridge trading decision.

The paper domain currently represents this internally as `primary_timely_automated`; preserve the mapping to the existing Stage 3 classification.

A timely-looking record without genuine automated provenance is not eligible.

Late manual records are not eligible.

The original source closing time is not the actual issuance time.

The target candle's future outcome is not an input to the strategy.

### Timing

For a native four-hour source candle opening at `t`:

- Source closes at `t + 4h`.
- Forecast becomes eligible at source close +60 seconds.
- Timely publication deadline is source close +16 minutes, exclusive.
- Original issuance, worker observation and decision must satisfy the approved temporal ordering.
- A new buy must finish before the eligible deadline and target boundary.

A late-discovered positive forecast must not trigger a purchase.

A valid negative forecast may create a persistent exit obligation while eligible. Once created, that obligation can survive the original deadline.

Do not fabricate a past-time decision based on a record discovered after its eligibility window.

### Exact values

Convert the Ridge forecast to Decimal without an accidental float threshold change during the adapter conversion.

Preserve the already-recorded scientific value; do not claim to recover precision that was absent in the original JSON number.

Ridge targets LONG only when:

`prediction > Decimal('1e-12')`

Equality or a smaller value targets CASH.

Do not retrain Ridge, change its threshold or select another model.

### Security

Treat original artifacts as untrusted files until validated.

Reject:

- Invalid checksums
- Duplicate JSON keys
- Unsafe relative paths
- Unexpected symlinks/path escapes
- Wrong source market
- Reused prediction identities
- Invalid model recipe
- Corrupted journals
- Contradictory automation evidence
- Unrecognised source schema
- Clock reversals
- Invalid numerical values

Fail closed with useful structured errors.

Do not silently downgrade an unverifiable forecast into a valid automated observation.

---

## 4. Public Binance market-data adapter

Create a separate market-data module.

Suggested location:

`src/backtest_badger/paper_market_data.py`

Support only:

- Binance Spot BTCUSDT
- Binance Spot ETHUSDT

No other symbols in v1.

### Public endpoints

Use the documented public Binance Spot interfaces:

**Best bid/ask:**

`GET /api/v3/ticker/bookTicker?symbol=BTCUSDT`

or ETHUSDT.

**Symbol filters:**

`GET /api/v3/exchangeInfo?symbol=BTCUSDT`

or ETHUSDT.

**Optional clock diagnostic:**

`GET /api/v3/time`

Use an official Binance public market-data host, preferably `https://data-api.binance.vision` where supported.

Consult the current official Binance Spot API documentation before implementation.

Do not use trading, account, wallet, order submission or signed API endpoints.

Do not create or request Binance API credentials.

### Quote evidence

For every acquired quote, retain:

- Original raw response bytes, subject to the existing 4,096-byte quote bound.
- Exact SHA-256.
- Original request URL.
- HTTP status.
- Symbol.
- Bid price.
- Ask price.
- Bid quantity.
- Ask quantity.
- Request start time.
- Response receipt time.
- Monotonic elapsed duration.
- Fresh process-run identity.

Use strict Decimal parsing.

Reject duplicate or unexpected fields where they invalidate the approved quote contract.

Validate the result using the existing `Quote` type and `validate_quote` logic.

### Timing limits

Preserve the Stage 4A defaults:

- Maximum request-to-response latency: 2 seconds.
- Maximum response-to-fill age: 1 second.
- Maximum submitted order lifetime: 30 seconds.

A stale quote must not produce a simulated fill.

Important: Binance `bookTicker` does not establish an exchange-side timestamp for the quote under this contract.

Client-observed response latency is not proof that a quoted price was executable at the exchange.

Keep this limitation explicit.

### Failure handling

Handle:

- Connection failure
- DNS error
- Read timeout
- HTTP 4xx/5xx
- Binance 429 rate limiting
- Binance 418 temporary ban
- Invalid JSON
- Unexpected symbol
- Oversized payload
- Invalid bid/ask
- Invalid depth
- Clock reversal
- Stale response

Never substitute the previous successful quote for a missing current quote.

Do not introduce an unbounded retry loop.

For 418/429, stop rather than repeatedly hammering the provider. Preserve a structured failure and any relevant bounded retry information without logging sensitive data.

---

## 5. Exchange-filter adapter

The approved prospective strategy requires effective market-order quantity and notional constraints.

Parse Binance `exchangeInfo` evidence into the existing:

`paper_types.Filters`

Support the applicable market-order rules, including:

- `MARKET_LOT_SIZE`
- `LOT_SIZE` where applicable
- `MIN_NOTIONAL`
- `NOTIONAL`
- Quantity step
- Minimum and maximum quantity
- Applicable minimum/maximum notional

Respect flags controlling whether notional limits apply to market orders.

Do not assume that a zero-valued/disabled rule is an active restriction.

Do not silently substitute arbitrary limits for missing source fields.

Where two applicable constraints interact, calculate a conservative effective intersection.

### Filter policy

The current Stage 4A v1 contract allows a maximum local filter age of one hour.

Retain:

- Original source identity
- Source response SHA-256
- Observation time
- Relevant original filter fields
- Effective interpreted constraints
- Version identifier

The effective filter object must correspond to the same market as the quote and portfolio.

A stale or unsupported filter must cause a rejected hypothetical attempt, not permissive sizing.

If Binance has introduced a rule incompatible with the approved v1 filter representation, report it explicitly and fail closed for the affected market.

Do not silently change the financial strategy or treat unsupported exchange rules as validated.

Do not claim that checking public symbol filters guarantees actual Binance market-order acceptance.

### Evidence size

The original `exchangeInfo` response may differ in size from `bookTicker`.

Use a separately documented bounded source-response limit suitable for symbol-specific filter responses.

Do not force the complete `exchangeInfo` body into the paper quote's existing 4,096-byte field.

Preserve original filter evidence privately with a hash and provide the necessary verified effective values to the approved persistence contract.

Do not commit live response archives unnecessarily.

---

## 6. Clock and process identity

Create a small, testable clock utility if existing helpers do not suffice.

Suggested location:

`src/backtest_badger/paper_clock.py`

Requirements:

- UTC-aware timestamps only.
- Reject naive or non-UTC timestamps.
- Independent monotonic duration measurement for HTTP calls.
- Detect backwards timestamps.
- Detect inconsistent supplied wall/monotonic observations.
- Reject negative elapsed durations.
- Capture actual observation/discovery times.
- Generate a unique process-run identity for each worker invocation.
- Never reuse a prior process-run identity after restart.

Support explicit clock injection for deterministic tests.

A Binance server-time diagnostic may identify suspicious offset but does not by itself prove the host is correctly synchronised.

Do not introduce a new automatic clock-skew threshold without documenting and obtaining approval for any material policy change.

Clock uncertainty that could invalidate the approved trading deadlines must fail closed.

---

## 7. Dry-run orchestration

Implement a **single-cycle, recovery-aware orchestrator**.

Suggested module:

`src/backtest_badger/paper_worker.py`

Use a clearly separated orchestrator and side-effect adapters.

Do not build a generic trading framework.

The worker should be designed around a future five-minute schedule, but this stage must not install or activate that schedule.

### Input responsibilities

The orchestrator receives:

- Verified forward-evidence reader
- Current clock
- Market-data adapter
- Effective filter adapter
- Portfolio-state reader
- Existing strategy/execution primitives
- Unique process-run identity
- Dry-run output sink

Production persistence is not a write target for this stage.

### State and strategy

Reuse:

- `paper_strategy`
- `paper_execution`
- `paper_accounting`
- `paper_reconciliation`

For recovery-state tests, use Stage 4C against disposable PostgreSQL databases containing fabricated evidence.

Do not create actual production paper portfolios.

### Planned transitions

The orchestrator must correctly distinguish:

- Eligible positive Ridge forecast while flat
- Eligible positive forecast while long
- Eligible nonpositive forecast while long
- Eligible nonpositive forecast while flat
- Ineligible or late forecast
- Missing expected horizon
- One missed horizon
- Two consecutive missed horizons
- Unresolved exit obligation
- Rejected or expired order
- Stale quote
- Unsupported symbol filters
- Missing scheduled valuation
- Previously completed operation
- Recoverable interrupted operation
- Integrity incident requiring pause

Do not collapse these states into a generic `TRADE` or `NO_TRADE` result.

### Sticky exits

An existing unresolved exit obligation overrides later positive forecasts.

It survives:

- Quote failures
- Rejections
- Order expiry
- Worker restart
- Later positive predictions

The future worker may retry an exit only with a new order attempt and fresh current-time quotation.

The approved cadence permits at most one new exit retry per five-minute cycle.

No expired quote may be reused.

Do not permit re-entry based on a forecast issued before the exit was satisfied.

Blocked-dust conditions remain paused pending explicit resolution.

### Missed horizons

Use the expected four-hour source grid.

A missing horizon must only be declared after its publication deadline.

Record its actual discovery time.

Do not invent a decision at the historical deadline.

Two consecutive missing horizons trigger the approved risk-off behaviour if there is an open position.

An eligible automated forecast resets the missed streak according to Stage 4A.

Do not treat a missing forecast as an actual negative prediction.

### Valuation scheduling

Prepare for the existing four-hour mark schedule:

- 00:10 UTC
- 04:10 UTC
- 08:10 UTC
- 12:10 UTC
- 16:10 UTC
- 20:10 UTC

Preserve the five-minute capture window.

A mark should use a freshly observed bid and the coherent ledger prefix at observation time.

A missing mark is an explicit gap.

Stage 4D.1 should validate schedule selection and planning, not persist genuine prospective valuation results.

### Important dry-run distinction

Implement the dry-run mode so that it produces **a proposed action and structured reasoning**, not actual financial events.

For example, a fabricated scenario may report:

- Forecast eligible
- Current position flat
- Proposed action BUY_REQUIRED
- Hypothetical order submission required
- Fresh quote required after order submission
- Portfolio unchanged
- No order submitted
- No fill recorded

A dry-run must never falsely label an independently fetched quote as a fill.

For a live read-only observation, do not reconstruct or claim a hypothetical executed trade from a quote obtained before a committed order intent.

---

## 8. Explicit dry-run modes

Provide two distinct modes.

### A. Deterministic fixture dry-run

This is the default.

Uses fabricated:

- Forward records and journals
- Quotes and symbol filters
- Portfolio states
- Timestamps
- Network failures
- Restarts and interruptions

It must be suitable for CI.

No external network calls.

No production database calls.

No real economic activity.

This mode may use disposable PostgreSQL revision `0002` databases where persistence integration is necessary to validate recovery.

Use the same immutable evidence and reconciliation contracts as the future service.

### B. Bounded read-only market-data smoke test

Implement as a separate explicit opt-in CLI action.

This request permits **a one-shot local public-market-data feasibility test** using the two allowed Binance Spot markets.

Limit the test to:

- At most one `bookTicker` request per market.
- At most one symbol-specific `exchangeInfo` request per market.
- At most one optional server-time request.
- No automatic retries.
- No recurring polling.
- No connection to private account APIs.
- No orders.
- No paper-portfolio writes.
- No production infrastructure access.

Report only:

- Reachability
- HTTP status
- Source validation
- Timestamp and latency observations
- Filter interpretation status
- Availability of the required fields
- Any contract incompatibilities

Do not present market-price snapshots as trades, portfolio results or prospective strategy observations.

If public market-data access is unavailable or blocked, report the failure without relaxing validation or substituting an unverified provider.

Any genuine forward-artifact inspection must likewise be read-only and must never create a trading history.

---

## 9. CLI and operational safety

Add a small local command interface following the existing project conventions.

Prefer explicit commands such as:

`paper dry-run`

`paper market-smoke`

These are illustrative names; inspect the current CLI before selecting final syntax.

Requirements:

- Dry-run mode is the default for new Stage 4D.1 commands.
- Real network access requires an explicit opt-in command or flag.
- No default database write path.
- No automatic production configuration discovery.
- No permission to create/fund/activate actual portfolios.
- No installation of systemd services.
- No cron or timers.
- No background daemon.
- No Cloudflare or R2 interaction.
- No exchange authentication.
- No order endpoints.

Never create a command that looks like a legitimate prospective worker but silently begins economic execution.

The final handoff must explain exactly which commands are safe and which future capabilities remain unimplemented.

---

## 10. Security and evidence requirements

The market-facing adapters must operate safely with untrusted input.

Use:

- Fixed allowed symbols.
- Fixed official HTTPS host allowlist.
- No user-controlled arbitrary network destinations.
- Strict URL construction.
- Bounded connection/read timeouts.
- Bounded response sizes.
- Strict JSON parsing.
- Correct SHA-256 over original bytes.
- Parameterised database queries where used.
- Safe local paths.
- No credential exposure.
- No logging of sensitive environment values.
- No uncontrolled retries.
- No execution after an integrity failure.

Do not redirect HTTP requests to arbitrary hosts.

If a required original artifact is unavailable, return a structured unavailable/error state.

Do not invent the missing source.

The public Binance REST quote has no guaranteed exchange-side execution timestamp under this design.

Keep quote evidence separate from simulated fill evidence.

---

## 11. Tests

Implement comprehensive tests for the new adapters and orchestration.

Suggested files:

- `tests/test_paper_forward_adapter.py`
- `tests/test_paper_market_data.py`
- `tests/test_paper_clock.py`
- `tests/test_paper_worker.py`
- `tests/integration/test_paper_worker.py`

Use the existing test infrastructure and naming conventions.

### Forecast authentication

Test:

- Valid original-format automated forecast
- Valid but late manual forecast
- Timely but unattributed forecast
- Wrong market
- Wrong Ridge model
- Invalid prediction
- Altered file bytes
- Valid content hash but conflicting file hash
- Invalid journal
- Journal mismatch
- Missing original journal
- Missing or extra predictions
- Incorrect four-hour boundary
- Future outcome not accessed
- Duplicate horizon
- Forecast discovered after deadline
- Timestamp reversal
- Corrupted model recipe
- Missing evidence paths

### Market-data parsing

Test:

- Valid BTC/ETH best bid/ask
- Invalid symbol
- Negative/zero prices
- Ask below bid
- Zero displayed liquidity
- Missing quantity
- Nonfinite Decimal
- Duplicate JSON fields
- Oversized response
- HTTP error
- Timeout
- 429/418
- Malformed body
- Stale quote
- Incorrect original SHA-256
- Clock inconsistency

### Filters

Test:

- MARKET_LOT_SIZE
- LOT_SIZE applicability
- NOTIONAL
- MIN_NOTIONAL
- Market applicability flags
- Enabled/disabled constraints
- Correct effective intersection
- Invalid step
- Incompatible quantity increments
- Minimum and maximum notional
- Stale filter snapshot
- Unsupported filter type where economically material
- Incorrect source identity
- Corrupted original evidence hash

### Orchestration and recovery

Test:

- Positive forecast while flat
- Repeated positive forecast while long
- Negative forecast while long
- Negative forecast while flat
- Sticky exit suppresses new buy
- Exit rejection followed by new eligible attempt
- Expired order not backfilled
- Restart requires a fresh process identity
- Old quote cannot become a later fill
- Crash after submitted order
- Crash after quote receipt
- Recovery after committed fill
- One missed horizon
- Two missed horizons
- Recovery after prolonged outage
- No backdated decisions
- No phantom trades
- Idempotent cycle planning
- Duplicated input evidence
- Inconsistent saved state
- Unresolved blocked dust
- Valuation window eligibility
- Explicit missing mark
- Clock skew detection
- Invalid future forecast
- No cross-market funding or holdings

### Important dry-run assertions

All fixture dry-run tests must explicitly verify that:

- No actual order is submitted.
- No production portfolio is funded.
- No genuine economic ledger is written.
- No background worker is activated.
- The original live forecasts/outcomes remain unchanged.
- Current market observations are not reclassified as historical fills.
- Any simulated economic changes occur only in disposable, explicitly fabricated test contexts.

### PostgreSQL integration

Run the applicable Stage 4C integration tests on disposable PostgreSQL 17 databases.

Exercise recovery snapshots and state reconstruction using fabricated evidence.

Do not connect these tests to production.

The real database integration must not be bypassed by a fake persistence implementation when testing recovery behaviour.

---

## 12. Verification

Run relevant checks, including:

- Ruff lint
- Ruff formatting
- Full applicable pytest suite
- Stage 4B.1 pure primitives regressions
- Stage 4C persistence and PostgreSQL tests
- Existing Stage 3 forecast and evaluation regressions
- Existing protected historical research tests
- Wheel/package build
- Git diff whitespace checks

Use the repository's existing isolated runner requirements for guarded historical tests.

On macOS, follow the Stage 4C handoff's private scratch-directory guidance to avoid the previously encountered pytest fixture ownership conflict.

Do not mistake an environment-related skipped test for a passing test.

Verify original Study 001 and Study 002 scientific evidence remains unchanged.

No genuine historical economic rerun is needed.

### Acceptance demonstration

Produce a deterministic fixture demonstration showing the complete decision lifecycle:

1. Verified positive Ridge record.
2. Flat portfolio.
3. BUY_REQUIRED.
4. Simulated submitted intent.
5. Synthetic quote and filters.
6. A successful simulated fill in a disposable test database.
7. Portfolio recovery with correct balances.
8. A subsequent negative signal.
9. Sticky exit.
10. Failed exit quote.
11. Restart and new exit attempt.
12. Successful final liquidation.
13. Correct final reconciliation.

Clearly label this as a fabricated demonstration, not prospective paper-trading activity.

Also demonstrate an interrupted order and a missing valuation without manufacturing a financial event.

Document exact test evidence and deterministic fixture identities.

---

## 13. Production boundaries

Do not:

- Connect to the Lightsail production database.
- Apply migration 0002 to production.
- Create or fund live paper portfolios.
- Activate the first genuine paper experiment.
- Install systemd paper services or timers.
- Add production environment variables.
- Modify backup/restore schedules.
- Modify production database roles.
- Change live Stage 3 collectors or scorers.
- Change R2 feeds or objects.
- Modify the website or Cloudflare configuration.
- Alter the existing forecast models.
- Retrain or regenerate genuine Ridge records.
- Rewrite original forward evidence.
- Use future target outcomes in trading decisions.
- Read the historical held-out labels to select strategy rules.
- Place actual Binance orders.
- Generate Binance trading API credentials.
- Implement real-money trading.
- Change the approved Stage 4A economics.
- Deploy a worker into production.

This stage may inspect existing authenticated evidence read-only and perform the specifically bounded public market-data smoke test.

All trading/accounting tests must use fabricated evidence and disposable databases.

---

## 14. Documentation and handoff

Create:

`docs/stage-04d1-prospective-integration.md`

Include:

1. Starting Git SHA.
2. Scientific and operational scope.
3. Authentic forecast-adapter design.
4. Automation-provenance validation.
5. Quote acquisition contract.
6. Exchange-filter acquisition and interpretation.
7. Original evidence identities.
8. Clock and freshness rules.
9. Process-run identity.
10. Dry-run orchestration architecture.
11. State transition and recovery matrix.
12. Interaction with Stage 4C persistence.
13. Exactly what dry-run does and does not persist.
14. Synthetic tests and PostgreSQL results.
15. Bounded read-only market-data observations, if executed.
16. Evidence of failure handling.
17. Resource and latency measurements.
18. Security limitations.
19. Full changed-file inventory.
20. Stage 4D.2 prerequisites.

Update where relevant:

- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- `prompts/README.md`

Archive this full prompt at:

`prompts/stage-04-paper/stage-04d1-prospective-integration.md`

Do not change the frozen Stage 4A protocol or completed Stage 4C evidence.

---

## 15. GitHub workflow

This request authorises:

- Local implementation
- Synthetic testing
- Disposable PostgreSQL testing
- The specifically bounded read-only public market-data check
- Documentation
- Commit and push of the verified implementation

After successful validation:

1. Review all changed files.
2. Confirm no private artifacts, keys or database dumps are included.
3. Confirm the original scientific evidence remains untouched.
4. Run all applicable checks.
5. Commit the focused implementation.
6. Push to main.
7. Verify both GitHub workflows pass for the exact final SHA.

Suggested commit:

`feat(paper): add prospective integration dry run`

Do not commit a false completion claim if critical acceptance tests are blocked.

If a material incompatibility is found between Stage 4A, the Stage 4C schema and current Binance filter behaviour, document the conflict and stop that affected path rather than silently changing the protocol.

The current Cloudflare candidate-only build workflow may run because of a GitHub push. Do not promote any candidate, change build variables or initiate a separate deployment.

---

## 16. Final completion report

Provide:

### Implementation

- Starting and final Git SHAs.
- New modules and interfaces.
- Forecast validation strategy.
- How Stage 3 original evidence is authenticated.
- Quote/filter validation approach.
- Clock and run-identity behaviour.
- Dry-run orchestration and recovery design.
- Reuse of Stage 4B.1 and Stage 4C.

### Testing

- Unit-test counts.
- PostgreSQL integration results.
- Synthetic lifecycle demonstration results.
- Fault-injection/recovery results.
- Read-only Binance smoke-test results, if performed.
- Regression-test totals.
- Lint, formatting and build results.
- Exact-commit GitHub CI results.

### Safety

- Confirmation no live paper portfolios exist because of this work.
- Confirmation no production DB writes were performed.
- Confirmation no worker was scheduled or activated.
- Confirmation no actual exchange orders were placed.
- Confirmation original forecasts and existing research are unchanged.
- Confirmation the website and forward feeds are unaffected.

### Next stage

Provide a focused Stage 4D.2 handoff covering:

1. Benchmarking full portfolio reconciliation under locks.
2. Least-privilege PostgreSQL roles.
3. Production migration and rollback/forward-recovery planning.
4. Backup coverage and isolated restoration of all five paper tables.
5. Preservation of original quote/filter/forecast artifacts.
6. Worker process isolation and resource limits.
7. Clock and source health monitoring.
8. Alerting and recovery procedures.
9. Safe staging rehearsal.
10. Explicit approvals needed before any prospective activation.

---

## Definition of success

Stage 4D.1 succeeds when:

- Original forward predictions are authenticated correctly.
- Only genuinely eligible automated forecasts can inform proposed trading decisions.
- Public Binance quote and filter evidence is parsed and validated reliably.
- The worker distinguishes observation, decision, order, quote and fill.
- The approved chronological and monetary policies remain unchanged.
- Crash recovery and sticky exits are handled correctly in synthetic integration scenarios.
- A deterministic single-cycle dry-run can explain what would happen without creating genuine financial history.
- Tests and CI pass.
- No production system or paper portfolio is activated.

**The desired outcome is a proven integration layer, not yet a running prospective trading system.**

Stop after implementation, validation, commit/push and the Stage 4D.2 handoff.
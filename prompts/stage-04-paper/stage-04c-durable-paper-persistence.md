# Backtest Badger — Stage 4C: Durable Paper-Trading Persistence and Transactional Integrity

## Objective

Implement Stage 4C of Backtest Badger: a production-quality, locally verified PostgreSQL persistence layer for future prospective paper trading.

The system already includes deterministic paper-trading primitives, historical replay, authentic forward forecasts and an approved prospective paper-trading specification.

This stage must connect the existing paper-trading primitives to persistent, transactional database storage.

The objective is not to start trading, launch a background service or publish paper portfolios.

It is to create a reliable foundation on which later prospective paper trading can operate.

**Central requirement: every simulated financial event must be durable, exactly accounted for, recoverable and independently auditable.**

A successful simulated fill must commit with exactly its two corresponding monetary postings and terminal order evidence in one PostgreSQL transaction.

A failed transaction must leave no partial financial state.

Crashes, duplicate requests and concurrent workers must not create duplicate fills, duplicate funding, negative balances or falsely completed exit obligations.

The implementation should be simple, maintainable Python and SQL, with rigorous integration tests.

This stage covers local development, isolated PostgreSQL testing, documentation, commit and push.

It does not authorise production database migrations or prospective trading activation.

---

## 1. Repository and starting state

Repository:

`~/Code/backtest-badger`

GitHub:

`owencrew/backtest-badger`

The latest known commit is:

`26c5827c2ae0bd0342484380d678e1fa61c6e1e3`

`feat(web): publish study 002 in the dig`

Both CI workflows passed for that revision.

The owner has subsequently manually promoted Study 002 on Cloudflare and reports that the website is working.

Verify the current Git HEAD, working tree and CI before editing. Do not reset or overwrite any newer work.

Read the repository instructions:

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`

### Approved paper-trading specifications

Read both completely:

- `docs/stage-04a-paper-trading-spec.md`
- `docs/stage-04a-prospective-evaluation-protocol.md`

These are the primary requirements for Stage 4C.

Do not casually reinterpret their architecture, numerical rules or accounting policies.

### Existing paper-trading implementation

Read:

- `docs/stage-04b1-deterministic-paper-primitives.md`
- `src/backtest_badger/paper_types.py`
- `src/backtest_badger/paper_strategy.py`
- `src/backtest_badger/paper_execution.py`
- `src/backtest_badger/paper_accounting.py`
- `tests/test_paper_primitives.py`

Inspect the existing historical replay modules where useful, but do not change their frozen methods or scientific outputs.

### Database implementation

Read:

- `migrations/env.py`
- `migrations/versions/0001_market_candles.py`
- `src/backtest_badger/db.py`
- `src/backtest_badger/config.py`
- `tests/integration/conftest.py`
- `tests/integration/test_migration_cli.py`
- Existing database integration tests
- `compose.yaml`
- `alembic.ini`

Also inspect:

`docs/deployment/production-infrastructure.md`

This is important for understanding why the existing production database and backup system must remain unchanged in this milestone.

---

## 2. Scope and existing architecture

The existing application has three PostgreSQL tables:

- `market`
- `candle`
- `candle_revision`

Its existing Alembic baseline is revision `0001`.

Stage 4A specifies exactly five new paper-trading tables:

1. `paper_portfolio`
2. `paper_decision`
3. `paper_order`
4. `paper_market_event`
5. `paper_ledger_entry`

Implement the approved five-table design using a new Alembic revision.

Do not replace or alter the existing market-data model.

Do not introduce a sixth paper-trading table without a clearly demonstrated requirement and explicit owner review.

Prefer standard PostgreSQL features, Psycopg, Alembic and existing Python primitives.

Avoid SQLAlchemy ORM models, generic event frameworks, message brokers and unnecessary dependencies.

### Initial portfolio policy

The approved prospective reference strategy is Ridge Sign v1.

Initial experiments will eventually include:

| Market | Strategy | Starting capital |
|---|---|---:|
| BTCUSDT | Ridge Sign v1 | 10,000 USDT |
| ETHUSDT | Ridge Sign v1 | 10,000 USDT |

Each market has an independent portfolio, cash balance, asset holdings, ledger and experiment identity.

However, **Stage 4C must not create or activate these portfolios in production**.

Use synthetic portfolios in disposable integration-test databases.

The actual inception of prospective experiments belongs to Stage 4D.

---

## 3. Phase A — Schema and migration

Implement a new versioned Alembic migration following the existing repository conventions.

Expected revision:

`0002`

Suggested file:

`migrations/versions/0002_paper_trading.py`

Verify the actual migration head before choosing the revision identifier.

### 3.1 paper_portfolio

Implement the approved portfolio identity, immutable configuration and mutable operational projections.

Include:

- UUID primary key
- Unique portfolio key
- Foreign key to existing market identity
- Market/base/quote asset identity
- Strategy and model versions
- Canonical configuration JSONB
- Configuration SHA-256
- Protocol SHA-256
- Implementation SHA-256
- Initial funding amount
- Creation, inception and activation timestamps
- Operational state
- Ledger high-water sequence

Use the approved states:

`DRAFT`, `ACTIVE`, `PAUSED`, `CLOSED`

Enforce:

- Exactly one initial funding event per portfolio.
- No arbitrary subsequent funding.
- Configuration immutability after activation.
- Valid state transitions with auditable events.
- `ledger_highwater` consistent with committed ledger entries.
- No cross-market or cross-portfolio contamination.
- No silent overwriting of configuration/protocol identities.

Distinguish mutable operational projections from immutable economic evidence.

A portfolio should not become ACTIVE merely because its initial funding entry exists.

The approved protocol requires a valid contemporaneous inception mark before prospective activation.

Stage 4C may implement the transactional machinery for such a transition using supplied synthetic evidence, but must not activate any genuine experiment.

### 3.2 paper_decision

Store immutable forecast decisions and prospective safety decisions.

Include the approved fields for:

- Portfolio and decision identity
- Deterministic decision key
- Forecast or safety decision kind
- Original source/target horizon
- Original forecast identity
- Artifact relative path and content hashes
- Actual issuance, observation and decision times
- Exact Decimal forecast
- Target exposure
- Decision result
- Sticky exit obligation indicator
- Missed-horizon streak and structured reason
- Strategy configuration fingerprint

Enforce uniqueness for deterministic decision keys.

Enforce the approved uniqueness of original forecast horizons.

The database must reject mutations to committed decisions.

A duplicate idempotency key with identical authoritative input should have a well-defined, non-mutating outcome.

A duplicate key with conflicting evidence must fail explicitly.

Do not replace or retime original forecast timestamps.

### 3.3 paper_order

Store order intent and the audited terminal status projection.

Statuses:

- `SUBMITTED`
- `FILLED`
- `REJECTED`
- `EXPIRED`

Each order belongs to exactly one portfolio and decision.

Enforce:

- Deterministic order identity.
- Correct portfolio association.
- Unique retry attempt identity.
- Positive attempt number.
- Approved submission and expiry chronology.
- Initial status SUBMITTED.
- Only one active SUBMITTED order per portfolio.
- Exactly one legal transition from SUBMITTED to a terminal state.
- No transition between terminal states.
- No modification to immutable original order intent.
- Matching terminal evidence in `paper_market_event`.

Use the approved partial unique index:

`UNIQUE(portfolio_id) WHERE status='SUBMITTED'`

The order status is a projection of the event history, not a substitute for it.

### 3.4 paper_market_event

Implement immutable market, execution, valuation and operational evidence.

Use the event types defined in the approved Stage 4A specification, including:

- `QUOTE_OBSERVED`
- `QUOTE_FAILED`
- `FILL`
- `ORDER_REJECTED`
- `ORDER_EXPIRED`
- `MARK_OBSERVED`
- `MARK_MISSING`
- `EXIT_SATISFIED`
- `PAUSE`
- `RESUME`
- `RECOVERY_NOTE`
- `EXIT_BLOCKED_DUST`

Retain the approved type-specific fields.

For genuine future quote events, the schema must be capable of recording the bounded original HTTP response, hash, bid/ask, sizes, request/receipt timestamps, observed latency and source identity.

For modelled fills, retain:

- Original order identity
- Referenced original quote event
- Exact simulated quantity and price
- Gross notional
- Fee
- Relevant filter evidence
- Policy fingerprint
- Ledger sequences before and after
- Original event/commit timestamps

For valuations, retain:

- Scheduled UTC mark slot
- Actual observation and snapshot timestamps
- Original quote evidence
- Saved ledger sequence
- Valuation policy fingerprint

For missing marks, preserve the scheduled slot and actual discovery time without fabricating a price.

Enforce:

- One successful FILL per order.
- One successful FILL per quote event.
- One terminal event per order.
- One EXIT_SATISFIED event per effective exit obligation.
- At most one scheduled valuation outcome per portfolio/slot/policy.
- Correct event-type-specific fields.
- Correct portfolio association.
- No mutation of prior events.

Use PostgreSQL constraints, partial unique indexes, composite foreign keys and triggers as appropriate.

Avoid generic JSONB blobs when the approved design requires strongly typed, queryable economic columns.

### 3.5 paper_ledger_entry

Implement the authoritative append-only financial ledger.

Required concepts:

- Unique ledger entry UUID
- Portfolio identity
- Per-portfolio sequence
- Entry type
- Linked fill event when applicable
- Asset
- Exact signed Decimal movement
- Actual posting timestamp

Allowed entry types:

- `INITIAL_FUNDING`
- `FILL`

Funding uses exactly one positive USDT posting.

A successful buy or sell produces exactly two entries:

- One USDT movement
- One base-asset movement

Enforce:

- Strictly positive ledger sequence numbers.
- Unique `(portfolio_id, ledger_seq)`.
- Unique original funding per portfolio.
- Exactly one USDT and one base posting per fill.
- No postings linked to rejected or expired orders.
- No ledger entry update or deletion.
- No unexplained funding or transfer types.

The ledger is a cross-asset movement record, not an incorrectly modelled same-currency debit/credit ledger.

Do not require the numeric USDT and BTC/ETH deltas to add to zero.

Value conservation must be verified using the executed quantity, price and fee.

---

## 4. Phase B — Database-enforced integrity

**This is the most important part of Stage 4C.**

Python validation is necessary but not sufficient.

Invalid economic state must also be rejected when a test bypasses the Python application and issues direct SQL.

### 4.1 Numeric validation

Use PostgreSQL NUMERIC for monetary values.

Preserve exact Decimal values and avoid binary floating-point conversions.

Reject invalid numeric input, including:

- NaN
- Infinity
- Negative quantities where forbidden
- Negative balances
- Invalid prices
- Invalid fee values
- Invalid ledger sequence values

Be careful with PostgreSQL's special NUMERIC ordering behaviour.

A simple `value > 0` check is not sufficient to reject every nonfinite special value.

Apply explicit finite bounds or equivalent validated constraints.

### 4.2 Immutable evidence

Economic evidence in:

- `paper_decision`
- `paper_market_event`
- `paper_ledger_entry`

must reject UPDATE and DELETE, including direct SQL.

For `paper_order`, only the explicitly permitted status transition is mutable.

For `paper_portfolio`, only documented operational projections may change.

Those changes must be auditable.

Do not permit arbitrary changes to historical configuration, execution or monetary evidence.

### 4.3 Cross-portfolio integrity

A fill, order, quote, decision and ledger posting must belong to the same portfolio.

A standalone foreign key to a globally unique event ID is insufficient if it permits referencing an event belonging to a different portfolio.

Use appropriate composite keys/foreign keys or equivalent enforceable constraints.

Add direct SQL tests deliberately attempting cross-portfolio references.

Every such attempt must fail.

### 4.4 Deferred financial integrity

Implement a PostgreSQL deferred constraint trigger, or a comparably concrete DB-enforced design, that verifies the complete financial transaction at commit.

For each successful fill:

1. Exactly two postings must exist.
2. The correct assets must be used.
3. Each movement must have the correct sign.
4. Quantity must match the fill.
5. USDT movement must match gross notional and fee.
6. The fill must correspond to the correct order and quote.
7. The order must have status FILLED.
8. The fill's saved ledger sequence range must match the postings.
9. The portfolio's high-water sequence must advance correctly.
10. The transaction must not produce negative balances.

**Checking only that two ledger rows exist is not sufficient.**

Also reject a terminal FILLED order with no matching fill and a REJECTED/EXPIRED order without its required terminal event.

Handle the reverse direction as well: a terminal event may not exist without the matching order state.

Use carefully ordered deferred checks to permit valid multi-statement transactions while rejecting incomplete commits.

### 4.5 Funding invariants

Initial funding must be exactly 10,000 USDT under the approved v1 policy and must occur exactly once per newly funded v1 portfolio.

Reject duplicate funding, wrong-asset funding and unsupported follow-up deposits.

A DRAFT portfolio may be unfunded before its funding transaction; don't make it impossible to create a valid DRAFT record.

---

## 5. Phase C — Transactional Python persistence layer

Create a small, clear persistence module.

Suggested location:

`src/backtest_badger/paper_persistence.py`

Additional small modules are acceptable where they materially improve separation of responsibilities.

Prefer ordinary functions and explicit transactions.

Do not implement a general repository framework.

### Minimum required operations

Implement tested functions or equivalent clear interfaces for:

1. Creating a versioned DRAFT portfolio.
2. Funding a portfolio exactly once.
3. Recording an immutable decision.
4. Submitting an order.
5. Recording a quote observation or failure.
6. Committing a successful modelled fill.
7. Rejecting or expiring an order.
8. Recording an exit satisfaction.
9. Recording an immutable observed or missing valuation.
10. Loading a portfolio's latest durable operational state.
11. Reconstructing balances from ledger entries.
12. Reconstructing weighted-average cost basis and realised P&L.
13. Reading a coherent as-of ledger snapshot.
14. Independently reconciling a portfolio.
15. Detecting incomplete or inconsistent recovery states.

The interfaces should accept validated supplied evidence and an explicit database connection/transaction context as appropriate.

They must not independently request Binance quotes, read current forward files or access a live clock to invent events.

Stage 4D will supply authentic future evidence and current timestamps.

### Reuse the existing primitives

Reuse, rather than reimplement:

- `paper_accounting`
- `paper_execution`
- `paper_strategy`
- `paper_types`

In particular, preserve the existing exact Decimal arithmetic, fee rounding, order eligibility and account transition rules.

Map existing immutable domain objects into the database carefully.

Avoid a second, independently evolving calculation of fees or trade economics.

Where database constraints need to reproduce a formula, document the exact agreement with the pure-function implementation and test both paths against one another.

Do not modify frozen historical experiments to support persistence.

---

## 6. Atomic successful fills

Implement a single, clearly identifiable transaction boundary for a successful simulated fill.

Required flow:

1. Begin a database transaction.
2. Lock the portfolio row with `SELECT ... FOR UPDATE`.
3. Lock the relevant SUBMITTED order.
4. Reconcile the current authoritative ledger state.
5. Check for duplicate order, fill or quote consumption.
6. Verify portfolio, policy and decision identities.
7. Validate the supplied quote/filter/fill evidence and chronology.
8. Recompute the expected monetary movements using approved primitives.
9. Insert the immutable FILL event.
10. Insert exactly two ledger entries.
11. Advance the portfolio high-water sequence.
12. Change the order status to FILLED.
13. Where appropriate, satisfy the outstanding exit obligation atomically.
14. Run the required reconciliation/integrity checks.
15. Commit.

No part of the success state may survive a rolled-back transaction.

### Fault injection

Add tests that deliberately fail at each important stage:

- Before inserting the fill
- After inserting the fill
- After the first posting
- After the second posting
- Before updating the high-water sequence
- Before terminalising the order
- Before exit satisfaction
- During final commit validation

For each failure, verify:

- No phantom completed order.
- No orphan fill.
- No partial ledger postings.
- No advanced high-water sequence.
- No false exit satisfaction.
- No negative or altered account balances.

Use direct database queries to prove rollback, not only Python return values.

---

## 7. Idempotency and concurrency

Design for a later prospective worker that may restart, lose its connection or run concurrently with another copy.

### Idempotency

Use deterministic keys and unique constraints to ensure:

- No duplicate portfolio funding.
- No duplicate decision from the same original forecast.
- No duplicate order attempt.
- No duplicate successful fill.
- No reuse of a quote event for multiple fills.
- No duplicate scheduled mark.
- No duplicate satisfaction of the same exit obligation.

On retry, a caller must be able to distinguish:

- Previously committed identical operation
- Previously failed/uncommitted operation
- Conflicting operation with reused identity

Never treat a conflicting payload as a harmless duplicate.

### Concurrent workers

Test using actual separate PostgreSQL transactions/connections.

At minimum, simulate:

- Two workers attempting to spend the same cash.
- Two workers attempting to sell the same asset holdings.
- Two workers attempting to fill the same order.
- Two workers attempting to submit different orders for one portfolio.
- Two workers attempting duplicate funding.
- One worker recording a valuation while another commits a fill.

Assert that only a valid serialised outcome commits.

Do not rely solely on a Python process lock.

Use the database's portfolio row lock and uniqueness constraints.

Use bounded lock and statement timeouts to prevent hanging tests.

---

## 8. Crash recovery and sticky exits

The approved Stage 4A protocol requires conservative recovery.

### Crash after order submission

A persisted SUBMITTED order is not proof of a fill.

After restart, the recovery reader must identify the outstanding order and its original expiry.

Do not invent an execution.

Do not retroactively fill using a quote obtained during a previous process run.

Provide the persistence functionality needed to record a genuine current-time expiry/rejection later.

### Crash after quote observation

A saved quote is evidence that a quote was observed.

It is not permission to reuse that stale quote for a simulated fill after restart.

Ensure the database records the relationship between:

- Order
- Quote event
- Original process/run identity
- Request/receipt times

A later worker must be able to recognise and reject stale quote reuse.

### Crash after committed fill

A completed fill and its paired postings must be recovered exactly.

A restarted worker must not post them again.

### Sticky exit obligations

Exit obligations must remain durable across:

- Rejected sell attempts
- Expired orders
- Quote failures
- Process restarts
- Later positive forecasts

A later positive forecast cannot cancel an unresolved exit obligation.

A new buy cannot reuse a signal that predates the exit satisfaction.

An exit may only be marked satisfied once the appropriate financial state is atomically flat.

Retain blocked-dust evidence and require explicit resolution later rather than silently writing holdings to zero.

Tests should use fabricated evidence and controlled clocks.

**Do not build or activate the live recovery scheduler in Stage 4C.**

---

## 9. Valuation persistence and exact replay

The approved prospective schedule is one mark every four hours at:

`00:10, 04:10, 08:10, 12:10, 16:10, 20:10 UTC`

with a five-minute capture window.

Stage 4C must implement the durable event and reconstruction contract, not the live timed worker.

### Observed marks

A valid observed mark stores:

- Scheduled slot
- Actual quote request/receipt and mark times
- Original quote evidence and SHA-256
- Actual bid/ask and available sizes
- Valuation policy identity
- Exact portfolio ledger high-water at the recorded snapshot

Capture the high-water under a portfolio lock.

A fill committed before that snapshot is included.

A fill committed after it is excluded.

### Missing marks

Persist a missing mark with its originally scheduled identity and the actual discovery time.

Do not populate it with a later quote.

Do not silently replace a missing mark after a market recovery.

### As-of reconstruction

A valuation must be reproducible from:

- The immutable portfolio ledger through its saved sequence
- The original retained quote/mark event
- The frozen valuation policy

Reconstruct:

`equity = cash_asof + base_quantity_asof × observed_bid`

Also reconstruct realised and unrealised P&L using existing accounting conventions.

Test that subsequent transactions do not alter an earlier mark's value.

Never use the latest market price to reproduce an earlier valuation.

Missing marks must remain explicit gaps.

---

## 10. PostgreSQL integration environment

This milestone requires **real PostgreSQL integration tests**.

Mock-only tests are not sufficient to validate isolation, deferred constraints or atomicity.

Use the project's existing PostgreSQL 17 environment and integration-test conventions.

Inspect:

`tests/integration/conftest.py`

Use the existing disposable test database fixture and `BADGER_TEST_ADMIN_DSN` pattern.

### Environment rules

- Use a newly created disposable test database.
- Verify the intended server/database identity before running migrations or destructive tests.
- Never run against the regular local development database unless it is demonstrably disposable and explicitly selected.
- Never run against production.
- Never drop or truncate a pre-existing database.
- Never reuse the production Docker volume.
- Never run `docker system prune` or remove production-related volumes.
- Do not alter the existing ingestion/forward database.
- Use temporary synthetic data only.

If local Docker/PostgreSQL is unavailable, try the existing supported local setup.

If it remains unavailable, complete the code and unit tests but clearly report that Stage 4C's database acceptance criteria are still blocked.

**Do not claim Stage 4C complete if the real database tests have not executed.**

### Migration tests

Verify on disposable databases:

1. Existing revision `0001` upgrades cleanly to `0002`.
2. All five paper tables are created with expected keys, indexes, checks, triggers and foreign keys.
3. Original market/candle data remain unchanged.
4. A repeated upgrade is harmless.
5. Fresh installation reaches the same expected schema.
6. Downgrade to `0001` is safe and explicitly guarded.
7. A downgrade with populated paper evidence does not silently destroy economic records.
8. Re-upgrade remains valid after a permitted disposable downgrade.
9. Unrelated pre-existing application data survive.
10. Migration failures roll back cleanly.

Avoid automatic destructive downgrades against a populated database.

The appropriate downgrade safeguard should be documented and tested.

---

## 11. Independent integrity and restore tests

Implement a separate read-only reconciliation function, not merely an assertion inside the write path.

It should verify:

- Portfolio configuration identities
- Initial funding
- Ledger continuity
- Ledger high-water correctness
- Fill/posting relationships
- Order status and terminal event agreement
- Quote provenance and chronology
- No duplicate consumed quote
- No duplicate financial event
- Nonnegative balances
- Weighted-average cost basis
- Realised P&L
- Exact as-of marks
- Sticky exit status

Failures should produce clear structured diagnostic reasons without exposing credentials or unnecessary private source data.

### Isolated database restore

If practical within the existing local test environment, exercise a real snapshot/restore into a second disposable database and confirm:

- All five table definitions and their constraints are present.
- Evidence row counts and identities match.
- Ledger balances replay identically.
- Historical valuation points reproduce exactly.
- Trigger protections remain active after restore.

Do not modify the production S3 backup process, restore timers or retention policy.

Extending operational backups to cover all five tables will be a later production readiness task.

---

## 12. Tests required

Add comprehensive unit and integration tests.

Suggested files:

- `tests/test_paper_persistence.py`
- `tests/integration/test_paper_persistence.py`
- `tests/integration/test_paper_migration.py`

Use the existing test conventions.

### Essential acceptance matrix

| Area | Required demonstration |
|---|---|
| Schema | Exactly five new paper tables, correct migration |
| Funding | Exactly one valid initial funding |
| Decisions | Immutable, unique, causally timestamped |
| Orders | One active order per portfolio, legal transitions |
| Quotes | Immutable original evidence, correct portfolio |
| Fills | One order, one quote, exactly two correct postings |
| Financial integrity | DB rejects missing/wrong postings |
| Atomicity | Every injected failure rolls back all changes |
| Concurrency | No double spend, double sell or duplicate fill |
| Recovery | Restart cannot invent or replay a fill |
| Sticky exits | Obligation survives failures until actually satisfied |
| Valuations | Exact as-of reconstruction |
| Missing marks | Permanent gaps, no fabricated prices |
| Cross-portfolio | Wrong-market references rejected |
| Immutability | Direct SQL mutations rejected |
| Replay | Loaded DB account matches pure-function accounting |
| Restore | Isolated snapshot reproduces state and constraints |
| Regression | Existing research, forward feeds and historical accounts unchanged |

### Worked numerical example

The approved Stage 4A specification includes a worked weighted-average-accounting example with a purchase, partial sale, realised P&L and remaining cost basis.

Use that exact example as an independent integration test.

Check Python arithmetic, stored NUMERIC values, ledger postings, replay and valuation all agree.

### Test quality

Include negative and adversarial tests.

Do not only test the Python happy path.

Assert actual database contents after failure, restart and concurrency scenarios.

Avoid tests that pass because a fake repository bypasses database behaviour.

---

## 13. Security and operational boundaries

The database code must be safe to use later in a long-running, untrusted-network environment.

Requirements:

- Parameterised SQL only for runtime values.
- No credentials printed or committed.
- Bounded database connection/statement/lock timeouts.
- No dynamic SQL from unsanitised input.
- Strict UUID, hash and market validation.
- Exact Decimal handling.
- Safe relative evidence paths.
- Original evidence size bounds.
- No unexpected cross-portfolio writes.
- No silent exception swallowing.
- No unbounded retry loops.
- No broad superuser permissions in ordinary application code.
- Database integrity violations fail closed.

Document the intended future least-privilege runtime database role and relevant schema permissions.

Do not change production database roles during this milestone.

### No live operations

Do not:

- Connect to or modify the Lightsail production database.
- Run Alembic against production.
- Create production paper portfolios.
- Activate paper-trading services.
- Add a recurring paper-trading scheduler.
- Make real Binance quote requests.
- Connect to private exchange APIs.
- Submit orders to Binance.
- Change the forward forecasting/scoring system.
- Change R2 objects.
- Change Cloudflare settings.
- Deploy website changes.
- Re-run existing historical economic experiments.
- Modify frozen Ridge or Study 002 research.
- Modify existing editorial approval hashes.
- Change production backups, restore drills or retention.
- Add new AWS infrastructure.

All simulated trading events in tests must use fabricated, explicitly labelled evidence.

Prospective economic observations must begin only after a separately reviewed future activation.

---

## 14. Implementation sequencing

Follow a deliberate sequence:

### Phase A — Design reconciliation

- Inspect approved Stage 4A contracts.
- Inspect existing Python primitives and migration/test infrastructure.
- Map each specified invariant to DB schema, DB trigger, transaction logic or application validation.
- Document any unimplementable or ambiguous constraints.
- Select the smallest maintainable implementation.

### Phase B — Schema and migration

- Implement the five tables.
- Implement keys, indexes, immutable triggers and relevant checks.
- Implement deferred financial integrity.
- Run migration tests on disposable PostgreSQL.

### Phase C — Transactional repository functions

- Implement funding.
- Implement decisions and orders.
- Implement quote events.
- Implement fill/terminal transactions.
- Implement valuation persistence.
- Implement loading and independent reconciliation.

### Phase D — Failure and concurrency tests

- Test invalid SQL.
- Test transactional rollback.
- Test simultaneous workers.
- Test crash recovery.
- Test sticky exits and valuation snapshots.

### Phase E — Verification and documentation

- Run full applicable tests.
- Validate migration and isolated restore.
- Review the changed-file inventory.
- Confirm no production systems were touched.
- Prepare the Stage 4C report.

Do not rush into a live worker or public dashboard.

If the database design reveals a genuine incompatibility with the approved Stage 4A contract, stop that affected implementation path, document the precise conflict and propose the smallest compatible correction.

Do not silently weaken the accounting guarantees.

---

## 15. Validation commands

Run appropriate commands using the actual environment:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

Run isolated PostgreSQL integration tests with the appropriately configured disposable test database.

Inspect the existing CI configuration to ensure the new integration tests are included in GitHub Actions.

Verify that database tests cannot accidentally connect to production.

Run all existing paper primitives and shared-accounting regressions.

Check existing frozen scientific files and relevant research result identities remain unchanged.

Where practical, run the wheel/package build and import validation.

Check:

`git diff --check`

Do not report tests as passing if they were skipped or not run.

Do not adjust financial assertions merely to obtain green tests.

---

## 16. Documentation

Create:

`docs/stage-04c-paper-trading-persistence.md`

Include:

1. Executive summary.
2. Starting revision.
3. Database migration identity.
4. Exact five-table schema.
5. Constraints and index inventory.
6. Economic immutability design.
7. Deferred trigger design and SQL examples.
8. Transaction boundaries.
9. Idempotency rules.
10. Recovery and sticky exits.
11. Ledger replay and valuation reconstruction.
12. Numeric precision and fee rounding.
13. Integration and concurrency results.
14. Failure-injection results.
15. Migration/downgrade results.
16. Local restore results.
17. Limitations and pending production prerequisites.
18. Full changed-file inventory.
19. Reproducible test instructions.
20. Recommended next stage.

Update where useful:

- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- `README.md`
- `prompts/README.md`

Archive this request verbatim at:

`prompts/stage-04-paper/stage-04c-durable-paper-persistence.md`

Preserve the existing Stage 4A protocols, Stage 4B reports and frozen historical research documents.

Avoid rewriting historical stage descriptions as if they were newly completed.

---

## 17. GitHub workflow

This request authorises local implementation, isolated test database operations, commit and push.

It does not authorise production installation.

After completing the implementation:

1. Inspect all changed files.
2. Confirm no secrets, database dumps or private data were staged.
3. Confirm no protected scientific files changed.
4. Confirm the migration and all applicable tests passed.
5. Commit the focused change.
6. Push to `main`.
7. Verify both GitHub CI workflows for the exact new SHA.

Suggested commit:

`feat(paper): implement durable paper trading persistence`

If the work requires multiple logical commits, use clear Conventional Commit messages.

Do not push a partially verified implementation and describe it as complete.

If the implementation cannot satisfy a mandatory database invariant, report the blocker accurately instead of presenting a green but incomplete milestone.

The existing Cloudflare GitHub integration may upload a candidate automatically. That is acceptable under the current candidate-only workflow, but no website promotion or deployment is needed for this backend-only stage.

Do not create additional Cloudflare builds manually.

---

## 18. Final completion report

Provide:

### Implementation

- Starting Git SHA
- Final Git SHA
- New migration revision
- Five-table schema summary
- New Python persistence interfaces
- Database-enforced financial constraints
- Reused Stage 4B.1 primitives
- Any deviations from Stage 4A and their rationale

### Verification

- Unit tests passed
- PostgreSQL integration tests passed
- Concurrent-writer tests passed
- Failure-injection tests passed
- Independent reconciliation results
- Migration upgrade/downgrade results
- Isolated restore results
- Existing paper and research regressions
- Lint and packaging checks
- GitHub CI results

### Safety

- Confirmation no production database was modified
- Confirmation no paper worker was activated
- Confirmation no actual market data or trades were used
- Confirmation existing forward feeds and website were unchanged
- Confirmation frozen research evidence is preserved

### Handoff

- New documentation paths
- Complete changed-file inventory
- Any known technical limitations
- Production migration prerequisites still outstanding
- Proposed Stage 4D implementation sequence
- Whether Stage 4C is complete or blocked

---

## Definition of success

Stage 4C is complete when:

1. All five approved paper-trading tables exist in a tested migration.
2. Valid simulated funding and financial transactions commit atomically.
3. Invalid/incomplete financial transactions are rejected by PostgreSQL.
4. Ledger entries and economic events cannot be modified retrospectively.
5. Concurrent workers cannot overspend or duplicate fills.
6. Recovery cannot turn old quotes or interrupted orders into invented fills.
7. Sticky exit obligations persist correctly.
8. Historical valuations reconstruct from their original saved ledger sequence.
9. An independent database reconciliation detects inconsistencies.
10. Real PostgreSQL integration tests pass.
11. Existing research and forward systems are unchanged.
12. GitHub CI passes for the committed implementation.
13. No production database or paper-trading service has been activated.

**The result should be a trustworthy persistence layer, not a running trading system.**

Stop after validated local development, commit/push and handoff. Stage 4D will handle genuine prospective integration and eventual controlled activation separately.
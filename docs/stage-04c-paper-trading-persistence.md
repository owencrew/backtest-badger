# Stage 4C — Durable paper-trading persistence

Stage 4C persists a simulated spot fill, its cash and base postings, its terminal
order state and any resulting exit satisfaction in one PostgreSQL transaction.
A separate reader rebuilds the account from original evidence. The verification
uses fabricated portfolios in disposable PostgreSQL 17 databases. Genuine
prospective inception and worker integration belong to Stage 4D.

Work started on clean `main` at `26c5827c2ae0bd0342484380d678e1fa61c6e1e3`.
Local and remote heads agreed and both CI and Frontend had succeeded. The
approved [technical specification](stage-04a-paper-trading-spec.md) and
[evaluation protocol](stage-04a-prospective-evaluation-protocol.md) govern v1.

## Schema and integrity inventory

Alembic revision `0002` follows `0001`. It adds exactly five tables. The frozen
[column definitions and indexes](../migrations/sql/0002/tables.sql),
[row guards](../migrations/sql/0002/guards.sql) and
[commit checks](../migrations/sql/0002/financial.sql) are the executable inventory.

| Table | Identity and durable evidence | Checks and indexes |
|---|---|---|
| `paper_portfolio` | UUID and unique cohort key, Binance spot market FK, currencies, strategy/model/recipe, canonical UTF-8 configuration plus JSONB and SHA-256, protocol/implementation/policy fingerprints, initial funding amount and timestamps | Starts DRAFT at sequence zero. Market identity, original funding time and configuration are fixed at creation. Only the audited state, activation time, state event pointer and financial high-water can advance. A guard pins the identity of a market referenced by a portfolio. |
| `paper_decision` | UUID, portfolio key, original forecast and prediction IDs, safe relative path, both original hashes, automation and model recipe, exact forecast, source and target, actual issuance/observation/decision times, exposure, reason, streak and effective obligation | Unique portfolio/decision key, original forecast and forecast horizon. Separate unique missing-horizon index. Four-hour grid, eligibility, sequence of missed horizons, actual holdings and pending exits govern the permitted action. |
| `paper_order` | UUID, decision, original client key/run, side/intent, positive attempt, cash/base/sequence/time snapshot, policy and submission/expiry | Composite decision FK, unique client key and decision/side/attempt. Partial unique portfolio index for SUBMITTED. Valid intent uses current balances. Thirty-second expiry, one buy attempt, sequenced exit retries at least five minutes apart. Only SUBMITTED → FILLED/REJECTED/EXPIRED is mutable. |
| `paper_market_event` | UUID, portfolio and relevant order/decision, actual event/recording times, original run/HTTP evidence and 4,096-byte body, parsed depth/prices, simulated economics, effective filter rules/hash/time, policy and ledger prefix or mark slot | Composite order/decision and self-FKs. Type-dependent nullability. Unique terminal outcome per order (also one fill per order), fill per consumed quote, quote identity per portfolio, satisfaction per exit, reference per exit outcome, and scheduled outcome per portfolio/slot/policy. Time indexes support portfolio chronology. |
| `paper_ledger_entry` | UUID, portfolio, sequence, funding or fill, currency, exact signed movement, actual posting time | Unique portfolio/sequence and fill/asset. Only positive 10,000 USDT at sequence 1 can open a portfolio. Only a same-portfolio fill can generate later postings. Cash is posted first, base second. |

Domains reject nonfinite money and timestamps, malformed hashes and empty keys.
The tables protect economic evidence from UPDATE, DELETE and TRUNCATE. Mutable
projections have separate guards. A funded DRAFT becomes ACTIVE only when its
first eligible observed inception mark commits. PAUSE and RESUME events drive
their corresponding transitions. A CLOSED portfolio requires a paused, flat
account, with all orders terminal and exits satisfied. Since Stage 4A has no
CLOSE event type, closure uses a RECOVERY_NOTE with reason `CLOSE`. The ledger
and events identify changes even when two supplied timestamps are equal.

## Transaction and idempotency contract

The Python entry points require an idle Psycopg connection. Each owns its outer
transaction and returns only after commit. Use the existing bounded
`db.connect_database` connector. Write transactions use READ COMMITTED,
UTC, a three-second lock timeout and a ten-second statement timeout. Writers
lock the portfolio first and then the order. Guards use the same portfolio lock
for inserts issued directly in SQL. Original order submission commits before a
quote observation can reference it.

`create_portfolio`, `fund_portfolio`, `record_decision`, `submit_order`,
`record_quote`, `record_quote_failure`, `commit_fill`, `terminate_order`,
`reject_dust`, `record_mark` and `record_operational_event` are the write interfaces.
`paper_records.configuration` builds the versioned v1 configuration. Stage 4D
supplies verified original evidence, caller timestamps and a fresh process-run
identity. The adapter must validate source authenticity, file hashes and current
clock health. Persistence makes no network, filesystem or exchange requests.

A UUIDv5 binds each identity to its portfolio, kind and original stable key.
Identical authoritative input returns the same UUID and `Receipt.created=False`.
An absent operation can commit once and returns `True`. Reusing an identity with
different fields raises `EvidenceConflict` or an explicit validation/integrity
error. A different key claiming the same unique economic outcome also fails.
A retried mark compares against its saved sequence even after later transactions.

`commit_fill` locks and reconciles, loads the committed decision/order and
original quote, checks run identity, re-executes `simulate_order` against the
original filter evidence and compares or inserts the immutable fill. It posts
both `Movement` values, advances high-water by two and terminalises the order.
A final sell records EXIT_SATISFIED inside this transaction. The writer then
independently replays the evidence before allowing PostgreSQL to commit.
Rejection/expiry transactions couple their event and terminal projection. A
dust rejection also appends EXIT_BLOCKED_DUST, retaining the effective filters,
quote and unresolved obligation. This event pauses the account. Ordinary RESUME
cannot release a dust block. Resolution requires a separately reviewed policy.

Each new decision, intent or observation follows the latest recorded evidence
time. A fill and its associated exit event retain their shared occurrence time
and recording time. The immediate guards enforce price, fee, depth, retained
quote hash and body, step, effective quantity/notional limits, freshness,
affordability and unchanged
order provenance. The deferred checks use the committed prefix to verify actual
balances, then join both postings to the fill by identity, asset, timestamp,
sequence and amount. They verify terminal evidence in **both** directions. All
checks must pass even if the caller bypasses the Python layer. For example, this
transaction against an otherwise valid submitted order fails at COMMIT:

```sql
BEGIN;
UPDATE paper_order SET status = 'FILLED' WHERE order_id = :submitted_order;
COMMIT;
```

This read-only query shows the two distinct currency movements of one committed
fill. Each amount must agree with the original execution evidence.

```sql
SELECT e.event_id, e.simulated_qty, e.simulated_price, e.fee_usdt,
       l.ledger_seq, l.asset, l.delta_units
FROM paper_market_event AS e
JOIN paper_ledger_entry AS l ON (l.portfolio_id, l.fill_event_id)
                             = (e.portfolio_id, e.event_id)
WHERE e.event_id = :fill_id
ORDER BY l.ledger_seq;
```

## Recovery, numerical policy and marks

`reconcile_portfolio` opens a read-only REPEATABLE READ snapshot and returns the
operational state, submitted intent and expiry, original pending quote evidence,
exit identity, missed streak, accounts by complete sequence and historic marks.
A later run terminalises an interrupted attempt at actual discovery time. Its run
identity cannot consume an earlier process's quote. A failed/expired buy waits
for a different timely forecast. An exit persists through failures and later
positive signals. Its retry has a new attempt number, order and quote. A buy
after liquidation requires original issuance strictly after exit satisfaction.

The audit cross-checks the original configuration/market, funding, order and
quote relationships, unique consumption, simulated results, every ledger
movement, terminal status, exit evidence and saved marks. It compares grouped
SQL balances with the pure accounting result. Integrity incidents carry a reason
and evidence UUID. A reader or writer encountering invalid evidence fails
closed. Restoring an interrupted transaction requires reading the durable
result by identity. Detection never creates a retrospective financial event.

Prices, quantities, fees and ledger deltas use unrestricted PostgreSQL NUMERIC
and Python Decimal. The versioned pure functions supply sizing, fees, weighted
average basis and realised P&L. The SQL checks duplicate only the needed admission
and conservation rules. A buy uses ask × 1.0002, a sell bid × 0.9998. Gross is
quantity × modelled price. The SQL equivalent of the primitive's upward 1e-8
fee rounding is `ceil(gross * 100000) * 0.00000001`. A buy posts
`-(gross + fee)` USDT and positive base. A sale posts `gross - fee` USDT and
negative base. The maximal affordable buy passes the rounded-fee test and the
next step fails it. The pure accounting implementation retains its 160-digit
exact context and its 80-digit division rule for partial basis allocation.

`asof_account` accepts only complete ledger prefixes. Valid marks pin the
portfolio high-water under lock, retain the bid/ask, original quote bytes and
snapshot time, and use `value_account` on that specific prefix. All scheduled
slots lie ten minutes after a four-hour UTC boundary and have a five-minute
window. A quote received before the last included posting cannot form the mark.
Missing marks retain their slot and actual discovery time and return an explicit
gap. Replaying an earlier mark uses only its original quote and saved sequence.

The specification's worked accounting example buys 10 and sells 4. The
integration test stores those illustrative amounts in a temporary PostgreSQL
table and checks both signed postings, SQL fee rounding, pure replay and the bid
valuation. It obtains 38.992008 USDT realised, 59.27988 unrealised and
10,098.271888 equity. An actual v1 order must use the full affordable buy or
sell all base. The order-path tests exercise that rule without admitting
partial prospective liquidations.

## Verification and reproduction

The test fixture creates random databases from template0 on a loopback-only
PostgreSQL 17 test server. It verifies the maintenance DB and server major
version, then drops only databases whose creation succeeded. Stage 4C was
exercised on a separate temporary-storage Docker container. The original
production backup rehearsal still targets revision 0001 in its disposable
fixture. The new restore test dumps all five populated paper tables and
restores them to a second fresh database, compares all rows, trigger and
constraint definitions, recovered state and Decimal mark values, and attempts
a forbidden mutation on the restored copy. A separate owner-only corruption
drill verifies the independent reader detects a wrong posting.

The migration tests cover fresh and repeated upgrade, a populated 0001 market
and candle, rollback of an intentionally conflicting migration, an empty
downgrade/re-upgrade and refusal of a downgrade once any portfolio exists.
Unrelated application data survive. Downgrade takes an exclusive lock before
checking for portfolios and uses explicit dependency order with no CASCADE.

Faults are injected by actual database triggers before and after the fill, after
each posting, before high-water, before terminal status, before satisfaction,
and by a deferred trigger at commit. Every case compares orders, events,
postings, balances and high-water against the original rows, then retries the
rolled-back fill. Separate connections race on funding, competing intents,
the same buy budget and sell holdings, duplicate fill, and mark versus sale.
The winning serial order determines the mark's saved prefix.

Use a fresh, separate local PostgreSQL 17 container with temporary storage.
Export its loopback `BADGER_TEST_ADMIN_DSN` with the `postgres` maintenance
database, explicit user/password and port. Export its container ID as
`BADGER_D2A_TEST_CONTAINER` for both restore drills. CI supplies its own
disposable service container. On macOS use a private scratch directory under
`/private/tmp`, with its group set to the invoking process group, and point
`TMPDIR` there. This satisfies the
existing writable-ancestor and private-file ownership regressions. Give long
pytest runs separate `--basetemp` directories to isolate fixture cleanup. From
the repository root run

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -m integration
uv run --locked pytest -o tmp_path_retention_policy=none
uv build --wheel
git diff --check
```

Integrity checks on the retained scientific files reproduced the published SHA-256
identities for the summary and detailed evidence of each study. All 57 files in
the Study 002 source freeze matched its manifest. These checks read existing
bytes without running either historical experiment.

Local verification used Python 3.12 and PostgreSQL 17:

| Check | Executed result |
|---|---|
| Complete root regression run | 3,139 passed, 88 expected skips in 19m 41s; the additional chronology case is included in the final focused run below |
| PostgreSQL integration plus paper primitives/mappings | 432 passed: 227 integration and 205 pure tests |
| Final paper persistence acceptance, including the added recorded-time regression | 45 passed, including all eight rollback points, separate-connection races, migration, corruption detection and real dump/restore |
| Isolated E.5 / E.5c / E.5d guarded fabricated suites | 87 / 55 / 153 passed; no guarded tests skipped |
| Ruff lint and formatting | Passed across 290 Python files |
| Wheel build and isolated imports | Wheel built successfully; persistence, reconciliation and dust handling imported from the wheel |
| Scientific evidence | Both studies' summary/evidence hashes and all 57 Study 002 frozen source hashes matched |

The genuine Study 001 experiment replay is deliberately opt-in and was not run.
The normal-suite E.5 skips are covered by its required isolated runner above.
Earlier macOS full-suite attempts exposed scratch-directory ownership and
concurrent fixture-cleanup issues; the dedicated scratch configuration above
addresses those environment conditions without changing application checks.

## Operational limits and Stage 4D handoff

Full reconciliation reads the portfolio history and retains complete prefixes
for valuation. Benchmark this work under the portfolio lock before selecting
production capacity or timeouts. Process identity and timestamps are supplied
evidence. The adapter must generate a fresh run ID after each restart and retain
the original forecast artifacts, filter source and executable fingerprints.
A database owner can disable triggers. Production therefore requires a separate
migration owner, controlled access, encrypted external backups and a tested
independent restore.

Use a dedicated non-owner runtime role with schema USAGE, SELECT on referenced
market and paper tables, INSERT on required evidence tables, UPDATE only on
`paper_order.status` and portfolio projection columns, and permissions for the
reviewed guard functions. Provision portfolio identity with a separate
inception role. The public reporting role needs read-only access to reviewed
queries/views. Reserve DDL, trigger management, TRUNCATE and DELETE for
administration. Restrict schema CREATE and role inheritance. Rehearse the exact
grants and role separation before deployment.

1. Implement and verify the original Stage 3 artifact reader, bounded public
   quote/filter adapters, clock checks and unique process-run handling using a
   separately approved integration scope.
2. Rehearse interrupted intents, missing horizons, blocked exits and valuation
   gaps with the planned worker and least-privilege roles.
3. Extend operational fingerprinting, encrypted backups, restore drills,
   monitoring and retention to include all five tables and original artifacts.
   The production rehearsal currently recognises revision 0001.
4. Review migration, rollback/forward-recovery and activation independently.
   Only after separate approval, fund independent market cohorts and capture the
   first eligible contemporaneous mark. Public reporting has its own gate.

## Changed-file inventory

| Files | Purpose |
|---|---|
| `migrations/versions/0002_paper_trading.py` | Version link, guards, deferred trigger registration, safe downgrade |
| `migrations/sql/0002/tables.sql`, `guards.sql`, `financial.sql` | Five tables and declarative constraints, write guards, commit checks |
| `src/backtest_badger/paper_persistence.py`, `paper_records.py`, `paper_reconciliation.py` | Transactional interfaces, contract mappings, independent recovery and replay |
| `tests/integration/test_paper_persistence.py`, `tests/test_paper_records.py` | Fabricated PostgreSQL acceptance and restore tests, pure mapping and precision tests |
| `tests/integration/conftest.py`, `test_candles.py`, `test_migration_cli.py`, `test_lightsail_rehearsal.py` | Local server guards, migration head expectations and deployed-baseline rehearsal fixture |
| `.github/workflows/ci.yml` | Supply the disposable service identity for restore coverage |
| `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/development-handoff.md`, `docs/stage-04c-paper-trading-persistence.md` | Current capability, verification and operational handoff |
| `prompts/README.md`, `prompts/stage-04-paper/stage-04c-durable-paper-persistence.md` | Verbatim request and index |

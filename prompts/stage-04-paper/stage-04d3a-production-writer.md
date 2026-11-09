# Backtest Badger — Stage 4D.3A: Production Paper-Trading Writer and Pre-Activation Verification

## Objective

Implement the complete prospective simulated-trading writer for Backtest Badger, building on the verified Stage 4D.2 implementation.

The system must be able to take a qualifying original forward forecast, determine the approved Ridge Sign v1 trading action, durably record a simulated order, request a genuinely fresh public Binance quotation after submission, and atomically record the resulting simulated fill and ledger movements.

It must also support missed horizons, sticky exits, rejected orders, missing valuations, process crashes and recovery.

**This stage is local implementation and isolated testing only.**

No production worker, portfolio or service may be activated.

The objective is a complete, tested writer suitable for a subsequent separately authorised Lightsail deployment.

---

## 1. Starting context

Repository:

`~/Code/backtest-badger`

GitHub:

`owencrew/backtest-badger`

Expected starting commit:

`12ad7c50a5a7f6354d931c16bd2469cfe02151b9`

Both GitHub workflows passed for that exact SHA.

Verify the current branch, commit, clean working tree and CI status.

Read:

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- `docs/stage-04a-paper-trading-spec.md`
- `docs/stage-04a-prospective-evaluation-protocol.md`
- `docs/stage-04c-paper-trading-persistence.md`
- `docs/stage-04d1-prospective-integration.md`
- `docs/stage-04d2-production-readiness.md`
- `docs/deployment/paper-migration-activation-checklist.md`
- `docs/deployment/production-infrastructure.md`

Inspect the existing implementations in:

- `paper_worker.py`
- `paper_recovery.py`
- `paper_persistence.py`
- `paper_reconciliation.py`
- `paper_evidence.py`
- `paper_artifacts.py`
- `paper_market_data.py`
- `paper_clock.py`
- `paper_operations.py`
- `paper_strategy.py`
- `paper_execution.py`
- `paper_accounting.py`
- `paper_records.py`
- `paper_types.py`
- `paper_checkpoint.py`

And the associated SQL migrations, role grants and integration tests.

Preserve the approved Stage 4A economic parameters and source-evidence contract.

---

## 2. Current state

Stage 4D.2 completed an isolated production-readiness rehearsal.

Its final assessment was:

**READY WITH CONDITIONS**

Verified capabilities include:

- Revision 0002 migration.
- Restricted PostgreSQL roles.
- Transactional simulated fills and ledger postings.
- Original forecast and market-evidence archiving.
- Independent database reconciliation.
- Backup and restore into a second PostgreSQL cluster.
- Synthetic recovery after interruptions.
- Independent simulated BTCUSDT/ETHUSDT portfolios.
- Operational diagnostics.
- Five-minute cadence rehearsal.

### Performance observations

The 365-day workload included:

- 4,380 decisions.
- 742 simulated fills.
- 105,078 collector journals.
- Concurrent BTC/ETH processing.
- Year-end checked-cycle median approximately 6.43 seconds.
- Year-end checked-cycle p95 approximately 6.59 seconds.
- Full reconciliation approximately 0.19 seconds.

These are local rehearsal measurements, not production-host guarantees.

**Important timing constraint:** the approved quote-use lifetime is only one second after receipt.

Therefore, expensive source discovery, original-evidence verification and full portfolio reconciliation must happen before requesting a perishable execution quote whenever the contract permits.

The implementation must never extend that one-second lifetime to accommodate slow processing.

---

## 3. Implement the prospective financial writer

Create a focused orchestration module, for example:

`src/backtest_badger/paper_writer.py`

Choose the exact module architecture after inspecting the current code.

The writer must reuse the existing deterministic planner, authentication layer, execution primitives and Stage 4C persistence interfaces.

Do not create a second trading engine.

### Core responsibilities

Implement a single-cycle operation that can:

1. Identify the authorised portfolio.
2. Acquire its per-portfolio execution exclusion.
3. Verify current clock health.
4. Recover the existing durable state.
5. Reconcile the original financial evidence.
6. Identify expected forecast horizons and valuation slots.
7. Authenticate original forecast and journal evidence.
8. Evaluate the frozen Ridge Sign v1 strategy.
9. Persist eligible decisions using authenticated archival admission.
10. Record permitted simulated order intents.
11. Obtain a fresh public quote after a committed order submission.
12. Validate the quote, effective filters and all deadlines.
13. Persist a successful simulated fill and paired ledger postings atomically.
14. Persist rejected/expired/failed attempts without financial postings.
15. Preserve unresolved exit obligations.
16. Record valid or missing scheduled valuations.
17. Reconcile the final durable state.
18. Produce a structured cycle result and operational diagnostics.

The writer must be restart-safe and idempotent.

Do not allow a transient process failure to produce duplicate simulated fills.

Do not allow an inconsistent account to continue trading.

---

## 4. Preserve the approved strategy and economics

The prospective reference strategy remains:

**Ridge Sign v1**

Trading universe:

- Binance Spot BTCUSDT.
- Binance Spot ETHUSDT.

Independent starting portfolios:

- 10,000 simulated USDT each.

Trading rule:

- Forecast greater than `1e-12`: target LONG.
- Forecast equal to or below `1e-12`: target CASH.

Other rules:

- No leverage.
- No short selling.
- No forced liquidation every four hours.
- Continuous holdings.
- No automatic trading using late or unattributed forecasts.
- Two consecutive missed horizons trigger risk-off behaviour.
- Sticky exits remain until their financial liquidation succeeds.
- Re-entry requires a new eligible forecast after exit satisfaction.

### Execution policy

Preserve:

- 10 bps fee per side.
- 2 bps adverse slippage per side.
- Buy: observed ask × 1.0002.
- Sell: observed bid × 0.9998.
- Fee rounding upward to 1e-8 USDT.
- Supported market lot/notional constraints.
- All-or-nothing simulated fills.
- Order expiry after 30 seconds.
- Quote request-to-receipt limit of 2 seconds.
- Quote receipt-to-use limit of 1 second.
- Maximum effective filter age of one hour.

Do not add the historical backtest's 1 bp half-spread: the prospective quote already includes the observed spread.

Do not claim that a hypothetical fill was actually executable on Binance.

---

## 5. Separate slow preparation from the perishable quote path

This is a particularly important requirement.

Structure the execution lifecycle so that the expensive work happens before the quote is requested.

### Preparation phase

Perform:

- Database state reconstruction.
- Independent integrity verification.
- Forecast authentication.
- Journal qualification.
- Strategy evaluation.
- Decision archival.
- Market-filter retrieval and validation.
- Filter-source archival.
- Order eligibility checks.
- Atomic order-intent submission.

Only after the SUBMITTED order is durably committed may the execution quote be requested.

### Quote and fill phase

Then:

1. Request a new public `bookTicker` quotation.
2. Capture actual request and response timestamps.
3. Validate the original response and monotonic duration.
4. Check market identity and displayed liquidity.
5. Validate the current account and committed order.
6. Apply the existing simulation rules.
7. Commit the quote and resulting fill evidence using the approved persistence contract.
8. Confirm final ledger consistency.

Keep this critical section small.

Avoid rereading entire forecast archives or performing unrelated expensive work after receiving the quote.

### Freshness failures

If database contention or another delay causes the quote to exceed the approved freshness limit:

- Do not fill.
- Record the correct rejection/expiry evidence.
- Preserve the original portfolio balance.
- Preserve any outstanding sticky exit.
- Allow a later eligible exit attempt with a new quote.

Do not backdate the fill to make the quote appear valid.

Do not silently increase the allowed one-second age.

### Timing benchmark

Measure the exact interval from quote receipt to the financially effective operation under:

- No contention.
- Typical history.
- One-year history.
- Simultaneous BTC/ETH cycles.
- Competing valuation operation.
- Contended portfolio lock.
- Deliberately slow database response.

If the implementation cannot satisfy the approved freshness contract under reasonable staging loads, mark the release blocked and propose an engineering correction.

Do not weaken the contract.

---

## 6. Recovery and idempotency

The writer must handle the following durable states correctly.

### Submitted order after restart

A submitted order is not proof of a fill.

Recover its original identity and expiry.

A restarted process must not use a quote obtained by the previous invocation.

If the order has expired, record expiry at the actual discovery time.

### Quote observed before crash

The original quote is retained as evidence.

It must not be reused as a fresh fill after restart.

The interrupted attempt must be terminalised according to the approved policy.

### Fill committed before crash

Recover the existing fill, postings and account high-water sequence.

Do not post the same trade again.

### Unresolved sticky exit

Retain the obligation across:

- Rejection.
- Expiry.
- Quote failure.
- Worker restart.
- Later positive Ridge forecasts.

A later eligible cycle may create one new exit attempt with a distinct identity and genuinely fresh quote.

Respect the approved five-minute retry spacing.

### Failed buy

Do not repeatedly buy from the same old positive forecast.

Wait for a newly eligible forecast.

### Integrity failure

Any inconsistency involving source evidence, balances, paired postings, timestamps, order status or portfolio identity must fail closed.

Do not automatically reconstruct missing evidence or repair the account.

---

## 7. Durable decisions and original evidence

The authenticated source archive implemented in Stage 4D.2 is mandatory for prospective economic writes.

Use its existing admission functions.

Before committing a forecast-driven decision:

- Validate the original Stage 3 record.
- Validate the exact automation journal snapshot.
- Preserve the original bytes privately.
- Verify their hashes.
- Validate the configured model recipe.
- Confirm eligibility at actual discovery time.
- Record the immutable decision identity and evidence references.

A changed or missing journal must never silently create an eligible trading signal.

For order attempts, retain the original filter evidence and pre-intent timing information.

For quotes, retain exact original bytes, hash, source URL and actual timestamps.

An archival failure must prevent any economic operation that depends on that evidence.

Keep private source evidence outside the website, public R2 objects and release directories.

---

## 8. Portfolio marks and missingness

Use the existing approved valuation schedule:

- 00:10.
- 04:10.
- 08:10.
- 12:10.
- 16:10.
- 20:10 UTC.

Each has a five-minute capture window.

A successful mark must use:

- A genuinely fresh observed quote.
- The original bid.
- An immutable quote identity.
- The portfolio's exact committed ledger prefix.
- The approved valuation policy.

A mark is not a trade.

A missing mark must remain explicitly missing.

Do not substitute an earlier or later price.

Do not backfill outages with retrospective market data.

If a mark and fill compete, PostgreSQL must establish a coherent serial ordering.

The original mark must remain reproducible after subsequent trades.

---

## 9. Production-safe process design

Prepare the writer for a future restricted systemd oneshot service.

Use the intended five-minute cadence, but do not install or enable a service in this stage.

### Isolation

The eventual writer will use:

- A dedicated restricted operating-system identity.
- Restricted PostgreSQL credentials.
- Read-only Stage 3 evidence roots.
- Private original-evidence storage.
- Explicit allowed public Binance hosts.
- No exchange-account credentials.
- No Cloudflare credentials.
- No access to production website deployment secrets.

### Default safety

Keep the existing safe proposal CLI unchanged.

A normal invocation must not suddenly start writing portfolio economics.

The new financial writer must require an explicit operational mode and reviewed configuration.

Do not build an accidental live activation path into the default `paper_worker` command.

### Lifecycle

Prepare the single-cycle program to support:

- Fresh process-run identity.
- Bounded execution time.
- Per-portfolio exclusion.
- Controlled cancellation.
- Safe restart.
- Structured exit code.
- Restricted credentials.
- Clock-health prerequisite.
- Source-health checks.
- Provider cooldown.
- Structured event logging.
- No overlapping financial execution.

Implement a separate local/staging entry point as appropriate.

Do not silently discover production credentials from unrelated environment settings.

---

## 10. Benchmarks and reliability tests

Run genuine PostgreSQL 17 integration tests using fabricated evidence.

Test:

- Positive forecast while flat.
- Positive forecast while long.
- Negative forecast while long.
- Negative forecast while flat.
- Valid buy.
- Valid sell.
- Rejected buy.
- Rejected sell.
- Expired order.
- Missing quote.
- Stale quote.
- Insufficient best-level liquidity.
- Unsupported filters.
- Quote acquired before order submission.
- Quote from an earlier process.
- One missed horizon.
- Two consecutive missed horizons.
- Sticky exit across restart.
- Failed exit retry.
- Filled exit.
- Re-entry using a new eligible forecast.
- Missing valuation.
- Mark/fill concurrency.
- Duplicate worker invocation.
- Duplicate forecast.
- Duplicate order intent.
- Duplicate fill.
- Corrupted journal.
- Missing original forecast.
- Original-evidence archival failure.
- Clock uncertainty.
- Provider 418/429.
- Database lock timeout.
- Worker termination.
- Uncertain commit outcome.
- Recovery after an interrupted transaction.

### Failpoint testing

Inject controlled failures:

- Before decision commit.
- After decision commit.
- Before order submission.
- After order submission.
- Before quote request.
- After quote receipt.
- After quote evidence persistence.
- During fill transaction.
- After fill commit but before response acknowledgement.
- During mark recording.
- During worker shutdown.

For every failure, inspect the actual database state.

There must be no duplicate trades, orphan ledger postings, phantom fills, lost sticky exits or invented historical marks.

### Full fabricated lifecycle

Rehearse both markets independently:

1. Funding and valid fabricated inception.
2. Positive forecasts.
3. Simulated entries.
4. Continuous holdings.
5. Marked equity.
6. Negative forecasts.
7. Failed exits.
8. Process restart.
9. New eligible exit attempts.
10. Liquidation.
11. Independent reconciliation.
12. Backup and restore verification.

All activity must be labelled fabricated.

No genuine market observations should create an economic account history during testing.

---

## 11. Clock, provider and performance gates

Stage 4D.2 identified the following operational limits.

The future host must have verified UTC synchronisation.

The proposed operational clock gate uses:

- A trustworthy synchronisation observation no older than five minutes.
- Measured uncertainty at most 100 milliseconds.

Treat those as readiness requirements, not evidence that the existing host already meets them.

A local monotonic clock does not prove external UTC accuracy.

The writer must fail closed when current-time accuracy cannot be established.

### Performance

Measure:

- Forecast discovery duration.
- Reconciliation time.
- Order preparation time.
- Submission commit time.
- Quote HTTP latency.
- Quote receipt-to-fill duration.
- Quote rejection frequency.
- Database lock waiting.
- Runtime memory.
- Overall cycle duration.
- Recovery duration after interruption.

Repeat relevant tests with representative one-year fabricated histories.

Separately report quote-path timings and whole-cycle timings.

The one-second quote-use requirement is not met merely because the overall cycle finishes in less than five minutes.

Keep the existing Stage 4A economic parameters fixed.

---

## 12. Operational diagnostics

Reuse the Stage 4D.2 incident taxonomy.

Provide structured reporting for:

- Missing forecast.
- Late forecast.
- Unqualified automation evidence.
- Missing or conflicting originals.
- Quote failure.
- Provider throttling.
- Stale filter evidence.
- Clock uncertainty.
- Database contention.
- Order rejection or expiry.
- Outstanding exit obligation.
- Blocked dust.
- Missing mark.
- Failed reconciliation.
- Failed backup.
- Interrupted worker.
- Cycle overlap.

Deduplicate equivalent incidents using stable identifiers.

Separate ordinary missingness from warnings and critical integrity incidents.

Critical integrity failures must stop economic execution for the affected portfolio.

Do not add external alert delivery credentials or production notification configuration at this stage.

---

## 13. Deployment and activation boundaries

This stage must not access or modify the production Lightsail environment.

Do not:

- SSH into the production host.
- Change the production database.
- Apply Alembic migration 0002 to production.
- Install the worker service.
- Start any background trading timer.
- Create genuine BTC/ETH paper portfolios.
- Fund genuine simulated portfolios.
- Activate prospective evaluation.
- Modify production backups.
- Change database roles.
- Change clock synchronisation settings.
- Modify the live forward collector or scorer.
- Change the Cloudflare website.
- Change R2 feeds.
- Place actual Binance orders.
- Create exchange trading credentials.
- Publish paper portfolio performance.
- Change existing scientific protocols.

This task authorises only local implementation, fabricated test data, isolated databases, verification, documentation, commit and push.

No live paper trading may begin automatically when the code is pushed.

### Production handoff

Prepare the exact future release requirements, including:

- Verified release SHA.
- Actual Lightsail deployment inspection.
- Actual production PostgreSQL revision.
- Production backup baseline.
- Reviewed migration.
- Restricted database roles.
- Private evidence directories.
- Worker runtime identity.
- Network and clock requirements.
- Memory and CPU headroom.
- Monitoring.
- Kill switch.
- Forward-recovery procedure.
- Per-market activation approvals.

Do not assume that GitHub main matches the currently deployed Lightsail release.

---

## 14. Documentation

Create:

`docs/stage-04d3a-production-writer.md`

Include:

- Implementation architecture.
- Starting and final Git commits.
- Writer interfaces.
- Exact decision-to-fill transaction lifecycle.
- Provenance and archival admission.
- Perishable quote timing.
- Failure and recovery matrix.
- Sticky exit handling.
- Valuation scheduling.
- Clock and provider safeguards.
- PostgreSQL concurrency results.
- Benchmark results.
- Known limitations.
- Test evidence.
- Changed-file inventory.
- Production deployment prerequisites.
- Explicit remaining approval gates.

Update:

- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- `README.md`
- `prompts/README.md`

Archive this prompt at:

`prompts/stage-04-paper/stage-04d3a-production-writer.md`

Preserve all approved scientific evidence, original strategies, Stage 4A protocols and existing Stage 3 outputs.

---

## 15. Validation and GitHub

Run:

- Appropriate full pytest suite.
- Actual PostgreSQL integration tests.
- Existing Stage 4B.1 accounting regressions.
- Stage 4C persistence regressions.
- Stage 4D.1 authentication and planner regressions.
- Stage 4D.2 backup, restore and security regressions.
- Isolated guarded historical runners.
- Ruff lint and formatting.
- Wheel build and import checks.
- Git whitespace checks.

Follow the documented macOS scratch-directory setup to avoid unrelated ownership and fixture-cleanup failures.

Do not claim that skipped tests passed.

Do not rerun genuine historical economic experiments.

After successful verification:

1. Review the full diff.
2. Confirm no private evidence or secrets are staged.
3. Confirm frozen scientific hashes are unchanged.
4. Commit and push the verified implementation to main.
5. Confirm both GitHub workflows pass for the exact final SHA.

Suggested commit:

`feat(paper): implement prospective simulated writer`

If mandatory correctness or timing tests remain blocked, report the blocker rather than declaring readiness.

Do not deploy anything to Lightsail.

Do not promote a Cloudflare candidate.

---

## 16. Completion report

Provide:

1. Starting commit.
2. Final commit.
3. Changed modules and files.
4. Writer execution architecture.
5. Original-evidence admission guarantees.
6. Decision and order persistence sequence.
7. Quote timing and freshness benchmark.
8. Atomic fill and ledger evidence.
9. Restart/idempotency results.
10. Sticky exit and missingness behaviour.
11. Valuation integrity.
12. Concurrent worker tests.
13. Full fabricated lifecycle results.
14. Backup/restore compatibility.
15. Unit and integration test totals.
16. Exact-commit GitHub CI results.
17. Known blockers.
18. Required production-host checks.
19. Deployment and kill-switch plan.
20. Recommended Stage 4D.3B steps.

End with one explicit verdict:

- READY FOR SEPARATE PRODUCTION DEPLOYMENT REVIEW
- READY WITH CONDITIONS
- BLOCKED

### Definition of success

Stage 4D.3A is successful when the writer can perform an entire genuine-format but fabricated simulated-trading lifecycle, using restricted PostgreSQL access and original-source evidence, with correct financial accounting, reproducible marks and safe recovery under failures.

All mandatory freshness, chronology, idempotency and integrity tests must pass.

**No actual prospective portfolio is created or activated during this stage.**

The completed writer remains inactive until separately approved production deployment and individual BTC/ETH activation decisions.
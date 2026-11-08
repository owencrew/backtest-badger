# Backtest Badger — Stage 4D.2: Production Readiness and Isolated Paper-Trading Rehearsal

## Objective

Prepare Backtest Badger's prospective paper-trading system for a future, separately authorised production activation.

Stages 4B.1, 4C and 4D.1 have established:

- Deterministic Ridge Sign v1 trading and accounting.
- Durable PostgreSQL persistence with atomic fills.
- Independent portfolio reconciliation and crash recovery.
- Authenticated original Stage 3 forecast provenance.
- Public Binance quote and exchange-filter validation.
- A safe, single-cycle, non-writing proposal worker.
- Fabricated end-to-end trading lifecycle verification.

Stage 4D.2 must test whether these components can operate safely, reliably and recoverably in a production-like environment.

**This is a production-readiness and isolated-rehearsal milestone, not permission to deploy or activate prospective trading.**

The goal is to produce a verified operational implementation, a tested deployment and recovery plan, and a clear list of remaining approval gates before Stage 4D.3.

Do not modify the existing live collectors, scorers, website, forward feeds or production database.

---

## 1. Starting context

Repository: `~/Code/backtest-badger`

GitHub: `owencrew/backtest-badger`

Expected starting commit:

`ed557d7759672fc84e24b4c54ff7d37dde539ac2`

Both GitHub workflows passed for this commit.

Verify HEAD, working-tree status and CI. Inspect newer commits if present; do not reset them.

Read:

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- `docs/stage-04a-paper-trading-spec.md`
- `docs/stage-04a-prospective-evaluation-protocol.md`
- `docs/stage-04b1-deterministic-paper-primitives.md`
- `docs/stage-04c-paper-trading-persistence.md`
- `docs/stage-04d1-prospective-integration.md`
- `docs/deployment/production-infrastructure.md`

Inspect all paper-related Python modules, both Alembic revisions, the SQL constraints and triggers, current PostgreSQL test fixtures, backup tooling, release scripts and GitHub CI configuration.

Treat the approved Stage 4A specification as the authoritative prospective economic contract.

Do not revise scientific or execution parameters to make production implementation easier.

---

## 2. Required stage boundaries

Stage 4D.2 authorises:

- Local development.
- Disposable PostgreSQL 17 testing.
- Isolated operational rehearsal.
- Synthetic long-duration workloads.
- Security and database permission testing.
- Backup and restore rehearsal.
- Readiness diagnostics.
- Documentation and deployment planning.
- Commit, push and exact-commit CI verification.

It does not authorise:

- Production SSH access or changes.
- Production Alembic migrations.
- Production PostgreSQL role changes.
- Deployment to Lightsail.
- Installation or activation of systemd services/timers.
- Genuine portfolio creation or funding.
- Production paper-trading writes.
- Real trading or exchange order submission.
- Modification of existing R2 or Cloudflare services.
- Changes to live forecast collection or scoring.
- Automatic website deployment or promotion.

Use existing locally retained materials and fabricated evidence.

If production-specific facts cannot be established without inspecting the live host, label them as **pending production verification** instead of assuming older documentation is current.

---

## 3. Phase A — Operational architecture and readiness inventory

Inspect how the completed modules would integrate into the existing Lightsail environment.

Document the intended architecture:

Stage 3 collector → original forecasts and automation journals → authenticated paper reader → Ridge policy → simulated intent → current public quote/filter evidence → Stage 4C transactional ledger → immutable valuation evidence.

Identify:

- Filesystem read/write boundaries.
- Database permissions.
- Worker process identity.
- Forecast discovery paths.
- Original evidence retention.
- Clock dependencies.
- Network dependencies.
- Failure recovery.
- Backup dependencies.
- Monitoring requirements.
- Production resource limits.
- Rollback and forward-recovery procedures.

Distinguish already implemented behaviour from functionality still required for Stage 4D.3.

Do not claim that the current proposal worker is already a production financial writer.

---

## 4. Phase B — Reconciliation and runtime performance

Stage 4C currently reconstructs financial state from durable evidence.

Its integrity guarantees are valuable, but full-history reconciliation may become expensive as portfolios accumulate events.

Build an isolated performance benchmark using synthetic data and real PostgreSQL.

### Test workloads

Create representative fabricated event histories for:

- 30 days.
- 90 days.
- 180 days.
- 365 days.

Include separate BTC and ETH portfolios.

Use the approved four-hour forecast and valuation schedule, including realistic quantities of:

- Forecast decisions.
- No-op decisions.
- Quotes.
- Modelled fills.
- Order failures.
- Scheduled observed marks.
- Missing marks.
- Unresolved exit obligations.

The workloads should be representative rather than constructed solely to make benchmarks fast.

Include an adverse case with repeated rejected exit attempts and a long event history.

### Measure

- Median and p95 cycle duration.
- Worst observed cycle duration.
- Database lock waiting.
- Reconciliation time.
- Ledger reconstruction time.
- Historical valuation reconstruction time.
- Forecast/journal discovery time.
- Database query counts.
- Process peak memory.
- CPU and disk activity.
- Database size growth.
- Concurrent portfolio processing.
- Concurrent fill/mark interactions.

Record the workload sizes and machine environment.

Compare results with the existing three-second lock timeout, ten-second statement timeout and intended five-minute worker schedule.

Determine whether full reconciliation remains practical.

If necessary, implement narrowly scoped, verified optimisations that preserve the authoritative immutable ledger and independent integrity checks.

Do not introduce an unverified mutable balance cache as a replacement for the ledger.

Never weaken database integrity to improve performance.

---

## 5. Phase C — Least-privilege PostgreSQL security

Stage 4C was validated using disposable databases with broad test permissions.

Rehearse a production-like role model with separate identities.

### Required roles

**Migration administrator**

Can perform authorised DDL and migration maintenance, but should not be used by the recurring worker.

**Portfolio inception operator**

Can carry out only the approved creation/funding/inception actions.

**Paper worker**

Can read required evidence and perform specifically authorised operational writes.

**Reporting reader**

Read-only access to approved portfolio, ledger and event data.

The recurring worker must not own database tables, disable triggers, create schemas, modify roles, truncate records or rewrite historical evidence.

### Requirements

Use disposable PostgreSQL 17 databases.

Create and test the exact grants required by the existing persistence interfaces.

Review:

- Schema USAGE.
- Table SELECT.
- Evidence INSERT.
- Restricted projection UPDATE.
- Sequence permissions where applicable.
- Function EXECUTE permissions.
- Ownership of trigger functions.
- SECURITY DEFINER usage, if any.
- Function search paths.
- Public/default privileges.
- Role inheritance.
- Permissions on existing market tables.

Ensure that granting the worker access to a trigger or helper function does not create a privilege-escalation path.

### Negative tests

The paper worker must be unable to:

- Disable constraints or triggers.
- Change original forecast evidence.
- Update ledger entries.
- Delete or truncate economic evidence.
- Modify a portfolio's frozen configuration.
- Modify another role's permissions.
- Create unexpected database objects.
- Perform migration administration.

Verify that legitimate simulated transactions still succeed under the restricted role.

Do not silently rely on PostgreSQL superuser privileges.

Document proposed grants and revocation procedures, but do not create production roles.

---

## 6. Phase D — Migration and recovery rehearsal

Current known migration sequence:

- `0001` — Market-data schema.
- `0002` — Paper-trading persistence.

Rehearse the upgrade from `0001` to `0002` in an isolated PostgreSQL 17 environment.

### Migration validation

Use an existing disposable baseline or create one with synthetic pre-existing market data.

Verify:

1. Existing market data survive unchanged.
2. Revision 0002 creates all five paper tables.
3. All expected indexes, constraints and triggers exist.
4. Original ingestion functionality remains operational.
5. Forward collection/scoring database access remains compatible.
6. A failed migration rolls back appropriately.
7. Fresh installation reaches the correct schema.
8. Empty downgrade remains possible under the approved safeguards.
9. Populated economic evidence cannot be destroyed by an ordinary downgrade.
10. Recovery after migration failure is documented and tested.

Produce a deployment plan specifying the future production checks, backup gate and migration command sequence, but do not execute it on the actual production host.

### Forward recovery

Once genuine paper evidence exists, automatic downgrade to revision 0001 must not be treated as a safe rollback.

Document how the operator would instead stop the new worker, preserve the paper tables, restore application compatibility or perform a specifically reviewed forward repair.

Never recommend dropping populated paper tables merely to restore an earlier code version.

---

## 7. Phase E — Portfolio inception constraint

Stage 4D.1 identified an important schema limitation:

**Revision 0002 requires portfolio inception within the scheduled valuation mark capture window.**

The approved valuation schedule is:

- 00:10
- 04:10
- 08:10
- 12:10
- 16:10
- 20:10 UTC

Each mark has a five-minute capture window.

Review the implementation against the Stage 4A prospective protocol.

Develop an explicit, auditable activation procedure that:

- Creates the independently configured portfolio cohort.
- Funds it exactly once.
- Captures a genuinely current original quote.
- Records the eligible observed inception mark.
- Activates only after the required evidence commits.
- Uses actual timestamps, never backdated timestamps.
- Handles unavailable quotes and missed activation windows.
- Cannot begin an experiment with invented historical positions.
- Does not activate BTC and ETH accidentally as a pooled account.

Prefer working within the approved scheduled-inception mechanism if it satisfies the protocol.

Do not change revision 0002 or the prospective methodology merely to permit arbitrary-time activation.

If the current schema makes a compliant inception impossible, document the exact conflict, propose the smallest separately reviewable correction and mark activation readiness blocked.

Test the proposed sequence only with fabricated evidence and disposable databases.

No actual prospective portfolios may be created.

---

## 8. Phase F — Original evidence retention and provenance

The authenticated paper system depends on original source evidence remaining available after a restart or restore.

Original Stage 3 forecast records may be retained immutably, but operational journal snapshots can change as a collection cycle finishes.

A referenced SHA-256 is insufficient if its corresponding original bytes are lost.

### Required design

Create or extend a private, content-addressed evidence-retention mechanism covering:

- Original forecast bytes.
- The exact automation journal snapshot used for qualification.
- Original journal SHA-256.
- The original Ridge prediction identity.
- Model recipe fingerprint.
- Original quote bytes.
- Original exchangeInfo/filter bytes.
- Applicable policy and implementation fingerprints.
- Original observation and decision timestamps.

The retained evidence must be independently recoverable.

Do not modify Stage 3's original journal publication mechanism unless a separately justified compatibility change is essential.

### Atomicity

Exercise interruption points such as:

- Forecast exists but journal has not appeared.
- Journal initially indicates a running operation.
- Journal snapshot changes between discovery and decision.
- Original evidence has been retained but decision not committed.
- Decision committed but order not submitted.
- Order submitted but quote not acquired.
- Quote acquired but fill not committed.
- Evidence retention fails.
- Process restarts between any two steps.

Determine precisely when private source-evidence archival must be completed relative to a durable paper decision.

If the necessary evidence cannot be retained and verified, fail closed instead of creating a durable decision whose source cannot later be reconstructed.

### Restore testing

Restore a complete fabricated portfolio into a second isolated environment with the original source evidence.

Verify that:

- Original hashes match.
- Forecast automation qualification can be reproduced.
- Decisions reference available originals.
- Quotes and filters reconcile.
- Ledger entries reconstruct exactly.
- Historical marks remain unchanged.
- Outstanding exit obligations remain identifiable.
- Missing original bytes produce an explicit integrity failure.

Keep original sources immutable and separate from public website/R2 presentation data.

---

## 9. Phase G — Backup and disaster recovery

Extend the rehearsal tooling to demonstrate that the planned operational backups would protect Stage 4C's new schema and all required original evidence.

Do not modify the production backup schedule.

Use disposable PostgreSQL, temporary storage and test-only credentials.

### Backup coverage

Include:

- All five paper tables.
- Required indexes and triggers.
- Schema migration identity.
- Portfolio configurations.
- Financial ledger.
- Decisions and orders.
- Quote/fill evidence.
- Valuation marks.
- Original forecast/journal evidence.
- Original filter-source evidence.
- Relevant configuration and code fingerprints.

### Restore verification

Perform an independent isolated restore.

Compare:

- Table and row identities.
- Schema fingerprints.
- Trigger and permission definitions.
- Ledger high-water sequences.
- Balances and holdings.
- Realised P&L.
- Pending exit obligations.
- Historical marked equity.
- Missing mark identities.
- Source artifact hashes.

Test corruption and missing-file detection.

Rehearse interrupted backups and incomplete snapshots.

A restored database must not silently create economic observations that did not exist in the backup.

### Operational runbook

Document the future production backup/restore changes needed once permission is granted.

Clearly distinguish those proposed changes from the currently installed Lightsail backup process.

Do not access or modify production S3/restic resources.

---

## 10. Phase H — Worker isolation and scheduling rehearsal

Design the eventual Lightsail paper worker as a separate, restricted process.

It should not run inside the existing forecast collector or scoring worker.

### Planned schedule

Use the approved five-minute worker cadence.

Rehearse it in isolated staging using fabricated evidence and a controlled clock.

Test:

- Normal cycle completion.
- Overlapping invocation.
- Process termination.
- Slow provider response.
- Database lock timeout.
- Missing forecast.
- Delayed automation journal.
- Missing quote.
- Unsupported filter.
- Missed mark.
- Rejected order.
- Pending sticky exit.
- Worker restart.
- Interrupted transaction.
- Host clock uncertainty.
- Repeated failed cycles.

Ensure a cycle can never spend twice because the previous invocation has not finished.

Use database-level idempotency and the existing per-portfolio locking guarantees.

A simulated current-time quote must not be represented as a fill without the correct previously committed intent.

### Worker security

Prepare the future configuration and service design covering:

- Separate system identity.
- Restricted filesystem paths.
- Read-only forecast access.
- Dedicated private evidence storage.
- Restricted database credentials.
- Public-only HTTPS network destinations.
- Resource and runtime limits.
- Single-cycle execution.
- Clear exit status.
- Structured logging.
- Process restart behaviour.

Service templates may be created for review, but **must not be installed or enabled**.

Do not run a background trading scheduler on the developer machine or Lightsail.

---

## 11. Phase I — Monitoring and alerts

Define and test operational diagnostics for prospective paper trading.

Required incident categories include:

- Missing expected forecast.
- Forecast discovered after deadline.
- Invalid original automation evidence.
- Journal/source inconsistency.
- Quote request failure.
- Provider 418/429.
- Stale or unsupported filters.
- Clock synchronisation uncertainty.
- Excessive cycle runtime.
- Database contention.
- Failed reconciliation.
- Pending or ageing exit obligation.
- Repeated failed exit attempts.
- Blocked dust.
- Missing scheduled valuation.
- Backup verification failure.
- Missing original evidence.
- Failed isolated restore.

Each diagnostic should retain enough structured context to investigate the problem without exposing credentials.

Distinguish expected operational missingness from genuine financial-integrity incidents.

Integrity failures should fail closed.

Use fabricated scenarios to verify classification and deduplication of incidents.

Do not configure production SNS, CloudWatch or other alert delivery during this stage.

Document the intended alert destinations and escalation procedure for later approval.

---

## 12. Phase J — End-to-end isolated rehearsal

Conduct an end-to-end rehearsal against a disposable PostgreSQL 17 database using fabricated forward and market evidence.

The rehearsal should include:

1. Migration from revision 0001 to 0002.
2. Creation of restricted database roles.
3. Creation of two independent fabricated portfolios.
4. Correct initial funding.
5. Valid fabricated inception marks.
6. Repeated five-minute cycles.
7. Verified positive/negative Ridge signals.
8. A successful hypothetical buy.
9. Continuous holdings.
10. Observed valuation marks.
11. A missing valuation.
12. An expired or rejected order.
13. A sticky risk exit.
14. Process interruption and restart.
15. Successful subsequent hypothetical liquidation.
16. Independent ledger reconciliation.
17. Complete backup of database and original evidence.
18. Restore into a new isolated environment.
19. Verification of matching financial and source identities.
20. Confirmation that no real system was modified.

Use different portfolio identities for BTC and ETH.

Record complete deterministic test evidence and any failure/retry attempts.

Explicitly label all account values as fabricated.

Do not use live market observations to create simulated economic performance during this rehearsal.

---

## 13. Verification and CI

Run the full applicable test suite, including:

- Stage 3 provenance tests.
- Stage 4B.1 accounting tests.
- Stage 4C database integrity tests.
- Stage 4D.1 adapter and planner tests.
- New Stage 4D.2 security, restore and operational tests.
- Existing frozen historical research regressions.
- Guarded isolated historical suites.
- Ruff lint and formatting.
- Wheel build and import checks.
- Git whitespace checks.

Use genuine PostgreSQL 17 transactions for database tests.

Use a loopback-only disposable server.

Preserve the required macOS scratch-directory configuration documented in Stage 4C.

Test malicious or incorrect input where relevant.

Do not weaken assertions to make tests pass.

If possible, include the new isolated readiness checks in GitHub CI without requiring production credentials or infrastructure.

Do not claim success for skipped tests.

---

## 14. Documentation and deployment handoff

Create:

`docs/stage-04d2-production-readiness.md`

Include:

- Exact starting and final Git commits.
- Architecture and security assessment.
- Performance measurements and limitations.
- PostgreSQL role/grant matrix.
- Migration plan.
- Portfolio inception procedure.
- Immutable evidence retention design.
- Backup coverage and restore results.
- Worker isolation and resource planning.
- Clock and provider-health checks.
- Alert taxonomy.
- Synthetic end-to-end rehearsal evidence.
- Complete testing results.
- Remaining operational blockers.
- Required owner approvals.
- Complete changed-file inventory.

Update relevant architecture, roadmap, README, development handoff and prompt index documentation.

Archive this prompt at:

`prompts/stage-04-paper/stage-04d2-production-readiness.md`

Preserve the approved Stage 4A protocol, existing historical evidence, Stage 4C records and Stage 4D.1 handoff.

Prepare a separate operator-facing production migration and activation checklist, but do not execute it.

---

## 15. Release and GitHub process

This request authorises:

- Local implementation.
- Isolated rehearsal.
- Test-only database operations.
- Documentation.
- Commit and push of the verified code.

After validation:

1. Review the complete diff.
2. Confirm no secrets or private test data are committed.
3. Confirm no scientific results were changed.
4. Confirm no production infrastructure was accessed or modified.
5. Commit the focused changes.
6. Push to `origin/main`.
7. Verify both GitHub workflows for the exact final SHA.

Suggested commit:

`feat(paper): rehearse production readiness and recovery`

If a critical integrity, security or recovery requirement remains unmet, do not falsely describe the stage as complete.

Document the blocker and provide the best partial implementation and test evidence.

Do not automatically deploy anything to Lightsail.

Do not promote any Cloudflare Worker candidate.

No actual portfolio activation is authorised.

---

## 16. Final report and readiness decision

Provide a concise but complete report covering:

1. Starting and final SHA.
2. Changed modules and files.
3. Database role security results.
4. Reconciliation benchmark results.
5. Migration and schema compatibility.
6. Validated portfolio inception procedure.
7. Original evidence archival and crash consistency.
8. Complete backup/restore verification.
9. Worker isolation and scheduling rehearsal.
10. Clock and network operational checks.
11. Monitoring and failure classification.
12. Test counts and GitHub CI status.
13. Any deviations from the approved Stage 4A design.
14. Known performance or operational limitations.
15. Items requiring a production environment inspection.
16. Remaining blockers and required owner authorisations.

Conclude with an explicit readiness status:

- **READY FOR SEPARATE DEPLOYMENT REVIEW**
- **READY WITH CONDITIONS**
- **BLOCKED**

Do not mark a system ready merely because unit tests pass.

The recommendation should account for the successful isolated migration, restricted-role operation, restore, source provenance, recovery, resource benchmarks and activation constraints.

### Definition of success

Stage 4D.2 is successful when the system can be safely rehearsed end to end with fabricated evidence under production-like constraints, and the remaining production actions are understood, documented and independently reviewable.

**No prospective trading begins during this milestone.**

Stage 4D.3 will require separate owner approval for the production migration/deployment, and an additional explicit activation decision for each genuine BTC and ETH simulated portfolio.
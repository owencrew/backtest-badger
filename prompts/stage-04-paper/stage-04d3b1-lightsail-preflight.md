# Backtest Badger — Stage 4D.3B.1: Lightsail Production Preflight and Deployment Preparation

## Objective

Prepare the verified prospective paper-trading system for a controlled deployment to the existing AWS Lightsail environment.

Stage 4D.3A has completed implementation and local validation of the financial writer.

The next task is to establish the actual state of the production environment, identify deployment incompatibilities, prepare safe production configuration and operational tooling, and produce an evidence-based deployment plan.

**This milestone must not activate paper trading or apply production changes.**

Read-only production inspection is permitted only after direct, explicit owner approval in the Codex chat.

All implementation changes and rehearsal tests must otherwise remain local or in disposable environments.

## 1. Starting context

Repository:

`~/Code/backtest-badger`

GitHub:

`owencrew/backtest-badger`

Expected starting commit:

`93c9a4f0d70dccb65ec80bf03097c71351d5a224`

Both GitHub workflows passed for this exact SHA.

Verify current HEAD, clean working tree and workflow results before editing.

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
- `docs/stage-04d3a-production-writer.md`
- `docs/deployment/paper-migration-activation-checklist.md`
- `docs/deployment/production-infrastructure.md`

Inspect all writer, persistence, archival, clock, checkpoint, monitoring and deployment modules.

Preserve the approved Stage 4A scientific protocol.

## 2. Verified Stage 4D.3A implementation

The latest committed writer passed:

- 3,351 full-suite tests, with 88 skips addressed through the documented guarded procedures where applicable.
- 274 PostgreSQL integration tests.
- All 11 process-kill scenarios.
- Independent simulated BTC/ETH account recovery and restore.
- Concurrent quote-admission tests.
- Deliberately stale-quote rejection tests.
- Exact scientific source-hash verification.

In the one-year fabricated workload, the maximum measured quote receipt-to-backend admission was approximately 23.17 ms.

The approved limit is 1,000 ms.

Do not assume these local results establish production latency.

Do not change the approved economic parameters or extend quote freshness deadlines.

## 3. Explicit approval boundary

Before accessing the production Lightsail host, ask for direct confirmation:

"May I perform a read-only inspection of the existing Backtest Badger Lightsail host to establish the actual deployment, database, service, resource and backup state? I will not modify production."

Only proceed with production inspection after that approval.

Read-only inspection must not alter services, configuration, database records, credentials, schedules, backups or deployment versions.

If access is unavailable or approval is not granted, complete the local deployment preparation and document all unverified assumptions.

Do not treat lack of host access as permission to infer current production details from historical documentation.

### Prohibited without separate subsequent approval

- Applying Alembic 0002 to production.
- Creating database users or changing privileges.
- Writing production environment files.
- Installing new packages or services.
- Changing systemd timers.
- Changing existing production releases.
- Changing production backup or monitoring services.
- Writing to production portfolio tables.
- Creating genuine paper portfolios.
- Activating the trading worker.

## 4. Production host inventory

After explicit inspection approval, establish the actual host state.

Inspect:

- Current immutable release SHA.
- Current application directory and deployment mechanism.
- Python runtime and dependency versions.
- PostgreSQL version and Alembic revision.
- Database identity and persistent Docker volume.
- Existing systemd service and timer definitions.
- Stage 3 collector and scorer health.
- Existing original forecast and journal paths.
- Current forecast publication cadence.
- Current host clock synchronisation.
- CPU and memory capacity.
- Disk usage and filesystem permissions.
- Existing backup and restore processes.
- Latest backup completion receipt.
- Latest independently verified restore.
- Alert delivery configuration and health.
- Existing operational locks and worker approval gates.

Use read-only commands.

Avoid printing, downloading or recording passwords, private keys, tokens, database DSNs or confidential environment values.

Do not disclose credentials in logs or GitHub.

Compare the current observations with the existing dated infrastructure report.

Document every meaningful discrepancy.

## 5. Production entry-point design

The current writer staging CLI deliberately requires:

- A database named `badger_test_<32 hex>`.
- A loopback PostgreSQL connection.
- An explicit `staging-once` mode.
- Fabricated test portfolios.

These safeguards must remain intact.

Do not weaken `staging-once`.

Instead, design a separate, reviewed production-capable entry point.

Requirements:

- Explicit production mode and configuration.
- Exact approved production database identity.
- Restricted worker credentials.
- Fixed allowed portfolio identity and market.
- Approved configuration fingerprint.
- Explicit release SHA.
- Private evidence and runtime paths.
- Read-only original forecast and journal roots.
- External trusted clock-health observation.
- Current provider-health validation.
- Five-minute single-cycle semantics.
- No automatic portfolio creation or funding.
- No default activation.
- No real exchange order transport.
- No automatic production database connection in ordinary development commands.

Prepare the implementation and synthetic tests locally.

The production entry point must refuse economic writes unless its separately approved installation and activation gates are satisfied.

Require positive proof of the approved runtime identity and portfolio state. Do not rely merely on the presence of environment variables.

Document the exact trust boundaries and how authorisation is verified.

The staged implementation must not allow a developer to accidentally target the live database.

## 6. Production service design

Prepare a dedicated restricted systemd oneshot service and timer configuration.

Do not install or enable them.

Use the existing recommendations where appropriate:

- Separate `badger-paper` Unix identity.
- `NoNewPrivileges=true`.
- `ProtectSystem=strict`.
- `ProtectHome=true`.
- `PrivateTmp=true`.
- Restricted writable directories.
- Read-only source mounts.
- Minimal Linux capabilities.
- Restricted address families.
- Fixed public Binance API host.
- Explicit database credentials.
- A 240-second runtime limit.
- Five-minute schedule with catch-up disabled.
- No overlapping execution.
- Safe SIGTERM handling.
- Structured incident logging.

Ensure the proposed sandbox can genuinely read the forecast roots, access the private archive and connect to the approved PostgreSQL endpoint.

Confirm that the service does not inherit collector, scoring, deployment, S3 or Cloudflare credentials.

Prepare an explicit disabled-by-default installation state.

No portfolio activation or scheduling is authorised in this milestone.

## 7. PostgreSQL production migration plan

The prospective trading schema is Alembic revision `0002`.

Inspect production's actual current revision if read-only host inspection has been approved.

Prepare the reviewed migration sequence.

Before a future migration, require:

1. A verified immutable release.
2. Actual database identity confirmation.
3. A recent successful encrypted backup.
4. An independent restore.
5. A maintenance window.
6. Reviewed migration ownership.
7. Correct role configuration.
8. Collector/scorer compatibility.
9. Documented forward-recovery procedure.

Rehearse any changed SQL against a disposable database or isolated restored copy.

The production migration must not run in this milestone.

If the schema is already at a different revision, do not guess or force an upgrade.

Produce a blocker report.

## 8. Restricted role installation plan

Use the Stage 4D.2 grant design as the starting point.

Required identities:

- Migration owner.
- Portfolio inception operator.
- Restricted paper worker.
- Reporting reader.
- Existing collector and scorer identities.

Review the actual production privilege dependencies before proposing changes.

Pay particular attention to:

- PUBLIC grants.
- Existing collector/scorer privileges.
- SECURITY DEFINER functions.
- Search paths.
- Large-object function access.
- Row-level security.
- Schema ownership.
- Trigger ownership.
- Database connection restrictions.

Test the proposed role changes on an isolated copy.

Do not alter production roles.

Ensure the worker cannot create/fund portfolios, rewrite evidence, bypass constraints or perform administration.

## 9. Backup and independent restoration

The existing operational backup process predates the five new paper tables.

Design the necessary extension so that future backups include:

- All nine application tables.
- Alembic revision.
- Schema and trigger definitions.
- Restricted-role configuration.
- Financial ledgers.
- Orders and decisions.
- Quote and valuation events.
- Original forecast and journal evidence.
- Original filter-response evidence.
- Private evidence archive.
- Operational runtime and incident records.
- Required policy and implementation fingerprints.

Rehearse the extended backup and restore locally or against a separately authorised isolated environment.

Verify that PostgreSQL and source evidence restore to one consistent checkpoint.

The original evidence archive must not be treated as disposable.

Record measured restore time and the potential recovery-point gap.

Do not change live backup schedules or S3 storage during this milestone.

## 10. Clock and market access

Inspect the proposed production clock gate.

The current policy requires a verified external synchronisation sample:

- No older than five minutes.
- Uncertainty no greater than 100 milliseconds.

Prepare a safe, independently controlled clock-observation mechanism.

Do not manufacture or manually timestamp a healthy clock sample.

A worker must fail closed if the clock cannot be trusted.

Review public Binance API access from the proposed process environment.

The writer should use only the approved unsigned market-data endpoints.

No exchange API keys or order endpoints are required.

If read-only host inspection is authorised, bounded public endpoint and TLS/DNS diagnostics may be performed only with separate explicit approval for those network requests. Do not issue repeated polling requests.

## 11. On-host performance and resource plan

The earlier local workload used a much larger development machine than the last recorded Lightsail specification.

Plan realistic capacity verification.

Assess:

- Cold process startup.
- Forecast/journal discovery.
- Full portfolio reconciliation.
- Original evidence archival.
- PostgreSQL lock waiting.
- Filter retrieval.
- Quote request and response latency.
- Quote receipt-to-admission.
- Commit acknowledgement.
- Memory and CPU peaks.
- Disk/WAL activity.
- Simultaneous BTC and ETH processing.
- Contention with the existing collector and scorer.
- Backup and restore activity.

Any actual on-host benchmark must be separately authorised and use fabricated data in an isolated database.

Do not create synthetic portfolio records in production.

Keep the quote receipt-to-use limit at one second.

Treat failures under representative load as release blockers rather than relaxing the approved policy.

## 12. Operational monitoring and kill switch

Prepare the operational monitoring architecture.

Required incident coverage:

- Missing forecast.
- Late or unqualified forecast.
- Conflicting journal.
- Missing original bytes.
- Provider 418/429.
- Stale quote or filters.
- Missed valuation.
- Database contention.
- Failed reconciliation.
- Worker silence.
- Unresolved exit.
- Repeated rejected exit.
- Blocked dust.
- Clock uncertainty.
- Failed backup.
- Failed isolated restore.

Provide a monitoring-health checklist and sample structured incident output.

Do not configure production alerting yet.

Prepare a documented kill switch that can:

1. Disable the paper timer.
2. Stop the paper service.
3. Revoke the worker database login.
4. Terminate outstanding worker sessions if authorised.
5. Preserve all committed evidence.
6. Reconcile and checkpoint before any recovery.

Stopping the paper worker must not stop the existing forecast collection or scoring services.

## 13. Isolated pre-deployment rehearsal

Using disposable PostgreSQL and fabricated evidence, verify the production-like entry point and service configuration.

At minimum:

1. Load approved config.
2. Reject unapproved portfolio identities.
3. Reject missing or mismatched release pins.
4. Reject unsafe credentials and filesystem paths.
5. Reject unauthorised database endpoints.
6. Verify restricted role permissions.
7. Recover a funded fabricated portfolio.
8. Authenticate fabricated original forecasts.
9. Submit a simulated order.
10. Capture a fresh fabricated quote.
11. Commit an atomic simulated fill.
12. Record valid and missing valuation marks.
13. Recover after a process interruption.
14. Preserve a sticky exit.
15. Prevent a second overlapping worker.
16. Verify clock-health rejection.
17. Test emergency shutdown.
18. Verify private evidence backup/restore.
19. Verify the original collector/scorer tests still pass.
20. Confirm no production resource was modified.

The rehearsal should use the same operational module interfaces as the proposed production writer.

Do not pretend that a localhost-only staging CLI is itself a validated production deployment.

## 14. Tests and CI

Run:

- Full pytest suite.
- PostgreSQL 17 integration tests.
- Role and privilege tests.
- Writer and recovery tests.
- Clock and network adapter tests.
- Backup/restore tests.
- Guarded historical regressions.
- Ruff lint and formatting.
- Wheel packaging/import validation.
- Git whitespace checks.
- Existing scientific hash verification.

Add tests for any new production configuration or service templates.

Keep the production entry point disabled in default tests.

No CI job should require production credentials or reach the production database.

Do not run new genuine historical backtests.

## 15. Documentation

Create:

`docs/stage-04d3b1-lightsail-preflight.md`

Include:

- Starting Git SHA.
- Production inspection approval status.
- Actual observed host state, if approved.
- Differences from historical infrastructure documentation.
- Proposed release architecture.
- Production entry-point design.
- Service and timer configuration.
- Exact database role plan.
- Migration and compatibility plan.
- Backup and independent restore evidence.
- Clock and network prerequisites.
- Resource and timing measurements.
- Alerting and kill-switch plan.
- Test results.
- Remaining blockers.
- Explicit future owner approvals.

Update:

- `docs/deployment/paper-migration-activation-checklist.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- Relevant architecture documents.
- `prompts/README.md`

Archive the complete prompt at:

`prompts/stage-04-paper/stage-04d3b1-lightsail-preflight.md`

Do not alter the Stage 4A scientific protocol or frozen historical results.

## 16. GitHub release

This task authorises local implementation, testing, documentation, commit and push.

It does not authorise a production deployment.

After all applicable checks pass:

1. Review the diff.
2. Check that no credentials or private operational artifacts are staged.
3. Confirm historical scientific evidence is unchanged.
4. Commit the verified implementation.
5. Push to `origin/main`.
6. Verify both workflows for the exact commit SHA.

Suggested commit:

`feat(paper): prepare Lightsail deployment and preflight`

If read-only production inspection was not approved, explicitly classify the host-dependent checks as unverified rather than claiming readiness.

Do not deploy to Lightsail.

Do not apply migration 0002 to production.

Do not install or enable the paper service.

Do not activate either simulated portfolio.

## 17. Completion report

Provide:

1. Starting and final Git SHAs.
2. Exact-commit CI status.
3. Production inspection approval and outcome.
4. Verified production state or outstanding inventory.
5. New production entry-point and service design.
6. Migration compatibility.
7. Restricted database role validation.
8. Backup and restore rehearsal.
9. Clock and Binance connectivity readiness.
10. Quote-timing evidence.
11. Process isolation and resource planning.
12. Monitoring and emergency stop procedure.
13. Full test results.
14. Complete changed-file inventory.
15. Remaining production blockers.
16. Proposed owner-approved installation sequence.

Finish with one explicit verdict:

- READY FOR CONTROLLED INSTALLATION REVIEW
- READY WITH CONDITIONS
- BLOCKED

**Do not confuse readiness for installation with permission to install or activate.**

Stage 4D.3B.2 will separately authorise controlled installation and production migration once the owner has reviewed the actual environment and rollback plan.

Stage 4D.3C will separately authorise each genuine portfolio activation.
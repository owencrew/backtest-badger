# Backtest Badger — Stage D2A: Lightsail Migration Rehearsal

Implement a safe, reproducible migration rehearsal from the existing Mac research environment to the new AWS Lightsail server.

D2A must prepare and test the backup, transfer, isolated restore and evidence validation workflow. It must NOT perform the final production cutover.

## Context

Backtest Badger is a quantitative research platform with a frozen historical dataset, pinned model training, immutable prospective predictions and automated outcome evaluation.

Completed:
- Stages 1–3D: research, forward prediction collection and automatic outcome scoring.
- Stage D1: Lightsail deployment foundation committed and installed.
- Commit deployed on Lightsail: `556e3a9b80066b2d83cf1e1e4ee5795fc6ec290f`.
- The Mac is actively running both LaunchAgents.
- The new server has no real research database or migrated evidence yet.

Server:
- SSH alias: `Ubuntu-1`
- Ubuntu 24.04.5 LTS, Linux x86_64
- Python 3.12.15 via uv
- Docker 29.9.1, Compose 5.6.0
- 2 vCPUs, approximately 4 GB RAM, 80 GB storage
- D1 installed at `/opt/backtest-badger/current`
- Persistent evidence root: `/var/lib/backtest-badger/artifacts`
- Private configuration root: `/etc/backtest-badger`

All three resource-constrained synthetic benchmarks passed:

- 17.60 seconds
- 17.81 seconds
- 18.11 seconds

Each benchmark used full-sized synthetic training input, preserved historical holdout isolation and completed under configured service limits.

These do not establish live database/provider performance.

## 1. Read existing specifications

Read:

- AGENTS.md
- README.md
- docs/architecture.md
- docs/roadmap.md
- docs/deployment/lightsail-foundation.md
- docs/deployment/lightsail-migration-runbook.md
- Stage 3A–3D guides and frozen Stage 3C evaluation protocol
- Current PostgreSQL Compose, Alembic migration, config, evidence layout, source versioning and forward verification implementation

Treat the existing D2 runbook as authoritative unless a concrete error requires a narrowly documented correction.

Inspect the actual repository implementation before writing scripts.

Do not modify frozen scientific source, recorded predictions, recorded outcomes or frozen training artifacts.

## 2. Define D2A safety boundaries

D2A is a rehearsal only.

It must never:

- Stop or reconfigure Mac LaunchAgents.
- Start any Lightsail production worker.
- Create `/etc/backtest-badger/workers-approved`.
- Enable Lightsail collection/scoring timers.
- Publish genuine predictions or outcomes.
- Rewrite historical evidence.
- Restore over an existing nonempty database.
- Modify the original Mac database.
- Change a source timestamp, issuance timestamp or runtime fingerprint.
- Modify the frozen Stage 3C protocol.
- Run tests against the original production research database with mutation privileges.
- Expose DB credentials, SSH keys or other secrets in source control or logs.

Design every potentially destructive operation to fail closed unless the exact target and intended operation are explicitly specified.

## 3. Rehearsal directory and database isolation

Define an explicit rehearsal layout on Lightsail, separate from:

- `/var/lib/backtest-badger/artifacts`
- The production Docker volume
- The active application release

Use a unique rehearsal identifier and a dedicated staging directory.

Use a separate PostgreSQL 17 rehearsal volume and Docker Compose project, with a private loopback-only endpoint on a nonproduction port.

Ensure rehearsal scripts cannot accidentally address the intended production database or production artifact directory.

Avoid `docker compose down -v`, volume deletion or recursive replacement unless explicitly operating on a disposable, identified rehearsal resource and separately authorised.

The D1 production database volume must remain absent during D2A unless there is a documented reason to prepare it separately.

## 4. PostgreSQL image and configuration

Prepare an operator procedure for selecting a trustworthy official PostgreSQL 17 image for linux/amd64.

Requirements:

- Pin a specific immutable image digest.
- Check architecture and major/minor version.
- Record the image reference and digest.
- Use the same reviewed image for rehearsal and later production restoration unless separately approved.
- Do not invent digests.
- Do not silently pull floating latest tags during an actual restore.

Provide safe scripts or exact documented commands for establishing:

- Private PostgreSQL admin credentials.
- Separate least-privilege worker credentials.
- Private environment-file permissions.
- Nonpublic loopback-only network binding.

D2A may create an isolated rehearsal database, but it must not initialise or activate the production research database.

Do not print resolved configurations containing passwords.

## 5. Complete Mac source inventory

Implement read-only inventory tooling for the Mac covering:

- Original PostgreSQL database identity, schema and row counts.
- Market data and complete candle revision history.
- All relevant Alembic state and source DB constraints.
- Complete `artifacts/` tree.
- Frozen Stage 1/2 research exports and manifests.
- Forward predictions and outcomes.
- Collector and scoring operational journals.
- REST acquisition and provenance evidence.
- Lock, interrupted and partial files.
- Historical backtests and economic diagnostic evidence.
- Git revision, source fingerprints, frozen protocol hash and `uv.lock`.

Produce machine-readable manifests with paths, sizes and SHA-256 hashes.

Do not exclude apparently unimportant scientific evidence merely to reduce transfer size.

Preserve all existing evidence exactly, including known late or incomplete observations.

## 6. Coherent backup and transfer

Implement an operator-driven backup workflow using PostgreSQL 17-compatible logical dumps and a complete artifact archive.

Important: The Mac is actively writing new research data.

A PostgreSQL `pg_dump` is transactionally coherent for the database, but an artifact archive collected at a different instant is NOT a single coherent cross-system checkpoint.

Therefore:

- An online D2A copy must be clearly labelled a nonauthoritative rehearsal snapshot.
- Do not describe it as a final consistent checkpoint.
- Avoid disrupting or blocking genuine collection/scoring.
- Detect or record files changing during inventory/archive where feasible.
- Keep failure and inconsistency evidence rather than silently repairing it.
- Require a fully quiescent final checkpoint during D2B before production activation.

Use new destination paths and never overwrite a previous backup.

Include a verified Git source archive/bundle if necessary for reproducibility.

Transfer data using SSH/rsync or another appropriate secure mechanism.

Preserve timestamps, paths and exact file bytes. Map ownership explicitly on Linux.

Verify source and destination inventories, both before and after archive extraction.

Use SHA-256 for content integrity.

Do not use `rsync --delete`, and never transfer secrets or the Mac virtual environment into the application artifact directory.

Document how the operator creates two independent encrypted backup copies, including at least one copy outside Lightsail, before final cutover.

Do not hardcode backup destination credentials.

## 7. Isolated PostgreSQL restore

Provide safe, repeatable commands/scripts to:

1. Verify the database dump before restoration.
2. Create a uniquely identified empty rehearsal volume/database.
3. Restore the database without `--clean`.
4. Validate tables, schemas, sequences, constraints and Alembic version.
5. Compare source and restored row counts, identity ranges, revision distributions and exact logical data.
6. Run read-only application health and market coverage queries.
7. Demonstrate database isolation from production.
8. Retain rehearsal logs and an explicit validation report.

Preserve exact decimal market values and historical revision records.

Do not apply schema migrations blindly to a restored database.

Do not use destructive integration tests against the restored research database.

## 8. Immutable forward evidence validation

On the isolated copied evidence, run the existing offline:

- Forward collection status.
- Forward scoring status.
- Prospective evaluation report.
- Frozen protocol and artifact checksum verification.

Validate that original predictions, outcomes, journals and source identities remain unchanged.

Account for the fact that original Mac forward records include Mac-specific runtime fingerprints.

A Linux x86_64 replay may fail strict provenance validation against historical Mac records even when the original records are valid.

Do not loosen verification requirements or alter original fingerprints.

Separate:
- Original Mac-record integrity.
- Structural/offline validation on Linux.
- Linux reproduction diagnostics.
- Prospective predictions generated after the eventual cutover.

Any Linux reproduction tests must use isolated data, retain the unchanged scientific recipe, and publish no genuine forward records.

## 9. Operational compatibility and performance

Prepare checks for:

- UTC/NTP synchronisation.
- Python and dependency versions.
- Actual model and source fingerprints.
- Frozen input availability.
- PostgreSQL health.
- Read-only source validation.
- REST/Binance network accessibility without publishing real forecasts.
- Resource limits and time to complete under concurrent representative load.
- Lightsail CPU credit/headroom considerations.
- Disk capacity sufficient for current database, original evidence, rehearsal copy and backups.

Do not silently tune models or bypass data validation to satisfy a deadline.

If the 4 GB instance is inadequate, report the limitation rather than weakening research integrity.

## 10. Automated safeguards and tests

Write narrow, independently testable tools for:

- Preflight checks.
- Source manifest generation.
- Backup verification.
- Restore-target isolation.
- Database snapshot comparison.
- Artifact checksum comparison.
- Rehearsal reporting.

Test wrong-host, wrong-database, pre-existing-volume, corrupt-archive, checksum mismatch, partial-transfer and accidental-production-path scenarios.

Include clear refusal behaviour.

Run existing tests, Ruff, shell checks and appropriate new tests.

Do not conduct another broad scientific audit or refactor existing scientific modules.

## 11. Documentation and operator workflow

Create:

- `docs/deployment/lightsail-d2a-rehearsal.md`
- Any necessary narrow migration scripts under `ops/lightsail/`

Update the existing deployment runbook, README, architecture and roadmap only where necessary.

Archive this prompt at:
`prompts/deployment/002-lightsail-migration-rehearsal.md`

Provide an explicit operator checklist broken into:

A. Prepare Mac backup destination.
B. Create verified source manifests and online rehearsal backup.
C. Transfer to Lightsail staging.
D. Initialise isolated rehearsal PostgreSQL.
E. Restore and compare.
F. Validate immutable research evidence.
G. Report readiness and unresolved D2B risks.

Each step must say whether it runs on Mac or Lightsail.

## 12. Execution restrictions

You may write and locally test the migration tooling.

Do not SSH into Lightsail, change its configuration, initialise its database, upload research artifacts, stop schedulers or execute production migration commands.

Do not commit or push changes.

No real forward evidence may be altered.

## 13. Completion report

Report:

1. Files created or modified.
2. Backup/export methodology.
3. Rehearsal isolation mechanism.
4. Database restore and validation coverage.
5. Immutable evidence verification.
6. Tests run and results.
7. Exact first operator commands for D2A.
8. Explicit limitations of an online rehearsal snapshot.
9. Any discrepancies or unresolved risks.
10. Requirements before D2B final cutover.

Stop after D2A tooling is prepared. Do not proceed to D2B automatically.
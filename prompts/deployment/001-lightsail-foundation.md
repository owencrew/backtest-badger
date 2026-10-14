# Backtest Badger — Stage D1: Lightsail Deployment Foundation

Implement a reproducible, secure deployment foundation for Backtest Badger on an existing clean AWS Lightsail Ubuntu 24.04 server.

This is a deployment-preparation stage, not authorisation to migrate live evidence, switch schedulers or modify scientific results.

## Target environment

- Lightsail instance: Ubuntu-1
- Public IP: 3.8.218.113
- OS: Ubuntu 24.04.5 LTS
- Architecture: x86_64
- CPU: 2 vCPU
- RAM: approximately 4 GB
- Disk: approximately 80 GB
- Docker Engine: 29.9.1
- Docker Compose: v5.6.0
- Python: 3.12.15, installed through uv
- Application account: ubuntu
- Existing SSH access: configured locally as `ssh Ubuntu-1`

The old crypto trading platform was deliberately decommissioned and its Lightsail instance deleted. This is a fresh replacement server.

The Mac currently runs two working LaunchAgents:

1. Stage 3B forward prediction collection.
2. Stage 3D forward outcome scoring.

Both must remain running during D1.

## 1. Inspect the repository

Read AGENTS.md, README, architecture, roadmap, and Stage 1–3 documentation relevant to persistence, frozen research inputs, forward recording, scoring, scheduling and backups.

Inspect the existing application configuration, database schema, migrations, Docker Compose files, artifact structure and locked dependencies.

Reuse working application components. Do not redesign the research engine.

## 2. Deployment layout

Prepare a minimal production-style directory structure, for example:

- `/opt/backtest-badger` — application source and locked environment.
- `/var/lib/backtest-badger` — persistent artifacts and application evidence.
- `/etc/backtest-badger` — private environment configuration.
- `/var/log/backtest-badger` — operational logs if required.

Avoid coupling runtime artifacts to a replaceable source checkout.

The existing Python application currently uses relative artifact paths. Design a compatible and tested directory/mount arrangement that preserves existing path expectations without changing fingerprinted scientific modules.

Use explicit working directories and permissions.

Document source revision pinning and how deployments can be rolled back without overwriting research evidence.

## 3. PostgreSQL

Prepare a dedicated PostgreSQL 17 Docker Compose configuration.

Requirements:

- Persistent Docker volume.
- Connection bound to 127.0.0.1 only.
- Database access not exposed publicly.
- Credentials loaded from a private environment file.
- Health checks.
- Automatic restart policy.
- Resource limits appropriate for approximately 4 GB RAM.
- Existing Alembic migrations.
- No dependence on the deleted legacy crypto application.

Keep PostgreSQL version compatible with the existing development database.

Do not include real credentials in Git.

Do not automatically create or restore the real database during D1.

## 4. Python environment

Use the existing `uv.lock` and Python 3.12.

Provide commands or scripts that establish a reproducible environment on the server.

Avoid unattended package resolution or automatic runtime upgrades.

Record:

- Git commit.
- Python version.
- Dependency lock checksum.
- Environment and deployment version.

Do not modify pinned scientific model implementations or frozen recipes.

## 5. systemd worker units

Prepare separate systemd services and timers for:

- `forward-cycle`
- `forward_scoring_operations cycle`

Use the existing commands and their native UTC timing policies.

Preserve the Stage 3B 15-minute issuance window.

Both workers must use the local private PostgreSQL connection.

Include:

- Independent services.
- Suitable scheduling intervals.
- Locking and idempotency already provided by the application.
- Appropriate startup dependencies.
- Non-root service execution.
- Explicit environment paths.
- Restricted filesystem permissions.
- Clear journal logging.
- No uncontrolled restart loops.

The scorer must not assume the collector has completed first.

D1 must NOT enable or start either timer.

## 6. Memory and performance

Provide a safe, optional 2 GB swap setup for the small Lightsail instance, with a low swappiness setting.

Add a bounded pre-cutover performance test demonstrating that BTCUSDT and ETHUSDT model calculations can finish within the collection deadline.

Use synthetic fixtures or an explicitly authorised test environment.

Avoid creating real forward records during deployment preparation.

Do not silently reduce training data, model parameters or verification requirements to improve performance.

## 7. Security

Prepare secure deployment defaults:

- Keep PostgreSQL bound to loopback.
- Run application processes as a non-root service account where practical.
- Do not expose secrets through Git, logs or systemd unit files.
- Use restrictive permissions for private configuration and artifacts.
- No public prediction submission API.
- No public database connection.
- No real trading credentials.
- No website deployment yet.

Do not change Lightsail networking rules or SSH keys automatically.

## 8. Migration planning

Create a separate, detailed migration runbook for the later D2 stage.

It must cover:

- Source Mac PostgreSQL backup.
- Transfer of complete database state needed for research.
- Frozen Stage 2A training artifacts.
- Original forward predictions.
- Original immutable forward outcomes.
- Collector and scoring operational journals.
- Source acquisition manifests/evidence.
- Checksums before and after transfer.
- Runtime/architecture compatibility, including macOS arm64 versus Linux x86_64.
- Model reproduction and source fingerprint limitations.
- Timely performance under real server resources.
- Server-side backup and restore.
- Exactly one active collector during final cutover.
- Recovery if deployment fails.
- Prevention of duplicate or backdated forecasts.

Do not execute the migration during D1.

## 9. Tests

Add tests or deployment validation scripts for:

- Compose configuration.
- systemd unit and timer syntax.
- Localhost-only PostgreSQL binding.
- Environment-file permissions.
- Deployment paths.
- Read-only status commands.
- Independent timer operation.
- No modifications to frozen evidence.
- Failure/restart behaviour.
- Clear detection of missing dependencies.

Run the existing Python test suite, Ruff and whitespace checks.

Do not run live prediction issuance during automated tests.

## 10. Documentation and scope

Create:

- `docs/deployment/lightsail-foundation.md`
- `docs/deployment/lightsail-migration-runbook.md`

Add deployment templates/scripts under `ops/lightsail/` or another narrowly scoped directory.

Update README, architecture and roadmap.

Archive this prompt under `prompts/deployment/001-lightsail-foundation.md`.

Do not modify existing forecast, evaluation, model or training source files.

Do not install anything on Lightsail directly from Codex in this stage.

Do not stop the existing Mac LaunchAgents.

Do not publish or replace scientific evidence.

Do not commit or push changes.

## 11. Completion report

Report:

1. Deployment architecture and files created.
2. Exact initial Lightsail installation commands.
3. Database layout and data preservation requirements.
4. Worker scheduling definitions.
5. Security boundaries.
6. Resource assumptions and performance risks.
7. Validation results.
8. Remaining D2 migration steps.

Stop after D1. Do not start the production services or proceed to D2 automatically.
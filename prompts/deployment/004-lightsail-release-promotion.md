# Backtest Badger — Stage D3B: Promote Prepared Lightsail Release

## Objective

Safely promote the already prepared Backtest Badger release on AWS Lightsail, verify production health, and document the result.

This is the final application-release reconciliation before Stage 5 website development.

Prioritise minimal operational disruption, reliable recovery and preserving existing forward evidence.

Do not introduce new infrastructure, modify research methodology or undertake unrelated improvements.

## Verified baseline

Read `AGENTS.md` and the D3A review first:

- `docs/deployment/lightsail-d3a-release-reconciliation.md`
- `docs/deployment/production-infrastructure.md`
- `docs/deployment/lightsail-migration-runbook.md`

Existing SSH connection: `ssh Ubuntu-1`

Current production release:

`e0d622d51e1edc120fb4f1b5229e46907ed6219d`

Prepared candidate release:

`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`

Verified GitHub Actions run: `40106649560`, successful.

D3A confirmed healthy PostgreSQL, six scheduled services, successful unattended backups, a fingerprint-verified restore drill and candidate compatibility.

The candidate has already been prepared and validated. Do not repeat preparation unnecessarily.

Confirm these facts against the actual host before acting.

## Explicit owner authorisation

By submitting this prompt, I authorise one supervised promotion of the prepared candidate to become the active production release.

This includes:

- Pausing and resuming the collection and scoring timers
- Allowing in-flight workers to complete
- Atomically changing `/opt/backtest-badger/current`
- Running existing read-only deployment and database checks
- Observing normal scheduled worker executions
- Reverting to the previous release if necessary and safe
- Writing a sanitised deployment report

No other production changes are authorised.

Do not modify database schema, original evidence, credentials, backup policies, systemd unit definitions or AWS configuration.

## Step 1 — Revalidate promotion prerequisites

Confirm the candidate's exact commit, preparation metadata, source checksums, locked dependencies and persistent artifacts link.

Confirm GitHub CI success for the candidate SHA.

Verify production PostgreSQL health, Alembic revision `0001`, NTP, disk capacity and the active release identity.

Require a successful off-machine backup within the previous 24 hours and fingerprint-verified isolated restore evidence within the previous seven days.

If the restore evidence is too old, check whether the next regularly scheduled restore drill has succeeded. Do not initiate a manual restore without separate authorisation.

Confirm that backup/retention operations are not in progress and that there is no concurrent release operator.

Stop if any material prerequisite fails.

## Step 2 — Safe promotion and failure handling

Use the existing D3A promotion plan as the starting point, but **review and improve its failure handling before execution**.

In particular, its example shell sequence uses `set -eu` but does not comprehensively recover from failures after timers have been stopped.

Ensure:

- The existing backup lock is held during the critical section
- Only collection/scoring timers are paused
- In-flight services finish normally
- The previous release remains available
- A failed pre-switch check leaves the previous release active and restores normal scheduling
- A failed candidate validation restores the old release before resuming timers, provided the old release is verified healthy
- If neither release can be verified safe, workers remain paused and the failure is clearly reported rather than blindly restarting
- An unexpected shell error or interruption cannot silently leave production in an ambiguous state
- Rollback does not modify the production database or historical artifacts

Use a small, understandable supervised procedure. Do not create a deployment framework or make permanent changes to production scripts merely for this one upgrade.

Use the existing immutable release directories and atomic symlink-switching method.

## Step 3 — Activate candidate

After all checks pass, promote:

`/opt/backtest-badger/releases/cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`

Verify that `/opt/backtest-badger/current` resolves to that exact directory.

Run both existing runtime validators and `badger db-health` under the appropriate production worker identity/environment.

These are validation commands only, not manual collection or scoring cycles.

Do not run database migrations, retrain models, regenerate forecasts or replay historical research.

## Step 4 — Resume and verify

Resume the existing collection and scoring timers only after candidate validation succeeds.

Confirm:

1. Both timers are active and correctly scheduled.
2. The next normal collection and scoring executions succeed.
3. Retained evidence remains valid.
4. There are no new invalid operations, unexpected missing horizons or mature-unscored backlogs.
5. Previously recorded forecasts and outcomes remain accessible.
6. New forecast identities correctly reflect the new dependency fingerprint.
7. Production PostgreSQL remains healthy and unchanged in schema.

Where practical during the supervised session, observe the next naturally eligible four-hour forecast issuance and its subsequent scoring eligibility.

If that observation cannot be completed during the session, report it as **pending follow-up**, not verified.

Do not create artificial forecast records or trigger unscheduled worker cycles.

## Step 5 — Rollback if necessary

If candidate validation fails, perform the planned source-only rollback after confirming the previous release remains compatible.

If candidate workers have already written new evidence, preserve that evidence and check compatibility before reverting.

Do not automatically retry deployment, delete evidence, restore the database or bypass scientific validators.

Clearly report any failure and the final active release.

## Step 6 — Documentation

Create:

`docs/deployment/lightsail-d3b-release-promotion.md`

Record the actual outcome, including:

- Old and new release SHA
- Exact promotion time
- Preconditions and backup/restore identities
- Validation commands and results
- Timer pause/resumption outcomes
- First observed post-promotion worker results
- New dependency-provenance implications
- Any pending follow-up checks or incidents
- Whether rollback occurred

Update `docs/deployment/production-infrastructure.md` and `docs/development-handoff.md` with the new verified production state, only if promotion succeeds.

Keep the report concise and exclude secrets or private forecast data.

Archive this full original prompt verbatim at:

`prompts/deployment/004-lightsail-release-promotion.md`

Update `prompts/README.md` as appropriate.

## Boundaries

- No Git commit or push
- No new application code
- No dependency upgrades beyond the prepared release
- No Alembic migrations
- No changes to the production PostgreSQL volume
- No historical replay or model fitting
- No manual forecast/scoring cycles
- No changes to backup retention or AWS monitoring
- No cleanup of historical Docker resources
- No website hosting, DNS or public network configuration
- No extra deployment attempts without authorisation

## Final response

State one of:

**PROMOTION SUCCESSFUL**, **PROMOTION FAILED — ROLLED BACK**, or **PROMOTION BLOCKED / INVESTIGATION REQUIRED**.

Report the actual active SHA, checks executed, worker health, recovery status, provenance changes, incidents and remaining follow-up items.

Distinguish immediately verified operations from future scheduled observations.

Recommend a Conventional Commit message for the reviewed documentation changes.

Do not commit, push or start website deployment.
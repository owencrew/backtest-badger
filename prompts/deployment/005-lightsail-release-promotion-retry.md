# Backtest Badger — Stage D3B.1: Correct and Retry Lightsail Promotion

## Objective

Correct the identified D3B temporary-helper import collision and complete one supervised production release promotion.

D3B failed before switching releases because a temporary helper named `inspect.py` shadowed Python's standard-library `inspect` module. The recovery helper encountered the same error.

The old release was independently verified and normal collection/scoring resumed after approximately 45 seconds. No scheduled execution was missed during the pause.

This is a narrowly scoped correction and retry. Do not redesign the deployment system.

## Baseline

Read `AGENTS.md`, followed by:

- `docs/deployment/lightsail-d3a-release-reconciliation.md`
- `docs/deployment/lightsail-d3b-release-promotion.md`
- `docs/deployment/production-infrastructure.md`

Use existing SSH access: `ssh Ubuntu-1`.

Original active release:

`e0d622d51e1edc120fb4f1b5229e46907ed6219d`

Prepared candidate:

`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`

Candidate CI: successful GitHub Actions run `40106649560`.

Do not target a newer documentation-only GitHub commit merely because main has advanced.

## Explicit authorisation

I authorise ONE additional supervised production promotion attempt after the failure has been corrected and the actual execution path has been tested.

This includes the established timer pause, release switch, runtime checks, worker resumption, observation and safe source-only rollback where required.

No other infrastructure changes are authorised.

## Step 1 — Correct the confirmed failure

The original incident was caused by executing a temporary Python helper named `inspect.py`.

Use a non-conflicting helper filename, or preferably remove the unnecessary temporary Python helper if the established validation commands can accomplish the same task more simply.

Where temporary helpers remain necessary, use Python safe-path execution such as `python -P -B`.

Critically, verify the **exact staged command**, filename, execution directory, interpreter, user and import environment before stopping any production timer.

The previous mock tests were insufficient because they did not exercise the real staged filename.

Do not merely repeat those tests and assume the collision is fixed.

Preserve the original failed D3B incident evidence.

## Step 2 — Verify readiness again

Before attempting promotion:

- Confirm the old production release is still active and healthy.
- Confirm the existing candidate has not changed.
- Confirm its recorded deployment metadata and locked environment.
- Confirm the exact candidate CI succeeded.
- Confirm PostgreSQL health and schema `0001`.
- Confirm collection/scoring evidence is valid.
- Confirm the latest off-machine backup is fresh and verifiable.
- Confirm a recent fingerprint-verified restore result.
- Confirm no concurrent backup, retention or promotion operator.
- Check the worker schedule and choose a safe interruption window.

If a required prerequisite fails, stop without pausing workers.

Do not prepare another candidate, run historical research or change the database.

## Step 3 — Test the actual recovery path

Before activation, exercise the corrected helper invocation and recovery checks in their intended execution context without altering production services.

Check shell syntax and the actual remote Python import environment.

Test recovery logic without injecting faults into live production services.

Avoid unnecessary new supervisors, scripts, permanent units or deployment frameworks. Use the simplest reliable approach that ensures an unexpected error does not silently strand the two workers.

## Step 4 — One supervised promotion

If all prerequisites and real-command checks pass:

1. Acquire the established backup lock.
2. Pause only the collection and scoring timers.
3. Allow in-flight workers to finish.
4. Confirm the old release and rollback path.
5. Atomically point `current` to the prepared candidate.
6. Run the existing runtime validators for both workers.
7. Verify PostgreSQL connectivity.
8. Resume collection and scoring.
9. Release the lock.
10. Observe successful natural scheduled worker executions.

No manual prediction or scoring cycles.

On failure, follow the safe recovery plan. Restore the old source link when compatible, validate it, and resume the workers. If neither release is safe, leave the workers paused and report the incident.

Do not automatically retry a second time.

## Step 5 — Verify new-release behaviour

Confirm the actual active commit.

Check the next natural collection and scoring executions and the current offline evidence status.

When a new four-hour forecast becomes eligible, verify its actual publication and new dependency-file provenance.

If its subsequent outcome is not yet mature, record that scoring observation as pending.

Do not fabricate forecasts, accelerate timestamps, alter immutable records or claim future events have already been observed.

## Step 6 — Documentation

Create:

`docs/deployment/lightsail-d3b1-release-retry.md`

Preserve the original D3B incident report unchanged.

If promotion succeeds, update:

- `docs/deployment/production-infrastructure.md`
- `docs/development-handoff.md`

Archive this prompt verbatim at:

`prompts/deployment/005-lightsail-release-promotion-retry.md`

Update the prompt index if appropriate.

## Hard boundaries

- Exactly one additional promotion attempt
- No database migration or data repair
- No application or scientific code changes
- No deployment to a new target SHA
- No additional dependency installation
- No backup-policy or monitoring changes
- No historical backtest execution
- No new permanent infrastructure
- No real-money trading
- No website deployment
- No Git commit or push

## Final response

State **PROMOTION SUCCESSFUL**, **PROMOTION FAILED — RECOVERED**, or **BLOCKED**.

Provide the old and new active commit identities, confirmation that the helper collision was corrected, exact preflight and runtime validation results, pause/resumption details, post-promotion worker observations, pending follow-up checks and any incidents.

Confirm that original production evidence remains intact.

Recommend a Conventional Commit message and stop for review.
Continue Backtest Badger Stage 5B.10 from the current working tree.

I want to simplify the deployment workflow.

**I approve the production activation of the isolated v2 feed on Lightsail and R2, subject to the technical checks below. You do not need to request further routine approvals for the backend installation, publication and scheduling operations explicitly described here.**

I will personally manage all Cloudflare dashboard changes, website version promotion and rollback.

### 1. Finalise and commit

Review the complete existing Stage 5B.10 diff. Preserve all completed work.

Verify the 261 Python tests, 144 frontend tests, new CI job, systemd files, public contract safeguards, scientific identities and documentation.

Ensure no credentials, private evidence or generated private candidates are staged.

Commit and push the reviewed code using:

`feat(ops): prepare isolated v2 forward feed activation`

Verify both GitHub workflows pass for the resulting exact commit SHA.

Confirm that Cloudflare's GitHub deployment command remains candidate-only (`pnpm exec wrangler versions upload`). A GitHub push may upload a website candidate, but must not promote it.

If CI fails, fix the issues and revalidate before production installation.

### 2. Activate v2 on Lightsail

You are authorised to:

- Rebuild and verify the reviewed installation artifact against the committed source.
- Install the isolated v2 helper, publisher, independent checker and four systemd units.
- Reuse the existing R2 bucket-scoped credentials without printing or modifying them.
- Create the dedicated private v2 state directories.
- Run preparation under the actual systemd resource limits.
- Publish genuine, strictly validated v2 data to `backtest-badger-forward/forward-v2.json`.
- Perform exact-byte R2 and independent HTTPS verification.
- Enable the independent v2 publisher and checker timers.
- Observe at least two successful scheduled publication/check cycles.
- Inspect read-only host logs and performance metrics.
- Disable only the new v2 timers if rollback is required.

Use the schedules, resource limits and safety controls documented in `docs/stage-05b10-forward-v2-production-activation.md`, adjusting only where measured technical evidence requires it.

Do not alter the existing v1 publisher/checker or the research collector/scorer.

Before the first PUT, confirm the exact-limit private qualification succeeds with adequate time and memory headroom. If it fails, stop and report the blocker rather than weakening scientific or security checks.

Ensure all public outputs originate from genuine validated evidence, never synthetic fixtures.

### 3. Verify public v2 health

Verify:

`https://data.backtestbadger.com/forward-v2.json`

Require HTTP 200, strict schema v2, valid BTC and ETH predictions, latest-scored observations, fresh original timestamps, correct CORS/cache headers, and successful independent HTTPS checking.

Confirm that:

`https://data.backtestbadger.com/forward-v1.json`

remains healthy, unchanged in implementation and continuously refreshing.

Check scheduled operation, publication hashes, score progression, latency and resource use.

Observe a genuine four-hour forecast transition if one occurs during the session. If not, record it as outstanding; do not fabricate or force one.

### 4. Cloudflare boundaries

I will handle Cloudflare myself.

Do not:

- Change Cloudflare build variables.
- Modify Cloudflare DNS, R2 settings, tokens or permissions.
- Modify Workers Builds settings.
- Trigger an additional website build manually.
- Promote or roll back Worker versions.
- Modify production www search indexing.
- Enable public Worker preview URLs.
- Retire the v1 endpoint.

Do not ask me for the Cloudflare version SHA or preview settings merely to finish the Lightsail/R2 backend activation. Those are relevant to my later manual website release.

### 5. Failure handling

If a safety-critical check fails, stop the affected activation and report the issue.

You may disable the newly installed v2 timers and preserve the validated private state for diagnosis without asking for a separate routine approval.

Do not change credentials, broaden permissions, overwrite v1, manipulate research evidence or force a scientific scoring event to resolve a failure.

### 6. Completion

Update `docs/stage-05b10-forward-v2-production-activation.md` and the current development handoff with the actual operations and outcomes.

Report:

- New commit SHA and both GitHub CI results
- Installed v2 release identity
- Actual constrained performance measurements
- Successful public v2 endpoint verification
- Publisher/checker timer status
- Two scheduled publication/check results
- v1 research/feed health
- Remaining limitations
- Any production rollback operations
- Exact Cloudflare steps I need to perform manually

Commit and push documentation corrections after validation if necessary, again requiring green CI for the resulting SHA.

**Stop when the v2 data feed is healthy. Do not deploy the website.**

The final handoff should clearly state that the only remaining website work is for me to update the Cloudflare build variable, trigger a build and manually promote the reviewed candidate.
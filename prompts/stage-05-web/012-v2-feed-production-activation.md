# Backtest Badger — Stage 5B.10: Controlled v2 Forward Feed Activation and Website Release

## Objective

Complete the production migration from Backtest Badger's version-1 public forward forecast feed to the new version-2 feed, enabling the **Latest Scored Forecasts** feature on the live website.

The goal is for visitors to see both:

1. The latest issued BTCUSDT and ETHUSDT forecasts, which may still be awaiting outcomes.
2. The most recently completed and genuinely scored primary timely-automated forecasts, showing the original model predictions, realised returns, forecast errors and saved directional outcomes.

The migration must preserve the existing functioning v1 pipeline, frozen scientific methodology, public website availability, editorial content and search indexing.

**This is a controlled production activation, not a research-development stage.**

Implement and validate the necessary infrastructure locally first. Use explicit owner approval gates for production writes, credential changes, R2 publication and website promotion.

Do not assume that permission to plan this stage constitutes permission to perform every production operation.

---

## 1. Starting context

Repository:

`~/Code/backtest-badger`

GitHub:

`owencrew/backtest-badger`

The owner has committed and pushed Stage 5B.9:

**Expected starting commit:**

`14ed627c28b99c484f7a2f63ef9fc694ad252436`

Commit message:

`feat(web): add latest scored forecasts and refine homepage`

Verify actual HEAD and GitHub CI before beginning. Do not assume the expected SHA is still HEAD or that a running workflow has succeeded.

Read:

- `AGENTS.md`
- `README.md`
- `web/README.md`
- `docs/development-handoff.md`
- `docs/stage-05b9-latest-scored-forecast.md`
- `docs/stage-05b8-post-launch-audit.md`
- `docs/deployment/forward-feed-cloudflare-setup.md`
- `docs/deployment/website-cloudflare-workers.md`
- `web/scripts/public_forward_export.py`
- `web/scripts/public_forward_v2.py`
- `web/scripts/stage_forward_snapshot.py`
- `web/scripts/publish_forward_r2.py`
- `web/scripts/check-forward-endpoint.ts`
- `web/scripts/validate-forward.ts`
- `web/scripts/validate-forward-v2.ts`
- `web/lib/forecast.ts`
- `web/components/forward-dashboard.tsx`
- `web/components/latest-scored-forecasts.tsx`
- All existing `ops/public-feed/` service, timer and configuration files
- Related Python and frontend tests

Inspect the repository's current release and operator procedures rather than assuming earlier deployment plans are still current.

### Current production environment

Website:

`https://www.backtestbadger.com`

Cloudflare Worker:

`backtest-badger-web`

Existing public data endpoint:

`https://data.backtestbadger.com/forward-v1.json`

Proposed v2 endpoint:

`https://data.backtestbadger.com/forward-v2.json`

R2 bucket:

`backtest-badger-forward`

Production research and public-feed host:

`ssh Ubuntu-1`

Existing isolated public-feed installation:

`/opt/backtest-badger-public-feed/`

Existing private publication state:

`/var/lib/backtest-badger-public-feed/`

Existing publisher configuration:

`/etc/backtest-badger-public-feed/`

Existing production website uses Cloudflare Workers Static Assets with a Next.js static export.

GoDaddy remains the domain registrar. Cloudflare provides authoritative DNS.

The www website is indexing-enabled and the sitemap has been submitted to Google Search Console.

The owner previously disabled public `workers.dev` and version URLs. Verify the actual current settings rather than assuming they have remained unchanged.

### Production release process

Workers Builds uses the deployment command:

`pnpm exec wrangler versions upload`

This must remain **candidate-only**. No automatic production promotion is permitted.

The source commit, both GitHub CI workflows, build settings, candidate version and owner approval must be recorded before release.

---

## 2. Non-negotiable scientific boundaries

Stage 5B.9 implemented a strict v2 public contract using genuine retained forward evidence and saved results from the frozen evaluator.

Preserve that implementation.

The v2 public feed contains:

- `schema_version: 2`
- The existing `latest` collection
- The existing `evaluations` collection
- The new `latest_scored` collection
- Original forecast and scoring timestamps
- Original recipe identity
- Original model predictions
- Saved numerical forecast errors
- Saved directional outcomes

Only the approved markets and models are allowed.

Markets:

- BTCUSDT
- ETHUSDT

Models:

- Zero
- Training Mean
- Ridge
- Gradient Boosting

Cohorts remain strictly separate:

- `primary_timely_automated`
- `secondary_late_manual`
- `timely_unattributed`

Latest-scored observations must come exclusively from successfully scored primary timely-automated forecasts.

Preserve exact Decimal-derived direction and correctness from the saved evaluator output. Do not recalculate those values using rounded frontend displays.

Preserve:

- Frozen forecast protocol and protocol hash
- Original issuance/target/scoring chronology
- Four-hour log-return calculations
- Saved signed and absolute errors
- Zero-model directional abstention
- Strict v1 and v2 validators
- Publication clock-regression protections
- Scientific provenance and evidence-integrity checks

Do not retrain models, rerun historical backtests or modify the frozen scorer.

Do not invent outcomes or reconstruct previous predictions using current models.

---

## 3. Phase A — Read-only baseline verification

Before making changes, inspect the current live production state.

### GitHub and repository

Verify:

- Local Git HEAD
- Clean or otherwise understood working tree
- Both GitHub CI workflows for the expected Stage 5B.9 commit
- Latest Cloudflare build state, where accessible
- Any unpromoted Worker candidates
- Current source-to-build provenance, where available

If CI has failed, investigate before proceeding.

Do not modify protected release settings to bypass a failure.

### Lightsail

Use read-only inspection to verify:

- Current research release identity
- Collector/scorer health
- Existing v1 publisher health
- Existing independent v1 checker health
- v1 systemd timer status
- Recent publication failures and timestamps
- Available memory and disk
- Running services and scheduled work
- Existing installed helper and Python/Node versions
- Existing private directory permissions

The v1 research, publisher and checker must be healthy before activation.

Do not interrupt, restart or upgrade them during baseline verification.

### Public website and v1 feed

Verify:

- Homepage and Burrow return HTTP 200 over HTTPS
- Apex and HTTP redirect correctly to www HTTPS
- Homepage metadata contains `index, follow`
- The 13-page sitemap remains accessible
- `robots.txt` advertises the sitemap
- Existing v1 endpoint passes strict schema and freshness validation
- BTC and ETH forecast cards work
- Existing aggregates remain correct
- No sensitive evidence or secrets are publicly exposed

Record a concise baseline with dates, versions, public-object SHA-256 and relevant timings.

**Stop immediately if there is an unexplained live outage, an active production incident or a scientific-integrity failure.**

---

## 4. Phase B — Implement isolated v2 production tooling

Implement the infrastructure necessary to publish and independently validate `forward-v2.json`.

This phase permits local repository code, tests and documentation changes.

It does not yet permit changes to the live host or R2 bucket.

### A. Versioned v2 publisher

Extend the existing infrastructure with a reviewed, explicitly versioned publishing path.

Requirements:

- Publish only to `backtest-badger-forward/forward-v2.json`.
- Never overwrite `forward-v1.json`.
- Reject all unexpected bucket and object destinations.
- Accept only a validated v2 candidate.
- Preserve the existing 64 KiB public size limit.
- Use the existing approved content type and cache policy.
- Use dedicated R2 credentials from the existing protected environment.
- Never embed credentials in code, logs or command arguments.
- Require a successful R2 PUT followed by exact-byte GET/readback validation.
- Verify SHA-256 against the intended published candidate.
- Preserve previous successfully validated private bytes.
- Fail closed on uncertain remote acknowledgement.
- Never advance local last-success state after a failed operation.
- Maintain independent v1 and v2 candidate/state files.
- Prevent overlapping v2 publisher runs.
- Reject source changes and evidence regression.
- Preserve original timestamps.
- Never substitute synthetic data during a failed production publication.

Prefer reuse of existing tested helpers where safe, without loosening v1 safeguards.

Keep the v1 publisher's behaviour unchanged.

### B. Independent v2 HTTPS checker

Implement a version-specific public endpoint checker.

It must independently fetch:

`https://data.backtestbadger.com/forward-v2.json`

Verify:

- HTTPS and certificate validity
- HTTP 200
- Approved URL and path
- JSON content type
- Expected Cache-Control
- Correct www CORS response
- Strict v2 schema
- Two approved markets
- Latest issued forecast coverage
- Primary/secondary/unattributed cohort separation
- Latest-scored presence when matched evidence exists
- Valid issuance, target and scoring chronology
- Genuine outcome/error consistency
- Fresh snapshot generation
- Nonregressing evidence cutoff
- Missed four-hour issuance detection
- Exact published-byte hash comparison where available
- 64 KiB size bound
- Safe handling of HTTP failures, stale data and invalid responses

The check must not merely trust a successful upload command.

Retain the existing v1 checker without changing its assumptions.

### C. Separate systemd configuration

Prepare version-specific v2 publisher/checker service and timer units.

Use distinct names, for example:

- `backtest-badger-public-feed-v2.service`
- `backtest-badger-public-feed-v2.timer`
- `backtest-badger-public-feed-v2-check.service`
- `backtest-badger-public-feed-v2-check.timer`

Names are suggestions; inspect the existing conventions.

Requirements:

- Independent schedules and state
- Appropriate CPU/memory quotas
- Explicit timeouts
- Read-only access to retained research evidence
- No unnecessary access to research databases
- No write permissions to research directories
- Restricted filesystem access
- Existing Linux hardening conventions
- Root-controlled environment configuration
- No credentials in journal output
- Private last-success and rollback artifacts
- No automatic retries that can create overlapping writers
- Clearly documented rollback/disable procedure

Do not change existing v1 unit files or disable v1 timers.

### D. Tests

Add focused tests for:

- Approved v2 destination only
- Rejection of v1 destination through the v2 path
- Rejection of malformed or synthetic production candidates
- Successful upload/readback
- Hash mismatch
- R2 write failure
- Readback failure
- Lost acknowledgement
- Preservation of previous candidate
- Unchanged v1 state
- Clock regression
- Missing scored observations
- Schema downgrade
- Invalid saved directional results
- Concurrent publisher invocation
- Timed-out preparation
- Oversized output
- Invalid CORS and HTTP metadata
- Stale issuance despite fresh publication clocks
- Accidental private-data exposure

Use mocked R2 requests and synthetic fixtures.

Do not perform public writes during these tests.

---

## 5. Phase C — Performance and resource validation

Stage 5B.9 validated v2 locally using 4,459 retained evidence files.

However, the v2 exporter also performs an additional file inventory and SHA-256 verification.

Its performance on Lightsail has not yet been established.

Before enabling a production v2 timer, benchmark preparation under representative host conditions.

### Requirements

Measure:

- Total preparation time
- Python CPU time
- Peak resident memory
- Disk I/O implications
- Evidence inventory/hash time
- Validator runtime
- Remaining headroom under the service deadline
- Competition with v1 publication and research jobs

Use the actual resource restrictions intended for production where practical.

Read retained evidence without mutating it.

Do not use an old local evidence copy as the sole performance benchmark.

The current v1 publisher historically takes approximately 37 seconds of wall time, but that is not a reliable estimate for v2.

The new schedule must not overload the host or interfere with four-hour research operations.

If v2 exceeds its bounded runtime or memory budget, do not activate the timer.

Investigate a safe improvement without weakening provenance checks, introducing scientific differences or silently increasing infrastructure spending.

Record the benchmark and recommended schedule.

### Schedule selection

Choose a ten-minute publication cadence only if justified by actual timings.

Stagger v2 publication and checker execution relative to existing v1 jobs.

Ensure the checker runs after the corresponding v2 publication can reasonably complete.

Avoid timer overlap, simultaneous expensive scans and a persistent freshness gap.

Explain the selected schedule and expected failure behaviour.

---

## 6. Approval Gate 1 — Production v2 publication

**Stop here before the first production write.**

Prepare an owner-facing activation summary showing:

1. Files changed and tests passed.
2. Genuine read-only performance benchmark.
3. Proposed v2 systemd installation paths.
4. Proposed timer schedules.
5. R2 bucket/key permissions required.
6. Public data exposure assessment.
7. Current v1 health.
8. Precise production write operations to be performed.
9. Rollback procedure.

Request explicit owner approval to install and activate v2 publication.

Do not interpret the existing Stage 5B.9 approval as authorisation.

The owner should handle Cloudflare dashboard configuration and any new credential creation personally.

Never request secret values in chat.

### R2 permissions

Determine whether the existing dedicated R2 credentials already allow the new object in the approved bucket.

Do not assume object-level permissions are available merely because the application enforces a destination allowlist.

If broader R2 permissions are required, explain exactly what changes and request approval first.

Do not rotate credentials or create new API tokens without approval.

The intended public endpoint uses the existing custom domain:

`data.backtestbadger.com`

Do not re-enable the retired `r2.dev` development endpoint.

A public R2 custom domain makes eligible objects accessible directly; CORS is not an authentication mechanism.

Publish only the reviewed public allowlist.

---

## 7. Phase D — Activate and validate the v2 feed

Proceed only after Gate 1 approval.

Install the isolated v2 helper without replacing the current v1 installation or research release.

Maintain independent deployable identities and a rollback-friendly installation.

### Initial publication

Perform a controlled genuine v2 publication.

Verify:

- Private preparation passed.
- Both schema validators passed where applicable.
- Public v2 bytes match the validated candidate.
- Public SHA-256 matches the expected digest.
- The R2 readback matches the uploaded object.
- The public HTTPS endpoint returns the intended content.
- Both BTC and ETH are present.
- Latest predictions and latest scored observations are distinct.
- Original forecast timestamps and values are unchanged.
- No synthetic or private records are exposed.
- The v1 endpoint remains unchanged and healthy.

### Automatic operation

After an initial successful publication and independent check, enable the authorised isolated timers.

Verify at least two genuine scheduled publication/check cycles.

Record exact cutoff, generation, SHA-256, service exit status and elapsed time for each.

Confirm that:

- Generation clocks advance.
- Saved scored observations remain stable when no new score arrives.
- The latest pending forecast changes only when a new genuine prediction is issued.
- Scored history advances only when genuine evaluated evidence becomes available.
- No outcome is reconstructed or attached to the wrong prediction.
- v1 and v2 remain separately healthy.

### Four-hour transition verification

Where a genuine issuance/scoring boundary occurs during the authorised observation period, verify the transition end to end.

The desired sequence is:

1. A new forecast is genuinely issued.
2. Its outcome is initially pending.
3. A previous scored forecast remains visible.
4. The new target boundary closes.
5. The frozen scorer publishes a genuine outcome.
6. The next validated v2 publication advances the latest-scored record.
7. The frontend correctly distinguishes new pending and newly completed observations.

Do not manually trigger, retime or fabricate research events to force the transition.

If no boundary is observed during the session, record that verification as outstanding rather than claiming it passed.

Keep v1 publishing and checking throughout.

---

## 8. Phase E — Prepare the Cloudflare website candidate

Begin this phase only after the genuine public v2 feed passes the required checks.

The production website currently uses the build-time variable:

`NEXT_PUBLIC_FORWARD_SNAPSHOT_URL=https://data.backtestbadger.com/forward-v1.json`

The intended new value will be:

`NEXT_PUBLIC_FORWARD_SNAPSHOT_URL=https://data.backtestbadger.com/forward-v2.json`

The owner should make that change in Cloudflare's production build configuration after the v2 endpoint is verified.

### Release prerequisites

Require:

- Exact reviewed source commit
- Both GitHub CI workflows successful for that commit
- A successful frontend build
- Correct v2 endpoint
- Verified publication freshness
- Working independent checker
- Rollback to the existing v1 configuration documented
- Candidate URL/indexing exposure assessed
- No unauthorised changes to Cloudflare security settings

If Stage 5B.10 introduces new repository code, do not assume the Stage 5B.9 commit's green CI validates that new code.

Stop for owner review before committing or pushing additional source changes.

### Search indexing and previews

Production www must remain indexable:

`BADGER_SEARCH_INDEXING=www-live-owner-approved`

But alternate public versions and previews must not become indexable duplicates.

The owner previously disabled the Worker `workers.dev` URL and version URLs.

Verify these settings remain disabled before uploading an indexing-enabled candidate.

Also verify preview-branch build behaviour separately.

Use local Wrangler inspection or genuinely protected preview mechanisms where needed.

Do not publicly expose an indexing-enabled candidate on another hostname just to simplify testing.

Do not disable indexing on the live www website as a workaround.

Cloudflare builds must continue using:

`pnpm exec wrangler versions upload`

Do not change the production command to `wrangler deploy`.

### Candidate verification

Build the website against the genuine v2 endpoint.

Before promotion, inspect:

- Home
- The Burrow
- The Dig
- Field Notes
- Field Guide
- About
- All approved article routes
- Latest predictions
- Latest scored forecasts
- BTC and ETH forecast cards
- All six Binance chart ranges
- Aggregate evaluation tables
- Mobile responsiveness
- Failed-refresh and stale states
- Canonical metadata
- Indexing policy
- Sitemap and robots output
- Redirect behaviour

Verify the homepage contains the approved headline:

**Understand the methods behind the numbers.**

Preserve all editorial source identities and approval hashes.

Do not expose private candidate JSON under `web/public/` or the static export directory.

---

## 9. Approval Gate 2 — Website production promotion

**Stop before promoting the new Worker.**

Present the owner with:

- Exact Git source commit
- Python and frontend CI links/status
- Cloudflare build identity
- Candidate Worker version ID
- Confirmed live v2 URL
- Latest v2 publication/checker results
- Candidate verification results
- Indexing/preview safeguards
- Exact current v1 Worker version retained for rollback
- Proposed promotion operation

Do not promote without explicit approval.

Once authorised, promote only the reviewed candidate to 100% of production traffic.

Do not change DNS, custom domains or unrelated Cloudflare settings.

---

## 10. Phase F — Post-release acceptance

After an approved promotion, perform public acceptance checks.

### Website

Confirm:

- `https://www.backtestbadger.com/` returns HTTP 200.
- The homepage shows the revised Field Guide headline.
- The Burrow loads genuine v2 data.
- BTC and ETH display latest issued predictions.
- BTC and ETH display latest scored forecasts.
- Values match the validated public v2 records.
- Original issuance, target and scored timestamps are correct.
- Signed and absolute errors are consistent.
- Directional outcomes match saved evidence.
- Zero remains N/A for direction.
- No synthetic examples appear as genuine results.
- Historical backtests remain separate.
- Responsive layouts remain usable.
- No broken navigation or article routes are introduced.

### Search and routing

Confirm:

- `index, follow` on production www.
- Canonical URLs point to www.
- Sitemap still contains 13 approved pages.
- Robots advertises the sitemap.
- HTTP requests redirect to HTTPS.
- Apex redirects to www.
- Path and query strings remain preserved.
- No unintended public preview/indexable duplicate exists.

### Feeds and infrastructure

Confirm:

- v2 HTTPS checker passes.
- v2 publication is fresh.
- v1 endpoint still passes.
- v1 publisher/checker timers remain enabled.
- Collector and scorer remain healthy.
- No resource exhaustion or recurring systemd failures.
- R2 access policy remains within approved scope.
- No private data is exposed.

Record the release timestamp and observed versions.

Do not claim long-term operational reliability based on a single successful post-release check.

---

## 11. Rollback and failure handling

Prepare and test the rollback procedure before production promotion.

### If v2 publication fails

- Preserve the previous validated private candidate.
- Do not advance clocks.
- Do not publish fabricated or stale-as-fresh evidence.
- Do not overwrite v1.
- Investigate the specific failure privately.
- Leave the old production website using v1 until v2 is healthy.

### If the v2 website fails after promotion

Request owner authorisation to restore the previously verified v1-configured Worker version.

Confirm that rollback restores the actual frontend configuration, not merely the source files.

Do not replace `forward-v2.json` with v1-format bytes.

Do not bypass the frontend's schema downgrade protection.

After rollback, recheck:

- Homepage
- Burrow
- v1 endpoint
- Both CI-backed deployment identities
- Indexing
- Sitemap
- Redirects
- Public-data freshness

Leave v1 publication functioning throughout the migration.

Do not retire either version as part of this stage.

---

## 12. Validation requirements

Run appropriate local tests before any production activation.

Include:

- Existing frozen evaluator tests
- v1 exporter tests
- v2 exporter tests
- v1/v2 public contract tests
- New publication tests
- New endpoint checker tests
- Existing frontend tests
- New v2 frontend regression tests
- Ruff lint and formatting
- ESLint
- TypeScript
- Prettier
- Static production build
- Static export audit
- Local Wrangler smoke checks
- Documentation-link validation
- `git diff --check`

Test both:

1. Normal default/noindex candidates.
2. Explicit owner-approved indexed production builds.

Do not weaken production assertions merely to make tests pass.

Preserve the seven approved editorial hashes and all protected scientific identities.

Where local tools or browser access cannot provide genuine production evidence, record the verification gap explicitly.

---

## 13. Documentation and operational handoff

Create:

`docs/stage-05b10-forward-v2-production-activation.md`

Include:

- Starting release identity
- Production-readiness baseline
- Technical architecture
- v2 publishing implementation
- v2 checker implementation
- R2 access and security assessment
- Performance benchmarks
- Timer schedule and isolation
- Activation approvals
- Genuine publication results
- v1/v2 compatibility checks
- Candidate build and source mapping
- Website promotion record, if approved
- Public acceptance results
- Rollback procedure
- Observed operational limitations
- Remaining owner decisions
- Next recommended development milestone

Update, as appropriate:

- `README.md`
- `web/README.md`
- `docs/development-handoff.md`
- `docs/deployment/forward-feed-cloudflare-setup.md`
- `docs/deployment/website-cloudflare-workers.md`
- `docs/roadmap.md`

Preserve historical reports as historical evidence.

Archive this complete prompt at:

`prompts/stage-05-web/012-v2-feed-production-activation.md`

Update `prompts/README.md`.

Do not change existing historical reports to imply that v2 was already live at an earlier date.

Document the actual operational state reached, including any phase intentionally deferred by an approval gate.

---

## 14. Hard boundaries

Without separate explicit approval, do not:

- Commit or push new repository changes
- Install or modify production systemd units
- Enable new production timers
- Upload to R2
- Change R2 permissions or credentials
- Create or rotate API tokens
- Modify production environment files
- Update the active Lightsail helper installation
- Change Cloudflare build variables
- Upload or promote a new Worker
- Modify DNS or custom domains
- Enable new paid resources
- Change production search-indexing settings
- Modify research collector/scorer services
- Modify retained research evidence
- Retrain models
- Change frozen scientific calculations
- Modify protected editorial approvals
- Delete or retire v1 services, endpoints or backups

The owner may explicitly authorise a later gated operation during this Codex session. Such approval applies only to the operation described at that gate.

Do not assume approval for additional production actions.

Never request private credentials or raw evidence to be pasted into the conversation.

Do not send retained private research evidence to external services.

---

## 15. Completion report

At the end, provide:

1. Current Git source and CI identity.
2. Summary of implemented production tooling.
3. Complete changed-file inventory.
4. Test and performance results.
5. v1 production health.
6. v2 publisher and checker status.
7. Evidence of genuine v2 publication, if approved.
8. Evidence of successful scheduled operation, if observed.
9. Four-hour transition verification or clearly stated outstanding status.
10. Website candidate and deployment status.
11. Indexing and preview safety checks.
12. Exact production changes performed and approvals obtained.
13. Rollback readiness.
14. Remaining operational risks and decisions.
15. Recommended Conventional Commit message.

Explicitly distinguish:

- Locally implemented
- Tested against synthetic evidence
- Tested against genuine retained evidence
- Validated on Lightsail
- Publicly activated
- Promoted to www
- Not completed or not authorised

Never report an unexecuted deployment as successful.

### Final success criteria

**Stage 5B.10 is fully complete only when:**

- The genuine v2 feed is publishing automatically and independently passing HTTPS validation.
- The v1 feed remains healthy.
- Both markets show correctly preserved scored and pending observations.
- The live Burrow reads v2 successfully.
- The approved production Worker is promoted.
- Public search indexing and existing routes remain intact.
- Scientific and editorial identities remain unchanged.
- A documented, verified rollback path remains available.

If owner authorisation is needed before reaching these conditions, stop at that gate with a concise approval request and clear evidence of the work completed.

The priority is a trustworthy, reversible production release — not deployment at any cost.
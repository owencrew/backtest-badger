# Backtest Badger — Stage 5B.5: Forward Forecast Feed Activation and Navigation Correction

## Owner authorisation

I am the owner of Backtest Badger.

I explicitly authorise Codex to carry out the necessary infrastructure changes, production configuration, credential setup, scheduled execution, public-safe data publication and local website integration required to activate the genuine forward forecast feed.

This authorisation supersedes the earlier Stage 5B.4 restriction against activating the feed, **only within the scope defined below**.

I authorise the work to proceed through completion without seeking separate written approval for every in-scope production operation.

Normal SSH, cloud-account, security and tool approval prompts must still be respected. Do not bypass denied permissions, authentication, MFA or provider requirements.

No unrestricted administrative authority is granted.

## Objective

Make genuine BTCUSDT and ETHUSDT forward predictions and scored outcomes from AWS Lightsail available to The Burrow.

The feed must update automatically as new forecasts and evaluations become available.

Use the existing validated Stage 5B.4 implementation.

Additionally, make one small navigation correction: restore Field Notes before Field Guide.

Do not rebuild the prediction system or change the research methodology.

The next milestone after this stage remains the first public website deployment on Cloudflare Workers Static Assets.

## 1. Read the existing implementation

Repository:

`~/Code/backtest-badger`

Starting commit:

`03e3f6022d17b78ceed2e6f19f1c5216f4f0b76a`

Read:

- `AGENTS.md`
- `docs/stage-05b4-mascot-navigation-forward-feed.md`
- `docs/stage-05b-market-dashboard.md`
- `docs/deployment/website-cloudflare-workers.md`
- `web/scripts/public_forward_export.py`
- `web/scripts/stage_forward_snapshot.py`
- `web/scripts/validate-forward.ts`
- `web/lib/forecast.ts`
- `web/components/forward-dashboard.tsx`
- Relevant Stage 3 forward-prediction and evaluation documentation

Verify the actual Git state, latest CI status and current Lightsail release identity.

Do not assume the deployed research release has changed because the website repository has advanced.

## 2. Navigation correction

The owner has requested one final change to the main navigation.

The correct order is:

1. Home
2. The Burrow
3. The Dig
4. Field Notes
5. Field Guide
6. About

Field Notes must appear immediately to the left of Field Guide.

Continue using the label **Field Guide**, not "The Field Guide".

Update the shared navigation in `web/components/site-header.tsx`.

Confirm the order is correct in both desktop and mobile navigation.

Preserve:

- Existing routes and URLs
- Active-link highlighting
- Mobile menu functionality
- Accessibility and keyboard navigation
- Existing article titles
- All four approved Field Notes
- All three approved Field Guides
- Existing SHA-256 publication approvals

Do not modify approved article source files or their hashes.

Add a simple regression test for the navigation order if practical.

This is a small presentation correction, not a website redesign.

## 3. Authorised Cloudflare infrastructure

I authorise creation and configuration of one dedicated Cloudflare R2 Standard storage bucket:

`backtest-badger-forward`

Its only intended public object is:

`forward-v1.json`

The preferred permanent URL is:

`https://data.backtestbadger.com/forward-v1.json`

I authorise:

- Creating this dedicated Standard R2 bucket.
- Configuring public read-only access to the explicitly approved JSON object.
- Creating a bucket-scoped publishing credential.
- Configuring appropriate object metadata, content type, HTTPS and caching.
- Configuring necessary CORS settings.
- Testing uploads, downloads and public access.
- Enabling the proposed data subdomain when the Cloudflare DNS zone is ready.
- Publishing genuine, validated version-1 forward snapshots on a recurring basis.

Do not use an existing private backup bucket.

Do not make raw research files, directories, credentials or operational journals public.

Do not use an account-wide Cloudflare administration token as a permanent credential on Lightsail.

Verify that the actual upload mechanism supports narrowly scoped credentials. If the pinned Wrangler command cannot use the required restricted credential, adapt the upload implementation to use an appropriate bucket-scoped R2 S3-compatible client rather than weakening the permission boundary.

The permanent credential must permit only the necessary operations on this dedicated bucket.

Use private configuration or environment files with restrictive permissions. Never commit, log or print secret values.

### Cloudflare account access

I will complete any required Cloudflare login, MFA, billing setup or credential-generation actions through the official interface when prompted.

Do not ask me to paste secrets into the Codex chat.

Use the Free plan and Standard R2 storage. Do not subscribe to paid services or accept a plan upgrade without additional authorisation.

Review projected consumption before activation. If free-tier capacity is likely to be exceeded, stop and report the projected cost.

## 4. DNS and initial public endpoint

The final website domain is:

`www.backtestbadger.com`

The intended data hostname is:

`data.backtestbadger.com`

The domain currently uses GoDaddy, and the website itself has not yet been deployed to Cloudflare Workers.

First determine whether the Cloudflare DNS zone and data hostname can be configured safely with the current account and domain arrangements.

I authorise adding and configuring the dedicated data hostname within an appropriately configured Cloudflare zone.

**Do not migrate the entire domain's authoritative nameservers or alter existing GoDaddy website/mail records automatically.**

If a full DNS migration is necessary, prepare the zone, inventory and compare the existing records, then present the exact GoDaddy nameserver action required. Do not bypass this boundary.

If the custom domain is not yet available, a temporary Cloudflare R2 development URL may be enabled solely to test genuine data display locally.

Such an endpoint is publicly accessible and rate-limited; do not treat it as the permanent production solution.

Disable the temporary development URL after the permanent HTTPS endpoint is verified.

Do not start the public website deployment as part of this task.

## 5. Authorised Lightsail changes

The production research host is accessible via:

`ssh Ubuntu-1`

I explicitly authorise installing a **separate, isolated public-export helper** on Lightsail.

Use the reviewed Stage 5B.4 proposal as the starting point.

Suggested location:

`/opt/backtest-badger-public-feed/`

Private staging:

`/var/lib/backtest-badger-public-feed/`

I authorise:

- Creating the required helper directories.
- Installing the reviewed exporter and its pinned dependencies.
- Configuring a separate, least-privileged service identity where practical.
- Providing read-only access to the retained forward evidence.
- Providing write access to the helper's private staging directory.
- Installing a bucket-scoped R2 publishing credential.
- Performing one-off export and publication tests.
- Installing a dedicated systemd service and timer.
- Enabling the new export timer.
- Inspecting service status and logs to validate successful operation.
- Making small corrections to this new helper if necessary for reliable operation.

Preserve the active research release and its virtual environment.

Do not modify or restart the existing forecast collector, scorer, PostgreSQL, research scheduler or other production applications.

Do not alter the database, frozen evaluators, model recipes or retained scientific evidence.

No new inbound Lightsail network port should be required.

## 6. First genuine production export

Prepare a fresh genuine snapshot from the current retained evidence.

Reuse the existing exporter, frozen evaluator and public JSON schema.

Validate with:

1. Existing Python/evaluator validation.
2. Existing TypeScript public-contract validation.

Preserve:

- Both markets.
- All four models.
- All three evaluation cohorts.
- Original forecast values.
- Original issuance timestamps.
- Original target-close timestamps.
- Original recorded outcomes.
- Original evaluation classifications and scores.
- Undefined metrics.
- Evidence cutoff and generation timestamps.

Do not generate any new model predictions or independently rescore historical evidence.

Confirm that the candidate contains no sensitive paths, internal journals, credentials or private research data.

### Explicit publication approval

I authorise publication of a freshly generated, fully validated version-1 public forecast snapshot and continued automatic publication of future snapshots satisfying the same approved schema and safeguards.

This is permission to make the allowlisted forecast values, timestamps, outcome records and evaluation statistics **publicly readable by anyone**.

It is not permission to publish the underlying raw evidence files.

Do not publish a candidate that fails validation or contains unexpected fields.

If the schema expands or the data categories change materially, obtain new approval.

## 7. Scheduled publication

Use a ten-minute initial schedule unless on-host measurements demonstrate a better safe interval.

The Stage 5B.4 report suggests a systemd oneshot service and timer.

Implement a bounded, non-overlapping export process with:

- Private staging.
- Atomic replacement.
- Validation before upload.
- Locking to prevent overlapping runs.
- Explicit command timeouts.
- Low process priority.
- Sensible memory and CPU safeguards.
- No catch-up burst after downtime.
- No interference with existing research services.

Benchmark the exporter on the Lightsail host before enabling recurring operation.

Confirm that its resource usage is acceptable for the existing server.

Do not upgrade or replace production research dependencies.

If the exporter fails, preserve the previous valid public snapshot and its original timestamps.

Do not publish synthetic fallback data or fabricate a fresh generation time.

## 8. Verify the public endpoint

After publication, test the actual HTTPS endpoint.

Verify:

- HTTP 200 for the approved JSON object.
- Correct JSON content type.
- Actual object bytes and SHA-256.
- Complete version-1 schema validation.
- No private data or unexpected keys.
- Correct Cache-Control behaviour.
- Appropriate CORS behaviour.
- Genuine BTCUSDT and ETHUSDT coverage.
- Correct source, issuance, target and evidence timestamps.
- All four model identifiers.
- All three evaluation cohorts.
- Accurate stale-data behaviour.
- No unintended directory or private-object access.

Do not interpret CORS as preventing direct public access: the approved object is deliberately public.

Verify at least two successive publication cycles.

Where practical, observe a genuine new forecast issuance or outcome-scoring transition. Do not fabricate such a transition if the observation window is insufficient.

Confirm that source-side failures do not interrupt the existing collector/scorer.

## 9. Connect the local Burrow

The website already supports:

`NEXT_PUBLIC_FORWARD_SNAPSHOT_URL`

Configure the local production-style build to fetch the approved public endpoint.

Use local, untracked environment configuration or another existing safe build mechanism.

Do not commit environment-specific secrets or private paths.

The URL itself is public and may later be configured in Cloudflare Workers Builds.

Verify:

- BTC and ETH forward predictions display correctly.
- Prediction timestamps are in UTC.
- Current forecast targets are clearly identified.
- Pending forecasts are distinct from scored outcomes.
- The three cohort types remain separate.
- Forecast accuracy tables show valid matched counts.
- Undefined statistics stay undefined.
- Stale and network-error states are truthful.
- The market price chart remains sourced directly from Binance.
- No synthetic fixture is presented as live evidence.

Test both Next.js development mode and the actual local Wrangler static production export.

Do not claim the public Workers website is already live.

## 10. Monitoring and rollback

Implement the smallest practical monitoring necessary to identify:

- Export job failures.
- Missing successful publications.
- Stale published evidence.
- Repeated invalid candidates.
- Unexpected resource usage.

Use existing host/systemd monitoring facilities where sufficient.

Do not introduce a new paid monitoring platform.

Document an exact rollback procedure that can:

1. Disable only the new public-feed timer.
2. Preserve the existing research system.
3. Revoke the dedicated publishing credential if necessary.
4. Disable public access to the feed.
5. Restore a prior approved snapshot where appropriate.
6. Revert local website configuration without modifying research evidence.

Test safe parts of rollback without unnecessarily disrupting a healthy live feed.

## 11. Validation and documentation

Run all relevant focused tests and frontend checks.

Additionally, confirm the final navigation reads:

**Home → The Burrow → The Dig → Field Notes → Field Guide → About**

Preserve all frozen scientific results and previously approved articles.

Do not modify the seven published Markdown articles or their approval hashes.

Create:

`docs/stage-05b5-forward-feed-activation.md`

Document:

- Cloudflare resources created.
- Public endpoint and exact JSON key.
- Sanitised credential and permission scope.
- Actual Lightsail release and helper installation.
- Export frequency and measured resource usage.
- Validation results.
- Two-cycle publication verification.
- CORS/caching behaviour.
- Local Burrow verification.
- Navigation correction.
- Monitoring and rollback.
- Remaining launch prerequisites.

Update the deployment runbook and frontend README as necessary.

Archive this revised prompt at:

`prompts/stage-05-web/007-forward-feed-activation.md`

Update the prompt index.

## 12. Explicit boundaries

The owner authorises the bounded R2 and Lightsail public-feed activation described above.

This does **not** authorise:

- Cloudflare website deployment.
- Workers website version promotion.
- Changes to www or apex website routing.
- Full GoDaddy nameserver migration without the separate DNS cutover step.
- Model retraining.
- New trading strategies.
- Forecast generation outside the existing system.
- Changes to scorer behaviour.
- Database writes or schema changes.
- Changes to frozen research evidence.
- General-purpose production administration.
- Paid cloud upgrades.
- Publishing additional private evidence categories.

Do not commit or push repository changes.

Do not confuse lack of additional written approval for in-scope operations with permission to bypass the execution environment's security approvals.

## 13. Completion criteria

The preferred outcome is:

**Genuine, automatically refreshed Lightsail forward data is publicly available through a validated HTTPS JSON endpoint and visible in the local Backtest Badger Burrow.**

The navigation must also display Field Notes before Field Guide.

If DNS/account limitations prevent reaching that outcome, complete all safely achievable infrastructure and local integration work.

Report the exact remaining obstacle and necessary owner action.

Do not claim the feed is live unless the public endpoint and local website genuinely retrieve it.

Provide the recommended Conventional Commit message.

Stop before the first public Cloudflare Workers website deployment.
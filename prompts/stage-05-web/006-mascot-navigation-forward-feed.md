# Backtest Badger — Stage 5B.4: Original Mascot, Navigation and Genuine Forward Forecast Integration

## Objective

Complete three improvements to the Backtest Badger website before its first Cloudflare Workers deployment.

1. Replace the existing homepage badger illustration with the owner's new original mascot image.
2. Rename and reorder the Field Guide navigation.
3. Connect The Burrow to genuine forward predictions and evaluation results produced by the existing AWS Lightsail research system.

Preserve the existing Next.js, React, TypeScript, semantic CSS, TradingView Lightweight Charts and Cloudflare Workers Static Assets stack.

Do not rebuild the website, migrate frameworks, modify frozen scientific behaviour or deploy the website.

The goal is to finish the pre-launch website, including as much of the genuine forecast integration as can safely be implemented and validated without unauthorised production changes.

## 1. Starting context

Repository:

`~/Code/backtest-badger`

Latest verified release-candidate commit:

`34b640e545392fe9c653d4490461ed6239e8a880`

The Python and Frontend GitHub Actions workflows both passed at this commit.

Read:

- `AGENTS.md`
- `web/AGENTS.md`, if present
- `web/README.md`
- `docs/stage-05a-website-design.md`
- `docs/stage-05b-market-dashboard.md`
- `docs/stage-05b2-history-and-launch-readiness.md`
- `docs/stage-05b3-editorial-publication.md`
- `docs/deployment/website-cloudflare-workers.md`
- `docs/development-handoff.md`
- Relevant Stage 3 forward-prediction, scoring, evaluation and operations documents

Inspect the current Git working tree before changes.

Preserve uncommitted files and existing scientific evidence.

## 2. Replace the badger mascot

The owner has supplied a new, original black-and-white badger illustration.

It shows a badger digging through earth containing subtle but clearly identifiable financial candlesticks.

The exact original image is saved locally at:

`~/Downloads/backtest-badger-mascot.png`

This is the approved replacement for the existing homepage engraving.

### Asset handling

1. Confirm that the local source file exists and inspect its dimensions, format and alpha channel.
2. Copy the approved artwork into the website's brand assets.
3. Preserve the original pixels and visual composition.
4. Avoid unnecessary image regeneration or redesign.
5. Optimise the delivered image for web performance if practical, retaining a faithful representation.
6. Document the original source filename and the resulting website asset.
7. Ensure the production build uses only the checked-in asset, not a path into Downloads.

A suitable target is:

`web/public/brand/badger-mascot.png`

If a WebP derivative offers a meaningful size reduction without visible degradation, use it while keeping an appropriate source/provenance record.

Do not commit unrelated files from Downloads.

### Homepage integration

Replace the existing:

`/brand/badger-engraving.png`

with the new mascot in the homepage hero.

Preserve the established layout:

- Dark charcoal website background
- Warm sand illustration panel
- Forest-green accents
- Modern typography
- Existing hero headings and calls to action

The supplied image has a white background.

Consider whether the existing CSS multiply-blending treatment produces a clean result on the warm sand panel.

Do not introduce an obvious white square, dark halo or visible image boundary.

Use CSS blending or layout adjustments where sufficient; do not aggressively remove the image background or damage its fine linework.

Pay particular attention to the trading candlesticks embedded in the soil. They should remain visible at normal desktop and mobile sizes.

Adjust the image scale, crop and positioning if necessary to make the composition attractive.

Avoid clipping the claws, candlesticks or important parts of the mascot.

### Branding scope

The new illustration should become the primary homepage mascot.

Review any other prominent reuse of the old full-body engraving.

Keep the existing simplified geometric badger head/favicon unless there is a compelling visual inconsistency. Do not generate a new favicon unnecessarily.

Update the brand asset README to accurately identify the new owner-supplied original artwork.

Remove the old engraving from the deployed public assets if it is no longer referenced, but preserve any separately retained historical source/reference required for repository provenance.

### Verification

Inspect the homepage at:

- 1440px desktop
- 768px tablet
- 390px mobile
- 320px narrow mobile

Confirm that the new mascot is properly sized, readable and consistent with the established design.

The user has confirmed that the supplied replacement illustration is original. No further third-party engraving is needed for the homepage.

Do not make broader legal claims about unrelated assets.

## 3. Rename and reorder Field Guide

Update the primary navigation to this exact order:

1. Home
2. The Burrow
3. The Dig
4. Field Guide
5. Field Notes
6. About

The important changes are:

- **Field Guide appears immediately to the left of Field Notes.**
- Remove the leading "The" from "The Field Guide" wherever it is used as the website section name.

Keep the URL unchanged:

`/field-guide/`

Do not rename slugs, Markdown files or article routes.

### Scope

Check and update relevant visible labels in:

- Desktop navigation
- Mobile navigation
- Field Guide page heading and breadcrumb
- Page metadata and section titles
- Footer navigation
- Homepage section references
- Article breadcrumbs
- Any other prominent website navigation or section labels

Use "Field Guide" consistently.

Keep the actual approved article titles unchanged.

Do not modify the content of already SHA-256-approved Markdown articles purely to change the section branding.

Preserve the publication approvals for all four Field Notes and all three guides.

Verify keyboard navigation, active-link highlighting and mobile-menu behaviour.

## 4. Genuine Lightsail forward forecasts — objective

The Burrow already displays genuine Binance market observations.

It also contains a forward-research dashboard, but no public snapshot source is currently configured.

We want to display genuine BTCUSDT and ETHUSDT predictions generated by the AWS Lightsail research system, updated regularly as new predictions and scored outcomes become available.

The implementation must distinguish:

- Market prices observed from Binance
- Predictions issued by Backtest Badger models
- Realised outcomes subsequently scored
- Forecast accuracy statistics
- Historical strategy backtests
- Prospective paper trading, which is not yet operational as a complete public service

**Never present a prediction as an observed market price or a forecast record as a simulated trading return.**

### Existing implementation to reuse

Inspect:

- `web/components/forward-dashboard.tsx`
- `web/lib/forecast.ts`
- `web/components/use-feed.ts`
- `web/scripts/public_forward_export.py`
- `web/scripts/validate-forward.ts`
- `web/tests/forecast.test.ts`
- `web/tests/test_public_export.py`

Stage 5B already implemented:

- A strict version-1 public forecast JSON contract
- Validation of timestamps, counts, statuses and outcomes
- Four model identifiers
- Three distinct evidence cohorts
- A read-only public-snapshot fetching adapter
- A private candidate exporter
- Browser refresh and stale/error states

Build on this work.

Do not invent a competing data schema or replace the validated existing pipeline.

## 5. Inspect the existing production evidence safely

The owner's existing Lightsail connection is:

`ssh Ubuntu-1`

The owner authorises **read-only SSH inspection** needed to identify the current release, the forecast evidence layout, the existing serving configuration and the feasibility of creating a reviewed public export.

Request normal command/network approval if the environment requires it.

If an approval request is rejected or blocked, stop the remote inspection and report the issue. Do not retry through an alternative route to bypass approval.

Read the existing deployment and Stage 3 documentation before connecting.

Inspect only the information necessary to establish:

- Current production release identity
- Relevant prediction and outcome evidence schemas
- Existing evaluation and export mechanisms
- Current evidence retention locations and access boundaries
- Current timestamp/freshness conventions
- Whether a public-safe HTTPS JSON endpoint already exists
- Whether an existing static host can safely serve a future snapshot
- Expected CPU, memory and I/O impact of export preparation

Do not print credentials, environment-variable values containing secrets, private raw forecast records, internal journals or sensitive operational details.

Do not change permissions, services, files, firewall rules, DNS, public ports or scheduled tasks during read-only inspection.

The previous Stage 5B report identified a deployed research release and compatible Stage 3C evidence contract. Confirm the actual present state rather than assuming it is unchanged.

## 6. Prepare a genuine forecast export

Reuse the existing:

`web/scripts/public_forward_export.py`

It should continue reading retained forecasts, recorded outcomes and evaluation evidence through the frozen validators.

Do not regenerate forecasts or independently recompute realised outcomes using a new method.

### Required scientific safeguards

Preserve:

- BTCUSDT and ETHUSDT separately
- Models: zero, training_mean, ridge and gradient_boosting
- Original model recipe identities
- Four-hour forecast targets
- Actual forecast issuance timestamps
- Completed source-candle timestamps
- Recorded prediction values
- Existing scorer outputs
- Strict status classification
- Recorded evaluation cohort
- Matched observation counts
- Null/undefined statistics where appropriate
- Exact evidence cutoff
- Export generation timestamp

The three cohorts remain:

- `primary_timely_automated`
- `secondary_late_manual`
- `timely_unattributed`

Do not combine them into one overall accuracy figure.

Late predictions may have an informational advantage over timely predictions. Preserve that distinction.

### Prepare the first genuine candidate

Using only authorised access and data-handling methods, attempt to prepare a **private, genuine, read-only-derived candidate** from the retained Lightsail evidence.

Prefer preparation from a stable, privately held evidence copy or another documented non-production-mutating method.

Do not put raw evidence in the website repository.

Do not place private evidence or a not-yet-approved public candidate inside `web/public/` or `web/out/`.

Do not commit generated live forecast values.

Validate the candidate using both:

1. Existing Python source/evaluator validators
2. The existing TypeScript public JSON validator

Check timestamps, model fields, counts, evidence consistency and freshness.

Record a sanitised summary of the candidate: coverage, model/cohort presence, timestamp bounds, validation status and any blockers.

Do not include raw sensitive paths, secrets or private journals in the final report.

The first genuine export remains private until its exact contents and publication destination are approved.

If generating a candidate requires a write to production, request specific owner approval before executing that command.

## 7. Design the recurring public snapshot publication

The website is a Next.js static export hosted on Cloudflare Workers Static Assets.

It does not have a continuously running Next.js backend.

Design a minimal publication mechanism so that Lightsail can produce regularly updated **public-safe JSON**, and the website can retrieve that JSON over HTTPS.

### Requirements

The solution should:

- Keep PostgreSQL private
- Avoid browser access to the Lightsail database
- Avoid exposing internal journals or evidence directories
- Avoid publishing application credentials
- Avoid opening a new public database or arbitrary server port
- Use a small, read-only JSON document
- Keep forecast data separate from static website releases
- Be inexpensive and easy to maintain
- Support browser-side refresh without rebuilding the website every few minutes
- Support future Cloudflare Workers Static Assets hosting

Consider an existing appropriately secured HTTPS static-serving location if available.

Otherwise recommend the simplest compatible publication destination after examining current Lightsail infrastructure and the planned Cloudflare website.

Do not create an unnecessary FastAPI service merely to serve one JSON file.

Do not require a permanent WebSocket connection or stream.

Do not couple forecast issuance or scoring to website availability.

### Publishing procedure

Prefer:

1. Read existing retained evidence.
2. Validate the evidence and evaluator output.
3. Generate a bounded public-safe candidate.
4. Validate the complete JSON contract.
5. Write to a private staging location.
6. Atomically publish the validated snapshot.
7. Make it available through a public read-only HTTPS endpoint.
8. Retain the previous validated snapshot if publication fails.

A roughly ten-minute export cadence is a reasonable starting hypothesis, but measure the actual workload before choosing the schedule.

The browser may poll every five minutes even though the models generate forecasts on a four-hour cycle.

Use sensible caching, for example a short HTTP cache lifetime, without falsely reporting stale content as freshly generated.

Document non-overlap, timeout, error handling, monitoring and rollback.

Do not allow a failed export to advance `generated_at` or `as_of`.

Do not create a public URL that exposes the containing private directory.

If the feed is hosted on a different origin from the website, allow only the necessary read-only CORS access, consistent with the deployment design.

### Production activation boundary

This stage authorises **researching, implementing, testing and preparing** the publishing mechanism.

It does not give blanket permission to modify production infrastructure.

Before any command that installs a scheduled job, publishes data externally, changes permissions, changes system services, opens a port, installs packages on production or creates cloud resources:

**Stop and request separate explicit approval with the exact proposed changes and rollback procedure.**

Once such approval is granted through the normal approval mechanism, perform only the approved scope.

Do not deploy the website or modify GoDaddy/Cloudflare DNS as part of this stage.

If remote activation remains blocked, finish the local implementation and document precisely what remains to make the feed genuinely live.

## 8. Connect The Burrow frontend

Use the existing `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` mechanism unless a minimal, justified change is needed.

This is a build-time, public frontend configuration value.

Support a future same-origin public JSON URL or a secure cross-origin HTTPS feed.

Do not embed credentials or private server details in the frontend.

Do not package an approved one-off forecast JSON file into the static website as the supposedly refreshing production feed. Subsequent forecast updates must be obtainable independently of website deployments.

### Required UI

The Burrow should communicate clearly:

**Market observations**

- BTC/ETH market-price chart
- Genuine Binance source
- Market-data refresh timestamp

**Forward predictions**

- Relevant market symbol
- Model name
- Next four-hour predicted log return
- Issue time in UTC
- Forecast target close in UTC
- Pending/settling/mature-unscored/scored status
- Recorded realised return where applicable
- Latest successful publication time

**Historical forward-evaluation evidence**

- MAE
- RMSE
- Forecast bias
- Directional accuracy when defined
- Matched observation counts
- Cohort classification
- Preliminary sample-size warnings

Keep the distinction between forecast error metrics and historical trading performance.

### User experience

Where practical, improve the forward dashboard's readability:

- Use compact prediction cards or a summary near the top of the forward section.
- Keep detailed model comparisons in a clearly labelled table.
- Show exact issuance and cutoff timestamps.
- Make it obvious whether data is recent or stale.
- Label values in intelligible units.
- Provide a short explanation of what the forecast represents.
- Keep the existing detailed methodology accessible.

Preserve the current research-first visual style.

Do not manufacture a predicted future price line from return forecasts unless the data convention, reference price and exact transformation are explicitly documented and validated.

Avoid displaying a model ranking or implying one strategy is profitable because it has lower prediction error.

### Real-data state

There must be a meaningful distinction between:

- No feed configured
- Feed loading
- Genuine data loaded
- Data stale
- Feed unavailable
- Outcome pending
- Outcome scored

If no genuine feed has been activated, continue displaying the truthful unavailable state.

Never switch to synthetic fixtures as a production fallback.

Test fixtures may be used only in isolated automated tests.

## 9. Validate forecast refresh

Verify:

- Five-minute polling
- No duplicate timers
- Hidden-page pause
- Resume on visibility
- Manual refresh
- Request cancellation
- Network failure
- Invalid JSON rejection
- Snapshot timestamp regression rejection
- Stale snapshot detection
- A newly issued forecast replacing the previous one
- A previously pending forecast becoming scored
- Correct UTC labels
- Correct market/model/cohort coverage
- No accidental display of future outcomes

Prefer extending the existing polling/forecast tests instead of implementing a new polling subsystem.

Do not mark a score as genuine if it has not passed the existing evaluator's validation.

Measure and report the difference between the polling frequency and the underlying forecast issuance frequency.

## 10. Retain scientific and publication safeguards

Preserve all existing verified 2024 historical backtest figures.

Do not modify:

- Frozen research evidence
- Forecast model recipes
- Existing evaluator definitions
- The collector/scorer scheduling
- Historical backtest accounting
- Approved Field Note or Field Guide Markdown
- Their SHA-256 publication approvals

Keep the four Field Notes and three Field Guides published.

Field Note 004 must remain the featured note.

Any edits to published article source bytes require separate review and new hash approval. Avoid them in this stage.

Preserve the existing search-indexing configuration and Cloudflare Workers readiness.

Do not start the public website deployment yet.

## 11. Testing and verification

Run the relevant checks:

- Frontend lint
- TypeScript
- Prettier
- Frontend unit tests
- Production static export
- Publication-leakage checks
- Local Wrangler HTTP smoke tests
- Python exporter tests
- Targeted research-evaluator regression tests where relevant
- Relevant Ruff checks
- Documentation and navigation link checks

Add tests for the new mascot asset and navigation order where useful.

Verify that the production output includes the new mascot and no longer references the old homepage engraving.

Check that "Field Guide" appears before "Field Notes" on desktop and mobile.

Verify the full approved article set remains accessible.

Test the forecast renderer using known synthetic test fixtures exclusively in isolated tests.

If a genuine private candidate is available, validate it separately and document the result without accidentally publishing its bytes.

Inspect desktop and mobile screenshots of:

- Homepage
- Primary navigation
- The Burrow
- The forecast section

Do not claim the public forecast feed is live until a genuine, successfully fetched and approved endpoint has been tested.

Do not claim GitHub CI has passed for uncommitted changes.

## 12. Documentation

Create:

`docs/stage-05b4-mascot-navigation-forward-feed.md`

Document:

- New mascot asset and provenance
- Visual changes
- Navigation changes
- Existing and proposed forward-feed architecture
- Genuine Lightsail evidence inspection
- Candidate validation results
- Public JSON contract
- Publication destination recommendation
- Refresh schedule and operational cost
- Security boundaries
- Local test results
- Outstanding approvals
- Exact next activation/deployment steps

Update as appropriate:

- `web/README.md`
- `web/public/brand/README.md`
- `docs/deployment/website-cloudflare-workers.md`
- `docs/development-handoff.md`
- `prompts/README.md`

Archive this complete request verbatim:

`prompts/stage-05-web/006-mascot-navigation-forward-feed.md`

Preserve the earlier archived prompts.

## 13. Hard boundaries

- No Git commit or push
- No Cloudflare website deployment
- No remote Workers version upload
- No DNS or GoDaddy changes
- No unapproved production writes
- No unapproved public forecast publication
- No production database exposure
- No new public ports
- No modifications to existing forecasting/scoring operations
- No new model training
- No historical backtest replay
- No modification of frozen evidence
- No automatic paper trading
- No real-money trading
- No Vite, Tailwind or FastAPI migration
- No paid infrastructure without approval

Read-only production inspection is permitted as described above, subject to normal access approval.

The task should progress as far as is safely possible now.

If genuine feed publication needs a separately authorised production step, do not abandon the other work. Finish the mascot, navigation, frontend integration and tests, then provide an exact, minimal activation proposal.

## 14. Final report

Report:

1. New mascot integration and screenshots.
2. Exact navigation changes.
3. Current Lightsail production release and evidence compatibility.
4. Whether a genuine export candidate was successfully prepared.
5. Candidate verification results.
6. Whether a public HTTPS forecast feed already exists.
7. Proposed feed host and refresh mechanism.
8. Whether genuine forecasts are visible in the local website.
9. What remains blocked by separate production/publication approval.
10. Frontend and Python test results.
11. Security and scientific safeguards.
12. Files changed.
13. Recommended Conventional Commit message.
14. Exact next steps before the first Cloudflare deployment.

**Stop for owner review before committing or publicly deploying.**

The next intended milestone is deployment of the completed Backtest Badger website to Cloudflare Workers Static Assets.
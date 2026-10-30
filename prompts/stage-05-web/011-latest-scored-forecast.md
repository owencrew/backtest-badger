# Backtest Badger — Stage 5B.9: Latest Scored Forecast and Homepage Refinement

## Objective

Enhance The Burrow by displaying the most recent genuinely scored four-hour forecast for BTCUSDT and ETHUSDT, alongside the existing latest predictions.

Visitors should be able to compare what each model predicted with what subsequently happened.

Additionally, make one small editorial improvement to the homepage by replacing the current Field Guide headline with:

**"Understand the methods behind the numbers."**

Maintain the existing visual identity, research integrity, deployment controls and scientific methodology.

This stage authorises local implementation, validation, documentation and read-only production inspection.

It does not authorise production deployment, Git commits, public feed changes or Lightsail writes.

## 1. Starting point

Repository:

`~/Code/backtest-badger`

Read and understand:

- `AGENTS.md`
- `README.md`
- `docs/development-handoff.md`
- `docs/stage-05b8-post-launch-audit.md`
- `docs/deployment/website-cloudflare-workers.md`
- `docs/deployment/forward-feed-cloudflare-setup.md`
- `web/scripts/public_forward_export.py`
- `web/scripts/stage_forward_snapshot.py`
- `web/scripts/publish_forward_r2.py`
- `web/lib/forecast.ts`
- `web/lib/forecast-display.ts`
- `web/components/forward-dashboard.tsx`
- `web/app/page.tsx`
- Relevant frontend and Python tests
- Frozen forward evaluation protocols
- Existing prompt archive

### Current production architecture

- Website: `https://www.backtestbadger.com`
- Worker: `backtest-badger-web`
- Hosting: Cloudflare Workers Static Assets
- Framework: Next.js static export, React and TypeScript
- Public feed: `https://data.backtestbadger.com/forward-v1.json`
- R2 bucket: `backtest-badger-forward`
- Publisher and independent checker: AWS Lightsail
- Source repository: `owencrew/backtest-badger`

GoDaddy remains the registrar. Cloudflare manages authoritative DNS.

The apex domain redirects to www, with HTTP-to-HTTPS enforcement configured.

Search indexing has been enabled on the production website. The owner has confirmed:

- Homepage metadata contains `index, follow`.
- `sitemap.xml` returns HTTP 200.
- `robots.txt` advertises the sitemap.
- The sitemap has been submitted successfully to Google Search Console.

Search Console submission does not establish that Google has already indexed the pages.

### Release workflow

Cloudflare Workers Builds uses:

`pnpm exec wrangler versions upload`

This uploads a candidate Worker version without automatically promoting it to production.

The owner explicitly reviews and promotes releases.

Preserve this workflow.

Before editing, inspect the current Git HEAD, working tree, relevant documentation and CI state.

Preserve any existing uncommitted work.

## 2. Required user experience

The Burrow should display two clearly differentiated sections.

### A. Latest predictions — existing functionality

Preserve the existing BTC and ETH forecast cards.

They should continue showing:

- Latest issued prediction
- Source candle close
- Forecast issuance time
- Target candle close
- Four model predictions
- Pending, mature-unscored or scored status
- Snapshot freshness
- Expandable technical details

The newest forecast will often still be awaiting its outcome. This is expected.

Do not replace this section with the latest scored observation.

### B. Latest scored forecasts — new functionality

Add a clearly labelled section below the latest predictions and before aggregate evaluation.

Suggested section title:

**Latest scored forecasts**

For BTCUSDT and ETHUSDT, display the most recent successfully scored **primary timely-automated** forecast.

Each market should show:

- Source candle close
- Original forecast issuance time
- Target candle close
- Outcome scoring time
- Actual observed four-hour log return
- Original predictions from all four models
- Each model's signed forecast error
- Each model's absolute forecast error
- Directional outcome: Correct, Incorrect or N/A
- Model recipe identity in expandable technical details

Present returns and errors in log-return basis points using existing display helpers.

The primary view should be compact, readable and visually consistent with the current forecast cards.

A possible comparison table:

| Model | Predicted (bps) | Actual (bps) | Error (bps) | Direction |
| --- | ---: | ---: | ---: | --- |
| Zero | 0.00 | +12.50 | −12.50 | N/A |
| Training mean | +1.50 | +12.50 | −11.00 | Correct |
| Ridge | −3.20 | +12.50 | −15.70 | Incorrect |
| Gradient boosting | +5.00 | +12.50 | −7.50 | Correct |

These values are **synthetic illustrations only**. They must never appear as real production observations.

Consider whether the actual return should be displayed once per market above the model table rather than repeated in every row.

Choose the clearer design while preserving accessibility.

Do not introduce another UI framework or charting library.

## 3. Selecting the latest scored observation

The public exporter must select from genuine, retained and validated forward evidence.

For each market:

1. Select only the `primary_timely_automated` cohort.
2. Require a genuine retained score.
3. Require outcome scoring to have occurred by the evidence cutoff.
4. Select the most recent scored prediction by original source/target candle chronology.
5. Preserve its original issuance, recipe and scored outcome.
6. Never reconstruct an old prediction using the current model.

If no qualified observation exists, display:

**"No completed timely forecast available yet."**

Do not silently substitute a late manual or unattributed observation.

Do not attach a previous observed market return to the latest pending prediction.

Handle duplicate or ambiguous evidence deterministically and fail closed where appropriate.

The latest scored forecast may predate the latest issued forecast by one or more four-hour intervals.

Represent this honestly.

## 4. Scientific interpretation

Preserve the frozen evaluator semantics.

The four models remain:

- Zero
- Training Mean
- Ridge
- Gradient Boosting

The original forecast predicts the native four-hour close-to-close logarithmic return.

Use the existing conventions:

`predicted bps = predicted log return × 10,000`

`actual bps = actual log return × 10,000`

`signed error = predicted − actual`

`absolute error = abs(signed error)`

Do not confuse log returns with simple percentage returns.

Directional correctness must follow the frozen strict-sign protocol:

- Positive prediction and positive actual: Correct
- Negative prediction and negative actual: Correct
- Nonzero prediction and opposite-sign or zero actual: Incorrect
- Exactly zero prediction: N/A, because it abstains

The Zero model remains eligible for numerical error measurement but not directional accuracy.

Do not change the original scorer, protocol, model definitions or forecast calculations.

Do not infer statistical significance, model superiority or profitability from a single observation.

Keep the distinction between forward prediction accuracy and portfolio returns explicit.

## 5. Public contract versioning

The current version-1 public contract is strict and rejects unexpected fields.

Do **not** append an unapproved field directly to the live `forward-v1.json`.

Design and implement a backward-compatible publication migration.

### Preferred approach

- Preserve the existing v1 exporter and checker.
- Introduce a reviewed **v2 public snapshot contract**.
- Retain existing `latest` and `evaluations` semantics.
- Add a strictly validated `latest_scored` collection.
- Permit at most one qualified latest-scored observation per market.
- Use a separate future R2 object, `forward-v2.json`, after owner approval.
- Prepare the frontend to consume v2 when configured, without disrupting the existing v1 website.

If repository inspection reveals a substantially safer design, explain the trade-offs before implementing the alternative.

Do not weaken existing validators merely to accept new fields.

### Contract requirements

Require:

- Explicit schema version
- Exact allowed keys
- Finite numerical values
- Strict UTC timestamp validation
- Approved market and model identities
- Genuine scored status
- Correct issuance, target and scoring chronology
- Saved error consistency
- Explicit cohort identity
- No duplicate market observations
- No unexpected private metadata
- No raw evidence paths
- Safe handling of absent scored observations
- Appropriate size and freshness limits

Preserve the current production v1 endpoint and its continuously refreshing feed.

Do not change the live R2 object or overwrite its bytes.

## 6. Export consistency and provenance

Latest issued forecasts, latest scored forecasts and aggregate evaluation must originate from a consistent validated evidence snapshot.

The new latest-scored selection must not reconstruct predictions using present-day model parameters.

Revalidate that retained source records and outcomes have not changed during preparation.

Verify that the selected latest-scored observation belongs to the relevant evaluated cohort's matched evidence.

Preserve original prediction and score values produced under the frozen evaluator.

Validate consistency between the v2 content and its v1 projection where applicable.

Do not overwrite a valid previous candidate if new candidate preparation fails.

Publication clocks must never regress.

## 7. Frontend implementation

Build the new section in the existing forward dashboard.

Requirements:

- Separate BTCUSDT and ETHUSDT displays
- Responsive desktop and mobile layout
- Clear distinction between predictions and observed outcomes
- Consistent bps formatting
- Accessible Correct / Incorrect / N/A labels
- Visible scoring timestamp
- Expandable technical details
- Original decimal values available to technical readers
- No narrow-screen overflow
- No unnecessary duplication of aggregate evaluation

Retain:

- Latest prediction cards
- Timely automated aggregate evaluation
- Late-manual disclosure
- Unattributed cohort empty state
- Refresh button
- Snapshot freshness handling
- Retained-last-good behaviour
- Honest error and unavailable states
- All six Binance chart ranges
- Existing navigation
- Published articles
- Mascot and visual identity

The existing latest-prediction components must continue to function with v1 during migration.

The v2 view must not display fabricated observations when v2 is unavailable.

## 8. Homepage copy refinement

Make one small editorial change to the homepage.

File:

`web/app/page.tsx`

Locate the Field Guide promotional section (`guide-band`).

### Existing headline

"You don’t need a PhD to ask better questions."

### Replacement headline

**"Understand the methods behind the numbers."**

Use this exact replacement wording.

Preserve the existing eyebrow:

"A field guide for curious minds"

Preserve the link:

"Explore Field Guide"

Also preserve all three existing Field Guide links, their destinations and metadata.

### Design requirements

- Maintain the existing visual design.
- Preserve the typography and colour palette.
- Use a natural line break where appropriate.
- Ensure the headline looks balanced at desktop, tablet and mobile widths.
- Avoid awkward wrapping or excessive whitespace.
- Do not alter other homepage sections.
- Do not change published article source bytes or approval hashes.

This is a scoped homepage copy change, not authorisation for a wider redesign.

Include a screenshot of the revised section in the final implementation report.

## 9. Testing

Add comprehensive tests covering the new functionality.

### Export and scientific integrity

1. Selection of the latest genuinely scored observation.
2. Newer pending forecast coexisting with an older scored forecast.
3. Independent BTC and ETH scored observations.
4. No available scored observation.
5. Exclusion of late-manual forecasts.
6. Exclusion of unattributed forecasts.
7. Rejection of ambiguous or conflicting evidence.
8. Original prediction and score values preserved.
9. Correct target-close and scoring chronology.
10. Signed and absolute error consistency.
11. Positive and negative directional correctness.
12. Zero baseline directional N/A.
13. Nonzero prediction against a zero actual return.
14. Tiny nonzero return formatting.
15. Strict v2 validation.
16. Schema-v1 compatibility.
17. Publication clock regression protection.
18. Atomic private candidate preparation.
19. No private evidence leakage.

### Frontend

20. Latest predictions and latest scored forecasts appear separately.
21. Correct BTC and ETH market assignment.
22. No invented values when scored observations are absent.
23. Responsive mobile rendering.
24. Accessible labels and keyboard navigation.
25. Browser refresh, stale and failed-network states.
26. Existing aggregate evaluation unchanged.
27. Homepage headline uses the exact approved wording.
28. Existing Field Guide links and titles are preserved.
29. Published editorial SHA-256 approvals remain unchanged.
30. Search metadata and sitemap remain correct.

Run all relevant checks:

- Python exporter tests
- Frontend tests
- ESLint
- TypeScript
- Prettier
- Production static build
- Export/publication audit
- Local Wrangler smoke tests
- Documentation-link validation

Use synthetic fixtures for deterministic testing.

Use genuine retained evidence only when a read-only source is authorised.

Never publish synthetic fixtures.

## 10. Deployment and migration plan

Prepare but do not execute the future production migration.

Document:

- New v2 contract validation
- Separate R2 object requirements
- Bucket/key permission implications
- Publisher changes
- Independent HTTPS checker changes
- Website build-time configuration
- Candidate Worker verification
- Timely/late cohort consistency
- Dual-running v1 and v2
- Migration sequencing
- Rollback to v1
- Eventual v1 retirement, only after separate approval

The current v1 feed must continue refreshing throughout development.

Do not assume existing R2 credentials permit a second key.

Do not broaden permissions or modify credentials automatically.

Do not install a production publisher or change Lightsail timers in this stage.

Do not deploy a v2 website before genuine v2 publication and validation have been separately approved.

### Cloudflare release safeguards

Preserve the candidate-only deployment command:

`pnpm exec wrangler versions upload`

The release process remains:

1. Commit approved changes.
2. Push to GitHub.
3. Verify exact-SHA Python and frontend CI.
4. Build and upload a candidate.
5. Validate the candidate and its source identity.
6. Obtain explicit owner promotion approval.
7. Promote the exact candidate.
8. Verify the public website.

These production steps are **not authorised for execution in Stage 5B.9**.

## 11. Search indexing and SEO safeguards

The website is now publicly launched and indexing-enabled.

The owner has successfully submitted the sitemap to Google Search Console.

Preserve:

- Canonical www URLs
- Page-specific descriptions and titles
- Open Graph metadata
- `index, follow` for the intended production www build
- The 13-page public sitemap
- The existing `robots.txt` sitemap reference
- Correct 301 redirects from apex to www and HTTP to HTTPS

Do not make public preview or candidate versions indexable.

Production indexing activation is not permission to expose duplicate candidate domains.

Use the existing `BADGER_SEARCH_INDEXING` gate appropriately during local testing.

Ensure that noindex local/candidate builds remain possible.

Do not introduce a second canonical domain.

Do not modify Cloudflare crawler settings, DNS, redirects or Google Search Console.

## 12. Documentation

Create:

`docs/stage-05b9-latest-scored-forecast.md`

Document:

- The updated user experience
- Homepage copy change
- Exact source-selection algorithm
- Scientific interpretation
- Contract-v2 design
- Data provenance safeguards
- Test results
- Screenshots
- Migration plan
- Rollback plan
- Known limitations
- Outstanding production decisions

Update existing architecture documentation only where necessary.

Preserve historical reports as historical evidence.

Archive this complete prompt at:

`prompts/stage-05-web/011-latest-scored-forecast.md`

Update:

`prompts/README.md`

## 13. Hard boundaries

This stage may modify local application code, tests and documentation.

Do not:

- Commit or push
- Deploy to Cloudflare
- Upload public R2 objects
- Overwrite `forward-v1.json`
- Change R2 credentials or bucket permissions
- Modify DNS
- Change Cloudflare release settings
- Enable paid infrastructure
- Modify Lightsail timers or services
- Write to production research directories
- Retrain models
- Change scoring methodology
- Modify frozen protocols
- Recalculate historical backtests
- Modify published article source bytes
- Change editorial SHA-256 approvals
- Reconfigure Google Search Console
- Publish artificial forecasts or outcomes

Production inspection is read-only.

Stop before any public feed migration, website promotion or production infrastructure change.

## 14. Completion report

Provide:

1. Summary of the new Latest Scored Forecast feature.
2. Screenshot of the BTC and ETH scored-forecast displays.
3. Screenshot of the revised homepage Field Guide section.
4. Exact selection and provenance rules.
5. Contract-v2 design and v1 compatibility.
6. Scientific interpretation and methodology safeguards.
7. Test results.
8. Local build validation.
9. Complete changed-file inventory.
10. Required production migration steps.
11. Known limitations and outstanding decisions.
12. Recommended Conventional Commit message.

Explicitly distinguish genuine production evidence from synthetic test examples.

Stop for owner review.

**Success means that the new Latest Scored Forecast feature and the revised homepage headline are locally implemented and validated, while the live website, search indexing, editorial approvals and existing forward-v1 pipeline remain operational and unchanged.**
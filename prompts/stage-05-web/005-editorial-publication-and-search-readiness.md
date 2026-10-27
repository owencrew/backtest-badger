# Backtest Badger — Stage 5B.3: Editorial Publication and Search Readiness

## Objective

Prepare all four existing Field Notes and all three Field Guides for publication in the first public release of Backtest Badger.

**The owner explicitly approves publication of all seven existing articles, subject to the final accuracy, security and link checks specified below.**

Preserve the existing SHA-256 publication gate, scientific results, website design and Cloudflare Workers Static Assets architecture.

Prepare search-engine metadata for the eventual launch at:

https://www.backtestbadger.com

Do not deploy publicly, modify DNS, commit or push.

The desired result is a fully working production static export containing all seven approved articles, ready for owner review and the next deployment stage.

## 1. Starting context

Repository:

`~/Code/backtest-badger`

Starting implementation:

- Next.js 16 with static export
- React and TypeScript
- Existing semantic CSS design system
- TradingView Lightweight Charts
- Cloudflare Workers Static Assets
- Wrangler
- GitHub Actions Python and frontend CI

Latest verified green commit:

`af247362260a982ed59514e321cc18984b58004f`

Both GitHub Actions workflows passed at this commit.

Read:

- `AGENTS.md`
- `web/AGENTS.md`, if present
- `README.md`
- `web/README.md`
- `docs/field-notes/README.md`
- `docs/stage-05b2-history-and-launch-readiness.md`
- `docs/deployment/website-cloudflare-workers.md`
- `web/lib/content.ts`
- `web/content/publication-approvals.json`
- Existing frontend publication/export tests
- All seven article sources
- Relevant scientific source reports

Inspect Git status before making changes.

Preserve existing uncommitted work.

## 2. Owner publication approval

The owner has authorised publishing all four Field Notes:

1. `001-when-market-data-isnt-complete.md`
2. `002-when-a-backtest-meets-trading-costs.md`
3. `003-the-price-of-changing-your-mind.md`
4. `004-one-minute-can-change-a-backtest.md`

And all three Field Guides:

1. `001-what-is-backtesting.md`
2. `002-understanding-performance-metrics.md`
3. `003-from-forecasts-to-trades.md`

The four Field Notes are in:

`docs/field-notes/`

The three Field Guides are in:

`web/content/guides/`

All seven were previously reviewed during Stage 5B.2 and considered technically suitable for publication.

Nevertheless, verify their final source bytes and content before recording approval.

### Editorial constraints

Preserve:

- Original research findings
- Historical figures
- Model descriptions
- Transaction-cost assumptions
- Evidence provenance
- Research limitations
- The distinction between historical and prospective evidence
- Original article dates

Do not rewrite an article solely to improve its tone.

Minor grammatical, formatting or broken-link corrections are permitted where unambiguous.

If any substantive scientific or factual correction is necessary, do not silently make it and approve the new text. Report the issue and leave that article pending further owner approval, while completing the other eligible articles.

Do not invent:

- New backtest results
- Market predictions
- Forecast accuracy statistics
- Trading performance
- Model-validation outcomes
- Publication dates representing a deployment that has not happened

This stage approves content for the next production release. It does not claim that the public website is already deployed.

## 3. Verify article dependencies

Read the complete source of each article.

Build an explicit inventory of all Markdown links, including:

- Relative article links
- Links to research documentation
- Internal website routes
- Heading anchors
- External citations
- GitHub source-report links

Verify all destinations.

### Specific Field Note dependencies

Field Note 004 links to Field Note 003.

Field Note 003 links to Field Note 002.

All three will be published, so these links should work on the public website.

Field Note 001 references Stage 1B.3 research documentation.

Field Note 002 references the Stage 2B and Stage 2C research reports.

Verify the actual filenames and Markdown anchors against the repository.

Confirm that existing Markdown link conversion creates correct production URLs, including trailing slashes and heading fragments.

All seven articles must remain accessible through direct URL navigation.

Do not introduce dead article links or links to unpublished drafts.

If a source link cannot be verified, identify it precisely and either correct it where unambiguous or report the blocker.

## 4. Apply the existing publication gate

The current production publication policy requires:

1. Source status equals `Published`.
2. The source file's complete UTF-8 SHA-256 equals an explicit approval recorded in `web/content/publication-approvals.json`.

Preserve this exact principle.

### Important source-format detail

Field Notes 001 and 002 use metadata such as:

`- **Publication status:** Draft`

Field Notes 003 and 004 currently use:

`Publication status: Draft`

The Field Guides use Markdown metadata.

Inspect the parser before updating statuses.

Use the supported source format consistently, and confirm that each article's status is correctly recognised.

Do not accidentally introduce publication metadata into article-body prose.

### Approval procedure

For each eligible article:

1. Finish the final approved source text.
2. Set its publication status to `Published`.
3. Compute SHA-256 over the complete final source bytes, including metadata and line endings.
4. Add its exact slug and SHA-256 to the correct collection in `web/content/publication-approvals.json`.
5. Verify that the loader includes it in production.
6. Verify that a mismatched hash excludes the article.
7. Verify that changing its status away from Published excludes it even with a matching approval record.

The approval file should contain exactly four Field Notes and three guides.

Do not weaken `publicationAllowed()`.

Do not implement a build-time function that automatically updates approval hashes whenever article files change.

**An article edit after approval must invalidate its approval until deliberately reviewed and reapproved.**

Preserve fail-closed behaviour for unknown environments and unapproved future articles.

Keep future Field Notes and Guides as Draft by default.

## 5. Update editorial indexes

Update:

`docs/field-notes/README.md`

Make the status inventory accurate.

Distinguish approved-for-production content from the website's actual deployment status.

Do not claim a public publication date or deployed website URL before launch.

Add a short editorial release record documenting:

- Seven article filenames
- Final slugs
- Source status
- SHA-256 approval identity
- Original article dates
- Owner approval for the initial website release
- Final checks performed

Avoid unnecessary duplication of article content in documentation.

## 6. Field Notes presentation

The Field Notes index should feature:

**004 — One Minute Can Change a Backtest**

The remaining articles should appear newest first:

- 003 — The Price of Changing Your Mind
- 002 — When a Backtest Meets Trading Costs
- 001 — When Market Data Isn't Complete

The featured note should be selected by the existing newest-eligible-article logic, not a hardcoded slug.

Verify:

- Featured image/illustration labels
- Article title
- Date
- Excerpt
- Reading-time estimate
- Navigation URL
- Related articles
- Full article layout
- Markdown tables and headings
- Internal and external links

The homepage should feature approved Field Notes rather than production placeholders.

Remove development-only draft messaging from published article displays.

Do not remove the publication gate.

## 7. Field Guide presentation

Publish all three introductory guides:

- What Is Backtesting?
- Understanding Performance Metrics
- From Forecasts to Trades

Verify the Field Guide index, guide cards and individual article layouts.

Ensure descriptions remain accurate.

The broader learning-map topics are educational subjects or planned additions, not necessarily implemented trading-platform functionality.

Do not imply that equities, derivatives, new trading strategies or an interactive trading service are already supported.

Preserve the existing distinction between educational content and actual platform capabilities.

## 8. Search-engine and social metadata

Prepare the website for public discovery once deployed to:

`https://www.backtestbadger.com`

The initial Cloudflare deployment will first be reviewed on a workers.dev hostname.

### Metadata requirements

Review Next.js metadata handling in the current installed version.

Implement suitable metadata for:

- Homepage
- The Burrow
- The Dig
- Field Notes index
- Individual Field Notes
- Field Guide index
- Individual Field Guides
- About / Methodology

Add descriptive and accurate:

- Page titles
- Meta descriptions
- Canonical URLs
- Open Graph metadata
- Twitter/X card metadata where appropriate

Use the approved article titles and actual article content.

Descriptions should be concise, readable and distinct between pages.

Avoid automated descriptions that contain raw Markdown syntax, internal filesystem paths or irrelevant implementation-stage information.

For the canonical website origin, use:

`https://www.backtestbadger.com`

Canonical paths must be page-specific.

For example:

- `/`
- `/burrow/`
- `/dig/`
- `/field-notes/`
- `/field-notes/<actual-slug>/`
- `/field-guide/`
- `/field-guide/<actual-slug>/`
- `/about/`

Do not assign the homepage as the canonical URL for every page.

Do not invent article URLs: derive them from the real source slugs.

### Search indexing boundary

The current root layout uses:

`robots: { index: false, follow: false }`

**Keep indexing disabled for the initial workers.dev launch candidate.**

Prepare a simple, documented release-time mechanism to enable indexing once the www domain is live, the website has been verified and the owner explicitly approves public indexing.

Do not turn on indexing merely because source articles are now approved.

Avoid accidentally treating workers.dev/version-preview URLs as canonical public pages.

If an environment-based indexing switch is used, it must default safely to noindex, be resolved at build time for this static export, and require deliberate launch configuration.

Explain how to review the emitted HTML and robots instructions.

Do not introduce a dynamic Worker application solely to manage SEO metadata.

### Sitemap

Prepare a sitemap containing only:

- Existing public site routes
- The seven explicitly approved article routes

Exclude:

- Draft articles
- Reserved publication-pending routes
- Development paths
- Test paths
- Private data routes
- Worker preview URLs

The sitemap should be generated from eligible content, not from an unrestricted directory listing.

Preserve the ability for future article approvals to update the sitemap correctly.

If the sitemap should not be exposed or submitted until public launch, document the activation step.

Review robots.txt behaviour for consistency with the current noindex policy.

Do not create contradictory indexing signals.

### Open Graph imagery

Prefer an existing approved brand asset where suitable.

The original badger engraving's public distribution rights are not yet confirmed.

Do not add new public promotional images using that artwork unless rights are established.

If necessary, prepare metadata without a custom Open Graph image and record the outstanding artwork decision.

## 9. Preserve Workers deployment readiness

The frontend must remain compatible with:

**Cloudflare Workers Static Assets**

Do not replace this with Cloudflare Pages.

Retain:

- Next.js static export
- Existing `web/wrangler.jsonc`
- Pinned Wrangler tooling
- Existing static export preparation
- Trailing-slash behaviour
- Genuine HTTP 404s
- Frontend GitHub Actions workflow
- Python CI workflow
- Existing market charts and forecast contracts

Do not add server-side rendering, FastAPI, a CMS or another backend service.

Do not modify the Lightsail production environment.

The Burrow should continue displaying genuine Binance observations.

The public Lightsail forecast snapshot remains unconnected and should still be labelled unavailable.

Historical research results in The Dig must remain unchanged.

## 10. Tests and acceptance criteria

Run the existing applicable checks:

- Frozen pnpm installation where needed
- ESLint
- TypeScript
- Prettier
- Production Next.js static build
- Frontend unit tests
- Publication approval tests
- Production export audit
- Local Wrangler HTTP smoke tests
- Relevant repository Ruff checks if Python tooling changes
- Markdown link validation

### Publication tests

Add or extend focused tests to establish:

1. Exactly four Field Notes are eligible in production.
2. Exactly three Field Guides are eligible in production.
3. All seven status values are Published.
4. All seven exact SHA-256 approvals match.
5. A changed source hash is rejected.
6. A Draft with a matching hash is rejected.
7. Unknown environments fail closed.
8. A future unapproved article remains excluded.
9. Published 004 is the featured Field Note.
10. All published article routes exist in the production export.
11. No reserved publication-pending routes remain publicly accessible.
12. No private research files, secrets or fixtures leak into static assets.
13. Approved source links resolve correctly.
14. SEO metadata does not reference development URLs or nonexistent article routes.

Do not remove the existing negative publication-leakage tests simply because all seven current sources are approved.

Preserve their usefulness for future drafts.

### Local Workers verification

Build the production static export and serve it using local Wrangler.

Verify:

- Homepage
- Field Notes index
- All four Field Note routes
- Field Guide index
- All three Field Guide routes
- About
- The Dig
- The Burrow
- Unknown article routes returning genuine 404s
- Internal navigation between related notes
- Article links from the homepage
- Correct URLs, metadata and canonical paths
- Desktop and mobile layouts

Inspect actual generated HTML rather than relying only on Next.js development rendering.

Confirm there are no draft banners on the seven approved article pages.

Retain visible uncertainty and limitations in the research prose.

### Scientific and CI boundary

Do not modify frozen science or numerical results.

The unchanged full Python CI suite remains mandatory on GitHub.

Local frontend tests do not replace successful GitHub Actions verification after the eventual commit.

Do not claim CI has passed for uncommitted work.

## 11. Documentation

Create:

`docs/stage-05b3-editorial-publication.md`

Document:

- Owner approval scope
- All seven exact publication identities
- Editorial/source-link review
- Status transitions
- SHA-256 calculation and verification
- New production routes
- Featured note selection
- Search metadata
- Sitemap and robots behaviour
- Remaining public-launch decisions
- Tests performed
- Any limitations

Update:

- `docs/field-notes/README.md`
- `web/README.md`
- `docs/deployment/website-cloudflare-workers.md`
- `prompts/README.md`

Make only the necessary documentation changes.

Archive this complete prompt verbatim at:

`prompts/stage-05-web/005-editorial-publication-and-search-readiness.md`

Do not reconstruct or alter earlier archived prompts.

## 12. Remaining launch boundaries

This task DOES authorise:

- Reviewing all seven articles
- Making minor editorial corrections
- Setting approved articles to Published
- Recording exact final SHA-256 approvals
- Updating production editorial routes and metadata
- Preparing search indexing and sitemap functionality
- Local build and Workers validation

This task DOES NOT authorise:

- Git commit
- Git push
- Public Cloudflare deployment
- Remote Workers preview upload
- DNS or GoDaddy changes
- Search-indexing activation
- Enabling public forecast exports
- Lightsail access or changes
- Scientific model changes
- Historical backtest execution
- Automatic paper trading
- Payments or paid services

Unresolved substantive content issues or artwork rights must be reported rather than silently approved.

## 13. Final report

When finished, provide:

1. The complete list of seven approved articles.
2. Source slugs and final SHA-256 hashes.
3. Any editorial changes made.
4. Link and source-report verification results.
5. Published homepage, Field Notes and Field Guide behaviour.
6. Confirmation that Field Note 004 is featured.
7. Canonical and social metadata implemented.
8. Sitemap and robots/indexing behaviour.
9. Production-export and Wrangler test results.
10. Remaining owner launch decisions.
11. Files changed.
12. Recommended Conventional Commit message.

Stop for owner review without committing, pushing or deploying.

**The next stage will be the first explicitly authorised Cloudflare Workers deployment of Backtest Badger.**
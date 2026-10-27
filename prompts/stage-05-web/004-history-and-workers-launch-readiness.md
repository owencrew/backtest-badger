# Backtest Badger — Stage 5B.2: Full Market History and Cloudflare Workers Launch Readiness

## Objective

Prepare Backtest Badger for its first public launch at:

**https://www.backtestbadger.com**

We have decided to use **Cloudflare Workers Static Assets**, NOT Cloudflare Pages.

Retain the existing Next.js frontend, React, TypeScript, CSS design system and charting implementation. We are not migrating to Vite, Tailwind or a new framework in this stage.

Our priorities are:

1. Add 1Y and ALL historical BTC/ETH chart ranges.
2. Configure Cloudflare Workers Static Assets and Wrangler.
3. Preserve the existing website, branding and research integrity.
4. Establish reliable frontend CI and deployment preparation.
5. Review editorial publication readiness.
6. Prepare the first launch at `www.backtestbadger.com`.

This stage must produce a locally tested, deployment-ready website and an accurate launch runbook.

**Do not deploy publicly or change DNS without separate owner authorisation.**

Prioritise getting a high-quality initial website launched quickly. Avoid unnecessary infrastructure and major refactoring.

## 1. Starting context

Repository:

`~/Code/backtest-badger`

Latest verified green CI baseline:

`7b1d7cd57341fbdcd6ce544826fbd98db9eccf67`

Successful GitHub Actions run:

`40248197609`

Read:

- `AGENTS.md`
- `web/AGENTS.md`, if present
- `README.md`
- `web/README.md`
- `docs/stage-05a-website-design.md`
- `docs/stage-05b-market-dashboard.md`
- `docs/stage-01b3-full-history.md`
- `docs/stage-02a-research-dataset.md`
- `docs/development-handoff.md`
- Current frontend, tests and GitHub Actions configuration

Check Git status before changing anything.

Preserve uncommitted work and all existing scientific code and research evidence.

## 2. Preserve the existing technology stack

Current frontend:

- Next.js 16 with static export
- React
- TypeScript
- Existing semantic CSS and design tokens
- TradingView Lightweight Charts
- Markdown-backed editorial content
- pnpm with a committed lockfile

Continue using this stack.

Do not introduce Vite, Tailwind CSS, Astro, another router, a CMS or a new component framework.

Do not migrate to server-rendered Next.js or add an application server.

The website should continue exporting static HTML, JavaScript, CSS, images and other approved assets to `web/out/`.

We want Cloudflare Workers as the hosting platform, but **we do not need server-side Worker execution for the initial website**.

Preserve the ability to introduce lightweight Worker endpoints in future, where justified.

Keep Python research workloads and PostgreSQL on AWS Lightsail.

## 3. Expand The Burrow's historical market charts

The current Burrow supports BTCUSDT and ETHUSDT using Binance Spot public data.

Existing ranges:

- 1D — 5-minute candles
- 7D — 30-minute candles
- 30D — hourly candles
- 90D — four-hour candles

Add:

- **1Y — daily candles**
- **ALL — weekly candles**

ALL History should show Binance Spot listing-era prices from August 2017 to the latest available observations, subject to actual API availability.

The repository also contains previously acquired and validated four-hour research data from 2017–2026, with documented gaps.

Do not expose the scientific research database or private evidence to construct the website chart.

Continue using the official Binance market-data-only public API.

### Historical-data handling

Verify Binance's current API specification.

Use a sensible candle interval for each range.

For ALL History, weekly candles should be sufficient to display almost nine years of BTC/ETH price history efficiently.

Support bounded pagination only if required.

Avoid downloading multi-year minute-level data into visitors' browsers.

Preserve strict validation of:

- Binance market identity
- UTC timestamps
- Chronological order
- Duplicates
- OHLC consistency
- Missing intervals
- Current incomplete candles
- Provider/server clock
- Response boundaries

Correctly handle Binance's weekly calendar boundaries. Weekly candles cannot simply inherit the existing Unix-epoch modulo alignment rule.

Handle the initial listing-era partial week correctly.

Do not classify dates before listing as missing candles.

Do not interpolate gaps or fabricate historical observations.

### Efficient refresh

Keep five-minute refreshes for recent market observations.

Avoid repeatedly downloading the entire historical archive at every refresh.

Distinguish stable historical candles from the changing recent tail.

Use straightforward browser caching where useful. Keep this lightweight.

Maintain cancellation, hidden-page polling behaviour, timeout handling and stale-data warnings.

Failed requests must not silently replace a valid snapshot or advance its timestamp.

### Chart presentation

Retain:

- BTC/ETH selection
- Candlestick and line modes
- Crosshair and UTC tooltips
- Accessible keyboard inspection
- Pan, zoom and reset
- Genuine Binance Spot source labels
- TradingView attribution
- Responsive desktop/mobile design

Add the two new ranges without overcrowding the existing controls.

Display the actual available history boundaries where helpful.

Maintain the charcoal, forest-green, warm-sand and slate-grey visual identity.

## 4. Cloudflare Workers Static Assets configuration

We are switching the hosting target from Cloudflare Pages to **Cloudflare Workers Static Assets**.

Use Cloudflare's current official documentation to verify the configuration.

The existing Next.js build uses:

`output: "export"`

It produces static files under:

`web/out/`

Create a minimal Wrangler configuration in the `web/` application.

A likely starting configuration is:

```jsonc
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "backtest-badger-web",
  "compatibility_date": "2026-10-26",
  "assets": {
    "directory": "./out",
    "html_handling": "auto-trailing-slash",
    "not_found_handling": "404-page"
  }
}
```

Treat this as a starting point, not an unverified final configuration.

Verify it against the installed Wrangler version and actual exported Next.js routes.

Prefer an **assets-only Worker** with no `main` script, API handler or Worker-side application runtime.

Do not configure SPA fallback for the pre-rendered Next.js routes.

The existing 404 page should return a real 404 response.

### Local Workers verification

Install Wrangler as a pinned local development dependency, using pnpm and the existing lockfile.

Select a current stable version compatible with the project's Node version.

Use `wrangler dev` or the currently recommended local Workers Static Assets preview workflow.

Verify:

- Homepage
- The Burrow
- The Dig
- Field Notes
- The Field Guide
- About / Methodology
- Nested article routes
- Static images and fonts
- Direct navigation and browser refresh
- Correct redirects and trailing slashes
- Genuine Binance chart requests
- Proper 404 behaviour

The local Workers preview must behave like the exported production website, not the Next.js development server.

Do not execute `wrangler deploy`, `wrangler preview`, `wrangler deploy --temporary` or any command that creates a remote deployment in this stage.

Local execution only.

## 5. Cloudflare Workers Builds

Our intended long-term workflow is:

**GitHub → CI verification → Cloudflare Workers → www.backtestbadger.com**

Use Cloudflare Workers Builds for automated builds and preview deployment workflows when appropriate.

Review Cloudflare's current support for:

- GitHub integration
- Monorepositories
- Production branch selection
- Build and deploy commands
- Worker preview deployments
- Version history
- Rollback
- Build watch paths
- Node and pnpm versions

### Determine exact build settings

The expected configuration is approximately:

- GitHub repository: `owencrew/backtest-badger`
- Worker name: `backtest-badger-web`
- Production branch: `main`
- Root directory: `web`
- Node.js: compatible Node 22 or newer
- Package manager: pinned pnpm
- Install command: `pnpm install --frozen-lockfile`
- Build command: `pnpm build`
- Static assets directory: `./out`
- Deployment tool: Wrangler

Verify the exact settings rather than assuming they work.

The Cloudflare Worker name and Wrangler configuration must match.

Pay particular attention to the Markdown content loader reading:

`../docs/field-notes/`

Verify that Workers Builds can access this relative directory when building the monorepository.

Make the smallest necessary adjustment if required, without duplicating raw research artifacts into the public site.

### CI gating — important

Workers Builds can deploy automatically when a commit is pushed to its configured production branch.

Our GitHub Actions checks may still be running at that moment.

We must not assume Workers Builds waits for GitHub CI to pass.

Design a simple, reliable workflow ensuring unverified commits do not automatically replace the public production website.

Consider:

- Workers Builds for branch previews and compilation
- Uploading production candidate versions without automatically promoting them
- Explicit promotion after green CI and owner review
- Or GitHub Actions deployment gated by the required frontend checks, if this is simpler and more reliable

Explain the trade-offs and recommend the least complicated solution.

Use Workers Builds where it genuinely helps, but don't build two competing deployment systems.

Do not enable automatic production deployment during this stage.

## 6. Frontend GitHub Actions

The existing Python CI is now green after resolving temporary-storage exhaustion.

Preserve that fix and the existing scientific tests.

Add a dedicated frontend CI job or a small separate workflow.

The frontend checks should include:

- Locked pnpm installation
- ESLint
- TypeScript
- Frontend unit tests
- Production static build
- Publication-leakage checks
- Workers configuration validation or local smoke tests where feasible

Use a supported Node version and pinned pnpm version.

Frontend checks should run independently from the large Python test suite where practical.

Do not weaken Python CI or skip guarded tests.

Avoid paid runners and unnecessary workflow complexity.

## 7. Publication readiness

The site includes four Field Notes and three Field Guide articles.

The editorial system requires both:

1. `Published` source status
2. A matching SHA-256 approval entry

Preserve this fail-closed publication gate.

Read all existing articles and assess accuracy, links, grammar, explanatory quality and suitability for public release.

Pay particular attention to:

**Field Note 004 — One Minute Can Change a Backtest**

This should be the featured Field Note when eligible.

Provide a concise editorial review and identify which articles are ready for owner approval.

Do not automatically mark articles Published or add approval hashes.

Do not silently rewrite scientific findings.

Ensure the production export contains no unapproved draft article bodies, routes or metadata.

If the current production build contains empty Field Notes and Field Guide sections, recommend a minimal publication set for the first launch.

Make sure the initial public website does not look unfinished merely because the development preview has more content than the approved production build.

### Mascot asset

Confirm the original engraved badger reference is displayed correctly.

The owner supplied the image, but public distribution rights must still be confirmed.

Flag any unresolved licensing question.

Do not replace the mascot with unrelated artwork.

## 8. Public website correctness

Retain all existing design and functionality.

Ensure the website distinguishes:

- Historical simulations
- Genuine prospective forecasts
- Scored forecast outcomes
- Planned paper trading
- Real-money trading, which is not implemented

The Burrow's Binance data should be genuine and accurately timestamped.

The forward prediction dashboard should remain unavailable until a reviewed public Lightsail snapshot is connected.

Do not invent forecast metrics or performance.

The Dig must preserve the exact verified 2024 results and existing Ridge explanation.

Do not modify frozen research data.

## 9. Workers custom domain and GoDaddy DNS plan

The intended public hostname is:

`www.backtestbadger.com`

Cloudflare Workers Custom Domains require the hostname to be within an active Cloudflare-managed DNS zone.

The domain is currently registered through GoDaddy.

Prepare an accurate migration and custom-domain runbook.

The preferred arrangement is:

- Keep GoDaddy as the domain registrar
- Add `backtestbadger.com` to Cloudflare DNS
- Carefully preserve existing DNS records
- Change the authoritative nameservers at GoDaddy only when authorised
- Configure the Worker Custom Domain for `www.backtestbadger.com`
- Verify managed HTTPS
- Redirect the bare apex domain to the www canonical hostname

Do not assume the external-DNS CNAME-only procedure used for Cloudflare Pages is sufficient for Workers Custom Domains.

### DNS precautions

Before nameserver migration, explain how to identify and preserve:

- Existing A, AAAA and CNAME records
- TXT verification records
- MX records
- SPF, DKIM and DMARC records
- Any other active domain services

Do not delete, replace or infer records.

Provide a checklist for verifying DNS after migration.

Prefer Cloudflare's normal custom-domain setup rather than routing traffic through Lightsail.

Do not perform the actual DNS migration or custom-domain activation in this stage.

## 10. Website launch and rollback runbook

Prepare a concise, practical owner-facing launch guide.

Cover:

1. Creating or accessing a Cloudflare account.
2. Adding the domain to Cloudflare DNS.
3. Configuring the Worker project and connecting GitHub.
4. Confirming exact build settings.
5. Preparing and verifying a non-production website build.
6. Testing published content and real Binance charts.
7. Confirming green GitHub CI.
8. Publishing the initial Worker version only after approval.
9. Connecting `www.backtestbadger.com`.
10. Configuring the bare-domain redirect.
11. Verifying HTTPS, routing and DNS.
12. Testing desktop/mobile from an external network.
13. Rolling back to a known-good Worker deployment.
14. Iterating through preview and reviewed production releases.

Be clear about which operations deploy immediately versus merely prepare or upload a candidate.

Do not accidentally publish a live website while testing launch readiness.

Keep the process achievable on Cloudflare's Free plan.

## 11. Validation

Run the applicable local checks:

- Frontend lint
- TypeScript
- Unit tests
- Formatting
- Production Next.js static build
- Workers Static Assets local preview
- Publication-leakage checks
- Relevant repository checks
- Documentation link validation

Test all six chart ranges for both BTC and ETH.

Verify real weekly candles from Binance, UTC week boundaries, historical coverage and recent-tail refresh.

Check missing-candle handling and error states.

Review the public production export for unapproved articles, private files and credentials.

Inspect desktop and mobile layout in a browser where available.

Do not claim a Cloudflare-hosted deployment was tested if only local Wrangler preview was used.

## 12. Documentation

Create:

`docs/stage-05b2-history-and-launch-readiness.md`

and:

`docs/deployment/website-cloudflare-workers.md`

Update:

- `web/README.md`
- Relevant project handoff documentation
- `prompts/README.md`

Archive this entire prompt verbatim at:

`prompts/stage-05-web/004-history-and-workers-launch-readiness.md`

Do not archive the earlier Cloudflare Pages version as the final selected prompt.

## 13. Hard boundaries

- No Git commit or push
- No public Cloudflare deployment
- No remote preview deployment without authorisation
- No DNS changes
- No GoDaddy changes
- No Lightsail access or modification
- No production PostgreSQL access
- No FastAPI implementation yet
- No Vite or Tailwind migration
- No new backend architecture
- No forecast regeneration or rescoring
- No historical trading backtests
- No modifications to frozen research evidence
- No automatic publication of editorial drafts
- No payments or paid services

The task is to make the existing frontend ready for launch on Workers Static Assets, not to create a new platform.

## 14. Final response

Report:

1. New 1Y and ALL market-chart behaviour
2. Exact candle intervals and verified data coverage
3. Handling of weekly boundaries and missing candles
4. Historical caching and refresh efficiency
5. Cloudflare Workers/Wrangler configuration
6. Local Workers preview results
7. Frontend CI additions and tests
8. Editorial publication recommendations
9. Exact Workers Builds configuration
10. Proposed CI-gated promotion workflow
11. GoDaddy/Cloudflare DNS migration steps
12. Remaining owner decisions for the initial launch
13. Files changed
14. Recommended Conventional Commit message

Stop for owner review before committing, pushing or deploying anything.

**Our next milestone after this stage is launching www.backtestbadger.com on Cloudflare Workers Static Assets.**
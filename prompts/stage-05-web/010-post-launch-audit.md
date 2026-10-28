# Backtest Badger — Stage 5B.8: Post-Launch Audit and Documentation Synchronisation

## Objective

Conduct a comprehensive but tightly scoped post-launch audit of Backtest Badger, verify that the public website and genuine forward-data pipeline are operating correctly, and update repository documentation to reflect the actual deployed infrastructure.

The website is now publicly live.

Do not implement new trading strategies, forecast models or major frontend features during this stage.

The objective is to establish a clean, trustworthy operational baseline before continuing development.

## 1. Current infrastructure

Repository:

`~/Code/backtest-badger`

Latest verified GitHub release-source commit:

`360c6130d3f304f275cb9f216cca4fa7c82b5976`

Both GitHub Actions workflows passed for this commit.

### Public website

`https://www.backtestbadger.com`

Hosted on Cloudflare Workers Static Assets.

Worker name:

`backtest-badger-web`

Deployment architecture:

- Next.js static export
- React and TypeScript
- Existing semantic CSS
- Cloudflare Workers Static Assets
- GitHub-connected Workers Builds
- Candidate uploads through `pnpm exec wrangler versions upload`
- Explicit owner promotion to production

### Domain management

GoDaddy remains the registrar.

Cloudflare is the authoritative DNS provider.

Nameservers:

- `brit.ns.cloudflare.com`
- `weston.ns.cloudflare.com`

The bare domain:

`https://backtestbadger.com`

redirects permanently to the www domain.

The redirect should preserve paths and query strings.

### Genuine forward feed

Permanent public endpoint:

`https://data.backtestbadger.com/forward-v1.json`

Cloudflare R2 bucket:

`backtest-badger-forward`

Public object:

`forward-v1.json`

The temporary `r2.dev` development endpoint has been disabled.

The website has been rebuilt and a new Worker version manually promoted, successfully restoring genuine forecast data from the permanent hostname.

### Lightsail

Existing research production server:

`ssh Ubuntu-1`

An isolated public-feed helper publishes validated snapshots approximately every ten minutes.

An independent HTTPS checker verifies the public object.

Both timers have been enabled and have previously completed successful scheduled runs.

The research collector and scorer remain separate services and must not be changed.

## 2. Read the existing repository documentation

Start with:

- `AGENTS.md`
- `README.md`
- `docs/development-handoff.md`
- `docs/deployment/website-cloudflare-workers.md`
- `docs/deployment/forward-feed-cloudflare-setup.md`
- `docs/stage-05b5-forward-feed-activation.md`
- `docs/stage-05b6-forward-dashboard-refinement.md`
- `web/README.md`
- `web/wrangler.jsonc`
- `web/lib/seo.ts`
- The frontend publication and export tests
- The existing prompt archive

Inspect the current Git working tree and preserve uncommitted work.

Distinguish what the repository documentation previously planned from what has now actually happened.

Do not assume a newer GitHub commit means the Lightsail research release has also been updated.

## 3. Verify the public website

Perform read-only checks against:

`https://www.backtestbadger.com`

Verify the main pages:

- Home
- The Burrow
- The Dig
- Field Notes
- Field Guide
- About

Verify all four approved Field Notes and all three approved Field Guides.

Confirm:

- The owner-supplied original mascot is displayed.
- Main navigation order is Home, The Burrow, The Dig, Field Notes, Field Guide, About.
- The homepage no longer displays "No hype" or "Honest negative results".
- Field Note 004 is featured.
- The full articles load directly.
- Unknown routes return genuine HTTP 404s.
- Trailing-slash navigation works.
- The website uses HTTPS.
- No unapproved drafts, fixtures or private artifacts are exposed.

Review desktop and mobile rendering where browser access is available.

Document any failures with exact affected URLs.

Do not make design changes solely for subjective preferences during this audit.

## 4. Verify The Burrow

Check that both BTCUSDT and ETHUSDT market charts retrieve genuine Binance observations.

Verify the six supported ranges:

- 1D
- 7D
- 30D
- 90D
- 1Y
- ALL

Confirm candle/line switching, timestamps and refresh behaviour.

For the forward section, verify:

- Both markets display.
- All four models are present.
- Forecast returns use correctly labelled basis points of log return.
- Source close, issuance and target timestamps are accurate.
- Pending and scored outcomes are distinguished.
- Primary timely-automated evaluation appears by default.
- Late-manual evaluation remains separate.
- Empty unattributed cohorts render correctly.
- Undefined metrics are not converted to zero.
- The Zero baseline has no invented directional accuracy.
- Stale and failed network requests produce truthful states.

Do not modify any scientific calculation, model recipe, timestamp or evaluation cohort.

## 5. Verify the permanent R2 feed

Fetch:

`https://data.backtestbadger.com/forward-v1.json`

Check:

- HTTPS and HTTP 200.
- Valid version-1 JSON.
- Both markets.
- All four models and three cohorts.
- Correct JSON content type.
- `Cache-Control: public, max-age=60, must-revalidate`.
- Appropriate CORS for `https://www.backtestbadger.com`.
- Evidence cutoff and generation timestamps.
- No unexpected private keys.
- No exposed credentials or private evidence.

Use the existing public-contract validator.

Where feasible, verify the public object against the independently validated publication identity.

Confirm through the browser Network inspector that the deployed Burrow requests the permanent data hostname.

The browser must not depend on the disabled temporary `r2.dev` endpoint.

Do not change the R2 bucket, permissions, credentials or CORS during this audit.

## 6. Verify scheduled publication and checker health

Read-only SSH inspection through `ssh Ubuntu-1` is authorised, subject to normal access approval.

Inspect:

```bash
systemctl list-timers --all 'backtest-badger-public-feed*'

systemctl is-enabled backtest-badger-public-feed.timer
systemctl is-enabled backtest-badger-public-feed-check.timer

sudo journalctl -u backtest-badger-public-feed.service --since '2 hours ago' --no-pager

sudo journalctl -u backtest-badger-public-feed-check.service --since '2 hours ago' --no-pager
```

Confirm:

- Both timers remain enabled.
- Recent scheduled exports succeeded.
- Independent checks report `public-feed-healthy`.
- Snapshot clocks advance across runs.
- New forecast values appear only following genuine model issuance.
- Outcomes are incorporated only after recorded scoring.
- Collector and scorer remain healthy.
- No recurring publication failures are apparent.
- Resource usage remains consistent with the measured operational baseline.

If any evidence is unavailable, report the limitation.

Do not restart services, change timers, install packages or make production writes.

Do not print secrets or private environment-file contents.

## 7. Audit Cloudflare release management

Verify the intended deployment configuration against the owner's actual Cloudflare dashboard settings where accessible.

The desired workflow is:

1. GitHub commit pushed.
2. GitHub Python and frontend CI run.
3. Workers Builds uploads a candidate.
4. Owner verifies the candidate and exact source SHA.
5. Owner manually promotes the selected version.
6. Public deployment is verified.

The configured deployment command should be:

`pnpm exec wrangler versions upload`

Verify that the existing live version corresponds to the intended, CI-approved source commit.

If the deployment identity cannot be obtained from read-only inspection, ask the owner to provide the relevant Cloudflare deployment information rather than inventing it.

Confirm that future GitHub pushes will not automatically promote new versions.

Do not modify Cloudflare configuration or trigger any build.

Document the manual promotion and rollback procedure clearly.

## 8. Audit DNS, HTTPS and redirects

Verify the publicly observable behaviour of:

- `https://www.backtestbadger.com`
- `https://backtestbadger.com`
- `https://data.backtestbadger.com/forward-v1.json`

Check that:

- The apex redirects to www using HTTP 301.
- The redirect preserves paths and query parameters.
- www does not redirect back to the apex.
- HTTPS certificates are valid.
- Both domains resolve through Cloudflare.
- The data endpoint resolves independently of the website Worker.
- No obsolete GoDaddy Website Builder destination remains in the intended public routing.

Do not modify DNS or registrar settings.

## 9. Search engine readiness

Inspect the deployed HTML, not just source code.

Confirm that public indexing is currently disabled as intended.

The site already has page-specific canonical metadata and an indexing gate controlled by:

`BADGER_SEARCH_INDEXING`

Do not enable indexing during this audit.

Review:

- Page titles
- Meta descriptions
- Canonical URLs
- robots directives
- Sitemap configuration
- Open Graph metadata
- Article metadata

Prepare a concise recommendation for when public indexing should be enabled.

The eventual production indexing activation must be separately owner-approved and validated on the actual deployed www website.

Do not change crawler policies merely to make audit checks pass.

## 10. Update documentation

Create:

`docs/stage-05b8-post-launch-audit.md`

This should contain:

- Actual production architecture.
- Verified public addresses.
- GitHub release commit and CI evidence.
- Cloudflare Worker and version identity where verified.
- Domain migration outcome.
- R2 and Lightsail operational status.
- Public website smoke-test results.
- Outstanding operational issues.
- Search-indexing status.
- Future development recommendations.

Update the current-state sections of:

- `README.md`
- `web/README.md`
- `docs/development-handoff.md`
- `docs/deployment/website-cloudflare-workers.md`
- `docs/deployment/forward-feed-cloudflare-setup.md`
- `docs/roadmap.md`, if its milestones require updating

Earlier stage reports are historical records. Preserve their original observations and limitations.

Where earlier guides describe planned operations as not yet completed, clearly distinguish their original stage scope from the current live status. Do not silently rewrite historical evidence.

The development handoff should now direct future Codex sessions to the live production architecture and the post-launch audit.

Archive this prompt at:

`prompts/stage-05-web/010-post-launch-audit.md`

Update `prompts/README.md`.

## 11. Future development backlog

Record but do not implement the following next feature:

**Latest Scored Forecast**

The Burrow currently highlights the latest issued prediction, which is usually pending because its target has not yet closed.

The proposed future enhancement should display the most recently completed and scored forecast separately from the currently pending prediction.

It should allow visitors to compare:

- Previous model predictions
- Actual observed return
- Forecast error
- Correct or incorrect directional prediction

This will likely require a reviewed extension of the public snapshot contract and exporter.

Preserve original evidence provenance and avoid changing scoring methodology.

Implementation belongs to a separate post-launch development stage.

Also record future research/platform improvements as backlog items without changing their current status.

## 12. Validation

For any documentation or code changes, run relevant checks:

- Documentation link validation
- Markdown formatting
- Frontend lint
- TypeScript
- Prettier
- Frontend tests
- Production static build
- Publication/export audit
- Local Wrangler smoke tests

Run targeted checks appropriate to the actual changed files.

Avoid unnecessary full historical research or backtest re-execution.

Keep all seven editorial SHA-256 approvals unchanged.

Do not edit published article source bytes.

## 13. Hard boundaries

This stage is read-only against production.

No:

- Git commits or pushes
- Cloudflare deployments
- Workers version uploads or promotions
- DNS changes
- R2 configuration changes
- Credential changes
- Lightsail service or timer modifications
- Research database writes
- Forecast model changes
- Backtest changes
- Public JSON schema changes
- Search-indexing activation
- New frontend features
- Paid infrastructure

Local documentation and test changes are permitted.

If a production problem is discovered, record its severity, supporting evidence and recommended fix. Do not automatically apply production changes.

## 14. Completion report

Provide:

1. Overall launch health assessment.
2. Public website results.
3. Forecast-feed health and freshness.
4. Lightsail scheduled publication results.
5. Worker version and release-management status.
6. DNS, HTTPS and redirect verification.
7. Indexing readiness.
8. Documentation changes.
9. Tests passed and limitations.
10. Outstanding issues prioritised by severity.
11. Recommended Conventional Commit message.
12. Suggested next development stage.

Stop for owner review.

**The intended result is a verified and fully documented production baseline for Backtest Badger, ready for continued development.**
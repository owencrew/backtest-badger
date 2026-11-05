# Backtest Badger — Stage 6A.2: Publish Study 002 in The Dig

## Objective

Turn The Dig into a polished research library featuring two genuine, independently verified historical trading studies:

- **Study 001 — The 2024 Ridge Sign Study**
- **Study 002 — Can a Slower Trend Beat the Noise?**

Create a dedicated Study 002 page at:

`/dig/study-002/`

The new page should showcase the genuine 2024 30-Day Trend research, including strategy explanations, performance comparisons, equity and drawdown visualisations, costs, trading activity, exposure and scientific limitations.

The result should feel like a professional quantitative research platform rather than a collection of static reports.

Preserve the existing Backtest Badger visual identity: dark charcoal, forest green, muted sage, warm sand, restrained typography and clean responsive layouts.

**The scientific research is already complete. This stage is frontend integration and editorial presentation, not another backtest.**

Implement, test, commit and push the verified website changes. The owner will manually review and promote the resulting Cloudflare Worker candidate.

Do not promote or roll back Worker versions automatically.

---

## 1. Starting context

Repository:

`~/Code/backtest-badger`

GitHub:

`owencrew/backtest-badger`

Expected Study 002 commit:

`04c485e6af74e52d0541ceab3a88ca0debb21346`

Commit message:

`feat(research): add study 002 daily trend backtest`

Both GitHub CI workflows were confirmed successful for that commit before this request.

Verify current HEAD, working-tree cleanliness and current CI state before editing. If HEAD has advanced, inspect those changes rather than resetting the repository.

Read:

### Repository instructions

- `AGENTS.md`
- `README.md`
- `web/README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`

### Verified Study 002 research

- `docs/studies/study-002-methodology.md`
- `docs/studies/study-002-config.json`
- `docs/studies/study-002-freeze.json`
- `docs/studies/study-002-slower-trend-results.md`
- `docs/studies/study-002-dig-draft.md`
- `docs/studies/study-002-field-note-draft.md`
- `docs/studies/study-002-assets/review-data.json`
- `docs/studies/study-002-assets/manifest.json`
- The six approved-source review charts under `docs/studies/study-002-assets/`

### Existing website

- `web/app/dig/page.tsx`
- `web/components/dig-explorer.tsx`
- `web/components/performance-chart.tsx`
- `web/lib/research.ts`
- `web/lib/seo.ts`
- `web/app/sitemap.ts`
- `web/lib/content.ts`
- `web/app/globals.css`
- `web/tests/research.test.ts`
- `web/tests/export.test.ts`
- Existing editorial components and mobile styles
- Cloudflare deployment documentation

Also read:

`docs/stage-04b2e5g-first-genuine-historical-backtest.md`

This remains the authoritative Study 001 result.

---

## 2. Scientific source of truth

Study 002 completed one genuine, authenticated 2024 historical backtest.

All six newly funded portfolios passed independent accounting verification.

The methodology and research configuration were frozen before the genuine run.

### Verified cumulative returns after costs

| Strategy | BTCUSDT | ETHUSDT |
|---|---:|---:|
| 30-Day Trend | +36.62% | +8.47% |
| Ridge Sign | −60.69% | −57.96% |
| Cash | 0.00% | 0.00% |
| Buy & Hold | +120.81% | +46.18% |

### Trading activity and costs

| Metric | BTCUSDT | ETHUSDT |
|---|---:|---:|
| Trend executions | 38 | 32 |
| Ridge executions | 1,140 | 998 |
| Trend attributed costs | 543.87 USDT | 422.61 USDT |
| Ridge attributed costs | 9,932.12 USDT | 9,239.49 USDT |
| Cost reduction | 94.5% | 95.4% |

### Maximum observed hourly drawdown

| Strategy | BTCUSDT | ETHUSDT |
|---|---:|---:|
| 30-Day Trend | 37.88% | 34.67% |
| Ridge Sign | 65.41% | 65.79% |
| Buy & Hold | 32.31% | 46.66% |
| Cash | 0.00% | 0.00% |

These are display summaries only.

All underlying numbers, units and exact Decimal strings must come from the committed scientific report and source-linked review data.

Do not substitute the rounded numbers above for authoritative retained values.

### Main research conclusion

**A slower rule cut the trading bill. It still missed much of the market's gain.**

The new strategy traded substantially less frequently and incurred around 95% less attributed costs than Ridge.

Both markets delivered positive 2024 returns, outperforming Ridge and Cash.

However, both underperformed Buy & Hold.

Bitcoin Trend also experienced a larger maximum observed hourly drawdown than Bitcoin Buy & Hold.

The comparison does not establish that reducing trading frequency alone caused the improved result, because the strategies used different signals and had different market exposure.

These results are exploratory retrospective simulations using a year already examined in earlier research.

They are not live trading results, a clean untouched out-of-sample evaluation or evidence of durable profitability.

Preserve these distinctions prominently throughout the page.

---

## 3. Redesign The Dig as a research library

Keep the existing route:

`/dig/`

Preserve the current Study 001 content, numerical results, interactive comparisons, methodology explanations and approved article links.

Do not move Study 001 to a new route in this milestone.

### New study navigation

Add a research-study selection section near the top of The Dig, following the introductory heading.

Create two visually balanced study cards.

### Study 001 card

**Study 001 — The 2024 Ridge Sign Study**

Suggested description:

"A machine-learning forecast becomes a trading decision. What happens when frequent position changes meet transaction costs?"

Metadata:

- Historical simulation
- Binance Spot BTC/ETH
- 2024
- Four-hour Ridge signals
- Evidence recorded 24 October 2026

Key finding:

"Frequent trading imposed a substantial cost burden and both accounts lost money."

The card should link to the existing Study 001 section on `/dig/`, using a stable anchor such as `#study-001`.

Do not remove or replace the existing study.

### Study 002 card

**Study 002 — Can a Slower Trend Beat the Noise?**

Suggested description:

"A simple 30-day trend rule trades once a day at most. Does slower decision-making translate into better results?"

Metadata:

- Historical simulation
- Binance Spot BTC/ETH
- 2024
- Daily 30-day trend
- Research run 1 November 2026

Key finding:

"About 95% lower trading costs than Ridge, but both markets still lagged Buy & Hold."

Link to:

`/dig/study-002/`

Use existing card styles and design tokens where practical.

A reusable `StudyCard` component is appropriate if it genuinely removes duplication.

Do not introduce a large generic experiment-management abstraction.

### Layout

On desktop:

- Two study cards in a clean two-column layout.
- Consistent typography, spacing and heights.
- Subtle hover and focus treatment.

On mobile:

- Cards stack vertically.
- Comfortable reading width and touch targets.
- No decorative emoji-style link icons.
- No horizontal overflow.

Distinguish the currently open study.

Preserve the existing Ridge charts and table behaviour beneath the new index.

---

## 4. Create the dedicated Study 002 page

Route:

`web/app/dig/study-002/page.tsx`

Use a clear page hierarchy.

### Section A — Introduction

Title:

**Can a Slower Trend Beat the Noise?**

Eyebrow or badge:

**Study 002 · Historical simulation**

Introductory copy should explain the research question in accessible terms.

Suggested opening:

"Our first study found that frequent trading was expensive. This time, we tested a simpler idea: follow the direction of the past 30 days, make one decision each day, and see what remains after trading costs."

Include the study date and a visible link to the full methodology.

### Section B — How the strategy works

Explain the rule simply:

1. At midnight UTC, compare the latest completed four-hour candle close with the close exactly 30 days earlier.
2. At 00:01 UTC, decide whether to target long or cash.
3. If the current price is higher, target long.
4. Otherwise, target cash.
5. A changed position trades hypothetically at the next native one-minute opening, 00:02 UTC.

Preserve the frozen details:

- Once-daily decisions
- Exactly 30 calendar days
- Positive trend means long
- Zero/negative trend means cash
- Continuous holdings between decisions
- No leverage or short selling
- No stop-loss, alternative thresholds or optimisation
- Separate 10,000 USDT accounts for each market
- 10 bps fee, 1 bp half-spread and 2 bps adverse slippage per side

Clarify that these are assumed historical execution references, not actual exchange fills.

Consider a restrained visual timeline for the midnight decision and 00:02 hypothetical execution.

Avoid unnecessary animation.

### Section C — Results at a glance

Show a compact comparison for BTCUSDT and ETHUSDT.

Include:

- 30-Day Trend return
- Ridge return
- Buy & Hold return
- Cash return
- Trend final marked portfolio value
- Trend maximum drawdown
- Trend trade count
- Trend attributed costs

Use a BTC/ETH segmented selector if appropriate.

For accessibility, ensure all values remain available in semantic tables, not just charts.

Do not pool the separate portfolios.

### Section D — Portfolio performance over time

Use the verified equity review chart as the starting visual reference.

Source:

`docs/studies/study-002-assets/equity.png`

If implementing an interactive chart, require the actual validated historical equity series and immutable source identity. Never reconstruct an equity path by interpolating monthly returns.

If the approved public data does not include the full verified time series in a safe presentation format, prefer a responsive, high-resolution static chart over invented interactivity.

Show the actual units, strategy legend, research period and explanatory caption.

### Section E — Risk and drawdown

Show:

- Verified drawdown chart
- Maximum observed hourly drawdowns
- Clear comparison to Buy & Hold and Ridge

Emphasise the mixed result:

- BTC Trend's 37.88% drawdown exceeded Buy & Hold's 32.31%.
- ETH Trend's 34.67% drawdown was lower than Buy & Hold's 46.66%.

Make it obvious that positive final returns do not imply a smooth equity curve.

### Section F — Exposure and trading behaviour

Show how often the strategy was invested versus in cash.

Use the verified exposure chart.

Highlight:

- BTC Trend was invested for 235 days.
- ETH Trend was invested for 190 days.
- Ridge was invested for fewer days in each market.
- Buy & Hold remained invested.

Explain that differences in exposure materially affect the strategy comparison.

Do not imply that trading frequency is the only variable that changed.

### Section G — Trading costs

Present the cost comparison as a prominent finding.

Consider a clean bar chart comparing the actual attributed costs of Trend, Ridge and Buy & Hold.

Break down the costs into:

- Fees
- Assumed half-spread
- Assumed slippage

Use the verified source values and include units.

Do not double-charge spread/slippage or treat attributed costs as an amount that can simply be added back to final equity to reconstruct a frictionless portfolio.

Include a concise interpretation:

"Trading less reduced costs substantially, but did not outperform the simpler Buy & Hold benchmark."

### Section H — Monthly performance

Display all 12 months of 2024.

Use the verified monthly return data.

Requirements:

- BTC/ETH selector or clearly separated market tables.
- Trend, Ridge, Buy & Hold and Cash where useful.
- Positive/negative formatting.
- Accessible numeric values.
- December explicitly labelled partial.
- No omitted negative months.

Keep the table usable on a 320px screen, with accessible horizontal scrolling if required.

The chart can supplement the table but must not replace it.

### Section I — What the results tell us

Explain the key research findings:

1. The fixed daily strategy generated far fewer trades.
2. Attributed costs fell dramatically.
3. Both markets produced positive returns after costs.
4. Both significantly underperformed Buy & Hold.
5. Drawdown results were mixed.
6. Slower signals still lagged some major rebounds.
7. Lower turnover cannot be isolated as the cause of improved returns.

The original report provides concrete examples, including the Bitcoin August 2024 reversals.

Use those examples where they improve understanding, but do not cherry-pick only favourable periods.

### Section J — Methodology, evidence and limitations

Include expandable detail explaining:

- Original data sources
- Study methodology
- Frozen configuration
- Historical execution assumptions
- Portfolio accounting
- Benchmark construction
- Risk-metric definitions
- Final observation at 31 December 2024 23:00 UTC
- Partial final day/month
- Existing limits of historical source availability
- Already-inspected 2024 evaluation period

Link to the full, committed research report and methodology on GitHub.

Use the immutable Study 002 research commit, or another verified immutable source revision, for reproducibility links.

Do not rely on floating `main` links where a stable research snapshot is needed.

A reader should be able to trace displayed financial claims to the committed report.

---

## 5. Public research data contract

Study 002 includes:

`docs/studies/study-002-assets/review-data.json`

This is an approximately 90 KB review-oriented data file, not an automatically approved public API contract.

It contains eight account records, monthly results, units, source identities and review metadata.

The raw private run includes a much larger evidence file. That private evidence must never be copied into the website.

### Requirements

1. Validate the original `review-data.json` against its committed manifest.
2. Validate its financial values against the authoritative Study 002 report.
3. Identify the minimum data required for website display.
4. Construct a small, explicit public presentation data module.
5. Preserve original Decimal strings for authoritative numerical values.
6. Convert to JavaScript numbers only for bounded chart presentation.
7. Carry source revision and relevant report hashes.
8. Reject unexpected, inconsistent or nonfinite values.
9. Never silently replace missing values with zero.
10. Preserve separate BTC and ETH account identities.

Do not simply copy all of the review package or its `unapproved_draft` metadata into `web/public`.

Prefer a narrow, reviewed public allowlist.

Suggested module:

`web/lib/study002.ts`

Use a descriptive typed interface and focused verification tests.

Preserve `web/lib/research.ts` as the authoritative existing Study 001 presentation module.

Do not change its verified Ridge results.

### Charts

The six existing charts are:

- `equity.png`
- `drawdown.png`
- `exposure.png`
- `activity.png`
- `costs.png`
- `monthly.png`

These are based on verified retained account evidence.

Inspect the existing assets and manifest before deciding which to use.

They are legitimate author-generated research visualisations, but are not necessarily the final website design.

Reuse the verified graphics when appropriate, with responsive sizing and readable labels.

If a more polished chart presentation is possible without sacrificing provenance, implement it using only actual verified data.

No synthetic chart values may be shown as genuine results.

Do not regenerate the economic backtest to produce charts.

---

## 6. Editorial quality

Use the scientific report and Study 002 integration draft as the factual basis.

The writing should be:

- Clear to technically curious visitors
- Rigorous and accurate
- Confident but not promotional
- Concise
- Transparent about negative findings
- Consistent with Backtest Badger's existing editorial style

Avoid phrases implying that the strategy is proven, profitable in general, or suitable for actual investment.

Prefer wording such as:

"Historical simulation"

"After assumed transaction costs"

"Observed hourly drawdown"

"One previously examined year"

"Not evidence of future performance"

Ensure all headline claims are supported directly by the report.

### Field Notes 005

The existing optional draft is:

`docs/studies/study-002-field-note-draft.md`

Title:

**A smaller trading bill is only part of the story**

Keep it as a draft.

Do not automatically:

- Copy it into the published Field Notes collection
- Change its status to Published
- Add its hash to `web/content/publication-approvals.json`
- Add a new Field Notes route or sitemap entry

We will handle its editorial review and publication in a separate small milestone.

Study 002's dedicated research page is the publication scope of this stage.

---

## 7. SEO and static export

The production website is hosted through a Next.js static export on Cloudflare Workers Static Assets.

The new page must work with the existing static-export architecture.

### New canonical route

`https://www.backtestbadger.com/dig/study-002/`

Add appropriate unique metadata:

- Page title
- Meta description
- Canonical URL
- Open Graph title and description
- Twitter summary metadata

Use `pageMetadata()` and existing site conventions.

Update `web/lib/seo.ts` and the public sitemap as required.

The current intended sitemap contains 13 URLs. Adding one approved Study 002 page should result in **14 URLs**, assuming no other public routes have been added.

The new route must be included in the production sitemap.

Preserve:

- www canonical hostname
- Existing seven approved editorial articles
- Homepage indexing
- Existing robots configuration
- Noindex candidate-build capability
- Production-only `BADGER_SEARCH_INDEXING=www-live-owner-approved` behaviour
- Existing redirects
- Disabled workers.dev and version-preview exposure

If new pages are generated in noindex local builds, their metadata must remain `noindex, nofollow` under the existing gate.

Do not expose a publicly indexable duplicate candidate hostname.

Do not modify Cloudflare dashboard settings.

---

## 8. Responsive design and accessibility

Study 002 should look polished on desktop and mobile.

Test at:

- 1440px
- 1024px
- 768px
- 390px
- 320px

Requirements:

- No document-level horizontal overflow
- No chart clipping
- Readable labels and table headings
- Semantic heading hierarchy
- Accessible tables
- Keyboard-operable market selection
- Clearly visible focus states
- Appropriate colour contrast
- Alt text and captions for charts
- No information conveyed by colour alone
- Touch-friendly controls
- Respect reduced-motion preferences

Avoid decorative emoji or floating link-arrow symbols on mobile.

Preserve the recent mobile navigation and hero-symbol fixes.

A deliberately clean, restrained experience is more valuable than adding complicated animation.

---

## 9. Regression and integrity tests

Add tests specifically for this release.

### Source verification

- Study 002 report exists.
- Source and asset manifest hashes match.
- Presentation values match the original report.
- BTC and ETH records remain separate.
- All expected strategies and benchmark rows are present.
- The 2024 period is correct.
- Monthly values cover the full year.
- December is labelled partial.
- No unsupported private fields are exported.
- Undefined numerical fields remain explicitly undefined.
- No synthetic placeholder results are presented.

### Study 001 preservation

- The original Ridge return values remain unchanged.
- Cash and Buy & Hold values remain unchanged.
- Study 001 table and chart remain functional.
- Existing research constants remain unchanged.
- Existing methodological explanations remain intact.
- The existing `/dig/` URL still works.

### Study 002 page

- `/dig/study-002/` is generated.
- The page has a unique canonical URL.
- Research classification is clearly visible.
- BTC and ETH selection works.
- Numerical display matches verified source values.
- Charts have appropriate labels.
- Costs and drawdowns are correctly represented.
- All monthly results remain accessible.
- Source links resolve.
- No private evidence paths leak into static assets.

### SEO and publication

- Production sitemap contains the expected new route.
- All 13 existing routes remain available.
- All seven existing editorial approval hashes remain unchanged.
- Unpublished Field Notes 005 is absent from public export.
- Local/noindex and production/indexed builds behave correctly.
- No unapproved research drafts or private artifacts leak into the export.

Run:

- `pnpm lint`
- `pnpm typecheck`
- `pnpm format:check`
- `pnpm test`
- `pnpm build`
- `pnpm test:export`
- `pnpm test:workers`

Run the relevant Python validation checks for the research presentation contract if necessary.

Do not rerun genuine Study 002 economics.

Also check documentation links and `git diff --check`.

---

## 10. Browser verification

Perform a local browser review of:

- The Dig index
- Existing Study 001 sections
- New Study 002 page
- All research charts
- BTC/ETH selector
- Mobile layout
- Keyboard navigation
- Source links

Capture screenshots showing:

1. The Dig with both study cards.
2. Study 002 desktop overview.
3. Study 002 equity and drawdown sections.
4. Study 002 trading-cost comparison.
5. Study 002 mobile layout.

Use actual verified Study 002 figures.

Do not fabricate screenshots or show synthetic example results as published evidence.

If browser automation is unavailable, document the limitation and use the available local preview/test mechanisms.

---

## 11. GitHub and Cloudflare workflow

This milestone authorises implementing, testing, committing and pushing the website changes.

### Git workflow

After all checks pass:

1. Inspect the complete changed-file inventory.
2. Confirm no private evidence or credentials are staged.
3. Confirm existing scientific methods and published articles are unchanged.
4. Commit the focused website changes.
5. Push to `main`.
6. Confirm both GitHub workflows pass for the exact new commit SHA.

Suggested commit:

`feat(web): publish study 002 in the dig`

Do not automatically promote the Cloudflare candidate.

### Cloudflare

Existing configuration:

- Worker: `backtest-badger-web`
- Production branch: `main`
- Root: `/web`
- Candidate-only upload: `pnpm exec wrangler versions upload`
- Forward feed: `https://data.backtestbadger.com/forward-v2.json`
- Production search-indexing flag: `www-live-owner-approved`

Preserve all these settings.

A GitHub push may create a new Ready Worker candidate automatically.

That is acceptable.

Do not manually deploy, promote, roll back or modify Cloudflare dashboard configuration.

The owner will review and manually promote the candidate after the implementation is complete.

The owner's manual production promotion is the final publication decision for Study 002.

### Rollback

Record the existing active Worker version before promotion.

The existing published website should remain operational and serve the existing Dig while the new candidate is built.

If Study 002 has a post-release problem, the owner can restore the previous known-working Worker version through Cloudflare Deployments.

No backend, R2 or Lightsail change should be necessary.

---

## 12. Documentation and deliverables

Create:

`docs/studies/study-002-web-publication.md`

Document:

- Site architecture changes
- Study 001 preservation
- Study 002 public data selection
- Source and asset verification
- Design decisions
- Scientific limitations
- New route and SEO
- Test results
- Browser screenshots
- Build/deployment status
- Manual Cloudflare promotion procedure
- Rollback procedure
- Remaining editorial decisions

Update appropriately:

- `README.md`
- `web/README.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- `prompts/README.md`

Archive this request at:

`prompts/stage-06-research/002-study-002-dig-publication.md`

Preserve the original Stage 6A.1 research report, frozen methodology and verified result identities.

Do not rewrite historical scientific documentation to reflect frontend design decisions.

---

## 13. Hard boundaries

Do not:

- Rerun the genuine Study 002 backtest
- Modify the frozen Study 002 strategy
- Change its lookback, threshold or costs
- Modify Study 001 methodology or results
- Regenerate Ridge forecasts
- Access Lightsail
- Change research collectors or scorers
- Modify R2 objects or feed configuration
- Change paper-trading functionality
- Place real trades
- Introduce new strategy performance claims
- Invent chart data
- Expose private account evidence
- Publish Field Notes 005
- Change the seven existing editorial approvals
- Modify DNS or Cloudflare build settings
- Automatically promote the website
- Add unnecessary frontend libraries
- Implement a generic backtesting application

Scope the work to a polished, source-verified Study 002 website integration.

---

## 14. Completion report

Provide:

1. Final Git commit SHA.
2. GitHub CI results.
3. Summary of the new Dig research-library structure.
4. Study 002 page architecture.
5. Verified source and presentation data identities.
6. Key scientific findings displayed.
7. Chart and accessibility implementation.
8. Mobile layout results.
9. Complete changed-file inventory.
10. Frontend test results.
11. Static export and sitemap verification.
12. Preservation of Study 001 and seven editorial approvals.
13. Confirmation that Field Notes 005 remains unpublished.
14. Confirmation that the existing v2 forward feed is unaffected.
15. Cloudflare candidate build/version details, if available.
16. Exact manual promotion and rollback instructions.
17. Known limitations and outstanding decisions.

### Definition of success

Stage 6A.2 is complete when:

- The Dig offers Study 001 and Study 002 as distinct research entries.
- Study 001 remains intact.
- Study 002 has a polished dedicated page.
- All displayed results come from verified historical evidence.
- Scientific limitations are prominent.
- Charts and data tables work on desktop and mobile.
- The production static export is valid.
- SEO and editorial safeguards remain intact.
- GitHub CI passes for the resulting commit.
- A new Cloudflare candidate is ready for the owner's manual promotion.

**Do not confuse a completed candidate with a production release.**

Stop after the verified code has been pushed and the deployment handoff is ready. The owner will handle the Cloudflare promotion.
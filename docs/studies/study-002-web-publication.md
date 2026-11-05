# Stage 6A.2 — Study 002 website publication candidate

Implementation and local validation: 4–5 November 2026 (Europe/London).
This is a **website candidate, not a production release**. The owner makes the
final Cloudflare promotion decision. The task authorises commit and push to main,
but no manual upload, deployment, rollback or dashboard configuration change.

## Architecture and editorial scope

The Dig at `/dig/` now starts with two balanced study cards. Study 001 remains on
that route at the stable `/dig/#study-001` anchor, with its original numerical
module, interactive chart/table, Ridge explanation, methodology and approved
article links. No Study 001 route migration occurs.

`/dig/study-002/` is a static Next.js page with a clear research classification,
question and balanced finding, midnight/00:01/00:02 strategy timeline, account
summaries, equity, drawdown, exposure, costs, monthly results, interpretation and
expandable methodology/provenance. Independent market filters in the summary,
cost and monthly sections default to both markets. Every table is server-rendered
and all values remain readable without JavaScript. No portfolio is pooled.

The shared site colours, typography, navigation, focus indicators and reduced-motion
rules remain. Cards stack on mobile; tables and hourly figures have labelled,
keyboard-focusable horizontal scrolling regions. Gains/losses have explicit signs,
not just colours. Controls have 44px minimum height; headings and captions are
semantic. No library or dependency was added.

Field Notes 005 remains an unpublished draft outside the content loader. The
seven existing editorial approvals are unchanged; no new article route exists.
The original scientific report, methodology, configuration, freeze and review
package preserve their historical draft wording and bytes.

## Public data selection and provenance

All source links resolve under immutable research commit
`04c485e6af74e52d0541ceab3a88ca0debb21346`.
The starting tree was clean at that commit. GitHub reported both baseline
[CI](https://github.com/owencrew/backtest-badger/actions/runs/41869307397) and
[Frontend](https://github.com/owencrew/backtest-badger/actions/runs/41869309633)
completed successfully before editing. Remote main was rechecked before release
preparation and still pointed to that baseline.

| Source | SHA-256 |
| --- | --- |
| Scientific report | `2abc73472ac9cddcda8f82ee15cfc5d146d528bdaa0cef3c7fe106a53ce4bab6` |
| Methodology | `99dd866a5d5636ac174056b9fb4099b5dd55261c3c1d6316bf8e94e143e67a71` |
| Configuration | `051db07a70230e0892ed8b87ec2e433987d0629651431bed1bd4d3cd782d461f` |
| Freeze | `a7efbb95d4cc8a7204b5c2a42ec5f2559d2d0eb4af46a01f0fc2559bd7035a64` |
| Review data | `b6dc4d632f353fb701467808df1e6f9438ec07b869b2c685b6cc2098c674180b` |
| Asset manifest | `3c9ac9f3a6748b10708e2c3dad4fd6c747063d6943f9e8714e728b54c72c32c1` |
| Public presentation JSON | `1654f486ca5112b5fac841ebf57b824f48ed29466249104e741cd65b18ef06e7` |

The original 90,933-byte review data is verified against the manifest, together
with all six charts and the review HTML. Every public account value and monthly
return is matched to its exact source string; financial display summaries are
also reconciled against the report tables. The report's original evidence and
summary hashes are retained as provenance, without copying private evidence.

`web/lib/study002-data.json` is a 23,696-byte explicit selection: eight separate
account identities, funding/first/final equity, return/drawdown fractions, buy/sell
counts, exposure seconds, four cost components, nullable descriptive Sharpe with
its reason, and 12 monthly returns with completeness flags. It also carries units,
period, source revision and report/manifest/evidence identities. No ledgers, fills,
signals, private paths, review status or generic account blobs are exported.

`web/lib/study002.ts` validates the allowlist, account identities, market/strategy
coverage, bounds, exact funding/return and cost-sum consistency, monthly order,
partial December and missing-statistic reasons. Missing/nonfinite/extra values
are rejected. Cash's original `0E-8` remains intact. BigInt decimal formatting
keeps display rounding separate from source strings. Number conversion is limited
to bounded cost-bar geometry and the small decimal exponent, not accounting.

## Charts and scientific limitations

All six original research charts were inspected. Only `equity.png`, `drawdown.png`
and `exposure.png` are shipped, byte-identical to the retained originals. The
public review package has no safe complete hourly-series contract, so no equity
path is interpolated or reconstructed. A CSS viewport shows the entire original
plotting area (source pixels y=190–1100), including axes, labels and legends.
Accessible HTML replaces the original review masthead and duplicate hash footer;
links expose the unmodified source figures and full immutable manifest. The
original PNG files retain their historical review labels when opened directly.

At narrow widths, figures retain a 1,000px minimum plotting width and scroll
inside their labelled region; they are not shrunk into unreadable thumbnails.
Summary/risk/exposure tables and explanatory text supply accessible comparisons.
Costs use simple labelled HTML bars on a shared 0–10,000 USDT scale, with complete
fee/half-spread/slippage tables. Monthly tables provide every month and all four
accounts per market; December is explicitly partial. Activity/monthly review
PNGs are not duplicated because their information is clearer in these tables.

The page prominently reports +36.62% BTC / +8.47% ETH Trend returns, far fewer
executions and roughly 95% lower attributed costs than Ridge, but underperformance
against Buy & Hold in both markets. BTC Trend's 37.88% observed hourly drawdown
exceeds Buy & Hold's 32.31%; ETH's 34.67% is below 46.66%. August's adverse Bitcoin
reversals and missed rebound sit alongside favourable annual results.

2024 was previously inspected; the study changes signals and market exposure as
well as cadence. This is not a causal frequency-only comparison, untouched
out-of-sample evidence, live performance, or durable profitability. Costs are
assumed; spread/slippage are embedded in execution prices and never double-charged.
Adding costs back cannot reconstruct a frictionless capital path. Final marks are
31 December 2024 at 23:00 UTC, with partial final day/month and no terminal sale.
Provider revisions, globally incomplete historical sources, unobserved intrahour
risk, assumed latency and absent liquidity/fillability evidence remain explicit.

## Local validation

Used pinned Node 24.22.1 and pnpm 11.25.0 for the final validation sequence.

| Check | Observed result |
| --- | --- |
| `pnpm lint` | Passed |
| `pnpm typecheck` | Passed |
| `pnpm format:check` | Passed |
| Default noindex `pnpm build` | Passed; new route generated |
| Default `pnpm test` | 157 passed, including the final preservation-pin test |
| Default `pnpm test:export` | 10 passed |
| Default `pnpm test:workers` | Passed: 14 routes, redirects/refresh, 9 assets and genuine HTTP 404s |
| Indexed build with exact production gate and existing v2 URL | Passed |
| Indexed `pnpm test` | 157 passed, including 12 Study 002 integrity/preservation tests |
| Indexed `pnpm test:export` | 10 passed |
| Indexed `pnpm test:workers` | Passed: same 14 routes and 9 assets |
| Browser | Both routes at 1440, 1024, 768, 390 and 320px; no document overflow |
| Browser controls | Study 001 and all Study 002 selectors, Enter activation and visible focus passed |
| Browser data | Three images loaded at native width 1800; all 24 market/month rows; no JavaScript errors |
| No-JavaScript browser | All 24 market/month rows accessible |

Production metadata has the unique www canonical, Open Graph and Twitter summary
values. The indexed sitemap contains all 13 prior URLs plus Study 002, exactly 14.
Default builds retain `noindex, nofollow` and omit sitemap discovery/file under
the existing gate. Export tests reject private paths, review metadata and the
unpublished Field Notes title. Source links were checked against the immutable
GitHub directory; local export navigation/fragment tests pass.

During implementation, new tests first exposed the source's valid zero-exponent
Decimal notation, incorrect test-only report-column selectors, and a partial-month
label split by HTML markup. These were corrected; no source values changed.
The first browser harness checked lazy images before loading; it now waits for
their decode. Sandbox restrictions required permission to launch a local browser
and bind loopback preview ports. No genuine research economics or Python scientific
implementation was executed or modified. Tests directly verify the presentation
contract using the public committed sources; no private artifact is needed.

## Browser evidence

Actual local static-export screenshots, not synthetic examples:

- [The Dig with both study cards](study-002-web-screenshots/dig-library-desktop.png)
- [Study 002 desktop overview](study-002-web-screenshots/study-002-desktop.png)
- [Equity](study-002-web-screenshots/study-002-equity.png)
- [Drawdown](study-002-web-screenshots/study-002-risk.png)
- [Trading costs](study-002-web-screenshots/study-002-costs.png)
- [390px mobile](study-002-web-screenshots/study-002-mobile-390.png)
- [320px mobile](study-002-web-screenshots/study-002-mobile-320.png)

Desktop, figure and mobile screenshots were visually inspected. The narrow charts
and tables intentionally scroll internally. A full screen-reader audit and
real-device Safari testing were not performed; browser acceptance used local
headless Chrome. The original research plots use colour-coded series; adjacent
text and numeric tables carry the findings without requiring colour perception.

## Release and manual rollback handoff

The authorised focused commit is `feat(web): publish study 002 in the dig` on
main. At document preparation, the final commit/push and its GitHub runs are still
pending; the completion handoff must record the exact final SHA, both workflow
URLs/conclusions and the Cloudflare candidate identity. Baseline CI above is not
substituted for new-commit CI. Do not promote until both new-commit workflows pass.

Read-only inspection of the authenticated Cloudflare Deployments tab on
5 November showed active version prefix **`25290d96`**, 100% traffic, associated
with `fix(web): hide decorative hero symbol on mobile`. The full UUID was not
exposed in that view; copy and record it before any owner promotion. This is the
rollback baseline, subject to rechecking that no other owner release intervened.

Owner promotion procedure:

1. Open Cloudflare → Workers & Pages → `backtest-badger-web` → Deployments.
   Record the currently active full version UUID and traffic allocation.
2. Find the Ready build for the exact final Git commit, open its build details,
   and record build ID and full candidate version UUID. Confirm both GitHub
   workflows succeeded for that same SHA. A successful upload alone is not release.
3. Preserve branch `main`, root `/web`, candidate-only
   `pnpm exec wrangler versions upload`,
   `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL=https://data.backtestbadger.com/forward-v2.json`,
   and `BADGER_SEARCH_INDEXING=www-live-owner-approved`. Keep workers.dev and
   version-preview exposure disabled. No setting change is needed for this stage.
4. Review the local screenshots, source data and candidate build evidence. In
   Deployments, choose **New deployment**, select that exact Ready version,
   allocate 100% traffic, review the selection and explicitly deploy it.
   This is the owner's production publication decision; Codex does not execute it.
5. Check www `/dig/`, `/dig/#study-001`, `/dig/study-002/`, all seven editorial
   pages, Burrow's existing v2 feed, canonical/robots metadata, 14-URL sitemap,
   mobile navigation, images, selectors, redirects and unknown-route 404s.

If a problem appears, the owner returns to Deployments, selects the recorded
previous known-working full UUID (currently prefix `25290d96`), deploys it to
100% traffic and verifies www and Burrow again. Do not rebuild an older revision
and assume identical assets; restore the retained known-working version. No
backend, R2, feed or Lightsail rollback is needed. No automatic promotion,
rollback, manual upload, DNS or Cloudflare dashboard setting change was performed.

Remaining decisions: owner candidate review/promotion, full rollback UUID recording,
and separate editorial review of Field Notes 005. Nothing here authorises another
genuine Study 002 run, a new strategy claim or real-money trading.

## Changed-file inventory

- `docs/studies/study-002-web-publication.md`
- `docs/studies/study-002-web-screenshots/dig-library-desktop.png`
- `docs/studies/study-002-web-screenshots/study-002-costs.png`
- `docs/studies/study-002-web-screenshots/study-002-desktop.png`
- `docs/studies/study-002-web-screenshots/study-002-equity.png`
- `docs/studies/study-002-web-screenshots/study-002-mobile-320.png`
- `docs/studies/study-002-web-screenshots/study-002-mobile-390.png`
- `docs/studies/study-002-web-screenshots/study-002-risk.png`
- `prompts/stage-06-research/002-study-002-dig-publication.md`
- `web/app/dig/study-002/page.tsx`
- `web/components/study-library.tsx`
- `web/components/study002-results.tsx`
- `web/lib/study002-data.json`
- `web/lib/study002.ts`
- `web/public/research/study-002/drawdown.png`
- `web/public/research/study-002/equity.png`
- `web/public/research/study-002/exposure.png`
- `web/tests/study002.test.ts`
- `README.md`
- `docs/development-handoff.md`
- `docs/roadmap.md`
- `prompts/README.md`
- `web/README.md`
- `web/app/dig/page.tsx`
- `web/app/globals.css`
- `web/lib/seo.ts`
- `web/scripts/smoke-workers.ts`
- `web/tests/export.test.ts`
- `web/tests/seo.test.ts`

# Backtest Badger website

The website is live at [www.backtestbadger.com](https://www.backtestbadger.com) on
Cloudflare Workers Static Assets (`backtest-badger-web`), using a Next.js static
export, React, TypeScript and semantic CSS. The frontend needs no database,
credentials or private research artifacts. The Burrow fetches genuine Binance
Spot observations and [forward snapshots](https://data.backtestbadger.com/forward-v1.json)
directly from the browser.

## Current production baseline — 28 October 2026

Read the [Stage 5B.8 post-launch audit](../docs/stage-05b8-post-launch-audit.md) first.
Cloudflare is authoritative DNS (`brit.ns.cloudflare.com`, `weston.ns.cloudflare.com`);
GoDaddy remains the registrar. The apex redirects to www with paths and queries
preserved. R2 bucket `backtest-badger-forward` serves the intended public key
`forward-v1.json`; its temporary development URL returns 401. Both isolated
Lightsail publication/checker timers are enabled and healthy. The active research
release remains `cceb6509…`, not the newer website source.

Website source `360c6130d3f304f275cb9f216cca4fa7c82b5976` has green Python and frontend
CI. The owner reports active Worker version `ff180090-8473-4c91-8e51-1bb918fa90bd`
and deploy command `pnpm exec wrangler versions upload`; exact version-to-source
and preview-build evidence remain outstanding. See the [release runbook](../docs/deployment/website-cloudflare-workers.md).
All seven editorial approvals remain unchanged. Subsequent read-only Stage 5B.9
checks on 28 October confirmed production `index, follow`, the 13-page sitemap,
its robots reference and the www HTTP-to-HTTPS 301 with path/query preservation.
The owner reports successful Search Console submission; this is not proof of indexing.
These observations supersede the historical audit's indexing/redirect gaps.
No production configuration was changed during either inspection.

## Stage 5B.9 — committed; v2 public activation pending

The [implementation report](../docs/stage-05b9-latest-scored-forecast.md) records
the latest-scored cards, exact homepage headline, genuine-data screenshots,
regression tests and controlled migration plan. The browser accepts strict v1 or
v2 snapshots; v1 retains existing predictions/aggregates and truthfully reports
that latest-scored observations are unavailable in that version.

Private v2 preparation uses the same command below with `--schema-version 2` and
a separate private output path. It adds only `latest_scored` and its saved
direction fields; retained prediction/scorer semantics are unchanged. V2 staging
rejects publication arguments. The v1 publisher/checker, public key and production
timers remain unchanged. No v2 endpoint is activated by this stage. A future
website build must switch `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` only after separately
approved genuine v2 publication and independent HTTPS validation. Keep candidate
builds noindex and preserve the explicit owner promotion workflow.

## Stage 5B.10 — isolated v2 tooling, not activated

See the [activation record](../docs/stage-05b10-forward-v2-production-activation.md)
for baseline, 4,991-file read-only host benchmark, tests, exact proposed operations,
rollback and approval gates. `publish_forward_v2.py` prepares genuine retained
evidence before any credential lookup; it accepts only the v2 destination and
keeps separate private success/rollback bytes. `check-forward-v2-endpoint.ts`
independently checks strict v2 HTTPS metadata, bytes, freshness and evidence
progression. New v2 units are prepared locally; v1 files/units are unchanged.

Build only the isolated helper bundles from the repository root:

```sh
node ops/public-feed/bundle-v2-validator.mjs /tmp/badger-v2-bundles
```

The publication CLI performs an external write and must not be run without Gate 1
approval. Private preparation remains available through the unchanged
`stage_forward_snapshot.py --schema-version 2` path. Keep private JSON outside
`web/public` and `web/out`. The browser contract and scientific values are unchanged.
Local Wrangler configuration explicitly preserves disabled workers.dev/version
URLs. Default builds are noindex; indexed release candidates require verified
alternate-host protection and explicit owner promotion. Do not change the live
build-time URL until the genuine public v2 feed passes acceptance.

## Run locally

Use pinned Node.js 24.22.1 (`.node-version`) and pnpm 11.25.0. From the repository:

```sh
cd web
pnpm install --frozen-lockfile
pnpm dev
```

Open <http://127.0.0.1:3000>. The dev server binds to loopback. Development can display
explicitly labelled future editorial drafts. Do not expose the development server publicly.

On this Mac, Node and pnpm were provided by Codex's bundled runtime. If your
terminal says either command is missing, the following PATH prefix uses the same
installed tools for this shell; it does not alter your shell configuration:

```sh
export PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback:$PATH"
```

```sh
pnpm lint
pnpm typecheck
pnpm format:check
pnpm build
pnpm test
pnpm test:export
pnpm test:workers
pnpm preview
```

`build` exports to `out/` and removes reserved not-found placeholders and the
maintainer asset README. `preview` runs **local-only Wrangler Static Assets** at
<http://127.0.0.1:8787>, separate from Next's development server. Run tests after
building: missing production output now fails the export audit. `test:workers`
starts a separate loopback server on port 8791, tests HTTP routes/redirects/assets
and 404s, then stops it. Build output, dependencies and Wrangler state are ignored.
Wrangler 4.153.0 is pinned locally; no login or cloud token is needed for preview.
Never substitute the remote `wrangler preview` command for this local script.

## Content and evidence

- `lib/research.ts`: display-only decimal strings from the public E.5g report.
  All six accounts are reconciled against the report in tests.
- `../docs/field-notes/`: original journal Markdown, read by server components.
- `content/guides/`: three approved introductory educational articles.
- `content/publication-approvals.json`: four Field Note and three guide SHA-256 approvals.
- `lib/content.ts`: shared content parsing and publication policy.

Production requires **both** `Publication status: Published` in an article's source
and an explicit `{ "slug": "filename-without-md", "sha256": "…" }` approval in its
collection. Hash the complete final UTF-8 source bytes, including metadata. Any
subsequent edit invalidates that approval. Changing a status alone is insufficient.
No environment flag permits drafts in a production build. Unknown environments
also fail closed. Development is a local editorial preview, not publication approval.
Review linked articles and source documents as part of publication approval.

When nothing is approved, the journal and guide indexes show honest empty states.
Each dynamic route generates a reserved `publication-pending` not-found entry so
Next's static exporter can build the empty collection; this is never linked in UI and is removed from the final export.
Draft bodies, titles and individual routes are excluded from the exported site.

## Structure

`app/` owns the six main pages and editorial routes. `components/` contains the
header, editorial views, research chart, market selector and decorative motion
study. `app/globals.css` contains semantic tokens and responsive styles. CSS is
used directly instead of adding Tailwind or a component library. The summary bar
chart uses a shared linear scale and HTML/CSS; no charting package is needed.

See the [Stage 5A design and validation report](../docs/stage-05a-website-design.md)
for scientific limits, technology choices, validation and next steps.

## Stage 5B market and forward feeds

The Burrow supports BTCUSDT/ETHUSDT, candlestick/line views and 1D/7D/30D/90D
ranges, plus 1Y (daily) and ALL (Monday-aligned weekly) listing-era history. Lightweight Charts 5.2.1 is attributed on the chart with licence files under
`public/licenses/`. Public Binance requests refresh about every five minutes only
while visible, with manual refresh, cancellation and explicit loading/error/stale
states. All displayed times use UTC. Network/region restrictions can block Binance;
there is no fabricated fallback.

The live build uses
`NEXT_PUBLIC_FORWARD_SNAPSHOT_URL=https://data.backtestbadger.com/forward-v1.json`.
Set this public value **before building** a connected local or release candidate;
it is never a secret. Without it the default remains truthfully unavailable.
The static browser client polls and validates snapshots without a server or database.
Do not connect `tests/fixtures/` to any running site or production export.

`lib/forecast.ts` defines the version 1 contract and strict validation. The separate
Python utility `scripts/public_forward_export.py` prepares a private candidate from
validated retained evidence using the existing frozen evaluator. It needs the
repository's locked Python environment; the website itself does not. An isolated
helper on Lightsail publishes validated snapshots to R2 every ten minutes; a
separate HTTPS checker verifies them. See the [Stage 5B report](../docs/stage-05b-market-dashboard.md)
for exact local preparation commands, field definitions, inspected release,
publishing proposal and operational impact.

Additional focused exporter checks, from the repository root:

```sh
.venv/bin/pytest -q web/tests/test_public_export.py
.venv/bin/ruff check web/scripts/public_forward_export.py web/tests/test_public_export.py
.venv/bin/ruff format --check web/scripts/public_forward_export.py web/tests/test_public_export.py
```

The regular frontend checks remain `pnpm lint`, `pnpm typecheck`, `pnpm build`,
then `pnpm test`. Tests use synthetic fixtures only. The production output check
accepts the truthful unconnected or awaiting-first-verified-fetch state. Stage 5B.3 approves all seven articles; 004 leads production Field Notes and
the home journal feature. Future unapproved sources remain excluded. Historical figures in `lib/research.ts` are unchanged.

## Historical implementation notes

The Stage 5B.2–5B.6 sections below retain their original preparation/activation
context. Their statements about pending deployment, disabled timers or the temporary
endpoint are historical, superseded by the production baseline above and Stage 5B.8.
Use the current deployment guides for operations; do not repeat initial setup.

## Stage 5B.2 launch readiness

1Y is 365 days plus the current daily candle; ALL begins with Binance's partial
listing week labelled 2017-08-14. Actual available endpoints and partial-week
limitations are visible on the chart. Long ranges use a per-tab memory cache:
refresh downloads the recent overlap, with a full recheck after 24 hours or a
page reload. Gaps remain explicit and provider revisions are possible.

Optional genuine API check (network required, excluded from offline CI):

```sh
node --import tsx scripts/check-market-live.ts
```

The independent Frontend workflow runs the local checks above without deployment
credentials. Python CI and frozen research remain unchanged. The selected host is
**Cloudflare Workers Static Assets**, with no server-side Worker or Pages project.
See the [launch/rollback runbook](../docs/deployment/website-cloudflare-workers.md)
for exact Workers Builds settings, candidate-only uploads, owner promotion after
green CI, and the separately authorised GoDaddy-to-Cloudflare DNS migration.
The [Stage 5B.2 report](../docs/stage-05b2-history-and-launch-readiness.md) records
coverage, editorial recommendations and validation limits. No deployment has run.

## Stage 5B.3 editorial release and search

All seven existing articles are Published in source and approved by exact SHA-256
for the next release. Original article dates are unchanged; this is not a claim
of public deployment. The [release record](../docs/stage-05b3-editorial-publication.md)
lists the exact identities and source-link inventory. Production includes four
notes (004 featured, then 003/002/001) and three introductory guides. New articles
still start as Draft. No build or test automatically refreshes approvals.

All 13 public pages have distinct descriptions, page-specific www canonicals,
Open Graph and Twitter summary metadata. There is no custom social image or
invented public publication timestamp. Canonicals always use
`https://www.backtestbadger.com`, including locally and on workers.dev candidates.

**Default candidate: indexing remains disabled.** Leave `BADGER_SEARCH_INDEXING`
unset for local review, initial workers.dev and later preview builds. HTML emits
`noindex,nofollow`. `robots.txt` allows crawling so robots can read that directive;
it does not advertise a sitemap. The sitemap generator uses only eligible content,
but the existing post-build preparation removes `out/sitemap.xml` while indexing
is disabled; `/sitemap.xml` then returns 404 from Wrangler.

Only after www is live, verified and explicitly approved for indexing, build with
`BADGER_SEARCH_INDEXING=www-live-owner-approved`. This exact build-time value
emits `index,follow`, retains the 13-route sitemap and advertises it in robots.txt.
Any other value defaults to noindex. Changing a runtime variable cannot change
already exported HTML. Follow the [launch runbook](../docs/deployment/website-cloudflare-workers.md)
for inspection, candidate isolation and deployment approval. Do not submit a
sitemap until that approved www release is live.

## Stage 5B.4 mascot, navigation and forward publication preparation

The homepage uses the owner's original mascot as a pixel-identical lossless WebP;
its PNG source is retained under `design-assets/`, outside the deployed assets.
Navigation is Home → The Burrow → The Dig → Field Notes → Field Guide → About.
Article source bytes, slugs, approvals, featured Note 004 and indexing are unchanged.

A genuine private Lightsail candidate passed both validators on 27 October 2026.
**No public feed is activated.** The default website still shows unavailable
forecasts. Never copy the private candidate into `public/` or `out/`.

`stage_forward_snapshot.py` wraps the existing exporter with non-overlap, a
120-second deadline, a 64 KiB limit, TypeScript validation and atomic private output.
Run from the repository root with explicit private evidence directories:

```sh
.venv/bin/python web/scripts/stage_forward_snapshot.py \
  --records /PRIVATE/forward-predictions \
  --outcomes /PRIVATE/forward-outcomes \
  --operations /PRIVATE/forward-operations \
  --output /PRIVATE-STAGING/last-success.json
```

The output parent must already exist and be private. Node/tsx must be available.
The optional `--publish-r2-object backtest-badger-forward/forward-v1.json` **writes externally and
requires separate owner approval before execution**. It uses the separately pinned S3 publisher with a bucket-scoped R2 credential,
uploads only the validated candidate and verifies exact object readback. It never
deploys website assets. The only allowed destination is
`backtest-badger-forward/forward-v1.json`. No cloud
credentials are needed for default private preparation. Stage 5B.5 authorises this isolated helper; its timer remains disabled until
account access, scoped credentials and endpoint verification are complete. See the
[Stage 5B.4 report](../docs/stage-05b4-mascot-navigation-forward-feed.md) for the
candidate identity, host recommendation, exact activation proposal and rollback.

The frontend rejects clock/forecast regression while retaining earlier evidence.
It distinguishes loading, error, stale publication, pending/settling/unscored and
scored outcomes. Five-minute visible-page polling is independent of four-hour
issuance. No fixture or genuine one-off candidate is bundled into the website.

## Stage 5B.5 activation status

The isolated Lightsail helper has generated a genuine candidate that passed both
validators. **No public endpoint is active or configured in this local build.**
The owner will configure Cloudflare personally using the [step-by-step guide](../docs/deployment/forward-feed-cloudflare-setup.md). Both new
timers are installed but disabled. See the [activation record](../docs/stage-05b5-forward-feed-activation.md)
for benchmark results, safeguards, verification gaps and rollback.

After the actual public object passes schema, hash, CORS and freshness checks, set
`NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` in ignored `web/.env.local` to that verified HTTPS
URL. Restart development and rebuild the static export; review both on loopback.
Do not use a guessed data hostname or bundle a private candidate into static assets.
Remove that one variable and restart/rebuild to disconnect the feed.

Independent endpoint check (no credentials):

```sh
node --import tsx scripts/check-forward-endpoint.ts "$NEXT_PUBLIC_FORWARD_SNAPSHOT_URL"
# Optional second argument: private path to the exact expected published bytes.
```

The checker validates size, complete schema, both markets, HTTP metadata, www CORS,
cutoff age and missed issuance separately. Unit tests use labelled synthetic fixtures
only; no fixture is connected to a running site. Navigation order is regression
tested in exported HTML and manually checked on desktop/mobile with keyboard use.

## Stage 5B.6 historical feed activation and dashboard refinement

The owner has activated the R2 development endpoint and both recurring Lightsail
timers. Read-only verification on 28 October 2026 confirmed repeated scheduled
publication/checker success, advancing snapshot clocks, unchanged forecast
identities between publications, and healthy collector/scorer results. The local
ignored build configuration now connects the genuine feed. Earlier stage sections
above describe their historical activation status; see the
[current verification and screenshot record](../docs/stage-05b6-forward-dashboard-refinement.md).

The Burrow leads with separate BTC/ETH cards and timely automated evaluations.
Forecasts, realised returns, MAE, RMSE, bias and signed errors display **log-return
basis points** (original value × 10,000), never simple percentage returns. Small
nonzero values below 0.01 bps use scientific notation to avoid displaying zero.
Original numeric values remain in technical disclosures. The public validator,
JSON contract, polling and regression checks are unchanged.

Late manual results are collapsed and explicitly incomparable with primary results.
Detailed evaluation includes every cohort's accounting, methodology, recipe-pooling
limits, unattributed evaluation and the original validated snapshot. Empty cohorts
show a message until matched data becomes available; Zero accuracy reads
`N/A — zero forecast` with `0 / 0`. Mobile tables are labelled keyboard-focusable
scroll regions. Homepage supporting labels retain their existing layout after
removing the two requested phrases; historical research figures are unchanged.

The temporary endpoint remains an environment value, never a source-code constant.
No website deployment, DNS/R2 change or indexing activation has been performed.

## Next feature backlog

**Latest Scored Forecast** is proposed, not implemented: separately show the most
recent completed/scored forecast alongside the current pending prediction, comparing
all model predictions, observed return, forecast error and directional correctness.
Review any versioned public-contract/exporter extension first; preserve provenance,
scoring methodology, Zero abstention and all cohort boundaries. See the
[post-launch backlog](../docs/stage-05b8-post-launch-audit.md#future-development).

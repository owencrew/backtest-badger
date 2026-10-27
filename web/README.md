# Backtest Badger website

Stages 5A–5B.2 form a local Next.js / React / TypeScript static website. The frontend
needs no database, credentials or private research artifacts. The Burrow fetches
genuine Binance Spot market data directly from the browser.

## Run locally

Use pinned Node.js 24.22.1 (`.node-version`) and pnpm 11.25.0. From the repository:

```sh
cd web
pnpm install --frozen-lockfile
pnpm dev
```

Open <http://127.0.0.1:3000>. The dev server binds to loopback. Development displays
explicitly labelled editorial drafts. Do not expose the development server publicly.

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
- `content/guides/`: three new educational drafts.
- `content/publication-approvals.json`: empty, fail-closed publication allowlists.
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

Forward forecasts are unavailable by default. After owner approval of a genuine
public snapshot, set `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` to a same-origin JSON path
or HTTPS URL **before building**. This is a public value, never a secret. The static
browser client polls and validates that snapshot without a server or database.
Do not connect `tests/fixtures/` to any running site or production export.

`lib/forecast.ts` defines the version 1 contract and strict validation. The separate
Python utility `scripts/public_forward_export.py` prepares a private candidate from
validated retained evidence using the existing frozen evaluator. It needs the
repository's locked Python environment; the website itself does not. It is not
installed or scheduled on Lightsail. See the [Stage 5B report](../docs/stage-05b-market-dashboard.md)
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
expects the default unconnected forward feed. No article approvals were added;
004 leads local Field Notes and the home journal feature, while production remains
fail-closed. Historical figures in `lib/research.ts` are unchanged.

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

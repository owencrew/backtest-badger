# Stage 5A — Website design and local prototype

25 October 2026, Europe/London. Local implementation only. The frontend lives in
`web/`; scientific Python code, original Field Notes, protocols and historical
evidence are unchanged. No AWS, Lightsail, production database, DNS, deployment,
research execution, model fitting, trading, commit or push occurred.

## Technology decision

Next.js 16.4.3, React 19.3.1 and TypeScript, with the App Router and static export.
The pnpm lockfile records the installed versions. Pages and Markdown render in
server components; only navigation, market selection, chart tooltips and the
motion study need client state. No API, authentication, CMS or database exists.

[Astro's islands](https://docs.astro.build/en/concepts/islands/) are a strong fit
for a primarily editorial site with isolated interactive widgets. Next.js was
chosen to follow the owner's preference and keep future dashboard interactions
within one React model. Its [static export](https://nextjs.org/docs/app/guides/static-exports)
supports the current file-based prototype without requiring a deployed server.
Moving to a server or reviewed read-only API later is a separate increment.

Plain CSS with semantic custom properties replaces the provisional Tailwind
choice: it keeps this small design system understandable without another styling
layer. The comparison chart uses accessible HTML/CSS on one shared linear scale;
no charting dependency is justified for six summary values. Markdown uses
`react-markdown` and `remark-gfm`, without raw HTML execution. Manrope is served
locally from Fontsource; no Google Fonts runtime request is needed.

## Information architecture and components

| Route | Working experience |
| --- | --- |
| `/` | Editorial hero, original mascot, verified featured study, research journey, destinations, draft discoveries and learning links |
| `/burrow/` | Forward research overview; explicitly unavailable statistics, timely/late cohort explanation and an activity empty state |
| `/dig/` | Both-market or individual-market filters, return bars, all six account summaries, costs, methodology disclosures and source attribution |
| `/field-notes/` | Featured research article and four local draft previews; empty state in the unapproved production build |
| `/field-notes/[slug]/` | Original Markdown, metadata, readable tables, related previews and corrected source links |
| `/field-guide/` | Six-topic learning map; three local introductory drafts and clearly planned remaining topics |
| `/field-guide/[slug]/` | Backtesting, performance metrics, and forecasts-to-trades introductions |
| `/about/` | Project introduction, methodology, evidence-stream distinctions, GitHub and a decorative motion study |

Shared components cover header/mobile navigation, footer, breadcrumb/page intro,
status labels, source dates, disclaimers, empty states, article cards/layout,
research chart and market explorer. A single stylesheet defines the visual system;
there is no internal component framework. Invalid/unapproved article paths show
the not-found experience. Navigation has active states, a skip link and keyboard
focus styles. Tables have captions and scoped headers, with contained horizontal
scroll on narrow screens rather than whole-page overflow.

## Visual identity

| Token | Value | Role |
| --- | --- | --- |
| `--color-bg` | `#121615` | Charcoal background |
| `--color-surface` | `#1D2522` | Research panels |
| `--color-surface-raised` | `#26312B` | Featured surface |
| `--color-text` | `#F4F1EA` | Warm primary text |
| `--color-text-muted` | `#AEB9B1` | Secondary text |
| `--color-primary` | `#315943` | Forest-green controls |
| `--color-primary-light` | `#A9CFAE` | Accessible light accent |
| `--color-sand` | `#D8C7A5` | Illustration and editorial accent |
| `--color-slate` | `#82908D` | Cash series and muted decoration |
| `--color-border` | `#37463E` | Panel divisions |
| `--color-negative` | `#E4A19A` | Losses |
| `--color-positive` | `#A9CFAE` | Gains |

Manrope is the main sans-serif family; system monospace is reserved for financial
values, identifiers and dates. Numbers have tabular alignment, explicit signs and
text labels so colour is not the sole indicator. Forest green appears on controls,
with light foreground text. The sand panel uses dark ink text.

The owner's engraving is copied unchanged to `web/public/brand/` and composited
with CSS multiply blending in a sand arch. The white rectangle disappears visually;
this is not an alpha-transparent bitmap. A small hand-constructed geometric SVG
head provides the transparent emblem, favicon and animation-ready badge. It is a
simplification inspired by facial markings, not a trace or a replacement character.
See the [asset record](../web/public/brand/README.md). No full woodcut vectorisation
or generated illustration was attempted. The decorative journal artwork has no
numerical axis or financial data and is hidden from assistive technology.

## Verified data and evidence boundaries

`web/lib/research.ts` transcribes public E.5g decimal strings. Links pin repository
revision `c6d2a1704c620c3136bda13b65f8c1e0dc546bfd`, the checked-out source at this
stage's start. The [authoritative report](stage-04b2e5g-first-genuine-historical-backtest.md)
is dated 24 October 2026; the final mark is 31 December 2024 at 23:00 UTC.

| Market | Ridge | Cash | Buy & Hold | Ridge costs, USDT |
| --- | ---: | ---: | ---: | ---: |
| BTCUSDT | −60.69% | 0.00% | +120.81% | 9,932.12 |
| ETHUSDT | −57.96% | 0.00% | +46.18% | 9,239.49 |

All accounts begin independently with 10,000 USDT. The Dig also shows final values,
maximum observed hourly drawdowns, buys/sells and turnover for all six accounts.
BTC Ridge has 570 buys/570 sells; ETH has 499/499. Each side assumes 10 bps fees,
1 bp half-spread and 2 bps adverse slippage. Spread/slippage are embedded in prices,
not deducted again. Buy & Hold retains unsold assets without an invented exit cost.

The chart presents cumulative returns, not annualised returns or an invented
equity curve. The period was previously inspected; results remain exploratory.
There is no live feed, fabricated accuracy statistic, paper portfolio or actual
backtest execution control. The Burrow labels its structure as reviewed on
25 October 2026, explicitly without claiming a current operating-system snapshot.
Operational counts in private/production contexts are not republished as statistics.

## Publication controls

`web/content/publication-approvals.json` has two empty allowlists. Original Field
Notes stay in `docs/field-notes/`; new educational drafts live under
`web/content/guides/`. Local development permits clearly labelled previews.
Production requires both `Published` source metadata and approval of the complete
file's SHA-256. Unknown environments fail closed. Changed bytes invalidate approval.
The gate applies to article routes, cards, excerpts, related links and home features.
There is no production preview override. Review related source links before
approving any article. The production build currently omits all seven drafts.

## Interactions and motion

Implemented: market filters update charts and tables together; pointer, tap and
keyboard chart details; Escape dismissal; native methodology disclosures;
responsive menu with active states and Escape closure; hover/focus treatments;
user-triggered backward badge movement along an abstract path in About.
The motion study explicitly says that no research is running. Its badge can be
reset; it has no progress percentage or result. CSS respects reduced motion.

Deferred: true job progress, a badge moving on verified historical prices,
equity/drawdown series, animated financial counters and live dashboard refresh.
Accurate values appear immediately rather than counting through fictional values.

## Local preview

```sh
cd web
pnpm install --frozen-lockfile
pnpm dev
# Open http://127.0.0.1:3000 (local editorial previews included).
```

Use Node 22.13+ and pnpm 11.25.0. Validation used bundled Node 24.22.1.
The machine did not initially expose Node on its shell PATH; the Codex bundled
runtime was used. For a normal terminal, install/use Node and pnpm on PATH first.

```sh
pnpm lint
pnpm typecheck
pnpm build
pnpm test
# Stop dev before serving the production export on the same port:
pnpm preview
```

The production preview intentionally has no draft articles. `web/.next-dev/`
separates development output from the production build. No Python or database
setup is necessary. See [web/README](../web/README.md) for the publication workflow.

## Validation and limitations

Executed successfully against the final implementation:

- `pnpm lint`, `pnpm exec prettier --check .`, `pnpm typecheck` and `pnpm build`.
- `pnpm test`: **12 passed, 0 failed, 0 skipped**, including exact reconciliation
  of all six account rows against the report, headline rounding, fail-closed
  publication policy and a scan of production output for leaked draft text/routes.
- All six unique local navigation targets in the production HTML resolve to
  exported pages. All ten relative document targets in the original Field Notes
  exist. All four journal and three guide routes were opened in the browser and
  showed their expected content and draft labels.
- In-app browser inspection at 1440px desktop, 768px tablet and 390px mobile;
  all six main pages also checked at 320px with no document-width overflow.
  Article layouts and data tables were visually reviewed. Mobile tables retain
  intentionally contained horizontal scrolling.
- Keyboard market selection updated the chart and table together. Focusing a
  chart bar opened its details; Escape dismissed them. Mobile menu navigation
  opened the chosen page and closed the menu. The user-triggered motion study
  changed its control to reset and animated backward inside its panel.
- Seven principal foreground/background token pairs were calculated at **7.05:1
  or better**, above the 4.5:1 normal-text threshold. Reduced-motion support was
  checked in CSS; the operating-system preference was not emulated. No formal
  screen-reader audit or full automated accessibility certification is claimed.
- Final browser warning/error log was empty after correcting Next's smooth-scroll
  metadata warning. Screenshots of the desktop home, mobile home and mobile Dig
  were saved in the chat's local visualization workspace for owner review.
- `git diff --check`, byte-for-byte prompt archive comparison and byte-for-byte
  original/served engraving comparison passed. Existing tracked changes are
  limited to README and prompt-index updates; no scientific source/evidence changed.

The initial direct `tsx` CLI test command encountered a sandbox IPC restriction;
the final script uses Node's test runner with `--import tsx`, which passed without
that IPC server. Dependency installation explicitly allows only esbuild and
unrs-resolver build scripts. Installation reported an upstream ESLint 9 deprecation
notice; the locked Next ESLint configuration and lint checks work. No Python suite
or historical research was run because scientific implementation is unchanged.

This is a first prototype, not a production release or a full accessibility
certification. No current prospective statistics have been approved. No full
transparent engraving was produced. Source-report links require internet access.
The original draft prose remains unchanged and still requires owner editorial
review; the new educational drafts also require review. A public launch would
need an explicit deployment scope, rights/attribution review and approved content.

Next increment: owner visual/editorial review, then an approved dated public-safe
forward-statistics export with cohort/sample metadata. Add a narrow read-only
adapter only when that data contract is approved. Keep paper portfolios and
backtest execution behind separately scoped implementation work.

The complete request is archived [verbatim](../prompts/stage-05-web/001-website-design-and-local-prototype.md).

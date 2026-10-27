# Stage 5B.3 — Editorial publication and search readiness

27 October 2026, Europe/London. Prepared from clean commit
`af247362260a982ed59514e321cc18984b58004f` for owner review. The owner explicitly
approved all four existing Field Notes and all three introductory Field Guides
for the initial website release, conditional on final accuracy, security and link
checks. Those checks found no substantive correction or article-level blocker.

**All seven are approved for production export; no public deployment has occurred.**
Published is the source eligibility status, not a claim of an actual launch date.
No commit, push, remote preview upload, DNS change, Lightsail access, public forecast
connection, model change or historical replay occurred. Original research prose,
figures, dates, limitations, costs and provenance are preserved. The
[complete request](../prompts/stage-05-web/005-editorial-publication-and-search-readiness.md)
is archived verbatim.

## Exact editorial release identities

All statuses below are **Published**. Filenames are the slug plus `.md`; routes are
`/field-notes/<slug>/` for notes and `/field-guide/<slug>/` for guides. These are
release-candidate routes, not assertions that those URLs are already deployed.

### Field Note 001 — When Market Data Isn't Complete

- Source: [001-when-market-data-isnt-complete.md](field-notes/001-when-market-data-isnt-complete.md)
- Slug: `001-when-market-data-isnt-complete`
- Original article date: **2026-10-13**; source status: **Published**
- SHA-256: `893b1a8271c54adeec40acc72a6e67e8af133b79c80bdbbe1b5cafdfd40116d4`

### Field Note 002 — When a Backtest Meets Trading Costs

- Source: [002-when-a-backtest-meets-trading-costs.md](field-notes/002-when-a-backtest-meets-trading-costs.md)
- Slug: `002-when-a-backtest-meets-trading-costs`
- Original article date: **2026-10-14**; source status: **Published**
- SHA-256: `b50c8fb540d9e1027ab3ded6dc1f55e15febdcea04cdcd434001b27c2796eff9`

### Field Note 003 — The Price of Changing Your Mind

- Source: [003-the-price-of-changing-your-mind.md](field-notes/003-the-price-of-changing-your-mind.md)
- Slug: `003-the-price-of-changing-your-mind`
- Original article date: **2026-10-24**; source status: **Published**
- SHA-256: `4aebfee182e5083721b1ceaf6ac6f7ed650824fd048778541f3d112b3a754bc3`

### Field Note 004 — One Minute Can Change a Backtest

- Source: [004-one-minute-can-change-a-backtest.md](field-notes/004-one-minute-can-change-a-backtest.md)
- Slug: `004-one-minute-can-change-a-backtest`
- Original article date: **2026-10-24**; source status: **Published**
- SHA-256: `93e87056c6e2510e4d8bbe1189bd012da8438e5ed7306f17166f1430414ca248`

### Field Guide 001 — What Is Backtesting?

- Source: [001-what-is-backtesting.md](../web/content/guides/001-what-is-backtesting.md)
- Slug: `001-what-is-backtesting`
- Original article date: **2026-10-25**; source status: **Published**
- SHA-256: `1681b2c8391973ef6faa2bdfcd0c7a58a36a0b8b5cb9d8516a78c679720e4020`

### Field Guide 002 — Understanding Performance Metrics

- Source: [002-understanding-performance-metrics.md](../web/content/guides/002-understanding-performance-metrics.md)
- Slug: `002-understanding-performance-metrics`
- Original article date: **2026-10-25**; source status: **Published**
- SHA-256: `78dd02de41408c098e837287027ddae794807928baf7d58865d482505008ffd0`

### Field Guide 003 — From Forecasts to Trades

- Source: [003-from-forecasts-to-trades.md](../web/content/guides/003-from-forecasts-to-trades.md)
- Slug: `003-from-forecasts-to-trades`
- Original article date: **2026-10-25**; source status: **Published**
- SHA-256: `b40e76e3838690e3875bd86764fc8f6dc0a3978694d05cfe7b24f03654d5ec89`

The final full UTF-8 source bytes, including metadata, LF line endings and final
newline, were hashed only after review and the status transition. Values were
entered explicitly in `web/content/publication-approvals.json`. Notes 003 and 004
moved their leading plain-text status into the shared Markdown metadata block;
the other five changed only Draft → Published. No article body or date changed.
There were no tone rewrites, new results or link corrections.

Recheck a reviewed file with `shasum -a 256 <source-file>` or Node's
`createHash("sha256").update(readFileSync(source)).digest("hex")`. No automated
approval refresh exists. A changed byte rejects the existing approval. A Draft is
rejected even with its matching hash. Explicit production is now required outside
local development; undefined, test, staging and preview environments fail closed
even for an otherwise approved article. Development remains a local preview only.
New articles still start Draft and require deliberate approval of their exact bytes.

## Accuracy and source-link review

Each article was read in full. Seven linked research reports were checked against
the narrative and key figures, with these results:

| Article | Evidence checked |
| --- | --- |
| Note 001 | Stage 1B.3's bounded September/June comparisons, 19,991 expected / 19,955 accepted observations and 36 stored gaps per market; maintenance remains a hypothesis, not an established cause. |
| Note 002 | Stage 2B forecast errors/direction and Stage 2C 13:00 entry / 16:00 exit, 10/1/2 bps costs, trade counts, +98.53% / −88.12% BTC Ridge returns and scenario-specific accounting. |
| Note 003 | E.5g's six independently funded accounts, returns, hourly drawdown, 570/499 buys and sells, 9,932.12 / 9,239.49 USDT costs, partial terminal mark and previously inspected 2024 history. |
| Note 004 | Frozen minute protocol, minute source engineering and genuine parity audit: 12:01 → 12:02 convention, 527,040 minutes and 8,784 marks per market, 17,568 exact pairs, zero mismatches and 101 preserved files. |
| Guides 001–003 | Causal timing, independent benchmarks, exploratory history, sampled drawdown, zero-rate/undefined Cash Sharpe, turnover and embedded costs agree with the research sources; paper trading and other strategy/asset families remain planned or educational. |

The complete direct Markdown inventory is **14 link occurrences**: eight research
report links (seven distinct reports, including two heading fragments), two note
cross-links and four existing site-route links. There are no standalone external
citations, reference-style links or inline local-heading links in these seven
sources. Research links become pinned public GitHub URLs at
`c6d2a1704c620c3136bda13b65f8c1e0dc546bfd`; all seven report URLs were successfully
retrieved through the GitHub connector. Their local contents also match the pinned
Git blobs byte-for-byte. Both linked heading IDs exist at that revision.

| From | Exact Markdown destination | Production destination |
| --- | --- | --- |
| Note 001 | `../stage-01b3-full-history.md#bounded-official-source-investigation` | [Target](https://github.com/owencrew/backtest-badger/blob/c6d2a1704c620c3136bda13b65f8c1e0dc546bfd/docs/stage-01b3-full-history.md#bounded-official-source-investigation) |
| Note 001 | `../stage-01b3-full-history.md#final-live-results-and-verification` | [Target](https://github.com/owencrew/backtest-badger/blob/c6d2a1704c620c3136bda13b65f8c1e0dc546bfd/docs/stage-01b3-full-history.md#final-live-results-and-verification) |
| Note 002 | `../stage-02c-execution-backtesting.md` | [Target](https://github.com/owencrew/backtest-badger/blob/c6d2a1704c620c3136bda13b65f8c1e0dc546bfd/docs/stage-02c-execution-backtesting.md) |
| Note 002 | `../stage-02b-predictive-baselines.md` | [Target](https://github.com/owencrew/backtest-badger/blob/c6d2a1704c620c3136bda13b65f8c1e0dc546bfd/docs/stage-02b-predictive-baselines.md) |
| Note 003 | `../stage-04b2e5g-first-genuine-historical-backtest.md` | [Target](https://github.com/owencrew/backtest-badger/blob/c6d2a1704c620c3136bda13b65f8c1e0dc546bfd/docs/stage-04b2e5g-first-genuine-historical-backtest.md) |
| Note 003 | `002-when-a-backtest-meets-trading-costs.md` | [Target](https://www.backtestbadger.com/field-notes/002-when-a-backtest-meets-trading-costs/) |
| Note 004 | `../stage-04b2c-minute-execution-protocol.md` | [Target](https://github.com/owencrew/backtest-badger/blob/c6d2a1704c620c3136bda13b65f8c1e0dc546bfd/docs/stage-04b2c-minute-execution-protocol.md) |
| Note 004 | `../stage-04b2d1-genuine-price-parity-audit.md` | [Target](https://github.com/owencrew/backtest-badger/blob/c6d2a1704c620c3136bda13b65f8c1e0dc546bfd/docs/stage-04b2d1-genuine-price-parity-audit.md) |
| Note 004 | `../stage-04b2c-minute-data-engineering.md` | [Target](https://github.com/owencrew/backtest-badger/blob/c6d2a1704c620c3136bda13b65f8c1e0dc546bfd/docs/stage-04b2c-minute-data-engineering.md) |
| Note 004 | `003-the-price-of-changing-your-mind.md` | [Target](https://www.backtestbadger.com/field-notes/003-the-price-of-changing-your-mind/) |
| Guide 001 | `/dig/` | [Target](https://www.backtestbadger.com/dig/) |
| Guide 001 | `/about/` | [Target](https://www.backtestbadger.com/about/) |
| Guide 002 | `/dig/` | [Target](https://www.backtestbadger.com/dig/) |
| Guide 003 | `/dig/` | [Target](https://www.backtestbadger.com/dig/) |

The unchanged Markdown converter preserves trailing slashes for article routes and
fragments on report URLs. Tests additionally exercise slash-before-fragment article
conversion. Generated HTML was checked for every converted article link, all
internal navigation targets and emitted fragment destinations. Direct browser
navigation and the article-body chain 004 → 003 → 002 work. Source reports remain
links to public documentation; private research artifacts are not copied into assets.

## Presentation and metadata

The existing newest-eligible sorting selects **004 — One Minute Can Change a
Backtest**, then 003, 002 and 001. No featured slug was hardcoded. Its illustration
label/title, original date, excerpt, five-minute reading estimate and link match
the source. The homepage features 004 then 003 and links to all three guides.
Guide cards appear in introductory order 001, 002, 003. All seven direct routes,
full prose, tables, headings, related cards and methodology navigation are present.
Draft labels are conditional on actual draft content, including local previews.
The learning-map qualification remains visible.

Next.js **16.4.3** installed metadata declarations and the official
[metadata](https://nextjs.org/docs/app/api-reference/functions/generate-metadata),
[robots](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/robots)
and [sitemap](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap)
documentation were reviewed. A small shared metadata helper supplies distinct
readable descriptions, fully specified titles, page-specific canonical URLs,
Open Graph website/article metadata and Twitter summary cards for all 13 pages.
Article descriptions use the existing editorial topic metadata, without raw
Markdown, filesystem paths or stage identifiers. Social titles match HTML titles.
All canonical/OG URLs use `https://www.backtestbadger.com` and real trailing-slash
routes. Original article dates are not repurposed as OG publication timestamps.
No new promotional image or dependency was introduced.

## Indexing and sitemap boundary

The final working export remains **noindex,nofollow**. Only the exact build-time
setting `BADGER_SEARCH_INDEXING=www-live-owner-approved` enables indexing; absent,
empty or other values remain disabled. Article approvals do not affect this switch.
The sitemap generator uses six existing primary routes and the production-eligible
loader for both collections, giving **13 entries** today. It never lists directories
indiscriminately or invents modification dates.

For candidates, static preparation removes `out/sitemap.xml`; its HTTP route returns
404 and robots.txt does not advertise it. Robots allows crawling so HTML noindex
can be read. This does not make the site private. After separately approved www
activation, the enabled build retains the sitemap and advertises it, with
index/follow HTML. Runtime variables cannot alter an existing static export.
The [Workers runbook](deployment/website-cloudflare-workers.md#search-activation-after-the-www-launch)
explains file inspection, rebuilding, isolation of workers.dev/Version URLs,
release approval, external verification and eventual sitemap submission.

Both branches were tested locally. The enabled branch was built **only in a
separate temporary test copy**, never uploaded or served publicly. The deliverable
`web/out/` remained the default noindex candidate throughout that test.

## Validation performed

| Check | Result |
| --- | --- |
| Frozen pnpm install | Passed with pinned Node 24.22.1 / pnpm 11.25.0; lockfile unchanged |
| ESLint / TypeScript / Prettier | Passed |
| Next.js production static build | Passed; all seven approved nested article routes generated |
| Frontend suite | **72 passed, zero skipped** |
| Explicit production export audit | **6 passed**, including metadata, links, publication, private-file/fixture scans and sitemap policy |
| Publication gate | Four notes / three guides, Published metadata, independently recomputed exact hashes; changed hashes, Draft with approval, unknown environments and future unapproved files rejected |
| Negative export build | A separate temporary copy included both Draft and Published-but-unapproved future notes/guides; all remained absent from rendered text, routes and sitemap; all six export audits passed |
| Indexing-enabled test build | Separate temporary copy: all six export audits passed; exactly 13 www sitemap entries, robots advertisement and index/follow HTML |
| Local Wrangler HTTP | Passed: 13 main/article pages, direct refreshes, trailing-slash and index.html 307 redirects preserving queries, six sampled assets, genuine 404s, metadata, no draft banners, robots and absent candidate sitemap |
| Responsive browser checks | All 13 pages at 1440px and 390px had no document-width overflow; no draft messaging; representative journal, guide, article and table layouts visually inspected |
| Navigation | Actual article-body clicks 004 → 003 → 002 succeeded; mobile menu opens; homepage/article hrefs and all exported internal links verified |
| Live browser observation | The Burrow loaded genuine BTCUSDT Binance observations at 12:36:39 UTC; forecasts remained unavailable. No captured browser warning/error logs during the route checks |
| Markdown dependencies | All 14 article link occurrences, seven pinned GitHub reports, both report fragments and 39 changed-document relative links/anchors verified |
| Source integrity | All article body bytes and original dates preserved; approved metadata hashes recomputed; prompt archive byte equality and diff whitespace checks passed |

The first HTML audit exposed the root homepage title-template difference; absolute
page titles fixed the mismatch. Two assertions were corrected for React's actual
`dateTime` attribute casing and text separator comments. The initial sandbox could
not bind Wrangler's loopback port; approved local execution passed. Port 8787 was
already occupied, so browser review used a separate local server on 8793 without
interfering with it. A temporary symlinked-dependency build was refused by pnpm's
path safety check; invoking the existing pinned Node/Next tooling directly in the
temporary copy completed both test builds without changing dependencies.

No Python tooling or frozen science changed, so Ruff and the full Python suite
were not rerun. The unchanged full Python CI and Frontend Actions must both pass
for the eventual committed SHA. The supplied green baseline is not a claim that
uncommitted Stage 5B.3 work has passed GitHub CI. No hosted Cloudflare, TLS, DNS,
search-engine processing or external-device launch check has occurred.

## Remaining owner launch decisions

- Resolve the existing engraving's public distribution rights/attribution before
  public deployment. It remains unchanged in the design and export; no social
  promotional use has been added.
- Review this candidate, then separately authorise commit/push and require both
  GitHub workflows green for that exact revision.
- Explicitly authorise the first Workers Static Assets deployment on workers.dev;
  keep noindex. No Pages, SSR, application Worker or backend was added.
- Separately approve DNS/www activation and complete external HTTPS/routing checks.
- Explicitly approve indexing only after www verification; isolate other public
  hostnames before serving an indexing-enabled asset bundle.
- The public forecast snapshot remains disconnected and unavailable. Enabling it
  requires a separate source/export review; no Lightsail access is needed here.

## Changed files

- `docs/stage-05b3-editorial-publication.md`
- `docs/field-notes/README.md`
- `web/README.md`
- `docs/deployment/website-cloudflare-workers.md`
- `prompts/README.md`
- `prompts/stage-05-web/005-editorial-publication-and-search-readiness.md`
- `docs/field-notes/001-when-market-data-isnt-complete.md`
- `docs/field-notes/002-when-a-backtest-meets-trading-costs.md`
- `docs/field-notes/003-the-price-of-changing-your-mind.md`
- `docs/field-notes/004-one-minute-can-change-a-backtest.md`
- `web/content/guides/001-what-is-backtesting.md`
- `web/content/guides/002-understanding-performance-metrics.md`
- `web/content/guides/003-from-forecasts-to-trades.md`
- `web/content/publication-approvals.json`
- `web/lib/content.ts`
- `web/lib/seo.ts`
- `web/app/layout.tsx`
- `web/app/page.tsx`
- `web/app/about/page.tsx`
- `web/app/burrow/page.tsx`
- `web/app/dig/page.tsx`
- `web/app/field-notes/page.tsx`
- `web/app/field-notes/[slug]/page.tsx`
- `web/app/field-guide/page.tsx`
- `web/app/field-guide/[slug]/page.tsx`
- `web/app/robots.ts`
- `web/app/sitemap.ts`
- `web/scripts/prepare-static.ts`
- `web/scripts/smoke-workers.ts`
- `web/tests/publication.test.ts`
- `web/tests/export.test.ts`
- `web/tests/editorial-links.test.ts`
- `web/tests/seo.test.ts`

Recommended commit after owner review:
`feat(web): approve editorial release and prepare search metadata`

Stop here for owner review. No commit, push or deployment was performed.

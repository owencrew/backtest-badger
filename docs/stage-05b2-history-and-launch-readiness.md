# Stage 5B.2 — Full market history and Workers launch readiness

26–27 October 2026, Europe/London. Local implementation and verification, starting
from clean commit `7b1d7cd57341fbdcd6ce544826fbd98db9eccf67`. The owner supplied
[green baseline run 40248197609](https://github.com/owencrew/backtest-badger/actions/runs/40248197609);
this stage did not rerun remote CI. No commit, push, remote preview, deployment,
DNS/GoDaddy action, Lightsail access, database access, model execution or change
to frozen evidence occurred. Next.js, React, TypeScript, semantic CSS and
Lightweight Charts remain in place. The [selected prompt](../prompts/stage-05-web/004-history-and-workers-launch-readiness.md)
is archived verbatim.

## Market history and genuine observations

The public market-data-only Binance API remains the sole source. No research
CSV, PostgreSQL query, proxy, credential or synthetic fallback supplies charts.
The official [kline contract](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data)
was checked for interval names, 12-field responses, inclusive millisecond bounds,
UTC timezone and maximum 1,000 rows. Market identity remains tied to an allowlisted
symbol in the request URL and checked against the ticker's returned symbol;
kline rows themselves do not include a symbol.

Live adapter verification at **19:24:49–19:24:57 UTC on 26 October 2026** produced
the same coverage/counts for **BTCUSDT and ETHUSDT**:

| Range | Interval | First candle opening UTC | Last candle opening UTC | Rows |
| --- | --- | --- | --- | ---: |
| 1D | 5m | 2026-10-25 19:20 | 2026-10-26 19:20 | 289 |
| 7D | 30m | 2026-10-19 19:00 | 2026-10-26 19:00 | 337 |
| 30D | 1h | 2026-09-26 19:00 | 2026-10-26 19:00 | 721 |
| 90D | 4h | 2026-07-28 16:00 | 2026-10-26 16:00 | 541 |
| 1Y | 1d | 2025-10-26 00:00 | 2026-10-26 00:00 | 366 |
| ALL | 1w | 2017-08-14 00:00 | 2026-10-26 00:00 | 481 |

All twelve responses passed validation, had zero **missing intervals at their
selected resolution**, and ended with an explicitly provisional candle. 1Y means
365 elapsed days rounded down to midnight, including the current candle. ALL
currently spans more than nine years, rather than the prompt's approximate nine.
These are dated provider observations, not a continuity guarantee or frozen
scientific dataset. The research's documented four-hour gaps are not contradicted
by an unbroken weekly grid; interruptions can occur inside weekly candles.

Weekly alignment uses Monday 00:00 UTC, offset from the Unix epoch's Thursday.
The verified first weekly bar is labelled **2017-08-14**, with normal Sunday
23:59:59.999 close, even though listing-era trading began on 17 August. The chart
preserves the returned label and explains the partial initial week. It does not
invent pre-listing prices or count pre-listing weeks as missing. Missing bars
from the expected listing week onward, including both response edges, remain
counted. Off-grid timestamps, duplicates, reversed rows, wrong close boundaries,
out-of-window data, invalid OHLC/volumes, bad symbols and clock errors are rejected.
No sorting, interpolation or manufactured replacement rows occur.

All ranges fit one request today. An explicit expected-grid limit rejects ranges
larger than 1,000 candles rather than silently truncating ALL; pagination is not
needed in this stage. A future longer archive will need a bounded pagination
change. The successful observation timestamp only advances after complete
validation and cancellation checks. Ticker price remains an observation time,
not an invented exchange trade timestamp.

## Cache, refresh and presentation

1Y and ALL retain validated raw candles in a per-tab, four-entry memory map,
keyed by symbol and range. Every five-minute/manual/visibility refresh fetches
the Binance clock and ticker plus candles from the previously last candle minus
one interval. The response must satisfy its own requested bounds before merging.
The overlap is replaced, not appended, so open-candle updates and recent revisions
do not duplicate timestamps. New day/week boundaries extend the tail correctly.

The full history is fetched again after 24 hours, or when the page is reloaded.
Old provider revisions can therefore remain unseen until that recheck. Failures,
invalid responses, backwards provider clocks and cancellation do not commit cache
changes. Full-history expiry is never advanced by a tail-only success. Recent
ranges retain their existing uncached bounded fetches. In the live check, each
1Y/ALL repeat downloaded **2 candles**, displaying 366/481 respectively.

The existing polling lifecycle retains one completion-scheduled timer, hidden-page
cancellation, a 15-second deadline, manual replacement, unmount cleanup and stale
warnings. Errors retain a mounted feed's last successful snapshot/time. Switching
market/range clears the old label's snapshot while the new request loads.
No persistent local storage, service worker or backend cache was added.

Six range buttons fit the existing controls, with wrapping allowed on narrow
screens. Actual first/last available candle openings appear above the chart.
Candles/line modes, BTC/ETH, crosshair UTC readout, keyboard slider, pan/zoom/reset,
TradingView attribution and the charcoal/forest/sand/slate palette are retained.
Forward forecasts remain unavailable; the six exact 2024 Dig accounts and Ridge
explanation are unchanged.

## Static hosting and CI

Wrangler **4.153.0**, selected from npm's stable tag, is pinned in the local
package and lockfile. Node **24.22.1** and pnpm **11.25.0** are pinned for CI/builds.
The dependency's workerd install script is explicitly allowed. pnpm added narrow
release-age exceptions for Wrangler and its Miniflare dependency; there is no
blanket install-script or release-age bypass.

`web/wrangler.jsonc` is assets-only, named `backtest-badger-web`, compatibility
`2026-10-26`, directory `./out`, `auto-trailing-slash`, `404-page`. No application
Worker script, SPA fallback, Pages project or server-rendered Next.js was added.
Local Wrangler successfully read this configuration and served the actual export.
A small post-build step removes Next's reserved publication-pending HTML routes,
which otherwise produce soft 404s on a static server, and the maintainer-only
brand README. The real exported `404.html` is retained.

`.github/workflows/frontend.yml` runs independently on pushes and pull requests:
frozen install, ESLint, TypeScript, Prettier, static build, frontend tests, explicit
export audit and local Wrangler HTTP smoke. It has read-only repository permission,
a 15-minute timeout, a standard Ubuntu 24.04 runner and no deployment secrets.
No path filters can leave a required frontend check permanently pending. The
existing Python workflow, its disk-exhaustion repair and guarded tests are unchanged.

The export audit now derives forbidden draft titles/topics/opening text and routes
from actual sources; it also checks for private directories, source/data files,
private-key markers, PostgreSQL URLs and synthetic fixture markers. Missing output
fails rather than silently skipping the publication check. Publication still
requires **Published status plus an exact source-byte SHA-256 approval**. Approval
files and all seven article sources remain unchanged.

## Editorial review for owner approval

All seven articles were read for clarity, grammar, claims, links and publication
fitness. The source reports corroborate the key figures and qualifications. No
substantive scientific correction or grammatical blocker was found. The statuses
below are recommendations, not approval or publication.

| Article | Review and owner recommendation |
| --- | --- |
| Note 001 — When Market Data Isn't Complete | Ready. Clearly separates checksum integrity from validity, preserves 19,955/19,991 counts and 36 gaps per market, and avoids asserting maintenance as proven cause. Its future-tense feature discussion is appropriate to its dated Stage 1B.3 narrative. Optional later note could point readers to completed work; do not rewrite the historical findings. |
| Note 002 — When a Backtest Meets Trading Costs | Ready. Tables agree with Stage 2C, including BTC Ridge +98.53% frictionless versus −88.12% with base costs; explains why separate compounding paths cannot be reconciled by subtracting costs across scenarios. Keeps the three-hour holding window and untouched holdout limits explicit. |
| Note 003 — The Price of Changing Your Mind | Ready. Matches all six E.5g values, trade counts, costs and partial terminal marks. Correctly distinguishes embedded spread/slippage from fees and rejects attributing differences from Stage 2C to execution frequency alone. Requires Note 002 for its internal link. |
| Note 004 — One Minute Can Change a Backtest | Ready and recommended feature. Explains 12:01 availability → 12:02 reference as a convention, not measured latency; 17,568 exact pairs, 8,784 hourly marks per market, 696 February hours and 101 preserved files match the parity report. Correctly limits hashes, first-trade timestamps and fillability claims. Requires Note 003 for its closing link. |
| Guide 001 — What Is Backtesting? | Ready; recommended first introductory guide. Accessible explanation of causality, costs, chronological evaluation and inspected 2024 history. Links point to existing Dig/About pages. |
| Guide 002 — Understanding Performance Metrics | Ready. States funding-relative return, sampled drawdown, zero reference rate and undefined Cash Sharpe correctly; avoids double-counting spread/slippage. |
| Guide 003 — From Forecasts to Trades | Ready. Clearly separates predictions, policy, execution, paper trading and real-money trading. Other strategy families are educational topics rather than implemented features. |

**Minimal connected launch set:** Notes **002 + 003 + 004**, and Guide **001**.
All seven are candidates for approval if the owner prefers a fuller launch.
Approving only 004 would leave a link to an unavailable 003 page, whose own link
requires 002. Resolve that closure through approval, not by bypassing the gate.
004 is the newest eligible article and will lead both journal and homepage.

Production currently has no approved articles. Homepage primary content remains
substantial; its secondary action now opens the live markets when the journal is
empty, and destinations use honest publication states. The Field Guide no longer
exposes build-process wording to visitors. Published guides will no longer carry
hard-coded draft labels, and a lone eligible note will not leave an empty “More”
section. Empty production sections are still disclosed; approving the small set
above is recommended before announcing launch.

The original engraving is retained byte-for-byte and rendered on the sand panel.
**Public distribution rights and attribution remain unconfirmed.** The owner must
resolve this before launch; the MIT code licence does not establish artwork rights.
No replacement artwork was created.

## Verification and remaining launch gates

- Local ESLint, TypeScript, formatting, production build and frontend tests run as
  recorded below; live market verification succeeded for all 12 market/range pairs.
- Local Workers smoke passed the six main pages, repeat requests, slash and
  `index.html` redirects (307 preserving query), byte-identical sampled CSS/JS/fonts,
  mascot/licence assets and real 404s for missing/private/draft-placeholder paths.
  There are no eligible nested articles yet; positive article-route verification
  remains part of the post-approval build. Missing nested routes were tested.
- Browser inspection used the actual local Wrangler production export, with genuine
  Binance requests. BTC ALL and ETH ALL/1Y, line/candlestick controls, earliest-candle
  keyboard readouts and manual refresh were exercised. Desktop/mobile checks and
  final local command outcomes are recorded in the validation summary below.
- No Cloudflare-hosted build, Version URL, TLS certificate, public Custom Domain or
  DNS migration was tested. Public launch remains separately authorised work.

The [owner launch/rollback runbook](deployment/website-cloudflare-workers.md)
contains exact Workers Builds settings, the monorepo content path, candidate upload
versus promotion, initial-Worker bootstrap, Free-plan limits and GoDaddy DNS record
preservation. Recommendation: Builds uploads versions; owner promotes a specific
version after exact-SHA green Python/frontend CI. Do not enable the default automatic
production deploy command. No competing Actions deployment pipeline was added.

Owner decisions: approve articles and exact hashes; confirm mascot rights; decide
search indexing/canonical metadata (current layout remains noindex/nofollow);
approve the first public workers.dev deployment and subsequent DNS/www activation;
reconcile the actual DNS/mail inventory. The public forward snapshot remains a
separate future approval, not a launch prerequisite.

## Final validation summary

Completed on 27 October, with live-market observations dated separately above:

| Check | Result |
| --- | --- |
| Frozen pnpm installation | Passed, including a fresh temporary install without shared node_modules |
| ESLint / TypeScript / Prettier | Passed in the working checkout and fresh build directory |
| Production Next.js export | Passed in both directories; sibling Markdown loader worked |
| Frontend tests | **60 passed, 0 skipped**, in both directories |
| Explicit publication export audit | Passed; no unapproved article bodies, titles, topics or routes found |
| Local Wrangler HTTP smoke | Passed: six main routes, redirects/reloads, six sampled assets and eight missing/private paths |
| Genuine Binance adapter | All 12 symbol/range pairs passed; four long-range refreshes downloaded two rows each |
| Browser | All 12 selections loaded genuine data; candle/line, UTC crosshair, keyboard, manual refresh, pan/zoom/reset exercised; no captured warnings/errors |
| Responsive inspection | Homepage/Burrow at 1440px; all main pages at 390px; six Burrow range controls at 320px. No document-width overflow in checked views; mobile menu opens correctly |
| Original mascot | Rendered on the homepage; `cmp` confirms original reference bytes |
| Python exporter regression | **6 passed** using synthetic fixtures |
| Repository Ruff | Lint and format passed; 247 Python files already formatted |
| Documentation | 53 relative links/anchors checked, plus pinned article source targets in Git |
| Integrity | Prompt byte comparison and `git diff --check` passed; protected source/evidence/publication files unchanged |

The fresh-directory check initially found two missing article files in its
interrupted temporary copy. Restoring the copy from the unchanged repository and
rebuilding produced all 60 passing tests. This was not a publication or source edit.
No full Python scientific suite or guarded historical replay was executed locally;
the unchanged Python workflow continues to require those checks in GitHub. The new
frontend workflow itself has not run remotely. Positive published nested-article
routes, hosted Workers Builds, public TLS and DNS remain launch-time checks.

## Change inventory

- Market adapter/dashboard/CSS: two ranges, Monday alignment, tail cache, boundaries.
- Homepage, journal and guide presentation: honest empty and published states.
- Wrangler config, runtime pin, package scripts, lockfile and workspace install policy.
- Static preparation, local Workers smoke and optional live-market verification scripts.
- Market/publication/export tests and independent frontend workflow.
- This report, deployment runbook, website README, development handoff and prompt index;
  the selected prompt is archived verbatim.

Exact paths, grouped by purpose:

- Chart: `web/lib/market.ts`, `web/components/market-dashboard.tsx`, `web/app/globals.css`.
- Editorial presentation: `web/app/page.tsx`, `web/app/field-notes/page.tsx`,
  `web/app/field-guide/page.tsx`.
- Hosting/tooling: `web/wrangler.jsonc`, `web/.node-version`, `web/package.json`,
  `web/pnpm-lock.yaml`, `web/pnpm-workspace.yaml`, `web/.gitignore`,
  `web/.prettierignore`, `web/eslint.config.mjs`, `web/tsconfig.json`.
- Verification/build: `web/scripts/prepare-static.ts`, `web/scripts/smoke-workers.ts`,
  `web/scripts/check-market-live.ts`, `web/tests/market.test.ts`,
  `web/tests/export.test.ts`, `web/tests/publication.test.ts`,
  `.github/workflows/frontend.yml`.
- Documentation: `web/README.md`, `docs/development-handoff.md`, this report,
  `docs/deployment/website-cloudflare-workers.md`, `prompts/README.md`,
  `prompts/stage-05-web/004-history-and-workers-launch-readiness.md`.

Recommended commit after owner review:
`feat(web): add full market history and Workers launch readiness`

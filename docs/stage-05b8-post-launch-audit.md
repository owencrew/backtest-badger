# Stage 5B.8 — Post-launch audit and documentation synchronisation

28 October 2026, Europe/London (UTC on this date). Public and host checks began
at 17:52 UTC. **The website and genuine forward pipeline are operational, with
one confirmed routing issue and release-management evidence gaps.** This is a
bounded observation, not a guarantee of continued availability.

Production inspection was read-only. No commit, push, build trigger, upload,
promotion, DNS/R2/credential change, service/timer change, research database write,
scientific calculation change, schema change, indexing activation or new frontend
feature occurred. Local documentation was updated and existing checks executed.
Earlier stage reports and all seven editorial source/approval identities are unchanged.

## Production architecture and addresses

| Component       | Current baseline                                                                           | Evidence                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Website         | [www.backtestbadger.com](https://www.backtestbadger.com), Worker `backtest-badger-web`     | Live HTML/assets/browser; Worker identity also in owner build log                         |
| Frontend        | Next.js static export, React/TypeScript, semantic CSS; Workers Static Assets               | Repository configuration and owner hosted build log                                       |
| Delivery        | GitHub-connected Workers Builds uploads candidates; explicit owner promotion               | Owner settings/log; automatic upload command confirmed, preview controls still unverified |
| Registrar / DNS | GoDaddy registrar; Cloudflare authoritative DNS                                            | Registrar owner-reported; NS independently queried through 1.1.1.1 and 8.8.8.8            |
| Nameservers     | `brit.ns.cloudflare.com`, `weston.ns.cloudflare.com`                                       | Both recursive resolvers                                                                  |
| Apex            | [backtestbadger.com](https://backtestbadger.com) → www HTTPS, HTTP 301                     | HTTP and HTTPS checks, including path/query preservation                                  |
| Forward feed    | [data.backtestbadger.com/forward-v1.json](https://data.backtestbadger.com/forward-v1.json) | HTTPS, strict contract, response headers and exact publication readback                   |
| R2              | `backtest-badger-forward`, intended public key `forward-v1.json`                           | Owner declaration and existing publisher code; no authenticated bucket listing            |
| Publishing      | Isolated Lightsail helper, ten-minute schedule, independent HTTPS checker                  | Read-only `ssh Ubuntu-1`, timer state, journals, two retained publication summaries       |
| Research        | Separate collector/scorer on Lightsail                                                     | Successful service results; current release symlink rechecked                             |

The website does not query the research database or ship private evidence. Market
prices come independently from Binance. The public feed is a validated projection
of retained genuine evidence, not simulated performance or a paper portfolio.

## Release identity and CI

The working tree began clean on `main` at
`360c6130d3f304f275cb9f216cca4fa7c82b5976`.
GitHub's public Actions API returned `completed / success` for that exact SHA:

- [CI run 40721333591](https://github.com/owencrew/backtest-badger/actions/runs/40721333591).
- [Frontend run 40721333709](https://github.com/owencrew/backtest-badger/actions/runs/40721333709).

The GitHub connector's combined-status response was empty; it was not treated as
CI success. Actions evidence above was fetched separately. These runs cover the
starting source commit, not this uncommitted documentation update.

The owner supplied active Worker version **`ff180090-8473-4c91-8e51-1bb918fa90bd`**
and the following dashboard settings:

- Root directory `/web`.
- Deploy command `pnpm exec wrangler versions upload`.
- Build command:
  `pnpm install --frozen-lockfile && pnpm lint && pnpm typecheck && pnpm format:check && pnpm build && pnpm test && pnpm test:export && pnpm test:workers`.
- Variable names: `NODE_VERSION`, `PNPM_VERSION`, `NEXT_TELEMETRY_DISABLED`,
  `SKIP_DEPENDENCY_INSTALL`, `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL`. Names alone do not
  establish values. No credentials were requested or inspected.

The supplied 17:38:30–17:43:15 UTC build log confirms Node 24.22.1, pnpm 11.25.0,
Wrangler 4.153.0, skipped automatic dependency installation, successful lint/types/
format/build, 88 tests, eight export tests, and local Workers smoke checks. It reads
assets from `/opt/buildhome/repo/web/out` and uploads the stated version at 17:43:13.
One asset-upload retry recovered successfully; it is not a failed deployment.
The log explicitly requires a later `wrangler versions deploy` to serve production.

The version URL and main alias both returned 200, `noindex,nofollow`, and homepage
bytes identical to www:

- [Exact version preview](https://ff180090-backtest-badger-web.owencrew1999.workers.dev/).
- [Main preview alias](https://main-backtest-badger-web.owencrew1999.workers.dev/).

Homepage SHA-256 across those three observations:
`e308a38d6e8957246ca2c789c73e297c0d7b285cb5cfb65d7fdb460e5e70dc94`.
This corroborates the served homepage, not the entire deployment or source identity.

**Remaining evidence:** the supplied log does not contain a Git SHA, build-detail
URL, active traffic allocation or non-production branch settings. Authenticated
Cloudflare inspection was unavailable (native browser access timed out). The owner
was asked for source mapping and preview settings; the returned log closes the
upload/build evidence gap but not those items. Record the version's exact SHA/build
link and whether non-production builds are disabled or also use upload-only commands.
Do not claim all future pushes are incapable of promotion until those paths are checked.

The selected release process remains: push reviewed commit → exact-SHA Python and
frontend CI → candidate upload → owner checks candidate/version/SHA → explicit
promotion → public verification. Workers Builds does not enforce the independent
GitHub CI gate. For rollback, retain a verified previous version, obtain owner
approval, select it in Deployments or use the explicit version rollback command,
then recheck www, routes, indexing and feed. A Worker rollback does not restore
DNS or R2. See the [release and rollback runbook](deployment/website-cloudflare-workers.md).

The Lightsail research release independently remains
`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`, resolved through
`/opt/backtest-badger/current`. It was not upgraded to website HEAD.

## Public website smoke results

All URLs below returned **HTTP 200 over verified HTTPS**, with full main content
matching a local production build from the checked-out release source. Comparing
normalised main text includes complete articles, not just titles or index excerpts.

| Page        | Exact URL                                                                             |
| ----------- | ------------------------------------------------------------------------------------- |
| Home        | <https://www.backtestbadger.com/>                                                     |
| The Burrow  | <https://www.backtestbadger.com/burrow/>                                              |
| The Dig     | <https://www.backtestbadger.com/dig/>                                                 |
| Field Notes | <https://www.backtestbadger.com/field-notes/>                                         |
| Field Guide | <https://www.backtestbadger.com/field-guide/>                                         |
| About       | <https://www.backtestbadger.com/about/>                                               |
| Note 001    | <https://www.backtestbadger.com/field-notes/001-when-market-data-isnt-complete/>      |
| Note 002    | <https://www.backtestbadger.com/field-notes/002-when-a-backtest-meets-trading-costs/> |
| Note 003    | <https://www.backtestbadger.com/field-notes/003-the-price-of-changing-your-mind/>     |
| Note 004    | <https://www.backtestbadger.com/field-notes/004-one-minute-can-change-a-backtest/>    |
| Guide 001   | <https://www.backtestbadger.com/field-guide/001-what-is-backtesting/>                 |
| Guide 002   | <https://www.backtestbadger.com/field-guide/002-understanding-performance-metrics/>   |
| Guide 003   | <https://www.backtestbadger.com/field-guide/003-from-forecasts-to-trades/>            |

Original mascot rendered on desktop/mobile. The downloaded lossless WebP is
byte-identical to the repository asset, SHA-256
`027832adaf9a2361ebd5c07e464cba405744d1419323e70c8c467bba4474911a`.
Navigation is Home → The Burrow → The Dig → Field Notes → Field Guide → About.
Note 004 leads the homepage feature and journal. Both unwanted homepage phrases
are absent. Historical research figures retain their verified simulation labels.

Unknown `/audit-unknown-5b8/`, both editorial `publication-pending/` paths, `/.env`,
`/tests/fixtures/forward.ts`, `/artifacts/`, `/docs/` and `/brand/README.md` returned
404 on www. `/burrow` and the slashless Note 004 route returned 307 to their
trailing-slash paths, which return 200. There is no SPA-style success fallback.

All 17 JavaScript assets referenced by the audited HTML loaded successfully. No
fixture/private-key/database-URL markers were found in those downloaded scripts;
local export tests additionally scan all generated assets and publication gates.
These are bounded probes, not a complete Cloudflare account/security inventory.

Browser review used 1440×1000 desktop and 390×844 mobile viewports. Homepage,
Burrow cards/tables, main indexes, Dig, About and Note 004 were inspected; no
page-wide horizontal overflow was observed on the checked mobile routes. Forecast
tables remain within labelled horizontal-scroll regions (344px region / 815px
content for primary tables). Mobile menu order and close-on-navigation worked.
Physical mobile-device and assistive-technology testing were not performed.

## The Burrow and scientific display

Both BTCUSDT and ETHUSDT loaded genuine Binance observations for **1D, 7D, 30D,
90D, 1Y and ALL** in the deployed browser. The existing optional live API checker
also passed all twelve market/range combinations at 17:57 UTC:

| Range | Interval | Candles per market | Observed missing candles |
| ----- | -------- | -----------------: | -----------------------: |
| 1D    | 5m       |                289 |                        0 |
| 7D    | 30m      |                337 |                        0 |
| 30D   | 1h       |                721 |                        0 |
| 90D   | 4h       |                541 |                        0 |
| 1Y    | 1d       |                366 |                        0 |
| ALL   | 1w       |                481 |                        0 |

ALL begins at the partial listing-week label 2017-08-14, ending 2026-10-26; weekly
bars do not prove uninterrupted underlying trading. Current candles are explicitly
provisional. The 1Y/ALL refresh check downloaded only two recent candles and retained
history. Candle/line switching and manual price refresh worked; the successful
refresh timestamp advanced to 17:58:49 UTC. UTC source/open/target labels remain
explicit. Existing tests cover five-minute visible-page polling and cancellation;
a full unattended five-minute browser poll was not separately timed in this audit.

The live forward section displayed both markets, Zero, Training mean, Ridge and
Gradient boosting. Primary timely-automated evaluation is visible by default;
late-manual evaluation is collapsed and separate. Empty unattributed cohorts show
no observations/uncalculable metrics, not a table of invented zeroes. Zero accuracy
reads `N/A — zero forecast`, with `0 / 0`. All return/error display values are
labelled **basis points of log return** (original value × 10,000), not simple returns.

Observed source close was 16:00 UTC and target close 20:00 UTC, both 28 October.
Original issuance strings in the validated feed were:

- BTC: `2026-10-28T16:01:12.936151Z`.
- ETH: `2026-10-28T16:01:22.953924Z`.

Both latest predictions were pending, with null realised returns/errors and null
scored timestamps. Each market had 85 primary issued / 84 matched / one pending /
zero mature-unscored / one missing primary opportunity, one late-manual issued and
matched observation, and zero unattributed observations. These are dated counts,
not new scientific findings. Pending forecasts and scored aggregate observations
are distinguished. No current latest-scored card exists.

Fresh/loading states and manual forecast refresh were observed live. Failure,
retained-last-good, stale, undefined metrics, pending→scored→next-issuance and clock
regression cases passed existing isolated tests. No network fault or fake/stale
payload was injected into production; those error states were not induced live.

The deployed Burrow JavaScript explicitly contains
`https://data.backtestbadger.com/forward-v1.json`; none of the downloaded referenced
scripts contains `.r2.dev`. The browser successfully rendered the matching genuine
snapshot. **A browser Network-inspector capture was unavailable through the exposed
browser API.** Compiled URL inspection, browser rendering and independent HTTPS
checks support permanent-host integration, but are not mislabelled as an inspector trace.

## Permanent feed validation and provenance

At 17:55 UTC the endpoint returned HTTP 200 over certificate-verified HTTPS:

- `Content-Type: application/json`.
- `Cache-Control: public, max-age=60, must-revalidate`.
- `Access-Control-Allow-Origin: https://www.backtestbadger.com` for www Origin.
- `Vary: Origin`; exposed ETag, Last-Modified and Cache-Control; `CF-Cache-Status: DYNAMIC`.
- Unapproved Origin returned public data without an allow-origin header, as expected.

The existing `validate-forward.ts` and `check-forward-endpoint.ts` passed. The
installed independent Lightsail checker additionally compared public response bytes
with its validated `last-success.json` and reported `public-feed-healthy`.

| Property        | Verified snapshot                                                  |
| --------------- | ------------------------------------------------------------------ |
| Schema          | Version 1, both markets, all four models and all three cohorts     |
| Bytes           | 10,979                                                             |
| SHA-256         | `72c9068ce52e01929e3caba3a2c64f2195bf495bf03030409d8f4ea27dabade3` |
| Evidence cutoff | `2026-10-28T17:53:17.353158Z`                                      |
| Generated       | `2026-10-28T17:53:32.736967Z`                                      |
| Last-Modified   | `Wed, 28 Oct 2026 17:53:36 GMT`                                    |

Strict nested allowlists reject unexpected fields; the inspected payload contains
no credentials, private paths or raw evidence. R2 root, `/.env`, `/private.json`,
`/previous-success.json` and `/forward-predictions/` all returned 404 at the data
hostname. Bucket-wide contents, permission configuration and credential scopes
were not authenticated/inspected. The old public development URL from the Stage
5B.6 prompt, `https://pub-0bc497d5cf374940a457d2529f7c55b4.r2.dev/forward-v1.json`,
returned **401**, consistent with disabled public access.

The Mac initially could not resolve the data hostname through its system resolver.
Both public recursive resolvers resolved it; a curl request using that observed
address with normal hostname/certificate verification succeeded. Later ordinary
resolution and the unmodified local endpoint checker succeeded. This was a transient
local resolver observation, not evidence of a persistent production outage. No DNS
or resolver settings were changed.

## Scheduled publication and Lightsail health

Read-only journal inspection covered the preceding two hours. Twelve scheduled
publisher runs from **15:53 through 17:43 UTC** succeeded at ten-minute intervals.
All twelve corresponding scheduled checker runs (**15:56–17:46**) reported
`public-feed-healthy`; an additional 17:33:10 check also succeeded. That off-cadence
check is not counted as a timer cycle. The subsequent 17:53 publication and 17:56
scheduled checker also succeeded. Both timers remained enabled.

Two successive retained validated publications were compared in memory:

| Run   | Cutoff                        | Generated                     | SHA-256                                                            |
| ----- | ----------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| 17:43 | `2026-10-28T17:43:17.828279Z` | `2026-10-28T17:43:33.042670Z` | `0b8a6cc7c846b02c8eca9c09e9893be2727bf7eacba6636580309c1cb7f0f8b4` |
| 17:53 | `2026-10-28T17:53:17.353158Z` | `2026-10-28T17:53:32.736967Z` | `72c9068ce52e01929e3caba3a2c64f2195bf495bf03030409d8f4ea27dabade3` |

Complete `latest` and `evaluations` arrays were equal; only clocks advanced.
No forecast or outcome was invented by refreshing/publication. This interval did
not cross a new four-hour issuance/scoring transition. Genuine new-transition
provenance was not independently replayed or traced through raw private evidence;
existing exporter validation/tests and recorded service results provide the bounded
assurance here. No manual collector/scorer runs were triggered.

Collector, scorer, publisher and checker all reported `Result=success`, exit 0.
Collector completed 17:56:06, scorer 17:52:12, publisher 17:53:37 and checker 17:56:05.
Inactive successful oneshot services are normal. Research timers remained enabled.
The failed-unit listing contains the retained historical D3B promotion incident,
as already documented in [D3B.1](deployment/lightsail-d3b1-release-retry.md); it is
not a newly failed publication/research service and was left intact.

Publisher resource sample: **36.41–37.13 seconds wall**, **9.092–9.295 seconds CPU**,
**199,168–199,716 KiB peak RSS** (about 195 MiB). This is consistent with the Stage
5B.5/5B.6 baseline and below the 90-second investigation / 384 MiB MemoryHigh markers.
Host: 3,832 MiB RAM, 2,729 MiB available, 68 GiB free disk, load 0.05/0.09/0.09.
No recurring publication failures appeared in the inspected window. Longer-term
capacity growth, backup freshness and external notification delivery were not audited.

## DNS, HTTPS and indexing

Apex, www and data returned Cloudflare addresses `104.21.34.54` and `172.67.198.198`.
Sharing proxy addresses does not identify origins; independent data hosting is
supported by the owner architecture, separate feed response and live browser URL,
not an invented DNS-only proof of R2 configuration. No obsolete GoDaddy Website
Builder destination appeared in the queried public routing. Private DNS records,
mail, DNSSEC and registrar control were not inventoried.

HTTPS certificate verification succeeded for apex, www and data without bypasses.
Both `https://backtestbadger.com/burrow/?check=1&range=ALL` and its HTTP equivalent
returned **301** to `https://www.backtestbadger.com/burrow/?check=1&range=ALL`.
www HTTPS returns 200 without redirecting to apex. **www HTTP returns 200** at
`http://www.backtestbadger.com/` and `http://www.backtestbadger.com/burrow/?check=1`.
This missing HTTPS enforcement is the confirmed routing defect.

All 13 deployed HTML pages have unique titles/descriptions, exact page-specific
www canonicals and Open Graph URLs, appropriate website/article OG types and
Twitter summary metadata. Article content/dates match the approved source; no
invented publication timestamp is added. HTML says **`noindex, nofollow`**.
`https://www.backtestbadger.com/robots.txt` returns `User-Agent: *` / `Allow: /`
without sitemap advertisement; `/sitemap.xml` returns 404. This intentional crawl
permission lets crawlers read noindex. It is not access control.

Recommend enabling indexing only after the HTTP redirect and release evidence gaps
are closed, alternate public preview/worker exposures are isolated, and the owner
separately approves `BADGER_SEARCH_INDEXING=www-live-owner-approved`. Rebuild and
validate the actual promoted www HTML, robots and 13-route sitemap. Keep preview
builds noindex; changing runtime variables cannot change an existing static export.
No crawler setting was changed for this audit.

## Outstanding issues by severity

| Priority | Finding / affected location                                                                             | Recommended next action                                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| P2       | www HTTP serves 200: `http://www.backtestbadger.com/`, `http://www.backtestbadger.com/burrow/?check=1`  | Separately approve HTTPS redirect for www; preserve paths/query; recheck HTTP/HTTPS without affecting other hosts       |
| P2       | Active Worker version lacks verified Git SHA/build-detail mapping; preview branch policy unknown        | Owner supplies source SHA/build URL and preview disabled/upload-only settings; retain exact CI/version/promotion record |
| P3       | Public version and main alias serve duplicate noindex bundles                                           | Resolve alternate-host isolation before indexing activation; no change needed merely to pass this audit                 |
| P3       | Network-inspector trace, physical-device checks and a new live issuance/scoring transition not captured | Complete targeted acceptance evidence during a later approved review; retain current tests and honest limits            |
| P3       | Systemd monitoring is healthy but external feed alert delivery is not established                       | Separately scope missing-invocation/notification monitoring; retain existing research operations backlog                |

No P0/P1 outage, exposed private payload or new scientific correctness failure was
observed. These results do not establish model profitability or full security coverage.

## Documentation and validation

Updated README, frontend README, current development handoff, both deployment
guides, roadmap and prompt index. Archived the complete original request at
[prompts/stage-05-web/010-post-launch-audit.md](../prompts/stage-05-web/010-post-launch-audit.md).
Historical stage reports remain unchanged; old setup sections are explicitly dated
and distinguished from current production operations.

Executed with pinned Node 24.22.1 / pnpm 11.25.0:

| Check                                                                                    | Result                                                                                          |
| ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Frontend lint / TypeScript / Prettier                                                    | Passed                                                                                          |
| Production static build with permanent URL and indexing disabled                         | Passed                                                                                          |
| Frontend tests                                                                           | 88 passed, no skips                                                                             |
| Publication/export audit                                                                 | 8 passed, also included in the 88                                                               |
| Local Wrangler smoke                                                                     | Passed: 13 routes, redirects, refresh, six assets, real 404s                                    |
| Python public exporter tests                                                             | 16 passed                                                                                       |
| Targeted exporter Python Ruff lint/format                                                | Passed                                                                                          |
| Live Binance checker                                                                     | Both markets, all six ranges, long-range tail refresh passed                                    |
| Public contract / endpoint check                                                         | Passed locally; host checker also matched exact validated publication bytes                     |
| Deployed page/content/metadata/asset checks                                              | Passed subject to the HTTP redirect finding                                                     |
| Documentation links, Markdown structure/whitespace, prompt and editorial identity checks | Passed: 159 local links/anchors, nine Markdown files, seven editorial hashes, exact prompt copy |

Documentation validation included nine incoming references to changed documents.
The new report passes Prettier; all changed documentation passes structural and
whitespace checks. The verbatim prompt intentionally preserves the supplied file’s
missing terminal newline. Only nine Markdown files changed; no published article,
approval manifest, historical stage report or application/scientific source changed.

Initial restricted-network/SSH/local Wrangler attempts needed authorised sandbox
escalation; Wrangler then passed using a temporary log path and local-only server.
The build-generated `next-env.d.ts` pointer was restored to its starting bytes.
No dependency install, historical research replay or full Python research suite was
needed. Browser fault injection and the unavailable Network inspector are not claimed
as completed tests. Local temporary HTTP evidence is under `/tmp/badger-audit/`;
this report retains the meaningful observations and identities without relying on
those temporary files being available in future sessions.

## Future development

**Suggested Stage 5B.9: Latest Scored Forecast**, after owner review of this baseline
and disposition of operational issues. Record the feature now; do not implement it
inside the audit. Show the most recently completed and scored forecast separately
from the latest pending prediction. Visitors should be able to compare each model's
previous prediction, actual observed return, forecast error and directional outcome.
Zero remains directionally ineligible rather than receiving invented correctness.

Review any extension of the versioned public snapshot contract/exporter before
implementation. Retain original evidence provenance, issuance/target/scoring times,
strict cohort separation and unchanged frozen scoring methodology. Do not reconstruct
historical predictions from current fits or treat forecast errors as portfolio returns.

Other backlog retains its existing status: Stage 4C–4E paper persistence/prospective
integration/reporting; external alert, backup/restore and retention verification;
separate owner-approved indexing; future research and asset-class expansion. No
model, strategy, holdout, paper portfolio or real-money capability is added here.

Recommended commit (not executed):
`docs(ops): record post-launch audit and synchronise live infrastructure guides`.

Stop for owner review; unresolved evidence remains explicitly open.

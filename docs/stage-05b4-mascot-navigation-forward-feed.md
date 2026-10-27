# Stage 5B.4 — Original mascot, navigation and forward feed preparation

27 October 2026, Europe/London. Started from clean release candidate
`34b640e545392fe9c653d4490461ed6239e8a880`. This stage is locally implemented;
**no website deployment, public forecast publication, production write, commit or
push occurred**. Genuine forecasts are not connected to the running website.

## Mascot and navigation

The owner-approved `backtest-badger-mascot.png` from Downloads is a 1254 × 1254
RGB PNG without alpha. Its 1,794,240 source bytes are retained at
`design-assets/badger-mascot-original.png`; SHA-256:
`329489b45da2249465a9bcf99fa57849aec168874f3968b5f9b35494aa2d2f47`.
The homepage uses `web/public/brand/badger-mascot.webp`, a 948,680-byte lossless
encoding: 47.1% smaller, with identical decoded RGB pixels. No drawing, crop,
background removal or image regeneration occurred. Multiply blending on the sand
panel, contain sizing and a taller mobile panel preserve claws and soil candles.
The tablet figure label has more inset space. The geometric mark/favicon remains.
The former deployed engraving is removed; `design-assets/badger-reference.png`
is retained as historical material. Originality confirmation applies to the new
owner-supplied work only. The build never reads Downloads.

The shared desktop/mobile navigation is exactly:
**Home → The Burrow → The Dig → Field Guide → Field Notes → About**.
Field Guide replaces The Field Guide in page metadata, section intro, homepage
references, editorial breadcrumbs and footer. Routes and article titles are
unchanged. All four notes and three guides retain their original source bytes and
SHA-256 approvals; 004 remains featured.

Screenshots are local, ignored artifacts under `artifacts/stage-5b4/screenshots/`:
`home-{1440,768,390,320}.png`, `burrow-{width}.png`, `forecast-{width}.png` and
mobile/tablet `navigation-{width}.png`. They show the truthful unconnected feed.
Keyboard Enter opens the menu; Escape closes it and returns focus; link selection
closes it; Field Guide has the active indicator. No page overflow at all four widths.

## Read-only Lightsail inspection and genuine candidate

Authorised SSH inspection confirmed the active Git release:
`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`.
Deployed `forward.py` and `forward_evaluation.py` still match local SHA-256:

- `8487507abd19e406e63561a1c0b9ac36a1a67af8345ac6bcc6625c4bec3c8178`
- `d03febfcf722f6fd04c3ab7f82aeb48d5fbe596b6c4380359e5df37df5e9f290`

The inspected evidence contains 160 forecasts, 158 outcomes and 3,776 collector
journals (4,094 files; 7,624,398 JSON bytes). Read-only inspection found nginx,
Apache and Caddy inactive, no listener on 80/443, and no snapshot at the checked
application public path. **No existing public-safe HTTPS feed was identified.**
This is a scoped host inspection, not an account-wide cloud-resource inventory.
No database connection, environment-secret read, private record/log printing,
service change or installed-package change was performed.

A remote in-memory inventory read each relevant JSON/partial file, then re-read
and hash-compared every file and compared directory membership before sending a
tar stream over SSH. There were no remote writes or writer pauses. It excludes
configuration, database, training files and scoring-operation journals. The local
copy is in a private temporary directory outside the repository, with private
permissions and a hash manifest. All 4,094 copied files still match that manifest.
This captures a stable observed interval, not a database transaction or a claim
that research has stopped changing since acquisition.

The unchanged frozen evaluator validated retained source records, saved outcomes,
cohort evidence and metrics. The existing exporter projected its version-1
allowlist, then the TypeScript validator accepted the complete candidate:

| Candidate property | Result |
| --- | --- |
| Python/evaluator validation | Passed |
| TypeScript public contract | Passed |
| Size | 10,978 bytes |
| SHA-256 | `f570a4a5ef546e8ffa203eb1b0c2fc8b14deec5629c7bec91ca9c1a985de8004` |
| Evidence cutoff (`as_of`) | 2026-10-27T18:41:07.237487Z |
| Generation (`generated_at`) | 2026-10-27T18:41:08.397921Z |
| Latest source close, both markets | 2026-10-27T16:00:00Z |
| BTC issuance | 2026-10-27T16:01:12.429713Z |
| ETH issuance | 2026-10-27T16:01:22.333734Z |
| Latest target close, both markets | 2026-10-27T20:00:00Z |
| Latest status | Pending, timely automated, both markets |

For **each market separately**: primary cohort has 79 issued / 78 matched / one
pending / zero mature-unscored; late manual has one issued / one matched;
unattributed has zero. All four model IDs are present throughout. Primary target
history begins 14 October 20:00 UTC; the late target is 14 October 16:00 UTC.
Empty-cohort metrics and zero-baseline directional accuracy remain null.
Original latest recipe fingerprints are preserved in the private candidate.
Counts are coverage, not profitability claims. All nonempty cohorts remain below
100 matched observations. No raw prediction values or journals are included here.

The candidate was fresh when validated and is deliberately retained unchanged;
its age must not be reset for review. A later read-only benchmark discarded its
in-memory result and preserved the exact original candidate hash. The evaluator's
cutoff applies to the captured evidence copy, not to files written after copying.
No candidate or raw evidence has entered `web/public/`, `web/out/` or Git.
Local private custody can be located via `/tmp/badger-5b4-private-location`; this
pointer is not production infrastructure and may disappear on temporary cleanup.
Archive privately under owner-controlled retention before relying on its longevity.

## Contract, browser behaviour and staging implementation

The [existing version-1 contract](stage-05b-market-dashboard.md#versioned-public-forward-contract)
is unchanged. The four models and three cohorts remain distinct; evaluator output
is authoritative. No independent outcome scoring, return conversion into prices,
model training, ranking or historical performance recalculation was introduced.
Latest recipe identities remain visible; pooled evaluation metrics retain the
frozen evaluator's existing recipe-epoch behaviour within each market/cohort.

The renderer now exposes a separately testable evidence view, clearer dimensionless
four-hour log-return units, a visible error-table caption, UTC source/issue/target
and cutoff times, and the generation time of the latest published snapshot.
Version 1 has **no separate publication timestamp**: generation is labelled as such,
not presented as proof of upload time. A successful browser fetch is not a new
forecast. Market observations still come directly from Binance.

A per-URL loader rejects decreasing cutoff/generation times and backwards latest
forecast identity/status. An aborted response cannot advance its retained baseline.
Failures retain earlier evidence with the existing stale/error treatment. URL checks
reject credentials, non-HTTPS external hosts and backslash/protocol-relative escapes.
The existing polling controller is reused: five minutes after completion, one timer,
manual refresh, hidden-page cancellation/pause, visibility resume, disposal and a
15-second request deadline. Publication becomes stale after 20 minutes by cutoff.
Pending → settling → mature-unscored labels use the target boundary and 60-second
settlement rule; only validated saved outcomes can display scored values.

`web/scripts/stage_forward_snapshot.py` reuses `public_forward_export.py`. Default
mode prepares privately, never uploads. It holds a nonblocking flock for staging
and optional upload, uses a 120-second CLI deadline, private temporary directory,
64 KiB payload cap, 30-second TypeScript subprocess deadline, monotonic candidate
clocks, fsync and atomic replacement. Failed validation preserves the previous
candidate. Both CLIs reject outputs under source evidence, public assets or export
output (including resolved symlink paths). Never unlink a live lock file.

Optional `--publish-r2-object BUCKET/forward-v1.json` invokes the locally pinned
Wrangler **only after both validators pass**, with a 30-second timeout, JSON content
type and `public, max-age=60, must-revalidate`. It uploads one file under the same
lock; no bucket creation or site deployment. It requires explicit owner approval
before use. The upload path was mocked in tests and never executed against a cloud.
The accepted local candidate is replaced only after upload success. A network
failure can leave acknowledgement uncertain even if a complete PUT succeeded:
verify the remote hash before retry/rollback; do not claim the old object certainly
survived that case. No failure fabricates a newer timestamp in the retained file.

## Proposed host, cadence and cost

Recommend a **dedicated Standard R2 bucket containing only `forward-v1.json`**,
served at a separately approved `https://data.backtestbadger.com/forward-v1.json`.
This is a proposed URL, not an existing endpoint. It keeps the static website and
forecast releases independent, requires no server process or public port on Lightsail,
and avoids putting public JSON into the private backup bucket. R2 public buckets
support custom domains; `r2.dev` is intended for development, so it is not the
production recommendation. Custom-domain setup needs the zone in Cloudflare and
separate DNS/resource approval. [Cloudflare public-bucket documentation](https://developers.cloudflare.com/r2/buckets/public-buckets/).

Allow CORS GET/HEAD only from `https://www.backtestbadger.com`; add an exact
workers.dev or loopback origin only if separately approved for review, then remove
it. No wildcard credentials or browser credentials. CORS is not data confidentiality:
the reviewed object is public to anyone. Keep all evidence/staging and prior copies
outside this dedicated public bucket. R2 does not provide public root bucket listing.
[Cloudflare CORS documentation](https://developers.cloudflare.com/r2/buckets/cors/).

R2 object reads/writes are strongly consistent; CDN caches can retain old objects.
Start without a cache-everything rule for JSON, with the 60-second object cache
header above; if caching is later enabled, cap edge TTL at 60 seconds and vary
cached CORS responses correctly. Never rewrite JSON clocks on HTTP fetch.
[Consistency](https://developers.cloudflare.com/r2/reference/consistency/),
[JSON caching behaviour](https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/).

Measured on the private Mac copy: initial preparation **1.165 s**, peak RSS
**201,998,336 bytes**. A separate read-only benchmark used **1.254 s wall / 1.167 s
CPU**, peak RSS **201,670,656 bytes**; zero block input increments reflected warm
cache, not zero logical reads. Data/journal parsing scales with retained history;
the exporter repeats evidence scans. The acquisition hashed about 15.25 MB of
source bytes across its two passes and transferred 10.51 MB with tar overhead.
These are not Lightsail export benchmarks. No forecast/scoring process was run.

A **ten-minute** export is a provisional starting point pending one approved
on-host benchmark: 144 runs/day, roughly 4,320 single-object PUTs per 30 days,
about 47 MB/month of this 11 KB JSON. The local CPU measurement suggests ~168 CPU
seconds/day before Node/upload overhead, not a host guarantee. Browser polling is
**five minutes**, so roughly **48 checks per four-hour forecast interval** for a
continuously visible tab. Export is 24 times per interval. Nominal evidence-to-screen
latency can approach 10 + 5 + 1 minutes plus processing; missing data remains explicit.

Standard R2 currently includes 10 GB-month, 1 million Class A and 10 million Class B
operations monthly; this feed's proposed write volume is small, but shared account
usage and public reads determine actual bills. Obtain budget approval before resource
creation; free tier is not a spending cap. [Current R2 pricing](https://developers.cloudflare.com/r2/pricing/).

## Exact activation proposal — not executed

Separate owner approval is required for each production/publication scope below.
No approval is inferred from this document or from possession of credentials.

1. Review the private candidate identified above, the public allowlist, the proposed
   bucket `backtest-badger-forward`, hostname and operating budget. Approve ongoing
   publication under the same schema explicitly. Refresh from a new stable copy
   before first live publication; review its exact hash and bytes. The dated review
   candidate must not masquerade as a continuously refreshed feed.
2. Under a separate infrastructure/DNS change, create the dedicated Standard bucket,
   attach the proposed hostname, configure exact-origin GET/HEAD CORS and HTTPS,
   keep r2.dev disabled, and provision a scoped publishing identity. Do not reuse
   backup credentials. Verify least-privilege compatibility with the pinned Wrangler
   upload command; no account-wide administration credentials on the research host.
3. Install a reviewed, pinned helper checkout/runtime outside the active research
   release, e.g. `/opt/backtest-badger-public-feed/`, with staging at
   `/var/lib/backtest-badger-public-feed/` (0700). This requires separate approval
   for files, dependencies, permissions and private credential provisioning.
   Do not upgrade the research virtualenv or flip its current release. Node 24.22.1,
   pnpm 11.25.0 and the locked frontend validator dependencies must be available
   in that helper environment; no runtime install/download in each export cycle.
4. First run the default staging command below on host without the upload option;
   measure resource use and full contract validation against current evidence.
   Approve the resulting candidate before the first PUT. Production concurrent
   mutation is checked by the exporter's repeated frozen report; a change causes
   failure and retry at the next tick, never a collector/scorer pause.
5. Only after approval, run the same command with
   `--publish-r2-object backtest-badger-forward/forward-v1.json`. Verify external
   GET bytes/hash, content type, cache headers and CORS with an Origin header.
   Confirm an unapproved origin receives no CORS allowance and private paths 404.
6. Install only a new `backtest-badger-public-feed.service` and `.timer`, independent
   of collection/scoring. Proposed timer: every ten minutes at minute 03/13/23/33/43/53,
   `Persistent=false` (no catch-up burst). Service: oneshot, private umask 0077,
   Nice=10, low I/O priority, TimeoutStartSec=150, MemoryMax=512M,
   KillMode=control-group, no restart loop. Use read-only evidence access and a
   separate writable staging/log directory; do not grant database credentials.
   Review actual unit files and sandbox paths before installation. The existing
   script lock prevents overlapping invocations of the same output path.
7. Monitor both service failure and independently fetched public cutoff age; alert
   on failures or age >20 minutes. Do not treat a successful timer invocation or
   successful GET as fresh evidence. Retain previous successful bytes privately
   before replacement and rotate only helper logs, never scientific evidence.
8. Set `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` to the verified approved URL at website
   build time. Confirm real fetch, both markets, all models/cohorts and at least one
   later snapshot/issuance and scoring transition; leave unavailable until then.
   Obtain exact-SHA green Python/Frontend CI after a separately approved commit/push.
   Follow the existing Workers runbook for separately approved deployment and DNS.
   Keep search indexing disabled until its separate www activation gate.

Proposed command shape, run from the **reviewed helper checkout** only after its
installation is approved (private source directories are supplied by the operator):

```sh
.venv/bin/python web/scripts/stage_forward_snapshot.py \
  --records "$FORWARD_RECORDS" --outcomes "$FORWARD_OUTCOMES" \
  --operations "$FORWARD_OPERATIONS" \
  --output /var/lib/backtest-badger-public-feed/last-success.json
# PUBLIC WRITE: append only after separate explicit publication approval:
# --publish-r2-object backtest-badger-forward/forward-v1.json
```

Rollback: stop/disable **only** the new feed timer and wait for its oneshot to exit;
leave collector/scorer untouched. Revoke the dedicated publisher credential if
needed. Under approval, restore the prior validated object bytes with their original
timestamps and verify after cache expiry; the browser rejects regression and retains
its newer snapshot until reload. If publication must be withdrawn, disable the new
bucket domain's public access. Keep private evidence and candidate copies. Remove
the frontend URL and rebuild only through the separately approved website release
process. Do not roll back scientific evidence, database state or research release.

## Local verification and files

- Frontend lint, TypeScript, Prettier and production static export: passed.
- Frontend tests: **78 passed**; separate publication/export audit: **7 passed**.
- Wrangler HTTP smoke: **13 public routes, redirects, refresh, six assets, true 404s**.
- Python exporter/staging plus frozen evaluator regressions: **122 passed**.
- Scoped Ruff lint and formatting, whitespace and 50 changed-document relative links: passed.
- Complete request archive matches the supplied bytes exactly.
- Isolated synthetic renderer, transitions, invalid/future outcomes, clock regression,
  network/JSON errors, cancellation, hidden/resume, timers and UTC labels: passed.
- Original mascot decode equality and PNG provenance hash: passed.
- Seven article approvals, 004 feature, historical research reconciliation and
  internal exported navigation/fragment checks: passed in frontend suite.
- Genuine candidate independently passed both validators; no live URL was tested.

The initial sandbox blocked SSH and local listener bindings; normal approval
allowed them. A first copy attempt used an older system Python and failed local
safe extraction; Python 3.12 completed it. macOS Downloads access was granted by
the owner. Wrangler and browser checks ran loopback-only. One long Python test name
was shortened after Ruff flagged line length; final checks passed. No remote CI
result is claimed for these uncommitted changes.

Changed areas: homepage/CSS; shared header/footer/editorial and guide labels;
forecast adapter/renderer and tests; exporter output guard; new private-stage/optional
R2-upload wrapper; static smoke/export checks; brand assets and provenance; this
report, web README, deployment runbook, development handoff and prompt index/archive.
No frozen `src/`, research tests, article Markdown, approval JSON, lockfile, CI,
Wrangler deployment config or historical evidence was changed.

Suggested commit, **not executed**:
`feat(web): add original mascot and prepare genuine forward feed`

Exact changed-file inventory (including new files and the removed engraving):

- `design-assets/badger-mascot-original.png`
- `docs/deployment/website-cloudflare-workers.md`
- `docs/development-handoff.md`
- `docs/stage-05b4-mascot-navigation-forward-feed.md`
- `prompts/README.md`
- `prompts/stage-05-web/006-mascot-navigation-forward-feed.md`
- `web/README.md`
- `web/app/field-guide/page.tsx`
- `web/app/globals.css`
- `web/app/page.tsx`
- `web/components/editorial.tsx`
- `web/components/forward-dashboard.tsx`
- `web/components/site-header.tsx`
- `web/components/ui.tsx`
- `web/lib/forecast.ts`
- `web/public/brand/README.md`
- `web/public/brand/badger-engraving.png`
- `web/public/brand/badger-mascot.webp`
- `web/scripts/public_forward_export.py`
- `web/scripts/smoke-workers.ts`
- `web/scripts/stage_forward_snapshot.py`
- `web/tests/export.test.ts`
- `web/tests/forecast.test.ts`
- `web/tests/test_public_export.py`

# Stage 5B.10 — Controlled v2 forward-feed activation

**30 October 2026, 23:21 UTC — v2 backend acceptance complete; website release owner-managed.**

The owner subsequently approved the [backend activation continuation](../prompts/stage-05-web/013-v2-backend-activation-approval.md),
including commit/push, isolated installation, genuine publication, timers and
backend rollback by disabling only the new timers. Website configuration, builds,
promotion and rollback are owner-managed. This supersedes the initial approval
gates below for backend operations only.

The reviewed implementation is committed and pushed as
`6a377e22e660f38cf919ab823ab45229b546c9b9`
(`feat(ops): prepare isolated v2 forward feed activation`). The source-only
artifact rebuilt from that commit is byte-identical to the reviewed archive below.
Both exact-SHA workflows passed before installation. No website deployment was performed.

The original preparation observations below are dated historical evidence; they
do not override the subsequent backend authorisation. The authorised continuation
ends at a healthy v2 feed. The website release remains owner-managed.

The [complete request](../prompts/stage-05-web/012-v2-feed-production-activation.md)
is archived verbatim. Historical reports remain unchanged.

## Approved backend activation — actual operations

The source commit `6a377e22e660f38cf919ab823ab45229b546c9b9` passed both
[CI](https://github.com/owencrew/backtest-badger/actions/runs/41133900665)
(including the new public-feed job and all guarded stages) and
[Frontend](https://github.com/owencrew/backtest-badger/actions/runs/41133900292).
The full CI workflow completed at 22:53:15 UTC; installation began only afterward.
The local 261 Python tests, 144 frontend tests, Ruff, TypeScript, ESLint and
Prettier were also rerun successfully before the implementation commit.

Installed immutable source release:

```text
/opt/backtest-badger-public-feed-v2/releases/0000dbb3ba66f2e0d4bc601543b6580ba9b4f2767f962abe4b9a8e4d90d111da/
```

The root-controlled `current` symlink points to that directory. The source-only
archive SHA-256 is the directory suffix; all 65 payload hashes in `MANIFEST.json`
passed after transfer. `RELEASE.json` records the implementation commit and archive
identity. The original reviewed archive and rebuilt committed-source archive are
byte-identical. Only documentation changed afterward; those changes are not a new
installed backend release.

The existing `.venv` and Node runtime were copied into the isolated release and
compared byte-for-byte. Relocated imports resolve inside the new release:
Python 3.12.3, NumPy 2.5.4, scikit-learn 1.9.1, boto3 1.42.7, Node 24.22.1.
An initial verification command mistakenly imported pandas, which is neither a
project dependency nor present in either runtime; verification was corrected to
the actual dependencies. No package was added/upgraded and no scientific check
was weakened. The existing root:root 0600 environment file remains unchanged;
its contents were not printed, copied or edited.

Both new private state directories are ubuntu:ubuntu 0700. Four new unit files
passed `systemd-analyze verify`; both timers stayed disabled until publication and
independent HTTPS verification succeeded. The runtime-only private qualification
unit omitted `EnvironmentFile` and the upload argument while preserving the exact
25% CPU, 384/512 MiB memory, 32-task, 150-second deadline and filesystem restrictions.

| Operation (30 October, UTC) | Result | Wall time | User/system CPU | Peak RSS |
| --- | --- | ---: | ---: | ---: |
| Private qualification, 22:57:35–22:58:13 | Both validators passed; no upload | 37.80 s | 8.82 / 0.59 s | 214,440 KiB |
| First publication, 22:58:57–22:59:38 | PUT acknowledged; exact R2 readback | 40.80 s | 9.64 / 0.53 s | 214,608 KiB |
| Scheduled publication 1, 23:08:00–23:08:41 | PUT acknowledged; exact R2 readback | 40.41 s | 9.46 / 0.58 s | 214,792 KiB |
| Scheduled publication 2, 23:18:00–23:18:42 | PUT acknowledged; exact R2 readback | 41.22 s | 9.68 / 0.58 s | 214,984 KiB |

Qualification was comfortably below the 90-second / 384 MiB stop thresholds.
Systemd recorded 9.510 CPU seconds for qualification, 10.273 for initial
publication and 10.141 for scheduled publication 1. RSS above is GNU `time`'s
process peak, not an aggregate cgroup peak. Post-exit cgroup MemoryPeak/I/O
counters were unavailable for qualification and the first publication. The
configured cgroup limits remained enforced. During scheduled publication 2,
live counters and its completion journal also recorded a 178,413,568-byte cgroup
peak (170.1 MiB), zero memory high/max/OOM events, 10.359 total CPU seconds,
zero physical disk reads and 81,920 bytes written. The CPU quota actively throttled
the process. This is a warm-cache observation, not a cold-cache or sustained-load test.

The independent checker passed at 23:00:04–23:00:08. A separate local HTTPS fetch
returned HTTP 200, strict schema v2, 14,220 bytes, JSON content type, cache policy
`public, max-age=60, must-revalidate` and exact
`Access-Control-Allow-Origin: https://www.backtestbadger.com`. Its bytes and hash
matched the publisher's private success and R2 readback. BTC and ETH latest
issuance used original 20:00 source closes, targeting 00:00; latest-scored source
closes were 16:00, with original BTC score time `20:07:11.864903Z` and ETH
`20:02:11.798461Z`. No timestamps or saved scientific values were rewritten.

Both new timers were enabled at 23:00:32. They are independent of v1: publisher
at :08/:18/:28/:38/:48/:58, checker at :00/:10/:20/:30/:40/:50 plus 45 seconds.
The extra scheduled 23:00:45 check also passed against the initial publication;
it is not counted as a scheduled publication/check cycle.

| Publication | Evidence cutoff / generation (UTC) | SHA-256 | Independent HTTPS check |
| --- | --- | --- | --- |
| Initial | 22:59:15.174826 / 22:59:33.474654 | `34e272a28c598bbc5daa5eb001b8351e253428743707fad913f5ad8407838e95` | 23:00:07, exact match |
| Scheduled 1 | 23:08:18.187049 / 23:08:36.393241 | `4a807d9fcaab06c705b8ab7c4c4508634c328dfcc5a6529e2e38bf1af5c28e82` | 23:10:48, exact match |
| Scheduled 2 | 23:18:19.100883 / 23:18:37.203861 | `e9f77cbb062b5bd5fb0db71068ba73cff73acad6eafdc94c79eb52fffd26d5c8` | 23:20:48, exact match |

Both scheduled publication/check pairs exited 0 with `Result=success`. Their
independent checks ran at 23:10:45–23:10:49 and 23:20:45–23:20:48, taking about
3–4 seconds and 0.334 / 0.335 CPU seconds. All four v1/v2 timers were verified
enabled and active after acceptance.
A separate public comparison from initial publication to scheduled publication 2
confirmed that only `as_of` and `generated_at` changed; all scientific fields were
identical. Primary counts remained 98 genuine / 97 matched / 1 pending / 0 mature
unscored per market. Original scored rows remained equal while fresh publication
clocks advanced.
A genuine four-hour boundary had not occurred by the 23:21 UTC acceptance cutoff;
no research run was forced. Website transition verification remains owner-managed.

The protected v1 helper/source/unit manifest (73 files) was unchanged after
installation and after both scheduled cycles: SHA-256
`f6a27f4de7f8c20f868bc8202809f9ba2f4f0e1e024cc2aa0c8b73449476d616`.
Research still points to release `cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`.
V1 publisher/checker and research collector/scorer continued succeeding on their
existing schedules. At 23:21 UTC they all had exit 0 / `Result=success`; collection
last completed 23:21:06, scoring 23:17:12, v1 publication 23:13:40 and checking
23:16:04. V1 independently passed strict HTTPS and exact-private-byte verification
with cutoff `23:13:17.821660Z`, generation `23:13:35.905015Z`, 10,971 bytes and
SHA-256 `cf67ac1714728a178fc0f424d031945338558807ffc01d91fcf07256f531db01`.
All v2 state files are 0600 within 0700 directories. The only failed unit is the
pre-existing historical D3B promotion unit, left unchanged.
No existing service, unit, scientific evidence, credential, permission or research
release was changed. No rollback operation was needed. Public probes of
`/qualification-v2.json`,
`/last-success-v2.json` and `/previous-success-v2.json` returned 404. These probes
are not a bucket-wide inventory.

The observations below preserve the initial preparation history. Current
activation results above supersede their proposed/not-yet-installed descriptions.

## Source and baseline

Starting local HEAD and expected Stage 5B.9 source:
`14ed627c28b99c484f7a2f63ef9fc694ad252436` (`feat(web): add latest scored forecasts
and refine homepage`). The working tree was clean. Both workflows subsequently
finished successfully, checked during this session:

- [Python CI](https://github.com/owencrew/backtest-badger/actions/runs/41069725744).
- [Frontend](https://github.com/owencrew/backtest-badger/actions/runs/41069725606).

These historical results validate the starting commit, **not the new implementation**.
A new `public-feed` job in Python CI explicitly collects `web/tests`; root pytest's
configured `testpaths` did not collect the Python exporter/publication suites.
The owner subsequently approved commit/push and required both workflows to pass
for the new exact SHA before backend installation.

Read-only Lightsail observations at 14:16–14:18 UTC, refreshed after the benchmark
at 15:44 UTC:

- Research current release:
  `cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`.
- Collector, scorer, v1 publisher and checker: `Result=success`, exit status 0.
  Both v1 timers enabled. No interruption/restart occurred.
- V1 publisher runs at `:03/10`, checker at `:06/10`. Collection runs at
  `:01/5`, scoring at `:02/5`; other backup/storage/retention timers remain.
- Recent v1 publications took 39.01–40.13 seconds, about 9.8–10.1 CPU seconds,
  and approximately 208,000 KiB peak RSS. Recent checks completed successfully.
- 3,832 MiB RAM total, 2,824 MiB available, no swap; 68 GiB available on root,
  12% used. These are observations, not reserved capacity.
- Python 3.12.3 and Node 24.22.1 in the isolated helper. Publisher CPU quota 25%,
  memory maximum 512 MiB and systemd deadline 150 seconds.
- Private state: ubuntu:ubuntu 0700; configuration directory root:root 0700;
  publisher environment root:root 0600. Secret contents were not read or printed.
- The single failed unit is the previously documented historical D3B promotion
  incident, not a new research/feed failure. It was left intact.

At 14:16 UTC, strict independent v1 HTTPS/schema/freshness/issuance validation and
exact comparison with the host's private last-success file passed. Public object:
10,972 bytes; cutoff `2026-10-30T14:13:17.813839Z`; generation
`2026-10-30T14:13:35.800569Z`; SHA-256
`b8e9a9ece3fc992ba7d8e6f375ee9aadbe0db0960599bcb5a7d8d78954dee87d`.
At 15:44 UTC the same check passed for cutoff `2026-10-30T15:43:17.586499Z`,
generation `2026-10-30T15:43:35.376033Z`, SHA-256
`2ad141e9d3a65022777f87ebeff68f5ac4179f9ea3db21601ad689b253c1295b`.
Normal v1 scheduled publication advances bytes; "unchanged" means its code,
configuration and operation were preserved, not that its object stopped updating.

Public baseline:

- Homepage and Burrow: HTTPS 200 using curl. Homepage has `index, follow` and
  canonical `https://www.backtestbadger.com/`.
- Sitemap: 13 locations. Robots allows crawling and advertises the www sitemap.
- HTTP www, HTTP apex and HTTPS apex redirect to HTTPS www with `/burrow/?check=1`
  preserved (301).
- Browser Burrow inspection showed both genuine pending forecasts targeting
  16:00 UTC, with original 12:01 issuance. Primary aggregates were 95 matched /
  96 issued per market; late/manual cohorts stayed separate. Zero direction N/A.
- V1 metadata: JSON, `public, max-age=60, must-revalidate`, exact www CORS.
  Strict allowlist rejects private/unexpected fields. This is not a bucket-wide
  object inventory or a comprehensive security audit.
- Python urllib's default client received Cloudflare 1010/403; curl and the
  browser succeeded. No protection was weakened to accommodate that client.
- Proposed `forward-v2.json`: 404. No genuine v2 publication occurred.

## Cloudflare evidence and unresolved provenance

Owner supplied version ID `1bb9d5bc-850e-4891-9f10-54c257814bd3` with screenshots:

- Successful build `9f8643ac`, marked manually deployed, duration 4m17s and
  displayed as "1d ago". Its exact source SHA and full build URL are not shown.
- Production branch `main`, root `/web`, deploy command
  `pnpm exec wrangler versions upload`, normal frontend validation build command.
- `BADGER_SEARCH_INDEXING=www-live-owner-approved`.
- Production workers.dev and wildcard preview/version URL toggles disabled;
  www custom domain present. Direct requests to the workers.dev hostname and
  the supplied version's short-prefix hostname returned 404.

This does not establish the newest Stage 5B.9 candidate identity or a verified
current-version-to-source mapping. Preview-branch/Previews Base configuration
also remains outstanding for the owner's later website review; it does not block
the authorised backend continuation. Git pushes may automatically upload candidates
through the existing upload-only command. Local `wrangler.jsonc` explicitly sets `workers_dev` and
`preview_urls` false to preserve the owner's disabled exposure on future uploads.
The remote settings themselves were not changed.

## Implementation

The v1 publisher, stager, exporter, checker, bundler and all four v1 units are
unchanged. The new v2 CLI has **no arbitrary candidate-file input**. It takes
retained evidence directories, invokes existing private v2 staging, and only then
uses the existing dedicated S3 client. A well-shaped JSON fixture alone cannot
prove scientific provenance; genuine evidence validation remains the frozen
Python loader's responsibility.

`web/scripts/publish_forward_v2.py`:

- Exact destination `backtest-badger-forward/forward-v2.json`; rejects v1 and all
  other destinations before preparation/credential lookup.
- Requires `last-success-v2.json` outside the v1 state directory. Persistent
  advisory lock prevents overlapping writers. Private temporary staging is
  cleaned up; published clocks/scored observations cannot regress.
- Reuses `public_forward_v2.prepare` through the unchanged private stager: frozen
  evaluator, before/after evidence inventory and SHA-256, strict v2 validation,
  exact saved Decimal-derived outcomes, both markets and 64 KiB maximum.
- Rejects stale cutoff or missed issuance before loading credentials, even if the
  export generation clock is fresh. Rejects disappearing/older issuance, rewritten predictions, changed saved
  scored rows and regressing genuine/matched counts in any cohort.
- Saves previous validated bytes **without reserialization** to
  `previous-success-v2.json` before attempting the write.
- Requires an explicit HTTP 200 PUT acknowledgement, followed by HTTP 200 S3 GET,
  exact-byte equality, SHA-256 equality, approved content type/cache policy.
  No SDK retry. Lost acknowledgement is failure even if a remote write happened.
- Only successful readback permits atomic private last-success replacement.
  CLI alarm is 120 seconds; fixed journal failure messages avoid SDK/evidence
  details. No synthetic fallback or retiming exists.

`web/scripts/check-forward-v2-endpoint.ts` independently fetches only
`https://data.backtestbadger.com/forward-v2.json`, with normal TLS verification,
redirect rejection and a 15-second request deadline. It checks HTTP 200, JSON,
exact cache policy/www CORS, streamed 64 KiB maximum, strict UTF-8/v2 contract,
both markets, settled primary scores whenever matched primary evidence exists,
chronology, saved numerical/directional consistency, publication age and missed
four-hour issuance after the existing 16-minute allowance. It compares exact
bytes with private publisher last-success and retains its own private validated
snapshot to detect cutoff/generation, score, issuance and count regression across
process restarts. Failed checks do not advance that state. Public checks establish
contract consistency, not independent authentication of intentionally private
raw research records.

The dedicated bundle script builds v2 validator/checker and a stdin-only benchmark
validator; no runtime package download is needed. The benchmark generator sends
reviewed Python modules and bundled JS to memory on the host, never raw evidence
to an external service. It checks installed frozen prediction/evaluator hashes
against the local source before executing.

## Genuine read-only performance benchmark

At `2026-10-30T15:42:04Z`, using the live retained directories and installed locked
Python/Node dependencies, with bytecode disabled, one BLAS thread, nice 10,
idle I/O priority and an outer 100-second timeout:

| Measurement | Result |
| --- | ---: |
| Retained evidence files | 4,991 |
| Whole command wall time (including imports) | 11.83 s |
| Measured total after benchmark imports | 11.5224 s |
| V2 preparation | 5.9548 s |
| Python user / system CPU | 10.9717 / 0.4988 s |
| Peak RSS | 210,960 KiB (206.0 MiB) |
| Inventory/hash scans | 0.3264 + 0.3232 s |
| Strict bundled validator | 0.0460 s |
| Logical reads during preparation | 46,486,797 bytes |
| Physical disk reads during preparation | 352,256 bytes |
| Physical disk writes | 0 bytes |
| Validated public projection | 14,240 bytes |

The small physical read count indicates warm-cache conditions; it is not a
cold-cache or sustained-load result. No production files, units, environment or
publication state were created/modified. An initial attempt failed to locate the
relative protocol document from the SSH home directory; rerunning from the
existing helper working directory succeeded. No scientific check was bypassed.

Candidate cutoff `2026-10-30T15:42:04.395450Z`, generation
`2026-10-30T15:42:09.673877Z`, SHA-256
`49572f5c6821d4db9b144ec09c8c84ae2d27babab6a7704d82f62e004552f89d`.
BTC and ETH latest issuance source: 12:00 UTC, pending. Separate primary scored
source: 08:00 UTC; original scoring timestamps BTC `12:07:12.796145Z`,
ETH `12:02:13.230629Z`. The candidate existed only in process memory/stdin and was
not saved publicly or uploaded.

**Limit:** no cgroup CPU/memory quota was created before production approval.
11.47 CPU seconds implies roughly 46 CPU-throttled seconds at 25%, plus I/O and
validation (an estimate, not a measured constrained run). Observed RSS is below
384 MiB soft / 512 MiB hard limits. A successful qualification under the installed
service's exact restrictions is mandatory **before the first PUT or timer enable**.
Stop if preparation exceeds 90 seconds or peak RSS reaches 384 MiB; investigate
without weakening provenance or silently expanding resources.

## Isolation and reviewed schedule

Proposed separate release root:
`/opt/backtest-badger-public-feed-v2/releases/<reviewed-artifact-sha256>/`, with
root-controlled `current` symlink. Source/protocol/bundles have independent manifest
hashes. Populate its Python and Node runtimes from copies of the existing pinned
helper runtimes; verify interpreter/module versions at the new location. Do not
modify or upgrade the original runtimes. A failed relocation blocks activation.

Private state directories, ubuntu:ubuntu 0700:

- `/var/lib/backtest-badger-public-feed-v2/`: publisher last-success, previous
  success and persistent lock; private qualification output uses a distinct name.
- `/var/lib/backtest-badger-public-feed-v2-check/`: `last-check-v2.json`.

Four new units under `/etc/systemd/system/`, all prefixed
`backtest-badger-public-feed-v2`. Publisher reads the existing root-protected
`/etc/backtest-badger-public-feed/publisher.env` via systemd only; no new secret or
configuration file is proposed. Checker receives no credentials.

Publisher: CPU 25%, MemoryHigh 384 MiB, MemoryMax 512 MiB, TasksMax 32,
TimeoutStartSec 150, no restart loop; source evidence bound read-only into a
private namespace. Research installation/state/database sockets and v1 state are
inaccessible; only v2 state is writable. Checker: CPU 10%, 128 MiB, 30-second
service deadline; read-only publisher state, only its own state writable.
Both follow existing filesystem/kernel/privilege hardening conventions.

Proposed publisher at minutes **08/18/28/38/48/58 UTC**. Checker at
**00/10/20/30/40/50 minutes, second 45** (2m45s later across the hour boundary).
The host's read-only `systemd-analyze calendar` accepted both expressions.
This separates expensive scans from v1 at :03/10 and from the usual collection/
scoring starts. Research jobs can run longer than their typical durations, so this
is staggering, not a guarantee of no contention. The checker starts 15 seconds
after the hard service window. Persistent=false and Restart=no prevent catch-up
bursts; the next natural tick retries. One missed publication can remain within
the 20-minute freshness threshold; repeated failures must alert an operator.
No external alert delivery is implemented or claimed.

## R2 permissions and exposure

The documented existing token is Object Read & Write scoped to this bucket.
[Cloudflare's permission model](https://developers.cloudflare.com/r2/api/tokens/)
permits reading/writing/listing objects within the selected bucket; the static
bucket credential is not restricted to one object by this application's allowlist.
The owner confirmed in this session that the existing token still has exactly
that bucket-only Object Read & Write scope, so the new key needs no broader
permission. This is owner-confirmed policy; the
successful v1 writer alone would not prove the complete scope. Do not print keys,
create tokens, rotate credentials or widen permissions to resolve a failure.

The custom domain makes the new reviewed JSON public. CORS is not authentication.
Only the strict public projection belongs in the bucket, never raw evidence,
backups, private state, bundles or credentials. Keep r2.dev disabled. Probes of the bucket root, `/.env`, `/private.json`, `/previous-success.json`
and `/forward-predictions/` all returned 404. This is not a bucket-wide inventory;
that inventory and current development-domain state still require owner confirmation.

## Validation and boundaries

Executed locally using Python 3.12 and Node 24.22.1 / pnpm 11.25.0:

- 261 Python tests: frozen forward/evaluation, v1/v2 exporter/stager and 27 new
  publisher tests. Faults cover destination/version, malformed synthetic source,
  private fields, size, deadline, direction, missing scores, clocks, concurrent
  lock, hash/metadata mismatch, PUT/GET failure and lost acknowledgement. All R2
  calls are mocked. V1 private state remains unchanged in transaction tests.
- 144 frontend tests including 16 new independent v2 checker cases, existing v1/v2
  public-contract and UI regressions. No test publishes fixtures.
- Whole-repository Ruff lint/format, ESLint, TypeScript and Prettier pass.
- Default/noindex static build, 9 export checks and local Wrangler smoke pass:
  13 routes, redirects, refresh, 6 assets and real HTTP 404s.
- Indexed static build, the same 144 frontend tests, 9 export checks and local
  Wrangler smoke also pass. Both configurations used the existing v1 public URL;
  neither was uploaded. Final documentation/path and protected-file checks are
  recorded below.

Wrangler initially could not bind loopback inside the sandbox; the same local-only
smoke test passed with the required local execution permission. No remote Worker
command ran. Builds remain configured against v1 for these regressions. Phase E's
v2-connected release candidate is intentionally deferred until v2 is publicly
verified. No new article, editorial approval or scientific source changed.

## Original Gate 1 plan — subsequently authorised

Approval is required by sections 6 and 14 of the archived owner request. The local checks below are complete and the owner confirmed existing token scope.
At initial preparation no installation/publication approval had been given. The
subsequent continuation now authorises these backend steps, conditional on
exact-commit green CI and successful exact-limit private qualification.
The precise proposed operations are:

1. Transfer only reviewed source/protocol/bundle files and their manifest into a
   new root-controlled v2 release directory. Copy existing pinned runtimes there;
   verify hashes/imports. Create the two private v2 state directories and `current`
   symlink. Leave the v1/research installations untouched.
2. Install only the four new v2 service/timer files, run systemd unit verification
   and daemon-reload, keeping all new timers disabled.
3. Run a bounded **private preparation-only qualification** under the publisher's
   exact CPU/memory/timeout/filesystem bindings, using a transient qualification
   unit without credentials. Write only a distinct private qualification candidate.
   Record duration/RSS and strict validation; remove no retained research evidence.
   Stop on limit violation. The continuation explicitly authorises this qualification.
4. With the owner-confirmed existing bucket credential, run one v2 publisher
   oneshot. This performs the first authorised PUT of `forward-v2.json`. Compare
   S3 and public bytes/hash, validate both markets and independent HTTPS checker.
5. Only if successful and v1/research remain healthy, enable the two v2 timers.
   Observe at least two scheduled publication/check cycles with timestamps, hashes,
   exit status and duration. Do not force research events.

The original preparation scope excluded commit/push, credential changes, Cloudflare configuration,
Worker upload/promotion, DNS, paid resources and research-service changes.

## Rollback and later release gates

Before website promotion, v1-configured www remains the fallback; a failed v2
activation does not require a website change. With the separately authorised
installation/disable scope, disable only the new v2 timers:

```sh
sudo systemctl disable --now backtest-badger-public-feed-v2.timer
sudo systemctl disable --now backtest-badger-public-feed-v2-check.timer
# Only if an in-flight run must be cancelled:
sudo systemctl stop backtest-badger-public-feed-v2.service
```

Retain v2 private success/rollback bytes and installed version. No R2 delete, v1
shutdown, clock rewrite or v1-schema substitution at the v2 URL. On uncertain
acknowledgement, inspect remote bytes against the intended candidate and backup;
local last-success is not evidence that the remote object stayed unchanged.
Future successful genuine publication may recover after investigation. Restoring
an old public v2 object would need a separately reviewed operation and may rightly
fail freshness/regression monitoring; do not reset those checks to hide it.

For website rollback, the supplied version ID is a **candidate rollback identity**
until its actual active state, exact source SHA and v1-configured asset mapping
are independently recorded. Do not claim rollback has been exercised. The owner manages any website promotion or rollback and its
homepage/Burrow/feed/indexing/sitemap/redirect checks.

The owner's website release follows genuine healthy public v2 operation and
exact-SHA green CI: set the build variable, build, review the exact candidate
version/build/source mapping and promote manually with preview protections intact.
Git pushes may upload candidates automatically; no manual build, upload or
promotion is part of this backend continuation. A real four-hour transition must
be observed naturally; no research job may be triggered to force one.

Next milestone: finish this controlled activation and observe genuine operation;
then separately scope longer-running monitoring/notification verification. Do not
infer profitability or long-term reliability from these tests.

## Initial local verification and reviewed installation artifact

Local link-path validation checked 162 Markdown targets with zero missing files.
The archived prompt is byte-identical to the supplied attachment. A Git comparison
confirms no change to scientific sources/protocol, editorial sources/approvals,
public v1 helpers, the v2 scientific exporter/contract, or existing v1 unit/config
files. Generated Next.js type-reference churn was restored to its starting bytes.
`git diff --check` passes. Full root integration/backtest suites were not rerun
locally; focused frozen-forward/export suites are reported above, and the starting
commit's full GitHub CI succeeded. These were the results available before the
subsequently authorised implementation commit and its own CI runs.

A local, private, source-only installation archive is prepared at
`/tmp/badger-5b10-reviewed-source.tar` (993,280 bytes, 66 files including manifest).
SHA-256:
`0000dbb3ba66f2e0d4bc601543b6580ba9b4f2767f962abe4b9a8e4d90d111da`.
It contains Python source, frozen protocol, dependency identity files, the exact
v2 bundles and four units. It contains no environment file, credentials, private
candidate or retained evidence. `MANIFEST.json` records every payload file hash.
At initial preparation it had not been transferred to production. Any code/bundle/unit change requires
rebuilding and reviewing a new archive identity before installation.

The proposed release directory suffix is that archive digest. Do not deploy an
unreviewed working-tree variant. Runtime copies are intentionally excluded from
the archive; copy only the existing pinned `.venv` and `node` directories into
the new release, verify relocated imports and versions, and record their identity.
All new units must pass host `systemd-analyze verify` and the exact-limit private
qualification before any public write. Unit runtime/namespace correctness has
not tested during the initial read-only preparation. The owner subsequently
authorised installation and required this trial before the first PUT.

## Complete changed-file inventory

- `.github/workflows/ci.yml`
- `README.md`
- `docs/deployment/forward-feed-cloudflare-setup.md`
- `docs/deployment/website-cloudflare-workers.md`
- `docs/development-handoff.md`
- `docs/roadmap.md`
- `docs/stage-05b10-forward-v2-production-activation.md`
- `ops/public-feed/backtest-badger-public-feed-v2-check.service`
- `ops/public-feed/backtest-badger-public-feed-v2-check.timer`
- `ops/public-feed/backtest-badger-public-feed-v2.service`
- `ops/public-feed/backtest-badger-public-feed-v2.timer`
- `ops/public-feed/benchmark-v2.py`
- `ops/public-feed/bundle-v2-validator.mjs`
- `prompts/README.md`
- `prompts/stage-05-web/012-v2-feed-production-activation.md`
- `prompts/stage-05-web/013-v2-backend-activation-approval.md`
- `web/README.md`
- `web/scripts/benchmark-forward-v2-validator.ts`
- `web/scripts/check-forward-v2-endpoint.ts`
- `web/scripts/publish_forward_v2.py`
- `web/tests/forward-v2-endpoint.test.ts`
- `web/tests/test_publish_v2.py`
- `web/wrangler.jsonc`

## Approval and completion ledger

| Scope | Actual state |
| --- | --- |
| Local implementation and synthetic fault tests | Committed/pushed; both exact-SHA workflows green |
| Genuine retained evidence on Lightsail | Validated in place; no raw transfer |
| Exact service quota/namespace qualification | Passed: 37.80 s, 214,440 KiB RSS; no upload |
| Existing R2 token scope | Owner confirmed bucket-only Object Read & Write; unchanged |
| Production writes / credentials / R2 uploads | Isolated v2 installed and published; credentials unchanged |
| V2 scheduled publication / independent checker | Both timers enabled/active; two scheduled cycles passed |
| Two scheduled v2 cycles | 23:08 / 23:10:45 and 23:18 / 23:20:45; all passed |
| Four-hour transition through v2 and frontend | Not observed at acceptance cutoff; website remains owner-managed |
| Website v2 build / www promotion | Owner changes build variable, triggers build and manually promotes reviewed candidate |
| Indexing/alternate URLs | Existing www indexing and disabled alternate exposure preserved |
| Preview-branch builds / exact rollback provenance | Owner's website release review; not a backend blocker |

Implementation commit: `6a377e22e660f38cf919ab823ab45229b546c9b9`
(`feat(ops): prepare isolated v2 forward feed activation`).

## Owner-managed website release

The backend continuation stops at a healthy v2 feed. Codex did not change
Cloudflare build variables, DNS, R2 settings, credentials, permissions or Workers
Builds settings, trigger a manual website build, or promote/roll back a Worker.
Git pushes may automatically upload candidates through the existing upload-only
command; an automatic upload is not a production promotion.

The remaining website release steps are for the owner:

1. Open Cloudflare → Workers & Pages → `backtest-badger-web` → Settings → Builds
   → Production → Variables and secrets. Set only
   `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` to
   `https://data.backtestbadger.com/forward-v2.json` and save it.
2. Keep `BADGER_SEARCH_INDEXING=www-live-owner-approved`, production branch `main`,
   root `/web`, the existing validation build command and candidate-only
   `pnpm exec wrangler versions upload`. Keep production workers.dev and
   version-preview URLs disabled; preserve the existing preview-branch safeguards.
3. Trigger a new build of the reviewed source. Confirm its successful validation
   log and exact commit/build/Worker-version mapping. The feed URL is a build-time
   value: changing it alone does not update the existing static website.
4. Review the resulting v2-configured candidate and record the current
   v1-configured active version as the rollback target. Manually promote the
   reviewed candidate when ready. No additional backend activation is needed.
5. After promotion, check homepage, Burrow current and latest-scored rows, original
   issuance/scoring timestamps, fresh v2 fetch, www indexing/canonical/robots,
   13-page sitemap, redirects preserving path/query and disabled alternate URLs.
   Keep v1 running. Any website rollback is also owner-managed.

At the 23:21 UTC acceptance cutoff, a natural four-hour issuance/scoring transition
and longer-running operational monitoring remained observations to collect; do not
force research events or treat a short successful activation as evidence of
long-term reliability.

## Documentation closeout

The post-activation documentation update changes seven Markdown files only; no
backend, scientific, editorial, frontend implementation or installed artifact
changed. All 134 relative Markdown targets checked resolve, `git diff --check`
and the frontend format check pass. Both workflows must also be green for the
resulting documentation commit before final handoff; that commit identity and its
CI results are reported separately from the installed source identity above.
Acceptance measurements in this report are dated through 23:21 UTC on 30 October.

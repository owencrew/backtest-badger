# Stage 5B.10 — Controlled v2 forward-feed activation

**30 October 2026 — backend activation approved; awaiting committed-source CI and
exact-limit qualification before installation/publication.**

The owner subsequently approved the [backend activation continuation](../prompts/stage-05-web/013-v2-backend-activation-approval.md),
including commit/push, isolated installation, genuine publication, timers and
backend rollback by disabling only the new timers. Website configuration, builds,
promotion and rollback are owner-managed. This supersedes the initial approval
gates below for backend operations only.

**Initial preparation record:**
No commit, push, production installation, R2 PUT, credential/configuration change,
Worker upload or promotion has been performed. V1 continues serving www. This
stage is **not complete** until the separately approved feed and website release
have passed their public acceptance checks.

The [complete request](../prompts/stage-05-web/012-v2-feed-production-activation.md)
is archived verbatim. Historical reports remain unchanged.

## Source and baseline

Starting local HEAD and expected Stage 5B.9 source:
`14ed627c28b99c484f7a2f63ef9fc694ad252436` (`feat(web): add latest scored forecasts
and refine homepage`). The working tree was clean. Both workflows subsequently
finished successfully, checked during this session:

- [Python CI](https://github.com/owencrew/backtest-badger/actions/runs/41069725744).
- [Frontend](https://github.com/owencrew/backtest-badger/actions/runs/41069725606).

These results validate the starting commit, **not these uncommitted changes**.
A new `public-feed` job in Python CI explicitly collects `web/tests`; root pytest's
configured `testpaths` did not collect the Python exporter/publication suites.
New code must be committed/pushed only after owner review, then receive green CI
for its own exact SHA before a website release.

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
also remains outstanding. Do not promote or upload an indexed candidate until
these are recorded. Local `wrangler.jsonc` now explicitly sets `workers_dev` and
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

## Isolation and proposed schedule

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

## Approval Gate 1 — proposed operations, not executed

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
   Stop on limit violation. This transient unit itself requires Gate 1 approval.
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
are independently recorded. Do not claim rollback has been exercised. After
Gate 2 promotion, request owner authorisation to restore the verified previous
v1-configured Worker, then recheck homepage/Burrow/feed/indexing/sitemap/redirects.

Phase E needs a genuine healthy public v2 endpoint, the new reviewed source commit
and both green workflows, owner-set v2 build variable, confirmed preview-branch
safety and exact candidate version/build/source mapping. Gate 2 then separately
approves promotion to 100% traffic. No candidate/upload/promotion for this stage
exists yet. A real four-hour issuance/scoring/frontend transition is outstanding;
no boundary was fabricated or research job triggered.

Next milestone: finish this controlled activation and observe genuine operation;
then separately scope longer-running monitoring/notification verification. Do not
infer profitability or long-term reliability from these tests.

## Final local verification and reviewed installation artifact

Local link-path validation checked 162 Markdown targets with zero missing files.
The archived prompt is byte-identical to the supplied attachment. A Git comparison
confirms no change to scientific sources/protocol, editorial sources/approvals,
public v1 helpers, the v2 scientific exporter/contract, or existing v1 unit/config
files. Generated Next.js type-reference churn was restored to its starting bytes.
`git diff --check` passes. Full root integration/backtest suites were not rerun
locally; focused frozen-forward/export suites are reported above, and the starting
commit's full GitHub CI succeeded. New uncommitted code has no GitHub CI result yet.

A local, private, source-only installation archive is prepared at
`/tmp/badger-5b10-reviewed-source.tar` (993,280 bytes, 66 files including manifest).
SHA-256:
`0000dbb3ba66f2e0d4bc601543b6580ba9b4f2767f962abe4b9a8e4d90d111da`.
It contains Python source, frozen protocol, dependency identity files, the exact
v2 bundles and four units. It contains no environment file, credentials, private
candidate or retained evidence. `MANIFEST.json` records every payload file hash.
It has **not** been transferred to production. Any code/bundle/unit change requires
rebuilding and reviewing a new archive identity before installation.

The proposed release directory suffix is that archive digest. Do not deploy an
unreviewed working-tree variant. Runtime copies are intentionally excluded from
the archive; copy only the existing pinned `.venv` and `node` directories into
the new release, verify relocated imports and versions, and record their identity.
All new units must pass host `systemd-analyze verify` and the exact-limit private
qualification before any public write. Unit runtime/namespace correctness has
not yet been tested on the host because installation requires approval.

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
| Local implementation and synthetic fault tests | Completed; commit/push authorised, pending exact-SHA CI |
| Genuine retained evidence on Lightsail | Read-only preparation/validation passed; no raw transfer |
| Exact service quota/namespace qualification | Authorised; pending exact-SHA CI and installation |
| Existing R2 token scope | Owner confirmed bucket-only Object Read & Write |
| Production writes / credentials / R2 uploads | No writes yet; backend activation authorised, credential changes forbidden |
| V2 scheduled publication / independent checker | Not installed or activated |
| Two scheduled v2 cycles | Not observed |
| Four-hour transition through v2 and frontend | Outstanding |
| New website v2 candidate / www promotion | Not prepared, uploaded or promoted; Gates 1 and 2 remain |
| Indexing/alternate URLs | Public www indexable; owner screenshots and tested alternate URLs show disabled exposure |
| Preview-branch builds / exact rollback provenance | Outstanding before website release |

Suggested Conventional Commit (only after owner authorisation):
`feat(ops): prepare isolated v2 forward feed activation`.

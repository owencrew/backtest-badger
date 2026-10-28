# Stage 5B.5 — Forward feed activation and navigation

28 October 2026, Europe/London. **Helper installed; feed not publicly active.**
The owner subsequently requested instructions to perform Cloudflare setup personally.
No Cloudflare login, resource creation, public upload, credential creation, DNS
change or Workers website deployment was performed. Both new host timers are
installed and disabled. No repository commit or push was made.

## Verified baseline

The repository started clean at `03e3f6022d17b78ceed2e6f19f1c5216f4f0b76a`.
Both exact-commit Actions runs succeeded:
[Python CI](https://github.com/owencrew/backtest-badger/actions/runs/40564389156)
and [Frontend](https://github.com/owencrew/backtest-badger/actions/runs/40564389001).
Those runs cover the starting commit, not these uncommitted changes.

Authorised SSH inspection confirmed the active research release remains
`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1` at
`/opt/backtest-badger/current`. The deployed implementations still match:

| File | SHA-256 |
| --- | --- |
| `forward.py` | `8487507abd19e406e63561a1c0b9ac36a1a67af8345ac6bcc6625c4bec3c8178` |
| `forward_evaluation.py` | `d03febfcf722f6fd04c3ab7f82aeb48d5fbe596b6c4380359e5df37df5e9f290` |
| Frozen protocol | `9bb655a374af27ecf41b0f31947dfad4256eb40e8973d53caf278507084d4bed` |

The collector and scorer retained successful results/exit status 0 before and
after the new helper's failure test. Neither was stopped, restarted or changed.
The research virtualenv, database, model recipes and scientific source files were
not modified. Existing forecast/scoring jobs continued their normal schedules.

## Isolated helper installed

- Root-owned code/runtime: `/opt/backtest-badger-public-feed/`.
- Private staging: `/var/lib/backtest-badger-public-feed/`, owner `ubuntu`, mode 0700.
- Private configuration directory: `/etc/backtest-badger-public-feed/`, root, 0700.
  **No filled credential file exists yet.**
- Independent Python 3.12.3 virtualenv, using hash-checked production dependencies
  exported from the repository's unchanged `uv.lock`.
- Separate S3 requirements: `ops/public-feed/r2-requirements.txt`, fully pinned and
  hashed; boto3 1.42.7 and its resolved dependencies. The research environment was
  not upgraded or reused.
- Node 24.22.1 from the official Linux x64 distribution, verified against the
  vendor SHA256 manifest. The existing TypeScript validator is bundled using
  esbuild from the locked frontend install; no Next.js/Wrangler installation or
  package download happens during an export.
- Rebuild the two standalone JavaScript entry points from the repository root with
  `node ops/public-feed/bundle-validator.mjs /tmp/badger-feed-bundle` after the
  locked frontend install. This bundles existing validation logic without a second
  schema implementation.
- `HELPER-SHA256SUMS` records the installed exporter, publisher, validator,
  monitor, frozen modules and protocol identities.

The publisher uses the S3-compatible API. Inspection of pinned Wrangler 4.153.0
confirmed its remote object PUT uses Cloudflare REST; Cloudflare states that
Object Read & Write tokens work only with the S3 API. Do not solve this by putting
an account-wide token on Lightsail. [R2 authentication](https://developers.cloudflare.com/r2/api/tokens/).

The only permitted upload is `backtest-badger-forward/forward-v1.json`. The helper
requires both markets before publication, validates with the frozen evaluator and
complete browser contract, performs one PUT with explicit metadata, then GETs the
stored object and compares exact bytes and headers. It never creates buckets or
changes public access. Credentials use explicit `R2_*` environment values, not
ambient AWS credentials or the research backup credential.

The Stage 5B.4 lock, 120-second total alarm, 30-second validator/upload deadlines,
64 KiB cap and atomic private replacement remain. Before replacement, a prior
successful snapshot is retained as `previous-success.json`, privately. Failure
preserves local last-success bytes/clocks; a lost PUT acknowledgement can still
mean the complete remote object changed, so verify the remote hash before rollback.
No synthetic fallback or fabricated generation timestamp is generated on failure.

### Service identity and isolation

Existing evidence and future atomic files are owner-only. A different Unix UID
would require widening evidence permissions or changing the writers. Instead the
new service reuses `ubuntu` **inside a restricted systemd filesystem namespace**.
It has read-only mounts of only predictions, outcomes and collection journals at
`/run/badger-feed-evidence/`; the original research tree, other research state,
home directories, database socket and Docker socket are inaccessible. Only the
separate staging directory is writable. No evidence ACL was changed.

An executed sandbox check confirmed all three mounted evidence types readable
and not writable, original research code/state and home inaccessible, and private
staging writable. This isolates the service filesystem; it is not a new host-wide
security principal against a compromised administrator or another `ubuntu` process.
The independent public checker uses `DynamicUser=true` and no S3 credentials.

Units are in `/etc/systemd/system/` and versioned under `ops/public-feed/`:

- `backtest-badger-public-feed.service` and `.timer`.
- `backtest-badger-public-feed-check.service` and `.timer`.

Export cadence: minutes 03/13/23/33/43/53 UTC. Checker: 06/16/26/36/46/56.
Both use `Persistent=false`, no catch-up burst. Export is oneshot with flock,
`Nice=10`, idle I/O priority, 25% CPU quota, MemoryHigh 384 MiB, MemoryMax 512 MiB,
TasksMax 32, TimeoutStartSec 150 and no restart loop. Units passed
`systemd-analyze verify`. No new listener/inbound port is introduced.

### Measured genuine export

Host inspection found 3,832 MiB total / about 2,823 MiB available RAM and 69 GiB
free disk. The private preflight ran with the export unit's actual sandbox and
resource limits, without upload or credentials:

| Measurement | Result |
| --- | --- |
| Elapsed | 33.64 seconds |
| User/system CPU | 7.81 / 0.57 seconds |
| Systemd total CPU | 8.476 seconds |
| GNU time peak RSS | 195,040 KiB (about 190 MiB) |
| Python/evaluator validation | Passed |
| Bundled TypeScript contract | Passed |

The 25% CPU limit explains the longer wall time. At this measured workload,
144 daily runs use about 20 CPU minutes/day (roughly 1.4% of one core on average),
plus publishing overhead. This supports the initial ten-minute cadence; retained
history grows, so these are measurements, not permanent capacity guarantees.

The original candidate remains private, with its original clocks:

| Property | Value |
| --- | --- |
| Bytes | 10,897 |
| SHA-256 | `54de5ae722bf98a437bbbebac6eb3ddc2299122d07baf0b541aea40a30c4474a` |
| Evidence cutoff | 2026-10-28T00:18:33.723922Z |
| Generated | 2026-10-28T00:18:49.304330Z |
| Source close, both markets | 2026-10-28T00:00:00Z |
| BTC issued | 2026-10-28T00:01:12.917133Z |
| ETH issued | 2026-10-28T00:01:22.847494Z |
| Target close, both markets | 2026-10-28T04:00:00Z |
| Latest status | Pending, timely automated, both markets |

Each market has 81 primary forecasts / 80 matched / one pending / zero
mature-unscored; one late-manual forecast matched; zero unattributed. All four
models and all three cohorts are present, with undefined statistics preserved.
The unchanged exporter projects only the version-1 allowlist; TypeScript rejects
unexpected keys at every object level. No raw paths, journals, credentials or
training data appear in that contract. The copied local candidate also passed the
original TypeScript validator. It is not bundled into `public/` or `out/`.

A controlled missing-source run of only the new helper failed with
`category=invalid_candidate`; the existing candidate SHA-256 and clocks remained
identical. This did not interrupt the collector or scorer. Disabling both new,
already-inactive timers was also tested. No publication rollback was tested because
no public upload occurred.

## Owner Cloudflare setup

Follow the concrete steps in [the public-feed operator guide](deployment/forward-feed-cloudflare-setup.md).
No further written approval for the already-authorised scope is needed; account
login, MFA, billing activation and credential entry remain owner actions.

Resource plan: **one Standard bucket** `backtest-badger-forward`, containing only
`forward-v1.json`. Preferred endpoint:
`https://data.backtestbadger.com/forward-v1.json` — **proposed, not active**.
A temporary managed `https://pub-….r2.dev/forward-v1.json` is acceptable for local
acceptance while the DNS migration remains pending. Its exact hostname is not yet
allocated. Never reuse the private backup bucket or CNAME a hostname to r2.dev.

A 30-day schedule needs approximately 4,320 PUTs, 4,320 S3 readbacks and 4,320
independent public checks, plus browser traffic; one object is at most 64 KiB.
R2 Standard includes 10 GB-month, one million Class A and ten million Class B
operations monthly. These incremental requirements are small, but **existing
account usage was not inspected**. Check account totals and projected public reads
before activation; the free tier is not a spending cap. Do not approve a paid
upgrade. [R2 pricing](https://developers.cloudflare.com/r2/pricing/).

Public DNS queries returned GoDaddy `ns23.domaincontrol.com` and
`ns24.domaincontrol.com`; apex A records `13.248.243.5`, `76.223.105.230`; www CNAME
`backtestbadger.com`. No answers were returned for the queried apex MX/TXT or data
hostname. This is a limited public observation, **not a complete zone inventory**.
The Cloudflare zone/account was not inspected or changed. No assigned Cloudflare
nameservers are known, so an exact registrar cutover pair cannot yet be supplied.
Free-plan full DNS migration must remain a separate, reviewed owner cutover.

### Planned public behaviour, not yet observed

`Content-Type: application/json`; `Cache-Control: public, max-age=60, must-revalidate`.
The CORS JSON allows GET/HEAD from www and the exact loopback review origins on
3000/8787, without browser credentials. CORS does not make this data confidential;
anyone may fetch it directly. Remove loopback origins after acceptance. Keep
previous snapshots private. Do not configure Cache Everything for this JSON;
verify actual cache behaviour if later adding a cache rule.

**Public HTTP 200, bytes/hash, caching, CORS, private-object denial and two successive
publication cycles are not yet verified.** No new issuance/scoring transition was
observed through a public feed. Those checks await the owner's R2 setup and scoped
credential. Fresh candidate preparation must run again at activation; do not
publish this review candidate as a fresh continuously updated feed.

## Local website and navigation

Correct shared order:
**Home → The Burrow → The Dig → Field Notes → Field Guide → About**.
Routes, active indicators, menu accessibility and all seven approved article source
bytes/hashes are preserved. The exported-navigation regression assertion was
updated. Desktop and 390px mobile browser checks confirmed the order, Enter opening,
Escape closing with focus returned to Menu, active Burrow highlighting and
close-on-link-selection. Field Notes still features 004 before 003/002/001.
Screenshots are ignored local artifacts under `artifacts/stage-5b5/screenshots/`.

The actual Next.js development server and local Wrangler static export were
opened and inspected. The unconnected forward state is truthful. Genuine Binance
market observations still load independently. No fixture was attached to either
site, and no environment-specific public URL has been configured because none
exists yet. The export audit now accepts either the unconnected state or the
awaiting-first-verified-fetch state needed by a configured build. Connected BTC/ETH
rendering, actual HTTPS fetch, local CORS and two-cycle UI refresh remain pending.

## Monitoring and rollback

The publisher emits sanitised categories for invalid candidates, public-contract
rejection, source/lock/deadline failure and publication/readback failure. GNU time
logs elapsed time, CPU and peak RSS for every run. Inspect repeated failures and
resource growth using journalctl and systemd; investigate elapsed times approaching
90 seconds or RSS approaching 384 MiB before the hard limits are reached.

The independent checker validates HTTP status, JSON content type, exact cache
policy, www CORS, size, full schema, both markets, cutoff age (20 minutes) and
missed forecast issuance (separate four-hour boundary plus 16-minute window).
A fresh exporter clock cannot hide missed source issuance from this check.
A failed service/check is visible in systemd and the journal; no email/page/SMS
alert or external notification service has been configured.

```sh
ssh Ubuntu-1
systemctl list-timers --all 'backtest-badger-public-feed*'
systemctl --failed
sudo journalctl -u backtest-badger-public-feed.service --since '1 day ago'
sudo journalctl -u backtest-badger-public-feed-check.service --since '1 day ago'
```

Exact scoped rollback:

1. `sudo systemctl disable --now backtest-badger-public-feed.timer`. A timer stop
   does not cancel an in-progress oneshot; let it finish, or for an incident stop
   **only** `backtest-badger-public-feed.service`. Never stop the research units.
2. Optionally disable the checker timer too. Leave it enabled if monitoring a
   deliberately retained endpoint; it should report old evidence as stale.
3. In Cloudflare R2 API tokens, revoke only the dedicated feed token. Do not touch
   the private backup token. Remove the filled private publisher environment file
   if retiring the helper; do not print it or erase research state.
4. In this dedicated bucket's Settings, disable the public development URL and
   disable every custom-domain access route. Verify unauthenticated requests fail.
   Removing only one public access route is insufficient if another stays enabled.
5. For a selective rollback, first stop publication, compare public bytes (a PUT
   timeout is ambiguous), validate the private `previous-success.json` with the
   installed Node validator, then upload **those original bytes** with the scoped
   S3 publisher and securely loaded credentials. Re-run the public checksum check;
   preserve its old timestamps, which may truthfully be stale. No previous approved
   public object exists yet in this stage, so do not perform this step now.
6. Remove only `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` from local `web/.env.local`,
   restart development and rebuild the static export. Do not edit research evidence.

See the operator guide for concrete activation and exact-byte restoration commands.

## Validation and remaining work

Completed: 125 distinct focused Python tests (16 exporter and 109 frozen evaluator); frontend
lint/typecheck/format, static build, 81 frontend contract/polling/publication/export
checks, and the existing local Workers smoke (13 routes, redirects, six assets,
real 404s). All seven approved articles and approval manifest retain their hashes.
The prompt archive is byte-for-byte identical to the supplied request.

Outstanding: owner R2/account usage review, bucket and scoped credential creation,
public endpoint configuration, first upload/readback, actual HTTPS/CORS/cache tests,
two successive scheduled publications, and connected local dev/production UI checks.
Permanent data-domain activation additionally requires the separately reviewed DNS
cutover. The first public Workers website deployment remains the next milestone.

Recommended commit after review: `feat(web): prepare isolated forward feed activation and correct navigation`.

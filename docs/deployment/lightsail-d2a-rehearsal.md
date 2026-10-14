# Stage D2A — Lightsail migration rehearsal

**Tooling prepared; no remote rehearsal or cutover executed.** This guide implements
only the rehearsal part of the [authoritative D2 runbook](lightsail-migration-runbook.md).
Every command below is an **operator procedure**, not an action already performed.
Do not run the runbook's production initialisation or activation sections in D2A.

The operator reports D1 installed at commit
`556e3a9b80066b2d83cf1e1e4ee5795fc6ec290f`, both Mac LaunchAgents running,
and three constrained synthetic benchmarks of 17.60, 17.81 and 18.11 seconds.
These establish neither actual provider/database latency nor concurrent production
capacity. No host facts were independently checked remotely during implementation.

## Boundaries and layout

D2A leaves Mac collection/scoring running. It never creates `workers-approved`,
starts/enables production services/timers, initialises the production DB, edits
scientific sources/protocols, changes a record or its runtime/issuance timestamps,
or generates genuine predictions/outcomes. There is no cleanup command. Retain
failed copies, attempt markers, volumes and logs; removal requires separate explicit
authorisation identifying the disposable resources. Never use `down -v`, `--clean`,
`rsync --delete`, `alembic upgrade`, source DB integration tests, or D1's
`prepare-release.sh` for this rehearsal.

| Resource | D2A location/identity |
| --- | --- |
| Operator tooling | New `/home/ubuntu/d2a-tools-<id>/`, separately checksum verified |
| Staging parent | `/var/lib/backtest-badger-rehearsals`, ubuntu owned, 0700 |
| Unique run | `<parent>/rYYYYMMDDtHHMMSSz-8hex/`, 0700 |
| Private plan/config | `plan.json`, `postgres.env`, `readonly.env`, `worker.env`, 0600 |
| Received backup | `<run>/inbox/`; never merged into an older copy |
| Copied checkout/evidence | `<run>/work/` and `<run>/work/artifacts/`; real directories |
| Independent Compose project | `badger-d2a-<id>` |
| Independent external volume | `badger-d2a-<id>-pg17` |
| Database / admin / worker | `d2a_<id with hyphen replaced by underscore>` / `d2a_admin` / `d2a_worker` |
| Endpoint | **127.0.0.1:55437**, never production port 5432 |
| Results | `<run>/restored-database`, `database-comparison.json`, `evidence-validation`, `rehearsal-report.json` |

The private `readonly.env` contains the inspection **admin** credential; the Python
snapshot code enforces read-only transactions from connection startup. The name
does not imply a read-only role. `worker.env` has a different generated password;
creating/granting its role is a separate step below. Never print these files or
resolved Compose configuration. All scripts suppress raw DB/Docker errors.
Docker administrators remain trusted and can inspect credentials/data.

Every remote action checks the exact reviewed hostname (SSH alias `Ubuntu-1` is
not necessarily `hostname`), Linux x86_64, private ownership/modes, fixed canonical
staging paths, absent production volume/gate, and inactive/disabled production
units. Missing/unreadable systemd state fails closed. Environment overrides cannot
select another Docker context or change Compose interpolation. Restore also checks
container image, project labels, mount, database/user and actual loopback binding.
Use one operator at a time; do not create manual DB clients during restore.

## A. Prepare Mac backup destination — Mac

Run Bash, with no shell tracing. Choose an **existing, privately mounted encrypted
backup destination outside the repository**. Do not substitute the artifact tree.
Do not stop or change either LaunchAgent. Inspect current identity/configuration
privately and set the reviewed values below; these are deliberate fail-closed
placeholders, not guessed host/database identities.

```bash
cd /Users/owencrew/Code/backtest-badger
bash
set -euo pipefail
set -o noclobber
umask 077
.venv/bin/python -B ops/lightsail/rehearsal.py --help
hostname
# Set these explicitly after review; do not source .env or print its contents.
mac_host=REVIEWED_MAC_HOSTNAME
source_db=REVIEWED_SOURCE_DATABASE
source_port=REVIEWED_SOURCE_PORT
backup_parent=/ABSOLUTE/APPROVED/ENCRYPTED/PRIVATE/DIRECTORY
# Parent must already exist, be owned by this user, and have mode 0700.
test -d "$backup_parent"
rehearsal_id="r$(date -u +%Y%m%dt%H%M%Sz)-$(openssl rand -hex 4)"
backup_dir="$backup_parent/$rehearsal_id"
test ! -e "$backup_dir"
# Read-only scheduler inspection. Retain the output privately if needed.
launchctl print "gui/$(id -u)/com.backtestbadger.forward-collection"
launchctl print "gui/$(id -u)/com.backtestbadger.forward-scoring"
# Identify only this project's DB container, then review before use.
docker compose ps -q postgres
```

Record operator, UTC start, Mac hardware/OS/Python, available disk space (`df -h`),
source container ID and source DB name/port. Use the complete 64-character container
ID. Make an explicit capacity plan: DB size, full artifact bytes, source archives,
backup archive, extracted rehearsal, restored DB, later final copy and reserve.
A logical dump can be much smaller than its restored DB. Reject a plan that would
consume the 80 GB disk or leave insufficient headroom for PostgreSQL sorts/WAL.
Long read-only snapshots retain old row versions; avoid coinciding with DDL, monitor
I/O/collection delays, and abort/retry later if necessary. No exclusive table locks
or scheduler coordination are used; normal DML can continue.

## B. Create manifests and online backup — Mac

The reviewed D2A files must be present in this checkout. They may remain uncommitted:
`source.tar` includes every tracked and nonignored untracked source file, plus a
Git HEAD bundle, binary working-tree patch and path/hash inventory. Review
`git status --short` for accidental secrets and needed **ignored** source first.
Ignored source outside `artifacts/` is not automatically included. Separately retain
historical fingerprint epochs and original OS/Python/installers in protected backup
storage; a current source bundle does not reconstruct every historical runtime.

```bash
source_container=REVIEWED_FULL_64_CHARACTER_CONTAINER_ID
uv run --locked --no-sync --offline --env-file .env python -B \
  ops/lightsail/rehearsal.py backup \
  --expect-host "$mac_host" --expect-database "$source_db" \
  --expect-port "$source_port" --container "$source_container" \
  --output "$backup_dir"
# Copy the printed manifest SHA-256 into a separately retained private audit record.
bundle_sha256=REVIEWED_PRINTED_64_CHARACTER_SHA256
.venv/bin/python -B ops/lightsail/rehearsal.py verify \
  --bundle "$backup_dir" --bundle-sha256 "$bundle_sha256"
```

Inherited `POSTGRES_*` values take precedence over `uv --env-file`; the explicit
host/DB/port checks must match the intended source. The script additionally compares
the TCP connection's PostgreSQL cluster identifier and database with the identified
Compose container. It does not modify the original database, artifact bytes/modes/
mtimes, lock inodes or installed schedulers. Reading can update filesystem atime.

The backup contains:

- Custom-format complete PostgreSQL 17 logical dump, checked `pg_restore --list`,
  schema SQL, Alembic state, exact row counts/hashes, markets, identity/UTC ranges,
  revision distributions, sequence states, source ownership/ACLs and a globals
  inventory **without role passwords**. Never execute that globals file on Linux.
- A read-only REPEATABLE READ exported snapshot shared by the dump, schema export
  and logical table audit. Rows use length-framed PostgreSQL JSON text and SHA-256;
  decimal values never pass through Python floats. All provenance columns and
  complete candle revisions participate. C collation fixes logical sort ordering.
- Complete `artifacts.tar`, including frozen Stage 1/2 inputs/manifests, experiments,
  backtests/economic diagnostics, acquisition/provenance, forecasts/outcomes,
  operational logs/cursors, hidden locks and partial/interrupted files. There are
  no scientific-directory exclusions. Empty directories, file modes and nanosecond
  mtimes are retained in PAX metadata; Linux ownership is explicitly mapped later.
- `artifacts.before.json`, `artifacts.archive.json`, `artifacts.after.json` and
  `online-changes.json`. The archive manifest describes the exact captured bytes.
  An append/replacement during capture is reported, not silently repaired. Symlinks,
  special files, unreadable files or truncation can fail the backup; retain the
  partial output and use a new ID after investigation.
- `source.bundle`, verified with Git, complete current `source.tar`, source/lock/
  protocol SHA-256 inventory, source status/patch and Python/platform/package
  versions. No `.env`, keys or Mac `.venv` are copied into source/artifacts.
- `bundle.json`, published only after successful export/archive checks. Its SHA-256
  must be retained outside the transferred bundle. Failure leaves `FAILED.json` or
  an unsealed partial directory; neither is a valid backup.

**This is always a nonauthoritative online rehearsal snapshot**, even when all scans
match. DB/artifacts have different capture times; files can change between scans,
and journals can refer to absent/later data. PostgreSQL sequences are not MVCC:
sequence movement during the dump/audit is detected and refused, but absence of a
detected change is not a cross-system consistency proof. Roles/ACLs are operator
inventory, not a synchronised cluster-wide backup. No historical late/incomplete
observation is removed or reclassified. D2B must repeat the entire capture with
all writers fully quiescent.

Before final cutover, create **two independently retained encrypted backup copies**,
at least one outside Lightsail. One example is the verified bundle on an encrypted
external disk plus a second new dated copy on a separate encrypted off-machine
backup store. Use your approved backup/encryption tool, separate access controls
and retention; provide credentials through that tool's private mechanism. Do not
hardcode tokens or assume an SSH transfer alone encrypts data at rest. Restore each
copy into a new directory and rerun `verify` against the separately retained hash.
Record destination identifiers, encryption/key recovery arrangements and successful
read-back verification privately. Lightsail staging is not either copy by default.

## C. Prepare isolated staging and transfer — Mac and Lightsail

**Mac:** copy only the reviewed tooling to a new private bootstrap directory. These
commands are manual future operator actions; implementation made no SSH connection.
Use the existing trusted SSH alias and host key; never bypass host-key verification.

```bash
tools_dir="/home/ubuntu/d2a-tools-$rehearsal_id"
ssh -o StrictHostKeyChecking=yes Ubuntu-1 "umask 077; mkdir '$tools_dir'"
shasum -a 256 ops/lightsail/rehearsal.py ops/lightsail/rehearsal_db.py \
  ops/lightsail/rehearsal_files.py ops/lightsail/compose.rehearsal.yaml
scp -p ops/lightsail/rehearsal.py ops/lightsail/rehearsal_db.py \
  ops/lightsail/rehearsal_files.py ops/lightsail/compose.rehearsal.yaml \
  "Ubuntu-1:$tools_dir/"
```

**Lightsail:** enter Bash as `ubuntu`, set the same ID and independently reviewed
manifest hash. Verify bootstrap file SHA-256s against the Mac values. Use the D1
interpreter to run bootstrap tooling; this does not edit the active release.

```bash
set -euo pipefail
set -o noclobber
umask 077
rehearsal_id=PASTE_THE_MAC_REHEARSAL_ID
bundle_sha256=PASTE_THE_RETAINED_MANIFEST_SHA256
server_host=REVIEWED_OUTPUT_OF_SERVER_HOSTNAME
tools_dir="/home/ubuntu/d2a-tools-$rehearsal_id"
python=/opt/backtest-badger/current/.venv/bin/python
sha256sum "$tools_dir/rehearsal.py" "$tools_dir/rehearsal_db.py" \
  "$tools_dir/rehearsal_files.py" "$tools_dir/compose.rehearsal.yaml"
# Only if the staging parent is absent; inspect an existing parent instead.
if test ! -e /var/lib/backtest-badger-rehearsals; then
  sudo install -d -o ubuntu -g ubuntu -m 0700 /var/lib/backtest-badger-rehearsals
fi
```

Select a trustworthy image from the [official PostgreSQL image](https://hub.docker.com/_/postgres).
Review the desired **17.x** release/security notes and its **linux/amd64** registry
manifest using `docker buildx imagetools inspect postgres:17`. Record the full
reviewed digest and version; do not copy an illustrative or invented digest. Tag
inspection is discovery only. Explicitly pull the immutable reference:

```bash
postgres_image=postgres:17@sha256:REPLACE_WITH_REVIEWED_DIGEST
postgres_version=REPLACE_WITH_REVIEWED_17_MINOR_VERSION
docker --context default pull --platform linux/amd64 "$postgres_image"
docker --context default image inspect "$postgres_image" \
  --format '{{.Architecture}} {{.Os}} {{json .RepoDigests}}'
"$python" -B "$tools_dir/rehearsal.py" prepare \
  --id "$rehearsal_id" --expect-host "$server_host" \
  --image "$postgres_image" --pg-version "$postgres_version"
run_dir="/var/lib/backtest-badger-rehearsals/$rehearsal_id"
"$python" -B "$tools_dir/rehearsal.py" preflight \
  --id "$rehearsal_id" --expect-host "$server_host"
# mkdir (not mkdir -p) refuses a prior/partial received backup.
mkdir -m 0700 "$run_dir/inbox"
```

`prepare` checks architecture/digest and runs only `postgres --version` without a
network or retained DB volume. It generates private independent credentials and a
recorded plan; no research database starts. Later commands use `pull_policy: never`.
Reuse this exact reviewed digest for final production restoration unless a different
image is separately reviewed/approved. See [Docker digest pinning](https://docs.docker.com/reference/cli/docker/image/pull/).

**Mac:** transfer the verified bundle into that new `inbox`. Use rsync 3.x on both
ends with nanosecond timestamp support; Apple's older bundled rsync may truncate
mtimes. Verification deliberately rejects that loss. Retain a partial transfer and
start a new run rather than merging a retry into unknown files.

```bash
rsync -a --checksum --protect-args -e 'ssh -o StrictHostKeyChecking=yes' \
  "$backup_dir/" "Ubuntu-1:/var/lib/backtest-badger-rehearsals/$rehearsal_id/inbox/"
```

**Lightsail:** validate all paths, sizes, modes, timestamps and SHA-256s before
extraction, then extract source and artifacts into new directories and verify again.
Tar owners are never adopted: every extracted file belongs to executing `ubuntu`.
Read-only scientific file modes and original mtimes are preserved. No recursive
chmod/chown of evidence is necessary.

```bash
"$python" -B "$tools_dir/rehearsal.py" verify \
  --bundle "$run_dir/inbox" --bundle-sha256 "$bundle_sha256"
"$python" -B "$tools_dir/rehearsal.py" unpack \
  --id "$rehearsal_id" --expect-host "$server_host" --bundle-sha256 "$bundle_sha256"
```

## D. Initialise the isolated PostgreSQL — Lightsail

Review disk space on **both** the staging filesystem and Docker's data filesystem
(`docker info --format '{{.DockerRootDir}}'`, `df -B1`). Set the required free-byte
budget from step A, including reserve. The automated free-space check measures the
staging filesystem; if Docker uses another filesystem, its free-space check is a
separate mandatory operator gate. No production volume should exist.

```bash
required_free_bytes=REVIEWED_INTEGER_BYTE_BUDGET
"$python" -B "$tools_dir/rehearsal.py" init \
  --id "$rehearsal_id" --expect-host "$server_host" --bundle-sha256 "$bundle_sha256" \
  --pg-version "$postgres_version" --required-free-bytes "$required_free_bytes" \
  --confirm "badger-d2a-$rehearsal_id-pg17"
ss -ltn '( sport = :55437 )'
```

Capture command stdout/stderr in new private log files when executing the checklist;
never enable shell tracing. The scripts suppress raw credential-bearing diagnostics.
`init` refuses an existing volume/container or attempt marker. It creates only the
labelled external rehearsal volume and independent project, with PG limited to
1 GiB/one CPU and no swap, matching D1's DB budget. A failed initialisation is retained;
it is never automatically adopted or removed. Port 55437 permits one run at a time.
Use separately authorised lifecycle handling if an earlier rehearsal occupies it.

## E. Restore and compare — Lightsail

```bash
rehearsal_db="d2a_${rehearsal_id//-/_}"
"$python" -B "$tools_dir/rehearsal.py" restore \
  --id "$rehearsal_id" --expect-host "$server_host" --bundle-sha256 "$bundle_sha256" \
  --confirm "$rehearsal_db" > "$run_dir/restore.stdout" 2> "$run_dir/restore.stderr"
```

Restore verifies the complete bundle and dump TOC before writing, requires an empty
DB without other sessions, and creates an exclusive attempt marker. `pg_restore`
uses `--exit-on-error --single-transaction --no-owner --no-acl`, never `--clean` or
migrations. All objects map to the isolated admin. Even a rolled-back failure
requires investigation and a **new** run; no automatic retry overwrites state.

`database-comparison.json` compares all four tables' exact logical hashes/counts,
market identities/ranges, native coverage, revision distributions, sequence values
and `is_called`, Alembic `0001`, and schema SQL (columns, indexes, constraints,
functions, trigger definitions/enabled state and sequence definitions). Only random
psql `\restrict` tokens and dump client/server version comment headers are excluded
from the schema hash. Cross-minor dump formatting differences can therefore fail
conservatively; retain both schemas and investigate, never weaken comparison silently.
Unexpected application schemas/tables fail closed for review instead of being skipped.
Distinct cluster IDs plus checked container/mount/network identity establish isolation.
Source ownership/ACLs are retained separately for explicit Linux role mapping.

Configure the worker **only inside this checked rehearsal container**. Obtain its
full ID from `initialized.json`, compare it to `docker compose ... ps -q`/the plan,
and open an interactive psql session (no passwords in shell arguments):

```bash
container=FULL_REHEARSAL_CONTAINER_ID_FROM_INITIALIZED_JSON
docker --context default exec -it "$container" sh -ec \
  'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

In psql, first inspect `\conninfo`, `SELECT current_database();` and `\du` and confirm
the exact rehearsal DB/admin. Refuse an existing worker role and investigate it.
Then apply the D1 worker grant policy to the isolated copy:

```sql
CREATE ROLE d2a_worker LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
\password d2a_worker
-- Enter the generated worker.env password from a private editor/password manager.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SELECT format('REVOKE ALL ON DATABASE %I FROM PUBLIC', current_database()) \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO d2a_worker', current_database()) \gexec
GRANT USAGE ON SCHEMA public TO d2a_worker;
GRANT SELECT ON market, candle, candle_revision TO d2a_worker;
GRANT INSERT, UPDATE ON candle TO d2a_worker;
GRANT INSERT ON candle_revision TO d2a_worker;
-- Review effective privileges without trying a mutation on research data.
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication
FROM pg_roles WHERE rolname='d2a_worker';
SELECT has_table_privilege('d2a_worker','candle','SELECT') AS can_select,
       has_table_privilege('d2a_worker','candle','INSERT') AS can_insert,
       has_table_privilege('d2a_worker','candle','UPDATE') AS can_update,
       has_table_privilege('d2a_worker','candle','DELETE') AS can_delete,
       has_table_privilege('d2a_worker','candle','TRUNCATE') AS can_truncate,
       has_schema_privilege('d2a_worker','public','CREATE') AS can_create;
```

Expected privileges: first three true; last three false. Review owners, memberships,
PUBLIC/default grants and all three tables. Worker must not own any table/schema,
manage roles or disable triggers. Keep role acceptance output separately; changes
in grants intentionally happen **after** exact restore comparison. Exercise actual
permission failures only on separate synthetic disposable databases, never through
integration fixtures aimed at the restored research cluster. Do not load test admin
DSNs into the production or restored research environment.

## F. Validate immutable evidence — Lightsail, with Mac replay separately

Build a **new** rehearsal environment. Use installed Python 3.12.15 and locked wheels;
do not copy the Mac virtualenv or change the active release's artifact link.

```bash
cd "$run_dir/work"
test ! -e .venv
uv sync --locked --no-dev --no-install-project --no-build \
  --python 3.12.15 --no-python-downloads
.venv/bin/python -B - <<'PY'
import sysconfig
from pathlib import Path
# Install only the copied source path, without modifying pyproject/lock/source.
with Path(sysconfig.get_path('purelib'), 'backtest_badger.pth').open('x') as out:
    out.write(str(Path.cwd() / 'src') + '\n')
PY
.venv/bin/python -B ops/lightsail/rehearsal.py evidence \
  --id "$rehearsal_id" --expect-host "$server_host" --bundle-sha256 "$bundle_sha256"
```

This verifies every copied source hash, frozen Stage 1/2 pins and the unchanged
Stage 3C protocol, then invokes the existing offline collection status, scoring
status and prospective report. Reports/exit codes are retained outside `artifacts`.
All original bytes, modes, paths and mtimes must still match after validation.
Nonzero status for interrupted/partial/invalid evidence is retained as an unresolved
finding. Investigate against the source snapshot; do not edit journals, relabel late
observations or turn a nonzero result into a blanket pass.

These are distinct claims:

1. **Original-record integrity:** exact file/semantic checksums, identities, timings,
   source windows, outcome/protocol structure, and retained journal links.
2. **Linux structural/offline validation:** those existing validators can run without
   fitting, DB access or provider calls. They do not establish historical ML replay.
3. **Original Mac full replay:** retain the original OS/Python/packages, code for
   each recorded fingerprint epoch and pinned training input. In a separately
   extracted copy on the Mac, run `.venv/bin/badger verify-forward --record <copy>`
   from that matching checkout and retain per-file exit codes. Do not point a copied
   checkout at original live artifacts. Unreconstructable epochs remain unresolved.
4. **Linux reproduction diagnostics:** execute unchanged pinned-data fits on the
   isolated copy under resource limits and retain recipes, timing and strict replay
   failures. Mac platform/Python fingerprints normally differ: a strict failure is
   not automatically original-record corruption. Never alter fingerprints/tolerances
   or write a replacement forecast to make replay pass.
5. **Future Linux prospective records:** after separately approved D2B, they form a
   new runtime epoch and use actual issuance times. No D2A diagnostic is genuine
   forward evidence or simulated trading performance.

An offline actual-input fit diagnostic, from the isolated checkout, is:

```bash
test ! -e ../linux-fit-diagnostics.json
.venv/bin/python -B - <<'PY'
import json, platform, time
from pathlib import Path
from backtest_badger.forward import fit_forward
results = {'kind': 'D2A_DIAGNOSTIC_ONLY', 'platform': platform.platform(), 'fits': {}}
for symbol in ('BTCUSDT', 'ETHUSDT'):
    start = time.monotonic()
    _, _, recipe = fit_forward(symbol)
    results['fits'][symbol] = {'recipe': recipe, 'seconds': time.monotonic() - start}
with Path('../linux-fit-diagnostics.json').open('x') as out:
    json.dump(results, out, indent=2)
PY
```

Wrap that diagnostic script in a new transient unit with D1's collection limits
(`MemoryMax=1536M`, `MemorySwapMax=512M`, `CPUQuota=150%`, `RuntimeMaxSec=620`,
`User=ubuntu`, `WorkingDirectory=<run>/work`, `ProtectSystem=strict`,
`ReadWritePaths=<run>`, `ProtectHome=read-only`, `PrivateTmp=true`). Run strict
`verify_forward` on original copied records separately and record failures unchanged;
comparison of recipes does not relax the verifier. Never call `record-forward`,
`forward-cycle` or scoring `cycle` to measure latency.

Prepare operational acceptance evidence, still only on rehearsal resources:

- `date -u`, `timedatectl status`, `timedatectl show -p NTPSynchronized`, and the
  installed NTP daemon's offset/last-sync evidence. UTC display alone is insufficient.
- `.venv/bin/python --version`, `uv pip freeze --python .venv/bin/python`, source
  inventory, fit recipes, training/protocol pins and D1 deployment metadata.
- Existing `badger db-health` via the copied CLI and `worker.env`, with exact host,
  port and DB reviewed. Use `uv run --no-sync --offline --env-file ../worker.env
  python -B -c 'from backtest_badger.cli import main; raise SystemExit(main())'
  db-health`. No admin test fixture is involved.
- Existing `coverage-report --symbol BTCUSDT ETHUSDT --interval 4h
  --start-month 2017-08 --end-month 2026-09` through the same copied CLI/worker env.
  Exit 1 for known incomplete history must remain disclosed. The snapshot already
  retains full ranges and revision distributions for all retained rows.
- Bounded public GETs to `https://data-api.binance.vision/api/v3/time` and
  `/api/v3/klines?symbol=BTCUSDT&interval=4h&limit=2&timeZone=0` (repeat for ETH).
  For example, `curl --fail --connect-timeout 5 --max-time 15 -D <new-header-file>
  -o <new-body-file> '<url>'`, with shell noclobber/new paths. Keep status/headers,
  UTC and duration outside artifacts. Do not ingest or publish anything. A curl
  success tests reachability, not the application's full validation/refresh budget.
- Repeat the existing synthetic benchmark at least three times under D1 caps,
  including cold starts and concurrent read-only copied-evidence scoring status
  (0.5 CPU/512 MiB) plus DB coverage/hash queries. Record wall time, memory peak,
  swap, I/O, cgroup throttling and provider/DB latency. Synthetic timings already
  supplied are context only. Genuine scoring/collection concurrency remains a
  separate synthetic-workload performance gate; read-only status is not a full
  substitute for outcome publication/refit/refresh workload.
- Inspect `free -h`, `vmstat`, `docker stats --no-stream` for the rehearsal container,
  and Lightsail console CPU utilisation/burst-capacity graphs over sustained load.
  Record the CPU credit reserve, disk/WAL/archive growth, and concurrent peak RSS.
  Require the D1 300-second compute budget plus realistic provider/DB reserves
  inside the 900-second issuance window. If 4 GB is insufficient, postpone/resize
  through separate approval; never tune the scientific recipe or omit validation.

## G. Report readiness and D2B risks — Lightsail

```bash
cd "$run_dir/work"
.venv/bin/python -B ops/lightsail/rehearsal.py report \
  --id "$rehearsal_id" --expect-host "$server_host" --bundle-sha256 "$bundle_sha256"
```

The exclusive `rehearsal-report.json` distinguishes `NOT_RUN` from attempted-but-`INCOMPLETE` checks, carries
online-change findings, and always states **D2B readiness false**. Attach operator
clock/provider/resource/role/backup results in separately named reports; an exported
summary is not approval. Preserve checksums for all those diagnostic files too.
Retain all data/logs for investigation; no cleanup or production promotion is implied.

Before D2B require explicit authorisation, a clean reviewed release, successful
actual-server rehearsal, trustworthy image, independent encrypted copies with
read-back/restore proof, resolved Mac/Linux replay scope and runtime epochs,
concurrent performance/CPU/disk/clock/provider gates, worker permission validation,
and an exactly-one-collector ownership/rollback plan. Then follow the original D2
runbook's **fully quiescent final checkpoint**, fresh empty final restore and
separately approved activation. The online rehearsal DB must not become production
by simply enabling its workers. Stop at D2A until these gates and authorisation exist.

## Local verification

Tests operate on synthetic files and an explicitly disposable local PG17 container.
They exercise unsafe hosts/paths/targets, pre-existing volumes, partial/corrupt
transfers, archive traversal/links, exact timestamps/bytes, read-only enforcement,
concurrent source updates, sequence drift, real custom dump/restore and immutable
revision triggers. No tests point at the original or copied research database.
Remote systemd/NTP/provider/performance gates are intentionally not claimed here.
Implementation validation results are recorded below.

The snapshot mechanism follows PostgreSQL's [exported snapshot documentation](https://www.postgresql.org/docs/17/functions-admin.html)
and [pg_dump snapshot option](https://www.postgresql.org/docs/17/app-pgdump.html).

### Executed implementation checks

- Full suite: **929 passed, zero skipped** against a new local PG17 container on
  `127.0.0.1:55439`, tmpfs storage, exclusively generated test databases. After the
  final archive `.`-path refusal and incomplete-report safeguards, the focused
  suite passed **49 tests**.
  The two real D2A integration cases cover read-only enforcement and shared-snapshot
  dump/restore under concurrent writes, exact decimals, revision triggers and sequences.
- Ruff lint passed; Ruff formatting passed for all **110 Python files**.
- Both Compose templates validated with synthetic credentials; no service started
  by template validation. Python parsing, Bash syntax for the existing two shell
  scripts and all **13** checklist Bash blocks, `git diff --check`, and byte-exact
  prompt archive comparison passed.
- ShellCheck was unavailable locally; no ShellCheck pass is claimed. Native systemd
  validation and all real Lightsail checks remain unexecuted.
- No scientific modules, migrations, dependency files, frozen protocol or launchd
  templates changed. No real research database/evidence was used by tests. No SSH,
  artifact upload, scheduler change, production initialisation, commit or push occurred.

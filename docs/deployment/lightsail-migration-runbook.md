# Stage D2 — Migration and cutover runbook (not executed in D1)

This is a plan for a separately authorised migration. D1 does **not** authorise
pausing the two Mac LaunchAgents, moving live evidence, restoring a real database,
starting server workers, or altering scientific results. The Mac remains the sole
active collection/scoring host until the explicit D2 cutover gate is satisfied.
Use the [foundation guide](lightsail-foundation.md) for paths, templates, private
configuration and worker constraints.

## 1. Establish scope, inventories and acceptance gates

Record the operator, approved maintenance window, source Mac, target `Ubuntu-1`,
source/destination commit(s), UTC time, Docker/PostgreSQL versions, Python exact
versions, dependency checksums, platform/architecture, disk/memory and active
scheduler state. The user reports both `com.backtestbadger.forward-collection` and
`com.backtestbadger.forward-scoring` are installed and working on the Mac; verify
both using read-only `launchctl print gui/UID/LABEL`. Do not use historical stage
docs' installation status as current state.

Choose a window after a successfully verified native collection horizon, allowing
time before the next close + 60 seconds. Record last issued identities and outcomes
for each market and the first eligible server horizon. If the work runs long,
accept and document missing opportunities. Never backdate a forecast or replay
missed timer timestamps. Manual `record-forward` is not a catch-up mechanism.

Before any switch require all of these:

- A clean pinned release, matching dependency lock and protocol, successful full
  tests, Compose/systemd validation and restricted private configuration.
- Healthy reviewed PostgreSQL 17 amd64 image with a recorded immutable digest;
  adequate disk space for a full backup, restore rehearsal and rollback copy.
- Verified original artifact inventory, coherent database backup, two independently
  retained encrypted copies and a successful restore rehearsal.
- A resolved architecture/runtime replay plan, read-only evidence validation and
  full-size performance results under actual server limits and concurrent load.
- Actual clock synchronisation, provider reachability in an authorised **test**
  environment, DB health, permissions, correct training pins, and no active server
  timer/service or `workers-approved` file during staging.
- An explicit decision that the Mac collector will be stopped before any server
  collection, plus a recovery owner and a defined observation window after cutover.

No D1 script performs these live actions. If any gate fails, leave Mac scheduling
in place and investigate using isolated copies. Rehearsal output is never promoted
to the genuine forward directories.

## 2. Preserve all state, not just current candles

Inventory the complete source `artifacts/` tree, including:

| Evidence | Required retained contents |
| --- | --- |
| Database | All application schemas/tables, `market` identities, exact `candle` values and watermarks, every `candle_revision`, constraints/triggers, sequences, `alembic_version`, role/privilege inventory |
| Frozen inputs | Stage 1 exports and manifests; `research/stage-2a-v1` exact CSV and manifest; all reproduction/verification evidence |
| Forward predictions | Every original filename and byte, issue/capture times, source windows, fingerprints, `.partial` and lock files |
| Forward outcomes | Every original immutable outcome and captured target/version; never regenerate to match a new host |
| Operations | Both `forward-operations` and `forward-scoring-operations`, completed/interrupted journals, cursor, provider pause state and console logs |
| Acquisition | `raw`, `manifests`, `rest/raw`, `rest/manifests`, revalidation plans/responses and anomaly/gap investigations |
| Other research | Experiments, execution archives/sidecars, backtests, economics and historical audit evidence |
| Reproduction environment | Matching code revisions and any original uncommitted patches, protocol, pyproject/lockfiles, package inventory, exact Python/platform info and deployment records |

Copy the whole artifacts tree rather than guessing which referenced files may be
needed. Preserve incomplete/error evidence too. Relative paths embedded in evidence
must remain relative to the same layout; absolute old Mac paths are historical
provenance, not instructions to rewrite the records. Never transfer `.env`, SSH
keys, real trading credentials or the Mac `.venv` as a Linux runtime. Back up necessary
secrets separately using an approved encrypted secret store.

## 3. Rehearse backup and restore before the final pause

A rehearsal can use an earlier coherent approved backup. A live `pg_dump` gives a
consistent database snapshot, but copying journals/artifacts while writers run does
not produce a coherent combined checkpoint. Treat such a live rehearsal as partial,
and repeat the final backup after stopping **all** writers in section 6.

During an authorised quiescent window on the Mac, from the source repository:

```bash
set -euo pipefail
umask 077
backup_dir=/absolute/approved/private/destination/badger-UTC_TIMESTAMP
mkdir "$backup_dir"
# Use the existing Backtest Badger Compose project, never the legacy project.
docker compose exec -T postgres sh -ec \
  'pg_dump --format=custom -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > "$backup_dir/database.dump"
docker compose exec -T postgres sh -ec \
  'pg_dumpall --globals-only --no-role-passwords -U "$POSTGRES_USER"' \
  > "$backup_dir/roles-without-passwords.sql"
find artifacts -type f -exec shasum -a 256 {} + > "$backup_dir/artifacts.sha256"
tar --format=pax -cpf "$backup_dir/artifacts.tar" artifacts
git rev-parse HEAD > "$backup_dir/source-commit.txt"
git diff --binary HEAD > "$backup_dir/source-working-tree.patch"
git status --porcelain > "$backup_dir/source-status.txt"
cp uv.lock pyproject.toml "$backup_dir/"
.venv/bin/python -c 'import platform; print(platform.python_version()); print(platform.platform()); print(platform.machine())' \
  > "$backup_dir/runtime.txt"
uv pip freeze --python .venv/bin/python > "$backup_dir/packages.txt"
(cd "$backup_dir" && shasum -a 256 database.dump roles-without-passwords.sql \
  artifacts.tar artifacts.sha256 source-commit.txt source-working-tree.patch \
  source-status.txt runtime.txt packages.txt uv.lock pyproject.toml > bundle.sha256)
```

Archive the recorded Git revision as a Git bundle or source archive as well, and
hash it into the backup inventory. `git diff` omits untracked files: inspect
`source-status.txt` and separately archive any needed untracked source before
calling the backup complete. Check `pg_restore --list database.dump` with a PG17
client and compare source table row counts, market identities, min/max UTC coverage,
version distributions, exact ordered logical-row hashes and sequence states against
a private audit record. Include schema/trigger definitions and all provenance fields,
not floating-point summaries. Use existing read-only `coverage` reports where
appropriate; incomplete history must remain explicitly incomplete.

Store the backup with restrictive permissions on an approved encrypted destination,
then create an independently retained off-machine copy. Use SSH/SCP or `rsync -a`
into a **new** private staging directory on the server; verify the known SSH host
key and do not change host keys/firewalls. Do not use `--delete` and do not copy
into active artifacts. Verify `bundle.sha256` with `sha256sum -c` after transfer.
Extract into another **empty** staging directory, then verify every file using
`artifacts.sha256`. Compare path lists/counts as well as hashes to detect missing or
extra files. Check original permissions and timestamps; ownership IDs must be mapped
explicitly from Mac to ubuntu, not blindly trusted.

## 4. Runtime and scientific compatibility gate

macOS arm64/Python 3.12.13 (the D1 local test environment) and Linux x86_64/Python
3.12.15 are different runtimes. `uv.lock` pins versions/wheel hashes but does not
promise identical arithmetic across CPU, BLAS, OS or Python builds. Never copy the
Mac virtualenv or serialize fitted models as a shortcut; the application refits its
fixed recipe from pinned pre-2024 training data.

`forward.fit_forward()` fingerprints `platform.platform()`, exact Python/package
versions, model parameters, training-row hashes, dependency files and twelve source
modules. `verify_forward()` requires exact recipe/provenance agreement in addition
to numerical tolerances (`rtol=1e-10`, `atol=1e-12`). An original Mac record will
normally **fail Linux full replay provenance**, even if numeric predictions agree.
This is a known gate, not evidence that the original prediction was corrupt.
Changing those validators, fingerprints, recipes or original records is outside D1
and must not be done silently during migration.

Preserve access to the original Mac OS/Python/library/source environment and trusted
training bytes for original-record replay. A source checkout alone is insufficient:
OS updates can change the platform fingerprint too. Archive environment details,
original dependencies/installers where available, and matching source for each
fingerprint epoch. Record which historical records can actually be replayed in the
retained environment, and clearly label those without a reconstructable runtime.
Do not claim universal reproducibility from checksums alone.

The collector's existing-record branch uses integrity/identity checks without a
refit. Stage 3C scoring preserves original runtime fingerprints and validates them
structurally rather than requiring the current platform; Stage 3D status can thus
validate migrated records/outcomes offline. Run both offline status commands and the
existing evaluation report on the staged copy, using a **separate rehearsal source
checkout** with its own `artifacts` link. Do not temporarily repoint the production
link or change source constants. Confirm the copied frozen protocol hash. Original
outcomes should validate without DB access; compare their complete-file checksums
before/after every rehearsal.

Separately reproduce full pinned-data fits on Linux in an authorised read-only
rehearsal, measure differences without tuning or replacing originals, and retain the
results as migration diagnostics. New Linux observations will carry the new runtime
fingerprint and form an explicit runtime epoch. Require unchanged scientific module
hashes/lockfile for D1. Any proposed scientific code change or relaxation of replay
requires separate review and must not be bundled into cutover.

Run the synthetic full-size benchmark at least three times under the foundation
resource limits, including cold caches and representative independent scoring/DB
load. Check total latency, memory, swap, disk I/O and Lightsail CPU credits. Measure
bounded data-refresh/DB latency only in an explicitly authorised isolated test DB
and evidence tree. Do not invoke the real collector to obtain a timing sample. If
under-budget performance cannot be demonstrated, postpone cutover or resize through
separate authorisation; do not shrink the training sample or omit verification.

## 5. Prepare and restore the target database (D2 only)

First fill private `postgres.env` and `worker.env`, choose the reviewed PG17 amd64
digest, explicitly pull it, and verify the resulting image version/architecture.
With environment values kept private, a privileged operator can use:

```bash
cd /opt/backtest-badger/current
# The reviewed image reference is not a secret; replace the full digest explicitly.
sudo docker pull postgres:17@sha256:REVIEWED_DIGEST
sudo docker image inspect postgres:17@sha256:REVIEWED_DIGEST \
  --format '{{.Architecture}} {{.Os}} {{json .RepoDigests}}'
sudo docker compose --env-file /etc/backtest-badger/postgres.env \
  -f ops/lightsail/compose.yaml config --quiet
sudo .venv/bin/python ops/lightsail/validate.py configuration
# Refuse an existing volume; investigate it rather than adopting/deleting it.
if sudo docker volume inspect backtest-badger-pg17 >/dev/null 2>&1; then
  echo 'Volume already exists: stop and inspect before proceeding.' >&2
  exit 1
fi
sudo docker volume create backtest-badger-pg17
sudo docker compose --env-file /etc/backtest-badger/postgres.env \
  -f ops/lightsail/compose.yaml up -d --wait
```

These commands initialise an empty database and are **prohibited in D1**. For a
rehearsal use another explicitly named test volume/project and loopback port; never
point an integration-test admin DSN at the restored research database. Confirm the
new intended DB has no application tables and no live clients before restoring:

```sh
sudo docker compose --env-file /etc/backtest-badger/postgres.env \
  -f ops/lightsail/compose.yaml exec -T postgres sh -ec \
  'pg_restore --exit-on-error --single-transaction --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < /absolute/private/staging/database.dump
```

Do not use `--clean`, automatic DB replacement or `alembic upgrade` before restoring
a dump that already contains the schema. `--no-owner --no-acl` intentionally maps
ownership to the new admin; preserve the source role inventory and review grants
explicitly. Do not execute source cluster globals wholesale on the new server.
Inspect Alembic and SQL state with privileged one-off commands, e.g.:

```sh
sudo systemd-run --wait --pipe --collect --unit=badger-migration-inspection \
  -p User=ubuntu -p Group=ubuntu -p WorkingDirectory=/opt/backtest-badger/current \
  -p EnvironmentFile=/etc/backtest-badger/postgres.env \
  /opt/backtest-badger/current/.venv/bin/alembic current
```

This env file omits host/port, so the existing config defaults to `127.0.0.1:5432`.
Confirm that is the intended target. Compare `alembic heads` (currently `0001`) with
the restored revision. A separately reviewed needed upgrade uses the same command
with `upgrade head`; never use `downgrade` as a rollback tactic.

In an interactive admin psql session create the runtime role **only if absent**;
if it exists, inspect it first. Set its password using `\password badger_worker`
interactively to the value privately saved in `worker.env`, without a plaintext
password SQL literal or shell argument. Apply:

```sql
CREATE ROLE badger_worker LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE backtest_badger TO badger_worker;
GRANT USAGE ON SCHEMA public TO badger_worker;
GRANT SELECT ON market, candle, candle_revision TO badger_worker;
GRANT INSERT, UPDATE ON candle TO badger_worker;
GRANT INSERT ON candle_revision TO badger_worker;
```

Review defaults/PUBLIC privileges and confirm the worker is not a table/schema
owner and cannot delete, truncate, disable triggers or create roles/tables. These
grants cover the unchanged application writes; migration/market administration
stays with the admin. Compare all source/restore data, revision history, exact
ordered logical hashes, sequences, constraints, triggers and Alembic state before
allowing new market ingestion. Confirm loopback binding with `ss -ltn` and Compose
health without exposing passwords. Rehearse connection failure and permission
failure against disposable copies; verify next-tick recovery and no restart loop.

## 6. Final coherent checkpoint and exactly-one-collector cutover

Do this only after rehearsal passes and the user explicitly authorises the D2
cutover. Preserve the original installed Mac plist files and their hashes. First
stop both Mac jobs and prevent their automatic reload during the cutover window:

```sh
launchctl bootout "gui/$(id -u)/com.backtestbadger.forward-collection"
launchctl bootout "gui/$(id -u)/com.backtestbadger.forward-scoring"
launchctl disable "gui/$(id -u)/com.backtestbadger.forward-collection"
launchctl disable "gui/$(id -u)/com.backtestbadger.forward-scoring"
```

Inspect launchd/process state and ensure there are no manual collectors, scorers,
refreshes, ingestion or revalidation writers on either host. Bootout can terminate
an in-flight process: retain its journal/partial evidence and inspect the last
published identities. Confirm the stable-inode locks are no longer held without
unlinking them. Record the cessation time and a single-owner handoff decision.

Repeat the complete database/artifact backup from section 3 after this pause. Transfer
and verify the **final** checkpoint. A previously running rehearsal DB is not the
final DB: use a separately approved fresh empty volume/database for the final
restore or explicitly prove it already contains exactly the final checkpoint. Never
restore over a nonempty rehearsal database. Preserve all earlier backups/volumes.
Move the verified final artifacts tree into the persistent location only while
workers are stopped, after proving the D1 placeholder directories are empty. Move
those placeholders aside into a dated private directory; do not merge over any
unknown evidence. Map ownership to ubuntu, keep private directories 0700, retain
original file bytes/timestamps and immutable file modes. Do not recursively make
read-only scientific files writable. Re-run the complete file inventory comparison.

Verify that the active release's artifact symlink has the intended target. Record
a pre-start status snapshot on both staged/original evidence sets. Perform runtime
preflights using a one-off systemd invocation that loads `worker.env` (both worker
choices), then `badger db-health` the same way; these commands must not invoke a
cycle. Confirm the worker role can execute intended writes only on a disposable
rehearsal database. Verify live frozen training hashes and protocol hash against
their pins and original backup. Preserve backups before the first fresh ingestion.

Only after all gates pass, while the Mac remains stopped:

```sh
# D2 final activation; this file must not exist during D1.
sudo install -o root -g root -m 0600 /dev/null /etc/backtest-badger/workers-approved
sudo systemctl daemon-reload
sudo systemctl enable --now backtest-badger-collection.timer
sudo systemctl enable --now backtest-badger-scoring.timer
systemctl list-timers --all 'backtest-badger-*'
```

Do not also start either service manually. Each waits for its own next UTC tick;
the first publication must use actual current UTC time. Observe at least one full
4h horizon and its target maturity: both markets, successful post-publication replay,
normal pending/then-scored progression, independent timers, disk/memory limits and
unchanged hashes for all migrated originals. New source/forecast/outcome/journal
files may append. Keep the Mac LaunchAgents disabled and retain their installation
and environment for original-record replay. Document missed opportunities explicitly.
Do not publish migration diagnostics as performance evidence or trading results.

## 7. Server backups and restore drills

After cutover, select an approved backup cadence and encrypted off-machine target;
no backup service is installed by D1. Every coherent checkpoint covers database,
complete persistent artifacts, release metadata, source/protocol/lockfiles and a
separate protected secrets backup. Pause both timers **and services** (and manual
writers), record interruption evidence, dump the DB, hash and archive files, then
restart the timers. A DB-only snapshot or Lightsail snapshot is insufficient proof
of artifact/DB coherence. Docker volume persistence is not a backup.

Use the section 3 pattern adapted to the production Compose file/private env and
`/var/lib/backtest-badger`. Server `pg_dump` runs inside the pinned PG17 container;
write the output with umask 077 into a new staging directory. Verify dump listing,
archive and file hashes before transfer, after transfer and after restore. Keep
multiple dated versions without propagating deletion into the only backup. Include
the service journal export for incident diagnosis, but artifact journals remain
necessary. Alerting/automatic retention needs a later explicitly scoped implementation.

Perform periodic restore drills into an isolated empty volume/database and directory,
with the approval gate absent and timers disabled. Check complete DB logical hashes,
revision protection, all artifact checksums, offline statuses and preserved runtime
replay limits. Prove recovery without accessing the live database or replacing
originals. A backup is not accepted until its restore was exercised.

## 8. Failure recovery and rollback

Before server activation: keep/re-enable Mac ownership after confirming there is no
server worker. Failed staging can be retained for investigation; restore nothing
over the original Mac evidence. No server-issued evidence exists to reconcile.

After server activation: stop and disable **both** server timers and services,
remove the approval gate, and verify no running/manual workers remain. Snapshot the
server's DB and entire artifacts, including any new predictions/outcomes, revisions
and interrupted journals, **before** rollback. Never simply restart the stale Mac
collector: it has a separate lock and may lack already-issued identities. Identify
all publications since the handoff, verify file hashes/identity conflicts, and choose
one authoritative complete database/artifact checkpoint. Move that state to the
chosen recovery host using the same empty-destination restore procedure, preserving
all original evidence. Conflicting same-identity bytes stop cutover for investigation;
never silently choose, overwrite or delete one. Retain both incident copies.

For a source-only regression, stop both server workers, retain the old/current link
and deployment manifests, verify the older release understands existing schema and
new evidence, then atomically switch `current` via a newly created sibling symlink
and `mv -T` on Linux. Keep the exact same persistent artifact link and DB volume.
Never roll scientific evidence back with source. If the schema/runtime cannot be
safely rolled back, keep workers stopped and diagnose on copies. No forced forecast
backfill is allowed; downtime becomes missing-opportunity evidence.

If recovery returns ownership to the Mac, reconcile server-era evidence and DB
first, check original runtime compatibility, prove server collection is stopped,
then `launchctl enable` the two preserved labels and `launchctl bootstrap` their
original plists. Bootstrap runs immediately: inspect actual UTC eligibility first.
Accept a missed window rather than altering clocks or issuing a late forecast under
the automated cohort. Keep exactly one active collector throughout the handback.

The D2 completion record should include inventories/checksums, restore/role tests,
runtime limitations, real server timing/load results, last Mac/first server
identities, actual activation times, immutable original preservation results,
backup location/restore proof and rollback ownership. D1 stops before this process.

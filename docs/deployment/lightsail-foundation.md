# Stage D1 — Lightsail deployment foundation

D1 prepares files and local tests only. Nothing was installed on Lightsail, no
remote connection was made, no database was created/restored there, and neither
server timer was enabled or started. Both existing Mac LaunchAgents must continue
running. Migration, scheduler cutover and real server performance acceptance are
separate [D2 work](lightsail-migration-runbook.md). No website or trading deployment
is included.

The supplied target is `Ubuntu-1` (`3.8.218.113`, existing `ssh Ubuntu-1` alias),
Ubuntu 24.04.5 x86_64, 2 vCPU, about 4 GiB RAM and 80 GB disk, Docker 29.9.1,
Compose 5.6.0, uv-managed Python 3.12.15. These are operator-supplied facts, not
remote observations. Do not change firewall rules, SSH keys or the legacy project.

## Layout and evidence boundaries

| Path | Owner / mode | Purpose |
| --- | --- | --- |
| `/opt/backtest-badger/releases/<full-commit>` | ubuntu, private parent 0700 | Clean detached source, per-release `.venv`, `deployment.json`; never update in place |
| `/opt/backtest-badger/current` | ubuntu | Link to one reviewed release; change only with workers stopped in D2 |
| Each release's `artifacts` | symlink | Always `/var/lib/backtest-badger/artifacts` |
| `/var/lib/backtest-badger` and `artifacts` | ubuntu:ubuntu 0700 | Persistent evidence, independent of checkout replacement |
| `/etc/backtest-badger` | root:ubuntu 0750 | Private configuration |
| `worker.env` | root:ubuntu 0640 | Loopback connection using the nonsuperuser `badger_worker` role |
| `postgres.env` | root:root 0600 | Bootstrap/admin DB password and reviewed image digest; only privileged Compose operations |
| `workers-approved` | root:root 0600, **absent in D1** | Deliberate D2 release gate for both services and timers |
| Docker volume `backtest-badger-pg17` | Docker managed | Whole PostgreSQL 17 cluster, external to Compose lifecycle; **not created in D1** |

Both workers have `WorkingDirectory=/opt/backtest-badger/current`. Therefore
`artifacts/research/stage-2a-v1`, all four forward evidence/operation directories,
`artifacts/rest`, `uv.lock`, `pyproject.toml` and the pinned Stage 3C protocol resolve
as before. The app still fingerprints the original source files. No scientific
module, frozen recipe, protocol, migration or dependency file needs modification.
A source-only rollback changes the release link, never the evidence link/volume.
An old release may not understand newer evidence/schema: confirm compatibility
first, preserve incident evidence, and never downgrade the live schema to roll back.

The host executes Python as `ubuntu`; PostgreSQL alone runs in Docker. systemd
makes source, frozen training and historic artifacts read-only within each worker's
mount namespace. The collector can write only predictions, collector operations
and REST evidence. The scorer can write only outcomes and scoring operations;
predictions and collector journals are read-only there. App publication remains
exclusive and immutable. An ubuntu administrator or root can still alter files;
these controls do not provide independent attestation against the owner.

## Initial installation commands — operator only, not executed by Codex

Use a reviewed commit **containing D1** after separately authorised commit/push or
an equivalent verified Git bundle. D1 itself neither commits nor pushes. The
pre-D1 SHA is not a substitute. On the server, as `ubuntu`, run the following in
Bash. Replace only `REVIEWED_FULL_40_CHARACTER_COMMIT`. The example deliberately
refuses an existing installation; upgrades use a new release and the D2 procedure.
No command in this section starts PostgreSQL or any worker.

```bash
ssh Ubuntu-1
set -euo pipefail
umask 077
revision=REVIEWED_FULL_40_CHARACTER_COMMIT
[[ $revision =~ ^[0-9a-f]{40}$ ]]
command -v git
command -v uv
command -v docker
command -v systemd-analyze
uv --version
docker --version
docker compose version
uv python find --no-python-downloads 3.12.15
uname -m
# Inspect clock synchronisation before any later live work.
timedatectl status

test ! -e /opt/backtest-badger
sudo install -d -o ubuntu -g ubuntu -m 0700 \
  /opt/backtest-badger /opt/backtest-badger/releases \
  /var/lib/backtest-badger /var/lib/backtest-badger/artifacts
sudo install -d -o root -g ubuntu -m 0750 /etc/backtest-badger
for directory in forward-predictions forward-outcomes forward-operations \
  forward-scoring-operations rest; do
  install -d -m 0700 "/var/lib/backtest-badger/artifacts/$directory"
done

git clone --no-checkout https://github.com/owencrew/backtest-badger.git \
  "/opt/backtest-badger/releases/$revision"
cd "/opt/backtest-badger/releases/$revision"
git checkout --detach "$revision"
bash ops/lightsail/prepare-release.sh "$revision"
ln -s "releases/$revision" /opt/backtest-badger/current

sudo install -o root -g root -m 0600 ops/lightsail/postgres.env.example \
  /etc/backtest-badger/postgres.env
sudo install -o root -g ubuntu -m 0640 ops/lightsail/worker.env.example \
  /etc/backtest-badger/worker.env
sudo install -o root -g root -m 0644 ops/lightsail/systemd/* \
  /etc/systemd/system/
# Confirm the D2 gate is absent. No enable/start/daemon-reload is needed in D1.
sudo test ! -e /etc/backtest-badger/workers-approved
.venv/bin/python ops/lightsail/validate.py templates --native-systemd
bash -n ops/lightsail/prepare-release.sh ops/lightsail/status.sh
bash ops/lightsail/status.sh
.venv/bin/python -B ops/lightsail/benchmark.py
```

Template credentials remain unusable until privately configured in D2. Use
`sudoedit` (without shell tracing) and a password manager or `openssl rand -hex 32`
in a private terminal to generate **separate** admin and worker passwords. Do not
paste passwords into shell arguments, Git, tickets, journals or command transcripts.
Use literal 64-character hexadecimal passwords to avoid systemd/Compose env-parser
ambiguity. The validator rejects placeholders and nonliteral values. Never `source`
these files. Never print resolved production `docker compose config`; use `config
--quiet`. Docker administrators can inspect container environment and volume data,
so membership in the Docker group remains a privileged trust boundary.

`prepare-release.sh` refuses dirty source, a short SHA, an incorrect directory or
an existing environment/evidence link. It requires installed Python **3.12.15**,
uses `uv sync --locked --no-dev --no-install-project --no-build
--no-python-downloads`, and checks the lock/dependency files remain byte-identical.
Locked wheels must exist for the platform; missing wheels/interpreter stop setup.
It adds a conventional source `.pth` and a tiny `badger` console entry point calling
the existing `cli.main`; this avoids resolving Hatchling build requirements outside
`uv.lock`. No package manager runs inside a worker. `deployment.json` records the
commit, Python, platform, architecture, uv version, deployment/environment version,
UTC preparation time, package versions, source/protocol and dependency checksums.
The record is operational metadata, not a scientific result. Retain it in backups.

Python installed by uv may live under `/home/ubuntu/.local/share/uv/python`; the
units use `ProtectHome=read-only` so the interpreter remains readable. Do not delete
that interpreter while any retained release depends on it. No automatic runtime
upgrade is configured. Recreate an environment in a new release for a reviewed
upgrade; never run unattended `uv sync` or `git pull` in the active release.

## PostgreSQL 17 preparation

`ops/lightsail/compose.yaml` is independent of the development Compose project and
of the deleted legacy server. It uses one named **external** volume, binds only
`127.0.0.1:5432`, checks `pg_isready`, restarts `unless-stopped`, bounds Docker logs,
and caps PostgreSQL at 1 GiB / one CPU with no container swap. Shared buffers are
256 MiB, work memory 4 MiB, maintenance memory 64 MiB and max connections 30.
Work memory is per operation; the container cap is the final bound.

Set `POSTGRES_IMAGE=postgres:17@sha256:<reviewed-digest>` in private `postgres.env`.
Choose and explicitly pull a verified linux/amd64 PostgreSQL 17 image during D2,
record the registry digest and image version, and inspect its architecture. No
invented digest is supplied and `pull_policy: never` prevents automatic replacement.
The same major version is used by development. Pinning does require deliberate
security patch review and tested upgrades; it does not make upgrades unnecessary.

D1 creates neither the external volume nor the database. In D2, an authorised
operator creates the volume, starts Compose, and restores into an explicitly empty
database. Never run `down -v`, `docker volume rm`, `alembic downgrade`, or restore
with `--clean` against live evidence. Changing initial `POSTGRES_*` values does not
change passwords/ownership in an existing cluster. A full logical dump includes
`market`, `candle`, `candle_revision`, revision-protection triggers/constraints,
sequences and `alembic_version`; transfer the whole application DB, not just candle
values. Forward evidence is on disk and requires a separate coherent backup.

The existing Alembic migration is `0001`. For a genuinely fresh disposable database
use existing `alembic upgrade head`; for the D2 restored DB inspect `alembic current`
and `alembic heads` first, and apply only a reviewed necessary upgrade. The
bootstrap/admin connection owns migrations; the worker must not own tables or have
superuser, CREATEDB or CREATEROLE privileges. D2 grants SELECT on the three market
tables, INSERT/UPDATE on `candle`, and INSERT on `candle_revision`. There are no
worker DELETE/TRUNCATE/DDL grants. The scorer's existing queries also use read-only
transactions. No public database or submission API is added.

## Scheduling and failure behaviour

| Worker | ExecStart | UTC timer | Hard service bound |
| --- | --- | --- | --- |
| Collection | `.venv/bin/badger forward-cycle` | Every hour at :01, :06, :11, …, :56 | 900 seconds plus 15-second stop grace |
| Scoring | `.venv/bin/python -m backtest_badger.forward_scoring_operations cycle` | Every hour at :02, :07, :12, …, :57 | 270 seconds plus 15-second stop grace; app processing bound 240 seconds |

At native 00/04/08/12/16/20 UTC boundaries, collection first becomes eligible at
close + 60 seconds. Its issuance window stays `[close + 60s, close + 16min)`;
:01, :06 and :11 are useful attempts, while :16 is already too late. Accuracy is
1 second with no random delay, but neither scheduler nor OS guarantees punctuality.
App UTC checks remain authoritative; a 900-second process timeout does not extend
the issuance deadline. A late wake checks only the actual current horizon. Both
timers use `Persistent=false` and do not replay missed timer events.

The scorer is offset for normal load distribution, **not ordered after collection**.
If a target has not arrived, it remains pending and retries on its own timer. Each
service depends on Docker startup, network-online and time-sync ordering; its
preflight checks configuration, source/runtime hashes, directories and then performs
the bounded existing `db-health`. It does not start a database. Docker's existing
restart policy brings up an authorised D2 database after reboot; if it is not ready,
the worker fails visibly and retries on the next tick. Verify actual NTP lock in D2:
`time-sync.target` ordering alone is not proof of clock correctness.

systemd avoids simultaneous executions of one oneshot service; the app's distinct
stable-inode `flock` locks and exclusive publications remain the final protections.
Never unlink locks while either job might run. `Restart=no` avoids immediate loops;
there is no `RemainAfterExit`. Exit 1 and 2 remain failures visible in systemd (no
blanket success-code masking). A killed/OOM process releases its lock, can leave a
partial or `running` journal, and retries at the next tick. Already-published
forecasts/outcomes win; they are never deleted to force a retry. Preserve interrupted
journals and inspect status before recovery. Single-host locks do not coordinate
Mac and Lightsail: exactly one collector is a D2 operational requirement.

Read-only inspection after authorised installation:

```sh
bash /opt/backtest-badger/current/ops/lightsail/status.sh
systemctl status backtest-badger-collection.timer backtest-badger-scoring.timer
systemctl list-timers --all 'backtest-badger-*'
sudo journalctl -u backtest-badger-collection.service -n 80 --no-pager
sudo journalctl -u backtest-badger-scoring.service -n 80 --no-pager
```

An inactive/missing timer is expected in D1; status exit codes reflect that. Offline
application status reads artifacts/protocol only and does not load secrets, connect,
fit, refresh, issue or score. It reports incomplete/invalid evidence without repairing
it. systemd writes console output to the host journal; JSON operational journals
remain the durable application history. No `/var/log/backtest-badger` is necessary.
Set and review the host journal's retention policy separately; do not rotate away
scientific or operational artifact JSON. Monitor disk space, memory, swap and failed
units manually until a separately scoped monitor exists.

## Memory, optional swap and performance gate

The configured ceilings total 3 GiB (PostgreSQL 1 GiB, collector 1.5 GiB, scorer
0.5 GiB), leaving roughly 1 GiB for Linux, Docker and caches. The collector is capped
at 1.5 CPUs, scorer at 0.5; DB can also contend for CPU. These are ceilings, not
reserved resources. Small Lightsail CPU burst budgets, cache state, slow disk,
provider backoff and simultaneous scoring affect latency. The 80 GB disk must hold
DB, raw source evidence, research, journals, releases and backups; do not prune
immutable evidence automatically. Keep encrypted off-machine backups.

Optional **operator-only** 2 GiB swap for an ext4 root filesystem follows. Skip this
if swap already exists; inspect and plan explicitly rather than replacing it. It
refuses existing paths/fstab entries. Do not use swap as evidence that a deadline
can be met. No swap command was run by D1.

```bash
sudo bash <<'SWAP'
set -euo pipefail
umask 077
test -z "$(swapon --noheadings --show)"
test "$(stat -f -c %T /)" = ext2/ext3
test ! -e /swapfile.badger
test ! -e /etc/sysctl.d/90-backtest-badger-swap.conf
! grep -q '/swapfile.badger' /etc/fstab
# Leave at least 4 GiB free after allocating 2 GiB.
test "$(df -B1 --output=avail / | tail -1)" -gt 6442450944
dd if=/dev/zero of=/swapfile.badger bs=1M count=2048 status=progress
chmod 0600 /swapfile.badger
mkswap /swapfile.badger
swapon /swapfile.badger
printf '/swapfile.badger none swap sw 0 0\n' >> /etc/fstab
printf 'vm.swappiness=10\n' > /etc/sysctl.d/90-backtest-badger-swap.conf
sysctl -p /etc/sysctl.d/90-backtest-badger-swap.conf
swapon --show
SWAP
```

If interrupted, inspect the existing file, active swap and fstab before any retry;
never automatically truncate a possibly active swapfile. To remove later, ensure
sufficient available RAM, use `swapoff /swapfile.badger`, then explicitly remove only
its fstab entry, sysctl file and inactive swapfile. Preserve other host settings.

`benchmark.py` generates a fresh synthetic Stage 2A-shaped dataset with **all 39,609
rows**, including **13,782 BTC and 13,783 ETH training rows**. Both held-out partitions
contain numeric sentinels that must never be parsed. It runs the unchanged recorder
and complete offline replay verifier for each market sequentially (four full fits),
with fixed model parameters and full input hash/schema/count/timing checks. Only
synthetic test input pins, a synthetic source window and clock are injected, as in
the existing test APIs. Synthetic records live in an automatically removed temporary
directory; neither PostgreSQL nor provider access is used, and socket access is
blocked. It never opens the real training artifacts or publishes live records.

A parent watchdog kills the child at 600 seconds; success requires total setup,
recording and verification under **300 seconds**. This leaves a provisional 300
seconds for worst-phase timer arrival and 300 for provider/DB latency and reserve
within the 900-second window. That allocation is an acceptance budget, not a bound
on provider behaviour. Fail closed if the server cannot satisfy it. Do not reduce
training data, model complexity, input validation or the replay verification.

Before D2 cutover, repeat at least three times on the actual server under the unit's
resource caps and simultaneous representative scoring/DB load in an authorised
isolated test environment. A later operator can apply the collection caps without
running the collector:

```sh
sudo systemd-run --wait --pipe --collect --unit=badger-synthetic-benchmark \
  -p User=ubuntu -p Group=ubuntu -p WorkingDirectory=/opt/backtest-badger/current \
  -p MemoryMax=1536M -p MemorySwapMax=512M -p CPUQuota=150% \
  -p RuntimeMaxSec=620 -p ProtectSystem=strict -p ProtectHome=read-only -p PrivateTmp=true \
  /opt/backtest-badger/current/.venv/bin/python -B ops/lightsail/benchmark.py
```

Save the report, peak RSS, `free -h`, CPU credit/throttling observations and disk
headroom. Synthetic timing is a capacity smoke test; D2 must additionally check
full pinned-input model replay in a read-only isolated rehearsal and bounded
refresh/DB timings. No server performance claim is made from a Mac run.

## Validation

Local commands (no server, live prediction or real database writes):

```sh
.venv/bin/python ops/lightsail/validate.py templates
.venv/bin/pytest -q tests/test_lightsail.py
.venv/bin/python -B ops/lightsail/benchmark.py
bash -n ops/lightsail/prepare-release.sh ops/lightsail/status.sh
uv run --locked --no-sync --offline ruff check .
uv run --locked --no-sync --offline ruff format --check .
uv run --locked --no-sync --offline pytest
git diff --check
```

`templates` runs native Compose parsing with fake credentials and checks loopback
binding, digest, external volume and resource/restart contracts. It reports native
systemd syntax as **not checked** unless `--native-systemd` is supplied. That flag
requires Linux and installed unit executable paths; missing tools fail clearly.
`runtime --worker collection|scoring` is a read-only service preflight and requires
D2-configured secrets in the process environment; it does not echo values. Collection
checks for training inputs, while scoring has no training dependency.

After privately filling the D2 environment files, run `sudo .venv/bin/python
ops/lightsail/validate.py configuration` from the release to check both files'
ownership/modes, the configuration directory, distinct passwords and the PG17
digest without printing secrets or connecting to PostgreSQL.

The focused tests check independent timers, restricted writes, path compatibility
across release links, environment mode/owner and placeholder failures, missing tools,
read-only status, full synthetic counts/holdout barrier, integrity failure and the
benchmark watchdog. Existing synthetic worker tests cover lock release, publication,
retry and interrupted-journal behaviour. A local disposable PostgreSQL 17 database
is required to run the existing integration cases; never use the development DB.
Executed results are recorded below after verification.

References used for deployment semantics: [Docker Compose services](https://docs.docker.com/reference/compose-file/services/),
[uv CLI](https://docs.astral.sh/uv/reference/cli/) and the Ubuntu 24.04 container's
installed `systemd-analyze` / systemd manuals. These inform deployment plumbing;
the existing Stage 1–3 code and frozen protocol remain authoritative scientifically.

### Executed D1 verification on 2026-10-14

- **880 tests passed, zero skipped**, including 24 deployment cases and all existing
  PostgreSQL integration cases. Only a disposable local PostgreSQL 17 container on
  `127.0.0.1:55439` and fixture-generated random databases were used. The final full
  run took 35.78 seconds; the disposable container was removed afterward.
- Ruff lint and formatting passed (103 Python files); Bash syntax, both embedded
  Python setup blocks, tracked diffs and whitespace in all 15 new files passed.
- Native Docker Compose 5.3.1 parsing/contract checks passed with synthetic values;
  no production configuration was resolved or printed.
- All four units passed native `systemd-analyze verify` in a disposable Ubuntu 24.04
  container, systemd 255.4-1ubuntu8.18. Both UTC calendar expressions parsed. Dummy
  executables and a dummy Docker unit satisfied syntax-check dependencies; this is
  **not** a running-systemd sandbox/reboot test or target-server installation test.
- The Mac arm64/Python 3.12.13 synthetic benchmark passed in **6.09 seconds** total:
  BTC record plus full replay 2.48 seconds, ETH 2.43 seconds; peak RSS about 248 MiB.
  It used all frozen-recipe training row counts and generated no real forecasts.
  Server x86_64/Python 3.12.15 timing and concurrent-load acceptance remain D2 gates.
- **1,044 pre-existing files** retained identical SHA-256, byte size and nanosecond
  modification time: scientific source, lock/dependency files, frozen protocol,
  installed/repository LaunchAgent plists and inventoried artifacts/completed
  journals. Active logs/state and in-progress journals were excluded from this
  immutable baseline; independent Mac jobs may append new operational evidence.
  The prompt archive matches the supplied request byte for byte.
- Read-only launchd inspection found both Mac jobs loaded and idle between scheduled
  invocations, last exit code 0 (collector 73 runs; scorer 20). Neither was stopped,
  reloaded or reconfigured. No SSH, Lightsail installation, real DB restore,
  scientific publication, commit, push or D2 execution occurred.

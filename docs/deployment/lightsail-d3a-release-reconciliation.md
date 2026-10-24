# Stage D3A — Lightsail release reconciliation

**Observed:** 24 October 2026, 16:28–16:33 UTC, through `ssh Ubuntu-1`.
**Result: HEALTHY / RELEASE UPDATE READY.** One inactive release was prepared;
production was not promoted. This is a dated observation, not continuous monitoring.

## Release identities and CI

| Item | Verified value |
| --- | --- |
| Active production SHA | `e0d622d51e1edc120fb4f1b5229e46907ed6219d` |
| Candidate SHA | `cceb6509edbb6e6a9fb577c112bf9c648e81c5a1` |
| Candidate directory | `/opt/backtest-badger/releases/cceb6509edbb6e6a9fb577c112bf9c648e81c5a1` |
| Preparation time | `2026-10-24T16:32:18.288027+00:00` |
| GitHub CI | [40106649560](https://github.com/owencrew/backtest-badger/actions/runs/40106649560), exact candidate SHA, `completed / success`, API updated `2026-10-24T16:25:25Z` |
| Local starting checkout | `main`, clean at the candidate SHA; no commit or push performed |

`current` resolved to `/opt/backtest-badger/releases/e0d622d51e1edc120fb4f1b5229e46907ed6219d`
both before and after preparation. A further pre-existing release directory,
`556e3a9b80066b2d83cf1e1e4ee5795fc6ec290f`, was retained without modification.
Both inspected releases have unchanged tracked files; the expected generated
`artifacts` symlink and `deployment.json` appear as untracked files after preparation.
The candidate was an exact clean detached checkout **before** running the script.

## Production health and recovery evidence

- Ubuntu **24.04.5 LTS, x86_64**; Python **3.12.15**, uv **0.13.1**;
  UTC timezone and NTP synchronised. The managed interpreter is under
  `/home/ubuntu/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/`.
- PostgreSQL **17.11** container `backtest-badger-lightsail-postgres-1` was healthy;
  its persistent volume is `backtest-badger-pg17`. Image digest:
  `sha256:3cec7eb015ba8adb28139fa5c83b8489cdf0e666e53dfdf20f598ae0cc8739e3`.
  An explicit read-only SQL transaction returned Alembic revision **0001**.
- All six timers were enabled/active. Their latest service results were
  `success`, exit **0**. Final worker completions: collection **16:31:04** and
  scoring **16:32:07** on 24 October. Worker unit files exactly match repository
  templates, with no worker drop-ins. The backup pause marker was absent.
- Offline checks under **both** releases accepted the retained evidence:
  **122 scored, 2 pending, 0 mature unscored**, no invalid records/outcomes,
  collector failures, incomplete cycles or partial journals. Neither market had
  a detected missed forecast horizon. Latest issuance was at **16:01 UTC**.
  These are operational counts, not accuracy or trading-performance claims.
- Retained operation timestamps account for every expected five-minute worker
  tick from **17 October 00:00 through 24 October 16:30 UTC**: 288 per worker per
  complete day, then 198 each on 24 October. No missing ticks were found in this
  bounded interval; earlier history is not asserted complete.
- **Unattended shared-snapshot backups:** one successful daily run on each of
  **17–24 October**, with nine component hash successes, saved remote snapshot
  and receipt publication signals. Latest checkpoint:
  `checkpoint-20261024T024008Z`; completion **02:40:29 UTC**;
  remote snapshot `cd970a1e7cb17fc2a20d8cf3f11ace5d76ced7f79f6f11bbcb566ed36519464d`.
  All nine latest local bundle hashes were independently rechecked successfully.
  A read-only, no-lock/no-cache restic inventory confirmed **12** remote snapshots.
- **Unattended restore:** **18 October 06:00:03–06:00:16 UTC**, retained result
  `PASS`, nine checkpoint hashes and exact source/restored fingerprint match.
  Snapshot `44b3a0709ff6f33ab3a2d487040c78d7a7eeb77e4057ddefe0670071bd6ab167`;
  audit covered **2 markets, 40,114 candles, 0 revisions, 1 Alembic row**, algorithm
  `sha256-postgres-copy-json-utc-v1`. Its transient container/volume are absent;
  result and restored audit remain at
  `/var/lib/backtest-badger-restore-drills/20261018T060003Z/`.
  This proves recovery of that snapshot, not restoration of the 24 October backup.
- **Unattended retention:** successful daily deletions on **17–24 October** at
  05:30. First removal was `checkpoint-20261015T173515Z`; latest removal was
  `checkpoint-20261021T024008Z`. Three checkpoints remain (22, 23 and 24 October),
  approximately **178, 189 and 198 MiB**. These deletions predate this inspection;
  no retention job was triggered here.
- Storage monitoring completed four scheduled runs per day on **17–23 October**
  and the three due runs on 24 October, all with healthy signals; latest **12:15:08**.
  Root disk: **7.5 GiB used / 77 GiB, 10%, 69 GiB available** before staging.
  RAM: **3.7 GiB**, about **2.8 GiB available**, no swap. Candidate occupies **269 MiB**.
  Persistent artifacts: **184 MiB**; retained restore evidence: **257 MiB**.
  Seven existing containers/volumes, including six historical test/recovery
  containers, remain untouched. Docker reported about **560 MB** of volume data.

Evidence came from service properties, sanitised journal summaries, retained
operation/result/audit files, script verification logic, snapshot inventory and
offline application status functions. No raw logs, credentials or forecast values
are included. A broad worker-journal read was stopped by terminating only its own
inspection processes; bounded evidence inspection supplied the results above.

## Compatibility and preparation

The comparison spans **42 commits / 126 changed files**. No existing application
Python file changed. Collection, scoring, CLI, DB code, frozen forward protocol,
Alembic files, Lightsail scripts, Compose and worker systemd templates are identical.
Additions implement local paper primitives, minute data/replay, authentication,
historical execution/reporting, tests and documentation; CI adds guarded test runs.
No new worker command or service is introduced.

`pyproject.toml` adds `cryptography>=46,<47`; the lockfile adds
**cryptography 46.0.7, cffi 2.1.1 and pycparser 3.11**. Existing locked package
versions are unchanged. The established `prepare-release.sh` installed locked
wheels with Python 3.12.15, without builds or interpreter downloads. It created
the candidate's metadata and symlink to `/var/lib/backtest-badger/artifacts`.
Manifest hashes/package versions, unchanged tracked source, previous recorded
package versions, persistent link, synthetic Compose validation, native systemd
validation and offline Alembic head **0001** passed.

**Provenance consequence:** forward recipes hash `uv.lock` and `pyproject.toml`.
New forecasts will therefore have a different recipe fingerprint despite unchanged
models and existing package versions. Collection retries and scoring validate old
evidence without requiring current dependency-file hashes; candidate offline
checks passed. Full deterministic replay requires the originating release/runtime.
Keep **both** release environments; do not rewrite historical records or relax
validators. Rollback retains all candidate-era evidence and uses its originating
release for exact replay. No model fit, historical replay or private research-input
transfer was performed. Production configuration/DB preflights for the candidate
remain D3B checks because `validate.py runtime` deliberately requires `current`.

## D3B promotion plan — proposed only

Obtain explicit activation approval. Recheck CI identity, candidate manifest and
source, evidence validity, NTP, database health/revision and available disk space.
Require a successful off-machine backup **within 24 hours**, its bundle integrity,
and a successful fingerprint restore **within seven days**; inspect the next
scheduled drill if promotion occurs later. If stale or failed, stop and separately
authorise the established backup/drill procedure; do not improvise recovery.
Confirm no other host/manual writer and no concurrent release operator.

Choose a quiet window after a successful native four-hour collection boundary.
Briefly pause only collection/scoring timers and let in-flight services finish;
this prevents a worker resolving mixed releases across its preflight and execution.
No database interruption, unit installation, daemon reload or migration is needed.
Retain the previous release and both deployment manifests before switching.

On `Ubuntu-1`, the following is a **future, operator-supervised** sequence. Stop
on any failed assertion. Do not resume timers after a failed candidate preflight
until the rollback below passes. If stopping before the switch, resume the old
timers once the old runtime is confirmed healthy. Keep this shell open while paused.

```bash
sudo -s
set -eu
old=/opt/backtest-badger/releases/e0d622d51e1edc120fb4f1b5229e46907ed6219d
candidate=/opt/backtest-badger/releases/cceb6509edbb6e6a9fb577c112bf9c648e81c5a1
test "$(readlink -f /opt/backtest-badger/current)" = "$old"
test "$(readlink -f "$candidate/artifacts")" = /var/lib/backtest-badger/artifacts
test ! -e /run/backtest-badger-backup-paused
# Coordinate with the existing backup/retention lock; do not remove it.
exec 9>>/run/backtest-badger-s3-backup.lock
flock -n 9
test "$(systemctl show backtest-badger-backup.service -p ActiveState --value)" = inactive
systemctl stop backtest-badger-collection.timer backtest-badger-scoring.timer
# Allow normal completion; do not stop/kill an in-flight worker.
deadline=$(( $(date +%s) + 930 ))
while :; do
  c=$(systemctl show backtest-badger-collection.service -p ActiveState --value)
  s=$(systemctl show backtest-badger-scoring.service -p ActiveState --value)
  if [ "$c" = inactive ] && [ "$s" = inactive ]; then break; fi
  test "$(date +%s)" -lt "$deadline"
  sleep 5
done
for worker in collection scoring; do
  test "$(systemctl show "backtest-badger-$worker.service" -p Result --value)" = success
done
test ! -e /opt/backtest-badger/current.d3b
test ! -L /opt/backtest-badger/current.d3b
sudo -u ubuntu ln -s "$candidate" /opt/backtest-badger/current.d3b
sudo -u ubuntu mv -T /opt/backtest-badger/current.d3b /opt/backtest-badger/current
for worker in collection scoring; do
  systemd-run --wait --pipe --collect --unit="badger-d3b-check-$worker" \
    -p User=ubuntu -p Group=ubuntu \
    -p WorkingDirectory=/opt/backtest-badger/current \
    -p EnvironmentFile=/etc/backtest-badger/worker.env \
    -p Environment=PYTHONDONTWRITEBYTECODE=1 \
    /opt/backtest-badger/current/.venv/bin/python -B \
    ops/lightsail/validate.py runtime --worker "$worker"
done
systemd-run --wait --pipe --collect --unit=badger-d3b-db-check \
  -p User=ubuntu -p Group=ubuntu \
  -p WorkingDirectory=/opt/backtest-badger/current \
  -p EnvironmentFile=/etc/backtest-badger/worker.env \
  -p Environment=PYTHONDONTWRITEBYTECODE=1 \
  /opt/backtest-badger/current/.venv/bin/badger db-health
systemctl start backtest-badger-collection.timer backtest-badger-scoring.timer
flock -u 9
exit
```

The transient checks above validate configuration/connectivity only; they do not
invoke application cycles. After resume, inspect timer next ticks and actual
service results, then sanitised offline status. Require the next normal collection
and scoring cycles to succeed. Observe the next native four-hour issuance for both
markets and scoring after its target matures: no invalid evidence, failure backlog
or unexpectedly mature-unscored records. Record the promotion timestamp and accept
any missed opportunity honestly; never backfill forecasts.

**Rollback conditions:** failed runtime/DB preflight, repeated worker failures,
invalid evidence, new mature-unscored backlog or missed eligible issuance linked
to the release. Before any candidate cycle, a failed preflight permits immediate
source-only reversal. After candidate execution, first preserve incident evidence
and confirm the previous release accepts the accumulated records using offline
status; do not restore the database or artifacts. Reacquire the same backup lock,
pause/drain workers as above, then reverse the link with a fresh sibling:

```bash
# In the same supervised root-shell setup, with old set and workers drained:
test ! -e /opt/backtest-badger/current.rollback-d3b
test ! -L /opt/backtest-badger/current.rollback-d3b
sudo -u ubuntu ln -s "$old" /opt/backtest-badger/current.rollback-d3b
sudo -u ubuntu mv -T /opt/backtest-badger/current.rollback-d3b /opt/backtest-badger/current
```

Repeat both runtime checks and DB health against `current` before resuming timers
and releasing the lock. If compatibility cannot be established, keep workers
paused and investigate; never downgrade schema or remove evidence. The known-good
previous release is the full active SHA above, not the older retained directory.

## Remaining risks and validation

No staging blocker was found. D3B approval must accept the brief worker pause and
dependency-file provenance change. Existing limitations remain: retention refuses
more than four checkpoints; legacy restores can lack fingerprint manifests;
remote restic pruning remains historically disabled; storage/retention services
have no `OnFailure` handler. Backup/restore failure handlers are configured, but
alert delivery and external Lambda/EventBridge executions, AWS budgets and S3
lifecycle settings were **not independently reverified**. No fresh restore was
triggered. Historical recovery containers/evidence require separate cleanup review.

Validation performed: exact-run GitHub CI and job success; read-only host/SQL and
recovery checks above; candidate preparation and native template validation;
local `pytest -q tests/test_lightsail.py` (**24 passed**), repository-wide Ruff
lint/format (**225 files already formatted**), shell syntax, Markdown link and
whitespace checks. Full pytest/guarded suites were verified through CI, not rerun
locally. No active release switch, production writes, service/timer/configuration
change, manual worker execution, backup/restore/retention invocation, website
deployment, local commit or push occurred.

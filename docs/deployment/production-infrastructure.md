# Production infrastructure and operations

**Backtest Badger — host observations updated on 24 October 2026 (UTC).**

This is the **current-state** production runbook, distinct from the historical [Lightsail foundation](lightsail-foundation.md), [migration plan](lightsail-migration-runbook.md) and [D2A rehearsal](lightsail-d2a-rehearsal.md). The migration documents describe earlier gates and may contain statements about Mac-only operation that are now historical. **Inspect the actual host and AWS configuration before making changes**; this document is not a live inventory.

### Release promoted on 24 October, 20:58 UTC

The authorised [D3B.1 retry](lightsail-d3b1-release-retry.md) activated
`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1` at **20:58:48.203002841 UTC**.
`current` resolves to that exact immutable release directory. The previous release
`e0d622d51e1edc120fb4f1b5229e46907ed6219d` and its environment remain available.
Exact-candidate CI passed. The earlier [D3B incident](lightsail-d3b-release-promotion.md)
remains preserved; its helper import collision was corrected and the real staged
commands were tested before the retry. No rollback occurred.

- Both runtime validators and DB health passed before and after activation.
  PostgreSQL **17.11** remains healthy on its existing volume, Alembic **0001**;
  the schema fingerprint is unchanged. Python **3.12.15**, synchronised NTP,
  root disk **10% used / 69 GiB free** were rechecked.
- Only collection/scoring timers paused, for approximately **23.9 seconds**;
  they resumed at **20:58:57 UTC**, before their next **21:01 / 21:02** ticks.
  Natural collection completed **21:01:06** and scoring **21:02:12**, both
  `success / exit 0`. All six timers remain scheduled; backup lock released.
- All **250** original forecast/outcome files retained their exact hashes.
  Post-worker checks at **21:02 UTC** found **124 scored, 2 pending**, with no invalid evidence,
  missed horizons or mature-unscored backlog. One pre-existing late issuance per
  market remains classified as late.
- Latest off-machine backup: **24 October 02:40:29 UTC**, checkpoint
  `checkpoint-20261024T024008Z`, snapshot `cd970a1e…`; all nine local hashes and
  remote presence/freshness rechecked. Latest fingerprint-verified isolated
  restore: **18 October 06:00 UTC**, snapshot `44b3a070…`, within seven days.
  No manual backup or restore was initiated. Next regular drill: **25 October 06:00**.
- The next new dependency-provenance issuance is expected **25 October 00:01 UTC**;
  its actual publication/hash check and subsequent scoring remain **pending**.
  Earliest target scoring eligibility: **04:01 UTC**, scheduled check **04:02**.
  Preserve both runtimes for exact replay; historical provenance was not rewritten.

The [D3A review](lightsail-d3a-release-reconciliation.md) retains the detailed
17–24 October unattended backup/retention and 18 October restore observations.
Detailed 16 October infrastructure observations below remain historical where
explicitly dated. External AWS configuration and alert delivery were not
independently rechecked during D3B.1. No permanent infrastructure or scientific
methodology changed.

## 1. Architecture and responsibility boundaries

```text
AWS Lightsail (Ubuntu 24.04; production Linux host)
  /opt/backtest-badger/current        pinned application release
  /etc/backtest-badger/               private configuration; never commit
  /var/lib/backtest-badger/           persistent artifacts, local checkpoints
  Docker: PostgreSQL 17, persistent named production volume
  systemd: collection + scoring every five minutes
           encrypted S3 backup daily
           isolated S3 restore drill weekly
           local disk monitoring + checkpoint retention
                 |
                 v
AWS S3 (eu-west-2): versioned bucket, encrypted restic repository
  restic/                             encrypted backup repository
  monitoring/latest.json              published backup completion receipt
                 |
                 +--> EventBridge -> Lambda freshness monitor -> SNS email
                 +--> CloudWatch Lambda Errors alarm -> SNS email
                 +--> backup / restore systemd failure handlers -> SNS email

AWS Budgets: monthly account-wide cost alert notifications
```

All times below are **UTC**. The host is not currently serving a confirmed production website or paper-trading order engine. The public site and paper trading remain separate planned work; do not conflate forward predictions/scoring with executed or simulated orders.

### Confirmed host resources (16 October 2026)

- Ubuntu 24.04 on AWS Lightsail; approximately 3.7 GiB RAM, no swap; root filesystem 77 GB with 6.7 GB used (~9%) and 70 GB available at last check.
- PostgreSQL 17 Docker container: `backtest-badger-lightsail-postgres-1`, database `backtest_badger`, persistent named volume `backtest-badger-pg17`. **Never remove, recreate, truncate or restore over this production volume.**
- Application checkout/release: `/opt/backtest-badger/current`. The migration-era release was reported as Git commit `e0d622d51e1edc120fb4f1b5229e46907ed6219d`; check `git rev-parse HEAD` for the *current* revision.
- Worker activation gate: `/etc/backtest-badger/workers-approved`. Treat as production authorisation: do not toggle merely to test scripts.
- A number of explicitly isolated historical recovery/test containers and volumes are intentionally preserved. Docker's apparent reclaimable storage is **not** permission to prune them.

## 2. Schedules and services

| Timer | Schedule | Function |
| --- | --- | --- |
| `backtest-badger-collection.timer` | Every 5 minutes | Capture new eligible forward predictions |
| `backtest-badger-scoring.timer` | Every 5 minutes | Score eligible recorded outcomes |
| `backtest-badger-backup.timer` | Daily **02:40 UTC** | Consistent checkpoint, encrypted upload and receipt |
| `backtest-badger-restore-drill.timer` | Sunday **06:00 UTC** | Restore latest snapshot to isolated PostgreSQL; validate and clean up on success |
| `backtest-badger-storage-monitor.timer` | **00:15, 06:15, 12:15, 18:15 UTC** | Local filesystem and backup-directory warnings |
| `backtest-badger-local-retention.timer` | Daily **05:30 UTC** | Retain newest three local checkpoints, subject to strict remote verification |

**External AWS schedule:** EventBridge invokes the backup freshness Lambda at **04:00 UTC daily**, independently of the Lightsail host.

Read-only health inspection:

```bash
systemctl list-timers --all 'backtest-badger-*'
for t in collection scoring backup restore-drill storage-monitor local-retention; do
  systemctl is-active "backtest-badger-$t.timer"
done
sudo docker inspect -f '{{.State.Health.Status}}' backtest-badger-lightsail-postgres-1
df -h /
sudo docker system df
```

Note: a timer being active means the schedule is enabled, **not** that its last execution succeeded. Inspect service results and journals separately:

```bash
systemctl show backtest-badger-backup.service -p Result -p ExecMainStatus
systemctl show backtest-badger-restore-drill.service -p Result -p ExecMainStatus
systemctl show backtest-badger-local-retention.service -p Result -p ExecMainStatus
sudo journalctl -u backtest-badger-backup.service -n 100 --no-pager
sudo journalctl -u backtest-badger-restore-drill.service -n 100 --no-pager
sudo journalctl -u backtest-badger-local-retention.service -n 50 --no-pager
```

Do not run collection/scoring manually or re-enable an old Mac scheduler without reviewing the single-writer and timing/provenance constraints in the migration runbook.

## 3. Backup procedure

Production entry point: `/usr/local/sbin/backtest-badger-s3-backup`, invoked by `backtest-badger-backup.service`. The successfully tested **shared-snapshot** implementation was made active on 16 October. A proven older backup script is preserved as `/usr/local/sbin/backtest-badger-s3-backup.pre-phase132` for deliberate rollback only.

The backup obtains an exclusive `flock` on `/run/backtest-badger-s3-backup.lock`. It temporarily pauses collection and scoring, waits for in-flight services, captures application/artifact/release evidence, and resumes the two timers even on failure via guarded cleanup/recovery. The database dump and source fingerprints use the **same exported PostgreSQL MVCC snapshot**, coordinated by `/usr/local/sbin/backtest-badger-snapshot-capture`.

Checkpoints live at `/var/lib/backtest-badger/backups/checkpoint-YYYYMMDDTHHMMSSZ`. Important members include:

- `database.dump` — PostgreSQL custom-format backup;
- `database-audit.json` — four-table, row-count and SHA-256 fingerprints from the same snapshot;
- `bundle.sha256` — integrity hashes of checkpoint components;
- `roles-without-passwords.sql`, `artifacts.tar`, `release-metadata.tar`, `release-path.txt`, `checkpoint-time.txt`, `service-journals.txt`, `database-objects.txt`.

Artifacts and release metadata have their own archival provenance; source-database fingerprints cover **only** `market`, `candle`, `candle_revision` and `alembic_version`, not arbitrary future tables or the byte-by-byte contents of artifacts. The algorithm identifier is `sha256-postgres-copy-json-utc-v1`. The dump and audit come from the same consistent database snapshot; their exact equality is checked after an independent restore.

Encrypted restic repository: `s3:s3.eu-west-2.amazonaws.com/backtest-badger-backups-1/restic`; snapshots tagged `production-checkpoint`. On verified successful upload the job publishes an S3 completion receipt at `monitoring/latest.json`. **The receipt is not itself proof of successful restore.**

Root-owned private configuration includes `/etc/backtest-badger/s3-backup.env` and `/etc/backtest-badger/restic-password`. Never display, echo, paste or commit their contents or AWS credentials, IAM keys, password material, private dataset contents or unredacted logs. Do not place encryption keys in Git.

Read-only snapshot inventory on the host:

```bash
sudo bash -c '
  set -Eeuo pipefail
  set -a
  source /etc/backtest-badger/s3-backup.env
  set +a
  export RESTIC_PASSWORD_FILE=/etc/backtest-badger/restic-password
  restic snapshots --tag production-checkpoint
'
```

The backup service has a 20-minute systemd timeout, control-group cancellation, pause-marker recovery, and an SNS `OnFailure` handler. Inspect service logs before considering any manual rerun. A backup that fails halfway through must not strand the collection/scoring timers paused.

## 4. Recovery and verification

Entry point: `/usr/local/sbin/backtest-badger-restore-drill`; systemd unit `backtest-badger-restore-drill.service`. It selects the latest eligible `production-checkpoint` snapshot (freshness rule currently less than 36 hours), downloads it into a unique private drill directory, verifies `bundle.sha256`, and restores the dump to a **new, isolated, network-disabled PostgreSQL 17 Docker container and separately named volume**. The drill checks schema/Alembic, markets, revisions, immutable-trigger presence, candle validity, and isolation. If `database-audit.json` exists it recalculates all four fingerprints from the recovered database and requires an exact match.

On a successful drill the transient container, volume and downloaded recovery payload are removed; a compact evidence record is preserved under `/var/lib/backtest-badger-restore-drills/`. On failure, diagnostic evidence is retained and the restore failure handler sends SNS notification. Never clean up a failed drill blindly.

A supervised service-run on **16 October 2026 at 13:17 UTC** restored the actual encrypted S3 snapshot `af11e72d...`, verified all nine checkpoint hashes, matched all four source/database fingerprints (2 markets, **40,096 candles**, 0 revisions, 1 Alembic row), passed candle integrity checks and cleaned up its transient recovery environment. This establishes a **tested recovery path for that checkpoint**, not a guarantee of every possible future database/schema change.

**Important limitation:** legacy checkpoints without `database-audit.json` are accepted with an explicit warning and only structural/integrity checks. Do not describe those as fingerprint-verified. Adding a required-audit policy for all new-format checkpoints is outstanding.

Read-only inspection of recovery evidence:

```bash
sudo journalctl -u backtest-badger-restore-drill.service -n 120 --no-pager
sudo ls -ld /var/lib/backtest-badger-restore-drills/*
```

A manual restore drill can be initiated only after confirming there is sufficient free disk/RAM and no other drill is running:

```bash
sudo systemctl start backtest-badger-restore-drill.service
systemctl show backtest-badger-restore-drill.service -p Result -p ExecMainStatus
```

If it fails, **do not immediately rerun**: inspect the journal and preserved evidence and investigate the alert. A true production disaster recovery is a separate, explicitly authorised operation following the historical migration/recovery runbook; **do not restore into the production database as a quick test**.

## 5. Monitoring and alerting

- **AWS Budgets:** account-wide recurring **USD $35/month** budget, four thresholds: $25 actual, $30 actual, $35 actual, and $35 forecast. Notifications are early warning, **not a hard spend cap**; reporting may lag.
- **Backup freshness:** EventBridge-driven independent Lambda `backtest-badger-backup-monitor` at 04:00 UTC reads the published checkpoint receipt. CloudWatch alarm `backtest-badger-lambda-errors` watches Lambda `Errors`. An independent missed-invocation alarm has **not** been confirmed installed.
- **Backup/restore failures:** systemd `OnFailure` handlers publish to the existing SNS alert topic. SNS subscription delivery and alarm paths were tested during deployment.
- **Local storage:** `/usr/local/sbin/backtest-badger-storage-monitor` runs every six hours. Sends SNS when root disk reaches **70%** (warning) or **85%** (critical), or local backups reach **5 GiB** (warning). Status-change deduplication means it does not necessarily remind the operator repeatedly while a warning persists. Monitor execution failure is **not independently alarmed**.
- **S3 bucket lifecycle:** Versioning enabled. Exactly two narrowly filtered rules: noncurrent `restic/locks/` versions after **30 days** and noncurrent `monitoring/` versions after **90 days**. **No lifecycle expiry rule on current restic repository data**, and no broad rule affecting `restic/data/`, `index/`, `snapshots/`, `config` or `keys/`.

Approximate reference sizes on 16 October: Lightsail root disk 9% used; three local checkpoints ~384 MiB; S3 current restic/receipt storage ~35 MiB; S3 historical lock versions occupy negligible space. These are observations, not permanent limits. S3 charges can include requests, transfers, replication/version storage and monitoring outside this inventory; budget notifications are not a guarantee of zero excess charges.

## 6. Local and remote retention

**Local (enabled):** `/usr/local/sbin/backtest-badger-local-retention-auto` is invoked daily at 05:30 UTC by `backtest-badger-local-retention.service`. It acts only when there are **exactly four** correctly named checkpoint directories. It checks that the newest three are represented by remote production snapshots and invokes `/usr/local/sbin/backtest-badger-local-retention` with an explicit `--delete --confirm checkpoint-NAME` for the oldest. The guarded script acquires the **same exclusive backup lock**, checks remote restic snapshot paths and required recovery file entries, and deletes **only that local directory**, not any remote snapshot. The guarded deletion was tested manually on 16 October; the wrapper was tested successfully with only three directories (**no deletion**). **Verified on 24 October:** the first unattended deletion succeeded on 17 October at 05:30, followed by successful daily deletions through 24 October; three local checkpoints remain. The exactly-four guard is still present.

**Fail-closed limitation:** if more than four checkpoints accumulate (e.g. a missed cleanup day), the automated wrapper refuses to clean any. This is safer than mass deletion but **not** a bounded-storage guarantee. Disk monitoring at 5 GiB provides a separate warning. The local script checks remote snapshot existence/file listing; it does **not** independently restore the candidate just before deletion.

**Remote (not enabled):** restic snapshot removal/pruning is deliberately disabled. A policy was reviewed in **dry-run only**: group by host and tags; keep latest 2, daily 7, weekly 4 and monthly 3. Neither automatic `restic forget` nor `restic prune` is scheduled. The current S3 lifecycle rules affect only obsolete temporary lock and monitoring object **versions**, not snapshot history. This preserves recovery points but means S3 storage could grow without bound as data volumes increase. Do **not** enable restic pruning or an S3 data-expiration policy without separate approval, full dry-run review and a recent successful restore.

Inspect local candidates without deleting:

```bash
sudo find /var/lib/backtest-badger/backups -mindepth 1 -maxdepth 1 \
  -type d -name 'checkpoint-*' -exec du -sh {} \;
sudo du -sh /var/lib/backtest-badger/backups
sudo journalctl -u backtest-badger-local-retention.service -n 70 --no-pager
```

## 7. Incident response quick reference

| Symptom | Safe initial response | Do **not** |
| --- | --- | --- |
| Collection/scoring timer inactive | Check `systemctl status`, relevant journal, pause marker and backup status; establish cause | Re-enable both writers or replay missed predictions indiscriminately |
| Backup failed / receipt stale | Inspect backup service, last successful snapshot, `/run/backtest-badger-backup-paused`, disk and S3 reachability; confirm worker timers recovered | Start repeated backups or clear locks/markers while work is active |
| Restore drill failed | Inspect its journal and preserved isolated evidence; check source snapshot age and manifest availability | Delete evidence or restore onto the production volume |
| Storage warning | `df -h /`, `du` local backups, Docker inventory, retention journals, AWS S3 inventory | Run `docker system prune`, `docker volume prune`, indiscriminate `rm -rf` or S3 lifecycle expiry |
| Unexpected AWS spend | Review Budgets, Cost Explorer grouped by service and region, S3 request/storage classes and transfer; adjust alerts | Assume Budgets automatically stops spending |
| Corrupt/unavailable production DB | Stop and preserve evidence; locate last validated restic recovery; prepare an **isolated** restore plan and approve cutover | Restore into active production or delete its named volume |

Any destructive operation should have an explicit target list, a fresh backup, an operator review, and an actionable rollback path. Work with the root-owned scripts and unit definitions as deployed; committing this document does **not** deploy or change infrastructure.

## 8. Security and deployment hygiene

- Keep `/etc/backtest-badger/` secrets, restic password, SNS/IAM credentials, and source data outside Git and outside user-visible diagnostic output.
- Dedicated least-privilege AWS backup credentials on Lightsail; bucket-level lifecycle configuration was performed with a separately authorised AWS console/CloudShell identity, not by granting the backup user extra management permissions.
- S3 bucket versioning protects historical versions; it does not replace a tested isolated restore.
- PostgreSQL is a persistent production container. Never test restore/upgrade/migration against the production data volume.
- Production release changes must respect pinned dependencies, scientific protocol/provenance, immutable observations, forward collection freshness and scoring semantics. Review the historical cutover gates before moving or restarting workers.
- A documentation commit alone does not change the running host. Keep server-owned operational scripts and systemd units under change control; consider moving reviewed, secret-free templates into the repository in a separate task.

## 9. Verification milestones and open items

**Proven by 16 October 2026:** one successful supervised shared-snapshot production backup and encrypted S3 upload; an independent manual recovery with identical four-table source fingerprints; a successful end-to-end supervised systemd restore drill; alert-path testing; AWS budget creation; local monitor successful service execution; exact-prefix bucket lifecycle rules; guarded deletion of one verified local checkpoint with all remote restic snapshots preserved; six active timers and healthy production PostgreSQL.

**Still to verify or implement:**

1. Independently verify the external **04:00** AWS monitor's invocations and alert delivery. **Closed on 24 October:** host evidence confirms the first 17 October shared-snapshot backup and automatic four-checkpoint deletion, plus all daily runs through 24 October.
2. Continue checking weekly fingerprint-verified restores. **Closed on 24 October:** the first unattended Sunday **18 October 06:00 UTC** drill passed, with result/audit retained and successful transient resources cleaned up. Next scheduled drill: **25 October 06:00 UTC**.
3. Independent alarm for *missing* backup-monitor Lambda invocations and, if desired, failures of storage/retention monitoring itself.
4. Safe, supervised remote restic retention/pruning after adequate recovery history accumulates; avoid aggressive S3 object lifecycle deletion.
5. Decide whether to require source audit manifests for all nonlegacy backups; update checks when new core tables/schema are introduced.
6. Address the automatic local-cleanup exactly-four-checkpoints limitation before a prolonged unattended period.
7. Document and version-control reviewed operational script/unit templates separately, without copying host secrets.

**Last host review:** 2026-10-24, D3B.1 promotion. **Last independently documented external AWS configuration review:** 2026-10-16. Update observations after later runs or changes; future forecast/scoring observations remain pending as stated above.

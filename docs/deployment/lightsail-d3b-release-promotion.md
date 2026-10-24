# Stage D3B — Lightsail release promotion attempt

**Result: PROMOTION BLOCKED / INVESTIGATION REQUIRED.** The one authorised attempt
failed before changing `current`. The old release was independently verified and
normal scheduling restored. No second promotion was attempted.

## Release identities and prerequisites

Inspected through `ssh Ubuntu-1` on **24 October 2026**, beginning **19:35 UTC**.
All times below are UTC. The [original request](../../prompts/deployment/004-lightsail-release-promotion.md)
and [D3A review](lightsail-d3a-release-reconciliation.md) define the scope.

| Item | Verified value |
| --- | --- |
| Actual active SHA, before and after attempt | `e0d622d51e1edc120fb4f1b5229e46907ed6219d` |
| Prepared candidate, still inactive | `cceb6509edbb6e6a9fb577c112bf9c648e81c5a1` |
| Candidate preparation time | `2026-10-24T16:32:18.288027+00:00` |
| Candidate deployment-manifest SHA-256 | `1feb0203b2d1aef8597a72be88bca77f490dec7dbb4c5a19957eaaa090a41da6` |
| Old deployment-manifest SHA-256 | `d6336d20e99f3bde2b626c983b21af3818c72450562c1bc66668ff52bc73b309` |
| Candidate CI | [40106649560](https://github.com/owencrew/backtest-badger/actions/runs/40106649560), exact SHA, `completed / success`, rechecked through GitHub API |
| Promotion timestamp | **None: the atomic symlink switch was never reached** |

Both release HEADs and tracked files matched their pinned commits. Generated
`deployment.json` and `artifacts` were the only untracked entries. All manifest
source/input hashes passed (52 candidate, 27 old), recorded runtime package
versions matched, and every installed distribution/version appeared in that
release's lockfile. Both use Python **3.12.15** and link `artifacts` to
`/var/lib/backtest-badger/artifacts`. No preparation or dependency install was repeated.

PostgreSQL **17.11** was healthy; an explicit `BEGIN READ ONLY` SQL check returned
Alembic **0001**. NTP was synchronised; root disk was **10% used**, **69 GiB free**.
All six timers initially ran normally, with successful completed services. Worker
unit/timer files matched repository templates, without drop-ins. Critical forward,
scoring, evaluation, Lightsail and Alembic files were unchanged between releases.
No backup pause marker, competing lock holder or concurrent operator was observed.
Backup, retention and restore services were inactive; the existing shared backup
lock was acquired during the attempt and again during supervised recovery.

Recovery prerequisites passed:

- **Off-machine backup:** `checkpoint-20261024T024008Z`, completed **02:40:29**;
  snapshot `cd970a1e7cb17fc2a20d8cf3f11ace5d76ced7f79f6f11bbcb566ed36519464d`,
  snapshot time **02:40:20.949122643**. All nine local bundle hashes passed again.
  Read-only restic `--no-lock --no-cache snapshots --json --tag production-checkpoint`
  confirmed its presence and age below 24 hours. The scheduled service journal
  confirmed upload and completion-receipt publication.
- **Isolated restore:** retained `20261018T060003Z/result.txt`, `PASS` at
  **18 October 06:00:15**, within seven days; snapshot
  `44b3a0709ff6f33ab3a2d487040c78d7a7eeb77e4057ddefe0670071bd6ab167`.
  Bounded journal evidence confirmed nine successful hashes, exact source/restored
  fingerprints, integrity checks and transient-resource cleanup. Retained audit:
  algorithm `sha256-postgres-copy-json-utc-v1`, 2 markets, 40,114 candles,
  0 revisions and 1 Alembic row. This verifies that older snapshot, not restoration
  of the latest backup. No manual backup or restore was initiated.

Both releases' offline `forward_operations.status_report()` and
`forward_scoring_operations.status_report()` accepted the retained evidence:
**122 scored, 2 pending, 0 mature unscored**, with no invalid evidence, missed
horizons, collector/scorer failures, incomplete cycles or partial journals.
One pre-existing late issuance per market remains honestly classified as late.

## Failure handling, incident and recovery

A temporary Bash supervisor and two read-only helpers were staged under
`/run/backtest-badger-d3b-20261024/`; existing production scripts and units were
not edited. A transient `backtest-badger-d3b-promotion.service` ran the procedure
independently of the SSH connection, retaining its journal and explicit state.
It held `/run/backtest-badger-s3-backup.lock`, armed cleanup before stopping timers,
allowed workers to finish, and required old-runtime evidence compatibility plus
runtime/DB validation before recovery could resume scheduling. An unknown release
or failed recovery check left workers paused. Rollback was source-only by design.

Local mocked failure-path tests passed for pre-switch failure, candidate failure,
unsafe old evidence, TERM interruption and partial timer-resume failure; shell
syntax and Python syntax checks passed. **These mocks did not test the actual
staged helper filename/import context**, which caused the incident below.

| Time on 24 October | Actual event |
| --- | --- |
| `19:39:13.352388211` | Shared lock held; final service/NTP/container prerequisites passed |
| `19:39:13.355766564` | Collection/scoring timer pause requested |
| `19:39:13.381393121` | Both timers paused; workers already drained |
| `19:39:13.469075557` | Pre-switch helper failed; guarded recovery began |
| `19:39:13.578302302` | Recovery helper also failed; explicit investigation state, workers paused, old SHA active |
| `19:39:58.037096451` | Independent old-release checks passed; both timers resumed |

**Agent-authored procedure error:** the helper was staged as `inspect.py`. Running
it as a Python script put its directory on the import path, shadowing the standard
library's `inspect` module while `importlib.metadata` loaded. The resulting circular
import prevented both the pre-switch check and the supervisor's recovery check.
This was a temporary orchestration failure, not evidence of an application defect.
The failure policy correctly preserved the old link and explicitly paused workers.

Supervised recovery used the earlier successful stdin invocation, avoiding that
filename collision. Under the backup lock it rechecked old-release integrity and
all retained evidence, then ran the existing commands under `ubuntu:ubuntu`, with
`WorkingDirectory=/opt/backtest-badger/current`, production `worker.env` loaded by
transient systemd checks, and `PYTHONDONTWRITEBYTECODE=1`:

```text
.venv/bin/python -B ops/lightsail/validate.py runtime --worker collection
.venv/bin/python -B ops/lightsail/validate.py runtime --worker scoring
.venv/bin/badger db-health
```

Both validators passed; DB health returned `PostgreSQL connectivity OK.` The exact
old `current` target was rechecked before timer resumption. Scheduling was paused
for approximately **45 seconds**, entirely between the normal **19:37** scoring
and **19:41** collection ticks. No scheduled tick was due during the pause.
No rollback symlink change occurred because no forward switch occurred.

A read-only diagnostic at **19:41:08–19:41:11** ran the exact staged helper
under the inactive candidate with `python -P -B`; it passed. Safe-path mode
excluded the helper directory from import lookup, confirming the cause and a
possible correction. The promotion procedure was not changed or rerun.

The original failed supervisor/state and temporary diagnostic files remain for
inspection. Its failed unit records this incident; it is not a worker failure.
The production runbook and development handoff were intentionally left unchanged:
the request permits their new-release updates only after successful promotion.

## Observations and remaining work

Final read-only observation: **19:42:38–19:42:42 UTC**.

- Normal collection execution **19:41:01–19:41:03**: `success`, exit **0**.
- Normal scoring execution **19:42:03–19:42:08**: `success`, exit **0**.
- Both worker timers enabled and active, next ticks **19:46** and **19:47**;
  all six timers scheduled. Backup lock released and pause marker absent.
- Old release integrity and both offline evidence checks passed again:
  **122 scored, 2 pending, 0 mature unscored**, no invalid records/outcomes,
  invalid journals/cursor, failures, partials, incomplete cycles or missed horizons.
  Previously recorded forecasts and outcomes remain accessible. The scorer's
  bounded cursor deferred 24 records normally; the complete inventory found no
  mature-unscored backlog. The two pre-existing late classifications are unchanged.
- PostgreSQL remained healthy. Post-recovery read-only SQL at **19:41:14** again
  returned Alembic **0001**. No schema-changing command was executed. A planned
  before/after schema-dump and immutable-file checksum baseline was never reached;
  no such byte-for-byte comparison is claimed.

These are **post-recovery old-release executions**, not candidate validation.

The candidate's additional locked packages remain **cryptography 46.0.7,
cffi 2.1.1 and pycparser 3.11**, with existing package versions unchanged.
Its `uv.lock` and `pyproject.toml` hashes differ from the active release, so a future
successful promotion will create a new forecast recipe-fingerprint epoch despite
unchanged models. **This attempt created no new dependency-provenance epoch:** no
candidate worker ran and no candidate forecast was issued. Both release environments
remain available; original forecast/outcome records were not edited or regenerated.

**Pending follow-up:** a separately authorised promotion after correcting the
helper import context and exercising the exact staged invocation before pausing
workers. Recheck all time-sensitive prerequisites then. Candidate runtime/DB
validation while active, first candidate worker success, native four-hour issuance,
new dependency identities and subsequent scoring eligibility remain **unverified**.
The next native issuance on the unchanged old release is expected at
**20:01 UTC**, outside this observation window; no
unscheduled cycles or artificial records are permitted. The next regular restore
drill is **25 October 06:00 UTC**. No automation or second attempt was started.

Only report/prompt documentation changed locally. No application code, schema,
production volume, historical evidence, credentials, persistent unit definitions,
backup policies or AWS configuration changed. No migration, model fitting,
historical replay, manual worker cycle, cleanup, website deployment, commit or push
was performed.

Local documentation validation: repository-wide Ruff lint/format passed
(**229 files already formatted**); whitespace, local Markdown links and verbatim
prompt comparison passed. No application test suite or research replay was run
for these documentation-only repository changes; the five temporary procedure
recovery tests above used mocks, not production failure injection.

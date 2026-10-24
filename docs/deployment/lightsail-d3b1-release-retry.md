# Stage D3B.1 — Corrected Lightsail promotion

**Result: PROMOTION SUCCESSFUL.** One additional authorised attempt activated the
prepared candidate on **24 October 2026**. No rollback or further retry occurred.
All times below are UTC. See the [original request](../../prompts/deployment/005-lightsail-release-promotion-retry.md),
[D3A review](lightsail-d3a-release-reconciliation.md) and unchanged
[D3B incident report](lightsail-d3b-release-promotion.md).

## Release and recovery prerequisites

| Item | Verified value |
| --- | --- |
| Previous active SHA, retained for recovery | `e0d622d51e1edc120fb4f1b5229e46907ed6219d` |
| New active SHA | `cceb6509edbb6e6a9fb577c112bf9c648e81c5a1` |
| Exact active directory | `/opt/backtest-badger/releases/cceb6509edbb6e6a9fb577c112bf9c648e81c5a1` |
| Candidate preparation time | `2026-10-24T16:32:18.288027+00:00` |
| Candidate deployment-manifest SHA-256 | `1feb0203b2d1aef8597a72be88bca77f490dec7dbb4c5a19957eaaa090a41da6` |
| CI, rechecked through GitHub API | [40106649560](https://github.com/owencrew/backtest-badger/actions/runs/40106649560), exact candidate SHA, `completed / success` |

Readiness checks began at **20:56:50**. Both release HEADs, tracked files,
preparation manifests, all recorded input hashes (27 old / 52 candidate), installed
lockfile versions and persistent artifacts links passed. Both use Python **3.12.15**.
The candidate was reused without preparation, installation or source changes;
newer documentation commits were not deployed.

PostgreSQL **17.11** was healthy, explicit read-only SQL returned Alembic **0001**,
NTP was synchronised, and root disk had **69 GiB free**, **10% used**. All six
scheduled services had successful latest completions; worker unit/timer files
matched repository templates. Backup, retention and restore were inactive; no
pause marker, competing lock holder or concurrent release operator was observed.
The 20:56 collection and 20:57 scoring runs had finished before the pause.

- **Backup:** `checkpoint-20261024T024008Z`, completed **02:40:29**, snapshot
  `cd970a1e7cb17fc2a20d8cf3f11ace5d76ced7f79f6f11bbcb566ed36519464d`.
  All nine bundle hashes passed again. Read-only restic `--no-lock --no-cache`
  inventory confirmed the snapshot and age under 24 hours. Its scheduled journal
  confirmed successful upload and completion-receipt publication.
- **Restore:** retained `20261018T060003Z/result.txt`, `PASS` at
  **18 October 06:00:15**, still within seven days, snapshot
  `44b3a0709ff6f33ab3a2d487040c78d7a7eeb77e4057ddefe0670071bd6ab167`.
  Bounded journal evidence confirmed nine hashes, exact source/restored fingerprints,
  integrity checks and isolated-resource cleanup: 2 markets, 40,114 candles,
  0 revisions and 1 Alembic row. This validates that older snapshot, not restoration
  of today's backup. No manual backup or restore was run.
- Both releases accepted retained evidence: **124 scored, 2 pending, 0 mature
  unscored**, no invalid evidence, missed horizons, worker failures, incomplete
  cycles or partial journals. One pre-existing late issuance per market remains.

## Corrected execution and recovery path

The temporary helper is now `release_audit.py`, invoked with **`python -P -B`**.
The existing procedure was reused with a separate temporary directory,
`/run/backtest-badger-d3b1-20261024/`; original D3B scripts, state, journal and
local incident report were preserved. Their recorded script/report hashes remain
unchanged. No permanent deployment scripts or systemd unit definitions were changed.

Before pausing anything, `/bin/bash .../promote.sh --preflight` executed the actual
staged validation functions. For **each exact release directory**, it invoked:

```text
sudo -u ubuntu RELEASE/.venv/bin/python -P -B /run/backtest-badger-d3b1-20261024/release_audit.py
```

The helper confirmed UID **1000**, the exact working directory/interpreter,
`sys.flags.safe_path = true` and `inspect.__file__` in the Python **3.12** standard
library. Both real invocations passed. The same old-release checks used by recovery
were therefore exercised in their actual context, without production fault injection.

Both runtime validators and DB health also passed before the pause, using transient
systemd checks as `ubuntu:ubuntu`, `WorkingDirectory=/opt/backtest-badger/current`,
`EnvironmentFile=/etc/backtest-badger/worker.env` and
`PYTHONDONTWRITEBYTECODE=1`. These same commands ran under the old release in the
critical section and then under the active candidate:

```text
.venv/bin/python -P -B ops/lightsail/validate.py runtime --worker collection
.venv/bin/python -P -B ops/lightsail/validate.py runtime --worker scoring
.venv/bin/badger db-health
```

All exited successfully. Each validator reported private configuration, release,
dependencies and persistent paths validated; DB health reported
`PostgreSQL connectivity OK.` No worker cycle was invoked by these checks.

The actual root-only evidence guard also ran before pause with
`/usr/bin/python3 -P -B`, capturing and verifying **250 original forecast/outcome
JSON files** and a schema-dump fingerprint. Shell syntax and five local mocked
failure scenarios passed, supplementing these real staged-command tests.
Preflight completed at **20:58:13.065362745**, without timer changes.

## Promotion timeline and evidence preservation

The same guarded Bash procedure ran through a transient supervisor, independent
of SSH connectivity. It held the existing backup lock throughout pause, validation
and resume. EXIT/HUP/INT/TERM handling retained the old-runtime verification and
source-only rollback path; unsafe recovery would leave workers explicitly paused.

| Time on 24 October | Event |
| --- | --- |
| `20:58:33.280685808` | Shared backup lock held; final prerequisites passed |
| `20:58:33.283396235` | Collection/scoring pause requested |
| `20:58:33.308651090` | Timers paused; workers drained |
| `20:58:48.203002841` | Atomic switch completed and exact candidate target confirmed |
| `20:58:57.151267315` | Candidate runtime, DB, offline evidence and preservation checks passed |
| `20:58:57.173874698` | Both timers resumed |
| `20:58:57.180022138` | Supervisor completed successfully, exit 0; lock released |

The pause lasted approximately **23.9 seconds**, between scheduled ticks; no tick
was due during it. Both timers remained enabled. Other scheduled services were
not paused or changed. The original release and runtime remain available.

All **250** original forecast/outcome files retained their exact SHA-256 hashes.
The schema-only dump fingerprint remained
`cbf58a059d554f8d3ea9aa4e7a224959b537197d2e0ad5c9e50b84f6507507cb`;
the comparison excludes PostgreSQL's random `restrict`/`unrestrict` tokens.
Read-only SQL after activation again returned Alembic **0001**. No database migration,
data repair, historical rewrite or artifact replacement occurred.

## Scheduled observations and provenance

Final scheduled-worker/evidence observation: **21:02:19–21:02:28 UTC**.

- Natural collection: **21:01:01–21:01:06**, `success`, exit **0**.
- Natural scoring: **21:02:02–21:02:12**, `success`, exit **0**.
- Final **21:03:01 UTC** check: PostgreSQL healthy, Alembic **0001**, exact
  candidate active, backup lock released and backup pause marker absent.
- Both timers active/enabled; next ticks **21:06 / 21:07**, all six timers scheduled.
- Candidate integrity and offline evidence checks passed: **124 scored, 2 pending,
  0 mature unscored**; no invalid evidence, missed horizons, failures, partials or
  incomplete cycles. The scorer's normal bounded cursor deferred 26 records;
  the complete inventory confirms this is not a mature-unscored backlog.
- The preservation guard passed again after those runs: all **250** original
  forecast/outcome file hashes and the schema fingerprint still match.
- A separate metadata-only read confirmed latest issuance at **20:01:10** (BTC)
  and **20:01:20** (ETH), both before promotion, retaining the old dependency hashes.
  There were **zero** post-promotion forecasts at inspection, as expected before
  the next native four-hour boundary. No private forecast values were exported.

The candidate adds **cryptography 46.0.7, cffi 2.1.1 and pycparser 3.11**; existing
package versions and scientific worker code remain unchanged. New forward recipes
hash these dependency files:

| File | Candidate SHA-256 |
| --- | --- |
| `uv.lock` | `c72f46f950e71665b8b490c975aa1119c5fee09006a1fb1d2a6bf0f9fb17403f` |
| `pyproject.toml` | `7be2cab2bec6ef6325e25c4f85c4ecc0be746bf015689fec32a6ad68fa2176ec` |

The latest four-hour issuance predates activation. **Pending follow-up:** observe
the next native issuance, expected **25 October 00:01 UTC**, and compare each new
record's `model.dependency_files_sha256` against the hashes above. Its target closes
at **04:00 UTC**; earliest scoring eligibility is **04:01 UTC**, with the first
scheduled scoring check at **04:02 UTC**. These future events and new forecast
identities are **not verified** by this session. Keep both originating runtimes for
exact replay; never rewrite older provenance or backfill missed opportunities.
The regular restore drill remains scheduled for **25 October 06:00 UTC**.

There was no new operational incident or rollback. The historical D3B failed
supervisor is intentionally retained as incident evidence. No manual prediction or
scoring cycles, historical research, application changes, dependency installation,
backup/monitoring changes, permanent infrastructure, website deployment, commit or
push occurred. The prompt was archived verbatim; production/handoff documentation
was updated only after successful activation.

Local validation: five mocked recovery scenarios, shell/Python syntax, real remote
preflight and runtime checks above; repository-wide Ruff lint and format passed
(**231 files already formatted**). Local Markdown links/whitespace, verbatim prompt
comparison and the unchanged D3B report hash passed. No application pytest suite
was rerun for these documentation-only repository changes.

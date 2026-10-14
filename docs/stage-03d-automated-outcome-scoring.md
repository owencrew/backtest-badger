# Stage 3D — Automated forward outcome scoring

Stage 3D adds independent orchestration around the unchanged Stage 3C `score()`
API. It uses the [frozen protocol](stage-03c-forward-evaluation-protocol.md), the
original forecasts and the existing local development configuration. The operator
had already scored four genuine BTC/ETH observations before this implementation,
including two timely automated observations. Those outcomes are preserved.
The new five-minute LaunchAgent is **opt-in and is not installed or enabled**.

## Commands

Run from `/Users/owencrew/Code/backtest-badger`:

```sh
# One bounded cycle; only eligible, unscored records can require PostgreSQL.
uv run --locked --env-file .env python -m backtest_badger.forward_scoring_operations cycle

# Offline; no configuration, database, provider or model work.
uv run --locked python -m backtest_badger.forward_scoring_operations status

# Existing Stage 3C descriptive metrics, unchanged.
uv run --locked python -m backtest_badger.forward_evaluation report
```

There are no CLI clock, date, path, batch, model or protocol overrides. Production
uses actual aware UTC timestamps, with reversal checks across the cycle and inside
the scorer. Python injections exist for isolated synthetic tests only. Run the
module from the project root so Stage 3C can locate its pinned protocol and code.
The scorer rejects non-loopback database hosts. Keep `.env` pointed at the local
development database; do not use production or tunnels.

## Selection, maturity and recovery

Each cycle discovers the prediction directory's JSON files across both markets
and visits at most **100 files**. A persisted filename cursor rotates through this
inventory, wrapping at its end. Every visited file consumes a slot, including
invalid, pending and already-scored records. Files beyond the bound remain queued;
`deferred_count` records their number. Nothing is permanently marked done in the
queue. A checkpoint is durably advanced **before each attempt**, so a repeatedly
failing, missing-target or interrupted record cannot monopolise later cycles.
Records added behind the cursor are visited after wrapping; older genuine records
remain eligible indefinitely. Queue position is not scientific evidence.

For each visited file the existing Stage 3C scorer validates original evidence,
checks any existing outcome, applies the frozen target maturity rule, and only
then opens a connection if necessary. An occupied outcome is semantically checked
against its original prediction and retained target; it is never rescored. An
unexpired target returns `pending_not_settled` without loading DB configuration.
A mature target absent from PostgreSQL returns `pending_target_missing`; subsequent
cycles retry it. No provider request, database mutation, refresh, forecast creation,
model fit or historical holdout access occurs in the scoring process.

For source 12:00 UTC, target close is 20:00 and maturity is **20:01 UTC**. The
collector and evaluator have independent schedules. If scoring runs before the
collector refreshes that target, pending is the expected result. Older mature
forecasts can be scored after downtime; no missed prediction is invented.
The first valid outcome's captured target version and cohort remain immutable.

The entire discovery/processing phase has a **240-second POSIX alarm**, independent
of the UTC evidence clock. On expiry the active attempt is recorded as failed,
unvisited files stay deferred and the next cycle resumes after the checkpoint.
The existing scorer also uses connection and SQL timeouts. Final operational
writes occur after cancelling the alarm. This is a main-thread, single-machine
POSIX implementation; signals cannot guarantee a hard deadline during an
uninterruptible kernel/filesystem operation. Very large inventories and journal
histories increase discovery, validation and status costs. Retained evidence is
never automatically pruned; review capacity if a rotation becomes too slow.

## Idempotency and failure visibility

A nonblocking `flock` on
`artifacts/forward-scoring-operations/.cycle.lock` prevents overlapping evaluator
cycles. It is independent of the collector's lock. Never delete or replace the
lock file while any evaluator might run. Process exit or termination releases it;
its continuing existence is normal. Manual Stage 3C scoring can race an evaluator;
Stage 3C's existing atomic exclusive outcome publication still permits one winner.

Each invocation gets a UUID journal under the separate gitignored
`artifacts/forward-scoring-operations/`. It records actual cycle and attempt times,
per-file `scored`, `already_scored`, `pending`, `failed` and `skipped` results,
fixed diagnostic categories, invalid collector-journal counts and deferred counts.
It does not copy targets, predictions, metrics, raw exception messages, connection
settings or secrets. Operational snapshots and the small `state/cursor.json` use
checksums, private temporary files, file fsync, atomic replace and directory fsync.
Only operational state is replaced. Outcome and forecast JSON are never replaced.

An initial journal failure prevents scoring. Later journal failures make the cycle
unsuccessful but permit unrelated records to be attempted. A cursor write failure
stops the batch with an explicit skipped result, preserving the fairness safeguard.
A malformed cursor fails visibly and is not automatically repaired. Failed staging
writes can leave `.partial` files, which status discloses. A killed process can
leave a `running` journal. Neither a partial file nor an operational success claim
substitutes for a validated immutable outcome. If publication succeeded just before
interruption or a durability error, retry validates that existing outcome offline.

Cycle exits: **0** for a completed batch without failures (pending and deferred work
are allowed); **1** for failed work, invalid collector journals returned by the
scorer, clock/timeout or operational-write failures; **2** for overlap or argument
errors. Per-record exceptions do not prevent unrelated records from being visited.
No immediate restart loop is configured; retry occurs at the next scheduled tick.

## Offline status and operator inspection

`status` shows the latest successful completed cycle and its status counts, latest
cycle, current valid scored filenames, pending unexpired predictions, mature
unscored predictions, historical failures with fixed categories, incomplete cycles,
invalid predictions/outcomes/collector journals/scoring journals/cursor, orphan
outcomes and partial-file counts. An error-free completed cycle can contain only
pending or already-scored records; its timestamp does not imply a new publication
or an empty backlog. `mature_unscored` means target availability is **unknown
offline**, not that PostgreSQL is missing a candle.

Status reuses Stage 3C prediction/outcome validators and never computes new metrics.
It validates operational checksums, shape and timestamps before reporting success.
Exit 1 indicates invalid/partial evidence or incomplete cycles; exit 0 indicates a
valid inventory. Historical completed failures remain listed even after recovery
and do not alone force status exit 1. Inspect `failures`, latest cycle and outstanding
work as well as the exit code. A running journal may be active or interrupted;
check launchd/process state before deciding. No automatic acknowledgement, deletion,
repair or external notification is provided. Hashes and local clocks are not
independent attestations against an owner rewriting evidence.

## Opt-in macOS scheduling

The example is `ops/launchd/com.backtestbadger.forward-scoring.plist`. It uses
`/opt/homebrew/bin/uv`, the explicit project and `.env` paths, `--locked --no-sync
--offline`, a 300-second interval, `RunAtLoad`, separate local logs and decimal
umask 63 (octal 077). Adapt every absolute path if using another checkout. Launchd
does not expand shell variables in plist strings. Dependencies must already exist.
The evaluator neither relies on nor controls the prediction collector's schedule.

These are **operator instructions, not installation performed by Stage 3D**:

```sh
cd /Users/owencrew/Code/backtest-badger
command -v uv
uv sync --locked
mkdir -p artifacts/forward-scoring-operations/logs "$HOME/Library/LaunchAgents"
chmod 700 artifacts/forward-scoring-operations artifacts/forward-scoring-operations/logs
chmod 600 .env
plutil -lint ops/launchd/com.backtestbadger.forward-scoring.plist
cp ops/launchd/com.backtestbadger.forward-scoring.plist \
  "$HOME/Library/LaunchAgents/com.backtestbadger.forward-scoring.plist"
chmod 600 "$HOME/Library/LaunchAgents/com.backtestbadger.forward-scoring.plist"

# Starts a cycle immediately; no sudo.
launchctl bootstrap "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.backtestbadger.forward-scoring.plist"
launchctl print "gui/$(id -u)/com.backtestbadger.forward-scoring"
# Optional request without terminating a running cycle; do not use kickstart -k.
launchctl kickstart "gui/$(id -u)/com.backtestbadger.forward-scoring"
uv run --locked python -m backtest_badger.forward_scoring_operations status
tail -n 80 artifacts/forward-scoring-operations/logs/stdout.log
tail -n 80 artifacts/forward-scoring-operations/logs/stderr.log

# Stop/unload only the evaluator, then inspect interrupted-cycle evidence.
launchctl bootout "gui/$(id -u)/com.backtestbadger.forward-scoring"
# Optional: prevent loading again at login by removing only its installed plist.
rm "$HOME/Library/LaunchAgents/com.backtestbadger.forward-scoring.plist"
```

Restart by bootstrapping the retained installed copy, or recopy it after removal.
If previously disabled, use `launchctl enable` for this evaluator's GUI-domain label
before bootstrap. Do not stop or change `com.backtestbadger.forward-collection`
during ordinary evaluator maintenance. Sleep, logout, shutdown and unavailable
Docker/PostgreSQL delay evaluation. Unlike prediction issuance, eligible scoring
can catch up after waking. This remains a development Mac, not guaranteed 24/7
infrastructure. Logs/journals accumulate. To rotate console logs, stop the evaluator,
move stdout/stderr to dated files, then restart; preserve the JSON evidence.

## Recovery and backups

For database failures, restore the existing local development service/configuration
and retry a cycle. For missing targets, allow the independent collector to refresh;
older market-data gaps require the existing separately authorised ingestion recovery
procedure. The evaluator will not fetch them. For invalid forecasts or outcomes,
preserve the files and investigate against trusted backups; never remove an outcome
to force rescoring. For partial/interrupted operations, retain evidence, inspect
process state, then retry. If the queue cursor is corrupt, stop the evaluator and
preserve its bytes in a dated incident backup before an operator moves only
`state/cursor.json` aside. Its absence restarts traversal from the beginning without
altering scores; no immutable prediction, outcome or cycle journal should be moved
or rewritten as routine recovery.

**Future forward-evidence backups must include all four directories below.** This
supersedes the two-directory example in the historical Stage 3B guide. A coherent
backup requires pausing both scheduled jobs and any manual writers during the
operator's chosen maintenance window, then restarting both. No collector stop or
backup installation is performed by this implementation.

Use a new empty staging directory at an approved destination, excluding `.env`:

```sh
cd /Users/owencrew/Code/backtest-badger
backup_dir="/absolute/path/to/new/backup-staging"
mkdir "$backup_dir"
find artifacts/forward-predictions artifacts/forward-outcomes \
  artifacts/forward-operations artifacts/forward-scoring-operations -type f \
  -exec shasum -a 256 {} + > "$backup_dir/files.sha256"
tar --format=pax -cpf "$backup_dir/forward-evidence.tar" \
  artifacts/forward-predictions artifacts/forward-outcomes \
  artifacts/forward-operations artifacts/forward-scoring-operations
(cd "$backup_dir" && shasum -a 256 forward-evidence.tar > archive.sha256)
```

Preserve the frozen protocol, matching source revision plus uncommitted patch,
`pyproject.toml`, `uv.lock`, runtime information and pinned training artifacts for
replay. Retain acquisition evidence separately under the established backup policy.
Copy encrypted dated backups off-machine using the operator's approved tool, keeping
multiple versions without propagating deletions into the only copy. Restore into a
new empty directory; never extract over live evidence:

```sh
cd /absolute/path/to/backup-copy
shasum -a 256 -c archive.sha256
mkdir restored
(cd restored && tar -xpf ../forward-evidence.tar && shasum -a 256 -c ../files.sha256)
```

Use the matching implementation's Stage 3C offline report with explicit restored
prediction/outcome/collector paths to validate scientific evidence. The Stage 3D
Python status API accepts isolated directories; its production CLI intentionally
has no path overrides. Preserve incomplete or corrupt evidence as incident history;
no automatic clean-up or backup service is added.

## Verification and boundaries

New synthetic tests cover maturity edges, both markets, multiple pending targets,
DB failure isolation, no-DB idempotency, invalid predictions/outcomes/journals,
partial writes, cursor recovery, clock reversals, bounded backlog rotation,
process overlap/termination and interrupted publication. A real Stage 3C scorer
integration test creates synthetic targets in a disposable PostgreSQL 17 database,
checks READ ONLY / REPEATABLE READ and exact target queries, retries missing targets,
then proves forecasts, targets, revision counts and existing scores are unchanged.
Tests never access live Binance or the development database.

The original collector's installed plist, repository plist and implementation,
all pre-existing package modules, dependency files, frozen protocol, predictions,
outcomes and completed collector journals are checked against a pre-change
SHA-256/size/mtime inventory. The collector continues independently and can append
new journals and forecasts. No historical holdout, fixed model, metric, scientific
validator or outcome schema is changed. No new dependencies, migration, trading,
paper trading, notifications, website, deployment, commit or push are included.
This implementation stops after Stage 3D.

### Executed verification on 2026-10-14

**856 tests passed, zero skipped**: all 817 pre-existing tests plus 38 new unit
cases and one new PostgreSQL integration case. The full suite used only the
disposable localhost:55439 PostgreSQL 17 container and its randomly named test
databases. The focused new unit suite passed separately. Ruff lint, Ruff formatting,
`git diff --check` and `plutil -lint` passed. The temporary test container was
removed after testing. No live Binance request was made by automated tests.

A genuine cycle at **20:25:34 UTC** (run
`7565889933e64053b336338162ba29b8`) completed successfully: six files visited,
four `already_scored`, two `pending_not_settled`, zero new scores, zero failures and
zero deferred files. These branches required no database connection. Offline
status validated all six predictions and four outcomes, with no invalid or partial
evidence. The source-16:00 predictions mature at 00:01 UTC on October 15.
Only new scoring-operation evidence was written by that cycle.

All **98 pre-existing files** in the preservation inventory retained identical
SHA-256, size and nanosecond mtime: existing package modules, dependency files,
frozen protocol, installed/repository collection plists, original forecasts,
outcomes and inventoried collector journals. The supplied prompt archive matches
byte for byte. A read-only launchd inspection found the collection job still loaded,
with 50 runs and last exit code 0; it was idle between scheduled invocations.
The original live prediction collector remained unchanged and was never stopped,
reloaded or reconfigured. The new scoring plist is not installed or enabled.

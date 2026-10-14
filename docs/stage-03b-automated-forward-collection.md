# Stage 3B — Reliable automated forward collection

Implemented for review on 2026-10-14. The opt-in collector produces unscored
BTCUSDT and ETHUSDT observations using the existing Stage 3A recorder and verifier.
It does not score outcomes, inspect holdout performance, change models or trade.
The fixed five features, four models and pinned pre-2024 training sample remain
unchanged. No new dependency, database schema, deployment or external service is
introduced. The LaunchAgent example is **not installed or enabled**.

## Commands and timing

From the project root, with the existing local development `.env`:

```sh
uv run --locked --env-file .env badger forward-cycle
uv run --locked badger forward-status
```

`forward-cycle` checks the actual aware UTC clock. There are no CLI clock, date,
source, output, horizon or deadline overrides. Python injection is for synthetic
tests only. Database configuration is loaded only for a market requiring work;
non-loopback database hosts are refused. Keep `.env` pointed at the existing
Backtest Badger development database; do not use production connections or tunnels.
`forward-status` is offline and needs neither `.env` nor PostgreSQL.

Native UTC close boundaries remain 00:00, 04:00, 08:00, 12:00, 16:00 and 20:00.
For a source candle opening at 08:00:

| Actual UTC time | Collector behaviour when no record exists |
| --- | --- |
| 12:00:00 through 12:00:59.999999 | `not-yet-eligible`; no configuration, database, provider or model work |
| 12:01:00 through 12:15:59.999999 | Refresh, validate, record and verify while still timely |
| 12:16:00 onward | `missed`; no late forecast is generated |
| 16:00:00 | Consider the next source candle, initially still settling |

The permitted window is `[feature_available_at, feature_available_at + 15 minutes)`.
The exact deadline is excluded. The cycle fixes one source identity at entry; a
slow first market cannot cause the second to silently switch horizons. Clock checks
before recording, throughout Stage 3A capture/calculation and immediately before
exclusive publication reject expiry and sampled reversals. A refresh already in
flight can finish after the deadline; its database observations remain valid market
data, but the cycle cannot publish a late forecast. The final deadline parameter
is optional in the Python recorder; existing manual recording semantics remain.

Successful diagnostics retain the actual `issued_at` and seconds since feature
eligibility, including fractional seconds. Stage 3A defines issuance as the real
post-calculation issuance decision immediately before writing the staging file;
the final guard separately checks time immediately before linking it. Local clock
correctness is still an assumption, and OS suspension between the check and link
cannot be made atomic with wall time. This is not independently witnessed timing.

## Collection, idempotency and recovery

The collector obtains a nonblocking POSIX `flock` on
`artifacts/forward-predictions/.cycle.lock`. All cycles targeting that directory
share the lock. Never delete or replace its inode while collection could be active.
Process exit, including termination, releases the lock; the empty file may remain.
An overlapping invocation records `collection_busy` and exits 2 without waiting,
provider requests or fits. Launchd itself also avoids a second instance of its job.
The filesystem lock is a single-machine safeguard, not a distributed lock.

For each market independently:

1. An occupied record identity is checked first, even after the collection deadline.
   Valid checksum/identity/timing evidence yields `already-recorded`, with no
   configuration load, database connection, provider request or model fitting.
   Invalid evidence fails visibly and is never overwritten or removed.
2. While timely, the existing `sync_recent` performs its bounded seven-day overlap
   and up-to-30-day automatic catch-up. The cycle requires successful complete
   provider and stored grids, no failed/incomplete pages, a fresh exact horizon and
   refresh timestamps belonging to this run. A fresh tail alone is insufficient.
3. The existing `record_forward` reads and validates the seven exact source rows,
   fits only the fixed frozen training data, and publishes all four forecasts using
   Stage 3A's synced staging file and exclusive atomic hard link. Manual writers
   do not take the cycle lock, but the existing exclusive link still prevents any
   overwrite if a manual command races collection.
4. `verify_forward` performs full retained-input and deterministic model replay of
   the newly published record. Verification failure is recorded as a failure; the
   immutable forecast remains present for inspection.

Provider, configuration, database, missing-source, prediction, verification and
file errors are isolated per market. An ordinary BTC failure does not prevent the
ETH attempt. Transient failures retry on a later invocation only while that exact
horizon is timely. Existing provider/socket/page bounds and database timeouts apply.
HTTP 418/429 creates a small shared provider pause under
`artifacts/forward-operations/state/provider-pause.json`, respecting numeric or HTTP
date `Retry-After` across markets and restarts. While paused, each due market records
a failure without another provider call. Missing/invalid/past retry information
requires operator review: stop the agent, inspect the original REST manifest and
only remove that pause file when the provider permits requests again. Historical
cycle evidence stays intact. Ordinary transport errors do not impose this pause.

Exit statuses are 0 for recorded, already-recorded or settling-only cycles; 1 for
any missed horizon, failed action or journal failure; 2 for an overlapping process
(or argparse usage error). A future successful cycle does not erase earlier failures.
The scheduler waits for its next five-minute tick after an ordinary process failure;
there is no immediate restart loop.

## Operational evidence and status

Separate gitignored `artifacts/forward-operations/` contains one small UUID-named
JSON journal per invocation, shared provider pause state, and optional launchd logs.
The journal is first synced with `state=running` and per-market
`interrupted_or_in_progress` outcomes, then atomically replaced after each market
and on completion. Journals include UTC start/finish times, source identity,
eligibility/deadline, market status, refresh outcome, fixed error category, and
record path, content checksum, exact-file checksum and issuance latency when known.
Complete source rows, model recipes and forecasts are not duplicated into journals.
Raw exception messages, database settings and provider response headers are not
printed by this command. Original REST acquisition evidence remains under
`artifacts/rest/` according to Stage 1C.1.

An initial journal write failure stops collection before any provider or model
work. Later journal failure makes the command fail, while preserving an earlier
complete snapshot and still attempting the other market. A crash can leave a
`.partial` file or `running` journal. Neither is evidence that a forecast was issued.
Status reports incomplete/unreadable journals and counts partial journal files.
Inspect these after checking whether a collector is still running; partial files
are never promoted automatically. A record published before a crash wins on retry,
even if verification or its operational journal was interrupted.

`forward-status` reports per market:

- Latest integrity-checked prediction and its actual issue latency.
- Latest successful replay recorded by a cycle, separately from checksum checks.
- Most recent cycle, failure count and latest failed attempt.
- Missing expired horizons on the native grid since the first retained cycle.
- Late manual records in that monitored range and invalid record files.

Downtime gaps are inferred from the earliest retained cycle through the actual
current clock, so sleeping through entire horizons is visible without backfilling.
Before the first cycle, monitoring has not started and no historical missing grid
is assumed. Keep journals to preserve that baseline. A missing or invalid forecast
is an absent observation, never a zero-return forecast. Late manual records remain
genuine manually issued observations but do not become timely automated ones.

`integrity_only` explicitly means checksum, identity and timing checks, **not full
model replay**. Existing records must be skipped without re-fitting, and their
recorded code/runtime may differ from today's checkout. If a crash or failed replay
requires investigation, use `verify-forward --record PATH` with the original pinned
training bytes, source revision and runtime in a separate checkout. The latest
successful replay can be null even when an existing record passed verification
before Stage 3B. The original Stage 3A schema and files are unchanged.

## Opt-in macOS LaunchAgent

The example is `ops/launchd/com.backtestbadger.forward-collection.plist`. It uses
this machine's explicit `/opt/homebrew/bin/uv` and
`/Users/owencrew/Code/backtest-badger` paths, an absolute `.env` path, the project
working directory and `StartInterval=300`. Adapt **all** paths for another checkout
or user; launchd does not expand `~` or shell variables in plist strings.
No database credentials are stored in the plist. Umask 63 is decimal for octal 077.

First prepare dependencies interactively with `uv sync --locked` and ensure Docker
Desktop and the existing development PostgreSQL service are available. The job uses
`--no-sync --offline` to avoid unattended uv package downloads or environment
updates; these flags do not disable Python's Binance requests. The existing `.env`
is loaded by uv, with inherited environment taking precedence as usual.

The following commands are operator instructions, **not executed by this stage**.
Installing/loading the example starts collection immediately (`RunAtLoad=true`):

```sh
cd /Users/owencrew/Code/backtest-badger
command -v uv  # confirm it matches the plist
uv sync --locked
mkdir -p artifacts/forward-operations/logs "$HOME/Library/LaunchAgents"
chmod 700 artifacts/forward-operations artifacts/forward-operations/logs
chmod 600 .env
plutil -lint ops/launchd/com.backtestbadger.forward-collection.plist
cp ops/launchd/com.backtestbadger.forward-collection.plist \
  "$HOME/Library/LaunchAgents/com.backtestbadger.forward-collection.plist"
chmod 600 "$HOME/Library/LaunchAgents/com.backtestbadger.forward-collection.plist"

# Install/start in the logged-in user's GUI domain; no sudo.
launchctl bootstrap "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.backtestbadger.forward-collection.plist"

# Request a run without killing an existing run. Avoid kickstart -k.
launchctl kickstart "gui/$(id -u)/com.backtestbadger.forward-collection"

# Inspect scheduling, process state and last exit status.
launchctl print "gui/$(id -u)/com.backtestbadger.forward-collection"
uv run --locked badger forward-status
tail -n 80 artifacts/forward-operations/logs/stdout.log
tail -n 80 artifacts/forward-operations/logs/stderr.log

# Stop/unload. A running process may be terminated; inspect its journal afterward.
launchctl bootout "gui/$(id -u)/com.backtestbadger.forward-collection"

# To prevent loading at a later login, also remove the installed copy.
rm "$HOME/Library/LaunchAgents/com.backtestbadger.forward-collection.plist"
```

Restart by copying and bootstrapping again, or bootstrap the retained installed
copy after a temporary stop. If the operator previously used `launchctl disable`,
first use `launchctl enable gui/UID/com.backtestbadger.forward-collection` with the
actual UID. Routine runs need no open terminal. Inspect status regularly; no
external notifications are configured. Logs and journals accumulate locally.
To rotate console logs, bootout, move stdout/stderr to dated filenames, then
bootstrap; preserve the cycle JSON history. Do not remove the prediction directory
or its lock file to fix a failed run.

The interval is independent of London daylight-saving time. According to the local
macOS `launchd.plist(5)` manual, `StartInterval` firings while asleep or already
running are missed. Sleep, shutdown, logout, unavailable Docker/PostgreSQL, network
failure and slow work can all prevent prompt collection. The next invocation uses
actual UTC time, never a scheduled historical timestamp. LaunchAgents run in the
user session, and this setup is **not a guarantee of 24/7 collection**.

## Off-machine backups and verification

No cloud account, credentials, remote destination or backup service is configured.
Choose an approved encrypted external disk or remote backup destination yourself.
Stop the agent and any manual writers first so the snapshot is coherent. Preserve
both `artifacts/forward-predictions/` and `artifacts/forward-operations/` together.
For example, with an absolute, newly created local staging directory:

```sh
cd /Users/owencrew/Code/backtest-badger
backup_dir="/absolute/path/to/new/backup-staging"
mkdir -p "$backup_dir"
find artifacts/forward-predictions artifacts/forward-operations -type f \
  -exec shasum -a 256 {} + > "$backup_dir/files.sha256"
tar --format=pax -cpf "$backup_dir/forward-evidence.tar" \
  artifacts/forward-predictions artifacts/forward-operations
(cd "$backup_dir" && shasum -a 256 forward-evidence.tar > archive.sha256)
```

PAX tar retains original bytes, file permissions and timestamps where supported.
Copy the archive and both checksum files off-machine with the operator's existing
approved tool (for example, a timestamp-preserving file copy or `rsync -a`). Keep
multiple dated copies; do not synchronize deletions into the only backup. Do not
include `.env` or credentials. Also retain the recorded source revision plus any
uncommitted patch, `uv.lock`, `pyproject.toml`, the pinned Stage 2A training artifact
and required runtime information separately for deterministic replay. Retaining
`artifacts/rest/` additionally preserves the referenced acquisition evidence.

On a backup copy, check the tar hash, then extract into a **new empty directory**,
never over live prediction evidence:

```sh
cd /absolute/path/to/backup-copy
shasum -a 256 -c archive.sha256
mkdir restored
(cd restored && tar -xpf ../forward-evidence.tar && shasum -a 256 -c ../files.sha256)
```

This verifies every original file byte, including whitespace not covered by the
semantic record checksum. Run offline `verify-forward` on restored predictions
using their matching recorded implementation/runtime to verify scientific replay.
Hashes detect changes relative to a trusted backup inventory; they do not prove
independent historical publication or prevent an owner changing both copies.

## Validation and scope

The automated suite uses synthetic UTC clocks and mocked refresh/provider results.
New tests exercise all six daily boundaries, both eligibility edges, deadline
expiry during refresh and publication, actual Stage 3A fitting/recording/replay on
synthetic training fixtures, duplicate cycles, cross-process lock contention and
termination recovery, stale/incomplete source rejection, independent failures,
secret redaction, safe retries, shared throttling, interrupted verification,
atomic operational-write failures, downtime gaps, late manual records and CLI
argument restrictions. Existing mocked-provider parsing and disposable PostgreSQL
integration tests remain in the full suite. No test contacts Binance.

The actual offline status check on 2026-10-14 found the first two records issued at
14:40:49.118473 UTC (BTC) and 14:40:51.090524 UTC (ETH), both for source opening
08:00 UTC. These pre-existing manually issued observations are retained verbatim;
their issue delays are 9,589.118473 and 9,591.090524 seconds. They predate the
unattended promptness policy and must not be relabelled on-time. The user reported
both had passed Stage 3A replay. Stage 3B checked their integrity without refitting.
No new genuine forward record or live refresh was produced in this stage; the
actual clock was outside the unattended collection window.

Final verification: **705 tests passed, zero skipped** (528 unit tests and 177
PostgreSQL integration cases), including 65 new Stage 3B tests. Tests used a
separate disposable PostgreSQL 17 container on localhost port 55439; the fixture
created and removed only random test databases. The container was removed afterward.
Ruff lint, formatting (86 Python files), `git diff --check` and `plutil -lint` passed.
The exact prompt archive matches the supplied bytes. All **891 pre-existing
artifacts** retain their original SHA-256, size and nanosecond modification time.
No remote CI run or installed LaunchAgent execution is claimed.

Added: `src/backtest_badger/forward_operations.py`,
`tests/test_forward_operations.py`,
`ops/launchd/com.backtestbadger.forward-collection.plist`, this guide and
`prompts/stage-03-forward/002-automated-forward-collection.md`.
Modified: `src/backtest_badger/forward.py` (optional publication deadline),
`src/backtest_badger/cli.py`, README, architecture and roadmap. Existing `artifacts/`
ignore rules already cover operational evidence, so `.gitignore` is unchanged. No scheduler installation, commit, push, production access, audit, Field
Note, outcome evaluation, paper trading or subsequent stage is included.

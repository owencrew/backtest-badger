# Stage 1B.3 — Historical coverage and frozen research datasets

Current status and recovered acquisition results are recorded in the
[historical-anomalies follow-up](#follow-up--historical-anomalies-and-recoverable-acquisition-2026-10-13).
The earlier blocked-run section is retained as historical evidence.

This stage adds explicitly bounded native 4h monthly backfills for Binance Spot
BTCUSDT and ETHUSDT, stored-data coverage reports and frozen CSV exports. No schema
migration or dependency was added. The existing single-month importer, downloader,
checksum/parser and atomic conflict-rejecting persistence remain shared.

## Boundaries and initial month

The requested months are **2017-08 through 2026-09 inclusive**. The verified source
range starts at **2017-08-17 04:00 UTC** and ends at **2026-10-01 00:00 UTC exclusive**.
There are 19,991 expected native 4h identities per market in that range. October
2026 and periods outside this range are unverified by this stage.

Only August 2017 native 4h for these two supported markets receives the explicit
initial-boundary policy. It must contain exactly 89 ordered observations, starting
at the independently recorded Stage 1A first open and continuing every four hours
through August 31 20:00 UTC. Missing first/internal/last candles, duplicate or
unexpected identities fail. By default, every later month requires the full calendar grid.
The follow-up adds a separately opted-in source-gap policy.
The existing 1h single-month validator is unchanged. No pre-boundary candles are
invented; this source boundary does not prove that Binance had no earlier trading
outside the verified source. Coverage metadata retains the boundary and evidence.

Before live imports, September ZIP and checksum availability was checked with HEAD
requests. Public REST `startTime=0&limit=1&interval=4h&timeZone=0` checks independently
confirmed the boundary again for both markets. These bounded evidence checks are
not a REST ingestion implementation. Responses and acquisition times are retained
in ignored local artifacts.

## Commands

Run from the repository root with the existing local `.env`. Commands never migrate
or reset the database. Both endpoints must be explicit, completed UTC months;
range commands support only 4h and reject starts before the verified first month.
No command automatically extends the requested endpoint.

```sh
# Small range, with optional validation-only acquisition:
uv run --locked badger backfill-history --symbol BTCUSDT --interval 4h --start-month 2017-08 --end-month 2017-09 --dry-run

# Full requested backfill (run the second only after the first succeeds):
uv run --locked --env-file .env badger backfill-history --symbol BTCUSDT --interval 4h --start-month 2017-08 --end-month 2026-09
uv run --locked --env-file .env badger backfill-history --symbol ETHUSDT --interval 4h --start-month 2017-08 --end-month 2026-09

# One consistent report covering both markets; nonzero exit if incomplete:
uv run --locked --env-file .env badger coverage-report --symbol BTCUSDT ETHUSDT --interval 4h --start-month 2017-08 --end-month 2026-09

# Frozen bytes and manifest in a new, never-overwritten dataset directory:
uv run --locked --env-file .env badger export-dataset --symbol BTCUSDT ETHUSDT --interval 4h --start-month 2017-08 --end-month 2026-09 --dataset-id binance-4h-201708-202609-v1
```

`badger ingest-archive --symbol BTCUSDT --interval 4h --month 2025-01` continues to
work. Configuration, error redaction and health commands are preserved.

## Restart, conflicts and evidence

The range command processes one archive at a time in calendar order, with bounded
monthly parsing memory. Each month is an independent atomic transaction. A failure
stops immediately with a nonzero exit status, the failed month, inserted/unchanged/
conflicting/stale totals, failed-observation count and per-month manifest location.
Unknown observation counts remain null; an unavailable ZIP does not establish the
number of missing candles. Later months are not attempted after a failure.

Retry the same explicit range after investigating a failure. Every retry fetches
fresh bytes and records a fresh acquisition time; content-identical raw ZIP storage
can be shared without treating cached bytes as a new response. Already stored
identical observations retain economic values, accepted version and original
provenance; only a later confirmation watermark may advance. Changed valid or stale
changed rows fail the entire month's writes. Historical revisions are never accepted
by this command. Existing evidence is retained under the Stage 1B.2 conventions.

Interrupted runs can leave an `in_progress` manifest even if a commit reached the
server. Treat this as unresolved, inspect the stored grid and retry safely. A later
successful committed import resolves the earlier failed attempt for that month;
all attempt counts remain visible. Dry runs cannot resolve database imports. A
failure after database commit but before final manifest publication still returns
failure and must be investigated/retried. No filesystem/database atomicity is claimed.

Coverage checks read PostgreSQL under one read-only REPEATABLE READ transaction.
They compare expected UTC identities against stored rows with `generate_series` and
report exact missing timestamps, first/last opens, expected/actual counts, duplicate
identities, current versions and historical revisions. They also flag unexpected
stored rows before the August boundary. Local manifests separately report successful
and failed attempt counts, unresolved imports and unavailable months (HTTP 404).
A 404 is acquisition evidence, never proof of missing or nonexistent candles.
Unreadable manifests prevent a complete result. No prices or zero-volume bars are
invented. Missing manifests cannot establish whether acquisition was attempted;
stored continuity remains the primary data completeness check.

## Frozen export contract

`artifacts/exports/<dataset-id>/candles.csv` is UTF-8 CSV with LF line endings, a fixed
header and rows ordered by symbol then UTC open time. It contains venue, market type,
symbol, base/quote assets, interval seconds, open time, OHLC, base/quote volume,
trade count, taker-buy volumes, accepted version, original `observed_at`, source kind,
URL and ZIP SHA-256. Numeric fields use exact Decimal fixed-point strings without
floating conversion; timestamps use explicit UTC offsets. Confirmation watermarks,
export times and local database IDs are excluded from CSV bytes.

Both markets, coverage queries and the streamed CSV use **one read-only REPEATABLE
READ transaction**. A concurrent correction cannot split the exported snapshot.
The sibling JSON manifest records dataset ID, creation time, selections, half-open
UTC range, per-market first/last observations and row counts, completeness and missing
intervals, source/version policy, export schema version, Git revision/worktree status,
implementation module hashes and SHA-256 of the actual retained CSV bytes. Repeating
an export under a new ID with unchanged selected rows yields identical bytes/hash;
manifest timestamps can differ. Accepted database corrections do not alter frozen
files. Today's backfill does not reconstruct what Binance published at every past
instant or establish historical point-in-time availability.

Incomplete coverage or unresolved import evidence refuses export by default.
`--allow-incomplete` is an explicit acknowledgement: the manifest is labelled
`incomplete`, retains missing timestamps and records the acknowledgement. It never
silently drops a gap from the requested range. A duplicate dataset ID fails without
overwriting. Files are first written with `.partial` suffixes; the final manifest
is published last and denotes a completed export. A failed export may leave a
reserved directory/partial files for investigation; use a new ID for retry. Files
are protected from overwriting by this tool, not from an administrator editing them.

Local raw evidence, manifests, reports and exports remain gitignored. They are **not
yet durable off-machine backups**. No cloud storage or artifact database is added.

## Initial validation and observed live results (before the follow-up)

At the end of the initial implementation, **the full historical dataset was
blocked by invalid provider data**. Validation stopped without relaxing the parser or proceeding to
later full-range imports. No full-range or acknowledged partial export was created.

On 2026-10-13, September 2026 ZIPs and sidecars for both markets returned HTTP 200
for all four HEAD checks. Both fresh earliest-REST probes matched Stage 1A. Eight
bounded monthly imports (August 2017, December 2024, January 2025 and September 2026
for each market) passed checksums, UTC coverage and persistence. The January imports
returned 186 unchanged observations per market. Full BTC range execution then
reconfirmed August (89 unchanged) and stopped at September 2017. The subsequent
full ETH range command was not executed because the first command failed.

**Precise blocker:** BTCUSDT September 2017 has a valid ZIP checksum, but only
179 rows versus 180 expected. CSV row 34 opens at 2017-09-06 12:00 UTC; its raw close
timestamp is `1504713600000`, whereas the required inclusive millisecond close is
`1504713599999`. Adding the source tick yields 16:00:00.001 UTC, violating the
4h boundary. Independently inspecting all raw opening identities also finds
**2017-09-06 16:00 UTC missing**. The entire archive was rejected before database
access. We make no inference about the cause or the availability of unattempted
months. Source ZIP SHA-256:
`8c67b103846a595324073048da4e0a119a65dc6cc49764bfdf633ac4580fe1f6`.

An independent PostgreSQL `EXCEPT` grid audit agrees exactly with the coverage
report. Current rows span these first/last timestamps because the bounded checks
included September 2026; their span does **not** establish continuous history.

| Observed result | BTCUSDT | ETHUSDT |
| --- | ---: | ---: |
| Expected identities in requested verified range | 19,991 | 19,991 |
| Stored current rows / versions | 641 | 641 |
| Missing stored intervals | 19,350 | 19,350 |
| Duplicate identities | 0 | 0 |
| Historical revisions | 0 | 0 |
| Successfully stored distinct archive months | 4 | 4 |
| Stage 1B.3 successful import attempts (including repeats) | 5 | 4 |
| Stage 1B.3 failed archives | 1 | 0 |
| Unavailable months observed (HTTP 404) | 0 | 0 |
| Months without import evidence in the requested range | 105 | 106 |

For both markets, first stored open is **2017-08-17 04:00 UTC** and last stored open
is **2026-09-30 20:00 UTC**. Every stored candle remains version 1. The missing
stored counts include unattempted months and the rejected whole month; they do not
claim 19,350 provider-source gaps. The single confirmed source gap above is separate.
No availability assertion is made about the 105/106 unattempted months.

Stage totals: **9 successful archive imports, 1 failed archive**, 910 inserted
observations, 461 unchanged confirmations, zero conflicts/stale observations and
179 rejected rows. The initial 372 January rows retain all exact economic values,
versions, original observation/recording times and provenance; only confirmation
watermarks advanced. Comparison against the retained Stage 1B.2 audit verified all
3,348 economic fields using exact Decimal equality and original string precision.

The live full-range export command returned exit code 1 for incomplete coverage.
**Export filenames, rows and SHA-256: none**, because no dataset was published.
The incomplete-export option was exercised only with isolated synthetic test data;
it was not used to bypass the live blocker.

Local evidence (all ignored):

- `artifacts/stage-01b3-preflight.json`: availability, retained REST response
  references and the initial database baseline.
- `artifacts/stage-01b3-bounded.json`: eight successful bounded import results.
- `artifacts/stage-01b3-coverage.json`: complete per-market missing-interval lists
  and import evidence. Attempt totals there also include retained Stage 1B.2 runs;
  the table above counts this stage only.
- `artifacts/stage-01b3-audit.json`: independent SQL results and raw-source defect.
- `artifacts/stage-01b3-exact-january.json`: exact Stage 1B.2 preservation audit.
- `artifacts/manifests/ce127bb337084d6a8c083161cc816583.json`: failed September
  acquisition/validation manifest; its verified raw ZIP and sidecar are retained.

Final automated validation: **247 tests passed — 116 unit and 131 PostgreSQL
integration cases** on a separate disposable PostgreSQL 17 server. Ruff lint and
format checks passed. Tests use mocked/synthetic provider data. They cover the
listing boundary and internal gaps, ordinary partial-month rejection, UTC/year/leap
boundaries, missing full months, restart/idempotency, existing conflict rollback,
exact export decimals, deterministic bytes/hash, concurrent corrections to both
markets under one snapshot, refusal/acknowledgement of incomplete data, failed-file
publication and frozen-file preservation after corrections. CI was not run remotely.

The exact prompt was archived without changing prior prompts. Development schema,
Docker volumes and pre-existing observations were preserved. Resolving the source
defect requires a separately reviewed decision; this implementation neither accepts
the anomalous boundary nor fabricates the absent candle. Stage 1C was not begun.

## Scope and file inventory

Created: `src/backtest_badger/history.py`, `src/backtest_badger/research.py`,
`tests/test_history.py`, `tests/integration/test_research.py`, this guide and the
exact prompt at `prompts/stage-01-market-data/004-full-history-and-research-export.md`.
Modified: `src/backtest_badger/archives.py`, `src/backtest_badger/ingestion.py`,
`src/backtest_badger/cli.py`, `tests/test_ingestion.py`, `docs/architecture.md`
and `docs/roadmap.md`.

No native 1h history, daily archives, REST ingestion, scheduled jobs, automatic
historical corrections, research models, backtests, dashboard or deployment was
added. No production or historical-repository access, commit or push is part of
this work. Stop here for review before Stage 1C.

## Follow-up — historical anomalies and recoverable acquisition (2026-10-13)

This section supersedes the earlier blocked-run results above. The follow-up
preserves strict single-month ingestion and adds `backfill-history
--allow-source-gaps`. There are no new tables, dependencies, source-repair paths,
REST ingestion, schedules or Stage 1C work. The substantive request is archived at
`prompts/stage-01-market-data/005-historical-anomalies-and-backfill-recovery.md`.

### Bounded official-source investigation

At 11:24–11:25 UTC on 2026-10-13, 16 bounded public GET requests acquired two
monthly 4h ZIPs, four daily ZIPs, their six checksum sidecars, and four historical
REST responses. All requests used only `data.binance.vision` or
`data-api.binance.vision`; no keys or private endpoints were used. All six ZIP
checksums passed. Every REST query fixed `symbol=BTCUSDT`, `timeZone=0`, `limit=1000`
and one UTC day via inclusive millisecond `startTime`/`endTime`. Daily and REST
1h/4h rows agree exactly across the first eleven fields using Decimal/integer
comparison. No alternative-timeframe observations were persisted.

Exact raw responses, checksums, URLs, acquisition times and SHA-256 hashes are
retained in `artifacts/stage-01b3-followup-investigation/`. The offline fixture
`tests/fixtures/binance-historical-comparison.json` retains all returned rows for
both days and source provenance, so regression tests require no connectivity.
The September monthly SHA-256 equals the previously retained failed archive:
`8c67b103846a595324073048da4e0a119a65dc6cc49764bfdf633ac4580fe1f6`.

All identities below are `(Binance Spot, BTCUSDT, native interval, UTC open)`;
hour ranges enumerate each whole hour inclusively.

| Day / source | Returned 4h opens | Returned 1h opens |
| --- | --- | --- |
| 2017-09-06 monthly | 00:00, 04:00, 08:00, 12:00, 20:00 | Not requested |
| 2017-09-06 daily / REST | 00:00, 04:00, 08:00, 12:00, **16:00**, 20:00 | 00:00–16:00, 23:00 |
| 2018-06-26 monthly | 00:00, 12:00, 16:00, 20:00 | Not requested |
| 2018-06-26 daily / REST | 00:00, 12:00, 16:00, 20:00 | 00:00, 01:00, 12:00–23:00 |

**September:** the missing 16:00 identity *does* exist in the daily archive and
REST, but its raw close equals its own open (`1504713600000`); it has zero trades,
zero volumes, and all four prices equal `4619.43`. It is not a valid complete
4h replacement. The monthly 12:00 row has the same OHLCV/trade counts as daily
and REST, but closes at `1504713600000` instead of their `1504713599999`.
The complete four returned hours 12:00–15:00 aggregate exactly to its OHLCV and
2,560 trades. All five shared monthly/daily 4h identities agree on every economic
field. The close discrepancy is thus **not consistent across sources**.

The 20:00 native 4h observation has a normal closing boundary but its economics
and 43 trades exactly equal the only returned hour in that interval, 23:00.
That native row is accepted as a provider observation, with this explicit warning:
it does **not** establish four hours of continuous trading. The unreturned
17:00–22:00 hourly intervals and zero-duration 16:00 placeholder are consistent
with an interruption. They do not independently prove exchange downtime, its
exact duration, or that the missing hours contained no trades.

**June:** monthly, daily and REST all return the 2018-06-26 00:00 4h row closing
at `1529978399999` (01:59:59.999), two hours before the expected boundary.
OHLCV/trade counts match across all three sources. The 04:00 and 08:00 4h
identities are absent in all three; hourly rows are absent from 02:00 through
11:00. This supports treating the shortened row separately from genuine,
still-unverified trading gaps. June monthly SHA-256:
`38ce9dbc3a80c20777b7a02745b4d8458476627a13f7e0d188df06b7f5cbfd12`.

[Binance issue 77](https://github.com/binance/binance-public-data/issues/77)
reports historical gaps and irregular closes, including June 2018. A repository
contributor explains that some absent klines reflect maintenance and that archive
data originated from the public API. This is supporting context, not a dated
maintenance confirmation for September 6. [Issue 374](https://github.com/binance/binance-public-data/issues/374)
reports missing historical 1m data; that report alone cannot establish the cause
of either interval investigated here.

**Inference:** September's monthly-only one-millisecond boundary difference likely
reflects historical serialization/export differences around an interruption,
rather than different trading economics. The normal alternative-source boundary
and hourly agreement support that interpretation. Provider internals, revision
history and a specific dated maintenance record remain unverified. These sources
are not independent venues and can share upstream defects.

### Validation decision and operational semantics

No irregular timestamp is normalized in this follow-up. Even though September's
12:00 row has strong corroboration, conservatively excluding it avoids introducing
a date-specific correction or treating all off-by-one/shortened intervals as
complete. The same rule applies to both symbols and every requested month:

| Condition | Strict default | Explicit gap-tolerant history |
| --- | --- | --- |
| ZIP/checksum/member/size failure | Fail before writes | Same |
| Invalid CSV, OHLCV, trade count, eligibility | Fail before writes | Same; even if that row also has an irregular close |
| Duplicate, misaligned, out-of-range or reordered identity | Fail before writes | Same; excluded rows still participate in identity/order checks |
| Missing expected source identity | Fail whole month | Record exact missing identity; accept valid neighbours |
| Irregular raw close between its open and exclusive interval end | Fail whole month | Exclude exact provider row; retain row number, identity, raw/expected close and reason |
| Close before open or after exclusive end | Fail whole month | Stop for review as a different anomaly class |
| Existing economic conflict or stale changed observation | Roll back whole batch | Same |

All accepted rows still require the exact normal inclusive close boundary and
unaltered economic validation. No synthetic, forward-filled, aggregated, clipped,
or alternative-source replacement is written. Gap tolerance changes **which
validated batch may be committed**, not the definition of a valid accepted row.
An exclusion is diagnostic quarantine in the retained ZIP/manifest, not a new
database table. Exact ZIP content hashes and original accepted provenance remain.

A successful partial acquisition has `validation_result=source_gaps`,
`candle_complete=false`, and an independent `database_write_outcome=committed`.
`actual_count` counts provider rows; `accepted_count` counts eligible rows;
`excluded_observations` preserves every quarantined identity and reason.
`source_missing_intervals` counts absent source identities, while
`missing_intervals` also includes excluded expected identities. Rejected rows do
not inflate inserted/unchanged counts. Conflicts or write errors roll back the
entire accepted batch; no accepted economic values are replaced.

Coverage separates successfully inspected months, committed months, source
missing intervals, excluded provider observations, unresolved failures, unavailable
archives, and months without any attempt evidence. Missing stored counts also
include unattempted/rejected months and must not be called provider trading gaps.
Unknown causes remain unknown. Source diagnostics survive successful partial
commits and are embedded in incomplete export manifests with hashes, identities,
reasons and evidence references; a full stored grid alone cannot hide them.
Dry runs do not resolve failed imports. All original attempt manifests remain.

The range command continues over these disclosed gaps and stops on any other
validation, acquisition, artifact or database failure. A successful exit means
acquisition completed under the requested policy, **not continuous coverage**.
Retry the same explicit range safely; unchanged accepted rows keep their original
values, versions and provenance. No cached file is represented as newly fetched.

```sh
uv run --locked --env-file .env badger backfill-history --symbol BTCUSDT --interval 4h --start-month 2017-08 --end-month 2026-09 --allow-source-gaps
uv run --locked --env-file .env badger backfill-history --symbol ETHUSDT --interval 4h --start-month 2017-08 --end-month 2026-09 --allow-source-gaps
```

The single-month `ingest-archive` CLI remains strict. A bounded one-month tolerant
check uses `backfill-history` with identical start/end months; `--dry-run` is also
supported without database settings.

### Research safety

Complete exports still fail while stored gaps or unresolved provider diagnostics
remain. Explicit `--allow-incomplete` exports retain the full coverage/gap manifest
and an `incomplete` label. No incomplete live export is implicitly authorized or
created by a backfill.

Future feature engineering and backtests must reject or explicitly handle windows
crossing missing intervals or anomalous provider observations. **Rows adjacent in
a CSV or query result are not necessarily consecutive market periods.** A rolling
indicator must validate timestamps before treating N stored rows as N consecutive
4h periods; it must not fill unknown prices or assume zero returns through gaps.
Normal native boundaries establish source-grid validity, not uninterrupted trading
or complete hourly evidence within a bar. The disclosed September 20:00 bar needs
that distinction in any future study of interruption-sensitive windows. This task
implements no features, ML, backtests or trading.

### Final live results and verification

The full acquisition **completed for both markets**, August 2017 through
September 2026 inclusive. All 220 distinct market-months were checksum verified,
inspected and committed under the explicit policy. There were **no new anomaly
classes requiring a stop**, failed acquisitions, conflicts or stale changed rows.
This is an acquired dataset **with known gaps**, not continuous history.

| Final result | BTCUSDT | ETHUSDT |
| --- | ---: | ---: |
| Successfully inspected / committed months | 110 | 110 |
| Months with complete accepted grids | 91 | 91 |
| Months with persistent source diagnostics | 19 | 19 |
| Expected native 4h identities | 19,991 | 19,991 |
| Accepted stored candles | 19,955 | 19,955 |
| Absent monthly-source identities | 17 | 17 |
| Excluded irregular-close observations | 19 | 19 |
| Remaining missing stored intervals | 36 | 36 |
| Failed / unavailable / unattempted months | 0 | 0 |
| Conflicts / stale changed observations | 0 | 0 |
| Duplicate identities / historical revisions | 0 | 0 |

First and last stored opens remain **2017-08-17 04:00 UTC** and
**2026-09-30 20:00 UTC**, respectively. Every stored row is version 1. No timestamps
were normalized. No missing interval was fabricated. The pre-existing **1,282
rows** retain every field except permitted confirmation-watermark advancement;
this was checked against a baseline of all rows, including original economic
values, versions, observation/recording times and provenance. An independent SQL
`EXCEPT` audit matches every coverage-report gap exactly.

Both markets have the following exact excluded and absent identities (UTC).
Raw close timestamps can differ slightly between symbols and are retained in each
market's diagnostic manifest. A dash means no identities in that category.

| Month | Excluded provider opens | Absent monthly-source opens |
| --- | --- | --- |
| 2017-09 | 2017-09-06 12:00 | 2017-09-06 16:00 |
| 2018-01 | 2018-01-04 00:00 | — |
| 2018-02 | — | 2018-02-08 04:00; 2018-02-08 08:00; 2018-02-08 12:00; 2018-02-08 16:00; 2018-02-08 20:00; 2018-02-09 00:00; 2018-02-09 04:00 |
| 2018-06 | 2018-06-26 00:00 | 2018-06-26 04:00; 2018-06-26 08:00 |
| 2018-07 | 2018-07-04 00:00 | 2018-07-04 04:00 |
| 2018-10 | 2018-10-19 04:00 | — |
| 2018-11 | 2018-11-14 00:00 | 2018-11-14 04:00 |
| 2019-03 | 2019-03-12 00:00 | 2019-03-12 04:00 |
| 2019-05 | 2019-05-15 00:00 | 2019-05-15 04:00; 2019-05-15 08:00 |
| 2019-08 | 2019-08-15 00:00 | 2019-08-15 04:00 |
| 2019-11 | 2019-11-13 00:00 | — |
| 2020-02 | 2020-02-19 08:00 | 2020-02-19 12:00 |
| 2020-04 | 2020-04-25 00:00 | — |
| 2020-06 | 2020-06-28 00:00 | — |
| 2020-12 | 2020-12-21 12:00 | — |
| 2021-02 | 2021-02-11 00:00 | — |
| 2021-04 | 2021-04-20 00:00; 2021-04-25 04:00 | — |
| 2021-08 | 2021-08-13 00:00 | — |
| 2021-09 | 2021-09-29 04:00 | — |

The follow-up made **222 successful import attempts**: two BTC bounded validations
with persistence, then 110 months per market. Across these attempts there were
**38,628 inserts, 1,637 unchanged confirmations and 40 row exclusions**. The latter
includes the two exclusions seen again when the bounded months were replayed:
there are **38 distinct excluded observations** across the two markets, plus
**34 distinct absent monthly-source identities**, totalling **72 stored gaps**.
The full-range runs alone returned 19 exclusions and 17 absent intervals per
market. Earlier failed attempts remain archived; their previous blocked status
was resolved by successful imports, while source diagnostics remain unresolved.

The full-range default export was actually attempted and refused for incomplete
coverage. **No complete or incomplete live export was published.** Offline
integration tests verify acknowledged incomplete exports include the full
coverage report, exclusions and exact gap manifest, and that filling the stored
grid alone does not erase unresolved provider diagnostics.

Final verification: **268 tests passed (133 unit, 135 PostgreSQL integration)**
using the existing fixture infrastructure and a separate temporary PostgreSQL 17
server; Ruff lint and formatting checks passed. Tests cover retained official
source comparisons, strict/tolerant missing intervals, both irregular-close
classes, malformed/economically invalid rows even when their close is also bad,
identity/order/checksum/ZIP safety, empty/all-excluded batch review, atomic partial
batch commit, conflict/stale/late database rollback, restart/idempotency,
coverage diagnostics and default/explicit export behavior. The disposable server
was removed after testing; the development database was neither reset nor
migrated. CI was not run remotely.

Retained local evidence (gitignored):

- `artifacts/stage-01b3-followup-investigation/`: original bounded source responses,
  ZIPs/sidecars, exact rows, URLs, timestamps and hashes.
- `artifacts/stage-01b3-followup-baseline.json`: all original accepted rows before
  any follow-up write.
- `artifacts/stage-01b3-followup-bounded.json`: September/June ingestion outcomes.
- `artifacts/stage-01b3-followup-full.log`: both full chronological runs and totals.
- `artifacts/stage-01b3-followup-coverage.json`: full per-market gap and provider
  exclusion diagnostics, source hashes and raw artifact references.
- `artifacts/stage-01b3-followup-audit.json`: exact final totals, original-row
  preservation, independent SQL checks and complete-export refusal.
- `artifacts/raw/` and `artifacts/manifests/`: exact acquisition evidence for every
  attempt, including the earlier failed strict September archive.

Remaining limitations: absent intervals have no known prices; maintenance is a
supported hypothesis rather than a verified cause for every gap. Only the two
bounded BTC days received daily/REST/hourly cross-source comparisons. Native bars
with regular boundaries can still span interruptions, as the September 20:00
comparison demonstrates. Structural validation cannot establish economic truth,
provider finality or historical publication time. Evidence remains local and
needs durable backup before dependable research operations. The offline JSON
fixture preserves comparisons, not a substitute for backing up original ZIPs.

No production or sibling-repository files/infrastructure were accessed or changed.
No commit, push, deployment, real-money trading or Stage 1C work was performed.

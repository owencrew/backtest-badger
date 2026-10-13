# Stage 1C.1 — Incremental REST tail and recent refresh

Implemented for Binance Spot BTCUSDT and ETHUSDT, native UTC 4h only. This stage
adds a synchronous command, strict REST parsing, bounded catch-up, recent revisions
and independent response/stored-grid diagnostics. No migration or dependency was
needed. Historical revalidation remains Stage 1C.2.

## Commands

Run from the repository root with the existing local development `.env`:

```sh
# Normal overlap plus bounded catch-up; run each market separately.
uv run --locked --env-file .env badger sync-recent --symbol BTCUSDT --interval 4h
uv run --locked --env-file .env badger sync-recent --symbol ETHUSDT --interval 4h

# The bounded live validation range used for this stage, first without DB writes.
uv run --locked --env-file .env badger sync-recent --symbol BTCUSDT --interval 4h --start 2026-10-01T00:00:00Z --dry-run
uv run --locked --env-file .env badger sync-recent --symbol ETHUSDT --interval 4h --start 2026-10-01T00:00:00Z --dry-run
uv run --locked --env-file .env badger sync-recent --symbol BTCUSDT --interval 4h --start 2026-10-01T00:00:00Z
uv run --locked --env-file .env badger sync-recent --symbol ETHUSDT --interval 4h --start 2026-10-01T00:00:00Z
```

`--settling-seconds 60` is the default, configurable from 0 through 86,400 whole
seconds. `--start` requires an aware UTC time on an exact 4h opening boundary.
Existing archive, history, export and health commands remain available.

A dry run reads PostgreSQL to choose the range and report actual stored gaps;
it never calls a database writer. It retains raw responses and manifests, validates
the entire returned range and records advisory old/new disagreements. Its insert,
unchanged and revision counters are zero because nothing was written. A successful
dry run may report missing stored rows that the subsequent real sync will insert.
Dry-run comparisons do not acquire row locks or guarantee a subsequent write outcome.

## Source contract and clocks

Official Binance documentation was consulted on 2026-10-13:

- [Market-data-only endpoints](https://developers.binance.com/en/docs/products/spot/faqs/market_data_only)
  provides public market data without authentication at `data-api.binance.vision`.
- [Kline contract](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints)
  defines `/api/v3/klines`, twelve fields, UTC time parameters, timezone selection,
  native 4h support and a maximum of 1,000 rows. Documented request weight is 2.
- [REST information and limits](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits)
  documents default millisecond timestamps, chronological responses, used-weight
  headers and HTTP throttling. No microsecond header is sent.

Every kline request explicitly sends `symbol`, `interval=4h`, `timeZone=0`,
`startTime`, `endTime` and `limit=1000`. The inclusive millisecond API `endTime` is
one millisecond before the fixed exclusive range end. URLs and parameters are
retained. Redirects are rejected. `/api/v3/time` supplies one bounded clock check
before acquiring klines; no private, trading, futures or UI-kline endpoints are used.

One local aware UTC run time is captured before network acquisition. Integer
`timedelta` floor arithmetic computes:

```text
end_exclusive = floor_to_UTC_4h(fixed_run_time - settling_delay)
latest_eligible_open = end_exclusive - 4 hours
eligible iff open_time + 4 hours + settling_delay <= fixed_run_time
```

Exactly at close plus delay, that candle becomes eligible. Just before it, the
previous cutoff remains in force. Time passing between pages never extends the
range. Current, settling or other out-of-window rows cause whole-page rejection;
none is persisted. The clock probe requires server time within the local request /
complete-response bracket plus five seconds, and a bracket no longer than ten
seconds. A failed/uncertain clock check stops the run. This checks coarse skew;
it is not precision clock synchronization. Local clock correctness remains required.
Sixty seconds is a provisional research policy, **not Binance finality**.

## Catch-up and pagination

The normal start is the earlier of `latest_stored_open + 4 hours` and
`end_exclusive - 7 days`. This refetches 42 eligible identities and catches up after
longer interruptions. A latest timestamp never proves that preceding candles exist.
Automatic catch-up exceeding 30 days fails with an explicit `--start` instruction.
An empty market also requires an explicit starting boundary.

Explicit recovery replaces the acquisition start, but must be within 180 days of
the eligible cutoff. The fixed cutoff remains the end; there is no implicit scan
back to 2017 or historical revalidation option. These bounds are operational limits,
not claims about the age at which provider data becomes final. Older acquisition
belongs to the existing explicit archive workflow or a future reviewed stage.

Each next request starts at the last returned opening time plus four hours,
including short pages. A short page is not assumed to end the series. An empty,
duplicate, backwards or out-of-order page fails. Gaps inside a valid response are
recorded without interpolation; valid neighbours may commit, but the sync reports
incomplete coverage and exits nonzero. The complete requested UTC grid is checked
against both validated responses and stored data. There is an additional cap of
16 kline pages per run; unresolved sparse ranges fail explicitly at that bound.

HTTP uses the existing standard-library conventions: 15-second socket timeout,
30-second body-read deadline checked between reads (a blocked read can add at most
the socket timeout), and a 2 MiB body cap plus one detection byte. Each request is
paced by one second. Transport errors and HTTP 500/502/503/504 receive at most three
attempts with two- and four-second backoff. HTTP 429/418 immediately stop without
an automatic retry, preserving `Retry-After` and used-weight diagnostics. Operators
must observe that supplied wait before another invocation; there is no cross-process
rate coordinator or scheduler. Other HTTP errors fail without retry. Bounds also
limit raw evidence per run; retention across separate runs remains a local operation.

## Validation and revision selection

Every accepted row must have exactly twelve elements. Prices and volumes must be
bounded ordinary decimal strings, converted directly to exact `Decimal` values.
Timestamps and trade counts must be JSON integers, excluding booleans. All economic
bounds reuse `validate_observation`. The inclusive close must equal open plus
four hours minus one millisecond. The final ignored field remains in raw evidence
and never participates in economic equality. No historical close-time exceptions,
normalizations, manufactured prices or volume fills are applied to REST data.
Malformed data rejects the whole page before any write, retaining the original
response and identifiable rejected rows for investigation.

`save_candles(..., mode="backfill")` retains its conflict-rejecting behavior.
Explicit `mode="recent-refresh"` reuses the same insert/lock/version SQL as
`save_candle`, with a caller-supplied revision range of at most seven days and at
most 1,000 validated native 4h REST observations. The CLI always supplies the fixed
seven-day range. **An explicit earlier acquisition start does not widen revision
authority.** Missing valid older rows can insert; changed existing older rows conflict.

Each page is one short transaction, with sorted lock order and no transaction
spanning HTTP. Identical confirmations retain economics, version and original
provenance, advancing only the observation watermark. Newer changed observations
inside authority archive the full previous row and increment the current version.
Stale changes and equal-time conflicts roll back the whole page, including any
other inserts, revisions or watermark updates. Previously committed pages survive.
A → B → A produces three versions even if a response hash/content repeats.

All disagreements retain the locked old row and incoming values with both sources.
Archive/REST disagreements are prominently reported; changes of at least 5% in any
price field or at least five changed identities in a page also produce warnings.
These are investigation flags, not economic truth tests or price clipping rules,
consistent with the original design. Structurally valid, authorized newer changes
are still versioned. No elaborate approval mechanism or automatic old-data mutation
is introduced. Acquisition order cannot prove which conflicting economic value is
true; significant discrepancies require inspection of the retained evidence.

## Provenance, evidence and diagnostics

Market `open_time`, complete-response `observed_at`, and database `recorded_at`
remain distinct. All rows from a page share acquisition time, `source_kind=rest`,
the exact request URL and SHA-256 of the exact complete response body. Acquisition
time is not Binance's original candle publication time. REST has no archive-style
checksum sidecar; the locally computed hash identifies the received bytes.

The existing artifact functions retain content-addressed bodies and atomically
replace run JSON manifests under ignored paths:

- `artifacts/rest/raw/<sha256>.json`: bounded response bytes, including error or
  invalid bodies; partial/oversized bodies are evidence only, never provenance for
  accepted candles. The suffix denotes endpoint format, not a promise of valid JSON.
- `artifacts/rest/manifests/<run_id>.json`: fixed policy/range, clock evidence,
  request parameters and headers, actual response URLs, times, hashes, body paths,
  attempts/rate diagnostics, page validation identities, disagreements, persistence
  outcomes, errors and final coverage. Page records are embedded in the run manifest.

Final summaries include inserted/unchanged/revised/stale/conflicting counts,
failed/incomplete pages, latest eligible/stored opens and exact stored missing
identities. PostgreSQL `generate_series` coverage runs under a read-only REPEATABLE
READ snapshot. `fresh` means the stored tail equals the latest eligible opening;
a fresh tail can still have interior gaps. `stored_complete` is separate from
`source_complete` and overall success. `source_missing_intervals` records holes in
inspected page spans; `unresolved_response_intervals` additionally includes
unacquired or rejected intervals, without claiming these are provider trading gaps.
Older historical diagnostics remain in the existing historical reports and do not
cause a complete recent window to fail.

Network failures leave accepted data intact. A commit transport failure reports
`failed_or_unknown`; reconcile the stored grid and retry deliberately. A crash or
artifact failure can leave an `in_progress` manifest after a successful DB commit.
There is no filesystem/database distributed transaction, and local ignored files
are not durable backups. The console reports known committed counts even when
final evidence publication fails.

## Actual live validation

On 2026-10-13, both explicit dry runs completed before real writes. Each validated
75 candles from **2026-10-01 00:00 UTC** through **2026-10-13 12:00 UTC exclusive**.
Both real syncs then committed, followed by one ordinary seven-day repeat each.
All six runs used the same eligible cutoff; no live economic revision was invented.

| Result | BTCUSDT | ETHUSDT |
| --- | ---: | ---: |
| Historical rows before sync | 19,955 | 19,955 |
| New REST candles inserted | 75 | 75 |
| Unchanged confirmations on ordinary repeat | 42 | 42 |
| Revised / stale / conflicting | 0 / 0 / 0 | 0 / 0 / 0 |
| Final current candles | 20,030 | 20,030 |
| Missing eligible identities in the requested October range | 0 | 0 |
| Failed / incomplete pages | 0 / 0 | 0 / 0 |
| Historical missing identities, unchanged | 36 | 36 |
| Historical revisions, final | 0 | 0 |

Latest stored and eligible open: **2026-10-13 08:00 UTC** for both markets; both
report fresh. The current **12:00 UTC** candle was excluded. All stored versions
remain 1. Real page acquisition times were **12:31:38.265668 UTC** (BTC) and
**12:31:42.669836 UTC** (ETH); database recording times followed each acquisition.
Repeats preserved original page provenance and created no revisions. No provider
anomalies, archive/REST disagreements, transport failures or throttles were observed.
HTTP failure behavior was verified with mocked responses, not induced live.

A before/after audit over historical rows and columns matched, including the
watermarks; the whole historical coverage report also matched exactly. All 39,910
historical observations were also compared against the frozen CSV using exact
Decimal values, versions, timestamps and original provenance. No previously
imported candle, source-gap evidence or exclusion diagnosis changed. The frozen
Stage 1B.3 export and its manifest were byte-for-byte unchanged:

```text
candles.csv:   e6052b8cca7bca00999ca4d7429af67db019c8ef261fa2b499f0fd6774dcd13b
manifest.json: a78d34256d3bcd789e6cc19a2807f432d1ffa1a73ecc81b5ea16b3859759a98a
```

Local evidence includes `artifacts/stage-01c1-baseline.json`,
`artifacts/stage-01c1-audit.json`, six `artifacts/stage-01c1-*.log` files, and the
REST run manifests. Initial persisted-page manifests are
`0ba189959ef242aea215ca3867edf6ec.json` (BTC) and
`772a6bc8d3c342abab896d0cc7263d75.json` (ETH).

## Verification and scope

Automated tests use mocked HTTP and the existing disposable PostgreSQL fixture
infrastructure. They cover exact cutoff thresholds, parsing/Decimal precision,
HTTP bounds/retries/throttling, pagination and missing grids, interrupted catch-up,
dry runs, provenance, A → B → A, stale/equal-time conflicts, page rollback,
concurrent locking and frozen export preservation. Historical strict/gap-tolerant
archive, migration, research and CLI tests remain in the full regression suite.
Final verification: **306 tests passed (161 unit, 145 PostgreSQL integration)**
on the separate disposable PostgreSQL 17 server. Ruff lint, Ruff formatting and
`git diff --check` passed. The substantive prompt archive matched the supplied file
byte-for-byte. CI was not run remotely. The disposable server was removed after
testing; development data and schema were not reset or migrated.

Created: `src/backtest_badger/rest.py`, `src/backtest_badger/recent.py`,
`tests/test_rest.py`, `tests/integration/test_recent.py`, this guide and the exact
prompt archive `prompts/stage-01-market-data/006-rest-tail-and-refresh.md`.
Changed: persistence batch mode, CLI and its focused test, README, architecture,
roadmap and the design's implementation-status note. No schema, dependency,
frozen dataset, historical artifact, sibling repository or production change.

Stage 1C.2 historical revalidation, daily archive automation, scheduling,
WebSockets, other intervals/assets, features, models, backtests, trading and website
work remain unimplemented. This stage stops here for review. No Field Note was
created; ordinary ingestion results did not warrant a new research article.

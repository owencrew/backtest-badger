# Stage 1A — Binance data feasibility and design

Status: feasibility verified on 2026-10-13. Stage 1B.1 implements and tests the
three-table schema and persistence policy; ingestion and exports remain planned.
See the [persistence guide](stage-01b1-persistence.md) for the implemented API.

## 1. Recommendation

Use Binance Spot **native UTC 4h candles** for BTCUSDT and ETHUSDT. Backfill from
Binance Vision monthly archives, then daily archives; fill the recent tail and
refresh recent candles through the public market-data-only REST API. Add native
1h data separately only when execution research or a bounded validation needs it.
Do not persist derived 4h candles or parent lineage.

Use three application tables: `market`, `candle`, `candle_revision`. Keep one
current candle and copy its previous version to history whenever a valid changed
observation replaces it. Identical re-fetches do not create revisions. Start with
a configurable 60-second settling delay and seven-day REST refresh window.
These are project defaults, not Binance guarantees of finality.

Stage 0 was inspected: Python 3.12, uv, argparse, environment-loaded immutable
settings, Psycopg with bounded connection/statement timeouts, and local PostgreSQL
17 in Compose. At the time of the Stage 1A inspection, the only database operation was `SELECT 1`.
Stage 1B.1 preserves these commands and configuration conventions while adding
explicit migrations and versioned candle persistence.

## 2. Official provider documentation

Consulted on 2026-10-13:

- [Binance Public Data](https://github.com/binance/binance-public-data): spot ZIP
  CSVs, interval support, archive organisation, checksum verification, timestamp
  transition, publication cadence and revisions. It documents all symbols and
  native 1h/4h; daily files arrive the following day and monthly files on the first
  Monday of the month. It specifies no precise daily publication hour. Spot
  archive timestamps change from milliseconds to microseconds on 2025-01-01.
  Archives can be replaced; the listed 2022-08-08 kline correction fixed
  inconsistent data and the update log records old/new checksums.
- [Spot REST specification](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md):
  chronological responses, default millisecond timestamps, optional
  `X-MBX-TIME-UNIT: MICROSECOND`, and millisecond/microsecond time parameters.
  Limits apply per IP; inspect `exchangeInfo` and used-weight headers. Respect
  `Retry-After` on 429/418; do not retry aggressively. The service is asynchronous.
- [Market Data Only FAQ](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md):
  `https://data-api.binance.vision` supports public `ping`, `time`, `exchangeInfo`
  and `klines` without credentials.
- [Kline endpoint](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market#klinecandlestick-data):
  `GET /api/v3/klines`, weight 2, default limit 500, maximum 1,000, native 1h/4h,
  UTC default timezone, and identity by open time within a symbol/interval.
  `startTime`/`endTime` remain UTC even if candle timezone changes. Use `klines`,
  not presentation-oriented `uiKlines`.
- [General endpoints](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/general):
  exchange information weight 20; ping and time weight 1 each.
- [Archive root](https://data.binance.vision/) and
  [published correction files](https://github.com/binance/binance-public-data/tree/master/updates).

Archive addresses follow:

```text
https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-YYYY-MM.zip
https://data.binance.vision/data/spot/daily/klines/{symbol}/{interval}/{symbol}-{interval}-YYYY-MM-DD.zip
```

Append `.CHECKSUM` to the ZIP URL for its SHA-256 sidecar. A matching checksum
establishes file integrity, not economic correctness or permanent immutability.

## 3. Actual Mac feasibility tests

Local requests ran on 2026-10-13, primarily 00:43:14–00:44:35 UTC. The initial
sandbox request failed DNS resolution; an authorised network-enabled retry
succeeded. No keys, private endpoints, database connections or production access
were used. Temporary scripts, downloaded bodies, response headers, request URLs,
fetch times, hashes and analysis are under `/private/tmp/badger-stage1a/` (ephemeral).

The scripted probes made **41 GET requests**, with 38 HTTP 200 and three HTTP 404
responses, totalling **87,991 response-body bytes**. Including the successful
preflight `/time` request gives 42 network-completed requests (including 404s) and 88,019 body
bytes, comfortably below 15 MB. Each request had a 5-second connect timeout,
15-second total timeout and 1 MB body cap; a cumulative guard stayed below 15 MB.
No complete history was downloaded. Documentation browsing is separate from these
local market-data probes.

### API requests and results

All paths below use `https://data-api.binance.vision` and returned HTTP 200:

| Request | Actual result |
| --- | --- |
| `/api/v3/ping`; `/api/v3/time` | Connectivity confirmed; sampled server time 2026-10-13 00:43:15.964 UTC. |
| `/api/v3/exchangeInfo?symbols=["BTCUSDT","ETHUSDT"]` (URL encoded) | Both `TRADING`, spot allowed; BTC/USDT and ETH/USDT identities confirmed. Advertised request weight 6,000/minute and raw requests 300,000/5 minutes; these are observations, not hard-coded future limits. |
| `/api/v3/klines?symbol={S}&interval={I}&timeZone=0&limit=4`, both symbols × 1h/4h | Each returned three closed candles and one still-open 2026-10-13 00:00 candle. Closed 1h opens: October 12 21:00–23:00; closed 4h opens: October 12 12:00, 16:00, 20:00 UTC. |
| Same four combinations with `startTime=0&limit=1` | Earliest returned open time was **2017-08-17 04:00 UTC**, matching all four August 2017 archives. |
| Four combinations with `startTime=1791676800000&endTime=1791763199999&limit=1000&timeZone=0` | October 11: 24 hourly and six four-hour candles per market; all **60/60** matched archives exactly after normalization. |
| BTCUSDT 1h, `startTime=1791676800000&endTime=1791680399999&limit=1`, microsecond header | Microsecond timestamps observed; normalized row exactly matched the default-millisecond response. |
| BTCUSDT 1h, `timeZone=0&limit=2&endTime=1791691199999`, starts `1791676800000`, then `1791684000000` | Two pages gave October 11 00:00, 01:00 then 02:00, 03:00, exactly matching the first four overlap rows. |

### Archive samples

Each successful ZIP contained one headerless, 12-column CSV. All ten SHA-256
checksums passed. Names expand using the URL patterns above; all daily samples
had the full expected day, and August samples were contiguous from the first
observed candle through month end.

| Period | Market | Interval | Rows | Timestamp unit |
| --- | --- | --- | ---: | --- |
| Monthly 2017-08 | BTCUSDT | 1h / 4h | 356 / 89 | milliseconds |
| Monthly 2017-08 | ETHUSDT | 1h / 4h | 356 / 89 | milliseconds |
| Daily 2024-12-31 | BTCUSDT | 1h | 24 | milliseconds |
| Daily 2025-01-01 | BTCUSDT | 1h | 24 | microseconds |
| Daily 2026-10-11 | BTCUSDT | 1h / 4h | 24 / 6 | microseconds |
| Daily 2026-10-11 | ETHUSDT | 1h / 4h | 24 / 6 | microseconds |

The two monthly July 2017 4h URLs returned 404. This supports, but alone does not
prove, the observed August start. BTCUSDT's daily **2026-10-12 4h** URL also returned
404 at **00:44:33 UTC on October 13**; its checksum was therefore not requested.
This is evidence that publication cannot be assumed at midnight, not evidence of
a permanently missing market day. Monthly cadence was documented, not measured.

**Quality results:** all 998 archive rows passed finite positive OHLC,
`low ≤ open/close ≤ high`, non-negative base/quote/taker volumes and trade counts,
taker volumes no greater than totals, UTC alignment and close-boundary checks.
No duplicates or missing internal intervals were found. Leading August dates
before the first observed candle are outside this tested coverage. Recent/API
sample rows also passed structural checks; the four current candles were excluded
from closed-candle eligibility. No future finality is implied.

Comparison joined on exact `(symbol, interval, UTC open_time)` and used `Decimal`
for all economic values and integers for trades/timestamps. All economic fields
matched in the 60-row overlap. Raw post-2025 close times differ in precision:
archive end-minus-1µs versus default API end-minus-1ms. Normalize both to the
exclusive interval end; do not report this as a correction. The 2017 ignored
column was nonzero in all 890 monthly rows; never require that field to be zero.

As an extra bounded check, aggregating October 11's hourly samples reproduced all
12 native 4h rows exactly, including volumes and trade counts. This small result
does not establish equality over all history. No actual value-changing revision
was witnessed, no historical continuity audit was performed, and rate-limit
failure/retry behaviour was not deliberately triggered.

## 4. Candle interpretation and timeframe choice

Archive column positions (one-based) and parsing contract:

| Positions | Meaning | Parse/storage |
| --- | --- | --- |
| 1, 7 | Open time, inclusive close time | Integer epochs in declared source units; timezone-aware UTC. Normalize close to exclusive end. |
| 2–5 | Open, high, low, close | Exact finite Decimal → PostgreSQL numeric. |
| 6, 8 | Base volume, quote volume | Exact non-negative Decimal → numeric. |
| 9 | Number of trades | Non-negative integer → bigint. |
| 10, 11 | Taker-buy base volume, quote volume | Exact non-negative Decimal → numeric. |
| 12 | Provider's unused field | Preserve in raw evidence; exclude from economic comparison and schema. |

CSV values are text; REST prices/volumes are strings and timestamps/counts are
JSON integers. Validate units from archive date/source contract, then validate
plausible dates and exact alignment; never guess units from digit count alone in
production. Use integer epoch arithmetic, avoiding floats and host-local time.
For 1h opens require whole UTC hours; 4h opens are 00, 04, 08, 12, 16, 20 UTC.
Represent each candle as `[open_time, open_time + interval)`.

| Choice | Correctness, complexity and future use |
| --- | --- |
| A: native 4h only | Smallest path to research, six rows/day/market; directly preserves Binance's observation. Does not resolve intrabar execution. |
| B: 1h → locally derived 4h | Transparent aggregation, but requires four complete aligned parents and policies for missing/revised parents, recomputation and reproducible versions. More data and implementation before research is usable. |
| **Selected: native 4h; independent native 1h when needed** | Starts as A. Adds finer execution/validation data without making feature availability depend on hourly completeness. Cross-timeframe differences are diagnostics, not automatic repair or blocking parent conflicts. |

Four-hour OHLC cannot determine intrabar price ordering. Hourly OHLC improves
resolution but still cannot prove fills or a within-hour path. A signal computed
after close plus settling delay cannot causally trade at the just-passed close or
next interval's already-passed open. Later execution research must choose an
available subsequent price and model delay, costs and slippage explicitly.

## 5. Minimal revision and quality policy

1. **Eligible observations:** require complete HTTP/ZIP/checksum validation,
   identity/range/schema checks and the structural checks above. An open candle
   is incomplete, even when its payload is structurally valid. A closed candle
   remains settling until `interval_end + 60 seconds ≤ trusted_now`. Check server
   clock against local UTC (initial tolerance 5 seconds); fail the incremental
   run clearly on excessive skew rather than accept uncertain closure.
2. **Identical values:** compare normalized economic fields exactly. Keep current
   version and original provenance unchanged, including the version's first
   observation time. Stage 1B.1 advances only a `last_observed_at` watermark on a
   later confirmation, preventing an older conflicting observation from replacing
   it. Exact retries change nothing. Future run manifests record repeat-fetch
   evidence, not additional candle versions.
3. **Changed valid values:** copy the previous current row into history and replace
   current atomically, incrementing the version. Retain source URL, body hash and
   fetch/write times for both versions. Accept only observation timestamps strictly
   newer than the current watermark: older changed observations return `stale`;
   equal-time conflicts raise explicitly. Treat an accepted change as a provider revision,
   not an unresolved vote. A later A→B→A change is a new version; do not impose a
   unique constraint on values or their hash.
4. **Refresh bounds:** every incremental run re-fetches the last seven days of
   closed candles, plus any explicit catch-up range. Seven days bounds routine
   network work; it is not a retention limit or a claim that older data is final.
   Deliberate historical revalidation accepts valid older corrections through the
   same atomic history path and reports changed identities and affected datasets.
   Never silently skip such a change solely because it is old.
5. **One intentional source per range:** monthly archives, then uncovered daily
   files, then REST tail. Ordinary backfill fills holes and compares existing data;
   changes to existing historical rows require explicit revalidation mode. Routine
   recent refresh uses REST. Revalidation selects an archive or REST explicitly;
   it must report disagreement, rather than repeatedly alternate sources until
   they appear to agree. Re-fetch evidence; do not treat cached-file replay as a
   newer provider observation. Binance exposes no global candle revision sequence,
   so retrieval order alone cannot prove one conflicting source is more correct.
6. **Scoped usability:** inference later checks only its actual input window,
   required versions, freshness and quality. A correction outside that window
   cannot block it. Previously issued predictions and frozen research datasets
   retain their exact inputs; new canonical data never rewrites them.

Quality classifications remain simple:

| Condition | Action |
| --- | --- |
| Incomplete / settling | Skip persistence; retry after eligibility. Kline REST has no finality flag. |
| Missing | Expected eligible identity absent after listing/start and within the requested range. Report the gap and retry deliberately; no interpolation or zero-volume fabrication. A missing archive file alone is not a missing candle. |
| Invalid | Parse, alignment, OHLC or volume invariant failed, or conflicting duplicates within one payload. Retain diagnostic evidence; do not replace canonical data. Fail that page/file transaction. |
| Valid revision | Eligible, structurally sound values differ from current. Preserve old version and select new according to the requested refresh/revalidation policy. |
| Anomalous observation | Structurally sound but unusual (large discontinuity, cross-timeframe disagreement, oscillating sources). Accept with diagnostic warning under the same policy; do not silently clip, interpolate, reject by an arbitrary price threshold, or claim it proves a correction. Later research may exclude a disclosed affected range. |

Missing input in a required window blocks that specific calculation; unrelated
historical warnings do not create a global readiness failure. Structural validity
is necessary, not sufficient proof that a price is economically accurate.

## 6. Implemented PostgreSQL schema — three application tables

Canonical-plus-history has one straightforward research query and copies rows
only on change. Immutable observations plus a current-selection table requires
another identity/pointer relationship, joins and lifecycle logic for every read.
Choose canonical-plus-history; no observation candidate table or event framework.

All columns below are NOT NULL unless marked optional. Timestamps are
`timestamptz` with microsecond precision; use aware UTC in Python and UTC database
sessions. Price/volume columns use **unconstrained `numeric`**, preserving incoming
decimal precision without scale rounding. Explicitly reject NaN and ±Infinity in
both application validation and SQL checks. Current exchange trading filters are
not historical precision rules.

| Table | Columns and keys |
| --- | --- |
| `market` | `market_id smallint generated always as identity` PK; `venue text` (`binance`), `market_type text` (`spot`), `symbol text`, `base_asset text`, `quote_asset text`; UNIQUE `(venue, market_type, symbol)`. Seed BTCUSDT and ETHUSDT; no generic provider objects or symbol registry service. |
| `candle` | PK `(market_id, interval_seconds, open_time)`; `market_id` FK → market; `interval_seconds integer` in (3600, 14400); `open_time timestamptz`; `open`, `high`, `low`, `close`, `base_volume`, `quote_volume`, `taker_buy_base_volume`, `taker_buy_quote_volume` numeric; `trade_count bigint`; `version integer` starting at 1; `observed_at timestamptz`, `recorded_at timestamptz`, `last_observed_at timestamptz`; `source_kind text` in (`archive`, `rest`), `source_url text`, `source_sha256 text`. |
| `candle_revision` | Full copy of the prior candle columns, plus `superseded_at timestamptz`. PK `(market_id, interval_seconds, open_time, version)`; composite FK on candle identity → `candle`, with deletion restricted. Only superseded versions live here; current is always in `candle`. |

`source_sha256` is the SHA-256 of exact fetched ZIP/REST body bytes, checked as
64 lowercase hexadecimal characters. It is provenance, not the equality key.
`source_url` contains the full public URL/query, never credentials. Retain request
headers (including timestamp unit) and parser version in the external run manifest.
Raw evidence and manifests can initially be stored by body hash in ignored local
`artifacts/`, not in Git. Durable retention/backups will be addressed as research
and deployment progress; local storage alone is not a durability guarantee. No ingestion-run table is needed yet:
structured JSON manifests contain run UUID, range/mode, source hashes, times,
insert/unchanged/revised/rejected counts, gaps and errors. Database revisions remain
auditable if a manifest is lost, but raw evidence would be incomplete; retain both.

Important constraints, on both candle tables where applicable:

- Supported interval and exact epoch alignment (`open_time` divisible by interval,
  no fractional seconds); finite market/observation timestamps; positive version.
- Finite OHLC, `0 < low ≤ high`, open/close within bounds; finite non-negative
  volumes, non-negative trades, taker volumes ≤ corresponding total volumes.
- `observed_at ≥ open_time + interval` and `recorded_at ≥ observed_at`;
  `last_observed_at ≥ observed_at`; history `superseded_at ≥ recorded_at` and
  `superseded_at ≥ last_observed_at`. Apply the settling delay in application
  logic, keeping configurable clock policy out of schema constraints.
- Market identity fields nonempty; no cascading deletes of canonical/history data.

No persisted close timestamp is needed: exclusive end is exactly derivable from
identity. The parser validates the provider's inclusive close before discarding
that representation. Primary-key B-trees cover planned queries: one market and
interval over an ordered date range, latest candle, and versions of an identity.
The market unique key handles symbol resolution. No extra hash/time indexes,
partitions or TimescaleDB are justified at this scale.

**Implemented idempotent transaction:** validate one observation before writing.
The API requires an idle autocommit Psycopg connection and owns a short READ
COMMITTED transaction. Insert missing identities with version 1 using
`ON CONFLICT DO NOTHING`; if another writer wins, a separate statement obtains a
fresh snapshot and locks the existing row with `SELECT ... FOR UPDATE`. Compare
all economic fields exactly. Identical values keep the version and provenance,
advancing only the observation watermark when necessary. Older changed writes
are explicitly stale; equal-time conflicts raise. A strictly newer changed write
copies the old row to history and updates current to version+1. One server
`clock_timestamp()` sampled after locking supplies replacement `recorded_at` and
old `superseded_at`. Failure rolls both changes back. Row UPDATE/DELETE of history
is rejected by a trigger; owners still have administrative powers.

No database locks are held during network requests, and no advisory locks are
needed. Concurrent absent-row insertions and revisions are tested against real
PostgreSQL. Source acquisition, whole-page/file validation and any batch-level
transaction requirements belong to Stage 1B.2. Replays must retain original
observation times; a new database write is not a new provider observation.

**Three different clocks:** `open_time`/derived end are market time.
`observed_at` is local response-received time, not Binance's undocumented original
publication time. `recorded_at` is this version's database write time; it is not a
precise commit-visibility timestamp. Historical backfills observed today cannot
claim to have been available to this system in 2017. Future research/prediction
recording time belongs to those later artifacts, not these Stage 1 tables.

**Reproducibility:** export a consistent dataset under a read-only REPEATABLE READ
transaction: ordered rows with identity+version, exact decimal values, range,
source hashes, export time, selection policy, code/parser version and a content
hash. Keep the export immutable. Historical versions remain retrievable from the
union of current and history by identity+version. Snapshot actual rows, not just a
wall-clock cutoff that could misrepresent commit visibility. Revised-history
research must be labelled as such; these archives cannot reconstruct what Binance
actually published at every historical instant. Later forward predictions must
save the inputs they read and their recording time. No research/prediction tables
are designed here.

## 7. Ingestion plan

Historical commands require explicit symbol, interval, start and exclusive end;
use native 4h by default. A **2024-01-01 through 2026-10-01 UTC** range can be an intermediate validation
milestone (6,024 expected 4h rows each before gaps), not a permanent restriction.
First prove a single month. Stage 1B.3 ultimately targets **full available historical
coverage** for the selected markets, from their observed 2017 start through a
declared cutoff, in bounded resumable increments. Verify actual coverage rather
than assuming continuity. Research sufficiency remains a later scientific decision.

Prefer monthly ZIPs for complete available months, daily ZIPs for uncovered closed
days, and REST for the remaining tail. Verify checksums before CSV parsing; cap
compressed/uncompressed sizes and read the expected member without arbitrary path
extraction. Keep absolute gaps visible and reject out-of-range/duplicate-invalid
rows. Do not use archive modification time as market or availability time.

REST pagination fixes a run cutoff and timezone 0. Request bounded start/end,
limit ≤1,000; filter returned identities to the intended half-open range and
closure cutoff. Advance `startTime` to last returned open + interval, never wall
clock or last close + an assumed unit. Stop and report an empty/non-advancing page;
do not silently declare an unfilled range complete. Use short timeouts, bounded
backoff for transient failures, provider-directed waits for throttling, and a
conservative request pace. Read current limits rather than baking in today's
6,000/minute observation.

Incremental commands refresh seven days plus a bounded explicit catch-up from the
latest persisted candle. Overlap handles recent changes, but a latest timestamp
does not prove historical completeness: run a date-grid gap check for every
requested range and allow explicit repair of older gaps. No scheduler is required
in Stage 1. A REST or archive outage leaves existing data intact and emits a
failed/partial diagnostic; freshness remains visible.

## 8. Independently verifiable implementation increments

| Increment | Scope and deliverables | Tests and objective acceptance | Dependencies / risks |
| --- | --- | --- | --- |
| **1B.1 — schema (implemented)** | First Alembic migration for the three tables and two markets; Psycopg write functions and canonical/history semantics. Alembic and its required migration dependencies only. | Disposable PostgreSQL tests: constraints, unique keys, exact Decimal round trips, A→B→A, identical repeat, atomic rollback, competing writers. Fresh migration succeeds; Stage 0 CLI/tests still work; one changed value leaves exactly one current and one historical version. | Implemented and tested with disposable PostgreSQL 17; see the persistence guide. No production migration. |
| **1B.2 — bounded archive ingestion** | Explicit-range CLI, checksum/parser/UTC validation, manifests/raw artifact retention, one-month native 4h backfill for both markets. | Fixtures across 2024/2025, malformed ZIP/CSV/checksum, nonzero ignored column, duplicates, gaps and partial listing month. Real bounded month yields expected grid or explicit gap report; second run adds no rows/revisions; invalid file has no partial commit. | Provider availability; transport success is not data completeness. Do not impose current precision filters on history. |
| **1B.3 — usable research dataset** | Expand month by month to full available historical coverage; ordered versioned export plus content hash and documented completeness report. | Export read consistently during a concurrent correction; frozen file/hash remains unchanged after revalidation. Every expected identity is present or a named gap; default “complete” export fails on gaps. A partial export requires explicit acknowledgement and gap manifest. | Builds on 1B.1–2; use bounded resumable commands, not a general orchestration framework. |
| **1C.1 — REST tail and refresh** | UTC paginated fetching, closure/settling cutoff, seven-day overlap, catch-up, freshness and gap diagnostics; same write path as 1B. | Empty/non-advancing pages, exact boundary pagination, current candle exclusion, clock skew, 429/418 Retry-After, transient failure and restart. Small archive/REST overlap compares exact identities/values; second identical run is a no-op. | REST availability and delayed database updates; one failed run must not corrupt canonical data. |
| **1C.2 — historical revalidation** | Explicit range/source revalidation, revision report and old/new provenance; bounded optional 1h/4h comparison without persisted aggregation. | Changed old candle accepted outside seven days; equal fetch creates no history; A→B→A preserved; failure between history insert/update rolls back. Frozen exports survive correction; a query of a disjoint recent window remains usable. No prediction engine is built to test this. | Older changes are only discovered when revalidated; cross-source disagreement may require investigation, not a voting system. |

Keep parsing, validation and persistence as plain functions. Reuse the same write
path for historical and incremental data; no generic exchange interface, derived
tables, separate observation lifecycle, scheduler or extra diagnostics database.

## 9. Readiness, limitations and review decisions

Stage 1B.1 implements and tests the three-table schema, version selection,
concurrency and atomic failure handling. Public connectivity, historical starting
samples, both timeframes, units, checksums and recent overlap were tested in
Stage 1A. Stop for implementation review before Stage 1B.2: ingestion, revalidation
commands and exports remain unimplemented.

- Full available historical coverage is the eventual Stage 1B.3 objective. Retain
  the initial 60-second settling delay and seven-day overlap for Stage 1C; neither
  is a provider finality promise.
- Complete historical continuity, revision frequency and exact publication lag
  remain unmeasured. Fetching now does not recover historical availability times.
- Latest archive 404s require retries/REST coverage. Public access from this Mac
  does not establish future Ubuntu/Lightsail availability; test that only when
  deployment access is explicitly authorised.
- Ignored local artifact/manifest storage is sufficient initially. Address durable
  retention as research and deployment progress; preserving versioned rows, raw
  evidence and exported values is essential for reproducibility.
- Review dataset/API terms before future public redistribution; this stage only
  read public data and does not establish redistribution rights.

Validation during Stage 1A: existing **26 pytest tests passed**;
Ruff lint and format checks passed (15 files). No dependencies, application code,
tables or migrations changed; no database health probe was rerun. No historical
repository, deployment, commit or push was involved.

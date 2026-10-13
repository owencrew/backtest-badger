# Stage 1B.2 — Bounded Binance archive ingestion

Implemented for one explicitly selected, completed calendar month, Binance Spot
BTCUSDT or ETHUSDT, and native `1h` or `4h`. Live validation is limited to January
2025 native 4h. No migration, REST ingestion, scheduling or full backfill is added.

## Commands

Run from the repository root. The existing development database must already be
at revision `0001`; this command never migrates or recreates it. Dry runs require
no database configuration or connection:

```sh
uv run --locked badger ingest-archive --symbol BTCUSDT --interval 4h --month 2025-01 --dry-run
uv run --locked badger ingest-archive --symbol ETHUSDT --interval 4h --month 2025-01 --dry-run
uv run --locked --env-file .env badger ingest-archive --symbol BTCUSDT --interval 4h --month 2025-01
uv run --locked --env-file .env badger ingest-archive --symbol ETHUSDT --interval 4h --month 2025-01
```

Repeat the two import commands to check idempotency. Each invocation re-fetches
exactly its selected month. All three selection arguments are required and checked
before network access; incomplete/future months are rejected. Errors return a
nonzero exit code. `badger health` and `badger db-health` retain their behaviour.

## Acquisition and validation

The standard-library downloader requests only the explicit HTTPS Binance Vision
monthly ZIP and `.CHECKSUM` sidecar. It checks SHA-256 against the exact ZIP bytes
before parsing, including the original sidecar filename. Network failures and
HTTP 500/502/503/504 get at most three attempts with 1/2-second waits; other HTTP
errors, including 404 and throttling, fail without an automatic retry. Redirects
are rejected. Each request has a 15-second socket timeout, a 60-second body-read
deadline checked between reads, and a bounded body. A blocked read can extend the
body deadline by at most the socket timeout. ZIP bodies are capped at 2 MiB,
sidecars at 1 KiB, uncompressed CSV at 8 MiB, and rows at 744 (a 31-day 1h month).

Only the exact expected CSV member is opened in memory; extra/misnamed members,
ZIP corruption, invalid UTF-8/CSV and oversized fields are rejected. There is no
filesystem extraction. Rows must have 12 nonempty fields. Prices and volumes are
parsed directly to `Decimal`, times and trades to integers. Numeric fields accept
ordinary decimal notation of at most 128 characters; floats and scientific
notation are not used. The ignored twelfth field may be nonzero and remains in
raw evidence, outside economic comparisons.

[Binance's archive contract](https://github.com/binance/binance-public-data#data-information)
specifies milliseconds before 2025 and microseconds from 2025-01-01. The requested
month selects units; digit counts do not. Inclusive provider close time plus one
source tick must equal `open_time + interval`. This exclusive end is derived
internally, as in Stage 1B.1. The parser enforces the existing finite OHLCV, taker
volume, bigint trade, alignment and closed-before-observed rules.

Each archive must match the complete UTC grid from month start through exclusive
next-month start. Missing, duplicate and out-of-month identities are reported in
the console and manifest. Reordered rows also fail. Any gap fails the entire
archive; nothing is filled or interpolated. Partial listing months therefore fail
this proof-stage policy. A 404 is acquisition failure, not a claim of no trading.
Integrity and structural checks do not prove that prices are economically correct.

The CSV contains no symbol column. The requested URL, sidecar filename and exact
member name bind it to the selected symbol/interval. Persistence resolves the
seeded market by venue/type/symbol; it never assumes a seed's numeric ID.

## Transaction and provenance behaviour

`save_candles(connection, observations, mode="backfill")` validates every input,
rejects duplicate identities and uses one short READ COMMITTED transaction.
It shares the existing single-observation SQL and version-selection logic.
Deterministic identity order limits lock-order contention. Insertion races use
`INSERT ... ON CONFLICT DO NOTHING`, then a fresh `SELECT ... FOR UPDATE` statement
compares the committed current row while holding its lock.

- Missing rows insert at version 1.
- Identical values keep their economic version and original provenance. Only a
  newer `last_observed_at` confirmation watermark advances.
- Changed existing values are explicit conflicts. Older changed observations are
  explicitly stale. Either condition raises `BatchConflict` with identities and
  rolls back all inserts and watermark changes in the archive.
- Validation/database failures never leave a partly committed month. The existing
  `save_candle()` API still supports intentional A → B → A revisions; this command
  never selects that revision mode.

Acquisition, artifact retention and CSV validation happen before opening the
write connection. No database locks span network or ZIP work. `open_time` is
market time; `observed_at` is local complete-ZIP-response time; `recorded_at` stays
server-generated. Every candle retains `source_kind=archive`, original URL and
exact ZIP SHA-256. Today's download does not establish historical availability.
Reparsing a `DownloadedArchive` preserves its supplied acquisition timestamp;
there is no local-file replay CLI or cache-as-new-observation shortcut.

## Local artifacts and failure handling

The existing `artifacts/` ignore rule covers all outputs relative to the working
directory:

- `artifacts/raw/<sha256>.zip`: verified exact bytes, reused only if bytes match.
- `artifacts/raw/<sha256>-<run_id>.CHECKSUM`: original sidecar for that acquisition.
- `artifacts/manifests/<run_id>.json`: source, hash, observation time, parser version,
  market/month, expected/actual counts, validation diagnostics, missing/duplicate
  identities, inserted/unchanged/conflicting/stale/rejected counts, write outcome
  and safe error category. Unknown counts are null rather than invented.

Verified bytes are retained even when subsequent CSV validation fails. Unverified
ZIP bodies are not promoted to raw artifacts. Manifests are replaced atomically
at acquisition, validation and write boundaries, then finalized. On rollback,
inserted/unchanged counts are zero; all validated input rows are rejected and
conflict/stale identity lists explain why. Network errors and database exceptions
never print raw exception text or environment values.

A transport loss at commit may leave `failed_or_unknown`; inspect stored data and
repeat backfill safely. If commit succeeds but final manifest writing fails, the
command returns failure and explicitly prints `committed` and its counts. The last
saved manifest can still say `in_progress`; it is not proof of rollback. Initial
artifact failure prevents database writes. Local files are not durable backups,
and no filesystem/database distributed transaction is claimed.

## Inspect data

Open the existing local Compose database without printing credentials:

```sh
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

```sql
SET TIME ZONE 'UTC';
SELECT m.symbol, count(*) AS candles, min(c.open_time), max(c.open_time),
       min(c.version), max(c.version)
FROM candle c JOIN market m USING (market_id)
WHERE m.venue = 'binance' AND m.market_type = 'spot'
  AND m.symbol IN ('BTCUSDT', 'ETHUSDT') AND c.interval_seconds = 14400
  AND c.open_time >= '2025-01-01T00:00:00Z'
  AND c.open_time < '2025-02-01T00:00:00Z'
GROUP BY m.symbol ORDER BY m.symbol;

SELECT m.symbol, count(*) FILTER (WHERE c.open_time IS NULL) AS missing
FROM market m CROSS JOIN generate_series(
  '2025-01-01T00:00:00Z'::timestamptz,
  '2025-01-31T20:00:00Z'::timestamptz, interval '4 hours'
) AS g(open_time)
LEFT JOIN candle c ON c.market_id = m.market_id
  AND c.interval_seconds = 14400 AND c.open_time = g.open_time
WHERE m.venue = 'binance' AND m.market_type = 'spot'
  AND m.symbol IN ('BTCUSDT', 'ETHUSDT')
GROUP BY m.symbol ORDER BY m.symbol;

SELECT m.symbol, c.open_time, c.open, c.close, c.observed_at, c.recorded_at,
       c.last_observed_at, c.source_kind, c.source_url, c.source_sha256
FROM candle c JOIN market m USING (market_id)
WHERE c.interval_seconds = 14400 AND c.open_time = '2025-01-01T00:00:00Z'
ORDER BY m.symbol;
SELECT count(*) AS revisions FROM candle_revision;
```

## Local validation results — 2026-10-13

The development database on loopback port 55432 was already revision `0001` and
contained zero candles/revisions. No development migration was run. Tests used a
separate temporary PostgreSQL 17.11 container and uniquely generated databases;
they never reset the development database. All provider requests in automated
tests are synthetic or mocked.

Final checks: **227 pytest tests passed** (101 unit and 126 real PostgreSQL
integration cases), including the existing Stage 1B.1 revision/concurrency and
constraint suite. Ruff lint and formatting checks passed. The prompt archive was
compared byte for byte; artifact paths are gitignored. GitHub Actions was not run
remotely. Use the [isolated test setup](stage-01b1-persistence.md#isolated-integration-tests)
to supply `BADGER_TEST_ADMIN_DSN`, then run:

```sh
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Live dry runs and first imports passed both checksums and full grids:

| Market | Validated | Inserted | Missing | Repeat inserted / unchanged | Revisions |
| --- | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | 186 | 186 | 0 | 0 / 186 | 0 |
| ETHUSDT | 186 | 186 | 0 | 0 / 186 | 0 |
| Total | 372 | 372 | 0 | 0 / 372 | 0 |

Verified retained ZIP hashes:

- BTCUSDT: `a410122c029a07931b639bcd96a304ea81904ab4dfcf2d88c016158190102520`
- ETHUSDT: `15dc4c8e426e7cd57367cd66a14515d87a2e710a14f99471ef03a6c2206419a2`

Read-only inspection compared all 3,348 economic fields (nine per candle) and
source provenance with parsed raw archives using exact Decimal equality. Independent
SQL grid checks found zero gaps; the database contains exactly 372 current candles
and zero revisions. First opens were BTC `93576.00000000` and ETH `3337.78000000`.
Sandboxed downloads initially failed; the two scoped dry runs and imports succeeded
with host network access. Failure manifests are retained alongside successful runs.
Repeat downloads passed checksums and returned 186 unchanged candles per market,
with no inserts, conflicts, stale observations or rejections. All original values,
versions, observation/recording times and provenance remained identical; only
confirmation watermarks advanced. Local before/after audit evidence is in
`artifacts/stage-01b2-verification-before.json` and
`artifacts/stage-01b2-verification-after.json`.
Live 1h ingestion and other months were deliberately not attempted.

## Scope and review

No dependencies were added; downloader, CSV, ZIP, hashing and manifest writing use
the standard library. Persistence continues to use Psycopg. There are no migrations,
new application tables, provider frameworks, cloud storage or backup orchestration.
The exact supplied request is archived in
`prompts/stage-01-market-data/003-historical-archive-ingestion.md`.

Stage 1B.3 remains deferred: full available history in bounded resumable increments,
listing-boundary policy, declared coverage reports and reproducible dataset exports.
REST refresh and deliberate historical revalidation remain Stage 1C. Provider
revisions, local clock accuracy, economic truth and durable evidence retention
remain limitations. Stop for review before expanding historical coverage. No
commit, push, deployment or access to the historical repository occurred.

## File inventory

| Change | Files |
| --- | --- |
| Created: acquisition and orchestration | `src/backtest_badger/archives.py`, `src/backtest_badger/ingestion.py` |
| Created: tests | `tests/test_archives.py`, `tests/test_ingestion.py`, `tests/integration/test_archive_batch.py` |
| Created: guide and exact request | `docs/stage-01b2-archive-ingestion.md`, `prompts/stage-01-market-data/003-historical-archive-ingestion.md` |
| Modified: shared persistence, connection and CLI | `src/backtest_badger/candles.py`, `src/backtest_badger/db.py`, `src/backtest_badger/cli.py` |
| Modified: synthetic fixtures | `tests/conftest.py` |
| Modified: implementation status and API notes | `docs/architecture.md`, `docs/roadmap.md`, `docs/stage-01a-market-data-design.md`, `docs/stage-01b1-persistence.md` |

The final complexity review kept two small ingestion modules, shared locked SQL,
standard-library acquisition and local JSON files. No generic data-quality layer,
provider interface, migration or additional dependency was introduced.

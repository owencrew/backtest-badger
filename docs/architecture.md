# Architecture

## Implemented in Stage 0

- **Python 3.12** and a conventional `src/backtest_badger` package keep development
  familiar and provide access to the scientific Python ecosystem in later stages.
- **uv** manages the virtual environment and locked dependencies. `pyproject.toml`
  defines the installable package and `badger` entry point; `uv.lock` gives local
  development and CI the same dependency resolution.
- **Configuration** is loaded on command execution from environment variables into
  an immutable settings record. Required values, port range and logging level are
  validated without echoing values. Importing the package does not read configuration
  or open connections. uv loads local `.env` files explicitly.
- **CLI** uses standard-library `argparse` and logging. `health` validates settings;
  `db-health` opens a short-lived Psycopg connection, executes `SELECT 1` and closes
  it. Connection and statement timeouts limit waits. Raw driver exceptions are not
  printed. SQLAlchemy is unnecessary for this single query.
- **PostgreSQL 17** runs locally through Docker Compose, bound to localhost and
  persisted in a named volume. PostgreSQL provides relational constraints and SQL
  for future market-data work. The major-version image receives patch updates;
  it is not pinned to an immutable digest. Schema changes are now explicit Alembic
  migrations; Compose initialization settings and existing volumes are unchanged.
- **pytest and Ruff** cover configuration, CLI success/failure, safe error reporting
  and connection lifecycle. GitHub Actions uses the lockfile and no production secrets.

The application runs on the host; only PostgreSQL runs in a container. The path is
`badger → validated settings → optional PostgreSQL probe`. There are no services,
repositories, schedulers, connection pools or feature placeholder packages.

## Implemented in Stage 1B.1

Alembic uses SQLAlchemy only for migration infrastructure and the existing
`POSTGRES_*` settings. Runtime persistence remains plain Psycopg functions in
`backtest_badger.candles`, with no ORM, provider interface or repository framework.

| Table | Identity and contents |
| --- | --- |
| `market` | Smallint identity PK; unique `(venue, market_type, symbol)`; nonempty base/quote and market identity fields. Migration seeds Binance Spot BTCUSDT and ETHUSDT without restricting other identities. |
| `candle` | PK `(market_id, interval_seconds, open_time)`; exact OHLC, base/quote/taker volumes, bigint trades; current positive version; observation/recording times; last-observed watermark; source kind, URL and SHA-256. FK to market. |
| `candle_revision` | Full prior row plus `superseded_at`; PK adds version; FK to current candle identity, with deletion restricted. UPDATE/DELETE trigger protects historical rows. |

All economic decimals use unconstrained `numeric`; all timestamps use
`timestamptz`. Checks enforce UTC 1h/4h alignment, finite positive prices,
OHLC bounds, finite nonnegative volumes, taker bounds, nonnegative bigint trades,
positive versions, finite timestamps, closed-before-observed and
observed-before-recorded ordering. History cannot be superseded before its
recording time or last observation. Source kind is archive/rest, URL is nonblank,
and SHA-256 is 64 lowercase hex digits. PostgreSQL numeric NaN sorts above infinity;
the explicit `< 'Infinity'::numeric` checks reject both. Only PK/unique indexes
exist. Alembic also maintains its conventional `alembic_version` metadata table.

Writers own one short READ COMMITTED transaction on an idle autocommit connection.
`INSERT ... ON CONFLICT DO NOTHING` handles absent-row races; a separate
`SELECT ... FOR UPDATE` sees and locks a competing winner. Economic equality is
an exact field comparison. A strictly newer changed observation copies current
to history, then increments current's version atomically. Shared write/supersession
time comes from `clock_timestamp()` after the lock. Failure rolls both writes back.
No locks surround HTTP requests, and no advisory locks are used.

Identical observations keep economic data, version and original provenance;
only `last_observed_at` may advance. This small metadata exception to a literal
no-op prevents a delayed changed observation from overriding a newer confirmation.
Older changed observations return `stale`; equal-time conflicts raise explicitly.
A → B → A retains versions 1, 2, 3 even when A's content hash repeats. History reads
union current and superseded rows in one PostgreSQL snapshot. Range reads are
ordered and half-open. See the [persistence guide](stage-01b1-persistence.md).

## Implemented in Stage 1B.2

`badger ingest-archive` selects one explicit month, seeded Binance Spot symbol and
native 1h/4h interval. Plain functions in `archives.py` perform bounded HTTPS
acquisition, exact ZIP checksum verification, Decimal/UTC parsing and complete
monthly-grid validation. `ingestion.py` retains ignored local raw evidence and
JSON manifests before invoking persistence; dry runs need no database connection.

`save_candles(..., mode="backfill")` reuses the single-row locked write path within
one archive transaction. Missing rows insert; identical rows retain versions and
original provenance, advancing only a newer observation watermark. Changed or stale
conflicting rows fail the whole batch without overwriting accepted history.
`save_candle()` retains Stage 1B.1 revision behaviour. No schema changes or new
runtime dependencies were needed. January 2025 4h validation imported 186 candles
per market, with zero gaps and zero revisions. See the
[archive ingestion guide](stage-01b2-archive-ingestion.md) for operations and results.

## Implemented in Stage 1B.3

`history.py` iterates explicit completed months chronologically and reuses
`ingest_archive` for one atomic transaction per month, stopping on failure.
`archives.py` recognises only the verified August 2017 native 4h boundary for the
two selected markets; later months require complete calendar grids by default.
An explicit `--allow-source-gaps` range option can atomically persist valid rows
while excluding irregular-close observations and recording absent identities.
Checksums, CSV/economic validity, identity checks and database conflict handling
remain strict; unexpected anomaly classes stop the range for review.
No timestamp repairs or alternative-source replacements are performed.

`research.py` compares the stored UTC grid with PostgreSQL `generate_series`,
reports revisions, local import evidence and persistent source diagnostics, and
streams deterministic exact CSVs. A successful partial commit does not erase a
month's anomalies or imply complete coverage. Export manifests include the full
gap/exclusion diagnostics. Future rolling windows must validate consecutive UTC
identities and explicitly handle interruptions; native boundaries alone do not
prove uninterrupted trading.
Both markets and all coverage queries share one read-only REPEATABLE READ snapshot.
New export directories retain immutable dataset bytes and JSON metadata with their
SHA-256, version/source policy, completeness and implementation revision. Missing
coverage refuses export unless explicitly acknowledged. No schema migration,
provider framework or dependency was added. See the
[full-history guide](stage-01b3-full-history.md) for actual live results and limits.

## Implemented in Stage 1C.1

`rest.py` acquires public native 4h Binance klines with bounded HTTP retries, pacing,
response sizes and page counts. A fixed UTC cutoff, configurable 60-second settling
delay and provider clock check exclude ineligible candles. Strict millisecond/Decimal
parsing retains response bytes before validation. `recent.py` plans seven-day overlap
plus up to 30 days of automatic catch-up; explicit recovery is limited to 180 days.

`badger sync-recent` resolves one market and uses one atomic transaction per page,
reusing the locked persistence SQL. Explicit recent-refresh batch mode permits
revisions only in the fixed seven-day window; older observations can fill holes or
confirm identical values, but cannot replace accepted history. Old/new values and
provenance remain visible for every disagreement, with warnings for archive/REST,
large-price or widespread changes. Dry runs read coverage without database writes.

Response-grid diagnostics and PostgreSQL stored-grid checks remain independent;
a fresh tail does not imply an unbroken range. Raw bodies and run/page evidence live
under ignored `artifacts/rest/`. Historical source diagnostics and frozen exports
remain untouched. Live validation added 75 candles per market through the October
13 12:00 UTC cutoff, with 42 unchanged confirmations per repeat and zero revisions.
See the [REST tail and refresh guide](stage-01c1-rest-tail-and-refresh.md).

## Intended direction (not implemented)

Add modules only when a development stage needs them. Deliberate historical
revalidation remains planned for Stage 1C.2.
Later stages add causal features, chronological ML evaluation, realistic backtests,
forward predictions and separately accounted paper trading.

Stage 1A's [market-data design](stage-01a-market-data-design.md)
selects Binance Spot native UTC 4h candles for BTCUSDT and ETHUSDT: Vision
archives for historical data and the public market-data-only REST API for the
recent tail. Native 1h candles may be added independently when needed. Three
implemented application tables (`market`, `candle`, `candle_revision`) keep current
values and superseded versions. Frozen versioned dataset exports can preserve
research inputs. Stage 1B.3 processes explicit historical ranges in bounded resumable
increments; actual completeness is reported from stored data, not assumed.
Stage 1C.1 implements initial defaults of a
60-second settling delay and seven-day refresh overlap. Raw artifacts/manifests
now live in ignored `artifacts/`, with durable retention addressed as
research and deployment progress. No historical revalidation, derived-candle tables,
parent invalidation machinery or generic provider abstractions exist.

The eventual public dashboard must use read-only database access and clearly label
research, forward predictions and simulated trading. AWS Lightsail on Ubuntu is a
future deployment target; Stage 0 has no production access or deployment setup.
The historical `crypto-trading-platform` repository is outside this project's
implementation boundary and is not required by any component.

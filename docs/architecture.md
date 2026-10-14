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

## Implemented in Stage 1C.2

`revalidation.py` provides separate review and explicitly approved apply commands
for one selected native 4h market and at most 30 historical days. Review reuses
public REST acquisition and strict parsing, retains all raw/invalid evidence and
compares every expected identity against one read-only PostgreSQL snapshot. Plans
and human-readable summaries live under ignored `artifacts/revalidation/`.

Apply verifies the plan fingerprint, implementation, original response bytes/hashes,
acquisition times and complete selected grid before database access. It never
fetches replacement observations. Explicit historical batch mode reuses the existing
SQL and deterministic row-lock order, checking full reviewed rows (including
versions, provenance and watermarks) or reviewed absences under concurrency. Any
mismatch, stale/equal-time conflict or write failure aborts the bounded transaction.
Changed observations preserve history; identical confirmations retain provenance
and only advance a newer watermark, as in existing writers. Ordinary backfill and
seven-day recent authority remain unchanged.

Malformed or partial responses block the whole plan; no synthetic repair, timestamp
normalization or automatic deletion of anomaly diagnostics occurs. Existing frozen
exports remain untouched. Four live review ranges found no economic revisions;
September 2017 zero-duration rows were rejected for both markets. See the
[historical revalidation guide](stage-01c2-historical-revalidation.md).

## Implemented in Stage 2A

`badger prepare-research` operates entirely on the frozen Stage 1B.3 files, without
configuration, database connections or provider requests. `frozen.py` verifies
pinned CSV and manifest hashes, exact schema, Decimal economics, market/UTC
identities, ordering and the full recorded gap/exclusion grid before passing any
rows to `features.py`. Incomplete-source acknowledgement is mandatory.

Five causal features use at most seven consecutive completed candles. One next-4h
close-to-close log-return label requires the next exact identity. Missing intervals
and registered source anomalies invalidate spanning windows; nothing is filled or
repaired. Feature and label availability explicitly include the settling delay.
Calendar train/validation/test boundaries share one availability clock across both
markets, with labels crossing partition ends purged. There is no fitted
preprocessing; zero and train-only mean references provide future comparisons.
Test distributions and scores remain withheld.

New local research directories retain deterministic CSVs and manifests with source
and implementation hashes, definitions, counts, split boundaries and exclusion
audits. The standard library suffices; no dependency or database change was needed.
The initial output has 39,609 eligible rows. This is predictive research, not an
execution model or a reconstruction of historical provider availability. See the
[Stage 2A guide](stage-02a-research-dataset.md) for exact timing, results and limits.

## Implemented in Stage 2B

`badger evaluate-models` verifies the pinned Stage 2A CSV and manifest entirely
offline. `model_data.py` enforces schema/order, identities, availability-based
partitions, label purging, finite model inputs, counts and recorded gap/anomaly
policy. It returns only training and validation rows; test outcomes are never
converted or passed to modelling. Source artifacts remain unchanged.

`evaluation.py` fits separate market models using NumPy and scikit-learn: zero,
training mean, a training-standardised Ridge Pipeline and fixed shallow gradient
boosting with early stopping disabled. Validation-only MAE, RMSE, both baseline
comparisons, training-mean-relative skill, correlation and direction/coverage are
reported with explicit undefined cases. No model search or pooled significance
claim is made. Model fitting and preparation are separate responsibilities.

Exclusively new gitignored experiment directories contain deterministic validation
forecasts without realised targets, a manifest with parameters/runtime/provenance
and output hashes, and a readable summary. Two actual runs reproduced all three
files byte for byte. No model database, serving, signals or execution simulation
is introduced. See the [Stage 2B guide](stage-02b-predictive-baselines.md).

## Implemented in Stage 2C

`badger prepare-execution-data` acquires exactly the 2024 native 1h monthly
archives for BTCUSDT and ETHUSDT, validating January for both before proceeding.
`execution_data.py` reuses strict archive acquisition/checksum/Decimal parsing and
retains source ZIPs, official sidecars, acquisition evidence and a complete hourly
opening-reference grid. These data never enter the canonical PostgreSQL tables.
Offline loading reparses all retained archives and reproduces the CSV exactly.

`forecast_data.py` verifies the pinned Stage 2B bytes, exact schema, identities,
baseline constants, chronology and all 17,560 validation forecast rows. Stage 2A
research CSV and holdout labels are not opened. Signal availability is source open
+ 4h + 60s; entry is the next hourly boundary and exit is source open + 8h. A
12:01 signal therefore enters at 13:00 and exits at 16:00, using independent native
1h opening references rather than the model's close-to-close target return.

`backtest.py` uses ordinary sequential functions and separate 10,000-USDT accounts
for each market/model/scenario. Forecast > 1e-12 enters long; otherwise cash.
Explicit Decimal accounting applies adverse spread/slippage and two-sided fees,
rounds quantity down for affordability, retains residual cash and verifies gross
minus costs equals net equity change. No overlapping positions or leverage exist.
All decisions are fixed before future prices are accessed for fill accounting.

New immutable local outputs retain trades, endpoint realised equity, fixed
frictionless/base/stress metrics, input/implementation hashes and a readable
historical-simulation summary. All four files reproduced byte for byte. Drawdown
observes only realised flat equity; no intrabar marks or Sharpe are invented.
No broker framework, dependency, database, model fitting, forward trading or
deployment was added. See the [Stage 2C guide](stage-02c-execution-backtesting.md)
for acquisition hashes, negative net results, tests and scientific limitations.

## Implemented in Stage 2D

`badger analyse-economics` reads only the pinned Stage 2C manifest, trades,
realised equity and summary. `economics.py` verifies hashes, schemas, the fixed
2024 account grids and cross-scenario trade schedules, then reconciles retained
cash flows and annual metrics without rerunning the engine. No forecast or research
files, native hourly sources, network or database are needed; upstream provenance
is carried from the verified manifest.

Scenario-specific quantities determine gross P&L and cost decomposition. UTC exit
timestamps assign whole round trips to all twelve calendar months; realised
balances carry forward and monthly return factors multiply to annual growth.
Fixed-sequence reference-price ratios provide analytical frictionless growth and
break-even round-trip log-cost budgets. The numerical quantity-floor difference
is measured separately. Zero and training-mean policies provide benchmark context
with explicit exposure/turnover differences; no strategy or cost search occurs.

New gitignored directories retain deterministic monthly and annual diagnostics
CSVs, a manifest with source/output/implementation hashes, and a readable summary.
Existing destinations are refused. Standard-library arithmetic and existing
serialization/validation helpers suffice; no dependency or architecture refactor
was introduced. See the [Stage 2D guide](stage-02d-economic-diagnostics.md) for
results, reconciliation, reproduction and scientific limits.

## Intended direction (not implemented)

Add modules only when a development stage needs them.
Later stages add robustness research, locked holdout evaluation,
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
research and deployment progress. Explicit historical review/apply is implemented;
no automated historical scans, derived-candle tables, parent invalidation machinery
or generic provider abstractions exist.

The eventual public dashboard must use read-only database access and clearly label
research, forward predictions and simulated trading. AWS Lightsail on Ubuntu is a
future deployment target; Stage 0 has no production access or deployment setup.
The historical `crypto-trading-platform` repository is outside this project's
implementation boundary and is not required by any component.

## Implemented in Stage 3A

`badger record-forward --symbol BTCUSDT|ETHUSDT` uses the existing local PostgreSQL
settings and one READ ONLY, REPEATABLE READ snapshot. `forward.py` determines the
current horizon from the actual UTC clock using Stage 1C.1's 60-second eligibility
policy, requests only seven exact native 4h candles, and validates market identity,
economics, versions, provenance and observation timestamps. Stale/incomplete data
fails; ingestion is a separate operator action.

`features.causal_features` supplies the original five ordered features without a
future target. A training-only mode in `model_data.py` verifies the pinned Stage 2A
artifact and skips both held-out partitions before numeric access. Existing
Stage 2B fit/predict helpers deterministically refit the fixed per-market zero,
mean, Ridge and shallow boosting definitions on pre-2024 training only. No fitted
model serialization or new dependencies are introduced.

One complete JSON document retains all four unscored forecasts, source versions
and exact Decimal economics, UTC evidence, ordered features and model/training/
implementation/runtime fingerprints. A synced private staging file, final live
clock check and exclusive atomic hard link publish a stable market/candle identity
under `artifacts/forward-predictions/`. Duplicates and later source revisions cannot
replace it. A directory-sync failure after publication is explicitly uncertain.

`badger verify-forward --record PATH` works offline: checksum/schema/timing checks,
retained-input feature replay and pinned training-only deterministic model replay.
It never substitutes current canonical candles. Local hashes and timestamps are
not independent historical-publication proof or durable backup. See the
[Stage 3A guide](stage-03a-forward-predictions.md). Scheduling, outcome evaluation,
paper trading and deployment remain outside this implementation.

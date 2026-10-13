# Stage 1B.1 — Market candle persistence

Schema and persistence only. No provider requests, ingestion commands, scheduler,
indicators or research pipeline are implemented. Observations in tests are synthetic.

## Migrations

From the repository root with a configured local `.env` and Stage 0 PostgreSQL:

```sh
uv sync --locked
uv run --locked --env-file .env alembic upgrade head
uv run --locked --env-file .env alembic current
uv run --locked alembic history
uv run --locked alembic upgrade head --sql  # inspect SQL without connecting
```

Migration `0001` creates three application tables, their constraints, an immutable
history trigger, and two market seeds. It does not change database settings or
unrelated tables. Repeating `upgrade head` does nothing. An existing conflicting
table causes a transactional failure rather than being adopted or overwritten.
Alembic uses the same `POSTGRES_*` configuration as `badger`; no credentials live
in `alembic.ini`. SQLAlchemy is used only by migrations, without ORM models.

`alembic downgrade base` removes the application tables **and their candle data**.
It is intended here only for disposable-database verification. It uses no CASCADE,
so unexpected dependencies block removal. Upgrade/downgrade/upgrade, including
populated history and preservation of an unrelated table, are integration-tested.
Do not delete development databases or Compose volumes to run these checks.

## Persistence API and selection policy

`backtest_badger.candles` provides:

- `CandleObservation`: an immutable input record containing identity, all economic
  fields, observation time and source details. Use `Decimal` from original strings;
  floats are rejected. Aware non-UTC timestamps are accepted and normalized by
  PostgreSQL; all API result timestamps are UTC.
- `validate_observation(observation)`: checks input types, finite values, OHLC and
  volume bounds, whole trade counts, alignment, closure and source metadata.
- `save_candle(connection, observation)`: returns `inserted`, `unchanged`,
  `revised` or `stale`; conflicting different values at the same observation time
  raise `ObservationConflict`. Other invalid inputs/database failures raise and
  roll back. The caller must handle and report stale/conflicting observations.
- `get_candles(connection, market_id, interval_seconds, start, end)`: ordered
  current candles in `[start, end)`; both bounds must be aware and start < end.
- `get_candle_history(connection, market_id, interval_seconds, open_time)`:
  all versions ordered by version, including current with `superseded_at=None`.
  Missing identities return an empty list. One UNION ALL statement prevents mixed
  snapshots during a concurrent correction.

Resolve `market_id` using `(venue, market_type, symbol)`; never assume seed IDs.
Supply an idle Psycopg connection with `autocommit=True` for writes. Each write
owns and commits its own READ COMMITTED transaction; nesting a write inside a
caller transaction is rejected. Configure bounded waits when opening connections:

```python
import psycopg
from backtest_badger.config import load_settings
from backtest_badger.candles import get_candle_history
from datetime import UTC, datetime

settings = load_settings()
with psycopg.connect(
    host=settings.host,
    port=settings.port,
    dbname=settings.database,
    user=settings.user,
    password=settings.password,
    autocommit=True,
    connect_timeout=5,
    options="-c timezone=UTC -c statement_timeout=5000",
) as connection:
    market_id = connection.execute(
        "SELECT market_id FROM market WHERE venue=%s AND market_type=%s AND symbol=%s",
        ("binance", "spot", "BTCUSDT"),
    ).fetchone()[0]
    versions = get_candle_history(
        connection, market_id, 14400, datetime(2024, 1, 1, tzinfo=UTC)
    )
    print(versions)  # empty until a caller explicitly persists an observation
```

The equality key consists of all four prices, all four volumes and trade count.
Source hashes identify raw response bodies, not candle versions. Identical
economic values preserve version, `observed_at`, `recorded_at`, URL, kind and hash.
Only `last_observed_at` advances on a later identical confirmation. Retrying the
same observation is a complete no-op. A → B → A creates three versions.

Changed values are accepted only if `observed_at` is strictly greater than the
current watermark. Earlier changes return `stale`; equal-time changes conflict.
For example, A observed at 10:00 and reconfirmed at 12:00 cannot be replaced by a
delayed B observed at 11:00. The watermark and comparison happen under a row lock.
Historical rows preserve the watermark as it stood when superseded.

`INSERT ... ON CONFLICT DO NOTHING` serializes missing-row insertion races via the
unique index. A subsequent READ COMMITTED statement sees the committed winner and
locks it with `FOR UPDATE`. Two revisions serialize on that row; each accepted
change archives exactly the previous current version. An older writer arriving
second is explicitly stale. A newer writer arriving second creates another version.
History insertion and current replacement commit or roll back together. No
unconditional conflict update, advisory lock, HTTP request or content-hash dedup.

Observation time is local response-received time, not provider publication time.
Recording time is a server clock sample, not a commit-visibility timestamp. Future
observation timestamps fail rather than poisoning selection. The eventual fetcher
must check clock skew, preserve original observation times on replay, validate
whole pages/files before writes and choose its intended source/revalidation mode.
Per-file all-or-nothing persistence is not part of this per-candle API and must be
decided in Stage 1B.2. The configurable 60-second settling delay is a Stage 1C
eligibility rule; this schema requires only a closed candle. Observation ordering
does not prove which of two conflicting providers' payloads is economically true.

The schema rejects numeric NaN/Infinity explicitly, including in history. This is
verified on PostgreSQL 17 and follows its documented
[numeric comparison semantics](https://www.postgresql.org/docs/17/datatype-numeric.html).
The history trigger rejects row UPDATE/DELETE. It is not a security boundary
against an owner who can disable triggers, truncate or drop tables. Future
deployment must use appropriate database roles. Write via the API; arbitrary
direct SQL on current rows bypasses the version-selection protocol.

## Inspect stored candles

Use the local Compose service and the environment already configured inside it:

```sh
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

```sql
SET TIME ZONE 'UTC';
SELECT * FROM market ORDER BY market_id;
SELECT m.symbol, c.open_time, c.open, c.high, c.low, c.close, c.version
FROM candle c JOIN market m USING (market_id)
WHERE m.venue = 'binance' AND m.market_type = 'spot' AND m.symbol = 'BTCUSDT'
  AND c.interval_seconds = 14400
  AND c.open_time >= '2024-01-01T00:00:00Z'
  AND c.open_time < '2024-01-02T00:00:00Z'
ORDER BY c.open_time;
```

For full provenance and historical values use `get_candle_history` above or
union the matching rows from `candle` and `candle_revision`, ordered by version.
An empty candle table after migration is expected: there is no downloader.

## Isolated integration tests

Never point tests at the development database. Start an independent container
with temporary storage and a dynamically assigned port:

```sh
docker run --detach --rm --name badger-persistence-tests \
  --publish 127.0.0.1::5432 --tmpfs /var/lib/postgresql/data \
  --env POSTGRES_USER=badger_test --env POSTGRES_PASSWORD=disposable_test_only \
  --env POSTGRES_DB=postgres postgres:17
docker exec badger-persistence-tests pg_isready -U badger_test -d postgres
docker port badger-persistence-tests 5432
```

Once ready, substitute the printed port below. These credentials are for this
disposable local server only; no development `.env` is loaded:

```sh
export BADGER_TEST_ADMIN_DSN='host=127.0.0.1 port=PORT dbname=postgres user=badger_test password=disposable_test_only'
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
docker stop badger-persistence-tests
unset BADGER_TEST_ADMIN_DSN
```

Each integration case creates a unique `badger_test_<uuid>` database from
`template0`, migrates only that database, closes connections, then drops only
the database it successfully created. There is no cleanup of arbitrary existing
databases and no fallback to `POSTGRES_DB`. An interrupted process may leave a
test database in the disposable container; stopping that container discards its
temporary storage. Without the explicit DSN, integration tests skip. CI supplies
an isolated PostgreSQL 17 service and runs them as part of ordinary pytest.

Raw artifacts and manifests can initially use ignored local `artifacts/`. Durable
retention/backups and full-history exports belong to later stages. No such
artifacts are generated by this stage.

## Verification and file inventory

Verified locally on 2026-10-13 with PostgreSQL 17.11: 169 tests passed (118 PostgreSQL
integration cases, 51 unit cases including all 26 Stage 0 tests). Ruff lint and
formatting passed. Without an explicit test DSN, the 118 integration cases skipped
and the 51 unit cases passed. Migration tests verified fresh/repeated upgrades,
populated downgrade, re-upgrade, unrelated data preservation, unchanged database
timezone, environment-configured CLI commands and offline SQL generation.
The exact supplied prompt was compared byte for byte with its archive. The
development database was not migrated; no production access, commit or push
occurred. GitHub Actions was configured but not run remotely.

| Change | Files |
| --- | --- |
| Created: migration infrastructure | `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_market_candles.py` |
| Created: persistence | `src/backtest_badger/candles.py` |
| Created: tests | `tests/test_candles.py`, `tests/integration/__init__.py`, `tests/integration/conftest.py`, `tests/integration/test_candles.py`, `tests/integration/test_migration_cli.py` |
| Created: documentation and prompt | `docs/stage-01b1-persistence.md`, `prompts/stage-01-market-data/002-schema-and-persistence.md` |
| Modified: dependencies and CI | `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml` |
| Modified: documentation and fixtures | `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/stage-01a-market-data-design.md`, `.gitignore`, `tests/conftest.py` |

The final complexity review retained plain functions and one observation record,
no ORM or generic repository, only required indexes, and row locks rather than
advisory locks. Remaining limitations are explicit: source selection and clock
trust belong to future ingestion, per-file atomicity is not yet implemented,
database owners can bypass history protections, and durable artifact retention
remains future work. Stage 1B.1 stops here pending implementation review.

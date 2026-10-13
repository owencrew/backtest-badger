"""Market identities and versioned native candles.

Revision ID: 0001
Revises: None
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE market (
            market_id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            venue text NOT NULL CHECK (btrim(venue) <> ''),
            market_type text NOT NULL CHECK (btrim(market_type) <> ''),
            symbol text NOT NULL CHECK (btrim(symbol) <> ''),
            base_asset text NOT NULL CHECK (btrim(base_asset) <> ''),
            quote_asset text NOT NULL CHECK (btrim(quote_asset) <> ''),
            UNIQUE (venue, market_type, symbol)
        )
    """)
    op.execute("""
        CREATE TABLE candle (
            market_id smallint NOT NULL REFERENCES market ON DELETE RESTRICT,
            interval_seconds integer NOT NULL,
            open_time timestamptz NOT NULL,
            open numeric NOT NULL,
            high numeric NOT NULL,
            low numeric NOT NULL,
            close numeric NOT NULL,
            base_volume numeric NOT NULL,
            quote_volume numeric NOT NULL,
            trade_count bigint NOT NULL CHECK (trade_count >= 0),
            taker_buy_base_volume numeric NOT NULL,
            taker_buy_quote_volume numeric NOT NULL,
            version integer NOT NULL CHECK (version > 0),
            observed_at timestamptz NOT NULL,
            recorded_at timestamptz NOT NULL,
            last_observed_at timestamptz NOT NULL,
            source_kind text NOT NULL CHECK (source_kind IN ('archive', 'rest')),
            source_url text NOT NULL CHECK (btrim(source_url) <> ''),
            source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
            PRIMARY KEY (market_id, interval_seconds, open_time),
            CONSTRAINT candle_interval CHECK (interval_seconds IN (3600, 14400)),
            CONSTRAINT candle_alignment CHECK (
                mod(extract(epoch FROM open_time), interval_seconds) = 0
            ),
            CONSTRAINT candle_times CHECK (
                isfinite(open_time) AND isfinite(observed_at)
                AND isfinite(recorded_at) AND isfinite(last_observed_at)
                AND observed_at >= open_time + interval_seconds * INTERVAL '1 second'
                AND recorded_at >= observed_at AND last_observed_at >= observed_at
            ),
            CONSTRAINT candle_ohlc CHECK (
                low <= open AND open <= high AND low <= close AND close <= high
            ),
            CONSTRAINT candle_taker_bounds CHECK (
                taker_buy_base_volume <= base_volume
                AND taker_buy_quote_volume <= quote_volume
            )
        )
    """)
    # PostgreSQL numeric NaN compares greater than Infinity. A positive lower
    # bound alone admits both; the strict Infinity upper bound excludes them.
    for column in ("open", "high", "low", "close"):
        op.execute(f"""
            ALTER TABLE candle ADD CONSTRAINT candle_{column}_finite_positive
            CHECK ({column} > 0 AND {column} < 'Infinity'::numeric)
        """)
    for column in (
        "base_volume",
        "quote_volume",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ):
        op.execute(f"""
            ALTER TABLE candle ADD CONSTRAINT candle_{column}_finite_nonnegative
            CHECK ({column} >= 0 AND {column} < 'Infinity'::numeric)
        """)
    # LIKE copies columns, NOT NULLs and CHECKs, but not keys or identity/defaults.
    op.execute("""
        CREATE TABLE candle_revision (
            LIKE candle INCLUDING CONSTRAINTS,
            superseded_at timestamptz NOT NULL,
            PRIMARY KEY (market_id, interval_seconds, open_time, version),
            FOREIGN KEY (market_id, interval_seconds, open_time)
                REFERENCES candle ON DELETE RESTRICT,
            CONSTRAINT revision_times CHECK (
                isfinite(superseded_at) AND superseded_at >= recorded_at
                AND superseded_at >= last_observed_at
            )
        )
    """)
    op.execute("""
        CREATE FUNCTION reject_candle_revision_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Candle revisions are immutable'
                USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER candle_revision_immutable
        BEFORE UPDATE OR DELETE ON candle_revision
        FOR EACH ROW EXECUTE FUNCTION reject_candle_revision_mutation()
    """)
    op.execute("""
        INSERT INTO market (venue, market_type, symbol, base_asset, quote_asset)
        VALUES ('binance', 'spot', 'BTCUSDT', 'BTC', 'USDT'),
               ('binance', 'spot', 'ETHUSDT', 'ETH', 'USDT')
    """)


def downgrade():
    # Deliberately no CASCADE: unexpected dependent objects must block removal.
    op.execute("DROP TABLE candle_revision")
    op.execute("DROP FUNCTION reject_candle_revision_mutation()")
    op.execute("DROP TABLE candle")
    op.execute("DROP TABLE market")

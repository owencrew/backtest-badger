from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backtest_badger.candles import CandleObservation


@pytest.fixture
def config_env():
    return {
        "POSTGRES_DB": "test_badger",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "private-test-password",
    }


@pytest.fixture
def candle_observation():
    D = Decimal
    OPEN = datetime(2024, 1, 1, tzinfo=UTC)
    OBSERVED = OPEN + timedelta(days=1)
    return CandleObservation(
        market_id=1,
        interval_seconds=14400,
        open_time=OPEN,
        open=D("42000.123456789012345678901234567890123456789"),
        high=D("43000"),
        low=D("41000"),
        close=D("42500.000000000000000000000000000000000000001"),
        base_volume=D("123.000000000000000000000000000000000000001"),
        quote_volume=D("5200000.123456789012345678901234567890123456789"),
        trade_count=1234,
        taker_buy_base_volume=D("60.0123456789012345678901234567890123456789"),
        taker_buy_quote_volume=D("2500000.123456789012345678901234567890123456789"),
        observed_at=OBSERVED,
        source_kind="archive",
        source_url="https://example.invalid/synthetic.zip",
        source_sha256="a" * 64,
    )

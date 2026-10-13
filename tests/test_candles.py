from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from backtest_badger.candles import validate_observation


@pytest.mark.parametrize(
    "changes",
    [
        {"market_id": 0},
        {"market_id": True},
        {"interval_seconds": 7200},
        {"interval_seconds": 3600.0},
        {"open_time": datetime(2024, 1, 1)},
        {"observed_at": datetime(2024, 1, 2)},
        {"open": 42000.1},
        {"high": Decimal("NaN")},
        {"low": Decimal("sNaN")},
        {"close": Decimal("Infinity")},
        {"base_volume": Decimal("-Infinity")},
        {"low": Decimal(0)},
        {"quote_volume": Decimal(-1)},
        {"open": Decimal(44000)},
        {"close": Decimal(40000)},
        {"taker_buy_base_volume": Decimal(1000)},
        {"taker_buy_quote_volume": Decimal(99999999)},
        {"trade_count": -1},
        {"trade_count": 2**63},
        {"trade_count": 1.5},
        {"trade_count": True},
        {"source_kind": "unknown"},
        {"source_url": " "},
        {"source_sha256": "A" * 64},
    ],
)
def test_reject_invalid_observations(candle_observation, changes):
    with pytest.raises(ValueError):
        validate_observation(replace(candle_observation, **changes))


def test_alignment_and_closure(candle_observation):
    for opened in (
        candle_observation.open_time + timedelta(microseconds=1),
        candle_observation.open_time + timedelta(hours=1),
    ):
        with pytest.raises(ValueError, match="align"):
            validate_observation(replace(candle_observation, open_time=opened))
    with pytest.raises(ValueError, match="closed"):
        validate_observation(
            replace(candle_observation, observed_at=candle_observation.open_time)
        )
    validate_observation(candle_observation)
    validate_observation(
        replace(
            candle_observation,
            base_volume=Decimal(0),
            quote_volume=Decimal(0),
            taker_buy_base_volume=Decimal(0),
            taker_buy_quote_volume=Decimal(0),
            trade_count=0,
        )
    )

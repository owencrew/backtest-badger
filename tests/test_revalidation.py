from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backtest_badger import revalidation as rv
from backtest_badger.candles import ECONOMIC_FIELDS
from backtest_badger.rest import STEP

START = datetime(2024, 1, 1, tzinfo=UTC)


@pytest.mark.parametrize(
    "start,end",
    [
        (START, START),
        (START, START + timedelta(days=31)),
        (START.replace(tzinfo=None), START + STEP),
        (START + timedelta(seconds=1), START + STEP),
        (START, START + timedelta(hours=5)),
        (START, START + STEP),
    ],
)
def test_invalid_bounds(start, end):
    with pytest.raises(ValueError):
        rv.validate_range("BTCUSDT", start, end, START + STEP)


def test_maximum_range_and_exact_settling_cutoff():
    end = START + timedelta(days=30)
    rv.validate_range("BTCUSDT", START, end, end + timedelta(seconds=60))
    with pytest.raises(ValueError):
        rv.validate_range("BTCUSDT", START, end, end + timedelta(seconds=59))


@pytest.mark.parametrize("field", ECONOMIC_FIELDS)
def test_all_nine_exact_economic_differences(
    field, candle_observation, historical_payload
):
    response = historical_payload([candle_observation])
    old = asdict(candle_observation)
    old["last_observed_at"] = old["observed_at"]
    # Tiny Decimal difference beyond the default arithmetic context's precision.
    old[field] = (
        old[field] + 1 if field == "trade_count" else Decimal(str(old[field]) + "1")
    )
    analysis = rv.compare(response, 1, START, START + STEP, {START: old})
    assert analysis["counts"]["changed"] == 1
    assert analysis["entries"][0]["changed_fields"] == [field]
    assert analysis["entries"][0]["proposed"]["source_sha256"] == response.sha256


def test_fingerprint_is_order_independent_but_content_sensitive():
    assert rv.fingerprint({"a": 1, "b": 2}) == rv.fingerprint({"b": 2, "a": 1})
    assert rv.fingerprint({"a": 1}) != rv.fingerprint({"a": 2})


def test_apply_requires_approval_before_artifacts_or_database(tmp_path):
    with pytest.raises(ValueError, match="approve-changes"):
        rv.apply_revalidation(tmp_path / "missing.json", None)
    assert not list(tmp_path.iterdir())

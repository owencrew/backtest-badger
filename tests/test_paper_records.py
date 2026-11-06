"""Pure evidence round trips for the revision 0002 adapter."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import pytest

from backtest_badger import paper_records as records
from backtest_badger.paper_types import (
    STEP,
    Action,
    D,
    Decision,
    Filters,
    Forecast,
    Portfolio,
    Quote,
)

T = datetime(2026, 1, 1, tzinfo=UTC)
H = records.fingerprint("fabricated")


def test_versioned_configuration_and_scoped_identity():
    config = records.configuration("ETHUSDT", H, "fabricated/α")
    shuffled = dict(reversed(config.items()))
    assert records.canonical(config) == records.canonical(shuffled)
    assert records.fingerprint(records.canonical(config)) != records.fingerprint(
        records.canonical(config | {"symbol": "BTCUSDT"})
    )
    pid = uuid4()
    assert records.identity(pid, "order", "a") == records.identity(pid, "order", "a")
    assert (
        len(
            {
                records.identity(pid, "order", "a"),
                records.identity(pid, "decision", "a"),
                records.identity(uuid4(), "order", "a"),
                records.identity(pid, "order", "b"),
            }
        )
        == 4
    )


@pytest.mark.parametrize("elapsed", [None, D("0.00000000000000000001"), D("2")])
def test_quote_roundtrip_preserves_exact_duration_and_original_bytes(elapsed):
    p = Portfolio("fabricated", "ETHUSDT", T, H, H, H)
    body = (
        b'{"symbol":"ETHUSDT","bidPrice":"1","askPrice":"2","askQty":"4","bidQty":"3"}'
    )
    original = Quote(
        "fabricated-quote",
        "fabricated-run",
        p.symbol,
        T,
        T,
        D(1),
        D(2),
        D(3),
        D(4),
        sha256(body).hexdigest(),
        body,
        "https://fabricated.invalid",
        elapsed_seconds=elapsed,
    )
    assert records.quote(p, records.quote_fields(original)) == original


@pytest.mark.parametrize("maximum", [None, D("123456789.000000000000000001")])
def test_effective_filter_roundtrip(maximum):
    f = Filters("ETHUSDT", T, H, D("0.025"), D("0.075"), D(10000), D(1), maximum)
    assert records.filters(records.filter_fields(f)) == f


@pytest.mark.parametrize(
    "prediction,expected",
    [("0.000000000001", 0), ("0.000000000001000000000000000000001", 1)],
)
def test_original_forecast_and_sticky_reference_survive_mapping(prediction, expected):
    p = Portfolio("fabricated", "ETHUSDT", T, H, H, H)
    at = T + timedelta(minutes=2)
    forecast = Forecast(
        p, "fabricated-original", T - STEP, at, at, D(prediction), H, H, H, H
    )
    d = Decision(
        "fabricated-decision",
        p,
        at,
        Action.IGNORED_EXIT_PENDING,
        "sticky_exit",
        0,
        T - STEP,
        forecast,
        obligation_id="earlier-exit",
    )
    fields = records.decision_fields(
        uuid4(), d, "fabricated/original.json", "ridge-original"
    )
    assert fields["target_exposure"] == expected
    assert records.decision(p, fields) == d
    assert records.decision(p, fields | {"obligation_key": None}) == replace(
        d, obligation_id=None
    )

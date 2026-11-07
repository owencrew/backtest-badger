from datetime import timedelta, timezone

import pytest

from backtest_badger import paper_fixture as fx
from backtest_badger.paper_clock import Clock, Sample, duration


def test_independent_timing_and_invocation_identity():
    start = Sample(fx.OPEN, 100, 120)
    end = Sample(fx.OPEN + timedelta(seconds=2), 2000000100, 2000000120)
    assert duration(start, end) == 2
    assert fx.fixed_clock(fx.OPEN).run_id != fx.fixed_clock(fx.OPEN).run_id


@pytest.mark.parametrize(
    "wall,ticks",
    [
        (fx.OPEN.replace(tzinfo=None), 0),
        (fx.OPEN.astimezone(timezone(timedelta(hours=1))), 0),
        (fx.OPEN, -1),
    ],
)
def test_invalid_samples(wall, ticks):
    with pytest.raises(ValueError):
        Clock(lambda: wall, lambda: ticks).now()


@pytest.mark.parametrize(
    "seconds,ticks", [(1, 1), (-1, 1000), (0, -1), (0, 2000000000)]
)
def test_reversal_or_jump(seconds, ticks):
    with pytest.raises(ValueError):
        duration(
            Sample(fx.OPEN, 0, 0),
            Sample(fx.OPEN + timedelta(seconds=seconds), ticks, ticks),
        )

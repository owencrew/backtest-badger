"""UTC observations bracketed by monotonic samples in one worker invocation."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from time import monotonic_ns
from uuid import uuid4

from backtest_badger.paper_types import require, utc


@dataclass(frozen=True)
class Sample:
    wall: datetime
    before_ns: int
    after_ns: int


def duration(start, end):
    """Allow sampling uncertainty and UTC's microsecond representation only."""
    wall_us = (utc(end.wall) - utc(start.wall)) // timedelta(microseconds=1)
    low = end.before_ns - start.after_ns
    high = end.after_ns - start.before_ns
    require(
        0 <= start.before_ns <= start.after_ns <= end.before_ns <= end.after_ns,
        "Monotonic clock reversal.",
    )
    require(
        wall_us >= 0 and low - 1000 <= wall_us * 1000 <= high + 1000,
        "Inconsistent wall and monotonic clocks.",
    )
    return Decimal(end.after_ns - start.after_ns).scaleb(-9)


class Clock:
    def __init__(self, wall=lambda: datetime.now(UTC), ticks=monotonic_ns):
        self.wall = wall
        self.ticks = ticks
        self.previous = None
        self.run_id = uuid4().hex
        self.claimed = False

    def begin_cycle(self):
        require(not self.claimed, "Worker invocation identity already used.")
        self.claimed = True

    def sample(self):
        before = self.ticks()
        sample = Sample(utc(self.wall()), before, self.ticks())
        require(0 <= before <= sample.after_ns, "Monotonic clock reversal.")
        if self.previous is not None:
            duration(self.previous, sample)
        self.previous = sample
        return sample

    def now(self):
        return self.sample().wall

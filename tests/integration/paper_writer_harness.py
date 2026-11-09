"""Fabricated market transport and independently advancing UTC/monotonic samples."""

from datetime import timedelta
from time import monotonic_ns

import psycopg

from backtest_badger import paper_fixture as fx
from backtest_badger.paper_clock import Clock
from backtest_badger.paper_market_data import FILTERS, Market
from backtest_badger.paper_operations import ClockHealth
from backtest_badger.paper_recovery import recover
from backtest_badger.paper_writer import Writer, WriterConfig


def transport(endpoint, symbol, clock, *, depth="1000"):
    p = Market(symbol)
    if endpoint == FILTERS:
        from types import SimpleNamespace

        return fx.filter_source(
            SimpleNamespace(symbol=symbol, base_asset=symbol[:-4]), clock
        )
    return fx.response(
        endpoint,
        p,
        clock,
        dict(symbol=symbol, bidPrice="100", askPrice="100", bidQty=depth, askQty=depth),
    )


def timed_writer(dsn, pid, root, at, *, acquire=transport, checkpoint=lambda _: None):
    with psycopg.connect(dsn, autocommit=True) as c:
        return writer_on(c, pid, root, at, acquire=acquire, checkpoint=checkpoint)


def writer_on(
    c, pid, root, at, *, acquire=transport, checkpoint=lambda _: None, health=None
):
    p = recover(c, pid).state.account.portfolio
    runtime = root / "runtime"
    runtime.mkdir(mode=0o700, exist_ok=True)
    config = WriterConfig(
        pid,
        p.symbol,
        p.config_sha256,
        root / "records",
        root / "operations",
        root / "private",
        runtime,
    )
    epoch = monotonic_ns()
    clock = Clock(lambda: at + timedelta(microseconds=(monotonic_ns() - epoch) // 1000))
    if health is None:
        health = ClockHealth(True, at, timedelta(milliseconds=1))
    return Writer(c, config, clock, health, acquire, checkpoint=checkpoint).run()

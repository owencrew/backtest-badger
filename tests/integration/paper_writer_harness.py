"""Fabricated market transport and independently advancing UTC/monotonic samples."""

import socket
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic_ns

import psycopg

from backtest_badger import paper_fixture as fx
from backtest_badger.paper_archive_service import accept_object
from backtest_badger.paper_artifacts import ArchiveView
from backtest_badger.paper_clock import Clock
from backtest_badger.paper_market_data import FILTERS, Market
from backtest_badger.paper_operations import ClockHealth
from backtest_badger.paper_production import verified_cycle
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


def timed_writer(
    dsn,
    pid,
    root,
    at,
    *,
    acquire=transport,
    checkpoint=lambda _: None,
    approval=None,
    archive_view=None,
):
    with psycopg.connect(dsn, autocommit=True) as c:
        return writer_on(
            c,
            pid,
            root,
            at,
            acquire=acquire,
            checkpoint=checkpoint,
            approval=approval,
            archive_view=archive_view,
        )


def writer_on(
    c,
    pid,
    root,
    at,
    *,
    acquire=transport,
    checkpoint=lambda _: None,
    health=None,
    approval=None,
    archive_view=None,
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
        archive_view or root / "private",
        runtime,
    )
    epoch = monotonic_ns()
    clock = Clock(lambda: at + timedelta(microseconds=(monotonic_ns() - epoch) // 1000))
    if health is None:
        health = ClockHealth(True, at, timedelta(milliseconds=1))
    if approval is not None:
        return verified_cycle(c, approval, config, clock, health, acquire)
    return Writer(c, config, clock, health, acquire, checkpoint=checkpoint).run()


@contextmanager
def archive_service(vault):
    # Keep the socket address below the macOS sockaddr_un limit.
    with (
        TemporaryDirectory(dir="/tmp") as temp,
        socket.socket(socket.AF_UNIX) as server,
        ThreadPoolExecutor(1) as pool,
    ):
        address = str(Path(temp) / "archive.sock")
        server.bind(address)
        server.listen()
        server.settimeout(0.1)
        stopped = Event()

        def serve():
            while not stopped.is_set():
                try:
                    conn, _ = server.accept()
                except TimeoutError:
                    continue
                with conn:
                    conn.settimeout(3)
                    accept_object(conn, vault)

        job = pool.submit(serve)
        try:
            yield ArchiveView(vault, address)
        finally:
            stopped.set()
            job.result(timeout=5)

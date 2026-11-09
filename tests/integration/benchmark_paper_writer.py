"""Opt-in fabricated writer measurements with the Stage 4D.2 history generator."""

import json
import resource
import sys
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg

from backtest_badger import paper_fixture as fx
from backtest_badger.paper_recovery import recover
from backtest_badger.paper_types import STEP

from .benchmark_paper import MIN, advance, establish, remaining_journals
from .paper_roles import isolated_roles, upgrade
from .paper_workload import originals, portfolio, publish_slot
from .paper_writer_harness import timed_writer


def concurrent_fills(dsn, states, root, at, scenario):
    with ThreadPoolExecutor(2) as pool:
        jobs = {
            s: pool.submit(timed_writer, dsn, pid, root, at)
            for s, (pid, _) in states.items()
        }
        for symbol, job in jobs.items():
            result = job.result()
            result["peak_rss_mib"] = resource.getrusage(
                resource.RUSAGE_SELF
            ).ru_maxrss / (1048576 if sys.platform == "darwin" else 1024)
            print("FABRICATED_WRITER", scenario, symbol, json.dumps(result), flush=True)
            assert result["result"] == "FILLED"
            assert result["timings"]["receipt_to_admission_s"] <= 1


def test_writer_year(test_admin, tmp_path):
    private, manifest = originals(tmp_path)
    with isolated_roles(*test_admin, uuid4().hex) as (dsns, roles):
        upgrade(dsns, roles)
        with psycopg.connect(dsns["operator"], autocommit=True) as operator:
            states = {
                s: establish(operator, portfolio(s), private, manifest)
                for s in ("BTCUSDT", "ETHUSDT")
            }
        with psycopg.connect(dsns["worker"], autocommit=True) as worker:
            for n in range(365 * 6):
                opened = fx.OPEN + n * STEP
                checkpoint = n + 1 in {180, 2190}
                positive = n + 2 in {180, 2190} or (n % 12 < 6 and not checkpoint)
                observed = publish_slot(
                    tmp_path,
                    opened,
                    dict.fromkeys(states, 0.001 if positive else -0.001),
                )
                for symbol, (pid, state) in states.items():
                    states[symbol] = (
                        pid,
                        advance(
                            worker, pid, state, n, observed[symbol], checkpoint, private
                        ),
                    )
                remaining_journals(
                    tmp_path, observed["BTCUSDT"], opened + STEP, range(1, 240, 5)
                )
                if checkpoint:
                    concurrent_fills(
                        dsns["worker"],
                        states,
                        tmp_path,
                        fx.ISSUED + n * STEP + 15 * MIN,
                        f"retry-{n + 1}",
                    )
                    for s, (pid, _) in states.items():
                        states[s] = pid, recover(worker, pid).state
            print(
                "FABRICATED journal count",
                len(list((tmp_path / "operations").iterdir())),
            )
            for n, signal in enumerate([0.001, -0.001, 0.001], start=2190):
                publish_slot(
                    tmp_path, fx.OPEN + n * STEP, dict.fromkeys(states, signal)
                )
                concurrent_fills(
                    dsns["worker"],
                    states,
                    tmp_path,
                    fx.ISSUED + n * STEP,
                    f"forecast-{n}",
                )

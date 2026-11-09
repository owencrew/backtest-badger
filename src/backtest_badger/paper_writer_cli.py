"""Run one local staging cycle against an existing fabricated account."""

import argparse
import fcntl
import json
import math
import os
import re
import signal
import stat
from datetime import datetime, timedelta
from pathlib import Path
from threading import Timer
from uuid import UUID

import psycopg
from psycopg.conninfo import conninfo_to_dict

from backtest_badger import forward
from backtest_badger.forward_scoring_operations import write_snapshot
from backtest_badger.paper_artifacts import directory, read_original
from backtest_badger.paper_clock import Clock
from backtest_badger.paper_market_data import MarketError, fetch, unique
from backtest_badger.paper_operations import ClockHealth, Incident
from backtest_badger.paper_types import digest, require, utc
from backtest_badger.paper_writer import Writer, WriterConfig


def private_directory(path):
    with directory(path) as fd:
        info = os.fstat(fd)
        require(
            info.st_uid == os.getuid() and not info.st_mode & 0o077,
            "Expected a private runtime directory.",
        )


def read_json(path, *, secret=False):
    with directory(path.parent) as fd:
        if secret:
            info = os.stat(path.name, dir_fd=fd, follow_symlinks=False)
            require(
                stat.S_ISREG(info.st_mode)
                and info.st_uid == os.getuid()
                and not info.st_mode & 0o077,
                "Expected owner-only reviewed file.",
            )
        return json.loads(read_original(fd, path.name, 65536), object_pairs_hook=unique)


def local_settings(path):
    data = read_json(path, secret=True)
    require(
        set(data)
        == {
            "mode",
            "dsn",
            "portfolio_id",
            "symbol",
            "config_sha256",
            "records",
            "journals",
            "archive",
            "runtime",
            "clock_observation",
        }
        and data["mode"] == "staging-once",
        "Expected a reviewed staging configuration.",
    )
    params = conninfo_to_dict(data["dsn"])
    require(
        not any(name.startswith("PG") for name in os.environ)
        and set(params) == {"host", "port", "dbname", "user", "password"}
        and params["host"] in {"127.0.0.1", "::1"}
        and params["user"]
        and params["password"]
        and params["port"].isascii()
        and params["port"].isdecimal()
        and 1 <= int(params["port"]) <= 65535
        and re.fullmatch(r"badger_test_[0-9a-f]{32}", params["dbname"]),
        "An explicit disposable loopback test database is required.",
    )
    require(data["symbol"] in {"BTCUSDT", "ETHUSDT"}, "Unknown staging market.")
    digest(data["config_sha256"])
    paths = [Path(data[name]) for name in ("records", "journals", "archive", "runtime")]
    for p in paths:
        require(
            p.is_absolute()
            and p.resolve(strict=True) == p
            and all(p != q and not p.is_relative_to(q) for q in paths if q is not p),
            "Expected separate absolute evidence directories.",
        )
        with directory(p):
            pass
    records, journals, archive, runtime = paths
    for path in (archive, runtime):
        require(
            not any(
                (parent / ".git").exists() or (parent / "pyproject.toml").is_file()
                for parent in (path, *path.parents)
            ),
            "Keep private writer data outside the release tree.",
        )
    private_directory(archive)
    private_directory(runtime)
    return (
        WriterConfig(
            UUID(data["portfolio_id"]),
            data["symbol"],
            data["config_sha256"],
            records,
            journals,
            archive,
            runtime,
        ),
        runtime,
        Path(data["clock_observation"]),
        params,
    )


def trusted_clock_path(path):
    """Only the external clock observer may replace its measurement."""
    if os.geteuid() == 0 or not path.is_absolute():
        return False
    for item in (*reversed(path.parents), path):
        info = item.lstat()
        if info.st_uid != 0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):
            return False
    return True


def clock_health(path):
    """Read the explicit external clock measurement."""
    try:
        if not trusted_clock_path(path):
            return None
        observation = read_json(path)
        require(
            set(observation) == {"synchronised", "sampled_at", "uncertainty_ms"}
            and type(observation["uncertainty_ms"]) in (float, int),
            "Expected a clock health observation.",
        )
        return ClockHealth(
            observation["synchronised"],
            utc(datetime.fromisoformat(observation["sampled_at"])),
            timedelta(milliseconds=observation["uncertainty_ms"]),
        )
    except (OSError, ValueError, OverflowError, TypeError, KeyError):
        return None


def shared_provider(runtime, transport=fetch):
    """Share Retry-After exclusions across market processes and restarts."""
    cooldown = runtime / "binance-cooldown.json"

    def acquire(endpoint, symbol, clock):
        with directory(runtime) as fd:
            lock = os.open(
                "binance.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=fd
            )
            try:
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    saved = json.loads(read_original(fd, cooldown.name, 4096))
                except FileNotFoundError:
                    saved = None
                if saved is not None:
                    pin = saved.pop("content_sha256")
                    require(
                        forward.sha256(forward.canonical(saved)) == pin,
                        "Damaged provider cooldown.",
                    )
                    wait = (
                        utc(datetime.fromisoformat(saved["until"])) - clock.now()
                    ).total_seconds()
                    if wait > 0:
                        raise MarketError(
                            "provider_cooldown", saved["status"], math.ceil(wait)
                        )
                try:
                    return transport(endpoint, symbol, clock)
                except MarketError as exc:
                    if exc.status in {418, 429}:
                        until = clock.now() + timedelta(
                            seconds=max(300, exc.retry_after or 0)
                        )
                        write_snapshot(
                            cooldown, {"status": exc.status, "until": until.isoformat()}
                        )
                    raise
            finally:
                os.close(lock)

    return acquire


class Cancelled(BaseException):
    pass


def restricted_account(conn, config):
    row = conn.execute(
        "SELECT current_user=session_user AND NOT (rolsuper OR rolbypassrls "
        "OR rolcreatedb OR "
        "rolcreaterole OR rolreplication OR rolinherit) AND NOT EXISTS (SELECT FROM "
        "pg_auth_members WHERE member=pg_roles.oid) AND NOT "
        "has_table_privilege(current_user, "
        "'paper_portfolio','INSERT') AND NOT has_table_privilege(current_user,"
        "'paper_ledger_entry',"
        "'DELETE') AND has_table_privilege(current_user,'paper_decision','INSERT') "
        "FROM pg_roles WHERE rolname=current_user"
    ).fetchone()
    require(row == (True,), "Expected the staging worker login.")
    cohort = conn.execute(
        "SELECT strategy_config->>'cohort' FROM paper_portfolio WHERE portfolio_id=%s",
        (config.portfolio_id,),
    ).fetchone()
    require(
        cohort and cohort[0].startswith("fabricated-"),
        "Expected a fabricated staging portfolio.",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["staging-once"])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    clock = Clock()
    config = None

    def cancel(_signum, _frame):
        raise Cancelled()

    previous = signal.signal(signal.SIGTERM, cancel)
    watchdog = Timer(240, lambda: os.kill(os.getpid(), signal.SIGTERM))
    watchdog.daemon = True
    watchdog.start()
    try:
        config, runtime, health_path, params = local_settings(args.config)
        with psycopg.connect(
            **params,
            autocommit=True,
            connect_timeout=3,
            sslmode="disable",
            options=(
                "-c search_path=pg_catalog,public,pg_temp -c statement_timeout=10000"
            ),
        ) as conn:
            restricted_account(conn, config)
            result = Writer(
                conn,
                config,
                clock,
                lambda: clock_health(health_path),
                shared_provider(runtime),
            ).run()
        print(json.dumps(result))
        return int(
            result["result"] == "STOPPED"
            or any(i["severity"] == "integrity" for i in result["incidents"])
        )
    except (Cancelled, KeyboardInterrupt):
        incident = (
            Incident(
                "worker_interrupted", config.portfolio_id, config.portfolio_id
            ).report(clock.now())
            if config
            else None
        )
        print(
            json.dumps(
                dict(result="INTERRUPTED", run_id=clock.run_id, incident=incident)
            )
        )
        return 2
    except (OSError, psycopg.Error, ValueError, KeyError, TypeError):
        print(
            json.dumps(
                dict(result="CONFIGURATION_OR_CONNECTION_FAILED", run_id=clock.run_id)
            )
        )
        return 1
    finally:
        watchdog.cancel()
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    raise SystemExit(main())

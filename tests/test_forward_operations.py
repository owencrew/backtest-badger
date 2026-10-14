"""Synthetic clocks, refreshes and training; no live provider requests."""

import json
import subprocess
import sys
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg
import pytest
from test_evaluation import research_source  # noqa: F401
from test_forward import NOW, OPENED, sample_window, synthetic_fit  # noqa: F401

from backtest_badger import cli, forward
from backtest_badger import forward_operations as ops
from backtest_badger.config import load_settings


@pytest.fixture
def cycle(tmp_path, monkeypatch, synthetic_fit, config_env):  # noqa: F811
    time = [NOW]
    calls = []
    monkeypatch.setattr(ops, "load_settings", lambda: load_settings(config_env))
    monkeypatch.setattr(ops, "connect_database", lambda _: nullcontext(None))
    monkeypatch.setattr(forward, "read_window", lambda c, s, t: sample_window(s))

    def refresh(symbol, settings, *, artifacts, result):
        calls.append(symbol)
        result.update(
            status="complete",
            source_complete=True,
            failed_pages=0,
            incomplete_pages=0,
            latest_eligible_open=OPENED.isoformat(),
            fixed_run_time=time[0].isoformat(),
            finished_at=time[0].isoformat(),
            coverage=dict(
                stored_complete=True,
                freshness="fresh",
                latest_stored_open=OPENED.isoformat(),
            ),
        )
        return 0

    monkeypatch.setattr(ops, "sync_recent", refresh)
    kwargs = dict(
        records=tmp_path / "records",
        operations=tmp_path / "operations",
        artifacts=tmp_path,
        source=synthetic_fit[0],
        clock=lambda: time[0],
    )

    def run():
        code = ops.run_cycle(**kwargs)
        journals = [
            json.loads(p.read_bytes()) for p in kwargs["operations"].glob("*.json")
        ]
        time[0] += timedelta(microseconds=1)
        return code, journals

    return run, kwargs, time, calls, refresh


def report(kwargs):
    return ops.status_report(
        **{k: kwargs[k] for k in ("records", "operations", "clock")}
    )


@pytest.mark.parametrize("hour", range(0, 24, 4))
@pytest.mark.parametrize(
    "seconds,expected",
    [
        (0, "not-yet-eligible"),
        (59.999999, "not-yet-eligible"),
        (60, "due"),
        (959.999999, "due"),
        (960, "missed"),
    ],
)
def test_all_utc_boundaries(hour, seconds, expected, monkeypatch, tmp_path):
    boundary = datetime(2026, 10, 15, hour, tzinfo=UTC)
    now = boundary + timedelta(seconds=seconds)
    opened = ops.horizon(now)
    assert opened == boundary - forward.STEP
    calls = []

    def config():
        calls.append("config")
        raise ValueError("synthetic")

    monkeypatch.setattr(ops, "load_settings", config)
    result = ops.collect_market(
        "BTCUSDT",
        opened,
        now,
        records=tmp_path,
        source=tmp_path,
        artifacts=tmp_path,
        clock=lambda: now,
    )
    if expected == "due":
        assert calls == ["config"] and result["error_category"] == "configuration"
    else:
        assert result["status"] == expected and calls == []


def test_real_recording_replay_and_repeat_without_work(cycle, monkeypatch):
    run, kwargs, _, calls, _ = cycle
    code, journals = run()
    assert code == 0 and calls == list(forward.SYMBOLS)
    first = journals[0]
    originals = {p: p.read_bytes() for p in kwargs["records"].glob("*.json")}
    for item in first["markets"].values():
        assert item["status"] == "recorded" and item["verification"] == "replayed"
        assert item["refresh"] == "complete_fresh"
        assert item["issuance_delay_seconds"] == 60
        assert forward.verify_forward(
            Path(item["record_path"]), source=kwargs["source"]
        )["verified"]
    for module, name in (
        (forward, "fit_forward"),
        (ops, "sync_recent"),
        (ops, "load_settings"),
        (ops, "connect_database"),
    ):
        monkeypatch.setattr(module, name, lambda *a, **k: pytest.fail("Repeated work"))
    assert run()[0] == 0
    assert all(p.read_bytes() == body for p, body in originals.items())
    status = report(kwargs)
    assert status["markets"]["BTCUSDT"]["latest_cycle"]["status"] == "already-recorded"
    assert status["markets"]["BTCUSDT"]["latest_prediction"]["content_sha256"]
    assert (
        status["markets"]["BTCUSDT"]["latest_replayed_prediction"]["verification"]
        == "replayed"
    )
    assert all(
        "source_candles" not in p.read_text()
        for p in kwargs["operations"].glob("*.json")
    )


@pytest.mark.parametrize(
    "failure", ["provider", "database", "prediction", "verification"]
)
def test_independent_failures_and_redaction(cycle, monkeypatch, failure, capsys):
    run, kwargs, _, calls, refresh = cycle
    secret = "postgresql://private:password@secret-host/private?token=SECRET"
    if failure in ("provider", "database"):

        def broken(symbol, settings, **kw):
            if symbol == "BTCUSDT":
                print(secret)
                if failure == "database":
                    raise psycopg.OperationalError(secret)
                raise RuntimeError(secret)
            return refresh(symbol, settings, **kw)

        monkeypatch.setattr(ops, "sync_recent", broken)
    else:
        name = "record_forward" if failure == "prediction" else "verify_forward"
        original = getattr(forward, name)

        def broken(*args, **kw):
            if (args[1] if failure == "prediction" else str(args[0])).find(
                "BTCUSDT"
            ) >= 0:
                raise RuntimeError(secret)
            return original(*args, **kw)

        monkeypatch.setattr(forward, name, broken)
    code, journals = run()
    assert code == 1
    assert journals[0]["markets"]["BTCUSDT"]["status"] == "failed"
    assert journals[0]["markets"]["ETHUSDT"]["status"] == "recorded"
    assert secret not in capsys.readouterr().out
    assert secret not in json.dumps(journals)
    assert report(kwargs)["markets"]["BTCUSDT"]["failure_count"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(source_complete=False),
        lambda r: r.update(failed_pages=1),
        lambda r: r.update(incomplete_pages=1),
        lambda r: r.update(status="failed_or_partial"),
        lambda r: r["coverage"].update(stored_complete=False),
        lambda r: r["coverage"].update(freshness="stale"),
        lambda r: r["coverage"].update(latest_stored_open="2026-10-14T04:00:00+00:00"),
        lambda r: r.update(fixed_run_time="2026-10-14T11:59:00+00:00"),
    ],
)
def test_refresh_must_be_successful_complete_fresh(cycle, monkeypatch, mutation):
    run, kwargs, _, _, refresh = cycle

    def bad(*a, **kw):
        refresh(*a, **kw)
        mutation(kw["result"])
        return 0

    monkeypatch.setattr(ops, "sync_recent", bad)
    monkeypatch.setattr(
        forward, "fit_forward", lambda *a: pytest.fail("Fitted stale data")
    )
    code, journals = run()
    assert code == 1
    assert all(v["status"] == "failed" for v in journals[0]["markets"].values())
    assert not list(kwargs["records"].glob("*.json"))


def test_retry_success_then_expired_does_no_work(cycle, monkeypatch):
    run, kwargs, time, calls, refresh = cycle
    monkeypatch.setattr(ops, "sync_recent", lambda *a, **k: 1)
    assert run()[0] == 1
    monkeypatch.setattr(ops, "sync_recent", refresh)
    assert run()[0] == 0
    time[0] += timedelta(minutes=20)
    assert run()[0] == 0  # existing records win even after deadline
    assert len(calls) == 2
    time[0] += forward.STEP
    assert run()[0] == 1
    assert len(calls) == 2
    assert report(kwargs)["markets"]["BTCUSDT"]["detected_missed_horizons"] == [
        (OPENED + forward.STEP).isoformat()
    ]


def test_deadline_crossed_during_refresh(cycle, monkeypatch):
    run, kwargs, time, _, refresh = cycle

    def slow(*a, **kw):
        refresh(*a, **kw)
        time[0] = OPENED + forward.STEP + forward.DELAY + ops.PROMPTNESS
        return 0

    monkeypatch.setattr(ops, "sync_recent", slow)
    assert run()[0] == 1
    assert not list(kwargs["records"].glob("*.json"))
    assert all(
        v["status"] == "missed"
        for v in report(kwargs)["markets"].values()
        for v in [v["latest_cycle"]]
    )


@pytest.mark.parametrize("phase", [2, 3, 4])
def test_final_publication_deadline_guard(cycle, phase):
    _, kwargs, _, _, _ = cycle
    deadline = OPENED + forward.STEP + forward.DELAY + ops.PROMPTNESS
    stamps = iter([NOW] * phase + [deadline] * (5 - phase))
    with pytest.raises(forward.PublicationDeadlineExceeded):
        forward.record_forward(
            None,
            "BTCUSDT",
            source=kwargs["source"],
            destination=kwargs["records"],
            clock=lambda: next(stamps),
            publication_deadline=deadline,
        )
    assert not list(kwargs["records"].glob("*.json"))
    assert not list(kwargs["records"].glob("*.partial"))
    # Existing manual semantics still permit a later genuinely current observation.
    assert forward.record_forward(
        None,
        "BTCUSDT",
        source=kwargs["source"],
        destination=kwargs["records"],
        clock=lambda: deadline,
    )[0].exists()


def test_missing_candles_model_error_and_clock_reversal(cycle, monkeypatch):
    run, kwargs, time, _, refresh = cycle
    monkeypatch.setattr(
        forward, "read_window", lambda c, s, t: (sample_window(s)[0], [])
    )
    assert run()[0] == 1
    monkeypatch.setattr(forward, "read_window", lambda c, s, t: sample_window(s))

    def reversed_refresh(*a, **kw):
        refresh(*a, **kw)
        time[0] -= timedelta(seconds=1)
        return 0

    monkeypatch.setattr(ops, "sync_recent", reversed_refresh)
    assert run()[0] == 1
    assert not list(kwargs["records"].glob("*.json"))


def test_invalid_existing_record_never_overwritten(cycle):
    run, kwargs, _, calls, _ = cycle
    kwargs["records"].mkdir()
    path = kwargs["records"] / f"{forward.record_id('BTCUSDT', OPENED)}.json"
    path.write_text('{"broken":true}')
    original = path.read_bytes()
    code, journals = run()
    assert code == 1 and calls == ["ETHUSDT"]
    assert journals[0]["markets"]["BTCUSDT"]["error_category"] == "existing_record"
    assert path.read_bytes() == original
    assert report(kwargs)["markets"]["BTCUSDT"]["invalid_records"] == [str(path)]


def test_concurrent_processes_and_crash_release(cycle):
    run, kwargs, _, calls, _ = cycle
    kwargs["records"].mkdir()
    script = """import fcntl, sys
with open(sys.argv[1], 'a') as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    print('ready', flush=True)
    sys.stdin.read()
"""
    with subprocess.Popen(
        [sys.executable, "-c", script, str(kwargs["records"] / ".cycle.lock")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    ) as child:
        try:
            assert child.stdout.readline().strip() == "ready"
            assert run()[0] == 2 and calls == []
            child.terminate()
            child.wait(timeout=10)
            assert run()[0] == 0 and len(calls) == 2
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=10)


def test_interrupted_after_publication_reconciles_without_refit(cycle, monkeypatch):
    run, kwargs, _, calls, _ = cycle
    original = forward.verify_forward

    def interrupt(*a, **k):
        raise KeyboardInterrupt

    monkeypatch.setattr(forward, "verify_forward", interrupt)
    with pytest.raises(KeyboardInterrupt):
        run()
    assert report(kwargs)["incomplete_cycles"] == 1
    assert len(list(kwargs["records"].glob("*.json"))) == 1
    monkeypatch.setattr(forward, "verify_forward", original)
    assert run()[0] == 0
    assert calls == ["BTCUSDT", "ETHUSDT"]
    assert report(kwargs)["markets"]["BTCUSDT"]["latest_replayed_prediction"] is None


def test_partial_operational_writes_and_downtime_reporting(cycle, monkeypatch):
    run, kwargs, time, _, _ = cycle
    original = ops.write_journal
    attempts = []

    def fail_once(path, journal):
        attempts.append(1)
        if len(attempts) == 2:
            raise OSError("SECRET")
        original(path, journal)

    monkeypatch.setattr(ops, "write_journal", fail_once)
    assert run()[0] == 1
    assert len(list(kwargs["records"].glob("*.json"))) == 2
    assert run()[0] == 0
    (kwargs["operations"] / ".cycle-crashed.partial").write_text("broken")
    (kwargs["operations"] / "corrupt.json").write_text("{")
    time[0] += timedelta(days=1)
    status = report(kwargs)
    assert status["unreadable_cycles"] == status["partial_journals"] == 1
    assert len(status["markets"]["BTCUSDT"]["detected_missed_horizons"]) == 5


def test_initial_journal_failure_stops_before_work(cycle, monkeypatch):
    run, _, _, calls, _ = cycle

    def fail(*a):
        raise OSError("private")

    monkeypatch.setattr(ops, "write_journal", fail)
    assert run()[0] == 1 and calls == []


def test_atomic_journal_preserves_previous_on_write_failure(tmp_path, monkeypatch):
    path = tmp_path / "journal.json"
    ops.write_journal(path, {"old": True})

    def fail(*a):
        raise OSError("private")

    monkeypatch.setattr(ops.os, "replace", fail)
    with pytest.raises(OSError):
        ops.write_journal(path, {"new": True})
    assert json.loads(path.read_bytes()) == {"old": True}
    assert not list(tmp_path.glob("*.partial"))


def test_remote_config_rejected_and_cli_offline(cycle, monkeypatch, config_env):
    run, _, _, calls, _ = cycle
    config_env["POSTGRES_HOST"] = "production.invalid"
    assert run()[0] == 1 and calls == []
    monkeypatch.setattr(ops, "run_cycle", lambda: 2)
    assert cli.main(["forward-cycle"]) == 2
    monkeypatch.setattr(ops, "status_report", lambda: {"offline": True})
    monkeypatch.setattr(cli, "load_settings", lambda: pytest.fail("Settings loaded"))
    assert cli.main(["forward-status"]) == 0
    for option in ("--now", "--start", "--source", "--deadline"):
        with pytest.raises(SystemExit):
            cli.main(["forward-cycle", option, "2024-01-01"])


def test_late_manual_record_is_not_relabelled_prompt(cycle):
    run, kwargs, time, _, _ = cycle
    time[0] = OPENED + forward.STEP + timedelta(hours=1)
    forward.record_forward(
        None,
        "BTCUSDT",
        source=kwargs["source"],
        destination=kwargs["records"],
        clock=lambda: time[0],
    )
    assert run()[0] == 1  # ETH missed; BTC retains its actual late issuance
    status = report(kwargs)["markets"]
    assert status["BTCUSDT"]["late_record_horizons"] == [OPENED.isoformat()]
    assert status["BTCUSDT"]["latest_prediction"]["issuance_delay_seconds"] == 3540
    assert status["ETHUSDT"]["detected_missed_horizons"] == [OPENED.isoformat()]


@pytest.mark.parametrize(
    "retry", ["600", "Wed, 14 Oct 2026 12:12:00 GMT", None, "SECRET"]
)
def test_provider_throttle_is_shared_and_persistent(cycle, monkeypatch, retry):
    run, kwargs, time, calls, refresh = cycle

    def throttled(symbol, settings, **kw):
        calls.append(symbol)
        kw["result"].update(
            error_category="rate_limit", error_details={"retry_after": retry}
        )
        return 1

    monkeypatch.setattr(ops, "sync_recent", throttled)
    assert run()[0] == 1
    assert calls == ["BTCUSDT"]  # shared IP pause also protects ETH
    monkeypatch.setattr(ops, "sync_recent", refresh)
    assert run()[0] == 1 and calls == ["BTCUSDT"]
    assert (
        "SECRET"
        not in (kwargs["operations"] / "state" / "provider-pause.json").read_text()
    )
    if retry not in (None, "SECRET"):
        time[0] = NOW + timedelta(minutes=10)
        assert run()[0] == 0
        assert calls == ["BTCUSDT", "BTCUSDT", "ETHUSDT"]


def test_cli_runs_real_synthetic_cycle(cycle, monkeypatch):
    _, kwargs, _, calls, _ = cycle
    original = ops.run_cycle
    monkeypatch.setattr(ops, "run_cycle", lambda: original(**kwargs))
    assert cli.main(["forward-cycle"]) == 0
    assert calls == list(forward.SYMBOLS)


def test_launchagent_is_explicit_and_contains_no_configuration_secrets():
    import plistlib

    with Path("ops/launchd/com.backtestbadger.forward-collection.plist").open(
        "rb"
    ) as handle:
        plist = plistlib.load(handle)
    args = plist["ProgramArguments"]
    assert Path(args[0]).is_absolute()
    assert Path(plist["WorkingDirectory"]).is_absolute()
    assert Path(args[args.index("--env-file") + 1]).is_absolute()
    assert args[-1] == "forward-cycle"
    assert plist["StartInterval"] == 300
    assert not plist.get("KeepAlive")
    assert not plist.get("EnvironmentVariables")


def test_database_connection_fails_independently_after_refresh(cycle, monkeypatch):
    run, _, _, _, _ = cycle
    connections = []

    def connect(settings):
        connections.append(1)
        if len(connections) == 1:
            raise psycopg.OperationalError("private connection details")
        return nullcontext(None)

    monkeypatch.setattr(ops, "connect_database", connect)
    code, journals = run()
    assert code == 1 and len(connections) == 2
    assert journals[0]["markets"]["BTCUSDT"]["error_category"] == "database"
    assert journals[0]["markets"]["ETHUSDT"]["status"] == "recorded"


def test_long_refresh_records_successful_source_outcome_but_misses_forecast(
    cycle, monkeypatch
):
    run, _, time, _, refresh = cycle

    def slow(*a, **kw):
        refresh(*a, **kw)
        time[0] += timedelta(minutes=15)
        kw["result"]["finished_at"] = time[0].isoformat()
        return 0

    monkeypatch.setattr(ops, "sync_recent", slow)
    code, journals = run()
    assert code == 1
    btc = journals[0]["markets"]["BTCUSDT"]
    assert btc["refresh"] == "complete_fresh" and btc["status"] == "missed"

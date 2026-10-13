import logging

import psycopg
import pytest

from backtest_badger import cli
from backtest_badger.config import load_settings


@pytest.fixture(autouse=True)
def isolate_configuration(monkeypatch, config_env):
    monkeypatch.setattr(cli, "load_settings", lambda: load_settings(config_env))
    previous_level = logging.getLogger().level
    yield
    logging.getLogger().setLevel(previous_level)


def test_health_never_connects(monkeypatch, capsys):
    def unexpected_connection(settings):
        pytest.fail("health must not connect to the database")

    monkeypatch.setattr(cli, "check_database", unexpected_connection)
    assert cli.main(["health"]) == 0
    assert capsys.readouterr().out == "Application configuration OK.\n"


def test_bad_configuration(config_env, caplog, capsys):
    config_env["POSTGRES_PORT"] = "private-invalid-value"
    assert cli.main(["health"]) == 2
    assert "POSTGRES_PORT" in caplog.text
    assert "private-invalid-value" not in caplog.text
    assert not capsys.readouterr().out


def test_database_success(monkeypatch, capsys):
    received = []
    monkeypatch.setattr(cli, "check_database", received.append)
    assert cli.main(["db-health"]) == 0
    assert len(received) == 1
    assert received[0].database == "test_badger"
    assert capsys.readouterr().out == "PostgreSQL connectivity OK.\n"


@pytest.mark.parametrize("exception", [psycopg.OperationalError, ValueError])
def test_database_failure_is_redacted(monkeypatch, caplog, capsys, exception):
    def fail(settings):
        raise exception(f"Connection failed: {settings.password}")

    monkeypatch.setattr(cli, "check_database", fail)
    assert cli.main(["db-health"]) == 1
    assert "Database health check failed" in caplog.text
    assert "private-test-password" not in caplog.text
    assert not capsys.readouterr().out


@pytest.mark.parametrize("args", [[], ["unknown"]])
def test_invalid_command(args, capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(args)
    assert error.value.code == 2
    assert "usage:" in capsys.readouterr().err


def test_recent_cli_forwards_explicit_policy(monkeypatch):
    from datetime import UTC, datetime

    received = {}

    def sync(symbol, settings, **kwargs):
        received.update(symbol=symbol, **kwargs)
        return 1

    monkeypatch.setattr(cli, "sync_recent", sync)
    assert (
        cli.main(
            [
                "sync-recent",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "4h",
                "--start",
                "2026-10-01T00:00:00Z",
                "--dry-run",
                "--settling-seconds",
                "120",
            ]
        )
        == 1
    )
    assert received == dict(
        symbol="BTCUSDT",
        start=datetime(2026, 10, 1, tzinfo=UTC),
        settling_seconds=120,
        dry_run=True,
    )

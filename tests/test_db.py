from unittest.mock import MagicMock

import psycopg
import pytest

from backtest_badger.config import load_settings
from backtest_badger.db import check_database


def test_probe_closes_connection_even_when_query_fails(monkeypatch, config_env):
    connect = MagicMock()
    connection = connect.return_value.__enter__.return_value
    connection.execute.side_effect = psycopg.OperationalError("Query failed")
    monkeypatch.setattr("backtest_badger.db.psycopg.connect", connect)
    with pytest.raises(psycopg.OperationalError):
        check_database(load_settings(config_env))
    connect.return_value.__exit__.assert_called_once()
    assert connect.call_args.kwargs["connect_timeout"] == 5
    assert connect.call_args.kwargs["options"] == "-c statement_timeout=5000"


def test_successful_read_only_probe(monkeypatch, config_env):
    connect = MagicMock()
    connection = connect.return_value.__enter__.return_value
    cursor = connection.execute.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)
    monkeypatch.setattr("backtest_badger.db.psycopg.connect", connect)
    check_database(load_settings(config_env))
    connection.execute.assert_called_once_with("SELECT 1")
    connect.return_value.__exit__.assert_called_once()
    connection.execute.return_value.__exit__.assert_called_once()


def test_connection_failure_propagates(monkeypatch, config_env):
    connect = MagicMock(side_effect=psycopg.OperationalError("Connection refused"))
    monkeypatch.setattr("backtest_badger.db.psycopg.connect", connect)
    with pytest.raises(psycopg.OperationalError):
        check_database(load_settings(config_env))

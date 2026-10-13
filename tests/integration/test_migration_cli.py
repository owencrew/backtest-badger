import os
import subprocess
import sys

import pytest
from psycopg.conninfo import conninfo_to_dict

from .conftest import ROOT

pytestmark = pytest.mark.integration


def test_environment_migrations_and_stage_zero_cli(empty_database):
    parameters = conninfo_to_dict(empty_database)
    env = os.environ | {
        "POSTGRES_HOST": parameters["host"],
        "POSTGRES_PORT": parameters["port"],
        "POSTGRES_DB": parameters["dbname"],
        "POSTGRES_USER": parameters["user"],
        "POSTGRES_PASSWORD": parameters["password"],
    }

    def run(*args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout

    for check in ("health", "db-health"):
        assert "OK" in run(
            "-c",
            "from backtest_badger.cli import main; "
            f"raise SystemExit(main(['{check}']))",
        )
    run("-m", "alembic", "upgrade", "head")
    assert "0001 (head)" in run("-m", "alembic", "current")
    assert "CREATE TABLE candle" in run("-m", "alembic", "upgrade", "head", "--sql")
    run("-m", "alembic", "downgrade", "base")
    run("-m", "alembic", "upgrade", "head")

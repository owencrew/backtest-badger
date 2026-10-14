"""Actual logical dump/restore only on explicitly configured disposable PG17."""

import importlib
import os
import sys
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from backtest_badger.candles import save_candle
from backtest_badger.config import Settings

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/lightsail"))
db = importlib.import_module("rehearsal_db")
f = importlib.import_module("rehearsal_files")
pytestmark = pytest.mark.integration


def settings(dsn):
    values = conninfo_to_dict(dsn)
    return Settings(
        values["host"],
        int(values["port"]),
        values["dbname"],
        values["user"],
        values["password"],
        "INFO",
    )


def test_readonly_audit_preserves_exact_values_and_detects_revisions(
    database, connection, candle_observation
):
    save_candle(connection, candle_observation)
    with db.readonly(settings(database)) as conn:
        assert conn.execute("SHOW transaction_read_only").fetchone() == ("on",)
        assert conn.execute("SHOW transaction_isolation").fetchone() == (
            "repeatable read",
        )
        before = db.audit(conn)
    save_candle(
        connection,
        replace(
            candle_observation,
            close=Decimal("42501.000000000000000000001"),
            observed_at=candle_observation.observed_at + timedelta(days=1),
        ),
    )
    with db.readonly(settings(database)) as conn:
        after = db.audit(conn)
    assert (
        before["tables"]["candle"]["logical_sha256"]
        != after["tables"]["candle"]["logical_sha256"]
    )
    assert after["tables"]["candle_revision"]["rows"] == 1
    with (
        pytest.raises(psycopg.errors.ReadOnlySqlTransaction),
        db.readonly(settings(database)) as conn,
    ):
        conn.execute("DELETE FROM candle")


def test_dump_shared_snapshot_restore_and_schema_sequences(
    database, connection, candle_observation, test_admin, tmp_path, monkeypatch
):
    container = os.environ.get("BADGER_D2A_TEST_CONTAINER")
    if not container:
        pytest.skip(
            "Set BADGER_D2A_TEST_CONTAINER to the disposable test container ID."
        )
    admin, admin_dsn = test_admin
    source = settings(database)
    save_candle(connection, candle_observation)
    save_candle(
        connection,
        replace(
            candle_observation,
            close=Decimal("42501.123456789012345678901"),
            observed_at=candle_observation.observed_at + timedelta(days=1),
        ),
    )
    chosen = source.database
    original_exec = db.db_exec

    def test_exec(cid, program, args=(), *, input=None, stdout=None):
        # Explicit generated test DB only. Never a real source database.
        assert chosen.startswith("badger_test_")
        command = [
            "exec",
            "-i",
            "-e",
            "PGOPTIONS=-c default_transaction_read_only=on -c timezone=UTC",
            cid,
            program,
            *args,
            "-U",
            source.user,
        ]
        if program != "pg_dumpall":
            command += ["-d", chosen]
        body = db.docker(*command, input=input, stdout=stdout)
        if program == "pg_dump" and "--format=custom" in args:
            # A genuine concurrent write after the exported snapshot must NOT
            # appear in either the dump or its source audit.
            connection.execute(
                "INSERT INTO market (venue,market_type,symbol,base_asset,quote_asset) "
                "OVERRIDING SYSTEM VALUE VALUES ('test','spot','LATE','L','Q')"
            )
        return body

    monkeypatch.setattr(db, "db_exec", test_exec)
    out = tmp_path / "source"
    out.mkdir()
    # Sequence movement is non-MVCC: detect it and keep the failed dump/audit.
    with pytest.raises(ValueError, match="Sequence state changed"):
        db.snapshot(source, container, out, dump=True)
    assert (out / "database.dump").is_file()
    assert (
        f.read_json(out / "database.json")["logical"]["tables"]["market"]["rows"] == 2
    )

    # Repeat with a row update that does not move a sequence; snapshot isolation
    # should hold while source continues writing.
    def stable_exec(cid, program, args=(), **kwargs):
        command = [
            "exec",
            "-i",
            "-e",
            "PGOPTIONS=-c default_transaction_read_only=on -c timezone=UTC",
            cid,
            program,
            *args,
            "-U",
            source.user,
        ]
        if program != "pg_dumpall":
            command += ["-d", chosen]
        body = db.docker(*command, **kwargs)
        if program == "pg_dump" and "--format=custom" in args:
            connection.execute(
                "UPDATE market SET base_asset='changed_after_snapshot' "
                "WHERE symbol='LATE'"
            )
        return body

    monkeypatch.setattr(db, "db_exec", stable_exec)
    out = tmp_path / "stable"
    out.mkdir()
    db.snapshot(source, container, out, dump=True)
    source_audit = f.read_json(out / "database.json")
    assert source_audit["sequences_stable"]
    target = "badger_test_" + uuid4().hex
    admin.execute(
        sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(target))
    )
    try:
        with (out / "database.dump").open("rb") as dump:
            db.docker(
                "exec",
                "-i",
                container,
                "pg_restore",
                "--exit-on-error",
                "--single-transaction",
                "--no-owner",
                "--no-acl",
                "-U",
                source.user,
                "-d",
                target,
                stdin=dump,
            )
        chosen = target
        restored = tmp_path / "restored"
        restored.mkdir()
        target_dsn = make_conninfo(admin_dsn, dbname=target)
        db.snapshot(settings(target_dsn), container, restored)
        assert (
            f.read_json(restored / "database.json")["logical"]
            == source_audit["logical"]
        )
        with psycopg.connect(target_dsn, autocommit=True) as conn:
            assert conn.execute("SELECT close FROM candle").fetchone()[0] == Decimal(
                "42501.123456789012345678901"
            )
            assert conn.execute("SELECT count(*) FROM candle_revision").fetchone() == (
                1,
            )
            with pytest.raises(psycopg.IntegrityError):
                conn.execute("DELETE FROM candle_revision")
    finally:
        monkeypatch.setattr(db, "db_exec", original_exec)
        admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(target)))

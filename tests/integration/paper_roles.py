"""Isolated cluster fixture with genuine password logins and no role membership."""

import os
import re
from contextlib import contextmanager
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from .conftest import ROOT, migrate


@contextmanager
def isolated_roles(admin, dsn, identity, *, source=True):
    assert re.fullmatch(r"[a-f0-9]{32}", identity)
    database = "badger_test_" + identity
    roles = {
        role: "p_" + role + "_" + identity
        for role in ("owner", "operator", "worker", "reader", "collector")
    }
    identifiers = {k: sql.Identifier(v) for k, v in roles.items()}
    identifiers["database"] = sql.Identifier(database)
    created = []
    dsns = {}
    try:
        for role, name in roles.items():
            password = uuid4().hex
            admin.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB "
                    "NOCREATEROLE "
                    "NOREPLICATION NOBYPASSRLS PASSWORD {}"
                ).format(identifiers[role], sql.Literal(password))
            )
            created.append(identifiers[role])
            dsns[role] = make_conninfo(
                dsn, dbname=database, user=name, password=password
            )
        admin.execute(
            sql.SQL(
                "CREATE DATABASE {database} OWNER {owner} TEMPLATE template0"
            ).format(**identifiers)
        )
        try:
            with psycopg.connect(
                make_conninfo(dsn, dbname=database), autocommit=True
            ) as bootstrap:
                bootstrap.execute(
                    "REVOKE EXECUTE ON FUNCTION pg_catalog.lo_create(oid), "
                    "pg_catalog.lo_creat(integer), "
                    "pg_catalog.lo_from_bytea(oid,bytea) FROM PUBLIC"
                )
            if source:
                migrate(dsns["owner"], "0001")
                # Model existing Stage 3 access before changing the PUBLIC defaults.
                with psycopg.connect(dsns["owner"]) as c:
                    c.execute(
                        sql.SQL(
                            "GRANT CONNECT ON DATABASE {database} TO {collector}; "
                            "GRANT USAGE ON SCHEMA public TO {collector}; "
                            "GRANT SELECT ON market,candle,candle_revision "
                            "TO {collector}; "
                            "GRANT INSERT,UPDATE ON candle TO {collector}; "
                            "GRANT INSERT ON candle_revision TO {collector}"
                        ).format(**identifiers)
                    )
            else:
                with psycopg.connect(dsns["owner"]) as c:
                    # pg_dump without --create excludes database-level ACLs.
                    c.execute(
                        sql.SQL(
                            "REVOKE ALL ON DATABASE {database} FROM PUBLIC; "
                            "GRANT CONNECT ON DATABASE {database} TO "
                            "{collector},{worker},{operator},{reader}"
                        ).format(**identifiers)
                    )
            yield dsns, identifiers
        finally:
            admin.execute(sql.SQL("DROP DATABASE {}").format(identifiers["database"]))
    finally:
        for name in reversed(created):
            admin.execute(sql.SQL("DROP ROLE {}").format(name))


def upgrade(dsns, identifiers):
    migrate(dsns["owner"])
    with psycopg.connect(dsns["owner"]) as c:
        c.execute(
            sql.SQL((ROOT / "ops/paper/grants.sql").read_text()).format(**identifiers)
        )


def restore_admin(test_admin):
    dsn = os.getenv("BADGER_TEST_RESTORE_DSN")
    if not dsn:
        pytest.skip(
            "Independent loopback restore cluster requires BADGER_TEST_RESTORE_DSN."
        )
    params = conninfo_to_dict(dsn)
    assert set(params) <= {"host", "port", "dbname", "user", "password"}
    assert params["host"] in {"127.0.0.1", "::1"} and params["dbname"] == "postgres"
    c = psycopg.connect(dsn, autocommit=True, connect_timeout=5)
    try:
        query = "SELECT system_identifier FROM pg_control_system()"
        assert (
            c.info.server_version // 10000 == 17
            and c.execute(query).fetchone() != test_admin[0].execute(query).fetchone()
        )
    except BaseException:
        c.close()
        raise
    return c, dsn

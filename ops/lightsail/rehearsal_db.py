"""Read-only PG17 inventories and synchronized logical export for D2A."""

import hashlib
import os
import re
import subprocess
from contextlib import contextmanager

import psycopg
from psycopg import sql
from rehearsal_files import require, write_json


def run(command, *, input=None, stdin=None, stdout=None, env=None, timeout=1800):
    """Never echo command arguments, environment or raw diagnostics."""
    result = subprocess.run(
        command,
        input=input,
        stdin=stdin,
        stdout=stdout or subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=timeout,
    )
    require(
        result.returncode == 0,
        f"External command failed ({command[0]}); diagnostics suppressed.",
    )
    return result.stdout


def docker(*args, **kwargs):
    # No remote Docker contexts or environment-driven target override.
    env = {
        k: v for k, v in os.environ.items() if not k.startswith(("DOCKER_", "COMPOSE_"))
    }
    return run(["docker", "--context", "default", *args], env=env, **kwargs)


def db_exec(container, program, args=(), *, input=None, stdout=None):
    require(re.fullmatch(r"[0-9a-f]{64}", container), "Require full container ID.")
    require(
        program in ("psql", "pg_dump", "pg_dumpall", "pg_restore"),
        "Unsupported database program.",
    )
    # The shell body is constant; user arguments are positional, never evaluated.
    body = 'exec "$@" -U "$POSTGRES_USER"'
    if program != "pg_dumpall":
        body += ' -d "$POSTGRES_DB"'
    return docker(
        "exec",
        "-i",
        "-e",
        "PGOPTIONS=-c default_transaction_read_only=on "
        "-c timezone=UTC -c lock_timeout=2000",
        container,
        "sh",
        "-ec",
        body,
        "d2a",
        program,
        *args,
        input=input,
        stdout=stdout,
    )


def query_container(container, query):
    return (
        db_exec(
            container,
            "psql",
            ["-X", "-A", "-t", "-v", "ON_ERROR_STOP=1"],
            input=query.encode(),
        )
        .decode()
        .strip()
    )


@contextmanager
def readonly(settings):
    # Server-side default from startup, before the first SQL instruction.
    with psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
        autocommit=True,
        connect_timeout=5,
        options="-c default_transaction_read_only=on "
        "-c timezone=UTC -c lock_timeout=2000 "
        "-c statement_timeout=300000",
    ) as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            yield conn


def sequences(conn):
    result = {}
    for schema, name in conn.execute("""
        SELECT n.nspname, c.relname FROM pg_class c
        JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE c.relkind='S' AND n.nspname NOT LIKE 'pg_%'
        AND n.nspname <> 'information_schema' ORDER BY 1,2
    """):
        result[f"{schema}.{name}"] = list(
            conn.execute(
                sql.SQL("SELECT last_value::text, is_called FROM {}.{}").format(
                    sql.Identifier(schema), sql.Identifier(name)
                )
            ).fetchone()
        )
    return result


def audit(conn):
    require(conn.info.server_version // 10000 == 17, "Require PostgreSQL 17.")
    require(
        conn.execute("SELECT count(*) FROM pg_largeobject_metadata").fetchone()[0] == 0,
        "Unexpected large objects; review logical comparison scope.",
    )
    schemas = [
        r[0]
        for r in conn.execute("""
        SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%'
        AND nspname <> 'information_schema' ORDER BY 1
    """)
    ]
    require(
        schemas == ["public"], "Unexpected application schemas; review export scope."
    )
    tables = [
        r[0]
        for r in conn.execute("""
        SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relkind IN ('r','p','f','m') ORDER BY 1
    """)
    ]
    require(
        set(tables) == {"market", "candle", "candle_revision", "alembic_version"},
        "Unexpected application tables; review schema before backup/restore.",
    )
    result = {"tables": {}, "sequences": sequences(conn)}
    for name in tables:
        # Hash PostgreSQL's exact text, NOT JSON-decoded floats. C collation makes
        # ordering independent of Mac/Linux locale; includes every provenance field.
        query = sql.SQL(
            "SELECT row_to_json(t)::text FROM public.{} t "
            'ORDER BY row_to_json(t)::text COLLATE "C"'
        ).format(sql.Identifier(name))
        count, sha = 0, hashlib.sha256()
        with conn.cursor(name="d2a_rows") as cursor:
            cursor.execute(query)
            for (row,) in cursor:
                body = row.encode("utf-8")
                sha.update(len(body).to_bytes(8, "big"))
                sha.update(body)
                count += 1
        result["tables"][name] = {"rows": count, "logical_sha256": sha.hexdigest()}
    result["alembic"] = [
        r[0]
        for r in conn.execute(
            "SELECT version_num FROM alembic_version ORDER BY version_num"
        )
    ]
    require(
        result["alembic"] == ["0001"], "Unexpected Alembic revision; do not migrate."
    )
    result["markets"] = [
        r[0]
        for r in conn.execute(
            "SELECT row_to_json(m)::text FROM market m ORDER BY market_id"
        )
    ]
    for name in ("candle", "candle_revision"):
        result[name + "_coverage"] = list(
            conn.execute(
                sql.SQL("""
            SELECT market_id, interval_seconds, count(*), min(open_time)::text,
                   max(open_time)::text, min(version), max(version)
            FROM {} GROUP BY 1,2 ORDER BY 1,2
        """).format(sql.Identifier(name))
            ).fetchall()
        )
        result[name + "_versions"] = list(
            conn.execute(
                sql.SQL("""
            SELECT market_id, interval_seconds, version, count(*) FROM {}
            GROUP BY 1,2,3 ORDER BY 1,2,3
        """).format(sql.Identifier(name))
            ).fetchall()
        )
    result["identity_range"] = list(
        conn.execute("SELECT min(market_id), max(market_id) FROM market").fetchone()
    )
    return result


def identity(conn):
    return dict(
        database=conn.info.dbname,
        user=conn.info.user,
        server_version=conn.info.server_version,
        system_identifier=conn.execute(
            "SELECT system_identifier::text FROM pg_control_system()"
        ).fetchone()[0],
        database_bytes=conn.execute(
            "SELECT pg_database_size(current_database())"
        ).fetchone()[0],
    )


def schema_digest(body):
    # PG17 clients insert random \restrict tokens and version headers. They are
    # pg_restore/psql transport guards, not schema. Keep every SQL definition.
    return hashlib.sha256(
        b"\n".join(
            line
            for line in body.splitlines()
            if not line.startswith(
                (b"\\restrict ", b"\\unrestrict ", b"-- Dumped from ", b"-- Dumped by ")
            )
        )
    ).hexdigest()


def snapshot(settings, container, output, *, dump=False):
    with readonly(settings) as conn:
        info = identity(conn)
        same = query_container(
            container, "SELECT system_identifier::text FROM pg_control_system();"
        )
        require(
            same == info["system_identifier"], "DB endpoint/container cluster mismatch."
        )
        require(
            query_container(container, "SELECT current_database();")
            == settings.database,
            "DB endpoint/container database mismatch.",
        )
        version = docker("exec", container, "pg_dump", "--version").decode().strip()
        require(re.search(r"\b17\.\d+", version), "Require PostgreSQL 17 dump client.")
        snap = conn.execute("SELECT pg_export_snapshot()").fetchone()[0]
        options = [
            "--no-owner",
            "--no-acl",
            "--snapshot=" + snap,
            "--lock-wait-timeout=2s",
        ]
        before = sequences(conn)
        if dump:
            with (output / "database.dump").open("xb") as handle:
                db_exec(
                    container, "pg_dump", ["--format=custom", *options], stdout=handle
                )
        schema = db_exec(container, "pg_dump", ["--schema-only", *options])
        (output / "schema.sql").write_bytes(schema)
        logical = audit(conn)
        stable = before == sequences(conn) == logical["sequences"]
        logical["schema_sha256"] = schema_digest(schema)
        write_json(
            output / "database.json",
            dict(
                identity=info,
                logical=logical,
                exported_snapshot=snap,
                client=version,
                sequences_stable=stable,
                # Ownership/grants intentionally map on restore; retain for review,
                # separately from the equality contract for scientific/schema data.
                source_privileges={
                    "relations": conn.execute("""
                        SELECT n.nspname, c.relname, pg_get_userbyid(c.relowner),
                               c.relacl::text FROM pg_class c
                        JOIN pg_namespace n ON n.oid=c.relnamespace
                        WHERE n.nspname='public' ORDER BY 1,2
                    """).fetchall(),
                    "schemas": conn.execute("""
                        SELECT nspname, pg_get_userbyid(nspowner), nspacl::text
                        FROM pg_namespace WHERE nspname='public'
                    """).fetchall(),
                    "database": conn.execute("""
                        SELECT pg_get_userbyid(datdba), datacl::text, encoding,
                               datcollate, datctype FROM pg_database
                        WHERE datname=current_database()
                    """).fetchone(),
                },
            ),
        )
        require(
            stable, "Sequence state changed during dump; retain failure and repeat."
        )
        if dump:
            globals_sql = db_exec(
                container, "pg_dumpall", ["--globals-only", "--no-role-passwords"]
            )
            (output / "roles-without-passwords.sql").write_bytes(globals_sql)
            with (output / "database.dump").open("rb") as handle:
                listing = docker(
                    "exec", "-i", container, "pg_restore", "--list", stdin=handle
                )
            (output / "dump.list").write_bytes(listing)

"""Seal and independently verify one revision 0002 private rehearsal checkpoint."""

import json
import os
import re
from hashlib import file_digest, sha256
from stat import S_ISREG

from psycopg import sql

from backtest_badger.paper_artifacts import directory, publish_once, read_original
from backtest_badger.paper_evidence import audit_sources, original_bytes, retain
from backtest_badger.paper_reconciliation import transaction
from backtest_badger.paper_types import require

TABLES = {
    "market",
    "candle",
    "candle_revision",
    "alembic_version",
    "paper_portfolio",
    "paper_decision",
    "paper_order",
    "paper_market_event",
    "paper_ledger_entry",
}


def inventory(cur):
    tables = {
        r["tablename"]
        for r in cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        )
    }
    require(tables == TABLES, "Review changed checkpoint coverage.")
    require(
        cur.execute("SELECT version_num FROM alembic_version").fetchall()
        == [{"version_num": "0002"}],
        "Wrong checkpoint revision.",
    )
    rows = {}
    for name in sorted(tables):
        h = sha256()
        count = 0
        with cur.connection.cursor(name="paper_inventory") as stream:
            stream.execute(
                sql.SQL(
                    "SELECT row_to_json(t)::text FROM public.{} t "
                    'ORDER BY row_to_json(t)::text COLLATE "C"'
                ).format(sql.Identifier(name))
            )
            for (value,) in stream:
                body = value.encode()
                h.update(len(body).to_bytes(8, "big") + body)
                count += 1
        rows[name] = [count, h.hexdigest()]
    seq = cur.execute(
        "SELECT last_value,is_called FROM market_market_id_seq"
    ).fetchone()
    return dict(rows=rows, market_sequence=seq)


def dump_hash(root):
    with directory(root) as fd:
        dump = os.open(
            "database.dump", os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=fd
        )
        with os.fdopen(dump, "rb") as stream:
            require(
                S_ISREG(os.fstat(dump).st_mode) and stream.read(5) == b"PGDMP",
                "Invalid dump.",
            )
            stream.seek(0)
            return file_digest(stream, "sha256").hexdigest()


def schema_hash(body):
    # PG17 patch releases randomise the psql transport token.
    body = b"\n".join(
        line
        for line in body.splitlines()
        if not line.startswith(
            (b"\\restrict ", b"\\unrestrict ", b"-- Dumped from ", b"-- Dumped by ")
        )
    )
    return sha256(body).hexdigest()


def privileges(cur, role_names):
    # Database ACLs, cluster identities and built-in grants aren't portable pg_dump
    # members.
    return dict(
        database=cur.execute(
            "SELECT datacl::text AS acl,pg_get_userbyid(datdba) AS owner "
            "FROM pg_database WHERE datname=current_database()"
        ).fetchone(),
        roles=cur.execute(
            "SELECT rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,"
            "rolreplication,rolbypassrls,rolconfig FROM pg_roles WHERE rolname=ANY(%s) "
            "ORDER BY rolname",
            (role_names,),
        ).fetchall(),
        memberships=cur.execute(
            "SELECT roleid::regrole::text AS role,member::regrole::text AS member "
            "FROM pg_auth_members WHERE member::regrole::text=ANY(%s) "
            "ORDER BY 1,2",
            (role_names,),
        ).fetchall(),
        large_objects=cur.execute(
            "SELECT proname,proacl::text FROM pg_proc WHERE pronamespace="
            "'pg_catalog'::regnamespace AND proname IN ('lo_create','lo_creat',"
            "'lo_from_bytea') ORDER BY proname"
        ).fetchall(),
    )


def capture(conn, root, target, dump, schema_dump, role_names):
    """Export a PG17 dump and its inventory from one shared snapshot."""
    target.mkdir(mode=0o700, exist_ok=False)
    archive = target / "originals"
    archive.mkdir(mode=0o700)
    with transaction(conn, readonly=True) as cur:
        snap = cur.execute("SELECT pg_export_snapshot() AS id").fetchone()["id"]
        data = inventory(cur)
        data["privileges"] = privileges(cur, role_names)
        data["schema"] = schema_hash(schema_dump(snap))
        ids = cur.execute(
            "SELECT portfolio_id FROM paper_portfolio ORDER BY 1"
        ).fetchall()
        for row in ids:
            audit_sources(cur, row["portfolio_id"], root)
        with directory(root) as fd:
            names = sorted(n for n in os.listdir(fd) if not n.endswith(".partial"))
        objects = {}
        for name in names:
            if re.fullmatch(r"[a-f0-9]{64}\.json", name):
                objects[name] = retain(archive, original_bytes(root, name[:-5]))
            else:
                require(
                    re.fullmatch(r"[a-f0-9-]{36}\.ref", name),
                    "Unexpected private archive member.",
                )
                with directory(root) as fd:
                    reference = read_original(fd, name, 64)
                original_bytes(root, reference.decode())
                publish_once(archive, name, reference)
                objects[name] = sha256(reference).hexdigest()
        for row in ids:
            audit_sources(cur, row["portfolio_id"], archive)
        with (target / "database.dump").open("xb") as stream:
            dump(snap, stream)
        require(
            cur.execute(
                "SELECT last_value,is_called FROM market_market_id_seq"
            ).fetchone()
            == data["market_sequence"],
            "Sequence changed during backup.",
        )
    data.update(dump=dump_hash(target), originals=objects)
    manifest = json.dumps(data, sort_keys=True).encode()
    # Separate receipt is released only after every file and directory is durable.
    (target / "manifest.json").write_bytes(manifest)
    for path in (
        target / "database.dump",
        target / "manifest.json",
        target,
        target.parent,
    ):
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return sha256(manifest).hexdigest()


def verify_bundle(target, pin):
    with directory(target) as fd:
        require(
            set(os.listdir(fd)) == {"manifest.json", "database.dump", "originals"},
            "Unexpected checkpoint members.",
        )
        manifest = read_original(fd, "manifest.json", 64 * 1024 * 1024)
    require(sha256(manifest).hexdigest() == pin, "Checkpoint receipt mismatch.")
    data = json.loads(manifest)
    require(dump_hash(target) == data["dump"], "Damaged dump.")
    archive = target / "originals"
    with directory(archive) as fd:
        require(
            set(os.listdir(fd)) == set(data["originals"]),
            "Missing or unexpected source object.",
        )
        for name, pin in data["originals"].items():
            if name.endswith(".ref"):
                reference = read_original(fd, name, 64)
                require(
                    sha256(reference).hexdigest() == pin, "Damaged intent reference."
                )
                original_bytes(archive, reference.decode())
            else:
                require(pin + ".json" == name, "Unexpected content identity.")
                original_bytes(archive, pin)
    return data


def verify_restored(conn, target, receipt, schema_dump, role_names):
    data = verify_bundle(target, receipt)
    with transaction(conn, readonly=True) as cur:
        snap = cur.execute("SELECT pg_export_snapshot() AS id").fetchone()["id"]
        require(
            schema_hash(schema_dump(snap)) == data["schema"],
            "Restored schema/ACL mismatch.",
        )
        require(
            privileges(cur, role_names) == data["privileges"],
            "Restored role or database privileges mismatch.",
        )
        for key, value in inventory(cur).items():
            require(data[key] == value, "Restored economic inventory mismatch.")
        ids = cur.execute(
            "SELECT portfolio_id FROM paper_portfolio ORDER BY 1"
        ).fetchall()
        return {
            r["portfolio_id"]: audit_sources(
                cur, r["portfolio_id"], target / "originals"
            )
            for r in ids
        }

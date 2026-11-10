"""One explicitly installed, owner-activated market cycle. No development defaults."""

import argparse
import json
import os
import pwd
import re
import signal
import stat
import sys
from hashlib import file_digest, sha256
from pathlib import Path
from uuid import UUID

import psycopg

from backtest_badger.paper_archive_service import SOCKET
from backtest_badger.paper_artifacts import ArchiveView, directory, read_original
from backtest_badger.paper_clock import Clock
from backtest_badger.paper_market_data import SYMBOLS, unique
from backtest_badger.paper_types import digest, require
from backtest_badger.paper_writer import Writer, WriterConfig
from backtest_badger.paper_writer_cli import (
    Cancelled,
    clock_health,
    private_directory,
    shared_provider,
    trusted_clock_path,
)

CONTROL = Path("/etc/backtest-badger/paper")
STATE = Path("/var/lib/badger-paper")
SOURCES = Path("/run/badger-paper-sources")
CLOCK = Path("/run/badger-paper-clock/observation.json")
RELEASES = Path("/opt/backtest-badger/paper-releases")


def protected_bytes(path):
    require(trusted_clock_path(path), "Approval requires a protected root-owned path.")
    with directory(path.parent) as fd:
        return read_original(fd, path.name, 65536)


def approval(install, activation, symbol, release, machine):
    data = json.loads(install, object_pairs_hook=unique)
    require(
        set(data)
        == {
            "mode",
            "symbol",
            "portfolio_id",
            "config_sha256",
            "implementation_sha256",
            "release",
            "deployment_sha256",
            "machine",
            "host",
            "port",
            "database",
            "role",
            "cluster",
            "database_oid",
            "security_sha256",
            "archive_identity",
            "records_identity",
            "journals_identity",
        }
        and data["mode"] == "production-once"
        and symbol in SYMBOLS
        and data["symbol"] == symbol
        and re.fullmatch("[0-9a-f]{40}", release)
        and data["release"] == release
        and re.fullmatch("[0-9a-f]{32}", machine)
        and data["machine"] == machine
        and data["host"] == "127.0.0.1"
        and type(data["port"]) is int
        and 1 <= data["port"] <= 65535
        and re.fullmatch("[a-z][a-z0-9_]{0,62}", data["database"])
        and data["database"] not in {"postgres", "template0", "template1"}
        and re.fullmatch("[a-z][a-z0-9_]{0,62}", data["role"])
        and data["role"] != "postgres"
        and re.fullmatch("[1-9][0-9]{0,19}", data["cluster"])
        and type(data["database_oid"]) is int
        and data["database_oid"] > 0,
        "Unapproved runtime binding.",
    )
    for name in ("records_identity", "journals_identity", "archive_identity"):
        identity = data[name]
        require(
            isinstance(identity, list)
            and len(identity) == 2
            and all(type(i) is int and i > 0 for i in identity),
            "Invalid original root identity.",
        )
    require(
        len({tuple(data[k + "_identity"]) for k in ("records", "journals", "archive")})
        == 3,
        "Shared source root.",
    )
    UUID(data["portfolio_id"])
    for key in (
        "config_sha256",
        "implementation_sha256",
        "security_sha256",
        "deployment_sha256",
    ):
        digest(data[key])
    require(
        json.loads(activation, object_pairs_hook=unique)
        == {
            "action": "activate-one-portfolio",
            "installation_sha256": sha256(install).hexdigest(),
        },
        "Missing matching portfolio activation.",
    )
    return data


def verify_release(root, release, pin):
    manifest = protected_bytes(root / "deployment.json")
    require(sha256(manifest).hexdigest() == pin, "Unapproved release manifest.")
    data = json.loads(manifest, object_pairs_hook=unique)
    require(data["git_commit"] == release, "Wrong release SHA.")
    files = data["files_sha256"]
    required = {
        "pyproject.toml",
        "uv.lock",
        "docs/stage-04a-prospective-evaluation-protocol.md",
        "docs/stage-04a-paper-trading-spec.md",
        *(
            str(p.relative_to(root))
            for p in (root / "src/backtest_badger").glob("*.py")
        ),
    }
    require(required <= files.keys(), "Incomplete release manifest.")
    for name, expected in files.items():
        relative = Path(name)
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            "Unsafe manifest member.",
        )
        path = root / relative
        require(
            trusted_clock_path(path) and path.is_file(), "Unprotected release member."
        )
        with path.open("rb") as stream:
            require(
                file_digest(stream, "sha256").hexdigest() == expected,
                "Release byte mismatch.",
            )


def installed(symbol, release):
    require(
        re.fullmatch("[0-9a-f]{40}", release) and symbol in SYMBOLS, "Invalid release."
    )
    unit = f"backtest-badger-paper@{symbol}.service"
    account = pwd.getpwnam("badger-paper")
    require(
        os.getuid() == os.geteuid() == account.pw_uid != 0
        and os.getgid() == os.getegid() == account.pw_gid
        and set(os.getgroups()) <= {account.pw_gid}
        and any(
            line.startswith("0::/") and line.endswith("/" + unit)
            for line in Path("/proc/self/cgroup").read_text().splitlines()
        )
        and not any(k.startswith("PG") for k in os.environ),
        "Expected the dedicated system service.",
    )
    root = RELEASES / release
    require(
        Path(sys.prefix) == root / ".venv"
        and Path(__file__).resolve() == root / "src/backtest_badger/paper_production.py"
        and trusted_clock_path(Path(__file__).resolve()),
        "Wrong immutable release.",
    )
    data = approval(
        protected_bytes(CONTROL / f"{symbol}.json"),
        protected_bytes(CONTROL / f"{symbol}.active"),
        symbol,
        release,
        protected_bytes(Path("/etc/machine-id")).decode().strip(),
    )
    verify_release(root, release, data["deployment_sha256"])
    config = WriterConfig(
        UUID(data["portfolio_id"]),
        symbol,
        data["config_sha256"],
        SOURCES / "records",
        SOURCES / "journals",
        ArchiveView(STATE / "archive", SOCKET),
        STATE / "runtime",
    )
    for path in (config.records, config.journals):
        with directory(path) as fd:
            identity = os.fstat(fd)
            require(
                [identity.st_dev, identity.st_ino] == data[path.name + "_identity"]
                and os.fstatvfs(fd).f_flag & os.ST_RDONLY,
                "Expected a read-only source mount.",
            )
            # Verify source readability under the actual service UID.
            names = (name for name in os.listdir(fd) if name.endswith(".json"))
            name = next(names, None)
            require(name is not None, "Source mount has no originals.")
            read_original(fd, name, 1024 * 1024)
    with directory(config.archive) as fd:
        info = os.fstat(fd)
        require(
            [info.st_dev, info.st_ino] == data["archive_identity"]
            and os.fstatvfs(fd).f_flag & os.ST_RDONLY
            and info.st_uid == os.getuid()
            and not info.st_mode & 0o077,
            "Expected the private read-only archive view.",
        )
    require(trusted_clock_path(config.runtime.parent), "Unsafe private state parent.")
    private_directory(config.runtime)
    require(
        not os.statvfs(config.runtime).f_flag & os.ST_RDONLY
        and os.access(config.runtime, os.W_OK),
        "Private runtime is not writable.",
    )
    return data, config, service_password(Path("/run/credentials") / unit)


def service_password(root):
    with directory(root) as fd:
        info = os.stat("db-password", dir_fd=fd, follow_symlinks=False)
        require(
            stat.S_ISREG(info.st_mode)
            and not info.st_mode & 0o077
            and info.st_uid in {0, os.getuid()}
            and os.fstatvfs(fd).f_flag & os.ST_RDONLY,
            "Expected private service credential.",
        )
        password = read_original(fd, "db-password", 1024).decode().rstrip("\n")
        require(password and "\x00" not in password, "Missing service credential.")
        return password


# The installer compares these catalog rows to the reviewed isolated grant design.
# The worker checks the approved snapshot for drift before opening the write path.
SECURITY = (
    """SELECT oid::regnamespace::text,nspowner,nspacl::text FROM pg_namespace
       WHERE nspname !~ '^pg_(temp|toast)' ORDER BY 1""",
    """SELECT relname,relowner,relacl::text,relrowsecurity,relforcerowsecurity
       FROM pg_class WHERE relnamespace='public'::regnamespace ORDER BY 1""",
    """SELECT attrelid::regclass::text,attname,attacl::text FROM pg_attribute
       WHERE attacl IS NOT NULL AND attrelid IN
       (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace)
       ORDER BY 1,2""",
    """SELECT oid::regprocedure::text,proowner,proacl::text,prosecdef,proconfig,prosrc
       FROM pg_proc WHERE pronamespace='public'::regnamespace OR oid IN
       ('pg_catalog.lo_create(oid)'::regprocedure,'pg_catalog.lo_creat(int)'::regprocedure,
        'pg_catalog.lo_from_bytea(oid,bytea)'::regprocedure) ORDER BY 1""",
    """SELECT tablename,policyname,roles,cmd,qual,with_check FROM pg_policies
       WHERE schemaname='public' ORDER BY 1,2""",
    """SELECT tgrelid::regclass::text,tgname,tgenabled,pg_get_triggerdef(oid)
       FROM pg_trigger WHERE tgrelid IN
       (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace)
       ORDER BY 1,2""",
    """SELECT datdba,datacl::text FROM pg_database WHERE datname=current_database()""",
)


def security_fingerprint(conn):
    rows = [conn.execute(query).fetchall() for query in SECURITY]
    return sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def verified_cycle(conn, data, config, clock, health, acquire):
    """Verify the live binding before entering the single-cycle writer."""
    identity = conn.execute(
        "SELECT current_database(), session_user, current_user, "
        "(SELECT system_identifier::text FROM pg_control_system()), "
        "(SELECT oid FROM pg_database WHERE datname=current_database()), "
        "(SELECT version_num FROM public.alembic_version)"
    ).fetchone()
    require(
        conn.info.host == data["host"]
        and conn.info.port == data["port"]
        and conn.info.server_version // 10000 == 17
        and identity
        == (
            data["database"],
            data["role"],
            data["role"],
            data["cluster"],
            data["database_oid"],
            "0002",
        ),
        "Unexpected database identity or revision.",
    )
    safe = conn.execute(
        """SELECT rolcanlogin AND NOT (rolsuper OR rolbypassrls OR rolcreatedb OR
        rolcreaterole OR rolreplication OR rolinherit) AND NOT EXISTS
        (SELECT FROM pg_auth_members WHERE member=r.oid) AND NOT
        has_database_privilege(current_database(),'TEMP,CREATE') AND NOT
        has_schema_privilege('public','CREATE') AND NOT
        has_table_privilege('paper_portfolio','INSERT') AND NOT
        has_any_column_privilege('paper_ledger_entry','UPDATE') AND NOT
        has_table_privilege('paper_ledger_entry','DELETE,TRUNCATE,TRIGGER') AND
        row_security_active('paper_ledger_entry') AND
        row_security_active('paper_market_event') AND
        current_setting('session_replication_role')='origin' AND
        current_setting('row_security')='on' AND NOT
        has_parameter_privilege('session_replication_role','SET') AND NOT
        has_function_privilege('pg_catalog.lo_create(oid)','EXECUTE') AND NOT
        has_function_privilege('pg_catalog.lo_creat(integer)','EXECUTE') AND NOT
        has_function_privilege('pg_catalog.lo_from_bytea(oid,bytea)','EXECUTE')
        FROM pg_roles r WHERE rolname=current_user"""
    ).fetchone()
    require(
        safe == (True,) and security_fingerprint(conn) == data["security_sha256"],
        "Unexpected database privileges.",
    )
    binding = conn.execute(
        """SELECT p.portfolio_id,m.symbol,p.strategy_config_sha256,
        p.implementation_sha256,
        p.state,m.venue,m.market_type FROM public.paper_portfolio p JOIN public.market m
        USING (market_id) WHERE portfolio_id=%s""",
        (config.portfolio_id,),
    ).fetchone()
    require(
        binding
        == (
            UUID(data["portfolio_id"]),
            data["symbol"],
            data["config_sha256"],
            data["implementation_sha256"],
            "ACTIVE",
            "binance",
            "spot",
        ),
        "Portfolio binding or activation mismatch.",
    )
    return Writer(conn, config, clock, health, acquire).run()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["production-once"])
    parser.add_argument("--market", choices=SYMBOLS, required=True)
    parser.add_argument("--release", required=True)
    args = parser.parse_args(argv)

    def cancel(_signum, _frame):
        raise Cancelled()

    previous = signal.signal(signal.SIGTERM, cancel)
    try:
        data, config, password = installed(args.market, args.release)
        with psycopg.connect(
            host=data["host"],
            port=data["port"],
            dbname=data["database"],
            user=data["role"],
            password=password,
            require_auth="scram-sha-256",
            sslmode="disable",
            connect_timeout=3,
            autocommit=True,
            options=(
                "-c search_path=pg_catalog,public,pg_temp -c statement_timeout=10000"
            ),
            application_name="badger-paper-" + args.market,
        ) as conn:
            result = verified_cycle(
                conn,
                data,
                config,
                Clock(),
                lambda: clock_health(CLOCK),
                shared_provider(config.runtime),
            )
        print(json.dumps(result))
        return int(
            result["result"] == "STOPPED"
            or any(i["severity"] == "integrity" for i in result["incidents"])
        )
    except (Cancelled, KeyboardInterrupt):
        print(json.dumps(dict(result="INTERRUPTED", symbol=args.market)))
        return 2
    except (OSError, ValueError, TypeError, KeyError, psycopg.Error):
        print(json.dumps(dict(result="PREFLIGHT_FAILED", symbol=args.market)))
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    raise SystemExit(main())

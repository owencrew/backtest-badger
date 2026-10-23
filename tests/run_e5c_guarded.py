"""Offline exact-file E.5c launcher; real modules, no discovery or stub extraction."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = (
    "__init__",
    "genuine_backtest_reporting_integration",
    "genuine_backtest_preparation",
    "genuine_minute_publication",
    "genuine_minute_replay",
    "genuine_minute_inputs",
    "genuine_minute_signed_approval",
    "genuine_minute_verification_operator",
    "genuine_minute_verification_runtime",
    "genuine_minute_verification_wiring",
    "genuine_minute_price_parity",
    "paper_minute_historical",
    "paper_minute_reporting",
    "paper_minute_integration",
    "paper_historical_evaluation",
    "paper_historical",
    "paper_accounting",
    "paper_execution",
    "paper_strategy",
    "paper_types",
    "forecast_data",
    "minute_execution_data",
    "execution_data",
    "model_data",
    "archives",
    "frozen",
    "ingestion",
    "features",
    "candles",
    "research",
    "db",
    "config",
    "history",
)
TESTS = (
    "test_genuine_backtest_reporting_integration",
    "test_genuine_minute_publication",
    "test_genuine_minute_replay",
    "test_genuine_minute_inputs",
    "test_genuine_minute_signed_approval",
    "test_paper_minute_reporting",
    "test_paper_minute_historical",
)
FILES = {ROOT + "/src/backtest_badger/" + n + ".py" for n in SOURCES}
FILES.update(ROOT + "/tests/" + n + ".py" for n in TESTS)
FILES.add(ROOT + "/tests/run_e5c_guarded.py")
BASE = os.path.abspath(sys._stdlib_dir)
RUNTIME = (BASE, ROOT + "/.venv/lib/python3.12/site-packages")
ORIGINAL_LSTAT = os.lstat


def check(path, *, metadata=False):
    if type(path) is int:
        raise PermissionError("Descriptor access denied")
    absolute = os.path.abspath(os.fsdecode(path))
    if any(
        p in absolute.split("/")
        for p in (
            "artifacts",
            "BacktestBadgerEvidence",
            "crypto-trading-platform",
            ".ssh",
            ".aws",
            ".env",
            ".codex",
        )
    ):
        raise PermissionError("Protected path denied before metadata access")
    allowed = (
        absolute in FILES
        or absolute == "/dev/null"
        or any(absolute == p or absolute.startswith(p + "/") for p in RUNTIME)
    )
    if metadata:
        allowed = (
            allowed
            or absolute == "/"
            or ROOT.startswith(absolute + "/")
            or absolute
            in (
                ROOT,
                ROOT + "/src",
                ROOT + "/src/backtest_badger",
                ROOT + "/tests",
            )
        )
    if not allowed:
        raise PermissionError("Non-allowlisted path: " + absolute)
    if not metadata and absolute != "/dev/null":
        current = "/"
        for part in absolute.strip("/").split("/"):
            current = os.path.join(current, part)
            try:
                mode = ORIGINAL_LSTAT(current).st_mode
            except FileNotFoundError:
                break
            if mode & 0o170000 == 0o120000:
                raise PermissionError("Symlink read denied")


def audit(event, args):
    if event == "open":
        check(args[0])
        if args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise PermissionError("Writes denied")
    if event in ("os.listdir", "os.scandir"):
        path = os.path.abspath(os.fsdecode(args[0]))
        if not any(path == p or path.startswith(p + "/") for p in RUNTIME):
            raise PermissionError("Repository discovery denied")
        check(path)
    if event == "os.chdir":
        if os.path.abspath(os.fsdecode(args[0])) != ROOT:
            raise PermissionError("Directory changes denied")
        return  # Pytest restores its known starting directory at shutdown.
    if event.startswith(("socket.", "subprocess.")) or event in (
        "os.system",
        "os.posix_spawn",
        "os.exec",
        "os.fork",
        "os.forkpty",
        "os.remove",
        "os.rename",
        "os.mkdir",
        "os.rmdir",
        "os.link",
        "os.symlink",
    ):
        raise PermissionError("Network/process/mutation denied")


def main():
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12 required")
    if sys.argv[1:] not in ([], ["--small"], ["--regressions"]):
        raise SystemExit("Only --small, --regressions or no arguments")
    sys.dont_write_bytecode = True
    sys.addaudithook(audit)
    for name in ("stat", "lstat"):
        original = getattr(os, name)

        def guarded(path, *args, _original=original, **kwargs):
            check(path, metadata=True)
            return _original(path, *args, **kwargs)

        setattr(os, name, guarded)
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ.pop("BADGER_TEST_ADMIN_DSN", None)
    os.environ.pop("DATABASE_URL", None)
    sys.path.append(RUNTIME[1])
    # Exact finder avoids Python's normal repository directory enumeration.
    import importlib.abc
    import importlib.util

    class ExactSource(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        def find_spec(self, fullname, path=None, target=None):
            if fullname == "backtest_badger":
                filename = ROOT + "/src/backtest_badger/__init__.py"
            elif fullname.startswith("backtest_badger."):
                filename = ROOT + "/src/" + fullname.replace(".", "/") + ".py"
            elif fullname in TESTS:
                filename = ROOT + "/tests/" + fullname + ".py"
            else:
                return None
            if filename not in FILES:
                raise PermissionError("Unreviewed project import: " + fullname)
            return importlib.util.spec_from_file_location(
                fullname,
                filename,
                loader=self,
                submodule_search_locations=[]
                if fullname == "backtest_badger"
                else None,
            )

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            with open(module.__spec__.origin, "rb") as stream:
                exec(
                    compile(stream.read(), module.__spec__.origin, "exec"),
                    module.__dict__,
                )

    sys.meta_path.insert(0, ExactSource())
    from pathlib import Path

    import pytest

    targets = [TESTS[0]]
    if sys.argv[1:] == ["--small"]:
        targets = ["test_paper_minute_reporting"]
    elif sys.argv[1:] == ["--regressions"]:
        targets += [
            "test_genuine_minute_publication",
            "test_genuine_minute_replay",
            "test_paper_minute_reporting",
            "test_paper_minute_historical",
        ]

    class ExactModule(pytest.Module):
        def _getobj(self):
            return __import__(self.path.stem)

        def collect(self):
            items = list(super().collect())
            if sys.argv[1:] == ["--small"]:
                names = {
                    "test_off_hour_costs_use_fill_evidence_and_independent_funding",
                    "test_unavailable_bh_and_zero_duration_short_period",
                    "test_after_last_mark_fill_is_flow_not_invented_valuation",
                    "test_pin_binds_evidence_even_when_accounting_is_unchanged",
                }
                return [item for item in items if item.originalname in names]
            return items

    class ExactFiles:
        passed = 0
        skipped = 0

        def pytest_sessionstart(self, session):
            session.collect = lambda: (
                ExactModule.from_parent(
                    session, path=Path(ROOT + "/tests/" + n + ".py")
                )
                for n in targets
            )

        def pytest_collection_finish(self, session):
            if sys.argv[1:] == ["--small"]:
                count, expected = len(session.items), 9
            else:
                count = sum(item.path.stem == TESTS[0] for item in session.items)
                expected = 55
            if count != expected:
                raise pytest.UsageError(f"E.5c collected {count}; expected {expected}")

        def pytest_runtest_logreport(self, report):
            self.skipped += int(report.skipped)
            self.passed += int(report.when == "call" and report.passed)

        def pytest_sessionfinish(self, session, exitstatus):
            if self.skipped or self.passed != session.testscollected:
                session.exitstatus = 1

    return pytest.main(
        [
            "-c",
            "/dev/null",
            "--rootdir=" + ROOT,
            "--noconftest",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:logging",
            "--assert=plain",
            "-s",
            "-q",
            *(ROOT + "/tests/" + n + ".py" for n in targets),
        ],
        plugins=[ExactFiles()],
    )


if __name__ == "__main__":
    raise SystemExit(main())

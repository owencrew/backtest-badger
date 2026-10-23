"""Exact-file E.5 unittest launcher: denial is installed before project imports.

Run: python3.12 -I -S -B tests/run_e5_guarded.py
No discovery, conftest, third-party plugins, original evidence or monetary replay.
Python hooks are procedural protection, not an OS sandbox against hostile code.
"""

import os
import sys

# Lexical only: do not resolve links, scan parents or read configuration.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_TESTS = 87  # 84 preparation cases plus three harness regressions.
ALLOWED = frozenset(
    ROOT + "/" + name
    for name in (
        "src/backtest_badger/genuine_backtest_preparation.py",
        "src/backtest_badger/genuine_minute_publication.py",
        "src/backtest_badger/genuine_minute_replay.py",
        "tests/test_genuine_backtest_preparation.py",
        "tests/run_e5_guarded.py",
        "docs/stage-04b2e5-run-contract.json",
    )
)
BASE = os.path.abspath(sys._stdlib_dir)
ORIGINAL_LSTAT = os.lstat


def check_path(path, *, metadata=False):
    if type(path) is int:
        raise PermissionError("File descriptor access denied")
    absolute = os.path.abspath(os.fsdecode(path))
    if any(
        part in absolute.split("/")
        for part in (
            "artifacts",
            "BacktestBadgerEvidence",
            "crypto-trading-platform",
            ".ssh",
            ".aws",
            ".env",
            ".codex",
        )
    ):
        raise PermissionError("Protected path denied")
    allowed = absolute in ALLOWED or absolute == BASE or absolute.startswith(BASE + "/")
    if not allowed:
        raise PermissionError("Non-allowlisted path denied")
    # lstat each lexical component without following a link, before every open.
    if not metadata:
        current = "/"
        for part in absolute.strip("/").split("/"):
            current = os.path.join(current, part)
            try:
                mode = ORIGINAL_LSTAT(current).st_mode
            except FileNotFoundError:
                break
            if mode & 0o170000 == 0o120000:
                raise PermissionError("Symlink denied")


def audit(event, args):
    if event == "open":
        check_path(args[0])
        flags = args[2]
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise PermissionError("Writes denied during tests")
    if event in ("os.listdir", "os.scandir"):
        # Python's import finder enumerates standard-library package directories.
        # Repository discovery remains denied, including all allowlisted parents.
        absolute = os.path.abspath(os.fsdecode(args[0]))
        if not (absolute == BASE or absolute.startswith(BASE + "/")):
            raise PermissionError("Discovery denied")
        check_path(absolute)
    if event == "os.chdir":
        raise PermissionError("Directory changes denied")
    if event.startswith(("socket.", "subprocess.", "ctypes.")) or event in (
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


sys.dont_write_bytecode = True
sys.addaudithook(audit)
for name in ("stat", "lstat"):
    original = getattr(os, name)

    def guarded(path, *args, _original=original, **kwargs):
        check_path(path, metadata=True)
        return _original(path, *args, **kwargs)

    setattr(os, name, guarded)

# Do not inspect configuration values or use third-party test plugin discovery.
os.environ.pop("BADGER_TEST_ADMIN_DSN", None)
os.environ.pop("DATABASE_URL", None)


def suite_succeeded(result):
    """An incomplete or skipped suite is not a successful CI gate."""
    return (
        result.wasSuccessful()
        and result.testsRun == EXPECTED_TESTS
        and not result.skipped
    )


if __name__ == "__main__":
    import types

    if sys.version_info[:2] != (3, 12):
        raise SystemExit("E.5 guarded tests require Python 3.12")

    if sys.argv[1:] == ["--candidate"]:
        candidate = types.ModuleType("e5_candidate")
        path = ROOT + "/src/backtest_badger/genuine_backtest_preparation.py"
        with open(path, "rb") as stream:
            exec(compile(stream.read(), path, "exec"), candidate.__dict__)
        sys.stdout.write(candidate.encode(candidate.candidate_contract()).decode())
        raise SystemExit(0)
    if sys.argv[1:]:
        raise SystemExit("Only no arguments or --candidate are supported")

    import unittest

    module = types.ModuleType("test_genuine_backtest_preparation")
    module.__file__ = ROOT + "/tests/test_genuine_backtest_preparation.py"
    module.E5_GUARDED = True
    module.E5_CHECK_PATH = check_path
    module.E5_SUITE_SUCCEEDED = suite_succeeded
    sys.modules[module.__name__] = module
    with open(module.__file__, "rb") as stream:
        exec(compile(stream.read(), module.__file__, "exec"), module.__dict__)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    if suite.countTestCases() != EXPECTED_TESTS:
        raise SystemExit(
            f"E.5 collected {suite.countTestCases()} tests; expected {EXPECTED_TESTS}"
        )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.stderr.write(
        f"E.5 guarded tests: ran {result.testsRun}, expected {EXPECTED_TESTS}, "
        f"skipped {len(result.skipped)}\n"
    )
    raise SystemExit(not suite_succeeded(result))

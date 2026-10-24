"""E.5d fabricated tests/pipe worker; procedural I/O guard, not an OS jail."""

import importlib.abc
import importlib.util
import os
import stat
import sys
import tempfile
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Reuse the exact prior read inventory without changing either prior launcher.
spec = importlib.util.spec_from_file_location(
    "e5c_inventory", ROOT + "/tests/run_e5c_guarded.py"
)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
FILES = (
    prior.FILES
    | {
        ROOT + "/src/backtest_badger/" + name + ".py"
        for name in ("genuine_backtest_custody", "genuine_backtest_operator")
    }
    | {
        ROOT + "/tests/test_genuine_backtest_operator.py",
        ROOT + "/tests/test_e5d_rehearsal_preparation.py",
        ROOT + "/ops/e5d_rehearsal_preflight.py",
        __file__,
        ROOT + "/src/backtest_badger/genuine_backtest_output_schema.json",
    }
)
WORKER = sys.argv[1:] == ["--worker"]
MEASURE = sys.argv[1:] == ["--measure"]
PREPARATION = sys.argv[1:] == ["--preparation"]
if sys.argv[1:] not in ([], ["--worker"], ["--measure"], ["--preparation"]):
    raise SystemExit("Only no arguments, --worker, --measure or --preparation")
E5D_TEMP = None if WORKER else tempfile.mkdtemp(prefix="e5d-fabricated-", dir="/tmp")
# /tmp is a symlink on macOS; all actual approved fixture paths use /private/tmp.
if E5D_TEMP:
    E5D_TEMP = os.path.realpath(E5D_TEMP)
RUNTIME = prior.RUNTIME
FD_PATHS = {}
ORIGINAL_OPEN = os.open
ORIGINAL_CLOSE = os.close


def absolute(path, dir_fd=None):
    if isinstance(path, int):
        if path in FD_PATHS:
            return FD_PATHS[path]
        raise PermissionError("Unknown descriptor")
    path = os.fsdecode(path)
    if not os.path.isabs(path):
        path = os.path.join(
            FD_PATHS[dir_fd] if dir_fd is not None else os.getcwd(), path
        )
    return os.path.abspath(path)


def check(path, *, write=False, metadata=False, dir_fd=None):
    path = absolute(path, dir_fd)
    if E5D_TEMP and (path == E5D_TEMP or path.startswith(E5D_TEMP + "/")):
        return path
    if path == "/dev/null":
        return path
    if write:
        raise PermissionError("Only fabricated scratch writes allowed")
    if (
        path in FILES
        or path == "/dev/null"
        or any(path == p or path.startswith(p + "/") for p in RUNTIME)
    ):
        return path
    if metadata and (
        path == "/"
        or any(p.startswith(path + "/") for p in FILES)
        or (E5D_TEMP and E5D_TEMP.startswith(path + "/"))
    ):
        return path
    raise PermissionError("Non-allowlisted access denied")


def guarded_open(path, flags, mode=0o777, *, dir_fd=None):
    write = bool(
        flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
    )
    target = check(
        path, write=write, metadata=bool(flags & os.O_DIRECTORY), dir_fd=dir_fd
    )
    fd = ORIGINAL_OPEN(target, flags, mode)
    FD_PATHS[fd] = target
    return fd


def guarded_close(fd):
    FD_PATHS.pop(fd, None)
    return ORIGINAL_CLOSE(fd)


def audit(event, args):
    if (
        event == "open"
        and isinstance(args[0], int)
        and stat.S_ISFIFO(os.fstat(args[0]).st_mode)
    ):
        return  # Only anonymous IPC pipe descriptors, never inherited regular files.
    if event == "open":
        check(
            args[0],
            write=bool(
                args[2]
                & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ),
            metadata=bool(args[2] & os.O_DIRECTORY),
        )
    if event in ("os.listdir", "os.scandir"):
        path = check(args[0], metadata=True)
        if not (
            (E5D_TEMP and (path == E5D_TEMP or path.startswith(E5D_TEMP + "/")))
            or any(path == p or path.startswith(p + "/") for p in RUNTIME)
        ):
            raise PermissionError("Repository discovery denied")
    if event in ("os.mkdir", "os.remove", "os.rmdir", "os.chmod"):
        check(args[0], write=True, dir_fd=args[-1] if args[-1] != -1 else None)
    if event in ("os.symlink", "os.link", "os.rename"):
        # Mutation tests may create links, but all their endpoints stay in scratch.
        check(args[0], write=True)
        check(args[1], write=True)
    if event == "subprocess.Popen":
        expected = [sys.executable, "-I", "-S", "-B", __file__, "--worker"]
        if WORKER or args[1] != expected:
            raise PermissionError("Only the exact fabricated pipe worker is allowed")
    if event.startswith("socket.") or event in (
        "os.system",
        "os.posix_spawn",
        "os.exec",
        "os.forkpty",
    ):
        raise PermissionError("Network/other processes denied")
    if event == "os.fork" and WORKER:
        raise PermissionError("Worker children denied")
    if event == "os.chdir" and args[0] != ROOT:
        raise PermissionError("Directory change denied")


class ExactSource(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "backtest_badger":
            filename = ROOT + "/src/backtest_badger/__init__.py"
        elif fullname.startswith("backtest_badger."):
            filename = ROOT + "/src/" + fullname.replace(".", "/") + ".py"
        elif fullname.startswith("test_"):
            filename = ROOT + "/tests/" + fullname + ".py"
        else:
            return None
        if filename not in FILES:
            raise PermissionError("Unreviewed project import")
        return importlib.util.spec_from_file_location(
            fullname,
            filename,
            loader=self,
            submodule_search_locations=[] if fullname == "backtest_badger" else None,
        )

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(module.__spec__.origin, "rb") as stream:
            exec(
                compile(stream.read(), module.__spec__.origin, "exec"), module.__dict__
            )


def main():
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12 required")
    sys.dont_write_bytecode = True
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("BADGER_TEST_ADMIN_DSN", None)
    sys.addaudithook(audit)
    os.open, os.close = guarded_open, guarded_close
    for name in ("stat", "lstat"):
        original = getattr(os, name)

        def guarded(path, *args, _original=original, **kwargs):
            check(path, metadata=True, dir_fd=kwargs.get("dir_fd"))
            return _original(path, *args, **kwargs)

        setattr(os, name, guarded)
    sys.path.append(RUNTIME[1])
    sys.meta_path.insert(0, ExactSource())
    if WORKER:
        from backtest_badger.genuine_backtest_operator import worker_stdio

        worker_stdio()
        return 0
    import pytest

    class ExactModule(pytest.Module):
        def _getobj(self):
            return __import__(self.path.stem)

        def collect(self):
            items = list(super().collect())
            if MEASURE:
                return [
                    item
                    for item in items
                    if item.originalname
                    == "test_full_supervisor_success_and_exclusive_publication"
                ]
            return items

    class Guarded:
        passed = 0
        skipped = 0

        def pytest_sessionstart(self, session):
            names = ["test_genuine_backtest_operator"]
            if not MEASURE:
                names.append("test_e5d_rehearsal_preparation")
            if PREPARATION:
                names = ["test_e5d_rehearsal_preparation"]
            session.collect = lambda: iter(
                [
                    ExactModule.from_parent(
                        session,
                        path=Path(ROOT + "/tests/" + name + ".py"),
                    )
                    for name in names
                ]
            )

        def pytest_collection_finish(self, session):
            expected = (
                1 if MEASURE else (PREPARATION_TESTS if PREPARATION else EXPECTED_TESTS)
            )
            if len(session.items) != expected:
                raise pytest.UsageError(f"Expected {expected} E.5d cases")

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
            ROOT + "/tests/test_genuine_backtest_operator.py",
        ],
        plugins=[Guarded()],
    )


PREPARATION_TESTS = 27
EXPECTED_TESTS = 126 + PREPARATION_TESTS
if __name__ == "__main__":
    raise SystemExit(main())

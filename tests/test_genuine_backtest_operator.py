"""Fabricated custody tests. Same-UID CI is explicitly NOT an OS isolation proof."""

import copy
import json
import os
import resource
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
import test_genuine_minute_publication as fixtures
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backtest_badger import genuine_backtest_custody as custody
from backtest_badger import genuine_backtest_operator as operator
from backtest_badger import genuine_minute_replay as public_gate

NOW = 1_790_000_000
ROOT = Path(__file__).absolute().parents[1]


@pytest.fixture
def scratch():
    import __main__

    base = getattr(__main__, "E5D_TEMP", None)
    return Path(tempfile.mkdtemp(prefix="e5d-case-", dir=base)).resolve()


@pytest.fixture(scope="module")
def invented():
    bodies, pins, _ = fixtures.fabricated.__wrapped__()
    signoff = fixtures.signoff_wire(fixtures.signoff_record(pins))
    pins = replace(pins, signoff=fixtures.fingerprint(signoff))
    return dict(zip(custody.INPUT_LIMITS, (*bodies, signoff), strict=True))


def signed(payload, key, *, domain=custody.DOMAIN):
    public = key.public_key().public_bytes_raw()
    value = {
        "schema": custody.ENVELOPE,
        "key_id": "sha256:" + sha256(public).hexdigest(),
        "payload": payload,
    }
    return custody.canonical(
        value | {"signature": key.sign(domain + custody.canonical(value)).hex()}
    )


def setup(root, bodies):
    for name in ("inputs", "runtime", "store", "publications"):
        (root / name).mkdir(mode=0o700)
    inputs = {}
    for name, body in bodies.items():
        path = root / "inputs" / (name + ".json")
        path.write_bytes(body)
        inputs[name] = {"path": str(path), "identity": custody.identity(body)}
    runtime = root / "runtime"
    (runtime / "fabricated-runtime.txt").write_bytes(b"invented runtime closure model")
    inventory = {
        "roles": {r: str(runtime) for r in custody.CLOSURE_ROLES},
        "roots": {
            str(runtime): {
                "fabricated-runtime.txt": custody.identity(
                    b"invented runtime closure model"
                )
            }
        },
    }
    p = {
        "schema": custody.SCHEMA,
        "fabricated_only": True,
        "attempt_id": "fabricated-once",
        "not_before": NOW - 10,
        "expires_at": NOW + 10,
        "maximum_attempts": 1,
        "resume": False,
        "method": custody.preparation.METHOD,
        "protocol": custody.preparation.PROTOCOL,
        "inputs": inputs,
        "output": str(root / "publications" / "result"),
        "implementation": {
            "commit": "a" * 40,
            "ci": {
                "commit": "a" * 40,
                "run_id": "123",
                "status": "completed",
                "conclusion": "success",
            },
            "closure": custody.identity(custody.canonical(inventory)),
        },
        "custody": {
            "store": str(root / "store"),
            "installation": "b" * 64,
            "supervisor_uid": os.getuid(),
            "worker_uid": os.getuid() + 1,
        },
        "limits": {
            "frame_bytes": 128 << 20,
            "total_output_bytes": 256 << 20,
            "wall_seconds": 600,
        },
        "publication_schema": operator.SCHEMA,
        "output_schema_identity": operator.output_schema()[1],
    }
    key = (
        Ed25519PrivateKey.generate()
    )  # Ephemeral fabricated key; never filesystem keys.
    return p, inventory, key


def enrol(p):
    # TEST installer only; production operator intentionally has no enrol/reset API.
    store = Path(p["custody"]["store"])
    (store / "installation.json").write_bytes(
        custody.canonical({"installation": p["custody"]["installation"]})
    )
    slot = store / custody.attempt_key(p)
    slot.mkdir(mode=0o700)
    (slot / "eligible.json").write_bytes(
        custody.canonical(
            {
                "approval": custody.identity(custody.canonical(p)),
                "attempt_id": p["attempt_id"],
            }
        )
    )
    return slot


def run(p, inventory, key, launch, **kwargs):
    return operator._run_fabricated(
        document=signed(p, key),
        reviewed=p,
        inventory=inventory,
        public_key=key.public_key().public_bytes_raw(),
        launch=launch,
        clock=lambda: NOW,
        mocked_principals=True,
        **kwargs,
    )


def fail(_):
    raise AssertionError("Worker must not start")


@pytest.mark.parametrize(
    "mutation",
    [
        "expired",
        "future",
        "method",
        "commit",
        "ci",
        "closure",
        "signer",
        "domain",
        "unknown",
        "genuine",
        "historical",
        "same_uid",
        "retry",
        "schema",
        "duplicate",
        "bool_limit",
    ],
)
def test_approval_rejections_before_io(scratch, invented, mutation):
    p, _, key = setup(scratch, invented)
    candidate = copy.deepcopy(p)
    if mutation == "expired":
        candidate["expires_at"] = NOW
    if mutation == "future":
        candidate["not_before"] = NOW + 1
    if mutation == "method":
        candidate["method"]["fee_bps"] = 0
    if mutation == "commit":
        candidate["implementation"]["commit"] = "c" * 40
    if mutation == "ci":
        candidate["implementation"]["ci"]["run_id"] = "999"
    if mutation == "closure":
        candidate["implementation"]["closure"]["sha256"] = "d" * 64
    if mutation == "unknown":
        candidate["extra"] = "forbidden"
    if mutation == "genuine":
        candidate["fabricated_only"] = False
    if mutation == "historical":
        candidate["inputs"]["manifest"]["identity"] = (
            custody.preparation.HISTORICAL_PINS["manifest"]
        )
    if mutation == "same_uid":
        candidate["custody"]["worker_uid"] = os.getuid()
    if mutation == "retry":
        candidate["maximum_attempts"] = 2
    if mutation == "schema":
        candidate["schema"] = custody.signing.PAYLOAD_SCHEMA
    if mutation == "bool_limit":
        candidate["limits"]["frame_bytes"] = True
    document = signed(
        candidate,
        Ed25519PrivateKey.generate() if mutation == "signer" else key,
        domain=custody.signing.DOMAIN if mutation == "domain" else custody.DOMAIN,
    )
    if mutation == "duplicate":
        document = document.replace(
            b'{"key_id":', b'{"schema":"duplicate","key_id":', 1
        )
    with pytest.raises(ValueError):
        custody.verify_approval(
            document,
            now=NOW,
            expected=p,
            public_key=key.public_key().public_bytes_raw(),
        )


def test_default_enrolled_owner_rejects_test_key(scratch, invented):
    p, _, key = setup(scratch, invented)
    with pytest.raises(ValueError):
        custody.verify_approval(signed(p, key), now=NOW, expected=p)


@pytest.mark.parametrize(
    "change", ["missing", "altered", "symlink", "ancestor", "hardlink", "fifo"]
)
def test_four_file_reader(scratch, invented, change):
    p, _, _ = setup(scratch, invented)
    file = Path(p["inputs"]["manifest"]["path"])
    if change == "ancestor":
        moved = scratch / "moved"
        file.parent.rename(moved)
        file.parent.symlink_to(moved, target_is_directory=True)
    else:
        file.unlink()
        if change == "altered":
            file.write_bytes(b"tampered")
        if change == "symlink":
            file.symlink_to(scratch / "inputs" / "integrity.json")
        if change == "hardlink":
            os.link(scratch / "inputs" / "integrity.json", file)
        if change == "fifo":
            os.mkfifo(file)
    with pytest.raises((ValueError, OSError)):
        custody.read_inputs(p)


@pytest.mark.parametrize(
    "change", ["missing", "altered", "extra", "symlink", "hardlink", "writable"]
)
def test_runtime_closure(scratch, invented, change):
    p, inventory, _ = setup(scratch, invented)
    runtime = scratch / "runtime"
    file = runtime / "fabricated-runtime.txt"
    if change == "missing":
        file.unlink()
    if change == "altered":
        file.write_bytes(b"tampered")
    if change == "extra":
        (runtime / "injected.py").write_bytes(b"extra")
    if change == "symlink":
        file.unlink()
        file.symlink_to(scratch / "inputs" / "manifest.json")
    if change == "hardlink":
        os.link(file, runtime / "alias")
    if change == "writable":
        file.chmod(0o666)
    with pytest.raises((ValueError, OSError)):
        custody.verify_closure(inventory, supervisor_uid=os.getuid())


@pytest.mark.parametrize(
    "change", ["installation", "slot", "eligible", "consumed", "mode"]
)
def test_protected_state_never_reconstructed(scratch, invented, change):
    p, _, _ = setup(scratch, invented)
    slot = enrol(p)
    if change == "installation":
        (scratch / "store" / "installation.json").unlink()
    if change == "slot":
        slot.rename(slot.with_name("lost"))
    if change == "eligible":
        (slot / "eligible.json").write_bytes(b"{}")
    if change == "consumed":
        (slot / "consumed.json").write_bytes(b"")
    if change == "mode":
        slot.chmod(0o777)
    with (
        custody.directory(scratch / "store") as fd,
        pytest.raises((ValueError, OSError)),
    ):
        custody.consume(fd, p)


@pytest.mark.parametrize(
    "point", ["created", "written", "file_synced", "directory_synced"]
)
def test_uncertain_consumption_never_retries(scratch, invented, point):
    p, _, _ = setup(scratch, invented)
    slot = enrol(p)

    def fault(event):
        if event == "consumed.json:" + point:
            raise OSError("Injected storage fault/lost acknowledgement")

    with custody.directory(scratch / "store") as fd:
        with pytest.raises(OSError):
            custody.consume(fd, p, fault=fault)
        assert (slot / "consumed.json").exists()
        with pytest.raises(FileExistsError):
            custody.consume(fd, p)


def test_concurrent_consumption_has_exactly_one_winner(scratch, invented):
    p, _, _ = setup(scratch, invented)
    enrol(p)

    def attempt(_):
        with custody.directory(scratch / "store") as fd:
            try:
                slot = custody.consume(fd, p)
            except FileExistsError:
                return False
            os.close(slot)
            return True

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(16))) == 1


@pytest.mark.parametrize(
    "point", ["created", "written", "file_synced", "directory_synced"]
)
def test_process_death_during_consumption(scratch, invented, point):
    p, _, _ = setup(scratch, invented)
    enrol(p)
    pid = os.fork()
    if pid == 0:
        with custody.directory(scratch / "store") as fd:
            custody.consume(
                fd,
                p,
                fault=lambda event: (
                    os._exit(73) if event == "consumed.json:" + point else None
                ),
            )
        os._exit(74)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 73
    with custody.directory(scratch / "store") as fd, pytest.raises(FileExistsError):
        custody.consume(fd, p)


def test_closed_genuine_routes_do_not_inspect_arguments():
    class Bomb:
        def __getattribute__(self, name):
            raise AssertionError("Inspected genuine input")

    with pytest.raises(PermissionError):
        custody.run_genuine_historical_operator(approval=Bomb())
    with pytest.raises(PermissionError):
        public_gate.replay_genuine_minute_historical(approval=Bomb())


@pytest.mark.parametrize(
    "change", ["reuse", "symlink", "overlap", "clock", "closure", "input"]
)
def test_preflight_failure_does_not_consume(scratch, invented, change):
    p, inventory, key = setup(scratch, invented)
    if change == "reuse":
        Path(p["output"]).mkdir()
    if change == "symlink":
        Path(p["output"]).symlink_to(scratch / "inputs")
    if change == "overlap":
        p["output"] = str(scratch / "inputs" / "bad-output")
    if change == "clock":
        p["expires_at"] = NOW
    if change == "closure":
        (scratch / "runtime" / "fabricated-runtime.txt").write_bytes(b"stale")
    if change == "input":
        Path(p["inputs"]["manifest"]["path"]).write_bytes(b"changed")
    slot = enrol(p)
    with pytest.raises((ValueError, OSError)):
        run(p, inventory, key, fail)
    assert not (slot / "consumed.json").exists()


@pytest.fixture(scope="module")
def full_wire(invented):
    # Real subprocess, real frozen full-year replay and reporting, MOCKED UID boundary.
    worker = operator.PipeWorker(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            str(ROOT / "tests/run_e5d_guarded.py"),
            "--worker",
        ],
        uid=os.getuid() + 1,
        gid=os.getgid(),
        seconds=600,
        maximum=128 << 20,
        mocked=True,
    )
    start = time.monotonic()
    try:
        for body in invented.values():
            worker.send(body)
        replay = worker.receive()
        retained = operator.retain_replay(replay)
        worker.send(operator.science(retained))
        report = worker.receive()
        operator.reconcile_report(report, replay=replay, retained=retained)
        worker.finish()
    finally:
        worker.close()
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    rss_bytes = rss if sys.platform == "darwin" else rss * 1024
    print(
        "E5D_FABRICATED_WORKER_MEASUREMENT",
        json.dumps(
            {
                "wall_seconds": round(time.monotonic() - start, 3),
                "peak_child_rss_bytes": rss_bytes,
                "replay_bytes": len(replay),
                "report_bytes": len(report),
                "input_bytes": sum(map(len, invented.values())),
                "scope": "full-year invented fixture; child lifetime RSS high-water",
            }
        ),
    )
    return replay, retained, report


class RecordedWorker:
    """Fast fault-state model using prior real worker bytes, never claims OS custody."""

    def __init__(self, full, slot):
        self.full, self.slot, self.received, self.sent = full, slot, 0, []

    def send(self, body):
        if len(self.sent) == 4:
            assert (self.slot / "handoff.json").exists()
            assert (self.slot / "replay.json").read_bytes() == self.full[0]
            assert operator.decode(body) == self.full[1]
        self.sent.append(body)

    def receive(self):
        self.received += 1
        return self.full[0 if self.received == 1 else 2]

    def finish(self):
        pass

    def close(self):
        pass


def test_full_supervisor_success_and_exclusive_publication(
    scratch, invented, full_wire
):
    p, inventory, key = setup(scratch, invented)
    slot = enrol(p)
    started = []
    events = []

    def launch(approved):
        assert (slot / "consumed.json").exists()
        assert "consumed.json:directory_synced" in events
        started.append(True)
        return operator.PipeWorker(
            [
                sys.executable,
                "-I",
                "-S",
                "-B",
                str(ROOT / "tests/run_e5d_guarded.py"),
                "--worker",
            ],
            uid=approved["custody"]["worker_uid"],
            gid=os.getgid(),
            seconds=600,
            maximum=128 << 20,
            mocked=True,
        )

    start = time.monotonic()
    receipt = run(p, inventory, key, launch, fault=events.append)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    multiplier = 1 if sys.platform == "darwin" else 1024
    print(
        "E5D_FABRICATED_SUPERVISOR_MEASUREMENT",
        json.dumps(
            {
                "wall_seconds": round(time.monotonic() - start, 3),
                "supervisor_lifetime_peak_rss_bytes": rss * multiplier,
                "child_lifetime_peak_rss_bytes": child.ru_maxrss * multiplier,
                "children_cpu_seconds": round(child.ru_utime + child.ru_stime, 3),
                "publication_bytes": sum(
                    path.stat().st_size for path in Path(p["output"]).iterdir()
                ),
                "custody_bytes": sum(path.stat().st_size for path in slot.iterdir()),
                "scope": "retained fixture wire included; CPU includes both workers",
            }
        ),
    )
    assert len(receipt["reports"]) == 6 and len(started) == 1
    assert (slot / "completed.json").exists()
    assert operator._read_completed_fabricated(p) == receipt
    # Completed output is never trusted from its marker alone, even later.
    for path in [
        *(
            Path(p["output"]) / n
            for n in ("evidence.json", "integrity.json", "manifest.json")
        ),
        slot / "completed.json",
        slot / "reports.json",
    ]:
        original = path.read_bytes()
        path.write_bytes(b"incomplete")
        with pytest.raises((ValueError, OSError)):
            operator._read_completed_fabricated(p)
        path.write_bytes(original)  # Restore this disposable corruption fixture only.
    assert (Path(p["output"]) / "evidence.json").read_bytes() == full_wire[2]
    for name in ("evidence.json", "integrity.json", "manifest.json"):
        assert (Path(p["output"]) / name).stat().st_mode & 0o777 == 0o600
    exported = (Path(p["output"]) / "integrity.json").read_bytes()
    assert str(scratch).encode() not in exported and b'"signature"' not in exported
    with pytest.raises((ValueError, OSError)):
        run(p, inventory, key, fail)


FAULT_FILES = [
    "inputs.json",
    "inputs-after.json",
    "replay.json",
    "handoff.json",
    "reports.json",
    "evidence.json",
    "integrity.json",
    "manifest.json",
    "completed.json",
]
FAULTS = [
    f"{name}:{phase}"
    for name in FAULT_FILES
    for phase in ("created", "written", "file_synced", "directory_synced")
]
FAULTS += [
    "output:created",
    "output:directory_synced",
    "handoff:acknowledged",
    "publication:readback",
]


@pytest.mark.parametrize("point", FAULTS)
def test_terminal_faults_never_promote_or_retry(scratch, invented, full_wire, point):
    p, inventory, key = setup(scratch, invented)
    slot = enrol(p)

    def fault(event):
        if event == point:
            raise OSError("Injected durable-point failure")

    with pytest.raises(OSError):
        run(p, inventory, key, lambda _: RecordedWorker(full_wire, slot), fault=fault)
    assert (slot / "consumed.json").exists()
    if not point.startswith("completed.json:"):
        assert not (slot / "completed.json").exists()
    with pytest.raises((ValueError, OSError)):
        run(p, inventory, key, fail)


@pytest.mark.parametrize(
    "mutation", ["replay", "account", "report", "association", "missing"]
)
def test_report_reconciles_against_protected_retention(full_wire, mutation):
    replay, retained, report = full_wire
    value = operator.decode(report)
    if mutation == "replay":
        value["evidence"]["projection_sha256"][0] = "0" * 64
    if mutation == "account":
        value["handoff_pins"]["accounts"][0]["fingerprint"] = "0" * 64
    if mutation == "report":
        value["reports"][0]["summary"]["initial_funding"] = "99999"
    if mutation == "association":
        value["reports"][0]["account_id"] = "wrong"
    if mutation == "missing":
        value["reports"].pop()
    with pytest.raises(ValueError):
        operator.reconcile_report(
            operator.science(value), replay=replay, retained=retained
        )


@pytest.mark.parametrize(
    "failure",
    [
        "launch",
        "replay_eof",
        "report_eof",
        "ack_lost",
        "exit",
        "input_changed",
        "readback",
    ],
)
def test_worker_and_readback_failures_are_terminal(
    scratch, invented, full_wire, failure
):
    p, inventory, key = setup(scratch, invented)
    slot = enrol(p)

    class BrokenWorker(RecordedWorker):
        def send(self, body):
            if failure == "ack_lost" and len(self.sent) == 4:
                raise BrokenPipeError("Retention acknowledgement lost")
            super().send(body)

        def receive(self):
            if (failure == "replay_eof" and self.received == 0) or (
                failure == "report_eof" and self.received == 1
            ):
                raise EOFError("Worker died during frame")
            return super().receive()

        def finish(self):
            if failure == "exit":
                raise ValueError("Nonzero worker exit")
            if failure == "input_changed":
                Path(p["inputs"]["manifest"]["path"]).write_bytes(b"changed")

    def launch(_):
        if failure == "launch":
            raise OSError("Worker launch failed")
        return BrokenWorker(full_wire, slot)

    def fault(event):
        if failure == "readback" and event == "manifest.json:directory_synced":
            (Path(p["output"]) / "evidence.json").write_bytes(b"corrupt")

    with pytest.raises((ValueError, OSError, EOFError)):
        run(p, inventory, key, launch, fault=fault)
    assert (slot / "consumed.json").exists()
    assert not (slot / "completed.json").exists()
    with pytest.raises((ValueError, OSError)):
        operator._read_completed_fabricated(p)
    with pytest.raises((ValueError, OSError)):
        run(p, inventory, key, fail)


@pytest.mark.parametrize("failure", ["short", "zero", "file_sync", "directory_sync"])
def test_actual_storage_errors_leave_consumed_name(
    scratch, invented, monkeypatch, failure
):
    p, _, _ = setup(scratch, invented)
    slot = enrol(p)
    write, sync = os.write, custody.sync

    def broken_write(fd, body):
        if failure == "zero":
            return 0
        if failure == "short":
            write(fd, body[:1])
            raise OSError("ENOSPC after partial write")
        return write(fd, body)

    calls = 0

    def broken_sync(fd):
        nonlocal calls
        calls += 1
        if (failure == "file_sync" and calls == 1) or (
            failure == "directory_sync" and calls == 2
        ):
            raise OSError("Durability unknown")
        return sync(fd)

    with monkeypatch.context() as patch:
        patch.setattr(os, "write", broken_write)
        patch.setattr(custody, "sync", broken_sync)
        with (
            custody.directory(scratch / "store") as fd,
            pytest.raises((ValueError, OSError)),
        ):
            custody.consume(fd, p)
    assert (slot / "consumed.json").exists()
    with custody.directory(scratch / "store") as fd, pytest.raises(FileExistsError):
        custody.consume(fd, p)


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"short",
        (129 << 20).to_bytes(8, "big"),
        (10).to_bytes(8, "big") + b"partial",
    ],
)
def test_incomplete_or_oversized_frames_fail(body):
    import io

    with pytest.raises(ValueError):
        operator._read_frame(io.BytesIO(body))


def test_worker_deadline_and_same_uid_refusal():
    command = [
        sys.executable,
        "-I",
        "-S",
        "-B",
        str(ROOT / "tests/run_e5d_guarded.py"),
        "--worker",
    ]
    with pytest.raises(ValueError):
        operator.PipeWorker(
            command, uid=os.getuid(), gid=os.getgid(), seconds=1, maximum=128 << 20
        )
    worker = operator.PipeWorker(
        command,
        uid=os.getuid() + 1,
        gid=os.getgid(),
        seconds=0.01,
        maximum=128 << 20,
        mocked=True,
    )
    try:
        with pytest.raises(ValueError, match="deadline"):
            worker.receive()  # No input is sent; no economic calculation starts.
    finally:
        worker.close()


@pytest.mark.parametrize(
    "mutation", ["unknown_nested", "private_string", "private_key", "wrong_type"]
)
def test_recursive_privacy_allowlist(full_wire, mutation):
    value = operator.decode(full_wire[2])
    if mutation == "unknown_nested":
        value["reports"][0]["summary"]["secret"] = "/private/fabricated-secret"
    if mutation == "private_string":
        value["reports"][0]["summary"]["label"] = "/private/fabricated-secret"
    if mutation == "private_key":
        value["evidence"]["source_identities"]["code_sha256"][
            "/private/fabricated-secret"
        ] = "0" * 64
    if mutation == "wrong_type":
        value["reports"][0]["summary"]["execution_interval_seconds"] = "60"
    with pytest.raises(ValueError):
        operator.validate_output(value, operator.output_schema()[0])


def test_expiry_rechecked_at_consumption(scratch, invented):
    p, inventory, key = setup(scratch, invented)
    slot = enrol(p)
    times = iter([NOW, NOW, NOW + 10])
    with pytest.raises(ValueError):
        operator._run_fabricated(
            document=signed(p, key),
            reviewed=p,
            inventory=inventory,
            public_key=key.public_key().public_bytes_raw(),
            launch=fail,
            clock=lambda: next(times),
            mocked_principals=True,
        )
    assert not (slot / "consumed.json").exists()

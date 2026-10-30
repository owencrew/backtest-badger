"""Emit a read-only in-memory benchmark for the authorised Lightsail host.

Build isolated JS bundles locally first. Pipe this program's output into the
installed Python on Lightsail with PYTHONDONTWRITEBYTECODE=1 and single-threaded
BLAS. No evidence or credential values are returned; no remote files are written.
This is NOT a publisher or a substitute for a quota-constrained activation trial.
"""

import argparse
import hashlib
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("validator", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
modules = {
    name: (root / "web/scripts" / f"{name}.py").read_text()
    for name in ("public_forward_export", "public_forward_v2")
}
hashes = {
    name: hashlib.sha256((root / "src/backtest_badger" / name).read_bytes()).hexdigest()
    for name in ("forward.py", "forward_evaluation.py")
}
print("modules = " + repr(modules))
print("expected_hashes = " + repr(hashes))
print("validator = " + repr(args.validator.read_text()))
print("""
import hashlib, json, resource, signal, subprocess, sys, time, types
from pathlib import Path
started = time.perf_counter()
def expired(*args):
    raise TimeoutError("Read-only benchmark deadline")
signal.signal(signal.SIGALRM, expired)
signal.alarm(90)
for name, expected in expected_hashes.items():
    path = Path("/opt/backtest-badger-public-feed/src/backtest_badger") / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("Frozen dependency identity mismatch")
for name, source in modules.items():
    module = types.ModuleType(name)
    module.__file__ = "/opt/backtest-badger-public-feed/web/scripts/" + name + ".py"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
v2 = sys.modules["public_forward_v2"]
folder = Path("/var/lib/backtest-badger/artifacts")
sources = tuple(folder / name for name in
    ("forward-predictions", "forward-outcomes", "forward-operations"))
measurements = []
original_inventory = v2.inventory
def inventory(paths):
    start = time.perf_counter()
    result = original_inventory(paths)
    measurements.append({"seconds": time.perf_counter() - start, "files": len(result)})
    return result
v2.inventory = inventory
def io_counts():
    return {k: int(v) for k, v in
        (line.split(":") for line in Path("/proc/self/io").read_text().splitlines())}
before_io = io_counts()
start = time.perf_counter()
value = v2.prepare(*sources)
preparation_seconds = time.perf_counter() - start
body = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\\n").encode()
start = time.perf_counter()
subprocess.run(["/opt/backtest-badger-public-feed/node/bin/node", "-e", validator],
    input=body, capture_output=True, check=True, timeout=30)
validator_seconds = time.perf_counter() - start
usage = resource.getrusage(resource.RUSAGE_SELF)
after_io = io_counts()
print(json.dumps({
    "status": "genuine-v2-read-only-benchmark-passed",
    "total_seconds": time.perf_counter() - started,
    "preparation_seconds": preparation_seconds,
    "validator_seconds": validator_seconds,
    "python_cpu_user_seconds": usage.ru_utime,
    "python_cpu_system_seconds": usage.ru_stime,
    "peak_rss_kib": usage.ru_maxrss,
    "io_delta": {k: after_io[k] - before_io[k] for k in before_io},
    "inventory": measurements,
    "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
    "as_of": value["as_of"], "generated_at": value["generated_at"],
    "latest": [{k: r[k] for k in ("symbol", "source_close_at", "status")}
        for r in value["latest"]],
    "latest_scored": [{k: r[k] for k in ("symbol", "source_close_at", "scored_at")}
        for r in value["latest_scored"]],
}))
""")

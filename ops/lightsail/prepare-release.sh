#!/bin/bash
# Operator-run, new release only. No DB, scheduler or evidence writes.
set -euo pipefail
umask 077
revision=${1:?Usage: prepare-release.sh FULL_GIT_COMMIT}
[[ $revision =~ ^[0-9a-f]{40}$ ]] || { echo 'Require a full commit SHA.' >&2; exit 1; }
[[ $(pwd -P) == "/opt/backtest-badger/releases/$revision" ]] || {
    echo 'Run from the matching new release directory.' >&2; exit 1;
}
[[ $(git rev-parse HEAD) == "$revision" && -z $(git status --porcelain) ]] || {
    echo 'Require a clean checkout of the requested commit.' >&2; exit 1;
}
[[ ! -e .venv && ! -e deployment.json && ! -e artifacts && ! -L artifacts ]] || {
    echo 'Refusing to replace an existing environment or artifacts.' >&2; exit 1;
}
command -v uv >/dev/null || { echo 'Missing uv.' >&2; exit 1; }
python_bin=$(uv python find --no-python-downloads 3.12.15)
[[ $("$python_bin" -c 'import platform; print(platform.python_version())') == 3.12.15 ]]
before=$(sha256sum uv.lock pyproject.toml)
uv sync --locked --no-dev --no-install-project --no-build \
    --python "$python_bin" --no-python-downloads
[[ $(sha256sum uv.lock pyproject.toml) == "$before" ]]
# Source-path installation avoids resolving an unpinned isolated build backend.
# The console script delegates directly to the existing project entry point.
.venv/bin/python - <<'PY'
import sysconfig
from pathlib import Path

root = Path.cwd()
Path(sysconfig.get_path("purelib"), "backtest_badger.pth").write_text(str(root / "src") + "\n")
entry = root / ".venv/bin/badger"
entry.write_text(f"#!{root}/.venv/bin/python\n"
                 "from backtest_badger.cli import main\nraise SystemExit(main())\n")
entry.chmod(0o700)
PY
ln -s /var/lib/backtest-badger/artifacts artifacts
.venv/bin/python - "$revision" <<'PY'
import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

data = {
    "deployment_version": "lightsail-d1-v1",
    "environment": "lightsail-ubuntu-24.04-x86_64",
    "git_commit": sys.argv[1],
    "python": platform.python_version(),
    "platform": platform.platform(),
    "machine": platform.machine(),
    "uv": subprocess.check_output(["uv", "--version"], text=True).strip(),
    "prepared_at": datetime.now(UTC).isoformat(),
    "files_sha256": {
        name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
        for name in ["uv.lock", "pyproject.toml",
                     "docs/stage-03c-forward-evaluation-protocol.md",
                     *map(str, sorted(Path("src/backtest_badger").glob("*.py")))]
    },
    "packages": {name: version(name) for name in (
        "numpy", "scipy", "scikit-learn", "joblib", "threadpoolctl", "psycopg",
        "alembic",
    )},
}
with Path("deployment.json").open("x") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PY
echo 'Release prepared. No current link, database or systemd service was changed.'

"""Exclusive manifest-last publication/verification in supplied temporary roots.

No genuine source paths can be opened here. Provenance reads a fixed allowlist of
implementation/protocol/lock files only. There is deliberately no executable CLI.
"""

import json
import os
import platform
import subprocess
import tempfile
from datetime import datetime
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

from backtest_badger.paper_accounting import Account
from backtest_badger.paper_historical import HistoricalMark, HourlyReference
from backtest_badger.paper_historical_evaluation import (
    END,
    KIND,
    PROTOCOL_REVISION,
    PROTOCOL_SHA256,
    PROTOCOL_VERSION,
    START,
    SYMBOLS,
    adapt_inputs,
    evaluate_bundle,
    json_bytes,
    ledger_records,
    scientific_payloads,
    verify_account,
)
from backtest_badger.paper_types import (
    D,
    Movement,
    Portfolio,
    Side,
    Trade,
    digest,
    require,
)

FILES = (
    "policy.json",
    "source_evidence.json",
    "decisions.json",
    "orders_trades.json",
    "ledger.json",
    "hourly_marks.json",
    "summary.json",
    "daily_monthly.csv",
    "summary.md",
)
IMPLEMENTATIONS = (
    "paper_historical_evaluation.py",
    "paper_historical_publication.py",
    "paper_historical.py",
    "paper_types.py",
    "paper_strategy.py",
    "paper_execution.py",
    "paper_accounting.py",
    "forecast_data.py",
    "execution_data.py",
    "archives.py",
    "candles.py",
    "ingestion.py",
    "evaluation.py",
    "model_data.py",
    "features.py",
    "frozen.py",
)


def implementation_provenance():
    """Code-only fingerprint; no artifact inspection or environment secrets."""
    source = Path(__file__).resolve().parent
    root = source.parent.parent
    protocol = root / "docs/stage-04b2-historical-validation-protocol.md"
    require(
        sha256(protocol.read_bytes()).hexdigest() == PROTOCOL_SHA256,
        "Frozen protocol bytes changed; stop for review.",
    )

    def git(*args):
        try:
            return subprocess.run(
                ["git", *args], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    status = git("status", "--porcelain", "--untracked-files=normal")
    return {
        "source_sha256": {
            name: sha256((source / name).read_bytes()).hexdigest()
            for name in IMPLEMENTATIONS
        },
        "uv_lock_sha256": sha256((root / "uv.lock").read_bytes()).hexdigest(),
        "pyproject_sha256": sha256((root / "pyproject.toml").read_bytes()).hexdigest(),
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "dependencies": {
                p: version(p)
                for p in ("numpy", "scikit-learn", "scipy", "joblib", "threadpoolctl")
            },
        },
        "git_revision": git("rev-parse", "HEAD"),
        "git_dirty": None if status is None else bool(status),
        "protocol_git_revision": git(
            "log",
            "-1",
            "--format=%H",
            "--",
            "docs/stage-04b2-historical-validation-protocol.md",
        ),
    }


def _temporary_directory(directory, temporary_root):
    root = Path(temporary_root).resolve(strict=True)
    require(
        root.is_dir()
        and any(
            root.is_relative_to(p.resolve())
            for p in (Path(tempfile.gettempdir()), Path("/tmp"))
        ),
        "Expected test-owned temporary root.",
    )
    path = Path(directory)
    require(
        path.parent.resolve(strict=True) == root
        and path.name not in ("", ".", "..")
        and "artifacts" not in path.parts
        and "artifacts" not in root.parts,
        "Destination must be a direct child of the supplied temporary root.",
    )
    require(not path.is_symlink(), "Symlink publication destination refused.")
    return root / path.name


def _write_exclusive(path, body):
    """Retain staging, fsync, then publish exclusively by atomic hard link."""
    partial = path.with_name(path.name + ".partial")
    with partial.open("xb") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    os.link(partial, path)  # Never replace an existing scientific file.
    partial.unlink()


def _portfolio(data):
    return Portfolio(
        **{**data, "inception_at": datetime.fromisoformat(data["inception_at"])}
    )


def _account(data):
    return Account(
        **{
            **data,
            "portfolio": _portfolio(data["portfolio"]),
            **{
                key: D(data[key])
                for key in ("cash", "quantity", "basis", "realised", "fees")
            },
            "at": datetime.fromisoformat(data["at"]),
            "trade_ids": tuple(data["trade_ids"]),
        }
    )


def _trade(data):
    return Trade(
        **{
            **data,
            "portfolio": _portfolio(data["portfolio"]),
            "side": Side(data["side"]),
            "at": datetime.fromisoformat(data["at"]),
            **{key: D(data[key]) for key in ("quantity", "price", "notional", "fee")},
            "postings": tuple(
                Movement(p["asset"], D(p["amount"])) for p in data["postings"]
            ),
        }
    )


def _mark(data, portfolio, trade_ids):
    ref = data["reference"]
    return HistoricalMark(
        **{
            **data,
            "reference": HourlyReference(
                **{
                    **ref,
                    "at": datetime.fromisoformat(ref["at"]),
                    "price": D(ref["price"]),
                }
            ),
            "account": _account(
                {
                    **data["account"],
                    "portfolio": portfolio,
                    "trade_ids": trade_ids[data["ledger_seq"]],
                }
            ),
            "equity": D(data["equity"]),
            "unrealised": D(data["unrealised"]),
        }
    )


def verify_payloads(files):
    """Deserialize and independently replay every account/mark and signed ledger."""
    require(set(files) == set(FILES), "Missing/unexpected scientific output.")
    accounts = json.loads(files["orders_trades.json"])
    marks = json.loads(files["hourly_marks.json"])
    ledger = json.loads(files["ledger.json"])
    require(
        len(accounts) == 6 and set(accounts) == set(marks) == set(ledger),
        "Expected six independent accounts.",
    )
    checks = {}
    reference_grids, identities = {}, set()
    for key, data in accounts.items():
        initial, final = _account(data["initial"]), _account(data["final"])
        trades = tuple(_trade(t) for t in data["trades"])
        ids = tuple(t.identity for t in trades)
        prefixes = {1 + 2 * i: ids[:i] for i in range(len(ids) + 1)}
        observations = tuple(
            _mark(m, data["initial"]["portfolio"], prefixes) for m in marks[key]
        )
        require(key == initial.portfolio.key, "Account identity mismatch.")
        identity = initial.portfolio.symbol, data["label"]
        require(identity not in identities, "Duplicate market/account role.")
        identities.add(identity)
        if observations:
            refs = tuple(m.reference for m in observations)
            previous = reference_grids.setdefault(initial.portfolio.symbol, refs)
            require(
                previous == refs, "Accounts lack matched original hourly references."
            )
        require(
            len(observations) == (0 if data["status"] == "unavailable" else 8784),
            "Incorrect published hourly coverage.",
        )
        checks[key] = verify_account(initial, trades, observations, final)
        require(
            json_bytes(ledger[key]) == json_bytes(ledger_records(initial, trades)),
            "Signed ledger differs from shared replay.",
        )
    require(
        identities
        == {(s, label) for s in SYMBOLS for label in ("ridge", "cash", "buy_and_hold")},
        "Wrong market/account roles.",
    )
    return checks


def publish_synthetic(
    destination, forecast_result, execution_result, *, evidence, temporary_root
):
    """Reserve once, evaluate twice, verify readback, publish manifest LAST.

    An interrupted/failed attempt is never resumed. Investigate it and use a new
    temporary destination. All fixture output explicitly disclaims authentication.
    """
    path = _temporary_directory(destination, temporary_root)
    path.mkdir()  # Includes refusal of an apparently empty existing directory.
    try:
        provenance = implementation_provenance()
        require(
            provenance["protocol_git_revision"] in (None, PROTOCOL_REVISION),
            "Protocol revision changed; review required.",
        )
        bundle = adapt_inputs(forecast_result, execution_result, evidence=evidence)
        report = evaluate_bundle(bundle)
        files = scientific_payloads(report)
        reproduced = scientific_payloads(evaluate_bundle(bundle))
        require(files == reproduced, "Scientific reproduction failed.")
        for name in FILES:
            _write_exclusive(path / name, files[name])
        retained = {name: (path / name).read_bytes() for name in FILES}
        require(retained == files, "Written scientific bytes differ.")
        checks = verify_payloads(retained)
        require(
            provenance == implementation_provenance(),
            "Implementation changed during publication.",
        )
        manifest = {
            "schema_version": 1,
            "experiment_version": "stage-4b2-base-v1",
            "kind": KIND,
            "status": "synthetic_test",
            "source_authentication": (
                "mocked_identifiers_not_genuine_file_authentication"
            ),
            "markets": SYMBOLS,
            "start": START,
            "end_exclusive": END,
            "protocol_version": PROTOCOL_VERSION,
            "protocol_sha256": PROTOCOL_SHA256,
            "protocol_git_revision": PROTOCOL_REVISION,
            "config_sha256": report["policy"]["config_sha256"],
            "input_identities": report["source_evidence"],
            "provenance": provenance,
            "coverage": {
                "expected_forecasts_per_market": 2195,
                "actual_forecasts": {
                    s: len(bundle.forecasts[i]) for i, s in enumerate(SYMBOLS)
                },
                "expected_hours_per_market": 8784,
                "actual_hours": {
                    s: len(bundle.references[i]) for i, s in enumerate(SYMBOLS)
                },
                "monthly_sources": 24,
                "missing": 0,
                "rejected": 0,
            },
            "reconciliation": checks,
            "outputs": {
                name: {"bytes": len(body), "sha256": sha256(body).hexdigest()}
                for name, body in files.items()
            },
        }
        body = json_bytes(manifest)
        _write_exclusive(path / "manifest.json", body)
        return sha256(body).hexdigest()  # External manifest identity, never recursive.
    except BaseException:
        # A hard kill may leave .partial files without this marker; no manifest
        # means uncommitted science. Even a late manifest-write failure fails closed.
        (path / "manifest.json").unlink(missing_ok=True)
        try:
            _write_exclusive(
                path / "failure.json",
                json_bytes(
                    {
                        "status": "failed_synthetic_publication",
                        "resume": False,
                        "recovery": (
                            "retain this attempt; investigate; "
                            "choose a fresh temporary destination"
                        ),
                    }
                ),
            )
        except OSError:
            pass
        raise


def verify_publication(directory, *, temporary_root, expected_manifest_sha256):
    """External manifest pin + all sizes/hashes + full shared-accounting replay."""
    digest(expected_manifest_sha256)
    path = _temporary_directory(directory, temporary_root)
    require(not (path / "manifest.json").is_symlink(), "Symlink manifest refused.")
    require(
        not (path / "failure.json").exists(), "Failed attempt is not a publication."
    )
    body = (path / "manifest.json").read_bytes()
    require(
        sha256(body).hexdigest() == expected_manifest_sha256,
        "Manifest identity mismatch.",
    )
    manifest = json.loads(body)
    require(
        manifest["status"] == "synthetic_test"
        and manifest["kind"] == KIND
        and manifest["protocol_sha256"] == PROTOCOL_SHA256
        and set(manifest["outputs"]) == set(FILES),
        "Invalid synthetic manifest.",
    )
    files = {}
    for name in FILES:
        require(not (path / name).is_symlink(), "Symlink output refused.")
        files[name] = (path / name).read_bytes()
        require(
            manifest["outputs"][name]
            == {
                "bytes": len(files[name]),
                "sha256": sha256(files[name]).hexdigest(),
            },
            "Missing/altered published output.",
        )
    require(
        verify_payloads(files) == manifest["reconciliation"],
        "Manifest reconciliation mismatch.",
    )
    return manifest

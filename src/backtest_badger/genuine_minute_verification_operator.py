"""Legacy closed gate, restricted fixtures, and shared verification publication.

The separate signed genuine entry point lives in genuine_minute_verification_runtime.
Fixture permissions and bindings remain distinct from that production route.
"""

import hashlib
import importlib.metadata
import os
import platform
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from backtest_badger import genuine_minute_inputs as auth
from backtest_badger.paper_types import digest, require

SCHEMA = "minute-input-verification-approval-v1"
SOURCE_KIND = "fabricated_temporary_fixture_bytes"
DESTINATION = "artifacts/audits/stage-04b2d3-minute-inputs-v1"
IMPLEMENTATION_FILES = tuple(
    sorted(
        {
            *auth.parity.IMPLEMENTATION_FILES,
            *(
                f"src/backtest_badger/{name}.py"
                for name in (
                    "__init__",
                    "config",
                    "db",
                    "features",
                    "forecast_data",
                    "genuine_minute_inputs",
                    "genuine_minute_verification_operator",
                    "history",
                    "research",
                )
            ),
            "docs/stage-04b2d3-genuine-minute-input-authentication.md",
            "docs/stage-04b2d4-genuine-verification-operator.md",
            "docs/stage-04b2d1-genuine-price-parity-audit.md",
        }
    )
)
DEPENDENCIES = (
    "alembic",
    "numpy",
    "psycopg",
    "psycopg-binary",
    "scikit-learn",
    "scipy",
    "SQLAlchemy",
    "joblib",
    "threadpoolctl",
)
APPROVAL_FIELDS = {
    "schema",
    "source_kind",
    "commit",
    "ci",
    "runtime",
    "implementation",
    "roots",
    "destination",
    "input_inventory",
    "pins",
    "monthly_sources",
    "hourly_monthly",
    "audit_code",
    "verification_only",
    "strategy_authorised",
    "economic_publication_authorised",
    "single_attempt",
    "resume",
}


class _SourceKind(Enum):
    FIXTURE = SOURCE_KIND
    GENUINE = "genuine_retained_stage2b_native_minute_prior_parity"
    SYNTHETIC_TEST = "synthetic_test_fabricated_signed_genuine_path"


@dataclass(frozen=True)
class _SourceRoots:
    forecast: Path
    minute: Path
    parity: Path


def run_genuine_minute_verification(*, approval) -> auth.AuthenticatedMinuteInputs:
    """Unconditionally refuse BEFORE inspecting approval or any filesystem path."""
    raise PermissionError(
        "Genuine verification wiring and invocation are not approved."
    )


def _json(value):
    return auth.policy.json_bytes(value)


def _bytes_identity(body):
    return {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def _without_stats(snapshot):
    return {
        name: {k: v for k, v in item.items() if k != "stat"}
        for name, item in snapshot.items()
    }


def _read_environment(checkout):
    """Read-only local checks; CI success is separately retained approval evidence."""

    def git(*args):
        return (
            subprocess.check_output(
                ["git", *args],
                cwd=checkout,
                env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
            )
            .decode()
            .strip()
        )

    return {
        "commit": git("rev-parse", "HEAD"),
        "clean": not git("status", "--porcelain=v1", "--untracked-files=all"),
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "dependencies": {
                name: importlib.metadata.version(name) for name in DEPENDENCIES
            },
        },
    }


def _validate_approval(approval, root):
    """Detach the supplied TEST declarations before any callbacks or source reads."""
    require(
        type(approval) is dict and set(approval) == APPROVAL_FIELDS,
        "Incomplete approval schema.",
    )
    approved = auth._json(_json(approval))
    require(
        approved["schema"] == SCHEMA
        and approved["source_kind"] == SOURCE_KIND
        and approved["verification_only"] is True
        and approved["single_attempt"] is True
        and approved["resume"] is False
        and approved["strategy_authorised"] is False
        and approved["economic_publication_authorised"] is False,
        "Invalid verification-only authority.",
    )
    require(
        type(approved["commit"]) is str
        and re.fullmatch("[0-9a-f]{40}", approved["commit"]),
        "Full reviewed commit required.",
    )
    ci = approved["ci"]
    require(
        set(ci) == {"commit", "run_id", "status", "conclusion"}
        and ci["commit"] == approved["commit"]
        and type(ci["run_id"]) is str
        and re.fullmatch("[1-9][0-9]*", ci["run_id"])
        and ci["status"] == "completed"
        and ci["conclusion"] == "success",
        "Successful CI for reviewed commit required.",
    )
    runtime = approved["runtime"]
    require(
        set(runtime) == {"python", "implementation", "dependencies"}
        and set(runtime["dependencies"]) == set(DEPENDENCIES)
        and all(
            type(v) is str and v
            for v in (
                runtime["python"],
                runtime["implementation"],
                *runtime["dependencies"].values(),
            )
        ),
        "Exact runtime/dependency versions required.",
    )
    require(
        approved["roots"]
        == {n: str(root / n) for n in ("forecast", "minute", "parity")}
        and approved["destination"] == str(root / "output"),
        "Exact fixture roots/destination required.",
    )
    pins = approved["pins"]
    require(set(pins) == set(auth.EXTERNAL_PINS), "Incomplete external pins.")
    for value in pins.values():
        digest(value)
        require(
            value not in auth.EXTERNAL_PINS.values(),
            "Genuine identity forbidden in fixture approval.",
        )
    inventories = approved["input_inventory"]
    require(
        set(inventories) == {"forecast", "minute", "parity"}, "Wrong source groups."
    )
    for group, names in (
        ("forecast", {"manifest.json", "validation_predictions.csv"}),
        ("minute", auth._release_names("1m")),
        ("parity", set(auth.PARITY_FILES)),
        ("implementation", set(IMPLEMENTATION_FILES)),
    ):
        identities = (
            approved["implementation"]
            if group == "implementation"
            else inventories[group]
        )
        require(set(identities) == names, "Wrong exact file allowlist.")
        for item in identities.values():
            require(
                set(item) == {"sha256", "bytes"}
                and type(item["bytes"]) is int
                and item["bytes"] > 0,
                "Exact independent hash/size required.",
            )
            digest(item["sha256"])
    auth._check_pins(
        inventories, pins, inventories["minute"]["minute_opens.csv"]["bytes"]
    )
    for path, key in (
        (auth.parity.HOURLY_PROTOCOL, "hourly_protocol"),
        (auth.parity.MINUTE_PROTOCOL, "minute_protocol"),
        (auth.parity.PIN_DOCUMENT, "minute_pin_document"),
    ):
        require(
            approved["implementation"][path]["sha256"] == pins[key],
            "Reviewed document and external declaration disagree.",
        )
    expected_months = [(r.symbol, r.month) for r in auth.minute.minute_requests()]
    for name in ("monthly_sources", "hourly_monthly"):
        rows = approved[name]
        require(
            type(rows) is list
            and all(type(r) is list and len(r) == 3 for r in rows)
            and [(r[0], r[1]) for r in rows] == expected_months,
            "Exact ordered monthly declarations required.",
        )
    require(
        set(approved["audit_code"]) == set(auth.parity.IMPLEMENTATION_FILES),
        "Complete retained auditor identities required.",
    )
    for value in approved["audit_code"].values():
        digest(value)
    return approved


def _code_snapshot(root, approved):
    actual = {
        name: auth._identity(root / "code" / name) for name in IMPLEMENTATION_FILES
    }
    require(
        _without_stats(actual) == approved["implementation"],
        "Reviewed implementation changed.",
    )
    return actual


def _environment(root, approved, reader):
    actual = reader(root)
    require(
        type(actual) is dict
        and actual.get("clean") is True
        and actual
        == {
            "commit": approved["commit"],
            "clean": True,
            "runtime": approved["runtime"],
        },
        "Dirty checkout or changed reviewed revision/runtime.",
    )
    return auth._json(_json(actual))


def _source_snapshot(root, approved):
    actual = auth._inventory(*(root / n for n in ("forecast", "minute", "parity")))
    require(
        {group: _without_stats(items) for group, items in actual.items()}
        == approved["input_inventory"],
        "Independent source inventory mismatch.",
    )
    return actual


def _verify_sources(
    root,
    approved,
    before,
    *,
    forecast_loader,
    minute_loader,
    lineage_validator,
    native_loader_evidence,
):
    """Restricted fixture route; never produces genuine scientific evidence."""
    return _verify_source_roots(
        _SourceRoots(*(root / name for name in ("forecast", "minute", "parity"))),
        approved,
        before,
        forecast_loader=forecast_loader,
        minute_loader=minute_loader,
        lineage_validator=lineage_validator,
        native_loader_evidence=native_loader_evidence,
        source_kind=_SourceKind.FIXTURE,
    )


def _verify_source_roots(
    roots,
    approved,
    before,
    *,
    forecast_loader,
    minute_loader,
    lineage_validator,
    native_loader_evidence,
    source_kind,
):
    """Shared scientific checks; route is explicit and cannot relabel a record."""
    require(type(roots) is _SourceRoots, "Explicit source roots required.")
    require(type(source_kind) is _SourceKind, "Explicit source route required.")
    pins = approved["pins"]
    monthly = {(s, m): row for s, m, row in approved["monthly_sources"]}
    size = approved["input_inventory"]["minute"]["minute_opens.csv"]["bytes"]
    manifest = auth._json(
        auth._read(roots.forecast / "manifest.json", pins["forecast_manifest"])
    )
    minute_manifest = auth._json(
        auth._read(roots.minute / "manifest.json", pins["minute_manifest"])
    )
    auth._minute_metadata(
        minute_manifest,
        before["minute"],
        monthly,
        pins,
        size,
        approved["implementation"]["src/backtest_badger/minute_execution_data.py"][
            "sha256"
        ],
    )
    lineage_validator(manifest)
    forecasts = auth._forecasts(forecast_loader(roots.forecast), manifest, pins)
    verified = minute_loader(
        roots.minute, expected_manifest_sha256=pins["minute_manifest"]
    )
    require(
        _json(verified) == _json(minute_manifest), "Native loader metadata mismatch."
    )
    references = auth._stream_projection(
        roots.minute / "minute_opens.csv",
        monthly,
        expected_sha256=pins["minute_csv"],
        expected_bytes=size,
    )
    bodies = {
        name: auth._read(roots.parity / name, before["parity"][name]["sha256"])
        for name in auth.PARITY_FILES
    }
    publication, report, provenance = auth._parity_evidence(
        bodies,
        pins,
        monthly,
        approved["audit_code"],
        {(s, m): value for s, m, value in approved["hourly_monthly"]},
        minute_manifest,
    )
    projections = tuple(auth.projection_sha256(refs) for refs in references)
    evidence = {
        "schema": "minute-input-scientific-evidence-v1",
        "source_kind": source_kind.value,
        "native_loader_evidence": native_loader_evidence,
        "pins": pins,
        "original_files": approved["input_inventory"],
        "code_sha256": {n: v["sha256"] for n, v in approved["implementation"].items()},
        "monthly_sources": approved["monthly_sources"],
        "recipe_identity_kind": "stage2b_manifest_sha256",
        "recipe_sha256": pins["forecast_manifest"],
        "forecast_manifest": manifest,
        "minute_metadata": minute_manifest,
        "parity_publication": publication,
        "parity_report": report,
        "parity_provenance": provenance,
        "projection_sha256": projections,
        "counts": {
            "forecast_accounts": 8,
            "forecasts_per_account": 2195,
            "native_rows": 1054080,
            "hourly_marks_per_market": 8784,
            "hypothetical_minutes_per_market": 2195,
            "references": 21958,
        },
        "limitations": auth.LIMITATIONS,
    }
    return auth.AuthenticatedMinuteInputs(
        forecasts, references, _json(evidence), projections
    )


def _directory_identity(path):
    info = auth._safe(path).lstat()
    require(stat.S_ISDIR(info.st_mode), "Expected directory.")
    return info.st_dev, info.st_ino


def _publish(fd, name, body, owned, checkpoint):
    """Exclusive partial + fsync + no-replace hard link, anchored to reserved fd."""
    partial = name + ".partial"
    checkpoint("create:" + name)
    handle = os.open(
        partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
    )
    with os.fdopen(handle, "wb") as stream:
        info = os.fstat(stream.fileno())
        owned[name] = (info.st_dev, info.st_ino)
        checkpoint("partial:" + name)
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    checkpoint("link:" + name)
    os.link(partial, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
    checkpoint("linked:" + name)
    os.unlink(partial, dir_fd=fd)
    os.fsync(fd)


def _readback(destination, payloads):
    require(
        set(os.listdir(auth._safe(destination))) == set(payloads),
        "Unexpected output inventory.",
    )
    identities = {}
    for name, expected in payloads.items():
        body = auth._read(
            destination / name,
            hashlib.sha256(expected).hexdigest(),
            limit=len(expected),
        )
        parsed = auth._json(body)
        canonical = (
            auth.scientific_json(parsed).encode("ascii")
            if name == "authenticated_inputs.json"
            else _json(parsed)
        )
        require(
            body == expected and canonical == body,
            "Noncanonical or changed output.",
        )
        identities[name] = _bytes_identity(body)
    return identities


def _crosscheck(
    payloads, approved, before, code_before, *, source_kind=_SourceKind.FIXTURE
):
    require(type(source_kind) is _SourceKind, "Explicit source route required.")
    science, integrity = (
        auth._json(payloads[n]) for n in ("authenticated_inputs.json", "integrity.json")
    )
    evidence = auth._json(science["source_evidence_json"])
    require(
        science["status"] == auth.STATUS
        and science["genuine_execution_authorised"] is False
        and evidence["source_kind"] == source_kind.value
        and evidence["pins"] == approved["pins"]
        and evidence["original_files"] == approved["input_inventory"]
        and evidence["recipe_sha256"] == approved["pins"]["forecast_manifest"]
        and evidence["code_sha256"]
        == {n: v["sha256"] for n, v in approved["implementation"].items()}
        and _json(integrity["sources_before"]) == _json(before)
        and _json(integrity["sources_after"]) == _json(before)
        and _json(integrity["code_before"]) == _json(code_before)
        and _json(integrity["code_after"]) == _json(code_before)
        and integrity["approval"] == approved,
        "Scientific/operational evidence disagrees with retained declarations.",
    )


def _run_fixture_verification(
    *,
    fixture_root,
    approval,
    forecast_loader,
    minute_loader,
    lineage_validator,
    environment_reader,
    native_loader_evidence,
) -> auth.AuthenticatedMinuteInputs:
    """PRIVATE pytest seam: no real roots/pins and no approved-by-default binding.

    Native evidence must explicitly distinguish injected metadata from unchanged
    loader revalidation of full fabricated archives. No shortening of the grid.
    """
    root = Path(fixture_root)
    temp = Path(tempfile.gettempdir()).resolve()
    require(
        root.is_absolute()
        and ".." not in root.parts
        and root.is_relative_to(temp)
        and not root.is_relative_to(auth.ROOT)
        and not {"artifacts", "crypto-trading-platform"}.intersection(root.parts),
        "Isolated fabricated temporary root required.",
    )
    approved = _validate_approval(approval, root)
    require(
        native_loader_evidence
        in (
            "injected_metadata_only_not_archive_revalidation",
            "unchanged_loader_full_fabricated_archive_revalidation",
        ),
        "Explicit native-loader test evidence required.",
    )
    if (
        native_loader_evidence
        == "unchanged_loader_full_fabricated_archive_revalidation"
    ):
        require(
            minute_loader is auth.minute.load_minute_execution_data,
            "Full native evidence requires unchanged loader binding.",
        )
    return _operate_fixture(
        root,
        approved,
        forecast_loader=forecast_loader,
        minute_loader=minute_loader,
        lineage_validator=lineage_validator,
        environment_reader=environment_reader,
        native_loader_evidence=native_loader_evidence,
    )


def _checkpoint(phase):
    """No-op fault-injection seam. It cannot grant source or execution authority."""


def _operate_fixture(root, approved, **bindings):
    destination = root / "output"
    directory_before = _directory_identity(root)
    for name in ("forecast", "minute", "parity", "code"):
        _directory_identity(root / name)
    return _operate_verified(
        destination,
        approved,
        source_kind=_SourceKind.FIXTURE,
        source_snapshot=lambda: _source_snapshot(root, approved),
        code_snapshot=lambda: _code_snapshot(root, approved),
        environment_reader=lambda: _environment(
            root, approved, bindings["environment_reader"]
        ),
        verify_sources=lambda before: _verify_sources(
            root,
            approved,
            before,
            **{k: v for k, v in bindings.items() if k != "environment_reader"},
        ),
        directory_before=directory_before,
    )


def _operate_verified(
    destination,
    approved,
    *,
    source_kind,
    source_snapshot,
    code_snapshot,
    environment_reader,
    verify_sources,
    directory_before,
):
    """Shared one-attempt publisher; callbacks are private, never public authority."""
    require(type(source_kind) is _SourceKind, "Explicit source route required.")
    root = destination.parent
    # Absence without following even a broken destination symlink; no source open.
    try:
        destination.lstat()
    except FileNotFoundError:
        pass
    else:
        raise FileExistsError("Attempt destination already reserved.")
    environment = environment_reader()
    code_before = code_snapshot()
    _checkpoint("before_reservation")
    parent_fd = os.open(auth._safe(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    fd = None
    owned = {}
    phase = "reservation"
    reserved = False
    try:
        require(
            (os.fstat(parent_fd).st_dev, os.fstat(parent_fd).st_ino)
            == directory_before,
            "Parent directory replaced.",
        )
        os.mkdir(
            destination.name, mode=0o700, dir_fd=parent_fd
        )  # Exactly once; no retry.
        reserved = True
        fd = os.open(
            destination.name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
        output_identity = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)

        def checkpoint(value):
            nonlocal phase
            phase = value
            _checkpoint(value)
            require(
                _directory_identity(root) == directory_before
                and _directory_identity(destination) == output_identity,
                "Reserved output directory moved.",
            )

        def preservation():
            require(
                source_snapshot() == before,
                "Sources changed during attempt.",
            )
            require(
                code_snapshot() == code_before,
                "Code inode/stat changed during attempt.",
            )
            require(
                environment_reader() == environment,
                "Environment changed during attempt.",
            )

        checkpoint("after_reservation")
        before = source_snapshot()
        checkpoint("source_verification")
        result = verify_sources(before)
        checkpoint("after_verification")
        preservation()
        payloads = {
            "authenticated_inputs.json": auth.authenticated_inputs_json(result),
            "integrity.json": _json(
                {
                    "schema": "minute-input-operational-integrity-v1",
                    "approval": approved,
                    "environment": environment,
                    "sources_before": before,
                    "sources_after": before,
                    "code_before": code_before,
                    "code_after": code_before,
                }
            ),
        }
        _crosscheck(payloads, approved, before, code_before, source_kind=source_kind)
        for name, body in payloads.items():
            _publish(fd, name, body, owned, checkpoint)
        checkpoint("output_readback")
        identities = _readback(destination, payloads)
        _crosscheck(
            {
                n: auth._read(destination / n, v["sha256"], limit=v["bytes"])
                for n, v in identities.items()
            },
            approved,
            before,
            code_before,
            source_kind=source_kind,
        )
        checkpoint("after_output_readback")
        preservation()
        checkpoint("before_manifest")
        # Includes mutations at the last fault boundary before final publication.
        preservation()
        manifest = _json(
            {
                "schema": "minute-input-verification-publication-v1",
                "kind": "source_authentication_only",
                "complete": True,
                "status": auth.STATUS,
                "source_kind": source_kind.value,
                "genuine_execution_authorised": False,
                "economic_results": False,
                "files": identities,
            }
        )
        _publish(fd, "manifest.json", manifest, owned, checkpoint)
        checkpoint("after_manifest")
        _readback(destination, {**payloads, "manifest.json": manifest})
        preservation()
        return result
    except BaseException as error:
        if reserved and fd is not None:
            # Only our own inode may be invalidated; never delete someone else's
            # collision or clean up partial/scientific evidence from this attempt.
            try:
                info = os.stat("manifest.json", dir_fd=fd, follow_symlinks=False)
                if (info.st_dev, info.st_ino) == owned.get("manifest.json"):
                    os.unlink("manifest.json", dir_fd=fd)
                    os.fsync(fd)
            except FileNotFoundError:
                pass
            try:
                safe_type = next(
                    (
                        name
                        for cls, name in (
                            (OSError, "OSError"),
                            (ValueError, "ValueError"),
                            (KeyboardInterrupt, "KeyboardInterrupt"),
                        )
                        if isinstance(error, cls)
                    ),
                    "Exception",
                )
                _publish(
                    fd,
                    "failure.json",
                    _json(
                        {
                            "schema": "minute-input-incomplete-attempt-v1",
                            "phase": phase,
                            "exception_type": safe_type,
                            "complete": False,
                            "resume": False,
                        }
                    ),
                    {},
                    lambda _: None,
                )
            except BaseException:
                pass  # Best effort only (disk failure/hard kill can prevent it).
        raise
    finally:
        if fd is not None:
            os.close(fd)
        os.close(parent_fd)

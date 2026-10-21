"""Signed genuine verification route, inactive until independent owner enrolment.

No CLI, key/observer/loader injection or signing API. The public call checks the
owner signature before any checkout, source or destination observation. Private
callbacks exist solely for fabricated tests, which publish a distinct test kind.
"""

import importlib.metadata
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

from backtest_badger import genuine_minute_signed_approval as signed
from backtest_badger import genuine_minute_verification_operator as operator
from backtest_badger.paper_types import require

auth = operator.auth
wiring = signed.wiring


def run_genuine_minute_verification(*, approval) -> auth.AuthenticatedMinuteInputs:
    """One signed read-only attempt, with original fixed production bindings."""
    detached = signed.preflight_owner_approval(approval=approval)
    approved = auth._json(detached)
    return _prepare_and_operate(
        approved,
        checkout=auth.ROOT,
        source_kind=operator._SourceKind.GENUINE,
        environment_reader=_read_environment,
        declaration_reader=_declared_sources,
        forecast_loader=auth.forecast.load_forecasts,
        lineage_validator=auth.policy._validate_lineage,
    )


def _git(checkout, *args):
    # Do not inherit alternate index/worktree/config or executable hook overrides.
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment.update(GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1")
    return subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", *args],
        cwd=checkout,
        env=environment,
        stderr=subprocess.DEVNULL,
    ).decode("utf-8")


def _read_environment(checkout):
    """Offline local observations only; there is deliberately no CI observer.

    Never traverse artifact roots via Git status. First reject tracked artifacts;
    status then covers every non-artifact path, including new untracked files.
    """
    require(
        _git(checkout, "rev-parse", "--show-toplevel").strip() == str(checkout),
        "Running checkout root differs.",
    )
    entries = _git(checkout, "ls-files", "--stage", "-z").split("\0")
    for entry in filter(None, entries):
        identity, name = entry.split("\t", 1)
        mode, _, stage = identity.split()
        require(
            stage == "0"
            and mode in ("100644", "100755")
            and name != "artifacts"
            and not name.startswith("artifacts/"),
            "Unsupported tracked checkout entry.",
        )
    flags = _git(checkout, "ls-files", "-v", "-z").split("\0")
    require(
        all(entry.startswith("H ") for entry in flags if entry),
        "Hidden index changes are forbidden.",
    )
    for name in signed.IMPLEMENTATION_FILES:
        if not name.startswith("src/") or not name.endswith(".py"):
            continue
        module = sys.modules.get(name[4:-3].replace("/", "."))
        if name.endswith("/__init__.py"):
            module = sys.modules.get(name[4:-12].replace("/", "."))
        if module is not None:
            require(
                Path(module.__file__).absolute() == checkout / name,
                "Imported code is outside reviewed checkout.",
            )
    dependencies = signed.DEPENDENCIES | (
        {"tzdata"} if sys.platform == "win32" else set()
    )
    return {
        "commit": _git(checkout, "rev-parse", "HEAD").strip(),
        "clean": not _git(
            checkout,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            ".",
            ":(exclude)artifacts",
        ).strip(),
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": sys.platform,
            "dependencies": {
                name: importlib.metadata.version(name) for name in sorted(dependencies)
            },
        },
    }


def _code_snapshot(checkout, approved):
    actual = {
        name: auth._identity(checkout / name) for name in signed.IMPLEMENTATION_FILES
    }
    require(
        operator._without_stats(actual) == approved["implementation"],
        "Reviewed implementation changed.",
    )
    return actual


def _declared_sources(checkout):
    """Read only the independently hash-pinned tracked document, never sources."""
    body = auth._read(
        checkout / wiring.PIN_DOCUMENT, dict(wiring.DECLARATIONS)["minute_pin_document"]
    )
    return wiring.approval_readiness(minute_pin_document=body)


def _check_declarations(approved, declarations):
    require(
        approved["pins"] == dict(declarations.declarations),
        "Source declarations differ.",
    )
    for row in declarations.sources:
        actual = approved["input_inventory"][row.group][row.name]
        require(
            actual["sha256"] == row.sha256
            and (row.bytes is None or actual["bytes"] == row.bytes),
            "Original source identity differs.",
        )
    require(
        len(declarations.sources) == 57
        and approved["monthly_sources"]
        == [[s, m, dict(values)] for s, m, values in declarations.monthly_sources],
        "Original monthly associations differ.",
    )
    # Both forecast lengths and the complete historical auditor map are mandatory
    # signed external evidence. Never fill their gaps from source metadata.


def _source_snapshot(roots, approved):
    actual = auth._inventory(roots.forecast, roots.minute, roots.parity)
    require(
        {group: operator._without_stats(items) for group, items in actual.items()}
        == approved["input_inventory"],
        "Independent source inventory mismatch.",
    )
    return actual


def _check_source_paths(roots):
    """Metadata/inventory checks only, after code/runtime; no original file opens."""
    for directory in (roots.forecast, roots.minute, roots.parity):
        operator._directory_identity(directory)
    require(
        set(os.listdir(auth._safe(roots.minute)))
        == {"manifest.json", "minute_opens.csv", "raw"}
        and set(os.listdir(auth._safe(roots.minute / "raw")))
        == {n[4:] for n in auth._release_names("1m") if n.startswith("raw/")}
        and set(os.listdir(auth._safe(roots.parity))) == set(auth.PARITY_FILES),
        "Unexpected source inventory.",
    )
    for directory, names in (
        (roots.forecast, ("manifest.json", "validation_predictions.csv")),
        (roots.minute, auth._release_names("1m")),
        (roots.parity, auth.PARITY_FILES),
    ):
        for name in names:
            auth._stamp(auth._safe(directory / name).lstat())


def _prepare_and_operate(
    approved,
    *,
    checkout,
    source_kind,
    environment_reader,
    declaration_reader,
    forecast_loader,
    lineage_validator,
):
    """Private integration seam. A test route can only publish fabricated evidence.

    Public production supplies fixed original bindings and no injected observations.
    The legacy fixture path never enters this function or produces its records.
    """
    signed._validate_payload(
        approved, reviewed_commit=approved["commit"], ci_run_id=approved["ci"]["run_id"]
    )
    require(
        source_kind
        in (operator._SourceKind.GENUINE, operator._SourceKind.SYNTHETIC_TEST),
        "Wrong verification route.",
    )
    require(
        approved["roots"] == {n: str(checkout / p) for n, p in wiring.ROOTS}
        and approved["destination"] == str(checkout / wiring.DESTINATION),
        "Exact running checkout paths required.",
    )
    if source_kind is operator._SourceKind.GENUINE:
        require(checkout == auth.ROOT, "Running checkout required.")
        require(approved["pins"] == dict(wiring.DECLARATIONS), "Genuine pins required.")
    else:
        # No original identities or repository paths in the private TEST route.
        require(
            checkout.is_absolute()
            and ".." not in checkout.parts
            and checkout.is_relative_to(Path(tempfile.gettempdir()).resolve())
            and not checkout.is_relative_to(auth.ROOT)
            and not {"artifacts", "crypto-trading-platform"}.intersection(
                checkout.parts
            )
            and not set(approved["pins"][key] for key in auth.EXTERNAL_PINS)
            & set(auth.EXTERNAL_PINS.values()),
            "Isolated fabricated test checkout required.",
        )
    # All of this precedes even source/destination stat or directory listing.
    operator._environment(checkout, approved, environment_reader)
    _code_snapshot(checkout, approved)
    _check_declarations(approved, declaration_reader(checkout))
    roots = operator._SourceRoots(
        *(Path(approved["roots"][n]) for n in ("forecast", "minute", "parity"))
    )
    destination = Path(approved["destination"])
    _check_source_paths(roots)
    parent_identity = operator._directory_identity(destination.parent)
    return operator._operate_verified(
        destination,
        approved,
        source_kind=source_kind,
        source_snapshot=lambda: _source_snapshot(roots, approved),
        code_snapshot=lambda: _code_snapshot(checkout, approved),
        environment_reader=lambda: operator._environment(
            checkout, approved, environment_reader
        ),
        verify_sources=lambda before: operator._verify_source_roots(
            roots,
            approved,
            before,
            forecast_loader=forecast_loader,
            minute_loader=auth.minute.load_minute_execution_data,
            lineage_validator=lineage_validator,
            native_loader_evidence=(
                "unchanged_loader_full_native_archive_revalidation"
                if source_kind is operator._SourceKind.GENUINE
                else (
                    "synthetic_test_unchanged_loader_full_"
                    "fabricated_archive_revalidation"
                )
            ),
            source_kind=source_kind,
        ),
        directory_before=parent_identity,
    )

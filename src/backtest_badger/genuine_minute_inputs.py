"""Stage 4B.2D.3 verification primitives; genuine operator gate remains CLOSED.

Only the private fixture harness executes I/O in this stage. No CLI, replay,
strategy, publication, discovery, environment switch or real-root override.
Frozen records document validation, not a security capability against Python code.
"""

import calendar
import csv
import hashlib
import json
import os
import re
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from backtest_badger import forecast_data as forecast
from backtest_badger import genuine_minute_price_parity as parity
from backtest_badger import minute_execution_data as minute
from backtest_badger import paper_historical_evaluation as policy
from backtest_badger.paper_minute_historical import (
    MinuteReference,
    next_minute_at,
    projection_sha256,
    reference_identity,
    scientific_json,
)
from backtest_badger.paper_types import STEP, digest, number, require, utc

ROOT = Path(__file__).absolute().parents[2]
FORECAST_PATH = "artifacts/experiments/stage-2b-v1"
MINUTE_PATH = parity.MINUTE_PATH
PARITY_PATH = parity.OUTPUT_PATH
STATUS = "source_authentication_complete_verification_only_replay_not_authorised"
PARITY_FILES = (
    "manifest.json",
    "parity_report.json",
    "provenance.json",
    "integrity.json",
    "discrepancies.csv",
)
ACCOUNT_KEYS = tuple((s, m) for s in minute.SYMBOLS for m in forecast.MODELS)
EXTERNAL_PINS = {
    "forecast_manifest": forecast.MANIFEST_SHA256,
    "forecast_csv": forecast.CSV_SHA256,
    "research_manifest": policy.RESEARCH_MANIFEST_SHA256,
    "research_csv": policy.RESEARCH_SHA256,
    "hourly_manifest": policy.HOURLY_MANIFEST_SHA256,
    "hourly_csv": policy.HOURLY_SHA256,
    "hourly_acquisition": policy.ACQUISITION_SHA256,
    "minute_manifest": parity.MINUTE_MANIFEST_SHA256,
    "minute_csv": parity.MINUTE_CSV_SHA256,
    "parity_manifest": (
        "53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d"
    ),
    "parity_report": "0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb",
    "hourly_protocol": policy.PROTOCOL_SHA256,
    "minute_protocol": parity.EXTERNAL_PINS["documents"][parity.MINUTE_PROTOCOL],
    "minute_pin_document": parity.EXTERNAL_PINS["documents"][parity.PIN_DOCUMENT],
}
LIMITATIONS = (
    "Verification only; genuine_execution_authorised=false; no replay or economics.",
    "Prior exact price parity is not strategy authority or evidence of fillability.",
    "Availability is source open +4h+60s, not historical publication or issuance.",
    "Unsigned archive checksums establish retained-byte identity, not attestation.",
    "Before/after identities detect observed changes, not coordinated hostile races.",
    "Frozen records and fingerprints are provenance, not tamper-proof capabilities.",
)


@dataclass(frozen=True)
class VerifiedForecast:
    symbol: str
    model: str
    record_id: str
    source_open: datetime
    assumed_available_at: datetime
    hypothetical_minute_at: datetime
    prediction: Decimal
    file_sha256: str


@dataclass(frozen=True)
class AuthenticatedMinuteInputs:
    """Immutable verification record, deliberately unrelated to replay bundles."""

    forecasts: tuple[tuple[VerifiedForecast, ...], ...]
    references: tuple[tuple[MinuteReference, ...], ...]
    source_evidence_json: bytes
    projection_sha256: tuple[str, str]
    status: str = field(default=STATUS, init=False)
    genuine_execution_authorised: bool = field(default=False, init=False)


def authenticate_minute_inputs(*, approval) -> AuthenticatedMinuteInputs:
    """Reserved future interface: EVERY call fails before any path or payload read.

    The exact-root/code-pin/one-use approval and exclusive-output operator wrapper
    is a reviewed-design requirement, not executable in this stage. No value of
    approval, flag or environment variable opens this gate. See the stage guide.
    """
    raise PermissionError(
        "Genuine verification operator gate is not approved/implemented."
    )


def authenticated_inputs_json(inputs: AuthenticatedMinuteInputs) -> bytes:
    """Deterministic scientific serialization; no invented issuance timestamp."""
    require(type(inputs) is AuthenticatedMinuteInputs, "Expected authenticated type.")
    return scientific_json(
        {
            "status": inputs.status,
            "genuine_execution_authorised": inputs.genuine_execution_authorised,
            "forecasts": inputs.forecasts,
            "references": inputs.references,
            "projection_sha256": inputs.projection_sha256,
            # Recipe floats stay inside canonical metadata JSON, never predictions.
            "source_evidence_json": inputs.source_evidence_json.decode("ascii"),
        }
    ).encode("ascii")


def _json(body):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON field.")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite JSON value.")

    return json.loads(body, object_pairs_hook=pairs, parse_constant=invalid)


def _safe(path):
    path = Path(path)
    require(
        path.is_absolute() and ".." not in path.parts, "Exact absolute path required."
    )
    for part in (*reversed(path.parents), path):
        require(not stat.S_ISLNK(part.lstat().st_mode), "Symlink path refused.")
    return path


def _stamp(info):
    require(stat.S_ISREG(info.st_mode), "Expected regular file.")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


@contextmanager
def _open_checked(path):
    path = _safe(path)
    before = _stamp(path.lstat())
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        require(_stamp(os.fstat(fd)) == before, "File replaced before open.")
        stream = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    with stream:
        yield stream
        require(_stamp(os.fstat(stream.fileno())) == before, "File changed while open.")
    require(_stamp(_safe(path).lstat()) == before, "File changed after read.")


def _identity(path):
    hashed, size = hashlib.sha256(), 0
    with _open_checked(path) as stream:
        stamp = _stamp(os.fstat(stream.fileno()))
        while chunk := stream.read(1024 * 1024):
            hashed.update(chunk)
            size += len(chunk)
    require(size == stamp[2], "File length changed.")
    return {"sha256": hashed.hexdigest(), "bytes": size, "stat": stamp}


def _read(path, expected, *, limit=2 * 1024 * 1024):
    with _open_checked(path) as stream:
        body = stream.read(limit + 1)
    require(len(body) <= limit, "Oversized metadata.")
    require(hashlib.sha256(body).hexdigest() == expected, "Original byte pin mismatch.")
    return body


def _release_names(interval):
    return {
        f"raw/{s}-{interval}-2024-{m:02d}.zip{suffix}"
        for s in minute.SYMBOLS
        for m in range(1, 13)
        for suffix in ("", ".CHECKSUM")
    } | (
        {"manifest.json", "minute_opens.csv"}
        if interval == "1m"
        else {"manifest.json", "hourly_opens.csv", "acquisition.json"}
    )


def _inventory(forecast_directory, minute_directory, parity_directory):
    # Forecast directory may contain other Stage 2B outputs; never enumerate it.
    require(
        set(os.listdir(_safe(minute_directory)))
        == {"manifest.json", "minute_opens.csv", "raw"}
        and set(os.listdir(_safe(minute_directory / "raw")))
        == {
            p.removeprefix("raw/") for p in _release_names("1m") if p.startswith("raw/")
        },
        "Incomplete/unexpected minute source inventory.",
    )
    require(
        set(os.listdir(_safe(parity_directory))) == set(PARITY_FILES),
        "Wrong parity inventory.",
    )
    return {
        group: {name: _identity(directory / name) for name in sorted(names)}
        for group, directory, names in (
            (
                "forecast",
                forecast_directory,
                ("manifest.json", "validation_predictions.csv"),
            ),
            ("minute", minute_directory, _release_names("1m")),
            ("parity", parity_directory, PARITY_FILES),
        )
    }


def _check_pins(snapshot, pins, processed_bytes):
    for group, name, key in (
        ("forecast", "manifest.json", "forecast_manifest"),
        ("forecast", "validation_predictions.csv", "forecast_csv"),
        ("minute", "manifest.json", "minute_manifest"),
        ("minute", "minute_opens.csv", "minute_csv"),
        ("parity", "manifest.json", "parity_manifest"),
        ("parity", "parity_report.json", "parity_report"),
    ):
        require(
            snapshot[group][name]["sha256"] == pins[key],
            "Independent source pin mismatch.",
        )
    require(
        snapshot["minute"]["minute_opens.csv"]["bytes"] == processed_bytes,
        "Processed size mismatch.",
    )


def _minute_metadata(
    manifest, snapshot, monthly, pins, processed_bytes, implementation
):
    require(
        policy.json_bytes(manifest)
        == policy.json_bytes(
            minute._manifest(
                manifest["sources"], pins["minute_csv"], processed_bytes, implementation
            )
        ),
        "Wrong minute format/coverage/status/implementation.",
    )
    require(
        tuple(monthly) == tuple((r.symbol, r.month) for r in minute.minute_requests()),
        "Wrong source order.",
    )
    require(len(manifest["sources"]) == 24, "Incomplete source associations.")
    for request, source in zip(
        minute.minute_requests(), manifest["sources"], strict=True
    ):
        pinned = monthly[request.symbol, request.month]
        expected = {
            **pinned,
            "symbol": request.symbol,
            "month": request.month,
            "interval": "1m",
            "observation_kind": "retrospective_full_archive_acquisition",
            "validation_status": "complete_checksum_and_native_grid",
        }
        require(
            policy.json_bytes(source) == policy.json_bytes(expected),
            "Wrong frozen monthly source.",
        )
        require(
            source["url"] == request.url
            and source["checksum_url"] == request.checksum_url
            and type(source["row_count"]) is int
            and source["row_count"] == request.row_count
            and utc(datetime.fromisoformat(source["observed_at"]))
            >= minute.EPOCH
            + timedelta(milliseconds=request.start_ms, minutes=request.row_count),
            "Wrong source URL/count/receipt association.",
        )
        for suffix, hash_key, size_key in (
            ("", "sha256", "zip_bytes"),
            (".CHECKSUM", "checksum_sha256", "checksum_bytes"),
        ):
            original = snapshot[f"raw/{request.stem}.zip{suffix}"]
            digest(source[hash_key])
            require(
                original["sha256"] == source[hash_key]
                and original["bytes"] == source[size_key],
                "Original ZIP/sidecar mismatch.",
            )
        require(
            type(source["csv_bytes"]) is int and source["csv_bytes"] > 0,
            "Invalid expanded size.",
        )


def _forecasts(result, manifest, pins):
    hashes, accounts = result
    require(
        hashes
        == {
            "manifest.json": pins["forecast_manifest"],
            "validation_predictions.csv": pins["forecast_csv"],
        },
        "Wrong forecast loader identity.",
    )
    require(tuple(accounts) == ACCOUNT_KEYS, "Expected eight ordered accounts.")
    output = []
    for symbol, model in ACCOUNT_KEYS:
        signals = accounts[symbol, model]
        require(len(signals) == 2195, "Wrong forecast count.")
        records = []
        for i, signal in enumerate(signals):
            opened = minute.START - STEP + i * STEP
            require(
                type(signal) is forecast.Signal
                and signal.symbol == symbol
                and signal.model == model
                and utc(signal.open_time) == opened
                and utc(signal.signal_time) == opened + STEP + timedelta(minutes=1),
                "Wrong forecast identity/grid/availability.",
            )
            number(signal.forecast)
            if model == "zero":
                require(signal.forecast == 0, "Wrong zero baseline.")
            if model == "training_mean":
                mean = manifest["markets"][symbol]["training_mean"]
                require(
                    not isinstance(mean, bool)
                    and signal.forecast == Decimal(format(mean, ".17g")),
                    "Wrong training mean.",
                )
            records.append(
                VerifiedForecast(
                    symbol,
                    model,
                    f"binance:spot:{symbol}:14400:{opened.isoformat()}:{model}",
                    opened,
                    signal.signal_time,
                    next_minute_at(signal.signal_time),
                    signal.forecast,
                    pins["forecast_csv"],
                )
            )
        output.append(tuple(records))
    return tuple(output)


def _stream_projection(path, monthly, *, expected_sha256, expected_bytes):
    """One bounded full-native-grid pass; retain only hours and planned minutes."""
    wanted = {minute.START + timedelta(hours=i) for i in range(8784)} | {
        minute.START + i * STEP + timedelta(minutes=2) for i in range(2195)
    }
    hashed, size, refs = hashlib.sha256(), 0, []
    with _open_checked(path) as stream:
        header = stream.readline(minute.MAX_LINE_BYTES + 1)
        require(header == minute.HEADER, "Wrong native header.")
        hashed.update(header)
        size += len(header)
        for request in minute.minute_requests():
            source = monthly[request.symbol, request.month]["sha256"]
            for i in range(request.row_count):
                line = stream.readline(minute.MAX_LINE_BYTES + 1)
                require(
                    0 < len(line) <= minute.MAX_LINE_BYTES and line.endswith(b"\n"),
                    "Missing/oversized/unterminated native row.",
                )
                hashed.update(line)
                size += len(line)
                require(size <= expected_bytes, "Excess processed bytes.")
                rows = list(csv.reader([line.decode("ascii")], strict=True))
                require(
                    len(rows) == 1 and len(rows[0]) == 4, "Wrong native row schema."
                )
                symbol, stamp, text, zip_hash = rows[0]
                ms = request.start_ms + i * 60000
                require(
                    symbol == request.symbol
                    and stamp == str(ms)
                    and zip_hash == source,
                    "Wrong native market/grid/monthly source.",
                )
                require(
                    len(text) <= 80 and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", text),
                    "Malformed native price.",
                )
                value = Decimal(text)
                require(value.is_finite() and value > 0, "Invalid native price.")
                at = minute.EPOCH + timedelta(milliseconds=ms)
                if at in wanted:
                    refs.append(
                        MinuteReference(
                            symbol,
                            reference_identity(symbol, at, 60),
                            at,
                            value,
                            expected_sha256,
                            source,
                        )
                    )
        require(not stream.read(1), "Excess native rows/bytes.")
    require(
        hashed.hexdigest() == expected_sha256 and size == expected_bytes,
        "Full native hash/size mismatch.",
    )
    require(len(refs) == 21958, "Wrong projection count.")
    return tuple(refs[:10979]), tuple(refs[10979:])


def _parity_counts(group, expected):
    required = {
        "expected",
        "matched_identities",
        "equal_prices",
        "mismatched_prices",
        "positive_differences",
        "negative_differences",
        "absolute_difference_sum",
        "absolute_difference_min",
        "absolute_difference_max",
        "absolute_difference_mean_exact_ratio",
    }
    require(set(group) == required, "Wrong parity count schema.")
    for key in (
        "expected",
        "matched_identities",
        "equal_prices",
        "mismatched_prices",
        "positive_differences",
        "negative_differences",
    ):
        value = (
            expected if key in ("expected", "matched_identities", "equal_prices") else 0
        )
        require(
            type(group[key]) is int and group[key] == value,
            "Incomplete/mismatched parity counts.",
        )
    for key in (
        "absolute_difference_sum",
        "absolute_difference_min",
        "absolute_difference_max",
    ):
        require(
            type(group[key]) is str
            and Decimal(group[key]).is_finite()
            and Decimal(group[key]) == 0,
            "Nonzero parity differences.",
        )
    require(
        policy.json_bytes(group["absolute_difference_mean_exact_ratio"])
        == policy.json_bytes(
            {"numerator": group["absolute_difference_sum"], "denominator": expected}
        ),
        "Wrong parity mean.",
    )


def _parity_evidence(
    bodies, pins, monthly, expected_audit_code, hourly_monthly, minute_manifest
):
    require(set(bodies) == set(PARITY_FILES), "Incomplete publication.")
    for name, key in (
        ("manifest.json", "parity_manifest"),
        ("parity_report.json", "parity_report"),
    ):
        require(
            hashlib.sha256(bodies[name]).hexdigest() == pins[key],
            "Original parity byte pin mismatch.",
        )
    manifest = _json(bodies["manifest.json"])
    require(
        set(manifest)
        == {"schema", "kind", "status", "files", "direct_timing_comparison_permitted"},
        "Wrong parity manifest schema.",
    )
    require(
        manifest["schema"] == "genuine-native-parity-publication-v1"
        and manifest["kind"] == "source_price_parity_only"
        and manifest["status"] == "exact_price_parity"
        and manifest["direct_timing_comparison_permitted"] is True,
        "Parity not authenticated exact success.",
    )
    require(
        set(manifest["files"]) == set(PARITY_FILES) - {"manifest.json"},
        "Wrong published file inventory.",
    )
    for name, identity in manifest["files"].items():
        require(
            policy.json_bytes(identity)
            == policy.json_bytes(
                {
                    "sha256": hashlib.sha256(bodies[name]).hexdigest(),
                    "bytes": len(bodies[name]),
                }
            ),
            "Published digest/size mismatch.",
        )
    require(
        bodies["discrepancies.csv"]
        == (",".join(parity.COLUMNS) + "\n").encode("ascii"),
        "Nonempty or wrong discrepancy CSV.",
    )
    report = _json(bodies["parity_report.json"])
    require(
        set(report)
        == {
            "schema",
            "status",
            "direct_timing_comparison_permitted",
            "native_interval_seconds",
            "start",
            "end_exclusive",
            "last_hour",
            "comparison",
            "overall",
            "per_symbol",
            "per_month",
            "per_symbol_month",
            "discrepancies",
            "structural_errors",
            "limitations",
            "authentication",
        },
        "Wrong actual auditor report schema.",
    )
    require(
        report["schema"] == "native-opening-price-parity-v1"
        and report["authentication"]
        == "genuine_pinned_releases_full_native_archive_revalidation"
        and report["status"] == "exact_price_parity"
        and report["direct_timing_comparison_permitted"] is True
        and report["discrepancies"] == []
        and report["structural_errors"] == []
        and report["native_interval_seconds"] == {"hourly": 3600, "minute": 60}
        and report["start"] == minute.START.isoformat()
        and report["end_exclusive"] == minute.END.isoformat()
        and report["last_hour"] == (minute.END - timedelta(hours=1)).isoformat()
        and report["comparison"]
        == "exact Decimal equality; no tolerance or substitution"
        and report["limitations"] == list(parity.LIMITATIONS),
        "Incomplete/ambiguous parity evidence.",
    )
    _parity_counts(report["overall"], 17568)
    expected = {
        "per_symbol": {s: 8784 for s in minute.SYMBOLS},
        "per_month": {
            f"2024-{m:02d}": calendar.monthrange(2024, m)[1] * 48 for m in range(1, 13)
        },
        "per_symbol_month": {
            f"{s}:2024-{m:02d}": calendar.monthrange(2024, m)[1] * 24
            for s in minute.SYMBOLS
            for m in range(1, 13)
        },
    }
    for name, groups in expected.items():
        require(set(report[name]) == set(groups), "Missing/excess parity buckets.")
        for key, count in groups.items():
            _parity_counts(report[name][key], count)
    provenance, integrity = (
        _json(bodies["provenance.json"]),
        _json(bodies["integrity.json"]),
    )
    require(
        set(provenance)
        == {
            "schema",
            "kind",
            "expected_external_pins",
            "implementation_sha256",
            "source_paths",
            "source_manifests",
            "native_rows_per_symbol",
            "projected_rows_per_symbol",
            "integrity",
            "limitations",
        }
        and provenance["limitations"] == list(parity.LIMITATIONS)
        and set(provenance["source_manifests"]) == {"hourly", "minute"},
        "Incomplete parity provenance schema.",
    )
    for value in expected_audit_code.values():
        digest(value)
    external = {
        "hourly": {
            "manifest.json": pins["hourly_manifest"],
            "hourly_opens.csv": pins["hourly_csv"],
            "acquisition.json": pins["hourly_acquisition"],
        },
        "minute": {
            "manifest.json": pins["minute_manifest"],
            "minute_opens.csv": pins["minute_csv"],
        },
        "documents": {
            parity.HOURLY_PROTOCOL: pins["hourly_protocol"],
            parity.MINUTE_PROTOCOL: pins["minute_protocol"],
            parity.PIN_DOCUMENT: pins["minute_pin_document"],
        },
    }
    require(
        provenance["schema"] == "genuine-native-parity-provenance-v1"
        and provenance["kind"] == "source_price_parity_only"
        and provenance["expected_external_pins"] == external
        and provenance["implementation_sha256"] == expected_audit_code
        and set(expected_audit_code) == set(parity.IMPLEMENTATION_FILES)
        and all(expected_audit_code[k] == v for k, v in external["documents"].items())
        and provenance["source_paths"]
        == {"hourly": parity.HOURLY_PATH, "minute": MINUTE_PATH}
        and provenance["native_rows_per_symbol"] == {"hourly": 8784, "minute": 527040}
        and type(provenance["projected_rows_per_symbol"]) is int
        and provenance["projected_rows_per_symbol"] == 8784,
        "Wrong parity release/code/protocol provenance.",
    )
    require(
        set(integrity) == {"before", "after"}
        and integrity["before"] == integrity["after"]
        and len(integrity["before"]) == 2,
        "Incomplete audit preservation.",
    )
    proof = provenance["integrity"]
    require(
        set(proof)
        == {
            "method",
            "source_file_count",
            "all_source_bytes_and_stats_unchanged",
            "sources",
            "loaders",
            "minute_projection",
        }
        and set(proof["sources"]) == {"hourly", "minute"}
        and proof["method"]
        == (
            "SHA-256, size, device/inode/mtime/ctime before and after "
            "for every source file"
        )
        and proof["loaders"]
        == (
            "Unchanged loaders replay every ZIP/checksum and "
            "reproduce complete processed CSVs"
        )
        and proof["minute_projection"]
        == (
            "Additional single streaming pass: ASCII/CSV, "
            "every timestamp/price/source, EOF/hash/size; retain HH:00 only"
        ),
        "Incomplete original audit methods.",
    )
    require(
        proof["all_source_bytes_and_stats_unchanged"] is True
        and type(proof["source_file_count"]) is int
        and proof["source_file_count"] == 101,
        "Incomplete original source integrity.",
    )
    for index, (release, interval) in enumerate((("hourly", "1h"), ("minute", "1m"))):
        snapshot = integrity["before"][index]
        require(
            set(snapshot) == _release_names(interval), "Wrong audited source inventory."
        )
        for identity in snapshot.values():
            require(
                set(identity) == {"sha256", "bytes", "stat"},
                "Wrong integrity identity.",
            )
            digest(identity["sha256"])
            require(
                type(identity["bytes"]) is int
                and identity["bytes"] > 0
                and len(identity["stat"]) == 5
                and all(type(v) is int and v >= 0 for v in identity["stat"])
                and identity["stat"][2] == identity["bytes"],
                "Invalid original file stats.",
            )
        require(
            proof["sources"][release]
            == {
                n: {k: v for k, v in ident.items() if k != "stat"}
                for n, ident in snapshot.items()
            },
            "Broken audit integrity links.",
        )
        for name, sha in external[release].items():
            require(
                snapshot[name]["sha256"] == sha, "Audited original source mismatch."
            )
        original = provenance["source_manifests"][release]
        if release == "minute":
            require(
                policy.json_bytes(original) == policy.json_bytes(minute_manifest)
                and snapshot["minute_opens.csv"]["bytes"]
                == minute_manifest["output"]["bytes"],
                "Different audited minute manifest.",
            )
        else:
            require(
                original["artifact_version"] == "binance-1h-2024-v1"
                and original["coverage"] == parity.hourly.coverage()
                and original["archive_count"] == 24
                and original["output_sha256"]
                == {
                    "hourly_opens.csv": pins["hourly_csv"],
                    "acquisition.json": pins["hourly_acquisition"],
                },
                "Wrong audited hourly manifest.",
            )
        require(len(original["sources"]) == 24, "Incomplete audit source associations.")
        seen = set()
        for source in original["sources"]:
            if release == "hourly":
                require(
                    source["complete"] is True and source["checksum_valid"] is True,
                    "Incomplete audited hourly archive.",
                )
            key = source["symbol"], source["month"]
            require(
                key in monthly and key not in seen, "Wrong/duplicate audited month."
            )
            seen.add(key)
            s, m = key
            stem = f"{s}-{interval}-{m}.zip"
            url = f"https://data.binance.vision/data/spot/monthly/klines/{s}/{interval}/{stem}"
            require(
                source["sha256"]
                == (
                    monthly[key]["sha256"]
                    if release == "minute"
                    else hourly_monthly[key]
                )
                and source["interval"] == interval
                and source["url"] == url
                and source["checksum_url"] == url + ".CHECKSUM"
                and source["row_count"]
                == calendar.monthrange(2024, int(m[-2:]))[1]
                * (1440 if release == "minute" else 24),
                "Wrong audited monthly association.",
            )
            for suffix, field_name in (
                ("", "sha256"),
                (".CHECKSUM", "checksum_sha256"),
            ):
                require(
                    snapshot[f"raw/{stem}{suffix}"]["sha256"] == source[field_name],
                    "Broken audited archive link.",
                )
                if release == "minute":
                    require(
                        snapshot[f"raw/{stem}{suffix}"]["bytes"]
                        == source["checksum_bytes" if suffix else "zip_bytes"],
                        "Broken audited archive size link.",
                    )
    return manifest, report, provenance


def _authenticate_fixture_inputs(
    *,
    fixture_root,
    pins,
    monthly_sources,
    processed_bytes,
    code_paths,
    expected_code_sha256,
    expected_audit_code_sha256,
    hourly_monthly,
    forecast_loader,
    minute_loader,
    lineage_validator,
) -> AuthenticatedMinuteInputs:
    """PRIVATE test seam. Invented pins/files only, under an isolated temp root.

    Test injection is intentionally absent from the public interface. The future
    wrapper must bind original loaders/default pins and unmodified lineage policy;
    never use the synthetic integration module's hash translation.
    """
    root = Path(fixture_root)
    # Lexical rejection precedes even stat; do not probe real retained artifacts.
    temp = Path(tempfile.gettempdir()).resolve()
    require(
        root.is_absolute()
        and ".." not in root.parts
        and root.is_relative_to(temp)
        and not root.is_relative_to(ROOT)
        and not {"artifacts", "crypto-trading-platform"}.intersection(root.parts),
        "Private harness requires isolated synthetic temporary root.",
    )
    require(set(pins) == set(EXTERNAL_PINS), "Incomplete external fixture pins.")
    for value in pins.values():
        digest(value)
        require(
            value not in EXTERNAL_PINS.values(),
            "Genuine pins forbidden in fixture harness.",
        )
    require(
        set(code_paths) == set(expected_code_sha256) and bool(code_paths),
        "Incomplete code pins.",
    )
    for path in code_paths.values():
        require(
            Path(path).is_relative_to(root) and ".." not in Path(path).parts,
            "Unexpected code root.",
        )
    _safe(root)
    directories = tuple(root / name for name in ("forecast", "minute", "parity"))
    code_before = {name: _identity(path) for name, path in code_paths.items()}
    require(
        {n: v["sha256"] for n, v in code_before.items()} == expected_code_sha256,
        "Reviewed code identity mismatch.",
    )
    before = _inventory(*directories)
    _check_pins(before, pins, processed_bytes)
    forecast_manifest = _json(
        _read(directories[0] / "manifest.json", pins["forecast_manifest"])
    )
    minute_manifest = _json(
        _read(directories[1] / "manifest.json", pins["minute_manifest"])
    )
    _minute_metadata(
        minute_manifest,
        before["minute"],
        monthly_sources,
        pins,
        processed_bytes,
        expected_code_sha256["minute_loader"],
    )
    lineage_validator(forecast_manifest)  # No translation/copy of genuine lineage.
    signals = _forecasts(forecast_loader(directories[0]), forecast_manifest, pins)
    verified = minute_loader(
        directories[1], expected_manifest_sha256=pins["minute_manifest"]
    )
    require(
        policy.json_bytes(verified) == policy.json_bytes(minute_manifest),
        "Minute loader metadata differs.",
    )
    references = _stream_projection(
        directories[1] / "minute_opens.csv",
        monthly_sources,
        expected_sha256=pins["minute_csv"],
        expected_bytes=processed_bytes,
    )
    bodies = {
        name: _read(directories[2] / name, before["parity"][name]["sha256"])
        for name in PARITY_FILES
    }
    publication, report, provenance = _parity_evidence(
        bodies,
        pins,
        monthly_sources,
        expected_audit_code_sha256,
        hourly_monthly,
        minute_manifest,
    )
    require(
        before == _inventory(*directories),
        "Original sources changed after verification.",
    )
    require(
        code_before == {n: _identity(p) for n, p in code_paths.items()},
        "Code changed after verification.",
    )
    projections = tuple(projection_sha256(refs) for refs in references)
    evidence = policy.json_bytes(
        {
            "status": STATUS,
            "genuine_execution_authorised": False,
            "source_kind": "fabricated_temporary_fixture_bytes",
            "pins": pins,
            "monthly_sources": [
                [*key, value] for key, value in monthly_sources.items()
            ],
            "original_files": {
                group: {
                    name: {k: v for k, v in ident.items() if k != "stat"}
                    for name, ident in snapshot.items()
                }
                for group, snapshot in before.items()
            },
            "forecast_manifest": forecast_manifest,
            "recipe_identity_kind": "stage2b_manifest_sha256",
            "recipe_sha256": pins["forecast_manifest"],
            "minute_metadata": minute_manifest,
            "parity_publication": publication,
            "parity_report": report,
            "parity_provenance": provenance,
            "code_sha256": expected_code_sha256,
            "projection_sha256": projections,
            "counts": {
                "forecast_accounts": 8,
                "forecasts_per_account": 2195,
                "forecasts": 17560,
                "native_rows": 1054080,
                "hourly_marks_per_market": 8784,
                "hypothetical_minutes_per_market": 2195,
                "references_per_market": 10979,
                "references": 21958,
            },
            "limitations": LIMITATIONS,
        }
    )
    return AuthenticatedMinuteInputs(signals, references, evidence, projections)

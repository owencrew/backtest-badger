"""Explicit, offline authentication and price parity for two frozen 2024 releases.

No CLI, discovery, acquisition, forecast reader or trading calculation. The public
entry point accepts only the approved paths and independently declared pins.
Private comparison helpers also support fabricated evidence in isolated tests.
"""

import calendar
import csv
import hashlib
import io
import json
import os
import re
import stat
from datetime import timedelta
from decimal import Decimal, localcontext
from pathlib import Path

from backtest_badger import execution_data as hourly
from backtest_badger import minute_execution_data as minute
from backtest_badger.paper_historical_evaluation import (
    ACQUISITION_SHA256,
    HOURLY_MANIFEST_SHA256,
    HOURLY_SHA256,
    MONTHLY_ZIP_SHA256,
    PROTOCOL_SHA256,
)
from backtest_badger.paper_types import money_context, number, require, utc

ROOT = Path(__file__).absolute().parents[2]
HOURLY_PATH = "artifacts/execution/binance-1h-2024-v1"
MINUTE_PATH = "artifacts/execution/binance-1m-2024-v1"
OUTPUT_PATH = "artifacts/audits/stage-04b2d1-native-parity-v1"
PIN_DOCUMENT = "docs/stage-04b2c-minute-source-pins.md"
HOURLY_PROTOCOL = "docs/stage-04b2-historical-validation-protocol.md"
MINUTE_PROTOCOL = "docs/stage-04b2c-minute-execution-protocol.md"
MINUTE_MANIFEST_SHA256 = (
    "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127"
)
MINUTE_CSV_SHA256 = "37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233"
MINUTE_CSV_BYTES = 107_002_277
EXTERNAL_PINS = {
    "hourly": {
        "manifest.json": HOURLY_MANIFEST_SHA256,
        "hourly_opens.csv": HOURLY_SHA256,
        "acquisition.json": ACQUISITION_SHA256,
    },
    "minute": {
        "manifest.json": MINUTE_MANIFEST_SHA256,
        "minute_opens.csv": MINUTE_CSV_SHA256,
    },
    "documents": {
        HOURLY_PROTOCOL: PROTOCOL_SHA256,
        MINUTE_PROTOCOL: (
            "c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b"
        ),
        PIN_DOCUMENT: (
            "967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c"
        ),
    },
}
# Fixed code/document allowlist, never artifact discovery. Full-checkout preservation
# is additionally recorded by the operator before/after the authorised invocation.
IMPLEMENTATION_FILES = (
    *(
        f"src/backtest_badger/{name}.py"
        for name in (
            "genuine_minute_price_parity",
            "execution_data",
            "minute_execution_data",
            "archives",
            "candles",
            "frozen",
            "ingestion",
            "model_data",
            "paper_historical_evaluation",
            "paper_historical",
            "paper_types",
            "minute_price_parity",
            "paper_minute_historical",
            "paper_accounting",
            "paper_execution",
            "paper_strategy",
        )
    ),
    HOURLY_PROTOCOL,
    MINUTE_PROTOCOL,
    PIN_DOCUMENT,
    "docs/stage-04b2c-minute-data-engineering.md",
    "pyproject.toml",
    "uv.lock",
)
COLUMNS = (
    "symbol",
    "utc_hour",
    "hourly_open",
    "minute_open",
    "minute_minus_hourly",
    "absolute_difference",
    "hourly_zip_sha256",
    "minute_zip_sha256",
    "hourly_manifest_sha256",
    "minute_manifest_sha256",
)
LIMITATIONS = (
    "Exact archived opening-price parity only; no strategy or economic calculation.",
    (
        "Checksums are unsigned; pins establish retained-byte identity, "
        "not exchange attestation."
    ),
    "Retrospective receipt timestamps do not establish historical source availability.",
    "No fresh provider access, quotes, depth, latency, fills or fillability evidence.",
    "2024 was previously inspected; this is not independent out-of-sample evidence.",
    (
        "Parity permission does not authorise forecast access, replay "
        "or economic publication."
    ),
    (
        "Before/after hashes and stats detect observed changes, "
        "not coordinated hostile races."
    ),
)


def _json(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def _sha(body):
    return hashlib.sha256(body).hexdigest()


def _safe_path(path, *, missing=False):
    """Reject symlinks in every component, including ancestors and broken links."""
    path = Path(path).absolute()
    require(".." not in path.parts, "Parent traversal refused.")
    for component in (*reversed(path.parents), path):
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            require(missing, "Missing evidence path.")
            continue
        require(not stat.S_ISLNK(mode), "Symlink evidence path refused.")
    return path


def _stat(path):
    info = _safe_path(path).lstat()
    require(stat.S_ISREG(info.st_mode), "Expected regular evidence file.")
    return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]


def _open(path):
    _stat(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        require(stat.S_ISREG(os.fstat(fd).st_mode), "Expected regular open file.")
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


def _file_identity(path):
    before = _stat(path)
    digest, size = hashlib.sha256(), 0
    with _open(path) as stream:
        while body := stream.read(1024 * 1024):
            digest.update(body)
            size += len(body)
    require(
        before == _stat(path) and size == before[2], "Evidence changed during read."
    )
    return {"sha256": digest.hexdigest(), "bytes": size, "stat": before}


def _read(path):
    with _open(path) as stream:
        return stream.read()


def _inventory(directory, interval):
    _safe_path(directory)
    names = {"manifest.json", "raw"}
    names |= (
        {"hourly_opens.csv", "acquisition.json"}
        if interval == "1h"
        else {"minute_opens.csv"}
    )
    require(
        set(os.listdir(directory)) == names, "Unexpected/incomplete release inventory."
    )
    raw = _safe_path(directory / "raw")
    expected = {
        f"{s}-{interval}-2024-{m:02d}.zip{suffix}"
        for s in minute.SYMBOLS
        for m in range(1, 13)
        for suffix in ("", ".CHECKSUM")
    }
    require(set(os.listdir(raw)) == expected, "Unexpected/incomplete raw inventory.")
    return {
        name: _file_identity(directory / name)
        for name in sorted((names - {"raw"}) | {f"raw/{n}" for n in expected})
    }


def _implementation(expected):
    require(
        set(expected) == set(IMPLEMENTATION_FILES), "Incomplete implementation pins."
    )
    actual = {p: _file_identity(ROOT / p)["sha256"] for p in IMPLEMENTATION_FILES}
    require(actual == expected, "Implementation changed from reviewed pre-run pins.")
    require(
        all(actual[p] == digest for p, digest in EXTERNAL_PINS["documents"].items()),
        "Frozen protocol/source-pin identity changed.",
    )
    return actual


def _minute_pins(body):
    """Parse only the frozen document's two exact 24-row tables, never local ZIPs."""
    hashes, urls = {}, {}
    for line in body.decode("utf-8").splitlines():
        parts = [x.strip().strip("`") for x in line.split("|")[1:-1]]
        if len(parts) == 8 and parts[0] in minute.SYMBOLS:
            key = tuple(parts[:2])
            require(key not in hashes, "Duplicate minute pin row.")
            hashes[key] = dict(
                zip(
                    (
                        "sha256",
                        "checksum_sha256",
                        "zip_bytes",
                        "checksum_bytes",
                        "csv_bytes",
                        "row_count",
                    ),
                    (*parts[2:4], *map(int, parts[4:])),
                    strict=True,
                )
            )
        if len(parts) == 5 and parts[0] in minute.SYMBOLS:
            key = tuple(parts[:2])
            require(key not in urls, "Duplicate minute URL row.")
            links = [
                re.fullmatch(r"\[(?:ZIP|CHECKSUM)\]\(([^)]+)\)", p) for p in parts[2:4]
            ]
            require(all(links), "Invalid source URL pin.")
            urls[key] = {
                "url": links[0][1],
                "checksum_url": links[1][1],
                "observed_at": parts[4],
            }
    expected = {(r.symbol, r.month) for r in minute.minute_requests()}
    require(hashes.keys() == urls.keys() == expected, "Incomplete minute pin tables.")
    return {key: {**hashes[key], **urls[key]} for key in sorted(expected)}


def _check_release_pins(snapshot, pins):
    for name, digest in pins.items():
        require(snapshot[name]["sha256"] == digest, f"External pin mismatch: {name}.")


def _source_tables(hour_manifest, minute_manifest, snapshots, minute_pins):
    require(
        hour_manifest["artifact_version"] == "binance-1h-2024-v1",
        "Wrong hourly source revision.",
    )
    require(hour_manifest["coverage"] == hourly.coverage(), "Wrong hourly coverage.")
    require(
        minute_manifest["artifact_version"] == minute.VERSION
        and minute_manifest["coverage"] == minute.coverage(),
        "Wrong minute revision/coverage.",
    )
    tables = []
    for interval, manifest, snapshot in zip(
        ("1h", "1m"), (hour_manifest, minute_manifest), snapshots, strict=True
    ):
        require(
            manifest["archive_count"] == len(manifest["sources"]) == 24,
            "Incomplete source records.",
        )
        table = {}
        for source in manifest["sources"]:
            key = source["symbol"], source["month"]
            require(
                key in MONTHLY_ZIP_SHA256 and key not in table,
                "Wrong/duplicate market-month source.",
            )
            symbol, month = key
            stem = f"{symbol}-{interval}-{month}"
            url = (
                "https://data.binance.vision/data/spot/monthly/klines/"
                f"{symbol}/{interval}/{stem}.zip"
            )
            require(
                source["interval"] == interval
                and source["url"] == url
                and source["checksum_url"] == url + ".CHECKSUM",
                "Wrong source interval/URL association.",
            )
            require(
                source["row_count"]
                == calendar.monthrange(2024, int(month[-2:]))[1]
                * (24 if interval == "1h" else 1440),
                "Wrong monthly count.",
            )
            for suffix, field in (("", "sha256"), (".CHECKSUM", "checksum_sha256")):
                identity = snapshot[f"raw/{stem}.zip{suffix}"]
                require(identity["sha256"] == source[field], "Raw source pin mismatch.")
                if interval == "1m":
                    require(
                        identity["bytes"]
                        == source["checksum_bytes" if suffix else "zip_bytes"],
                        "Raw source size mismatch.",
                    )
            if interval == "1h":
                require(
                    source["sha256"] == MONTHLY_ZIP_SHA256[key]
                    and source["complete"] is True
                    and source["checksum_valid"] is True,
                    "Wrong reviewed hourly ZIP identity/status.",
                )
            else:
                require(
                    all(source[k] == v for k, v in minute_pins[key].items()),
                    "Frozen minute source table mismatch.",
                )
            table[key] = source
        require(table.keys() == MONTHLY_ZIP_SHA256.keys(), "Incomplete source table.")
        tables.append(table)
    return tables


def _stream_minute_projection(path, sources, *, expected_sha256, expected_bytes):
    """One bounded pass over the full processed grid; retain HH:00 opens only."""
    digest, size, projection = hashlib.sha256(), 0, []
    with _open(path) as stream:
        header = stream.readline(minute.MAX_LINE_BYTES + 1)
        require(header == minute.HEADER, "Wrong minute CSV header.")
        digest.update(header)
        size += len(header)
        for request in minute.minute_requests():
            source_hash = sources[request.symbol, request.month]["sha256"]
            for i in range(request.row_count):
                line = stream.readline(minute.MAX_LINE_BYTES + 1)
                require(
                    0 < len(line) <= minute.MAX_LINE_BYTES and line.endswith(b"\n"),
                    "Missing/oversized/unterminated minute row.",
                )
                digest.update(line)
                size += len(line)
                rows = list(csv.reader([line.decode("ascii")], strict=True))
                require(len(rows) == 1 and len(rows[0]) == 4, "Invalid minute CSV row.")
                symbol, timestamp, price, source = rows[0]
                stamp = request.start_ms + i * 60_000
                require(
                    symbol == request.symbol
                    and timestamp == str(stamp)
                    and source == source_hash,
                    "Invalid minute grid/source association.",
                )
                require(
                    len(price) <= 80 and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", price),
                    "Invalid minute price string.",
                )
                value = Decimal(price)
                require(value.is_finite() and value > 0, "Invalid minute price.")
                if i % 60 == 0:
                    projection.append(
                        (symbol, minute.EPOCH + timedelta(milliseconds=stamp), value)
                    )
        require(not stream.read(1), "Extra minute CSV rows/bytes.")
    require(
        digest.hexdigest() == expected_sha256 and size == expected_bytes,
        "Minute stream hash/size mismatch.",
    )
    return projection


def _hour_grid():
    return (
        (s, minute.START + timedelta(hours=i))
        for s in minute.SYMBOLS
        for i in range(8784)
    )


def _counts():
    return {
        "expected": 0,
        "matched_identities": 0,
        "equal_prices": 0,
        "mismatched_prices": 0,
        "positive_differences": 0,
        "negative_differences": 0,
        "absolute_difference_sum": Decimal(0),
        "absolute_difference_min": None,
        "absolute_difference_max": Decimal(0),
    }


def _compare(hour_rows, minute_rows, tables, manifest_hashes):
    """Pure full-year comparison; supplied inputs alone do not authenticate sources."""
    overall, symbols, months, symbol_months, discrepancies = _counts(), {}, {}, {}, []
    with localcontext(money_context()):
        for key, left, right in zip(_hour_grid(), hour_rows, minute_rows, strict=True):
            require(len(left) == len(right) == 3, "Invalid projection record.")
            require(
                left[:2] == right[:2] == key, "Invalid ordered hourly projection grid."
            )
            symbol, at = key
            utc(left[1])
            utc(right[1])
            h, m = number(left[2]), number(right[2])
            require(h > 0 and m > 0, "Invalid positive projection price.")
            difference = m - h
            absolute = abs(difference)
            month = at.strftime("%Y-%m")
            groups = (
                overall,
                symbols.setdefault(symbol, _counts()),
                months.setdefault(month, _counts()),
                symbol_months.setdefault(f"{symbol}:{month}", _counts()),
            )
            for group in groups:
                group["expected"] += 1
                group["matched_identities"] += 1
                group["equal_prices"] += int(h == m)
                group["mismatched_prices"] += int(h != m)
                group["positive_differences"] += int(difference > 0)
                group["negative_differences"] += int(difference < 0)
                group["absolute_difference_sum"] += absolute
                previous = group["absolute_difference_min"]
                group["absolute_difference_min"] = (
                    absolute if previous is None else min(previous, absolute)
                )
                group["absolute_difference_max"] = max(
                    group["absolute_difference_max"], absolute
                )
            if h != m:
                discrepancies.append(
                    dict(
                        zip(
                            COLUMNS,
                            (
                                symbol,
                                at.isoformat(),
                                str(h),
                                str(m),
                                str(difference),
                                str(absolute),
                                tables[0][symbol, month]["sha256"],
                                tables[1][symbol, month]["sha256"],
                                *manifest_hashes,
                            ),
                            strict=True,
                        )
                    )
                )
    for group in (
        overall,
        *symbols.values(),
        *months.values(),
        *symbol_months.values(),
    ):
        for name in (
            "absolute_difference_sum",
            "absolute_difference_min",
            "absolute_difference_max",
        ):
            group[name] = str(group[name])
        group["absolute_difference_mean_exact_ratio"] = {
            "numerator": group["absolute_difference_sum"],
            "denominator": group["expected"],
        }
    return {
        "schema": "native-opening-price-parity-v1",
        "status": "source_price_discrepancy" if discrepancies else "exact_price_parity",
        "direct_timing_comparison_permitted": not discrepancies,
        "native_interval_seconds": {"hourly": 3600, "minute": 60},
        "start": minute.START.isoformat(),
        "end_exclusive": minute.END.isoformat(),
        "last_hour": (minute.END - timedelta(hours=1)).isoformat(),
        "comparison": "exact Decimal equality; no tolerance or substitution",
        "overall": overall,
        "per_symbol": symbols,
        "per_month": months,
        "per_symbol_month": symbol_months,
        "discrepancies": discrepancies,
        "structural_errors": [],
        "limitations": LIMITATIONS,
    }


def _csv(report):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(report["discrepancies"])
    return output.getvalue().encode("ascii")


def _write(path, body):
    # Exclusive creation, fsync, then exclusive publication. Never resumes a partial.
    partial = path.with_name(path.name + ".partial")
    with partial.open("xb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def _verify_outputs(destination, payloads):
    require(
        set(os.listdir(destination)) == set(payloads),
        "Unexpected audit output inventory.",
    )
    identities = {}
    for name, expected in payloads.items():
        body = _read(destination / name)
        require(body == expected, "On-disk audit output differs from verified payload.")
        identities[name] = {"sha256": _sha(body), "bytes": len(body)}
    report = json.loads(_read(destination / "parity_report.json"))
    rows = list(
        csv.DictReader(io.StringIO(_read(destination / "discrepancies.csv").decode()))
    )
    require(rows == report["discrepancies"], "Discrepancy CSV/JSON mismatch.")
    require(
        len(rows) == report["overall"]["mismatched_prices"]
        and report["direct_timing_comparison_permitted"] == (not rows),
        "Invalid published parity counts/flag.",
    )
    return identities


def audit_genuine_minute_price_parity(
    *,
    hourly_directory,
    minute_directory,
    destination,
    expected_pins,
    expected_implementation_sha256,
):
    """Authenticate the exact approved releases, then publish one exclusive audit.

    All arguments are mandatory. No configurable period, alternate pin override,
    source discovery or genuine-data test mode. Exceptions propagate; a reserved
    attempt retains failure evidence without a valid final manifest.
    """
    require(expected_pins == EXTERNAL_PINS, "Unapproved external pin declarations.")
    directories = tuple(
        Path(p).absolute() for p in (hourly_directory, minute_directory)
    )
    destination = Path(destination).absolute()
    require(
        directories == (ROOT / HOURLY_PATH, ROOT / MINUTE_PATH)
        and destination == ROOT / OUTPUT_PATH,
        "Unapproved source/output directory.",
    )
    _safe_path(destination, missing=True)
    require(not os.path.lexists(destination), "Audit destination already exists.")
    implementation = _implementation(expected_implementation_sha256)
    pins = _minute_pins(_read(ROOT / PIN_DOCUMENT))
    # Preflight inspects ONLY the two explicitly approved source trees.
    before = (_inventory(directories[0], "1h"), _inventory(directories[1], "1m"))
    for snapshot, release in zip(before, ("hourly", "minute"), strict=True):
        _check_release_pins(snapshot, expected_pins[release])
    require(
        before[1]["minute_opens.csv"]["bytes"] == MINUTE_CSV_BYTES,
        "Minute processed size mismatch.",
    )
    manifests = tuple(json.loads(_read(d / "manifest.json")) for d in directories)
    tables = _source_tables(*manifests, before, pins)
    _safe_path(destination.parent, missing=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()  # No alternate output, overwrite, resume or deletion.
    phase = "source_authentication"
    try:
        metadata, prices = hourly.load_execution_data(directories[0])
        require(
            metadata
            == {
                "manifest_sha256": expected_pins["hourly"]["manifest.json"],
                "output_sha256": manifests[0]["output_sha256"],
                "coverage": manifests[0]["coverage"],
                "sources": manifests[0]["sources"],
            },
            "Verified hourly metadata mismatch.",
        )
        verified_minute = minute.load_minute_execution_data(
            directories[1],
            expected_manifest_sha256=expected_pins["minute"]["manifest.json"],
        )
        require(verified_minute == manifests[1], "Verified minute metadata mismatch.")
        phase = "complete_grid_projection"
        projection = _stream_minute_projection(
            directories[1] / "minute_opens.csv",
            tables[1],
            expected_sha256=expected_pins["minute"]["minute_opens.csv"],
            expected_bytes=MINUTE_CSV_BYTES,
        )
        phase = "exact_price_comparison"
        report = _compare(
            ((s, at, price) for (s, at), price in prices.items()),
            projection,
            tables,
            (
                expected_pins["hourly"]["manifest.json"],
                expected_pins["minute"]["manifest.json"],
            ),
        )
        report["authentication"] = (
            "genuine_pinned_releases_full_native_archive_revalidation"
        )
        phase = "source_preservation"
        after = (_inventory(directories[0], "1h"), _inventory(directories[1], "1m"))
        require(before == after, "Source changed during audit.")
        require(
            _implementation(expected_implementation_sha256) == implementation,
            "Implementation changed during audit.",
        )
        provenance = {
            "schema": "genuine-native-parity-provenance-v1",
            "kind": "source_price_parity_only",
            "expected_external_pins": expected_pins,
            "implementation_sha256": implementation,
            "source_paths": {"hourly": HOURLY_PATH, "minute": MINUTE_PATH},
            "source_manifests": {"hourly": manifests[0], "minute": manifests[1]},
            "native_rows_per_symbol": {"hourly": 8784, "minute": 527040},
            "projected_rows_per_symbol": 8784,
            "integrity": {
                "method": (
                    "SHA-256, size, device/inode/mtime/ctime before and after "
                    "for every source file"
                ),
                "source_file_count": sum(map(len, before)),
                "all_source_bytes_and_stats_unchanged": True,
                "sources": {
                    release: {
                        name: {k: v for k, v in value.items() if k != "stat"}
                        for name, value in snapshot.items()
                    }
                    for release, snapshot in zip(
                        ("hourly", "minute"), before, strict=True
                    )
                },
                "loaders": (
                    "Unchanged loaders replay every ZIP/checksum and "
                    "reproduce complete processed CSVs"
                ),
                "minute_projection": (
                    "Additional single streaming pass: ASCII/CSV, "
                    "every timestamp/price/source, EOF/hash/size; "
                    "retain HH:00 only"
                ),
            },
            "limitations": LIMITATIONS,
        }
        payloads = {
            "provenance.json": _json(provenance),
            "parity_report.json": _json(report),
            "discrepancies.csv": _csv(report),
            "integrity.json": _json({"before": before, "after": after}),
        }
        phase = "output_verification"
        for name, body in payloads.items():
            _write(destination / name, body)
        identities = _verify_outputs(destination, payloads)
        # Recheck sources/code after output verification, before the final manifest.
        require(
            before
            == (_inventory(directories[0], "1h"), _inventory(directories[1], "1m")),
            "Source changed before manifest publication.",
        )
        _implementation(expected_implementation_sha256)
        manifest = _json(
            {
                "schema": "genuine-native-parity-publication-v1",
                "kind": "source_price_parity_only",
                "status": report["status"],
                "files": identities,
                "direct_timing_comparison_permitted": report[
                    "direct_timing_comparison_permitted"
                ],
            }
        )
        phase = "manifest_publication"
        _write(destination / "manifest.json", manifest)
        require(
            _read(destination / "manifest.json") == manifest,
            "Manifest readback mismatch.",
        )
        return {
            "manifest_sha256": _sha(manifest),
            "manifest_bytes": len(manifest),
            "files": identities,
            "status": report["status"],
            "overall": report["overall"],
            "per_symbol": report["per_symbol"],
            "direct_timing_comparison_permitted": report[
                "direct_timing_comparison_permitted"
            ],
        }
    except BaseException as error:
        (destination / "manifest.json").unlink(missing_ok=True)
        try:
            _write(
                destination / "failure.json",
                _json(
                    {
                        "status": "invalid_source_or_incomplete_publication",
                        "phase": phase,
                        "exception_type": type(error).__name__,
                        "direct_timing_comparison_permitted": False,
                        "complete": False,
                        "resume": False,
                    }
                ),
            )
        except OSError:
            pass
        raise

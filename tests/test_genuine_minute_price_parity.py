"""Fabricated evidence only; real artifacts, loader calls, network and DB forbidden."""

import builtins
import copy
import io
import json
import os
import socket
from datetime import timedelta
from decimal import Decimal, localcontext
from pathlib import Path

import psycopg
import pytest

from backtest_badger import forecast_data, model_data
from backtest_badger import genuine_minute_price_parity as audit

REAL_ROOT = Path(__file__).absolute().parents[1]


@pytest.fixture(autouse=True)
def offline_boundary(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail(
            "Genuine loader/network/database access forbidden in synthetic tests"
        )

    for module, name in (
        (audit.hourly, "load_execution_data"),
        (audit.minute, "load_minute_execution_data"),
        (forecast_data, "load_forecasts"),
        (model_data, "load_model_data"),
        (psycopg, "connect"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
    ):
        monkeypatch.setattr(module, name, forbidden)

    def guard(original):
        def guarded(file, *args, **kwargs):
            if isinstance(file, (str, bytes, os.PathLike)):
                path = Path(os.fsdecode(file)).absolute()
                assert not path.is_relative_to(REAL_ROOT / "artifacts")
                assert "crypto-trading-platform" not in path.parts
            return original(file, *args, **kwargs)

        return guarded

    for module, name in (
        (builtins, "open"),
        (io, "open"),
        (os, "open"),
        (os, "listdir"),
        (os, "scandir"),
    ):
        monkeypatch.setattr(module, name, guard(getattr(module, name)))


def rows():
    return [(s, at, Decimal("100.00")) for s, at in audit._hour_grid()]


def tables():
    return [
        {
            (r.symbol, r.month): {
                "sha256": audit._sha(f"fabricated:{n}:{r.stem}".encode())
            }
            for r in audit.minute.minute_requests()
        }
        for n in (1, 2)
    ]


def compare(left=None, right=None):
    return audit._compare(
        rows() if left is None else left,
        rows() if right is None else right,
        tables(),
        ("a" * 64, "b" * 64),
    )


def test_full_fabricated_year_exact_equality_and_boundaries():
    right = [(s, at, Decimal("100.000000")) for s, at, _ in rows()]
    result = compare(right=right)
    assert result["direct_timing_comparison_permitted"]
    assert result["overall"]["expected"] == result["overall"]["equal_prices"] == 17568
    assert result["per_symbol"]["BTCUSDT"]["expected"] == 8784
    assert result["per_symbol"]["ETHUSDT"]["expected"] == 8784
    assert result["per_month"]["2024-02"]["expected"] == 1392
    assert result["last_hour"] == "2024-12-31T23:00:00+00:00"
    assert not result["structural_errors"]
    assert not result["discrepancies"]
    assert audit._csv(result).decode() == ",".join(audit.COLUMNS) + "\n"
    assert audit._json(result) == audit._json(compare(right=right))


def test_no_tolerance_exact_signed_differences_and_context_independence():
    right = rows()
    right[0] = (*right[0][:2], Decimal("100.000000000000000000000000000001"))
    right[-1] = (*right[-1][:2], Decimal("99.75"))
    with localcontext() as context:
        context.prec = 3
        result = compare(right=right)
    assert result["status"] == "source_price_discrepancy"
    assert result["direct_timing_comparison_permitted"] is False
    assert result["overall"]["mismatched_prices"] == 2
    assert result["overall"]["positive_differences"] == 1
    assert result["overall"]["negative_differences"] == 1
    assert (
        result["overall"]["absolute_difference_sum"]
        == "0.250000000000000000000000000001"
    )
    first, last = result["discrepancies"]
    assert Decimal(first["minute_minus_hourly"]) == Decimal("1e-30")
    assert last["minute_minus_hourly"] == "-0.25"
    assert first["hourly_zip_sha256"] != first["minute_zip_sha256"]
    assert first["hourly_manifest_sha256"] != first["minute_manifest_sha256"]


@pytest.mark.parametrize("side", ["hour", "minute"])
@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "reorder",
        "offhour",
        "market",
        "endpoint",
        "float",
        "nan",
        "zero",
    ],
)
def test_invalid_projection_fails_closed(side, mutation):
    left, right = rows(), rows()
    target = left if side == "hour" else right
    s, at, price = target[0]
    if mutation == "missing":
        target.pop()
    elif mutation == "duplicate":
        target.insert(0, target[0])
    elif mutation == "reorder":
        target[0], target[1] = target[1], target[0]
    elif mutation == "offhour":
        target[0] = s, at + timedelta(minutes=1), price
    elif mutation == "market":
        target[0] = "XRPUSDT", at, price
    elif mutation == "endpoint":
        target[-1] = s, audit.minute.END, price
    else:
        target[0] = (
            s,
            at,
            {"float": 100.0, "nan": Decimal("NaN"), "zero": Decimal(0)}[mutation],
        )
    with pytest.raises(ValueError):
        compare(left, right)


@pytest.fixture(scope="module")
def full_minute_csv(tmp_path_factory):
    path = tmp_path_factory.mktemp("fabricated-native-grid") / "minute.csv"
    sources = tables()[1]
    with path.open("wb") as stream:
        stream.write(audit.minute.HEADER)
        for request in audit.minute.minute_requests():
            digest = sources[request.symbol, request.month]["sha256"]
            for i in range(request.row_count):
                stream.write(
                    (
                        f"{request.symbol},{request.start_ms + 60000 * i},"
                        f"100.00,{digest}\n"
                    ).encode()
                )
    return path, sources, audit._file_identity(path)


def test_streams_all_fabricated_minutes_and_keeps_only_hours(full_minute_csv):
    path, sources, identity = full_minute_csv
    projection = audit._stream_minute_projection(
        path,
        sources,
        expected_sha256=identity["sha256"],
        expected_bytes=identity["bytes"],
    )
    assert projection == rows()
    assert len(projection) == 17568
    assert sum(at.month == 2 and at.day == 29 for _, at, _ in projection) == 48


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "order",
        "timestamp",
        "market",
        "source",
        "nan",
        "infinity",
        "exponent",
        "zero",
        "negative",
        "header",
        "ascii",
        "oversize",
    ],
)
def test_strict_stream_rejects_malformed_rows(tmp_path, mutation):
    path = tmp_path / "invented.csv"
    source = tables()[1]
    fields = ["BTCUSDT", "1704067200000", "100", source["BTCUSDT", "2024-01"]["sha256"]]
    values = {
        "timestamp": (1, "1704067200001"),
        "market": (0, "ETHUSDT"),
        "source": (3, "f" * 64),
        "nan": (2, "NaN"),
        "infinity": (2, "Infinity"),
        "exponent": (2, "1e2"),
        "zero": (2, "0"),
        "negative": (2, "-1"),
        "order": (1, "1704067260000"),
        "ascii": (2, "é"),
        "oversize": (2, "1" * 3000),
    }
    if mutation in values:
        index, value = values[mutation]
        fields[index] = value
    line = (",".join(fields) + "\n").encode()
    body = audit.minute.HEADER + line
    if mutation == "missing":
        body = audit.minute.HEADER
    elif mutation == "duplicate":
        body += line
    elif mutation == "header":
        body = b"wrong\n" + line
    path.write_bytes(body)
    with pytest.raises((ValueError, UnicodeError)):
        audit._stream_minute_projection(
            path, source, expected_sha256=audit._sha(body), expected_bytes=len(body)
        )


@pytest.mark.parametrize("mutation", ["hash", "size", "extra"])
def test_stream_final_hash_size_and_eof(full_minute_csv, tmp_path, mutation):
    path, sources, identity = full_minute_csv
    digest, size = identity["sha256"], identity["bytes"]
    if mutation == "hash":
        digest = "0" * 64
    elif mutation == "size":
        size += 1
    else:
        import shutil

        copy_path = tmp_path / "extra.csv"
        shutil.copyfile(path, copy_path)
        with copy_path.open("ab") as stream:
            stream.write(b"extra\n")
        path = copy_path
    with pytest.raises(ValueError):
        audit._stream_minute_projection(
            path, sources, expected_sha256=digest, expected_bytes=size
        )


@pytest.fixture
def fabricated_release(tmp_path, monkeypatch):
    """Plumbing uses fabricated trees and explicit stub loader boundaries.

    Pins are monkeypatched ONLY in tests. Production has no alternate pin/path or
    short-grid mode. Separate tests exercise the unmodified complete CSV projector.
    """
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    manifests, pins, source_hashes = (
        [],
        {"hourly": {}, "minute": {}, "documents": {}},
        {},
    )
    pin_lines, url_lines = [], []
    for interval, relative, label in (
        ("1h", audit.HOURLY_PATH, "hourly"),
        ("1m", audit.MINUTE_PATH, "minute"),
    ):
        directory = tmp_path / relative
        (directory / "raw").mkdir(parents=True)
        sources = []
        for request in audit.minute.minute_requests():
            symbol, month = request.symbol, request.month
            stem = f"{symbol}-{interval}-{month}"
            raw = f"fabricated bytes {stem}".encode()
            digest = audit._sha(raw)
            checksum = f"{digest}  {stem}.zip\n".encode()
            (directory / "raw" / f"{stem}.zip").write_bytes(raw)
            (directory / "raw" / f"{stem}.zip.CHECKSUM").write_bytes(checksum)
            url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{stem}.zip"
            source = {
                "symbol": symbol,
                "month": month,
                "interval": interval,
                "url": url,
                "checksum_url": url + ".CHECKSUM",
                "sha256": digest,
                "checksum_sha256": audit._sha(checksum),
                "observed_at": "2026-10-18T00:00:00+00:00",
                "row_count": request.row_count // (60 if interval == "1h" else 1),
            }
            if interval == "1h":
                source.update(complete=True, checksum_valid=True)
                source_hashes[symbol, month] = digest
            else:
                source.update(
                    zip_bytes=len(raw), checksum_bytes=len(checksum), csv_bytes=12345
                )
                pin_lines.append(
                    f"| {symbol} | {month} | `{digest}` | `{audit._sha(checksum)}` | "
                    f"{len(raw)} | {len(checksum)} | 12345 | {request.row_count} |"
                )
                url_lines.append(
                    f"| {symbol} | {month} | [ZIP]({url}) | "
                    f"[CHECKSUM]({url}.CHECKSUM) | {source['observed_at']} |"
                )
            sources.append(source)
        csv_name = "hourly_opens.csv" if interval == "1h" else "minute_opens.csv"
        (directory / csv_name).write_bytes(b"fabricated loader boundary\n")
        pins[label][csv_name] = audit._sha((directory / csv_name).read_bytes())
        manifest = {
            "artifact_version": f"binance-{interval}-2024-v1",
            "archive_count": 24,
            "coverage": audit.hourly.coverage()
            if interval == "1h"
            else audit.minute.coverage(),
            "sources": sources,
        }
        if interval == "1h":
            body = audit._json({"status": "complete", "sources": sources})
            (directory / "acquisition.json").write_bytes(body)
            pins[label]["acquisition.json"] = audit._sha(body)
            manifest["output_sha256"] = pins[label].copy()
        (directory / "manifest.json").write_bytes(audit._json(manifest))
        pins[label]["manifest.json"] = audit._sha(audit._json(manifest))
        manifests.append(manifest)
    for name, body in (
        (audit.PIN_DOCUMENT, "\n".join(pin_lines + url_lines) + "\n"),
        (audit.HOURLY_PROTOCOL, "fabricated hourly protocol\n"),
        (audit.MINUTE_PROTOCOL, "fabricated minute protocol\n"),
    ):
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(body)
        pins["documents"][name] = audit._sha(body.encode())
    (tmp_path / "implementation.py").write_text("# fabricated code boundary\n")
    implementation_files = ("implementation.py", *pins["documents"])
    implementation = {
        p: audit._sha((tmp_path / p).read_bytes()) for p in implementation_files
    }
    monkeypatch.setattr(audit, "IMPLEMENTATION_FILES", implementation_files)
    monkeypatch.setattr(audit, "EXTERNAL_PINS", pins)
    monkeypatch.setattr(audit, "MONTHLY_ZIP_SHA256", source_hashes)
    monkeypatch.setattr(audit, "MINUTE_CSV_BYTES", len(b"fabricated loader boundary\n"))
    calls = []
    prices = {(s, at): price for s, at, price in rows()}

    def hour_loader(directory):
        assert directory == tmp_path / audit.HOURLY_PATH
        calls.append("hourly")
        return {
            "manifest_sha256": pins["hourly"]["manifest.json"],
            "output_sha256": manifests[0]["output_sha256"],
            "sources": manifests[0]["sources"],
            "coverage": manifests[0]["coverage"],
        }, prices

    def minute_loader(directory, *, expected_manifest_sha256):
        assert directory == tmp_path / audit.MINUTE_PATH
        assert expected_manifest_sha256 == pins["minute"]["manifest.json"]
        calls.append("minute")
        return manifests[1]

    def projector(path, sources, *, expected_sha256, expected_bytes):
        assert calls == ["hourly", "minute"]
        assert path == tmp_path / audit.MINUTE_PATH / "minute_opens.csv"
        assert expected_sha256 == pins["minute"]["minute_opens.csv"]
        assert expected_bytes == audit.MINUTE_CSV_BYTES
        assert len(sources) == 24
        return rows()

    monkeypatch.setattr(audit.hourly, "load_execution_data", hour_loader)
    monkeypatch.setattr(audit.minute, "load_minute_execution_data", minute_loader)
    monkeypatch.setattr(audit, "_stream_minute_projection", projector)
    return (
        {
            "hourly_directory": tmp_path / audit.HOURLY_PATH,
            "minute_directory": tmp_path / audit.MINUTE_PATH,
            "destination": tmp_path / audit.OUTPUT_PATH,
            "expected_pins": copy.deepcopy(pins),
            "expected_implementation_sha256": implementation,
        },
        calls,
        manifests,
        prices,
    )


def test_wrapper_authenticates_before_projection_and_preserves_sources(
    fabricated_release,
):
    options, calls, _, _ = fabricated_release
    before = [
        audit._inventory(options[key], interval)
        for key, interval in (("hourly_directory", "1h"), ("minute_directory", "1m"))
    ]
    result = audit.audit_genuine_minute_price_parity(**options)
    assert calls == ["hourly", "minute"]
    assert result["direct_timing_comparison_permitted"]
    assert result["overall"]["equal_prices"] == 17568
    destination = options["destination"]
    assert result["manifest_sha256"] == audit._sha(
        (destination / "manifest.json").read_bytes()
    )
    for name, identity in result["files"].items():
        assert identity["bytes"] == (destination / name).stat().st_size
        assert identity["sha256"] == audit._sha((destination / name).read_bytes())
    assert before == [
        audit._inventory(options[key], interval)
        for key, interval in (("hourly_directory", "1h"), ("minute_directory", "1m"))
    ]
    provenance = json.loads((destination / "provenance.json").read_bytes())
    assert provenance["integrity"]["source_file_count"] == 101
    with pytest.raises(ValueError, match="already exists"):
        audit.audit_genuine_minute_price_parity(**options)


def test_negative_parity_is_complete_publication(fabricated_release):
    options, _, _, prices = fabricated_release
    prices[next(iter(prices))] = Decimal("99.999999999999999999999999999999")
    result = audit.audit_genuine_minute_price_parity(**options)
    assert result["status"] == "source_price_discrepancy"
    assert result["direct_timing_comparison_permitted"] is False
    assert result["overall"]["mismatched_prices"] == 1
    assert (options["destination"] / "manifest.json").is_file()


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_directory",
        "wrong_output",
        "wrong_pins",
        "manifest",
        "csv",
        "zip",
        "sidecar",
        "missing",
        "extra",
        "symlink_file",
        "symlink_directory",
        "symlink_ancestor",
        "symlink_output",
        "existing_output",
        "code",
        "protocol",
    ],
)
def test_preflight_refuses_without_loader_or_publication(fabricated_release, mutation):
    options, calls, _, _ = fabricated_release
    directory = options["minute_directory"]
    target = directory / "raw" / "BTCUSDT-1m-2024-01.zip"
    if mutation == "wrong_directory":
        options["minute_directory"] = directory.parent / "unapproved"
    elif mutation == "wrong_output":
        options["destination"] = directory.parent / "unapproved"
    elif mutation == "wrong_pins":
        options["expected_pins"]["minute"]["manifest.json"] = "0" * 64
    elif mutation in ("manifest", "csv", "zip", "sidecar"):
        target = {
            "manifest": directory / "manifest.json",
            "csv": directory / "minute_opens.csv",
            "zip": target,
            "sidecar": target.with_suffix(".zip.CHECKSUM"),
        }[mutation]
        target.write_bytes(target.read_bytes() + b"tamper")
    elif mutation == "missing":
        target.unlink()
    elif mutation == "extra":
        (directory / "failure.json").write_text("{}")
    elif mutation == "symlink_file":
        target.unlink()
        target.symlink_to("absent")
    elif mutation in ("symlink_directory", "symlink_ancestor"):
        target = (
            directory / "raw" if mutation == "symlink_directory" else directory.parent
        )
        renamed = target.with_name(target.name + "-retained")
        target.rename(renamed)
        target.symlink_to(renamed, target_is_directory=True)
    elif mutation in ("symlink_output", "existing_output"):
        options["destination"].parent.mkdir(parents=True)
        if mutation == "symlink_output":
            options["destination"].symlink_to("absent")
        else:
            options["destination"].mkdir()
    else:
        target = audit.ROOT / (
            "implementation.py" if mutation == "code" else audit.HOURLY_PROTOCOL
        )
        target.write_text("changed\n")
    with pytest.raises((ValueError, FileNotFoundError)):
        audit.audit_genuine_minute_price_parity(**options)
    assert not calls
    assert not (options["destination"] / "manifest.json").exists()


@pytest.mark.parametrize(
    "mutation", ["interval", "month_hash", "url", "count", "incomplete"]
)
def test_metadata_must_match_independent_declarations(fabricated_release, mutation):
    options, _, manifests, _ = fabricated_release
    snapshot = (
        audit._inventory(options["hourly_directory"], "1h"),
        audit._inventory(options["minute_directory"], "1m"),
    )
    pins = audit._minute_pins((audit.ROOT / audit.PIN_DOCUMENT).read_bytes())
    source = manifests[1]["sources"][0]
    if mutation == "interval":
        source["interval"] = "1h"
    elif mutation == "month_hash":
        source["sha256"] = manifests[1]["sources"][1]["sha256"]
    elif mutation == "url":
        source["url"] += "wrong"
    elif mutation == "count":
        manifests[1]["coverage"]["row_counts"]["BTCUSDT"] -= 1
    else:
        manifests[1]["sources"].pop()
    with pytest.raises(ValueError):
        audit._source_tables(*manifests, snapshot, pins)


@pytest.mark.parametrize(
    "failure",
    [
        "hourly_loader",
        "minute_loader",
        "changed_source",
        "changed_code",
        "partial_output",
        "output_tamper",
        "manifest_link",
    ],
)
def test_failures_never_leave_success_manifest(
    fabricated_release, monkeypatch, failure
):
    options, _, _, _ = fabricated_release

    def fail(*args, **kwargs):
        raise ValueError("injected fabricated failure")

    if failure in ("hourly_loader", "minute_loader"):
        module = audit.hourly if failure == "hourly_loader" else audit.minute
        name = (
            "load_execution_data"
            if failure == "hourly_loader"
            else "load_minute_execution_data"
        )
        monkeypatch.setattr(module, name, fail)
    elif failure in ("changed_source", "changed_code"):
        original = audit._stream_minute_projection

        def changed(*args, **kwargs):
            projection = original(*args, **kwargs)
            target = (
                options["hourly_directory"] / "hourly_opens.csv"
                if failure == "changed_source"
                else audit.ROOT / "implementation.py"
            )
            target.write_bytes(target.read_bytes() + b"changed")
            return projection

        monkeypatch.setattr(audit, "_stream_minute_projection", changed)
    elif failure == "output_tamper":
        original = audit._verify_outputs

        def tampered(destination, payloads):
            (destination / "parity_report.json").write_bytes(b"{}")
            return original(destination, payloads)

        monkeypatch.setattr(audit, "_verify_outputs", tampered)
    else:
        original = audit._write

        def interrupted(path, body):
            if failure == "partial_output" and path.name == "discrepancies.csv":
                path.with_suffix(".partial").write_bytes(body[:10])
                fail()
            original(path, body)
            if failure == "manifest_link" and path.name == "manifest.json":
                fail()

        monkeypatch.setattr(audit, "_write", interrupted)
    with pytest.raises(ValueError):
        audit.audit_genuine_minute_price_parity(**options)
    destination = options["destination"]
    assert not (destination / "manifest.json").exists()
    evidence = json.loads((destination / "failure.json").read_bytes())
    assert evidence["complete"] is False
    assert evidence["direct_timing_comparison_permitted"] is False
    with pytest.raises(ValueError, match="already exists"):
        audit.audit_genuine_minute_price_parity(**options)


def test_write_exclusivity_and_symlink_refusal(tmp_path):
    path = tmp_path / "output.json"
    audit._write(path, b"original")
    with pytest.raises(FileExistsError):
        audit._write(path, b"replacement")
    assert path.read_bytes() == b"original"
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="Symlink"):
        audit._read(link)


def test_pin_document_parser_requires_complete_unique_tables(fabricated_release):
    body = (audit.ROOT / audit.PIN_DOCUMENT).read_bytes()
    assert len(audit._minute_pins(body)) == 24
    with pytest.raises(ValueError):
        audit._minute_pins(body + body.splitlines(keepends=True)[0])
    with pytest.raises(ValueError):
        audit._minute_pins(b"\n".join(body.splitlines()[1:]))


def test_identical_fabricated_publications_reproduce_scientific_bytes(
    fabricated_release,
):
    options, calls, _, _ = fabricated_release
    first_result = audit.audit_genuine_minute_price_parity(**options)
    destination = options["destination"]
    retained = destination.with_name("retained-fabricated-test-publication")
    destination.rename(retained)
    calls.clear()
    second_result = audit.audit_genuine_minute_price_parity(**options)
    assert first_result == second_result
    for name in first_result["files"]:
        assert (retained / name).read_bytes() == (destination / name).read_bytes()
    assert (retained / "manifest.json").read_bytes() == (
        destination / "manifest.json"
    ).read_bytes()


def test_mutation_after_output_verification_invalidates_publication(
    fabricated_release, monkeypatch
):
    options, _, _, _ = fabricated_release
    original = audit._verify_outputs

    def changed(destination, payloads):
        result = original(destination, payloads)
        source = options["minute_directory"] / "raw" / "ETHUSDT-1m-2024-12.zip"
        source.write_bytes(source.read_bytes() + b"changed after output verification")
        return result

    monkeypatch.setattr(audit, "_verify_outputs", changed)
    with pytest.raises(ValueError, match="changed before manifest"):
        audit.audit_genuine_minute_price_parity(**options)
    assert not (options["destination"] / "manifest.json").exists()
    assert (options["destination"] / "failure.json").is_file()

"""Offline envelope integrity, never permission to invoke genuine verification.

Only the private verifier accepts an injected key, for fabricated tests. The
production preflight is unconditionally closed, even if constants are changed.
No signing, file-reading, key-enrolment, invocation or publication API exists.
"""

import calendar
import json
import re
import unicodedata
from datetime import UTC, datetime
from hashlib import sha256

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from backtest_badger import genuine_minute_verification_operator as fixture_contract
from backtest_badger import genuine_minute_verification_wiring as wiring

SCHEMA = "minute-input-owner-signature-v1"
PAYLOAD_SCHEMA = "minute-input-verification-intent-v1"
DOMAIN = b"BACKTEST_BADGER_MINUTE_INPUT_VERIFICATION_APPROVAL_V1\n"
TRUSTED_OWNER_PUBLIC_KEY = None
TRUSTED_OWNER_KEY_ID = None
MAX_DOCUMENT_BYTES = 1024 * 1024
IMPLEMENTATION_FILES = tuple(
    sorted(
        {
            *wiring.IMPLEMENTATION_FILES,
            "src/backtest_badger/genuine_minute_signed_approval.py",
            "docs/stage-04b2d6-genuine-verification-activation.md",
            "docs/stage-04b2d7-offline-signed-approval.md",
        }
    )
)
# Full non-Windows CPython runtime closure of the current lock, not dev tools.
# Windows additionally requires tzdata. Names use lockfile normalization.
DEPENDENCIES = frozenset(
    {
        *(name.lower() for name in wiring.DEPENDENCIES),
        "cryptography",
        "cffi",
        "pycparser",
        "mako",
        "markupsafe",
        "typing-extensions",
        "cloudpickle",
        "narwhals",
    }
)
MONTHLY_FIELDS = {
    "sha256",
    "checksum_sha256",
    "zip_bytes",
    "checksum_bytes",
    "csv_bytes",
    "row_count",
    "url",
    "checksum_url",
    "observed_at",
}


def preflight_owner_approval(*, approval):
    """Refuse before argument inspection or I/O; enrolment alone cannot enable it."""
    raise PermissionError("Owner trust enrolment and genuine invocation remain closed.")


def _require(condition):
    if not condition:
        raise ValueError("Invalid offline approval.")


def _tree(value, depth=0):
    """Exact builtin types only: never call object adapters or dataclasses.asdict."""
    _require(depth <= 32)
    kind = type(value)
    if kind is str:
        _require(
            unicodedata.normalize("NFC", value) == value
            and all(ord(c) >= 32 and not 0xD800 <= ord(c) <= 0xDFFF for c in value)
        )
    elif kind is int:
        _require(-(2**63) <= value < 2**63)
    elif kind is bool:
        pass
    elif kind is list:
        for item in value:
            _tree(item, depth + 1)
    elif kind is dict:
        for key, item in value.items():
            _require(type(key) is str)
            _tree(key, depth + 1)
            _tree(item, depth + 1)
    else:
        _require(False)


def canonical_approval_bytes(value):
    """V1 UTF-8/NFC JSON, sorted keys, compact separators, no terminal newline.

    This signing format is distinct from scientific evidence JSON. No floats,
    nulls, custom objects, U+0000..U+001F or implicit type conversions.
    """
    try:
        _tree(value)
        body = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        _require(len(body) <= MAX_DOCUMENT_BYTES)
        return body
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise ValueError("Invalid offline approval.") from None


def _fields(value, fields):
    _require(type(value) is dict and value.keys() == set(fields))


def _hex(value, size=64):
    _require(type(value) is str and re.fullmatch(f"[0-9a-f]{{{size}}}", value))


def _positive(value):
    _require(type(value) is int and 0 < value < 2**63)


def _identities(value, names):
    _fields(value, names)
    for item in value.values():
        _fields(item, {"sha256", "bytes"})
        _hex(item["sha256"])
        _positive(item["bytes"])


def _validate_payload(payload, *, reviewed_commit, ci_run_id):
    """Validate an inert intent, not genuine evidence or fixture execution rights.

    Expected review identities are independent TEST inputs here. Future production
    validation must also compare enrolled owner declarations and observed runtime.
    """
    auth = fixture_contract.auth
    _fields(payload, fixture_contract.APPROVAL_FIELDS)
    _require(payload["schema"] == PAYLOAD_SCHEMA)
    _require(payload["source_kind"] == wiring.verification_plan().future_source_kind)
    for name, expected in wiring.verification_plan().required_flags:
        _require(payload[name] is expected)
    _hex(reviewed_commit, 40)
    _hex(payload["commit"], 40)
    _require(payload["commit"] == reviewed_commit)
    _require(type(ci_run_id) is str and re.fullmatch("[1-9][0-9]*", ci_run_id))
    _fields(payload["ci"], {"commit", "run_id", "status", "conclusion"})
    _require(
        payload["ci"]
        == {
            "commit": reviewed_commit,
            "run_id": ci_run_id,
            "status": "completed",
            "conclusion": "success",
        }
    )
    runtime = payload["runtime"]
    _fields(runtime, {"python", "implementation", "platform", "dependencies"})
    _require(runtime["implementation"] == "CPython")
    _require(
        type(runtime["python"]) is str
        and re.fullmatch(r"3\.12\.(0|[1-9][0-9]*)", runtime["python"])
    )
    _require(runtime["platform"] in ("darwin", "linux", "win32"))
    dependencies = DEPENDENCIES | (
        {"tzdata"} if runtime["platform"] == "win32" else set()
    )
    _fields(runtime["dependencies"], dependencies)
    for version in runtime["dependencies"].values():
        _require(type(version) is str and re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", version))

    # Lexical comparison only. Never resolve/stat even an ancestor of these paths.
    _fields(payload["roots"], dict(wiring.ROOTS))
    destination = payload["destination"]
    _require(type(destination) is str and destination.startswith("/"))
    _require(all(p not in ("", ".", "..") for p in destination.split("/")[1:]))
    _require("\\" not in destination and destination.endswith("/" + wiring.DESTINATION))
    checkout = destination[: -len(wiring.DESTINATION)]
    _require(payload["roots"] == {name: checkout + path for name, path in wiring.ROOTS})

    inventories = payload["input_inventory"]
    _fields(inventories, {"forecast", "minute", "parity"})
    _identities(
        inventories["forecast"], {"manifest.json", "validation_predictions.csv"}
    )
    _identities(inventories["minute"], auth._release_names("1m"))
    _identities(inventories["parity"], auth.PARITY_FILES)
    _identities(payload["implementation"], IMPLEMENTATION_FILES)
    _fields(payload["audit_code"], auth.parity.IMPLEMENTATION_FILES)
    for value in payload["audit_code"].values():
        _hex(value)
    pins = payload["pins"]
    _fields(pins, dict(wiring.DECLARATIONS))
    for value in pins.values():
        _hex(value)
    for group, name, key in (
        ("forecast", "manifest.json", "forecast_manifest"),
        ("forecast", "validation_predictions.csv", "forecast_csv"),
        ("minute", "manifest.json", "minute_manifest"),
        ("minute", "minute_opens.csv", "minute_csv"),
        ("parity", "manifest.json", "parity_manifest"),
        ("parity", "parity_report.json", "parity_report"),
        ("parity", "provenance.json", "parity_provenance"),
        ("parity", "integrity.json", "parity_integrity"),
        ("parity", "discrepancies.csv", "parity_discrepancies"),
    ):
        _require(inventories[group][name]["sha256"] == pins[key])
    for path, key in (
        (auth.parity.HOURLY_PROTOCOL, "hourly_protocol"),
        (auth.parity.MINUTE_PROTOCOL, "minute_protocol"),
        (wiring.PIN_DOCUMENT, "minute_pin_document"),
    ):
        _require(payload["implementation"][path]["sha256"] == pins[key])

    months = [
        (s, f"2024-{m:02d}") for s in ("BTCUSDT", "ETHUSDT") for m in range(1, 13)
    ]
    for name in ("monthly_sources", "hourly_monthly"):
        rows = payload[name]
        _require(type(rows) is list and len(rows) == 24)
        _require(all(type(r) is list and len(r) == 3 for r in rows))
        _require([(r[0], r[1]) for r in rows] == months)
    for _, _, value in payload["hourly_monthly"]:
        _hex(value)
    for symbol, month, row in payload["monthly_sources"]:
        _fields(row, MONTHLY_FIELDS)
        for key in ("sha256", "checksum_sha256"):
            _hex(row[key])
        for key in ("zip_bytes", "checksum_bytes", "csv_bytes", "row_count"):
            _positive(row[key])
        number = int(month[-2:])
        _require(row["row_count"] == calendar.monthrange(2024, number)[1] * 1440)
        stem = f"{symbol}-1m-{month}.zip"
        url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/1m/{stem}"
        _require(row["url"] == url and row["checksum_url"] == url + ".CHECKSUM")
        receipt = row["observed_at"]
        _require(
            type(receipt) is str
            and re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
                r"(?:\.[0-9]{6})?\+00:00",
                receipt,
            )
        )
        end = datetime(2025 if number == 12 else 2024, number % 12 + 1, 1, tzinfo=UTC)
        observed = datetime.fromisoformat(receipt)
        _require(observed.isoformat() == receipt and observed >= end)
        for suffix, hash_key, size_key in (
            ("", "sha256", "zip_bytes"),
            (".CHECKSUM", "checksum_sha256", "checksum_bytes"),
        ):
            _require(
                inventories["minute"][f"raw/{stem}{suffix}"]
                == {
                    "sha256": row[hash_key],
                    "bytes": row[size_key],
                }
            )


def _verify_envelope(*, document, public_key, key_id, reviewed_commit, ci_run_id):
    """Pure INTERNAL fabricated-key seam; return detached canonical payload bytes.

    Injected key/review identities are never production authority. A successful
    result has no execution eligibility and cannot open either genuine gate.
    """
    try:
        _require(type(public_key) is bytes and len(public_key) == 32)
        _require(
            type(key_id) is str and key_id == "sha256:" + sha256(public_key).hexdigest()
        )
        _require(type(document) is bytes and len(document) <= MAX_DOCUMENT_BYTES)

        def pairs(items):
            result = {}
            for name, value in items:
                _require(name not in result)
                result[name] = value
            return result

        def invalid(_):
            raise ValueError("Invalid offline approval.")

        envelope = json.loads(
            document.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_float=invalid,
            parse_constant=invalid,
        )
        _require(canonical_approval_bytes(envelope) == document)
        _fields(envelope, {"schema", "key_id", "payload", "signature"})
        _require(envelope["schema"] == SCHEMA and envelope["key_id"] == key_id)
        _hex(envelope["signature"], 128)
        authenticated = {
            name: envelope[name] for name in ("schema", "key_id", "payload")
        }
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            bytes.fromhex(envelope["signature"]),
            DOMAIN + canonical_approval_bytes(authenticated),
        )
        _validate_payload(
            envelope["payload"], reviewed_commit=reviewed_commit, ci_run_id=ci_run_id
        )
        return canonical_approval_bytes(envelope["payload"])
    except (
        ValueError,
        TypeError,
        KeyError,
        RecursionError,
        UnicodeError,
        InvalidSignature,
    ):
        # No candidate values, decoder excerpts, paths or crypto internals in errors.
        raise ValueError("Invalid offline approval.") from None

"""Pure publication-to-replay bridge; no operational entry, I/O or authority.

External pins must come from a separately trusted owner-reviewed boundary. Matching
caller-invented bytes and pins do NOT establish independent authentication. Frozen
Python records are not capabilities. Original publication/sign-off bytes stay unread
during development; the D.14 writer contract is supplied independently by the owner.
"""

import json
from dataclasses import dataclass, field, fields
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256

from backtest_badger import genuine_minute_inputs as auth
from backtest_badger import genuine_minute_replay as replay
from backtest_badger import genuine_minute_signed_approval as signed
from backtest_badger import genuine_minute_verification_operator as operator
from backtest_badger import paper_minute_historical as minute
from backtest_badger.paper_accounting import Account, fund_account
from backtest_badger.paper_historical import HistoricalDecision
from backtest_badger.paper_types import STEP, Portfolio, digest, number, require, utc

KIND = "genuine_publication_hypothetical_minute_replay"
SOURCE_KIND = operator._SourceKind.GENUINE.value
FILES = ("manifest.json", "authenticated_inputs.json", "integrity.json")
LIMITS = (4096, 32 * 1024 * 1024, 1024 * 1024)
SIGNOFF_PUBLICATION = "artifacts/audits/stage-04b2d3-minute-inputs-v1"
SIGNOFF_CHECKS = (
    "Exact no-follow publication path; exactly three existing files",
    "Independently retained manifest SHA-256 before parsing",
    "All manifest-declared companion hashes and byte lengths",
    "Strict canonical JSON, scientific and operational crosschecks",
    "Original 57 source, 45 implementation, and 22 historical audit identities",
    "Second exact-file byte/hash/metadata readback",
)
SIGNOFF_LIMITATIONS = (
    "Read-only post-publication readback, not genuine verification rerun",
    "No original data sources, signed approval, private signing key "
    "or strategy engine read",
    "CI success was previously independently checked, not re-queried by this script",
    "Observed file preservation does not exclude hostile replace/restore races",
    "Procedure restricts inputs by exact paths; no OS-enforced sandbox",
    "No economic or replay authority is conferred by this sign-off",
)


@dataclass(frozen=True)
class _Fingerprint:
    sha256: str
    bytes: int


@dataclass(frozen=True)
class _PublicationPins:
    """Separately retained identities, never calculated by the reader from input."""

    manifest: _Fingerprint
    authenticated_inputs: _Fingerprint
    integrity: _Fingerprint
    signoff: _Fingerprint


@dataclass(frozen=True)
class _VerifiedPublication:
    """Revalidated at replay; neither this type nor its fields grant authority."""

    bodies: tuple[bytes, bytes, bytes]
    pins: _PublicationPins
    inputs: auth.AuthenticatedMinuteInputs


@dataclass(frozen=True)
class _ReconciledSignoff:
    """Historical document agreement only; not an execution capability."""

    body: bytes
    publication: _VerifiedPublication


@dataclass(frozen=True)
class _PublicationMinuteSource:
    symbol: str
    publication: _PublicationPins
    forecast_sha256: str
    model_recipe_sha256: str
    manifest_sha256: str
    file_sha256: str
    monthly_sources: tuple[tuple[str, str, str], ...]
    projected_sha256: str
    kind: str = field(default=KIND, init=False)


@dataclass(frozen=True)
class _PublicationReplayResult:
    symbol: str
    source: _PublicationMinuteSource
    decisions: tuple[HistoricalDecision, ...]
    accounts: tuple[minute.MinuteAccount, ...]
    end_exclusive: datetime = field(default=minute.END, init=False)
    protocol_version: str = field(default=minute.PROTOCOL_VERSION, init=False)
    protocol_sha256: str = field(default=minute.PROTOCOL_SHA256, init=False)
    kind: str = field(default=KIND, init=False)
    status: str = field(
        default="hypothetical_previously_inspected_validation", init=False
    )
    authority: str = field(
        default="not_granted_by_private_conversion_or_replay", init=False
    )


def _fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Wrong exact field set.")


def _fingerprint(value, limit):
    require(type(value) is _Fingerprint, "Immutable external fingerprint required.")
    require(type(value.sha256) is str, "Exact fingerprint string required.")
    digest(value.sha256)
    require(
        type(value.bytes) is int and 0 < value.bytes <= limit, "Invalid byte bound."
    )


def _identity(body):
    return {"sha256": sha256(body).hexdigest(), "bytes": len(body)}


def _canonical(body, *, science=False):
    value = auth._json(body)
    encoded = (
        minute.scientific_json(value).encode("ascii")
        if science
        else operator._json(value)
    )
    require(body == encoded, "Noncanonical publication encoding.")
    return value


def _snapshot(snapshot, expected):
    _fields(snapshot, expected)
    for name, item in snapshot.items():
        _fields(item, ("sha256", "bytes", "stat"))
        require(
            operator._json({k: item[k] for k in ("sha256", "bytes")})
            == operator._json(expected[name]),
            "Retained identity mismatch.",
        )
        stamp = item["stat"]
        require(
            type(stamp) is list
            and len(stamp) == 5
            and all(type(v) is int and v >= 0 for v in stamp)
            and stamp[2] == item["bytes"],
            "Invalid retained stat claim.",
        )


def _validate_integrity(integrity):
    _fields(
        integrity,
        (
            "schema",
            "approval",
            "environment",
            "sources_before",
            "sources_after",
            "code_before",
            "code_after",
        ),
    )
    require(
        integrity["schema"] == "minute-input-operational-integrity-v1",
        "Wrong integrity schema.",
    )
    approved = integrity["approval"]
    _fields(approved, operator.APPROVAL_FIELDS)
    # Pure schema/intent validation only: no envelope verification, key or file read.
    signed._validate_payload(
        approved, reviewed_commit=approved["commit"], ci_run_id=approved["ci"]["run_id"]
    )
    require(
        operator._json(integrity["environment"])
        == operator._json(
            {
                "commit": approved["commit"],
                "clean": True,
                "runtime": approved["runtime"],
            }
        ),
        "Original environment disagrees with verification intent.",
    )
    require(
        operator._json(integrity["sources_before"])
        == operator._json(integrity["sources_after"])
        and operator._json(integrity["code_before"])
        == operator._json(integrity["code_after"]),
        "Original preservation claims disagree.",
    )
    _fields(integrity["sources_before"], approved["input_inventory"])
    for group, expected in approved["input_inventory"].items():
        _snapshot(integrity["sources_before"][group], expected)
    _snapshot(integrity["code_before"], approved["implementation"])
    return approved


def _retained_metadata(value, identity):
    """Original indented encoding used by the source/parity publishers."""
    body = (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    require(_identity(body) == identity, "Retained source metadata pin mismatch.")


def _lineage(manifest, pins):
    # Do not invoke the protected original-source policy or translate its hashes.
    _fields(
        manifest,
        (
            "experiment_version",
            "input",
            "feature_order",
            "target",
            "fit_partition",
            "evaluation_partition",
            "test_policy",
            "metric_definitions",
            "random_seed",
            "thread_limit",
            "reproducibility_tolerance",
            "runtime",
            "implementation_sha256",
            "preprocessing",
            "limitations",
            "markets",
            "output_sha256",
        ),
    )
    require(
        manifest["experiment_version"] == "stage-2b-v1"
        and manifest["fit_partition"] == "train"
        and manifest["evaluation_partition"] == "validation"
        and manifest["feature_order"] == list(auth.policy.FEATURES),
        "Wrong research recipe/partitions.",
    )
    _fields(
        manifest["input"],
        (
            "feature_definitions",
            "target_definition",
            "split_boundaries",
            "split_clock",
            "settling_seconds",
            "exclusion_policy",
            "known_anomalies",
            "source_selection_policy",
            "counts",
            "input_hashes",
        ),
    )
    require(
        manifest["input"]["input_hashes"]
        == {
            "research.csv": pins["research_csv"],
            "manifest.json": pins["research_manifest"],
        }
        and type(manifest["input"]["settling_seconds"]) is int
        and manifest["input"]["settling_seconds"] == 60,
        "Wrong research lineage.",
    )
    _fields(manifest["output_sha256"], ("validation_predictions.csv", "summary.md"))
    require(
        manifest["output_sha256"]["validation_predictions.csv"] == pins["forecast_csv"],
        "Wrong prediction lineage.",
    )
    _fields(manifest["markets"], minute.SYMBOLS)
    for symbol, count in zip(minute.SYMBOLS, (13782, 13783), strict=True):
        market = manifest["markets"][symbol]
        _fields(
            market,
            (
                "training_count",
                "validation_count",
                "training_mean",
                "validation_metrics",
                "model_parameters",
                "fitted_scaler",
            ),
        )
        require(
            type(market["training_count"]) is int
            and market["training_count"] == count
            and type(market["validation_count"]) is int
            and market["validation_count"] == 2195,
            "Wrong train/validation counts.",
        )
        require(type(market["training_mean"]) in (int, float), "Invalid training mean.")
        params = market["model_parameters"]
        _fields(params, (*auth.forecast.MODELS, "ridge_scaler"))
        require(
            operator._json(params["ridge"])
            == operator._json(
                {
                    "alpha": 1.0,
                    "copy_X": True,
                    "fit_intercept": True,
                    "max_iter": None,
                    "positive": False,
                    "random_state": None,
                    "solver": "svd",
                    "tol": 0.0001,
                }
            )
            and params["ridge_scaler"]
            == {"copy": True, "with_mean": True, "with_std": True},
            "Wrong frozen Ridge/scaler recipe.",
        )
        scaler = market["fitted_scaler"]
        _fields(scaler, ("mean", "scale", "n_samples_seen"))
        require(
            type(scaler["n_samples_seen"]) is int and scaler["n_samples_seen"] == count,
            "Scaler not training-only.",
        )
        for name in ("mean", "scale"):
            require(
                type(scaler[name]) is list and len(scaler[name]) == 5,
                "Wrong scaler dimensions.",
            )
            for value in scaler[name]:
                require(type(value) in (float, int), "Invalid recipe number.")
                value = number(Decimal(str(value)))
                require(name != "scale" or value > 0, "Invalid scale.")


def _validate_evidence(evidence, approved, projections):
    _fields(
        evidence,
        (
            "schema",
            "source_kind",
            "native_loader_evidence",
            "pins",
            "original_files",
            "code_sha256",
            "monthly_sources",
            "recipe_identity_kind",
            "recipe_sha256",
            "forecast_manifest",
            "minute_metadata",
            "parity_publication",
            "parity_report",
            "parity_provenance",
            "projection_sha256",
            "counts",
            "limitations",
        ),
    )
    pins = approved["pins"]
    require(
        evidence["schema"] == "minute-input-scientific-evidence-v1"
        and evidence["source_kind"] == SOURCE_KIND
        and evidence["native_loader_evidence"]
        == "unchanged_loader_full_native_archive_revalidation"
        and evidence["pins"] == pins
        and evidence["original_files"] == approved["input_inventory"]
        and evidence["code_sha256"]
        == {n: v["sha256"] for n, v in approved["implementation"].items()}
        and evidence["monthly_sources"] == approved["monthly_sources"]
        and evidence["recipe_identity_kind"] == "stage2b_manifest_sha256"
        and evidence["recipe_sha256"] == pins["forecast_manifest"]
        and pins["minute_protocol"] == minute.PROTOCOL_SHA256
        and evidence["projection_sha256"] == projections
        and evidence["limitations"] == list(auth.LIMITATIONS),
        "Scientific/intent evidence mismatch.",
    )
    require(
        operator._json(evidence["counts"])
        == operator._json(
            {
                "forecast_accounts": 8,
                "forecasts_per_account": 2195,
                "native_rows": 1054080,
                "hourly_marks_per_market": 8784,
                "hypothetical_minutes_per_market": 2195,
                "references": 21958,
            }
        ),
        "Wrong scientific counts.",
    )
    inventory = approved["input_inventory"]
    _retained_metadata(
        evidence["forecast_manifest"], inventory["forecast"]["manifest.json"]
    )
    _lineage(evidence["forecast_manifest"], pins)
    metadata = evidence["minute_metadata"]
    _retained_metadata(metadata, inventory["minute"]["manifest.json"])
    monthly = {(s, m): row for s, m, row in approved["monthly_sources"]}
    auth._minute_metadata(
        metadata,
        inventory["minute"],
        monthly,
        pins,
        inventory["minute"]["minute_opens.csv"]["bytes"],
        approved["implementation"]["src/backtest_badger/minute_execution_data.py"][
            "sha256"
        ],
    )
    _parity_links(evidence, approved)


def _parity_links(evidence, approved):
    inventory, pins = approved["input_inventory"]["parity"], approved["pins"]
    for key, name in (
        ("parity_publication", "manifest.json"),
        ("parity_report", "parity_report.json"),
        ("parity_provenance", "provenance.json"),
    ):
        _retained_metadata(evidence[key], inventory[name])
    publication = evidence["parity_publication"]
    _fields(
        publication,
        ("schema", "kind", "status", "files", "direct_timing_comparison_permitted"),
    )
    require(
        publication
        == {
            "schema": "genuine-native-parity-publication-v1",
            "kind": "source_price_parity_only",
            "status": "exact_price_parity",
            "direct_timing_comparison_permitted": True,
            "files": {n: v for n, v in inventory.items() if n != "manifest.json"},
        },
        "Broken retained parity publication links.",
    )
    report = evidence["parity_report"]
    _fields(
        report,
        (
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
        ),
    )
    require(
        report["schema"] == "native-opening-price-parity-v1"
        and report["status"] == "exact_price_parity"
        and report["direct_timing_comparison_permitted"] is True
        and report["authentication"]
        == "genuine_pinned_releases_full_native_archive_revalidation"
        and report["discrepancies"] == report["structural_errors"] == []
        and report["limitations"] == list(auth.parity.LIMITATIONS)
        and report["start"] == minute.START.isoformat()
        and report["end_exclusive"] == minute.END.isoformat()
        and report["last_hour"] == (minute.END - minute.HOUR).isoformat()
        and report["native_interval_seconds"] == {"hourly": 3600, "minute": 60}
        and report["comparison"]
        == "exact Decimal equality; no tolerance or substitution",
        "Incomplete retained parity success.",
    )
    auth._parity_counts(report["overall"], 17568)
    groups = {
        "per_symbol": {s: 8784 for s in minute.SYMBOLS},
        "per_month": {
            f"2024-{m:02d}": auth.calendar.monthrange(2024, m)[1] * 48
            for m in range(1, 13)
        },
        "per_symbol_month": {
            f"{s}:2024-{m:02d}": auth.calendar.monthrange(2024, m)[1] * 24
            for s in minute.SYMBOLS
            for m in range(1, 13)
        },
    }
    for name, values in groups.items():
        _fields(report[name], values)
        for key, count in values.items():
            auth._parity_counts(report[name][key], count)
    provenance = evidence["parity_provenance"]
    _fields(
        provenance,
        (
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
        ),
    )
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
            auth.parity.HOURLY_PROTOCOL: pins["hourly_protocol"],
            auth.parity.MINUTE_PROTOCOL: pins["minute_protocol"],
            auth.parity.PIN_DOCUMENT: pins["minute_pin_document"],
        },
    }
    require(
        provenance["schema"] == "genuine-native-parity-provenance-v1"
        and provenance["kind"] == "source_price_parity_only"
        and provenance["expected_external_pins"] == external
        and provenance["implementation_sha256"] == approved["audit_code"]
        and len(approved["audit_code"]) == 22
        and all(
            approved["audit_code"][n] == h for n, h in external["documents"].items()
        )
        and provenance["source_paths"]
        == {"hourly": auth.parity.HOURLY_PATH, "minute": auth.MINUTE_PATH}
        and provenance["native_rows_per_symbol"] == {"hourly": 8784, "minute": 527040}
        and type(provenance["projected_rows_per_symbol"]) is int
        and provenance["projected_rows_per_symbol"] == 8784
        and provenance["limitations"] == list(auth.parity.LIMITATIONS),
        "Broken retained auditor/source links.",
    )
    _fields(provenance["source_manifests"], ("hourly", "minute"))
    require(
        provenance["source_manifests"]["minute"] == evidence["minute_metadata"],
        "Different parity minute source.",
    )
    proof = provenance["integrity"]
    _fields(
        proof,
        (
            "method",
            "source_file_count",
            "all_source_bytes_and_stats_unchanged",
            "sources",
            "loaders",
            "minute_projection",
        ),
    )
    require(
        proof["all_source_bytes_and_stats_unchanged"] is True
        and type(proof["source_file_count"]) is int
        and proof["source_file_count"] == 101,
        "Incomplete retained parity preservation.",
    )
    _fields(proof["sources"], ("hourly", "minute"))
    require(
        proof["sources"]["minute"] == approved["input_inventory"]["minute"],
        "Different retained native sources.",
    )
    for release, interval in (("hourly", "1h"), ("minute", "1m")):
        signed._identities(proof["sources"][release], auth._release_names(interval))
        for name, value in external[release].items():
            require(
                proof["sources"][release][name]["sha256"] == value,
                "Parity source pin swap.",
            )
    hourly = provenance["source_manifests"]["hourly"]
    require(
        hourly["artifact_version"] == "binance-1h-2024-v1"
        and hourly["coverage"] == auth.parity.hourly.coverage()
        and hourly["archive_count"] == 24
        and hourly["output_sha256"]
        == {n: h for n, h in external["hourly"].items() if n != "manifest.json"},
        "Wrong retained hourly lineage.",
    )
    _verify_hourly_associations(hourly["sources"], approved["hourly_monthly"])


def _verify_hourly_associations(sources, declarations):
    """Verify 24 monthly hourly sources by (symbol, month), not list position.

    This matches the original genuine auditor's key-based association policy.
    Reject duplicates, missing/extra keys, changed hashes or failed integrity flags.
    """
    require(
        type(sources) is list and len(sources) == 24,
        "Incomplete hourly sources.",
    )
    require(
        type(declarations) is list and len(declarations) == 24,
        "Incomplete reviewed hourly associations.",
    )
    expected = {}
    for row in declarations:
        require(type(row) is list and len(row) == 3, "Invalid hourly declaration.")
        symbol, month, source_sha256 = row
        require(
            type(symbol) is str
            and type(month) is str
            and type(source_sha256) is str
            and (symbol, month) not in expected,
            "Duplicate/invalid reviewed hourly association.",
        )
        digest(source_sha256)
        expected[symbol, month] = source_sha256

    seen = set()
    for source in sources:
        require(type(source) is dict, "Invalid retained hourly source.")
        symbol, month = source["symbol"], source["month"]
        require(
            type(symbol) is str and type(month) is str,
            "Invalid retained hourly market/month.",
        )
        key = symbol, month
        require(
            key in expected
            and key not in seen
            and source["sha256"] == expected[key]
            and source["complete"] is True
            and source["checksum_valid"] is True,
            "Retained hourly source association changed.",
        )
        seen.add(key)
    require(seen == set(expected), "Incomplete retained hourly associations.")


def _records(science, evidence):
    def rows(groups, cls, times, decimals, counts):
        require(
            type(groups) is list and len(groups) == counts[0], "Wrong account count."
        )
        result = []
        for group in groups:
            require(type(group) is list and len(group) == counts[1], "Wrong row count.")
            converted = []
            for row in group:
                _fields(row, (f.name for f in fields(cls)))
                values = dict(row)
                for name in times:
                    require(type(row[name]) is str, "String UTC timestamp required.")
                    values[name] = utc(datetime.fromisoformat(row[name]))
                    require(
                        values[name].isoformat() == row[name],
                        "Noncanonical UTC timestamp.",
                    )
                for name in decimals:
                    require(
                        type(row[name]) is str and len(row[name]) <= 100,
                        "Bounded Decimal string required.",
                    )
                    values[name] = number(Decimal(row[name]))
                    require(
                        str(values[name]) == row[name], "Noncanonical Decimal string."
                    )
                converted.append(cls(**values))
            result.append(tuple(converted))
        return tuple(result)

    forecasts = rows(
        science["forecasts"],
        auth.VerifiedForecast,
        ("source_open", "assumed_available_at", "hypothetical_minute_at"),
        ("prediction",),
        (8, 2195),
    )
    replay._convert_verified_forecasts(forecasts, evidence["pins"]["forecast_csv"])
    for (symbol, model), account in zip(auth.ACCOUNT_KEYS, forecasts, strict=True):
        if model == "training_mean":
            mean = Decimal(
                format(
                    evidence["forecast_manifest"]["markets"][symbol]["training_mean"],
                    ".17g",
                )
            )
            require(
                all(row.prediction == mean for row in account),
                "Training mean mismatch.",
            )
    references = rows(
        science["references"], minute.MinuteReference, ("at",), ("price",), (2, 10979)
    )
    required = sorted(
        {minute.START + i * minute.HOUR for i in range(8784)}
        | {minute.START + i * STEP + 2 * minute.MINUTE for i in range(2195)}
    )
    monthly = {(s, m): row["sha256"] for s, m, row in evidence["monthly_sources"]}
    for symbol, refs, projection in zip(
        minute.SYMBOLS, references, science["projection_sha256"], strict=True
    ):
        for ref, at in zip(refs, required, strict=True):
            require(
                ref.symbol == symbol
                and ref.at == at
                and ref.file_sha256 == evidence["pins"]["minute_csv"]
                and ref.source_sha256 == monthly[symbol, at.strftime("%Y-%m")],
                "Minute union/order/source mismatch.",
            )
        require(
            minute.projection_sha256(refs) == projection, "Projection digest mismatch."
        )
    return auth.AuthenticatedMinuteInputs(
        forecasts,
        references,
        science["source_evidence_json"].encode("ascii"),
        tuple(science["projection_sha256"]),
    )


def _parse_verified_publication(
    *, manifest, authenticated_inputs, integrity, expected, signoff_claim
):
    """In-memory only. Sign-off fingerprint agreement is NOT sign-off validation."""
    require(
        type(expected) is _PublicationPins,
        "Independent immutable publication pins required.",
    )
    bodies = (manifest, authenticated_inputs, integrity)
    for body, pin, limit in zip(
        bodies,
        (expected.manifest, expected.authenticated_inputs, expected.integrity),
        LIMITS,
        strict=True,
    ):
        _fingerprint(pin, limit)
        require(
            type(body) is bytes
            and len(body) == pin.bytes
            and sha256(body).hexdigest() == pin.sha256,
            "External publication bytes/hash mismatch.",
        )
    _fingerprint(expected.signoff, 1024 * 1024)
    _fingerprint(signoff_claim, 1024 * 1024)
    require(
        signoff_claim == expected.signoff,
        "External sign-off fingerprint claim changed.",
    )
    try:
        publication = _canonical(manifest)
        operational = _canonical(integrity)
        science = _canonical(authenticated_inputs, science=True)
        require(
            operator._json(publication)
            == operator._json(
                {
                    "schema": "minute-input-verification-publication-v1",
                    "kind": "source_authentication_only",
                    "complete": True,
                    "status": auth.STATUS,
                    "source_kind": SOURCE_KIND,
                    "genuine_execution_authorised": False,
                    "economic_results": False,
                    "files": {
                        n: _identity(b)
                        for n, b in zip(FILES[1:], bodies[1:], strict=True)
                    },
                }
            )
            and publication["complete"] is True
            and publication["genuine_execution_authorised"] is False
            and publication["economic_results"] is False,
            "Invalid publication manifest/associations.",
        )
        _fields(
            science,
            (
                "status",
                "genuine_execution_authorised",
                "forecasts",
                "references",
                "projection_sha256",
                "source_evidence_json",
            ),
        )
        require(
            science["status"] == auth.STATUS
            and science["genuine_execution_authorised"] is False,
            "Verification cannot grant replay authority.",
        )
        require(
            type(science["projection_sha256"]) is list
            and len(science["projection_sha256"]) == 2,
            "Two projection pins required.",
        )
        for value in science["projection_sha256"]:
            digest(value)
        require(
            type(science["source_evidence_json"]) is str
            and len(science["source_evidence_json"]) <= 1024 * 1024,
            "Bounded evidence required.",
        )
        evidence = _canonical(science["source_evidence_json"].encode("ascii"))
        approved = _validate_integrity(operational)
        _validate_evidence(evidence, approved, science["projection_sha256"])
        inputs = _records(science, evidence)
        require(
            auth.authenticated_inputs_json(inputs) == authenticated_inputs,
            "Typed roundtrip changed bytes.",
        )
        return _VerifiedPublication(bodies, expected, inputs)
    except (
        KeyError,
        TypeError,
        IndexError,
        UnicodeError,
        RecursionError,
        InvalidOperation,
    ) as error:
        raise ValueError("Malformed verified publication.") from error


def _validate_independent_signoff(*, signoff, expected_signoff, publication, expected):
    """Reconcile exact D.14 bytes with independently pinned publication evidence.

    Caller-created pins cannot establish independence. Reparse retained publication
    bytes rather than trusting an injected record. No source reads, signature/CI
    refresh, strategy execution or authority transfer takes place here.
    """
    _fingerprint(expected_signoff, 1024 * 1024)
    require(
        type(signoff) is bytes
        and len(signoff) == expected_signoff.bytes
        and sha256(signoff).hexdigest() == expected_signoff.sha256,
        "External sign-off bytes/hash mismatch.",
    )
    require(
        type(expected) is _PublicationPins, "Independent publication pins required."
    )
    _fingerprint(expected.signoff, 1024 * 1024)
    require(expected_signoff == expected.signoff, "External sign-off pin changed.")
    require(type(publication) is _VerifiedPublication, "Parsed publication required.")
    require(
        type(publication.bodies) is tuple and len(publication.bodies) == 3,
        "Immutable original publication bodies required.",
    )
    try:
        record = _canonical(signoff)
        checked = _parse_verified_publication(
            **dict(zip(FILES_KEYS, publication.bodies, strict=True)),
            expected=expected,
            signoff_claim=expected_signoff,
        )
        require(publication == checked, "Injected/changed verified record.")
        manifest = _canonical(checked.bodies[0])
        approved = _canonical(checked.bodies[2])["approval"]
        evidence = _canonical(checked.inputs.source_evidence_json)
        identities = {
            name: {"sha256": pin.sha256, "bytes": pin.bytes}
            for name, pin in zip(
                FILES,
                (expected.manifest, expected.authenticated_inputs, expected.integrity),
                strict=True,
            )
        }
        # The manifest binds its two companions; its own identity is bound by
        # exact externally pinned bytes above, never by a self-referential hash.
        require(
            operator._json(manifest["files"])
            == operator._json({name: identities[name] for name in FILES[1:]}),
            "Manifest/external identity mismatch.",
        )
        # Canonical encoded comparison preserves bool/int/float distinctions and
        # enforces every key, scalar type and ordered descriptive statement.
        declaration = {
            "schema": "stage-04b2d14-publication-signoff-v1",
            "status": "PASS",
            "original_execution_commit": approved["commit"],
            "reviewed_ci_run_id": approved["ci"]["run_id"],
            "publication": SIGNOFF_PUBLICATION,
            "independent_manifest_sha256": expected.manifest.sha256,
            "published_file_identities": identities,
            "publication_kind": manifest["kind"],
            "source_kind": manifest["source_kind"],
            "verification_flags": {
                name: approved[name]
                for name in (
                    "verification_only",
                    "single_attempt",
                    "resume",
                    "strategy_authorised",
                    "economic_publication_authorised",
                )
            },
            "genuine_execution_authorised": manifest["genuine_execution_authorised"],
            "economic_results": manifest["economic_results"],
            "scientific_counts": {
                "forecast_accounts": len(checked.inputs.forecasts),
                "forecasts": sum(map(len, checked.inputs.forecasts)),
                "reference_markets": len(checked.inputs.references),
                "references": sum(map(len, checked.inputs.references)),
                "native_minute_rows_authenticated": evidence["counts"]["native_rows"],
            },
            "checks": list(SIGNOFF_CHECKS),
            "limitations": list(SIGNOFF_LIMITATIONS),
        }
        require(
            operator._json(record) == operator._json(declaration),
            "Independent sign-off contract/publication mismatch.",
        )
        return _ReconciledSignoff(signoff, checked)
    except (KeyError, TypeError, IndexError, UnicodeError, RecursionError) as error:
        raise ValueError("Malformed independent sign-off.") from error


def _replay_verified_publication(publication, *, expected, signoff_claim):
    """Private pure seam; a future operator must supply separate execution authority.

    Reparse original bytes against external pins. Never trust an injected dataclass,
    relabel a fixture result, create a SyntheticPriceSource, or open a public gate.
    """
    require(type(publication) is _VerifiedPublication, "Parsed publication required.")
    require(
        type(publication.bodies) is tuple and len(publication.bodies) == 3,
        "Immutable original publication bodies required.",
    )
    checked = _parse_verified_publication(
        **dict(zip(FILES_KEYS, publication.bodies, strict=True)),
        expected=expected,
        signoff_claim=signoff_claim,
    )
    require(publication == checked, "Injected/changed verified record.")
    inputs = checked.inputs
    evidence = auth._json(inputs.source_evidence_json)
    pins = evidence["pins"]
    forecasts = replay._convert_verified_forecasts(
        inputs.forecasts, pins["forecast_csv"]
    )
    results = []
    for index, symbol in enumerate(minute.SYMBOLS):
        source = _PublicationMinuteSource(
            symbol,
            expected,
            pins["forecast_csv"],
            pins["forecast_manifest"],
            pins["minute_manifest"],
            pins["minute_csv"],
            tuple(
                (s, m, row["sha256"])
                for s, m, row in evidence["monthly_sources"]
                if s == symbol
            ),
            inputs.projection_sha256[index],
        )
        plan = minute._plan(
            symbol, forecasts[index], (), minute.END, source.forecast_sha256
        )
        initial = {}
        for label in ("ridge", "cash", "buy_and_hold"):
            portfolio = Portfolio(
                f"{KIND}:{symbol}:{label}",
                symbol,
                minute.START,
                sha256(minute.PROTOCOL_VERSION.encode()).hexdigest(),
                minute.PROTOCOL_SHA256,
                source.model_recipe_sha256,
                strategy_id="ridge_sign" if label == "ridge" else f"analytical_{label}",
            )
            initial[label] = fund_account(Account(portfolio), minute.START)
        decisions, accounts = minute._replay_minute_core(
            plan,
            inputs.references[index],
            {minute.START + i * minute.HOUR for i in range(8784)},
            initial,
            end_exclusive=minute.END,
        )
        results.append(_PublicationReplayResult(symbol, source, decisions, accounts))
    return tuple(results)


FILES_KEYS = ("manifest", "authenticated_inputs", "integrity")

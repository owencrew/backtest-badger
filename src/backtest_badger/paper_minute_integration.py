"""Pure Stage 4B.2D.2 fixture adaptation, never genuine authentication/execution.

External TEST pins bind supplied values, not original artifact bytes. There is no
loader, I/O, strategy call, genuine mode, permission override or publisher here.
"""

import calendar
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256

from backtest_badger.forecast_data import MODELS, Signal
from backtest_badger.paper_historical import END, HOUR, START, HistoricalForecast
from backtest_badger.paper_historical_evaluation import (
    FORECAST_SHA256,
    HOURLY_MANIFEST_SHA256,
    HOURLY_SHA256,
    RECIPE_SHA256,
    RESEARCH_MANIFEST_SHA256,
    RESEARCH_SHA256,
    _validate_lineage,
    json_bytes,
)
from backtest_badger.paper_minute_historical import (
    FROZEN_MINUTE_MANIFEST_SHA256,
    MINUTE,
    PROTOCOL_SHA256,
    PROTOCOL_VERSION,
    SYMBOLS,
    MinuteReference,
    SyntheticPriceSource,
    next_minute_at,
    price_source_sha256,
    projection_sha256,
    scientific_json,
    validate_price_projection,
)
from backtest_badger.paper_types import STEP, digest, number, require, utc

# Declarations from tracked frozen guides only; never read/recomputed from data.
FROZEN_MINUTE_CSV_SHA256 = (
    "37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233"
)
FROZEN_PARITY_MANIFEST_SHA256 = (
    "53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d"
)
FROZEN_PARITY_REPORT_SHA256 = (
    "0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb"
)
PIN_NAMES = (
    "forecast_manifest",
    "forecast_csv",
    "research_manifest",
    "research_csv",
    "hourly_manifest",
    "hourly_csv",
    "minute_manifest",
    "minute_csv",
    "parity_manifest",
    "parity_report",
)
GENUINE_DECLARATIONS = (
    RECIPE_SHA256,
    FORECAST_SHA256,
    RESEARCH_MANIFEST_SHA256,
    RESEARCH_SHA256,
    HOURLY_MANIFEST_SHA256,
    HOURLY_SHA256,
    FROZEN_MINUTE_MANIFEST_SHA256,
    FROZEN_MINUTE_CSV_SHA256,
    FROZEN_PARITY_MANIFEST_SHA256,
    FROZEN_PARITY_REPORT_SHA256,
)
ACCOUNT_KEYS = tuple((s, m) for s in SYMBOLS for m in MODELS)
AUTHENTICATION = "fabricated_supplied_evidence_only_not_genuine_authentication"


def evidence_sha256(value):
    """Canonical JSON fingerprint; manifest recipe floats are metadata, not money."""
    return sha256(json_bytes(value)).hexdigest()


def forecast_snapshot_sha256(forecast_result):
    """Stream all eight ordered Signal collections; retain this TEST pin upstream."""
    hashes, accounts = forecast_result
    require(set(accounts) == set(ACCOUNT_KEYS), "Expected all eight forecast accounts.")
    result = sha256(json_bytes(hashes))
    for key in ACCOUNT_KEYS:
        result.update(scientific_json(key).encode())
        for signal in accounts[key]:
            require(type(signal) is Signal, "Expected unchanged loader Signal type.")
            result.update(scientific_json(signal).encode())
    return result.hexdigest()


@dataclass(frozen=True)
class PreparedMinuteBundle:
    """Immutable synthetic inputs, with baselines retained for revalidation only."""

    accounts: tuple[tuple[Signal, ...], ...]
    forecasts: tuple[tuple[HistoricalForecast, ...], ...]
    references: tuple[tuple[MinuteReference, ...], ...]
    sources: tuple[SyntheticPriceSource, ...]
    end_exclusive: datetime
    source_evidence_json: bytes
    status: str = "synthetic_test"
    authentication: str = AUTHENTICATION


def _evidence(evidence, expected):
    # Permission gate precedes any payload inspection, including fingerprints.
    require(
        type(evidence) is dict and evidence.get("status") == "synthetic_test",
        "Permission gate: genuine integration is not implemented or authorised.",
    )
    digest(expected)
    require(
        evidence_sha256(evidence) == expected, "External TEST evidence pin mismatch."
    )
    require(
        evidence["protocol_version"] == PROTOCOL_VERSION
        and evidence["protocol_sha256"] == PROTOCOL_SHA256
        and evidence["selected_model"] == "ridge"
        and evidence["recipe_identity_kind"] == "stage2b_manifest_sha256",
        "Wrong protocol, selected model or recipe identity kind.",
    )
    pins = evidence["pins"]
    require(set(pins) == set(PIN_NAMES), "Missing/extra independent TEST source pins.")
    for value in pins.values():
        digest(value)
        require(
            value not in GENUINE_DECLARATIONS,
            "Genuine release declarations cannot be used as fixture pins.",
        )
    require(
        evidence["model_recipe_sha256"] == pins["forecast_manifest"],
        "Recipe must identify the whole Stage 2B manifest.",
    )
    end = utc(datetime.fromisoformat(evidence["end_exclusive"]))
    require(
        START < end <= END and not (end.minute or end.second or end.microsecond),
        "Expected a synthetic hourly endpoint within the frozen year.",
    )
    return pins, end


def _lineage(manifest, pins):
    require(
        manifest["input"]["input_hashes"]
        == {
            "research.csv": pins["research_csv"],
            "manifest.json": pins["research_manifest"],
        }
        and manifest["output_sha256"]["validation_predictions.csv"]
        == pins["forecast_csv"],
        "Wrong original research/prediction TEST lineage.",
    )
    # Reuse the unchanged policy validator. Translate ONLY already checked fixture
    # hash declarations in a detached copy; never change or authenticate input bytes.
    policy = json.loads(json_bytes(manifest))
    policy["input"]["input_hashes"] = {
        "research.csv": RESEARCH_SHA256,
        "manifest.json": RESEARCH_MANIFEST_SHA256,
    }
    policy["output_sha256"]["validation_predictions.csv"] = FORECAST_SHA256
    _validate_lineage(policy)


def _minute_metadata(metadata, evidence, pins):
    expected_coverage = {
        "start": START.isoformat(),
        "end_exclusive": END.isoformat(),
        "interval_seconds": 60,
        "row_counts": {s: 527040 for s in SYMBOLS},
        "total_rows": 1054080,
        "missing": 0,
        "complete": True,
    }
    require(
        metadata["artifact_version"] == "binance-1m-2024-v1"
        and metadata["format_version"] == "minute-opens-csv-v1"
        and metadata["status"]
        == "validated_source_structure_not_approved_for_evaluation"
        and metadata["source_authentication"]
        == "checksums_are_not_signed_provider_attestations"
        and json_bytes(metadata["coverage"]) == json_bytes(expected_coverage)
        and type(metadata["archive_count"]) is int
        and metadata["archive_count"] == 24,
        "Wrong full native release contract; projection is not full coverage.",
    )
    require(
        metadata["output"]["name"] == "minute_opens.csv"
        and metadata["output"]["sha256"] == pins["minute_csv"],
        "Wrong processed native source identity.",
    )
    require(
        type(metadata["output"]["bytes"]) is int and metadata["output"]["bytes"] > 0,
        "Invalid processed byte count.",
    )
    digest(metadata["implementation_sha256"])
    monthly = evidence["monthly_sources"]
    keys = [(s, f"2024-{m:02d}") for s in SYMBOLS for m in range(1, 13)]
    require(len(monthly) == len(metadata["sources"]) == 24, "Missing monthly sources.")
    for key, pin, row in zip(keys, monthly, metadata["sources"], strict=True):
        symbol, month = key
        require(
            len(pin) == 4
            and tuple(pin[:2]) == key
            and (row["symbol"], row["month"]) == key,
            "Missing/duplicate/reordered market-month source.",
        )
        digest(pin[2])
        digest(pin[3])
        url = (
            "https://data.binance.vision/data/spot/monthly/klines/"
            f"{symbol}/1m/{symbol}-1m-{month}.zip"
        )
        require(
            row["interval"] == "1m"
            and row["url"] == url
            and row["checksum_url"] == url + ".CHECKSUM"
            and row["sha256"] == pin[2]
            and row["checksum_sha256"] == pin[3]
            and type(row["row_count"]) is int
            and row["row_count"] == calendar.monthrange(2024, int(month[-2:]))[1] * 1440
            and row["observation_kind"] == "retrospective_full_archive_acquisition"
            and row["validation_status"] == "complete_checksum_and_native_grid",
            "Wrong native monthly ZIP/sidecar provenance.",
        )
        for name in ("zip_bytes", "checksum_bytes", "csv_bytes"):
            require(
                type(row[name]) is int and row[name] > 0, "Invalid native byte count."
            )
        month_end = datetime(2024, int(month[-2:]), 1, tzinfo=START.tzinfo) + timedelta(
            days=calendar.monthrange(2024, int(month[-2:]))[1]
        )
        require(
            utc(datetime.fromisoformat(row["observed_at"])) >= month_end,
            "Retrospective source receipt predates month end.",
        )
    require(
        len({p[2] for p in monthly}) == len({p[3] for p in monthly}) == 24,
        "Duplicate monthly source/checksum pins.",
    )
    return tuple(tuple(p[:3]) for p in monthly)


def _parity(parity, pins):
    """Validate a TEST proof-shaped record, not the genuine auditor's wire format."""
    manifest, report = parity["manifest"], parity["report"]
    require(
        evidence_sha256(manifest) == pins["parity_manifest"]
        and evidence_sha256(report) == pins["parity_report"],
        "Independent parity manifest/report TEST pin mismatch.",
    )
    require(
        manifest
        == {
            "kind": "synthetic_price_parity_fixture",
            "status": "synthetic_test",
            "report_sha256": pins["parity_report"],
        },
        "Wrong parity fixture manifest/status.",
    )
    require(
        report["status"] == "synthetic_test"
        and report["direct_timing_comparison_permitted"] is True
        and report["structural_errors"] == []
        and report["discrepancies"] == [],
        "Parity failure blocks timing comparison; no permission is granted.",
    )
    for name, version in (
        ("hourly", "binance-1h-2024-v1"),
        ("minute", "binance-1m-2024-v1"),
    ):
        require(
            report[name]
            == {
                "version": version,
                "manifest_sha256": pins[name + "_manifest"],
                "file_sha256": pins[name + "_csv"],
            },
            "Parity proof belongs to different source releases.",
        )
    require(
        json_bytes(report["counts"])
        == json_bytes(
            {
                "expected": 17568,
                "matched": 17568,
                "equal": 17568,
                "mismatched": 0,
                "per_market": {s: 8784 for s in SYMBOLS},
            }
        ),
        "Incomplete parity counts.",
    )
    hours = report["matched_hours"]
    require(len(hours) == 17568, "Missing parity hours.")
    for i, row in enumerate(hours):
        require(
            row == [SYMBOLS[i // 8784], (START + (i % 8784) * HOUR).isoformat()],
            "Missing/duplicate/reordered parity hour.",
        )


def adapt_minute_inputs(
    forecast_result,
    forecast_manifest,
    minute_metadata,
    minute_projection,
    parity_evidence,
    *,
    evidence,
    expected_evidence_sha256,
) -> PreparedMinuteBundle:
    """Adapt fabricated loader-shaped inputs. Required external pin has no default.

    evidence.end_exclusive can shorten synthetic prefixes only. Native metadata,
    recipe validation_count and prior parity still describe the complete year.
    All forecasts (including baselines) and references remain source-ordered.
    """
    try:
        pins, end = _evidence(evidence, expected_evidence_sha256)
        hashes, accounts = forecast_result
        require(
            hashes
            == {
                "manifest.json": pins["forecast_manifest"],
                "validation_predictions.csv": pins["forecast_csv"],
            },
            "Wrong forecast loader byte declarations.",
        )
        require(
            set(accounts) == set(ACCOUNT_KEYS), "Expected all eight forecast accounts."
        )
        _lineage(forecast_manifest, pins)
        monthly = _minute_metadata(minute_metadata, evidence, pins)
        _parity(parity_evidence, pins)
        snapshots = evidence["snapshots"]
        require(
            snapshots["forecasts"] == forecast_snapshot_sha256(forecast_result)
            and snapshots["forecast_manifest"] == evidence_sha256(forecast_manifest)
            and snapshots["minute_metadata"] == evidence_sha256(minute_metadata),
            "Supplied loader values changed after TEST snapshot pinning.",
        )
        count = min(2195, ((end - START) // HOUR + 3) // 4)
        forecasts = []
        for symbol in SYMBOLS:
            for model in MODELS:
                signals = accounts[symbol, model]
                require(len(signals) == count, "Wrong forecast count.")
                for i, signal in enumerate(signals):
                    require(
                        type(signal) is Signal
                        and signal.symbol == symbol
                        and signal.model == model
                        and utc(signal.open_time) == START - STEP + i * STEP
                        and utc(signal.signal_time) == signal.open_time + STEP + MINUTE,
                        "Wrong forecast market/model/grid/order/availability.",
                    )
                    number(signal.forecast)
                    if model == "zero":
                        require(signal.forecast == 0, "Zero baseline is not zero.")
                    if model == "training_mean":
                        mean = forecast_manifest["markets"][symbol]["training_mean"]
                        require(
                            not isinstance(mean, bool)
                            and signal.forecast == Decimal(format(mean, ".17g")),
                            "Training-mean baseline differs from manifest.",
                        )
            forecasts.append(
                tuple(
                    HistoricalForecast(
                        symbol,
                        f"binance:spot:{symbol}:14400:{s.open_time.isoformat()}:ridge",
                        s.open_time,
                        s.signal_time,
                        s.forecast,
                        pins["forecast_csv"],
                    )
                    for s in accounts[symbol, "ridge"]
                )
            )
        # Require a bounded, already projected sequence, never materialise a native
        # million-row iterator. No sorting/deduplication of supplied source rows.
        require(
            type(minute_projection) in (tuple, list),
            "Expected bounded projection sequence.",
        )
        times = sorted(
            {START + i * HOUR for i in range((end - START) // HOUR)}
            | {next_minute_at(s.feature_available_at) for s in forecasts[0]}
        )
        require(
            len(minute_projection) == 2 * len(times),
            "Incomplete/extra minute projection.",
        )
        require(
            projection_sha256(minute_projection) == snapshots["projection"],
            "Projection changed after TEST snapshot pinning.",
        )
        references, sources = [], []
        for index, symbol in enumerate(SYMBOLS):
            refs = tuple(
                minute_projection[index * len(times) : (index + 1) * len(times)]
            )
            source = SyntheticPriceSource(
                60,
                pins["minute_manifest"],
                pins["minute_csv"],
                monthly,
                projection_sha256(refs),
            )
            validate_price_projection(
                refs,
                source,
                interval_seconds=60,
                expected_source_sha256=price_source_sha256(source),
            )
            require(
                all(
                    r.symbol == symbol and r.at == at
                    for r, at in zip(refs, times, strict=True)
                ),
                "Wrong market/missing/duplicate/reordered required minute.",
            )
            references.append(refs)
            sources.append(source)
        retained = json_bytes(
            {
                "evidence": evidence,
                "forecast_manifest": forecast_manifest,
                "minute_metadata": minute_metadata,
                "parity_evidence": parity_evidence,
                "authentication": AUTHENTICATION,
                "genuine_execution_authorised": False,
                "genuine_timing_comparison_authorised": False,
            }
        )
        return PreparedMinuteBundle(
            tuple(tuple(accounts[k]) for k in ACCOUNT_KEYS),
            tuple(forecasts),
            tuple(references),
            tuple(sources),
            end,
            retained,
        )
    except (KeyError, TypeError, IndexError, AttributeError, OverflowError) as error:
        raise ValueError("Malformed synthetic integration evidence.") from error


def validate_minute_integration(bundle, *, expected_evidence_sha256) -> None:
    """Recheck every input against retained TEST pins; hashes grant no approval."""
    require(
        type(bundle) is PreparedMinuteBundle
        and bundle.status == "synthetic_test"
        and bundle.authentication == AUTHENTICATION,
        "Permission gate: expected synthetic prepared inputs.",
    )
    require(
        type(bundle.source_evidence_json) is bytes, "Immutable evidence bytes required."
    )
    try:
        retained = json.loads(bundle.source_evidence_json)
        pins = retained["evidence"]["pins"]
        require(
            type(bundle.accounts) is tuple and len(bundle.accounts) == 8,
            "Expected immutable eight-account collection.",
        )
        forecast_result = (
            {
                "manifest.json": pins["forecast_manifest"],
                "validation_predictions.csv": pins["forecast_csv"],
            },
            dict(zip(ACCOUNT_KEYS, bundle.accounts, strict=True)),
        )
        rebuilt = adapt_minute_inputs(
            forecast_result,
            retained["forecast_manifest"],
            retained["minute_metadata"],
            tuple(r for refs in bundle.references for r in refs),
            retained["parity_evidence"],
            evidence=retained["evidence"],
            expected_evidence_sha256=expected_evidence_sha256,
        )
        require(bundle == rebuilt, "Prepared records, status or provenance changed.")
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError("Malformed prepared integration bundle.") from error

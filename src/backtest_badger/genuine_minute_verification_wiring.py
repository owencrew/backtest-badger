"""Non-executing production binding plan and NOT_APPROVED evidence template.

No dispatcher, approval constructor, path reader or genuine invocation exists.
Names below are declarations, never dynamically imported/resolved call targets.
Only explicitly supplied, hash-pinned tracked-document bytes may be parsed.
"""

from dataclasses import dataclass, field
from hashlib import sha256

PIN_DOCUMENT = "docs/stage-04b2c-minute-source-pins.md"
DECLARATIONS = (
    (
        "forecast_manifest",
        "af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581",
    ),
    (
        "forecast_csv",
        "e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674",
    ),
    (
        "research_manifest",
        "a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e",
    ),
    (
        "research_csv",
        "04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8",
    ),
    (
        "hourly_manifest",
        "1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d",
    ),
    ("hourly_csv", "39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a"),
    (
        "hourly_acquisition",
        "926697a89eb7c018ca5913f1e3c4c1170715db5639d444a58a78012e92aec055",
    ),
    (
        "minute_manifest",
        "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127",
    ),
    ("minute_csv", "37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233"),
    (
        "parity_manifest",
        "53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d",
    ),
    (
        "parity_report",
        "0d0bdb2901ecf9c18d4bf7511ba8220f088082b9d4f0005549b99b484ad2f5fb",
    ),
    (
        "parity_provenance",
        "fb44c49bf468ca976706567f7997ff61cdfe3f5157eca387c796b73fba0556eb",
    ),
    (
        "parity_integrity",
        "5594e11f44cbc0e820595501a508b47f6f7b55508de3c2895c7b6ae6e64ab395",
    ),
    (
        "parity_discrepancies",
        "0afb86f6389a1ab6a6931f0a96bd3ef0484bbd172f8bcd8b2fc7b8e9dea4a755",
    ),
    (
        "minute_pin_document",
        "967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c",
    ),
    (
        "hourly_protocol",
        "b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b",
    ),
    (
        "minute_protocol",
        "c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b",
    ),
)
ROOTS = (
    ("forecast", "artifacts/experiments/stage-2b-v1"),
    ("minute", "artifacts/execution/binance-1m-2024-v1"),
    ("parity", "artifacts/audits/stage-04b2d1-native-parity-v1"),
)
DESTINATION = "artifacts/audits/stage-04b2d3-minute-inputs-v1"
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
# Exact proposed closure, not hashes of the current candidate and not an approval.
# Tests check this against the unchanged operator and transitive project imports.
IMPLEMENTATION_FILES = tuple(
    sorted(
        (
            *(
                f"src/backtest_badger/{name}.py"
                for name in (
                    "__init__",
                    "archives",
                    "candles",
                    "config",
                    "db",
                    "execution_data",
                    "features",
                    "forecast_data",
                    "frozen",
                    "genuine_minute_inputs",
                    "genuine_minute_price_parity",
                    "genuine_minute_verification_operator",
                    "genuine_minute_verification_wiring",
                    "history",
                    "ingestion",
                    "minute_execution_data",
                    "minute_price_parity",
                    "model_data",
                    "paper_accounting",
                    "paper_execution",
                    "paper_historical",
                    "paper_historical_evaluation",
                    "paper_minute_historical",
                    "paper_strategy",
                    "paper_types",
                    "research",
                )
            ),
            "docs/stage-04b2-historical-validation-protocol.md",
            "docs/stage-04b2c-minute-execution-protocol.md",
            "docs/stage-04b2c-minute-data-engineering.md",
            PIN_DOCUMENT,
            "docs/stage-04b2d1-genuine-price-parity-audit.md",
            "docs/stage-04b2d3-genuine-minute-input-authentication.md",
            "docs/stage-04b2d4-genuine-verification-operator.md",
            "docs/stage-04b2d5-genuine-verification-wiring.md",
            "AGENTS.md",
            ".python-version",
            ".github/workflows/ci.yml",
            "pyproject.toml",
            "uv.lock",
        )
    )
)


@dataclass(frozen=True)
class Binding:
    """Symbolic argument names and literal keyword values; never callables."""

    role: str
    target: str
    arguments: tuple[str, ...]
    literal_keywords: tuple[tuple[str, str | int], ...] = ()


@dataclass(frozen=True)
class VerificationPlan:
    bindings: tuple[Binding, ...]
    roots: tuple[tuple[str, str], ...] = ROOTS
    destination: str = DESTINATION
    implementation_files: tuple[str, ...] = IMPLEMENTATION_FILES
    future_source_kind: str = "genuine_retained_stage2b_native_minute_prior_parity"
    result_type: str = "backtest_badger.genuine_minute_inputs.AuthenticatedMinuteInputs"
    execution_authorised: bool = field(default=False, init=False)
    executable: bool = field(default=False, init=False)
    required_flags: tuple[tuple[str, bool], ...] = (
        ("verification_only", True),
        ("single_attempt", True),
        ("resume", False),
        ("strategy_authorised", False),
        ("economic_publication_authorised", False),
    )
    phases: tuple[str, ...] = (
        "validate_and_detach_external_approval",
        "check_code_runtime_clean_revision_and_symlink_free_absent_destination",
        "reserve_sole_destination_consuming_attempt_before_source_opens",
        "verify_exact_external_57_file_inventory_forecast_named_files_only",
        "validate_lineage_forecasts_native_archives_full_projection_prior_publication",
        "recheck_sources_code_runtime",
        "exclusive_fsynced_science_then_integrity_and_canonical_readback",
        "recheck_sources_code_runtime_before_manifest",
        "exclusive_manifest_last_readback_and_final_preservation",
        "on_failure_keep_forensics_invalidate_only_owned_manifest_never_retry",
    )


def verification_plan() -> VerificationPlan:
    """Describe the future bindings without importing any project operator."""
    prefix = "backtest_badger."
    return VerificationPlan(
        (
            Binding(
                "forecast_loader",
                prefix + "forecast_data.load_forecasts",
                ("approved_forecast_root",),
            ),
            Binding(
                "lineage_validator",
                prefix + "paper_historical_evaluation._validate_lineage",
                ("original_forecast_manifest",),
            ),
            Binding(
                "minute_loader",
                prefix + "minute_execution_data.load_minute_execution_data",
                ("approved_minute_root",),
                (("expected_manifest_sha256", dict(DECLARATIONS)["minute_manifest"]),),
            ),
            Binding(
                "projection",
                prefix + "genuine_minute_inputs._stream_projection",
                ("approved_minute_csv", "externally_pinned_monthly_sources"),
                (
                    ("expected_sha256", dict(DECLARATIONS)["minute_csv"]),
                    ("expected_bytes", 107002277),
                ),
            ),
            Binding(
                "prior_publication",
                prefix + "genuine_minute_inputs._parity_evidence",
                (
                    "original_five_file_bodies",
                    "original_external_pins",
                    "externally_pinned_monthly_sources",
                    "retained_audit_code",
                    "retained_hourly_monthly",
                    "verified_minute_metadata",
                ),
            ),
        )
    )


@dataclass(frozen=True)
class SourceDeclaration:
    group: str
    name: str
    sha256: str | None
    bytes: int | None
    declaration_source: str


@dataclass(frozen=True)
class Readiness:
    """A checklist, deliberately incompatible with the operator approval schema."""

    sources: tuple[SourceDeclaration, ...]
    monthly_sources: tuple[tuple[str, str, tuple[tuple[str, str | int], ...]], ...]
    missing_evidence: tuple[str, ...]
    declarations: tuple[tuple[str, str], ...] = DECLARATIONS
    dependencies: tuple[str, ...] = DEPENDENCIES
    status: str = field(default="NOT_APPROVED", init=False)
    readiness: str = field(default="NOT_READY", init=False)
    access: str = field(default="NO_SOURCE_ACCESS", init=False)


def approval_readiness(*, minute_pin_document: bytes | None = None) -> Readiness:
    """Build an unapprovable checklist from declarations, optionally a frozen doc.

    There is intentionally no candidate approval, path, code/CI/runtime observation
    or owner-consent argument. Unknown evidence cannot be supplied/self-pinned here.
    The document parameter is its already-read tracked bytes, never an artifact.
    The existing pure table parser is reused only AFTER the literal hash check.
    No source file's presence, length or contents is observed by this function.
    """
    pins = dict(DECLARATIONS)
    monthly = {}
    if minute_pin_document is not None:
        if type(minute_pin_document) is not bytes:
            raise TypeError("Expected frozen tracked-document bytes.")
        if sha256(minute_pin_document).hexdigest() != pins["minute_pin_document"]:
            raise ValueError("Frozen tracked-document identity mismatch.")
        # No operator import or invocation; this parser only consumes supplied bytes.
        from backtest_badger.genuine_minute_price_parity import _minute_pins

        monthly = _minute_pins(minute_pin_document)
    sources = [
        SourceDeclaration(group, name, pins[key], size, origin)
        for group, name, key, size, origin in (
            (
                "forecast",
                "manifest.json",
                "forecast_manifest",
                None,
                "forecast_data.py",
            ),
            (
                "forecast",
                "validation_predictions.csv",
                "forecast_csv",
                None,
                "forecast_data.py",
            ),
            ("minute", "manifest.json", "minute_manifest", 19749, PIN_DOCUMENT),
            ("minute", "minute_opens.csv", "minute_csv", 107002277, PIN_DOCUMENT),
            ("parity", "manifest.json", "parity_manifest", 740, "Stage 4B.2D.1 guide"),
            (
                "parity",
                "parity_report.json",
                "parity_report",
                18452,
                "Stage 4B.2D.1 guide",
            ),
            (
                "parity",
                "provenance.json",
                "parity_provenance",
                60610,
                "Stage 4B.2D.1 guide",
            ),
            (
                "parity",
                "integrity.json",
                "parity_integrity",
                61684,
                "Stage 4B.2D.1 guide",
            ),
            (
                "parity",
                "discrepancies.csv",
                "parity_discrepancies",
                162,
                "Stage 4B.2D.1 guide",
            ),
        )
    ]
    for symbol in ("BTCUSDT", "ETHUSDT"):
        for month in range(1, 13):
            label = f"2024-{month:02d}"
            row = monthly.get((symbol, label), {})
            for suffix, hash_key, size_key in (
                ("", "sha256", "zip_bytes"),
                (".CHECKSUM", "checksum_sha256", "checksum_bytes"),
            ):
                sources.append(
                    SourceDeclaration(
                        "minute",
                        f"raw/{symbol}-1m-{label}.zip{suffix}",
                        row.get(hash_key),
                        row.get(size_key),
                        f"{PIN_DOCUMENT}:{symbol}:{label}",
                    )
                )
    missing = (
        "separately_reviewed_genuine_enabled_source_change",
        "clean_full_reviewed_future_commit",
        "independently_checked_successful_ci_for_that_exact_commit",
        "independently_retained_transitive_code_document_config_hashes_and_lengths",
        "validated_import_closure_at_future_revision",
        "exact_run_boundary_python_implementation_and_dependency_versions",
        "externally_retained_forecast_manifest_byte_length",
        "externally_retained_forecast_csv_byte_length",
        "independent_retention_of_complete_57_file_source_inventory",
        "independent_retention_of_ordered_monthly_identities_urls_grids_and_receipts",
        "independently_retained_hourly_monthly_and_complete_prior_auditor_identities",
        "exact_absolute_roots_and_destination_for_approved_checkout",
        "expressly_approved_destination_absence_ignore_and_symlink_preflight",
        "owner_one_read_only_attempt_authorisation_after_enabled_code_review_and_ci",
    )
    if minute_pin_document is None:
        missing += ("hash_verified_tracked_minute_pin_document_tables",)
    return Readiness(
        tuple(sorted(sources, key=lambda row: (row.group, row.name))),
        tuple((s, m, tuple(row.items())) for (s, m), row in monthly.items()),
        missing,
    )

"""Verified-record replay integration exercised ONLY with invented records.

The public genuine route always refuses. No publication reader, signing, paths,
loaders or writer exists here. Private fixtures test conversion/accounting, not
source authenticity. Python records and fingerprints are not security capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256

from backtest_badger import genuine_minute_inputs as auth
from backtest_badger import paper_minute_historical as minute
from backtest_badger.paper_accounting import Account, fund_account
from backtest_badger.paper_historical import HistoricalDecision, HistoricalForecast
from backtest_badger.paper_types import STEP, Portfolio, digest, number, require, utc

FIXTURE_KIND = "fabricated_verified_input_minute_replay"
FIXTURE_STATUS = "fabricated_records_only_not_genuine_results"


def replay_genuine_minute_historical(*, approval):
    """Closed before argument inspection: exact-publication ingestion is absent.

    Verification approval, a dataclass, manifest, flag or status cannot grant
    strategy authority. A separately reviewed reader AND execution approval are
    required in a later stage; the existing verification approval is never reused.
    """
    raise PermissionError("Genuine publication ingestion and replay remain closed.")


@dataclass(frozen=True)
class _FixtureDeclarations:
    """Independent TEST declarations, retained before passing invented records."""

    inputs_sha256: str
    forecast_sha256: str
    model_recipe_sha256: str
    minute_manifest_sha256: str
    minute_file_sha256: str
    monthly_sources: tuple[tuple[str, str, str], ...]
    projection_sha256: tuple[str, str]
    protocol_version: str
    protocol_sha256: str


@dataclass(frozen=True)
class _FixtureMinuteSource:
    symbol: str
    manifest_sha256: str
    file_sha256: str
    monthly_sources: tuple[tuple[str, str, str], ...]
    projected_sha256: str
    kind: str = field(default=FIXTURE_KIND, init=False)
    status: str = field(default=FIXTURE_STATUS, init=False)


@dataclass(frozen=True)
class _FixtureReplayInputs:
    original: auth.AuthenticatedMinuteInputs
    forecasts: tuple[tuple[HistoricalForecast, ...], ...]
    sources: tuple[_FixtureMinuteSource, ...]
    kind: str = field(default=FIXTURE_KIND, init=False)
    genuine_execution_authorised: bool = field(default=False, init=False)


@dataclass(frozen=True)
class _FixtureReplayResult:
    symbol: str
    source: _FixtureMinuteSource
    input_sha256: str
    forecast_sha256: str
    model_recipe_sha256: str
    decisions: tuple[HistoricalDecision, ...]
    accounts: tuple[minute.MinuteAccount, ...]
    end_exclusive: datetime = field(default=minute.END, init=False)
    protocol_version: str = field(default=minute.PROTOCOL_VERSION, init=False)
    protocol_sha256: str = field(default=minute.PROTOCOL_SHA256, init=False)
    kind: str = field(default=FIXTURE_KIND, init=False)
    status: str = field(default=FIXTURE_STATUS, init=False)
    authentication: str = field(
        default="fabricated_records_not_source_authentication", init=False
    )
    genuine_execution_authorised: bool = field(default=False, init=False)
    economic_results: bool = field(default=False, init=False)


def _validate_fixture_declarations(declarations):
    require(
        type(declarations) is _FixtureDeclarations,
        "Private fixture declarations required.",
    )
    require(
        declarations.protocol_version == minute.PROTOCOL_VERSION
        and declarations.protocol_sha256 == minute.PROTOCOL_SHA256,
        "Frozen minute protocol mismatch.",
    )
    require(
        type(declarations.projection_sha256) is tuple
        and len(declarations.projection_sha256) == 2,
        "Two immutable projection pins required.",
    )
    for value in (
        declarations.inputs_sha256,
        declarations.forecast_sha256,
        declarations.model_recipe_sha256,
        declarations.minute_manifest_sha256,
        declarations.minute_file_sha256,
        *declarations.projection_sha256,
    ):
        digest(value)
        require(
            value not in auth.EXTERNAL_PINS.values(),
            "Genuine source pin forbidden in fixture replay.",
        )
    require(
        type(declarations.monthly_sources) is tuple,
        "Immutable monthly sources required.",
    )
    expected = tuple((s, f"2024-{m:02d}") for s in minute.SYMBOLS for m in range(1, 13))
    require(
        len(declarations.monthly_sources) == len(expected), "24 monthly pins required."
    )
    for row, key in zip(declarations.monthly_sources, expected, strict=True):
        require(
            type(row) is tuple and len(row) == 3 and row[:2] == key,
            "Wrong monthly source order/identity.",
        )
        digest(row[2])


def _adapt_fixture_inputs(inputs, *, declarations) -> _FixtureReplayInputs:
    """Private in-memory, full-grid fixture seam; no genuine ingestion/authority.

    The independent whole-record pin includes original evidence bytes and ALL
    eight forecast accounts. Neither rehashing received data nor price parity
    authenticates an original publication. No prices reach the forecast converter.
    """
    _validate_fixture_declarations(declarations)
    require(
        type(inputs) is auth.AuthenticatedMinuteInputs, "Expected verified record type."
    )
    require(
        inputs.status == auth.STATUS and inputs.genuine_execution_authorised is False,
        "Verification record must remain non-authorising.",
    )
    require(type(inputs.source_evidence_json) is bytes, "Immutable evidence required.")
    evidence = auth._json(inputs.source_evidence_json)
    require(
        evidence["source_kind"]
        in (
            "fabricated_temporary_fixture_bytes",
            "synthetic_test_fabricated_signed_genuine_path",
        ),
        "Private replay requires fabricated evidence.",
    )
    require(
        sha256(auth.authenticated_inputs_json(inputs)).hexdigest()
        == declarations.inputs_sha256,
        "Verified records changed after pinning.",
    )
    pins = evidence["pins"]
    require(
        pins["forecast_csv"] == declarations.forecast_sha256
        and pins["forecast_manifest"] == declarations.model_recipe_sha256
        and pins["minute_manifest"] == declarations.minute_manifest_sha256
        and pins["minute_csv"] == declarations.minute_file_sha256
        and pins["minute_protocol"] == declarations.protocol_sha256
        and evidence["recipe_identity_kind"] == "stage2b_manifest_sha256"
        and evidence["recipe_sha256"] == declarations.model_recipe_sha256,
        "Independent source/recipe/protocol pin mismatch.",
    )
    require(
        type(inputs.projection_sha256) is tuple
        and inputs.projection_sha256 == declarations.projection_sha256
        and evidence["projection_sha256"] == list(declarations.projection_sha256),
        "Independent projection declarations disagree.",
    )
    monthly = evidence["monthly_sources"]
    require(
        type(monthly) is list and len(monthly) == 24, "Incomplete monthly provenance."
    )
    require(
        tuple((s, m, row["sha256"]) for s, m, row in monthly)
        == declarations.monthly_sources,
        "Monthly provenance mismatch.",
    )
    for name in ("genuine_execution_authorised", "economic_results"):
        require(
            evidence.get(name, False) is False,
            "Fixture evidence cannot grant authority.",
        )
    counts = evidence["counts"]
    require(
        all(
            type(counts.get(name)) is int and counts[name] == count
            for name, count in (
                ("forecast_accounts", 8),
                ("forecasts_per_account", 2195),
                ("native_rows", 1054080),
                ("hourly_marks_per_market", 8784),
                ("hypothetical_minutes_per_market", 2195),
                ("references", 21958),
            )
        ),
        "Wrong scientific counts.",
    )
    forecasts = _convert_verified_forecasts(
        inputs.forecasts, declarations.forecast_sha256
    )
    require(
        type(inputs.references) is tuple and len(inputs.references) == 2,
        "Two immutable reference streams required.",
    )
    marks_at = {minute.START + i * minute.HOUR for i in range(8784)}
    required = sorted(
        marks_at | {minute.START + i * STEP + 2 * minute.MINUTE for i in range(2195)}
    )
    monthly_pins = {(s, m): h for s, m, h in declarations.monthly_sources}
    sources = []
    for index, symbol in enumerate(minute.SYMBOLS):
        refs = inputs.references[index]
        require(
            type(refs) is tuple and len(refs) == 10979,
            "Full immutable minute union required.",
        )
        for ref, at in zip(refs, required, strict=True):
            require(type(ref) is minute.MinuteReference, "Expected native minute type.")
            ref.__post_init__()
            require(
                ref.symbol == symbol
                and ref.at == at
                and ref.file_sha256 == declarations.minute_file_sha256
                and ref.source_sha256 == monthly_pins[symbol, at.strftime("%Y-%m")],
                "Minute grid/market/file/month provenance mismatch.",
            )
        require(
            minute.projection_sha256(refs) == declarations.projection_sha256[index],
            "Minute projection changed.",
        )
        sources.append(
            _FixtureMinuteSource(
                symbol,
                declarations.minute_manifest_sha256,
                declarations.minute_file_sha256,
                tuple(row for row in declarations.monthly_sources if row[0] == symbol),
                declarations.projection_sha256[index],
            )
        )
    return _FixtureReplayInputs(inputs, forecasts, tuple(sources))


def _convert_verified_forecasts(accounts, forecast_sha256):
    """Pure structural conversion; the function/output grants no replay authority."""
    require(
        type(accounts) is tuple and len(accounts) == 8,
        "All eight immutable forecast accounts required.",
    )
    ridge = []
    for (symbol, model), records in zip(auth.ACCOUNT_KEYS, accounts, strict=True):
        require(
            type(records) is tuple and len(records) == 2195,
            "Exactly 2195 immutable forecasts per account required.",
        )
        converted = []
        for i, record in enumerate(records):
            require(type(record) is auth.VerifiedForecast, "Expected VerifiedForecast.")
            opened = minute.START - STEP + i * STEP
            available = opened + STEP + minute.MINUTE
            require(
                record.symbol == symbol
                and record.model == model
                and utc(record.source_open) == opened
                and utc(record.assumed_available_at) == available
                and utc(record.hypothetical_minute_at)
                == minute.next_minute_at(available)
                and record.record_id
                == f"binance:spot:{symbol}:14400:{opened.isoformat()}:{model}"
                and record.file_sha256 == forecast_sha256,
                "Forecast identity/grid/availability/CSV pin mismatch.",
            )
            number(record.prediction)
            if model == "zero":
                require(record.prediction == 0, "Invalid zero baseline.")
            if model == "ridge":
                converted.append(
                    HistoricalForecast(
                        record.symbol,
                        record.record_id,
                        record.source_open,
                        record.assumed_available_at,
                        record.prediction,
                        record.file_sha256,
                    )
                )
        if model == "ridge":
            ridge.append(tuple(converted))
    return tuple(ridge)


def _replay_fixture_inputs(inputs, *, declarations) -> tuple[_FixtureReplayResult, ...]:
    """PRIVATE invented-record replay only; fixed full-year policy, no overrides."""
    bundle = _adapt_fixture_inputs(inputs, declarations=declarations)
    results = []
    for index, symbol in enumerate(minute.SYMBOLS):
        # Reuse exactly the existing price-free planner and monetary loop.
        plan = minute._plan(
            symbol,
            bundle.forecasts[index],
            (),
            minute.END,
            declarations.forecast_sha256,
        )
        initial = {}
        for label in ("ridge", "cash", "buy_and_hold"):
            portfolio = Portfolio(
                f"{FIXTURE_KIND}:{symbol}:{label}",
                symbol,
                minute.START,
                sha256(minute.PROTOCOL_VERSION.encode()).hexdigest(),
                minute.PROTOCOL_SHA256,
                declarations.model_recipe_sha256,
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
        results.append(
            _FixtureReplayResult(
                symbol,
                bundle.sources[index],
                declarations.inputs_sha256,
                declarations.forecast_sha256,
                declarations.model_recipe_sha256,
                decisions,
                accounts,
            )
        )
    return tuple(results)

"""Private fabricated-only replay/report handoff; no I/O or execution authority.

The test author retains producer fingerprints BEFORE handing records to reporting.
Same-process retention is structural consistency, never a security capability.
"""

import json
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import Literal

from backtest_badger import genuine_backtest_preparation as preparation
from backtest_badger import genuine_minute_publication as publication
from backtest_badger import paper_minute_historical as minute
from backtest_badger import paper_minute_reporting as reporting
from backtest_badger.paper_types import INITIAL_CASH, digest, require

_SCHEMA = "stage-04b2e5c-fabricated-economic-evidence-v1"
_LIMIT = 128 * 1024 * 1024
_LABELS = ("ridge", "cash", "buy_and_hold")
_LIMITATIONS = (
    "Entirely invented inputs and hypothetical TEST arithmetic; no real profits.",
    "Historical authenticity is not proven by structural consistency.",
    "Independent fingerprint retention is a caller obligation, not proven here.",
    "Same-process private records are not security capabilities or authority.",
    "Upstream source/sign-off claims are fabricated, not fresh source audits.",
    "Availability is assumed; archive opens are not executable quotes or fills.",
    "Final day/month returns are partial; no 2025 price or terminal liquidation.",
    "Market portfolios and daily/monthly alternative aggregations stay separate.",
    "E.5 raw transport remains TEST-only with accounting NOT_PERFORMED.",
)


@dataclass(frozen=True)
class _TestFlags:
    fabricated_only: Literal[True] = field(default=True, init=False)
    execution_authorised: Literal[False] = field(default=False, init=False)
    economic_publication: Literal[False] = field(default=False, init=False)
    source_authentication_proven: Literal[False] = field(default=False, init=False)


@dataclass(frozen=True)
class _FabricatedReplay(_TestFlags):
    publication: publication._VerifiedPublication
    signoff: publication._ReconciledSignoff
    results: tuple[publication._PublicationReplayResult, ...]


@dataclass(frozen=True)
class _AccountPin:
    account_id: str
    fingerprint: str


@dataclass(frozen=True)
class _HandoffPins:
    replay_sha256: str
    accounts: tuple[_AccountPin, ...]


@dataclass(frozen=True)
class _FabricatedReport(_TestFlags):
    # Immutable canonical bytes from the checked reporting boundary. A decoder
    # needs this retained context as well as a separately retained export hash.
    canonical: bytes


def _bounded_json(value: object) -> bytes:
    """Bound work before using the shared scientific encoder (no cyclic walk)."""
    pending = [(value, 0)]
    nodes = 0
    characters = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        require(depth <= 32 and nodes <= 8_000_000, "Evidence traversal limit.")
        if is_dataclass(item) and not isinstance(item, type):
            pending.extend((getattr(item, f.name), depth + 1) for f in fields(item))
        elif type(item) is dict:
            require(len(item) <= 100_000, "Evidence mapping limit.")
            require(all(type(k) is str for k in item), "String keys required.")
            pending.extend((v, depth + 1) for v in item.values())
            pending.extend((k, depth + 1) for k in item)
        elif type(item) in (tuple, list):
            require(len(item) <= 100_000, "Evidence sequence limit.")
            pending.extend((v, depth + 1) for v in item)
        elif isinstance(item, str):
            characters += len(item)
            require(len(item) <= 1_048_576, "Evidence string limit.")
        elif type(item) is int:
            require(abs(item) < 2**63, "Evidence integer limit.")
        else:
            require(
                item is None or isinstance(item, (bool, int, Decimal, datetime)),
                "Unsupported evidence type.",
            )
        require(characters <= _LIMIT, "Evidence character limit.")
    body = minute.scientific_json(value).encode("ascii")
    require(len(body) <= _LIMIT, "Evidence byte limit.")
    return body


def _flags(value: _TestFlags) -> None:
    require(
        value.fabricated_only is True
        and value.execution_authorised is False
        and value.economic_publication is False
        and value.source_authentication_proven is False,
        "Fabricated-only flags required.",
    )


def _prepare_fabricated_replay(
    *,
    manifest: bytes,
    authenticated_inputs: bytes,
    integrity: bytes,
    signoff: bytes,
    expected: publication._PublicationPins,
    fabricated_only: Literal[True],
) -> _FabricatedReplay:
    require(fabricated_only is True, "Explicit fabricated-only declaration required.")
    require(
        type(expected) is publication._PublicationPins, "Publication pins required."
    )
    for name, limit in zip(
        preparation.PIN_NAMES, (*publication.LIMITS, 1024 * 1024), strict=True
    ):
        publication._fingerprint(getattr(expected, name), limit)
    historical = {v["sha256"] for v in preparation.HISTORICAL_PINS.values()}
    require(
        all(
            getattr(expected, name).sha256 not in historical
            for name in preparation.PIN_NAMES
        ),
        "Historical publication identities forbidden in TEST integration.",
    )
    parsed = publication._parse_verified_publication(
        manifest=manifest,
        authenticated_inputs=authenticated_inputs,
        integrity=integrity,
        expected=expected,
        signoff_claim=expected.signoff,
    )
    evidence = json.loads(parsed.inputs.source_evidence_json)
    recipe = evidence["forecast_manifest"]
    require(
        recipe["test_policy"] == "fabricated metadata only"
        and recipe["limitations"] == "fabricated full-year test",
        "Explicit fabricated recipe markers required; no genuine evidence.",
    )
    real_data = {
        pin
        for name, pin in publication.auth.EXTERNAL_PINS.items()
        if name not in ("hourly_protocol", "minute_protocol", "minute_pin_document")
    }
    require(
        not real_data.intersection(evidence["pins"].values()),
        "Historical data identities forbidden in TEST integration.",
    )
    reconciled = publication._validate_independent_signoff(
        signoff=signoff,
        expected_signoff=expected.signoff,
        publication=parsed,
        expected=expected,
    )
    results = publication._replay_verified_publication(
        reconciled.publication,
        expected=expected,
        signoff_claim=expected.signoff,
    )
    return _FabricatedReplay(parsed, reconciled, results)


def _replay_evidence(value: _FabricatedReplay) -> dict:
    require(type(value) is _FabricatedReplay, "Fabricated producer envelope required.")
    _flags(value)
    require(
        type(value.publication) is publication._VerifiedPublication,
        "Parsed publication required.",
    )
    require(
        type(value.signoff) is publication._ReconciledSignoff,
        "Reconciled sign-off required.",
    )
    require(
        value.signoff.publication == value.publication, "Sign-off/publication changed."
    )
    # Frozen dataclasses are not proof of parsing. Reconcile retained bytes and
    # pins again before consuming caller-visible converted records.
    publication._validate_independent_signoff(
        signoff=value.signoff.body,
        expected_signoff=value.publication.pins.signoff,
        publication=value.publication,
        expected=value.publication.pins,
    )
    require(
        type(value.results) is tuple and len(value.results) == 2,
        "Two ordered markets required.",
    )
    for index, result in enumerate(value.results):
        require(
            type(result) is publication._PublicationReplayResult,
            "Publication replay type required.",
        )
        require(result.symbol == minute.SYMBOLS[index], "Market order changed.")
        require(
            type(result.accounts) is tuple
            and tuple(a.label for a in result.accounts) == _LABELS
            and type(result.decisions) is tuple
            and len(result.decisions) == 2195
            and len(value.publication.inputs.references[index]) == 10979
            and result.end_exclusive == minute.END,
            "Frozen replay counts/order/endpoint changed.",
        )
        require(
            type(result.source) is publication._PublicationMinuteSource
            and result.source.symbol == result.symbol
            and result.source.publication == value.publication.pins
            and result.kind == publication.KIND
            and result.protocol_version == minute.PROTOCOL_VERSION
            and result.protocol_sha256 == minute.PROTOCOL_SHA256,
            "Replay source/protocol association changed.",
        )
        for account in result.accounts:
            require(type(account) is minute.MinuteAccount, "MinuteAccount required.")
            require(
                account.initial.cash == INITIAL_CASH, "Independent funding changed."
            )
    evidence = json.loads(value.publication.inputs.source_evidence_json)
    # Only parser-checked identities, never recipe free text, approval, roots,
    # operational snapshots, credentials or arbitrary source metadata.
    sources = {
        name: evidence[name] for name in ("pins", "original_files", "code_sha256")
    }
    return {
        "publication_pins": value.publication.pins,
        "publication_claims": json.loads(value.publication.bodies[0]),
        "signoff_claims": json.loads(value.signoff.body),
        "source_identities": sources,
        "forecasts": value.publication.inputs.forecasts,
        "references": value.publication.inputs.references,
        "projection_sha256": value.publication.inputs.projection_sha256,
        "results": value.results,
    }


def _retain_fabricated_handoff(value: _FabricatedReplay) -> _HandoffPins:
    """PRODUCER operation. Retain separately before report receipt or mutations."""
    body = _bounded_json(_replay_evidence(value))
    return _HandoffPins(
        sha256(body).hexdigest(),
        tuple(
            _AccountPin(
                account.initial.portfolio.key,
                reporting.minute_reporting_fingerprint(
                    account,
                    end_exclusive=minute.END,
                ),
            )
            for result in value.results
            for account in result.accounts
        ),
    )


def _report_fabricated_replay(
    value: _FabricatedReplay,
    *,
    expected: _HandoffPins,
) -> _FabricatedReport:
    """Consumer: never derive expected pins from the received accounts."""
    require(
        type(expected) is _HandoffPins, "Separately retained handoff pins required."
    )
    digest(expected.replay_sha256)
    require(
        type(expected.accounts) is tuple and len(expected.accounts) == 6,
        "Six account pins required.",
    )
    evidence = _replay_evidence(value)
    require(
        sha256(_bounded_json(evidence)).hexdigest() == expected.replay_sha256,
        "Retained replay handoff mismatch (not upstream authentication).",
    )
    reports = []
    accounts = tuple(a for r in value.results for a in r.accounts)
    require(
        len({a.initial.portfolio.key for a in accounts}) == 6,
        "Independent account identities required.",
    )
    for account, pin in zip(accounts, expected.accounts, strict=True):
        require(type(pin) is _AccountPin, "Typed account pin required.")
        require(
            account.initial.portfolio.key == pin.account_id,
            "Account pin order/identity mismatch.",
        )
        minute.verify_minute_account(account, end_exclusive=minute.END)
        summary = reporting.minute_reporting_summary(
            account,
            end_exclusive=minute.END,
            expected_fingerprint=pin.fingerprint,
        )
        native = minute.minute_account_summary(account, end_exclusive=minute.END)
        require(
            summary["performance"]
            == (native if account.status == "available" else None),
            "Native/report accounting mismatch.",
        )
        if account.status == "available":
            for side, costs in native["costs_by_side"].items():
                reported = summary["costs_by_side"][side]
                for name, report_name in (
                    ("count", "count"),
                    ("notional", "notional"),
                    ("fees", "fees"),
                    ("half_spread", "hypothetical_half_spread"),
                    ("slippage", "hypothetical_slippage"),
                ):
                    require(
                        costs[name] == reported[report_name],
                        "Minute-fill costs differ.",
                    )
        report = {
            "account_id": pin.account_id,
            "account_fingerprint": pin.fingerprint,
            "replay_fingerprint": expected.replay_sha256,
            "ledger_verification": (
                "unchanged_minute_verifier_passed_on_fabricated_records"
            ),
            "fingerprint_status": (
                "matches_separately_supplied_pin_independence_not_proven"
            ),
            "signed_ledger": minute.minute_ledger_records(account),
            "summary": summary,
        }
        reports.append(
            {**report, "report_id": sha256(_bounded_json(report)).hexdigest()}
        )
    return _FabricatedReport(
        _bounded_json(
            {
                "schema": _SCHEMA,
                "fabricated_only": True,
                "execution_authorised": False,
                "economic_publication": False,
                "source_authentication_proven": False,
                "external_independence_proven": False,
                "accounting_status": "verified_fabricated_records_only",
                "handoff_pins": expected,
                "protocol": preparation.PROTOCOL,
                "method": preparation.METHOD,
                "evidence": evidence,
                "reports": reports,
                "limitations": _LIMITATIONS,
            }
        )
    )


def _encode_test_report(value: _FabricatedReport) -> bytes:
    require(type(value) is _FabricatedReport, "Retained fabricated report required.")
    _flags(value)
    require(
        type(value.canonical) is bytes and 0 < len(value.canonical) <= _LIMIT,
        "Bounded report bytes required.",
    )
    return value.canonical


def _decode_test_report(
    body: bytes,
    *,
    expected_sha256: str,
    retained: _FabricatedReport,
) -> dict:
    """Context-bound lossless decode, NOT standalone certification of JSON.

    Equality to the retained checked report enforces its entire closed schema,
    scalar types, report identities and exact Decimal strings. Both this context
    and the export hash must be retained before mutation, not made from a candidate.
    """
    digest(expected_sha256)
    require(
        type(body) is bytes and 0 < len(body) <= _LIMIT,
        "Bounded report bytes required.",
    )
    require(
        sha256(body).hexdigest() == expected_sha256,
        "Retained TEST export hash mismatch.",
    )
    require(
        body == _encode_test_report(retained),
        "Retained verified report/schema mismatch.",
    )
    try:
        value = json.loads(body)
        publication._fields(
            value,
            (
                "schema",
                "fabricated_only",
                "execution_authorised",
                "economic_publication",
                "source_authentication_proven",
                "external_independence_proven",
                "accounting_status",
                "handoff_pins",
                "protocol",
                "method",
                "evidence",
                "reports",
                "limitations",
            ),
        )
        require(
            type(value) is dict and value.get("schema") == _SCHEMA,
            "Wrong TEST report schema.",
        )
        require(
            value["fabricated_only"] is True
            and all(
                value[name] is False
                for name in (
                    "execution_authorised",
                    "economic_publication",
                    "source_authentication_proven",
                    "external_independence_proven",
                )
            ),
            "TEST-only report flags required.",
        )
        for name, declaration in (
            ("protocol", preparation.PROTOCOL),
            ("method", preparation.METHOD),
            ("limitations", _LIMITATIONS),
        ):
            require(
                _bounded_json(value[name]) == _bounded_json(declaration),
                "Changed report declaration.",
            )
        require(
            value["accounting_status"] == "verified_fabricated_records_only",
            "Wrong accounting status.",
        )
        require(
            type(value["reports"]) is list and len(value["reports"]) == 6,
            "Six reports required.",
        )
        require(_bounded_json(value) == body, "Noncanonical TEST report.")
        return value
    except (RecursionError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Malformed TEST report.") from error

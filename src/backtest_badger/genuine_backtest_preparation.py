"""E.5 inert contract and TEST-only evidence encoding; no runner or I/O.

All trust inputs below are *claims*. Structural agreement never proves external
independence, owner consent, CI success, file freshness or accounting correctness.
The state machine models future requirements; it consumes no actual authority.
"""

import json
import re
from dataclasses import fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from pathlib import PurePosixPath

SCHEMA = "stage-04b2e5-one-shot-candidate-v1"
EXPORT_SCHEMA = "stage-04b2e5-fabricated-evidence-v1"
OWNER = "OWNER_FILL_AFTER_SEPARATE_REVIEW"
TEST = "TEST_ONLY_fabricated_in_memory_not_authenticated"
START = datetime(2024, 1, 1, tzinfo=UTC)
END = datetime(2025, 1, 1, tzinfo=UTC)
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
LABELS = ["ridge", "cash", "buy_and_hold"]
KIND = "genuine_publication_hypothetical_minute_replay"
PIN_NAMES = ["manifest", "authenticated_inputs", "integrity", "signoff"]
# Declarations transcribed from E.2/E.3, never observed or opened here.
HISTORICAL_PINS = dict(
    zip(
        PIN_NAMES,
        [
            {
                "sha256": (
                    "3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea"
                ),
                "bytes": 560,
            },
            {
                "sha256": (
                    "2581482b4b8a60fa1a53f7710ed080be7de25d50a76fcae35c8aaf64f2cb2168"
                ),
                "bytes": 15272413,
            },
            {
                "sha256": (
                    "23c3d17b2e5b67de701d9a0dd22d6135a907057b9acaeb16bcbdb4cb9c613a8b"
                ),
                "bytes": 74200,
            },
            {
                "sha256": (
                    "21b04470e861a039750bf7b665b993d332bf998fcc5b9fea47dc2c8b80f334b4"
                ),
                "bytes": 2020,
            },
        ],
        strict=True,
    )
)
ORIGINAL_COMMIT = "94584dc4b08f06441cff3bcd7983bba1ca0afe8d"
PROTOCOL = {
    "version": "historical-minute-execution-v1",
    "sha256": "c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b",
}
METHOD = {
    "start_inclusive": "2024-01-01T00:00:00Z",
    "end_exclusive": "2025-01-01T00:00:00Z",
    "markets": SYMBOLS,
    "strategy": "ridge_sign",
    "threshold": "0.000000000001",
    "accounts": LABELS,
    "funding_each_usdt": "10000",
    "independent_portfolios": True,
    "availability": "source_open_plus_4h_plus_60s_assumed",
    "execution": "strictly_next_native_minute_12:01_to_12:02",
    "buy_and_hold_inception": "2024-01-01T00:00:00Z",
    "marks": "native_minute_HH:00_trade_before_mark",
    "last_mark": "2024-12-31T23:00:00Z",
    "fee_bps": 10,
    "half_spread_bps": 1,
    "adverse_slippage_bps": 2,
    "fee_quantum_round_up": "0.00000001",
    "quantity_step": "0.000001",
    "money": "Decimal_160_digits_Inexact_trapped",
    "ratios_and_wac": "Decimal_80_digits_HALF_EVEN",
    "sticky_exits": True,
    "ledger_prefix_checks": True,
    "forced_final_liquidation": False,
    "source_forecasts_per_market": 2195,
    "hourly_marks_per_available_account": 8784,
    "refit_reforecast_search": False,
    "research_status": "previously_inspected_exploratory_validation_not_untouched_OOS",
}
# Role closure, NOT a claim that the transitive dependency inventory is complete.
CLOSURE = {
    "public_guard": (
        "backtest_badger.genuine_minute_replay:replay_genuine_minute_historical"
    ),
    "private_parser": (
        "backtest_badger.genuine_minute_publication:_parse_verified_publication"
    ),
    "signoff_validator": (
        "backtest_badger.genuine_minute_publication:_validate_independent_signoff"
    ),
    "private_replay": (
        "backtest_badger.genuine_minute_publication:_replay_verified_publication"
    ),
    "planner": "backtest_badger.paper_minute_historical:_plan",
    "monetary_core": "backtest_badger.paper_minute_historical:_replay_minute_core",
    "ledger_check": "backtest_badger.paper_minute_historical:verify_minute_account",
    "minute_summary": "backtest_badger.paper_minute_historical:minute_account_summary",
    "accounting": "backtest_badger.paper_accounting",
    "types": "backtest_badger.paper_types",
    "strategy": "backtest_badger.paper_strategy:evaluate_strategy",
    "affordability": "backtest_badger.paper_execution:affordable_quantity",
    "historical_types": "backtest_badger.paper_historical",
    "authentication": "backtest_badger.genuine_minute_inputs",
    "historical_intent_schema": "backtest_badger.genuine_minute_signed_approval",
    "historical_integrity_schema": (
        "backtest_badger.genuine_minute_verification_operator"
    ),
    "preparation": "backtest_badger.genuine_backtest_preparation",
    "future_runner": OWNER,
    "future_reporter": OWNER,
}
METRICS = {
    "implemented_export": "lossless_evidence_and_counts_only_no_computed_metrics",
    "future_summary": "unchanged_minute_account_summary",
    "equity_and_pnl": (
        "retain_exact_marks_cash_quantity_basis_realised_unrealised_equity"
    ),
    "funding_return": "(last_observed_equity-10000)/10000",
    "drawdown": "funding_then_observed_hourly_reference_marks_only",
    "daily_monthly": "DEFERRED_minute_fill_cost_adapter_requires_review",
    "final_day": "2024-12-31_00:00_to_23:00_partial_exclude_complete_day_statistics",
    "december": "partial_one_hour_short_no_2025_endpoint_price",
    "flows": "actual_minute_fill_time_in_half_open_calendar_bucket",
    "inception_costs": "included_funding_return_precede_first_BH_mark_to_mark_return",
    "realised_unrealised_returns": "DEFERRED_no_new_return_metric_approved",
}
WARNINGS = [
    TEST,
    "Previously inspected exploratory 2024 validation; not untouched out-of-sample.",
    "Retrospective archive opens are not contemporaneous quotes or actual fills.",
    "No actual latency, liquidity, depth, market-impact or fillability evidence.",
    "No proof of profitability or tradable alpha; no portfolio aggregation.",
    "Structural validation proves neither external independence nor owner approval.",
    "Accounting verification and reporting integration remain future review gates.",
]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _fields(value, names):
    _require(type(value) is dict and set(value) == set(names), "Wrong exact fields")


def _json_value(value):
    if type(value) is dict:
        _require(all(type(k) is str for k in value), "String keys required")
        return {k: _json_value(v) for k, v in value.items()}
    if type(value) is list:
        return [_json_value(v) for v in value]
    _require(value is None or type(value) in (str, bool, int), "No floats/nonfinite")
    return value


def encode(value):
    """Canonical JSON bytes; no float, custom-object or implicit coercion path."""
    return (
        json.dumps(
            _json_value(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def decode(body):
    _require(
        type(body) is bytes and len(body) <= 128 * 1024 * 1024, "Bounded bytes required"
    )

    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def no_number(_):
        raise ValueError("No floats/nonfinite")

    try:
        result = json.loads(
            body,
            object_pairs_hook=pairs,
            parse_float=no_number,
            parse_constant=no_number,
        )
        _require(encode(result) == body, "Noncanonical encoding")
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("Invalid JSON encoding/depth") from exc
    return result


def identity(body):
    _require(type(body) is bytes, "Exact bytes required")
    return {"sha256": sha256(body).hexdigest(), "bytes": len(body)}


def _digest(value, length=64):
    _require(
        type(value) is str and re.fullmatch(f"[0-9a-f]{{{length}}}", value),
        "Invalid hash",
    )


def _pin(value):
    _fields(value, ("sha256", "bytes"))
    _digest(value["sha256"])
    _require(
        type(value["bytes"]) is int and 0 < value["bytes"] <= 128 * 1024 * 1024,
        "Invalid byte length",
    )


def _equal(value, expected, message):
    _require(encode(value) == encode(expected), message)


def candidate_contract():
    """Machine-readable inert template. Every unresolved identity stays explicit."""
    return decode(
        encode(
            {
                "schema": SCHEMA,
                "mode": "preparation_only",
                "execution_authorised": False,
                "historical": {
                    "pins": HISTORICAL_PINS,
                    "verification_commit": ORIGINAL_COMMIT,
                    "verification_ci_run": OWNER,
                    "published_flags": {
                        "genuine_execution_authorised": False,
                        "economic_results": False,
                    },
                    "identity_origin": "owner_retained_declarations_not_reverified",
                },
                "implementation": {
                    "checkout": OWNER,
                    "ci": {"run_id": OWNER, "commit": OWNER, "conclusion": "success"},
                    "roles": {
                        k: {"symbol": v, "file_identity": OWNER}
                        for k, v in CLOSURE.items()
                    },
                    "transitive_code_dependency_closure": OWNER,
                    "python": OWNER,
                    "lockfile": OWNER,
                    "pyproject": OWNER,
                },
                "protocol": PROTOCOL,
                "method": METHOD,
                "metrics": METRICS,
                "paths": {k: OWNER for k in PIN_NAMES},
                "output": {
                    "directory": OWNER,
                    "policy": "exclusive_fresh_no_overwrite_atomic_manifest_last",
                },
                "approval": {
                    "kind": "distinct_exact_payload_one_shot_owner_approval",
                    "payload": OWNER,
                    "validation": OWNER,
                },
                "attempt": {
                    "maximum": 1,
                    "resume": False,
                    "retry": False,
                    "persistence": "DEFERRED_durable_consume_before_computation",
                },
            }
        )
    )


def validate_candidate(body):
    """Only the frozen placeholder template is accepted; never execution authority."""
    _equal(decode(body), candidate_contract(), "Candidate differs from frozen template")
    return {
        "structurally_valid": True,
        "execution_authorised": False,
        "external_independence_proven": False,
    }


def _absolute(value):
    _require(
        type(value) is str
        and value.startswith("/")
        and not value.startswith("//")
        and "\x00" not in value,
        "Absolute POSIX path required",
    )
    path = PurePosixPath(value)
    _require(
        str(path) == value and value != "/" and ".." not in path.parts,
        "Canonical absolute path required",
    )
    return path


def validate_test_contract(body, *, expected_history, expected_implementation):
    """Filled fabricated specimen only. Expected claims are separately supplied.

    This is intentionally incapable of accepting a populated genuine contract.
    A later owner-approved runner must implement the real trust boundary.
    """
    value = decode(body)
    template = candidate_contract()
    _fields(value, template)
    _require(value["mode"] == TEST, "TEST-only contract required")
    for key in (
        "schema",
        "execution_authorised",
        "protocol",
        "method",
        "metrics",
        "attempt",
    ):
        _equal(value[key], template[key], "Frozen contract mismatch: " + key)
    historical = value["historical"]
    _fields(historical, template["historical"])
    _equal(historical, expected_history, "Historical external claim mismatch")
    _fields(historical["pins"], PIN_NAMES)
    genuine_hashes = {p["sha256"] for p in HISTORICAL_PINS.values()}
    for pin in historical["pins"].values():
        _pin(pin)
        _require(pin["sha256"] not in genuine_hashes, "Genuine pin forbidden in TEST")
    _digest(historical["verification_commit"], 40)
    _require(
        historical["verification_commit"] != ORIGINAL_COMMIT,
        "Historical authority reuse",
    )
    _require(
        re.fullmatch("[1-9][0-9]*", historical["verification_ci_run"] or ""),
        "Invalid historical CI",
    )
    _require(historical["identity_origin"] == TEST, "Fabricated provenance required")
    _equal(
        historical["published_flags"],
        template["historical"]["published_flags"],
        "Historical flags",
    )
    implementation = value["implementation"]
    _fields(implementation, template["implementation"])
    _equal(implementation, expected_implementation, "Implementation/CI claim mismatch")
    _digest(implementation["checkout"], 40)
    _require(
        implementation["checkout"] != historical["verification_commit"],
        "Identity substitution",
    )
    _fields(implementation["ci"], ("commit", "run_id", "conclusion"))
    _require(
        implementation["ci"]["commit"] == implementation["checkout"]
        and implementation["ci"]["conclusion"] == "success"
        and type(implementation["ci"]["run_id"]) is str
        and re.fullmatch("[1-9][0-9]*", implementation["ci"]["run_id"]),
        "Green exact-checkout CI required",
    )
    _fields(implementation["roles"], CLOSURE)
    for role, symbol in CLOSURE.items():
        row = implementation["roles"][role]
        _fields(row, ("symbol", "file_identity"))
        _require(
            row["symbol"] == ("TEST_ONLY:" + role if symbol == OWNER else symbol),
            "Role changed",
        )
        _pin(row["file_identity"])
    for key in ("transitive_code_dependency_closure", "lockfile", "pyproject"):
        _pin(implementation[key])
    _fields(implementation["python"], ("version", "executable", "dependencies"))
    _require(
        type(implementation["python"]["version"]) is str
        and re.fullmatch(r"3\.12\.[0-9]+", implementation["python"]["version"]),
        "Pinned Python 3.12 required",
    )
    for key in ("executable", "dependencies"):
        _pin(implementation["python"][key])
    _fields(value["paths"], PIN_NAMES)
    paths = [_absolute(value["paths"][k]) for k in PIN_NAMES]
    _require(len(set(paths)) == 4, "Four distinct paths required")
    _require(all(p.parts[1] == "TEST_ONLY" for p in paths), "Invented paths only")
    _fields(value["output"], template["output"])
    _require(
        value["output"]["policy"] == template["output"]["policy"],
        "Output policy changed",
    )
    output = _absolute(value["output"]["directory"])
    _require(
        output.parts[1] == "TEST_ONLY" and "artifacts" not in output.parts,
        "Invented fresh output required",
    )
    _require(
        all(
            output != p
            and output not in p.parents
            and p.parent not in output.parents
            and output != p.parent
            for p in paths
        ),
        "Input/output overlap",
    )
    _equal(
        value["approval"],
        template["approval"],
        "Approval cannot be embedded as authority",
    )
    return value


def _time(value):
    _require(type(value) is str, "UTC timestamp string required")
    result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    _require(result.strftime("%Y-%m-%dT%H:%M:%SZ") == value, "Canonical UTC required")
    return result


def test_preflight(
    contract,
    *,
    approval,
    owner_claim,
    observed,
    now,
    expected_history,
    expected_implementation,
):
    """Simulate claim agreement without granting authority or reading files."""
    value = validate_test_contract(
        contract,
        expected_history=expected_history,
        expected_implementation=expected_implementation,
    )
    payload = decode(approval)
    _fields(
        payload,
        (
            "schema",
            "purpose",
            "contract",
            "paths",
            "pins",
            "implementation",
            "method",
            "output",
            "attempt_id",
            "not_before",
            "expires_at",
            "maximum_attempts",
        ),
    )
    _require(
        payload["schema"] == "stage-04b2e5-TEST-approval-v1"
        and payload["purpose"] == "distinct_one_shot_historical_evaluation_TEST_ONLY",
        "Distinct owner approval required; historical consent is not authority",
    )
    _equal(payload["contract"], identity(contract), "Approval payload changed")
    for key in ("paths", "implementation", "method", "output"):
        _equal(payload[key], value[key], "Approval scope mismatch: " + key)
    _equal(payload["pins"], value["historical"]["pins"], "Approval pin mismatch")
    _require(
        type(payload["maximum_attempts"]) is int and payload["maximum_attempts"] == 1,
        "Exactly one attempt required",
    )
    _digest(payload["attempt_id"])
    _require(
        _time(payload["not_before"]) <= _time(now) < _time(payload["expires_at"]),
        "Expired/not-yet-valid approval",
    )
    _fields(
        owner_claim, ("kind", "approval", "signature", "external_independence_proven")
    )
    _require(
        owner_claim["kind"] == "fabricated_owner_validation_claim"
        and owner_claim["external_independence_proven"] is False,
        "Counterfeit proof of independence",
    )
    _equal(owner_claim["approval"], identity(approval), "Owner claim payload mismatch")
    _require(
        owner_claim["signature"] == "TEST_ONLY:" + sha256(approval).hexdigest(),
        "Fabricated signature claim mismatch",
    )
    _fields(observed, ("implementation", "pins", "output_exists", "attempt_state"))
    _equal(
        observed["implementation"], value["implementation"], "Stale implementation/CI"
    )
    _equal(observed["pins"], payload["pins"], "Observed pin mismatch")
    _require(
        observed["output_exists"] is False, "Output directory already exists/uncertain"
    )
    _require(observed["attempt_state"] == "UNSTARTED", "Consumed/uncertain attempt")
    return {
        "state": "READY_MODEL_ONLY",
        "execution_authorised": False,
        "external_independence_proven": False,
        "approval": identity(approval),
    }


def attempt_transition(state, event):
    """Pure transition table, not a durable token, clock, execution or retry mechanism.

    Consume MUST be durable before future computation; failure to establish that
    is uncertain/terminal. Readiness must be revalidated at that boundary later.
    """
    transitions = {
        ("UNSTARTED", "refuse_preflight"): "REFUSED_NOT_ATTEMPTED",
        ("UNSTARTED", "accept_test_preflight"): "READY_MODEL_ONLY",
        ("READY_MODEL_ONLY", "consume_before_start"): "CONSUMED_STARTED",
        ("READY_MODEL_ONLY", "consume_uncertain"): "UNCERTAIN_TERMINAL",
        ("READY_MODEL_ONLY", "approval_expired"): "REFUSED_NOT_ATTEMPTED",
        ("CONSUMED_STARTED", "complete"): "COMPLETED_TERMINAL",
        ("CONSUMED_STARTED", "crash"): "CRASHED_TERMINAL",
        ("CONSUMED_STARTED", "status_unknown"): "UNCERTAIN_TERMINAL",
    }
    _require((state, event) in transitions, "Forbidden transition; no retry/resume")
    target = transitions[state, event]
    return {
        "state": target,
        "authority_consumed_or_uncertain": target
        in (
            "CONSUMED_STARTED",
            "COMPLETED_TERMINAL",
            "CRASHED_TERMINAL",
            "UNCERTAIN_TERMINAL",
        ),
        "execution_authorised": False,
    }


def _record(value):
    """Lossless scientific field transport; does not calculate or certify economics."""
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _record(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Decimal):
        _require(
            value.is_finite()
            and len(value.as_tuple().digits) <= 160
            and -160 <= value.as_tuple().exponent <= 80,
            "Invalid exact Decimal",
        )
        return str(value)
    if isinstance(value, datetime):
        _require(value.utcoffset() == timedelta(0), "UTC evidence required")
        return value.isoformat()
    if isinstance(value, Enum):
        return _record(value.value)
    if type(value) in (tuple, list):
        return [_record(v) for v in value]
    if type(value) is dict:
        _require(all(type(k) is str for k in value), "String fields required")
        return {k: _record(v) for k, v in value.items()}
    return _json_value(value)


def result_identity(results):
    return identity(encode(_record(results)))


def _reference(ref, source, at):
    """Check provenance and native time identity; never determine a trading price."""
    _require(at.utcoffset() == timedelta(0), "UTC reference required")
    _fields(
        ref,
        (
            "symbol",
            "record_id",
            "at",
            "price",
            "file_sha256",
            "source_sha256",
            "interval_seconds",
            "venue",
            "market_type",
        ),
    )
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    _require(
        ref["symbol"] == source["symbol"]
        and ref["at"] == at.isoformat()
        and START <= at < END
        and not (at.second or at.microsecond)
        and ref["file_sha256"] == source["file_sha256"]
        and ref["source_sha256"] == source["monthly_sources"][at.month - 1][2]
        and type(ref["interval_seconds"]) is int
        and ref["interval_seconds"] == 60
        and ref["venue"] == "binance"
        and ref["market_type"] == "spot"
        and ref["record_id"]
        == f"binance:spot:{source['symbol']}:60:"
        f"{(at - epoch) // timedelta(milliseconds=1)}",
        "Reference source/time swap",
    )
    _require(type(ref["price"]) is str, "Exact price string required")
    price = Decimal(ref["price"])
    _record(price)
    _require(price > 0, "Positive reference required")


def encode_test_evidence(
    results,
    *,
    contract,
    fabricated_bodies,
    expected_results,
    expected_history,
    expected_implementation,
):
    """TEST-only lossless transport of existing publication replay result shapes.

    Exact result pins must be retained separately before calling. These pins and
    class names detect accidental substitution, not malicious Python fabrication.
    No real parser, sign-off validator, monetary core or source loader is called.
    """
    value = validate_test_contract(
        contract,
        expected_history=expected_history,
        expected_implementation=expected_implementation,
    )
    _fields(fabricated_bodies, PIN_NAMES)
    for key in PIN_NAMES:
        _equal(
            identity(fabricated_bodies[key]),
            value["historical"]["pins"][key],
            "Fabricated file pin mismatch",
        )
        record = decode(fabricated_bodies[key])
        _require(
            type(record) is dict and record.get("provenance") == TEST,
            "Explicit fabricated bytes required",
        )
    # A small TEST envelope, deliberately not an imitation of authenticated E.2 schema.
    science = decode(fabricated_bodies["authenticated_inputs"])
    _fields(science, ("provenance", "sources"))
    _fields(science["sources"], SYMBOLS)
    _require(
        type(results) is tuple and len(results) == 2,
        "Two separate result markets required",
    )
    _pin(expected_results)
    _equal(result_identity(results), expected_results, "Retained result pin mismatch")
    counts = {}
    for symbol, result in zip(SYMBOLS, results, strict=True):
        _require(
            type(result).__name__ == "_PublicationReplayResult"
            and type(result).__module__ == "backtest_badger.genuine_minute_publication",
            "Publication result shape required; fixture relabelling forbidden",
        )
        row = _record(result)
        _fields(
            row,
            (
                "symbol",
                "source",
                "decisions",
                "accounts",
                "end_exclusive",
                "protocol_version",
                "protocol_sha256",
                "kind",
                "status",
                "authority",
            ),
        )
        _require(
            row["symbol"] == symbol
            and row["kind"] == KIND
            and row["status"] == "hypothetical_previously_inspected_validation"
            and row["authority"] == "not_granted_by_private_conversion_or_replay"
            and row["end_exclusive"] == END.isoformat()
            and row["protocol_version"] == PROTOCOL["version"]
            and row["protocol_sha256"] == PROTOCOL["sha256"],
            "Result policy/authority changed",
        )
        source = row["source"]
        _equal(
            {k: v for k, v in source.items() if k != "publication"},
            science["sources"][symbol],
            "Source swap",
        )
        _fields(
            source,
            (
                "symbol",
                "publication",
                "forecast_sha256",
                "model_recipe_sha256",
                "manifest_sha256",
                "file_sha256",
                "monthly_sources",
                "projected_sha256",
                "kind",
            ),
        )
        _require(
            source["symbol"] == symbol and source["kind"] == KIND, "Source kind changed"
        )
        # No recursive self-pin: TEST science carries source identities only;
        # the result carries all four independently retained publication pins.
        _equal(
            source["publication"], value["historical"]["pins"], "Publication pin swap"
        )
        for key in (
            "forecast_sha256",
            "model_recipe_sha256",
            "manifest_sha256",
            "file_sha256",
            "projected_sha256",
        ):
            _digest(source[key])
            _require(
                source[key] not in {p["sha256"] for p in HISTORICAL_PINS.values()},
                "Genuine source identity",
            )
        _require(
            type(source["monthly_sources"]) is list
            and len(source["monthly_sources"]) == 12,
            "Twelve monthly pins required",
        )
        for i, monthly in enumerate(source["monthly_sources"], 1):
            _require(
                type(monthly) is list
                and len(monthly) == 3
                and monthly[:2] == [symbol, f"2024-{i:02}"],
                "Monthly source order",
            )
            _digest(monthly[2])
        decisions = row["decisions"]
        _require(
            len(decisions) == 2195 and len({d["identity"] for d in decisions}) == 2195,
            "Missing/duplicate decisions",
        )
        for i, decision in enumerate(decisions):
            opened = START - timedelta(hours=4) + i * timedelta(hours=4)
            _require(
                decision["symbol"] == symbol
                and decision["source_open"] == opened.isoformat()
                and decision["at"]
                == (opened + timedelta(hours=4, seconds=60)).isoformat()
                and decision["miss"] is None,
                "Decision grid/missingness",
            )
            forecast = decision["forecast"]
            _require(
                forecast["file_sha256"] == source["forecast_sha256"]
                and forecast["source_open"] == decision["source_open"],
                "Forecast source swap",
            )
        accounts = row["accounts"]
        _require([a["label"] for a in accounts] == LABELS, "Independent account order")
        by_decision = {d["identity"]: d for d in decisions}
        counts[symbol] = {"decisions": len(decisions), "accounts": {}}
        for account in accounts:
            _fields(
                account,
                ("label", "initial", "final", "fills", "marks", "status", "reason"),
            )
            account_id = f"{KIND}:{symbol}:{account['label']}"
            for state in (account["initial"], account["final"]):
                _require(
                    state["portfolio"]["key"] == account_id
                    and state["portfolio"]["symbol"] == symbol,
                    "Account/market aggregation forbidden",
                )
            _require(
                account["initial"]["cash"] == "10000"
                and account["initial"]["at"] == START.isoformat(),
                "Initial funding",
            )
            seen_fills = set()
            previous_fill = None
            for fill in account["fills"]:
                _fields(
                    fill,
                    (
                        "reference",
                        "trade",
                        "decision_id",
                        "half_spread_cost",
                        "slippage_cost",
                        "kind",
                    ),
                )
                trade = fill["trade"]
                at = datetime.fromisoformat(trade["at"])
                _reference(fill["reference"], source, at)
                _require(
                    fill["kind"] == "hypothetical_native_minute_execution"
                    and trade["identity"] not in seen_fills
                    and (previous_fill is None or previous_fill < at)
                    and trade["portfolio"] == account["initial"]["portfolio"],
                    "Duplicate/reordered/misidentified fill",
                )
                seen_fills.add(trade["identity"])
                previous_fill = at
                if account["label"] == "ridge":
                    _require(
                        fill["decision_id"] in by_decision, "Missing fill decision"
                    )
                    decision = by_decision[fill["decision_id"]]
                    _require(
                        at
                        == datetime.fromisoformat(decision["at"])
                        + timedelta(minutes=1),
                        "Fill must use strictly next native minute",
                    )
                else:
                    _require(
                        account["label"] == "buy_and_hold"
                        and at == START
                        and fill["decision_id"] is None
                        and trade["side"] == "BUY",
                        "Comparator execution mismatch",
                    )
            marks = account["marks"]
            if account["status"] == "unavailable":
                _require(
                    account["label"] == "buy_and_hold"
                    and not marks
                    and not account["fills"]
                    and account["reason"]
                    == "inception_full_fee_affordable_buy_infeasible"
                    and account["initial"] == account["final"],
                    "Invalid unavailable benchmark",
                )
            else:
                _require(
                    account["status"] == "available"
                    and account["reason"] is None
                    and len(marks) == 8784,
                    "Missing hourly marks",
                )
                for i, mark in enumerate(marks):
                    at = START + i * timedelta(hours=1)
                    _reference(mark["reference"], source, at)
                    _require(mark["account_id"] == account_id, "Mark account swap")
            counts[symbol]["accounts"][account["label"]] = {
                "fills": len(account["fills"]),
                "marks": len(marks),
                "status": account["status"],
            }
    return encode(
        {
            "schema": EXPORT_SCHEMA,
            "provenance": TEST,
            "execution_authorised": False,
            "external_independence_proven": False,
            "economic_publication": False,
            "contract_identity": identity(contract),
            "original_file_claims": value["historical"],
            "implementation_claims": value["implementation"],
            "protocol": PROTOCOL,
            "method": METHOD,
            "metrics": METRICS,
            "warnings": WARNINGS,
            "results_identity": expected_results,
            "counts": counts,
            "results": _record(results),
            "accounting_validation": "NOT_PERFORMED_transport_only_TEST",
            "approval_and_private_paths": "intentionally_excluded",
        }
    )


def decode_test_evidence(body, *, expected):
    """Exact retained export identity and schema roundtrip, never genuine results."""
    _pin(expected)
    _equal(identity(body), expected, "Export integrity mismatch")
    value = decode(body)
    _fields(
        value,
        (
            "schema",
            "provenance",
            "execution_authorised",
            "external_independence_proven",
            "economic_publication",
            "contract_identity",
            "original_file_claims",
            "implementation_claims",
            "protocol",
            "method",
            "metrics",
            "warnings",
            "results_identity",
            "counts",
            "results",
            "accounting_validation",
            "approval_and_private_paths",
        ),
    )
    _require(
        value["schema"] == EXPORT_SCHEMA
        and value["provenance"] == TEST
        and value["execution_authorised"] is False
        and value["economic_publication"] is False
        and value["external_independence_proven"] is False,
        "TEST-only evidence required",
    )
    _equal(value["metrics"], METRICS, "Unreviewed metrics")
    _equal(value["method"], METHOD, "Changed method")
    _equal(value["protocol"], PROTOCOL, "Changed protocol")
    _equal(value["warnings"], WARNINGS, "Missing warnings")
    _require(
        value["accounting_validation"] == "NOT_PERFORMED_transport_only_TEST"
        and value["approval_and_private_paths"] == "intentionally_excluded",
        "Counterfeit verification/privacy claim",
    )
    _equal(
        identity(encode(value["results"])),
        value["results_identity"],
        "Result identity mismatch",
    )
    return value

"""Invented records/ephemeral pins only; no genuine backtest or publication."""

import builtins
import copy
import io
import json
import os
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from hashlib import sha256
from uuid import uuid4

import pytest

from backtest_badger import genuine_minute_inputs as auth
from backtest_badger import genuine_minute_replay as integration
from backtest_badger import genuine_minute_verification_operator as operator
from backtest_badger import genuine_minute_verification_runtime as runtime
from backtest_badger import paper_historical_evaluation as hourly
from backtest_badger import paper_minute_historical as minute
from backtest_badger import paper_minute_integration as synthetic
from backtest_badger.paper_types import STEP, Action, D


@pytest.fixture(autouse=True)
def no_io(monkeypatch):
    """All new APIs are pure; even temporary publication is forbidden here."""

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay integration must not perform I/O or verification")

    for module, name in (
        (builtins, "open"),
        (io, "open"),
        (os, "open"),
        (os, "stat"),
        (os, "lstat"),
        (os, "listdir"),
        (os, "scandir"),
        (os, "mkdir"),
        (os, "rename"),
        (os, "link"),
        (auth, "authenticate_minute_inputs"),
        (runtime, "run_genuine_minute_verification"),
        (operator, "_publish"),
        (operator, "_operate_verified"),
        (auth.parity, "audit_genuine_minute_price_parity"),
        (auth.forecast, "load_forecasts"),
        (auth.minute, "load_minute_execution_data"),
    ):
        monkeypatch.setattr(module, name, forbidden)
    yield
    # Restore before pytest's own report/cache/temp cleanup observations.
    monkeypatch.undo()


def pin(inputs):
    return sha256(auth.authenticated_inputs_json(inputs)).hexdigest()


@pytest.fixture(scope="module")
def fabricated():
    nonce = uuid4().hex

    def fake(label):
        return sha256((nonce + ":invented:" + label).encode()).hexdigest()

    pins = {key: fake(key) for key in auth.EXTERNAL_PINS}
    # Independent literal frozen methodology; all DATA identities remain invented.
    pins["minute_protocol"] = (
        "c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b"
    )
    monthly = tuple(
        (s, f"2024-{m:02d}", fake(f"{s}-{m}"))
        for s in minute.SYMBOLS
        for m in range(1, 13)
    )
    months = {(s, m): value for s, m, value in monthly}
    forecasts = []
    for symbol, model in auth.ACCOUNT_KEYS:
        records = []
        for i in range(2195):
            opened = minute.START - STEP + i * STEP
            available = opened + STEP + minute.MINUTE
            value = D(
                ("1.000000000000000000000000000000000001", "1", "1e-12", "0", "1")[
                    min(i, 4)
                ]
            )
            records.append(
                auth.VerifiedForecast(
                    symbol,
                    model,
                    f"binance:spot:{symbol}:14400:{opened.isoformat()}:{model}",
                    opened,
                    available,
                    available + minute.MINUTE,
                    value if model == "ridge" else D(0),
                    pins["forecast_csv"],
                )
            )
        forecasts.append(tuple(records))
    times = sorted(
        {minute.START + i * minute.HOUR for i in range(8784)}
        | {minute.START + i * STEP + 2 * minute.MINUTE for i in range(2195)}
    )
    references = tuple(
        tuple(
            minute.MinuteReference(
                symbol,
                minute.reference_identity(symbol, at, 60),
                at,
                D(100 if symbol == "BTCUSDT" else 200),
                pins["minute_csv"],
                months[symbol, at.strftime("%Y-%m")],
            )
            for at in times
        )
        for symbol in minute.SYMBOLS
    )
    projections = tuple(minute.projection_sha256(refs) for refs in references)
    evidence = {
        "source_kind": "fabricated_temporary_fixture_bytes",
        "pins": pins,
        "monthly_sources": [[s, m, {"sha256": h}] for s, m, h in monthly],
        "recipe_identity_kind": "stage2b_manifest_sha256",
        "recipe_sha256": pins["forecast_manifest"],
        "projection_sha256": projections,
        "counts": {
            "forecast_accounts": 8,
            "forecasts_per_account": 2195,
            "native_rows": 1054080,
            "hourly_marks_per_market": 8784,
            "hypothetical_minutes_per_market": 2195,
            "references": 21958,
        },
    }
    inputs = auth.AuthenticatedMinuteInputs(
        tuple(forecasts), references, auth.policy.json_bytes(evidence), projections
    )
    declarations = integration._FixtureDeclarations(
        pin(inputs),
        pins["forecast_csv"],
        pins["forecast_manifest"],
        pins["minute_manifest"],
        pins["minute_csv"],
        monthly,
        projections,
        "historical-minute-execution-v1",
        pins["minute_protocol"],
    )
    return inputs, declarations


def adapt(pair):
    return integration._adapt_fixture_inputs(pair[0], declarations=pair[1])


def reseal(inputs, declarations):
    """Only TEST authors can retain new pins; malformed shapes must still fail."""
    return inputs, replace(declarations, inputs_sha256=pin(inputs))


def test_complete_conversion_preserves_all_records_and_timing(fabricated):
    inputs, declarations = fabricated
    bundle = adapt(fabricated)
    assert bundle.original is inputs
    assert sum(map(len, inputs.forecasts)) == 17560
    assert sum(map(len, inputs.references)) == 21958
    assert (
        inputs.genuine_execution_authorised
        is bundle.genuine_execution_authorised
        is False
    )
    for index in range(2):
        originals = inputs.forecasts[index * 4 + 2]
        for original, converted in zip(originals, bundle.forecasts[index], strict=True):
            assert converted.source_open == original.source_open
            assert (
                converted.feature_available_at
                == original.source_open + STEP + timedelta(seconds=60)
            )
            assert converted.prediction.as_tuple() == original.prediction.as_tuple()
            assert converted.record_id == original.record_id
            assert converted.file_sha256 == declarations.forecast_sha256
        noon = bundle.forecasts[index][3]
        assert (
            noon.feature_available_at.hour == 12
            and noon.feature_available_at.minute == 1
        )
        assert minute.next_minute_at(noon.feature_available_at).minute == 2
        refs = inputs.references[index]
        assert sum(r.at.month == 2 and r.at.minute == 0 for r in refs) == 696
        assert refs[-1].at == minute.END - minute.HOUR
        assert (
            originals[-1].hypothetical_minute_at
            == minute.END - 8 * minute.HOUR + 2 * minute.MINUTE
        )
    with pytest.raises(FrozenInstanceError):
        bundle.kind = "genuine"
    assert pin(inputs) == declarations.inputs_sha256


def test_shared_core_economic_parity_and_isolated_identities(fabricated):
    inputs, declarations = fabricated
    bundle = adapt(fabricated)
    results = integration._replay_fixture_inputs(inputs, declarations=declarations)
    keys = set()
    for index, result in enumerate(results):
        refs = inputs.references[index]
        source = minute.SyntheticPriceSource(
            60,
            declarations.minute_manifest_sha256,
            declarations.minute_file_sha256,
            bundle.sources[index].monthly_sources,
            declarations.projection_sha256[index],
        )
        expected = minute.replay_minute_historical(
            result.symbol,
            bundle.forecasts[index],
            refs,
            source=source,
            expected_source_sha256=minute.price_source_sha256(source),
            forecast_sha256=declarations.forecast_sha256,
            model_recipe_sha256=declarations.model_recipe_sha256,
        )
        # Compare ALL decisions, fills, accounts, ledger sequence and mark fields;
        # the only allowed difference is the namespace of portfolio-linked IDs.
        for name in ("decisions", "accounts"):
            assert minute.scientific_json(
                getattr(result, name)
            ) == minute.scientific_json(getattr(expected, name)).replace(
                minute.KIND, integration.FIXTURE_KIND
            )
        assert result.kind == result.source.kind == integration.FIXTURE_KIND
        assert result.status == result.source.status == integration.FIXTURE_STATUS
        assert not result.genuine_execution_authorised and not result.economic_results
        assert "not_source_authentication" in result.authentication
        assert len(result.decisions) == 2195
        assert [d.action for d in result.decisions[:5]] == [
            Action.BUY_REQUIRED,
            Action.HOLD,
            Action.EXIT_REQUIRED,
            Action.CASH_NOOP,
            Action.BUY_REQUIRED,
        ]
        ridge, cash, bh = result.accounts
        assert [len(a.fills) for a in result.accounts] == [3, 0, 1]
        assert cash.final.cash == D(10000) and cash.final.quantity == 0
        assert ridge.fills[0].trade.at == minute.START + 2 * minute.MINUTE
        assert bh.fills[0].trade.at == minute.START
        assert ridge.fills[0].trade.price == (
            D("100.03") if index == 0 else D("200.06")
        )
        assert ridge.fills[0].trade.quantity == (
            D("99.870138") if index == 0 else D("49.935069")
        )
        assert ridge.fills[0].trade.fee == D("9.99000991")
        for account in result.accounts:
            keys.add(account.initial.portfolio.key)
            assert account.initial.cash == D(10000)
            assert account.initial.portfolio.symbol == result.symbol
            assert len(account.marks) == 8784
            minute.verify_minute_account(account, end_exclusive=minute.END)
            ledger = minute.minute_ledger_records(account)
            assert {r["account_id"] for r in ledger} == {account.initial.portfolio.key}
            assert all(m.reference.symbol == result.symbol for m in account.marks)
    assert len(keys) == 6
    assert pin(inputs) == declarations.inputs_sha256


class Poison:
    def __getattribute__(self, name):
        raise AssertionError("Closed gate inspected argument")


@pytest.mark.parametrize("candidate", [None, True, "genuine", {}, "poison"])
def test_public_gate_unconditional(candidate):
    if candidate == "poison":
        candidate = Poison()
    with pytest.raises(PermissionError, match="remain closed"):
        integration.replay_genuine_minute_historical(approval=candidate)


def test_dataclass_manifest_and_synthetic_source_cannot_authorise(fabricated):
    inputs, declarations = fabricated
    for candidate in (
        inputs,
        declarations,
        adapt(fabricated).sources[0],
        {"genuine_execution_authorised": True, "status": "genuine"},
    ):
        with pytest.raises(PermissionError):
            integration.replay_genuine_minute_historical(approval=candidate)
    with pytest.raises(ValueError, match="declarations"):
        integration._replay_fixture_inputs(inputs, declarations=True)
    with pytest.raises(ValueError, match="verified record type"):
        integration._replay_fixture_inputs({}, declarations=declarations)
    with pytest.raises(TypeError):
        integration.replay_genuine_minute_historical(
            approval=inputs, allow_genuine=True
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "synthetic_test"),
        ("status", "genuine"),
        ("genuine_execution_authorised", True),
        ("genuine_execution_authorised", 0),
    ],
)
def test_mutated_record_authority(fabricated, field, value):
    inputs = copy.copy(fabricated[0])
    object.__setattr__(inputs, field, value)
    with pytest.raises(ValueError, match="non-authorising"):
        adapt((inputs, fabricated[1]))


@pytest.mark.parametrize(
    "field",
    [
        "inputs_sha256",
        "forecast_sha256",
        "model_recipe_sha256",
        "minute_manifest_sha256",
        "minute_file_sha256",
        "protocol_version",
        "protocol_sha256",
    ],
)
def test_wrong_independent_declaration(fabricated, field):
    with pytest.raises(ValueError):
        adapt((fabricated[0], replace(fabricated[1], **{field: "a" * 64})))


@pytest.mark.parametrize(
    "field,declared",
    [
        ("forecast_sha256", "forecast_csv"),
        ("model_recipe_sha256", "forecast_manifest"),
        ("minute_file_sha256", "minute_csv"),
        ("minute_manifest_sha256", "minute_manifest"),
    ],
)
def test_real_source_declarations_forbidden(fabricated, field, declared):
    with pytest.raises(ValueError, match="Genuine source pin"):
        adapt(
            (
                fabricated[0],
                replace(fabricated[1], **{field: auth.EXTERNAL_PINS[declared]}),
            )
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "count",
        "account_missing",
        "list",
        "reordered",
        "wrong_type",
        "model",
        "symbol",
        "source_open",
        "assumed_available_at",
        "hypothetical_minute_at",
        "record_id",
        "file_sha256",
        "prediction",
        "float",
        "nan",
        "zero_baseline",
        "naive",
    ],
)
def test_malformed_forecast_even_with_new_fixture_snapshot(fabricated, mutation):
    inputs, declarations = fabricated
    accounts = list(inputs.forecasts)
    records = list(accounts[2])
    if mutation == "count":
        records.pop()
    elif mutation == "account_missing":
        accounts.pop()
    elif mutation == "reordered":
        records[0], records[1] = records[1], records[0]
    elif mutation == "wrong_type":
        records[0] = {}
    elif mutation == "zero_baseline":
        accounts[0] = (replace(accounts[0][0], prediction=D(1)), *accounts[0][1:])
    elif mutation != "list":
        field, value = {
            "model": ("model", "zero"),
            "symbol": ("symbol", "ETHUSDT"),
            "source_open": ("source_open", minute.START),
            "assumed_available_at": ("assumed_available_at", minute.START),
            "hypothetical_minute_at": (
                "hypothetical_minute_at",
                minute.START + minute.MINUTE,
            ),
            "record_id": ("record_id", "wrong"),
            "file_sha256": ("file_sha256", "a" * 64),
            "prediction": ("prediction", D("1e-161")),
            "float": ("prediction", 0.1),
            "nan": ("prediction", D("NaN")),
            "naive": ("source_open", records[0].source_open.replace(tzinfo=None)),
        }[mutation]
        records[0] = replace(records[0], **{field: value})
    accounts[2] = records if mutation == "list" else tuple(records)
    candidate = replace(inputs, forecasts=tuple(accounts))
    with pytest.raises(ValueError):
        adapt(reseal(candidate, declarations))


@pytest.mark.parametrize(
    "mutation",
    [
        "count",
        "list",
        "market_order",
        "duplicate",
        "reordered",
        "type",
        "at",
        "price",
        "file_sha256",
        "source_sha256",
        "interval_seconds",
        "record_id",
    ],
)
def test_invalid_minute_projection_even_with_new_snapshot(fabricated, mutation):
    inputs, declarations = fabricated
    streams = list(inputs.references)
    refs = list(streams[0])
    if mutation == "count":
        refs.pop()
    elif mutation == "duplicate":
        refs[1] = refs[0]
    elif mutation == "reordered":
        refs[0], refs[1] = refs[1], refs[0]
    elif mutation == "type":
        refs[0] = {}
    elif mutation not in ("market_order", "list"):
        ref = copy.copy(refs[1])
        value = {
            "at": minute.START + minute.MINUTE,
            "price": D(-1),
            "file_sha256": "a" * 64,
            "source_sha256": declarations.monthly_sources[1][2],
            "interval_seconds": 3600,
            "record_id": "hourly",
        }[mutation]
        object.__setattr__(ref, mutation, value)
        refs[1] = ref
    streams[0] = refs if mutation == "list" else tuple(refs)
    if mutation == "market_order":
        streams.reverse()
    with pytest.raises(ValueError):
        adapt(reseal(replace(inputs, references=tuple(streams)), declarations))


@pytest.mark.parametrize(
    "mutation",
    [
        "kind",
        "csv",
        "recipe",
        "protocol",
        "monthly",
        "counts",
        "projection",
        "authority",
        "economic",
        "projection_tuple",
        "monthly_order",
    ],
)
def test_evidence_and_projection_pin_rejections(fabricated, mutation):
    inputs, declarations = fabricated
    evidence = json.loads(inputs.source_evidence_json)
    if mutation == "kind":
        evidence["source_kind"] = "genuine_retained_stage2b_native_minute_prior_parity"
    elif mutation in ("csv", "protocol"):
        evidence["pins"]["forecast_csv" if mutation == "csv" else "minute_protocol"] = (
            "a" * 64
        )
    elif mutation == "recipe":
        evidence["recipe_sha256"] = "a" * 64
    elif mutation == "monthly":
        evidence["monthly_sources"][0][2]["sha256"] = "a" * 64
    elif mutation == "counts":
        evidence["counts"]["references"] = 21958.0
    elif mutation == "projection":
        evidence["projection_sha256"][0] = "a" * 64
    elif mutation in ("authority", "economic"):
        evidence[
            "genuine_execution_authorised"
            if mutation == "authority"
            else "economic_results"
        ] = True
    elif mutation == "projection_tuple":
        inputs = replace(
            inputs, projection_sha256=("a" * 64, inputs.projection_sha256[1])
        )
    else:
        declarations = replace(
            declarations, monthly_sources=tuple(reversed(declarations.monthly_sources))
        )
    inputs = replace(inputs, source_evidence_json=auth.policy.json_bytes(evidence))
    with pytest.raises(ValueError):
        adapt(reseal(inputs, declarations))


@pytest.mark.parametrize("what", ["prediction", "price", "baseline", "evidence"])
def test_mutation_cannot_be_blessed_by_self_hashing(fabricated, what):
    inputs, declarations = fabricated
    if what in ("prediction", "baseline"):
        accounts = list(inputs.forecasts)
        index = 2 if what == "prediction" else 7
        accounts[index] = (
            replace(accounts[index][0], prediction=D(37)),
            *accounts[index][1:],
        )
        inputs = replace(inputs, forecasts=tuple(accounts))
    elif what == "price":
        refs = inputs.references
        inputs = replace(
            inputs,
            references=((replace(refs[0][0], price=D(101)), *refs[0][1:]), refs[1]),
        )
    else:
        inputs = replace(
            inputs, source_evidence_json=inputs.source_evidence_json + b" "
        )
    with pytest.raises(ValueError, match="changed after pinning"):
        adapt((inputs, declarations))


def test_unchanged_synthetic_entry_points_reject_verified_record(fabricated):
    inputs, declarations = fabricated
    bundle = adapt(fabricated)
    with pytest.raises(ValueError, match="synthetic source"):
        minute.replay_minute_historical(
            "BTCUSDT",
            bundle.forecasts[0],
            inputs.references[0],
            source=bundle.sources[0],
            expected_source_sha256="a" * 64,
            forecast_sha256=declarations.forecast_sha256,
            model_recipe_sha256=declarations.model_recipe_sha256,
        )
    with pytest.raises(ValueError):
        hourly.evaluate_bundle(inputs)
    with pytest.raises(ValueError):
        hourly.adapt_inputs(inputs, inputs, evidence={"status": auth.STATUS})
    with pytest.raises((ValueError, PermissionError)):
        synthetic.adapt_minute_inputs(
            inputs,
            {},
            {},
            (),
            {},
            evidence={"status": auth.STATUS},
            expected_evidence_sha256="a" * 64,
        )
    with pytest.raises(ValueError):
        minute.SyntheticPriceSource(
            60, "a" * 64, "b" * 64, (), "c" * 64, status=auth.STATUS
        )


def test_projection_rechecked_after_independent_record_snapshot(fabricated):
    inputs, declarations = fabricated
    refs = inputs.references
    changed = replace(
        inputs,
        references=(
            (replace(refs[0][0], price=D(101)), *refs[0][1:]),
            refs[1],
        ),
    )
    with pytest.raises(ValueError, match="Minute projection changed"):
        adapt(reseal(changed, declarations))


def test_one_markets_prices_cannot_affect_other_account(fabricated):
    inputs, declarations = fabricated
    before = integration._replay_fixture_inputs(inputs, declarations=declarations)
    refs = (
        tuple(replace(r, price=D(300)) for r in inputs.references[0]),
        inputs.references[1],
    )
    projections = tuple(minute.projection_sha256(rows) for rows in refs)
    evidence = json.loads(inputs.source_evidence_json)
    evidence["projection_sha256"] = projections
    changed = replace(
        inputs,
        references=refs,
        projection_sha256=projections,
        source_evidence_json=auth.policy.json_bytes(evidence),
    )
    declarations = replace(
        declarations, projection_sha256=projections, inputs_sha256=pin(changed)
    )
    after = integration._replay_fixture_inputs(changed, declarations=declarations)
    assert before[0].accounts != after[0].accounts
    assert before[1].accounts == after[1].accounts
    assert before[0].decisions == after[0].decisions
    assert before[1].decisions == after[1].decisions


def test_io_guards_block_reads_stats_and_publication_before_observation():
    for call in (
        lambda: builtins.open("never-open"),
        lambda: os.stat("never-stat"),
        lambda: os.listdir("never-list"),
        lambda: os.mkdir("never-create"),
        lambda: operator._publish(None, None, None, None, None),
        lambda: runtime.run_genuine_minute_verification(approval=Poison()),
    ):
        with pytest.raises(AssertionError, match="must not perform"):
            call()

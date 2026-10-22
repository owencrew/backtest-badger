"""Invented full-year publication bytes only; never original evidence or authority."""

from dataclasses import replace
from hashlib import sha256

import pytest
import test_genuine_minute_inputs as fixtures
import test_genuine_minute_replay as prior
import test_genuine_minute_signed_approval as signatures

from backtest_badger import genuine_minute_publication as bridge
from backtest_badger import genuine_minute_replay as replay

# This fixture also blocks stat/list/open and verifier/loader/publisher calls.
no_io = prior.no_io
auth = bridge.auth
minute = bridge.minute
operator = bridge.operator


def fingerprint(body):
    return bridge._Fingerprint(sha256(body).hexdigest(), len(body))


def serialize(science, integrity):
    bodies = (minute.scientific_json(science).encode(), operator._json(integrity))
    manifest = operator._json(
        {
            "schema": "minute-input-verification-publication-v1",
            "kind": "source_authentication_only",
            "complete": True,
            "status": auth.STATUS,
            "source_kind": bridge.SOURCE_KIND,
            "genuine_execution_authorised": False,
            "economic_results": False,
            "files": {
                n: fixtures.ident(b)
                for n, b in zip(bridge.FILES[1:], bodies, strict=True)
            },
        }
    )
    return (manifest, *bodies)


def repin(bodies, signoff):
    # TEST authors retain new invented pins to test structural checks beyond hashes.
    return bridge._PublicationPins(*(fingerprint(b) for b in bodies), signoff)


@pytest.fixture(scope="module")
def fabricated():
    inputs, old_pins = prior.fabricated.__wrapped__()
    evidence = auth._json(inputs.source_evidence_json)
    approved = signatures.complete_payload()
    approved["pins"].update(evidence["pins"])
    pins = approved["pins"]
    months = {(s, m): value for s, m, value in old_pins.monthly_sources}
    for s, m, row in approved["monthly_sources"]:
        row["sha256"] = months[s, m]
        stem = f"raw/{s}-1m-{m}.zip"
        approved["input_inventory"]["minute"][stem]["sha256"] = months[s, m]
    for path, key in (
        (auth.parity.HOURLY_PROTOCOL, "hourly_protocol"),
        (auth.parity.MINUTE_PROTOCOL, "minute_protocol"),
        (auth.parity.PIN_DOCUMENT, "minute_pin_document"),
    ):
        approved["implementation"][path]["sha256"] = pins[key]
        approved["audit_code"][path] = pins[key]
    recipe = fixtures.recipe(pins)
    recipe.update(
        {
            "target": "log_return_4h",
            "test_policy": "fabricated metadata only",
            "metric_definitions": {},
            "random_seed": 42,
            "thread_limit": 1,
            "reproducibility_tolerance": {"rtol": 1e-10, "atol": 1e-12},
            "runtime": {},
            "implementation_sha256": {},
            "preprocessing": "train-only",
            "limitations": "fabricated full-year test",
        }
    )
    for name in (
        "feature_definitions",
        "target_definition",
        "split_boundaries",
        "split_clock",
        "exclusion_policy",
        "known_anomalies",
        "source_selection_policy",
        "counts",
    ):
        recipe["input"][name] = {}
    recipe["output_sha256"]["summary.md"] = signatures.invented("summary")
    for market in recipe["markets"].values():
        market["validation_metrics"] = {}
        market["model_parameters"].update(
            {
                "zero": {"constant": 0.0},
                "training_mean": {"constant": 0.0},
                "gradient_boosting": {},
            }
        )
    recipe_body = auth.parity._json(recipe)
    pins["forecast_manifest"] = sha256(recipe_body).hexdigest()
    inventory = approved["input_inventory"]
    inventory["forecast"]["manifest.json"] = fixtures.ident(recipe_body)
    inventory["forecast"]["validation_predictions.csv"]["sha256"] = pins["forecast_csv"]
    inventory["minute"]["minute_opens.csv"]["sha256"] = pins["minute_csv"]
    metadata = auth.minute._manifest(
        [
            {
                **row,
                "symbol": s,
                "month": m,
                "interval": "1m",
                "observation_kind": "retrospective_full_archive_acquisition",
                "validation_status": "complete_checksum_and_native_grid",
            }
            for s, m, row in approved["monthly_sources"]
        ],
        pins["minute_csv"],
        inventory["minute"]["minute_opens.csv"]["bytes"],
        approved["implementation"]["src/backtest_badger/minute_execution_data.py"][
            "sha256"
        ],
    )
    metadata_body = auth.minute._json(metadata)
    pins["minute_manifest"] = sha256(metadata_body).hexdigest()
    inventory["minute"]["manifest.json"] = fixtures.ident(metadata_body)

    def snapshot(values):
        return {n: {**v, "stat": [1, 2, v["bytes"], 4, 5]} for n, v in values.items()}

    parity = fixtures.publication(
        pins,
        {(s, m): row for s, m, row in approved["monthly_sources"]},
        metadata,
        snapshot(inventory["minute"]),
        approved["audit_code"],
        {(s, m): h for s, m, h in approved["hourly_monthly"]},
    )
    inventory["parity"] = {n: fixtures.ident(b) for n, b in parity.items()}
    for name, key in (
        ("provenance.json", "parity_provenance"),
        ("integrity.json", "parity_integrity"),
        ("discrepancies.csv", "parity_discrepancies"),
    ):
        pins[key] = sha256(parity[name]).hexdigest()
    evidence.update(
        {
            "schema": "minute-input-scientific-evidence-v1",
            "source_kind": bridge.SOURCE_KIND,
            "native_loader_evidence": (
                "unchanged_loader_full_native_archive_revalidation"
            ),
            "pins": pins,
            "original_files": inventory,
            "code_sha256": {
                n: v["sha256"] for n, v in approved["implementation"].items()
            },
            "monthly_sources": approved["monthly_sources"],
            "recipe_sha256": pins["forecast_manifest"],
            "forecast_manifest": recipe,
            "minute_metadata": metadata,
            "parity_publication": auth._json(parity["manifest.json"]),
            "parity_report": auth._json(parity["parity_report.json"]),
            "parity_provenance": auth._json(parity["provenance.json"]),
            "limitations": list(auth.LIMITATIONS),
        }
    )
    science = auth._json(
        auth.authenticated_inputs_json(
            replace(inputs, source_evidence_json=operator._json(evidence))
        )
    )
    before = {g: snapshot(items) for g, items in inventory.items()}
    code = snapshot(approved["implementation"])
    integrity = {
        "schema": "minute-input-operational-integrity-v1",
        "approval": approved,
        "environment": {
            "commit": approved["commit"],
            "clean": True,
            "runtime": approved["runtime"],
        },
        "sources_before": before,
        "sources_after": before,
        "code_before": code,
        "code_after": code,
    }
    bodies = serialize(science, integrity)
    # Opaque invented bytes: deliberately no guessed private sign-off JSON schema.
    signoff = fingerprint(b"invented independent sign-off fingerprint only")
    return bodies, repin(bodies, signoff), (inputs, old_pins)


def parse(bodies, pins):
    return bridge._parse_verified_publication(
        **dict(zip(bridge.FILES_KEYS, bodies, strict=True)),
        expected=pins,
        signoff_claim=pins.signoff,
    )


def changed(fabricated, mutate):
    bodies, pins, _ = fabricated
    science, integrity = (auth._json(b) for b in bodies[1:])
    evidence = auth._json(science["source_evidence_json"])
    mutate(science, integrity, evidence)
    science["source_evidence_json"] = operator._json(evidence).decode()
    bodies = serialize(science, integrity)
    return bodies, repin(bodies, pins.signoff)


def test_full_year_pure_conversion_and_roundtrip(fabricated):
    bodies, pins, _ = fabricated
    verified = parse(bodies, pins)
    assert verified.bodies == bodies and verified.pins == pins
    assert auth.authenticated_inputs_json(verified.inputs) == bodies[1]
    assert sum(map(len, verified.inputs.forecasts)) == 17560
    assert sum(map(len, verified.inputs.references)) == 21958
    assert not verified.inputs.genuine_execution_authorised
    assert not set(
        auth._json(verified.inputs.source_evidence_json)["pins"].values()
    ) & (set(auth.EXTERNAL_PINS.values()) - {minute.PROTOCOL_SHA256})
    with pytest.raises(ValueError, match="fabricated"):
        replay._adapt_fixture_inputs(verified.inputs, declarations=fabricated[2][1])


def test_full_year_shared_core_parity_with_unchanged_fixture(fabricated):
    bodies, pins, original = fabricated
    result = bridge._replay_verified_publication(
        parse(bodies, pins), expected=pins, signoff_claim=pins.signoff
    )
    expected = replay._replay_fixture_inputs(original[0], declarations=original[1])
    # Every decision, fill, ledger prefix and mark matches. Portfolio namespaces
    # and recipe provenance deliberately differ BEFORE any economics is calculated.
    for actual, old in zip(result, expected, strict=True):
        assert type(actual) is bridge._PublicationReplayResult
        assert type(actual.source) is bridge._PublicationMinuteSource
        assert not isinstance(actual.source, minute.SyntheticPriceSource)
        for name in ("decisions", "accounts"):
            want = minute.scientific_json(getattr(old, name)).replace(
                replay.FIXTURE_KIND, bridge.KIND
            )
            want = want.replace(
                original[1].model_recipe_sha256, actual.source.model_recipe_sha256
            )
            assert minute.scientific_json(getattr(actual, name)) == want
        assert actual.source.publication == pins
        assert actual.accounts[1].final.cash == prior.D(10000)


@pytest.mark.parametrize("index", range(3))
@pytest.mark.parametrize(
    "mutation",
    (
        "hash",
        "length",
        "bytes",
        "noncanonical",
        "duplicate",
        "nan",
        "infinity",
        "overflow",
    ),
)
def test_each_publication_byte_boundary(fabricated, index, mutation):
    bodies, pins, _ = fabricated
    bodies = list(bodies)
    if mutation == "hash":
        names = ("manifest", "authenticated_inputs", "integrity")
        pin = getattr(pins, names[index])
        pins = replace(pins, **{names[index]: replace(pin, sha256="0" * 64)})
    elif mutation == "length":
        names = ("manifest", "authenticated_inputs", "integrity")
        pin = getattr(pins, names[index])
        pins = replace(pins, **{names[index]: replace(pin, bytes=pin.bytes + 1)})
    else:
        if mutation == "bytes":
            bodies[index] += b" "
        elif mutation == "noncanonical":
            bodies[index] += b"\n"
        elif mutation == "duplicate":
            bodies[index] = b'{"duplicate":0,"duplicate":1}\n'
        else:
            value = {"nan": b"NaN", "infinity": b"Infinity", "overflow": b"1e999"}[
                mutation
            ]
            bodies[index] = b'{"bad":' + value + b"}\n"
        if mutation != "bytes":
            pins = repin(bodies, pins.signoff)
    with pytest.raises(ValueError):
        parse(tuple(bodies), pins)


@pytest.mark.parametrize(
    "key,value",
    (
        ("kind", "economic_results"),
        ("source_kind", operator.SOURCE_KIND),
        ("complete", False),
        ("complete", 1),
        ("genuine_execution_authorised", True),
        ("economic_results", True),
        ("status", "success"),
        ("schema", "unknown"),
        ("extra", False),
    ),
)
def test_manifest_semantics_even_with_new_test_pins(fabricated, key, value):
    bodies, pins, _ = fabricated
    manifest = auth._json(bodies[0])
    manifest[key] = value
    bodies = (operator._json(manifest), *bodies[1:])
    with pytest.raises(ValueError):
        parse(bodies, repin(bodies, pins.signoff))


@pytest.mark.parametrize("name", bridge.FILES[1:])
@pytest.mark.parametrize("mutation", ("missing", "extra", "size", "float_size", "hash"))
def test_manifest_companions(fabricated, name, mutation):
    bodies, pins, _ = fabricated
    manifest = auth._json(bodies[0])
    if mutation == "missing":
        del manifest["files"][name]
    elif mutation == "extra":
        manifest["files"][name]["extra"] = 1
    elif mutation == "size":
        manifest["files"][name]["bytes"] += 1
    elif mutation == "float_size":
        manifest["files"][name]["bytes"] = float(manifest["files"][name]["bytes"])
    else:
        manifest["files"][name]["sha256"] = "0" * 64
    bodies = (operator._json(manifest), *bodies[1:])
    with pytest.raises(ValueError):
        parse(bodies, repin(bodies, pins.signoff))


@pytest.mark.parametrize("group", ("forecasts", "references"))
@pytest.mark.parametrize(
    "mutation",
    ("missing", "duplicate", "reorder", "extra_field", "pin", "nonfinite", "time"),
)
def test_rows_fail_closed_after_repin(fabricated, group, mutation):
    def mutate(science, integrity, evidence):
        rows = science[group][0]
        if mutation == "missing":
            rows.pop()
        elif mutation == "duplicate":
            rows[1] = rows[0]
        elif mutation == "reorder":
            rows[0], rows[1] = rows[1], rows[0]
        elif mutation == "extra_field":
            rows[0]["extra"] = False
        elif mutation == "pin":
            rows[0]["file_sha256"] = "0" * 64
        elif mutation == "nonfinite":
            rows[0]["prediction" if group == "forecasts" else "price"] = "NaN"
        else:
            key = "source_open" if group == "forecasts" else "at"
            rows[0][key] = rows[1][key]

    with pytest.raises(ValueError):
        parse(*changed(fabricated, mutate))


@pytest.mark.parametrize(
    "target,key,value",
    (
        ("evidence", "source_kind", operator.SOURCE_KIND),
        (
            "evidence",
            "native_loader_evidence",
            "injected_metadata_only_not_archive_revalidation",
        ),
        ("evidence", "recipe_sha256", "0" * 64),
        ("evidence", "schema", "unknown"),
        ("science", "genuine_execution_authorised", True),
        ("science", "status", "success"),
        ("approval", "strategy_authorised", True),
        ("approval", "economic_publication_authorised", True),
        ("approval", "verification_only", False),
        ("approval", "commit", "f" * 40),
        (
            "approval",
            "ci",
            {
                "commit": "a" * 40,
                "run_id": "123456",
                "status": "completed",
                "conclusion": "failure",
            },
        ),
        ("integrity", "environment", {}),
    ),
)
def test_scientific_operational_intent_agreement(fabricated, target, key, value):
    def mutate(science, integrity, evidence):
        {
            "science": science,
            "integrity": integrity,
            "evidence": evidence,
            "approval": integrity["approval"],
        }[target][key] = value

    with pytest.raises(ValueError):
        parse(*changed(fabricated, mutate))


@pytest.mark.parametrize(
    "name",
    (
        "forecast_csv",
        "forecast_manifest",
        "minute_csv",
        "minute_manifest",
        "minute_protocol",
        "parity_manifest",
        "research_csv",
        "research_manifest",
    ),
)
def test_pin_swaps(fabricated, name):
    def mutate(science, integrity, evidence):
        evidence["pins"][name] = "0" * 64

    with pytest.raises(ValueError):
        parse(*changed(fabricated, mutate))


@pytest.mark.parametrize(
    "kind",
    ("recipe", "auditor", "counts", "monthly", "projection", "code", "model", "mean"),
)
def test_retained_science_links(fabricated, kind):
    def mutate(science, integrity, evidence):
        if kind == "recipe":
            evidence["forecast_manifest"]["markets"]["BTCUSDT"]["model_parameters"][
                "ridge"
            ]["alpha"] = 2.0
        elif kind == "auditor":
            evidence["parity_provenance"]["implementation_sha256"].pop(
                next(iter(integrity["approval"]["audit_code"]))
            )
        elif kind == "counts":
            evidence["counts"]["references"] = 21957
        elif kind == "monthly":
            evidence["monthly_sources"][0], evidence["monthly_sources"][1] = (
                evidence["monthly_sources"][1],
                evidence["monthly_sources"][0],
            )
        elif kind == "projection":
            evidence["projection_sha256"][0] = science["projection_sha256"][0] = (
                "0" * 64
            )
        elif kind == "code":
            evidence["code_sha256"][next(iter(evidence["code_sha256"]))] = "0" * 64
        elif kind == "model":
            science["forecasts"][6][0]["model"] = "gradient_boosting"
        else:
            science["forecasts"][1][0]["prediction"] = "1"

    with pytest.raises(ValueError):
        parse(*changed(fabricated, mutate))


def test_signoff_is_only_external_fingerprint_not_invented_schema(fabricated):
    bodies, pins, _ = fabricated
    for claim in (
        replace(pins.signoff, bytes=pins.signoff.bytes + 1),
        replace(pins.signoff, sha256="0" * 64),
        {"approved": True},
    ):
        with pytest.raises(ValueError):
            bridge._parse_verified_publication(
                **dict(zip(bridge.FILES_KEYS, bodies, strict=True)),
                expected=pins,
                signoff_claim=claim,
            )


def test_injected_record_rejected_before_monetary_core(fabricated, monkeypatch):
    bodies, pins, _ = fabricated
    record = parse(bodies, pins)
    monkeypatch.setattr(minute, "_replay_minute_core", fixtures.forbidden)
    for injected in (
        record.inputs,
        {},
        replace(record, inputs=replace(record.inputs, forecasts=())),
        replace(record, bodies=(b"{}", *bodies[1:])),
        replace(record, pins=replace(pins, signoff=fingerprint(b"changed"))),
    ):
        with pytest.raises(ValueError):
            bridge._replay_verified_publication(
                injected, expected=pins, signoff_claim=pins.signoff
            )


def test_public_gate_remains_closed_before_inspection():
    class Hostile:
        def __getattribute__(self, name):
            raise AssertionError("Approval inspected")

    with pytest.raises(PermissionError, match="remain closed"):
        replay.replay_genuine_minute_historical(approval=Hostile())


@pytest.mark.parametrize("index", range(8))
def test_every_forecast_account_required(fabricated, index):
    def mutate(science, integrity, evidence):
        science["forecasts"][index].pop()

    with pytest.raises(ValueError, match="row count"):
        parse(*changed(fabricated, mutate))


@pytest.mark.parametrize(
    "kind", ("duplicate", "nan", "infinity", "overflow", "spacing")
)
def test_nested_evidence_encoding(fabricated, kind):
    bodies, pins, _ = fabricated
    science, integrity = (auth._json(body) for body in bodies[1:])
    science["source_evidence_json"] = {
        "duplicate": '{"a":0,"a":1}\n',
        "nan": '{"a":NaN}\n',
        "infinity": '{"a":Infinity}\n',
        "overflow": '{"a":1e999}\n',
        "spacing": science["source_evidence_json"] + " ",
    }[kind]
    bodies = serialize(science, integrity)
    with pytest.raises(ValueError):
        parse(bodies, repin(bodies, pins.signoff))


@pytest.mark.parametrize(
    "value", ("garbage", "1e999999", "1.0e0", "Infinity", "-Infinity")
)
def test_malformed_or_unbounded_decimal(fabricated, value):
    def mutate(science, integrity, evidence):
        science["forecasts"][2][0]["prediction"] = value

    with pytest.raises(ValueError):
        parse(*changed(fabricated, mutate))


@pytest.mark.parametrize("index,limit", tuple(enumerate(bridge.LIMITS)))
def test_external_bounds_checked_before_json(fabricated, index, limit, monkeypatch):
    bodies, pins, _ = fabricated
    name = bridge.FILES_KEYS[index]
    monkeypatch.setattr(auth, "_json", fixtures.forbidden)
    with pytest.raises(ValueError, match="bound"):
        parse(
            bodies,
            replace(pins, **{name: replace(getattr(pins, name), bytes=limit + 1)}),
        )


def test_record_cannot_open_public_or_synthetic_routes(fabricated):
    bodies, pins, _ = fabricated
    record = parse(bodies, pins)
    with pytest.raises(PermissionError):
        replay.replay_genuine_minute_historical(approval=record)
    with pytest.raises(ValueError):
        minute.price_source_sha256(record)
    with pytest.raises(ValueError):
        prior.hourly.evaluate_bundle(record)


def test_changed_original_commit_and_ci_not_blessed_by_candidate(fabricated):
    bodies, pins, _ = fabricated
    science, integrity = (auth._json(body) for body in bodies[1:])
    integrity["approval"]["commit"] = "b" * 40
    integrity["approval"]["ci"]["commit"] = "b" * 40
    integrity["approval"]["ci"]["run_id"] = "999999"
    integrity["environment"]["commit"] = "b" * 40
    with pytest.raises(ValueError, match="External publication"):
        parse(serialize(science, integrity), pins)

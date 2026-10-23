"""Invented publications only; the acceptance path calls the real implementations."""

import json
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest
import test_genuine_minute_publication as fixtures
import test_genuine_minute_replay as prior
import test_paper_minute_reporting as reporter_fixtures

from backtest_badger import genuine_backtest_reporting_integration as integration
from backtest_badger import genuine_minute_replay as gate
from backtest_badger import paper_minute_historical as minute
from backtest_badger import paper_minute_reporting as reporting

no_io = prior.no_io
offline = reporter_fixtures.offline


@pytest.fixture(autouse=True)
def no_database(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Database access forbidden")

    monkeypatch.setattr(fixtures.fixtures.psycopg, "connect", forbidden)


@pytest.fixture(scope="module")
def full():
    # Fixed invented nonce, never original bytes; no signing fixture is invoked.
    calls = {}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            prior, "uuid4", lambda: SimpleNamespace(hex="e5c-fabricated-fixed")
        )
        for module, name in (
            (integration.publication, "_parse_verified_publication"),
            (integration.publication, "_validate_independent_signoff"),
            (integration.publication, "_replay_verified_publication"),
            (minute, "_replay_minute_core"),
            (minute, "verify_minute_account"),
            (reporting, "minute_reporting_summary"),
        ):
            original = getattr(module, name)

            def counted(*args, _name=name, _original=original, **kwargs):
                calls[_name] = calls.get(_name, 0) + 1
                return _original(*args, **kwargs)

            patch.setattr(module, name, counted)
        # Guard loader/publisher APIs even while module-scoped fixtures are built.
        guard = prior.no_io.__wrapped__(patch)
        next(guard)
        bodies, pins, _ = fixtures.fabricated.__wrapped__()
        signoff = fixtures.signoff_wire(fixtures.signoff_record(pins))
        pins = replace(pins, signoff=fixtures.fingerprint(signoff))
        arguments = dict(zip(fixtures.bridge.FILES_KEYS, bodies, strict=True)) | {
            "signoff": signoff,
            "expected": pins,
            "fabricated_only": True,
        }
        produced = integration._prepare_fabricated_replay(**arguments)
        retained = integration._retain_fabricated_handoff(produced)
        report = integration._report_fabricated_replay(produced, expected=retained)
        body = integration._encode_test_report(report)
        export_hash = sha256(body).hexdigest()  # Retained before mutation/receipt.
        decoded = integration._decode_test_report(
            body,
            expected_sha256=export_hash,
            retained=report,
        )
        guard.close()
    return arguments, produced, retained, report, body, export_hash, decoded, calls


def test_real_full_year_parser_core_reporting_contract(full):
    _, produced, retained, report, body, export_hash, value, calls = full
    assert calls["_parse_verified_publication"] >= 3
    assert calls["_validate_independent_signoff"] >= 1
    assert calls["_replay_verified_publication"] == 1
    assert calls["_replay_minute_core"] == 2
    assert calls["verify_minute_account"] >= 6
    assert calls["minute_reporting_summary"] == 6
    assert integration._encode_test_report(report) == body
    assert integration._bounded_json(value) == body
    assert sha256(body).hexdigest() == export_hash
    assert value["schema"] != integration.preparation.EXPORT_SCHEMA
    assert value["fabricated_only"] is True
    for key in (
        "execution_authorised",
        "economic_publication",
        "source_authentication_proven",
        "external_independence_proven",
    ):
        assert value[key] is False
    assert tuple(r.symbol for r in produced.results) == minute.SYMBOLS
    assert len({r["report_id"] for r in value["reports"]}) == 6
    assert len({p.account_id for p in retained.accounts}) == 6
    assert b"/fabricated-review/" not in body
    assert b'"approval":' not in body and b'"signature":' not in body
    for result in produced.results:
        assert len(result.decisions) == 2195
        assert tuple(a.label for a in result.accounts) == integration._LABELS
        for account in result.accounts:
            assert len(account.marks) == 8784
            assert account.initial.cash == minute.D(10000)
            assert account.marks[-1].reference.at == minute.END - minute.HOUR
        assert result.accounts[0].final.quantity > 0  # No terminal liquidation.
        assert not result.accounts[1].fills  # Cash has no invented trades.
        assert result.accounts[2].fills[0].trade.at == minute.START
    for report_row in value["reports"]:
        assert report_row["replay_fingerprint"] == retained.replay_sha256
        content = {k: v for k, v in report_row.items() if k != "report_id"}
        assert (
            sha256(integration._bounded_json(content)).hexdigest()
            == report_row["report_id"]
        )
        summary = report_row["summary"]
        daily = [p for p in summary["observations"] if p["period"] == "daily"]
        monthly = [p for p in summary["observations"] if p["period"] == "monthly"]
        assert len(daily) == 366 and len(monthly) == 12
        assert daily[59]["start"].startswith("2024-02-29")
        assert daily[-1]["complete"] is False
        assert monthly[-1]["missing_boundary_seconds"] == 3600
        assert daily[-1]["flow_complete"] is True


@pytest.mark.parametrize(
    "name", ("manifest", "authenticated_inputs", "integrity", "signoff")
)
def test_candidate_bytes_fail_upstream_pins(full, name):
    args = full[0] | {name: full[0][name] + b" "}
    with pytest.raises(ValueError, match="External .*bytes/hash mismatch"):
        integration._prepare_fabricated_replay(**args)


@pytest.mark.parametrize("name", integration.preparation.PIN_NAMES)
def test_changed_independent_publication_pin(full, name):
    args = full[0]
    pin = replace(getattr(args["expected"], name), sha256="0" * 64)
    with pytest.raises(ValueError, match="External .*bytes/hash mismatch"):
        integration._prepare_fabricated_replay(
            **(
                args
                | {
                    "expected": replace(args["expected"], **{name: pin}),
                }
            )
        )


def test_repinned_signoff_body_still_requires_real_reconciliation(full):
    args = full[0]
    record = json.loads(args["signoff"])
    record["economic_results"] = True
    body = fixtures.signoff_wire(record)
    with pytest.raises(ValueError, match="sign-off contract/publication mismatch"):
        integration._prepare_fabricated_replay(
            **(
                args
                | {
                    "signoff": body,
                    "expected": replace(
                        args["expected"], signoff=fixtures.fingerprint(body)
                    ),
                }
            )
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "decision",
        "source",
        "price",
        "missing_reference",
        "duplicate_reference",
        "reordered_reference",
        "ledger",
        "fill",
        "mark",
        "market_order",
    ),
)
def test_downstream_mutation_uses_previously_retained_pins(full, mutation):
    produced, retained = full[1:3]
    result = produced.results[0]
    account = result.accounts[0]
    if mutation == "decision":
        changed = replace(result.decisions[0], reason="substitution")
        result = replace(result, decisions=(changed, *result.decisions[1:]))
    elif mutation == "source":
        result = replace(result, source=replace(result.source, file_sha256="0" * 64))
    elif mutation in (
        "price",
        "missing_reference",
        "duplicate_reference",
        "reordered_reference",
    ):
        refs = produced.publication.inputs.references[0]
        if mutation == "price":
            refs = (replace(refs[0], price=minute.D(101)), *refs[1:])
        elif mutation == "missing_reference":
            refs = refs[1:]
        elif mutation == "duplicate_reference":
            refs = (refs[1], *refs[1:])
        else:
            refs = (refs[1], refs[0], *refs[2:])
        inputs = replace(
            produced.publication.inputs,
            references=(refs, produced.publication.inputs.references[1]),
        )
        parsed = replace(produced.publication, inputs=inputs)
        produced = replace(
            produced,
            publication=parsed,
            signoff=replace(produced.signoff, publication=parsed),
        )
    elif mutation == "ledger":
        account = replace(
            account, final=replace(account.final, cash=account.final.cash + 1)
        )
    elif mutation == "fill":
        fill = replace(account.fills[0], slippage_cost=minute.D(99))
        account = replace(account, fills=(fill, *account.fills[1:]))
    elif mutation == "mark":
        mark = replace(account.marks[0], equity=minute.D(1))
        account = replace(account, marks=(mark, *account.marks[1:]))
    else:
        produced = replace(produced, results=tuple(reversed(produced.results)))
    if mutation in ("ledger", "fill", "mark"):
        result = replace(result, accounts=(account, *result.accounts[1:]))
    if mutation != "market_order":
        produced = replace(produced, results=(result, produced.results[1]))
    with pytest.raises(
        ValueError, match="handoff mismatch|counts/order|Market order|Injected/changed"
    ):
        integration._report_fabricated_replay(produced, expected=retained)


def test_independent_account_hash_is_not_rederived(full):
    retained = full[2]
    changed = replace(retained.accounts[0], fingerprint="0" * 64)
    with pytest.raises(ValueError, match="changed after fingerprint retention"):
        integration._report_fabricated_replay(
            full[1],
            expected=replace(
                retained,
                accounts=(changed, *retained.accounts[1:]),
            ),
        )


@pytest.mark.parametrize(
    "mutation",
    ("schema", "extra", "bool_type", "report_id", "decimal_type", "account_id"),
)
def test_export_closed_schema_even_with_repinned_candidate_hash(full, mutation):
    value = json.loads(full[4])
    if mutation == "schema":
        value["schema"] = integration.preparation.EXPORT_SCHEMA
    elif mutation == "extra":
        value["unreviewed"] = "metadata"
    elif mutation == "bool_type":
        value["economic_publication"] = 0
    elif mutation == "decimal_type":
        value["reports"][0]["summary"]["initial_funding"] = 10000
    else:
        value["reports"][0][mutation] = "forged-or-stale"
    body = integration._bounded_json(value)
    with pytest.raises(ValueError, match="verified report/schema mismatch"):
        integration._decode_test_report(
            body, expected_sha256=sha256(body).hexdigest(), retained=full[3]
        )


def test_retained_export_hash_detects_mutation(full):
    with pytest.raises(ValueError, match="export hash mismatch"):
        integration._decode_test_report(
            full[4] + b" ", expected_sha256=full[5], retained=full[3]
        )


@pytest.mark.parametrize("value", (False, 1, None, "true"))
def test_no_genuine_or_implicit_mode(full, value):
    with pytest.raises(ValueError, match="fabricated-only"):
        integration._prepare_fabricated_replay(**(full[0] | {"fabricated_only": value}))


def test_synthetic_result_cannot_be_promoted(full):
    synthetic = reporter_fixtures.invented(hours=4)
    with pytest.raises(ValueError, match="Publication replay type"):
        integration._report_fabricated_replay(
            replace(full[1], results=(synthetic, full[1].results[1])), expected=full[2]
        )


def test_still_closed_public_entry_does_not_inspect_hostile_arguments():
    class Hostile:
        def __getattribute__(self, name):
            raise AssertionError("Hostile argument inspected")

        def __bool__(self):
            raise AssertionError("Hostile truth check")

    for argument in (Hostile(), None, {"fabricated_only": True}, True):
        with pytest.raises(PermissionError):
            gate.replay_genuine_minute_historical(approval=argument)


def test_bounded_serializer_rejects_cycles_floats_and_oversize():
    cycle = []
    cycle.append(cycle)
    for value in (cycle, [0.1], "x" * 1_048_577, [None] * 100_001):
        with pytest.raises(ValueError):
            integration._bounded_json(value)


def test_adapter_unavailable_and_no_trades_use_existing_core():
    result = reporter_fixtures.invented(hours=4, values=("0",), inception="1e20")
    pins = tuple(
        reporting.minute_reporting_fingerprint(a, end_exclusive=result.end_exclusive)
        for a in result.accounts
    )
    summaries = tuple(
        reporting.minute_reporting_summary(
            a, end_exclusive=result.end_exclusive, expected_fingerprint=p
        )
        for a, p in zip(result.accounts, pins, strict=True)
    )
    assert all(not a.fills for a in result.accounts)
    assert summaries[2]["status"] == "unavailable"
    assert summaries[2]["performance"] is None
    assert summaries[2]["observations"] == ()


def test_original_e5_transport_not_promoted(full):
    old = integration.preparation
    with pytest.raises(ValueError):
        old.decode_test_evidence(full[4], expected=old.identity(full[4]))
    assert old.EXPORT_SCHEMA == "stage-04b2e5-fabricated-evidence-v1"


@pytest.mark.parametrize("mutation", ("ledger", "fill", "mark", "consistent_cash_mark"))
def test_account_verifier_and_independent_account_pin_are_distinct(full, mutation):
    produced, retained = full[1:3]
    market = produced.results[0]
    index = 1 if mutation == "consistent_cash_mark" else 0
    account = market.accounts[index]
    if mutation == "ledger":
        account = replace(account, final=replace(account.final, cash=minute.D(0)))
        message = "Final minute ledger mismatch"
    elif mutation == "fill":
        fill = replace(account.fills[0], half_spread_cost=minute.D(0))
        account = replace(account, fills=(fill, *account.fills[1:]))
        message = "Altered minute execution evidence"
    elif mutation == "mark":
        account = replace(
            account,
            marks=(replace(account.marks[0], equity=minute.D(0)), *account.marks[1:]),
        )
        message = "Minute mark differs"
    else:
        mark = account.marks[0]
        account = replace(
            account,
            marks=(
                replace(mark, reference=replace(mark.reference, price=minute.D(123))),
                *account.marks[1:],
            ),
        )
        minute.verify_minute_account(account, end_exclusive=minute.END)
        message = "changed after fingerprint retention"
    accounts = list(market.accounts)
    accounts[index] = account
    changed = replace(
        produced,
        results=(replace(market, accounts=tuple(accounts)), produced.results[1]),
    )
    # Deliberately forge ONLY the outer handoff hash to isolate the downstream
    # verifier and old independently retained account pin, not to accept evidence.
    forged = replace(
        retained,
        replay_sha256=sha256(
            integration._bounded_json(integration._replay_evidence(changed))
        ).hexdigest(),
    )
    with pytest.raises(ValueError, match=message):
        integration._report_fabricated_replay(changed, expected=forged)


def test_original_historical_publication_pins_forbidden_before_parser(
    full, monkeypatch
):
    def forbidden(**kwargs):
        raise AssertionError("Historical candidate reached parser")

    monkeypatch.setattr(
        integration.publication, "_parse_verified_publication", forbidden
    )
    args = full[0]
    pin = integration.publication._Fingerprint(
        **integration.preparation.HISTORICAL_PINS["manifest"]
    )
    with pytest.raises(ValueError, match="Historical publication identities forbidden"):
        integration._prepare_fabricated_replay(
            **(args | {"expected": replace(args["expected"], manifest=pin)})
        )


@pytest.mark.parametrize("name", ("manifest", "integrity", "signoff"))
def test_retained_upstream_bodies_are_revalidated(full, name):
    produced = full[1]
    if name == "signoff":
        changed = replace(
            produced,
            signoff=replace(produced.signoff, body=produced.signoff.body + b" "),
        )
    else:
        bodies = list(produced.publication.bodies)
        index = 0 if name == "manifest" else 2
        bodies[index] += b" "
        parsed = replace(produced.publication, bodies=tuple(bodies))
        changed = replace(
            produced,
            publication=parsed,
            signoff=replace(produced.signoff, publication=parsed),
        )
    with pytest.raises(ValueError, match="External .*bytes/hash mismatch"):
        integration._report_fabricated_replay(changed, expected=full[2])


def test_bound_checked_before_json_or_hash(full, monkeypatch):
    monkeypatch.setattr(integration, "_LIMIT", 16)
    with pytest.raises(ValueError, match="Bounded report bytes"):
        integration._decode_test_report(
            b"x" * 17, expected_sha256="0" * 64, retained=full[3]
        )


@pytest.mark.parametrize("pins", (None, {}, (), True))
def test_report_requires_typed_retained_handoff(full, pins):
    with pytest.raises(ValueError, match="Separately retained handoff pins"):
        integration._report_fabricated_replay(full[1], expected=pins)


@pytest.mark.parametrize("pin", (None, {}, True, ("0" * 64, 1)))
def test_publication_pin_field_types_are_strict(full, pin):
    arguments = full[0]
    with pytest.raises(ValueError):
        integration._prepare_fabricated_replay(
            **(
                arguments
                | {
                    "expected": replace(arguments["expected"], manifest=pin),
                }
            )
        )


def test_full_year_unavailable_bh_contract_from_new_invented_publication(full):
    # Author a second FABRICATED scenario before fixing its input pins: all-zero
    # forecasts and an infeasible inception price. No existing candidate is
    # repaired or silently repinned at the consumer; no original evidence exists.
    original = full[1].publication.inputs
    references = tuple(
        (replace(group[0], price=minute.D("1e20")), *group[1:])
        for group in original.references
    )
    projections = tuple(minute.projection_sha256(group) for group in references)
    source_claims = json.loads(original.source_evidence_json)
    source_claims["projection_sha256"] = projections
    inputs = replace(
        original,
        forecasts=tuple(
            tuple(replace(row, prediction=minute.D(0)) for row in group)
            for group in original.forecasts
        ),
        references=references,
        projection_sha256=projections,
        source_evidence_json=fixtures.operator._json(source_claims),
    )
    science = json.loads(fixtures.auth.authenticated_inputs_json(inputs))
    bodies = fixtures.serialize(science, json.loads(full[0]["integrity"]))
    pins = fixtures.repin(bodies, full[0]["expected"].signoff)
    signoff = fixtures.signoff_wire(fixtures.signoff_record(pins))
    pins = replace(pins, signoff=fixtures.fingerprint(signoff))
    produced = integration._prepare_fabricated_replay(
        **dict(zip(fixtures.bridge.FILES_KEYS, bodies, strict=True)),
        signoff=signoff,
        expected=pins,
        fabricated_only=True,
    )
    retained = integration._retain_fabricated_handoff(produced)
    report = integration._report_fabricated_replay(produced, expected=retained)
    body = integration._encode_test_report(report)
    expected = sha256(body).hexdigest()
    decoded = integration._decode_test_report(
        body, expected_sha256=expected, retained=report
    )
    assert len(decoded["reports"]) == 6
    for market in produced.results:
        assert all(not account.fills for account in market.accounts)
        assert [len(account.marks) for account in market.accounts] == [8784, 8784, 0]
    for row in decoded["reports"]:
        summary = row["summary"]
        if summary["label"] == "buy_and_hold":
            assert summary["status"] == "unavailable"
            assert summary["performance"] is None
            assert summary["observations"] == []
        else:
            assert summary["performance"]["last_mark_pnl"] == "0"

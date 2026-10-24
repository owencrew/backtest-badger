"""E.5e local I/O over invented publications only; never original evidence."""

import json
import socket
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, localcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
import test_genuine_minute_publication as fixtures
import test_genuine_minute_replay as prior

from backtest_badger import local_historical_backtest as runner
from backtest_badger.paper_types import D


def forbidden(*args, **kwargs):
    raise AssertionError("No economics/source acquisition/network/database expected")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(fixtures.fixtures.psycopg, "connect", forbidden)
    monkeypatch.setattr(fixtures.auth, "authenticate_minute_inputs", forbidden)
    monkeypatch.setattr(fixtures.auth.forecast, "load_forecasts", forbidden)
    monkeypatch.setattr(fixtures.auth.minute, "load_minute_execution_data", forbidden)


@pytest.fixture(scope="module")
def invented(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(prior, "uuid4", lambda: SimpleNamespace(hex="e5e-invented"))
        guard = prior.no_io.__wrapped__(patch)
        next(guard)
        bodies, pins, _ = fixtures.fabricated.__wrapped__()
        signoff = fixtures.signoff_wire(fixtures.signoff_record(pins))
        guard.close()
    pins = replace(pins, signoff=fixtures.fingerprint(signoff))
    root = tmp_path_factory.mktemp("e5e-invented-inputs")
    paths = {}
    for name, body in zip(
        runner.preparation.PIN_NAMES, (*bodies, signoff), strict=True
    ):
        paths[name] = root / (name + ".json")
        paths[name].write_bytes(body)
    return paths, pins


@pytest.fixture
def pinned(invented, monkeypatch):
    paths, pins = invented
    monkeypatch.setattr(runner, "_pins", lambda: pins)
    return dict(paths), pins


@pytest.fixture(scope="module")
def full(invented, tmp_path_factory):
    paths, pins = invented
    calls, captured = {}, {}
    root = tmp_path_factory.mktemp("e5e-fabricated-runs")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(runner, "_pins", lambda: pins)
        patch.setattr(socket, "socket", forbidden)
        patch.setattr(fixtures.fixtures.psycopg, "connect", forbidden)
        patch.setattr(fixtures.auth, "authenticate_minute_inputs", forbidden)
        for module, name in (
            (runner.publication, "_parse_verified_publication"),
            (runner.publication, "_validate_independent_signoff"),
            (runner.publication, "_replay_verified_publication"),
            (runner.minute, "_replay_minute_core"),
            (runner.minute, "verify_minute_account"),
            (runner.reporting, "minute_reporting_summary"),
        ):
            original = getattr(module, name)

            def counted(*args, _name=name, _original=original, **kwargs):
                calls[_name] = calls.get(_name, 0) + 1
                result = _original(*args, **kwargs)
                if _name == "_replay_verified_publication":
                    captured["results"] = result
                return result

            patch.setattr(module, name, counted)
        arguments = ["run", "--execute", "--output-dir", str(root)]
        for name, path in paths.items():
            arguments += ["--" + name.replace("_", "-"), str(path)]
        assert runner.main(arguments) == 0
        (first,) = root.iterdir()
        # Second complete replay exercises repeatability, not a cached report.
        second = runner.run(paths, root, execute=True)
    return first, second, calls, captured["results"], pins


def test_full_path_six_accounts_and_repeatability(full):
    first, second, calls, results, pins = full
    assert first != second
    assert calls["_replay_verified_publication"] == 2
    assert calls["_replay_minute_core"] == 4
    assert calls["minute_reporting_summary"] == 12
    assert calls["verify_minute_account"] >= 12
    assert calls["_parse_verified_publication"] >= 6
    assert calls["_validate_independent_signoff"] == 2
    for name in ("summary.json", "summary.md", "private/evidence.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    marker = runner.verify_output(first)
    assert marker["complete"] is True
    metadata = json.loads((first / "run.json").read_bytes())
    assert metadata["input_identities"] == json.loads(runner._bytes(pins))
    assert metadata["execution"]["source_files"]["runner"]["sha256"]
    summary = json.loads((first / "summary.json").read_bytes())
    rows = summary["accounts"]
    assert len({r["account_id"] for r in rows}) == 6
    assert len(summary["ridge_comparisons"]) == 4
    assert "previously_inspected" in summary["research_classification"]
    for row, account in zip(
        rows, (a for r in results for a in r.accounts), strict=True
    ):
        assert row["ledger_verification"] == "passed"
        assert row["complete_day_statistics"]["count"] == 365
        assert account.initial.cash == D(10000)
        assert len(account.marks) == 8784
        assert row["ledger_identity"] == runner.preparation.identity(
            runner._bytes(runner.minute.minute_ledger_records(account))
        )
        assert row[
            "account_fingerprint"
        ] == runner.reporting.minute_reporting_fingerprint(
            account, end_exclusive=runner.minute.END
        )
        if account.label == "cash":
            assert row["performance"]["funding_relative_marked_return"] == "0"
            assert row["descriptive_statistics"]["zero_rate_sharpe"]["value"] is None
            assert not account.fills
        else:
            assert account.final.quantity > 0  # No forced terminal liquidation.
    details = json.loads((first / "private/evidence.json").read_bytes())
    for report in details["reports"]:
        observations = report["summary"]["observations"]
        assert len(observations) == 378
        assert sum(o["complete"] for o in observations) == 376
    for name in ("summary.json", "private/evidence.json"):
        body = (first / name).read_bytes()
        assert b'"approval":' not in body and b'"signature":' not in body
        assert b"/fabricated-review/" not in body


def test_preflight_has_no_economics_or_output(pinned, monkeypatch):
    paths, pins = pinned
    monkeypatch.setattr(runner.publication, "_replay_verified_publication", forbidden)
    monkeypatch.setattr(runner.minute, "_replay_minute_core", forbidden)
    monkeypatch.setattr(runner, "_write", forbidden)
    assert runner.preflight(paths).publication.pins == pins


@pytest.mark.parametrize("name", runner.preparation.PIN_NAMES)
@pytest.mark.parametrize("change", ("tamper", "truncate", "missing", "wrong_pin"))
def test_input_failures_before_parser_or_economics(
    pinned, tmp_path, monkeypatch, name, change
):
    paths, pins = pinned
    monkeypatch.setattr(runner.publication, "_parse_verified_publication", forbidden)
    monkeypatch.setattr(runner.publication, "_replay_verified_publication", forbidden)
    if change == "wrong_pin":
        bad = replace(pins, **{name: replace(getattr(pins, name), sha256="0" * 64)})
        monkeypatch.setattr(runner, "_pins", lambda: bad)
    else:
        body = paths[name].read_bytes()
        paths[name] = tmp_path / "changed.json"
        if change != "missing":
            paths[name].write_bytes(
                body[:-1] if change == "truncate" else b"!" + body[1:]
            )
    with pytest.raises(ValueError, match=name):
        runner.preflight(paths)


@pytest.mark.parametrize("change", ("bad_status", "changed_counts", "malformed"))
def test_signoff_structure_even_with_invented_repin(
    pinned, tmp_path, monkeypatch, change
):
    paths, pins = pinned
    record = json.loads(paths["signoff"].read_bytes())
    if change == "bad_status":
        record["status"] = "FAIL"
    else:
        record["scientific_counts"]["forecasts"] = 1
    body = b"not json" if change == "malformed" else fixtures.signoff_wire(record)
    paths["signoff"] = tmp_path / "bad-signoff.json"
    paths["signoff"].write_bytes(body)
    monkeypatch.setattr(
        runner, "_pins", lambda: replace(pins, signoff=fixtures.fingerprint(body))
    )
    monkeypatch.setattr(runner.publication, "_replay_verified_publication", forbidden)
    with pytest.raises(ValueError):
        runner.preflight(paths)


@pytest.mark.parametrize("change", ("protocol", "step", "fees", "method", "period"))
def test_changed_method_before_input_read(pinned, monkeypatch, change):
    if change == "protocol":
        monkeypatch.setattr(runner.minute, "PROTOCOL_SHA256", "0" * 64)
    elif change == "step":
        monkeypatch.setattr(runner.minute, "QUANTITY_STEP", D("0.01"))
    elif change == "fees":
        monkeypatch.setattr(runner.accounting, "FEE_RATE", D("0.002"))
    elif change == "method":
        monkeypatch.setitem(runner.preparation.METHOD, "threshold", "1")
    else:
        monkeypatch.setattr(runner.minute, "END", datetime(2026, 1, 1, tzinfo=UTC))
    monkeypatch.setattr(Path, "open", forbidden)
    with pytest.raises(ValueError, match="methodology"):
        runner.preflight(pinned[0])


def test_consent_and_cli_rejection_before_input_access(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "preflight", forbidden)
    with pytest.raises(ValueError, match="consent"):
        runner.run({}, tmp_path)
    arguments = ["run", "--output-dir", str(tmp_path)]
    for name in runner.preparation.PIN_NAMES:
        arguments += ["--" + name.replace("_", "-"), "unused"]
    with pytest.raises(SystemExit) as error:
        runner.main(arguments)
    assert error.value.code == 2


def test_default_pins_are_retained_and_no_cli_override():
    pins = runner._pins()
    assert pins.authenticated_inputs.bytes == 15272413
    assert (
        pins.manifest.sha256
        == "3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea"
    )
    with pytest.raises(SystemExit) as error:
        runner.main(["preflight", "--expected-pins", "invented"])
    assert error.value.code == 2


@pytest.mark.parametrize("change", ("report", "costs", "ledger", "account_identity"))
def test_report_ledger_inconsistency(full, monkeypatch, change):
    account = full[3][0].accounts[0]
    fingerprint = runner.reporting.minute_reporting_fingerprint(
        account, end_exclusive=runner.minute.END
    )
    if change in ("report", "costs"):
        original = runner.reporting.minute_reporting_summary

        def altered(*args, **kwargs):
            summary = original(*args, **kwargs)
            if change == "report":
                summary["performance"]["last_mark_pnl"] = D(123)
            else:
                summary["costs_by_side"]["BUY"]["fees"] = D(123)
            return summary

        monkeypatch.setattr(runner.reporting, "minute_reporting_summary", altered)
    else:
        final = replace(account.final, cash=account.final.cash + 1)
        account = (
            replace(account, final=final)
            if change == "ledger"
            else replace(account, label="cash")
        )
    with pytest.raises(ValueError):
        runner._account_report(account, fingerprint)


def test_statistics_defined_values_partial_exclusion_and_decimal_context():
    summary = {
        "status": "available",
        "last_observed_mark": SimpleNamespace(
            reference=SimpleNamespace(at=runner.minute.START + timedelta(days=365)),
            equity=D(11000),
        ),
        "observations": [
            {"period": "daily", "complete": complete, "return": value}
            for complete, value in (
                (True, D(".01")),
                (True, D("-.01")),
                (False, D(1000)),
            )
        ],
    }
    stats = runner._descriptive_statistics(summary)
    assert stats["annualised_return"]["value"] == D(".1")
    assert stats["zero_rate_sharpe"]["value"] == 0
    assert float(stats["annualised_daily_volatility"]["value"]) == pytest.approx(
        (0.0002 * 365) ** 0.5
    )
    with localcontext() as context:
        context.prec, context.rounding = 6, ROUND_DOWN
        assert runner._descriptive_statistics(summary) == stats
    # Repeated long Decimals must not acquire variance from rounded summation.
    summary["observations"] = [
        {"period": "daily", "complete": True, "return": D("0." + "1234567890" * 8)}
        for _ in range(365)
    ]
    constant = runner._descriptive_statistics(summary)
    assert constant["annualised_daily_volatility"]["value"] == 0
    assert constant["zero_rate_sharpe"]["value"] is None
    summary["observations"] = []
    assert (
        runner._descriptive_statistics(summary)["annualised_daily_volatility"]["value"]
        is None
    )
    summary["status"] = "unavailable"
    assert all(
        v == {"value": None, "reason": "account_unavailable"}
        for v in runner._descriptive_statistics(summary).values()
    )


def test_unavailable_account_preserved(full):
    account = full[3][0].accounts[2]
    unavailable = replace(
        account,
        final=account.initial,
        fills=(),
        marks=(),
        status="unavailable",
        reason="inception_full_fee_affordable_buy_infeasible",
    )
    pin = runner.reporting.minute_reporting_fingerprint(
        unavailable, end_exclusive=runner.minute.END
    )
    row, detail = runner._account_report(unavailable, pin)
    assert row["performance"] is None and row["costs_by_side"] is None
    assert detail["summary"]["observations"] == ()
    assert row["reason"] == unavailable.reason


@pytest.fixture
def output_only(monkeypatch):
    """Small I/O lifecycle tests; the full fixture above tests the scientific path."""
    parsed = SimpleNamespace(pins=runner._pins())
    monkeypatch.setattr(
        runner, "preflight", lambda paths: SimpleNamespace(publication=parsed)
    )
    monkeypatch.setattr(
        runner.publication, "_replay_verified_publication", lambda *a, **k: ()
    )
    monkeypatch.setattr(
        runner, "_reports", lambda *a: ({"accounts": [], "ridge_comparisons": []}, [])
    )


@pytest.mark.parametrize(
    "failure", ("replay", "summary", "partial_write", "corrupt_readback")
)
def test_incomplete_output_has_no_completion_marker(
    output_only, tmp_path, monkeypatch, failure
):
    original = runner._write

    def failing(path, body):
        if path.name == "summary.json":
            if failure == "partial_write":
                path.with_suffix(".json.tmp").write_bytes(body[:10])
                raise OSError("injected partial write")
            if failure == "corrupt_readback":
                return original(path, b"corrupt")
            raise OSError("injected summary failure")
        original(path, body)

    if failure == "replay":
        monkeypatch.setattr(
            runner.publication, "_replay_verified_publication", forbidden
        )
    else:
        monkeypatch.setattr(runner, "_write", failing)
    with pytest.raises((ValueError, OSError, AssertionError)):
        runner.run({}, tmp_path, execute=True)
    (directory,) = tmp_path.iterdir()
    assert (directory / "run.json").exists()
    assert not (directory / "COMPLETE.json").exists()
    with pytest.raises(ValueError, match="Incomplete"):
        runner.verify_output(directory)


def test_overwrite_prevention(output_only, tmp_path, monkeypatch):
    instant = datetime(2026, 10, 24, tzinfo=UTC)
    monkeypatch.setattr(runner, "datetime", SimpleNamespace(now=lambda zone: instant))
    monkeypatch.setattr(runner, "uuid4", lambda: SimpleNamespace(hex="fixed-test-id"))
    directory = runner.run({}, tmp_path, execute=True)
    before = (directory / "COMPLETE.json").read_bytes()
    with pytest.raises(FileExistsError):
        runner.run({}, tmp_path, execute=True)
    assert (directory / "COMPLETE.json").read_bytes() == before
    with pytest.raises(FileExistsError):
        runner._write(directory / "summary.md", b"replacement")
    assert (directory / "summary.md").read_bytes() != b"replacement"


@pytest.mark.parametrize("change", ("tamper", "missing", "marker"))
def test_completion_reader_rejects_inconsistent_output(output_only, tmp_path, change):
    directory = runner.run({}, tmp_path, execute=True)
    if change == "tamper":
        (directory / "summary.md").write_bytes(b"changed")
    elif change == "missing":
        (directory / "private/evidence.json").unlink()
    else:
        (directory / "COMPLETE.json").write_bytes(b"{}")
    with pytest.raises(ValueError):
        runner.verify_output(directory)


def test_legacy_public_gates_remain_closed():
    from backtest_badger import genuine_backtest_custody, genuine_minute_replay

    with pytest.raises(PermissionError):
        genuine_minute_replay.replay_genuine_minute_historical(approval=None)
    with pytest.raises(PermissionError):
        genuine_backtest_custody.run_genuine_historical_operator()

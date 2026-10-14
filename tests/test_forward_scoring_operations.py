"""Stage 3D tests use synthetic forecasts, clocks and targets, never Binance."""

import copy
import json
import multiprocessing
import os
import time
from contextlib import nullcontext
from datetime import timedelta
from pathlib import Path

import psycopg
import pytest
from test_evaluation import research_source  # noqa: F401
from test_forward import recording, synthetic_fit  # noqa: F401
from test_forward_evaluation import (  # noqa: F401
    CAPTURED,
    SETTLED,
    forbidden,
    rewrite,
)
from test_forward_evaluation import (
    evidence as evidence_fixture,
)

from backtest_badger import forward
from backtest_badger import forward_evaluation as fe
from backtest_badger import forward_scoring_operations as ops

evidence = evidence_fixture


def cycle(e, **kwargs):
    return ops.run_cycle(
        records=e["path"].parent,
        outcomes=e["outcomes"],
        collector_operations=e["operations"],
        operations=e["path"].parent.parent / "scoring-operations",
        clock=kwargs.pop("clock", lambda: CAPTURED),
        connect=kwargs.pop("connect", lambda: nullcontext(None)),
        **kwargs,
    )


def status(e, **kwargs):
    return ops.status_report(
        records=e["path"].parent,
        outcomes=e["outcomes"],
        collector_operations=e["operations"],
        operations=e["path"].parent.parent / "scoring-operations",
        clock=kwargs.pop("clock", lambda: CAPTURED),
    )


def clone(e, *, steps=0, symbol="ETHUSDT"):
    """Construct separate synthetic retained evidence, never edit genuine records."""
    record = copy.deepcopy(e["record"])
    shift = steps * forward.STEP
    market = record["market"]
    market.update(
        symbol=symbol, base_asset=symbol[:-4], market_id=1 if symbol == "BTCUSDT" else 2
    )
    candles = [fe.candle_from_json(c) for c in record["source_candles"]]
    for candle in candles:
        candle["market_id"] = market["market_id"]
        candle["source_url"] = candle["source_url"].replace("BTCUSDT", symbol)
        for key in forward.TIME_FIELDS:
            candle[key] += shift
    model = record["model"]
    model["symbol"] = symbol
    model.pop("model_recipe_sha256")
    model["model_recipe_sha256"] = fe.sha256(fe.canonical(model))
    predictions = {
        p["model_id"]: p["predicted_log_return_4h"] for p in record["predictions"]
    }
    value = forward.evidence(
        market,
        candles,
        forward.validate_window(
            market,
            candles,
            candles[-1]["open_time"],
            fe.utc_time(record["captured_at"]) + shift,
        ),
        predictions,
        model,
        *(
            fe.utc_time(record[k]) + shift
            for k in ("captured_at", "calculated_at", "issued_at")
        ),
    )
    path = e["path"].parent / f"{value['record_id']}.json"
    path.touch(exist_ok=False)
    rewrite(path, value)
    fe.load_prediction(path)
    return path


@pytest.mark.parametrize("offset", [-1, -0.000001, 0, 0.000001, 86400 * 365])
def test_maturity_boundary(evidence, offset):
    now = SETTLED + timedelta(seconds=offset)
    journal, code = cycle(
        evidence,
        clock=lambda: now,
        connect=forbidden if offset < 0 else lambda: nullcontext(None),
    )
    assert code == 0
    assert journal["results"][0]["reason"] == (
        "pending_not_settled" if offset < 0 else "scored"
    )
    assert journal["started_at"] == now.isoformat()


def test_multiple_pending_and_missing_retry(evidence, monkeypatch):
    clone(evidence)
    monkeypatch.setattr(fe, "read_target", lambda *a: [])
    journal, code = cycle(evidence)
    assert code == 0
    assert [r["reason"] for r in journal["results"]] == ["pending_target_missing"] * 2
    assert len(status(evidence)["mature_unscored"]) == 2
    monkeypatch.setattr(fe, "read_target", lambda *a: [evidence["target"]])
    journal, code = cycle(evidence)
    assert journal["results"][0]["status"] == "scored"
    assert journal["results"][1]["status"] == "failed"  # Wrong-market target rejected.
    assert code == 1


def test_unexpired_multiple_no_configuration(evidence):
    clone(evidence)
    journal, code = cycle(
        evidence, clock=lambda: SETTLED - timedelta(seconds=1), connect=forbidden
    )
    assert code == 0
    assert [r["status"] for r in journal["results"]] == ["pending", "pending"]
    assert (
        len(
            status(evidence, clock=lambda: SETTLED - timedelta(seconds=1))[
                "pending_predictions"
            ]
        )
        == 2
    )


def test_existing_valid_score_no_db_and_no_mutation(evidence):
    assert cycle(evidence)[1] == 0
    paths = [evidence["path"], evidence["outcomes"] / evidence["path"].name]
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
    journal, code = cycle(evidence, connect=forbidden)
    assert code == 0 and journal["results"][0]["status"] == "already_scored"
    assert before == [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
    report = status(evidence)
    assert report["evidence_valid"] and report["latest_successful_cycle"]
    assert len(report["scored"]) == 1


def test_database_failure_isolated_and_redacted(evidence, monkeypatch):
    clone(evidence)
    calls = []

    def connect():
        calls.append(1)
        if len(calls) == 1:
            raise psycopg.OperationalError("password=SECRET host=PRIVATE")
        return nullcontext(None)

    monkeypatch.setattr(fe, "read_target", lambda *a: [])
    journal, code = cycle(evidence, connect=connect)
    assert code == 1 and len(calls) == 2
    assert [r["status"] for r in journal["results"]] == ["failed", "pending"]
    assert "SECRET" not in json.dumps(journal)
    assert "PRIVATE" not in json.dumps(journal)
    assert status(evidence)["failures"]
    assert cycle(evidence)[1] == 0
    assert status(evidence)["failures"]  # Historical failure survives recovery.


@pytest.mark.parametrize("kind", ["prediction", "outcome", "orphan", "collector"])
def test_invalid_evidence_visible_and_never_repaired(evidence, kind):
    e = evidence
    if kind == "prediction":
        path = e["path"].parent / "broken.json"
    elif kind in ("outcome", "orphan"):
        e["outcomes"].mkdir()
        path = e["outcomes"] / (e["path"].name if kind == "outcome" else "orphan.json")
    else:
        path = e["operations"] / "broken.json"
    path.write_bytes(b'{"password":"DO_NOT_LOG"')
    before = path.read_bytes()
    journal, _ = cycle(e)
    assert "DO_NOT_LOG" not in json.dumps(journal)
    assert path.read_bytes() == before
    assert not status(e)["evidence_valid"]
    if kind == "prediction":
        assert {r["status"] for r in journal["results"]} == {"failed", "scored"}


def test_corrupt_existing_outcome_avoids_database(evidence):
    cycle(evidence)
    path = evidence["outcomes"] / evidence["path"].name
    value = json.loads(path.read_bytes())
    value["actual_log_return_4h"] = 2
    rewrite(path, value, "outcome_sha256")
    journal, code = cycle(evidence, connect=forbidden)
    assert code == 1 and journal["results"][0]["status"] == "failed"


def test_long_backlog_rotates_past_pending_and_failures(evidence, monkeypatch):
    for n in range(1, 31):
        clone(evidence, steps=n, symbol="BTCUSDT" if n % 2 else "ETHUSDT")
    original = fe.score
    visited = []

    def score(path, **kwargs):
        visited.append(path.name)
        if path.name == evidence["path"].name:
            raise psycopg.OperationalError("unavailable")
        return original(path, **kwargs)

    monkeypatch.setattr(fe, "score", score)
    monkeypatch.setattr(fe, "read_target", lambda *a: [])
    now = CAPTURED + timedelta(days=1000)
    for _ in range(7):
        journal, _ = cycle(evidence, batch_size=5, clock=lambda: now)
        assert len(journal["results"]) == 5
        assert journal["deferred_count"] == 26
    assert len(set(visited[:31])) == 31
    assert visited.count(evidence["path"].name) == 2


@pytest.mark.parametrize("phase", ["initial", "progress", "cursor", "final"])
def test_operational_write_failure(evidence, monkeypatch, phase):
    clone(evidence)
    original = ops.write_snapshot
    calls = []

    def write(path, value):
        calls.append(path)
        fail = (
            (phase == "initial" and len(calls) == 1)
            or (phase == "progress" and len(calls) == 3)
            or (phase == "cursor" and path.name == "cursor.json")
            or (phase == "final" and value.get("state") == "complete")
        )
        if fail:
            raise OSError("secret disk failure")
        return original(path, value)

    monkeypatch.setattr(ops, "write_snapshot", write)
    journal, code = cycle(evidence)
    assert code == 1
    assert "secret" not in json.dumps(journal)
    assert len(journal["results"]) == {"initial": 0, "cursor": 1}.get(phase, 2)
    if phase in ("initial", "cursor"):
        assert not evidence["outcomes"].exists()
    monkeypatch.setattr(ops, "write_snapshot", original)
    assert cycle(evidence)[0]["results"]


def test_partial_snapshots_and_invalid_state(evidence):
    folder = evidence["path"].parent.parent / "scoring-operations"
    (folder / "state").mkdir(parents=True)
    (folder / ".scoring-ab.partial").write_bytes(b"unfinished")
    (folder / "state/cursor.json").write_bytes(b"invalid")
    journal, code = cycle(evidence, connect=forbidden)
    assert code == 1 and "invalid_cursor" in journal["errors"]
    report = status(evidence)
    assert (
        report["invalid_cursor"] and report["partial_files"]["scoring_operations"] == 1
    )
    assert not report["evidence_valid"]


def test_fsync_failure_retains_partial(evidence, monkeypatch):
    folder = evidence["path"].parent.parent / "scoring-operations"

    def fail(fd):
        raise OSError("disk")

    monkeypatch.setattr(os, "fsync", fail)
    assert cycle(evidence)[1] == 1
    assert list(folder.glob("*.partial"))
    assert not evidence["outcomes"].exists()


def test_timeout_rotates_and_recovers(evidence, monkeypatch):
    clone(evidence)
    original = fe.score
    monkeypatch.setattr(fe, "score", lambda *a, **k: time.sleep(5))
    journal, code = cycle(evidence, max_seconds=0.05, batch_size=1)
    assert code == 1 and journal["state"] == "timed_out"
    assert journal["results"][0]["reason"] == "interrupted_or_time_limit"
    monkeypatch.setattr(fe, "score", original)
    monkeypatch.setattr(fe, "read_target", lambda *a: [])
    next_journal, code = cycle(evidence, batch_size=1)
    assert code == 0
    assert (
        next_journal["results"][0]["record_file"]
        != journal["results"][0]["record_file"]
    )


def test_clock_reversal_visible(evidence):
    stamps = iter([CAPTURED, CAPTURED - timedelta(seconds=1), CAPTURED])
    journal, code = cycle(evidence, clock=lambda: next(stamps), connect=forbidden)
    assert code == 1 and journal["state"] == "failed"


@pytest.mark.parametrize("clock_value", [CAPTURED.replace(tzinfo=None), "invalid"])
def test_invalid_clock_rejected(evidence, clock_value):
    with pytest.raises((ValueError, AttributeError, TypeError)):
        cycle(evidence, clock=lambda: clock_value, connect=forbidden)


def test_process_overlap_termination_and_publication_recovery(evidence):
    context = multiprocessing.get_context("fork")
    ready = context.Event()

    def worker():
        original = fe.score

        def score(*args, **kwargs):
            result = original(*args, **kwargs)
            ready.set()  # Published, but journal still says running.
            time.sleep(30)
            return result

        fe.score = score
        cycle(evidence)

    process = context.Process(target=worker)
    process.start()
    try:
        assert ready.wait(10)
        journal, code = cycle(evidence, connect=forbidden)
        assert code == 2 and journal["state"] == "busy"
        assert status(evidence)["incomplete_cycles"]
    finally:
        process.terminate()
        process.join(10)
    journal, code = cycle(evidence, connect=forbidden)
    assert code == 0 and journal["results"][0]["status"] == "already_scored"
    assert status(evidence)["incomplete_cycles"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("state", "unknown"),
        ("finished_at", None),
        ("results", "bad"),
        ("discovered_count", -1),
        ("run_id", "wrong"),
    ],
)
def test_invalid_journal_not_success(evidence, field, value):
    journal, _ = cycle(evidence)
    path = (
        evidence["path"].parent.parent
        / "scoring-operations"
        / f"{journal['run_id']}.json"
    )
    journal[field] = value
    ops.write_snapshot(path, journal)
    report = status(evidence)
    assert report["invalid_scoring_journals"]
    assert report["latest_successful_cycle"] is None


@pytest.mark.parametrize(
    "argument", ["--as-of", "--clock", "--records", "--batch-size"]
)
def test_cli_rejects_overrides(argument):
    with pytest.raises(SystemExit) as error:
        ops.main(["cycle", argument, "arbitrary"])
    assert error.value.code == 2


def test_cli_offline_and_redaction(evidence, monkeypatch, capsys):
    report = status(evidence)
    monkeypatch.setattr(ops, "status_report", lambda: report)
    monkeypatch.setattr(fe, "local_connection", forbidden)
    assert ops.main(["status"]) == 0
    assert json.loads(capsys.readouterr().out)["mature_unscored"]

    def fail():
        raise RuntimeError("password=SECRET")

    monkeypatch.setattr(ops, "run_cycle", fail)
    assert ops.main(["cycle"]) == 1
    assert "SECRET" not in capsys.readouterr().err


def test_launchagent_configuration():
    import plistlib

    path = Path("ops/launchd/com.backtestbadger.forward-scoring.plist")
    value = plistlib.loads(path.read_bytes())
    assert value["StartInterval"] == 300
    assert value["Umask"] == 63
    assert value["ProgramArguments"][-3:] == [
        "-m",
        "backtest_badger.forward_scoring_operations",
        "cycle",
    ]
    assert "forward-scoring-operations" in value["StandardErrorPath"]
    assert value["ProgramArguments"][0].startswith("/")


def test_unreadable_inventory_is_not_empty_success(tmp_path, monkeypatch):
    records = tmp_path / "records"
    records.mkdir()
    original = Path.iterdir

    def read(path):
        if path == records:
            raise PermissionError("private-path")
        return original(path)

    monkeypatch.setattr(Path, "iterdir", read)
    journal, code = ops.run_cycle(
        records=records,
        outcomes=tmp_path / "outcomes",
        collector_operations=tmp_path / "collector",
        operations=tmp_path / "ops",
        connect=forbidden,
    )
    assert code == 1 and journal["state"] == "failed"
    assert "private-path" not in json.dumps(journal)
    with pytest.raises(PermissionError):
        ops.status_report(
            records=records,
            outcomes=tmp_path / "outcomes",
            collector_operations=tmp_path / "collector",
            operations=tmp_path / "ops",
        )

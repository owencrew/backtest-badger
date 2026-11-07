"""Original-format fabricated files only. Never open the outcome directory."""

import json
import shutil
from datetime import timedelta
from pathlib import Path

import pytest

from backtest_badger import forward, forward_evaluation
from backtest_badger import paper_fixture as fx
from backtest_badger.paper_forward_adapter import EvidenceError, read_forecast
from backtest_badger.paper_strategy import evaluate_strategy
from backtest_badger.paper_types import D, eligible_forecast


@pytest.fixture
def sources(tmp_path):
    records = tmp_path / "records"
    ops = tmp_path / "operations"
    records.mkdir()
    ops.mkdir()
    r, j = [
        sorted((fx.ROOT / folder).glob("*.json"))[0]
        for folder in ("records", "operations")
    ]
    return Path(shutil.copy(r, records)), Path(shutil.copy(j, ops))


def read(sources, at=fx.ISSUED):
    r, j = sources
    return read_forecast(
        fx.portfolio(), fx.OPEN, r.parent, j.parent, fx.fixed_clock(at)
    )


def revise(r, j, mutate):
    record = json.loads(r.read_bytes())
    mutate(record)
    record.pop("content_sha256")
    record["content_sha256"] = forward.sha256(forward.canonical(record))
    body = forward.canonical(record) + b"\n"
    r.write_bytes(body)
    journal = json.loads(j.read_bytes())
    journal["markets"]["BTCUSDT"].update(
        file_sha256=forward.sha256(body), content_sha256=record["content_sha256"]
    )
    j.write_bytes(forward.canonical(journal))


def test_original_bytes_and_worker_discovery(sources, monkeypatch):
    monkeypatch.setattr(
        forward_evaluation, "read_target", lambda *a: pytest.fail("outcome")
    )
    original = [f.read_bytes() for f in sources]
    at = fx.ISSUED + timedelta(seconds=1)
    o = read(sources, at)
    assert o.forecast.issued_at == fx.ISSUED and o.forecast.observed_at == at
    assert o.forecast.automation_sha256 == forward.sha256(original[1])
    assert o.forecast.file_sha256 == forward.sha256(original[0])
    assert eligible_forecast(o.forecast, at)
    assert o.prediction_id == o.forecast.record_id + ":ridge"
    assert [f.read_bytes() for f in sources] == original


@pytest.mark.parametrize(
    "value,target", [(1e-12, 0), (1.0000000000000002e-12, 1), (0, 0), (-1e-10, 0)]
)
def test_recorded_decimal(sources, value, target):
    revise(
        *sources, lambda r: r["predictions"][2].update(predicted_log_return_4h=value)
    )
    f = read(sources).forecast
    assert f.prediction == D(str(value)) and evaluate_strategy(f.prediction) == target


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(schema_version=2),
        lambda r: r["market"].update(symbol="ETHUSDT"),
        lambda r: r["predictions"][2].update(model_id="zero"),
        lambda r: r["predictions"][2].update(predicted_log_return_4h="NaN"),
        lambda r: r["predictions"][2].update(
            prediction_id=r["predictions"][1]["prediction_id"]
        ),
        lambda r: r["predictions"].pop(),
        lambda r: r["predictions"].append(r["predictions"][0]),
        lambda r: r.update(source_open_time=fx.ISSUED.isoformat()),
        lambda r: r["model"]["parameters"]["ridge"].update(alpha=42),
    ],
)
def test_invalid_record_with_valid_outer_hash(sources, mutate):
    revise(*sources, mutate)
    with pytest.raises(EvidenceError, match="invalid_original"):
        read(sources)


@pytest.mark.parametrize(
    "mutation",
    [
        "bad_bytes",
        "duplicate_key",
        "hash",
        "timestamp",
        "path",
        "journal",
        "future",
        "duplicate",
        "absent",
    ],
)
def test_conflicts_pause(sources, mutation):
    r, j = sources
    doc = json.loads(j.read_bytes())
    entry = doc["markets"]["BTCUSDT"]
    if mutation == "bad_bytes":
        r.write_bytes(r.read_bytes() + b" ")
    elif mutation == "duplicate_key":
        j.write_bytes(
            j.read_bytes().replace(b'{"deadline"', b'{"state":"complete","deadline"')
        )
    elif mutation == "absent":
        r.unlink()
    elif mutation == "journal":
        j.write_bytes(b"{")
    elif mutation == "duplicate":
        doc["run_id"] = "a" * 32
        j = j.with_name(j.name.replace("1" * 32, "a" * 32))
        j.write_bytes(forward.canonical(doc))
    else:
        if mutation == "hash":
            entry["file_sha256"] = "0" * 64
        elif mutation == "path":
            entry["record_path"] = "../elsewhere/" + r.name
        elif mutation == "timestamp":
            doc["finished_at"] = fx.OPEN.isoformat()
        elif mutation == "future":
            doc["finished_at"] = (fx.ISSUED + timedelta(seconds=10)).isoformat()
        j.write_bytes(forward.canonical(doc))
    with pytest.raises(EvidenceError):
        read(sources)


def test_missing_late_and_unattributed(sources):
    r, j = sources
    deadline = fx.OPEN + timedelta(hours=4, minutes=16)
    assert not eligible_forecast(read(sources, deadline).forecast, deadline)
    j.unlink()
    assert read(sources).forecast.cohort == "timely_unattributed"
    record = json.loads(r.read_bytes())
    record["issued_at"] = deadline.isoformat()
    record.pop("content_sha256")
    record["content_sha256"] = forward.sha256(forward.canonical(record))
    r.write_bytes(forward.canonical(record) + b"\n")
    assert read(sources, deadline).forecast.cohort == "secondary_late_manual"
    r.unlink()
    assert read(sources) is None
    j.parent.rmdir()
    with pytest.raises(EvidenceError, match="original_unavailable"):
        read(sources)


@pytest.mark.parametrize("link", ["file", "root"])
def test_symlinks_and_clock_reversal(sources, link):
    r, j = sources
    with pytest.raises(EvidenceError):
        read(sources, fx.ISSUED - timedelta(seconds=1))
    original = r if link == "file" else r.parent
    moved = original.with_name("moved")
    original.rename(moved)
    original.symlink_to(moved)
    with pytest.raises(EvidenceError, match="invalid_original"):
        read(sources)

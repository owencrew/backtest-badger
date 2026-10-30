"""Mocked v2 publication faults; all fixtures synthetic, never network writes."""

import copy
import fcntl
import hashlib
import io
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from test_public_export import exporter
from test_public_export import synthetic as synthetic
from test_public_v2 import add_row, enrich, summary


@pytest.fixture
def publisher(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "scripts"))
    import publish_forward_v2

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 15, 13, tzinfo=UTC)

    monkeypatch.setattr(publish_forward_v2, "datetime", Clock)
    return publish_forward_v2


@pytest.fixture
def candidate(publisher, synthetic):
    import public_forward_v2

    report, rows, clock = enrich(synthetic)
    add_row(rows, symbol="ETHUSDT", hour=4)
    add_row(rows, hour=12, scored=False)
    add_row(rows, symbol="ETHUSDT", hour=12, scored=False)
    summary(report, rows)
    return public_forward_v2.project(report, rows, clock)


class Storage:
    def __init__(self, fault=None):
        self.fault = fault
        self.body = None
        self.calls = []

    def put_object(self, **kwargs):
        self.calls.append(("put", kwargs))
        if self.fault == "write":
            raise OSError("mock write failure")
        self.body = kwargs["Body"]
        if self.fault == "lost_ack":
            raise TimeoutError("mock lost acknowledgement after remote write")
        return {
            "ResponseMetadata": {"HTTPStatusCode": 500 if self.fault == "ack" else 200}
        }

    def get_object(self, **kwargs):
        self.calls.append(("get", kwargs))
        if self.fault == "read":
            raise OSError("mock read failure")
        return {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "Body": io.BytesIO(b"wrong hash" if self.fault == "hash" else self.body),
            "ContentType": "text/html"
            if self.fault == "metadata"
            else "application/json",
            "CacheControl": "public, max-age=60, must-revalidate",
        }


def setup(publisher, candidate, tmp_path, monkeypatch):
    import public_forward_v2

    sources = [tmp_path / n for n in ("records", "outcomes", "operations")]
    output = tmp_path / publisher.STATE_NAME
    exporter.write_candidate(candidate, output)
    monkeypatch.setattr(public_forward_v2, "prepare", lambda *args: candidate)
    v1 = tmp_path / "last-success.json"
    v1.write_bytes(b"untouched v1 bytes")
    return sources, output, v1


@pytest.mark.parametrize(
    "destination",
    [
        "backtest-badger-forward/forward-v1.json",
        "other/forward-v2.json",
        "backtest-badger-forward/private.json",
        "backtest-badger-forward/forward-v2.json/",
    ],
)
def test_only_v2_destination(publisher, tmp_path, destination):
    with pytest.raises(ValueError, match="destination"):
        publisher.publish(
            tmp_path,
            tmp_path,
            tmp_path,
            tmp_path / publisher.STATE_NAME,
            destination=destination,
        )
    assert not list(tmp_path.iterdir())


def test_upload_exact_bytes_and_private_rollback(
    publisher, candidate, tmp_path, monkeypatch
):
    sources, output, v1 = setup(publisher, candidate, tmp_path, monkeypatch)
    # Noncanonical whitespace proves rollback retains exact original bytes.
    old = json.dumps(candidate).encode()
    output.write_bytes(old)
    candidate["generated_at"] = "2026-10-15T13:00:01Z"
    storage = Storage()
    monkeypatch.setattr(publisher, "client", lambda: storage)
    digest = publisher.publish(*sources, output)
    assert digest == hashlib.sha256(storage.body).hexdigest()
    assert output.read_bytes() == storage.body
    assert (tmp_path / "previous-success-v2.json").read_bytes() == old
    assert output.stat().st_mode & 0o777 == 0o600
    assert v1.read_bytes() == b"untouched v1 bytes"
    assert [k for k, _ in storage.calls] == ["put", "get"]
    assert all(
        k["Bucket"] == "backtest-badger-forward" and k["Key"] == "forward-v2.json"
        for _, k in storage.calls
    )


@pytest.mark.parametrize(
    "fault", ["hash", "write", "read", "lost_ack", "ack", "metadata"]
)
def test_remote_failure_preserves_success(
    publisher, candidate, tmp_path, monkeypatch, fault
):
    sources, output, v1 = setup(publisher, candidate, tmp_path, monkeypatch)
    old = output.read_bytes()
    storage = Storage(fault)
    monkeypatch.setattr(publisher, "client", lambda: storage)
    with pytest.raises((OSError, ValueError)):
        publisher.publish(*sources, output)
    assert output.read_bytes() == old
    assert (tmp_path / "previous-success-v2.json").read_bytes() == old
    assert v1.read_bytes() == b"untouched v1 bytes"
    assert not list(tmp_path.glob(".publish-v2-*"))


@pytest.mark.parametrize(
    "fault",
    [
        "clock",
        "missing_score",
        "downgrade",
        "direction",
        "private",
        "size",
        "timeout",
        "changed_score",
        "changed_prediction",
    ],
)
def test_rejected_candidate_never_contacts_r2(
    publisher, candidate, tmp_path, monkeypatch, fault
):
    import public_forward_v2
    import stage_forward_snapshot

    sources, output, v1 = setup(publisher, candidate, tmp_path, monkeypatch)
    old = output.read_bytes()
    if fault == "clock":
        candidate["as_of"] = candidate["generated_at"] = "2026-10-15T12:59:59Z"
    elif fault == "missing_score":
        candidate["latest_scored"].pop()
    elif fault == "downgrade":
        candidate["schema_version"] = 1
    elif fault == "direction":
        candidate["latest_scored"][0]["models"]["zero"]["directional_correct"] = True
    elif fault == "private":
        candidate["private_path"] = "DO_NOT_PUBLISH"
    elif fault == "size":
        monkeypatch.setattr(stage_forward_snapshot, "MAX_BYTES", 1)
    elif fault == "timeout":

        def expired(*args):
            raise TimeoutError("synthetic preparation deadline")

        monkeypatch.setattr(public_forward_v2, "prepare", expired)
    elif fault == "changed_score":
        candidate["latest_scored"][0]["recipe_sha256"] = "b" * 64
    else:
        # Same scored row must agree with latest, so change both consistently;
        # progression still rejects the immutable original recipe identity.
        candidate["latest"][0]["recipe_sha256"] = "b" * 64
        candidate["latest_scored"][0]["recipe_sha256"] = "b" * 64

    def forbidden():
        pytest.fail("Rejected preparation must not load credentials or contact R2")

    monkeypatch.setattr(publisher, "client", forbidden)
    with pytest.raises((ValueError, OSError, subprocess.CalledProcessError)):
        publisher.publish(*sources, output)
    assert output.read_bytes() == old
    assert v1.read_bytes() == b"untouched v1 bytes"


def test_overlapping_publisher_fails_before_preparation(
    publisher, candidate, tmp_path, monkeypatch
):
    sources, output, _ = setup(publisher, candidate, tmp_path, monkeypatch)
    with output.with_suffix(".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            publisher.publish(*sources, output)


def test_real_loader_rejects_synthetic_input(publisher, tmp_path, monkeypatch):
    sources = [tmp_path / n for n in ("records", "outcomes", "operations")]
    for folder in sources:
        folder.mkdir()
    (sources[0] / "synthetic.json").write_text('{"synthetic":true}')

    def forbidden():
        pytest.fail("Invalid evidence must never reach R2")

    monkeypatch.setattr(publisher, "client", forbidden)
    with pytest.raises((ValueError, RuntimeError)):
        publisher.publish(*sources, tmp_path / publisher.STATE_NAME)
    assert not (tmp_path / publisher.STATE_NAME).exists()


def test_issued_prediction_and_counts_cannot_regress(publisher, candidate):
    for fault in ("count", "source", "prediction"):
        current = copy.deepcopy(candidate)
        if fault == "count":
            current["evaluations"][0]["matched_count"] -= 1
        elif fault == "source":
            current["latest"][0]["source_close_at"] = "2026-10-15T00:00:00Z"
        else:
            current["latest"][0]["models"]["ridge"]["predicted_log_return_4h"] = 1
        with pytest.raises(ValueError):
            publisher.check_progress(candidate, current)


def test_reject_v1_state_file(publisher, tmp_path):
    with pytest.raises(ValueError, match="isolated"):
        publisher.publish(tmp_path, tmp_path, tmp_path, tmp_path / "last-success.json")


@pytest.mark.parametrize("fault", ["cutoff", "issuance"])
def test_stale_production_candidate_rejected(publisher, candidate, fault):
    if fault == "cutoff":
        candidate["as_of"] = candidate["generated_at"] = "2026-10-15T12:30:00Z"
    else:
        candidate["latest"][0]["source_close_at"] = "2026-10-15T08:00:00Z"
    with pytest.raises(ValueError, match="stale"):
        publisher.check_freshness(candidate, datetime(2026, 10, 15, 13, tzinfo=UTC))


def test_first_failed_publication_creates_no_success(
    publisher, candidate, tmp_path, monkeypatch
):
    sources, output, _ = setup(publisher, candidate, tmp_path, monkeypatch)
    output.unlink()
    monkeypatch.setattr(publisher, "client", lambda: Storage("lost_ack"))
    with pytest.raises(TimeoutError):
        publisher.publish(*sources, output)
    assert not output.exists()
    assert not (tmp_path / "previous-success-v2.json").exists()

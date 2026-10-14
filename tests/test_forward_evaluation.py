"""Synthetic clocks, records and candles only; never inspect genuine outcomes."""

import copy
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from psycopg.pq import TransactionStatus
from test_evaluation import research_source  # noqa: F401
from test_forward import NOW, OPENED, recording, sample_window, synthetic_fit  # noqa: F401

from backtest_badger import forward
from backtest_badger import forward_evaluation as fe

SETTLED = OPENED + 2 * forward.STEP + forward.DELAY
CAPTURED = SETTLED + timedelta(seconds=10)


def forbidden(*args, **kwargs):
    pytest.fail("Forbidden fitting, network, database or forecast-write action")


def rewrite(path, value, checksum="content_sha256"):
    value = copy.deepcopy(value)
    value.pop(checksum, None)
    value[checksum] = fe.sha256(fe.canonical(value))
    path.chmod(0o644)
    path.write_bytes(fe.canonical(value) + b"\n")


def journal_for(path):
    prediction = fe.load_prediction(path)
    record = prediction["record"]
    stamp = record["issued_at"]
    return {
        "schema_version": 1,
        "run_id": "a" * 32,
        "source_open_time": record["source_open_time"],
        "feature_available_at": record["feature_available_at"],
        "deadline": (
            fe.utc_time(record["feature_available_at"]) + fe.PROMPTNESS
        ).isoformat(),
        "started_at": record["captured_at"],
        "finished_at": stamp,
        "state": "complete",
        "markets": {},
    }


def write_journal(path, operations, *, status="recorded"):
    from backtest_badger.forward_operations import record_summary

    prediction = fe.load_prediction(path)
    record = prediction["record"]
    journal = journal_for(path)
    journal["markets"] = {symbol: {"status": "failed"} for symbol in fe.SYMBOLS}
    journal["markets"][record["market"]["symbol"]] = {
        **record_summary(
            path, record["market"]["symbol"], fe.grid_time(record["source_open_time"])
        ),
        "status": status,
        "verification": "replayed",
        "refresh": "complete_fresh",
        "error_category": None,
    }
    operations.mkdir(exist_ok=True)
    target = operations / f"{path.stem}-cycle.json"
    target.write_bytes(fe.canonical(journal) + b"\n")
    return target, journal


@pytest.fixture
def evidence(recording, tmp_path, monkeypatch):  # noqa: F811
    run, market, rows, _ = recording
    path, record = run()
    target = copy.deepcopy(rows[-1])
    target.update(
        open_time=OPENED + forward.STEP,
        close=Decimal("110"),
        observed_at=SETTLED,
        recorded_at=SETTLED,
        last_observed_at=SETTLED,
    )
    operations, outcomes = tmp_path / "operations", tmp_path / "outcomes"
    journal_path, journal = write_journal(path, operations)
    monkeypatch.setattr(fe, "read_target", lambda connection, saved: [target])
    # No model fitting or provider operation is permitted after original recording.
    monkeypatch.setattr(forward, "fit_forward", forbidden)
    monkeypatch.setattr(forward, "record_forward", forbidden)
    monkeypatch.setattr(forward, "verify_forward", forbidden)
    return dict(
        path=path,
        record=record,
        target=target,
        operations=operations,
        outcomes=outcomes,
        journal_path=journal_path,
        journal=journal,
        market=market,
    )


def score(e, **kwargs):
    return fe.score(
        e["path"],
        outcomes=e["outcomes"],
        operations=e["operations"],
        clock=kwargs.pop("clock", lambda: CAPTURED),
        connect=kwargs.pop("connect", lambda: nullcontext(None)),
        **kwargs,
    )


def outcome(e):
    return fe.load_outcome(
        e["outcomes"] / e["path"].name, fe.load_prediction(e["path"])
    )


def report(e, **kwargs):
    return fe.report(
        records=e["path"].parent,
        outcomes=e["outcomes"],
        operations=e["operations"],
        as_of=kwargs.pop("as_of", CAPTURED),
        **kwargs,
    )


def test_protocol_pin():
    assert fe.protocol() == {"version": "stage-3c-v1", "sha256": fe.PROTOCOL_SHA256}


def test_record_to_score_preserves_forecast_and_original_source(evidence):
    e = evidence
    before = e["path"].read_bytes(), e["path"].stat().st_mtime_ns
    assert score(e)["status"] == "scored"
    result = outcome(e)
    assert result["cohort"]["name"] == fe.COHORTS[0]
    assert result["original_source_close"] == "107"
    assert result["actual_log_return_4h"] == pytest.approx(
        float((Decimal(110) / Decimal(107)).ln())
    )
    assert result["target_open_time"] == (OPENED + forward.STEP).isoformat()
    assert result["target_candle"] == forward._json(e["target"])
    assert result["predictions"] == e["record"]["predictions"]
    assert result["prediction_file_sha256"] == fe.sha256(before[0])
    assert before == (e["path"].read_bytes(), e["path"].stat().st_mtime_ns)
    assert result["protocol"]["sha256"] == fe.PROTOCOL_SHA256
    assert result["model_errors"]["zero"]["directional_correct"] is None
    assert e["path"].stat().st_mode & 0o222 == 0
    assert (e["outcomes"] / e["path"].name).stat().st_mode & 0o222 == 0


@pytest.mark.parametrize(
    "offset,expected",
    [
        (-1, "pending_not_settled"),
        (-0.000001, "pending_not_settled"),
        (0, "scored"),
        (1, "scored"),
    ],
)
def test_exact_settling_boundary(evidence, monkeypatch, offset, expected):
    if offset < 0:
        monkeypatch.setattr(fe, "read_target", forbidden)
    result = score(
        evidence,
        clock=lambda: SETTLED + timedelta(seconds=offset),
        connect=forbidden if offset < 0 else lambda: nullcontext(None),
    )
    assert result["status"] == expected
    assert evidence["outcomes"].exists() == (expected == "scored")


def test_missing_outcome_is_pending_without_file(evidence, monkeypatch):
    monkeypatch.setattr(fe, "read_target", lambda *a: [])
    assert score(evidence)["status"] == "pending_target_missing"
    assert not evidence["outcomes"].exists()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda t: t.update(open_time=t["open_time"] - forward.STEP),
        lambda t: t.update(interval_seconds=3600),
        lambda t: t.update(market_id=2),
        lambda t: t.update(close=Decimal(0)),
        lambda t: t.update(close=110.0),
        lambda t: t.update(high=Decimal(1)),
        lambda t: t.update(base_volume=Decimal(-1)),
        lambda t: t.update(taker_buy_base_volume=Decimal(999)),
        lambda t: t.update(trade_count=True),
        lambda t: t.update(version=0),
        lambda t: t.update(version=True),
        lambda t: t.update(observed_at=SETTLED - timedelta(microseconds=1)),
        lambda t: t.update(recorded_at=SETTLED - timedelta(seconds=1)),
        lambda t: t.update(recorded_at=CAPTURED + timedelta(seconds=1)),
        lambda t: t.update(last_observed_at=CAPTURED + timedelta(seconds=1)),
        lambda t: t.update(last_observed_at=SETTLED - timedelta(seconds=1)),
        lambda t: t.update(source_sha256="bad"),
        lambda t: t.update(source_url=t["source_url"].replace("BTCUSDT", "ETHUSDT")),
        lambda t: t.update(source_url=t["source_url"].replace("4h", "1h")),
        lambda t: t.update(source_url=t["source_url"].replace("https", "http")),
        lambda t: t.pop("source_kind"),
    ],
)
def test_invalid_stale_or_malformed_target(evidence, mutation):
    mutation(evidence["target"])
    with pytest.raises((ValueError, TypeError, KeyError)):
        score(evidence)
    assert not evidence["outcomes"].exists()


def test_old_completed_target_valid_and_archive_identity(evidence):
    target = evidence["target"]
    target.update(
        source_kind="archive",
        source_url="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/4h/BTCUSDT-4h-2026-10.zip",
    )
    assert (
        score(evidence, clock=lambda: CAPTURED + timedelta(days=60))["status"]
        == "scored"
    )


def test_duplicate_target_rows_rejected(evidence, monkeypatch):
    monkeypatch.setattr(fe, "read_target", lambda *a: [evidence["target"]] * 2)
    with pytest.raises(ValueError, match="Duplicate"):
        score(evidence)


@pytest.mark.parametrize(
    "clocks",
    [
        (CAPTURED, CAPTURED - timedelta(seconds=1)),
        (CAPTURED, CAPTURED, CAPTURED - timedelta(seconds=1)),
    ],
)
def test_clock_reversals(evidence, clocks):
    values = iter(clocks)
    with pytest.raises(ValueError, match="Clock reversed"):
        score(evidence, clock=lambda: next(values))
    assert not evidence["outcomes"].exists()


@pytest.mark.parametrize(
    "seconds,cohort", [(0, 0), (899.999999, 0), (900, 1), (9589.118473, 1)]
)
def test_exact_primary_secondary_boundaries(evidence, seconds, cohort):
    record = copy.deepcopy(evidence["record"])
    stamp = (
        OPENED + forward.STEP + forward.DELAY + timedelta(seconds=seconds)
    ).isoformat()
    record.update(captured_at=stamp, calculated_at=stamp, issued_at=stamp)
    # At the very first second DB recording must already be available.
    for row in record["source_candles"]:
        row["recorded_at"] = row["observed_at"]
    rewrite(evidence["path"], record)
    write_journal(evidence["path"], evidence["operations"])
    assert score(evidence)["cohort"] == fe.COHORTS[cohort]


@pytest.mark.parametrize(
    "change",
    [
        "absent",
        "already-recorded",
        "file_hash",
        "content_hash",
        "failed",
        "wrong_issue",
        "wrong_source",
        "refresh",
    ],
)
def test_timing_alone_never_proves_automation(evidence, change):
    path, journal = evidence["journal_path"], evidence["journal"]
    item = journal["markets"]["BTCUSDT"]
    if change == "absent":
        path.unlink()
    else:
        if change in ("already-recorded", "failed"):
            item["status"] = change
        elif change == "file_hash":
            item["file_sha256"] = "0" * 64
        elif change == "content_hash":
            item["content_sha256"] = "0" * 64
        elif change == "wrong_issue":
            item["issued_at"] = OPENED.isoformat()
        elif change == "wrong_source":
            item["source_open_time"] = "bad"
        else:
            item["refresh"] = "failed"
        path.write_bytes(fe.canonical(journal))
    assert score(evidence)["cohort"] == fe.COHORTS[2]


def test_in_progress_other_market_still_qualifies(evidence):
    journal = evidence["journal"]
    journal.update(state="running", finished_at=None)
    evidence["journal_path"].write_bytes(fe.canonical(journal))
    assert score(evidence)["cohort"] == fe.COHORTS[0]


def test_revisions_and_idempotency_do_not_read_database(evidence, monkeypatch):
    score(evidence)
    before = (evidence["outcomes"] / evidence["path"].name).read_bytes()
    evidence["target"].update(close=Decimal(112), version=2)
    monkeypatch.setattr(fe, "read_target", forbidden)
    assert score(evidence, connect=forbidden)["status"] == "already_scored"
    assert (evidence["outcomes"] / evidence["path"].name).read_bytes() == before
    assert outcome(evidence)["target_candle"]["version"] == 1
    # Reports use embedded cohort evidence even if the live journal disappears.
    evidence["journal_path"].unlink()
    assert (
        report(evidence)["markets"]["BTCUSDT"]["cohorts"][fe.COHORTS[0]]["scored"] == 1
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(target_open_time=r["source_open_time"]),
        lambda r: r.update(target_close_boundary=r["source_open_time"]),
        lambda r: r.update(issued_at=r["target_close_boundary"]),
        lambda r: r.update(kind="backtest"),
        lambda r: r.update(schema_version=True),
        lambda r: r.update(extra=True),
        lambda r: r["market"].update(symbol="ETHUSDT"),
        lambda r: r["predictions"].pop(),
        lambda r: r["predictions"][0].update(predicted_log_return_4h=0.1),
        lambda r: r["predictions"][1].update(predicted_log_return_4h=999),
        lambda r: r["predictions"][2].update(predicted_log_return_4h=True),
        lambda r: r["predictions"][2].update(prediction_id="altered"),
        lambda r: r["model"].update(training_count=0),
        lambda r: r["source_candles"][-1].update(close="108"),
        lambda r: r["source_candles"][-1].update(close=107),
        lambda r: r["feature_values"].pop(),
    ],
)
def test_rehashed_bad_prediction_rejected(evidence, mutation):
    record = copy.deepcopy(evidence["record"])
    mutation(record)
    rewrite(evidence["path"], record)
    with pytest.raises(ValueError):
        score(evidence, connect=forbidden)


@pytest.mark.parametrize(
    "body", [b"{}", b"[]", b"null", b"broken", b'{"x":1,"x":2}', b'{"x": NaN}']
)
def test_malformed_predictions(evidence, body):
    evidence["path"].chmod(0o644)
    evidence["path"].write_bytes(body)
    with pytest.raises(ValueError):
        score(evidence, connect=forbidden)


def test_hash_and_exact_bytes_checked(evidence):
    path = evidence["path"]
    path.chmod(0o644)
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="Exact file"):
        fe.load_prediction(path)
    path.write_bytes(original.replace(b'"107"', b'"108"'))
    with pytest.raises(ValueError, match="Checksum"):
        fe.load_prediction(path)


def test_checkout_fingerprint_difference_does_not_require_replay(evidence):
    record = copy.deepcopy(evidence["record"])
    recipe = record["model"]
    recipe["implementation_sha256"] = {
        k: "0" * 64 for k in recipe["implementation_sha256"]
    }
    recipe.pop("model_recipe_sha256")
    recipe["model_recipe_sha256"] = fe.sha256(fe.canonical(recipe))
    rewrite(evidence["path"], record)
    assert score(evidence)["status"] == "scored"


@pytest.mark.parametrize(
    "change",
    [
        "broken",
        "rehashed_metric",
        "rehashed_price",
        "rehashed_cohort",
        "protocol",
        "prediction_hash",
    ],
)
def test_existing_corrupt_conflicting_score_never_replaced(evidence, change):
    score(evidence)
    path = evidence["outcomes"] / evidence["path"].name
    value = json.loads(path.read_bytes())
    if change == "broken":
        path.chmod(0o644)
        path.write_text("broken")
    else:
        if change == "rehashed_metric":
            value["model_errors"]["ridge"]["absolute_error"] = 100
        elif change == "rehashed_price":
            value["original_source_close"] = "123"
        elif change == "rehashed_cohort":
            value["cohort"]["name"] = fe.COHORTS[1]
        elif change == "protocol":
            value["protocol"]["sha256"] = "0" * 64
        else:
            value["prediction_file_sha256"] = "0" * 64
        rewrite(path, value, "outcome_sha256")
    before = path.read_bytes()
    with pytest.raises(ValueError):
        score(evidence, connect=forbidden)
    assert path.read_bytes() == before
    result = report(evidence)
    assert result["invalid_outcomes"] == [path.name]
    assert result["markets"]["BTCUSDT"]["cohorts"][fe.COHORTS[0]]["scored"] == 0


def test_exclusive_publication_and_partial_cleanup(evidence, monkeypatch):
    real_link = fe.os.link
    monkeypatch.setattr(
        fe.os, "link", lambda *a: (_ for _ in ()).throw(OSError("failed"))
    )
    with pytest.raises(OSError):
        score(evidence)
    assert list(evidence["outcomes"].iterdir()) == []
    monkeypatch.setattr(fe.os, "link", real_link)
    score(evidence)
    value = outcome(evidence)
    value.pop("outcome_sha256")
    with pytest.raises(FileExistsError):
        fe.publish_outcome(value, evidence["outcomes"] / evidence["path"].name)


def test_concurrent_scores_have_one_winner(evidence, monkeypatch):
    barrier = Barrier(2)
    monkeypatch.setattr(
        fe, "read_target", lambda *a: (barrier.wait(), [evidence["target"]])[1]
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: score(evidence), range(2)))
    assert sorted(r["status"] for r in results) == ["already_scored", "scored"]
    assert len(list(evidence["outcomes"].glob("*.json"))) == 1


@pytest.mark.parametrize(
    "actual,predicted,direction,correct",
    [
        (0, 0, 0, None),
        (0, 0.1, 0, False),
        (0.1, 1e-20, 1, True),
        (-0.1, -1e-20, -1, True),
        (0.1, -0.1, 1, False),
    ],
)
def test_exact_sign_without_tolerance(actual, predicted, direction, correct):
    metrics = fe.model_errors(
        [{"model_id": "ridge", "predicted_log_return_4h": predicted}], actual, direction
    )["ridge"]
    assert metrics["directional_correct"] is correct
    assert metrics["signed_error"] == predicted - actual
    assert metrics["squared_error"] == (predicted - actual) ** 2


def test_exact_flat_outcome_and_zero_baseline_denominators(evidence):
    evidence["target"]["close"] = Decimal(107)
    score(evidence)
    result = outcome(evidence)
    assert result["actual_log_return_4h"] == 0
    assert all(e["actual_direction"] == 0 for e in result["model_errors"].values())
    metrics = fe.aggregate([result])["models"]
    assert metrics["zero"]["directional_denominator"] == 0
    assert metrics["zero"]["directional_accuracy"] is None
    assert metrics["ridge"]["relative_error_improvement"]["zero"] == {
        "mae": None,
        "rmse": None,
    }


def test_matched_metrics_hand_calculation_and_duplicates():
    rows = []
    for i, actual in enumerate([1.0, -2.0]):
        predictions = [
            {"model_id": name, "predicted_log_return_4h": value}
            for name, value in zip(fe.MODELS, [0, 0.5, 2, -1], strict=True)
        ]
        rows.append(
            {
                "prediction_record_id": str(i),
                "actual_log_return_4h": actual,
                "model_errors": fe.model_errors(predictions, actual, fe.sign(actual)),
            }
        )
    result = fe.aggregate(rows)
    ridge = result["models"]["ridge"]
    assert ridge["mae"] == 2.5
    assert ridge["rmse"] == pytest.approx((17 / 2) ** 0.5)
    assert ridge["forecast_bias"] == 2.5
    assert ridge["mean_realised_log_return"] == -0.5
    assert ridge["directional_accuracy"] == 0.5
    assert ridge["directional_denominator"] == 2
    assert ridge["relative_error_improvement"]["zero"]["mae"] == pytest.approx(
        1 - 2.5 / 1.5
    )
    assert result["matched_record_ids"] == ["0", "1"]
    with pytest.raises(ValueError, match="Duplicate"):
        fe.aggregate(rows + [rows[0]])
    rows[1]["model_errors"].pop("ridge")
    with pytest.raises(ValueError, match="Incomplete"):
        fe.aggregate(rows)


def test_empty_offline_report_and_undefined_metrics(tmp_path, monkeypatch):
    monkeypatch.setattr(fe, "connect_database", forbidden)
    monkeypatch.setattr(fe, "load_settings", forbidden)
    result = fe.report(
        records=tmp_path, outcomes=tmp_path, operations=tmp_path, as_of=CAPTURED
    )
    assert result["evidence_valid"]
    assert result["monitoring_source_start"] is None
    for market in result["markets"].values():
        assert market["missing_prediction_count"] is None
        for cohort in market["cohorts"].values():
            assert cohort["genuine_predictions"] == cohort["scored"] == 0
            assert cohort["models"]["zero"]["mae"] is None
            assert cohort["models"]["zero"]["directional_accuracy"] is None


def test_pending_mature_invalid_missing_counts(evidence):
    assert (
        report(evidence, as_of=NOW)["markets"]["BTCUSDT"]["cohorts"][fe.COHORTS[0]][
            "pending_not_settled"
        ]
        == 1
    )
    result = report(evidence)
    btc = result["markets"]["BTCUSDT"]
    assert btc["cohorts"][fe.COHORTS[0]]["mature_unscored"] == 1
    assert btc["missing_prediction_count"] == 0
    assert result["markets"]["ETHUSDT"]["missing_prediction_count"] == 1
    later = report(evidence, as_of=CAPTURED + 3 * forward.STEP)
    assert later["markets"]["BTCUSDT"]["missing_prediction_count"] == 3
    evidence["path"].chmod(0o644)
    evidence["path"].write_text("broken")
    result = report(evidence)
    assert result["invalid_predictions"] == [evidence["path"].name]
    assert result["markets"]["BTCUSDT"]["missing_prediction_count"] == 0
    assert len(result["markets"]["BTCUSDT"]["invalid_expected_prediction_ids"]) == 1


def test_deterministic_report_and_capture_cutoff(evidence, monkeypatch):
    score(evidence)
    monkeypatch.setattr(fe, "connect_database", forbidden)
    a, b = report(evidence, period="month"), report(evidence, period="month")
    assert fe.canonical(a) == fe.canonical(b)
    btc = a["markets"]["BTCUSDT"]["cohorts"][fe.COHORTS[0]]
    assert btc["matched_count"] == 1
    assert "Preliminary" in btc["warning"]
    assert btc["periods"][0]["metrics"] is None
    assert btc["periods"][0]["partial_period"]
    earlier = report(evidence, as_of=CAPTURED - timedelta(seconds=1))
    assert (
        earlier["markets"]["BTCUSDT"]["cohorts"][fe.COHORTS[0]]["mature_unscored"] == 1
    )


@pytest.mark.parametrize(
    "stamp,period,expected",
    [
        ("2027-02-01T00:00:00+00:00", "month", "2027-02-01T00:00:00+00:00"),
        ("2027-02-01T00:00:00+00:00", "week", "2027-02-01T00:00:00+00:00"),
        ("2027-01-31T23:59:59+00:00", "week", "2027-01-25T00:00:00+00:00"),
        ("2027-01-01T00:00:00+00:00", "week", "2026-12-28T00:00:00+00:00"),
    ],
)
def test_utc_period_grouping(stamp, period, expected):
    start, end = fe.period_bounds(fe.utc_time(stamp), period)
    assert start.isoformat() == expected
    assert start <= fe.utc_time(stamp) < end


def test_invalid_journal_orphan_and_partials_disclosed(evidence):
    evidence["journal_path"].write_text("broken")
    evidence["outcomes"].mkdir()
    (evidence["outcomes"] / "orphan.json").write_text("{}")
    (evidence["outcomes"] / ".test.partial").write_text("incomplete")
    result = report(evidence)
    assert result["invalid_journals"] == [evidence["journal_path"].name]
    assert result["orphan_outcomes"] == ["orphan.json"]
    assert result["partial_outcomes"] == 1
    assert not result["evidence_valid"]


def test_independent_btc_eth_records(tmp_path, monkeypatch, synthetic_fit):  # noqa: F811
    source, _, _ = synthetic_fit
    paths = []
    targets = {}
    for symbol in fe.SYMBOLS:
        market, rows = sample_window(symbol)
        monkeypatch.setattr(forward, "read_window", lambda *a, m=market, r=rows: (m, r))
        path, _ = forward.record_forward(
            None,
            symbol,
            source=source,
            destination=tmp_path / "records",
            clock=lambda: NOW,
        )
        paths.append(path)
        write_journal(path, tmp_path / "operations")
        target = copy.deepcopy(rows[-1])
        target.update(
            open_time=OPENED + forward.STEP,
            close=Decimal(110 if symbol == "BTCUSDT" else 105),
            observed_at=SETTLED,
            recorded_at=SETTLED,
            last_observed_at=SETTLED,
        )
        targets[symbol] = target
    monkeypatch.setattr(
        fe, "read_target", lambda conn, record: [targets[record["market"]["symbol"]]]
    )
    for path in paths:
        fe.score(
            path,
            outcomes=tmp_path / "outcomes",
            operations=tmp_path / "operations",
            clock=lambda: CAPTURED,
            connect=lambda: nullcontext(None),
        )
    result = fe.report(
        records=tmp_path / "records",
        outcomes=tmp_path / "outcomes",
        operations=tmp_path / "operations",
        as_of=CAPTURED,
    )
    assert all(
        m["cohorts"][fe.COHORTS[0]]["scored"] == 1 for m in result["markets"].values()
    )
    btc, eth = [
        m["cohorts"][fe.COHORTS[0]]["models"]["zero"]["mean_realised_log_return"]
        for m in result["markets"].values()
    ]
    assert btc > 0 > eth


def test_read_target_exact_read_only_snapshot(evidence, monkeypatch):
    statements = []

    class Connection:
        autocommit = True
        info = type("Info", (), {"transaction_status": TransactionStatus.IDLE})()

        def transaction(self):
            return nullcontext()

        def execute(self, query):
            statements.append(query)

        @contextmanager
        def cursor(self, **kwargs):
            yield self

        def fetchone(self):
            return evidence["market"]

    connection = Connection()

    class Cursor:
        def execute(self, query, params):
            statements.append(query)
            assert params == ("BTCUSDT",)

        def fetchone(self):
            return evidence["market"]

    connection.cursor = lambda **k: nullcontext(Cursor())

    def read(conn, market_id, interval, start, end):
        assert conn is connection
        assert (market_id, interval, start, end) == (
            1,
            14400,
            OPENED + forward.STEP,
            OPENED + 2 * forward.STEP,
        )
        return [evidence["target"]]

    monkeypatch.undo()  # Restore actual read_target, then patch only the SQL leaf.
    monkeypatch.setattr(fe, "get_candles", read)
    assert fe.read_target(connection, evidence["record"]) == [evidence["target"]]
    assert statements[:2] == [
        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY",
        "SET LOCAL TIME ZONE 'UTC'",
    ]
    assert all(s.startswith(("SELECT", "SET")) for s in statements)
    evidence["market"]["market_id"] = 9
    with pytest.raises(ValueError, match="identity"):
        fe.read_target(connection, evidence["record"])


def test_cli_offline_and_scoring_status(evidence, monkeypatch, capsys):
    monkeypatch.setattr(fe, "connect_database", forbidden)
    monkeypatch.setattr(fe, "load_settings", forbidden)
    args = [
        "report",
        "--records",
        str(evidence["path"].parent),
        "--outcomes",
        str(evidence["outcomes"]),
        "--operations",
        str(evidence["operations"]),
        "--as-of",
        CAPTURED.isoformat(),
    ]
    assert fe.main(args) == 0
    assert json.loads(capsys.readouterr().out)["evidence_valid"]
    real_score = fe.score
    monkeypatch.setattr(
        fe,
        "score",
        lambda path: real_score(
            path,
            outcomes=evidence["outcomes"],
            operations=evidence["operations"],
            clock=lambda: NOW,
            connect=forbidden,
        ),
    )
    assert fe.main(["score", "--record", str(evidence["path"])]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "pending_not_settled"


@pytest.mark.parametrize(
    "option", ["--as-of", "--now", "--source", "--settling-seconds"]
)
def test_score_has_no_clock_or_training_override(option):
    with pytest.raises(SystemExit) as error:
        fe.main(["score", "--record", "unused.json", option, "2026-10-14"])
    assert error.value.code == 2


def test_protocol_change_blocks_before_any_outcome_access(
    evidence, monkeypatch, tmp_path
):
    changed = tmp_path / "protocol.md"
    changed.write_bytes(fe.PROTOCOL.read_bytes() + b"changed")
    monkeypatch.setattr(fe, "PROTOCOL", changed)
    with pytest.raises(ValueError, match="Protocol hash"):
        score(evidence, connect=forbidden)


def test_rehashed_changed_forecast_conflicts_with_existing_score(evidence):
    score(evidence)
    original_score = (evidence["outcomes"] / evidence["path"].name).read_bytes()
    record = copy.deepcopy(evidence["record"])
    record["predictions"][2]["predicted_log_return_4h"] += 0.01
    rewrite(evidence["path"], record)
    with pytest.raises(ValueError, match="conflicts"):
        score(evidence, connect=forbidden)
    assert (evidence["outcomes"] / evidence["path"].name).read_bytes() == original_score


def test_dangling_outcome_link_is_never_replaced(evidence):
    evidence["outcomes"].mkdir()
    path = evidence["outcomes"] / evidence["path"].name
    path.symlink_to("absent-target")
    with pytest.raises(FileNotFoundError):
        score(evidence, connect=forbidden)
    assert path.is_symlink()


def test_directory_fsync_failure_retains_visible_evidence(evidence, monkeypatch):
    fsync = fe.os.fsync
    count = 0

    def fail_directory(fd):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("directory fsync failed")
        return fsync(fd)

    monkeypatch.setattr(fe.os, "fsync", fail_directory)
    with pytest.raises(RuntimeError, match="durability"):
        score(evidence)
    assert outcome(evidence)["prediction_record_id"] == evidence["record"]["record_id"]
    assert score(evidence, connect=forbidden)["status"] == "already_scored"


def test_historical_holdout_rejected_before_connection(evidence):
    record = copy.deepcopy(evidence["record"])
    record["source_open_time"] = "2026-09-30T08:00:00+00:00"
    rewrite(evidence["path"], record)
    with pytest.raises(ValueError, match="holdout"):
        score(evidence, connect=forbidden)


def test_source_revision_is_never_queried(evidence, monkeypatch):
    # Only target is returned by this read. A later canonical source could be
    # anything; it cannot enter the target definition or denominator.
    canonical_source = {"close": Decimal("9999"), "version": 2}

    def target_only(connection, record):
        assert record["source_candles"][-1]["close"] == "107"
        assert canonical_source["close"] != Decimal(
            record["source_candles"][-1]["close"]
        )
        return [evidence["target"]]

    monkeypatch.setattr(fe, "read_target", target_only)
    score(evidence)
    assert outcome(evidence)["original_source_close"] == "107"
    assert outcome(evidence)["actual_log_return_4h"] == fe.log_return(
        Decimal(110), Decimal(107)
    )


def test_hundred_observations_period_thresholds_and_empty_periods(
    evidence, monkeypatch
):
    original = evidence["record"]
    for index in range(100):
        shift = index * forward.STEP
        record = copy.deepcopy(original)
        record.pop("content_sha256")
        for key in (
            "source_open_time",
            "source_close_boundary",
            "feature_available_at",
            "captured_at",
            "calculated_at",
            "issued_at",
            "target_open_time",
            "target_close_boundary",
        ):
            record[key] = (fe.utc_time(record[key]) + shift).isoformat()
        for candle in record["source_candles"]:
            for key in forward.TIME_FIELDS:
                candle[key] = (fe.utc_time(candle[key]) + shift).isoformat()
        identity = forward.record_id("BTCUSDT", OPENED + shift)
        record["record_id"] = identity
        for item in record["predictions"]:
            item["prediction_id"] = f"{identity}:{item['model_id']}"
        path = evidence["path"].parent / f"{identity}.json"
        if index:
            forward.publish(record, path, lambda shift=shift: NOW + shift)
        write_journal(path, evidence["operations"])
        target = copy.deepcopy(evidence["target"])
        for key in forward.TIME_FIELDS:
            target[key] += shift
        monkeypatch.setattr(fe, "read_target", lambda *a, t=target: [t])
        fe.score(
            path,
            outcomes=evidence["outcomes"],
            operations=evidence["operations"],
            clock=lambda shift=shift: CAPTURED + shift,
            connect=lambda: nullcontext(None),
        )
    cutoff = datetime(2026, 12, 1, tzinfo=UTC)
    monthly = report(evidence, as_of=cutoff, period="month")
    cohort = monthly["markets"]["BTCUSDT"]["cohorts"][fe.COHORTS[0]]
    assert cohort["scored"] == 100
    assert "Descriptive" in cohort["warning"]
    october, november, december = cohort["periods"]
    assert october["metrics"]["matched_count"] == 100
    assert october["partial_period"] is False
    assert november["scored_predictions"] == 0 and november["metrics"] is None
    assert december["partial_period"] is True
    weekly = report(evidence, as_of=cutoff, period="week")
    periods = weekly["markets"]["BTCUSDT"]["cohorts"][fe.COHORTS[0]]["periods"]
    assert any(p["metrics"] and p["scored_predictions"] >= 30 for p in periods)
    assert all(p["metrics"] is None for p in periods if p["scored_predictions"] < 30)


def test_nonlocal_configuration_refused(monkeypatch, config_env):
    for name, value in config_env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("POSTGRES_HOST", "example.org")
    monkeypatch.setattr(fe, "connect_database", forbidden)
    with pytest.raises(ValueError, match="local development"):
        fe.local_connection()


def test_decimal_direction_survives_float_underflow(evidence):
    evidence["target"]["close"] = Decimal("107." + "0" * 399 + "1")
    score(evidence)
    saved = outcome(evidence)
    assert saved["actual_log_return_4h"] == 0.0
    assert saved["model_errors"]["zero"]["actual_direction"] == 1
    assert saved["model_errors"]["training_mean"]["predicted_direction"] == -1
    assert saved["model_errors"]["training_mean"]["directional_correct"] is False

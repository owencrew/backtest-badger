"""Synthetic forward clocks/data only; no provider calls or real holdout outcomes."""

import copy
import json
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from threading import Barrier

import numpy as np
import pytest
from test_evaluation import research_source  # noqa: F401

from backtest_badger import cli, evaluation, forward, model_data
from backtest_badger.features import causal_features
from backtest_badger.model_data import FEATURES, TARGET

OPENED = datetime(2026, 10, 14, 8, tzinfo=UTC)
NOW = OPENED + forward.STEP + timedelta(minutes=2)


def sample_window(symbol="BTCUSDT"):
    market = dict(
        market_id=1 if symbol == "BTCUSDT" else 2,
        venue="binance",
        market_type="spot",
        symbol=symbol,
        base_asset=symbol[:-4],
        quote_asset="USDT",
    )
    rows = []
    for i in range(7):
        opened = OPENED + (i - 6) * forward.STEP
        rows.append(
            dict(
                market_id=market["market_id"],
                interval_seconds=14400,
                open_time=opened,
                open=Decimal(100 + i),
                high=Decimal(110 + i),
                low=Decimal(90 + i),
                close=Decimal(101 + i),
                base_volume=Decimal(10 + i),
                quote_volume=Decimal(1000),
                taker_buy_base_volume=Decimal(1),
                taker_buy_quote_volume=Decimal(100),
                trade_count=10,
                version=1,
                observed_at=opened + forward.STEP + timedelta(seconds=60),
                recorded_at=opened + forward.STEP + timedelta(seconds=61),
                last_observed_at=opened + forward.STEP + timedelta(seconds=60),
                source_kind="rest",
                source_sha256="a" * 64,
                source_url=f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}"
                "&interval=4h&timeZone=0&limit=1000",
            )
        )
    return market, rows


@pytest.fixture
def synthetic_fit(research_source, monkeypatch):  # noqa: F811
    source, rows, manifest, write = research_source
    # Guard both non-training partitions, not only the original test partition.
    for row in rows:
        if row["split"] != "train":
            row[TARGET] = "NEVER_CONVERT"
            for name in FEATURES:
                row[name] = "NEVER_CONVERT"
    pins = write()
    real_load = model_data.load_model_data

    def load(path, *, training_only):
        assert training_only is True
        return real_load(path, training_only=True, **pins)

    monkeypatch.setattr(forward, "load_model_data", load)
    return source, rows, manifest


@pytest.fixture
def recording(tmp_path, monkeypatch, synthetic_fit):
    source, _, _ = synthetic_fit
    market, rows = sample_window()
    monkeypatch.setattr(forward, "read_window", lambda *a: (market, rows))

    def run(clock=lambda: NOW, symbol="BTCUSDT"):
        return forward.record_forward(
            None, symbol, source=source, destination=tmp_path / "records", clock=clock
        )

    return run, market, rows, source


def test_training_only_does_not_access_heldout_numerics(synthetic_fit):
    _, rows, manifest = synthetic_fit

    class Guard(dict):
        def __getitem__(self, key):
            if self.get("split") != "train" and key in (*FEATURES, TARGET):
                pytest.fail("Accessed a held-out numeric cell")
            return super().__getitem__(key)

    selected = model_data.select_rows(map(Guard, rows), manifest, training_only=True)
    assert all(
        len(v["train"]) == 240 and not v["validation"] for v in selected.values()
    )


def test_fixed_fit_reuses_models_deterministically(synthetic_fit):
    source, _, _ = synthetic_fit
    a, b = (
        forward.fit_forward("BTCUSDT", source),
        forward.fit_forward("BTCUSDT", source),
    )
    assert a[2] == b[2]
    assert a[2]["training_count"] == 240
    assert a[2]["parameters"]["ridge"]["alpha"] == 1
    assert a[2]["parameters"]["gradient_boosting"]["random_state"] == 42
    x = np.array([[0.01, 0.02, 0.03, 0.04, 1.0]])
    for name, values in evaluation.predict_models(*a[:2], x).items():
        np.testing.assert_array_equal(
            values, evaluation.predict_models(*b[:2], x)[name]
        )
    assert forward.fit_forward("ETHUSDT", source)[0] != a[0]


def test_feature_values_and_exact_decimals():
    market, rows = sample_window()
    values = forward.validate_window(market, rows, OPENED, NOW)
    expected = [
        math.log(107 / 106),
        math.log(107 / 104),
        math.log(107 / 101),
        math.sqrt(sum(math.log((102 + i) / (101 + i)) ** 2 for i in range(6))),
        16 / 12.5,
    ]
    assert values == list(
        causal_features([dict(r, symbol="BTCUSDT") for r in rows]).values()
    )
    np.testing.assert_allclose(values, expected, rtol=1e-13)
    assert all(isinstance(r["close"], Decimal) for r in rows)


@pytest.mark.parametrize(
    "seconds,eligible",
    [
        (0, False),
        (59.999999, False),
        (60, True),
        (61, True),
        (14399, True),
        (14400, False),
    ],
)
def test_settling_and_target_boundaries(seconds, eligible):
    now = OPENED + forward.STEP + timedelta(seconds=seconds)
    if eligible:
        assert forward.current_open(now) == OPENED
    else:
        with pytest.raises(ValueError, match="settling"):
            forward.current_open(now)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda m, r: r.pop(0),
        lambda m, r: r.insert(0, r[0]),
        lambda m, r: r[0].update(open_time=r[1]["open_time"]),
        lambda m, r: r[0].update(close=Decimal("NaN")),
        lambda m, r: r[0].update(close=Decimal(0)),
        lambda m, r: r[0].update(close=200.0),
        lambda m, r: r[0].update(base_volume=Decimal(-1)),
        lambda m, r: r[0].update(high=Decimal(1)),
        lambda m, r: r[0].update(trade_count=True),
        lambda m, r: r[0].update(version=0),
        lambda m, r: r[0].update(version=True),
        lambda m, r: r[0].update(market_id=2),
        lambda m, r: r[0].update(interval_seconds=3600),
        lambda m, r: m.update(venue="other"),
        lambda m, r: m.update(base_asset="ETH"),
        lambda m, r: r[0].update(source_sha256="bad"),
        lambda m, r: r[0].update(source_url="https://example.com"),
        lambda m, r: r[0].update(source_kind="unknown"),
        lambda m, r: r[0].update(observed_at=NOW + timedelta(seconds=1)),
        lambda m, r: r[0].update(recorded_at=NOW + timedelta(seconds=1)),
        lambda m, r: r[0].update(last_observed_at=NOW + timedelta(seconds=1)),
        lambda m, r: r[0].update(
            recorded_at=r[0]["observed_at"] - timedelta(seconds=1)
        ),
        lambda m, r: r[0].update(open_time=r[0]["open_time"].replace(tzinfo=None)),
        lambda m, r: r[0].update(
            observed_at=NOW.astimezone(timezone(timedelta(hours=1)))
        ),
        lambda m, r: [
            v.update(base_volume=Decimal(0), taker_buy_base_volume=Decimal(0))
            for v in r
        ],
    ],
)
def test_invalid_window_rejected(mutation):
    market, rows = sample_window()
    mutation(market, rows)
    with pytest.raises(ValueError):
        forward.validate_window(market, rows, OPENED, NOW)


def test_stale_database_not_used(recording, tmp_path):
    run, _, rows, _ = recording
    rows.pop()
    with pytest.raises(ValueError, match="Stale data"):
        run()
    assert not (tmp_path / "records").exists()


@pytest.mark.parametrize(
    "stamp", [NOW.replace(tzinfo=None), NOW.astimezone(timezone(timedelta(hours=1)))]
)
def test_invalid_clock(recording, stamp):
    with pytest.raises(ValueError, match="aware UTC"):
        recording[0](clock=lambda: stamp)


def test_record_replay_duplicate_and_revision_preservation(recording):
    run, _, rows, source = recording
    path, record = run()
    original = path.read_bytes()
    assert record["feature_names"] == list(FEATURES)
    assert record["target_close_boundary"] == (OPENED + 2 * forward.STEP).isoformat()
    assert len(record["predictions"]) == 4
    assert record["source_candles"] == forward._json(rows)
    assert forward.verify_forward(path, source=source)["verified"]
    rows[-1].update(close=Decimal(108), version=2, source_sha256="b" * 64)
    with pytest.raises(FileExistsError):
        run()
    assert path.read_bytes() == original
    assert forward.verify_forward(path, source=source)["verified"]
    assert not list(path.parent.glob("*.partial"))


@pytest.mark.parametrize("phase", [2, 3, 4])
def test_crossing_target_during_calculation_or_publication(recording, tmp_path, phase):
    run, _, _, _ = recording
    stamps = [NOW] * phase + [OPENED + 2 * forward.STEP] * (5 - phase)
    iterator = iter(stamps)
    with pytest.raises(ValueError, match="Target has already closed"):
        run(clock=lambda: next(iterator))
    assert not list((tmp_path / "records").glob("*.json"))
    assert not list((tmp_path / "records").glob("*.partial"))
    assert run()[0].exists()  # a failed attempt does not reserve an identity


@pytest.mark.parametrize("phase", [1, 2, 3, 4])
def test_clock_reversal(recording, phase):
    stamps = [NOW] * phase + [NOW - timedelta(seconds=1)] * (5 - phase)
    iterator = iter(stamps)
    with pytest.raises(ValueError, match="Clock reversed"):
        recording[0](clock=lambda: next(iterator))


@pytest.mark.parametrize("failure", ["write", "link"])
def test_publication_failure_safe_retry(recording, monkeypatch, tmp_path, failure):
    target = "fsync" if failure == "write" else "link"
    original = getattr(forward.os, target)

    def fail(*args):
        raise OSError("synthetic failure")

    monkeypatch.setattr(forward.os, target, fail)
    with pytest.raises(OSError):
        recording[0]()
    assert not list((tmp_path / "records").glob("*"))
    monkeypatch.setattr(forward.os, target, original)
    assert recording[0]()[0].exists()


def test_directory_fsync_failure_is_explicit(recording, monkeypatch):
    original = forward.os.fsync
    calls = 0

    def sync(fd):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("directory sync failed")
        return original(fd)

    monkeypatch.setattr(forward.os, "fsync", sync)
    with pytest.raises(RuntimeError, match="Record visible.*durability"):
        recording[0]()
    with pytest.raises(FileExistsError):
        recording[0]()


def test_concurrent_publication_has_one_winner(recording, tmp_path):
    _, record = recording[0]()
    record.pop("content_sha256")
    path = tmp_path / "race" / "record.json"
    barrier = Barrier(2)

    def attempt():
        try:
            forward.publish(
                copy.deepcopy(record), path, lambda: (barrier.wait(), NOW)[1]
            )
            return "success"
        except FileExistsError:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == ["duplicate", "success"]
    assert not list(path.parent.glob("*.partial"))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(schema_version=2),
        lambda r: r.update(outcome=123),
        lambda r: r.update(feature_names=list(reversed(FEATURES))),
        lambda r: r["feature_values"].__setitem__(0, 99),
        lambda r: r["predictions"][0].update(predicted_log_return_4h=0.2),
        lambda r: r["predictions"][0].update(model_id="other"),
        lambda r: r["predictions"].pop(),
        lambda r: r["model"].update(model_recipe_sha256="0" * 64),
        lambda r: r["source_candles"][0].update(close="102"),
        lambda r: r["source_candles"][0].update(close=101),
        lambda r: r["source_candles"][0].update(
            recorded_at="2026-10-14T16:00:00+00:00"
        ),
        lambda r: r.update(issued_at="2026-10-14T16:00:00+00:00"),
        lambda r: r.update(calculated_at="2026-10-14T12:03:00+00:00"),
        lambda r: r.update(target_close_boundary="2026-10-14T20:00:00+00:00"),
        lambda r: r.update(issued_at="2026-10-14T12:02:00"),
    ],
)
def test_verifier_rejects_rehashed_invalid_evidence(recording, tmp_path, mutation):
    _, record = recording[0]()
    record.pop("content_sha256")
    mutation(record)
    record["content_sha256"] = forward.sha256(forward.canonical(record))
    path = tmp_path / "altered.json"
    path.write_bytes(forward.canonical(record))
    with pytest.raises(ValueError):
        forward.verify_forward(path, source=recording[3])


def test_hash_and_duplicate_json_keys(recording, tmp_path):
    _, record = recording[0]()
    record["feature_values"][0] = 123
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="SHA-256"):
        forward.verify_forward(path, source=recording[3])
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        forward.verify_forward(path, source=recording[3])


def test_independent_market_records(tmp_path, monkeypatch, synthetic_fit):
    monkeypatch.setattr(forward, "read_window", lambda c, s, t: sample_window(s))
    records = [
        forward.record_forward(
            None, s, source=synthetic_fit[0], destination=tmp_path, clock=lambda: NOW
        )
        for s in forward.SYMBOLS
    ]
    assert records[0][0] != records[1][0]
    assert (
        records[0][1]["model"]["model_recipe_sha256"]
        != records[1][1]["model"]["model_recipe_sha256"]
    )
    assert all(
        forward.verify_forward(p, source=synthetic_fit[0])["verified"]
        for p, _ in records
    )


@pytest.mark.parametrize(
    "option", ["--issued-at", "--now", "--start", "--clock", "--source"]
)
def test_no_production_timestamp_or_training_overrides(option):
    with pytest.raises(SystemExit) as result:
        cli.main(["record-forward", "--symbol", "BTCUSDT", option, "2024-01-01"])
    assert result.value.code == 2


def test_verify_cli_is_offline(recording, monkeypatch, capsys):
    path, _ = recording[0]()
    real_verify = forward.verify_forward
    monkeypatch.setattr(
        forward, "verify_forward", lambda p: real_verify(p, source=recording[3])
    )
    monkeypatch.setattr(cli, "load_settings", lambda: pytest.fail("Loaded DB settings"))
    assert cli.main(["verify-forward", "--record", str(path)]) == 0
    assert "unscored" in capsys.readouterr().out
    assert cli.main(["verify-forward", "--record", str(path.parent / "missing")]) == 1


def test_record_cli_summary_and_no_sync(recording, monkeypatch, capsys, config_env):
    from contextlib import nullcontext

    from backtest_badger.config import load_settings

    run, _, _, _ = recording
    result = run()
    monkeypatch.setattr(cli, "load_settings", lambda: load_settings(config_env))
    monkeypatch.setattr(
        cli, "connect_database", lambda _: nullcontext("read connection")
    )
    monkeypatch.setattr(cli, "sync_recent", lambda *a: pytest.fail("Ingested data"))

    def record(conn, symbol):
        assert conn == "read connection" and symbol == "BTCUSDT"
        return result

    monkeypatch.setattr(forward, "record_forward", record)
    assert cli.main(["record-forward", "--symbol", "BTCUSDT"]) == 0
    output = capsys.readouterr().out
    assert str(result[0]) in output and "Unscored" in output
    assert all(p["prediction_id"] in output for p in result[1]["predictions"])


@pytest.mark.parametrize(
    "error,visible",
    [
        (ValueError("Stale data: refresh separately"), "Stale data"),
        (FileExistsError("Already recorded"), "original retained"),
        (OSError("private details"), "details suppressed"),
    ],
)
def test_record_cli_failures(monkeypatch, config_env, caplog, error, visible):
    from contextlib import nullcontext

    from backtest_badger.config import load_settings

    monkeypatch.setattr(cli, "load_settings", lambda: load_settings(config_env))
    monkeypatch.setattr(cli, "connect_database", lambda _: nullcontext(None))

    def fail(*a):
        raise error

    monkeypatch.setattr(forward, "record_forward", fail)
    assert cli.main(["record-forward", "--symbol", "ETHUSDT"]) == 1
    assert visible in caplog.text and "private details" not in caplog.text


@pytest.mark.parametrize("body", ["null", "[]", "{}", "42", '{"content_sha256":null}'])
def test_malformed_json_rejected(tmp_path, body):
    path = tmp_path / "malformed.json"
    path.write_text(body)
    with pytest.raises(ValueError):
        forward.verify_forward(path)

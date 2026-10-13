"""Synthetic research cases; never read the actual frozen market dataset."""

import copy
import csv
import hashlib
import json
import math
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from backtest_badger.features import (
    FEATURE_DEFINITIONS,
    KNOWN_ANOMALIES,
    SPLITS,
    build_rows,
    causal_features,
    fit_reference,
    log_return,
    partition,
    prepare_dataset,
    target_summaries,
)
from backtest_badger.frozen import DATASET_ID, STEP, SYMBOLS, load_frozen, utc_time
from backtest_badger.research import COLUMNS

START = datetime(2023, 12, 28, tzinfo=UTC)


def candles(start=START, n=36, symbol="BTCUSDT"):
    return [
        {
            "venue": "binance",
            "market_type": "spot",
            "symbol": symbol,
            "base_asset": symbol[:-4],
            "quote_asset": "USDT",
            "interval_seconds": 14400,
            "open_time": start + i * STEP,
            "open": Decimal(100 + i),
            "high": Decimal(1000),
            "low": Decimal(1),
            "close": Decimal(100 + i),
            "base_volume": Decimal(i + 1),
            "quote_volume": Decimal(1000),
            "trade_count": 1,
            "taker_buy_base_volume": Decimal(0),
            "taker_buy_quote_volume": Decimal(0),
            "version": 1,
            "observed_at": datetime(2026, 10, 13, tzinfo=UTC),
            "source_kind": "archive",
            "source_url": "https://example.invalid/synthetic",
            "source_sha256": "a" * 64,
        }
        for i in range(n)
    ]


@pytest.fixture
def frozen_source(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    rows = {s: candles(symbol=s) for s in SYMBOLS}
    removed = [START + 9 * STEP, START + 10 * STEP]
    manifest = {
        "dataset_id": DATASET_ID,
        "export_schema_version": 1,
        "dataset_file": "candles.csv",
        "symbols": list(SYMBOLS),
        "interval": "4h",
        "start": START.isoformat(),
        "end_exclusive": (START + 36 * STEP).isoformat(),
        "status": "incomplete",
        "incomplete_acknowledged": True,
        "selection_policy": "Synthetic snapshot, not point-in-time publication",
        "row_counts": dict.fromkeys(SYMBOLS, 34),
        "coverage": {
            "interval_seconds": 14400,
            "start": START.isoformat(),
            "end_exclusive": (START + 36 * STEP).isoformat(),
            "status": "incomplete",
            "complete": False,
            "unreadable_manifests": [],
            "markets": {},
        },
    }
    for symbol in SYMBOLS:
        rows[symbol] = [r for r in rows[symbol] if r["open_time"] not in removed]
        manifest["coverage"]["markets"][symbol] = {
            "actual_count": 34,
            "expected_count": 36,
            "missing_count": 2,
            "missing_intervals": [t.isoformat() for t in removed],
            "first_observed": START.isoformat(),
            "last_observed": (START + 35 * STEP).isoformat(),
            "duplicate_identity_count": 0,
            "unexpected_before_boundary": 0,
            "failed_or_unresolved_imports": [],
            "months_without_import_evidence": [],
            "months_not_attempted": [],
            "known_source_missing_count": 1,
            "excluded_provider_observation_count": 1,
            "source_diagnostics": [
                {
                    "source_missing_intervals": [removed[0].isoformat()],
                    "missing_intervals": [t.isoformat() for t in removed],
                    "excluded_observations": [
                        {
                            "open_time": removed[1].isoformat(),
                            "reason": "irregular_close_time",
                            "action": "excluded_without_normalization",
                        }
                    ],
                }
            ],
        }

    def write():
        with (source / "candles.csv").open("w", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(COLUMNS)
            for values in rows.values():
                for row in values:
                    writer.writerow(
                        [
                            v.isoformat() if isinstance(v, datetime) else v
                            for v in (row[k] for k in COLUMNS)
                        ]
                    )
        return repin(source, manifest)

    return source, rows, manifest, write


def repin(source, manifest):
    digest = hashlib.sha256((source / "candles.csv").read_bytes()).hexdigest()
    manifest["sha256"] = digest
    (source / "manifest.json").write_text(json.dumps(manifest))
    return {
        "expected_csv_sha256": digest,
        "expected_manifest_sha256": hashlib.sha256(
            (source / "manifest.json").read_bytes()
        ).hexdigest(),
    }


def test_hand_calculated_features():
    rows = candles(n=7)
    for i, row in enumerate(rows):
        row["close"] = Decimal(2) ** i
    result = causal_features(rows)
    assert result["log_return_4h"] == pytest.approx(math.log(2))
    assert result["log_return_12h"] == pytest.approx(3 * math.log(2))
    assert result["log_return_24h"] == pytest.approx(6 * math.log(2))
    assert result["realised_volatility_24h"] == pytest.approx(
        math.sqrt(6) * math.log(2)
    )
    assert result["relative_base_volume"] == 2


def test_volatility_is_not_demeaned_or_annualised():
    rows = candles(n=7)
    for row, price in zip(rows, [1, 2, 1, 2, 1, 2, 1], strict=True):
        row["close"] = Decimal(price)
    assert causal_features(rows)["realised_volatility_24h"] == pytest.approx(
        math.sqrt(6) * math.log(2)
    )
    assert causal_features(rows)["log_return_24h"] == 0


def test_precision_preserved_before_logarithm():
    assert log_return(
        Decimal("100.000000000000000000000000000000000000001"), Decimal("100")
    ) == pytest.approx(1e-41, rel=1e-12, abs=0)


def test_alignment_and_warmup():
    rows, counts, audit = build_rows(
        {"BTCUSDT": candles(n=12)}, START, START + 12 * STEP
    )
    assert len(rows) == 5
    first = rows[0]
    assert first["open_time"] == START + 6 * STEP
    assert first["feature_available_at"] == utc_time("2023-12-29T04:01:00Z")
    assert first["target_open_time"] == START + 7 * STEP
    assert first["target_close_time"] == START + 8 * STEP
    assert first["target_available_at"] == utc_time("2023-12-29T08:01:00Z")
    assert first["target_log_return_4h"] == pytest.approx(math.log(107 / 106))
    assert counts["BTCUSDT"]["dropped"]["rolling_warmup"] == 6
    assert counts["BTCUSDT"]["dropped"]["source_end_target"] == 1
    assert len(audit) == 7


def test_future_values_cannot_change_features_or_earlier_labels():
    data = candles(n=20)
    before, _, _ = build_rows({"BTCUSDT": data}, START, START + 20 * STEP)
    changed = copy.deepcopy(data)
    for row in changed[11:]:
        row["close"] *= 100
        row["base_volume"] *= 900
    after, _, _ = build_rows({"BTCUSDT": changed}, START, START + 20 * STEP)
    for a, b in zip(before, after, strict=True):
        if a["open_time"] <= data[10]["open_time"]:
            assert {k: a[k] for k in FEATURE_DEFINITIONS} == {
                k: b[k] for k in FEATURE_DEFINITIONS
            }
        if a["open_time"] < data[10]["open_time"]:
            assert a["target_log_return_4h"] == b["target_log_return_4h"]
    assert before[4]["target_log_return_4h"] != after[4]["target_log_return_4h"]
    assert causal_features(data[4:11]) == {k: before[4][k] for k in FEATURE_DEFINITIONS}


@pytest.mark.parametrize("missing", [8, 9, 10])
def test_missing_windows_never_bridge_or_fill(missing):
    data = candles(n=22)
    gap = data[missing]["open_time"]
    reduced = [r for r in data if r["open_time"] != gap]
    rows, counts, audit = build_rows({"BTCUSDT": reduced}, START, START + 22 * STEP)
    assert all(
        not r["open_time"] - 6 * STEP <= gap <= r["open_time"] + STEP for r in rows
    )
    assert counts["BTCUSDT"]["dropped"]["missing_candle_window"] == 7
    assert any(r["open_time"] == gap + 7 * STEP for r in rows)
    assert any(a["missing_in_range"] == [gap.isoformat()] for a in audit)
    assert len(reduced) == 21


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.pop(3),
        lambda rows: rows[3].update(open_time=rows[2]["open_time"]),
        lambda rows: rows[3].update(symbol="ETHUSDT"),
    ],
)
def test_causal_features_refuse_invalid_window(mutate):
    data = candles(n=7)
    mutate(data)
    with pytest.raises(ValueError, match="seven consecutive"):
        causal_features(data)


def test_zero_volume_is_not_filled():
    data = candles(n=9)
    for row in data[:6]:
        row["base_volume"] = Decimal(0)
    assert causal_features(data[:7]) is None
    rows, counts, _ = build_rows({"BTCUSDT": data}, START, START + 9 * STEP)
    assert counts["BTCUSDT"]["dropped"]["zero_volume_history"] == 1
    assert rows[0]["open_time"] == data[7]["open_time"]
    data[6]["base_volume"] = Decimal(0)
    assert causal_features(data[2:9])["relative_base_volume"] == 6.75


def test_known_anomaly_is_excluded_even_with_full_grid():
    anomaly = utc_time(KNOWN_ANOMALIES[0]["open_time"])
    start = anomaly - 10 * STEP
    rows, counts, audit = build_rows(
        {"BTCUSDT": candles(start=start, n=22)}, start, start + 22 * STEP
    )
    assert counts["BTCUSDT"]["dropped"]["known_anomaly_window"] == 8
    assert all(
        not r["open_time"] - 6 * STEP <= anomaly <= r["open_time"] + STEP for r in rows
    )
    assert len([a for a in audit if a["known_anomalies"]]) == 8


@pytest.mark.parametrize("boundary", [s[2] for s in SPLITS])
@pytest.mark.parametrize("delay", [0, 60, 14399])
def test_split_clock_and_label_purge(boundary, delay):
    start = boundary - 10 * STEP
    rows, counts, _ = build_rows(
        {"BTCUSDT": candles(start=start, n=20)},
        start,
        start + 20 * STEP,
        settling_seconds=delay,
    )
    assert counts["BTCUSDT"]["dropped"]["split_boundary_label"] == 1
    for row in rows:
        name, end = partition(row["feature_available_at"])
        assert name == row["split"]
        assert row["feature_available_at"] < row["target_available_at"] < end
    assert not any(r["open_time"] == boundary - 2 * STEP for r in rows)
    if boundary.year != 2026:
        at_boundary = next(r for r in rows if r["open_time"] == boundary - STEP)
        assert at_boundary["split"] == (
            "validation" if boundary.year == 2024 else "test"
        )


@pytest.mark.parametrize("delay", [-1, 14400, True, 1.5])
def test_invalid_settling_delay(delay):
    with pytest.raises(ValueError, match="Settling"):
        build_rows({}, START, START + STEP, settling_seconds=delay)


def test_reference_fits_only_train_and_no_holdout_summaries():
    rows = [
        {"symbol": s, "split": split, "target_log_return_4h": value}
        for s in SYMBOLS
        for split, value in [
            ("train", 1.0),
            ("train", 3.0),
            ("validation", -400.0),
            ("test", 10000.0),
        ]
    ]
    assert fit_reference(rows) == dict.fromkeys(SYMBOLS, 2)
    rows[-1]["target_log_return_4h"] = -1e30
    assert fit_reference(rows) == dict.fromkeys(SYMBOLS, 2)
    assert isinstance(target_summaries(rows)["BTCUSDT"]["test"], str)
    with pytest.raises(ValueError, match="No eligible training"):
        fit_reference([r for r in rows if r["split"] == "test"])


def test_frozen_precision_and_diagnostics(frozen_source):
    source, rows, _, write = frozen_source
    rows["BTCUSDT"][0]["close"] = Decimal("100.000000000000000000000000000000000000001")
    manifest, loaded = load_frozen(source, acknowledge_incomplete=True, **write())
    assert loaded["BTCUSDT"][0]["close"] == rows["BTCUSDT"][0]["close"]
    assert len(loaded["BTCUSDT"]) == 34
    assert manifest["status"] == "incomplete"


def test_requires_own_acknowledgement(frozen_source):
    source, _, _, write = frozen_source
    with pytest.raises(ValueError, match="acknowledge-incomplete"):
        load_frozen(source, **write())


@pytest.mark.parametrize("filename", ["candles.csv", "manifest.json"])
def test_pinned_bytes_reject_alteration(frozen_source, filename):
    source, _, _, write = frozen_source
    pins = write()
    with (source / filename).open("a") as f:
        f.write("\n")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        load_frozen(source, acknowledge_incomplete=True, **pins)


@pytest.mark.parametrize(
    "change",
    [
        lambda rows, m: m.update(export_schema_version=2),
        lambda rows, m: m.update(interval="1h"),
        lambda rows, m: m.update(status="complete"),
        lambda rows, m: m["row_counts"].update(BTCUSDT=35),
        lambda rows, m: m["coverage"]["markets"]["BTCUSDT"].update(
            missing_intervals=[]
        ),
        lambda rows, m: rows["BTCUSDT"].reverse(),
        lambda rows, m: rows["BTCUSDT"].insert(1, rows["BTCUSDT"][0]),
        lambda rows, m: rows["BTCUSDT"][0].update(interval_seconds=3600),
        lambda rows, m: rows["BTCUSDT"][0].update(venue="other"),
        lambda rows, m: rows["BTCUSDT"][0].update(open_time=START.replace(minute=1)),
        lambda rows, m: rows["BTCUSDT"][0].update(open_time=START.replace(tzinfo=None)),
        lambda rows, m: rows["BTCUSDT"][0].update(close=Decimal("NaN")),
        lambda rows, m: rows["BTCUSDT"][0].update(close=Decimal(0)),
        lambda rows, m: rows["BTCUSDT"].pop(12),
        lambda rows, m: m["coverage"]["markets"]["BTCUSDT"]["source_diagnostics"][0][
            "excluded_observations"
        ][0].update(reason="unknown"),
    ],
)
def test_incompatible_inputs_rejected_even_with_matching_hashes(frozen_source, change):
    source, rows, manifest, write = frozen_source
    change(rows, manifest)
    with pytest.raises(ValueError):
        load_frozen(source, acknowledge_incomplete=True, **write())


def test_schema_rejected(frozen_source):
    source, _, manifest, write = frozen_source
    write()
    content = (
        (source / "candles.csv").read_bytes().replace(b"close,", b"closing_price,", 1)
    )
    (source / "candles.csv").write_bytes(content)
    with pytest.raises(ValueError, match="schema"):
        load_frozen(source, acknowledge_incomplete=True, **repin(source, manifest))


def test_deterministic_artifact_and_preservation(frozen_source, tmp_path):
    source, _, _, write = frozen_source
    pins = write()
    original = {p.name: p.read_bytes() for p in source.iterdir()}
    a, b = tmp_path / "a", tmp_path / "b"
    reports = [
        prepare_dataset(source, out, acknowledge_incomplete=True, **pins)
        for out in (a, b)
    ]
    assert reports[0] == reports[1]
    assert (a / "research.csv").read_bytes() == (b / "research.csv").read_bytes()
    assert (a / "manifest.json").read_bytes() == (b / "manifest.json").read_bytes()
    digest = hashlib.sha256((a / "research.csv").read_bytes()).hexdigest()
    assert digest == reports[0]["sha256"]
    for item in reports[0]["counts"].values():
        assert item["source_rows"] == item["eligible_rows"] + sum(
            item["dropped"].values()
        )
    with (a / "research.csv").open() as f:
        for row in csv.DictReader(f):
            if row["split"] == "train":
                assert row["prediction_train_mean"] == ""
            else:
                means = reports[0]["reference_predictions"]["training_mean_by_market"]
                assert float(row["prediction_train_mean"]) == means[row["symbol"]]
    with pytest.raises(FileExistsError):
        prepare_dataset(source, a, acknowledge_incomplete=True, **pins)
    assert {p.name: p.read_bytes() for p in source.iterdir()} == original
    assert not list(a.glob("*.partial"))


def test_cli_offline_success(monkeypatch, tmp_path, capsys):
    from backtest_badger import cli

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Offline research must not load DB configuration or open connections"
        )

    monkeypatch.setattr(cli, "load_settings", forbidden)
    monkeypatch.setattr(cli, "connect_database", forbidden)
    seen = {}

    def prepare(source, output, **kwargs):
        seen.update(source=source, output=output, **kwargs)
        return {
            "counts": {},
            "total_eligible_rows": 2,
            "sha256": "a" * 64,
            "target_summaries": {},
        }

    monkeypatch.setattr(cli, "prepare_dataset", prepare)
    output = tmp_path / "research"
    assert (
        cli.main(
            [
                "prepare-research",
                "--output",
                str(output),
                "--acknowledge-incomplete",
                "--settling-seconds",
                "120",
            ]
        )
        == 0
    )
    assert seen["acknowledge_incomplete"] is True
    assert seen["settling_seconds"] == 120
    assert seen["output"] == output
    assert "Research manifest" in capsys.readouterr().out


def test_cli_requires_ack_before_configuration_or_files(monkeypatch, tmp_path, caplog):
    from backtest_badger import cli

    monkeypatch.setattr(cli, "load_settings", lambda: pytest.fail("No settings needed"))
    output = tmp_path / "research"
    assert cli.main(["prepare-research", "--output", str(output)]) == 1
    assert "acknowledge-incomplete" in caplog.text
    assert not output.exists()


def test_manifest_mutation_cannot_hide_csv_change(frozen_source):
    source, _, manifest, write = frozen_source
    pins = write()
    content = (source / "candles.csv").read_bytes().replace(b"100,1000", b"101,1000", 1)
    (source / "candles.csv").write_bytes(content)
    repin(source, manifest)
    with pytest.raises(ValueError, match="manifest SHA-256"):
        load_frozen(source, acknowledge_incomplete=True, **pins)


def test_markets_share_boundaries_but_not_rolling_history():
    start = datetime(2024, 12, 29, tzinfo=UTC)
    markets = {s: candles(start=start, n=30, symbol=s) for s in SYMBOLS}
    for row in markets["ETHUSDT"]:
        row["close"] = Decimal(42)
    rows, counts, _ = build_rows(markets, start, start + 30 * STEP)
    assert counts["BTCUSDT"]["splits"] == counts["ETHUSDT"]["splits"]
    assert {r["split"] for r in rows} == {"validation", "test"}
    assert all(r["log_return_4h"] == 0 for r in rows if r["symbol"] == "ETHUSDT")
    assert all(r["log_return_4h"] > 0 for r in rows if r["symbol"] == "BTCUSDT")

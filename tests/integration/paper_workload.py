"""Generate Stage 3-shaped originals from packaged fabricated candles only."""

import json
from dataclasses import replace
from datetime import timedelta
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from backtest_badger import forward
from backtest_badger import paper_evidence as evidence
from backtest_badger import paper_fixture as fx
from backtest_badger import paper_records as rec
from backtest_badger.forward_evaluation import candle_from_json
from backtest_badger.paper_forward_adapter import Observation
from backtest_badger.paper_types import STEP, D, Forecast, Portfolio

COHORT = "fabricated-stage-4d2"
ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/stage-04a-prospective-evaluation-protocol.md"
IMPLEMENTATION = ROOT / "src/backtest_badger/paper_persistence.py"
BASE = json.loads(next((fx.ROOT / "records").glob("*080000Z.json")).read_bytes())


@lru_cache(maxsize=2)
def recipe(symbol):
    model = dict(BASE["model"], symbol=symbol)
    del model["model_recipe_sha256"]
    model["model_recipe_sha256"] = forward.sha256(forward.canonical(model))
    return model


def portfolio(symbol, inception=fx.INCEPTION):
    pin = recipe(symbol)["model_recipe_sha256"]
    config = rec.configuration(symbol, pin, COHORT)
    return Portfolio(
        f"{COHORT}-{symbol}",
        symbol,
        inception,
        rec.fingerprint(rec.canonical(config)),
        sha256(PROTOCOL.read_bytes()).hexdigest(),
        pin,
    )


def publish_slot(root, opened, signals):
    """One shared two-market journal, two independently hashed Ridge records."""
    issued = opened + STEP + timedelta(minutes=11)
    run = rec.identity("fabricated", "journal", opened.isoformat()).hex
    journal = dict(
        schema_version=1,
        run_id=run,
        source_open_time=opened.isoformat(),
        started_at=issued.isoformat(),
        finished_at=issued.isoformat(),
        feature_available_at=(opened + STEP + forward.DELAY).isoformat(),
        deadline=(opened + STEP + timedelta(minutes=16)).isoformat(),
        state="complete",
        markets={},
    )
    originals = {}
    for symbol, signal in signals.items():
        market_id = 1 if symbol == "BTCUSDT" else 2
        market = dict(
            BASE["market"], symbol=symbol, base_asset=symbol[:-4], market_id=market_id
        )
        candles = []
        for row in BASE["source_candles"]:
            candle = candle_from_json(row)
            candle.update(
                {key: candle[key] + (opened - fx.OPEN) for key in forward.TIME_FIELDS}
            )
            candle.update(
                market_id=market_id,
                source_url=candle["source_url"].replace("BTCUSDT", symbol),
            )
            candles.append(candle)
        features = forward.validate_window(market, candles, opened, issued)
        predictions = dict.fromkeys(forward.MODELS, 0.0)
        predictions["ridge"] = signal
        record = forward.evidence(
            market,
            candles,
            features,
            predictions,
            recipe(symbol),
            issued,
            issued,
            issued,
        )
        content = forward.sha256(forward.canonical(record))
        body = forward.canonical(dict(record, content_sha256=content)) + b"\n"
        name = record["record_id"] + ".json"
        (root / "records" / name).write_bytes(body)
        journal["markets"][symbol] = dict(
            status="recorded",
            record_path=str(forward.RECORDS / name),
            issued_at=issued.isoformat(),
            source_open_time=opened.isoformat(),
            issuance_delay_seconds=600.0,
            verification="replayed",
            refresh="complete_fresh",
            error_category=None,
            file_sha256=forward.sha256(body),
            content_sha256=content,
        )
        f = Forecast(
            portfolio(symbol),
            record["record_id"],
            opened,
            issued,
            issued,
            D(str(signal)),
            forward.sha256(body),
            content,
            recipe(symbol)["model_recipe_sha256"],
            None,
        )
        originals[symbol] = Observation(
            f, record["record_id"] + ":ridge", name, None, body
        )
    for symbol in ("BTCUSDT", "ETHUSDT"):
        journal["markets"].setdefault(symbol, {"status": "failed"})
    raw = forward.canonical(journal) + b"\n"
    filename = f"{issued:%Y%m%dT%H%M%S%fZ}-{run}.json"
    (root / "operations" / filename).write_bytes(raw)
    evidence = dict(
        filename=filename, file_sha256=forward.sha256(raw), json_utf8=raw.decode()
    )
    return {
        s: replace(
            o,
            forecast=replace(o.forecast, automation_sha256=evidence["file_sha256"]),
            journal=evidence,
        )
        for s, o in originals.items()
    }


def originals(root):
    for name in ("records", "operations", "private"):
        (root / name).mkdir(mode=0o700)
    archive = root / "private"
    release = [
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        PROTOCOL,
        ROOT / "docs/stage-04a-paper-trading-spec.md",
        *sorted((ROOT / "src/backtest_badger").glob("*.py")),
        *sorted((ROOT / "migrations/sql/0002").glob("*.sql")),
        *sorted((ROOT / "migrations/versions").glob("*.py")),
    ]
    manifest = {
        str(path.relative_to(ROOT)): evidence.retain(archive, path.read_bytes())
        for path in release
    }
    implementation = evidence.retain(archive, forward.canonical(manifest))
    for symbol in ("BTCUSDT", "ETHUSDT"):
        unsigned = dict(recipe(symbol))
        pin = unsigned.pop("model_recipe_sha256")
        assert evidence.retain(archive, forward.canonical(unsigned)) == pin
    return archive, implementation

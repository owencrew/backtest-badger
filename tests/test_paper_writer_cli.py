import json
from datetime import timedelta

import pytest

from backtest_badger import paper_fixture as fx
from backtest_badger import paper_writer_cli as cli
from backtest_badger.paper_market_data import QUOTE, MarketError


@pytest.mark.parametrize("argv", [[], ["dry-run"], ["staging-once"]])
def test_writer_requires_explicit_mode_and_reviewed_config(argv):
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    assert exc.value.code == 2


@pytest.mark.parametrize("status", [418, 429])
def test_cooldown_survives_restart_and_applies_to_both_markets(tmp_path, status):
    attempts = []

    def throttle(endpoint, symbol, clock):
        attempts.append(symbol)
        raise MarketError("rate_limited", status, 620)

    start = fx.fixed_clock(fx.ISSUED)
    with pytest.raises(MarketError, match="rate_limited"):
        cli.shared_provider(tmp_path, throttle)(QUOTE, "BTCUSDT", start)
    restarted = cli.shared_provider(tmp_path, throttle)
    with pytest.raises(MarketError, match="provider_cooldown") as exc:
        restarted(QUOTE, "ETHUSDT", fx.fixed_clock(fx.ISSUED + timedelta(minutes=5)))
    assert exc.value.retry_after == 320 and attempts == ["BTCUSDT"]
    with pytest.raises(MarketError, match="rate_limited"):
        restarted(QUOTE, "ETHUSDT", fx.fixed_clock(fx.ISSUED + timedelta(seconds=621)))
    assert attempts == ["BTCUSDT", "ETHUSDT"]


def test_clock_requires_a_trustworthy_current_observation(tmp_path, monkeypatch):
    path = tmp_path / "health"
    assert cli.clock_health(path) is None
    path.write_text(
        json.dumps(
            dict(
                synchronised=True, sampled_at=fx.ISSUED.isoformat(), uncertainty_ms=101
            )
        )
    )
    assert cli.clock_health(path) is None
    monkeypatch.setattr(cli, "trusted_clock_path", lambda p: p == path)
    assert not cli.clock_health(path).trusted(fx.ISSUED)
    path.write_text("{}")
    assert cli.clock_health(path) is None

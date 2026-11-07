"""Fixed, fabricated BTC evidence for the offline CLI and PostgreSQL rehearsal."""

import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path

from backtest_badger import paper_records as rec
from backtest_badger.paper_accounting import Account, fund_account
from backtest_badger.paper_clock import Clock
from backtest_badger.paper_forward_adapter import read_forecast
from backtest_badger.paper_market_data import (
    FILTERS,
    QUOTE,
    Response,
    parse_quote,
    url_for,
)
from backtest_badger.paper_recovery import Recovery
from backtest_badger.paper_strategy import State
from backtest_badger.paper_types import D, Portfolio
from backtest_badger.paper_worker import cycle

ROOT = Path(__file__).with_name("paper_fixtures")
OPEN = datetime(2026, 10, 14, 8, tzinfo=UTC)
INCEPTION = OPEN + timedelta(hours=4, minutes=10)
ISSUED = INCEPTION + timedelta(minutes=1)
COHORT = "fabricated-stage-4d1"
RECIPE = "c83e3f41ebb0059e4d4173c871e26979918462600eaa3b0e9554dcd3419b169c"


def fixed_clock(at):
    return Clock(lambda: at, lambda: 0)


def portfolio():
    config = rec.configuration("BTCUSDT", RECIPE, COHORT)
    return Portfolio(
        COHORT,
        "BTCUSDT",
        INCEPTION,
        rec.fingerprint(rec.canonical(config)),
        rec.fingerprint(COHORT),
        RECIPE,
    )


def original(p, opened, clock):
    return read_forecast(p, opened, ROOT / "records", ROOT / "operations", clock)


def response(endpoint, p, clock, payload):
    body = json.dumps(payload, separators=(",", ":")).encode()
    return Response(
        url_for(endpoint, p.symbol),
        200,
        body,
        sha256(body).hexdigest(),
        clock.sample(),
        clock.sample(),
        clock.run_id,
    )


def quote(p, clock, price="100"):
    r = response(
        QUOTE,
        p,
        clock,
        dict(
            symbol=p.symbol,
            bidPrice=price,
            askPrice=price,
            bidQty="1000",
            askQty="1000",
        ),
    )
    return parse_quote(r, p, clock.now())


def filter_source(p, clock):
    lots = dict(filterType="LOT_SIZE", minQty="0.01", maxQty="1000", stepSize="0.01")
    market = dict(filterType="MARKET_LOT_SIZE", minQty="0", maxQty="500", stepSize="0")
    notional = dict(
        filterType="MIN_NOTIONAL", applyToMarket=True, minNotional="5", avgPriceMins=5
    )
    symbol = dict(
        symbol=p.symbol,
        status="TRADING",
        isSpotTradingAllowed=True,
        orderTypes=["MARKET"],
        baseAsset=p.base_asset,
        quoteAsset="USDT",
        filters=[lots, market, notional],
    )
    return response(FILTERS, p, clock, {"symbols": [symbol], "exchangeFilters": []})


def demonstration():
    p = portfolio()
    account = fund_account(Account(p), INCEPTION)
    view = Recovery(
        State(account, OPEN, INCEPTION),
        "ACTIVE",
        INCEPTION,
        slots=frozenset({INCEPTION}),
    )
    assert account.cash == D(10000)
    return cycle(
        lambda: view,
        original,
        filter_source,
        quote,
        fixed_clock(ISSUED),
        lambda plan: None,
    )

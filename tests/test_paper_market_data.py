import io
import json
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
from urllib.error import HTTPError, URLError

import pytest

from backtest_badger import paper_fixture as fx
from backtest_badger import paper_market_data as md
from backtest_badger.paper_types import D


def raw(r, body):
    return replace(r, body=body, sha256=sha256(body).hexdigest())


def payload(r, value):
    return raw(r, json.dumps(value).encode())


@pytest.fixture(params=md.SYMBOLS)
def ticker(request):
    market = md.Market(request.param)
    obj = dict(
        symbol=market.symbol, bidPrice="99.99", askPrice="100", bidQty="0", askQty="2"
    )
    return fx.response(md.QUOTE, market, fx.fixed_clock(fx.ISSUED), obj), market


def test_quote_without_exchange_timestamp_or_guaranteed_depth(ticker):
    r, m = ticker
    q = md.parse_quote(r, m, fx.ISSUED)
    assert q.raw_body == r.body and q.bid == D("99.99") and q.bid_quantity == 0
    assert q.run_id == r.run_id and q.elapsed_seconds == 0


@pytest.mark.parametrize(
    "change",
    [
        "negative",
        "zero",
        "crossed",
        "quantity",
        "depth",
        "symbol",
        "nonfinite",
        "binary",
        "extra",
        "duplicate",
        "oversized",
        "malformed",
        "hash",
        "url",
        "status",
        "stale",
        "monotonic",
    ],
)
def test_invalid_ticker(ticker, change):
    r, m = ticker
    obj = json.loads(r.body)
    now = fx.ISSUED
    updates = {
        "negative": {"askPrice": "-1"},
        "zero": {"bidPrice": "0"},
        "crossed": {"askPrice": "99"},
        "depth": {"askQty": "-1"},
        "symbol": {"symbol": "SOLUSDT"},
        "nonfinite": {"askPrice": "NaN"},
        "binary": {"bidPrice": 99.99},
        "extra": {"time": 0},
    }
    if change in updates:
        r = payload(r, obj | updates[change])
    elif change == "quantity":
        del obj["bidQty"]
        r = payload(r, obj)
    elif change == "duplicate":
        r = raw(r, b'{"bidQty":"1",' + r.body[1:])
    elif change == "oversized":
        r = raw(r, r.body + b" " * 4096)
    elif change == "malformed":
        r = raw(r, b"{")
    elif change == "hash":
        r = replace(r, sha256="a" * 64)
    elif change == "url":
        r = replace(r, url="https://example.invalid")
    elif change == "status":
        r = replace(r, status=301)
    elif change == "stale":
        now += timedelta(seconds=1, microseconds=1)
    else:
        r = replace(r, end=replace(r.end, before_ns=1000000, after_ns=1000000))
    with pytest.raises(md.MarketError, match="invalid_quote"):
        md.parse_quote(r, m, now)


def rules(changes=lambda rows: None):
    p = fx.portfolio()
    r = fx.filter_source(p, fx.fixed_clock(fx.ISSUED))
    obj = json.loads(r.body)
    changes(obj["symbols"][0]["filters"])
    return payload(r, obj), p


@pytest.mark.parametrize(
    "min_flag,max_flag,expected_min,expected_max",
    [
        (True, True, 12, 500),
        (False, False, 5, None),
        (False, True, 5, 500),
        (True, False, 12, None),
    ],
)
def test_intersect_lot_and_notional(min_flag, max_flag, expected_min, expected_max):
    def changes(rows):
        rows[0].update(minQty="0.04", stepSize="0.03")
        rows[1].update(minQty="0.07", stepSize="0.02", maxQty="10")
        rows.append(
            dict(
                filterType="NOTIONAL",
                minNotional="12",
                maxNotional="500",
                applyMinToMarket=min_flag,
                applyMaxToMarket=max_flag,
                avgPriceMins=5,
            )
        )

    r, p = rules(changes)
    f = md.effective_filters(r, p, fx.ISSUED)
    assert (f.step, f.min_quantity, f.max_quantity) == (D(".06"), D(".07"), 10)
    assert (f.min_notional, f.max_notional) == (expected_min, expected_max)
    assert f.payload_sha256 == r.sha256


@pytest.mark.parametrize(
    "change",
    [
        "missing_step",
        "missing_max",
        "all_steps_disabled",
        "empty_grid",
        "negative",
        "wrong_bool",
        "unknown",
        "position",
        "duplicate",
        "ttl",
        "hash",
        "symbol",
        "url",
        "oversized",
        "exchange",
        "spot",
        "market",
    ],
)
def test_filters_fail_closed(change):
    def changes(rows):
        if change == "missing_step":
            rows[0].pop("stepSize")
        elif change == "missing_max":
            rows[1].pop("maxQty")
        elif change == "all_steps_disabled":
            rows[0]["stepSize"] = "0"
        elif change == "empty_grid":
            rows[0]["stepSize"] = "0.3"
            rows[1].update(stepSize="0.2", maxQty="0.4")
        elif change == "negative":
            rows[1]["stepSize"] = "-1"
        elif change == "wrong_bool":
            rows[2]["applyToMarket"] = 1
        elif change in ("unknown", "position"):
            rows.append(
                {"filterType": "MAX_POSITION" if change == "position" else "NEW_RULE"}
            )
        elif change == "duplicate":
            rows.append(rows[0])

    r, p = rules(changes)
    now = fx.ISSUED
    if change == "ttl":
        now += timedelta(hours=1, microseconds=1)
    if change == "hash":
        r = replace(r, sha256="1" * 64)
    if change == "url":
        r = replace(r, url=r.url.replace("BTC", "ETH"))
    if change == "oversized":
        r = raw(r, r.body + b" " * 65536)
    if change in ("symbol", "exchange", "spot", "market"):
        obj = json.loads(r.body)
        if change == "exchange":
            obj["exchangeFilters"] = [{"filterType": "UNKNOWN"}]
        else:
            obj["symbols"][0].update(
                {
                    "symbol": {"symbol": "ETHUSDT"},
                    "spot": {"isSpotTradingAllowed": False},
                    "market": {"orderTypes": ["LIMIT"]},
                }[change]
            )
        r = payload(r, obj)
    with pytest.raises(md.MarketError):
        md.effective_filters(r, p, now)


def test_disabled_notional_and_market_lot_only():
    def changes(rows):
        del rows[0]
        rows[0]["stepSize"] = "0.1"
        rows[1]["applyToMarket"] = False

    r, p = rules(changes)
    f = md.effective_filters(r, p, fx.ISSUED + timedelta(hours=1))
    assert f.min_notional == 0 and f.min_quantity == 0 and f.max_quantity == 500


@pytest.mark.parametrize("status", [301, 400, 418, 429, 500])
def test_http_stop_and_retry_metadata(monkeypatch, status):
    calls = []

    class Opener:
        def open(self, req, timeout):
            calls.append(req.full_url)
            raise HTTPError(
                req.full_url, status, "fixture", {"Retry-After": "30"}, io.BytesIO(b"")
            )

    monkeypatch.setattr(md, "build_opener", lambda *args: Opener())
    rows = md.smoke(fx.fixed_clock(fx.ISSUED))
    assert len(calls) == len(set(calls)) == (1 if status in (418, 429) else 4)
    assert all(r["status"] == status and r["retry_after_seconds"] == 30 for r in rows)


@pytest.mark.parametrize(
    "exc,expected",
    [
        (URLError(md.gaierror()), "dns"),
        (TimeoutError(), "timeout"),
        (OSError(), "connection"),
    ],
)
def test_transport(monkeypatch, exc, expected):
    class Opener:
        def open(self, *a, **k):
            raise exc

    monkeypatch.setattr(md, "build_opener", lambda *a: Opener())
    with pytest.raises(md.MarketError, match=expected):
        md.fetch(md.QUOTE, "BTCUSDT", fx.fixed_clock(fx.ISSUED))


def test_no_arbitrary_url_or_symbol():
    for endpoint, symbol in [
        (md.QUOTE, "ETHUSDT#bad"),
        ("https://example.com", "BTCUSDT"),
    ]:
        with pytest.raises(ValueError):
            md.url_for(endpoint, symbol)


def test_opt_in_private_filter_retention(tmp_path):
    from backtest_badger.paper_artifacts import retain_body

    r, p = rules()
    tmp_path.chmod(0o700)
    for _ in range(2):
        retain_body(tmp_path, r.body, r.sha256)
    saved = tmp_path / (r.sha256 + ".json")
    assert saved.read_bytes() == r.body and saved.stat().st_mode & 0o777 == 0o400
    saved.chmod(0o600)
    saved.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="Archive conflict"):
        retain_body(tmp_path, r.body, r.sha256)
    tmp_path.chmod(0o755)
    with pytest.raises(ValueError, match="owner-only"):
        retain_body(tmp_path, r.body, r.sha256)


def test_fetch_bounds_and_original_identity(monkeypatch):
    body = b'{"test":"fabricated transport"}'

    class Reply(io.BytesIO):
        code = 200
        headers = {"Content-Length": str(len(body))}

        def geturl(self):
            return md.url_for(md.FILTERS, "BTCUSDT")

    class Opener:
        def open(self, req, timeout):
            assert timeout == 2 and req.get_method() == "GET"
            return Reply(body)

    monkeypatch.setattr(md, "build_opener", lambda *a: Opener())
    r = md.fetch(md.FILTERS, "BTCUSDT", fx.fixed_clock(fx.ISSUED))
    assert r.body == body and r.sha256 == sha256(body).hexdigest()
    body = b"x" * 65537
    with pytest.raises(md.MarketError, match="oversized"):
        md.fetch(md.FILTERS, "BTCUSDT", fx.fixed_clock(fx.ISSUED))


def test_opener_has_no_redirect_following():
    from urllib.request import Request

    source = md.url_for(md.QUOTE, "BTCUSDT")
    assert (
        md._NoRedirect().redirect_request(
            Request(source), None, 302, "", {}, "https://example.invalid"
        )
        is None
    )


def test_unrecognised_field_on_quantity_constraint_stops_sizing():
    r, p = rules(lambda rows: rows[0].update(newQuantityCondition="fabricated"))
    with pytest.raises(md.MarketError, match="unsupported_filter_fields:LOT_SIZE"):
        md.effective_filters(r, p, fx.ISSUED)

"""One-shot, public-only Spot observations. No quote cache or order transport."""

import json
import re
import signal
from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from http.client import HTTPException
from math import lcm
from socket import gaierror
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

from backtest_badger.archives import _NoRedirect
from backtest_badger.forward_scoring_operations import CycleTimeout, time_limit
from backtest_badger.paper_artifacts import retain_body
from backtest_badger.paper_clock import Sample, duration
from backtest_badger.paper_types import (
    Filters,
    Quote,
    identifier,
    money_context,
    number,
    require,
    validate_filters,
    validate_quote,
)
from backtest_badger.rest import BASE

QUOTE = "ticker/bookTicker"
FILTERS = "exchangeInfo"
LIMIT = {QUOTE: 4096, FILTERS: 65536}
SYMBOLS = ("BTCUSDT", "ETHUSDT")


@dataclass(frozen=True)
class Market:
    symbol: str
    venue: str = "binance"
    market_type: str = "spot"


def url_for(endpoint, symbol):
    require(endpoint in LIMIT and symbol in SYMBOLS, "Unsupported public source.")
    return f"{BASE}{endpoint}?symbol={symbol}"


class MarketError(ValueError):
    def __init__(self, code, status=None, retry_after=None):
        super().__init__(code)
        self.code = code
        self.status = status
        self.retry_after = retry_after


@dataclass(frozen=True)
class Response:
    url: str
    status: int
    body: bytes
    sha256: str
    start: Sample
    end: Sample
    run_id: str


def fetch(endpoint, symbol, clock):
    # The explicit foreground action also bounds DNS, TLS and slow HTTP headers.
    url = url_for(endpoint, symbol)
    require(not signal.getitimer(signal.ITIMER_REAL)[0], "An outer alarm is active.")
    try:
        with time_limit(2):
            return _request(url, LIMIT[endpoint], clock)
    except CycleTimeout:
        raise MarketError("timeout") from None


def _request(url, limit, clock):
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    start = clock.sample()
    status = None
    try:
        try:
            resp = opener.open(Request(url), timeout=2)
        except HTTPError as exc:
            resp = exc
        with resp:
            status = resp.code
            if status != 200:
                retry = resp.headers.get("Retry-After", "")
                retry = int(retry) if re.fullmatch(r"[0-9]{1,9}", retry) else None
                raise MarketError(
                    "rate_limited" if status in (418, 429) else "http", status, retry
                )
            require(resp.geturl() == url, "Response URL changed.")
            body = bytearray()
            while len(body) <= limit:
                chunk = resp.read1(limit + 1 - len(body))
                if not chunk:
                    break
                body.extend(chunk)
            end = clock.sample()
            if len(body) > limit:
                raise MarketError("oversized", status)
            length = resp.headers.get("Content-Length")
            if length is not None and length != str(len(body)):
                raise MarketError("incomplete", status)
    except (URLError, HTTPException, OSError) as exc:
        cause = getattr(exc, "reason", exc)
        code = (
            "dns"
            if isinstance(cause, gaierror)
            else ("timeout" if isinstance(cause, TimeoutError) else "connection")
        )
        raise MarketError(code, status) from None
    return Response(
        url, status, bytes(body), sha256(body).hexdigest(), start, end, clock.run_id
    )


def unique(pairs):
    require(len(pairs) == len(dict(pairs)), "Duplicate JSON keys.")
    return dict(pairs)


def reject_constant(_):
    raise ValueError("Nonfinite JSON value.")


def verified_body(response, endpoint, market):
    identifier(response.run_id)
    require(
        response.url == url_for(endpoint, market.symbol)
        and type(response.status) is int
        and response.status == 200,
        "Invalid original source.",
    )
    require(
        type(response.body) is bytes
        and 0 < len(response.body) <= LIMIT[endpoint]
        and sha256(response.body).hexdigest() == response.sha256,
        "Invalid response size or SHA-256.",
    )
    elapsed = duration(response.start, response.end)
    require(elapsed <= 2, "Stale HTTP response.")
    return json.loads(
        response.body.decode("utf-8"),
        object_pairs_hook=unique,
        parse_constant=reject_constant,
    ), elapsed


def decimal_field(value):
    require(
        isinstance(value, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value),
        "Invalid decimal string.",
    )
    return number(Decimal(value))


def parse_quote(response, market, at):
    try:
        obj, elapsed = verified_body(response, QUOTE, market)
        q = Quote(
            uuid4().hex,
            response.run_id,
            obj["symbol"],
            response.start.wall,
            response.end.wall,
            *(
                decimal_field(obj[key])
                for key in ("bidPrice", "askPrice", "bidQty", "askQty")
            ),
            response.sha256,
            response.body,
            response.url,
            elapsed_seconds=elapsed,
        )
        validate_quote(q, market, at)
        return q
    except (ValueError, TypeError, KeyError, ArithmeticError, RecursionError) as exc:
        raise MarketError("invalid_quote", response.status) from exc


# Price/stop, iceberg, amend and list fields do not constrain a lone unpriced,
# base-quantity market intent. Account position rules are not representable.
OTHER = {
    "PRICE_FILTER",
    "PERCENT_PRICE",
    "PERCENT_PRICE_BY_SIDE",
    "ICEBERG_PARTS",
    "MAX_NUM_ALGO_ORDERS",
    "MAX_NUM_ICEBERG_ORDERS",
    "TRAILING_DELTA",
    "MAX_NUM_ORDER_AMENDS",
    "MAX_NUM_ORDER_LISTS",
}


# Newly added fields in a rule used for sizing need explicit interpretation.
ACTIVE_FIELDS = {
    "LOT_SIZE": {"minQty", "maxQty", "stepSize"},
    "MARKET_LOT_SIZE": {"minQty", "maxQty", "stepSize"},
    "MIN_NOTIONAL": {"minNotional", "applyToMarket", "avgPriceMins"},
    "NOTIONAL": {
        "minNotional",
        "maxNotional",
        "applyMinToMarket",
        "applyMaxToMarket",
        "avgPriceMins",
    },
    "MAX_NUM_ORDERS": {"maxNumOrders"},
}


def applicable(rule, flag, field):
    require(type(rule[flag]) is bool, "Expected market applicability boolean.")
    value = decimal_field(rule[field])
    return value if rule[flag] else Decimal(0)


def effective_filters(response, market, at):
    """Recheck the retained source bytes, market identity and TTL on every use."""
    try:
        obj, _ = verified_body(response, FILTERS, market)
        return _filter_rules(
            obj, market, response.end.wall, response.sha256, at, response.status
        )
    except MarketError:
        raise
    except (ValueError, TypeError, KeyError, ArithmeticError, RecursionError) as exc:
        raise MarketError("invalid_filters", response.status) from exc


def retained_filters(body, market, observed_at, fingerprint, at):
    """Replay archived exchangeInfo at its original persisted observation time."""
    require(
        0 < len(body) <= LIMIT[FILTERS] and sha256(body).hexdigest() == fingerprint,
        "Invalid archived filter original.",
    )
    obj = json.loads(
        body.decode("utf-8"), object_pairs_hook=unique, parse_constant=reject_constant
    )
    return _filter_rules(obj, market, observed_at, fingerprint, at, 200)


def _filter_rules(obj, market, observed_at, fingerprint, at, status):
    (symbol,) = obj["symbols"]
    require(
        obj["exchangeFilters"] == []
        and symbol["symbol"] == market.symbol
        and symbol["baseAsset"] == market.symbol[:-4]
        and symbol["quoteAsset"] == "USDT"
        and symbol["status"] == "TRADING"
        and symbol["isSpotTradingAllowed"] is True
        and isinstance(symbol["orderTypes"], list)
        and "MARKET" in symbol["orderTypes"],
        "Unsupported exchange or symbol.",
    )
    rules = {f["filterType"]: f for f in symbol["filters"]}
    require(len(rules) == len(symbol["filters"]), "Duplicate filter type.")
    if unknown := rules.keys() - OTHER - ACTIVE_FIELDS.keys():
        # Only report a bounded Binance-style type token from untrusted data.
        name = sorted(unknown)[0]
        label = name if re.fullmatch(r"[A-Z_]{1,48}", name) else "unknown"
        raise MarketError("unsupported_filter:" + label, status)
    for name in rules.keys() & ACTIVE_FIELDS.keys():
        if rules[name].keys() - ACTIVE_FIELDS[name] - {"filterType"}:
            raise MarketError("unsupported_filter_fields:" + name, status)
    if "MAX_NUM_ORDERS" in rules:
        count = rules["MAX_NUM_ORDERS"]["maxNumOrders"]
        require(type(count) is int and count >= 1, "Unsupported order limit.")
    lots = [rules[k] for k in ("LOT_SIZE", "MARKET_LOT_SIZE") if k in rules]
    steps = [v for f in lots if (v := decimal_field(f["stepSize"]))]
    maxima = [v for f in lots if (v := decimal_field(f["maxQty"]))]
    require(steps and maxima, "Missing representable quantity step or maximum.")
    with localcontext(money_context()):
        exponent = min(s.as_tuple().exponent for s in steps)
        step = Decimal(lcm(*(int(s.scaleb(-exponent)) for s in steps))).scaleb(exponent)
    minimum = max(decimal_field(f["minQty"]) for f in lots)
    nmin = Decimal(0)
    nmax = None
    if "MIN_NOTIONAL" in rules:
        nmin = applicable(rules["MIN_NOTIONAL"], "applyToMarket", "minNotional")
    if "NOTIONAL" in rules:
        rule = rules["NOTIONAL"]
        nmin = max(nmin, applicable(rule, "applyMinToMarket", "minNotional"))
        nmax = applicable(rule, "applyMaxToMarket", "maxNotional") or None
    f = Filters(
        market.symbol,
        observed_at,
        fingerprint,
        step,
        minimum,
        min(maxima),
        nmin,
        nmax,
    )
    validate_filters(f, market, at, acquired_by=at)
    return f


def smoke(clock, acquire=fetch, *, filter_archive=None):
    observations = []
    for symbol in SYMBOLS:
        for endpoint in (QUOTE, FILTERS):
            item = {"symbol": symbol, "endpoint": endpoint}
            observations.append(item)
            try:
                r = acquire(endpoint, symbol, clock)
                item.update(
                    status=r.status,
                    source_sha256=r.sha256,
                    started_at=r.start.wall.isoformat(),
                    received_at=r.end.wall.isoformat(),
                    elapsed_seconds=str(duration(r.start, r.end)),
                )
                if endpoint == FILTERS and filter_archive is not None:
                    require(
                        len(r.body) <= LIMIT[FILTERS]
                        and r.url == url_for(endpoint, symbol),
                        "Invalid filter archive source.",
                    )
                    retain_body(filter_archive, r.body, r.sha256)
                parser = parse_quote if endpoint == QUOTE else effective_filters
                parser(r, Market(symbol), clock.now())
                item["validation"] = "valid"
            except MarketError as exc:
                item.update(
                    validation=exc.code,
                    status=exc.status,
                    retry_after_seconds=exc.retry_after,
                )
                if exc.status in (418, 429):
                    return observations
            except OSError:
                item["validation"] = "archive_unavailable"
                return observations
            except ValueError:
                item["validation"] = "clock_or_source_failure"
                return observations
    return observations

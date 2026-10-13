import io
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from backtest_badger import rest

START = datetime(2026, 10, 1, tzinfo=UTC)


def row(opened=START):
    stamp = (opened - rest.EPOCH) // rest.MILLISECOND
    return [
        stamp,
        "100.123456789012345678901234567890123456789",
        "110",
        "90",
        "105",
        "123",
        stamp + 14400000 - 1,
        "12000",
        1234,
        "60",
        "6000",
        "ignored",
    ]


def response(rows, url="https://example.invalid/klines"):
    return rest.Response(
        json.dumps(rows).encode(), url, START + timedelta(days=181), 200, {}
    )


@pytest.mark.parametrize("delta,expected", [(-1, -1), (0, 0), (1, 0)])
def test_exact_settling_threshold(delta, expected):
    now = START + timedelta(seconds=60, microseconds=delta)
    assert rest.eligible_end(now) == START + expected * rest.STEP
    assert rest.eligible_end(START, 0) == START


def test_catchup_overlap_and_explicit_bounds():
    end = START + timedelta(days=20)
    assert rest.sync_start(end, end - rest.STEP) == end - timedelta(days=7)
    assert rest.sync_start(end, START - rest.STEP) == START
    assert rest.sync_start(end, None, START) == START
    with pytest.raises(ValueError, match="30 days"):
        rest.sync_start(end, end - timedelta(days=31))
    with pytest.raises(ValueError, match="explicit"):
        rest.sync_start(end, None)
    for start in (
        end,
        end - timedelta(days=181),
        START.replace(tzinfo=None),
        START + timedelta(seconds=1),
    ):
        with pytest.raises(ValueError):
            rest.sync_start(end, None, start)


def test_url_exact_milliseconds_and_page_precision():
    from urllib.parse import parse_qs, urlsplit

    url = rest.kline_url("BTCUSDT", START, START + rest.STEP)
    params = parse_qs(urlsplit(url).query)
    assert params == dict(
        symbol=["BTCUSDT"],
        interval=["4h"],
        timeZone=["0"],
        startTime=[str(row()[0])],
        endTime=[str(row()[6])],
        limit=["1000"],
    )
    downloaded = response([row()], url)
    (observation,) = rest.parse_page(
        downloaded, market_id=1, start=START, end=START + rest.STEP
    )
    assert observation.open == Decimal(row()[1])
    assert observation.observed_at == downloaded.observed_at
    assert observation.source_sha256 == downloaded.sha256
    assert observation.source_url == url and observation.source_kind == "rest"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.pop(),
        lambda r: r.append("extra"),
        lambda r: r.__setitem__(6, r[6] + 1),
        lambda r: r.__setitem__(1, 100.0),
        lambda r: r.__setitem__(1, "NaN"),
        lambda r: r.__setitem__(5, "1e9"),
        lambda r: r.__setitem__(8, True),
        lambda r: r.__setitem__(0, r[0] + 1),
        lambda r: r.__setitem__(9, "999"),
    ],
)
def test_strict_rows(mutate):
    value = row()
    mutate(value)
    with pytest.raises(rest.RestError):
        rest.parse_page(
            response([value]), market_id=1, start=START, end=START + rest.STEP
        )


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [row(), row()],
        [row(START + rest.STEP), row()],
        [row(START - rest.STEP)],
        [row(START + 2 * rest.STEP)],
    ],
)
def test_empty_order_nonadvancing_and_current_exclusion(rows):
    with pytest.raises(rest.RestError):
        rest.parse_page(
            response(rows), market_id=1, start=START, end=START + 2 * rest.STEP
        )


def test_malformed_json_and_size():
    from dataclasses import replace

    for body in (b"{", b"null", b"{}", json.dumps([row()] * 1001).encode()):
        with pytest.raises(rest.RestError):
            rest.parse_page(
                replace(response([]), body=body),
                market_id=1,
                start=START,
                end=START + rest.STEP,
            )


class HTTPResponse(io.BytesIO):
    def __init__(self, body=b"[]", status=200, headers=None):
        super().__init__(body)
        self.code = status
        self.headers = headers or {}

    def geturl(self):
        return rest.BASE + "klines"


@pytest.fixture
def network(monkeypatch):
    calls, sleeps, retained, attempts = [], [], [], []
    outcomes = []

    def open_request(request, timeout):
        calls.append((request, timeout))
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(
        rest, "build_opener", lambda *a: SimpleNamespace(open=open_request)
    )
    monkeypatch.setattr(rest.time, "sleep", sleeps.append)

    def fetch():
        return rest.fetch(
            rest.BASE + "klines", retain=retained.append, attempts=attempts
        )

    return SimpleNamespace(
        outcomes=outcomes,
        calls=calls,
        sleeps=sleeps,
        retained=retained,
        attempts=attempts,
        fetch=fetch,
    )


def test_retry_timeouts_then_server_then_success(network):
    network.outcomes.extend([TimeoutError(), HTTPResponse(status=503), HTTPResponse()])
    assert network.fetch().body == b"[]"
    assert len(network.calls) == 3 and network.sleeps == [1, 2, 4]
    assert all(c[1] == 15 for c in network.calls)
    assert len(network.retained) == 2


def test_retry_limit(network):
    network.outcomes.extend([TimeoutError()] * 3)
    with pytest.raises(rest.RestError, match="3 attempts"):
        network.fetch()
    assert len(network.calls) == 3


@pytest.mark.parametrize("status", [429, 418])
def test_throttle_stops_without_retry_and_retains_retry_after(network, status):
    network.outcomes.append(
        HTTPError(
            rest.BASE + "klines",
            status,
            "limited",
            {"Retry-After": "120", "X-MBX-USED-WEIGHT-1M": "6000"},
            io.BytesIO(b'{"code":-1}'),
        )
    )
    with pytest.raises(rest.RestError) as error:
        network.fetch()
    assert error.value.category == "rate_limit"
    assert error.value.details["retry_after"] == "120"
    assert len(network.calls) == 1 and len(network.retained) == 1


@pytest.mark.parametrize(
    "body,headers", [(b"x" * (rest.MAX_BODY + 2), {}), (b"[]", {"Content-Length": "3"})]
)
def test_bounded_and_incomplete_body_retained(network, body, headers):
    network.outcomes.append(HTTPResponse(body, headers=headers))
    with pytest.raises(rest.RestError):
        network.fetch()
    assert len(network.retained[0].body) <= rest.MAX_BODY + 1


def test_clock_skew():
    from dataclasses import replace

    stamp = (START - rest.EPOCH) // rest.MILLISECOND
    r = replace(
        response({"serverTime": stamp}), observed_at=START + timedelta(seconds=1)
    )
    assert rest.check_clock(r, START) == START
    with pytest.raises(rest.RestError, match="tolerance"):
        rest.check_clock(r, START + timedelta(seconds=10))

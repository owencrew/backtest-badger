"""Immutable Stage 4B.1 contracts; no I/O, clocks, or Stage 2/3 imports."""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Context, Decimal, Inexact
from enum import StrEnum
from hashlib import sha256

D = Decimal
STEP = timedelta(hours=4)
INITIAL_CASH = D("10000")
FEE_RATE = D("0.001")
SLIPPAGE = D("0.0002")
FEE_QUANTUM = D("0.00000001")
EXECUTION_POLICY = "stage-4a-execution-v1"
VALUATION_POLICY = "stage-4a-bid-v1"


def money_context(*, division=False):
    """160-digit exact arithmetic; only WAC division rounds at 80 digits."""
    context = Context(prec=80 if division else 160, rounding=ROUND_HALF_EVEN)
    context.traps[Inexact] = not division
    return context


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite_decimal(value):
    require(
        isinstance(value, Decimal) and value.is_finite(), "Expected finite Decimal."
    )
    return value


def number(value):
    finite_decimal(value)
    # Bound work/representation; reject rather than silently round oversized inputs.
    require(
        len(value.as_tuple().digits) <= 160 and -160 <= value.as_tuple().exponent <= 80,
        "Decimal exceeds supported precision.",
    )
    return value


def utc(value):
    require(
        isinstance(value, datetime) and value.utcoffset() == timedelta(0),
        "Expected aware UTC timestamp.",
    )
    return value


def grid(value):
    utc(value)
    require(
        value.hour % 4 == 0 and not (value.minute or value.second or value.microsecond),
        "Expected native four-hour UTC boundary.",
    )
    return value


def identifier(value):
    require(
        isinstance(value, str) and bool(value.strip()), "Expected nonblank identity."
    )


def digest(value):
    require(
        isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None,
        "Expected SHA-256 fingerprint.",
    )


@dataclass(frozen=True)
class Portfolio:
    key: str
    symbol: str
    inception_at: datetime
    config_sha256: str
    protocol_sha256: str
    model_recipe_sha256: str
    venue: str = "binance"
    market_type: str = "spot"
    strategy_id: str = "ridge_sign"
    strategy_version: str = "1"

    def __post_init__(self):
        identifier(self.key)
        utc(self.inception_at)
        require(
            self.symbol in ("BTCUSDT", "ETHUSDT")
            and self.venue == "binance"
            and self.market_type == "spot",
            "Unsupported market.",
        )
        for value in (
            self.config_sha256,
            self.protocol_sha256,
            self.model_recipe_sha256,
        ):
            digest(value)
        identifier(self.strategy_id)
        identifier(self.strategy_version)

    @property
    def base_asset(self):
        return self.symbol.removesuffix("USDT")


@dataclass(frozen=True)
class Forecast:
    """Already verified source; upstream reader owns JSON and automation checks."""

    portfolio: Portfolio
    record_id: str
    source_open: datetime
    issued_at: datetime
    observed_at: datetime
    prediction: Decimal
    file_sha256: str
    content_sha256: str
    model_recipe_sha256: str
    automation_sha256: str | None
    cohort: str = "primary_timely_automated"
    model_id: str = "ridge"
    horizon_seconds: int = 14400

    def __post_init__(self):
        require(isinstance(self.portfolio, Portfolio), "Invalid forecast portfolio.")
        identifier(self.record_id)
        grid(self.source_open)
        utc(self.issued_at)
        utc(self.observed_at)
        finite_decimal(self.prediction)
        for value in (self.file_sha256, self.content_sha256, self.model_recipe_sha256):
            digest(value)
        if self.automation_sha256 is not None:
            digest(self.automation_sha256)
        require(self.issued_at <= self.observed_at, "Forecast clock reversal.")
        require(
            type(self.horizon_seconds) is int and self.horizon_seconds == 14400,
            "Expected four-hour forecast.",
        )
        require(self.model_id == "ridge", "Expected Ridge forecast.")

    @property
    def available_at(self):
        return self.source_open + STEP + timedelta(seconds=60)

    @property
    def deadline(self):
        return self.source_open + STEP + timedelta(minutes=16)


class Action(StrEnum):
    BUY_REQUIRED = "BUY_REQUIRED"
    HOLD = "HOLD"
    CASH_NOOP = "CASH_NOOP"
    EXIT_REQUIRED = "EXIT_REQUIRED"
    IGNORED_EXIT_PENDING = "IGNORED_EXIT_PENDING"
    SIGNAL_STALE = "SIGNAL_STALE"
    SIGNAL_MISSED = "SIGNAL_MISSED"
    SIGNAL_INELIGIBLE = "SIGNAL_INELIGIBLE"
    EXIT_SATISFIED = "EXIT_SATISFIED"
    POSITION_UPDATED = "POSITION_UPDATED"
    ORDER_TERMINAL = "ORDER_TERMINAL"


@dataclass(frozen=True)
class Decision:
    identity: str
    portfolio: Portfolio
    at: datetime
    action: Action
    reason: str
    missed_streak: int
    source_open: datetime | None = None
    forecast: Forecast | None = None
    obligation_id: str | None = None

    def __post_init__(self):
        require(isinstance(self.portfolio, Portfolio), "Invalid decision portfolio.")
        identifier(self.identity)
        utc(self.at)
        require(self.at >= self.portfolio.inception_at, "Decision before inception.")
        require(isinstance(self.action, Action), "Unknown decision action.")
        identifier(self.reason)
        require(
            type(self.missed_streak) is int and self.missed_streak >= 0,
            "Invalid missed streak.",
        )
        if self.source_open is not None:
            grid(self.source_open)
        if self.forecast is not None:
            require(isinstance(self.forecast, Forecast), "Invalid forecast evidence.")
            require(
                self.forecast.portfolio == self.portfolio
                and self.forecast.source_open == self.source_open
                and self.forecast.observed_at <= self.at,
                "Decision evidence mismatch.",
            )
        if self.obligation_id is not None:
            identifier(self.obligation_id)


@dataclass(frozen=True)
class Balances:
    portfolio: Portfolio
    cash: Decimal
    quantity: Decimal
    ledger_seq: int
    at: datetime

    def __post_init__(self):
        require(isinstance(self.portfolio, Portfolio), "Invalid balance portfolio.")
        require(
            number(self.cash) >= 0 and number(self.quantity) >= 0, "Negative balance."
        )
        require(
            type(self.ledger_seq) is int and self.ledger_seq >= 1, "Unfunded snapshot."
        )
        utc(self.at)
        require(self.at >= self.portfolio.inception_at, "Balance before inception.")


@dataclass(frozen=True)
class Quote:
    """Parsed, caller-verified body evidence, never an exchange execution guarantee."""

    identity: str
    run_id: str
    symbol: str
    request_started_at: datetime
    response_received_at: datetime
    bid: Decimal
    ask: Decimal
    bid_quantity: Decimal
    ask_quantity: Decimal
    payload_sha256: str
    raw_body: bytes
    source_url: str
    venue: str = "binance"
    market_type: str = "spot"
    http_status: int = 200
    payload_validated: bool = True
    # Exact duration from a monotonic clock, if available; never binary float.
    elapsed_seconds: Decimal | None = None


@dataclass(frozen=True)
class Filters:
    """Effective intersection of all applicable market-size/notional constraints."""

    symbol: str
    observed_at: datetime
    payload_sha256: str
    step: Decimal
    min_quantity: Decimal
    max_quantity: Decimal
    min_notional: Decimal
    max_notional: Decimal | None
    version: str = "effective-market-filters-v1"
    supported: bool = True
    venue: str = "binance"
    market_type: str = "spot"


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Movement:
    asset: str
    amount: Decimal


@dataclass(frozen=True)
class Trade:
    """Calculated monetary proposal; execution provenance belongs to Fill."""

    identity: str
    portfolio: Portfolio
    side: Side
    at: datetime
    quantity: Decimal
    price: Decimal
    notional: Decimal
    fee: Decimal
    postings: tuple[Movement, Movement]
    ledger_seq_before: int
    policy: str = EXECUTION_POLICY


def validate_quote(quote, portfolio, at):
    utc(at)
    require(isinstance(quote, Quote), "Missing quote.")
    identifier(quote.identity)
    identifier(quote.run_id)
    identifier(quote.source_url)
    digest(quote.payload_sha256)
    require(
        type(quote.raw_body) is bytes and 0 < len(quote.raw_body) <= 4096,
        "Invalid quote payload size (v1 limit: 4096 bytes).",
    )
    require(
        sha256(quote.raw_body).hexdigest() == quote.payload_sha256,
        "Quote payload hash mismatch.",
    )
    prices = {
        "bidPrice": quote.bid,
        "askPrice": quote.ask,
        "bidQty": quote.bid_quantity,
        "askQty": quote.ask_quantity,
    }

    def unique_fields(pairs):
        require(len(pairs) == len(dict(pairs)), "Duplicate quote fields.")
        return dict(pairs)

    try:
        payload = json.loads(quote.raw_body, object_pairs_hook=unique_fields)
        require(
            isinstance(payload, dict)
            and set(payload) == {"symbol", *prices}
            and payload["symbol"] == quote.symbol,
            "Quote payload/parsed fields mismatch.",
        )
        for key, value in prices.items():
            require(
                isinstance(payload[key], str) and D(payload[key]) == value,
                "Quote payload/parsed prices mismatch.",
            )
    except (ArithmeticError, TypeError, UnicodeError, ValueError) as error:
        raise ValueError("Malformed quote payload.") from error
    utc(quote.request_started_at)
    utc(quote.response_received_at)
    require(
        (quote.venue, quote.market_type, quote.symbol)
        == (portfolio.venue, portfolio.market_type, portfolio.symbol),
        "Quote market mismatch.",
    )
    require(
        quote.payload_validated is True
        and type(quote.http_status) is int
        and quote.http_status == 200,
        "Invalid quote payload or HTTP failure.",
    )
    require(0 < number(quote.bid) <= number(quote.ask), "Invalid bid/ask.")
    require(
        number(quote.bid_quantity) >= 0 and number(quote.ask_quantity) >= 0,
        "Invalid displayed quantity.",
    )
    require(
        quote.request_started_at <= quote.response_received_at <= at,
        "Quote clock reversal.",
    )
    require(
        quote.response_received_at - quote.request_started_at <= timedelta(seconds=2)
        and at - quote.response_received_at <= timedelta(seconds=1),
        "Stale quote.",
    )
    if quote.elapsed_seconds is not None:
        require(0 <= number(quote.elapsed_seconds) <= 2, "Invalid monotonic duration.")


def validate_filters(filters, portfolio, at, *, acquired_by):
    utc(at)
    utc(acquired_by)
    require(isinstance(filters, Filters), "Missing filters.")
    utc(filters.observed_at)
    digest(filters.payload_sha256)
    require(
        filters.version == "effective-market-filters-v1" and filters.supported is True,
        "Unsupported filters.",
    )
    require(
        (filters.venue, filters.market_type, filters.symbol)
        == (portfolio.venue, portfolio.market_type, portfolio.symbol),
        "Filter market mismatch.",
    )
    require(
        filters.observed_at <= acquired_by <= at
        and at - filters.observed_at <= timedelta(hours=1),
        "Stale/future filters.",
    )
    require(
        number(filters.step) > 0
        and 0 <= number(filters.min_quantity) <= number(filters.max_quantity)
        and filters.max_quantity >= filters.step
        and number(filters.min_notional) >= 0,
        "Invalid filter limits.",
    )
    if filters.max_notional is not None:
        require(
            number(filters.max_notional) > 0
            and filters.max_notional >= filters.min_notional,
            "Invalid notional bounds.",
        )
    from decimal import localcontext

    with localcontext(money_context()):
        minimum = filters.min_quantity
        remainder = minimum % filters.step
        if remainder:
            minimum += filters.step - remainder
        require(
            max(filters.step, minimum) <= filters.max_quantity,
            "No allowed quantity on the effective step.",
        )


def validate_size(quantity, notional, filters):
    from decimal import localcontext

    with localcontext(money_context()):
        require(
            number(quantity) > 0 and quantity % filters.step == 0,
            "Quantity is zero or off step.",
        )
        require(
            filters.min_quantity <= quantity <= filters.max_quantity,
            "Quantity outside filters.",
        )
        require(
            number(notional) >= filters.min_notional
            and (filters.max_notional is None or notional <= filters.max_notional),
            "Notional outside filters.",
        )


def eligible_forecast(forecast, at):
    """Logical eligibility only; does not duplicate Stage 3's artifact verifier."""
    utc(at)
    require(forecast.observed_at <= at, "Forecast observed after decision.")
    return (
        forecast.available_at <= forecast.issued_at <= forecast.observed_at <= at
        and at < forecast.deadline
        and forecast.issued_at > forecast.portfolio.inception_at
        and forecast.cohort == "primary_timely_automated"
        and forecast.automation_sha256 is not None
        and forecast.model_recipe_sha256 == forecast.portfolio.model_recipe_sha256
    )

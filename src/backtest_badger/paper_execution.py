"""One-shot internal order simulation from supplied prospective evidence only."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import localcontext
from enum import StrEnum

from backtest_badger.paper_accounting import calculate_trade, fee_for
from backtest_badger.paper_types import (
    EXECUTION_POLICY,
    FEE_RATE,
    SLIPPAGE,
    Action,
    Balances,
    D,
    Decision,
    Filters,
    Quote,
    Side,
    Trade,
    eligible_forecast,
    identifier,
    money_context,
    number,
    require,
    utc,
    validate_filters,
    validate_quote,
    validate_size,
)


@dataclass(frozen=True)
class Order:
    identity: str
    decision: Decision
    balances: Balances
    run_id: str
    submitted_at: datetime
    expires_at: datetime
    policy: str = EXECUTION_POLICY

    def __post_init__(self):
        require(
            isinstance(self.decision, Decision) and isinstance(self.balances, Balances),
            "Invalid order decision/balances.",
        )
        identifier(self.identity)
        identifier(self.run_id)
        utc(self.submitted_at)
        utc(self.expires_at)
        require(
            self.decision.portfolio == self.balances.portfolio,
            "Order portfolio mismatch.",
        )
        require(
            self.decision.at <= self.submitted_at
            and self.balances.at <= self.submitted_at
            and self.expires_at == self.submitted_at + timedelta(seconds=30),
            "Invalid order timing/expiry.",
        )
        require(self.policy == EXECUTION_POLICY, "Unsupported execution policy.")
        require(
            self.decision.action in (Action.BUY_REQUIRED, Action.EXIT_REQUIRED),
            "Decision does not authorise an order.",
        )
        if self.side == Side.BUY:
            require(
                self.balances.quantity == 0
                and self.decision.forecast is not None
                and eligible_forecast(self.decision.forecast, self.decision.at)
                and self.submitted_at < self.decision.forecast.deadline,
                "Buy requires flat balance and eligible signal window.",
            )
        else:
            require(
                self.balances.quantity > 0
                and self.decision.obligation_id == self.decision.identity,
                "Sell requires an outstanding exit obligation.",
            )

    @property
    def side(self):
        return Side.BUY if self.decision.action == Action.BUY_REQUIRED else Side.SELL


class Status(StrEnum):
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Reason(StrEnum):
    FILLED = "FILLED"
    ORDER_EXPIRED = "ORDER_EXPIRED"
    SIGNAL_EXPIRED = "SIGNAL_EXPIRED"
    QUOTE_FAILED = "QUOTE_FAILED"
    INVALID_QUOTE = "INVALID_QUOTE"
    INVALID_FILTERS = "INVALID_FILTERS"
    INVALID_SIZE = "INVALID_SIZE"
    INSUFFICIENT_CASH = "INSUFFICIENT_CASH"
    INSUFFICIENT_LIQUIDITY = "INSUFFICIENT_LIQUIDITY"
    EXIT_BLOCKED_DUST = "EXIT_BLOCKED_DUST"


@dataclass(frozen=True)
class Fill:
    order: Order
    quote: Quote
    filters: Filters
    trade: Trade


@dataclass(frozen=True)
class Result:
    order: Order
    at: datetime
    status: Status
    reason: Reason
    fill: Fill | None = None
    quote: Quote | None = None
    filters: Filters | None = None
    run_id: str = ""

    @property
    def postings(self):
        return () if self.fill is None else self.fill.trade.postings


def affordable_quantity(cash, price, step):
    """Maximal step-multiple after fee ceiling; never shrink for depth/filters."""
    require(
        number(cash) >= 0 and number(price) > 0 and number(step) > 0,
        "Invalid sizing inputs.",
    )
    with localcontext(money_context()):
        # Integer ratios avoid rounding a quotient across a lot-step boundary.
        numerator, denominator = cash.as_integer_ratio()
        unit_n, unit_d = (price * step * (1 + FEE_RATE)).as_integer_ratio()
        upper = numerator * unit_d // (denominator * unit_n)
        low, high = 0, upper
        while low < high:
            middle = (low + high + 1) // 2
            notional = D(middle) * step * price
            if notional + fee_for(notional) <= cash:
                low = middle
            else:
                high = middle - 1
        return D(low) * step


def simulate_order(order, quote, filters, fill_at, *, run_id, existing=()):
    """Return one terminal proposal. Explicit prior results detect duplicates.

    Re-evaluating identical inputs without history is deterministic computation,
    not idempotent persistence. Never interpret a proposal as a committed fill.
    """
    require(isinstance(order, Order), "Expected submitted order.")
    require(quote is None or isinstance(quote, Quote), "Expected quote evidence.")
    utc(fill_at)
    identifier(run_id)
    require(fill_at >= order.submitted_at, "Fill clock reversal.")
    require(
        type(existing) is tuple and all(isinstance(r, Result) for r in existing),
        "Invalid existing-result context.",
    )
    for prior in existing:
        require(prior.order.identity != order.identity, "Order already processed.")
        if prior.order.balances.portfolio == order.balances.portfolio:
            require(prior.at <= fill_at, "Reordered execution attempt.")
            require(
                not (
                    order.side == Side.BUY
                    and prior.order.decision.identity == order.decision.identity
                ),
                "Buy decision already attempted; wait for a new forecast.",
            )
        if quote is not None and prior.quote is not None:
            require(prior.quote.identity != quote.identity, "Quote already attempted.")
        if prior.fill is not None:
            require(
                prior.fill.trade.identity != order.identity + ":fill",
                "Fill already used.",
            )

    def reject(reason, status=Status.REJECTED):
        return Result(
            order, fill_at, status, reason, quote=quote, filters=filters, run_id=run_id
        )

    if fill_at >= order.expires_at:
        return reject(Reason.ORDER_EXPIRED, Status.EXPIRED)
    if order.side == Side.BUY and fill_at >= order.decision.forecast.deadline:
        return reject(Reason.SIGNAL_EXPIRED)
    if quote is None:
        return reject(Reason.QUOTE_FAILED)
    try:
        validate_quote(quote, order.balances.portfolio, fill_at)
        require(order.run_id == run_id == quote.run_id, "Quote from another run.")
        require(order.submitted_at <= quote.request_started_at, "Pre-submission quote.")
    except ValueError:
        return reject(Reason.INVALID_QUOTE)
    try:
        validate_filters(
            filters, order.balances.portfolio, fill_at, acquired_by=order.submitted_at
        )
    except ValueError:
        return reject(Reason.INVALID_FILTERS)
    with localcontext(money_context()):
        price = (
            quote.ask * (1 + SLIPPAGE)
            if order.side == Side.BUY
            else quote.bid * (1 - SLIPPAGE)
        )
        quantity = (
            affordable_quantity(order.balances.cash, price, filters.step)
            if order.side == Side.BUY
            else order.balances.quantity
        )
        if quantity == 0:
            return reject(Reason.INSUFFICIENT_CASH)
        try:
            validate_size(quantity, quantity * price, filters)
        except ValueError:
            dust = order.side == Side.SELL and (
                quantity % filters.step != 0
                or quantity < filters.min_quantity
                or quantity * price < filters.min_notional
            )
            return reject(Reason.EXIT_BLOCKED_DUST if dust else Reason.INVALID_SIZE)
        depth = quote.ask_quantity if order.side == Side.BUY else quote.bid_quantity
        if quantity > depth:
            return reject(Reason.INSUFFICIENT_LIQUIDITY)
        try:
            trade = calculate_trade(
                order.balances.portfolio,
                order.identity + ":fill",
                order.side,
                fill_at,
                quantity,
                price,
                ledger_seq_before=order.balances.ledger_seq,
            )
        except ValueError:
            return reject(Reason.INVALID_SIZE)
        require(
            order.balances.cash + trade.postings[0].amount >= 0
            and order.balances.quantity + trade.postings[1].amount >= 0,
            "Insufficient cash/base.",
        )
        return Result(
            order,
            fill_at,
            Status.FILLED,
            Reason.FILLED,
            Fill(order, quote, filters, trade),
            quote,
            filters,
            run_id,
        )

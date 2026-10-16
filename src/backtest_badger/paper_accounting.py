"""Exact paired cash/base proposals and replayable weighted-average accounting."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import ROUND_UP, Inexact, localcontext

from backtest_badger.paper_types import (
    EXECUTION_POLICY,
    FEE_QUANTUM,
    FEE_RATE,
    INITIAL_CASH,
    SLIPPAGE,
    VALUATION_POLICY,
    Balances,
    D,
    Movement,
    Portfolio,
    Quote,
    Side,
    Trade,
    digest,
    grid,
    identifier,
    money_context,
    number,
    require,
    utc,
    validate_filters,
    validate_quote,
    validate_size,
)


def fee_for(notional):
    require(number(notional) > 0, "Notional must be positive.")
    with localcontext(money_context()):
        fee_context = money_context()
        fee_context.traps[Inexact] = False
        return (notional * FEE_RATE).quantize(
            FEE_QUANTUM, rounding=ROUND_UP, context=fee_context
        )


def calculate_trade(
    portfolio, identity, side, at, quantity, price, *, ledger_seq_before
):
    """Monetary arithmetic only; does not assert quote or strategy eligibility."""
    require(isinstance(portfolio, Portfolio), "Invalid trade portfolio.")
    identifier(identity)
    utc(at)
    require(at >= portfolio.inception_at, "Trade before inception.")
    require(isinstance(side, Side), "Invalid side.")
    require(
        type(ledger_seq_before) is int
        and ledger_seq_before >= 1
        and ledger_seq_before % 2 == 1,
        "Invalid funded ledger prefix.",
    )
    require(number(quantity) > 0 and number(price) > 0, "Invalid trade quantity/price.")
    with localcontext(money_context()):
        notional = quantity * price
        fee = fee_for(notional)
        cash = -(notional + fee) if side == Side.BUY else notional - fee
        base = quantity if side == Side.BUY else -quantity
        require(
            cash != 0 and (cash < 0 if side == Side.BUY else cash > 0),
            "Fee consumes sale proceeds.",
        )
        return Trade(
            identity,
            portfolio,
            side,
            at,
            quantity,
            price,
            notional,
            fee,
            (Movement("USDT", cash), Movement(portfolio.base_asset, base)),
            ledger_seq_before,
        )


@dataclass(frozen=True)
class Account:
    portfolio: Portfolio
    cash: D = D(0)
    quantity: D = D(0)
    basis: D = D(0)
    realised: D = D(0)
    fees: D = D(0)
    ledger_seq: int = 0
    at: datetime | None = None
    trade_ids: tuple[str, ...] = ()

    @property
    def balances(self):
        reconcile(self)
        require(self.ledger_seq > 0, "Account is unfunded.")
        return Balances(
            self.portfolio, self.cash, self.quantity, self.ledger_seq, self.at
        )


def reconcile(account):
    """Check aggregates; replay() additionally proves history and fee totals."""
    require(isinstance(account, Account), "Invalid account.")
    for value in (account.cash, account.quantity, account.basis, account.fees):
        require(number(value) >= 0, "Negative account value.")
    number(account.realised)
    require(
        type(account.ledger_seq) is int and account.ledger_seq >= 0,
        "Invalid ledger sequence.",
    )
    require(
        type(account.trade_ids) is tuple
        and len(set(account.trade_ids)) == len(account.trade_ids),
        "Duplicate trades.",
    )
    for identity in account.trade_ids:
        identifier(identity)
    if account.ledger_seq == 0:
        require(
            account.at is None
            and not account.trade_ids
            and all(
                v == 0
                for v in (
                    account.cash,
                    account.quantity,
                    account.basis,
                    account.realised,
                    account.fees,
                )
            ),
            "Unfunded account has financial activity.",
        )
        return
    utc(account.at)
    require(account.at >= account.portfolio.inception_at, "Account clock reversal.")
    require(
        account.ledger_seq == 1 + 2 * len(account.trade_ids),
        "Broken ledger high-water.",
    )
    require(
        (account.quantity == 0) == (account.basis == 0), "Unexplained remaining basis."
    )
    with localcontext(money_context()):
        require(
            account.cash + account.basis - INITIAL_CASH == account.realised,
            "Cash/basis/realised P&L do not reconcile.",
        )


def fund_account(account, at):
    reconcile(account)
    require(account.ledger_seq == 0, "Initial funding already recorded.")
    utc(at)
    require(at == account.portfolio.inception_at, "Funding must match inception.")
    return replace(account, cash=INITIAL_CASH, ledger_seq=1, at=at)


def apply_trade(account, trade):
    """Apply a complete validated monetary pair, once, to one funded account."""
    reconcile(account)
    require(account.ledger_seq > 0, "Unfunded account.")
    require(
        isinstance(trade, Trade) and trade.portfolio == account.portfolio,
        "Trade/account mismatch.",
    )
    require(trade.identity not in account.trade_ids, "Duplicate fill.")
    require(trade.ledger_seq_before == account.ledger_seq, "Reordered ledger prefix.")
    require(trade.at >= account.at, "Reordered trade.")
    number(trade.notional)
    number(trade.fee)
    require(
        type(trade.postings) is tuple and len(trade.postings) == 2,
        "Exactly two immutable postings required.",
    )
    for posting in trade.postings:
        require(isinstance(posting, Movement), "Invalid posting.")
        require(number(posting.amount) != 0, "Zero posting.")
    expected = calculate_trade(
        trade.portfolio,
        trade.identity,
        trade.side,
        trade.at,
        trade.quantity,
        trade.price,
        ledger_seq_before=trade.ledger_seq_before,
    )
    require(
        trade == expected and trade.policy == EXECUTION_POLICY,
        "Invalid fill amounts, signs, policy or paired postings.",
    )
    with localcontext(money_context()):
        cash = account.cash + trade.postings[0].amount
        quantity = account.quantity + trade.postings[1].amount
        require(cash >= 0 and quantity >= 0, "Insufficient cash/base.")
        basis, realised = account.basis, account.realised
        if trade.side == Side.BUY:
            basis += trade.notional + trade.fee
        else:
            require(account.quantity > 0, "No owned base.")
            # Full liquidation releases the exact remaining basis, not Q*(B/Q).
            if quantity == 0:
                released = basis
            else:
                numerator = basis * trade.quantity
                with localcontext(money_context(division=True)):
                    released = numerator / account.quantity
            basis -= released
            realised += trade.notional - trade.fee - released
        result = replace(
            account,
            cash=cash,
            quantity=quantity,
            basis=basis,
            realised=realised,
            fees=account.fees + trade.fee,
            ledger_seq=account.ledger_seq + 2,
            at=trade.at,
            trade_ids=account.trade_ids + (trade.identity,),
        )
    reconcile(result)
    return result


def replay(portfolio, trades):
    """One initial funding followed by caller-ordered synthetic monetary evidence."""
    account = fund_account(Account(portfolio), portfolio.inception_at)
    for trade in trades:
        account = apply_trade(account, trade)
    return account


@dataclass(frozen=True)
class Mark:
    portfolio: Portfolio
    identity: str
    marked_at: datetime
    asof_ledger_seq: int
    quote: Quote | None
    policy_sha256: str
    policy: str = VALUATION_POLICY
    slot: datetime | None = None


@dataclass(frozen=True)
class Valuation:
    mark: Mark
    equity: D | None
    unrealised: D | None
    realised: D
    fees: D
    unavailable_reason: str | None = None


def value_account(account, mark):
    """Value only the supplied historical prefix; invalid prices remain unavailable."""
    reconcile(account)
    require(
        isinstance(mark, Mark) and mark.portfolio == account.portfolio,
        "Mark/account mismatch.",
    )
    identifier(mark.identity)
    utc(mark.marked_at)
    digest(mark.policy_sha256)
    require(mark.policy == VALUATION_POLICY, "Unsupported valuation policy.")
    require(
        type(mark.asof_ledger_seq) is int
        and mark.asof_ledger_seq == account.ledger_seq > 0
        and mark.marked_at >= account.at,
        "Wrong mark ledger prefix/time.",
    )
    if mark.slot is not None:
        utc(mark.slot)
        grid(mark.slot - timedelta(minutes=10))
        if not mark.slot <= mark.marked_at < mark.slot + timedelta(minutes=5):
            return Valuation(
                mark,
                None,
                None,
                account.realised,
                account.fees,
                "Outside mark capture window.",
            )
    try:
        validate_quote(mark.quote, mark.portfolio, mark.marked_at)
        require(
            mark.quote.request_started_at >= mark.portfolio.inception_at,
            "Quote request before portfolio inception.",
        )
        # Receipt is the locally observed quotation time. Equal-time ordering
        # and a transactionally coherent snapshot remain Stage 4C obligations.
        require(
            mark.quote.response_received_at >= account.at,
            "Quote observed before pinned ledger transaction.",
        )
        if mark.slot is not None:
            require(
                mark.slot
                <= mark.quote.request_started_at
                < mark.slot + timedelta(minutes=5),
                "Outside mark capture window.",
            )
    except ValueError as error:
        return Valuation(mark, None, None, account.realised, account.fees, str(error))
    with localcontext(money_context()):
        value = account.quantity * mark.quote.bid
        equity, unrealised = account.cash + value, value - account.basis
        require(
            account.realised + unrealised == equity - INITIAL_CASH,
            "Marked P&L does not reconcile.",
        )
        return Valuation(mark, equity, unrealised, account.realised, account.fees)


def net_liquidation(account, mark, filters):
    """Hypothetical full-sale equity; None when liquidation is undefined."""
    valuation = value_account(account, mark)
    if valuation.equity is None:
        return None
    if account.quantity == 0:
        return account.cash
    try:
        validate_filters(
            filters,
            account.portfolio,
            mark.marked_at,
            acquired_by=mark.quote.request_started_at,
        )
        with localcontext(money_context()):
            price = mark.quote.bid * (1 - SLIPPAGE)
            trade = calculate_trade(
                account.portfolio,
                "hypothetical-liquidation",
                Side.SELL,
                mark.marked_at,
                account.quantity,
                price,
                ledger_seq_before=account.ledger_seq,
            )
            validate_size(trade.quantity, trade.notional, filters)
            require(
                account.quantity <= mark.quote.bid_quantity, "Insufficient bid depth."
            )
            return account.cash + trade.postings[0].amount
    except ValueError:
        return None

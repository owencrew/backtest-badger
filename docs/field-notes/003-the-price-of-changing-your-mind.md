Publication status: Draft

# The Price of Changing Your Mind

- **Date:** 2026-10-24
- **Stage:** 4B.2E.5g — Genuine native-minute historical backtest
- **Topic:** Continuous holdings, turnover and an unsuccessful Ridge strategy

A strategy can hold a position across several forecasts and still change its mind
far too often. In Backtest Badger's genuine 2024 native-minute backtest, the Ridge
strategy bought and sold Bitcoin 570 times each. Its independently funded Ether
account made 499 buys and 499 sells. Both finished with less than half their
starting money.

This experiment asked whether a fixed predictive model could support a simple
long-or-cash policy with continuous holdings and explicit trading costs. Ridge
regression is a linear prediction model whose fitting penalises large
coefficients. Here, its retained forecasts estimate the next four-hour return.
The economic question is separate: what happens when those forecasts drive a
portfolio under a specified execution rule?

## A forecast becomes a position

The run reused the original training-only model recipe and retained validation
forecasts. There was no retraining, new feature, threshold search or forecast
regeneration. Each market supplied 2,195 decisions.

The policy targets a long position when the forecast exceeds the frozen numerical
threshold of `1e-12`; otherwise it targets cash. While already long, another
positive signal means holding the existing position. A cash target means selling.
A later eligible positive signal can buy again after that exit. Bitcoin and Ether
never share capital.

Timing is part of the rule. A completed four-hour candle ending at 12:00 UTC is
assumed usable for a forecast at 12:01. The hypothetical trade uses the strictly
next native one-minute opening, 12:02. That protects the ordering of signal and
execution within the simulation; it does not measure real computation or order
latency, or prove the opening price was available for the required quantity.

Each market has three independent portfolios, funded once with **10,000 USDT**:
Ridge, Cash and Buy & Hold. Cash makes no trades and earns no interest. Buy & Hold
buys once at January 1 00:00 and retains its assets; Ridge's earliest eligible
execution is 00:02. There is no leverage, short selling or forced year-end sale.
The same frozen per-side assumptions apply to purchases and sales: **10 basis
points in fees, 1 basis point of half-spread and 2 basis points of adverse
slippage**. One basis point is 0.01%.

## What the accounts show

The [E.5g research report](../stage-04b2e5g-first-genuine-historical-backtest.md)
records the following results. Monetary values and percentages here are rounded
to two decimal places; returns are relative to initial funding and include costs.

| Market and portfolio | Final marked value (USDT) | Cumulative return |
| --- | ---: | ---: |
| BTCUSDT · Ridge | 3,930.86 | −60.69% |
| BTCUSDT · Cash | 10,000.00 | 0.00% |
| BTCUSDT · Buy & Hold | 22,081.23 | +120.81% |
| ETHUSDT · Ridge | 4,204.39 | −57.96% |
| ETHUSDT · Cash | 10,000.00 | 0.00% |
| ETHUSDT · Buy & Hold | 14,617.58 | +46.18% |

Final values use the December 31 23:00 UTC mark. The final day and December are
partial observations. Both Ridge accounts finish in cash. Buy & Hold values
include unsold assets and do not deduct an invented terminal sale cost.

Ridge underperformed both benchmarks in both markets. Its maximum drawdown at
observed hourly marks was **65.41% for BTC and 65.79% for ETH**. Buy & Hold had
substantial drawdowns too; a higher terminal value did not make it risk-free.

Continuous holding avoided a mandatory exit after every forecast window, yet
position changes remained frequent. Their cost was material:

| Ridge account | Buys / sells | Traded notional (USDT) | Total attributed costs (USDT) |
| --- | ---: | ---: | ---: |
| BTCUSDT | 570 / 570 | 7,640,090.53 | 9,932.12 |
| ETHUSDT | 499 / 499 | 7,107,303.19 | 9,239.49 |

Traded notional sums the value of buys and sells. Reusing capital means it can
reach millions even though each account started with 10,000 USDT. Total costs
combine fees and the hypothetical spread/slippage attribution; the latter are
already embedded in execution prices, not extra cash fees. Each Buy & Hold
account incurred approximately **12.99 USDT** for its single inception purchase.

Costs approaching the original funding do not mean every trade lost money.
Positive trade-price movements offset part of the burden. Nor can we add those
costs back to final equity and call the result a frictionless backtest: different
costs would change affordable quantities and the capital available for later
trades. This run included no zero-cost replay or cost-sensitivity experiment.
The evidence establishes a large cost burden, not the isolated causal contribution
of costs to a hypothetical alternative strategy.

## A different experiment from the hourly study

[Field Note 002](002-when-a-backtest-meets-trading-costs.md) describes Stage 2C's
fixed-window trades: a 12:01 signal entered at 13:00 and exited at 16:00 using
native hourly references. The present policy uses the next minute and can hold
across successive positive signals. Both the timing and the holding convention
changed. Their results are **not a controlled, like-for-like experiment in
execution frequency**. A smaller loss here cannot be attributed to faster
execution alone.

## Useful engineering, unsuccessful trading

All six accounts passed the existing ledger verification, and a separate output
check confirmed the completion marker and file identities. Retained input hashes,
frozen decisions and exact accounting make the result inspectable. A research
pipeline is useful when it reveals that a proposed strategy fails its economic
comparison; profitability is not a software acceptance test.

The result is narrower than a verdict on predictive modelling. This particular
Ridge policy, on these markets and this period, lost heavily under the frozen
assumptions. Understanding why its signals reverse so often is a future research
question, not an explanation established by this run.

The year 2024 had already been inspected. These are exploratory historical
simulations, not untouched out-of-sample validation, prospective paper trading or
real returns. BTC and ETH are correlated, and one year cannot establish future
reliability. Archive openings omit historical order books, quantity-specific
liquidity and market impact. Nothing here proves that predictive models cannot
help, that a different policy would succeed, or that the model should be promoted.
It provides a reproducible negative result worth keeping.

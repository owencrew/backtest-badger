# What Is Backtesting?

- **Date:** 2026-10-25
- **Topic:** Historical simulation and the questions a backtest can answer
- **Publication status:** Draft

A backtest applies a specified decision rule to historical observations and accounts for the resulting hypothetical trades. It asks what that rule would have done under stated assumptions, not what an investor actually earned.

## Start with a rule and a clock

Define what information a strategy can use, when it becomes available and when a hypothetical trade may occur. Using a candle's closing price to make a decision and then trading at an earlier price introduces look-ahead bias: the simulation knows something the trader could not yet know.

Backtest Badger's native-minute study assumes a four-hour candle ending at 12:00 becomes usable at 12:01. The execution reference is the strictly next minute opening, 12:02. That is a modelling convention, not proof that an order could fill there.

## Compare against a meaningful alternative

A strategy's return needs context. Cash and Buy & Hold answer different questions: did taking these decisions improve on holding the initial balance, or on buying the asset once? Each account needs independent initial funding and clearly disclosed cost assumptions.

Fees, bid/ask spread and slippage can change the result substantially. An archive opening price is not a historical order book. Liquidity, latency and market impact remain limitations when they are not measured.

## Keep learning separate from testing

Models and preprocessing should learn from training data only. Validation helps assess choices chronologically; an untouched test period provides a different kind of evidence. Repeatedly trying ideas on the same period can overfit the research process itself, even when the code never reads future data directly.

The year 2024 was already inspected in this project. Its backtest is therefore exploratory, not untouched out-of-sample evidence. A good-looking historical result would still require new evidence before any claim about future performance.

## What is implemented here?

The Dig contains a completed 2024 crypto spot simulation: a frozen Ridge long-or-cash strategy and independently funded Cash and Buy & Hold benchmarks. The website does not execute new backtests. Read [the study](/dig/) and [its methodology](/about/) before interpreting the returns.

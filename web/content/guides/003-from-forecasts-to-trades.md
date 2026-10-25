# From Forecasts to Trades

- **Date:** 2026-10-25
- **Topic:** Why a better prediction is not automatically a better investment
- **Publication status:** Draft

A forecast estimates an outcome. A strategy decides what to do about that estimate. Execution determines whether, when and at what price an order might fill. These are separate steps, and each introduces assumptions.

## A model is not a portfolio

A model might estimate the next four-hour return. Its prediction errors can be compared with simple reference forecasts. Even an improvement in accuracy does not tell us whether a strategy can trade profitably after costs, or whether its actual holding window matches the forecast target.

Backtest Badger's historical Ridge policy targets long when the frozen forecast is above a small numerical threshold, and cash otherwise. This decision rule is a particular implementation; it is not the definition of all machine-learning strategies.

## Historical and prospective evidence

A historical backtest replays a rule against past observations under stated execution assumptions. A genuine forward forecast is recorded before its outcome is known and can later be scored. Forward prediction records do not themselves place orders or establish portfolio returns.

Prospective paper trading would add simulated orders and accounting as new observations arrive. That complete service is planned here. Real trading would place actual orders and risk real capital; it is not implemented.

## Different strategy ideas

Trend following seeks to participate in sustained moves. Momentum uses persistence in past returns as a signal. Mean reversion looks for deviations that may reverse. Buy & Hold makes an initial purchase and retains the asset. These broad descriptions are educational; they do not imply each family is implemented or successful.

The [historical study](/dig/) currently compares Ridge, Cash and Buy & Hold on crypto spot markets. New strategy families, other asset classes and any actual trading require their own carefully scoped work.

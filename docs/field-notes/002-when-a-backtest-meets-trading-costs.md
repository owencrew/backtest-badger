# When a Backtest Meets Trading Costs

- **Date:** 2026-10-14
- **Stage:** 2C — Execution-aware historical backtesting
- **Topic:** Execution timing, transaction costs and strategy viability
- **Publication status:** Published

One of our first simulated trading strategies nearly doubled its starting capital. Then we included trading costs. The same strategy lost almost nine-tenths of it.

Backtest Badger had reached a useful milestone: verified historical market data, causal features, and fixed predictive models evaluated on a chronological validation period. The next question was no longer simply whether a model could predict the next four-hour return. It was whether those predictions could support trades after accounting for *when* a signal becomes available and *what* trading costs.

The initial evidence was modest. During 2024 validation, Ridge regression reduced next-four-hour return RMSE against a training-mean forecast by approximately 0.14% for BTCUSDT and 0.15% for ETHUSDT. ETH's gradient-boosted model improved RMSE by approximately 0.73%, but correctly predicted the direction of only 47.52% of the evaluated returns. Small changes in forecast error did not establish a usable trading advantage.

## A price we could not have traded

Each prediction used a completed four-hour candle and became eligible 60 seconds after that candle closed. For example, a candle ending at 12:00 UTC produced a signal at 12:01. Buying at the 12:00 close would have meant using a price from before the signal was available.

We deliberately adopted a slower, inspectable execution convention: enter using the 13:00 UTC opening price of an independently sourced native one-hour Binance candle, then exit using the 16:00 opening price. The resulting three-hour holding period differs from the four-hour close-to-close return the model predicts. That distinction is part of the experiment, not a detail to hide.

For the 2024 validation year, we independently acquired 24 monthly one-hour archives—12 for BTCUSDT and 12 for ETHUSDT—plus their official checksum files. All 17,568 hourly observations passed the identity and boundary checks, with no missing or rejected hours in this execution dataset.

## The same trades, with and without costs

We fixed one simple long-or-cash rule before viewing results: buy when the forecast was strictly positive above the project's predefined numerical tolerance; otherwise hold cash. Every qualifying trade used the account's affordable cash balance, with no borrowing or short selling. Each model and market started with its own simulated 10,000 USDT account.

Our frictionless diagnostic assumed no fees, spread or slippage. The base scenario assumed, **per side**, a 10-basis-point taker fee, a 1-basis-point half-spread and 2 basis points of slippage. One basis point is 0.01%; the base assumptions therefore cost roughly **26 basis points per completed buy-and-sell round trip** when prices are unchanged. These are explicit illustrative assumptions, not reconstructed historical quotes or fills.

The results for three of the 2024 accounts show the problem:

| Market and predictor | Round trips | Frictionless net return | Base-cost net return |
| --- | ---: | ---: | ---: |
| BTCUSDT · Ridge | 1,083 | +98.53% | −88.12% |
| BTCUSDT · Training mean | 2,195 | +98.74% | −99.34% |
| ETHUSDT · Ridge | 832 | +9.98% | −87.36% |

These percentages are **historical simulations**, not paper-trading or live-account results. The zero-return predictor made no trades and preserved its 10,000 USDT balance. The training-mean predictor was always positive in this experiment and therefore traded every eligible window; its impressive-looking frictionless BTC return did not require sophisticated machine learning.

The BTC Ridge base-cost account makes the accounting concrete. It generated **3,438.97 USDT of gross trading P&L using that scenario's executed quantities**, but incurred **9,423.57 USDT in fees**, **942.36 USDT in spread costs**, and **1,884.71 USDT in slippage**. Net P&L was **−8,811.67 USDT**, leaving approximately **1,188.33 USDT**.

The frictionless account generated **9,852.93 USDT** of profit, but it followed a different compounding capital path: without costs, it retained more cash for later positions. Subtracting the base scenario's costs from the frictionless scenario's gross profit would therefore be an invalid comparison. Each scenario must reconcile its own quantities, cash flows and costs.

## What the result actually tells us

Turnover matters. A seemingly modest cost per trade can dominate a weak forecasting advantage when an account repeatedly buys and sells at full size. It also matters *which* returns are being forecast: improvements on the four-hour research target do not automatically imply improvements on the delayed three-hour trading exposure.

The backtester checked that buy and sell costs were charged in the adverse direction, that quantities were affordable, and that gross P&L minus recorded costs reconciled to each account's net equity change. Two independent runs reproduced the frozen backtest outputs byte for byte. The result was not rescued by changing the signal threshold, retraining the models or choosing a more flattering fee scenario after seeing losses.

There are important limits. Hourly opening prices are historical reference points, not guaranteed executable prices. The simulation does not reconstruct order books, liquidity, market impact, exchange lot-size minimums or the exact spread and fees faced by a trader in 2024. The original data were acquired retrospectively. BTC and ETH share market conditions, and one validation year cannot establish broader performance or statistical significance. The 2025–September 2026 test holdout was not evaluated.

So this experiment does **not** show that all frequent trading is unprofitable, or that these models could never be useful under another carefully specified approach. It shows something narrower and more defensible: **the fixed, high-turnover long/cash policies we tested were economically unviable under our base and stress cost assumptions**. In this case, the backtester was useful precisely because it refused to turn a promising-looking cost-free result into a profitability claim.

The next research step is to examine the integrated methodology and investigate robustness without rewriting this result or repeatedly tuning against the same validation year. Full technical assumptions, scenario tables, accounting reconciliation and artifact hashes are recorded in the [Stage 2C execution-backtesting report](../stage-02c-execution-backtesting.md). The predictive metrics and their limitations are documented in the [Stage 2B baseline report](../stage-02b-predictive-baselines.md).

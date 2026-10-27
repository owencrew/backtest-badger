# Understanding Performance Metrics

- **Date:** 2026-10-25
- **Topic:** Return, risk and the costs hidden behind a headline number
- **Publication status:** Published

A portfolio's final return tells you where it ended. It does not tell you how difficult the journey was, how often the strategy traded or whether the result is likely to repeat.

## Return and drawdown

Cumulative return is the change in portfolio value relative to its initial funding. With no later external cash flows, it is final value divided by initial funding, minus one. It is different from an annualised return, which scales performance to a stated time convention.

Drawdown is a decline from a previous peak. Maximum drawdown reports the largest observed decline. The sampling frequency matters: Backtest Badger's 2024 study uses hourly marks and initial funding, so losses between those marks can remain unobserved. A positive final return does not mean an account avoided deep drawdowns.

## Volatility and Sharpe ratio

Volatility describes variability in returns; it treats upward and downward movements as variation. A Sharpe ratio compares mean excess return with return variability. Its sampling frequency, reference rate and annualisation convention must be disclosed.

The study uses complete UTC daily returns and a zero reference rate. Cash has zero volatility and an undefined Sharpe ratio, not a Sharpe ratio of zero. These are descriptive statistics for the observed period, not guarantees.

## Turnover and transaction costs

Turnover measures trading activity, but definitions differ. Here it is the sum of buy and sell execution notionals divided by original funding. Capital can be recycled many times, so turnover can greatly exceed one.

Fees are explicit charges. Spread is the gap between bid and ask; a half-spread assumption represents one side's disadvantage relative to a reference. Slippage represents further adverse movement between a reference and execution. In this study, spread and slippage are embedded in execution prices. Their reporting attribution must not be deducted a second time.

## Read the metrics together

Start with independent benchmark comparisons, then consider drawdown, costs and the evidence period. A single ratio cannot establish a robust strategy. Explore the [verified account comparison](/dig/) for the project's actual historical findings.

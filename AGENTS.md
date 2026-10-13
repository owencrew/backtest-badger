
# Backtest Badger — Agent Instructions

## Project

Backtest Badger is an open-source quantitative research platform
for market-data engineering, machine learning, backtesting and
paper-trading analytics.

Website: https://backtestbadger.com

The platform starts with cryptocurrency spot markets but should
remain extensible to other asset classes.

## Primary Objectives

1. Demonstrate high-quality Python, SQL, data engineering and ML.
2. Produce reliable, scientifically credible research.
3. Provide an attractive, understandable public dashboard.
4. Investigate economic viability without assuming profitability.

## Engineering Principles

- Prefer simple, readable, maintainable Python.
- Minimise dependencies, abstraction and operational complexity.
- Use plain functions unless classes provide a clear benefit.
- Do not introduce frameworks for hypothetical future requirements.
- Avoid duplicated logic and version-specific implementations.
- Reuse established libraries instead of building unnecessary
  custom infrastructure.
- Implement the smallest complete solution to each requirement.
- Do not expand the scope beyond the requested development stage.

## Scientific Correctness

Never compromise:

- Causal feature generation and prevention of look-ahead bias.
- Chronological training, validation and testing.
- Train-only preprocessing and leakage controls.
- Realistic execution timing and transaction costs.
- Reproducible datasets, models and backtests.
- Honest handling of missing data and provider revisions.
- Separation of backtests, forward predictions and paper trading.

Do not represent simulated performance as real trading results.

## Development Workflow

- Work incrementally, one scoped task at a time.
- Inspect relevant existing code before changing it.
- Write focused tests for important behaviour.
- Run relevant tests and lint checks after changes.
- Report what changed, what was tested and any remaining issues.
- Do not claim tests passed unless they were actually executed.
- Do not commit, push or deploy unless explicitly requested.

## Repository Boundaries

The sibling crypto-trading-platform repository is historical
reference material only.

Never modify its files, database, configuration, artifacts
or deployment.

Do not access production infrastructure unless explicitly
authorised for the specific task.

## Security

- Never commit credentials, API keys or secrets.
- Keep database credentials in environment configuration.
- Use read-only access for public dashboard queries.
- Do not expose database administration functionality publicly.
- Do not implement real-money trading without explicit approval.

## Product Identity

Product: Backtest Badger
Official tagline: A little badger. A lot of backtests.

Main sections:
- The Burrow — dashboard and live analytics
- The Dig — research and backtesting
- Field Notes — experiment history

The design should be playful and approachable while keeping
financial information professional and transparent.

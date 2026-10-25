# Backtest Badger — Stage 5B: Live Market Dashboard and Research Experience

## Objective

Improve the existing Backtest Badger website by making The Burrow useful with genuine Binance market data, preparing a safe connection to existing Lightsail forward predictions, and improving the presentation and explanation of historical research.

Preserve the established charcoal, forest-green and sand identity, mascot artwork, navigation and existing scientific results.

Do not rebuild the frontend from scratch.

## Starting point

Repository: `~/Code/backtest-badger`

Read:

- `AGENTS.md`
- `web/AGENTS.md` if present
- `web/README.md`
- `docs/stage-05a-website-design.md`
- `docs/development-handoff.md`
- `docs/stage-04b2e5g-first-genuine-historical-backtest.md`
- Stage 3A–3D forward-prediction and evaluation documentation
- Current website components and tests

Inspect the Git working tree first. Preserve any uncommitted changes.

Current deployed Lightsail application release is recorded as `cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`. Do not infer it has subsequently changed.

## Part A — The Burrow: real Binance price charts

Implement a professional, interactive BTCUSDT and ETHUSDT market dashboard.

Use genuine Binance Spot public market data, preferably from the documented market-data-only API at:

`https://data-api.binance.vision`

Verify the current official API specification before implementation.

Use a well-supported financial charting library where appropriate. TradingView Lightweight Charts is a strong candidate; check its current API and fulfil its licence/attribution requirements.

### Interface

Include:

- BTC/ETH selector
- Current observed price in USDT
- Historical price chart
- Candlestick/line viewing where practical
- Useful date ranges such as 1D, 7D, 30D and 90D
- Crosshair and price/time tooltips
- Clearly displayed data source: Binance Spot
- Data refresh timestamp
- Automatic refresh approximately every five minutes
- A manual refresh control
- Loading, error and stale-data states

Allow a wider analytical content area than the present narrow editorial column, while retaining excellent mobile layouts.

Choose sensible candle intervals for the selected range.

Validate returned symbols, chronological order, timestamps, numeric values, candle completeness and duplicate timestamps.

Distinguish the current potentially incomplete candle from completed observations.

Display UTC times consistently and make time conventions understandable.

Do not invent or interpolate missing prices.

A failed request must not silently preserve old values with a false "updated" timestamp.

Avoid unnecessary polling when the page is hidden; clean up refresh intervals and pending requests.

Do not require exchange account credentials or introduce trading capabilities.

## Part B — Lightsail forward prediction integration

The existing Lightsail deployment issues real BTCUSDT/ETHUSDT forward predictions and scores outcomes.

We want visitors to see genuine current forecasts and historical prediction accuracy alongside Binance market prices.

This must remain separate from historical backtesting and paper trading.

### Inspect existing evidence contracts

Read the Stage 3A–3D implementation and documentation.

You are authorised to use the existing `ssh Ubuntu-1` connection for **read-only inspection** of the production application's release identity, evidence schema and public-export feasibility.

Request normal approval for SSH/network access if needed.

Do not inspect credentials or print raw private files or sensitive logs.

Do not alter production files, systemd services, database tables, scheduler configuration, firewall rules, IAM policies, DNS or S3 settings.

### Design and implement a minimal public data contract

Create a small versioned JSON contract for deliberately published forward research statistics.

Candidate public fields:

- Market symbol
- Data-source identification
- Source candle close and forecast issuance timestamps
- Target candle closing time
- Forecast model identifier
- Predicted four-hour log return, with an explanatory display conversion if useful
- Outcome pending/scored status
- Realised target return, if verified and mature
- Model-specific forecast errors
- Valid cohort classification
- Matched sample counts and evaluation period
- Export generation time and freshness

Use existing validated evidence and evaluator definitions. Do not create new forecasts or recalculate historical outcomes with different rules.

Preserve timely automated versus late manual cohort distinctions.

Don't publish raw operational journals, sensitive paths, database configuration or private research datasets.

Choose a simple long-term mechanism such as an atomic, periodically refreshed, public-safe static JSON snapshot served separately from the production database.

The website should be able to fetch this JSON without requiring a Next.js server or direct database access.

Do not build an authenticated API, new database, WebSocket service or elaborate cloud infrastructure unless genuinely necessary.

### Local implementation boundary

Implement and test the JSON types, validation, fetching adapter and Burrow presentation locally.

Use explicitly labelled development fixtures for testing. Do not present synthetic fixtures as genuine current forecasts.

If an existing verified, public-safe snapshot can be produced without modifying production, document how it was derived and make its date/status explicit.

If no approved public snapshot exists, keep the website's forecast values unavailable and show a meaningful explanatory state.

Prepare the minimal export/publishing procedure and operational impact assessment for owner review.

**Do not deploy or schedule this exporter on Lightsail in this stage.**

A separate authorised deployment step will connect the actual regularly refreshed forecast feed. Once connected, the frontend should update its forecast display when a new published snapshot becomes available.

Remember that the forecast cycle is four-hourly even though the dashboard polls more frequently.

Do not present predicted log returns as observed market prices or trade recommendations.

## Part C — Improve Field Notes

Currently Field Note 003 is hardcoded as the featured article.

Change the feature selection so the latest eligible article is featured automatically.

For the current local preview, this should be:

**004 — One Minute Can Change a Backtest**

Ensure the featured illustration and labels update consistently with the selected article rather than remaining hardcoded to 003.

The other Field Notes should appear below, newest first.

Preserve the existing publication approval system.

Never expose an unapproved draft in a production static export.

## Part D — Explain Ridge in The Dig

Improve the readability of the existing historical backtest page.

Add a prominent explanation of:

1. What Ridge regression is.
2. Why the model is called Ridge.
3. What it predicts in this implementation.
4. The five historical market features used.
5. How the predicted return becomes a long/cash decision.
6. Why continuous holding does not necessarily imply low turnover.
7. How execution timing and transaction costs influence outcomes.
8. Why this particular result does not establish that all predictive trading fails.

Use clear, concise language and a small visual decision-flow diagram where helpful.

Preserve exact scientific definitions, including the frozen sign threshold and the distinction between completed-candle timestamps, assumed forecast availability and hypothetical minute execution.

Clearly separate Ridge, Cash and Buy & Hold.

Link to the E.5g report and relevant Field Notes.

Add a short glossary or tooltip explanations for drawdown, turnover, basis points, slippage and Sharpe ratio where useful.

Do not change the genuine historical results.

## Part E — Visual improvements

Retain the existing brand.

Increase the prominence and available width of charts on desktop, without making editorial articles excessively wide.

Improve the hierarchy of analytical cards, typography and date/source labels.

Make The Burrow feel like a genuine research dashboard, not a generic placeholder.

Maintain responsiveness, keyboard navigation, contrast, tooltips and reduced-motion support.

Do not add excessive animation or unrelated new components.

## Testing and acceptance

Verify:

- Genuine Binance data loads for both symbols.
- Charts update when market/range selection changes.
- Automatic refresh works without creating repeated intervals.
- Invalid/unavailable market responses have clear states.
- Time boundaries and sorting are correct.
- Forecast JSON validation rejects malformed or inconsistent payloads.
- No fabricated live values appear in the production export.
- Draft-publication protection still works.
- Field Note 004 is featured in development.
- Ridge explanations match the authoritative research methodology.
- Existing historical account figures are unchanged.
- TypeScript, lint, tests and production build pass.
- Desktop and mobile browser checks pass.

Use synthetic data only in clearly identified unit-test fixtures.

Do not run historical backtests, fit predictive models or change scientific source code.

## Documentation

Create:

`docs/stage-05b-market-dashboard.md`

Document the Binance integration, chart design, polling behaviour, data sources, forecast JSON contract, local verification, limitations and exact proposed next step to activate the public feed.

Update `web/README.md` as necessary.

Archive this prompt verbatim at:

`prompts/stage-05-web/003-market-dashboard-and-research-explanations.md`

Update `prompts/README.md`.

## Hard boundaries

- No Git commit or push
- No live website deployment
- No DNS changes
- No production database changes
- No production scheduler or configuration changes
- No public port opening
- No forecast regeneration or rescore
- No new trading strategies in this stage
- No edits to frozen historical evidence
- No automated paper trading or real trading

## Final response

Report the exact frontend changes, which charts are genuinely data-driven, what is working locally, what still needs a public Lightsail feed, the tests performed and the recommended next deployment step.

Provide a Conventional Commit recommendation.

Stop for owner review.
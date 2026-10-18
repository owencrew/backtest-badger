Implement Stage 4B.2D only in the existing backtest-badger repository.
The objective is to implement the previously approved one-minute historical execution methodology using synthetic data only, with independent cash and buy-and-hold benchmarks and a synthetic-only hourly/minute price-parity audit.
Use High reasoning effort. Prioritise correctness, scientific integrity, deterministic results and minimal changes to existing code.
Expected starting HEAD:
0329b12643e9668d9eae1cfedc459ca4d08b0f46
Verify a clean checkout and successful GitHub CI before beginning. If the baseline differs, investigate and report before making changes.
Read:
- AGENTS.md
- docs/stage-04b2c-minute-execution-protocol.md
- docs/stage-04b2c-minute-source-pins.md
- docs/stage-04b2-historical-validation-protocol.md
- docs/stage-04b2b-historical-evaluation-integration.md
- The existing historical replay, evaluation, publication, strategy, execution and accounting modules and their tests.
Frozen one-minute protocol:
historical-minute-execution-v1
SHA-256:
c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b
Frozen minute dataset manifest:
673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127
The existing hourly methodology remains separately frozen and must not be modified.
Important restrictions:
Do not open, list, hash or inspect any genuine artifacts/ data, including the acquired minute dataset, original hourly prices, historical forecasts, Stage 3 evidence or withheld 2025–2026 data.
Do not call existing genuine source loaders, download new archives, query databases or access production.
No genuine historical trading calculations or performance publication are authorised.
All tests and simulations must use explicitly fabricated data.
Create:
src/backtest_badger/paper_minute_historical.py
Use the smallest maintainable implementation and reuse existing shared accounting and strategy functions wherever appropriate.
The existing strategy uses 2,195 Ridge forecasts per market for 2024.
Each forecast is assumed available 60 seconds after the previous four-hour candle closes.
The first hypothetical execution price is the strictly next native one-minute opening.
Examples:
Even if an event occurs exactly at a minute boundary, execution must wait until the next minute.
Preserve the exact Ridge threshold:
prediction > Decimal('1e-12')
Positive forecasts target a long position. All other eligible forecasts target cash.
No future minute prices or candle high/low/close information may influence a trading decision.
The first possible Ridge trade in 2024 is January 1 at 00:02. The last eligible signal is December 31 at 16:01, executable at 16:02.
Do not invent an additional 20:01 signal.
Preserve the approved continuous-holding behaviour:
- BUY when flat and receiving an eligible positive signal.
- HOLD while long and receiving another positive signal.
- SELL the full position on a nonpositive signal.
- CASH_NOOP when flat and receiving a nonpositive signal.
- Permit re-entry after liquidation when a new eligible positive signal arrives.
Implement explicit synthetic missing-signal tests for sticky risk-off exit obligations, including two consecutive misses, discovery timestamps and overlapping later forecasts.
A pending exit must not be cancelled by a subsequent positive forecast.
Missing genuine source evidence must eventually block real evaluation rather than generating invented outage histories.
Use the existing shared accounting primitives, including:
fund_account, calculate_trade, apply_trade, replay, reconcile and affordable_quantity.
Apply exactly the frozen costs:
- Fee: 10 basis points per side.
- Hypothetical half-spread: 1 basis point.
- Adverse slippage: 2 basis points.
- Quantity step: 0.000001.
- Initial account capital: 10,000 USDT.
Buy price = minute opening × 1.0003.
Sell price = minute opening × 0.9997.
Preserve exact Decimal arithmetic, fee rounding, funding and signed ledger postings.
Do not deduct spread or slippage twice.
Do not create artificial trades when the portfolio is already in its target position.
Do not liquidate holdings automatically at year-end.
Use explicit one-minute reference types.
Do not represent native one-minute openings as though they came from the old native one-hour archive.
Preserve the distinct identities of:
- One-minute price-source observations.
- One-minute hypothetical executions.
- Hourly portfolio valuations sourced from minute openings.
- Existing native-hourly historical evaluations.
- Prospective paper trading.
No real quote or fillability claims are permitted.
The complete frozen minute dataset contains 1,054,080 observations, but the strategy generates only one forecast every four hours.
Design the replay to consume supplied synthetic prices at required execution times and hourly valuation times.
Do not create a million portfolio snapshots.
The full dataset integrity requirement belongs to the separately verified upstream minute-data source; a projected set of execution/mark prices must not be presented as independent full-source authentication.
Support deterministic short synthetic fixtures and complete full-year synthetic grids.
Full-year mode must validate exactly 2,195 forecasts and 8,784 hourly valuations per market.
Reject missing, duplicate, reordered, incorrectly timed or misidentified evidence.
Each market must support three independent 10,000-USDT accounts:
1. Ridge strategy.
2. Static cash.
3. Buy-and-hold.
Cash never trades.
Buy-and-hold purchases the maximum fee-affordable quantity at January 1, 2024, 00:00 using the native one-minute opening and the same costs and quantity step.
It holds until year-end without a forced sale.
If the initial purchase is mathematically infeasible, report the benchmark unavailable without substituting another price.
All three accounts must maintain separate balances, trade histories, ledgers and valuations.
Do not directly reuse hourly evaluation helpers where they assume every trade occurs at an hourly opening. Create minimal minute-aware equivalents where necessary.
Retain hourly marks at each HH:00 UTC.
Use native one-minute HH:00 opening prices rather than the old separately sourced hourly prices.
Each market requires 8,784 marks in full-year mode.
The final mark is December 31, 2024, 23:00.
At an hourly timestamp, an already scheduled execution occurs before the portfolio mark. A decision discovered at that timestamp cannot use the same opening.
Each mark must reconcile its actual ledger prefix, cash, asset quantity, cost basis, realised and unrealised profit or loss, and total equity.
Exposure durations use actual minute-level entry and exit times.
Do not manufacture a January 2025 valuation.
Any reported maximum drawdown is based on hourly observations, not an invented continuous minute-by-minute equity curve.
Create:
src/backtest_badger/minute_price_parity.py
This must be a pure, offline, supplied-input module.
Its purpose is to compare two separately sourced, explicitly supplied price-reference grids:
- Native hourly opening prices.
- Native minute opening prices sampled at HH:00.
In full-year mode, verify all 17,568 market/hour identities across BTCUSDT and ETHUSDT.
Compare prices using exact Decimal equality.
There must be no tolerance, interpolation, source substitution or silent correction.
Retain a deterministic report containing matched identities, counts, missing observations, extra or duplicated observations, and every exact price discrepancy.
A mismatch must set:
direct_timing_comparison_permitted = False
Distinguish the two legitimate source identities; they should not be expected to have identical source hashes, only exactly matching prices and timestamps. Invalid or tampered provenance must fail validation.
Include synthetic tests in which one or more minute opening prices differ from the hourly prices.
Do not run the auditor on the genuine acquired minute dataset or original hourly archive.
That real parity audit requires separate owner authorisation.
Create focused tests, including:
tests/test_paper_minute_historical.py
tests/test_minute_price_parity.py
Cover:
- Correct strictly-next-minute execution, including exact boundaries.
- Continuous holding without unnecessary trading.
- BUY, HOLD, SELL, CASH_NOOP and re-entry.
- Sticky risk-off exits and synthetic missing signals.
- Fee-aware affordability and exact Decimal accounting.
- Complete sale and correct position balances.
- Independent cash and buy-and-hold accounts.
- Correct inception buy-and-hold treatment.
- Hourly mark reconciliation after minute-level executions.
- Missing, duplicated, reordered and malformed references.
- Full-year synthetic coverage and leap-year boundaries.
- Deterministic repeated execution and scientific serialization.
- Exact-price parity success and discrepancies.
- No look-ahead bias or implicit later-price substitution.
- Rejection of unsupported intervals or mismatched source identities.
- Preservation of old hourly functionality.
Tests must explicitly prevent network access, databases, source loaders and genuine artifact reads.
Avoid quadratic serialization and excessive memory use.
Create:
docs/stage-04b2d-minute-replay-engine.md
Document the APIs, event ordering, causal timing, financial reconciliation, benchmarks, data contracts, limitations and future genuine-data integration gates.
Archive this substantive prompt at:
prompts/stage-04-paper/006-minute-replay-and-parity-audit.md
Update architecture, roadmap and development handoff narrowly.
Do not modify existing frozen protocols, previously approved scientific source modules, old tests or the source-pin metadata.
Run focused tests, the locked full suite where applicable, Ruff lint and formatting, and Git whitespace checks.
Clearly report PostgreSQL tests skipped locally; do not claim CI passed unless CI actually ran.
Return:
- Starting and final Git revisions.
- All changed files.
- Focused and total test results.
- Preserved frozen protocol/source hashes.
- New API signatures.
- Explanation of deterministic execution and ledger reconciliation.
- Any assumptions or limitations.
- Outstanding requirements for genuine parity auditing and historical evaluation.
Do not commit, push, deploy, execute real historical data or proceed to another development stage.
Stop after Stage 4B.2D synthetic implementation and await review and approval.
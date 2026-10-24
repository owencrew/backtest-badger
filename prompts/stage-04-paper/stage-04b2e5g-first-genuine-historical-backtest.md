# Backtest Badger — Stage 4B.2E.5g: First Genuine 2024 Historical Backtest

## Objective

Execute, verify and analyse the first genuine 2024 native-minute historical backtest using the existing E.5e local runner and the four authenticated publication artifacts that passed E.5f preflight.

This is a major research milestone for Backtest Badger.

**Prioritise simplicity, scientific correctness, reproducibility and a useful final analysis.**

Do not build another execution framework or introduce unnecessary infrastructure.

## Starting state

- E.5e implementation commit: `c39f572c046253b196c12b476c9170d71b0468bb`
- E.5e CI run: `40084535405`, completed successfully
- E.5f: Genuine four-file preflight PASSED, exit status 0
- Existing Python environment: CPython 3.12.13
- All four genuine historical inputs matched their retained SHA-256 and byte-length pins
- Independent sign-off, publication associations and frozen methodology passed validation
- No genuine economic backtest has yet been executed

Read `AGENTS.md` first, followed by the E.5e runner guide, E.5f preflight record and relevant source code.

Confirm the current HEAD and working-tree state.

If E.5f has been committed after the E.5e baseline, confirm that its commit changes documentation only and that the E.5e scientific/runner implementation is unchanged.

## Explicit owner authorisation

**By submitting this prompt, I explicitly authorise ONE local genuine 2024 historical economic backtest using the previously authenticated publication and the existing reviewed E.5e runner.**

This authorisation includes:

- Read-only access to the four original publication artifacts already identified and validated in E.5f
- Repeating the existing preflight
- Running the genuine economic replay once
- Writing the resulting research outputs to the specified local artifacts directory
- Reading and analysing the completed results
- Creating a concise, non-sensitive research report in the repository

It does not authorise changing the methodology, modifying original evidence, accessing production, publishing to the website, or performing real-money trading.

Do not execute the backtest more than once without further authorisation.

## Step 1 — Confirm readiness

Verify:

1. The exact reviewed local runner and scientific code are unchanged.
2. The four existing authenticated publication artifacts are available at the same confirmed paths established in E.5f.
3. The Python environment and dependencies are available.
4. The output parent is on the local filesystem and is not inside a tracked Git directory.
5. There is sufficient available disk space and memory for the expected full-year replay.

Use the existing E.5f record and narrowly scoped local lookups. Do not scan unrelated private directories or print original artifact contents.

Use this output parent:

`artifacts/paper-historical/stage-04b2e5e-local-runs/`

This directory is Git-ignored.

## Step 2 — Repeat the genuine preflight

Invoke the unchanged existing CLI:

```bash
.venv/bin/python -m backtest_badger.local_historical_backtest preflight \
  --manifest "$MANIFEST" \
  --authenticated-inputs "$AUTHENTICATED_INPUTS" \
  --integrity "$INTEGRITY" \
  --signoff "$SIGNOFF"
```

Use the actual, previously confirmed local paths.

If preflight fails, stop immediately. Do not change pins, substitute sources, regenerate data or attempt economic replay.

## Step 3 — Execute the genuine historical backtest

If readiness and preflight both pass, execute **exactly one** genuine run using the existing implementation:

```bash
OUTPUT_PARENT="$PWD/artifacts/paper-historical/stage-04b2e5e-local-runs"

.venv/bin/python -m backtest_badger.local_historical_backtest run --execute \
  --manifest "$MANIFEST" \
  --authenticated-inputs "$AUTHENTICATED_INPUTS" \
  --integrity "$INTEGRITY" \
  --signoff "$SIGNOFF" \
  --output-dir "$OUTPUT_PARENT"
```

Do not change the frozen strategy, forecasts, timestamps, accounting, transaction costs, benchmarks or any scientific assumptions.

The six intended accounts are:

- BTCUSDT — Ridge, Cash, Buy & Hold
- ETHUSDT — Ridge, Cash, Buy & Hold

All accounts retain the approved independent 10,000 USDT initial funding.

If execution fails or produces an incomplete result, preserve the diagnostic evidence and stop. Do not automatically retry or modify scientific code.

## Step 4 — Verify completed results

If the run succeeds:

1. Capture the exact run directory printed by the CLI.
2. Execute `verify-output` against that directory.
3. Confirm the completion marker and hashes of every expected output file.
4. Confirm six distinct accounts with their actual availability statuses.
5. Check that all available account ledgers passed verification.
6. Confirm BTC and ETH remain independent portfolios.
7. Confirm the input pins, protocol and frozen methodology match the approved declarations.

Do not manually edit generated results.

Do not publish or commit the detailed private evidence.

## Step 5 — Analyse the economic results

Read the completed `summary.json` and `summary.md`.

Produce a clear analysis for each market comparing Ridge against Cash and Buy & Hold.

Where available, present:

- Starting and final marked portfolio values
- Cumulative return
- Annualised descriptive return
- Maximum observed-hourly drawdown
- Annualised volatility
- Descriptive Sharpe ratio
- Number of buys and sells
- Turnover and total transaction costs
- Final cash and asset holdings
- Daily and monthly performance patterns
- Differences between Ridge and Buy & Hold
- Material differences in economic performance between BTC and ETH

Use the exact computed numbers. Do not invent values, replace unavailable metrics with zero or add unsupported assumptions.

Explain the economic significance of the findings, including whether the strategy outperformed its benchmarks after costs.

Be willing to conclude that the strategy performs poorly or shows no trading edge. Negative results are valuable research outcomes.

## Step 6 — Research interpretation

Discuss what the evidence actually supports.

In particular:

- The effect of trading costs and turnover
- Whether Ridge outperformed simply holding the underlying asset
- Whether the cash benchmark was preferable
- The importance of execution assumptions
- The limitations of using an already-inspected 2024 exploratory sample
- The distinction between historical simulations and prospective performance

Never describe these as live trading profits, proven alpha, or untouched out-of-sample results.

Do not introduce new parameter tuning or strategy variations during this stage.

## Step 7 — Documentation and prompt archive

Archive this complete original prompt verbatim at:

`prompts/stage-04-paper/stage-04b2e5g-first-genuine-historical-backtest.md`

Update `prompts/README.md` as appropriate.

Create a concise research report:

`docs/stage-04b2e5g-first-genuine-historical-backtest.md`

The report should include:

- Exact implementation commit and execution environment
- Input and methodology identities, without private paths
- Preflight and output-verification results
- Six-account performance comparison
- Meaningful findings and limitations
- Location of the retained private local results, described without exposing sensitive absolute paths
- Any unresolved issues or follow-up research questions

If execution fails, record the failure instead of manufacturing a results report.

Do not edit the frozen scientific documents or previous archived prompts.

Do not perform a broad repository documentation cleanup yet.

## Boundaries

- One genuine economic execution maximum
- No automatic retry
- No parameter tuning or model retraining
- No new historical data acquisition
- No forecast regeneration
- No scientific contract changes
- No network or AWS Lightsail access
- No database modification
- No website publication
- No real-money trading
- No commit, push or deployment

Avoid rerunning expensive synthetic test suites when no implementation changes have been made.

## Final response

State **GENUINE BACKTEST COMPLETED**, **BACKTEST FAILED**, or **BLOCKED**.

If completed, show a readable performance comparison of all six accounts with exact reported values, followed by the most important research conclusions.

Include:

1. Preflight result
2. Actual execution and completion status
3. Exact run directory and output verification status
4. Six-account results
5. Economic interpretation
6. Important limitations
7. Files changed
8. Confirmation that this prompt was archived
9. Recommended Conventional Commit message

Do not claim success unless the run and output verification actually completed.

**The priority is to complete and understand this first genuine backtest, not to develop additional infrastructure.**
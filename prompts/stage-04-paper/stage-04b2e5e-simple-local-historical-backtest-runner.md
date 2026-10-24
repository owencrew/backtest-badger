# Backtest Badger — Stage 4B.2E.5e: Simple Local Genuine Historical Backtest Runner

## Objective

Implement the simplest reliable, maintainable local execution path for the first genuine 2024 BTCUSDT and ETHUSDT native-minute historical backtest.

This is a **personal quantitative research and portfolio project**, intended to showcase high-quality Python, data engineering, machine learning, backtesting and software design.

Prioritise **minimum complexity, maximum scientific correctness**.

## Starting point

- Repository: `backtest-badger`
- Expected baseline HEAD: `9ba227f6213e235885d7331e4dd8aa729a5bc0b5`
- GitHub Actions run `40046950460` completed successfully, including all three E.5/E.5c/E.5d guarded suites.
- Read `AGENTS.md` first, then inspect the exact relevant implementation, scientific contracts, tests and stage documentation before editing.
- Confirm the actual checkout and report any differences from this baseline.

## Explicit owner decision: simplified threat model

The owner has authorised a change in engineering approach.

This project runs locally under the control of its developer. We are **not defending against a malicious developer or compromised local process**.

Therefore, do not require:

- Separate privileged supervisor and worker identities
- Administrative installation or protected macOS runtime trees
- App Sandbox, mandatory access control or custom kernel-level enforcement
- Separate custody principals or protected signing services
- Anti-rollback, irreversible one-shot consumption or artificial restrictions on repeating a legitimate research experiment
- Comprehensive runtime/OS attestation

The E.5d fabricated implementation and original review records can remain as historical development evidence. They are **not prerequisites for the new local runner**.

Document this owner-approved change clearly in one concise new decision record. Do not retrospectively rewrite historical evidence or alter frozen scientific methodology.

We still require normal application safety, integrity checks and explicit operator consent before a genuine run.

## Scientific requirements — unchanged

Preserve the existing approved historical methodology exactly:

- 2024 BTCUSDT and ETHUSDT Binance Spot observations
- Frozen Ridge Sign strategy and model/forecast inputs
- Causal forecast availability
- Approved next-native-minute execution timing
- Existing fee, half-spread, slippage and quantity-step assumptions
- Three independent 10,000 USDT accounts per market: Ridge, Cash and Buy & Hold
- Continuous holdings, no forced terminal liquidation
- Existing Decimal accounting and full ledger verification
- Explicit treatment of unavailable accounts or incomplete evidence
- Honest research classification: previously inspected exploratory 2024 history, not untouched out-of-sample performance or live trading

Do not refit models, regenerate forecasts, modify thresholds, revise assumptions or rerun source acquisition/authentication.

## Implementation

Build a small, understandable local runner, preferably a single orchestration module with a thin CLI.

**Reuse existing scientific code. Do not build another strategy engine, ledger, reporting engine or complex orchestration framework.**

Inspect and reuse the applicable functions in:

- `genuine_minute_publication.py`
- `paper_minute_historical.py`
- `paper_minute_reporting.py`
- `genuine_backtest_reporting_integration.py`
- `genuine_backtest_preparation.py`

Important: the existing E.5c integration is explicitly fabricated-only. Do not simply remove its fabricated checks or relabel synthetic results as genuine. Extract or reuse common scientific operations safely where appropriate, and preserve the old test contracts.

### Inputs

The runner should accept explicit local paths for the four existing genuine publication artifacts: manifest, authenticated inputs, integrity and independent sign-off.

Before any economic calculation:

1. Verify the expected file sizes and SHA-256 hashes against the retained independently established historical pins.
2. Validate the existing publication structure, evidence associations and independent sign-off using the established implementation.
3. Confirm the frozen execution protocol and expected 2024 market/account identities.
4. Reject missing, malformed, inconsistent or substituted inputs with clear errors.

Do not read original historical files in this development task. Do not guess their locations.

### Execution

Provide a clear local command with separate validation/preflight and explicit execution modes.

Keep the interface simple. No signatures, elaborate approval JSON, role impersonation or OS installation.

The eventual genuine run must require an explicit operator action, but **do not invoke that action in this task**.

Repeated research runs may be supported, provided outputs are versioned and cannot silently overwrite or be mistaken for previous runs.

### Outputs

Produce useful, human-readable results suitable for eventual website presentation, including:

- Strategy, market, period and methodology identity
- Cumulative and annualised returns where meaningful
- Drawdown, volatility and risk-adjusted measures where well-defined
- Trade counts, turnover, transaction costs and end-of-period holdings
- Ridge comparisons against Cash and Buy & Hold
- Daily/monthly return series where supported
- Verified account and ledger identities
- Exact input identities, execution version, timestamps and research limitations

Use the existing reporting functions wherever possible. Do not invent unsupported statistics or silently convert unavailable metrics to zero.

Separate a concise presentation-friendly summary from detailed private research evidence. Never publish original model, source or signing artifacts unnecessarily.

Write results to a clearly specified local output directory, using unique run identifiers, complete-file writes and a final completion marker so incomplete executions are unmistakable.

### Testing

Use fabricated fixtures only.

Cover successful full-path replay, the six account results, input tampering, wrong hashes, missing files, invalid sign-off, changed method assumptions, report/ledger inconsistency, incomplete output and overwrite prevention.

Ensure output is deterministic apart from explicitly recorded run metadata.

Retain existing fabricated tests and established public gates unless a specific, documented change is essential. No security theatre or redundant defensive frameworks.

Run focused tests, Ruff and relevant regression tests. Report exact results; do not claim unexecuted suites passed.

Avoid expanding CI with another expensive redundant full-year suite unless it adds material coverage. Prefer a small number of strong integration tests.

## Documentation and prompt archive

Create a concise E.5e implementation guide and update the current development handoff.

Explicitly distinguish:

- Historical E.5d security-heavy design
- Owner-approved simplified E.5e local execution model
- What is implemented and genuinely tested
- What remains unexecuted
- Exact manual procedure needed for the first authorised genuine run

Do not broadly refactor or consolidate repository documentation yet; that is a separate upcoming stage.

**Important — archive this Codex prompt in the repository.**

Save a complete, verbatim Markdown copy of this request to:

`prompts/stage-04-paper/stage-04b2e5e-simple-local-historical-backtest-runner.md`

Requirements:

1. Preserve the full original prompt, including all instructions and acceptance criteria. Do not summarise or rewrite it.
2. Use the existing `prompts/stage-04-paper/` directory and follow its established naming conventions.
3. If useful, update `prompts/README.md` to reference the new archived prompt, following the existing structure.
4. Treat the archived prompt as a development history record. Do not modify earlier archived prompts.
5. Include the archived prompt in the final changed-file summary.

For future stages, continue this convention of archiving each original Codex development request under the appropriate `prompts/` subdirectory.

## Hard boundaries for this task

**This task authorises implementation and fabricated-data testing only.**

Do not:

- Read genuine historical publication files, original datasets or private keys
- Execute the genuine 2024 economic backtest
- Change frozen scientific contracts
- Access AWS Lightsail or production databases
- Make network requests or deploy a website
- Commit, push or deploy without separate owner authorisation

If a genuine-only integration issue cannot be resolved without inspecting original evidence, document the precise blocker rather than inventing a result.

## Final response

Report:

1. Architecture and implementation changes
2. Tests actually run, with pass/fail counts
3. Files changed and any scientific contracts affected
4. Remaining genuine-run blockers
5. Exact proposed local preflight and genuine execution commands, clearly marked **NOT EXECUTED**
6. Confirmation that the complete prompt was archived at the required path
7. Recommended Conventional Commit message

Keep the solution focused, readable and as small as practical.
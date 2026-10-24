# Backtest Badger — Stage 4B.2E.5h: Research Narrative and Documentation Reconciliation

## Objective

Make the Backtest Badger repository coherent, current and compelling to technical peers, hiring managers and future website visitors.

The first genuine 2024 native-minute historical backtest is now complete. The Ridge strategy lost approximately 60.69% on BTCUSDT and 57.96% on ETHUSDT, substantially underperforming Cash and Buy & Hold.

These are negative but valuable results. Communicate them accurately and explain what they demonstrate about quantitative research and software engineering.

**Focus on clarity, quality and simplicity. This is documentation work, not new research or infrastructure development.**

## Starting point

Read `AGENTS.md` first.

Then inspect:

- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- `docs/stage-04b2e5g-first-genuine-historical-backtest.md`
- `docs/stage-04b2e5e-local-execution-decision.md`
- `docs/deployment/production-infrastructure.md`
- `docs/field-notes/README.md`
- Existing Field Notes 001 and 002
- Current relevant source code and Git history where needed

Confirm the latest reviewed commit and successful CI. Preserve uncommitted changes.

## Task 1 — Reconcile high-level documentation

Update the README, architecture, roadmap and development handoff so they accurately describe the current project.

In particular:

- Record the completed genuine 2024 historical backtest.
- Explain the distinction between historical research, live forward predictions, prospective paper trading and real trading.
- Clearly identify implemented capabilities versus planned product features.
- Correct stale references to earlier development stages.
- Ensure the current Lightsail infrastructure status is represented consistently with the existing production runbook, without claiming that the latest research code is deployed.
- Explain the simplified local execution approach and why the earlier E.5d security-heavy implementation is no longer an operational prerequisite.
- Identify the next product milestone: a polished public website.

Preserve detailed historical stage documentation and original research evidence. Do not rewrite historical claims to make the project appear more advanced.

Keep the main README concise and attractive. Link to technical documentation rather than duplicating it.

## Task 2 — Field Note 003: The genuine backtest

Create a new Field Note focused on the actual 2024 native-minute research findings.

Suggested title:

**The Price of Changing Your Mind**

Focus on:

- Why the strategy was tested
- The causal signal and execution assumptions
- Independent Ridge, Cash and Buy & Hold portfolios
- Ridge's frequent position changes
- The actual 2024 results and transaction-cost burden
- Why a successful research pipeline can reveal an unsuccessful trading strategy
- What this does and does not establish about predictive models

Importantly, distinguish this experiment from the earlier Stage 2C hourly execution study. The trading policies and holding conventions differ, so their results must not be presented as a controlled like-for-like execution-frequency experiment.

Read Field Note 002 before writing. Avoid duplicating its discussion of earlier trading costs.

Use only verified figures from the E.5g research report.

## Task 3 — Field Note 004: Research data integrity

Create a second technical Field Note about native-minute market-data verification and the importance of causal execution timing.

Suggested title:

**One Minute Can Change a Backtest**

Explain:

- Why the price used for execution must occur after the signal becomes available
- The difference between four-hour forecast candles, hourly reference data and native-minute execution data
- The documented 12:01 signal availability and 12:02 execution convention
- The earlier exact-price parity audit of 17,568 hourly/minute pairs
- Why source authentication, timing checks and immutable evidence matter
- What these checks do not establish about actual market fillability

Verify the exact claims against the relevant Stage 4B.2C/D technical documentation. Do not infer findings or present previous verification as new testing.

## Editorial standards

Both articles must:

- Follow `docs/field-notes/README.md` conventions
- Start with `Publication status: Draft`
- Be readable by technically curious non-specialists
- Include concrete, verified examples
- Avoid exaggerated claims of profitability, accuracy or causality
- Distinguish findings, hypotheses and limitations
- Be suitable for future presentation on backtestbadger.com
- Exclude private input paths, credentials and private research evidence

Update the Field Notes index to include both entries.

## Task 4 — Future website handoff

Add a short, practical section to the development handoff explaining what the public website can now use:

- Verified research summaries and statistics
- Historical strategy-versus-benchmark comparisons
- Existing prospective forecast/outcome evidence
- Field Notes articles
- Clear methodology and limitations

Separate this from the paper-trading features that remain unimplemented.

Do not select a website framework, create frontend code or modify AWS in this stage.

## Prompt archive

Archive this complete prompt verbatim at:

`prompts/stage-04-paper/stage-04b2e5h-research-narrative-documentation.md`

Update `prompts/README.md` where appropriate.

Do not alter earlier archived prompts.

## Boundaries

- No further economic backtest execution
- No modifications to the frozen research methodology
- No parameter tuning or model retraining
- No reading private historical evidence unnecessarily
- No source-code refactoring
- No database or AWS changes
- No website implementation yet
- No commit, push or deployment

This should be a focused documentation reconciliation, not a comprehensive rewrite of every project document.

## Validation and final response

Check Markdown links, numerical consistency with the E.5g report, Git diff and whitespace.

Report:

1. Documents updated and why
2. Any previously inconsistent claims corrected
3. Both Field Notes and their verified evidence
4. Remaining documentation gaps
5. Recommended next product-development stage
6. Exact files changed
7. Recommended Conventional Commit message

Do not commit or push. Return the work for review.
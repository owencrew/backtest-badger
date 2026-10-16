# Backtest Badger — Stage 4B.1: Valuation Timing Corrections

Act as a senior Python engineer reviewing the completed Stage 4B.1 deterministic paper-trading primitives.

The existing implementation is pushed to GitHub. Before Stage 4B.2 begins, address two narrowly identified temporal-integrity gaps in portfolio valuation.

## 1. Inspect before modifying

Read `AGENTS.md`, the approved Stage 4A technical specification and prospective evaluation protocol, `paper_accounting.py`, `paper_strategy.py`, `paper_types.py`, the current Stage 4B.1 implementation guide and existing synthetic tests.

Verify the current Git commit before making changes.

## 2. Prevent mixed-time valuation snapshots

Ensure a valuation cannot use a quotation observed before a financial transaction included in its pinned ledger sequence.

Preserve the current exact `Decimal` valuation and ledger-replay behaviour.

Explicitly document that full transactional snapshot consistency and equal-timestamp event ordering remain Stage 4C persistence responsibilities.

Add focused synthetic tests proving that pre-trade quotations cannot value post-trade holdings.

## 3. Enforce valuation capture boundaries

Ensure the portfolio's initial quote request does not precede its actual inception.

For scheduled valuation slots, require quotation capture to begin within the approved five-minute window, not merely assign a mark timestamp within that window.

Reject invalid evidence or return an unavailable valuation as appropriate to the existing API contract. Never silently replace invalid quotes or reconstruct past marks.

Add tests for exact window boundaries, before-window requests, stale quotes and valid inception observations.

## 4. Preserve all existing functionality

Do not modify Ridge strategy rules, fees, slippage, accounting equations, portfolio balances, sticky exit obligations, trading filters or successful order behaviour.

Do not introduce PostgreSQL migrations, historical backtesting, network access, workers or production changes.

Do not modify approved Stage 4A protocol documents as part of this task. Report any documentation inconsistencies separately.

## 5. Tests and documentation

Run the full existing synthetic test suite, Ruff lint and formatting checks.

Update the Stage 4B.1 implementation guide with the clarified valuation timing contract.

Archive this exact substantive prompt at:

`prompts/stage-04-paper/002-valuation-timing-corrections.md`

Follow existing prompt-archive conventions.

## 6. Completion report

Report the exact changes, new regression tests, results of the complete test suite, and any unresolved limitation.

Do not commit, push, deploy or begin Stage 4B.2.

Stop after this correctness correction.

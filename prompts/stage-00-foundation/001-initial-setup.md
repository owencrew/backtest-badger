# Backtest Badger — Stage 0: Minimal Project Foundation

You are acting as a senior Python software engineer and quantitative research architect.

We are building **Backtest Badger**, an open-source quantitative research platform.

- **Tagline:** Digging for Alpha.
- **Website:** https://backtestbadger.com
- **GitHub:** https://github.com/owencrew/backtest-badger
- **Local repository:** `~/Code/backtest-badger`
- **Development:** macOS
- **Future deployment:** AWS Lightsail (Ubuntu)

The repository already exists and is connected to GitHub.

Your task is to implement **Stage 0 only: a minimal, maintainable project foundation**.

Do not implement quantitative research functionality, market ingestion or the website yet.

## 1. Engineering principles

The previous crypto research project accumulated excessive operational complexity, duplicated code and version-specific infrastructure.

Backtest Badger must take a deliberately different approach.

Our overriding principle is:

**Minimum complexity. Maximum correctness.**

- Prefer readable Python and straightforward functions.
- Minimise dependencies and unnecessary abstractions.
- Do not build infrastructure for hypothetical requirements.
- Avoid generic repository/service/interface patterns unless clearly justified.
- Reuse established libraries rather than implementing unnecessary frameworks.
- Make changes incrementally.
- Keep the system easy for one developer to maintain.
- Preserve rigorous scientific correctness as quantitative functionality is introduced.

Do not expand the requested scope.

## 2. Repository boundaries

The original project is located at:

`~/Code/crypto-trading-platform`

It is a historical reference containing valuable backtesting and ML implementations.

For Stage 0:

- Do not access or modify the original repository.
- Do not copy existing project code.
- Do not access its databases, credentials or AWS deployment.
- All implementation changes must remain inside `backtest-badger`.

Do not commit, push or deploy anything without explicit approval.

## 3. Python foundation

Set up:

- Python 3.12
- uv for dependency management
- Conventional `src/backtest_badger/` package
- `pyproject.toml` and committed `uv.lock`
- Basic environment-based configuration
- Structured or standard Python logging, whichever is simpler
- pytest
- Ruff

Use only dependencies needed for Stage 0.

Do not install pandas, NumPy, scikit-learn, CCXT, Streamlit or Plotly yet unless there is a concrete Stage 0 requirement.

Create a minimal CLI with:

- `badger health` — verifies basic application configuration.
- `badger db-health` — checks PostgreSQL connectivity.

Both commands should report concise, useful errors and appropriate exit codes without exposing secrets.

## 4. Local database environment

Configure Docker Compose to run PostgreSQL locally.

Requirements:

- Use a supported PostgreSQL version.
- Local development only.
- Persist database data in a named Docker volume.
- Bind the database port to localhost.
- Use development-only environment credentials.
- Provide `.env.example`.
- Ensure `.env` and secrets are gitignored.
- Demonstrate a successful database health check.

Use SQLAlchemy for straightforward database connectivity if appropriate.

Do not create application tables or placeholder migrations yet.

Introduce Alembic during Stage 1, when the first real database schema is defined.

Do not add unnecessary database abstractions.

## 5. AGENTS.md

An initial agent-instructions document already exists in the repository.

Inspect it before making changes.

Preserve its useful existing instructions.

Maintain it as the concise, authoritative set of coding-agent guidelines covering:

- Project purpose.
- Engineering simplicity.
- Scientific correctness.
- Security.
- Testing and development conventions.
- Repository boundaries.
- Incremental development.
- Restrictions on production access and deployment.

Update it only when enduring engineering conventions change.

Do not turn it into a development diary or duplicate the roadmap.

## 6. Prompts directory

Maintain a `prompts/` directory containing a chronological record of prompts supplied to Codex.

This Stage 0 prompt should be preserved at:

`prompts/stage-00-foundation/001-initial-setup.md`

Do not overwrite or paraphrase the original prompt.

Create `prompts/README.md` briefly explaining:

- The purpose of the prompt archive.
- Stage-based organisation.
- Chronological naming conventions.
- How subsequent Codex prompts should be recorded.
- The requirement to review prompts for sensitive information before committing.

Do not store complete conversation transcripts or Codex outputs automatically.

Do not treat archived prompts as authoritative specifications when they conflict with the current code or project documentation.

## 7. License

Add a standard MIT `LICENSE` file.

Use:

Copyright (c) 2026 Owen Crew

The license applies to the new project's code. Do not assume third-party code or assets can automatically be relicensed.

Mention the MIT license in the README.

## 8. Documentation

Create three concise documents.

### README.md

A professional GitHub README describing:

- What Backtest Badger is.
- Its purpose and engineering philosophy.
- Current implementation status.
- Planned quantitative research functionality.
- Local installation and setup.
- How to start PostgreSQL.
- How to run health checks.
- How to run tests.
- License and roadmap links.

Do not claim functionality exists before it has been implemented.

### docs/architecture.md

Document the actual Stage 0 architecture and the intended future direction.

Explain why we use Python, PostgreSQL, uv and a simple modular package.

Clearly distinguish implemented components from planned functionality.

Keep the document concise.

### docs/roadmap.md

Define the development roadmap:

- Stage 0 — Foundation.
- Stage 1 — Market Data Engine.
- Stage 2 — Quantitative Research, ML and Backtesting.
- Stage 3 — Live Predictions.
- Stage 4 — Paper Trading and Performance.
- Stage 5 — Polished Website and Public Launch.
- Stage 6 — Research and Asset-Class Expansion.

Include simple acceptance criteria for each stage.

Mark Stage 0 as in progress until its completion criteria have been verified.

Do not create unnecessary additional documentation.

## 9. Testing and CI

Write a small pytest suite covering meaningful Stage 0 behaviour.

Include appropriate tests for:

- Configuration handling.
- CLI behaviour.
- Database connection failures.
- Application initialisation where relevant.

Do not write trivial tests solely to increase test counts.

Create a GitHub Actions workflow that:

- Installs dependencies using uv and the committed lockfile.
- Runs Ruff.
- Runs pytest.
- Requires no production secrets.

Keep the workflow straightforward.

Do not introduce deployment automation yet.

## 10. Explicit exclusions

Do not implement:

- Market-data ingestion.
- Historical data downloading.
- Feature engineering.
- ML models.
- Trading strategies.
- Backtesting.
- Paper trading.
- Live prediction scheduling.
- Website or dashboard interfaces.
- Badger mascot or other visual assets.
- AWS deployment.
- Domain configuration.
- Real-money trading functionality.
- Additional infrastructure beyond what Stage 0 requires.

Do not create empty packages for future features.

Do not create complicated database schemas or state machines.

## 11. Final validation and report

Once implementation is complete:

1. Run the applicable tests and lint checks.
2. Verify that the package installs correctly.
3. Verify that the CLI health command works.
4. Verify local PostgreSQL connectivity if Docker is available.
5. Check the Git working tree and inspect the files changed.
6. Review the implementation for unnecessary complexity.
7. Correct straightforward issues discovered during validation.

Report:

- Files created or modified.
- Final project structure.
- Key architectural decisions.
- Actual test results.
- Commands needed to run the project locally.
- Any unresolved issues.
- Anything deliberately deferred to Stage 1.

Do not claim tests passed unless they were executed.

Do not commit or push changes.

**Stop after Stage 0.**

The goal is to establish the smallest reliable foundation for Backtest Badger, not to begin implementing the quantitative platform prematurely.
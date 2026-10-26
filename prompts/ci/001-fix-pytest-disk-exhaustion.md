# Backtest Badger — Fix GitHub Actions CI Disk Exhaustion

## Objective

Restore consistently green GitHub Actions CI without weakening scientific tests, disabling verification or changing production behaviour.

The latest two commits failed:

- `ef4d29162524f18357ec1bd7e54522e6bcc9bce9`
- `9cf942ba977ee8e0d02c9170e36c2f54a0b392e5`

Their GitHub Actions runs were:

- `40191098358`
- `40216243848`

The previous deployment documentation commit `c6d2a1704c620c3136bda13b65f8c1e0dc546bfd` passed.

## Confirmed investigation findings

Both failed runs:

- Successfully installed dependencies.
- Passed Ruff lint and formatting.
- Failed during `uv run --locked pytest`.
- Collected 3,134 Python tests.
- Reported widespread `OSError: [Errno 122] Disk quota exceeded` exceptions while writing pytest temporary files under `/tmp/pytest-of-runner/`.
- Subsequently reported numerous secondary failures involving missing files, assertions and fixture setup.
- Skipped the guarded E.5/E.5c/E.5d tests because the main pytest step failed.

The existing scientific Python tests were not modified in either website commit.

This strongly suggests a CI temporary-storage exhaustion problem, not a demonstrated regression in the website.

However, do not assume every reported failure is secondary without verification.

## Instructions

Read `AGENTS.md`, `.github/workflows/ci.yml`, `pyproject.toml` and relevant test fixtures.

Start with a clean working-tree check.

### 1. Diagnose storage usage

Inspect the actual CI logs and determine which tests and fixtures consume substantial temporary storage.

Pay particular attention to:

- Pytest's default temporary-directory retention
- Large synthetic minute-data archives
- Fabricated full-year replay fixtures
- Module/session-scoped fixture directories
- PostgreSQL test resources
- Temporary files left after successful tests
- Available disk space and filesystem/inode limits on GitHub-hosted runners

Add lightweight storage diagnostics to CI if useful, including disk availability before and after the Python suite.

Do not assume that unrelated assertion failures are genuine until they are retested without storage exhaustion.

### 2. Implement the smallest reliable fix

Prefer an environment/CI configuration solution rather than modifying frozen scientific code.

First consider reducing pytest temporary-directory retention, for example with the supported pytest setting:

`tmp_path_retention_policy=none`

Verify that this does not break tests relying on fixture lifetime.

If that is insufficient, consider dividing the existing tests into logical groups running with separate temporary directories or isolated GitHub Actions jobs.

Preserve PostgreSQL integration testing and required environment configuration.

Ensure every existing test is still executed and the guarded integration checks remain mandatory.

Do not simply skip large tests or declare them optional.

Keep execution reasonably efficient and avoid unnecessary new CI complexity.

### 3. Verification

Run appropriate local checks.

Verify that the proposed workflow is syntactically correct.

Run the full feasible Python suite, ideally using a Linux environment representative of GitHub Actions.

If tests pass locally but CI capacity remains unverified, state that clearly.

After the owner approves and pushes the change, GitHub Actions must confirm whether the fix succeeds.

Do not report success solely because a smaller subset passes.

### 4. Boundaries

- Do not change frozen research evidence.
- Do not modify trading strategies or modelling logic.
- Do not disable any scientific assertions.
- Do not remove tests from the required suite.
- Do not use paid GitHub runner resources.
- Do not deploy the website.
- Do not access or modify Lightsail.
- Do not change AWS or production databases.
- Do not commit or push.

### 5. Documentation

Create a concise report:

`docs/ci-disk-exhaustion-fix.md`

Explain the root cause, changes, limitations and how the fix was validated.

Archive this prompt verbatim:

`prompts/ci/001-fix-pytest-disk-exhaustion.md`

Update `prompts/README.md` if appropriate.

### Final response

Report:

1. Confirmed root cause or remaining uncertainty
2. Tests/fixtures responsible for the largest storage consumption
3. Exact changes made to CI
4. Whether all 3,134 Python tests remain included
5. Status of the guarded E.5 checks
6. Local validation results
7. Any remaining need for a GitHub-hosted verification run
8. Recommended Conventional Commit message

Stop for owner review.

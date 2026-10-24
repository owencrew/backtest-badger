**Backtest Badger — Stage 4B.2E.5f: First Genuine 2024 Input Preflight**

**Objective**

Prepare and perform the first **read-only preflight of the existing authenticated 2024 historical publication** using the committed E.5e local runner.

This is a personal quantitative research project. Prioritise simplicity, scientific correctness and rapid progress towards the first real historical backtest.

**Do not execute the economic backtest in this task.**

**Baseline**

- Repository: backtest-badger
- Expected commit: c39f572c046253b196c12b476c9170d71b0468bb
- GitHub Actions run 40084535405: completed successfully
- Stage E.5e runner: src/backtest_badger/local_historical_backtest.py

Read the exact root AGENTS.md first. Confirm HEAD and working-tree status. Do not reset or discard changes.

**Authorised access**

By submitting this request, I authorise **read-only access to the four existing genuine historical publication artifacts solely for E.5e preflight**:

1. Publication manifest
2. Authenticated inputs
3. Integrity document
4. Independent publication sign-off

This does not authorise economic execution, reading raw minute ZIP/CSV archives, accessing private signing keys, re-running source authentication, modifying original evidence or accessing production systems.

**Task**

**1. Locate the existing artifacts**

Use the existing documentation, prior operator guides and known publication output conventions to identify the four retained files.

Search narrowly within documented research/output locations on the local Mac. Do not scan unrelated personal directories, credentials, other repositories or cloud infrastructure.

Do not regenerate, substitute or repin any file.

If the files cannot be located with confidence, stop and explain precisely what locations need to be supplied. Do not invent paths or create replacements.

**2. Verify the environment**

Confirm:

- Clean, reviewed Git checkout
- Python 3.12 and existing project dependencies
- Expected E.5e local runner present
- Retained historical pin declarations unchanged

Do not install new dependencies or modify code unnecessarily.

**3. Run genuine preflight**

If all four original paths are established, invoke the existing CLI:

.venv/bin/python -m backtest_badger.local_historical_backtest preflight \\

  --manifest "$MANIFEST" \\

  --authenticated-inputs "$AUTHENTICATED_INPUTS" \\

  --integrity "$INTEGRITY" \\

  --signoff "$SIGNOFF"

Use actual confirmed local paths through the variables.

The preflight must verify the existing pinned byte identities, publication associations and independent sign-off.

This step must **not** call run --execute or perform economic replay.

On failure, capture the error and identify the smallest likely cause. Do not bypass validation, change pins or repair historical evidence automatically.

**4. Report readiness**

If preflight passes, report:

- Commit and Python environment
- Confirmation that all four artifacts were located
- Whether each pinned identity matched
- Whether publication and independent sign-off validation passed
- Exact preflight command and exit status
- Any remaining blockers before economic execution
- Proposed output parent for the first run, without creating results yet

Do not print original publication contents, confidential source records, private paths or secrets in the report.

**5. Save this prompt**

Archive a complete, verbatim copy of this request at:

prompts/stage-04-paper/stage-04b2e5f-genuine-historical-preflight.md

Preserve all instructions. Do not alter previous archived prompts.

If preflight actually runs, create a concise, non-sensitive result record at:

docs/stage-04b2e5f-genuine-preflight.md

Update prompts/README.md if consistent with established practice.

Do not make unrelated documentation changes.

**Hard boundaries**

- No genuine economic backtest yet
- No model fitting, forecasts or source regeneration
- No new execution architecture
- No changes to frozen scientific modules
- No network, AWS, database or production access
- No commit, push or deployment

Do not rerun expensive fabricated suites unless a code change makes that necessary. The reviewed E.5e CI baseline is already green.

**Final response**

Clearly state **PREFLIGHT PASSED**, **PREFLIGHT FAILED**, or **BLOCKED — FILES NOT LOCATED**.

Summarise actual checks, blockers and any changed files. Provide the exact proposed genuine run --execute command, clearly labelled **NOT EXECUTED**.

Recommend a Conventional Commit message for any documentation changes.

Stop after reporting. The first genuine economic backtest requires my next explicit authorisation.

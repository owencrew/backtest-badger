# Stage 4B.2E.5f — first genuine historical input preflight

2026-10-24, Europe/London. **PREFLIGHT PASSED**, exit status **0**.
No economic replay was performed.

The exact root `AGENTS.md` was the first file read. HEAD matched the requested
reviewed baseline `c39f572c046253b196c12b476c9170d71b0468bb`; the starting working
tree was clean. GitHub Actions run `40084535405` was reported successful by the
owner and was not queried (no network access).

The existing `.venv/bin/python` is CPython **3.12.13**. The installed project
dependencies imported successfully; Alembic 1.20.0, cryptography 46.0.7,
NumPy 2.5.4, psycopg/psycopg-binary 3.3.6 and scikit-learn 1.9.1 match `uv.lock`.
Installed pytest 9.1.1 and Ruff 0.17.0 also match the lockfile. The E.5e runner
resolves to this checkout. Source, historical pin declarations, the retained
run-contract declarations, `pyproject.toml` and `uv.lock` match the baseline.
No dependencies were installed and no code was changed.

The exact retained locations were established from the prior E.2 operator
request and publication conventions. All four files were found directly, as
regular files with no symlink path components; no directory inventory or broader
personal-directory search was needed. Private absolute paths are omitted here.

| Original artifact | Pinned bytes | Size and SHA-256 result |
| --- | ---: | --- |
| Publication manifest | 560 | Matched |
| Authenticated inputs | 15,272,413 | Matched |
| Integrity document | 74,200 | Matched |
| Independent publication sign-off | 2,020 | Matched |

The unchanged runner checked all four identities against `HISTORICAL_PINS`
before parsing. Frozen methodology checks, publication associations and the
independent sign-off contract/publication reconciliation all passed. This
reconciles retained evidence; it does not rerun original source authentication.

Exact preflight invocation, with the four variables set to confirmed absolute
local paths in the invoking shell (values deliberately omitted):

```sh
.venv/bin/python -m backtest_badger.local_historical_backtest preflight \
  --manifest "$MANIFEST" \
  --authenticated-inputs "$AUTHENTICATED_INPUTS" \
  --integrity "$INTEGRITY" \
  --signoff "$SIGNOFF"
```

Exit status: **0**. CLI output:

```text
Preflight passed: four retained pins, publication and sign-off; no economic replay performed.
```

No input compatibility blocker was detected by preflight. The first economic run
still requires the owner's next explicit authorisation and agreement on the
output destination. Proposed output parent, relative to the repository:
`artifacts/paper-historical/stage-04b2e5e-local-runs/`. It was not created or
tested for output writes. The runner will create a fresh run directory and repeat
preflight on execution; economic replay and output lifecycle compatibility with
these genuine inputs remain untested.

Proposed command — **NOT EXECUTED**. Re-establish the four confirmed input
variables in the future shell without publishing their private values:

```sh
OUTPUT_PARENT="$PWD/artifacts/paper-historical/stage-04b2e5e-local-runs"
.venv/bin/python -m backtest_badger.local_historical_backtest run --execute \
  --manifest "$MANIFEST" \
  --authenticated-inputs "$AUTHENTICATED_INPUTS" \
  --integrity "$INTEGRITY" \
  --signoff "$SIGNOFF" \
  --output-dir "$OUTPUT_PARENT"
```

Original evidence was read only and not copied, repaired, regenerated or repinned.
No raw minute ZIP/CSV archives, private signing keys, unrelated repositories,
network, AWS, databases or production systems were accessed. No model fitting,
forecast generation, economic execution, commit, push or deployment occurred.
Expensive fabricated suites were not rerun because no code changed.

Validation: `git diff --check`, `.venv/bin/ruff check . --no-cache` and
`.venv/bin/ruff format --check . --no-cache` passed (220 Python files already
formatted). Final source/dependency/run-contract comparison with the baseline
passed. No pytest suite was executed.

The complete request is archived at
[`stage-04b2e5f-genuine-historical-preflight.md`](../prompts/stage-04-paper/stage-04b2e5f-genuine-historical-preflight.md).
Only this result record, that new prompt archive and `prompts/README.md` changed.

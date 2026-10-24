# Stage 4B.2E.5e — simple local historical backtest runner

2026-10-24, Europe/London. Implementation and fabricated testing only.
Starting checkout was clean at the exact requested baseline
`9ba227f6213e235885d7331e4dd8aa729a5bc0b5`. The owner supplied the successful
GitHub Actions run `40046950460`; it was not queried here. No network requests,
production access, original evidence reads, model fitting, forecast generation,
source authentication reruns or genuine economic replay were performed.

## Local architecture

`backtest_badger.local_historical_backtest` is a single orchestration module
with an argparse CLI (`python -m ...`). The [owner-approved execution decision](stage-04b2e5e-local-execution-decision.md)
supersedes E.5d's installation/custody prerequisites for this local route.
Historical records and all frozen scientific modules remain unchanged.

`preflight` reads only the four explicitly supplied local files. It checks all
four sizes and SHA-256s against `genuine_backtest_preparation.HISTORICAL_PINS`
before parsing, uses `_parse_verified_publication`, and reconciles the independently
pinned sign-off with `_validate_independent_signoff`. These validators enforce
publication associations, forecast/reference grids, model lineage, fixed timing,
market identities and original historical evidence claims. Runtime checks also
reject changed protocol, period, funding, quantity step, fees, Decimal precision
and the frozen method declaration. There is no pin, model or method override.

`run --execute` requires explicit consent before opening inputs. It repeats
preflight and uses the retained bytes for `_replay_verified_publication`, which
calls the established planner and monetary core. It checks the two markets and
six ordered, independently funded accounts. Reporting retains each verified
account fingerprint before calling `minute_reporting_summary`, reconciles native
performance and account state, and exports `minute_ledger_records` identities.

The E.5c fabricated integration was inspected for its handoff and reconciliation
pattern. It is neither invoked nor weakened: this runner uses the common E.5b
reporting and publication APIs directly. Same-process fingerprints detect ordinary
inconsistency; they do not establish an independent custody principal. The old
`replay_genuine_minute_historical` and `run_genuine_historical_operator` gates
still refuse. Only the new explicitly consenting local route can execute.

## Output and interpretation

An explicit output parent receives a fresh UTC-timestamp/UUID directory, created
exclusively with mode 0700. Failed directories are retained and never resumed or
overwritten. Repeating an experiment creates a new run. Files are staged, flushed,
fsynced and atomically hard-linked into place without replacement. All output
identities are retained before writing and checked on readback before completion.
Use a local filesystem supporting same-directory hard links.

| File | Purpose |
| --- | --- |
| `run.json` | Run ID, UTC start, explicit consent, four exact input identities, execution version, Python version and hashes of loaded project sources (including uncommitted code), frozen protocol/method and limitations |
| `summary.md` | Human-readable six-account returns, observed-hourly drawdown, trade counts and limitations |
| `summary.json` | Exact presentation-oriented metrics, holdings, costs, turnover, account/ledger identities and Ridge-minus-benchmark return differences |
| `private/evidence.json` | Replay decisions, fills, hourly marks, signed ledger postings, complete reporting records and daily/monthly return/cost series |
| `COMPLETE.json` | Written last: completion time and exact identities of all four files above |

Only a directory passing `verify-output` should be consumed. Missing/malformed
completion, missing files or hash disagreement means incomplete/unusable output.
This is local integrity checking, not signed certification or a power-loss-proof
storage system. Source hashes are reproducibility metadata, not comprehensive
runtime/OS attestation. Retain the reviewed checkout and dependency lock with the
run. Do not publish the private evidence or original inputs automatically. No
original publication, model, approval, sign-off or signing material is copied.

Existing reporting supplies funding-relative cumulative return, exact costs and
turnover, observed-hourly drawdown, exposure, final holdings and complete-day
statistics. Daily/monthly series retain partial endpoints. Unavailable accounts
keep their reasons and `null` performance; they are never replaced with zero.
The six-account count includes an unavailable B&H account if inception is infeasible.

Supplemental **descriptive** statistics use Decimal's existing 80-digit division
context and the verified report, without changing the frozen reporting schema.
Daily returns are summed first in the existing 160-digit exact context, avoiding
spurious variance for repeated long Decimal values:

- Annualised funding return: `(last_equity / 10000) ** (365 * 86400 / elapsed_seconds) - 1`,
  where elapsed time ends at the last observed mark, not the unobserved 2025 boundary.
  Nonpositive equity or elapsed time produces `null` with a reason.
- Daily sample volatility uses only complete UTC daily mark returns, denominator
  `n - 1`; annualised volatility is that standard deviation times `sqrt(365)`.
- Descriptive zero-rate Sharpe is `mean_daily / sample_std_daily * sqrt(365)`.
  Fewer than two days or zero variance makes Sharpe undefined (`null` and reason).
  Cash volatility is legitimately zero; its Sharpe is undefined.

The 365-day scaling is a stated descriptive convention, not an inference of
independent returns or a profitability claim. Daily mark returns exclude B&H's
already-charged inception cost; funding-relative returns/drawdown include it.
There are 365 complete days, a partial December 31 and a partial December; no
2025 valuation or terminal sale is invented. BTC and ETH remain separate.

## Manual first-run procedure — NOT EXECUTED

1. Review this change and its fabricated test results. Obtain separate owner
   authorisation for access to the four genuine files and the first genuine run.
   E.5e implementation approval alone is not that authorisation.
2. Use the reviewed Python 3.12 environment. Set the five variables below to
   owner-confirmed absolute paths. Their values are deliberately not supplied or
   discovered by this development task. The first four paths refer to existing
   retained files; `OUTPUT_PARENT` is a local destination for fresh run directories.
3. Run preflight. It reads the publication/sign-off only and performs no economic
   replay. Stop on any mismatch; do not repin, regenerate inputs or loosen checks.

```sh
# NOT EXECUTED. Set these only after separate owner authorisation.
MANIFEST='/absolute/owner-confirmed/manifest.json'
AUTHENTICATED_INPUTS='/absolute/owner-confirmed/authenticated_inputs.json'
INTEGRITY='/absolute/owner-confirmed/integrity.json'
SIGNOFF='/absolute/owner-confirmed/independent-signoff.json'
OUTPUT_PARENT='/absolute/owner-selected/local-results'

.venv/bin/python -m backtest_badger.local_historical_backtest preflight \
  --manifest "$MANIFEST" --authenticated-inputs "$AUTHENTICATED_INPUTS" \
  --integrity "$INTEGRITY" --signoff "$SIGNOFF"
```

4. Review the successful preflight, destination and approved revision. The explicit
   operator action below performs the economic replay and produces local results.
   No approval signature, service installation or E.5d rehearsal is needed.

```sh
# NOT EXECUTED: genuine economic execution; separate owner authorisation required.
.venv/bin/python -m backtest_badger.local_historical_backtest run --execute \
  --manifest "$MANIFEST" --authenticated-inputs "$AUTHENTICATED_INPUTS" \
  --integrity "$INTEGRITY" --signoff "$SIGNOFF" --output-dir "$OUTPUT_PARENT"

# NOT EXECUTED: use the exact run directory printed by the successful command.
.venv/bin/python -m backtest_badger.local_historical_backtest verify-output \
  --run-dir '/absolute/output-parent/exact-printed-run-id'
```

5. Review all six accounts, unavailable reasons, holdings, comparisons and research
   limitations. Retain all attempts, including failures. Website presentation is
   a later, separately authorised activity. Never label the result untouched OOS,
   actual trading, or prospective paper trading.

Genuine-only compatibility remains **unverified** because the original bytes were
not opened. No particular genuine-only defect was observed; successful fabricated
replay cannot prove real-byte compatibility or performance. If preflight rejects
the pinned publication/sign-off, retain the exact error and request a scoped
investigation. Do not invent a successful result or rerun source authentication.

## Validation record

The new tests use invented publication bytes with test-only monkeypatches of the
retained pins, temporary local files and blocked acquisition/network/database calls.
No production pin override is exposed. Two full-path full-year fabricated replays
exercise the real parser, sign-off, both monetary cores, all six ledger verifiers
and reports. Summaries and detailed evidence must be byte-identical across runs;
only run metadata/completion differ. Small lifecycle tests isolate failed writes,
readback corruption, missing completion, tampering and overwrite prevention.
Existing E.5/E.5c/E.5d guarded launchers and CI configuration remain unchanged.

Executed locally with installed dependencies; no dependency fetch or CI run:

| Command | Result |
| --- | --- |
| `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_local_historical_backtest.py` | **43 passed**, zero failures/skips, 45.74 seconds on final run |
| `.venv/bin/python -I -S -B tests/run_e5_guarded.py` | **87 passed**, zero failures/skips, 35.516 seconds |
| `.venv/bin/python -I -S -B tests/run_e5c_guarded.py --regressions` | **603 passed**, zero failures/skips, 569.32 seconds; includes all 55 mandatory E.5c cases |
| `.venv/bin/python -I -S -B tests/run_e5d_guarded.py` | **153 passed**, zero failures/skips, 737.66 seconds |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | Passed, 218 files |
| `git diff --check` and prompt `cmp` against the supplied attachment | Passed; verbatim archive confirmed |

The initial new-suite run had 41 passes and one test-call failure (the legacy
gate requires an `approval` argument). The test invocation was corrected without
changing the gate. A separate numerical check exposed rounded-sum noise for
constant daily returns; exact summation and its regression were added before the
final 43-pass run. The full ordinary/DB suite was not run.

The full original prompt is archived verbatim at
[`prompts/stage-04-paper/stage-04b2e5e-simple-local-historical-backtest-runner.md`](../prompts/stage-04-paper/stage-04b2e5e-simple-local-historical-backtest-runner.md).
Future substantive requests continue the existing per-stage prompt archive convention.

# Stage 3C — Prospective forecast evaluation

Implemented for review on 2026-10-14. **No actual forward outcomes were inspected
or scored.** Validation used synthetic predictions, clocks and target candles,
plus an isolated PostgreSQL test server. The development database was not queried.
The first four genuine forward files were not parsed; preservation checks hashed
their opaque bytes only. The existing collector continued independently.

## Frozen protocol and scientific scope

The [protocol](stage-03c-forward-evaluation-protocol.md), version `stage-3c-v1`,
was written and frozen before implementing scoring or accessing outcome data:

```text
SHA-256: 9bb655a374af27ecf41b0f31947dfad4256eb40e8973d53caf278507084d4bed
```

The evaluator pins this digest and refuses modified protocol bytes. Every score
and report records it. Material changes after viewing results require a separately
versioned protocol and separate evidence; never edit this version or rescore an
occupied identity. Review the protocol before genuine scoring.

The target remains `ln(C[t+1] / C[t])`: C[t] is the original exact source close
inside the forecast, and C[t+1] is the next native Binance Spot 4h close. A source
opening 12:00 targets opening 16:00 / closing 20:00; scoring starts at 20:01 UTC.
This is a candle-to-candle log return, not an issued-at-to-close return, percentage,
trade, or evidence of executable profitability. No actual holdout data, strategy
simulation, model fitting, parameter tuning or model promotion enters Stage 3C.

| Cohort | Rule |
| --- | --- |
| `primary_timely_automated` | Issued within `[feature_available_at, +15 minutes)` and before target close, with a matching Stage 3B `recorded` / `replayed`, `complete_fresh` journal entry linking the exact forecast hashes and issuance. |
| `secondary_late_manual` | Issued at or after that deadline but before target close; includes both original source-08:00 manual records from 2026-10-14. |
| `timely_unattributed` | Timely valid forward evidence without a qualifying automated journal; separate from primary. |

Clock time alone cannot prove unattended origin: Stage 3A has no automation flag.
An `already-recorded` journal entry alone is insufficient. The qualifying journal's
exact UTF-8 bytes and SHA-256 are embedded in the first score, so later journal
loss or recovery cannot silently reclassify it. A successful market entry can
qualify while the other market's cycle is still running. Local evidence is not
independently witnessed publication or tamper-proof attestation.

## Commands for future manual use

Run from `/Users/owencrew/Code/backtest-badger`. These commands are documentation
only: **none of the genuine scoring commands below were executed**. Use the
existing local development `.env`; the module rejects non-loopback database hosts.
Do not point that configuration at production or a tunnel. No sync or download is
triggered; the existing collector refreshes data independently.

After protocol review, the exact command for the first automated BTC record is:

```sh
uv run --locked --env-file .env python -m backtest_badger.forward_evaluation score \
  --record artifacts/forward-predictions/binance-spot-BTCUSDT-4h-20261014T120000Z.json
```

To manually score all four original records, preserving their separate cohorts:

```sh
for symbol in BTCUSDT ETHUSDT; do
  for source in 20261014T080000Z 20261014T120000Z; do
    uv run --locked --env-file .env python -m backtest_badger.forward_evaluation score \
      --record "artifacts/forward-predictions/binance-spot-${symbol}-4h-${source}.json"
  done
done
```

Source-08:00 records require actual current time at or after 16:01 UTC; source-12:00
requires 20:01 UTC on 2026-10-14. The target also has to exist as a valid completed
observation in the database. There is no scoring clock, source-data, settling-delay,
training, model or historical override. Python injections are for synthetic tests.

Offline reporting, with no `.env`, database or provider connection:

```sh
uv run --locked python -m backtest_badger.forward_evaluation report
uv run --locked python -m backtest_badger.forward_evaluation report --period week
uv run --locked python -m backtest_badger.forward_evaluation report --period month

# Repeatable cutoff; select the UTC cutoff appropriate to the report.
uv run --locked python -m backtest_badger.forward_evaluation report \
  --as-of 2026-10-15T00:00:00+00:00
```

`report` also accepts `--records`, `--outcomes` and `--operations` for retained
backup copies or isolated synthetic evidence. Run from the repository root so the
pinned protocol is available. JSON is emitted to stdout, with undefined values as
`null`; no report file is overwritten automatically. Identical files and cutoff
produce byte-identical output. Outcome files captured later than the cutoff and
forecasts issued later than it do not enter that report's scores.

| Scoring status | Meaning | Exit |
| --- | --- | ---: |
| `scored` | New immutable outcome published for all four models. | 0 |
| `already_scored` | Existing evidence validated; no DB connection or new capture. | 0 |
| `pending_not_settled` | Actual clock precedes target close + 60s; no outcome query. | 2 |
| `pending_target_missing` | Exact target absent from the read-only snapshot. | 2 |
| Failure | Invalid/conflicting forecast, target, provenance, configuration, clock or publication; stderr diagnostic, no overwrite. | 1 |

Reports return 0 for valid retained evidence, including an empty sample; they
return 1 if invalid forecasts, outcomes, journals or orphan outcomes are disclosed.
Argparse usage errors return 2. Missing journals can leave automation unattributed;
the scoring JSON lists unreadable journals. Fix evidence through investigation,
never by deleting an occupied outcome to force a revised score.

## Evidence validation and immutability

`forward_evaluation.py` is a standalone Python module. No existing CLI registration,
dependency or live-prediction implementation was changed. It reuses established
pure validation, Decimal logarithm and read-only snapshot helpers. Scoring never
calls model fitting, historical replay, provider acquisition or database writers.

Forecast validation checks canonical exact bytes, duplicate JSON keys, content and
recipe checksums, filename/record/prediction identities, exact schema, market/native
interval, seven retained source candles, causal feature values, fixed recipe and
saved baselines, finite forecasts and all source/capture/calculation/issuance times.
Sources before 2026-10-14 are ineligible, excluding the historical holdout. Recipe
fingerprints are retained and validated structurally, not compared with the active
checkout. Full ML replay remains a separate Stage 3A verification in the original
source/runtime environment; scoring does not read training files.

One READ ONLY, REPEATABLE READ transaction queries the exact market and exactly
the target interval. Market-ID remapping is rejected, not acknowledged implicitly.
The target must satisfy economic/OHLC/volume/trade constraints, UTC identity,
positive version, native Binance REST/monthly-archive URL and SHA-256 rules.
Its original observation must be at or after close + 60 seconds, and observation,
recording and watermark timestamps must precede the evaluation capture. A later
watermark cannot rescue an unsettled original observation. Delayed scoring of a
valid completed observation is allowed. No canonical source row is queried.

The separate `artifacts/forward-outcomes/RECORD_ID.json` contains:

- Original prediction ID, content SHA-256 and exact-file SHA-256, market/source/
  target identities, original issuance and frozen cohort evidence.
- Original source close and full captured target candle, including all exact
  Decimal economics, version, source URL/kind/hash, observation/recording times,
  last-observed watermark and evaluation capture timestamp.
- Actual log return, all four original forecasts, individual errors and directions.
- Protocol identity, evaluation/dependency-module fingerprints, Python version and
  an `outcome_sha256` of the canonical content excluding that checksum field.

A private `.partial` file is flushed, made read-only and fsynced, then published by
exclusive hard link; the directory is fsynced afterward. No replace/overwrite is
used. Concurrent attempts have one winner. A directory-fsync failure reports that
the file is visible but durability is uncertain; retry validates it. Partial files
are not scores and are disclosed offline. Existing evidence is semantically
revalidated against its original forecast and retained candle before returning
`already_scored`, without touching PostgreSQL. Corruption or conflicting forecast
bytes fail visibly, including recomputed checksums with inconsistent metrics.

The first accepted target version remains fixed. Canonical provider revisions,
source revisions and later cohort evidence never replace it. Keep original
forecasts, outcome files, operational journals, protocol and matching implementation
together in the operator's existing backup process. No new backup service or
unattended scoring job was installed. Permissions/hashes are safeguards, not
protection against an owner rewriting all evidence and checksums.

## Metrics, counts and periods

Per market/model/cohort: genuine/scored counts; pending, mature-unscored and invalid
outcomes; MAE, RMSE, forecast bias, mean realised log return; directional numerator,
denominator, accuracy and coverage; and MAE/RMSE improvement against both original
zero and saved training-mean benchmarks (`1 - model_error / baseline_error`).
All comparisons use the identical complete observation IDs, listed with the
matched count. Missing one model invalidates the entire outcome, preventing
comparisons across different timestamp subsets. Zero baseline errors and empty
denominators return `null`, not zero.

Direction uses strict sign with no economic tolerance. Exactly zero forecasts
abstain. Exactly flat targets count as incorrect for nonzero predictions. Actual
direction also uses exact Decimal close comparison, even if a minuscule derived
return underflows binary float. Prices remain exact strings and derived metrics
retain raw float precision; JSON does not round results into percentages.

Offline reports cannot know whether a mature target exists in PostgreSQL. They
therefore call an unscored mature forecast `mature_unscored`, not “missing target.”
Missing prediction counts use expired promptness horizons since the earliest
retained valid Stage 3B cycle, including downtime gaps. They are unknown without
that monitoring baseline. Absent expected files and invalid expected files are
listed separately. Primary missing-opportunity counts also include horizons having
only late or unattributed observations; other cohorts have no defined opportunity
grid. Malformed forecasts with unknown cohort, orphan scores and invalid journals
are disclosed separately. No missing forecast is substituted or backfilled.

Weeks start Monday 00:00 UTC; months start day 1. Group by target closing endpoint,
using half-open boundaries. Optional reports retain intervening empty periods and
flag incomplete current periods. Counts always appear; period metrics require
30 scores/week or 100/month for the particular market/cohort. The all-period report
works with zero, one or hundreds of observations. Under 100 scored observations,
comparisons are explicitly preliminary. Larger samples remain descriptive; the
threshold is a reporting convention, not statistical power or automatic promotion.

## Verification and unchanged boundaries

Synthetic tests exercise actual Stage 3A recording with synthetic training data,
then scoring without model refits. They cover exact target alignment/settling,
all cohort boundaries, stale/malformed/duplicate/missing targets, native provenance,
source-price preservation, provider revisions, altered hashes/bytes/recipes,
conflicting outcomes, exclusive and concurrent publication, uncertain directory
durability, clocks, matched metrics, zero/flat/underflow directions, empty samples,
100 observations, period boundaries/thresholds/empty periods, missingness,
independent BTC/ETH results, deterministic reports and offline CLI behaviour.

PostgreSQL tests use only a separate disposable PostgreSQL 17 container, bound to
localhost:55439, with no existing volume. Fixtures create/migrate/drop random test
databases. They assert exact target query bounds and inspect `transaction_read_only`
and `transaction_isolation`; PostgreSQL rejects a test mutation inside the snapshot.
Synthetic candle rows and revision counts remain unchanged after reads.

Final verification: **817 tests passed, zero skipped**: 637 unit tests and 180
PostgreSQL integration tests. This includes **109 new synthetic cases and 3 new
PostgreSQL cases**; all 705 pre-existing regression cases passed. The focused
synthetic suite also passed independently. Executed with the existing locked
environment:

```sh
.venv/bin/pytest -q tests/test_forward_evaluation.py
# BADGER_TEST_ADMIN_DSN was set only to the disposable localhost:55439 server.
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
git diff --check
```

Ruff lint, formatting and whitespace checks passed. No live Binance requests were
used and no remote CI run is claimed. All **45 pre-existing files** in the scoped
preservation inventory retained identical SHA-256, size and nanosecond mtime:
existing package Python modules, both dependency files, both LaunchAgent plists,
all four original forecast JSON files and the original top-level operation journals.
No source data, holdout file or realised outcome was parsed for this inventory.
The prompt archive matches the supplied bytes exactly and the frozen protocol
digest remains unchanged. The disposable test container was removed after testing.
The separate outcome directory is prepared but contains **zero genuine outcome
records**.

Added: this guide, the frozen protocol, `src/backtest_badger/forward_evaluation.py`,
`tests/test_forward_evaluation.py`, `tests/integration/test_forward_evaluation.py`
and the verbatim prompt at `prompts/stage-03-forward/003-forward-evaluation.md`.
Updated: README and roadmap. Existing Stage 3A/3B guides, fingerprinted modules,
`pyproject.toml`, `uv.lock`, installed/repository LaunchAgent plists, forecasts and
historical operation journals were preserved. No collector restart or interruption,
database migration, holdout inspection, genuine outcome scoring, trading, website,
deployment, commit, push, new scheduler, audit or Field Note was performed.
Stage 3C stops here; Stage 4 paper trading has not begun.

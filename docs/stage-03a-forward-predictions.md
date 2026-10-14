# Stage 3A — Manual forward prediction recording

Implemented for review on 2026-10-14. This records **unscored forward observations**,
not trading recommendations, simulated trades or demonstrated profitable models.
Stage 2D's fixed trading policies lost money under base and stress costs (zero
remained cash). No model, feature, parameter or training boundary was selected or
changed in response to those results.

## Manual operation

Run from the repository root, using the existing local development environment.
Refresh each market separately when needed; recording never invokes ingestion:

```sh
uv run --locked --env-file .env badger sync-recent --symbol BTCUSDT --interval 4h
uv run --locked --env-file .env badger sync-recent --symbol ETHUSDT --interval 4h

uv run --locked --env-file .env badger record-forward --symbol BTCUSDT
uv run --locked --env-file .env badger record-forward --symbol ETHUSDT

# Offline; replace the filename with the path printed by record-forward.
uv run --locked badger verify-forward --record artifacts/forward-predictions/RECORD.json
```

Existing `sync-recent` catch-up limits and explicit recovery rules remain in the
[Stage 1C.1 guide](stage-01c1-rest-tail-and-refresh.md). Recording offers only
`--symbol`; no clock, timestamp, historical start, settling-delay, model, training
pin or output override exists in the production CLI. Python clock/path injection
is for synthetic tests. Normal configuration comes from the existing `POSTGRES_*`
settings. This stage authorised only the local development database.

Each command records all four forecasts together or fails. It prints the record
path, actual issue time, target endpoint, unique forecast identities and full
17-significant-digit log returns. Existing identities fail explicitly without
replacement. There is no scheduler, service, order submission, paper trading,
scoring, website, migration or new dependency.

## Fixed feature and model provenance

The five Stage 2A features remain in this exact order:

1. `log_return_4h = ln(C[t]/C[t-1])`
2. `log_return_12h = ln(C[t]/C[t-3])`
3. `log_return_24h = ln(C[t]/C[t-6])`
4. `realised_volatility_24h = sqrt(sum(r[i]^2, i=t-5..t))`
5. `relative_base_volume = V[t]/mean(V[t-6..t-1])`

`features.causal_features` computes them directly from exactly seven consecutive
native four-hour candles. Prices/volumes stay Decimal until the existing helpers
convert derived values to floats. Zero historical volume, missing observations,
invalid economics and incorrect identities fail; there is no filling or repair.
The forward path never calls `build_rows`, reads candle `t+1`, or calculates a label.

Every invocation deterministically refits the existing `evaluation.fit_models`
and uses `evaluation.predict_models`, independently for the selected market:

| Identifier | Fixed Stage 2B definition |
| --- | --- |
| `zero` | Constant zero |
| `training_mean` | Selected market's pre-2024 training-target mean |
| `ridge` | Training-fitted StandardScaler + Ridge(alpha=1, solver="svd") |
| `gradient_boosting` | Squared-error loss, 100 trees, learning rate 0.03, depth 2, minimum leaf 100, full subsample, seed 42, no early stopping |

The default source is `artifacts/research/stage-2a-v1/`. Both pins are unchanged:

```text
research.csv:  04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8
manifest.json: a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e
```

`model_data.load_model_data(training_only=True)` retains the existing full-artifact
schema, hash, chronological identity, split, count, gap and anomaly validation.
It skips validation and test rows **before accessing numerical features or targets**.
Whole-file hashing and CSV tokenisation necessarily read their bytes opaquely.
No held-out labels are converted, returned to fitting, predicted or scored.
The ordinary Stage 2B loader behaviour is unchanged.

The original feature-availability split and strict label purging still apply:
training features and their target availability must precede 2024-01-01 UTC.
BTC uses 13,782 training rows and ETH 13,783. All fitting and inference retain
Stage 2B's one-thread numerical limit. No incremental learning or rolling refit
on newer outcomes occurs; each run refits the same frozen training sample.

Records retain ordered selected-training-row hashes, both artifact pins, full
estimator/scaler parameters and baseline constants, Python/platform and relevant
package versions, the dependency-file hashes (`uv.lock`, `pyproject.toml`), and
hashes of the implementation modules. A `model_recipe_sha256` hashes this entire
deterministic recipe. It identifies the reproducible fit, not a serialized model.
Refitting is small enough to avoid a fitted-estimator cache, registry or any
pickle/joblib deserialisation. Keep the pinned artifacts, source version and locked
runtime for later verification; cross-version/platform reproduction is not promised.

## Clocks, freshness and source selection

`rest.eligible_end` reuses the existing integer UTC-grid policy:

```text
end = floor_to_4h(actual_UTC_now - 60 seconds)
t = end - 4 hours
feature_available_at = t + 4 hours + 60 seconds
target_close_boundary = t + 8 hours
```

For source opening **08:00 UTC**, the close boundary is **12:00**, feature eligibility
is **12:01**, and the next candle's endpoint is **16:00**. The forecast predicts
`ln(C[t+1]/C[t])`. That reference interval has already started when a forecast is
issued; it is not four hours of exposure beginning at issuance. Manual delays
reduce the unknown portion of the horizon and must not be hidden in later research.

The required source is determined by the actual clock, never by the latest row
that happens to exist. During **12:00–12:00:59.999999**, the new source is still
settling and the older forecast's target has already closed, so recording fails.
At 12:01 exactly it becomes eligible. A database missing that newly required row
fails with a stale-data message. A complete tail does not excuse missing older
members of the seven-candle window.

`research_snapshot` enforces one PostgreSQL **READ ONLY, REPEATABLE READ** snapshot.
The market lookup checks Binance Spot identity and base/quote assets. The only
candle range is `[t-24h, t+4h)`, ordered by opening; no future target row is queried.
Existing economic validation checks exact Decimal prices, OHLC bounds, volumes,
taker volumes, trade counts, grid alignment and closed-before-observed ordering.
Native-interval source URL identity, source kind, SHA-256 format and version are
validated. REST URLs must identify Binance's public klines endpoint, the selected
symbol, 4h interval and UTC timezone; archive URLs identify the native monthly file.

All timestamps must be aware UTC. Each retained version's `observed_at`,
`recorded_at` and `last_observed_at` must be no later than `captured_at`, sampled
after the snapshot read. Original observation must precede database recording
and the last-observation watermark. No later revision is substituted.

The application computes predictions, then samples `calculated_at` and `issued_at`.
After writing and syncing the private staging file, it samples the actual clock
again immediately before the exclusive publication operation. It requires:

```text
feature_available_at <= captured_at <= calculated_at <= issued_at <= final_clock
final_clock < target_close_boundary
```

The selected horizon must still be current. A reversal between sampled clocks,
expired horizon, computation failure or failed pre-publication write leaves no
published record. No historical replay can be labelled forward through the CLI.
`issued_at` is the local post-calculation issuance decision, just before staging;
the final clock check enforces continued eligibility immediately before publication.
The final check is an execution guard, not a separate timestamp persisted afterward.

## Record schema and immutable publication

Schema version 1 is a single JSON document per market/source-candle observation:

```text
artifacts/forward-predictions/binance-spot-BTCUSDT-4h-YYYYMMDDTHHMMSSZ.json
```

The stable identity omits the candle version and model fingerprint deliberately:
a provider revision or code update cannot authorise a second forecast for the same
market/candle/model. Each of the four `prediction_id` values appends `:<model_id>`
to that record identity. The JSON retains:

- Market identity, native interval, source open/close boundary, feature eligibility,
  capture/calculation/issue times, target open/close boundary and horizon definition.
- Ordered feature names/values and original definitions.
- Seven complete source rows: every economic value as a Decimal string, database
  market ID, opening, interval, version, all three observation/recording timestamps,
  source kind, exact URL and provider-response/archive SHA-256 reference.
- Model/training/runtime/implementation evidence described above.
- Four finite dimensionless next-four-hour log-return predictions.
- `content_sha256` of UTF-8 JSON with sorted keys, compact separators and no NaN,
  excluding only the hash field itself. Formatting whitespace is not part of this
  semantic content checksum. Duplicate JSON keys are rejected by verification.

No future price, realised outcome, score, hypothetical trade or P&L appears in the
record. The retained source rows are sufficient to rebuild inputs without current
canonical rows. Source hashes reference Stage 1 retained acquisition evidence;
this verifier validates provenance structure and replays retained economics, but
does not re-download or reparse raw provider responses to authenticate them.

Publication writes a uniquely named `.forward-*.partial` file in the same directory,
flushes and fsyncs it, sets its permissions read-only, performs the final clock
check, then uses `os.link` to publish atomically without replacement. The directory
is fsynced before success is reported. All four models share one file, so a partial
set cannot appear. Existing paths win even under simultaneous processes. A filename
collision is an explicit failure, never an overwrite or a silently renewed issue time.

Normal failures clean up staging files and allow retry while the same horizon is
still eligible. A process crash can leave `.partial` files; they are not records,
are never promoted by a later invocation, and do not reserve a final identity.
After inspection, they may be removed manually. If directory fsync fails after the
link, the command explicitly reports that the record is visible but durability is
uncertain: inspect and verify that file; do not delete it to retry the forecast.
A crash after publication but before console output is likewise resolved by
verifying the existing immutable file. Ordinary retries refuse it.

## Independent verification and provider revisions

`verify-forward` does not load database settings, connect to PostgreSQL, call a
provider or write any files. It checks the hash, exact reconstructed schema,
identities, UTC clock ordering, eligibility, target endpoint, source timings and
provenance. It reconstructs all five features from the seven retained rows, refits
the four fixed models from the pinned training artifact, checks recipe evidence
against the recorded implementation/runtime, and compares each numerical forecast
using Stage 2B's `rtol=1e-10, atol=1e-12`. Other reconstructed fields match exactly.
Verification success means reproducible unscored evidence; it does not imply skill.

A later provider revision is a new canonical observation in Stage 1's versioning
system. It never updates a forward JSON file. Verification uses the exact version
and economics retained at issuance, even when current PostgreSQL rows differ.
If the runtime, implementation or training files change, verification fails rather
than silently substituting the new recipe. Restore the recorded source/environment
and pinned training bytes in a separate checkout for historical verification.

## Actual local validation

At **2026-10-14 14:12:11 UTC**, both local markets were stale. Their latest stored
source opening was **2026-10-13 08:00 UTC**; the required opening was
**2026-10-14 08:00 UTC**, with target endpoint **16:00 UTC**. Each required window
had only one of its seven candles and was missing six. Eligibility was rejected
for both markets. **No genuine predictions were recorded**, no retrospective
example was fabricated, and no data refresh was invoked. The manual refresh
commands above are the next operator-controlled step.

Two independent deterministic fits per market using the real pinned training
artifact produced identical model recipes and identical numerical outputs on a
clearly synthetic feature vector. No forward artifact was created by this check.
Training means were BTC `0.00015407868521495738` and ETH
`0.00010708164895640677`. Ordered training-row fingerprints:

```text
BTC: 5da5db3e98a947b7d3d4bc718eb36552210154417f60891b375ea476b9e90c1d
ETH: 81fa7ca0863fed5f96aa730ea60c6d3823b4c53aca223a7e107c59d0da4fa481
```

The synthetic test suite exercises complete artifact publication and offline replay,
wrong/rehashed schema and evidence, source revisions, timing boundaries, model reuse,
held-out numeric access guards, distinct markets, concurrent duplicate publication,
clock reversals, disk failures and CLI dispatch. Disposable PostgreSQL tests check
actual read-only enforcement, repeatable snapshots, exact source bounds, provenance,
missing markets and stale rows. Automated tests never contact Binance.

Final verification: **640 tests passed, zero skipped**: 463 unit tests and 177
PostgreSQL integration cases on a separate temporary PostgreSQL 17 container.
This includes 85 new Stage 3A cases. Ruff lint, Ruff formatting (82 Python files)
and `git diff --check` passed. The test container was removed afterward. No remote
CI run is claimed. The exact prompt archive matches the supplied bytes.

The complete existing artifact inventory — **880 files** — retained identical
SHA-256, size and nanosecond modification times. Frozen datasets, experiments,
backtests and earlier evidence were unchanged. No prior audit or Field Note changed.
New ignored evidence lives separately from genuine forecasts under
`artifacts/forward-validation/stage-3a-v1/`: `live-eligibility.json`,
`training-reproduction.json` and `verification.json`.

Tests were executed with `BADGER_TEST_ADMIN_DSN` pointing only at the disposable
localhost server, using `.venv/bin/pytest -q`. The integration fixtures created,
migrated and dropped their own random databases; the development store was only
read for the explicitly requested eligibility check. Other executed checks were
`.venv/bin/ruff check .`, `.venv/bin/ruff format --check .` and `git diff --check`.

## Scientific and operational limits

Local timestamps are evidence of local recording, **not independent cryptographic
proof of historical publication**. Clock correctness remains an operator assumption;
this offline command does not contact an independent time authority. Sampling can
detect reversals between checks, not an incorrectly set but steadily advancing clock.
OS suspension between the final clock check and filesystem publication cannot be
made atomic with wall time. Local permissions and hashes are not tamper-proof:
an owner can alter files and recompute hashes. No signed timestamp, remote witness
or durable off-machine backup is introduced.

The 60-second delay is a policy, not provider finality. Single-provider revisions,
missing history, market shifts, correlated BTC/ETH observations and the fixed
pre-2024 training sample limit interpretation. These forecasts are not evidence
of actionable trading value. Manual availability and delays can introduce selection
effects; any future scoring protocol must account for actual issue times and be
scoped separately before examining outcomes.

This stage ends at recording and verification. No Field Note, scheduling, holdout
assessment, outcome scoring, paper trading, deployment, commit or push is included.

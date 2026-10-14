# Stage 3C — Prospective forecast evaluation protocol

Version: **stage-3c-v1**, frozen for implementation on **2026-10-14**, before
accessing any realised forward outcome. No genuine outcome scoring is authorised
during implementation. The operator will review this protocol and synthetic tests
before separately running scoring. This file's exact UTF-8 bytes are SHA-256 pinned
in the evaluator and identified in every outcome and report. The digest is recorded
outside this file to avoid a self-referential checksum. Do not edit this version
after results are viewed: material changes require a separately named new protocol
and separate evidence, with an explanation, never replacement of scored records.

## Eligible predictions and cohorts

Eligible records are original Stage 3A schema-v1 `unscored_forward_observation`
JSON files for Binance Spot BTCUSDT or ETHUSDT, native 14,400-second candles, with
exact identity filenames, canonical published bytes, valid content and recipe
checksums, four finite saved forecasts, valid retained seven-candle source evidence,
causal features and ordered capture/calculation/issuance timestamps. All must obey
`feature_available_at <= captured_at <= calculated_at <= issued_at < target_close`.
Only prospective sources opening on or after 2026-10-14 00:00 UTC enter this release;
the 2025–September 2026 holdout is ineligible and never queried. Scoring verifies
retained evidence without fitting models, reading training files or requiring the
active checkout's fingerprints to match the original recipe. This is integrity
verification, not full historical model replay or proof of publication.

Classify independently of outcomes:

- **primary_timely_automated**: actual issuance lies in
  `[feature_available_at, feature_available_at + 15 minutes)`, before target close,
  and a retained Stage 3B journal links this exact record's content/file hashes,
  source identity and issue time to a successful `recorded` / `replayed` result
  with `complete_fresh` refresh. The journal must have valid cycle timing and
  structure. A completed market entry in a still-running cycle also suffices;
  the other market need not succeed. An `already-recorded` entry alone does not
  establish automated origin. Retain the qualifying journal bytes and hash with
  the score. If several qualify, choose the earliest cycle, then filename.
- **secondary_late_manual**: valid forward issuance at or after the promptness
  deadline but before target close. Stage 3B cannot produce these under its
  deadline guard. This includes the two original 2026-10-14 source-08:00 BTC/ETH
  manual observations; do not pool them with primary observations.
- **timely_unattributed**: timely valid records without qualifying automated
  evidence. Report separately; do not infer automation from clock time alone.

Cohort assignment and supporting evidence are frozen when first scored. Missing,
unreadable or interrupted journals are disclosed. Recovery of better evidence
later requires separate investigation, not retroactive cohort changes. Local
journals and hashes are neither signed attestations nor independent witnesses.

## Exact target and availability

`actual_log_return_4h = ln(C[t+1] / C[t])`, where C[t] is the exact Decimal source
close retained in the original prediction, and C[t+1] is the immediately following
native Binance Spot four-hour candle's close. Match exact market identity, including
local market ID and base/quote assets, interval and opening time. Never read or
substitute the canonical source candle to define C[t]. This is a candle-to-candle
log return, **not a return from issued_at, an executable return or a percentage**.

Source 12:00 closes 16:00, features become available 16:01, a 16:04 forecast targets
opening 16:00 / endpoint 20:00, and scoring is forbidden before **20:01 UTC**.
Scoring uses the actual aware UTC clock; no CLI clock or settling-delay override.
Python clock injection exists only for synthetic tests. Check before any outcome
read and after capture; reject sampled clock reversals. No historical backfills,
new forecasts, target imputation or replacement of missing forecasts is allowed.

## Outcome data and provenance

Read only the exact target identity from the existing local development PostgreSQL
store in one idle-autocommit READ ONLY, REPEATABLE READ snapshot. No database writes,
provider requests or synchronisation occur. Non-loopback connections are refused;
the operator must use the development configuration, never production or tunnels.
Reject market-ID remapping or source-identity mismatch; this version offers no
acknowledgement override. Missing exact targets produce `pending_target_missing`.
Before close + 60s return `pending_not_settled` without reading target data.

Require the full existing candle schema, finite positive Decimal prices, OHLC
bounds, nonnegative and consistent volumes/trade counts, native UTC alignment,
positive integer version, valid source SHA-256 and native Binance REST/archive URL
identity. `observed_at` must be at or after the target close + 60s; an earlier
observation is rejected as stale/unsettled, even if its watermark is newer.
Require `observed_at <= recorded_at <= evaluation_captured_at` and
`observed_at <= last_observed_at <= evaluation_captured_at`. There is no maximum
age for a valid completed observation: delayed scoring is permitted. Retain all
economic fields, source kind/URL/hash, version, observation time, database recording
time, watermark and evaluation capture time exactly. Invalid data fails visibly;
pending and invalid attempts publish no successful outcome record.

The first valid captured canonical target version wins. Later provider revisions
are never substituted, even on retry. Original source revisions are also ignored.
Revision sensitivity may be investigated separately without rewriting evidence.
The 60-second delay is a policy, not a guarantee of provider finality.

## Individual and aggregate metrics

Use each of the four original published values (`zero`, `training_mean`, `ridge`,
`gradient_boosting`) without fitting, rounding, clipping or threshold optimisation.
The training-mean benchmark is the mean saved in that record's fixed pre-2024 recipe;
it is never recomputed from realised forward returns. The zero benchmark is exactly
zero. Preserve Decimal input prices; use the Stage 2A guarded-precision logarithm
and binary floats for derived returns/errors, without display rounding in JSON.

For prediction p and actual y, retain error `p-y`, absolute error `abs(p-y)`, squared
error `(p-y)^2`, predicted and actual directions (-1, 0, +1), and directional
correctness. Direction uses strict mathematical sign, **no tolerance**. Exactly
zero forecasts abstain (`directional_correct = null`); every nonzero forecast
counts in the direction denominator. An exactly zero actual return counts as an
incorrect direction for every nonzero forecast. Actual direction also follows the
exact Decimal close comparison, so numerical underflow cannot turn a nonzero price
move into a flat economic direction. This protocol intentionally does not inherit
Stage 2B's 1e-12 directional tolerance or Stage 2C trading thresholds.

For each market, cohort and model, compute MAE = mean absolute error, RMSE = sqrt
mean squared error, bias = mean(p-y), mean realised log return, direction numerator,
denominator, accuracy = correct/nonzero forecasts, and directional coverage.
All model/baseline comparisons use the same complete scored record identities;
one invalid model invalidates the whole score. Relative error improvement is
`1 - model_error / baseline_error`, separately for MAE and RMSE against both zero
and saved training mean. Positive means smaller error; negative means worse.
Report the common matched count and identities. Zero baseline error, empty samples
and zero directional denominators are **undefined (JSON null)**, never zero.
Keep BTC and ETH and every cohort separate. Do not rank, select or promote models.

## Missingness, duplicates and immutable evidence

One atomic exclusive outcome JSON publication per prediction identity under
`artifacts/forward-outcomes/`, separate from predictions and operation journals.
Retain prediction content and exact-file hashes, source/target identities, issue
time, cohort evidence, original source close, full target evidence, all forecasts
and errors, protocol version/hash, implementation/runtime fingerprints and outcome
checksum. Idempotent retry verifies the existing evidence and returns
`already_scored` before database access. Conflict, corruption, duplicate identities
or altered prediction bytes must never overwrite evidence. Partial files do not
count as scores. All four models share one immutable outcome.

Offline reports read only retained prediction/outcome/journal files. Counts include
valid genuine predictions, scored, not-yet-settled, mature-but-unscored (target
availability unknown offline), and invalid outcomes for otherwise valid records.
Malformed predictions with unknowable cohort are listed separately by filename,
not silently dropped or assigned a fabricated cohort. Orphan/duplicate outcome
files and invalid journals are separately disclosed. Report invalid evidence with
an unsuccessful command exit as well as the usable descriptive results.

Missing predictions can be distinguished from unscored predictions only relative
to a monitoring grid: use the earliest valid retained Stage 3B cycle's source
opening through each expired promptness deadline at the report's UTC as-of time.
Count absent files separately from invalid expected files. Also report missing
primary observations (including late/unattributed records) on that grid. Before
monitoring began or without journals, missing counts are unknown (null), not zero.
Missing primary counts belong to the primary cohort; missing secondary/unattributed
opportunities are undefined. Preserve gaps, including entire downtime horizons.
No outcome missingness reason is inferred from an absent score file. Missingness
may be selective; complete-case accuracy must not conceal these counts.

## Reporting periods and sample warnings

Default reporting is all retained eligible evidence as of an explicit UTC timestamp
(default actual current time); exclude forecasts issued later and scores captured
later than that cutoff. Identical evidence and cutoff yield deterministic JSON,
ordered by identity, without a fresh generated-at timestamp. Reports identify the
cutoff and protocol. They do not query the database to resolve pending data.

Optional week/month summaries group by **target closing endpoint**. Weeks start
Monday 00:00 UTC (ISO week year); months start day 1 at 00:00 UTC. Boundaries are
half-open, so an endpoint exactly on Monday/month-start belongs to the new period.
Include intervening empty periods. Always print counts; period metrics require
at least 30 scored observations per market/cohort/week or 100 per month. Below that
threshold, period metrics are null with an insufficient-sample warning; all-period
metrics remain available even for one score. Include incomplete current periods
with their boundaries and explicit partial-period status; no favourable selection.

Under **100 scored primary observations per market**, prominently label primary
comparisons preliminary. Also flag any cohort/period below 100 as preliminary.
The 100-observation threshold is a reporting convention, not a power calculation.
Larger samples remain descriptive, with no automatic significance claim, winner,
promotion, persistent-alpha or executable-profitability claim. No significance
tests, bootstrapping, threshold search or strategy optimisation belongs here.

## Scientific limits and exclusions

Unattended collection can miss horizons; manual lateness observes part of the
target interval and creates selection effects. Even timely forecasts begin after
the reference source close. Market/time dependence, correlated BTC/ETH outcomes,
single-provider revisions, missing data, fixed pre-2024 training and changing
conditions limit generalisation. Markets, weeks and months are not independent
replications. Forecast errors are not simulated or real trading returns and do
not model fills, latency, fees or costs. Negative results remain valid results.

Preserve the live collector, its LaunchAgent, implementation fingerprints, original
records, fixed models/features/training and untouched historical holdout. No
trading, paper trading, scheduler, new service, dashboard, migration, deployment,
model selection, audit or Field Note is part of Stage 3C.

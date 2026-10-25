# Stage 5B — Live market dashboard and research explanations

25 October 2026, Europe/London. Local implementation for owner review. No commit,
push, website deployment, production write, scheduler change, forecast generation,
rescoring, model fitting or historical replay was performed. Original scientific
source, frozen protocols, Field Note sources and historical account values are
unchanged. The starting Git tree was clean.

## The Burrow: genuine market observations

The existing Next.js static website now fetches public Binance Spot observations
directly in the browser. There is no Next.js API, exchange account, credential,
proxy, database connection or trading capability.

Official specifications checked before implementation:

- [Binance market-data-only URLs](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md).
- [Spot REST market endpoints](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market), including the 12-field kline tuple, UTC timezone, millisecond timestamps and 1,000-row limit.
- [Lightweight Charts v5 API](https://tradingview.github.io/lightweight-charts/docs/5.0) and the [v5.2.1 attribution notice](https://github.com/tradingview/lightweight-charts/blob/v5.2.1/NOTICE).

`web/lib/market.ts` uses `https://data-api.binance.vision/api/v3/time`, `/klines`
and `/ticker/price`. The server clock fixes each window; ticker and candles then
load together. Responses are credential-free, uncached and bounded by a 15-second
request deadline. The ticker has no last-trade timestamp: the interface explicitly
calls its price the latest value received and records the successful observation
time, not an exchange trade time. Ticker and candle requests are not atomic and
can legitimately differ slightly.

| Range | Candle interval | Typical observations including the open candle |
| --- | --- | --- |
| 1D | 5 minutes | 289 |
| 7D | 30 minutes | 337 |
| 30D | 1 hour | 721 |
| 90D | 4 hours | 541 |

The starting boundary is rounded down to the selected UTC candle grid, so the
visible range can extend by less than one interval. No pagination is needed.
Validation checks the allowed market and range, ticker symbol, finite positive
prices, OHLC bounds, volumes/trade counts, exact close timestamps, grid alignment,
strict order, duplicates, requested window and the server/device clock difference.
Kline tuples contain no symbol; their identity is bound to the fixed request URL,
with the separately returned ticker symbol checked. This is provider trust, not
independent cryptographic market-data verification.

Missing intervals, including missing window edges, are counted and disclosed.
They are never sorted into a plausible order, invented or interpolated. Disjoint
runs use separate line/candle series, with whitespace observations preserving the
time-axis spacing across gaps. A close time before the sampled Binance clock marks
a completed interval; the current interval is provisional and sand-coloured.
Completed does not mean immune to later provider revisions. This display rule is
separate from research's one-minute settling policy.

Lightweight Charts **5.2.1** supplies candlesticks, lines, pan/zoom and crosshair.
An HTML OHLC/time readout and keyboard observation slider expose values without
requiring a canvas interaction. Reset view restores the full window; refreshes
preserve the inspected time range. The public chart carries the TradingView notice,
link and attribution logo. Apache 2.0 licence and NOTICE are also served under
`web/public/licenses/`. No library source was modified.

`web/lib/polling.ts` owns one completion-scheduled five-minute timer and one request
per feed. Manual refresh cancels/replaces a request. Hidden-page events cancel the
request and timer; returning to the page refreshes once. Unmount clears timers,
listeners and pending requests. Generation checks prevent old responses from
replacing a newer selection. BTC/range changes clear the previous selection's
values, avoiding a BTC price beneath an ETH label. Failures preserve any previous
successful snapshot and its timestamp, with an explicit stale/error message.
Timeouts also fail visibly; requests do not overlap in an automatic retry loop.

The market card displays loading, unavailable, error and stale states. Staleness
includes a failed refresh, more than ten minutes since the last success at a
refresh check, or an excessively old candle tail. There is no rapid background
age timer. Freshness is checked at request/visibility events; hidden pages are not
continuously updated. Network/region restrictions and Binance rate limits can
prevent access; no alternate or synthetic price is substituted.

## Production inspection and export feasibility

After the owner explicitly confirmed read-only SSH permission, `ssh Ubuntu-1`
confirmed that both `current` and Git HEAD resolve to:

`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`

Only release identity, evidence directory presence, allowlisted schema metadata
from one retained prediction and one outcome, and two implementation hashes were
returned. No credentials, raw records, journals or sensitive logs were printed.
No production command that generates forecasts, fits models, queries the database,
scores outcomes, writes an export, or changes services was invoked.

The inspected prediction/outcome schema is version 1, with the four expected model
identifiers, saved model errors, frozen cohort metadata and `stage-3c-v1` protocol
hash `9bb655a374af27ecf41b0f31947dfad4256eb40e8973d53caf278507084d4bed`.
Deployed `forward.py` and `forward_evaluation.py` hashes match the local files:

- `8487507abd19e406e63561a1c0b9ac36a1a67af8345ac6bcc6625c4bec3c8178`
- `d03febfcf722f6fd04c3ab7f82aeb48d5fbe596b6c4380359e5df37df5e9f290`

This supports an offline export from retained evidence without a production DB
connection or a new service API. It is schema/implementation inspection, not a
full production evidence audit. A proposed public snapshot location was absent;
no approved public URL or public-safe snapshot was identified or created. Therefore
forecast numbers remain unavailable in the website. Operational file counts are
not republished as performance statistics.

## Versioned public forward contract

The executable types and strict validator are in `web/lib/forecast.ts`. Version 1
allows only these fields; unexpected keys at every object level are rejected.

| Object | Fields and interpretation |
| --- | --- |
| Root | `schema_version: 1`, `kind: public_forward_research`, `data_source: Binance Spot`, `protocol: stage-3c-v1`, pinned `protocol_sha256`, `generated_at`, `as_of`, `latest`, `evaluations` |
| Latest forecast (at most one per market with evidence) | `symbol`, `source_close_at` (UTC boundary), `issued_at`, `target_close_at`, `recipe_sha256`, `cohort`, `status`, nullable `scored_at` and `actual_log_return_4h`, `models` |
| Per-model latest values | `predicted_log_return_4h`, nullable `signed_error`, `absolute_error`, `squared_error`; copied from retained predictions/outcomes |
| Evaluation (exactly six: each market × each cohort) | `symbol`, `cohort`, nullable `first_target_close_at`, `genuine_predictions`, `matched_count`, `pending_not_settled`, `mature_unscored`, nullable `missing_predictions`, `models` |
| Per-model all-period evaluation | Nullable `mae`, `rmse`, `forecast_bias`, `directional_accuracy`; integer `directional_correct`, `directional_denominator` |

All four models are mandatory: `zero`, `training_mean`, `ridge`,
`gradient_boosting`. Cohorts are `primary_timely_automated`,
`secondary_late_manual`, `timely_unattributed`. Cohorts are copied from the frozen
score where available; pending cohorts use the existing evaluator classifier.
Clock time alone is never treated as proof of automation.

The target is `ln(C[t+1]/C[t])`, using the retained original source close and the
next native 4h close. No return conversion is presented as a market price. Status
is `pending_not_settled`, `mature_unscored`, or `scored`. Outcomes are permitted only
at/after target close +60 seconds and before the evidence cutoff. The prospective
source-start restriction, +60-second issuance availability and +15-minute promptness
window are validated. Exact numeric errors are copied and consistency-checked,
not substituted with newly scored outcomes. Browser floating-point checks use
1e-12 absolute/relative tolerance; original validation remains the Python authority.
Browser timestamp comparisons have millisecond precision; original evidence retains
Python microseconds. Publication must use the original validators first.

Evaluation metrics are the evaluator's **all-retained-evidence** report at the
explicit cutoff, with each cohort's earliest retained target endpoint shown. There
is no selected weekly/monthly subset, new aggregation rule, ranking or recipe-epoch
filter. The existing report pools recipe fingerprints within each market/cohort;
latest observations expose their own recipe hash. Accuracy uses strict sign and
zero abstentions, distinct from historical trading's 1e-12 threshold. Model sample
counts are common; null denominators remain undefined. Missing primary opportunity
counts remain null if the monitoring grid is unknown and are undefined for other
cohorts. Invalid evidence stops export rather than disappearing from the sample.
Every comparison below 100 matched observations is labelled preliminary.

`generated_at` must follow `as_of` by at most five minutes, and future exports beyond
a one-minute device-clock tolerance are rejected. A snapshot older than **20
minutes** by its cutoff is marked stale, even if its HTTP fetch just succeeded.
This is publication freshness: forecasts are still issued every four hours.
Expired forecast targets are labelled mature/settling rather than still current.

The adapter uses an optional build-time public variable:
`NEXT_PUBLIC_FORWARD_SNAPSHOT_URL`. It accepts same-origin paths or HTTPS URLs,
fetches with no credentials/no cache, validates the entire snapshot, and updates
on each five-minute/manual/visibility refresh. The variable is unset by default.
No fixture is imported by application code or copied into public assets.

## Local candidate exporter and proposed publishing procedure

`web/scripts/public_forward_export.py` prepares a private JSON candidate using
existing `report`, `load_prediction`, `load_outcome`, `journals` and `classify`
functions. It never calls `score`, `record_forward`, model fitting, provider HTTP or
database setup. It reuses retained scores and evaluator metrics, preserves frozen
cohorts, checks matched identities, and compares reports before/after projection
at one cutoff to reject changing evidence. It refuses invalid/partial outcomes,
missing directories or an output under any input directory. The allowlist excludes
private paths, raw journals, source candles, training data, configuration, evidence
filenames and operational diagnostics.

The output uses a private same-directory temporary file, flush/fsync, atomic replace
and directory fsync. This is candidate preparation, not public deployment. It was
unit-tested with synthetic data only; it has not been run on genuine evidence or
installed on Lightsail. Review the first genuine candidate before public use.

Example **local-only** preparation after obtaining an authorised, private, stable
copy of the three evidence directories (replace the input placeholders):

```sh
# From the repository root, using the existing locked Python environment:
mkdir -p artifacts/public-preview
.venv/bin/python web/scripts/public_forward_export.py \
  --records /path/to/private-copy/forward-predictions \
  --outcomes /path/to/private-copy/forward-outcomes \
  --operations /path/to/private-copy/forward-operations \
  --output artifacts/public-preview/forward-v1.json
cd web
node --import tsx scripts/validate-forward.ts ../artifacts/public-preview/forward-v1.json
```

The input copy is not a public artifact. The candidate remains private until
approved; never copy raw evidence directories into `web/public` or `out`.

**Exact recommended next deployment scope, after owner review:**

1. Approve the contract, first genuine candidate, public destination and operating
   budget. Use the matching locked runtime, protocol and evaluator implementation.
2. Separately authorise installing only the reviewed exporter as an independent,
   low-priority, bounded job reading retained evidence and writing a separate staging
   area. Do not change the collector/scorer or expose the database. Start with a
   ten-minute export schedule; it catches four-hour issuances and later scores while
   remaining within the twenty-minute freshness budget. A five-minute schedule is
   possible only after measuring the full evidence-scan cost.
3. Validate the candidate, then atomically replace one public `forward-v1.json` on
   the owner's approved existing static host. Serve `application/json`, a cache
   lifetime no longer than 60 seconds, and CORS for the website origin if cross-origin.
   Public hosting must not expose staging files, private evidence or directory lists.
   No new port, DNS change or S3 configuration is assumed or performed here.
4. Set `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` to that public URL, rebuild the static
   website and deploy only under separate authorisation. Check both markets, all
   cohorts, undefined metrics, target expiry, failure/staleness and subsequent updates.
5. If export fails, leave the previous public file with its original times. Observe
   the failure privately; do not advance `generated_at` or serve a synthetic fallback.
   Roll back the connection by removing the public URL and rebuilding, or by restoring
   a previously approved file whose original timestamp remains visible as stale.

Operational impact: repeated retained-file validation and aggregation consume CPU,
RAM and disk reads proportional to evidence/journal history (the candidate exporter
currently performs two report scans plus projection validation). Measure wall time
and memory on an approved copy before choosing production limits. Use non-overlap
and bounded execution in the later job wrapper. Atomic replacement prevents partial
HTTP JSON. The exporter needs evidence read permission and separate staging write
permission only, no database credentials or cloud administration privileges.
Browser demand goes to the static host, not the production DB. No such job or
publishing mechanism was activated in this stage.

## Research and editorial presentation

The Burrow and The Dig can use a 1,512px outer analytical area on desktop; articles
retain their existing reading widths. Existing charcoal, forest-green and sand,
mascot, navigation, focus states and reduced-motion rules remain. No new animation
was added.

The Field Notes index selects the first article from the existing descending eligible
sequence. Its number, title and decorative illustration labels derive from that
article. Local preview features **004 — One Minute Can Change a Backtest**, followed
by 003, 002, 001. Home's two-note feature uses the same newest-first collection.
Production still requires Published metadata **and** an exact SHA-256 approval.
No article was approved or edited, and drafts remain absent from the static export.

The Dig adds a prominent Ridge explanation: linear weighted prediction, squared
coefficient penalty and the historical ridge-analysis origin of its name; train-only
scaling/model fitting;
five exact features; close-to-close log-return target; frozen long/cash threshold;
continuous holding versus turnover; timing and per-side costs; independent Cash and
Buy & Hold accounts; limits on generalisation. A semantic four-step diagram preserves
12:00 candle close → assumed 12:01 availability → sign decision → strictly next
12:02 minute execution. Glossary entries explain drawdown, turnover, basis points,
slippage and Sharpe without inventing a Sharpe result. It links the E.5g report and
retains publication-gated relevant Field Notes. All six result rows are unchanged.
The [scikit-learn Ridge documentation](https://scikit-learn.org/stable/modules/linear_model.html#ridge-regression-and-classification)
and local Stage 2A/2B/3A definitions informed the explanation. The name’s origin
was checked against Roger W. Hoerl’s [historical account](https://doi.org/10.1080/00401706.2020.1742207),
which derives regression from earlier response-surface ridge analysis; the diagonal
matrix adjustment is not used as a false etymology.

## Verification and limitations

- Real Binance adapter checks succeeded for both symbols and all four ranges:
  289/337/721/541 observations respectively, no gaps in those responses, final candle
  correctly provisional. These were live verification requests, not saved fixtures.
- Browser checks verified genuine BTC and ETH prices, range/mode changes, keyboard
  candle inspection, manual refresh and the honest unavailable forecast state.
- TypeScript, ESLint, Prettier, production static build and **56 frontend tests** passed; tests cover
  malformed market responses, ordering/boundaries/gaps, forecast consistency and
  maturity, visibility/manual/timeout cleanup, publication gates and all six exact
  E.5g account rows. Production output is scanned for draft and synthetic-fixture leaks.
- **Six synthetic Python tests**, Ruff lint and Ruff format checks passed. Tests cover allowlist projection, compatibility with the browser
  validator, private candidate permissions, invalid/partial evidence, mismatched
  samples, failed serialisation and missing inputs. No genuine evidence was scored
  or fitted in testing. No broad scientific test suite or historical replay was run.
- Desktop checks at 1440px and mobile checks at 390px/320px passed on the inspected
  Burrow, Dig and Field Notes views, with no document-width overflow. Development
  features 004; the separate static production preview shows the publication-pending
  empty state. The production Burrow also loaded genuine data. Crosshair, keyboard
  candle selection, manual refresh and chart/range controls were exercised. Final
  browser warning/error logs were empty. Reduced-motion CSS remains in place;
  OS preference emulation and a formal screen-reader audit were not performed.
- `git diff --check`, relative documentation links and byte-for-byte prompt archive
  comparison passed. No scientific source, original tests, frozen evidence, article
  source, publication approval or historical display-value file changed.
- The public forecast connection remains deliberately absent. Schema compatibility
  is verified, but the first genuine candidate and publication procedure still need
  review and a separately authorised deployment. No current accuracy claim is made.

The complete request is archived [verbatim](../prompts/stage-05-web/003-market-dashboard-and-research-explanations.md).

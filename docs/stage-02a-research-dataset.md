# Stage 2A — Reproducible research dataset and causal features

Implemented for review. This is an offline research foundation, with no ML model,
strategy, execution simulation, live prediction or database mutation. It uses the
existing Stage 1B.3 export, rather than the refreshed database. No new dependency
is needed: `csv`, `Decimal`, `math` and `statistics` are sufficient for this dataset.

## Run and reproduce

From the repository root, without `.env`, database connectivity or provider access:

```sh
uv run --locked badger prepare-research \
  --output artifacts/research/stage-2a-v1 \
  --acknowledge-incomplete

# Use a new output directory for every reproduction; existing outputs are refused.
uv run --locked badger prepare-research \
  --output artifacts/research/stage-2a-v1-reproduction \
  --acknowledge-incomplete
```

The default source is `artifacts/exports/binance-4h-history-v1/`. `--source` can
locate a byte-identical copy; it cannot authorize a different dataset.
`--acknowledge-incomplete` is mandatory even though the original exporter also
recorded acknowledgement. `--settling-seconds` defaults to 60; this increment
accepts integer delays from 0 through 14,399 seconds, strictly below the single
prediction horizon. The default is a research assumption, not provider finality.

Outputs are `research.csv` and `manifest.json`, under gitignored local storage.
A new directory is exclusively reserved; `.partial` files precede publication and
the final manifest is published last. A failed run may leave an unfinished output
directory; inspect it and select a new directory. Neither existing frozen inputs
nor earlier research outputs are overwritten. Files require off-machine backup;
this stage does not introduce one.

## Frozen input verification

`frozen.py` separates input validation from all feature calculations. It hashes
the exact bytes subsequently parsed and checks both hashes against pins reviewed
from the Stage 1B.3 artifact and corroborated by the Stage 1C.2 preservation audit:

```text
CSV:      e6052b8cca7bca00999ca4d7429af67db019c8ef261fa2b499f0fd6774dcd13b
Manifest: a78d34256d3bcd789e6cc19a2807f432d1ffa1a73ecc81b5ea16b3859759a98a
```

The manifest's own CSV hash must agree. Changing CSV bytes and recomputing only
its manifest hash cannot bypass the pins. Alternate pins are available only as
Python arguments for synthetic fixtures; the CLI has no override. A future
source release requires an explicit reviewed change, never silent substitution.

Validation covers schema version and exact CSV header; Binance Spot BTCUSDT and
ETHUSDT market/asset identities; native 14,400-second intervals; aware UTC grid
alignment; strictly increasing `(symbol, open_time)` identities; range, versions,
closed-before-observed provenance and shared exact economic constraints. All prices
and volumes are parsed directly to `Decimal`. Prices remain exact in output;
logarithms and volume ratios use Decimal arithmetic with operand-dependent
precision plus 32 guard digits, then convert derived results to binary floats.
CSV floats use 17 significant digits. No intermediate price cast to float occurs.

The full expected UTC grid is compared to CSV identities, manifest counts and
first/last observations. Missing identities must agree exactly with the union of
recorded source absences and excluded irregular-close rows. Unrecognized anomaly
policies, unresolved imports, unreadable evidence, duplicates, unsorted rows,
unexpected timestamps and unrecorded gaps fail preparation.

Actual verification: **39,910 candles**, 19,955 per market, starting
2017-08-17 04:00 UTC and ending with the 2026-09-30 20:00 UTC candle. The manifest
range ends at 2026-10-01 00:00 UTC exclusively. Each market has 19,991 expected
identities, **17 missing source identities plus 19 excluded irregular-close
observations**, totalling 36 gaps. There are no unexpected timestamps, duplicates
or additional discontinuities. Both input hashes remain unchanged after research.

## Features, target and exact availability

Let `t` identify the latest completed native candle by its UTC **opening** time,
`C[t]` be its close, `V[t]` its base volume, and `r[t] = ln(C[t]/C[t-1])`.
Subscripts advance by exactly four hours, never by adjacent CSV positions.

| Output feature | Definition | Required completed candles |
| --- | --- | --- |
| `log_return_4h` | `ln(C[t]/C[t-1])` | `t-1 .. t` |
| `log_return_12h` | `ln(C[t]/C[t-3])` | Every identity `t-3 .. t` |
| `log_return_24h` | `ln(C[t]/C[t-6])` | Every identity `t-6 .. t` |
| `realised_volatility_24h` | Square root of the sum of the six squared returns `r[t-5] .. r[t]` | `t-6 .. t` |
| `relative_base_volume` | `V[t] / mean(V[t-6], ..., V[t-1])` | `t-6 .. t` |

All five features become eligible at **`t + 4h + settling_delay`**. The volatility
is an unannualised realised variation measure, without demeaning or a sample
standard-deviation denominator. Volume compares the just-completed candle with
six preceding candles, excluding the current candle from its denominator. A zero
historical-volume denominator excludes the row; zero current volume with a
positive historical denominator is valid. No optional hour feature is added.

The sole target, `target_log_return_4h`, is **`ln(C[t+1]/C[t])`**. Both identities
must exist exactly four hours apart. Its endpoint close is `t + 8h`; the label
becomes eligible at **`t + 8h + settling_delay`**. Features use only `t-6 .. t`;
only the label reads `t+1`. Full rows conservatively require all eight identities
`t-6 .. t+1`, with no missing or flagged candles anywhere in that window.

For a candle opening at 08:00 UTC, the default feature time is 12:01 UTC and the
label endpoint is 16:00 UTC, available at 16:01. `close_time` means the exclusive
interval boundary, not the provider's last millisecond. The artifact separately
records source open, close boundary, feature availability, target open, target
close boundary and target availability, retaining market identity and exact current
close/base volume/version.

**This target is predictive research, not an executable return.** The 12:00 close
has already occurred when the 12:01 signal is eligible. Stage 2C must independently
model order submission, latency, fills and costs; it cannot assume a fill at that
12:00 close. These availability times describe a hypothetical market-time policy.
The frozen observations were acquired in 2026 and do not reconstruct historical
provider publication, revisions or actual historical signal availability.

## Gap and anomaly policy

No forward-fill, interpolation, synthetic prices, synthetic zero-volume bars or
timestamp repair is performed. Features and labels look up explicit timestamps.
After a gap, a row becomes eligible only after its entire required window is
present again. Rolling warm-up at the initial source boundary is counted
separately from recovery following a missing candle.

The source manifest's irregular-close exclusions remain absent and invalidate
all spanning windows. In addition, the existing Stage 1B.3 investigation found
that **BTCUSDT 2017-09-06 20:00 UTC** has normal native boundaries but economics
matching the sole returned hour, 23:00. Stage 2A flags this retained candle and
excludes every feature/target window using it. The manifest's `known_anomalies`
registry links that prior evidence; `exclusion_audit` lists each dropped source
identity, primary reason, missing in-range identities and overlapping known flags.
Eligible rows have `known_anomaly=false`, meaning no *registered* anomaly in the
required window, not proof of error-free trading data.

This extra retained-candle flag is BTC-specific because the cited hourly comparison
was BTC-specific. ETH's manifest gaps and irregular-close exclusions are enforced,
but absence of the same confirmed flag is not proof of ETH continuity within that
bar. The policy is fixed before inspecting target results. There is no new Field
Note: this applies the existing documented discovery rather than establishing a new
one. Normally bounded candles elsewhere can still conceal unobserved interruptions.

## Chronological partitions and leakage controls

Both markets use the same **feature-availability clock** and half-open boundaries:

| Partition | Feature availability (UTC) |
| --- | --- |
| Train | Available eligible source history before 2024-01-01 00:00 |
| Validation | 2024-01-01 00:00 through 2025-01-01 00:00 exclusive |
| Test | 2025-01-01 00:00 through 2026-10-01 00:00 exclusive |

Additionally, **target availability must be strictly before the partition end**.
For example, a December 31 16:00 candle gives a 20:01 signal but its label becomes
available January 1 00:01, so it is purged. A December 31 20:00 candle gives a
January 1 00:01 signal and belongs to the new partition. Its backward feature
context may come from the prior partition; that is available past data, not leakage.
At the default delay, the final retained test row opens September 30, 2026 at
12:00, signals at 16:01 and has its target available at 20:01.

Rows remain ordered by market and time. There is no shuffling, scaling, clipping,
imputation, global normalisation, preprocessing fit or tuned feature selection.
Two no-skill references are retained: constant zero and one mean training target
per market. Training means are applied only to validation/test rows; their training
prediction cells are empty because a whole-training-set mean would use later labels
for earlier training observations. Baselines are not scored here. Later modelling
must fit any preprocessing solely on training rows.

Test labels are retained for later reproducible evaluation, but **test distribution
summaries and scores are withheld**. Preparation inspects structural integrity and
eligibility, not test performance. No choice is tuned against holdout results.
The holdout is a research protocol rather than an access-control mechanism: future
work must continue to preserve it.

## Actual counts and sanity checks

| Result | BTCUSDT | ETHUSDT |
| --- | ---: | ---: |
| Source CSV rows | 19,955 | 19,955 |
| Eligible feature/target rows | 19,804 | 19,805 |
| Training | 13,782 | 13,783 |
| Validation | 2,195 | 2,195 |
| Test | 3,827 | 3,827 |
| Initial rolling warm-up dropped | 6 | 6 |
| Missing-candle windows dropped | 140 | 140 |
| Additional known-anomaly windows dropped | 1 | 0 |
| Partition-boundary labels dropped | 3 | 3 |
| Feature availability outside partition range | 1 | 1 |
| Other endpoint / zero-volume-history drops | 0 | 0 |

Total eligible: **39,609**. Counts are mutually exclusive and reconcile to every
source CSV row. The 36 absent identities per market are not source CSV rows and
are not counted again as dropped observations. Most windows using the additional
BTC anomaly already cross manifest gaps; the extra flag removes one more row.
The audit retains overlaps. Drop precedence is: outside split range, label crossing
split end, initial warm-up, missing source-end target, missing in-range candle,
known anomaly, zero historical volume. This makes the last two source observations
range/boundary exclusions rather than double-counting a missing endpoint.

Target summaries below use dimensionless log returns. Standard deviations use the
population denominator. Full precision is retained in the manifest.

| Market / partition | Count | Mean | Std deviation | Minimum | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| BTC train | 13,782 | 0.000154079 | 0.016088139 | -0.229365819 | 0.271623711 |
| BTC validation | 2,195 | 0.000364770 | 0.011084271 | -0.083710909 | 0.069280429 |
| ETH train | 13,783 | 0.000107082 | 0.019868500 | -0.249468087 | 0.274701764 |
| ETH validation | 2,195 | 0.000175658 | 0.013561051 | -0.150715305 | 0.097781192 |

No inference of predictability, profitability or executable performance follows
from these descriptive summaries. Test distributions remain uninspected.

## Reproducibility, checks and file inventory

Generated CSV SHA-256:

```text
04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8
```

Implementation version: `stage-2a-v1`. The manifest records source ID and both
hashes, original source-selection policy and coverage, definitions, settling delay,
gap/anomaly policies, split clock/boundaries, per-market counts and exclusion audit,
training reference constants, permitted summaries, implementation module hashes,
Python version and output hash. There is no creation timestamp or output path in
the manifest, so unchanged code/runtime/input/configuration reproduce identical
CSV and manifest bytes. Floating math portability across Python/platform versions
is not promised; the runtime and implementation fingerprints make changes visible.

The two actual runs above produced byte-identical CSV **and** manifest files.
The manifest SHA-256 is
`a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e`.
`artifacts/research/stage-2a-verification.json` retains the reproduction checks,
unchanged source hashes, matching implementation fingerprints and verbatim prompt
check. The disposable test container was stopped and removed after validation.

Validation: **405 pytest tests passed**, including all **173 PostgreSQL integration
cases** on a separate disposable PostgreSQL 17 server, plus 52 new synthetic research
and CLI cases. Ruff lint and formatting pass. Tests cover hand-calculated returns,
volatility and volume, precision, future-value perturbation, exact target alignment,
missing grids, anomalies, warm-up, zero denominators, shared chronological boundaries,
label purging, train-only reference fitting, withheld holdout summaries, deterministic
files, overwrite refusal, source preservation, strict schemas and altered inputs.
No provider requests or market-data database access occurred during preparation.

Added:

- `src/backtest_badger/frozen.py`: source integrity checks and exact parsing.
- `src/backtest_badger/features.py`: causal rows, splits, references and artifact publication.
- `tests/test_features.py`: synthetic checks.
- This guide and `prompts/stage-02-research/001-research-dataset-and-features.md`.

Modified: CLI, README, architecture and roadmap. The prompt is archived verbatim.
No schema, dependency, existing frozen artifact or Field Note was changed.

Remaining limits are the incomplete single-provider history, uncertain within-bar
continuity and publication timing, retrospective canonical versions, a deliberately
small fixed feature set, shared market conditions across BTC/ETH, and no execution
or cost model. Local artifacts lack durable backup. Stage 2A stops here for review;
modelling and Stage 2C execution assumptions require separate work.

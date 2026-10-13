# Stage 2B — Predictive baselines and chronological evaluation

Implemented for review on 2026-10-14. The fixed question is whether recent returns,
realised volatility and volume predict the next four-hour close-to-close log return
better than zero and training-mean forecasts. This measures statistical
predictability; it does not measure trading profitability.

## Run and reproduce

```sh
uv run --locked badger evaluate-models \
  --source artifacts/research/stage-2a-v1 \
  --output artifacts/experiments/stage-2b-v1

uv run --locked badger evaluate-models \
  --source artifacts/research/stage-2a-v1 \
  --output artifacts/experiments/stage-2b-v1-reproduction
```

These directories already exist locally. Choose a new directory for another run;
existing destinations are refused. The command is offline and does not load
application settings or connect to PostgreSQL or Binance. `--source` locates an
identical copy of the reviewed artifact; no CLI hash, feature or parameter
overrides are offered. `artifacts/` is gitignored. Publication reserves a new
directory and writes through `.partial` files, with the final manifest last.
A failed write may leave an incomplete directory; use a new destination after
investigating it. Local artifacts still require durable backup.

## Input integrity and holdout discipline

`model_data.py` validates input independently of fitting in `evaluation.py`.
The exact bytes subsequently parsed must match both pinned hashes:

```text
Stage 2A research.csv:
04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8
Stage 2A manifest.json:
a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e
```

It checks the exact CSV schema/order, manifest feature and target definitions,
Binance Spot BTCUSDT/ETHUSDT identities, unique chronological market/open-time
pairs, finite model features, finite training/validation labels, all feature/label
timestamps, the recorded gap/anomaly exclusion policy, forbidden windows and
reviewed partition counts. It uses the existing manifest and Stage 2A definitions;
it neither recreates features nor reconstructs the frozen source.

The feature order is fixed: `log_return_4h`, `log_return_12h`, `log_return_24h`,
`realised_volatility_24h`, `relative_base_volume`. The target remains
`target_log_return_4h = ln(C[t+1]/C[t])`.

Stage 2A's feature-availability clock and strict label purging are preserved:
features are available at opening time + 4h + 60 seconds; labels at opening time
+ 8h + 60 seconds. Labels must be available strictly before their partition end.
Thus an opening time of December 31 at 20:00 belongs to the following year's
partition. No rows are randomly split, shuffled between partitions or refitted
using validation data.

| Market | Train, before 2024 | Validation, 2024 | Test, Jan 2025–Sep 2026 |
| --- | ---: | ---: | ---: |
| BTCUSDT | 13,782 | 2,195 | 3,827 withheld |
| ETHUSDT | 13,783 | 2,195 | 3,827 withheld |

Whole-file hashing and CSV tokenisation necessarily read test bytes. Structural
checks and feature finiteness checks cover the full artifact, but test target
cells and stored baseline forecasts are never retrieved for numerical conversion,
returned to modelling, summarised or scored. The loader returns only training and
validation observations. No test predictions are generated. Sentinel and access-
guard tests enforce this distinction. Test counts are existing structural metadata,
not performance evidence. Stage 2A and the original frozen export hashes were
verified unchanged after the experiment.

## Fixed models and dependencies

Each market gets independent fresh estimators; neither features nor labels are
pooled across markets. All configurations below were fixed before viewing results.
Each estimator was fitted once per run; the second identical run checks
reproducibility and does not select or tune models. No quarterly exploratory
breakdown or hyperparameter search was added.

| Identifier | Configuration |
| --- | --- |
| `zero` | Constant 0; no fitted parameter |
| `training_mean` | Arithmetic mean of that market's training labels only |
| `ridge` | `Pipeline(StandardScaler(), Ridge(alpha=1.0, solver="svd"))`; centring, scaling and coefficients fitted on training only; intercept enabled |
| `gradient_boosting` | `GradientBoostingRegressor`: squared-error loss, 100 trees, learning rate 0.03, depth 2, minimum 100 samples per leaf, subsample 1.0, random state 42, `n_iter_no_change=None`; no preprocessing |

Shallow trees, large leaves and shrinkage deliberately limit flexibility. Early
stopping is disabled, so no internal random validation partition is created. Full
estimator/scaler parameters, including unchanged library defaults, are recorded
in the manifest. Fitted scaler means, scales and sample counts are also retained.
The choices follow the official [Ridge documentation](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html)
and [gradient boosting documentation](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html).

Added NumPy and scikit-learn through uv. The lockfile resolves NumPy **2.5.4** and
scikit-learn **1.9.1**, with SciPy 1.18.1, joblib 1.6.0, threadpoolctl 3.7.0,
cloudpickle 3.1.2 and narwhals 2.27.1 transitively. Actual execution used Python
3.12.13 on macOS ARM64. Numerical fitting/prediction runs under a one-thread limit.
Training means are 0.0001540786852149574 for BTC and approximately
0.0001070816489564068 for ETH; neither includes validation labels.

## Metric definitions

Predictions, targets, MAE and RMSE are **dimensionless log returns**.
MAE is mean absolute error; RMSE is the square root of mean squared error and
weights large misses more strongly. Relative error improvement is
`1 - model_error / baseline_error`, separately for each metric and baseline:
positive is better, negative is deterioration, and zero baseline error is undefined.

The reported skill score is `1 - model_MSE / training_mean_forecast_MSE`, with both
errors evaluated on validation. It is explicitly a training-mean-relative skill
score, not ordinary R² against the validation sample mean. A zero denominator
returns JSON `null` / Markdown `undefined`.

Pearson correlation measures linear co-movement, not error magnitude or sign
accuracy. It is undefined with fewer than two observations or when either vector's
population standard deviation is at most `1e-12 * max(1, max(abs(vector)))`.
This numerical convention rejects constant and near-constant series.

Directional accuracy counts sign matches only where `abs(prediction) > 1e-12`;
smaller forecasts abstain. Coverage is that fraction of all validation rows.
An exactly zero realised target counts as an incorrect direction for a nonzero
forecast. No nonzero forecasts means undefined directional accuracy. A constant
positive training mean has defined sign accuracy (the positive-return frequency)
but undefined correlation. These conventions were fixed before scoring and are
not optimised trading thresholds.

## Actual 2024 validation results

| Market | Model | MAE | RMSE | Skill vs mean | Pearson | Direction | Coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | zero | 0.00747388 | 0.01109027 | -0.00072142 | undefined | undefined | 0.000% |
| BTCUSDT | training_mean | 0.00746805 | 0.01108627 | 0.00000000 | undefined | 52.392% | 100.000% |
| BTCUSDT | ridge | 0.00744768 | 0.01107059 | 0.00282760 | 0.05751800 | 52.027% | 100.000% |
| BTCUSDT | gradient_boosting | 0.00747445 | 0.01108611 | 0.00002902 | 0.02710184 | 52.027% | 100.000% |
| ETHUSDT | zero | 0.00904873 | 0.01356219 | -0.00014221 | undefined | undefined | 0.000% |
| ETHUSDT | training_mean | 0.00904732 | 0.01356122 | 0.00000000 | undefined | 50.752% | 100.000% |
| ETHUSDT | ridge | 0.00901798 | 0.01354070 | 0.00302400 | 0.05874273 | 52.620% | 100.000% |
| ETHUSDT | gradient_boosting | 0.00902689 | 0.01346292 | 0.01444558 | 0.14063311 | 47.517% | 100.000% |

Relative improvements (percent):

| Market | Model | MAE vs zero | MAE vs mean | RMSE vs zero | RMSE vs mean |
| --- | --- | ---: | ---: | ---: | ---: |
| BTCUSDT | training_mean | +0.078% | +0.000% | +0.036% | +0.000% |
| BTCUSDT | ridge | +0.351% | +0.273% | +0.177% | +0.141% |
| BTCUSDT | gradient_boosting | -0.008% | -0.086% | +0.038% | +0.001% |
| ETHUSDT | training_mean | +0.016% | +0.000% | +0.007% | +0.000% |
| ETHUSDT | ridge | +0.340% | +0.324% | +0.158% | +0.151% |
| ETHUSDT | gradient_boosting | +0.241% | +0.226% | +0.732% | +0.725% |

Ridge has small MAE and RMSE improvements against both baselines in both markets.
BTC boosting worsens MAE by 0.086% versus the training mean and improves RMSE by
only 0.00145%; it does not consistently outperform that simple baseline.
ETH boosting has the largest RMSE improvement (0.725% versus the training mean),
with Pearson correlation 0.141, yet its direction accuracy is 47.517%, below the
constant-positive training mean's 50.752%. BTC Ridge's direction accuracy is also
below its training-mean baseline despite better regression errors.

These discrepancies show why correlation, regression error and direction accuracy
must be reported separately. A model can reduce large numerical errors while
getting more signs wrong. The comparison establishes only the measured differences
on this validation sample. It does not establish reliable statistical predictability,
significance or economic usefulness, and no model is promoted or selected for use.

Returns are noisy and conditions change. Both markets share conditions and are
correlated; their results are not independent confirmations. The single-provider
observations were collected retrospectively and retain known gaps/anomaly exclusions.
Results describe one fixed 2024 validation period. Close-to-close targets start
before the assumed feature eligibility time, so their returns are not executable
fills. Fees, spreads, slippage, latency and all trading mechanics remain unmodelled.
No ordinary accuracy difference is presented as significant without a method that
accounts for time dependence. No profitability conclusion or Field Note publication
is made from this small experiment.

## Artifacts and reproducibility

Both `artifacts/experiments/stage-2b-v1/` and
`artifacts/experiments/stage-2b-v1-reproduction/` contain:

- `validation_predictions.csv`: **17,560 rows**, four forecasts for each of 4,390
  validation observations. Market identity, source opening time, feature availability,
  model identifier, prediction and source research CSV hash; no realised targets.
- `manifest.json`: input hashes, ordered features, target/split definitions,
  train/validation counts, complete model parameters, scaler audit, preprocessing,
  runtime versions, random seed, implementation hashes, validation metrics and
  hashes of the CSV and summary. No creation time or destination-dependent content.
- `summary.md`: compact comparison and metric conventions with limitations.

Output SHA-256 values (identical in both directories):

```text
validation_predictions.csv:
e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674
manifest.json:
af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581
summary.md:
fea8dbb5218b6e2d530ff7a78a3ad47c22f9fa89d572f754851be02e3e769efa
```

The two separate CLI processes produced byte-identical predictions, metrics,
manifests and summaries. Maximum absolute prediction difference was **0**.
The defined numerical tolerance is `rtol=1e-10, atol=1e-12` with the same locked
runtime and configuration. Cross-version/platform identity is not promised.
`artifacts/experiments/stage-2b-verification.json` records the comparison, output
hashes, unchanged Stage 2A and frozen-export hashes, matching implementation
fingerprints, lockfile fingerprint and exact prompt archival check.

## Validation and changed files

`uv run --locked pytest -q`: **274 passed, 173 skipped**, including **42 new
synthetic Stage 2B cases**. The skipped cases require an explicitly configured
isolated PostgreSQL test server; none was configured for this offline stage.
Ruff lint, Ruff formatting checks and `git diff --check` passed.

Focused tests cover ordered features, exact calendar selection and purged boundary
labels, train-only scaling/fitting and baseline values, cross-market independence,
validation-label perturbations, opaque/guarded test outcomes, hand-calculated metrics,
constant/near-constant edge cases, nonfinite/missing inputs, schema and hash rejection,
repeatable fitting and artifact bytes, provenance hashes, overwrite refusal and
CLI operation without configuration or database access. Tests use no live Binance
connectivity or real holdout observations.

Added `model_data.py`, `evaluation.py`, `tests/test_evaluation.py`, this guide and
the verbatim prompt at `prompts/stage-02-research/002-predictive-baselines.md`.
Updated the CLI, `pyproject.toml`, `uv.lock`, README, architecture and roadmap.
Stage 2A code/artifacts, ingestion infrastructure and the development database were
not modified. No commit or push was made. Stage 2B ends here; Stage 2C is not begun.

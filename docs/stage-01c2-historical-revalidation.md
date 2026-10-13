# Stage 1C.2 — Controlled historical revalidation

Implemented for Binance Spot BTCUSDT and ETHUSDT, native UTC 4h observations.
Review acquires evidence and reads PostgreSQL without changing candles or their
watermarks. A separate, explicitly approved apply replays that evidence through
the existing atomic version-preserving writer. No migration or dependency was added.

## Commands and approval

Run from the repository root with the existing local development configuration:

```sh
uv run --locked --env-file .env badger revalidate-history \
  --symbol BTCUSDT --interval 4h \
  --start 2026-09-01T00:00:00Z --end 2026-09-03T00:00:00Z

# Inspect both the generated JSON and its adjacent .txt summary first.
uv run --locked --env-file .env badger apply-revalidation \
  --plan artifacts/revalidation/plans/<plan-id>.json --approve-changes

# Historical anomaly investigation; this range currently yields a blocked plan.
uv run --locked --env-file .env badger revalidate-history \
  --symbol BTCUSDT --interval 4h \
  --start 2017-09-06T00:00:00Z --end 2017-09-07T00:00:00Z
```

Both bounds are required, aware UTC, exactly aligned to 4h; the end is exclusive.
A nonempty operation spans at most 30 days (180 identities). The whole range must
have closed and settled for 60 seconds at the fixed review start time. The existing
public REST downloader, request parameters, clock probe, retry/throttle handling,
body limits and strict millisecond/Decimal parser are reused.

One request with `limit=1000` accommodates the entire bounded range. There is no
historical pagination, scheduler or automatic rescan. A missing identity, empty
response, invalid row, duplicate, out-of-order identity or out-of-range row blocks
the **whole plan**. Valid neighbours are still compared for investigation. The
operator can deliberately review a narrower complete range; editing away a bad
row in a plan does not make its original response applicable.

`ready_for_approval` means validation completed, not that a person approved it.
The apply flag explicitly approves **all proposed observations in that plan's
range**, including valid missing identities and confirmation-watermark advances.
There is no implicit approval, per-row selection flag or automatic retry with fresh
source data. A blocked plan is never applicable. Review exits 0 for a complete
review, 1 for blocked/failed work; apply exits 0 only on a confirmed commit with
its final report saved. CLI usage/configuration errors retain their existing codes.

## Comparison and source limitations

Each expected identity has one classification: missing from the provider, valid
but missing from PostgreSQL, economically identical, economically changed, or
invalid. Row-level errors also retain unexpected/unidentifiable observations.
The shared REST inspection function collects every row's diagnostic while ordinary
`parse_page` still rejects an entire malformed page.

All nine economic fields use exact Decimal/integer equality: four prices, four
volumes and trade count. Changes include old and proposed values, changed fields,
existing version, original/proposed source URLs and hashes, observation timestamps,
recording time and confirmation watermark. Archive/REST disagreements, price
changes of at least 5%, widespread disagreements and stale/equal-time changes
receive investigation warnings. These warnings do not establish economic truth.

A newly acquired historical observation describes what this endpoint returned at
acquisition time. It cannot establish what Binance originally published at market
time. Normal native boundaries do not establish uninterrupted trading within a
bar. Sources from the same provider can share defects. This stage compares REST
with accepted canonical values; it performs no hourly resampling, timestamp repair,
synthetic insertion or independent economic adjudication.

## Local evidence and integrity

All new artifacts live under ignored `artifacts/revalidation/`:

- `raw/<sha256>.json`: exact response bytes, including clock/error/invalid evidence.
- `plans/<id>.json` and `.txt`: selection, acquisition metadata, parser version,
  implementation hashes, request URLs, response paths/hashes/headers, exact proposed
  observations, reviewed database rows, classifications, warnings, prior historical
  source diagnostics, status and reviewed-content fingerprint.
- `applications/<id>.json`: immutable-plan reference/fingerprint, explicit approval
  time, selected range/source, review counters, committed counts, conflicts/stale
  identities and commit/rollback outcome for each application attempt.

The fingerprint is SHA-256 over canonical, sorted JSON excluding only the
fingerprint field. It detects accidental alteration; an editable JSON file and a
recomputable hash are **not cryptographic authorization**. The local operator's
explicit CLI approval, retained-byte validation and locked database comparison
are all required. This is not an adversarial multi-user approval service.

Before opening the apply database connection, the implementation checks bounded
plan size, unique JSON keys, schema/status/interval, parser version and exact hashes
of the REST, persistence and revalidation modules. It verifies original request
URLs against selection, complete HTTP 200 bodies, original SHA-256 and optional
Content-Length, UTC acquisition chronology, the retained clock check and review-time
eligibility. It reparses the exact selected payload and reconstructs all comparisons;
the entire ordered grid and all proposed changes must match the review. It performs
**no HTTP requests** and never replaces acquisition time with apply time.

Implementation changes conservatively require a fresh review, even when an edit
might be behavior-preserving. Absolute raw paths require retaining files in place
or generating a new review after relocation. Local evidence requires durable backup;
this stage adds no storage service. SHA-256 identifies received bytes and does not
provide a provider signature or independently attest to the operator's clock.

## Atomic persistence and stale reviews

The explicit `historical-revalidation` batch mode is separate from unchanged
`backfill` and `recent-refresh` modes. Backfill still rejects revisions. Ordinary
recent refresh retains at most seven days of revision authority; an older catch-up
start cannot widen it. Neither command can select historical authority.

All selected observations validate before the transaction begins. One bounded
READ COMMITTED transaction processes identities in deterministic sorted order.
`INSERT ... ON CONFLICT DO NOTHING` serializes absent-row races; a separate
`SELECT ... FOR UPDATE` locks an existing winner. The full locked row must equal
its reviewed state, including version, all economic values, provenance, recording
and observation times, and watermark. A reviewed absence must still be absent.
Competing inserts, deletions, revisions and even intervening confirmation-watermark
changes invalidate the plan and roll back the whole batch. No locks surround HTTP.

For a changed observation strictly newer than the accepted watermark, the shared
SQL copies the complete old row into `candle_revision`, replaces current values
and provenance, and increments the version. A → B → A preserves versions 1, 2 and 3.
Older changes are stale; equal-time changes conflict. Either aborts the complete
batch, including earlier inserts, revisions and watermark updates.

Identical approved observations create no revision and preserve the original
version, observation/recording times and source provenance. As with existing
writers, their watermark advances only if the reviewed response is newer. This
prevents a delayed changed response from superseding a newer confirmation. Review
alone never advances it. Successful changes or watermark advances make the old
review state obsolete; another apply requires a fresh review. An exact no-change
replay can succeed when every reviewed field still matches.

Historical authority has no arbitrary age expiry or seven-day limit: it is bound
to the explicit maximum-30-day range, exact response, implementation and database
snapshot. Observation ordering and locked state checks continue to apply regardless
of how long approval takes. There is no override for stale observations.

## Missing candles, anomalies and frozen datasets

A valid missing identity is only a proposal until explicitly approved. Inserts
must satisfy the same eligibility, alignment, inclusive-close, OHLCV, trade-count
and provenance checks. Zero-duration placeholders and malformed closes are never
normalized into full candles. Incomplete pages cannot partially apply.

Earlier archive manifests and investigation notes are retained unchanged. Each
review captures relevant prior source diagnostics; its application report links
the new evidence if a missing identity is subsequently accepted. Filling a database
hole does not erase an earlier provider anomaly or establish resolution of its
cause. Existing coverage and export diagnostics remain visible. A substantive
resolution can be documented separately with both sources retained.

Applying canonical corrections never invokes the exporter or rewrites an existing
dataset. The superseded rows remain queryable with `get_candle_history`. Integration
tests freeze an old CSV and manifest, apply a synthetic revision, create a new export
with a different content hash/manifest, then return to the original economic values.
The original export bytes remain unchanged throughout. Revised canonical history
must not silently replace inputs to earlier research.

## Failure recovery

Inspect the `.txt`, plan and application report. Repair missing/corrupt artifacts
from trusted retained copies or create a fresh review; do not relabel a fresh fetch
as the old response. Changed canonical state requires a fresh review and explicit
approval. Invalid provider data remains evidence, never an invitation to force apply.

Known validation/conflict errors and server-reported transactional failures report
rollback with zero committed changes. A lost connection during COMMIT reports
`failed_or_unknown`: compare canonical rows/history with the reviewed proposals
before proceeding. An artifact failure before writing prevents persistence. A
crash or final report failure can leave `in_progress` evidence after a commit;
the console reports known committed counts, but exits unsuccessfully if it cannot
publish the final report. There is no filesystem/database distributed transaction.
Driver/network errors do not expose credentials or connection details.

## Actual live review and preservation audit

On 2026-10-13, review-only acquisition inspected both symbols over September 1–3,
2026 and September 6, 2017. No live apply was executed and no provider correction
was manufactured. Application mechanics were tested only with controlled synthetic
responses in the disposable PostgreSQL 17 server.

| Range (UTC, end exclusive) | Market | Inspected | Identical | Changed | Valid missing DB | Invalid | Outcome |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2026-09-01 → 2026-09-03 | BTCUSDT | 12 | 12 | 0 | 0 | 0 | Ready for approval |
| 2026-09-01 → 2026-09-03 | ETHUSDT | 12 | 12 | 0 | 0 | 0 | Ready for approval |
| 2017-09-06 → 2017-09-07 | BTCUSDT | 6 | 4 | 0 | 1 | 1 | Blocked |
| 2017-09-06 → 2017-09-07 | ETHUSDT | 6 | 4 | 0 | 1 | 1 | Blocked |

All expected source identities were present. For both early-day responses, 12:00
has the normal inclusive close `1504713599999` and is valid but absent from the
canonical database. The 16:00 record has open **equal to close** at `1504713600000`,
zero trades and zero volumes. Its four prices are `4619.43` for BTC and `335.00` for
ETH. It fails the full-4h close-boundary check. The whole plan is blocked, including
the valid 12:00 proposal; nothing is inserted or repaired. These observations
corroborate the prior interruption investigation and reveal no genuine economic
revision against accepted canonical rows.

The audit compares complete ordered current and revision rows, including all
watermarks, and the historical coverage report before/after. Both markets retain
**20,030 current rows, 36 historical gaps, version 1 throughout and zero revisions**.
All 702 pre-existing raw/archive-manifest/export files were hashed before and after
and remained byte-identical. The frozen Stage 1B.3 export remains:

```text
candles.csv:   e6052b8cca7bca00999ca4d7429af67db019c8ef261fa2b499f0fd6774dcd13b
manifest.json: a78d34256d3bcd789e6cc19a2807f432d1ffa1a73ecc81b5ea16b3859759a98a
```

Local audit and live evidence: `artifacts/stage-01c2-baseline.json`,
`artifacts/stage-01c2-audit.json`, `artifacts/stage-01c2-live-reviews.json` and
`artifacts/stage-01c2-live-reviews-final.log`, plus the referenced review plans and
raw bodies. Earlier reviews remain retained when a later implementation change
requires a new compatible plan. Final compatible plan IDs are:

| Market | September 2026 review | September 2017 blocked review |
| --- | --- | --- |
| BTCUSDT | `dfbf783940824c8f965930140b6659ca` | `d9a4eafcc6e4440ab989aeb06bcf67bd` |
| ETHUSDT | `c99dbaf172814b87a2f53614ac2f3129` | `1fa4651d6fb4482b86039b8c8af217c2` |

## Verification and scope

The full suite passes **353 tests: 180 unit and 173 PostgreSQL integration tests**.
Ruff lint, Ruff formatting and `git diff --check` pass. The substantive prompt is
archived byte-for-byte at `prompts/stage-01-market-data/007-historical-revalidation.md`.
CI uses mocked provider responses and the existing disposable database fixtures;
it does not depend on Binance availability. CI was not run remotely.

The final rerun after the confirmation-watermark adjustment passed in 12.92 seconds;
its output is retained in `artifacts/stage-01c2-final-pytest.log`. The focused test
also confirms that an approved identical observation makes a delayed changed
observation stale. No regression was found. The disposable PostgreSQL container
had no remaining fixture databases and was stopped and removed. Test connection
configuration was command-scoped; development configuration was not changed.

Created: `src/backtest_badger/revalidation.py`, `tests/test_revalidation.py`,
`tests/integration/test_revalidation.py`, this guide and the prompt archive.
Modified: `candles.py`, `rest.py`, `cli.py`, shared test fixtures, CLI tests, README,
architecture, roadmap and the Stage 1A implementation-status note.

The main intentional simplifications are one complete page, one selected market,
one bounded transaction and whole-plan approval. No partial application or historical
scan automation is provided. Historical holes and unresolved source diagnostics
remain real limitations for research. No new Field Note was warranted: the live
anomaly evidence corroborates the established lesson rather than changing it.
No migration, new dependency, production/sibling-repository access, deployment,
commit or push occurred. Stage 1C.2 stops here for review; Stage 2 is not begun.

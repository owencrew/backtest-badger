# Stage 4D.2 — Production readiness and isolated rehearsal

**READY WITH CONDITIONS for a separate deployment review.** The isolated system migrated, operated under restricted logins and restored both financial and original-source evidence into an independent PostgreSQL cluster. Stage 4D.3 still needs an approved production writer, a host inventory, a production backup extension and an individual owner decision for each prospective account.

Work began on clean main at `ed557d7759672fc84e24b4c54ff7d37dde539ac2`. Both starting workflows succeeded. The Stage 4A specifications and both migration revisions retain their original bytes. [Starting CI](https://github.com/owencrew/backtest-badger/actions/runs/42420246439) · [Starting Frontend](https://github.com/owencrew/backtest-badger/actions/runs/42420246462)

## Operational architecture

Stage 3 writes original forecasts and mutable operation journals. The authenticated reader checks the Stage 3 publication, market/model/recipe, UTC chronology, Ridge value and automation cohort. The Stage 4D.1 process emits a proposal. The isolated harness commits an authenticated decision, commits a simulated intent, acquires a new fabricated quote and calls Stage 4C for a terminal event and atomic ledger postings. A valuation pins a complete ledger prefix and the contemporaneous bid. All prices, funds, fills, positions and P&L in this report are fabricated.

The proposed paper UID needs read-only access to the collector's `artifacts/forward-predictions` and `artifacts/forward-operations` directories and owner-private writable source storage. Stage 3 keeps its existing publication workflow. Reporting uses a private read-only database identity. The forensic originals and database dump belong outside the website, public R2 and the release tree. Live host state, installed backups/timers, DNS/TLS, clock accuracy, resource headroom and egress policy are **pending production verification**. [Operator checklist](deployment/paper-migration-activation-checklist.md) · [Dated infrastructure record](deployment/production-infrastructure.md)

## Migration, grants and activation

The fixture creates fresh databases from template0 on loopback PG17. An ordinary database owner runs Alembic. An independent collector saves a candle at 0001. After upgrade and grant changes, the same login reads the unchanged candle, records a revision and runs the original forward source-window and target-scoring queries. The Stage 4C suite also forces a name collision during 0002, checks rollback to 0001, retries after removing the fixture conflict, downgrades an empty schema, upgrades again and verifies refusal of populated downgrade. Fresh installs and restored objects undergo the constraint/trigger checks.

| Identity | Rights exercised |
| --- | --- |
| Bootstrap / disaster recovery administrator | Creates the isolated databases and logins, revokes PUBLIC access to three large-object creation functions and restores a reviewed full dump including protected system ACLs. |
| Migration owner | Owns database, migration objects and trigger functions. Runs Alembic, schema maintenance and grants. No cluster administration or superuser capability. |
| Inception operator | Reads market and five paper tables, inserts drafts, initial funding and inception marks, updates guarded portfolio projections. |
| Paper worker | Reads the same six tables, inserts decisions, orders, operational events and fill postings, updates order status and guarded portfolio projections. Row policies restrict posting type and exclude inception and discretionary state events. |
| Reporting reader | SELECT on market and five paper tables. Public presentation would need separately reviewed views and its own access decision. |
| Pre-existing collector/scorer fixture | Explicit CONNECT and schema USAGE, reads market/candles/revisions and retains ingestion grants. No paper decision access. |

The worker has no membership, schema CREATE, database TEMP, ledger UPDATE, DELETE, TRUNCATE, market writes, sequence privileges or trigger-management rights. Tests connect as each login and attempt prohibited mutations, trigger/constraint bypass, role escalation, large-object creation, temporary objects and administration. PostgreSQL rejects worker funding and inception even on a valid draft, and rejects operator operational marks. Row locks, uniqueness, immediate/deferred triggers and independent ledger audits remain active.

One installed portfolio trigger uses SECURITY DEFINER to take a row lock on market during inception. Its non-superuser migration owner and fixed `pg_catalog, public, pg_temp` search path are verified. Runtime logins cannot invoke or attach it. The two writing roles can execute the reviewed lock/latest/pending/config helpers. Only the worker needs the fee helper. PUBLIC and future default function grants are revoked in the rehearsal database. Paper identifiers use UUIDs and computed ledger sequences. Inventory legacy users' effective grants before translating the SQL. [Grant template](../ops/paper/grants.sql)

Inception opens, funds and marks in **one transaction** using the existing 0002 guards. The actual opening sample can fall inside the slot, e.g. 12:10:13 UTC. Filters and a same-invocation original quote follow that sample. The mark pins its filter evidence through the immutable quote key. A timeout or missed window leaves zero rows. An uncertain commit is resolved by reading the stable cohort and auditing its evidence. BTC and ETH had separate portfolio IDs and funding entries. Neither the schedule nor any economic parameter changed. The first quote and filters remain available for the analytical benchmark.

## Private originals and recovery

Forecast bytes, the exact qualifying journal snapshot, quote bytes, exchangeInfo, recipe, policies, protocol, release manifest and canonical config use SHA-256 object names. Exclusive publication writes a private staging file, fsyncs, links, verifies identical bytes on replay and syncs the directory. Source reads reject unsafe traversal/symlinks and bound file sizes. The application verifies Stage 3 qualification from the stored bytes **before** committing a decision. The DB records artifact/prediction IDs, file/content/journal/recipe hashes, discovery/issue/decision times, configuration and policy identities. The order's stable per-run reference locates a content-addressed receipt with its exact pre-intent filters, URL, UTC times and monotonic samples, including for interrupted and rejected attempts.

A running journal with a recorded qualifying market entry may subsequently complete. Recovery checks the retained bytes, compares the original market claim and publisher identity, and uses the snapshot named by the durable decision. An absent unpublished journal delays a timely decision. Conflicting claims and missing or corrupt required originals produce integrity failures. Archival without a committed decision leaves harmless recoverable objects. A submitted order cannot acquire a restarted fill from its previous invocation. The low-level Stage 4C interfaces assume a trusted caller. The future writer must exclusively use archival admission for prospective economic writes.

The checkpoint streams a custom PG17 dump from an exported repeatable-read snapshot, fingerprints exact ordered rows of all nine public tables, records the market identity sequence, compares schema dumps including triggers, indexes, column ACLs and policies, and verifies role attributes/memberships, database and protected function ACLs. A private second copy of source objects and intent references is re-audited against that snapshot. An interrupted dump has no released receipt. Restore requires a separately held manifest digest and exact file membership.

Independent restore used a second cluster with a distinct system identifier, fresh database and separately recreated roles/passwords. An initial owner-only restore failed on the protected ACL for `lo_creat` and rolled back. The corrected drill used a recovery administrator for the full dump and verified permissions again using the restored worker login. A truncated dump, an absent source object and corrupted filters were detected. Historical valuations, every ledger prefix, realised P&L, outstanding obligation and missing mark matched the source snapshot. The existing dated Lightsail checkpoint audits four tables. Encrypted transport, cadence, monitoring and retention changes for 0002 require approval.

## Fabricated end-to-end evidence

| Market | Fabricated portfolio ID | Cash USDT | Units | Realised USDT | Ledger high-water | End state |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| BTCUSDT | `1d35514b-38b3-5590-9dcd-cedabc0f7ed4` | 0.01240240 | 99.88 | 0 | 3 | Long, sticky risk exit after two missed horizons |
| ETHUSDT | `b14b3c7f-71f8-5545-a3fe-23d2ba8fd942` | 9976.02880000 | 0 | −23.97120000 | 5 | Flat after expiry, rejection and subsequent simulated sale |

Each portfolio began at 10,000 USDT and retained three marks, including one missing slot. BTC's open exit decision `92e6cebb-6d2f-57cf-827d-ff90606a433b` survived restore. The nine table inventories contained two markets, one candle, zero earlier candle revisions, one Alembic row, two portfolios, five decisions, five orders, fifteen market events and eight ledger entries. Deterministic economic identities are compared across the backup. Process run IDs and observation IDs are deliberately fresh.

The harness waited for journal evidence, authenticated positive/negative records, held continuously, restarted between decision and intent, expired an interrupted order, rejected an exit and retried on the five-minute cadence. A real child process was killed while its transaction contained an uncommitted mark. The competing invocation reported overlap until PostgreSQL released the disconnected backend's lock. A fresh invocation then saw only the committed inception mark. Stage 4C races exercise duplicate funding, competing submissions, double-fill prevention and simultaneous fill/mark admission.

## Monitoring and operational gates

Structured incident keys derive from category, portfolio and horizon/obligation/evidence ID. UTC observation time, attempts, duration, HTTP status and numeric Retry-After can be logged. Records exclude credentials and arbitrary provider messages. Count repeated keys across restarts. Preserve first/latest occurrences, count and affected evidence in the future log collector.

| Class | Signals and response |
| --- | --- |
| Expected missingness | Missing/late forecast, pending journal, unavailable quote, missing valuation, newly pending exit. Record slot, portfolio and actual observation. Keep gaps and sticky obligations visible. |
| Operational warning | 418/429, stale/unsupported filters, uncertain clock, runtime ≥240 s, contention/overlap, repeated failures, ageing exit or repeat rejection. Check the dependency and retry from durable state on the next permitted cycle. Respect provider cooldown. |
| Integrity or recovery incident | Invalid original automation, conflicting journal, failed reconciliation, missing originals, blocked dust, failed backup or isolated restore. Stop affected economic actions and preserve the DB, originals and last known good receipt. Require investigation before resumption. |

The proposed service writes JSON to a private journal with deduplicated escalation to the owner's approved operations destination. A separate monitor should report missing receipts and backup/restore failures. External alert delivery, service exit integration, NTP source, HTTPS policy and production headroom remain pending. The Stage 4D.1 proposal CLI retains its existing entry points.

## Measurement and verification

The synthetic workload advances one horizon and valuation every four hours for each portfolio. Signals hold or stay flat for multiple horizons, then reverse. Every 31st eligible mark misses its window. The adverse case forces a position and rejects three exit attempts before each checkpoint. The year contains 4,380 decisions, 742 fills, 742 execution quotes, 46 failed quotes and rejected orders, 370 satisfied exits, 4,240 observed marks and 140 missing marks. Both portfolios still owe an exit when sampled. The full five-minute collector journal history includes already-recorded and unsuccessful invocations.

Local machine: Apple M4 Pro, 14 logical CPUs, 24 GiB, arm64 macOS 26.5.2, Python 3.12.13. PostgreSQL 17.10 ran in Docker on loopback with a private 2 GiB tmpfs data volume. An independent restore cluster had its own 1 GiB tmpfs. These measurements include other local verification work and cached files. Physical SSD latency, cold starts and constrained Lightsail load require separate measurements.

| Days | Decisions, both | Journal files | Cycle median / p95 / max, s | Discovery, s¹ | Ledger replay / mark calculations / full reconciliation, ms² | Client peak RSS, MiB | DB growth, MiB |
| ---: | ---: | ---: | --- | ---: | --- | ---: | ---: |
| 30 | 360 | 8,598 | 0.463 / 0.483 / 0.483 | 1.024 | 2.1 / 3.5 / 17.0 | 182.4 | 1.16 |
| 90 | 1,080 | 25,878 | 1.229 / 1.276 / 1.276 | 2.349 | 6.3 / 11.5 / 58.5 | 204.1 | 3.38 |
| 180 | 2,160 | 51,798 | 2.433 / 2.462 / 2.462 | 4.534 | 13.8 / 24.8 / 82.2 | 219.3 | 6.28 |
| 365 | 4,380 | 105,078 | 4.770 / 4.824 / 4.824 | 9.901 | 30.5 / 58.8 / 170.5 | 265.8 | 12.39 |

¹ Maximum of the two concurrent per-market discovery measurements. The cycle figures measure an outstanding exit retry with archive verification, full reconciliation, account reread and proposal. A new-horizon discovery is timed separately. Six warm cycles per market ran concurrently, 12 observations per checkpoint. With nearest-rank p95, the maximum is the p95 in this sample. Each checked cycle issued 50 client SQL statements, including transaction setup. Trigger-internal SQL is additional.

² Ledger time sums simulated order and account trade replay. Mark time covers prefix valuation. Reconciliation total also includes SQL transfer, quote/posting validation and relationship checks. Combined client CPU seconds for the sampling/discovery batches were 4.47, 11.49, 22.66 and 45.36. Cumulative PostgreSQL buffer hits were 211,181, 1,006,018, 2,981,534 and 10,501,853. The database reported 31 block reads and zero temporary spill bytes at each sample. A tmpfs block read is not a physical disk read.

The year-end concurrent mark and sell both committed. The mark used sequence 743 and the sell advanced it to 745. The mark took 0.012 s, the fill took 0.380 s, and 5 ms sampling of PostgreSQL lock waits attributed approximately 0.006 s to the fill. A separately held row lock produced the expected lock timeout at 3.01 s and no economic change. The ten-second statement timeout applies per SQL statement. The five-minute scheduling interval and Python/file discovery have separate clocks. Full reconciliation was practical for this workload without a mutable balance cache or relaxed integrity checks. The year-end discovery cost makes it important to complete discovery **before** requesting a perishable order quote. Host validation must also measure the one-second quote-use limit and 30-second intent expiry under load.

### Executed verification

| Check | Result |
| --- | --- |
| Starting full root suite, PG17 and private macOS scratch | 3,274 passed, 88 skipped in 20m 15s |
| All PostgreSQL integration cases after the archive, role and checkpoint additions | 237 passed in 36.94 s, followed by 4 final readiness cases including the newly added conflicting-publisher case |
| Core paper unit checks including operational diagnostics | 364 passed; 31 operational diagnostic cases also passed independently |
| Guarded E.5 / E.5c / E.5d runners | 87 / 55 / 153 passed |
| Study 001 read-only pinned replay | 1 passed. Reconstructed original summary and detailed evidence bytes matched. |
| Frozen science | Both studies' retained summary/evidence hashes and all 57 Study 002 source pins matched. |
| Full-history benchmark | One explicit benchmark passed in 361.33 s, including the year-end race. |
| Packaging and static checks | Ruff lint and format, wheel build, wheel-only imports of the new modules, offline proposal and Git whitespace checks passed. |

The normal root suite gates 87 cases on the isolated E.5 runner and one on explicit read-only authority to replay Study 001. Each was run via its required entry point. For reproduction, use the Stage 4C private macOS scratch setup, two independent loopback PG17 clusters, explicit source/restore maintenance DSNs and full container IDs. Point `BADGER_TEST_ADMIN_DSN` and `BADGER_D2A_TEST_CONTAINER` at the source, and `BADGER_TEST_RESTORE_DSN` and `BADGER_TEST_RESTORE_CONTAINER` at the target. Use separate pytest basetemps. Run the following from the checkout with the locked environment.

```sh
pytest tests/integration
pytest -s tests/integration/benchmark_paper.py
pytest -o tmp_path_retention_policy=none
python -I -S -B tests/run_e5_guarded.py
python -I -S -B tests/run_e5c_guarded.py
python -I -S -B tests/run_e5d_guarded.py
```

During fixture development the first generated candle timestamp used incorrect datetime arithmetic. A mixed-order pytest selection also lost its integration fixtures. Both were corrected and rerun. The process-kill test initially assumed instant server-side disconnect cleanup. The confirmed behaviour is that overlap stays blocked until PostgreSQL releases the session lock. The bootstrap restore ACL issue and its resolution are described above.

## Release and inventory

The exact final **implementation** SHA is `e8880d599edd6862c95598ee009f8a9bacf19dea`. The final release commit adds this handoff, checklist and prompt. Its own SHA is recorded in the delivery message and can be resolved in any full checkout with the following command. Use that SHA to select the two GitHub workflow runs. A commit cannot contain its own literal SHA.

```sh
git log -1 --diff-filter=A --format=%H -- docs/stage-04d2-production-readiness.md
```

[Implementation commit](https://github.com/owencrew/backtest-badger/commit/e8880d599edd6862c95598ee009f8a9bacf19dea) · [CI runs](https://github.com/owencrew/backtest-badger/actions/workflows/ci.yml) · [Frontend runs](https://github.com/owencrew/backtest-badger/actions/workflows/frontend.yml)

| Changed paths | Purpose |
| --- | --- |
| `src/backtest_badger/paper_artifacts.py`, `paper_evidence.py` | Exclusive publication, original verification, intent filter receipts, restart qualification and atomic inception |
| `src/backtest_badger/paper_persistence.py`, `paper_market_data.py` | Shared cursor-level inception steps and effective-filter parser |
| `src/backtest_badger/paper_checkpoint.py`, `paper_operations.py`, `paper_worker.py` | Snapshot/restore verification, process exclusion, clock gates, diagnostics, provider status |
| `ops/paper/grants.sql` | Isolated privilege template |
| `tests/integration/paper_roles.py`, `paper_workload.py`, `benchmark_paper.py`, `test_paper_readiness.py`, `tests/test_paper_operations.py` | Genuine logins, fabricated originals, long histories, crash/DR and failure tests |
| `.github/workflows/ci.yml` | Second PostgreSQL 17 service, loopback publishes, CI restore configuration |
| `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/development-handoff.md`, this report and `docs/deployment/paper-migration-activation-checklist.md` | Capability, measurements, operator decisions and gates |
| `prompts/README.md`, `prompts/stage-04-paper/stage-04d2-production-readiness.md` | Prompt index and verbatim request |

The owner must approve production inspection, migration/release and role changes, backup/retention changes, restricted worker installation and monitoring. Each genuine BTC and ETH simulated portfolio needs an additional explicit activation decision. Public reporting remains separately gated.

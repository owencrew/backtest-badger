# Roadmap

**Current summary: 24 October 2026.** Each stage is scoped independently. Planned
capabilities are not current features. The first genuine native-minute 2024
backtest is complete; the next product milestone is **Stage 5: a polished public
website**, using research and forward evidence already available. It need not
wait for prospective paper-trading implementation.

[E.5g](stage-04b2e5g-first-genuine-historical-backtest.md) records verified independent
Ridge, Cash and Buy & Hold accounts for each market. Ridge lost **60.69% on BTCUSDT
and 57.96% on ETHUSDT**, versus Cash at 0% and Buy & Hold at **+120.81% / +46.18%**.
These are exploratory historical results after fixed costs, marked through
December 31 23:00 UTC, not live or prospective paper-trading performance.

Historical simulations, live forward forecasts and their scored outcomes are
implemented evidence streams. Prospective paper trading will simulate orders as
new observations arrive; its service is still planned. Real trading is outside
scope.

| Stage | Status | Acceptance criteria |
| --- | --- | --- |
| **0 — Foundation** | Complete | Python 3.12 package installs from the uv lockfile; configuration and both CLI checks work; local PostgreSQL connectivity is demonstrated when Docker is available; pytest and Ruff pass; CI, license and concise documentation exist. |
| **1A — Market Data Feasibility and Design** | Complete; schema decisions refined in 1B.1 | Official Binance documentation reviewed; bounded public API/archive tests completed; timeframe, revision policy and minimal schema proposed in the [Stage 1A design](stage-01a-market-data-design.md). Schema implemented in 1B.1; bounded monthly archives implemented in 1B.2. |
| **1B.1 — Schema and Persistence** | Implemented | Three application tables and market seeds; Alembic upgrade/downgrade; exact Decimal persistence; version-preserving writes; stale-write handling and PostgreSQL concurrency/rollback tests; ingestion added separately in 1B.2. |
| **1B.2 — Bounded Archive Ingestion** | Implemented | Explicit monthly native 1h/4h CLI; bounded checksum/parser validation; atomic conflict-rejecting backfill; local raw evidence and manifests. January 2025 live 4h import: 186 candles per market, zero gaps/revisions. |
| **1B.3 — Full Historical Coverage and Research Dataset** | Implemented; acquired with known gaps | All 220 market-months through September 2026 inspected and committed; 19,955 candles and 36 disclosed gaps per market. Frozen 39,910-row export is explicitly incomplete. See [results](stage-01b3-full-history.md). |
| **1C.1 — REST Tail and Recent Refresh** | Implemented | Fixed eligible cutoff, strict native 4h REST, seven-day refresh, bounded catch-up, atomic page revisions and stored-grid diagnostics. Live: 75 new candles per market, 20,030 total each; zero recent gaps/revisions, historical gaps and frozen export preserved. See [guide](stage-01c1-rest-tail-and-refresh.md). |
| **1C.2 — Historical Revalidation** | Implemented | Explicit maximum-30-day REST review and approved exact-response replay; locked snapshot checks, atomic version history, invalid-page rejection and frozen export preservation. Live reviews: no economic revisions; zero-duration 2017 rows rejected for both markets. See [guide](stage-01c2-historical-revalidation.md). |
| **2A — Reproducible Research Dataset and Causal Features** | Implemented | Pinned frozen-source verification, explicit incomplete acknowledgement, gap/anomaly-safe causal features and one 4h target; availability-based chronological splits and label purging; train-only no-skill references; deterministic 39,609-row artifact and untouched holdout. See [guide](stage-02a-research-dataset.md). |
| **2B — Predictive Modelling** | Implemented | Pinned Stage 2A input validation; separate-market zero/mean, Ridge and shallow boosting comparisons; training-only preprocessing/fitting, 2024 validation metrics and untouched test outcomes. Two byte-identical runs. See [results](stage-02b-predictive-baselines.md). |
| **2C — Backtesting** | Implemented | Independent native 2024 1h references from 24 verified archives; offline pinned validation forecasts, delayed three-hour long/cash simulation, explicit two-sided costs and independent Decimal accounts. All trading accounts lose under base/stress assumptions; zero stays cash. Four byte-identical output files across two runs. See [results](stage-02c-execution-backtesting.md). |
| **2D — Economic Diagnostics and Robustness** | Implemented | Read-only postmortem of pinned Stage 2C accounts: scenario-specific costs, all twelve months, geometric cost budgets and existing baseline comparisons. Annual and monthly reconciliation, deterministic artifacts and untouched holdout. See [results](stage-02d-economic-diagnostics.md). |
| **3A — Forward Prediction Recording** | Implemented | Manual current-horizon forecasts from seven validated native 4h candles; fixed pre-2024 fits, strict live UTC checks, immutable shared evidence and offline replay. First genuine BTC/ETH records were subsequently issued on 2026-10-14 and verified. See [guide](stage-03a-forward-predictions.md). |
| **3B — Automated Forward Collection** | Implemented; Lightsail snapshot 2026-10-16 | Independent idempotent BTC/ETH cycles, strict 15-minute promptness, exclusive publication, offline status and missed-horizon evidence; separately installed macOS LaunchAgent and backup guidance. See [guide](stage-03b-automated-forward-collection.md). |
| **3C — Prospective Forecast Evaluation** | Implemented; first four genuine observations scored | Frozen protocol, standalone manual scorer with read-only exact-target snapshots, immutable outcome evidence and matched offline metrics; separate timely automated/late manual cohorts, missingness and sample warnings. Original implementation validated synthetically; subsequent manual scoring verified four genuine observations. See [guide](stage-03c-forward-evaluation.md). |
| **3D — Automated Forward Outcome Scoring** | Implemented; Lightsail snapshot 2026-10-16 | Independent bounded cycles reuse the frozen scorer; no-DB pending/existing checks, fair retry cursor, exclusive publication, operational history and offline status. Existing collector/evidence preserved. See [guide](stage-03d-automated-outcome-scoring.md). |
| **D1 — Lightsail Deployment Foundation** | Installed; superseded operating snapshot | Host Python, loopback PostgreSQL and pinned releases. The [production runbook](deployment/production-infrastructure.md) records active Lightsail collection/scoring as of 16 October; the original foundation guide is historical. |
| **D2A — Migration Rehearsal** | Tooling implemented; later recovery verified | Original [rehearsal guide](deployment/lightsail-d2a-rehearsal.md) preserves preparation gates; the production runbook records supervised restore/fingerprint verification and remaining unattended checks. |
| **D2B — Migration and Scheduler Cutover** | Lightsail operation recorded 2026-10-16 | Production PostgreSQL and collection/scoring are recorded active in the [runbook](deployment/production-infrastructure.md). No fresh host check or latest-research deployment is implied. |
| **4A — Paper-Trading Architecture and Prospective Protocol** | **Approved (2026-10-16); design only** | [Technical specification](stage-04a-paper-trading-spec.md) and [prospective evaluation protocol](stage-04a-prospective-evaluation-protocol.md) approved; no application implementation, migrations or deployment. |
| **4B.1 — Deterministic Paper Primitives** | Implemented locally | Synthetic pure-function strategy transitions, quote/filter execution, paired Decimal accounting, replay and immutable-mark valuation. See [guide](stage-04b1-deterministic-paper-primitives.md); no live integration or persistence. |
| **4B.2A — Historical Replay Mechanics** | Implemented; synthetic validation | Supplied-input hourly continuous holdings and exact accounting. The [engine guide](stage-04b2a-historical-replay-engine.md) preserves its stage scope; the later genuine result uses the separate minute path. |
| **4B.2B — Historical Integration and Reporting** | Implemented; synthetic validation | Supplied-loader integration, independently funded benchmarks and immutable reporting. See [guide](stage-04b2b-historical-evaluation-integration.md); genuine minute execution followed separately in E.5g. |
| **4B.2C — Minute Design and Source Engineering** | Implemented; genuine source release verified/frozen | [Frozen methodology](stage-04b2c-minute-execution-protocol.md) and [18 October source pins](stage-04b2c-minute-source-pins.md); earlier synthetic-only status is historical. |
| **4B.2D — Minute Replay, Parity and Authentication** | Implemented; genuine parity completed | [D.1 audit](stage-04b2d1-genuine-price-parity-audit.md): 17,568 exact hourly/minute opening-price pairs, zero discrepancies. Later retained publication/sign-off supplies the local runner; parity itself is not economic evidence. |
| **4B.2E.1–5d — Replay/Reporting Integration and Guarded Operator** | Implemented; fabricated development evidence | Reusable replay/reporting components remain; E.5d installation/custody blockers are not prerequisites for the separate [E.5e local route](stage-04b2e5e-local-execution-decision.md). |
| **4B.2E.5e–5g — Local Execution and Genuine Backtest** | Complete | One-process pinned-input runner, successful genuine preflight, one genuine 2024 replay and six verified accounts. See [E.5g results](stage-04b2e5g-first-genuine-historical-backtest.md); no tuning or model promotion. |
| **4B.2E.5h — Research Narrative** | Documentation prepared for review | Current summaries reconciled; [Field Notes 003 and 004](field-notes/README.md) drafted; website evidence handoff added. No new research or deployment. |
| **4C–4E — Paper Persistence, Prospective Integration and Reporting** | Future, gated | Independently approve isolated database integrity, prospective quote/worker activation and reporting. No production changes authorised. |
| **5 — Polished Website and Public Launch** | **Live; post-launch audit 2026-10-28** | Workers static website, permanent R2 forward feed and seven approved articles. Indexing remains disabled; see [Stage 5B.8](stage-05b8-post-launch-audit.md) for verified health, HTTP redirect issue and release-evidence gaps. |
| **6 — Research and Asset-Class Expansion** | Planned | New research and asset classes are supported by documented evidence, appropriate data/execution assumptions and reproducible validation without compromising existing results. |

Real-money trading is outside this roadmap and requires explicit approval.

## Stage 5 — Live product and next backlog

The website is live at <https://www.backtestbadger.com>; the genuine public feed is
<https://data.backtestbadger.com/forward-v1.json>. See the
[post-launch audit](stage-05b8-post-launch-audit.md) and current
[development handoff](development-handoff.md). Close its operational verification
items before separately approving indexing or further product development.

**Latest Scored Forecast — proposed, not implemented.** Show the most recently
completed/scored forecast separately from the latest pending prediction. Compare
previous predictions with actual observed return, forecast error and directional
correctness, preserving Zero's ineligible direction. A reviewed public-contract and
exporter extension will likely be needed. Preserve original provenance, scoring
methodology and cohort separation; implementation requires a separate stage.

Research/platform backlog retains its existing status: Stage 4C–4E prospective
paper trading, operational alert/backup/retention verification, later research and
asset-class expansion. This documentation audit changes none of those milestones.

### Original Stage 5 website design context

The planning notes below predate the live site and remain historical context.

The first website can present the genuine 2024 result, independent benchmarks,
existing prospective forecast/outcome evidence, methodology and limitations.
Use the [website handoff](development-handoff.md#5-next-product-milestone--the-public-website)
for content and acceptance criteria. Paper portfolio screens depend on later
Stage 4C–4E implementation; no framework or hosting change is selected here.

**Field Notes journal**

The repository's [Field Notes](field-notes/README.md) journal holds curated
engineering and research articles for this future website section. Entries begin
as drafts and require editorial review before publication; they are not automatic
development logs. Website presentation and publishing remain Stage 5 work.

**Animated backtesting mascot**

When a user initiates a backtest, a small animated badger could follow the historical
price chart backwards, representing the platform investigating past market data.
This is a future product-design idea, not a Stage 0 requirement.

The animation should eventually:

- Follow the shape of a historical price line from right to left.
- Be visually engaging but subtle and professional.
- Reflect backtest progress where technically feasible, rather than displaying
  misleading artificial progress.
- Avoid interfering with chart readability or performance.
- Respect reduced-motion accessibility preferences.
- Work appropriately on desktop and mobile.

## Historical milestone records

The records below preserve implementation-time results and gates. Statements such
as “awaiting review”, “unimplemented”, “no genuine run” or “next approval” refer to
that increment, not today's project status. The current table above supersedes
those pending-stage summaries; detailed reports and frozen protocols are unchanged.

## Stage 1A findings and proposed direction

On 2026-10-13, public Binance access from the Mac succeeded after the sandbox's
initial DNS failure. Ten ZIP checksums and 998 archive rows passed validation;
60 overlapping archive/REST candles matched exactly after timestamp normalization.
Both markets' first returned 1h/4h candle was 2017-08-17 04:00 UTC. These bounded
samples do not establish complete historical continuity. The October 12 daily
archive was still unavailable at 00:44 UTC on October 13, so REST must cover the
tail without assuming midnight archive publication.

The selected design uses native UTC 4h candles, independent native 1h only when
needed, and three tables (`market`, `candle`, `candle_revision`). A 60-second
settling delay and seven-day overlap are initial project defaults, not provider
finality guarantees. Stage 1B/1C scopes, acceptance criteria and unresolved risks
are in the [design document](stage-01a-market-data-design.md). Stage 1B.1 implements
the schema and persistence; later increments await implementation review.

## Stage 0 validation

Stage 0 was verified locally on 2026-10-13 with Python 3.12.13: 26 pytest tests
passed, Ruff lint and formatting passed, source/wheel builds and isolated wheel
installation succeeded, and both CLI checks passed against local PostgreSQL.
CLI error exit codes and credential redaction were also checked. The GitHub
Actions workflow is configured but has not run remotely; no commit or push was made.

## Stage 1B.1 implementation

The [persistence guide](stage-01b1-persistence.md) documents the schema, API,
revision policy, migrations, inspection queries and isolated test setup. Runtime
uses Psycopg; SQLAlchemy is limited to Alembic. Only three application tables and
required PK/unique indexes exist. Concurrent writes use short transactions and
row locks, with no advisory locks around network requests. Immutable superseded
versions retain original provenance; identical confirmations advance only a
last-observed watermark to reject delayed conflicting writes.

Raw data and manifests can initially use ignored local `artifacts/`; durable
retention follows as research and deployment progress. Stage 1C retains the
60-second settling-delay and seven-day refresh-overlap defaults. That persistence
increment included no downloading, archive parsing, REST updates, scheduling,
research or dashboard work.
Local migration verification uses only disposable databases. Stage 1B.2 is
documented separately below. No commit, push or deployment is part of this stage.

Local verification on 2026-10-13: **169 pytest tests passed**, including **118 real
PostgreSQL integration cases** on PostgreSQL **17.11** and all 26 Stage 0 tests.
Without a test DSN, 51 unit tests pass and 118 integration cases skip explicitly.
Ruff lint and formatting pass. Fresh/repeated upgrades, populated downgrade,
re-upgrade, offline SQL and the normal environment-configured migration CLI were
verified. An unrelated table and database timezone survived migration cycling.
The prompt archive matches the supplied prompt byte for byte. GitHub Actions is
configured for the full suite but has not been run remotely.

## Stage 1B.2 implementation

The [archive ingestion guide](stage-01b2-archive-ingestion.md) documents explicit
single-month commands, full-grid validation, atomic backfill conflict handling,
provenance and ignored local artifacts. Standard-library acquisition adds no
dependencies or schema migration. Live January 2025 native 4h ingestion yielded
372 candles, zero gaps and zero revisions across BTCUSDT and ETHUSDT. Stage 1B.3
coverage expansion and exports remain deferred until review; no automatic extra
months, REST ingestion, scheduling or historical revalidation were added.

Local final verification: 227 tests passed (101 unit, 126 PostgreSQL integration),
plus Ruff lint and formatting. Each repeated live import returned 186 unchanged
candles and no inserts or revisions; exact values and original provenance remained
unchanged. Only confirmation watermarks advanced. The temporary test container was
separate from the existing development database, which remained at revision 0001.

## Stage 1B.3 implementation

The [full-history guide](stage-01b3-full-history.md) records commands, restart
semantics, initial-boundary evidence, actual backfill results and snapshot exports.
The two-market source start is 2017-08-17 04:00 UTC; the requested exclusive end is
2026-10-01 00:00 UTC. Completeness is checked against stored identities, with no
interpolation or silent exclusion of gaps. Unchanged imports preserve accepted
versions and provenance. Existing monthly ingestion and persistence are reused;
no new schema or dependencies are introduced. Stage 1C remains unimplemented and
requires review before work begins.

Initial Stage 1B.3 verification: 247 tests passed (116 unit, 131 isolated PostgreSQL
integration), with Ruff lint/format passing. Eight bounded imports passed, then
full BTC backfill stopped at September 2017's invalid close boundary and missing
16:00 UTC candle on September 6. Each market has 641 stored candles; January
observations and provenance are preserved, with zero revisions. The declared
full range remains incomplete and its export was refused. No validation was
weakened, no later full-range imports were attempted after the blocker, and no
partial live export was implicitly approved.


### Stage 1B.3 historical-anomalies follow-up

Implemented opt-in `backfill-history --allow-source-gaps`, preserving strict
monthly defaults, economic/identity/checksum validation and atomic conflict
rejection. Missing intervals and excluded irregular-close rows remain visible
in coverage and export manifests; no timestamp normalization or replacement
candles were added. Official September 2017 and June 2018 comparisons are retained
as offline regression fixtures; interruption-sensitive research windows must
explicitly handle gaps and cannot assume uninterrupted trading within native bars.

Both full histories through September 2026 were acquired: **110 months and 19,955
stored native 4h candles per market**, with **17 absent monthly-source intervals
and 19 excluded rows per market** (36 stored gaps each). All 1,282 pre-existing
rows were preserved; there were zero conflicts, stale changes, failures or
revisions. Complete export remains correctly refused. Final checks: **268 tests
passed (133 unit, 135 isolated PostgreSQL integration)**, plus Ruff lint/format.
See the [full-history guide](stage-01b3-full-history.md) for exact identities,
investigation, source disagreement, totals and remaining limits. Stage 1C remains
unimplemented; stop here for review.


### Stage 1C.2 controlled historical revalidation

Separate review/apply commands now retain bounded historical evidence, require
explicit whole-plan approval and reject changed database state or altered source
bytes. Tests cover exact comparisons, concurrency, stale/equal-time selection,
atomic rollback, missing valid insertions, anomaly retention and frozen exports.
Both markets' two-day September 2026 reviews are identical; September 6, 2017 plans
are blocked by zero-duration 16:00 observations. No live apply was executed.
The final audit preserves 20,030 current rows and 36 historical gaps per market,
zero revisions and the original frozen export hash. Stage 2 was not begun in that
increment; Stage 2A is recorded below.

### Stage 2A research foundation

Offline preparation verifies the frozen 39,910-row export and its manifest against
reviewed hashes, preserving all original artifacts and the market-data database.
The resulting 39,609 eligible observations retain exact source prices and explicit
UTC signal/label availability. Every feature/target window requires uninterrupted
4h identities and excludes recorded anomalies. The prior BTC partial-trading
observation receives an explicit retained-candle exclusion.

Train/validation/test counts are 13,782 / 2,195 / 3,827 for BTC and
13,783 / 2,195 / 3,827 for ETH. Test target summaries and performance remain
withheld. Zero and training-mean reference predictions are retained without model
training or strategy optimisation. Full verification: 405 tests passed, including
173 isolated PostgreSQL integration cases, plus Ruff lint/format checks.
See the [guide](stage-02a-research-dataset.md) for definitions, exclusions, hashes,
reproduction and scientific limitations. Stop after Stage 2A for review.

### Stage 2B predictive baselines

The fixed five features and original splits now feed independent BTC/ETH Ridge
and shallow gradient boosting fits. Each market has 2,195 validation observations;
training counts are 13,782 and 13,783. Ridge reduces RMSE versus the training mean
by 0.141% (BTC) and 0.151% (ETH). Boosting reduces ETH RMSE by 0.725% but achieves
only 47.517% directional accuracy; BTC boosting worsens MAE. These small and mixed
validation improvements establish neither statistical significance nor profitability.

All three experiment artifacts reproduce byte for byte, with unchanged source
hashes and no test forecasts/scores. Verification: 274 tests passed, 173 database
integration cases skipped without an isolated test DSN; Ruff lint/format and diff
checks passed. See the [guide](stage-02b-predictive-baselines.md) for full comparisons,
metric conventions and limitations. Stage 2C is recorded below.

### Stage 2C execution-aware validation backtesting

All 24 native Binance Spot 1h archives for 2024 passed official checksum and strict
monthly-grid validation: 8,784 rows per market, zero missing/rejected observations.
The frozen artifact is independent of the 4h research dataset and never enters
the canonical database. Its retained sources are replayed before each offline run.

The fixed policy trades forecasts above 1e-12: 12:01 availability, 13:00 entry and
16:00 exit, with separate 10,000-USDT market/model/scenario accounts. Base and
stress assumptions produce negative net results for every account that trades;
base losses range from 87.36% to 99.63%. Frictionless gains do not establish
executable profitability. Gross and net results, detailed costs, realised-equity
drawdowns and the model-target/execution-return distinction remain explicit.

All four outputs reproduce byte for byte; an independent cash-flow check agrees.
Stage 2B hashes and Stage 2A metadata remain unchanged, and the research CSV and
test labels were never opened. Verification: 343 tests passed, 173 PostgreSQL
integration cases skipped without an isolated test DSN; Ruff lint/format and diff
checks passed. See the [guide](stage-02c-execution-backtesting.md) for source/output
hashes, complete results and limitations. That increment stopped before Stage 2D,
holdout evaluation, tuning, model promotion, live trading or deployment.

### Stage 2D economic postmortem

The audited Stage 2C manifest and retained CSV/summary hashes match; all 24 accounts
reconcile without rerunning or altering trades. The new offline analysis retains
288 calendar-month account rows, actual scenario cost decomposition, exposure,
turnover and analytical fixed-sequence cost budgets. BTC Ridge has a 6.33-bps
round-trip log-cost budget, versus 26.00/46.00 bps base/stress drag; ETH boosting
loses frictionlessly and has no nonnegative budget. Positive frictionless results
do not establish alpha over the always-positive training-mean baseline.

All four outputs reproduce byte for byte. Verification: 382 tests passed, 173
PostgreSQL integration cases skipped without an isolated test DSN; Ruff lint and
format checks passed. Existing frozen inputs and the holdout remain untouched.
See the [guide](stage-02d-economic-diagnostics.md) for annual/monthly results,
hashes, cost calculations and interpretation limits. Review these findings before
separately scoping Stage 3 as forward observation, with no profitability promotion.
Stop after Stage 2D: no Stage 3 implementation, tuning, test evaluation or trading.

### Stage 3A forward observations

Manual recording and offline verification now retain the original five features
and all four fixed models, deterministically fitted only on pinned pre-2024 rows.
Current-horizon checks reject stale/incomplete inputs, clock reversals and expired
outcomes; read-only snapshots preserve exact versioned source evidence. One
exclusive atomic JSON publication protects all four model identities together.

The local eligibility inspection on 2026-10-14 found both markets stale, with six
of seven required candles missing; no live forecast was recorded. No automatic
refresh, historical replay, scoring or strategy promotion occurred. Training-only
reproduction checks and synthetic/offline/database tests are documented in the
[guide](stage-03a-forward-predictions.md). Stop after Stage 3A; scheduling, forward
outcome evaluation and paper trading remain separately scoped future work.


### Stage 3B automated forward collection

The existing refresh, fixed training-only recording and retained-evidence replay
now run in one deadline-limited, process-locked cycle. Existing predictions are
skipped without network or fitting; per-market failures, issuance latency and
missed horizons remain in separate operational history. A five-minute macOS
LaunchAgent example is supplied but not installed or enabled. Original artifacts
are preserved; no new genuine observation was produced during this implementation.
See the [guide](stage-03b-automated-forward-collection.md) for status, recovery,
installation, off-machine backups and development-machine reliability limits.
Stop after Stage 3B; outcome evaluation and paper trading remain unscoped.

### Stage 3C prospective forecast evaluation

The [protocol](stage-03c-forward-evaluation-protocol.md) was frozen before any
outcome access. A separate module scores the saved four forecasts against the
exact next native 4h close using the original retained source close. Timely
automated observations require matching Stage 3B provenance; late manual and
timely unattributed records remain separate. Atomic exclusive outcome publication
freezes the first captured target version and cohort. Offline reports disclose
missingness, matched counts, benchmark errors and preliminary-sample limitations.

The user reports the Stage 3B LaunchAgent is now installed and collecting locally;
Stage 3C leaves it and its fingerprinted code unchanged. No development-database
queries, genuine outcome inspection/scoring, holdout access, new jobs, trading or
deployment were performed. Review the protocol and [test results](stage-03c-forward-evaluation.md)
before manually running genuine scoring. Stage 4 remains unstarted.


### Stage 3D automated outcome scoring

An independent orchestration module now scores eligible genuine forecasts through
the unchanged Stage 3C API, with per-record failure isolation, no-DB validation of
existing outcomes, pending retries and a durable rotating backlog cursor. Bounded,
process-locked cycles and offline diagnostics retain incomplete and invalid evidence.
A separate five-minute LaunchAgent is supplied without installation or enablement.
The original live prediction collector remains unchanged and operational.
The [guide](stage-03d-automated-outcome-scoring.md) covers commands, tests, recovery,
limitations and backups including both outcomes and scoring operations. Stop after
Stage 3D; Stage 4 paper trading remains unstarted.

**Stage 4B.2C approval (2026-10-17):** Reviewed synthetic one-minute acquisition code passed GitHub CI. The [minute-execution methodology](stage-04b2c-minute-execution-protocol.md) is now frozen as `historical-minute-execution-v1`. Next approval is **only** a specifically scoped genuine 24-archive/sidecar acquisition with a fixed code revision and new destination; minute replay, source parity and economic results remain separately gated.


### Stage 4B.2D — synthetic minute replay and parity (awaiting review)

The minute source release was separately acquired, verified and frozen; see the
[Stage 4B.2C.3 pins](stage-04b2c-minute-source-pins.md). Stage 4B.2D now implements
the frozen strictly-next-minute methodology with fabricated inputs, independent
cash and inception buy-and-hold benchmarks, compact hourly mark reconciliation
and a pure exact-price parity auditor. Full synthetic 2024 coverage preserves the
2,195-signal / 8,784-mark grids per market and the missing final 20:01 signal.

The owner separately authorised Stage 4B.2D.1 implementation and one read-only
genuine hourly/minute price audit after all synthetic/preflight gates pass.
The completed audit authenticated both full releases and found **zero exact
mismatches across 17,568 HH:00 pairs**; no economic calculation was run. The
[audit guide](stage-04b2d1-genuine-price-parity-audit.md) retains the output pins
and validation/preservation evidence. The subsequently authorised Stage 4B.2D.2
implements only synthetic integration design/tests, as recorded below; actual
source access, strategy calculation and immutable economic publication require
later explicit authorisation. No real replay, holdout access, production work
or advance to Stage 4C–4E is included.


### Stage 4B.2D.2 — forecast/minute integration (synthetic; awaiting review)

The [pure adapter and synthetic tests](stage-04b2d2-minute-forecast-integration.md)
validate all original loader account shapes, model lineage, required next-minute
references and independently pinned fixture parity evidence. The complete-year
fixture has 2,195 forecasts and 10,979 projected references per market. Existing
loaders, scientific protocols, replay guards and monetary modules are unchanged.

Next: owner/code review and CI, then separately approved genuine authentication
implementation and exact read-only input scope with a fresh verification output.
A separate typed genuine replay boundary, actual economic calculation, reproduction
and immutable publication require later approval. No genuine source was opened
or economic result produced by this synthetic stage.

### Stage 4B.2D.3 — input authentication primitives (synthetic tests only)

The [authentication guide](stage-04b2d3-genuine-minute-input-authentication.md)
describes the separate frozen `AuthenticatedMinuteInputs` type, original-byte
checks, full native-grid streaming projection, unchanged forecast/lineage policy
and actual five-file parity schema validation. Only invented temporary fixtures
were processed. Source and projection identities remain distinct; execution
authority is always false. Existing synthetic replay/integration gates are unchanged.

The public authentication interface still rejects every call before I/O.
Stage 4B.2D.4 below adds the separately closed verification/publication operator.
Genuine verification, real replay and economic publication retain distinct approvals.

### Stage 4B.2D.4 — closed one-use verification operator

The [operator guide](stage-04b2d4-genuine-verification-operator.md) describes strict
external approval pins, atomic one-use reservation, source/code preservation,
exclusive publication and manifest-last readback. Full native fabricated archives
and the unchanged validators exercise the private temporary fixture path.
Scientific verification bytes remain reproducible; filesystem evidence is separate.

Both public interfaces remain unconditionally closed. No genuine artifact was
opened or inventoried, and no economic calculation was performed. Next is owner/code
review, then separately reviewed exact-root production wiring and explicit approval
for one read-only genuine verification attempt. Genuine replay and economic
reproduction/publication require subsequent distinct authorisations.

### Stage 4B.2D.5 — verification wiring preparation (awaiting review)

The [binding plan and readiness template](stage-04b2d5-genuine-verification-wiring.md)
now make original loader contracts, exact 57-file declarations, implementation
allowlist and missing approval evidence inspectable without an executable genuine
path. The existing fixture runner, publisher and all prior code/tests remain
unchanged. Both public genuine gates still refuse before argument inspection.

Next: owner review of this preparation, then separately authorised/reviewed
genuine-enabled wiring, clean commit and matching green CI, complete externally
retained evidence (including both original forecast lengths), and a distinct
one-attempt read-only invocation approval. Destination state remains uninspected.
Genuine replay, strategy execution and economic publication retain later gates.

### Stage 4B.2D.6 — activation blocked on independent approval authority

The [activation review proposal](stage-04b2d6-genuine-verification-activation.md)
uses the owner-authorised fail-closed fallback. No independent approval anchor
or reviewed observation mechanism has been designated; selecting one requires
an owner decision. Both public APIs and all production code remain unchanged.
New refusal regressions supplement the existing fabricated native/publisher tests.
Both forecast lengths, complete prior auditor identities and future enabled-code/
CI/runtime evidence remain unresolved. Review this proposal before implementing
the trusted approval mechanism; no genuine invocation is authorised.

### Stage 4B.2D.7 — offline Ed25519 approval integrity (awaiting review)

The owner selected offline Ed25519, resolving Stage 4B.2D.6's design-choice
blocker. The [signed-approval guide](stage-04b2d7-offline-signed-approval.md)
defines a strict canonical UTF-8 envelope, domain-separated real signature
verification and a complete inert 57-file intent schema. Fabricated tests use
ephemeral keys; `cryptography>=46,<47` and its dependencies are locked.
Production key/ID constants remain `None`; the new preflight and both unchanged
genuine gates refuse before inspecting arguments or accessing any paths.

Next: owner review, separate independently confirmed public-key enrolment and
reviewed genuine activation code with matching CI, complete independent evidence
(including both forecast sizes and the original auditor identity map), then
separate one-attempt permission. Signature integrity alone grants no source
access, single-use guarantee, replay authority or economic publication rights.


### Stage 4B.2D.8 — signed verification integration, unenrolled

The [owner-key and integration guide](stage-04b2d8-owner-key-enrolment-verification-integration.md)
records a separate `genuine_minute_verification_runtime.run_genuine_minute_verification`
entry point. It connects the V1 Ed25519 preflight to clean-checkout/runtime and
external code/source declarations, original scientific validators and the shared
one-use publisher. CI claims are signed owner declarations, never locally verified
GitHub attestations. At the end of Stage 4B.2D.8 both owner trust constants were
`None`; enrolment is recorded in Stage 4B.2D.9 below. The legacy public refusals,
fixture restrictions, source loaders, protocols, readiness checklist and scientific
semantics are preserved.

Implementation and fabricated tests only, awaiting owner review. Full-native test
publication is explicitly `synthetic_test_fabricated_signed_genuine_path`; no genuine
source/destination was inspected or output published. The then-outstanding steps
were review/commit/green CI, separate public-key enrolment, independent acquisition
of both missing forecast lengths and the complete historical auditor map, then a
separately signed one-attempt approval. No strategy/replay or economic authority is added.

### Stage 4B.2D.9 — owner public key enrolled locally

The [enrolment guide](stage-04b2d9-owner-public-key-enrolment.md) records the
owner-supplied 32-byte Ed25519 public key and independently pinned raw-byte SHA-256
ID. Only the verifier constants and its descriptive module sentence changed in
production source. The separate signed runtime can now in principle accept a
future valid, complete owner-signed approval; no such approval or genuine
invocation is supplied or authorised here. Invalid candidates reject before
source/destination I/O; both legacy public gates still refuse unconditionally.

Next: owner review of this uncommitted change, separate commit/push permission
and green CI for that exact future commit. Both original forecast byte lengths,
the complete historical auditor map, all future reviewed code/runtime/document
identities and the exact complete signed intent remain outstanding. Evidence
acquisition and any later single invocation need separate permission. No original
source/destination access, signing, replay, economics or deployment occurred.

## Stage 4B.2E.1 — verified-record replay seam, fabricated tests only

The [integration guide](stage-04b2e1-genuine-replay-integration.md) documents the
closed genuine replay API, private full-grid fixture adapter and minimal shared
minute accounting loop. Existing synthetic type/status gates remain unchanged.
All eight forecast accounts and 21,958 projected minute rows remain bound to
independent fixture declarations; only Ridge drives trading. Test source, result
and portfolio identities explicitly distinguish this path from synthetic replay.

The owner reports successful Stage 4B.2D.13 verification and Stage 4B.2D.14
exact-publication readback; retained evidence was not inspected or reused here.
These later declarations supersede earlier pending-verification descriptions.
Exact-publication ingestion and genuine strategy execution remain closed. Review
the uncommitted diff and the guide's disclosed initial discovery deviation before
separately authorising commit/push and CI. A later independently reviewed reader,
explicit source-access scope and separate execution/publication approvals are
required. No genuine backtest, signing, economic publication or deployment ran.

## Stage 4B.2E.2 — publication-to-replay bridge, fabricated tests only

The [bridge guide](stage-04b2e2-publication-replay-bridge.md) supersedes E.1's
pending-reader description. A private pure reader validates three supplied
publication bodies against separately trusted external byte/hash pins, retained
verification intent and science/integrity links. Full-year typed conversion feeds
the unchanged shared monetary core with distinct publication source/result and
portfolio identities. Existing fixture and synthetic boundaries remain unchanged;
the public genuine replay gate still refuses before inspection or I/O.

The original publication and private sign-off remain unread. The sign-off is
represented only by an external fingerprint claim, not an invented JSON schema
or execution authority. Review of its exact original schema after separately
authorised read-only access remains a required future integration step. No real
runner, genuine replay or economic publication is enabled. Review this uncommitted
change and its disclosed initial filename-discovery deviation before separately
authorising commit/push, CI, exact original reads, one genuine strategy evaluation,
and any immutable economic publication.

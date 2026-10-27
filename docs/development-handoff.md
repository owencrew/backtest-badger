# Development handoff — Backtest Badger

**Last updated:** 2026-10-27 (Europe/London)
**Repository:** https://github.com/owencrew/backtest-badger
**Product:** https://backtestbadger.com — *A little badger. A lot of backtests.*
**Next priority:** Owner review and first public launch of www.backtestbadger.com
on Cloudflare Workers Static Assets. Stage 5B.2 is locally prepared; no public
deployment or DNS change has occurred.
Prospective paper-trading integration remains a separate future milestone.

## Website readiness — current handoff

Read the [Stage 5B.4 report](stage-05b4-mascot-navigation-forward-feed.md) and
[Workers launch/rollback guide](deployment/website-cloudflare-workers.md).
The original owner-supplied mascot is integrated as lossless WebP. Navigation is
Home, The Burrow, The Dig, Field Guide, Field Notes, About. All four Field Notes
and three guides are approved by unchanged source hashes; 004 remains featured.
Search metadata is prepared and indexing remains disabled.

Read-only Lightsail inspection on 27 October reconfirmed release
`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`. A private genuine candidate from 160
forecasts and 158 outcomes passed both frozen Python and browser validators.
No public feed was identified or activated. The Burrow retains the truthful
unavailable state. The local staging/optional R2 publisher is prepared and tested;
its external-write mode was not executed. See the report for the candidate hash,
resource measurements, dedicated R2 recommendation, exact approval scope and rollback.

Next: owner review, separately authorised commit/push and exact-SHA CI, then
separately approved feed infrastructure/publication and first website deployment.
Do not deploy or install jobs under this stage's read-only authorisation. DNS and
indexing remain separate gates. Frozen science and historical figures are unchanged.

Sections below retain the earlier research/operations handoff. Its description of
website planning and draft publication is historical; use this current section
and the Stage 5B.3/5B.4 reports for frontend status.

## 1. Resume here

Read [AGENTS.md](../AGENTS.md), [README](../README.md),
[architecture](architecture.md), [roadmap](roadmap.md), the
[E.5g genuine backtest report](stage-04b2e5g-first-genuine-historical-backtest.md)
and the [production runbook](deployment/production-infrastructure.md).
The production runbook now includes the **24 October D3B.1 promotion**:
`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1` is active on Lightsail.
See the [retry report](deployment/lightsail-d3b1-release-retry.md) for verified
operations and pending forecast-provenance observations. Never infer that a newer
GitHub HEAD is deployed.

Historical E.5h starting branch: `main`, clean at
`ed69f8b3f18592bec183e058c6659e59a0641f42` (E.5g report).
The implementation explicitly identified as reviewed in the
[E.5f record](stage-04b2e5f-genuine-preflight.md) and E.5g report is
`c39f572c046253b196c12b476c9170d71b0468bb` (E.5e local runner).
At the earlier E.5h review, GitHub's Actions API was checked on 24 October: [CI run 40084535405](https://github.com/owencrew/backtest-badger/actions/runs/40084535405)
completed successfully for that exact implementation commit. That report
commit's [CI run 40105024756](https://github.com/owencrew/backtest-badger/actions/runs/40105024756)
was still in progress when checked; success and separate review approval for that
commit are not inferred. These were dated E.5h observations. D3B.1 subsequently rechecked
[CI run 40106649560](https://github.com/owencrew/backtest-badger/actions/runs/40106649560):
`completed / success` for the exact now-active candidate. Deployment does not
validate later uncommitted documentation changes.

This file describes current capabilities and next work. Detailed stage guides
preserve the authorisations, limitations and tests at their original stage;
“not yet executed” in those records does not undo a later documented milestone.

## 2. Implemented capabilities and evidence boundaries

| Area | Current capability |
| --- | --- |
| Foundation | Python 3.12, uv lockfile, pytest/Ruff, GitHub Actions and CLI; plain functions and minimal dependencies |
| Market data | Binance Spot BTCUSDT/ETHUSDT archives and recent REST; exact PostgreSQL candles, immutable revisions, visible gaps and frozen exports |
| Research | Causal features, chronological partitions, train-only fixed models and retained validation forecasts; untouched holdout policy preserved |
| Earlier economics | Stage 2C hourly fixed-window round trips and Stage 2D cost diagnostics; preserve their original results |
| Minute research | Verified native-minute release, exact hourly/minute price parity, authenticated forecast/reference publication, simple local runner and completed genuine 2024 backtest |
| Forward evidence | Genuine timestamped forecasts, automated collection, immutable scored outcomes and prospective accuracy reports; timely/late cohorts remain distinct |
| Paper foundations | Deterministic strategy, execution and Decimal accounting/valuation primitives; no complete prospective order/fill/portfolio service |
| Hosting | Lightsail PostgreSQL and collection/scoring, plus backups, restore drills and monitoring, in the dated production snapshot |
| Public product | Local static website and genuine Binance dashboard implemented; Workers launch prepared. Private genuine candidate validated; public feed not connected; all seven articles approved |

Historical backtests simulate the past. Forward predictions are issued before
outcomes but do not create orders. Prospective paper trading will simulate
execution as new evidence arrives. Real trading uses actual money and orders;
it is not implemented or authorised. No result establishes a trading edge.

## 3. Latest research and the local execution decision

[E.5g](stage-04b2e5g-first-genuine-historical-backtest.md) records exactly one genuine
2024 native-minute economic replay on 24 October. All six independent accounts
passed ledger verification; separate `verify-output` returned exit 0. The outer
resource-statistics wrapper failed after execution because of a sandbox
restriction; this was not a failed replay and did not cause a retry.

| Market | Ridge return | Cash return | Buy & Hold return | Ridge total costs (USDT) |
| --- | ---: | ---: | ---: | ---: |
| BTCUSDT | −60.69% | 0.00% | +120.81% | 9,932.12 |
| ETHUSDT | −57.96% | 0.00% | +46.18% | 9,239.49 |

Figures are rounded from E.5g. Every account starts with 10,000 USDT. Final values
are marked at December 31 23:00 UTC; Buy & Hold has unsold assets and no terminal
liquidation cost. Ridge made 570 buys/570 sells for BTC and 499/499 for ETH.
Costs are 10 bps fee, 1 bp half-spread and 2 bps adverse slippage per side.
They are frozen assumptions, not measured historical fills.

The retained Ridge forecasts use source-open +4h+60s availability and the strictly
next minute opening: 12:01 → 12:02. Continuous holdings differ from Stage 2C's
13:00 entry/16:00 exit rule; comparing their results does not isolate execution
frequency. Previously inspected 2024 data, correlated markets, assumed latency
and absent liquidity/market-impact evidence limit conclusions. No refit, tuning,
frictionless replay or holdout evaluation occurred in E.5g.

The [E.5e decision](stage-04b2e5e-local-execution-decision.md) and
[runner guide](stage-04b2e5e-simple-local-historical-runner.md) define the operational
route: one local process, four explicit retained files, size/hash and sign-off
validation, unchanged science, explicit `run --execute`, and fresh output
directories with completion checks. E.5d's privileged supervisor, custody,
signature and OS-installation prerequisites do not apply to this separate route.
It protects against ordinary mistakes and inconsistent evidence, not a malicious
developer or compromised local process. Old fabricated contracts and refusal
gates remain unchanged. E.5f established genuine preflight compatibility; E.5g
established successful genuine execution. Neither is still pending.

## 4. Production boundary and remaining operational evidence

The [production runbook](deployment/production-infrastructure.md) records the
successful **24 October 20:58 UTC** promotion from
`e0d622d51e1edc120fb4f1b5229e46907ed6219d` to
`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`. The old environment remains available.
The [D3B incident](deployment/lightsail-d3b-release-promotion.md) is unchanged;
[D3B.1](deployment/lightsail-d3b1-release-retry.md) corrected the temporary helper
collision, tested real staged commands and completed one authorised retry.

Both worker runtime validators and DB health passed. PostgreSQL 17.11 remains
healthy at Alembic **0001**, with unchanged schema fingerprint. A **23.9-second**
timer pause missed no scheduled ticks. Natural collection completed **21:01:06 UTC**
and scoring **21:02:12 UTC**, both successfully with exit **0**. All **250** original forecast/outcome files
retained their hashes; offline checks found **124 scored, 2 pending**, no invalid
evidence, missed horizons or mature-unscored backlog. Existing late classifications
remain. These are operational counts, not performance claims.

The first new candidate-era four-hour issuance is expected **25 October 00:01 UTC**.
Actual publication/dependency hashes and subsequent scoring (earliest eligibility
**04:01 UTC**, scheduled check **04:02**) remain pending. Keep both runtimes and
original records: dependency-file changes create a new recipe-fingerprint epoch.
No manual cycles, backfilling, historical research or website deployment occurred.

Daily off-machine backups and local retention succeeded unattended on 17–24 October;
the 18 October isolated restore matched exact database fingerprints. Their freshness
and evidence were rechecked before promotion. External AWS alert delivery,
missing-invocation monitoring, the exactly-four-checkpoint cleanup restriction and
disabled remote restic pruning remain separate operational items. Do not restart
old Mac schedulers or alter production to reconcile historical documentation.

## 5. Next product milestone — the public website

The first website can use the following existing material:

- **The Dig:** verified E.5g summaries, six-account strategy/benchmark comparisons,
  costs, trade counts and disclosed hourly drawdowns. Use the report's exact
  figures as source; label rounded values and funding-relative returns. Any later
  charts must use verified series with their actual endpoints, never invented
  curves from summary statistics.
- **The Burrow:** existing prospective forecast/outcome evidence, presented as
  forecast accuracy rather than returns. Preserve issuance times, timely/late
  cohorts, matched sample counts, missing outcomes and preliminary-sample warnings.
  [Stage 3C](stage-03c-forward-evaluation.md) and
  [Stage 3D](stage-03d-automated-outcome-scoring.md) define the contracts; a dated,
  sanitised content export is still needed for current public statistics.
- **Field Notes:** [001–004](field-notes/README.md) are draft articles for editorial
  review. 003 explains the genuine backtest; 004 explains native-minute integrity
  and causal execution. Draft presence is not publication approval.
- **Methodology and limitations:** link the research protocol and reports, state
  the inspected 2024 period, timing/cost assumptions, independent funding,
  partial endpoints and lack of proven market fillability. Keep historical,
  forward and future paper-trading labels visible beside the relevant figures.

Practical next scope: define the page/content structure, prepare a small reviewed
public data contract from existing summaries, design accessible research views,
and implement the website in a separately scoped stage. Acceptance should cover
source attribution, readable methodology, responsive layouts, accessible tables
and charts, clear data dates and no private evidence exposure. Public database
queries, if needed, must be read-only. No framework is selected here.

Paper portfolio screens must wait for Stage 4C–4E: persistent order/fill/ledger
integrity, prospective quote/filter collection, worker integration, activation and
reporting remain unimplemented. The approved [Stage 4A specification](stage-04a-paper-trading-spec.md)
and [prospective protocol](stage-04a-prospective-evaluation-protocol.md) retain those
requirements. The website can begin with research and forecasts without implying
paper portfolios already exist. Hosting changes and public launch need their own
scope and authorisation.

## 6. Review and continuity

E.5h changes documentation only. Original technical stage reports, frozen methods,
source code, private inputs and research outputs remain unchanged. No economics,
model fitting, database operations, AWS work, commit, push or deployment is part
of this stage. Maintain a concise current handoff; retain historical details in
the linked reports and Git history.

Remaining documentation work: review the draft articles for publication, prepare
dated public forward-statistics content, and complete the pending forward
provenance/scoring observations in the D3B.1 report. Older guides deliberately retain their original gates;
use the architecture/roadmap current summaries to interpret them.

E.5h validation: 150 local Markdown links/anchors (including incoming links to
changed documents), E.5g table rounding, draft metadata, whitespace and verbatim
prompt comparison passed. Repository-wide Ruff lint and formatting passed (225
files formatted). All other tracked files match the starting HEAD. No pytest,
source authentication or economic replay was run for this documentation change.

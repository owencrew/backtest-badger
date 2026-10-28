# Stage 5B.6 — Forward dashboard refinement and live feed verification

28 October 2026, Europe/London (UTC on this date). Local implementation for owner
review, starting from clean Git commit `889bcf3`. No commit, push, public website
deployment, DNS/resource/credential change, production write, service/timer change,
training or backtest occurred. The owner's existing ignored local feed configuration
was used unchanged. The sibling historical repository was not accessed.

## Scheduled pipeline: observed evidence

Read-only SSH through `Ubuntu-1` inspected timer enablement, the requested 60-line
publisher/checker journals, service results and the two retained validated snapshots.
Both publication timers are **enabled**. `list-timers` reported the publisher's last
trigger at 09:23 UTC and checker's at 09:26 UTC, with next triggers 09:33/09:36.
Ten consecutive publisher runs from 07:53 through 09:23 started on the configured
ten-minute schedule and finished successfully. The checker journal included fifteen
successive scheduled `public-feed-healthy` results from 07:06 through 09:26.
These are scheduled cycles, not just the initial manual activation executions.

Two successive confirmed cycles (28 October, UTC):

| Publisher start | Evidence cutoff (`as_of`) | Generation (`generated_at`) | Independent check |
| --- | --- | --- | --- |
| 09:13:00 | 2026-10-28T09:13:17.629131Z | 2026-10-28T09:13:32.735041Z | Healthy at 09:16:03 |
| 09:23:00 | 2026-10-28T09:23:17.284074Z | 2026-10-28T09:23:32.771830Z | Healthy at 09:26:03 |

Public SHA-256 respectively:

- `39e7ec0d07faf4b5898be786b88be9881a92ef35519cc4157bcbdb993b22cb99`
- `275ddc9d0128edb925afcf91a7cf968cc791eb7df6852ca7e36c9e6420c545da`

An in-memory comparison of `previous-success.json` and `last-success.json` confirmed
that **both complete `latest` arrays and complete `evaluations` arrays were equal**
across those two publications. Only the snapshot clocks advanced. No new prediction,
new outcome or retimed issuance is claimed for that interval.

Publisher/checker unit results were `success`, exit status 0. Publisher runs in the
inspected sample took 35.91–37.10 seconds, about 9 seconds CPU, and 197,520–198,020 KiB
peak RSS. The collector exited successfully at 09:31:05 and scorer at 09:32:12, both
status 0; their timers continued on their existing schedules. No changes were made
to either. `systemctl --failed` lists the historical D3B promotion supervisor:
[the prior retry report](deployment/lightsail-d3b1-release-retry.md) explicitly records
its intentional retention as incident evidence. It is not a newly failed research
or publication unit, and was left untouched.

## Public contract and local integration

The existing `check-forward-endpoint.ts` passed against the owner's actual R2
endpoint using the pinned Node 24.22.1 runtime. The initially confirmed object was
10,975 bytes, matching the second SHA-256 above. The checker verifies the complete
strict public schema, both markets, freshness, current source issuance, size,
HTTP 200, JSON content type, `public, max-age=60, must-revalidate` and www CORS.
Unknown fields are rejected throughout the contract. The accepted payload contains
only the allowed public fields: no private paths, journals, credentials or training
artifacts. This is a payload validation, not a bucket-wide account inventory.

Both development (port 3000) and local Wrangler production preview (port 8787)
loaded the genuine HTTPS feed directly in the browser, demonstrating allowed local
CORS. No synthetic fixture, private candidate or one-off snapshot was connected to
any running site or copied to public/export assets. The temporary endpoint is not
hardcoded in application source. Its appearance in the verbatim prompt archive is
historical request context only.

During browser review the cutoff advanced to **2026-10-28 09:33:17 UTC**, generated
**09:33:33 UTC**. Both markets showed source close **08:00 UTC**, target close
**12:00 UTC**, timely automated, outcome pending. BTC issued **08:01:12 UTC** and
ETH **08:01:22 UTC**. These are display precision; the original microsecond timestamp
strings remain inspectable in technical details. Each market separately had
83 issued / 82 matched / one pending / zero mature-unscored primary observations,
one missing primary opportunity, one issued/matched late manual observation and
zero unattributed observations. Counts are observed data, never hardcoded UI values.

Two initial/reload production-preview requests timed out before obtaining data;
the page truthfully showed unavailable and no verified snapshot. Manual refresh
recovered fresh genuine evidence after the first timeout. The resumed review
loaded the genuine feed successfully on initial navigation. No application console errors were recorded after recovery.
This documents an observed transient request failure, not a promise of uninterrupted
network access. The feed's stale, failure-with-retained-data, pending, settling,
mature-unscored and scored render states are covered by isolated tests. Network
failure and maturation were not forced by altering the live feed or system clock.

Final independent HTTPS recheck after the final build passed with cutoff
**2026-10-28T09:43:17.833570Z**, generated **2026-10-28T09:43:33.122979Z**,
10,975 bytes and SHA-256
`f263deea0caad6ef576b064a92ce15ba3508170a39945e12710b2b0c20e490ea`.
This was fresh at verification; freshness is an observation, not a permanent status.

After the usage-limit interruption, verification resumed at approximately 15:10 UTC.
The local Wrangler process had stopped and was restarted on loopback only. The
final HTTP smoke test passed again. The latest independent public checker result
was **healthy**, cutoff **2026-10-28T15:03:17.505078Z**, generated
**2026-10-28T15:03:32.714194Z**, 10,982 bytes, SHA-256
`ceea6b23892f82ed58cc709cbc463abeaa09bde678c461c21d0475d55f24741d`.
The final browser review loaded that genuine snapshot: both markets now had source
close 12:00 UTC, target close 16:00 UTC, pending outcomes and 84 issued / 83 matched
primary observations each. This later evidence was naturally issued/scored by the
existing research system, without intervention. Final desktop prediction/detail
screenshots reflect the later snapshot; earlier screenshots retain their actual
capture times and counts. The corrected strict-sign methodology was verified in
the final production browser view.

## Homepage and dashboard presentation

Removed exactly **No hype** and **Honest negative results** from the homepage. The
remaining hero labels and evidence strip balance using existing responsive styles;
no filler or hero redesign was needed. The headline, tagline, original mascot,
embedded candlesticks, colours, typography, historical Ridge losses and other
research messages remain intact. Navigation remains Home → The Burrow → The Dig →
Field Notes → Field Guide → About. Field Note 004 remains featured.

The default forecast view now contains:

1. Separate BTCUSDT/ETHUSDT cards: status, cohort, snapshot freshness, target/source/
   issuance UTC times, four model forecasts and an explicitly unscored or scored
   realised outcome. Each card expands to its recipe identity and original values.
2. Primary timely automated evaluation for each market, visible without opening a
   disclosure. Counts, four models, MAE/RMSE/bias, correct/eligible counts and
   directional percentages remain descriptive, with the under-100 warning.
3. **Late manual forecasts**, collapsed with per-market issued/matched counts in
   its summary. It explains the additional-information timing advantage, keeps all
   metrics and qualifies small-sample percentages. It never pools primary and late.
4. **Detailed forecast evaluation**, collapsed: methodology, exact cohort accounting,
   pending/mature-unscored/missing counts, earliest target, cutoff/generation,
   recipe-pooling limitations, unattributed results and the entire validated public
   snapshot in its original units, including all models and cohorts.

Presentation conversion is **log return × 10,000**. One basis point means 0.0001
log-return units; no exponential conversion to simple returns occurs.

| Original log return | Display |
| --- | --- |
| 0.0002 | +2.00 bps |
| -0.0005 | −5.00 bps |
| 0 | 0.00 bps |
| 0.0000002 | +2.00e-3 bps |

Below 0.01 bps, three-significant-digit scientific notation avoids rounding nonzero
values to zero. The same conversion is used for realised return, MAE, RMSE, bias
and signed error. Signed error and bias retain prediction-minus-outcome sign.
Directional accuracy stays a percentage. Under the frozen strict-sign evaluator,
only zero predictions abstain; nonzero predictions against zero outcomes remain
eligible and count as incorrect. The displayed methodology and its regression test
explicitly preserve this distinction. Technical JSON preserves original numeric
values; squared errors stay in squared log-return units. Null/undefined metrics do
not become zero.

Zero directional accuracy reads **N/A — zero forecast**, retains **0 / 0**, and
explains the zero eligible denominator; defined Zero MAE/RMSE/bias still display.
Other zero denominators read **N/A — no eligible directions**. A cohort with no
issued observations says **No observations recorded in this cohort.** Issued but
unmatched cohorts instead say **No matched outcomes recorded in this cohort.** Both
explain why metrics cannot yet be calculated. A validated newly populated cohort
automatically renders its table; no current count is encoded in application code.

## Responsive and accessibility review

Inspected homepage and Burrow in both Next.js development and Wrangler production
preview at **1440, 768, 390 and 320 pixels**. At every width, document scroll width
equalled viewport width. Cards share a row at 1440 and stack at 768/390/320. Full
mascot and soil candlesticks remain visible. All model names and values are readable;
long tables scroll inside their labelled regions instead of widening the page.
Original JSON details also stay inside a bounded scroll region.

Native `details`/`summary` controls opened with pointer click and Enter and closed
with Space. Focus outlines were visible; Tab moved between named table regions.
At 320px, ArrowRight moved the primary table's horizontal offset from 0 to 39.5px
within its 286px client width / 815px content width. Headers have column/row scopes
and captions. Mobile text explains horizontal scrolling and keyboard controls.
Disclosure targets measured at least 44px tall (observed 51.8px and above), supporting
touch use. Actual physical touch-device and screen-reader testing were not performed;
these are responsive browser, keyboard, semantics and target-size checks.

## Validation

Pinned Node **24.22.1**, pnpm **11.25.0**. Executed:

| Check | Result |
| --- | --- |
| ESLint | Passed |
| TypeScript (`tsc --noEmit`) | Passed |
| Prettier | Passed |
| Frontend tests | 88 passed, no skips |
| Production static build | Passed; all seven approved articles included |
| Publication/export audit | 8 passed (also included in the 88-test suite) |
| Local Wrangler HTTP smoke | Passed: 13 routes, redirects, refresh, six assets, real 404s |
| Public HTTPS checker | Passed, full schema/coverage/clocks/HTTP/CORS |
| Prompt archive byte comparison | Exact match |
| Scientific/editorial source comparison against HEAD | Unchanged |

The tests cover both cards, all models, signed/zero/tiny bps, null/undefined values,
direction counts/percentages, Zero N/A, visible primary evaluation, closed secondary
and technical disclosures, dynamic empty-to-populated cohorts, unmatched states,
UTC clocks, freshness/errors, immutable rendering and the unchanged contract.
Existing polling cancellation/regression, publication approvals, fixture-leakage,
research reconciliation and navigation tests remain green. Export tests assert the
two unwanted homepage phrases are absent while retained messages/figures remain.

Initial SSH/network and Wrangler smoke attempts were blocked by the local sandbox;
authorised read-only network/local-preview escalation succeeded. No policy rejection
or unresolved access blocker remains. No Python file changed, so Python tests were
not run. Generated Next route-type pointer changes were restored to the starting
tracked content rather than included as a source change.

## Screenshots

Local ignored artifacts under `artifacts/stage-5b6/screenshots/` (not deployed):

- `dev-home-{1440,768,390,320}.jpg` and `production-home-{1440,768,390,320}.jpg`.
- `dev-predictions-{1440,768,390,320}.jpg` and `production-predictions-{1440,768,390,320}.jpg`.
- `production-primary-{1440,320}.jpg`, `dev-primary-320.jpg`.
- `dev-details-1440.jpg`, `production-details-1440.jpg`.
- `dev-empty-320.jpg`, `production-empty-390.jpg`, `production-late-768.jpg`.

[Desktop homepage](../artifacts/stage-5b6/screenshots/production-home-1440.jpg) ·
[Mobile homepage](../artifacts/stage-5b6/screenshots/production-home-390.jpg) ·
[Latest BTC/ETH](../artifacts/stage-5b6/screenshots/production-predictions-1440.jpg) ·
[Primary evaluation](../artifacts/stage-5b6/screenshots/production-primary-1440.jpg) ·
[Expanded details and empty cohorts](../artifacts/stage-5b6/screenshots/production-details-1440.jpg).

## Changed files and launch handoff

- `web/app/page.tsx`: the two requested copy removals.
- `web/components/forward-dashboard.tsx`: hierarchy, disclosures and explicit states.
- `web/lib/forecast-display.ts`: presentation-only model labels/bps/direction formatting.
- `web/app/globals.css`: cards, disclosures, bounded details and responsive scrolling hints.
- `web/tests/forecast.test.ts`, `web/tests/export.test.ts`: requested regressions.
- `web/README.md`, this report, prompt archive and `prompts/README.md`: current status
  and traceable request record.

The JSON validator/schema, use-feed/polling, public exporter/checker, scientific
calculations, model recipes, historical evidence, all seven article sources and
SHA-256 approvals were not modified. No environment endpoint was changed.

Recommended Conventional Commit after owner review:
`feat(web): refine forward dashboard and homepage presentation`

Remaining launch work:

1. Owner review of this local candidate and screenshots; commit/push only when requested.
2. Explicitly approve the first Workers Static Assets candidate deployment using
   the existing [launch runbook](deployment/website-cloudflare-workers.md), keeping
   indexing disabled. The website has not been deployed here.
3. Decide the production feed hostname and approve its separate DNS/R2 setup; the
   existing r2.dev URL remains the temporary development endpoint. Review the exact
   candidate-origin CORS requirement before a workers.dev integration check; current
   successful local CORS does not demonstrate access from a new candidate origin.
4. Verify the deployed candidate, genuine feed and all approved article routes before
   owner-approved www/DNS promotion. Preserve existing website/mail routing and use
   the documented rollback. Enable indexing only under the later explicit www approval.
5. Continue operational monitoring of publication/checker health and resource growth.
   Existing systemd checks provide local logs/status; no external notification service
   was added. Keep the original scientific observations and failure history intact.

Stop for owner review. The next milestone is the first public Backtest Badger
Cloudflare Workers Static Assets deployment.

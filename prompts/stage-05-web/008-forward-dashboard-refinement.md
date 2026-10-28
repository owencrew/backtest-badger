# Backtest Badger — Stage 5B.6: Forward Dashboard Refinement, Homepage Polish and Live Feed Verification

## Objective

Complete three focused improvements before the first Cloudflare Workers deployment:

1. Verify that the scheduled Lightsail → Cloudflare R2 forward-data pipeline is operating reliably.
2. Improve the presentation of genuine forward forecasts and evaluation statistics in The Burrow.
3. Refine the homepage's first impression by removing two unnecessarily negative introductory phrases.

Preserve the existing scientific calculations, validated data pipeline, publication controls and overall website design.

Do not commit, push or deploy the public website.

## 1. Starting context

Repository:

`~/Code/backtest-badger`

Read:

- `AGENTS.md`
- `web/README.md`
- `docs/stage-05b-market-dashboard.md`
- `docs/stage-05b4-mascot-navigation-forward-feed.md`
- `docs/stage-05b5-forward-feed-activation.md`
- `docs/deployment/forward-feed-cloudflare-setup.md`
- `web/app/page.tsx`
- `web/components/forward-dashboard.tsx`
- `web/lib/forecast.ts`
- `web/components/use-feed.ts`
- `web/tests/forecast.test.ts`
- `web/app/globals.css`

Inspect the latest Git state and preserve uncommitted work.

The owner has manually configured:

- Cloudflare R2 bucket `backtest-badger-forward`
- Restricted Lightsail publishing credentials
- Temporary public R2 development endpoint
- CORS policy
- Publisher and independent verification services
- Both recurring systemd timers
- Local `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL`

The genuine public feed is:

`https://pub-0bc497d5cf374940a457d2529f7c55b4.r2.dev/forward-v1.json`

The local Burrow has successfully displayed genuine BTCUSDT and ETHUSDT predictions and evaluation statistics.

## 2. Verify scheduled publication

The initial manual export and independent HTTPS verification succeeded.

Both systemd timers were subsequently enabled.

The publisher runs at minutes 03/13/23/33/43/53 UTC; the independent checker runs three minutes later.

Read-only SSH verification through `ssh Ubuntu-1` is authorised, subject to normal environment access approvals.

Inspect:

```bash
systemctl list-timers --all 'backtest-badger-public-feed*'

systemctl is-enabled backtest-badger-public-feed.timer
systemctl is-enabled backtest-badger-public-feed-check.timer

sudo journalctl -u backtest-badger-public-feed.service -n 60 --no-pager

sudo journalctl -u backtest-badger-public-feed-check.service -n 60 --no-pager
```

Verify that at least two scheduled publication cycles, rather than only manual executions, have completed successfully.

Confirm:

- Publisher execution succeeds.
- Independent checker reports `public-feed-healthy`.
- `as_of` and `generated_at` advance across successful cycles.
- Public JSON passes the complete validation contract.
- BTC and ETH are both present.
- No unexpected private fields or credentials are exposed.
- Unchanged predictions are not fabricated or relabelled.
- The existing collector and scorer remain unaffected.

If fewer than two scheduled cycles have occurred, report that accurately.

Do not make production changes without separately scoped authorisation. Investigate read-only and report any operational issues.

## 3. Homepage copy refinement

The owner wants the homepage to feel welcoming, professional and confident, rather than overly focused on unsuccessful strategies or defensive language.

In `web/app/page.tsx`, remove these two exact phrases:

- **"No hype"** — currently in the hero's short supporting labels.
- **"Honest negative results"** — currently in the "Built on evidence" strip.

Do not replace them with similar negative or defensive wording.

Preserve the other existing homepage messages, including:

- Open source
- Reproducible research
- Real market data
- Explicit trading costs
- Independent benchmarks

Keep the homepage's central headline:

**Dig into the evidence.**

And tagline:

**A little badger. A lot of backtests.**

### Visual layout

After removing the two phrases, ensure the hero supporting labels and evidence strip still look balanced.

Adjust spacing or layout only where necessary.

Avoid introducing arbitrary filler text simply to restore the previous number of labels.

Keep the overall visual identity:

- Original owner-supplied badger mascot
- Charcoal background
- Forest-green accents
- Warm-sand highlights
- Existing typography and responsive structure

Do not redesign the hero.

### Preserve research integrity

The intention is to improve first impressions, not obscure the historical research.

Continue to present the genuine negative Ridge backtest results accurately in The Dig and existing research sections.

Do not change verified performance figures or risk disclosures.

The site should project curiosity, rigorous analysis and transparency without unnecessarily leading with failure-oriented messaging.

## 4. Redesign The Burrow's forward section

The current forward dashboard contains two latest-forecast cards, six cohort evaluation tables, multiple undefined values and lengthy decimal representations.

Make it easier to interpret while retaining complete access to the underlying evidence.

### A. Latest predictions

Retain separate BTCUSDT and ETHUSDT forecast cards.

Each should clearly show:

- Latest forecast status
- Source candle close
- Forecast issuance time
- Target close time
- Four model predictions
- Realised outcome, when scored
- Evidence cohort
- Snapshot freshness

Keep all timestamps in UTC.

Establish a stronger visual hierarchy so the latest predictions are immediately understandable.

Do not treat pending forecasts as scored outcomes.

Keep the existing methodology accessible.

### B. Convert log-return presentation to basis points

The underlying forecasts are four-hour close-to-close logarithmic returns.

Display them as log-return basis points:

`log-return bps = log return × 10,000`

Examples:

- `0.0002` → `+2.00 bps`
- `-0.0005` → `−5.00 bps`
- `0` → `0.00 bps`

Use the label:

**Four-hour predicted log return (bps)**

Explain that one basis point corresponds to 0.0001 log-return units.

Do not silently convert logarithmic returns into simple percentage returns.

Retain sufficient precision for very small nonzero predictions.

Preserve the exact underlying values and public JSON schema.

Apply the same unit conversion consistently to displayed MAE, RMSE, forecast bias and signed error.

Directional accuracy remains a percentage.

Retain original decimal representations in technical details where appropriate.

### C. Primary evaluation

Present the `primary_timely_automated` cohort prominently by default.

Include separate BTC and ETH evaluations with:

- Matched observation count
- MAE (log-return bps)
- RMSE (log-return bps)
- Forecast bias (log-return bps)
- Correct / eligible direction counts
- Directional accuracy
- All four model names

Maintain the preliminary sample warning when fewer than 100 observations are matched.

Do not highlight a model as the best based solely on these results.

Do not imply statistical significance or trading profitability.

### D. Zero baseline

The Zero model predicts exactly zero.

Under the frozen strict-sign directional protocol, it has no eligible directional predictions.

Instead of an unexplained `Undefined`, display:

**N/A — zero forecast**

Explain that its directional denominator is zero.

Retain the `0 / 0` count.

Show its MAE, RMSE and bias when defined.

Never display an undefined directional accuracy as 0%.

### E. Late manual observations

Move `secondary_late_manual` evaluation results into an expandable section labelled:

**Late manual forecasts**

Show the observation count clearly.

Explain that late forecasts are not directly comparable with timely automated predictions because they can benefit from additional information timing.

Retain the complete metrics inside the expanded view.

Clearly qualify percentages based on very small samples.

Do not pool late observations with primary forecasts.

### F. Empty cohorts

The `timely_unattributed` cohort currently has zero observations.

Instead of two full tables containing undefined statistics, display a concise empty-state message:

**No observations recorded in this cohort.**

Explain that evaluation metrics cannot be calculated without matched outcomes.

Determine this dynamically from the validated feed.

If observations become available later, render the appropriate evaluation table automatically.

Do not hardcode the current counts.

### G. Detailed evaluation

Provide an expandable section such as:

**Detailed forecast evaluation**

Retain the complete research context:

- All cohorts
- All models
- Issued and matched counts
- Pending and mature-unscored observations
- Missing primary opportunities
- Earliest target close
- Evidence cutoff
- Model recipe identity
- Recipe-pooling limitations
- Methodology explanations

Technical visitors should still be able to inspect the complete evidence.

Do not discard data or alter the JSON contract.

## 5. Snapshot freshness and error states

Preserve the existing feed polling and regression safeguards.

The interface must correctly distinguish:

- Loading
- Fresh published snapshot
- Stale snapshot
- Request failure with retained last-good data
- No feed configured
- Pending prediction
- Settling target
- Mature unscored outcome
- Scored outcome

Display the actual evidence cutoff and generation time.

A successful HTTP fetch is not itself a newly issued forecast.

Keep manual refresh, background polling and visibility-aware cancellation.

## 6. Mobile usability

Inspect at:

- 1440px desktop
- 768px tablet
- 390px mobile
- 320px narrow mobile

Ensure:

- BTC and ETH cards stack correctly.
- Models and numbers remain readable.
- Long tables use accessible horizontal scrolling where needed.
- Disclosure controls work with mouse, touch and keyboard.
- No page-width overflow occurs.
- The revised homepage labels remain visually balanced.
- The original mascot and embedded candlesticks remain clearly visible.

Use the existing CSS design system.

Do not introduce Tailwind or a new UI framework.

## 7. Scientific and editorial safeguards

Do not modify:

- Predictions or outcomes
- Model recipes
- Forecast timestamps
- Evaluation calculations
- Cohort definitions
- Matched observation counts
- Frozen protocols
- Public JSON schema
- Publication schedule
- Historical backtest evidence
- Approved Field Note or Field Guide source files
- Editorial SHA-256 approvals

Field Note 004 must remain featured.

The main navigation remains:

**Home → The Burrow → The Dig → Field Notes → Field Guide → About**

Keep the shorter name "Field Guide".

All changes to forecast numbers must be presentation-only conversions or formatting.

Null must not become zero.

## 8. Testing

Extend the frontend tests to cover:

1. BTC and ETH prediction cards.
2. All four model forecasts.
3. Positive, negative and zero basis-point formatting.
4. Very small nonzero values.
5. Null and undefined metrics.
6. Directional count and percentage presentation.
7. Zero baseline accuracy as N/A.
8. Primary evaluation visible by default.
9. Late manual disclosures.
10. Empty unattributed cohort.
11. Automatic rendering when an empty cohort receives observations.
12. UTC timestamps.
13. Fresh/stale/error states.
14. Preservation of the public JSON validation rules.
15. No synthetic fixture leakage.
16. Removal of "No hype" and "Honest negative results" from the exported homepage.

Run:

- ESLint
- TypeScript
- Prettier
- Frontend unit tests
- Production static build
- Publication/export audit
- Local Wrangler HTTP smoke tests
- Relevant Python tests only if Python files are changed

Keep all seven published articles and their exact approvals intact.

## 9. Browser review

Inspect the revised homepage and Burrow in:

1. Next.js local development.
2. Local Wrangler static production preview.

Use the genuine public R2 feed for the integration check.

Do not hardcode the temporary endpoint into tracked source files.

Inspect and capture screenshots of:

- Homepage desktop/mobile
- Latest BTC and ETH predictions
- Primary evaluation
- Expanded detailed statistics
- Empty cohort presentation

Confirm that the revised homepage no longer contains the two unwanted phrases.

Do not deploy publicly.

## 10. Documentation

Create:

`docs/stage-05b6-forward-dashboard-refinement.md`

Document:

- Actual scheduled publication verification
- Evidence timestamps
- Homepage copy changes
- Default forecast dashboard layout
- Basis-point presentation convention
- Zero-baseline and empty-cohort handling
- Accessibility checks
- Test results
- Local production-preview results
- Screenshots
- Remaining launch tasks

Update relevant frontend documentation only where necessary.

Archive this complete prompt at:

`prompts/stage-05-web/008-forward-dashboard-refinement.md`

Update `prompts/README.md`.

## 11. Hard boundaries

- No Git commit or push
- No website deployment
- No DNS changes
- No Cloudflare resource changes
- No credential changes
- No R2 or CORS modifications
- No Lightsail service or timer changes
- No research collector/scorer changes
- No modifications to frozen scientific evidence
- No model training or new backtests
- No edits to published article source files
- No public forecast schema changes
- No paid infrastructure

Read-only operational verification is authorised, subject to normal access approvals.

If an operational fault is discovered, investigate and report it without making unapproved production changes.

## 12. Completion report

Provide:

1. Publisher and checker health verification.
2. Latest confirmed public snapshot freshness.
3. Homepage changes.
4. Dashboard layout changes.
5. Basis-point formatting examples.
6. Zero-baseline and empty-cohort handling.
7. Desktop/mobile screenshots.
8. Accessibility verification.
9. Tests and build results.
10. Changed files.
11. Recommended Conventional Commit message.
12. Remaining steps before the first Cloudflare Workers deployment.

Stop for owner review.

**The next milestone is the first public deployment of Backtest Badger on Cloudflare Workers Static Assets.**
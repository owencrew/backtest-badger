# The Dig — Study 002 integration and editorial draft

**Unpublished; owner review required.** This file and the generated review assets
live outside the Next.js application, static assets and production content loader.
They are not referenced by a public route or sitemap. Opening `review.html`
locally does not approve publication. No existing editorial hash changes.

## Smallest safe integration after approval

Keep `/dig/` and its approved Study 001 experience intact. Add a small study-card
index above the current study, with two explicit versioned entries. Initially,
Study 001 links to its existing section; Study 002 can link to a dedicated
`/dig/study-002/` only after approval. Later, a separately reviewed redirect can
move Study 001 to `/dig/study-001/` without breaking existing links. Do not build
a general experiment framework or mix constants from the two studies.

Each card should include study number/title, research classification, decision
rule, period, evidence date, publication status, one balanced finding and a source
link. A study selector may navigate between pages; the market selector remains
within each study and must not imply combined funding or independent replications.

Dedicated Study 002 view, in order:

1. “Can a Slower Trend Beat the Noise?” and a visible **Historical simulation** label.
2. A plain-language question and the fixed 30-day daily rule.
3. BTC/ETH selector, independent account table, net returns and drawdown.
4. Equity and drawdown charts with a shared scale per market; clear strategy legend.
5. Long/cash exposure, monthly trading and cost comparison.
6. All twelve monthly returns, explicitly labelling partial December.
7. Findings, limitations and source-linked methodology/run identities.
8. Optional Field Notes draft, subject to its own editorial approval.

Use the existing forest, slate, sand and loss colours. The existing research chart
colours encode **strategy**, not market; keep BTC and ETH in separately labelled
panels. The draft follows that convention. Preserve the original source revision
and numerical constants in `web/lib/research.ts`. A later presentation module may
accept the reviewed account/data contract as props, with Study 001 unchanged.

## Data contract and review package

The generated `study-002-assets/review-data.json` uses exact Decimal strings,
explicit units, `publication_status=unapproved_draft`, all six independent new
accounts, two fixed Ridge references, twelve monthly observations per account,
and source hashes/relative report links. Undefined metrics retain null and reason.
The contract is a review artifact, not an automatically loaded website feed.

Charts use all retained hourly marks where appropriate, with full evidence hashes
printed in their captions. Review PNGs may be used as a layout reference; a later
accessible interactive implementation should retain table equivalents and avoid
inventing daily paths from monthly returns. The locally openable `review.html`
has no network dependencies, includes a noindex directive, and is absent from the
production static-export tree. `manifest.json` identifies every review artifact.

Publication review should approve the exact data/copy/chart identities first.
Then implement only the new route/card and reusable presentational components,
run frontend/accessibility/responsive/export tests, verify the unchanged Study 001
numbers and seven editorial approvals, and obtain separate deployment authority.
No route, sitemap, release workflow or public content is changed in this stage.

The final accessible summary and outcome-specific copy are in the
[scientific report](study-002-slower-trend-results.md).

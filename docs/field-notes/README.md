# Field Notes

Field Notes is Backtest Badger's curated technical research journal: meaningful
engineering discoveries and quantitative research findings, written for
technically curious readers. These Markdown articles supply the
website's Field Notes section. All four existing notes are approved for the initial
production release; no public deployment or publication date is claimed.

## What belongs here

Choose stories with a useful finding, an evidence-backed decision or a research
implication worth explaining beyond the immediate development task. Explain the
problem, what was observed, the decision made and what it means for future work.
An unresolved question can be a worthwhile finding if its limits are clear.

Not every task needs an article. Routine bug fixes, configuration changes, minor
refactors and ordinary Codex interactions should not automatically become Field
Notes. This is a curated journal, not a generated development log or prompt archive.

## Entry conventions

- Use sequential filenames: `001-short-descriptive-title.md`, then `002-...`.
  Keep published entry numbers stable.
- Start with a descriptive title and simple Markdown metadata. Use the initial
  draft date in ISO format, the relevant project stage, a topic and a publication
  status. New entries always start as **Draft**.
- Keep articles concise and readable. Explain necessary technical terms and use
  concrete examples; link to detailed technical documentation instead of copying
  complete investigations, logs or implementation histories.
- Separate observations from hypotheses and unknowns. Attribute evidence, check
  figures against verified project results and state material limitations.
  Never invent experiments, causes, performance statistics or outcomes.
- Describe planned research as planned. Keep backtests, forward predictions,
  paper trading and real trading distinct; simulated results are not live returns.
- Exclude credentials, secrets and sensitive infrastructure details. Supporting
  links must also be suitable for their intended audience.

Use this metadata beneath each title:

```markdown
- **Date:** YYYY-MM-DD
- **Stage:** Relevant project stage
- **Topic:** Short topic description
- **Publication status:** Draft
```

Before publication, review factual accuracy, clarity, source links and sensitive
details. A draft's presence in the repository does not authorize publication.
Change the source status to **Published** only after deliberate editorial approval,
then record the SHA-256 of the complete final source in
`web/content/publication-approvals.json`. Here Published means approved for a
production build, not evidence of deployment. Keep the original article date;
record any actual public launch date separately after deployment. Every later edit
invalidates approval until reviewed and explicitly reapproved. For substantive
later corrections, add a dated correction explaining what changed.

## Entries

| Entry | Date | Stage | Status |
| --- | --- | --- | --- |
| [001 — When Market Data Isn't Complete](001-when-market-data-isnt-complete.md) | 2026-10-13 | 1B.3 | Published — release approved |
| [002 — When a Backtest Meets Trading Costs](002-when-a-backtest-meets-trading-costs.md) | 2026-10-14 | 2C | Published — release approved |
| [003 — The Price of Changing Your Mind](003-the-price-of-changing-your-mind.md) | 2026-10-24 | 4B.2E.5g | Published — release approved |
| [004 — One Minute Can Change a Backtest](004-one-minute-can-change-a-backtest.md) | 2026-10-24 | 4B.2C–4B.2D.1 | Published — release approved |

The [Stage 5B.3 editorial release record](../stage-05b3-editorial-publication.md)
contains all seven note/guide filenames, slugs, original dates and exact SHA-256
approvals, plus the final source/link checks. Public deployment, artwork rights
and search-indexing activation remain separate owner decisions.

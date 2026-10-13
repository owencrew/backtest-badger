# Field Notes

Field Notes is Backtest Badger's curated technical research journal: meaningful
engineering discoveries and quantitative research findings, written for
technically curious readers. These Markdown articles may eventually supply the
public website's Field Notes section. This directory establishes the editorial
source; publishing and website implementation remain future work.

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
Change the status to **Published** only after deliberate editorial approval and
actual publication; add a publication date and link at that point. For substantive
later corrections, add a dated correction explaining what changed.

## Entries

| Entry | Date | Stage | Status |
| --- | --- | --- | --- |
| [001 — When Market Data Isn't Complete](001-when-market-data-isnt-complete.md) | 2026-10-13 | 1B.3 | Draft |

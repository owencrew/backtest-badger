# Backtest Badger website

Stage 5A is a local Next.js / React / TypeScript prototype. It is independent of
the Python package and needs no database, credentials or research artifacts.

## Run locally

Use Node.js 22.13+ (Node 24 LTS recommended) and pnpm 11.25.0. From the repository:

```sh
cd web
pnpm install --frozen-lockfile
pnpm dev
```

Open <http://127.0.0.1:3000>. The dev server binds to loopback. Development displays
explicitly labelled editorial drafts. Do not expose the development server publicly.

On this Mac, Node and pnpm were provided by Codex's bundled runtime. If your
terminal says either command is missing, the following PATH prefix uses the same
installed tools for this shell; it does not alter your shell configuration:

```sh
export PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback:$PATH"
```

```sh
pnpm lint
pnpm typecheck
pnpm build
pnpm test
pnpm preview
```

Stop the dev server before using `preview` on the same port. `build` exports to
`out/`; `preview` serves those production files locally. Run tests after the build
to include the production draft-leak check. That test explicitly skips if `out/`
does not yet exist. Build output and dependencies are ignored by Git.

## Content and evidence

- `lib/research.ts`: display-only decimal strings from the public E.5g report.
  All six accounts are reconciled against the report in tests.
- `../docs/field-notes/`: original journal Markdown, read by server components.
- `content/guides/`: three new educational drafts.
- `content/publication-approvals.json`: empty, fail-closed publication allowlists.
- `lib/content.ts`: shared content parsing and publication policy.

Production requires **both** `Publication status: Published` in an article's source
and an explicit `{ "slug": "filename-without-md", "sha256": "…" }` approval in its
collection. Hash the complete final UTF-8 source bytes, including metadata. Any
subsequent edit invalidates that approval. Changing a status alone is insufficient.
No environment flag permits drafts in a production build. Unknown environments
also fail closed. Development is a local editorial preview, not publication approval.
Review linked articles and source documents as part of publication approval.

When nothing is approved, the journal and guide indexes show honest empty states.
Each dynamic route generates a reserved `publication-pending` not-found entry so
Next's static exporter can build the empty collection; this is never linked in UI.
Draft bodies, titles and individual routes are excluded from the exported site.

## Structure

`app/` owns the six main pages and editorial routes. `components/` contains the
header, editorial views, research chart, market selector and decorative motion
study. `app/globals.css` contains semantic tokens and responsive styles. CSS is
used directly instead of adding Tailwind or a component library. The summary bar
chart uses a shared linear scale and HTML/CSS; no charting package is needed.

See the [Stage 5A design and validation report](../docs/stage-05a-website-design.md)
for scientific limits, technology choices, validation and next steps.

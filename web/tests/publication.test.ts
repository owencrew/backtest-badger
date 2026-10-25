import assert from "node:assert/strict";
import { test } from "node:test";
import {
  type Article,
  publicationAllowed,
  readArticles,
  editorialHref,
} from "../lib/content";
import approvals from "../content/publication-approvals.json";

const draft: Article = {
  slug: "003-example",
  title: "Draft title",
  date: "2026-10-25",
  topic: "test",
  status: "Draft",
  excerpt: "Draft excerpt",
  body: "Private draft body",
  minutes: 1,
  sourceFile: "003-example.md",
  sha256: "a".repeat(64),
};
test("drafts are allowed only in explicit development mode", () => {
  assert.equal(publicationAllowed(draft, "development", []), true);
  for (const environment of ["production", "test", undefined, "preview"]) {
    assert.equal(publicationAllowed(draft, environment, []), false);
    assert.equal(
      publicationAllowed(draft, environment, [
        { slug: draft.slug, sha256: draft.sha256 },
      ]),
      false,
    );
  }
});
test("publication requires published metadata and approval of the exact source bytes", () => {
  const published = { ...draft, status: "Published" };
  assert.equal(publicationAllowed(published, "production", []), false);
  assert.equal(
    publicationAllowed(published, "production", [
      { slug: published.slug, sha256: "outdated" },
    ]),
    false,
  );
  assert.equal(
    publicationAllowed(published, "production", [
      { slug: "different", sha256: published.sha256 },
    ]),
    false,
  );
  assert.equal(
    publicationAllowed(published, "production", [
      { slug: published.slug, sha256: published.sha256 },
    ]),
    true,
  );
});
test("all existing editorial entries are excluded without approval", () => {
  assert.deepEqual(approvals, { fieldNotes: [], guides: [] });
  assert.equal(readArticles("fieldNotes").length, 0);
  assert.equal(readArticles("guides").length, 0);
});
test("Markdown research sources point to pinned public repository files", () => {
  assert.equal(
    editorialHref("003-the-price-of-changing-your-mind.md", "fieldNotes"),
    "/field-notes/003-the-price-of-changing-your-mind/",
  );
  assert.match(
    editorialHref(
      "../stage-01b3-full-history.md#final-live-results-and-verification",
      "fieldNotes",
    ),
    /\/blob\/[a-f0-9]{40}\/docs\/stage-01b3-full-history\.md#final-live-results-and-verification$/,
  );
});

test("local preview features latest eligible note 004, with remaining notes newest first", (t) => {
  const env: Record<string, string | undefined> = process.env;
  const before = env.NODE_ENV;
  env.NODE_ENV = "development";
  t.after(() => {
    if (before === undefined) delete env.NODE_ENV;
    else env.NODE_ENV = before;
  });
  assert.deepEqual(
    readArticles("fieldNotes").map((a) => a.slug.slice(0, 3)),
    ["004", "003", "002", "001"],
  );
});

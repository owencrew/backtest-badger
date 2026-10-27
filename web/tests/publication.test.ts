import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  readFileSync,
  mkdtempSync,
  mkdirSync,
  writeFileSync,
  rmSync,
} from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
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
test("production loader includes only sources with exact publication approval", () => {
  for (const collection of ["fieldNotes", "guides"] as const) {
    const articles = readArticles(collection, "production");
    assert.equal(articles.length, collection === "fieldNotes" ? 4 : 3);
    assert.equal(approvals[collection].length, articles.length);
    for (const article of articles) {
      assert.equal(article.status, "Published");
      const directory =
        collection === "fieldNotes" ? "../docs/field-notes" : "content/guides";
      const bytes = readFileSync(path.join(directory, article.sourceFile));
      assert.equal(
        article.sha256,
        createHash("sha256").update(bytes).digest("hex"),
      );
      assert.doesNotMatch(article.body, /Publication status:/);
      const changed = {
        ...article,
        sha256: createHash("sha256")
          .update(Buffer.concat([bytes, Buffer.from("\n")]))
          .digest("hex"),
      };
      assert.equal(
        publicationAllowed(changed, "production", approvals[collection]),
        false,
      );
      const draft = { ...article, status: "Draft" };
      assert.equal(
        publicationAllowed(draft, "production", [
          { slug: draft.slug, sha256: draft.sha256 },
        ]),
        false,
      );
      assert.ok(
        approvals[collection].some(
          (approval: { slug: string; sha256: string }) =>
            approval.slug === article.slug &&
            approval.sha256 === article.sha256,
        ),
      );
    }
  }
});
test("even approved Published content fails closed in unknown environments", () => {
  const article = readArticles("fieldNotes", "production")[0];
  for (const environment of [undefined, "", "preview", "staging", "test"]) {
    assert.equal(
      publicationAllowed(article, environment, approvals.fieldNotes),
      false,
    );
  }
});

test("future sources without approvals are excluded by the real loader", () => {
  const cwd = process.cwd();
  const root = mkdtempSync(path.join(tmpdir(), "badger-publication-"));
  try {
    mkdirSync(path.join(root, "web/content/guides"), { recursive: true });
    mkdirSync(path.join(root, "docs/field-notes"), { recursive: true });
    for (const dir of ["docs/field-notes", "web/content/guides"]) {
      for (const [number, status] of [
        ["998", "Draft"],
        ["999", "Published"],
      ]) {
        writeFileSync(
          path.join(root, dir, `${number}-future.md`),
          `# Future private article\n\n- **Publication status:** ${status}\n\nDO_NOT_PUBLISH\n`,
        );
      }
    }
    process.chdir(path.join(root, "web"));
    for (const collection of ["fieldNotes", "guides"] as const) {
      assert.deepEqual(readArticles(collection, "production"), []);
      assert.equal(readArticles(collection, "development").length, 2);
    }
  } finally {
    process.chdir(cwd);
    rmSync(root, { recursive: true, force: true });
  }
});

test("production features eligible note 004 followed by 003, 002, 001", () => {
  assert.deepEqual(
    readArticles("fieldNotes", "production").map((a) => a.slug.slice(0, 3)),
    ["004", "003", "002", "001"],
  );
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

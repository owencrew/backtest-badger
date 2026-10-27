import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { readArticles, editorialHref } from "../lib/content";
import { repository, sourceRevision } from "../lib/research";
import { publicPaths } from "../lib/seo";

test("all approved Markdown dependencies resolve to eligible routes or source report anchors", () => {
  let count = 0;
  for (const collection of ["fieldNotes", "guides"] as const) {
    const articles = readArticles(collection, "production");
    for (const article of articles) {
      const directory =
        collection === "fieldNotes" ? "../docs/field-notes" : "content/guides";
      const raw = readFileSync(
        path.join(directory, article.sourceFile),
        "utf8",
      );
      // Current sources use inline Markdown links; unexpected reference-style
      // links require extending this inventory instead of silently skipping them.
      assert.doesNotMatch(raw, /^\s*\[[^\]]+\]:/m);
      for (const [, href] of raw.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
        count++;
        const [file, fragment] = href.split("#");
        if (file.startsWith("/")) {
          assert.ok(publicPaths.includes(file), href);
          assert.ok(existsSync(path.join("app", file, "page.tsx")), href);
        } else {
          const source = path.join(directory, file);
          assert.ok(existsSync(source), source);
          if (file.startsWith("../")) {
            assert.equal(
              editorialHref(href, collection),
              `${repository}/blob/${sourceRevision}/docs/${href.slice(3)}`,
            );
          } else {
            assert.ok(
              articles.some((a) => a.sourceFile === file),
              `Unpublished dependency: ${href}`,
            );
            assert.equal(
              editorialHref(href, collection),
              `/${collection === "fieldNotes" ? "field-notes" : "field-guide"}/${file.replace(/\.md$/, "/")}${fragment ? `#${fragment}` : ""}`,
            );
          }
          if (fragment) {
            const headings = [
              ...readFileSync(source, "utf8").matchAll(/^#{1,6} (.+)$/gm),
            ].map((m) =>
              m[1]
                .toLowerCase()
                .replace(/[^\p{L}\p{N}_\-\s]/gu, "")
                .replace(/ /g, "-"),
            );
            assert.ok(headings.includes(fragment), `${source}#${fragment}`);
          }
        }
      }
    }
  }
  assert.equal(
    count,
    14,
    "Review and update the explicit link inventory when sources change",
  );
});

test("editorial article conversion preserves trailing slash before heading fragment", () => {
  assert.equal(
    editorialHref(
      "003-the-price-of-changing-your-mind.md#what-the-accounts-show",
      "fieldNotes",
    ),
    "/field-notes/003-the-price-of-changing-your-mind/#what-the-accounts-show",
  );
});

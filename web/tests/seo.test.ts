import assert from "node:assert/strict";
import { test } from "node:test";
import sitemap from "../app/sitemap";
import robots from "../app/robots";
import {
  indexingEnabled,
  publicPaths,
  siteOrigin,
  articleMetadata,
} from "../lib/seo";
import { readArticles } from "../lib/content";

test("indexing requires the exact deliberate launch setting", () => {
  for (const value of ["", "true", "1", "false", "preview", "www-live"]) {
    assert.equal(indexingEnabled(value), false);
  }
  assert.equal(indexingEnabled("www-live-owner-approved"), true);
});

test("sitemap contains exactly the six site routes and seven eligible articles", () => {
  const entries = sitemap();
  const expected = [...publicPaths];
  for (const collection of ["fieldNotes", "guides"] as const) {
    for (const article of readArticles(collection, "production")) {
      const section =
        collection === "fieldNotes" ? "field-notes" : "field-guide";
      expected.push(`/${section}/${article.slug}/`);
      const metadata = articleMetadata(article, collection);
      assert.equal(
        metadata.alternates?.canonical,
        `${siteOrigin}/${section}/${article.slug}/`,
      );
      assert.deepEqual(metadata.title, {
        absolute: `${article.title} | Backtest Badger`,
      });
      assert.doesNotMatch(
        metadata.description!,
        /\*|`|\.md|Stage |localhost|workers\.dev/,
      );
    }
  }
  assert.equal(entries.length, 13);
  assert.deepEqual(
    entries.map((e) => e.url).sort(),
    expected.map((p) => siteOrigin + p).sort(),
  );
  assert.ok(entries.every((e) => e.lastModified === undefined));
});

test("robots permits reading noindex and advertises a sitemap only after approval", () => {
  const before = process.env.BADGER_SEARCH_INDEXING;
  try {
    delete process.env.BADGER_SEARCH_INDEXING;
    assert.equal(indexingEnabled(), false);
    assert.deepEqual(robots(), { rules: { userAgent: "*", allow: "/" } });
    process.env.BADGER_SEARCH_INDEXING = "www-live-owner-approved";
    assert.equal(robots().sitemap, `${siteOrigin}/sitemap.xml`);
  } finally {
    if (before === undefined) delete process.env.BADGER_SEARCH_INDEXING;
    else process.env.BADGER_SEARCH_INDEXING = before;
  }
});

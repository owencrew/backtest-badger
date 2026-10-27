import { rmSync } from "node:fs";
import { indexingEnabled } from "../lib/seo";
// Next needs a generated parameter when a collection has no eligible articles.
// Its notFound() output is still an HTML asset; remove it to preserve HTTP 404s.
for (const collection of ["field-notes", "field-guide"]) {
  rmSync(`out/${collection}/publication-pending`, {
    recursive: true,
    force: true,
  });
}
// Maintainer provenance stays in the repository, outside the public asset set.
rmSync("out/brand/README.md", { force: true });

// Withhold discovery until the www launch and explicit owner indexing approval.
if (!indexingEnabled()) rmSync("out/sitemap.xml", { force: true });

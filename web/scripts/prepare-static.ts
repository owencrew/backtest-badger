import { rmSync } from "node:fs";
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

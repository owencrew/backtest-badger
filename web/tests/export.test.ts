import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { readArticles } from "../lib/content";

assert.ok(
  existsSync("out/index.html"),
  "Run pnpm build before testing the production export.",
);

const environment: Record<string, string | undefined> = process.env;
environment.NODE_ENV = "production";

const output = path.join(process.cwd(), "out");
function files(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? files(path.join(directory, entry.name))
      : [path.join(directory, entry.name)],
  );
}
test("production export excludes draft article text and draft routes", () => {
  const forbidden = [
    "SYNTHETIC_PRIVATE_PATH",
    "SYNTHETIC-TEST-IDENTITY",
    "DO_NOT_PUBLISH",
    "Synthetic Binance-shaped unit data",
  ];
  // Inspect every source independently of the production loader. Only approved
  // sources may contribute titles, topics, opening text or individual routes.
  for (const [collection, directory, route] of [
    ["fieldNotes", "../docs/field-notes", "field-notes"],
    ["guides", "content/guides", "field-guide"],
  ] as const) {
    const allowed = readArticles(collection).map((article) => article.slug);
    for (const name of readdirSync(directory).filter((name) =>
      /^\d{3}-.+\.md$/.test(name),
    )) {
      const slug = name.replace(/\.md$/, "");
      if (allowed.includes(slug)) continue;
      assert.equal(existsSync(path.join(output, route, slug)), false, slug);
      const source = readFileSync(path.join(directory, name), "utf8");
      forbidden.push(source.match(/^# (.+)$/m)![1]);
      const topic = source.match(/^- \*\*Topic:\*\* (.+)$/m)?.[1];
      if (topic) forbidden.push(topic);
      const body = source
        .replace(/^Publication status: .+\n+/m, "")
        .replace(/^# .+\n+/m, "")
        .replace(/^- \*\*.+\n/gm, "")
        .trim();
      forbidden.push(body.split("\n")[0]);
    }
  }
  const exported = files(output);
  for (const file of exported) {
    assert.doesNotMatch(
      file,
      /(?:^|\/)(?:\.env[^/]*|artifacts|tests|scripts|docs|node_modules)(?:\/|$)/,
    );
    assert.doesNotMatch(file, /\.(?:py|pem|key|map|md|csv|parquet)$/);
    if (/\.(html|txt|js|json)$/.test(file)) {
      const contents = readFileSync(file, "utf8");
      assert.doesNotMatch(
        contents,
        /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|postgres(?:ql)?:\/\//,
      );
      for (const text of forbidden)
        assert.equal(
          contents.includes(text),
          false,
          `Unapproved draft leaked to ${file}`,
        );
    }
  }
});

test("production Burrow contains an honest unavailable forecast state", () => {
  const html = readFileSync(path.join(output, "burrow/index.html"), "utf8");
  assert.match(html, /Forward forecasts are not published yet/);
  assert.match(html, /No successful refresh yet/);
  assert.doesNotMatch(html, /synthetic-candidate|SYNTHETIC/);
});

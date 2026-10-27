import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { readArticles, editorialHref } from "../lib/content";
import { indexingEnabled, siteOrigin } from "../lib/seo";
import sitemap from "../app/sitemap";

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

const decode = (s: string) =>
  s
    .replace(/&amp;/g, "&")
    .replace(/&#x27;|&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");

test("every public page has distinct canonical and social metadata in exported HTML", () => {
  const descriptions = new Set<string>();
  for (const { url } of sitemap()) {
    const pathname = new URL(url).pathname;
    const html = readFileSync(
      path.join(output, pathname, "index.html"),
      "utf8",
    );
    const head = html.split("</head>")[0];
    assert.ok(head.includes(`<link rel="canonical" href="${url}"`), pathname);
    assert.ok(
      head.includes(`<meta property="og:url" content="${url}"`),
      pathname,
    );
    assert.match(head, /name="twitter:card" content="summary"/);
    const description = decode(
      head.match(/name="description" content="([^"]+)"/)![1],
    );
    assert.ok(description.length > 30 && description.length < 200, pathname);
    assert.ok(
      !descriptions.has(description),
      `Duplicate description: ${pathname}`,
    );
    descriptions.add(description);
    const title = decode(head.match(/<title>(.*?)<\/title>/)![1]);
    for (const key of ["og:title", "twitter:title"]) {
      assert.equal(
        decode(
          head.match(
            new RegExp(`(?:name|property)="${key}" content="([^"]+)"`),
          )![1],
        ),
        title,
      );
    }
    for (const key of ["og:description", "twitter:description"]) {
      assert.equal(
        decode(
          head.match(
            new RegExp(`(?:name|property)="${key}" content="([^"]+)"`),
          )![1],
        ),
        description,
      );
    }
    assert.doesNotMatch(
      head,
      /localhost|127\.0\.0\.1|workers\.dev|publication-pending|property="og:image"|article:published_time/,
    );
    assert.doesNotMatch(description, /\*|`|\.md|\/Users\/|Stage /);
    assert.ok(
      head.includes(
        `name="robots" content="${indexingEnabled() ? "index, follow" : "noindex, nofollow"}"`,
      ),
      pathname,
    );
  }
});

test("approved article content, dates, reading times and converted links reach the export", () => {
  for (const collection of ["fieldNotes", "guides"] as const) {
    const route = collection === "fieldNotes" ? "field-notes" : "field-guide";
    assert.equal(
      existsSync(path.join(output, route, "publication-pending")),
      false,
    );
    for (const article of readArticles(collection)) {
      const html = readFileSync(
        path.join(output, route, article.slug, "index.html"),
        "utf8",
      );
      const markup = decode(
        html
          .replace(/<script\b[^>]*>[\s\S]*?<\/script>/g, "")
          .replace(/<!--.*?-->/g, ""),
      );
      assert.ok(markup.includes(`<h1>${article.title}</h1>`));
      assert.ok(markup.includes(`dateTime="${article.date}"`));
      assert.ok(markup.includes(`${article.minutes} min read`));
      assert.doesNotMatch(
        markup,
        /Local editorial preview|Draft ·|Read the preview|Publication status:/,
      );
      assert.match(markup, /Keep digging/);
      if (article.body.includes("| ---")) assert.match(markup, /<table>/);
      if (article.body.includes("## ")) assert.match(markup, /<h2>/);
      for (const match of article.body.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
        const target = editorialHref(match[1], collection);
        assert.ok(
          markup.includes(`href="${target}"`),
          `${article.slug}: ${target}`,
        );
      }
    }
  }
  const index = readFileSync(
    path.join(output, "field-notes/index.html"),
    "utf8",
  );
  const articles = readArticles("fieldNotes");
  let previous = -1;
  for (const article of articles) {
    const position = index.indexOf(`href="/field-notes/${article.slug}/"`);
    assert.ok(position > previous, article.slug);
    previous = position;
  }
  assert.match(index, /Field Note \/ <!-- -->004/);
  const home = readFileSync(path.join(output, "index.html"), "utf8");
  for (const article of articles.slice(0, 2)) {
    assert.ok(home.includes(`href="/field-notes/${article.slug}/"`));
  }
});

test("all exported internal navigation targets and fragments exist", () => {
  for (const file of files(output).filter((file) => file.endsWith(".html"))) {
    const html = readFileSync(file, "utf8").replace(
      /<script\b[^>]*>[\s\S]*?<\/script>/g,
      "",
    );
    for (const match of html.matchAll(/<a\b[^>]*href="([^"]+)"/g)) {
      const href = decode(match[1]);
      if (!href.startsWith("/") && !href.startsWith("#")) continue;
      const [pathname, fragment] = href.split("#");
      const target = pathname
        ? path.join(
            output,
            pathname,
            pathname.endsWith("/") ? "index.html" : "",
          )
        : file;
      assert.ok(existsSync(target), `${file} → ${href}`);
      if (fragment)
        assert.ok(
          readFileSync(target, "utf8").includes(`id="${fragment}"`),
          `${file} → ${href}`,
        );
    }
  }
});

test("sitemap serving and robots discovery agree with the build indexing policy", () => {
  const robots = readFileSync(path.join(output, "robots.txt"), "utf8");
  assert.match(robots, /Allow: \//);
  assert.doesNotMatch(robots, /Disallow: \/|workers\.dev|localhost/);
  assert.equal(existsSync(path.join(output, "sitemap.xml")), indexingEnabled());
  if (indexingEnabled()) {
    assert.ok(robots.includes(`Sitemap: ${siteOrigin}/sitemap.xml`));
    const xml = readFileSync(path.join(output, "sitemap.xml"), "utf8");
    assert.deepEqual(
      [...xml.matchAll(/<loc>(.*?)<\/loc>/g)].map((m) => m[1]).sort(),
      sitemap()
        .map((e) => e.url)
        .sort(),
    );
  } else {
    assert.doesNotMatch(robots, /Sitemap:/);
  }
});

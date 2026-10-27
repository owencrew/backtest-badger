import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { readdirSync, readFileSync } from "node:fs";
import { setTimeout as delay } from "node:timers/promises";
import { indexingEnabled, siteOrigin } from "../lib/seo";

const base = "http://127.0.0.1:8791";
const child = spawn(
  process.execPath,
  [
    "node_modules/wrangler/bin/wrangler.js",
    "dev",
    "--local",
    "--ip",
    "127.0.0.1",
    "--port",
    "8791",
    "--inspector-port",
    "0",
  ],
  {
    detached: true,
    stdio: ["ignore", "pipe", "pipe"],
    env: {
      ...process.env,
      WRANGLER_SEND_METRICS: "false",
    },
  },
);
let logs = "";
child.stdout.on("data", (data) => {
  logs += data;
});
child.stderr.on("data", (data) => {
  logs += data;
});
async function get(path: string) {
  return fetch(`${base}${path}`, {
    redirect: "manual",
    signal: AbortSignal.timeout(5000),
  });
}
try {
  let ready = false;
  for (let attempt = 0; attempt < 60; attempt++) {
    if (child.exitCode !== null) throw new Error(logs);
    if (logs.includes("Ready on")) {
      ready = true;
      break;
    }
    await delay(500);
  }
  assert.ok(ready, `Local Wrangler did not start:\n${logs}`);
  const routes = [
    "/",
    "/burrow/",
    "/dig/",
    "/field-notes/",
    "/field-guide/",
    "/about/",
  ];
  // Exercise every approved nested article, including after owner publication.
  for (const collection of ["field-notes", "field-guide"]) {
    for (const entry of readdirSync(`out/${collection}`, {
      withFileTypes: true,
    })) {
      if (entry.isDirectory()) routes.push(`/${collection}/${entry.name}/`);
    }
  }
  for (const route of routes) {
    const response = await get(route);
    assert.equal(response.status, 200, route);
    assert.match(response.headers.get("content-type") ?? "", /text\/html/);
    const html = await response.text();
    assert.match(html, /Backtest Badger/);
    assert.ok(
      html.includes(`<link rel="canonical" href="${siteOrigin}${route}"`),
      route,
    );
    assert.ok(
      html.includes(
        `name="robots" content="${indexingEnabled() ? "index, follow" : "noindex, nofollow"}"`,
      ),
      route,
    );
    assert.doesNotMatch(
      html,
      /Draft ·|Local editorial preview|Read the preview/,
    );
    assert.equal((await get(route)).status, 200, `Refresh ${route}`);
    if (route !== "/") {
      for (const alias of [route.slice(0, -1), `${route}index.html`]) {
        const redirect = await get(`${alias}?check=1`);
        assert.equal(redirect.status, 307, alias);
        assert.equal(
          new URL(redirect.headers.get("location")!, base).pathname,
          route,
        );
        assert.equal(
          new URL(redirect.headers.get("location")!, base).search,
          "?check=1",
        );
      }
    }
  }
  const robots = await get("/robots.txt");
  assert.equal(robots.status, 200);
  assert.equal((await robots.text()).includes("Sitemap:"), indexingEnabled());
  assert.equal(
    (await get("/sitemap.xml")).status,
    indexingEnabled() ? 200 : 404,
  );
  for (const route of [
    "/does-not-exist/",
    "/field-notes/unapproved/",
    "/field-guide/unapproved/",
    "/field-notes/publication-pending/",
    "/field-guide/publication-pending/",
    "/.env",
    "/docs/field-notes/",
    "/artifacts/",
  ]) {
    const response = await get(route);
    assert.equal(response.status, 404, route);
    assert.match(await response.text(), /Backtest Badger/);
  }
  const assets = [
    "/brand/badger-mascot.webp",
    "/brand/badger-mark.svg",
    "/licenses/lightweight-charts-LICENSE.txt",
  ];
  for (const directory of ["css", "chunks", "media"]) {
    const names = readdirSync(`out/_next/static/${directory}`, {
      recursive: true,
    }) as string[];
    const file = names.find((name) => /\.(css|js|woff2)$/.test(name));
    assert.ok(file, `No ${directory} asset`);
    assets.push(`/_next/static/${directory}/${file}`);
  }
  for (const asset of assets) {
    const response = await get(asset);
    assert.equal(response.status, 200, asset);
    assert.deepEqual(
      Buffer.from(await response.arrayBuffer()),
      readFileSync(`out${asset}`),
    );
  }
  console.log(
    `Local Workers smoke passed: ${routes.length} routes, redirects, refresh, ${assets.length} assets, real HTTP 404s.`,
  );
} catch (error) {
  console.error(logs);
  throw error;
} finally {
  if (child.pid) {
    try {
      process.kill(-child.pid, "SIGTERM");
    } catch {
      /* already exited */
    }
  }
}

import assert from "node:assert/strict";
import { test } from "node:test";
import { checkEndpoint } from "../scripts/check-forward-endpoint";
import { syntheticSnapshot } from "./fixtures/forward";

const url = "https://public-feed.example/forward-v1.json";
const headers = {
  "content-type": "application/json",
  "cache-control": "public, max-age=60, must-revalidate",
  "access-control-allow-origin": "https://www.backtestbadger.com",
};

test("endpoint monitoring fails on stale cutoff, stale issuance, or bad CORS", async (t) => {
  const snapshot = syntheticSnapshot();
  const latest = snapshot.latest[0];
  snapshot.latest.push({ ...structuredClone(latest), symbol: "ETHUSDT" });
  snapshot.evaluations = snapshot.evaluations.map((e) =>
    e.symbol === "ETHUSDT"
      ? {
          ...structuredClone(
            snapshot.evaluations.find(
              (b) => b.symbol === "BTCUSDT" && b.cohort === e.cohort,
            )!,
          ),
          symbol: "ETHUSDT",
        }
      : e,
  );
  t.mock.method(Date, "now", () => Date.parse("2026-10-15T13:00:00Z"));
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response(JSON.stringify(snapshot), { headers }),
  );
  await assert.rejects(checkEndpoint(url), /issuance is stale/);
  snapshot.as_of = "2026-10-15T12:00:00Z";
  snapshot.generated_at = snapshot.as_of;
  await assert.rejects(checkEndpoint(url), /cutoff is stale/);
  t.mock.method(
    globalThis,
    "fetch",
    async () =>
      new Response("{}", { headers: { "content-type": "application/json" } }),
  );
  await assert.rejects(checkEndpoint(url), /metadata\/CORS mismatch/);
});

test("endpoint monitor rejects non-HTTPS and oversized responses", async (t) => {
  await assert.rejects(
    checkEndpoint("http://public-feed.example/forward-v1.json"),
  );
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response("x".repeat(65537), { headers }),
  );
  await assert.rejects(checkEndpoint(url), /size budget/);
});

test("endpoint monitor accepts current genuine-shaped coverage without retiming", async (t) => {
  const snapshot = syntheticSnapshot();
  const latest = snapshot.latest[0];
  latest.source_close_at = "2026-10-15T12:00:00Z";
  latest.issued_at = "2026-10-15T12:01:00Z";
  latest.target_close_at = "2026-10-15T16:00:00Z";
  latest.status = "pending_not_settled";
  latest.scored_at = null;
  latest.actual_log_return_4h = null;
  for (const model of Object.values(latest.models)) {
    model.signed_error = model.absolute_error = model.squared_error = null;
  }
  snapshot.evaluations[0].genuine_predictions = 2;
  snapshot.evaluations[0].pending_not_settled = 1;
  snapshot.latest.push({ ...structuredClone(latest), symbol: "ETHUSDT" });
  snapshot.evaluations = snapshot.evaluations.map((e) =>
    e.symbol === "ETHUSDT"
      ? {
          ...structuredClone(
            snapshot.evaluations.find(
              (b) => b.symbol === "BTCUSDT" && b.cohort === e.cohort,
            )!,
          ),
          symbol: "ETHUSDT",
        }
      : e,
  );
  const original = JSON.stringify(snapshot);
  t.mock.method(Date, "now", () => Date.parse("2026-10-15T13:00:00Z"));
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response(original, { headers }),
  );
  const messages: string[] = [];
  t.mock.method(console, "log", (message: string) => messages.push(message));
  await checkEndpoint(url);
  assert.equal(JSON.parse(messages[0]).as_of, snapshot.as_of);
  assert.equal(JSON.stringify(snapshot), original);
});

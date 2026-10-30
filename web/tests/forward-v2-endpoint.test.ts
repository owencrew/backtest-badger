import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import {
  checkV2Endpoint,
  checkProgress,
  V2_URL,
} from "../scripts/check-forward-v2-endpoint";
import { syntheticV2 } from "./fixtures/forward-v2";
const headers = {
  "content-type": "application/json",
  "cache-control": "public, max-age=60, must-revalidate",
  "access-control-allow-origin": "https://www.backtestbadger.com",
};
const now = Date.parse("2026-10-15T13:00:00Z");

test("v2 HTTPS exact-byte success and independent last-check state", async (t) => {
  const dir = mkdtempSync(join(tmpdir(), "badger-v2-check-"));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const expected = join(dir, "last-success-v2.json"),
    state = join(dir, "last-check-v2.json");
  const original = JSON.stringify(syntheticV2());
  writeFileSync(expected, original);
  t.mock.method(Date, "now", () => now);
  t.mock.method(
    globalThis,
    "fetch",
    async (_url: string, options?: RequestInit) => {
      assert.equal(_url, V2_URL);
      assert.equal(options?.redirect, "error");
      return new Response(original, { headers });
    },
  );
  const result = await checkV2Endpoint(V2_URL, expected, state);
  assert.equal(result.status, "public-feed-v2-healthy");
  assert.equal(readFileSync(state, "utf8"), original);
  writeFileSync(expected, original + " ");
  await assert.rejects(
    checkV2Endpoint(V2_URL, expected, state),
    /bytes differ/,
  );
  assert.equal(readFileSync(state, "utf8"), original);
});

for (const fault of [
  "http",
  "cors",
  "cache",
  "type",
  "size",
  "json",
  "downgrade",
  "missing_score",
  "private",
  "direction",
  "stale",
  "issuance",
  "network",
]) {
  test(`v2 checker rejects ${fault} without advancing state`, async (t) => {
    const dir = mkdtempSync(join(tmpdir(), "badger-v2-fail-"));
    t.after(() => rmSync(dir, { recursive: true, force: true }));
    const state = join(dir, "last-check-v2.json");
    const snapshot = syntheticV2();
    const original = JSON.stringify(snapshot);
    writeFileSync(state, original);
    const responseHeaders = { ...headers };
    if (fault === "cors") responseHeaders["access-control-allow-origin"] = "*";
    if (fault === "cache") responseHeaders["cache-control"] = "max-age=86400";
    if (fault === "type") responseHeaders["content-type"] = "text/html";
    if (fault === "downgrade") Object.assign(snapshot, { schema_version: 1 });
    if (fault === "missing_score") snapshot.latest_scored.pop();
    if (fault === "private")
      Object.assign(snapshot, { raw_evidence: "DO_NOT_PUBLISH" });
    if (fault === "direction")
      snapshot.latest_scored[0].models.zero.directional_correct = true;
    if (fault === "stale")
      snapshot.as_of = snapshot.generated_at = "2026-10-15T12:30:00Z";
    if (fault === "issuance") {
      snapshot.as_of = snapshot.generated_at = "2026-10-15T16:30:00Z";
      for (const row of snapshot.latest) row.status = "mature_unscored";
      for (const row of snapshot.evaluations) {
        row.mature_unscored = row.pending_not_settled;
        row.pending_not_settled = 0;
      }
    }
    t.mock.method(Date, "now", () =>
      fault === "issuance" ? Date.parse(snapshot.as_of) : now,
    );
    t.mock.method(globalThis, "fetch", async () => {
      if (fault === "network") throw new Error("network failure");
      return new Response(
        fault === "size"
          ? "x".repeat(65537)
          : fault === "json"
            ? "{"
            : JSON.stringify(snapshot),
        { headers: responseHeaders, status: fault === "http" ? 503 : 200 },
      );
    });
    await assert.rejects(checkV2Endpoint(V2_URL, undefined, state));
    assert.equal(readFileSync(state, "utf8"), original);
  });
}

test("checker rejects URL substitutions before fetching", async (t) => {
  t.mock.method(globalThis, "fetch", () => {
    throw new Error("must not fetch");
  });
  for (const url of [
    V2_URL.replace("v2", "v1"),
    V2_URL.replace("https:", "http:"),
    V2_URL + "?x=1",
    V2_URL.replace("data.", "other."),
    V2_URL.replace(".com/", ".com:443/"),
  ])
    await assert.rejects(checkV2Endpoint(url), /approved/);
});

test("v2 durable checker rejects microsecond, score, issuance and aggregate regression", () => {
  for (const fault of ["clock", "score", "issuance", "prediction", "counts"]) {
    const previous = syntheticV2(),
      current = structuredClone(previous);
    if (fault === "clock") {
      previous.as_of = previous.generated_at = "2026-10-15T13:00:00.000002Z";
      current.as_of = current.generated_at = "2026-10-15T13:00:00.000001Z";
    } else if (fault === "score")
      current.latest_scored[0].recipe_sha256 = "b".repeat(64);
    else if (fault === "issuance")
      current.latest[0].source_close_at = "2026-10-15T08:00:00Z";
    else if (fault === "prediction")
      current.latest[0].models.ridge.predicted_log_return_4h += 0.001;
    else current.evaluations[0].matched_count--;
    assert.throws(() => checkProgress(previous, current), /regressed|changed/);
  }
});

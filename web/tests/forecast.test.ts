import assert from "node:assert/strict";
import { test } from "node:test";
import {
  validateForecast,
  fetchForecast,
  models,
  type ForecastSnapshot,
} from "../lib/forecast";
import { syntheticSnapshot } from "./fixtures/forward";
const now = Date.parse("2026-10-15T13:00:00Z");
test("synthetic public contract preserves all markets, cohorts, baselines and null denominators", () => {
  const fixture = syntheticSnapshot();
  assert.deepEqual(validateForecast(fixture, now), fixture);
  // Old valid snapshots remain reference evidence; the UI marks their as-of time stale.
  assert.deepEqual(validateForecast(fixture, now + 86_400_000), fixture);
});
const invalid: [string, (f: ForecastSnapshot) => void][] = [
  ["version", (f) => Object.assign(f, { schema_version: 2 })],
  [
    "unapproved extra fields",
    (f) => Object.assign(f, { private_path: "SYNTHETIC_PRIVATE_PATH" }),
  ],
  ["wrong protocol", (f) => (f.protocol_sha256 = "a".repeat(64))],
  ["future generation", (f) => (f.generated_at = "2026-10-16T13:00:00Z")],
  ["stale generation cutoff", (f) => (f.generated_at = "2026-10-15T13:06:00Z")],
  ["non-UTC date", (f) => (f.as_of = "2026-10-15T13:00:00")],
  ["invalid calendar date", (f) => (f.as_of = "2026-02-30T13:00:00Z")],
  ["duplicate forecast", (f) => f.latest.push(f.latest[0])],
  ["missing cohort", (f) => f.evaluations.pop()],
  ["duplicate cohort", (f) => (f.evaluations[5] = f.evaluations[0])],
  ["invalid market", (f) => Object.assign(f.latest[0], { symbol: "DOGEUSDT" })],
  [
    "wrong horizon",
    (f) => (f.latest[0].target_close_at = "2026-10-15T12:00:00Z"),
  ],
  ["early issuance", (f) => (f.latest[0].issued_at = "2026-10-15T04:00:59Z")],
  ["late primary", (f) => (f.latest[0].issued_at = "2026-10-15T04:16:00Z")],
  ["early score", (f) => (f.latest[0].scored_at = "2026-10-15T08:00:59Z")],
  [
    "nonfinite prediction",
    (f) => (f.latest[0].models.ridge.predicted_log_return_4h = Infinity),
  ],
  [
    "missing model",
    (f) =>
      delete (f.latest[0].models as Partial<(typeof f.latest)[0]["models"]>)
        .zero,
  ],
  [
    "inconsistent errors",
    (f) => (f.latest[0].models.ridge.signed_error = -0.005),
  ],
  ["matched count", (f) => (f.evaluations[0].matched_count = 2)],
  [
    "direction denominator",
    (f) => (f.evaluations[0].models.ridge.directional_denominator = 2),
  ],
  [
    "zero abstention",
    (f) => (f.evaluations[0].models.zero.directional_accuracy = 0),
  ],
  ["empty sample metric", (f) => (f.evaluations[1].models.ridge.mae = 0)],
  ["RMSE below MAE", (f) => (f.evaluations[0].models.ridge.rmse = 0)],
  ["secondary missing grid", (f) => (f.evaluations[1].missing_predictions = 0)],
];
for (const [name, mutate] of invalid)
  test(`rejects ${name}`, () => {
    const fixture = syntheticSnapshot();
    mutate(fixture);
    assert.throws(() => validateForecast(fixture, now));
  });
test("pending versus mature-unscored boundary is target close plus 60 seconds", () => {
  const f = syntheticSnapshot();
  f.generated_at = f.as_of = "2026-10-15T08:00:59Z";
  Object.assign(f.latest[0], {
    status: "pending_not_settled",
    scored_at: null,
    actual_log_return_4h: null,
  });
  for (const model of models)
    Object.assign(f.latest[0].models[model], {
      signed_error: null,
      absolute_error: null,
      squared_error: null,
    });
  Object.assign(f.evaluations[0], { matched_count: 0, pending_not_settled: 1 });
  for (const model of models)
    Object.assign(f.evaluations[0].models[model], {
      mae: null,
      rmse: null,
      forecast_bias: null,
      directional_correct: 0,
      directional_denominator: 0,
      directional_accuracy: null,
    });
  validateForecast(f, now);
  f.as_of = f.generated_at = "2026-10-15T08:01:00Z";
  assert.throws(() => validateForecast(f, now));
  f.latest[0].status = "mature_unscored";
  Object.assign(f.evaluations[0], {
    pending_not_settled: 0,
    mature_unscored: 1,
  });
  validateForecast(f, now);
  f.latest[0].models.ridge.signed_error = 0;
  assert.throws(() => validateForecast(f, now));
});
test("forecast fetch uses credential-free uncached JSON and refuses malformed feed", async (t) => {
  const fixture = syntheticSnapshot();
  t.mock.method(
    globalThis,
    "fetch",
    async (_url: string, options: RequestInit) => {
      assert.equal(options.cache, "no-store");
      assert.equal(options.credentials, "omit");
      return Response.json(fixture);
    },
  );
  assert.deepEqual(
    await fetchForecast("/forward-v1.json", new AbortController().signal),
    fixture,
  );
  fixture.latest[0].models.zero.predicted_log_return_4h = 1;
  await assert.rejects(
    fetchForecast(
      "https://example.com/forward-v1.json",
      new AbortController().signal,
    ),
  );
  await assert.rejects(
    fetchForecast(
      "http://example.com/forward-v1.json",
      new AbortController().signal,
    ),
  );
});

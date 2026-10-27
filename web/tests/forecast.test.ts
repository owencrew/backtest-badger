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
  ["future outcome", (f) => (f.latest[0].scored_at = "2026-10-15T13:01:00Z")],
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

test("refresh accepts pending → scored → next issuance and rejects clock regression", async (t) => {
  const { createForecastLoader, forecastIsStale, forecastStatus } =
    await import("../lib/forecast");
  const scored = syntheticSnapshot();
  const pending = structuredClone(scored);
  pending.as_of = pending.generated_at = "2026-10-15T07:59:00Z";
  Object.assign(pending.latest[0], {
    status: "pending_not_settled",
    scored_at: null,
    actual_log_return_4h: null,
  });
  for (const m of models) {
    Object.assign(pending.latest[0].models[m], {
      signed_error: null,
      absolute_error: null,
      squared_error: null,
    });
    Object.assign(pending.evaluations[0].models[m], {
      mae: null,
      rmse: null,
      forecast_bias: null,
      directional_correct: 0,
      directional_denominator: 0,
      directional_accuracy: null,
    });
  }
  Object.assign(pending.evaluations[0], {
    matched_count: 0,
    pending_not_settled: 1,
  });
  let response = pending;
  t.mock.method(globalThis, "fetch", async () => Response.json(response));
  const load = createForecastLoader("/forward-v1.json");
  const signal = new AbortController().signal;
  assert.equal((await load(signal)).latest[0].status, "pending_not_settled");
  assert.equal(
    forecastStatus(pending.latest[0], Date.parse("2026-10-15T07:59:00Z")),
    "Outcome pending",
  );
  assert.equal(
    forecastStatus(pending.latest[0], Date.parse("2026-10-15T08:00:00Z")),
    "Target closed · settling",
  );
  assert.equal(
    forecastStatus(pending.latest[0], Date.parse("2026-10-15T08:01:00Z")),
    "Mature · score not published",
  );
  response = scored;
  assert.equal((await load(signal)).latest[0].status, "scored");
  response = pending;
  await assert.rejects(load(signal), /regressed/);
  response = structuredClone(scored);
  response.generated_at = "2026-10-15T13:01:00Z";
  await load(signal);
  response = scored;
  await assert.rejects(load(signal), /regressed/);
  response = structuredClone(pending);
  response.as_of = response.generated_at = "2026-10-15T13:05:00Z";
  Object.assign(response.latest[0], {
    source_close_at: "2026-10-15T12:00:00Z",
    issued_at: "2026-10-15T12:01:00Z",
    target_close_at: "2026-10-15T16:00:00Z",
  });
  Object.assign(response.evaluations[0], {
    genuine_predictions: 2,
    matched_count: 1,
    models: scored.evaluations[0].models,
  });
  assert.equal(
    (await load(signal)).latest[0].target_close_at,
    "2026-10-15T16:00:00Z",
  );
  assert.equal(
    forecastIsStale(response, Date.parse(response.as_of) + 1_200_000),
    false,
  );
  assert.equal(
    forecastIsStale(response, Date.parse(response.as_of) + 1_200_001),
    true,
  );
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(load(controller.signal), /abort/i);
});

test("network and invalid JSON failures reject without replacing accepted evidence", async (t) => {
  const { createForecastLoader } = await import("../lib/forecast");
  let mode = 0;
  t.mock.method(globalThis, "fetch", async () => {
    if (mode === 1) throw new Error("Offline");
    if (mode === 2) return new Response("{broken");
    return Response.json(syntheticSnapshot());
  });
  const load = createForecastLoader("/forward-v1.json");
  const signal = new AbortController().signal;
  await load(signal);
  mode = 1;
  await assert.rejects(load(signal));
  mode = 2;
  await assert.rejects(load(signal));
  mode = 0;
  assert.deepEqual(await load(signal), syntheticSnapshot());
});

test("isolated forecast renderer shows UTC, all model/cohort labels and undefined accuracy", async () => {
  const { createElement } = await import("react");
  const { renderToStaticMarkup } = await import("react-dom/server");
  const { ForecastEvidence } = await import("../components/forward-dashboard");
  const data = validateForecast(syntheticSnapshot(), now);
  const html = renderToStaticMarkup(
    createElement(ForecastEvidence, { data, checkedAt: now }),
  );
  for (const text of [
    "BTCUSDT",
    "ETHUSDT",
    "UTC",
    "Outcome scored",
    "training mean",
    "gradient boosting",
    "ridge",
    "zero",
    "Undefined",
    "Late manual",
    "Timely automated",
    "automation unattributed",
    "Preliminary",
    "MAE",
    "RMSE",
    "Bias",
    "dimensionless",
    "recipe",
  ])
    assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /portfolio value|profit|ranking/i);
});

test("feed URLs cannot embed credentials or escape same-origin path checks", async () => {
  for (const url of [
    "https://user:secret@example.com/feed.json",
    "//example.com/feed.json",
    "/\\example.com/feed.json",
    "relative.json",
  ])
    await assert.rejects(
      fetchForecast(url, new AbortController().signal),
      /credential-free/,
    );
});

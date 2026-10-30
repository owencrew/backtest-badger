import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  ForecastEvidence,
  ForecastFeedView,
} from "../components/forward-dashboard";
import {
  validateForecast,
  validateForecastV2,
  validatePublicForecast,
  createForecastLoader,
  forecastProjection,
  models,
} from "../lib/forecast";
import { directionOutcome } from "../lib/forecast-display";
import { syntheticV2 } from "./fixtures/forward-v2";
import { syntheticSnapshot } from "./fixtures/forward";
const now = Date.parse("2026-10-15T13:00:00Z");

test("v2 preserves the strict v1 projection and distinguishes pending/latest scored by market", () => {
  const f = syntheticV2();
  assert.deepEqual(validateForecastV2(f, now), f);
  const { latest_scored, ...rest } = f;
  assert.equal(latest_scored.length, 2);
  assert.deepEqual(
    validateForecast({ ...rest, schema_version: 1 }, now).latest,
    f.latest,
  );
  assert.throws(() => validateForecast(f, now));
  assert.throws(() => validateForecastV2(syntheticSnapshot(), now));
  assert.deepEqual(
    validatePublicForecast(syntheticSnapshot(), now),
    syntheticSnapshot(),
  );
  assert.deepEqual(validatePublicForecast(f, now), f);
});
const invalid: [string, (f: ReturnType<typeof syntheticV2>) => void][] = [
  ["duplicate market", (f) => (f.latest_scored[1] = f.latest_scored[0])],
  ["missing matched market", (f) => f.latest_scored.pop()],
  ["extra root key", (f) => Object.assign(f, { private_path: "/private" })],
  [
    "extra scored key",
    (f) => Object.assign(f.latest_scored[0], { record_id: "private" }),
  ],
  [
    "extra model key",
    (f) =>
      Object.assign(f.latest_scored[0].models.ridge, { recipe: "private" }),
  ],
  [
    "late manual",
    (f) =>
      Object.assign(f.latest_scored[0], {
        cohort: "secondary_late_manual",
        issued_at: "2026-10-15T04:17:00Z",
      }),
  ],
  [
    "unattributed",
    (f) => Object.assign(f.latest_scored[0], { cohort: "timely_unattributed" }),
  ],
  [
    "not scored",
    (f) => Object.assign(f.latest_scored[0], { status: "mature_unscored" }),
  ],
  [
    "scored before target",
    (f) => (f.latest_scored[0].scored_at = "2026-10-15T08:00:59Z"),
  ],
  [
    "scored after cutoff",
    (f) => (f.latest_scored[0].scored_at = "2026-10-15T13:00:01Z"),
  ],
  [
    "wrong horizon",
    (f) => (f.latest_scored[0].target_close_at = "2026-10-15T12:00:00Z"),
  ],
  [
    "timestamp offset",
    (f) => (f.latest_scored[0].issued_at = "2026-10-15T04:01:00+00:00"),
  ],
  [
    "invalid calendar",
    (f) => (f.latest_scored[0].scored_at = "2026-02-30T08:02:00Z"),
  ],
  [
    "nonfinite",
    (f) => (f.latest_scored[0].models.ridge.predicted_log_return_4h = NaN),
  ],
  [
    "unknown model",
    (f) => Object.assign(f.latest_scored[0].models, { custom: {} }),
  ],
  [
    "wrong market",
    (f) => Object.assign(f.latest_scored[0], { symbol: "DOGEUSDT" }),
  ],
  ["wrong recipe", (f) => (f.latest_scored[0].recipe_sha256 = "bad")],
  [
    "signed error",
    (f) => (f.latest_scored[0].models.ridge.signed_error += 1e-14),
  ],
  [
    "absolute error",
    (f) => (f.latest_scored[0].models.ridge.absolute_error = -0.005),
  ],
  ["squared error", (f) => (f.latest_scored[0].models.ridge.squared_error = 1)],
  [
    "direction mismatch",
    (f) => (f.latest_scored[0].models.ridge.directional_correct = false),
  ],
  [
    "zero eligible",
    (f) => (f.latest_scored[0].models.zero.directional_correct = true),
  ],
  ["wrong actual direction", (f) => (f.latest_scored[0].actual_direction = -1)],
  [
    "unknown direction",
    (f) => Object.assign(f.latest_scored[0], { actual_direction: 2 }),
  ],
];
for (const [name, mutate] of invalid)
  test(`v2 rejects ${name}`, () => {
    const f = syntheticV2();
    mutate(f);
    assert.throws(() => validateForecastV2(f, now));
  });

test("same issuance must agree across collections regardless of JSON key ordering", () => {
  const f = syntheticV2();
  f.latest = f.latest_scored.map(forecastProjection);
  for (const e of f.evaluations.filter((e) => e.matched_count))
    Object.assign(e, { genuine_predictions: 1, pending_not_settled: 0 });
  validateForecastV2(f, now);
  f.latest[0] = Object.fromEntries(
    Object.entries(f.latest[0]).reverse(),
  ) as (typeof f.latest)[0];
  validateForecastV2(f, now);
  f.latest[0].recipe_sha256 = "b".repeat(64);
  assert.throws(() => validateForecastV2(f, now), /Conflicting/);
});

test("strict saved direction covers negative, positive, zero actual and zero abstention", () => {
  for (const actual of [-0.002, 0, 0.002]) {
    const f = syntheticV2(),
      row = f.latest_scored[0];
    row.actual_log_return_4h = actual;
    row.actual_direction = Math.sign(actual) as -1 | 0 | 1;
    for (const [index, model] of models.entries()) {
      const p =
        index === 0 ? 0 : index === 1 ? -0.001 : index === 2 ? 0.001 : 1e-15;
      const error = p - actual;
      Object.assign(row.models[model], {
        predicted_log_return_4h: p,
        signed_error: error,
        absolute_error: Math.abs(error),
        squared_error: error * error,
        directional_correct:
          p === 0 ? null : Math.sign(p) === row.actual_direction,
      });
      assert.equal(
        directionOutcome(row.models[model].directional_correct),
        p === 0
          ? "N/A"
          : Math.sign(p) === Math.sign(actual)
            ? "Correct"
            : "Incorrect",
      );
    }
    validateForecastV2(f, now);
  }
});

test("v2 rendering separates observations and preserves aggregate evaluation and empty states", () => {
  const f = syntheticV2();
  const html = renderToStaticMarkup(
    createElement(ForecastEvidence, { data: f, checkedAt: now }),
  );
  assert.ok(
    html.indexOf("Latest predictions") <
      html.indexOf("Latest scored forecasts"),
  );
  assert.ok(
    html.indexOf("Latest scored forecasts") <
      html.indexOf("Timely automated evaluation"),
  );
  for (const [symbol, actual] of [
    ["BTCUSDT", "+50.00 bps"],
    ["ETHUSDT", "−20.00 bps"],
  ]) {
    const card = html.match(
      new RegExp(
        `<article[^>]*aria-label="${symbol} latest scored forecast"[\\s\\S]*?</article>`,
      ),
    )![0];
    for (const label of [
      actual,
      "Source candle close",
      "Forecast issued",
      "Outcome scored",
      "Predicted",
      "Signed error",
      "Absolute error",
      "Direction:",
      "Correct",
      "N/A",
      "Scored forecast technical details",
      'tabindex="0"',
    ])
      assert.ok(card.includes(label), label);
  }
  assert.match(html, /Incorrect/);
  assert.match(html, /\+2\.00e-3 bps/);
  assert.doesNotMatch(html, /<details[^>]*\bopen/);
  const v1 = syntheticSnapshot();
  const absent = renderToStaticMarkup(
    createElement(ForecastEvidence, { data: v1, checkedAt: now }),
  );
  assert.match(absent, /unavailable in this version-1 snapshot/);
  f.latest_scored = [];
  for (const e of f.evaluations.filter((e) => e.matched_count)) {
    e.matched_count = 0;
    e.genuine_predictions = 1;
    for (const m of models)
      Object.assign(e.models[m], {
        mae: null,
        rmse: null,
        forecast_bias: null,
        directional_correct: 0,
        directional_denominator: 0,
        directional_accuracy: null,
      });
  }
  validateForecastV2(f, now);
  const empty = renderToStaticMarkup(
    createElement(ForecastEvidence, { data: f, checkedAt: now }),
  );
  assert.equal(
    empty.split("No completed timely forecast available yet.").length - 1,
    2,
  );
  assert.doesNotMatch(empty, /Observed four-hour log return/);
});

test("v2 refresh rejects lost or changed retained scores, clock and schema regression", async (t) => {
  let response = syntheticV2();
  t.mock.method(globalThis, "fetch", async () => Response.json(response));
  const load = createForecastLoader("/forward-v2.json"),
    signal = new AbortController().signal;
  await load(signal);
  response.latest_scored[0].recipe_sha256 = "b".repeat(64);
  await assert.rejects(load(signal), /changed/);
  response = syntheticV2();
  response.as_of = response.generated_at = "2026-10-15T12:59:00Z";
  await assert.rejects(load(signal), /regressed/);
  t.mock.method(globalThis, "fetch", async () =>
    Response.json(syntheticSnapshot()),
  );
  await assert.rejects(load(signal), /schema regressed/);
  t.mock.method(globalThis, "fetch", async () => {
    throw new Error("offline");
  });
  await assert.rejects(load(signal), /offline/);
  const html = renderToStaticMarkup(
    createElement(ForecastFeedView, {
      data: syntheticV2(),
      error: "offline",
      loading: false,
      checkedAt: now + 3600000,
      refresh() {},
    }),
  );
  assert.match(html, /last-good snapshot retained/);
  assert.match(html, /BTCUSDT latest scored forecast/);
});

test("microsecond cutoff violations and submillisecond source misalignment fail closed", () => {
  const f = syntheticV2();
  f.latest_scored[0].scored_at = "2026-10-15T13:00:00.000001Z";
  assert.throws(() => validateForecastV2(f, now), /mature at scoring/);
  f.latest_scored[0].scored_at = "2026-10-15T08:02:00Z";
  f.latest_scored[0].source_close_at = "2026-10-15T04:00:00.000001Z";
  assert.throws(() => validateForecastV2(f, now), /horizon/);
});

test("bounded browser fetching rejects oversized and invalid UTF-8 responses", async (t) => {
  const { fetchForecast } = await import("../lib/forecast");
  for (const bytes of [new Uint8Array(65537), new Uint8Array([0xff])]) {
    t.mock.method(globalThis, "fetch", async () => new Response(bytes));
    await assert.rejects(
      fetchForecast("/forward-v2.json", new AbortController().signal),
    );
  }
});

test("saved Decimal direction remains authoritative if the numeric return underflows", () => {
  const f = syntheticV2(),
    row = f.latest_scored[0];
  row.actual_log_return_4h = 0;
  row.actual_direction = 1;
  for (const model of models) {
    const p = row.models[model].predicted_log_return_4h;
    Object.assign(row.models[model], {
      signed_error: p,
      absolute_error: Math.abs(p),
      squared_error: p * p,
    });
  }
  validateForecastV2(f, now);
});

// Decimal arithmetic reference cases, synthetic only. The browser never rewrites
// the saved values just because binary64 subtraction yields an adjacent number.
for (const [prediction, actual, signed, squared] of [
  [0.0003, 0.0001, 0.0002, 0.00000004],
  [-0.0003, -0.0001, -0.0002, 0.00000004],
  [3e-20, 1e-20, 2e-20, 4e-40],
  [0.10000000000000002, 0.1, 2e-17, 4e-34],
])
  test(`v2 accepts bounded Decimal/binary rounding at ${prediction} without rewriting evidence`, () => {
    const f = syntheticV2(),
      row = f.latest_scored[0];
    row.actual_log_return_4h = actual;
    row.actual_direction = Math.sign(actual) as -1 | 1;
    for (const model of models) {
      const p = model === "zero" ? 0 : prediction;
      const error = model === "zero" ? -actual : signed;
      Object.assign(row.models[model], {
        predicted_log_return_4h: p,
        signed_error: error,
        absolute_error: Math.abs(error),
        squared_error: model === "zero" ? actual * actual : squared,
        directional_correct:
          p === 0 ? null : Math.sign(p) === row.actual_direction,
      });
    }
    const before = JSON.stringify(f);
    validateForecastV2(f, now);
    assert.equal(JSON.stringify(f), before);
    // Materially wrong errors, even small in absolute units, remain invalid.
    row.models.ridge.signed_error +=
      Math.max(Math.abs(prediction), Math.abs(actual)) * 1e-12;
    assert.throws(() => validateForecastV2(f, now), /saved forecast errors/);
  });

test("v2 error tolerance preserves zero, signs, tiny values and squared-error units", () => {
  for (const fault of ["zero", "sign", "absolute", "square", "tiny"]) {
    const f = syntheticV2(),
      row = f.latest_scored[0];
    if (fault === "zero") {
      row.models.ridge.predicted_log_return_4h = row.actual_log_return_4h;
      Object.assign(row.models.ridge, {
        signed_error: Number.MIN_VALUE,
        absolute_error: Number.MIN_VALUE,
        squared_error: 0,
      });
    } else if (fault === "sign") row.models.ridge.signed_error *= -1;
    else if (fault === "absolute") row.models.ridge.absolute_error += 1e-14;
    else if (fault === "square") row.models.ridge.squared_error += 1e-16;
    else {
      row.actual_log_return_4h = 1e-20;
      for (const m of models) {
        const p = m === "zero" ? 0 : 3e-20,
          error = p - 1e-20;
        Object.assign(row.models[m], {
          predicted_log_return_4h: p,
          signed_error: error,
          absolute_error: Math.abs(error),
          squared_error: error * error,
        });
      }
      row.models.ridge.signed_error = 0;
    }
    assert.throws(
      () => validateForecastV2(f, now),
      /saved forecast errors/,
      fault,
    );
  }
});

test("v2 rounding allowance is bounded by eight epsilon at the operand scale", () => {
  for (const factor of [4, 16]) {
    const f = syntheticV2(),
      row = f.latest_scored[0];
    const model = row.models.ridge;
    const error = model.predicted_log_return_4h - row.actual_log_return_4h;
    const scale = Math.max(
      Math.abs(model.predicted_log_return_4h),
      Math.abs(row.actual_log_return_4h),
      Math.abs(error),
    );
    model.signed_error = error + factor * Number.EPSILON * scale;
    model.absolute_error = Math.abs(model.signed_error);
    model.squared_error = model.signed_error * model.signed_error;
    if (factor === 4) validateForecastV2(f, now);
    else
      assert.throws(() => validateForecastV2(f, now), /saved forecast errors/);
  }
});

test("v2 loader retains last good snapshot after missing scored market or microsecond regression", async (t) => {
  let response = syntheticV2();
  response.as_of = response.generated_at = "2026-10-15T13:00:00.000002Z";
  t.mock.method(globalThis, "fetch", async () => Response.json(response));
  const load = createForecastLoader("/forward-v2.json"),
    signal = new AbortController().signal;
  const good = await load(signal);
  response = structuredClone(good) as ReturnType<typeof syntheticV2>;
  response.latest_scored.pop();
  await assert.rejects(load(signal), /coverage/);
  response = structuredClone(good) as ReturnType<typeof syntheticV2>;
  response.generated_at = response.as_of = "2026-10-15T13:00:00.000001Z";
  await assert.rejects(load(signal), /regressed/);
  response = structuredClone(good) as ReturnType<typeof syntheticV2>;
  assert.deepEqual(await load(signal), good);
});

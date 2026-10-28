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

// These snapshots are rendered only in unit tests, never connected to a site.
function twoMarketSnapshot() {
  const data = syntheticSnapshot();
  data.latest.push({ ...structuredClone(data.latest[0]), symbol: "ETHUSDT" });
  data.evaluations[3] = {
    ...structuredClone(data.evaluations[0]),
    symbol: "ETHUSDT",
  };
  return validateForecast(data, now);
}
async function renderEvidence(data = twoMarketSnapshot(), checkedAt = now) {
  const { createElement } = await import("react");
  const { renderToStaticMarkup } = await import("react-dom/server");
  const { ForecastEvidence } = await import("../components/forward-dashboard");
  return renderToStaticMarkup(
    createElement(ForecastEvidence, { data, checkedAt }),
  );
}

test("log-return basis points preserve sign, zero, very small values and missingness", async () => {
  const { logReturnBps } = await import("../lib/forecast-display");
  for (const [value, expected] of [
    [0.0002, "+2.00 bps"],
    [-0.0005, "−5.00 bps"],
    [0, "0.00 bps"],
    [-0, "0.00 bps"],
    [0.0000002, "+2.00e-3 bps"],
    [-0.0000000001, "−1.00e-6 bps"],
    [null, "N/A — no matched outcomes"],
    [undefined, "N/A — no matched outcomes"],
  ] as const)
    assert.equal(logReturnBps(value), expected);
});

test("BTC and ETH cards show four models, bps, original evidence and UTC clocks", async () => {
  const data = twoMarketSnapshot();
  const before = JSON.stringify(data);
  const html = await renderEvidence(data);
  for (const symbol of ["BTCUSDT", "ETHUSDT"]) {
    const card = html.match(
      new RegExp(
        `<article[^>]*aria-label="${symbol} latest prediction"[\\s\\S]*?</article>`,
      ),
    )![0];
    for (const name of ["Zero", "Training mean", "Ridge", "Gradient boosting"])
      assert.ok(card.includes(`<dt>${name}</dt>`));
    for (const label of [
      "Outcome scored",
      "Target close",
      "Source candle close",
      "Forecast issued",
      "UTC",
      "Four-hour predicted log return (bps)",
      "Realised log return",
      "+50.00 bps",
      "Signed error −50.00 bps",
      "Model recipe identity",
      "0.005",
      "Fresh published snapshot",
    ])
      assert.ok(card.includes(label), label);
  }
  assert.match(html, /0\.0001 log-return units/);
  assert.match(html, /Evidence cutoff .*UTC/);
  assert.match(html, /Snapshot generated .*UTC/);
  assert.equal(JSON.stringify(data), before);
});

test("primary evaluations are visible by default, secondary and technical disclosures closed", async () => {
  const html = await renderEvidence();
  const primary = html.match(
    /<section class="primary-evaluation"[\s\S]*?<\/section><\/section>/,
  )![0];
  assert.doesNotMatch(primary, /<details/);
  assert.equal((primary.match(/<table /g) ?? []).length, 2);
  for (const label of [
    "MAE (bps)",
    "RMSE (bps)",
    "Forecast bias (bps)",
    "Direction correct / eligible",
    "Directional accuracy",
    "Preliminary",
    "1 matched",
    "1 / 1",
    "100.0%",
    "0 / 0",
    "N/A — zero forecast",
  ])
    assert.ok(primary.includes(label), label);
  assert.match(
    html,
    /<details class="forecast-disclosure"><summary>Late manual forecasts/,
  );
  assert.match(
    html,
    /<details class="forecast-disclosure"><summary>Detailed forecast evaluation/,
  );
  assert.doesNotMatch(html, /<details[^>]*\bopen/);
  assert.match(html, /not directly comparable/);
  assert.match(html, /additional information timing/);
  assert.match(html, /zero predictions abstain/);
  assert.match(
    html,
    /against a zero outcome remain eligible and count as incorrect/,
  );
  assert.match(html, /BTCUSDT: 0 matched \/ 0 issued/);
  for (const label of [
    "Pending / unsettled",
    "Mature unscored",
    "Missing primary opportunities",
    "Earliest target close",
    "pools retained recipe identities",
    "Original snapshot values",
  ])
    assert.ok(html.includes(label), label);
});

test("zero accuracy is never zero percent; nonzero models can have zero eligible directions", async () => {
  const { directionAccuracy } = await import("../lib/forecast-display");
  const metrics = syntheticSnapshot().evaluations[0].models.zero;
  assert.equal(directionAccuracy("zero", metrics), "N/A — zero forecast");
  assert.equal(
    directionAccuracy("ridge", metrics),
    "N/A — no eligible directions",
  );
  assert.equal(
    directionAccuracy("ridge", {
      ...metrics,
      directional_denominator: 1,
      directional_accuracy: 0,
    }),
    "0.0%",
  );
  assert.equal(
    directionAccuracy("ridge", {
      ...metrics,
      directional_correct: 1,
      directional_denominator: 3,
      directional_accuracy: 1 / 3,
    }),
    "33.3%",
  );
});

test("empty cohorts omit metric tables and automatically show them with matched evidence", async () => {
  const data = twoMarketSnapshot();
  const getUnattributed = (html: string) =>
    html.match(
      /<section class="evaluation-cohort" aria-label="BTCUSDT Timely · automation unattributed evaluation"[\s\S]*?<\/section>/,
    )![0];
  const empty = getUnattributed(await renderEvidence(data));
  assert.match(empty, /No observations recorded in this cohort\./);
  assert.match(empty, /cannot be calculated without matched outcomes/);
  assert.doesNotMatch(empty, /<table/);
  data.evaluations[2] = {
    ...structuredClone(data.evaluations[0]),
    cohort: "timely_unattributed",
  };
  const populated = getUnattributed(
    await renderEvidence(validateForecast(data, now)),
  );
  assert.match(populated, /<table/);
  assert.match(populated, /1 matched/);
  assert.doesNotMatch(populated, /No observations recorded/);
});

test("unmatched issued evidence is not described as an empty cohort or a scored outcome", async () => {
  const data = twoMarketSnapshot();
  data.as_of = data.generated_at = "2026-10-15T07:59:00Z";
  for (const f of data.latest) {
    Object.assign(f, {
      status: "pending_not_settled",
      scored_at: null,
      actual_log_return_4h: null,
    });
    for (const m of models)
      Object.assign(f.models[m], {
        signed_error: null,
        absolute_error: null,
        squared_error: null,
      });
  }
  for (const e of data.evaluations.filter(
    (e) => e.cohort === "primary_timely_automated",
  )) {
    Object.assign(e, { matched_count: 0, pending_not_settled: 1 });
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
  validateForecast(data, now);
  for (const [time, status] of [
    ["07:59:00", "Outcome pending"],
    ["08:00:00", "Target closed · settling"],
    ["08:01:00", "Mature · score not published"],
  ]) {
    const html = await renderEvidence(data, Date.parse(`2026-10-15T${time}Z`));
    assert.ok(html.includes(status));
    assert.match(html, /No matched outcomes recorded/);
    assert.match(html, /Not scored/);
    assert.doesNotMatch(html, /Outcome scored|Signed error/);
  }
});

test("rendered feed distinguishes loading, fresh, stale and failure with retained evidence", async () => {
  const { createElement } = await import("react");
  const { renderToStaticMarkup } = await import("react-dom/server");
  const { ForecastFeedView, ForwardDashboard } =
    await import("../components/forward-dashboard");
  const data = twoMarketSnapshot();
  const render = (props: Partial<Parameters<typeof ForecastFeedView>[0]>) =>
    renderToStaticMarkup(
      createElement(ForecastFeedView, {
        checkedAt: now,
        loading: false,
        refresh: () => {},
        ...props,
      }),
    );
  assert.match(render({ loading: true }), /Checking published snapshot/);
  assert.match(render({ loading: true }), /disabled=""/);
  assert.match(render({ data }), /Fresh published snapshot/);
  assert.match(render({ data, checkedAt: now + 1_200_001 }), /Snapshot stale/);
  const failure = render({ data, error: "Offline" });
  assert.match(failure, /Request failed · last-good snapshot retained/);
  assert.match(failure, /Retained values below have not been updated/);
  assert.match(failure, /BTCUSDT latest prediction/);
  assert.doesNotMatch(failure, /Fresh published snapshot/);
  const unavailable = render({ error: "Offline" });
  assert.match(unavailable, /No verified snapshot loaded/);
  assert.doesNotMatch(unavailable, /latest prediction/);
  const previous = process.env.NEXT_PUBLIC_FORWARD_SNAPSHOT_URL;
  try {
    delete process.env.NEXT_PUBLIC_FORWARD_SNAPSHOT_URL;
    assert.match(
      renderToStaticMarkup(createElement(ForwardDashboard)),
      /Forward forecasts are not published yet/,
    );
  } finally {
    if (previous !== undefined)
      process.env.NEXT_PUBLIC_FORWARD_SNAPSHOT_URL = previous;
  }
});

import assert from "node:assert/strict";
import { test } from "node:test";
import {
  validateMarket,
  windowFor,
  ranges,
  fetchMarket,
  type Range,
} from "../lib/market";
// Synthetic Binance-shaped unit data. No fixtures are used by the website.
const now = Date.parse("2026-10-25T12:03:00Z");
function fixture(range: Range = "1D") {
  const { start } = windowFor(range, now),
    { step } = ranges[range];
  return Array.from(
    { length: Math.floor((now - start) / step) + 1 },
    (_, i) => [
      start + i * step,
      "100",
      "110",
      "90",
      "105",
      "10",
      start + (i + 1) * step - 1,
      "1000",
      12,
      "5",
      "500",
      "0",
    ],
  );
}
const ticker = { symbol: "BTCUSDT", price: "105" };
test("all ranges fit a single UTC-aligned Binance page and distinguish open candle", () => {
  for (const range of Object.keys(ranges) as Range[]) {
    const result = validateMarket(
      "BTCUSDT",
      range,
      ticker,
      fixture(range),
      now,
      now,
    );
    assert.ok(result.candles.length <= 1000);
    assert.equal(result.missing, 0);
    assert.equal(result.candles.at(-1)!.complete, false);
    assert.ok(result.candles.slice(0, -1).every((c) => c.complete));
  }
});
test("gaps remain missing rather than invented, including window edges", () => {
  const rows = fixture();
  rows.splice(5, 2);
  rows.shift();
  rows.pop();
  assert.equal(
    validateMarket("BTCUSDT", "1D", ticker, rows, now, now).missing,
    4,
  );
});
for (const [name, mutate] of [
  [
    "duplicates",
    (r: unknown[][]) => {
      r[1] = r[0];
    },
  ],
  ["reversed order", (r: unknown[][]) => r.reverse()],
  [
    "invalid OHLC",
    (r: unknown[][]) => {
      r[0][2] = "50";
    },
  ],
  [
    "nonfinite",
    (r: unknown[][]) => {
      r[0][1] = "Infinity";
    },
  ],
  [
    "empty number",
    (r: unknown[][]) => {
      r[0][1] = "";
    },
  ],
  [
    "wrong close timestamp",
    (r: unknown[][]) => {
      r[0][6] = Number(r[0][6]) + 1;
    },
  ],
  [
    "unaligned timestamp",
    (r: unknown[][]) => {
      r[0][0] = Number(r[0][0]) + 1;
    },
  ],
  [
    "impossible volume",
    (r: unknown[][]) => {
      r[0][9] = "11";
    },
  ],
] as const)
  test(`rejects ${name}`, () => {
    const r = fixture();
    mutate(r);
    assert.throws(() => validateMarket("BTCUSDT", "1D", ticker, r, now, now));
  });
test("rejects wrong market, clock mismatch and empty responses", () => {
  assert.throws(() =>
    validateMarket("ETHUSDT", "1D", ticker, fixture(), now, now),
  );
  assert.throws(() =>
    validateMarket("BTCUSDT", "1D", ticker, fixture(), now, now + 60_001),
  );
  assert.throws(() => validateMarket("BTCUSDT", "1D", ticker, [], now, now));
});
test("exact close boundary completes preceding candle", () => {
  const rows = fixture();
  rows.pop();
  const boundary = Number(rows.at(-1)![6]) + 1;
  assert.equal(
    validateMarket(
      "BTCUSDT",
      "1D",
      ticker,
      rows,
      boundary,
      boundary,
    ).candles.at(-1)!.complete,
    true,
  );
});
test("fetch requests selected market/range and rejects failed HTTP without a snapshot", async (t) => {
  const urls: string[] = [];
  t.mock.method(Date, "now", () => now);
  t.mock.method(
    globalThis,
    "fetch",
    async (url: string, options: RequestInit) => {
      urls.push(url);
      assert.equal(options.credentials, "omit");
      return Response.json(
        url.includes("/time")
          ? { serverTime: now }
          : url.includes("/klines")
            ? fixture("90D")
            : { symbol: "ETHUSDT", price: "105" },
      );
    },
  );
  const result = await fetchMarket(
    "ETHUSDT",
    "90D",
    new AbortController().signal,
  );
  assert.equal(result.symbol, "ETHUSDT");
  assert.ok(
    urls.some(
      (u) =>
        u.includes("symbol=ETHUSDT&interval=4h") && u.includes("timeZone=0"),
    ),
  );
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response("Unavailable", { status: 429 }),
  );
  await assert.rejects(
    fetchMarket("BTCUSDT", "1D", new AbortController().signal),
    /429/,
  );
});

test("weekly candles use Monday UTC, including the partial listing week", () => {
  const rows = fixture("ALL");
  assert.equal(
    new Date(Number(rows[0][0])).toISOString(),
    "2017-08-14T00:00:00.000Z",
  );
  assert.notEqual(Number(rows[0][0]) % ranges.ALL.step, 0);
  for (const symbol of ["BTCUSDT", "ETHUSDT"] as const) {
    const result = validateMarket(
      symbol,
      "ALL",
      { ...ticker, symbol },
      rows,
      now,
      now,
    );
    assert.equal(result.missing, 0);
    assert.ok(result.candles.every((c) => new Date(c.time).getUTCDay() === 1));
  }
  rows.splice(2, 1);
  rows.shift();
  rows.pop();
  assert.equal(
    validateMarket("BTCUSDT", "ALL", ticker, rows, now, now).missing,
    3,
  );
  const thursday = fixture("ALL").map((r) => {
    r[0] = Number(r[0]) + 3 * 86_400_000;
    r[6] = Number(r[6]) + 3 * 86_400_000;
    return r;
  });
  assert.throws(() =>
    validateMarket("BTCUSDT", "ALL", ticker, thursday, now, now),
  );
});

test("weekly completion rolls at Monday midnight, including year boundaries", () => {
  const boundary = Date.parse("2027-01-04T00:00:00Z");
  const start = boundary - ranges.ALL.step;
  const row = [
    start,
    "100",
    "110",
    "90",
    "105",
    "10",
    boundary - 1,
    "1000",
    12,
    "5",
    "500",
    "0",
  ];
  assert.equal(
    validateMarket(
      "BTCUSDT",
      "ALL",
      ticker,
      [row],
      boundary - 1,
      boundary - 1,
      start,
    ).candles[0].complete,
    false,
  );
  const result = validateMarket(
    "BTCUSDT",
    "ALL",
    ticker,
    [row],
    boundary,
    boundary,
    start,
  );
  assert.equal(result.candles[0].complete, true);
  assert.equal(result.missing, 1);
});

for (const range of ["1Y", "ALL"] as const) {
  test(`${range} caches validated history, refreshes overlap, isolates symbols and expires daily`, async (t) => {
    let clock = now;
    let failure = "";
    let close = "105";
    let cancelled: AbortController | undefined;
    const starts: number[] = [];
    t.mock.method(Date, "now", () => clock);
    t.mock.method(globalThis, "fetch", async (url: string) => {
      const parsed = new URL(url);
      if (parsed.pathname.endsWith("/time"))
        return Response.json({ serverTime: clock });
      const symbol = parsed.searchParams.get("symbol");
      if (parsed.pathname.endsWith("/price"))
        return Response.json({ symbol, price: close });
      const start = Number(parsed.searchParams.get("startTime"));
      starts.push(start);
      if (failure === "http") return new Response("Failure", { status: 503 });
      const fullStart = windowFor(range, clock).start;
      const { step } = ranges[range];
      const rows = Array.from(
        { length: Math.floor((clock - fullStart) / step) + 1 },
        (_, i) => {
          const time = fullStart + i * step;
          return [
            time,
            "100",
            "110",
            "90",
            close,
            "10",
            time + step - 1,
            "1000",
            12,
            "5",
            "500",
            "0",
          ];
        },
      ).filter((r) => Number(r[0]) >= start);
      if (failure === "bounds")
        rows.unshift([start - step, ...rows[0].slice(1)]);
      if (failure === "duplicate") rows.push(rows[0]);
      if (failure === "empty") rows.length = 0;
      cancelled?.abort();
      return Response.json(rows);
    });
    const load = (symbol: "BTCUSDT" | "ETHUSDT" = "BTCUSDT") =>
      fetchMarket(symbol, range, new AbortController().signal);
    const initial = await load();
    assert.equal(starts.at(-1), windowFor(range, clock).start);
    clock += 300_000;
    close = "106";
    const refreshed = await load();
    assert.equal(
      starts.at(-1),
      initial.candles.at(-1)!.time - ranges[range].step,
    );
    assert.equal(refreshed.candles.length, initial.candles.length);
    assert.equal(refreshed.candles[0].close, 105);
    assert.equal(refreshed.candles.at(-1)!.close, 106);
    assert.equal(initial.candles.at(-1)!.close, 105);
    assert.equal(initial.observedAt, now);
    for (failure of ["http", "bounds", "duplicate", "empty"])
      await assert.rejects(load());
    failure = "";
    cancelled = new AbortController();
    await assert.rejects(fetchMarket("BTCUSDT", range, cancelled.signal));
    cancelled = undefined;
    await load("ETHUSDT");
    assert.equal(starts.at(-1), windowFor(range, clock).start);
    // Cross midnight/Monday before cache expiry: the previous open candle closes
    // and the new candle appears without downloading stable history again.
    clock = Number(refreshed.candles.at(-1)!.closeTime) + 1;
    const rollover = await load();
    assert.equal(
      starts.at(-1),
      initial.candles.at(-1)!.time - ranges[range].step,
    );
    assert.equal(rollover.missing, 0);
    assert.equal(rollover.candles.at(-2)!.complete, true);
    assert.equal(rollover.candles.at(-1)!.complete, false);
    clock = now - 1000;
    await assert.rejects(load(), /backwards/);
    clock = now + 86_400_000;
    const expired = await load();
    assert.equal(starts.at(-1), windowFor(range, clock).start);
    assert.equal(expired.candles[0].close, 106);
    assert.equal(expired.missing, 0);
  });
}

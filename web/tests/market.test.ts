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

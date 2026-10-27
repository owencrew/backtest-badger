// Optional live verification; never part of offline CI or a research export.
import assert from "node:assert/strict";
import { fetchMarket, ranges, symbols, utc, type Range } from "../lib/market";
const originalFetch = globalThis.fetch;
let klineRows = 0;
globalThis.fetch = async (...args) => {
  const response = await originalFetch(...args);
  if (String(args[0]).includes("/klines?")) {
    const rows = await response.clone().json();
    klineRows = Array.isArray(rows) ? rows.length : 0;
  }
  return response;
};
for (const symbol of symbols) {
  for (const range of Object.keys(ranges) as Range[]) {
    const result = await fetchMarket(
      symbol,
      range,
      AbortSignal.timeout(15_000),
    );
    console.log(
      JSON.stringify({
        symbol,
        range,
        interval: ranges[range].interval,
        server: utc(result.serverTime),
        first: utc(result.candles[0].time),
        last: utc(result.candles.at(-1)!.time),
        candles: result.candles.length,
        missing: result.missing,
        tailComplete: result.candles.at(-1)!.complete,
      }),
    );
    if (range === "1Y" || range === "ALL") {
      const refreshed = await fetchMarket(
        symbol,
        range,
        AbortSignal.timeout(15_000),
      );
      assert.ok(klineRows <= 3, "Expected only the recent tail on refresh");
      assert.equal(refreshed.candles[0].time, result.candles[0].time);
      console.log(
        `${symbol} ${range} refresh: ${klineRows} downloaded, ${refreshed.candles.length} displayed`,
      );
    }
  }
}

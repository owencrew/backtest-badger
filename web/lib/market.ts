export const symbols = ["BTCUSDT", "ETHUSDT"] as const;
export type Symbol = (typeof symbols)[number];
export const ranges = {
  "1D": { days: 1, interval: "5m", step: 300_000 },
  "7D": { days: 7, interval: "30m", step: 1_800_000 },
  "30D": { days: 30, interval: "1h", step: 3_600_000 },
  "90D": { days: 90, interval: "4h", step: 14_400_000 },
} as const;
export type Range = keyof typeof ranges;
export const BINANCE = "https://data-api.binance.vision";
export const REFRESH_MS = 300_000;
export type Candle = {
  time: number;
  closeTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  complete: boolean;
};
export type MarketSnapshot = {
  symbol: Symbol;
  range: Range;
  price: number;
  observedAt: number;
  serverTime: number;
  candles: Candle[];
  missing: number;
};
export function requireValue(
  condition: unknown,
  message: string,
): asserts condition {
  if (!condition) throw new Error(message);
}
function decimal(value: unknown, positive = true): number {
  requireValue(
    typeof value === "string" && /^\d+(\.\d+)?$/.test(value),
    "Invalid Binance numeric value.",
  );
  const n = Number(value);
  requireValue(
    Number.isFinite(n) && (positive ? n > 0 : n >= 0),
    "Invalid Binance numeric value.",
  );
  return n;
}
export function windowFor(range: Range, now: number) {
  const { days, step } = ranges[range];
  return {
    start: Math.floor((now - days * 86_400_000) / step) * step,
    end: now,
  };
}
export function validateMarket(
  symbol: Symbol,
  range: Range,
  ticker: unknown,
  raw: unknown,
  serverTime: number,
  observedAt: number,
): MarketSnapshot {
  requireValue(
    symbols.includes(symbol) && range in ranges,
    "Unsupported market or range.",
  );
  requireValue(
    Number.isSafeInteger(serverTime) &&
      serverTime > 0 &&
      Math.abs(serverTime - observedAt) < 60_000,
    "Binance clock differs from this device; check your clock.",
  );
  requireValue(
    typeof ticker === "object" &&
      ticker !== null &&
      "symbol" in ticker &&
      ticker.symbol === symbol &&
      "price" in ticker,
    "Binance returned an unexpected symbol.",
  );
  const price = decimal(ticker.price);
  requireValue(
    Array.isArray(raw) && raw.length > 0 && raw.length <= 1000,
    "No usable Binance candles returned.",
  );
  const { step } = ranges[range];
  const { start, end } = windowFor(range, serverTime);
  let previous = start - step;
  let missing = 0;
  const candles = raw.map((r): Candle => {
    requireValue(
      Array.isArray(r) && r.length === 12,
      "Invalid Binance candle shape.",
    );
    const [time, o, h, l, c, v, closeTime, q, trades, tb, tq] = r;
    requireValue(
      Number.isSafeInteger(time) &&
        time % step === 0 &&
        time >= start &&
        time <= end &&
        time > previous,
      "Unordered, duplicate or out-of-window Binance timestamps.",
    );
    requireValue(
      closeTime === time + step - 1,
      "Incomplete Binance candle interval.",
    );
    const [open, high, low, close] = [o, h, l, c].map((n) => decimal(n));
    requireValue(
      low <= Math.min(open, close) &&
        high >= Math.max(open, close) &&
        low <= high,
      "Invalid Binance OHLC bounds.",
    );
    requireValue(
      decimal(tb, false) <= decimal(v, false) &&
        decimal(tq, false) <= decimal(q, false) &&
        Number.isSafeInteger(trades) &&
        trades >= 0,
      "Invalid Binance candle volumes.",
    );
    missing += (time - previous) / step - 1;
    previous = time;
    return {
      time,
      closeTime,
      open,
      high,
      low,
      close,
      complete: closeTime < serverTime,
    };
  });
  missing += Math.floor(serverTime / step) - previous / step;
  return { symbol, range, price, observedAt, serverTime, candles, missing };
}
export async function fetchJson(
  url: string,
  signal: AbortSignal,
): Promise<unknown> {
  const response = await fetch(url, {
    signal,
    cache: "no-store",
    credentials: "omit",
  });
  if (!response.ok)
    throw new Error(
      `Data request failed (HTTP ${response.status}). Try again later.`,
    );
  return response.json();
}
export async function fetchMarket(
  symbol: Symbol,
  range: Range,
  signal: AbortSignal,
): Promise<MarketSnapshot> {
  const clock = await fetchJson(`${BINANCE}/api/v3/time`, signal);
  requireValue(
    typeof clock === "object" &&
      clock !== null &&
      "serverTime" in clock &&
      typeof clock.serverTime === "number",
    "Invalid Binance server clock.",
  );
  const serverTime = clock.serverTime;
  const { start, end } = windowFor(range, serverTime);
  const query = new URLSearchParams({
    symbol,
    interval: ranges[range].interval,
    startTime: String(start),
    endTime: String(end),
    timeZone: "0",
    limit: "1000",
  });
  const [candles, ticker] = await Promise.all([
    fetchJson(`${BINANCE}/api/v3/klines?${query}`, signal),
    fetchJson(`${BINANCE}/api/v3/ticker/price?symbol=${symbol}`, signal),
  ]);
  return validateMarket(symbol, range, ticker, candles, serverTime, Date.now());
}
export const utc = (ms: number) =>
  new Date(ms)
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d{3}Z$/, " UTC");

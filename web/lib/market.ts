export const symbols = ["BTCUSDT", "ETHUSDT"] as const;
export type Symbol = (typeof symbols)[number];
export const ranges = {
  "1D": { days: 1, interval: "5m", step: 300_000 },
  "7D": { days: 7, interval: "30m", step: 1_800_000 },
  "30D": { days: 30, interval: "1h", step: 3_600_000 },
  "90D": { days: 90, interval: "4h", step: 14_400_000 },
  "1Y": { days: 365, interval: "1d", step: 86_400_000 },
  ALL: { days: 0, interval: "1w", step: 604_800_000 },
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
// Both supported markets have a first partial listing week labelled by Binance
// with its normal Monday opening, not the first trade timestamp.
export const LISTING_WEEK = Date.parse("2017-08-14T00:00:00Z");
const MONDAY_OFFSET = 4 * 86_400_000; // 1970-01-05, not Unix epoch Thursday
export const HISTORY_TTL_MS = 86_400_000;
export function candleStart(range: Range, time: number) {
  const offset = range === "ALL" ? MONDAY_OFFSET : 0;
  return (
    Math.floor((time - offset) / ranges[range].step) * ranges[range].step +
    offset
  );
}
export function windowFor(range: Range, now: number) {
  const { days } = ranges[range];
  return {
    start:
      range === "ALL"
        ? LISTING_WEEK
        : candleStart(range, now - days * 86_400_000),
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
  requestedStart = windowFor(range, serverTime).start,
): MarketSnapshot {
  requireValue(
    symbols.includes(symbol) && range in ranges,
    "Unsupported market or range.",
  );
  requireValue(
    Number.isSafeInteger(serverTime) &&
      Number.isSafeInteger(observedAt) &&
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
  const { start: windowStart, end } = windowFor(range, serverTime);
  const start = requestedStart;
  requireValue(
    start >= windowStart && start <= end && candleStart(range, start) === start,
    "Invalid Binance request boundary.",
  );
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
        candleStart(range, time) === time &&
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
  missing += (candleStart(range, serverTime) - previous) / step;
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
// Per-tab memory only: four bounded entries (two symbols × two long ranges).
// Raw rows are retained only after validation; no private data or disk storage.
const history = new Map<
  string,
  { rows: unknown[][]; checkedAt: number; serverTime: number }
>();
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
  requireValue(
    Number.isSafeInteger(serverTime) &&
      Math.abs(serverTime - Date.now()) < 60_000,
    "Binance clock differs from this device; check your clock.",
  );
  const { start, end } = windowFor(range, serverTime);
  const { step } = ranges[range];
  // All six ranges currently fit one page. Fail explicitly rather than truncate
  // ALL history if it eventually outgrows Binance's 1,000-row limit.
  requireValue(
    (candleStart(range, end) - start) / step + 1 <= 1000,
    "This history exceeds the supported Binance request window.",
  );
  const key = `${symbol}/${range}`;
  const cached = history.get(key);
  if (cached)
    requireValue(
      serverTime >= cached.serverTime,
      "Binance server clock moved backwards.",
    );
  const reuse = cached && serverTime - cached.checkedAt < HISTORY_TTL_MS;
  const requestStart = reuse
    ? Math.max(start, Number(cached.rows.at(-1)![0]) - step)
    : start;
  const query = new URLSearchParams({
    symbol,
    interval: ranges[range].interval,
    startTime: String(requestStart),
    endTime: String(end),
    timeZone: "0",
    limit: "1000",
  });
  const [tail, ticker] = await Promise.all([
    fetchJson(`${BINANCE}/api/v3/klines?${query}`, signal),
    fetchJson(`${BINANCE}/api/v3/ticker/price?symbol=${symbol}`, signal),
  ]);
  const observedAt = Date.now();
  // Validate the response against its own requested bounds before merging.
  validateMarket(
    symbol,
    range,
    ticker,
    tail,
    serverTime,
    observedAt,
    requestStart,
  );
  const rows = reuse
    ? [
        ...cached.rows.filter(
          (r) => Number(r[0]) >= start && Number(r[0]) < requestStart,
        ),
        ...(tail as unknown[][]),
      ]
    : (tail as unknown[][]);
  const snapshot = validateMarket(
    symbol,
    range,
    ticker,
    rows,
    serverTime,
    observedAt,
  );
  signal.throwIfAborted();
  if (range === "1Y" || range === "ALL")
    history.set(key, {
      rows,
      checkedAt: reuse ? cached.checkedAt : serverTime,
      serverTime,
    });
  return snapshot;
}
export const utc = (ms: number) =>
  new Date(ms)
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d{3}Z$/, " UTC");

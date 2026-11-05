import data from "./study002-data.json";

export const studySymbols = ["BTCUSDT", "ETHUSDT"] as const;
export type StudySymbol = (typeof studySymbols)[number];
export const strategyNames = {
  trend_30d_daily_v1: "30-Day Trend",
  ridge: "Ridge Sign",
  buy_and_hold: "Buy & Hold",
  cash: "Cash",
} as const;
export type StudyStrategy = keyof typeof strategyNames;
export interface StudyAccount {
  id: string;
  symbol: StudySymbol;
  strategy: StudyStrategy;
  initialFunding: string;
  firstEquity: string;
  finalEquity: string;
  returnFraction: string;
  drawdownFraction: string;
  buys: number;
  sells: number;
  exposureSeconds: number;
  fees: string;
  halfSpread: string;
  slippage: string;
  totalCosts: string;
  sharpe: { value: string | null; reason: string | null };
  monthly: { month: string; complete: boolean; returnFraction: string }[];
}

// Decimal source strings remain authoritative. BigInt handles display rounding,
// including percentages, without converting financial values to binary floats.
export function decimalParts(value: string): [bigint, bigint] {
  if (typeof value !== "string" || value.length > 180)
    throw new Error("Invalid Study 002 decimal");
  const match = value.match(/^(-?\d+)(?:\.(\d+))?(?:E([+-]?\d{1,3}))?$/);
  if (!match) throw new Error("Invalid Study 002 decimal");
  const [, whole, fraction = "", exponent = "0"] = match;
  const places = fraction.length - Number(exponent);
  if (Math.abs(places) > 180) throw new Error("Invalid decimal exponent");
  const numerator = BigInt(whole + fraction);
  return places >= 0
    ? [numerator, 10n ** BigInt(places)]
    : [numerator * 10n ** BigInt(-places), 1n];
}
export function studyNumber(
  value: string,
  digits = 2,
  multiplier = 1n,
  divisor = 1n,
) {
  const [numerator, sourceDenominator] = decimalParts(value);
  const denominator = sourceDenominator * divisor;
  const scaled = numerator * multiplier * 10n ** BigInt(digits);
  const absolute = scaled < 0n ? -scaled : scaled;
  const rounded = (absolute * 2n + denominator) / (2n * denominator);
  const text = rounded.toString().padStart(digits + 1, "0");
  const whole = (digits ? text.slice(0, -digits) : text).replace(
    /\B(?=(\d{3})+(?!\d))/g,
    ",",
  );
  return `${scaled < 0n ? "−" : ""}${whole}${digits ? `.${text.slice(-digits)}` : ""}`;
}
export function studyPercent(value: string, signed = true) {
  const [n] = decimalParts(value);
  return `${signed && n > 0n ? "+" : ""}${studyNumber(value, 2, 100n)}%`;
}
export function returnTone(value: string) {
  const [n] = decimalParts(value);
  return n < 0n ? "negative" : n > 0n ? "positive" : "";
}
// Bounded chart presentation only. Never used for accounting or display rounding.
export function costBarWidth(value: string) {
  decimalParts(value);
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0 || n > 10000)
    throw new Error("Invalid cost chart bound");
  return n / 100;
}
function keys(value: object, expected: string[]) {
  if (Object.keys(value).sort().join() !== expected.sort().join())
    throw new Error("Unexpected Study 002 fields");
}
function inRange(value: string, low: bigint, high: bigint) {
  const [n, d] = decimalParts(value);
  if (n < low * d || n > high * d)
    throw new Error("Out-of-range Study 002 value");
}
export function validateStudyAccounts(
  value: unknown,
): asserts value is StudyAccount[] {
  if (!Array.isArray(value) || value.length !== 8)
    throw new Error("Expected eight accounts");
  const identities = new Set<string>();
  for (const a of value) {
    if (!a || typeof a !== "object") throw new Error("Invalid account");
    keys(a, [
      "id",
      "symbol",
      "strategy",
      "initialFunding",
      "firstEquity",
      "finalEquity",
      "returnFraction",
      "drawdownFraction",
      "buys",
      "sells",
      "exposureSeconds",
      "fees",
      "halfSpread",
      "slippage",
      "totalCosts",
      "sharpe",
      "monthly",
    ]);
    if (
      !studySymbols.includes(a.symbol) ||
      !Object.hasOwn(strategyNames, a.strategy)
    )
      throw new Error("Unexpected market or strategy");
    const expectedId = `${a.strategy === "ridge" ? "genuine_publication_hypothetical_minute_replay" : "study-002"}:${a.symbol}:${a.strategy}`;
    if (a.id !== expectedId || identities.has(a.id))
      throw new Error("Inconsistent account identity");
    identities.add(a.id);
    if (a.initialFunding !== "10000") throw new Error("Invalid funding");
    for (const field of ["firstEquity", "finalEquity"])
      inRange(a[field], 0n, 100000n);
    inRange(a.returnFraction, -1n, 10n);
    inRange(a.drawdownFraction, 0n, 1n);
    for (const field of ["fees", "halfSpread", "slippage", "totalCosts"])
      inRange(a[field], 0n, 10000n);
    const [equity, equityScale] = decimalParts(a.finalEquity);
    const [growth, growthScale] = decimalParts(a.returnFraction);
    if (equity * growthScale !== 10000n * equityScale * (growthScale + growth))
      throw new Error("Inconsistent funding-relative return");
    const components = [a.fees, a.halfSpread, a.slippage].map(decimalParts);
    const [total, totalScale] = decimalParts(a.totalCosts);
    const scale = components.reduce((acc, [, d]) => acc * d, totalScale);
    if (
      components.reduce((sum, [n, d]) => sum + n * (scale / d), 0n) !==
      total * (scale / totalScale)
    )
      throw new Error("Inconsistent attributed costs");
    for (const field of ["buys", "sells", "exposureSeconds"]) {
      if (
        !Number.isSafeInteger(a[field]) ||
        a[field] < 0 ||
        a[field] > (field === "exposureSeconds" ? 31622400 : 2196)
      )
        throw new Error("Invalid activity");
    }
    keys(a.sharpe, ["value", "reason"]);
    if (a.sharpe.value === null) {
      if (
        a.strategy !== "cash" ||
        a.sharpe.reason !== "insufficient_days_or_zero_variance"
      )
        throw new Error("Missing statistic reason");
    } else {
      inRange(a.sharpe.value, -100n, 100n);
      if (a.sharpe.reason !== null || a.strategy === "cash")
        throw new Error("Inconsistent statistic");
    }
    if (!Array.isArray(a.monthly) || a.monthly.length !== 12)
      throw new Error("Missing months");
    a.monthly.forEach((m: StudyAccount["monthly"][number], i: number) => {
      keys(m, ["month", "complete", "returnFraction"]);
      if (
        m.month !== `2024-${String(i + 1).padStart(2, "0")}` ||
        m.complete !== i < 11
      )
        throw new Error("Inconsistent monthly period");
      inRange(m.returnFraction, -1n, 10n);
    });
  }
}
keys(data, [
  "sourceRevision",
  "sourceHashes",
  "summaryHashes",
  "periodStart",
  "lastMark",
  "units",
  "accounts",
]);
keys(data.units, ["money", "returns", "exposure"]);
validateStudyAccounts(data.accounts);
export const study002 = data as Omit<typeof data, "accounts"> & {
  accounts: StudyAccount[];
};
export const studySourceRoot = `https://github.com/owencrew/backtest-badger/blob/${study002.sourceRevision}/docs/studies`;
export const studyReportUrl = `${studySourceRoot}/study-002-slower-trend-results.md`;
export const studyMethodUrl = `${studySourceRoot}/study-002-methodology.md`;

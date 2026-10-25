// Transcribed from the public E.5g report, never from private run artifacts.
// Decimal strings preserve the source; Number conversion is presentation-only.
export const repository = "https://github.com/owencrew/backtest-badger";
export const sourceRevision = "c6d2a1704c620c3136bda13b65f8c1e0dc546bfd";
export const reportFile = "stage-04b2e5g-first-genuine-historical-backtest.md";
export const reportUrl = `${repository}/blob/${sourceRevision}/docs/${reportFile}`;
export const research = {
  evidenceDate: "2026-10-24",
  finalMark: "2024-12-31 23:00 UTC",
  period: "2024",
  initialCapital: "10000",
  source: reportUrl,
  model: "Ridge sign · long / cash",
  feeBps: 10,
  halfSpreadBps: 1,
  slippageBps: 2,
};

export type Account = {
  strategy: "Ridge" | "Cash" | "Buy & Hold";
  returnPct: string;
  finalValue: string;
  drawdownPct: string;
  buys: number;
  sells: number;
  turnover: string;
  costs: string;
};
export type Market = { symbol: string; name: string; accounts: Account[] };
export const markets: Market[] = [
  {
    symbol: "BTCUSDT",
    name: "Bitcoin",
    accounts: [
      {
        strategy: "Ridge",
        returnPct: "-60.69144349771232",
        finalValue: "3930.855650228768",
        drawdownPct: "65.410518",
        buys: 570,
        sells: 570,
        turnover: "764.0090531145331794",
        costs: "9932.118043791232",
      },
      {
        strategy: "Cash",
        returnPct: "0",
        finalValue: "10000",
        drawdownPct: "0.000000",
        buys: 0,
        sells: 0,
        turnover: "0",
        costs: "0",
      },
      {
        strategy: "Buy & Hold",
        returnPct: "120.81233105286866",
        finalValue: "22081.233105286866",
        drawdownPct: "32.310653",
        buys: 1,
        sells: 0,
        turnover: "0.9989997144093134",
        costs: "12.986097463134",
      },
    ],
  },
  {
    symbol: "ETHUSDT",
    name: "Ether",
    accounts: [
      {
        strategy: "Ridge",
        returnPct: "-57.95605761760247",
        finalValue: "4204.394238239753",
        drawdownPct: "65.787102",
        buys: 499,
        sells: 499,
        turnover: "710.7303185600881653",
        costs: "9239.494456250247",
      },
      {
        strategy: "Cash",
        returnPct: "0",
        finalValue: "10000",
        drawdownPct: "0.000000",
        buys: 0,
        sells: 0,
        turnover: "0",
        costs: "0",
      },
      {
        strategy: "Buy & Hold",
        returnPct: "46.17584036417081",
        finalValue: "14617.584036417081",
        drawdownPct: "46.655060",
        buys: 1,
        sells: 0,
        turnover: "0.9990008613482919",
        costs: "12.986112372919",
      },
    ],
  },
];
export function number(value: string | number, digits = 2) {
  return Number(value).toLocaleString("en-GB", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}
export function percent(value: string | number) {
  const n = Number(value);
  return `${n < 0 ? "−" : n > 0 ? "+" : ""}${number(Math.abs(n))}%`;
}

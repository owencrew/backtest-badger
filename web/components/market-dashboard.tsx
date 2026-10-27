"use client";
import { useCallback, useState } from "react";
import {
  fetchMarket,
  ranges,
  symbols,
  utc,
  REFRESH_MS,
  type Range,
  type Symbol,
} from "@/lib/market";
import { MarketChart, priceText } from "./market-chart";
import { useFeed } from "./use-feed";
import { Status } from "./ui";
function MarketFeed({
  symbol,
  range,
  mode,
}: {
  symbol: Symbol;
  range: Range;
  mode: "Candles" | "Line";
}) {
  const loader = useCallback(
    (signal: AbortSignal) => fetchMarket(symbol, range, signal),
    [symbol, range],
  );
  const { data, loading, error, checkedAt, refresh } = useFeed(loader);
  const stale =
    !!data &&
    (!!error ||
      checkedAt - data.observedAt > REFRESH_MS * 2 ||
      data.serverTime - data.candles.at(-1)!.closeTime > ranges[range].step);
  return (
    <>
      <div className="market-summary">
        <div>
          <p className="eyebrow">{symbol} · Observed price</p>
          <strong className="market-price">
            {data ? priceText(data.price) : "—"} <small>USDT</small>
          </strong>
        </div>
        <div className="market-refresh">
          <Status muted={stale || !data}>
            {loading
              ? "Refreshing…"
              : stale
                ? "Stale · last successful observation"
                : data
                  ? "Public market data"
                  : "Unavailable"}
          </Status>
          <button
            className="button button-secondary"
            onClick={refresh}
            disabled={loading}
          >
            Refresh prices
          </button>
        </div>
      </div>
      <p className="small muted">
        Source: <a href="https://data.binance.vision/">Binance Spot</a> ·{" "}
        {ranges[range].interval} candles ·{" "}
        {data
          ? `Last successful refresh ${utc(data.observedAt)}`
          : "No successful refresh yet"}
      </p>
      {error && (
        <p role="alert" className="feed-error">
          Market request failed: {error}{" "}
          {data
            ? "The displayed values are from the timestamp above."
            : "No price has been substituted. Binance may be unavailable from your network or region."}
        </p>
      )}
      {data ? (
        <>
          <p className="small muted">
            Available candle openings: {utc(data.candles[0].time)} to{" "}
            {utc(data.candles.at(-1)!.time)}.
            {range === "ALL" &&
              " Weeks begin Monday UTC. The first week includes only listing-era trading from August 2017; its Monday label is not a first-trade date. Weekly bars do not establish uninterrupted trading within each week."}
          </p>
          <MarketChart data={data} mode={mode} />
          {data.missing > 0 && (
            <p className="feed-error">
              {data.missing} missing candle interval(s) in this window. Gaps are
              not interpolated.
            </p>
          )}
        </>
      ) : (
        <div className="chart-empty" role="status">
          {loading
            ? "Loading Binance market observations…"
            : "Market chart unavailable. Use Refresh prices to retry."}
        </div>
      )}
      <p className="panel-footnote">
        Refreshes about every five minutes while this page is visible. Price is
        the latest ticker value received, not a streaming quote; Binance
        supplies no trade timestamp on this endpoint. Candles may be revised by
        the provider.
        {(range === "1Y" || range === "ALL") &&
          " Earlier candles are cached in this tab for up to 24 hours; refresh updates the latest two intervals. Reload the page to recheck the full history."}
      </p>
    </>
  );
}
export function MarketDashboard() {
  const [symbol, setSymbol] = useState<Symbol>("BTCUSDT");
  const [range, setRange] = useState<Range>("7D");
  const [mode, setMode] = useState<"Candles" | "Line">("Candles");
  return (
    <section
      className="research-panel market-panel"
      aria-label="Binance market dashboard"
    >
      <div className="panel-heading">
        <div>
          <p className="eyebrow">The market, observed</p>
          <h2>Bitcoin & Ether</h2>
        </div>
        <div className="market-selector" role="group" aria-label="Market">
          {symbols.map((s) => (
            <button
              key={s}
              aria-pressed={s === symbol}
              onClick={() => setSymbol(s)}
            >
              {s === "BTCUSDT" ? "BTC" : "ETH"}
            </button>
          ))}
        </div>
      </div>
      <div className="chart-controls">
        <div className="market-selector" role="group" aria-label="Date range">
          {(Object.keys(ranges) as Range[]).map((r) => (
            <button
              key={r}
              aria-pressed={r === range}
              onClick={() => setRange(r)}
            >
              {r}
            </button>
          ))}
        </div>
        <div className="market-selector" role="group" aria-label="Chart view">
          {(["Candles", "Line"] as const).map((m) => (
            <button
              key={m}
              aria-pressed={m === mode}
              onClick={() => setMode(m)}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
      <MarketFeed
        key={`${symbol}/${range}`}
        symbol={symbol}
        range={range}
        mode={mode}
      />
    </section>
  );
}

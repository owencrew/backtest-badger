"use client";
import { useEffect, useRef, useState } from "react";
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  ColorType,
  type UTCTimestamp,
  type IChartApi,
  type Time,
} from "lightweight-charts";
import {
  ranges,
  windowFor,
  utc,
  type MarketSnapshot,
  type Candle,
} from "@/lib/market";
export const priceText = (n: number) =>
  n.toLocaleString("en-GB", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
export function MarketChart({
  data,
  mode,
}: {
  data: MarketSnapshot;
  mode: "Candles" | "Line";
}) {
  const element = useRef<HTMLDivElement>(null);
  const chartApi = useRef<IChartApi | null>(null);
  const visibleRange = useRef<{ from: Time; to: Time } | null>(null);
  const [selectedTime, setSelectedTime] = useState<number | null>(null);
  const selected =
    data.candles.find((c) => c.time === selectedTime) ?? data.candles.at(-1)!;
  useEffect(() => {
    if (!element.current) return;
    const chart = createChart(element.current, {
      autoSize: true,
      height: 430,
      layout: {
        background: { type: ColorType.Solid, color: "#1D2522" },
        textColor: "#AEB9B1",
        attributionLogo: true,
      },
      grid: {
        vertLines: { color: "#26312B" },
        horzLines: { color: "#37463E" },
      },
      localization: {
        locale: "en-GB",
        timeFormatter: (time: number) => utc(time * 1000),
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: "#37463E",
      },
      rightPriceScale: { borderColor: "#37463E" },
    });
    chartApi.current = chart;
    if (data.missing > 0) {
      const { start } = windowFor(data.range, data.serverTime);
      const { step } = ranges[data.range];
      const spacing = chart.addSeries(LineSeries, {
        lastValueVisible: false,
        priceLineVisible: false,
      });
      spacing.setData(
        Array.from(
          { length: Math.floor((data.serverTime - start) / step) + 1 },
          (_, i) => ({ time: ((start + i * step) / 1000) as UTCTimestamp }),
        ),
      );
    }
    // Separate contiguous runs prevent a line from drawing across missing observations.
    const segments: Candle[][] = [];
    for (const candle of data.candles) {
      const last = segments.at(-1);
      if (!last || candle.time - last.at(-1)!.time !== ranges[data.range].step)
        segments.push([candle]);
      else last.push(candle);
    }
    for (const segment of segments) {
      if (mode === "Candles") {
        const series = chart.addSeries(CandlestickSeries, {
          upColor: "#A9CFAE",
          downColor: "#E4A19A",
          wickUpColor: "#A9CFAE",
          wickDownColor: "#E4A19A",
          borderVisible: false,
          lastValueVisible: false,
          priceLineVisible: false,
        });
        series.setData(
          segment.map((c) => ({
            time: (c.time / 1000) as UTCTimestamp,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
            ...(c.complete ? {} : { color: "#D8C7A5", wickColor: "#D8C7A5" }),
          })),
        );
      } else {
        const series = chart.addSeries(LineSeries, {
          color: "#A9CFAE",
          lineWidth: 2,
          lastValueVisible: false,
          priceLineVisible: false,
          pointMarkersVisible: segment.length === 1,
        });
        series.setData(
          segment.map((c) => ({
            time: (c.time / 1000) as UTCTimestamp,
            value: c.close,
            ...(c.complete ? {} : { color: "#D8C7A5" }),
          })),
        );
      }
    }
    if (visibleRange.current)
      chart.timeScale().setVisibleRange(visibleRange.current);
    else chart.timeScale().fitContent();
    chart.subscribeCrosshairMove((event) => {
      if (typeof event.time === "number") setSelectedTime(event.time * 1000);
    });
    return () => {
      visibleRange.current = chart.timeScale().getVisibleRange();
      chartApi.current = null;
      chart.remove();
    };
  }, [data, mode]);
  return (
    <>
      <div className="candle-readout" aria-live="polite">
        <span>
          {utc(selected.time)} ·{" "}
          {selected.complete
            ? "Completed interval"
            : "Open candle · provisional"}
        </span>
        <span className="mono">
          O {priceText(selected.open)} · H {priceText(selected.high)} · L{" "}
          {priceText(selected.low)} · C {priceText(selected.close)} USDT
        </span>
      </div>
      <div
        ref={element}
        className="market-chart"
        role="img"
        aria-label={`${data.symbol} ${data.range} ${mode.toLowerCase()} chart. UTC candle opening times; use the observation slider below for keyboard access to exact values.`}
      />
      <div className="chart-access">
        <label>
          Inspect candle{" "}
          <input
            aria-label="Inspect candle"
            type="range"
            min={0}
            max={data.candles.length - 1}
            value={data.candles.indexOf(selected)}
            onChange={(event) =>
              setSelectedTime(data.candles[Number(event.target.value)].time)
            }
            aria-valuetext={`${utc(selected.time)}, close ${selected.close} USDT, ${selected.complete ? "complete" : "provisional"}`}
          />
        </label>
        <button
          className="button button-secondary"
          onClick={() => chartApi.current?.timeScale().fitContent()}
        >
          Reset view
        </button>
      </div>
      <p className="small muted">
        Drag to pan · Scroll or pinch to zoom · Crosshair values above · All
        times UTC, labelled by candle opening. Sand marks a potentially
        incomplete candle.
      </p>
      <p className="small muted">
        TradingView Lightweight Charts™ · Copyright (с) 2025 TradingView, Inc.{" "}
        <a className="text-link" href="https://www.tradingview.com/">
          TradingView
        </a>
        {" · "}
        <a href="/licenses/lightweight-charts-LICENSE.txt">
          Apache 2.0 licence
        </a>
      </p>
    </>
  );
}

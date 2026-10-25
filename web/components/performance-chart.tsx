"use client";
import { useId, useState } from "react";
import { type Market, number, percent } from "@/lib/research";

// A shared linear scale across every market. These are summary bars, not a time series.
const minimum = -80;
const maximum = 140;
const position = (value: number) =>
  ((value - minimum) / (maximum - minimum)) * 100;
export function PerformanceComparisonChart({
  markets,
  compact = false,
}: {
  markets: Market[];
  compact?: boolean;
}) {
  const id = useId();
  const [active, setActive] = useState<string | null>(null);
  return (
    <figure
      className={`performance-chart ${compact ? "compact-chart" : ""}`}
      aria-labelledby={`${id}-caption`}
    >
      <figcaption id={`${id}-caption`} className="chart-caption">
        <span>Cumulative return after costs</span>
        <span className="mono">2024 · %</span>
      </figcaption>
      <div className="chart-axis" aria-hidden="true">
        <div />{" "}
        <div className="axis-track">
          {[-60, 0, 60, 120].map((tick) => (
            <span key={tick} style={{ left: `${position(tick)}%` }}>
              {tick > 0 ? "+" : ""}
              {tick}%
            </span>
          ))}
        </div>
        <div />
      </div>
      {markets.map((market) => (
        <div className="chart-market" key={market.symbol}>
          <div className="chart-market-label">
            <strong>{market.name}</strong>
            <span className="mono">{market.symbol}</span>
          </div>
          {market.accounts.map((account) => {
            const value = Number(account.returnPct);
            const key = `${market.symbol}-${account.strategy}`;
            const tone =
              account.strategy === "Ridge"
                ? "ridge"
                : account.strategy === "Cash"
                  ? "cash"
                  : "hold";
            return (
              <div className="chart-row" key={key}>
                <span className="chart-series-label">
                  <i className={`legend-dot ${tone}`} />
                  {account.strategy}
                </span>
                <div className="bar-track">
                  {[-60, 0, 60, 120].map((tick) => (
                    <span
                      key={tick}
                      className={tick === 0 ? "gridline zero-line" : "gridline"}
                      style={{ left: `${position(tick)}%` }}
                      aria-hidden="true"
                    />
                  ))}
                  <button
                    className="bar-target"
                    aria-label={`${market.symbol}, ${account.strategy}: ${percent(value)} cumulative return; final value ${number(account.finalValue)} USDT. Historical simulation.`}
                    aria-describedby={
                      active === key ? `${id}-tooltip` : undefined
                    }
                    onMouseEnter={() => setActive(key)}
                    onMouseLeave={() => setActive(null)}
                    onFocus={() => setActive(key)}
                    onBlur={() => setActive(null)}
                    onKeyDown={(e) => {
                      if (e.key === "Escape") setActive(null);
                    }}
                    onClick={() => setActive(key)}
                  >
                    <span
                      className={`bar ${tone} ${value === 0 ? "zero-bar" : ""}`}
                      style={{
                        left: `${position(Math.min(0, value))}%`,
                        width:
                          value === 0
                            ? "3px"
                            : `${(Math.abs(value) / (maximum - minimum)) * 100}%`,
                      }}
                    />
                  </button>
                  {active === key && (
                    <div
                      id={`${id}-tooltip`}
                      role="tooltip"
                      className="chart-tooltip"
                    >
                      <strong>
                        {market.name} · {account.strategy}
                      </strong>
                      <span>{percent(value)} return</span>
                      <span>{number(account.finalValue)} USDT final value</span>
                      <small>Independent 10,000 USDT starting capital</small>
                    </div>
                  )}
                </div>
                <span
                  className={`chart-value mono ${value < 0 ? "negative" : value > 0 ? "positive" : ""}`}
                >
                  {percent(value)}
                </span>
              </div>
            );
          })}
        </div>
      ))}
      {!compact && (
        <p className="chart-help">
          Zero line = initial capital preserved. Hover, tap or focus a bar for
          account details. Escape closes the tooltip.
        </p>
      )}
    </figure>
  );
}

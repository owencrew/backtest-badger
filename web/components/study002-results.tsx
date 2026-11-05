"use client";
import { useState } from "react";
import {
  study002,
  studySymbols,
  strategyNames,
  studyNumber,
  studyPercent,
  returnTone,
  costBarWidth,
  type StudySymbol,
} from "@/lib/study002";

// All eight accounts are server-rendered and readable without JavaScript.
// Each section has its own optional market filter.
export function Study002Results({
  section,
}: {
  section: "overview" | "costs" | "monthly";
}) {
  const [selected, setSelected] = useState<StudySymbol | "all">("all");
  const symbols = selected === "all" ? studySymbols : [selected];
  return (
    <div className="study-results">
      <div
        className="market-selector"
        role="group"
        aria-label={`Filter ${section} by market`}
      >
        {(["all", ...studySymbols] as const).map((symbol) => (
          <button
            key={symbol}
            aria-pressed={selected === symbol}
            onClick={() => setSelected(symbol)}
          >
            {symbol === "all"
              ? "Both markets"
              : symbol === "BTCUSDT"
                ? "Bitcoin"
                : "Ether"}
          </button>
        ))}
      </div>
      <p className="small muted" aria-live="polite">
        {selected === "all" ? "Bitcoin and Ether" : selected} · Separate 10,000
        USDT accounts. Scroll tables horizontally on small screens.
      </p>
      {symbols.map((symbol) => {
        const accounts = study002.accounts.filter((a) => a.symbol === symbol);
        const trend = accounts[0];
        return (
          <div key={symbol}>
            {section === "overview" && (
              <>
                <div className="study-metrics">
                  <div>
                    <span>{symbol} · 30-Day Trend</span>
                    <strong>{studyPercent(trend.returnFraction)}</strong>
                    <span>Return after assumed costs</span>
                  </div>
                  <div>
                    <span>Final marked value</span>
                    <strong>{studyNumber(trend.finalEquity)}</strong>
                    <span>USDT · started with 10,000</span>
                  </div>
                  <div>
                    <span>Observed hourly drawdown</span>
                    <strong>
                      {studyPercent(trend.drawdownFraction, false)}
                    </strong>
                    <span>Largest decline from a previous peak</span>
                  </div>
                </div>
                <div
                  className="table-wrap"
                  tabIndex={0}
                  role="region"
                  aria-label={`${symbol} account results; scroll horizontally`}
                >
                  <table className="comparison-table">
                    <caption>{symbol} · Results after assumed costs</caption>
                    <thead>
                      <tr>
                        <th scope="col">Account</th>
                        <th scope="col">Return</th>
                        <th scope="col">
                          Final value
                          <br />
                          USDT
                        </th>
                        <th scope="col">
                          Max. hourly
                          <br />
                          drawdown
                        </th>
                        <th scope="col">
                          Executions
                          <br />
                          (buys / sells)
                        </th>
                        <th scope="col">
                          Costs
                          <br />
                          USDT
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {accounts.map((a) => (
                        <tr key={a.id}>
                          <th scope="row">{strategyNames[a.strategy]}</th>
                          <td className={returnTone(a.returnFraction)}>
                            {studyPercent(a.returnFraction)}
                          </td>
                          <td>{studyNumber(a.finalEquity)}</td>
                          <td>{studyPercent(a.drawdownFraction, false)}</td>
                          <td>
                            {a.buys + a.sells} ({a.buys} / {a.sells})
                          </td>
                          <td>{studyNumber(a.totalCosts)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            {section === "costs" && (
              <>
                <figure className="study-cost-bars">
                  <figcaption>
                    {symbol} · Attributed costs in USDT
                    <span className="small muted">
                      Shared linear scale · 0 to 10,000 USDT
                    </span>
                  </figcaption>
                  {accounts.map((a) => (
                    <div className="study-cost-row" key={a.id}>
                      <div>
                        <span>{strategyNames[a.strategy]}</span>
                        <strong className="mono">
                          {studyNumber(a.totalCosts)} USDT
                        </strong>
                      </div>
                      <div className="study-cost-track" aria-hidden="true">
                        <span
                          className={`study-cost-bar ${a.strategy}`}
                          style={{ width: `${costBarWidth(a.totalCosts)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </figure>
                <div
                  className="table-wrap"
                  tabIndex={0}
                  role="region"
                  aria-label={`${symbol} cost breakdown; scroll horizontally`}
                >
                  <table className="comparison-table">
                    <caption>{symbol} · Cost breakdown in USDT</caption>
                    <thead>
                      <tr>
                        <th scope="col">Account</th>
                        <th scope="col">Fees</th>
                        <th scope="col">
                          Assumed
                          <br />
                          half-spread
                        </th>
                        <th scope="col">
                          Assumed
                          <br />
                          slippage
                        </th>
                        <th scope="col">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {accounts.map((a) => (
                        <tr key={a.id}>
                          <th scope="row">{strategyNames[a.strategy]}</th>
                          <td>{studyNumber(a.fees)}</td>
                          <td>{studyNumber(a.halfSpread)}</td>
                          <td>{studyNumber(a.slippage)}</td>
                          <td>{studyNumber(a.totalCosts)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            {section === "monthly" && (
              <div
                className="table-wrap"
                tabIndex={0}
                role="region"
                aria-label={`${symbol} monthly returns; scroll horizontally`}
              >
                <table className="comparison-table">
                  <caption>{symbol} · Monthly mark-to-mark returns (%)</caption>
                  <thead>
                    <tr>
                      <th scope="col">Month</th>
                      {accounts.map((a) => (
                        <th scope="col" key={a.id}>
                          {strategyNames[a.strategy]}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {trend.monthly.map((month, i) => (
                      <tr key={month.month}>
                        <th scope="row">
                          {month.month}
                          {!month.complete && <span> (partial)</span>}
                        </th>
                        {accounts.map((a) => (
                          <td
                            key={a.id}
                            className={returnTone(a.monthly[i].returnFraction)}
                          >
                            {studyPercent(a.monthly[i].returnFraction)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

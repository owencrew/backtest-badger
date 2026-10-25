"use client";
import { useState } from "react";
import { markets, number, percent } from "@/lib/research";
import { PerformanceComparisonChart } from "./performance-chart";

export function DigExplorer() {
  const [selected, setSelected] = useState("all");
  const visible =
    selected === "all" ? markets : markets.filter((m) => m.symbol === selected);
  return (
    <>
      <section className="research-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">The benchmark test</p>
            <h2>Did the strategy earn its keep?</h2>
          </div>
          <div
            className="market-selector"
            role="group"
            aria-label="Filter results by market"
          >
            {[{ symbol: "all", name: "Both markets" }, ...markets].map((m) => (
              <button
                key={m.symbol}
                aria-pressed={selected === m.symbol}
                onClick={() => setSelected(m.symbol)}
              >
                {m.name}
              </button>
            ))}
          </div>
        </div>
        <PerformanceComparisonChart markets={visible} />
        <p className="panel-footnote" aria-live="polite">
          {selected === "all" ? "Both markets" : visible[0].name} · Separate
          10,000 USDT accounts · No leverage or short selling
        </p>
      </section>
      <section className="section-block">
        <div className="section-heading">
          <h2>Inside the accounts</h2>
          <span className="small muted">
            All values include the frozen cost assumptions
          </span>
        </div>
        <p className="small muted">
          On smaller screens, scroll each table horizontally to see all account
          metrics.
        </p>
        {visible.map((market) => (
          <div
            className="table-wrap"
            key={market.symbol}
            tabIndex={0}
            role="region"
            aria-label={`${market.name} account comparison; scroll horizontally on small screens`}
          >
            <table className="comparison-table">
              <caption>
                {market.name}{" "}
                <span className="mono muted">/ {market.symbol}</span>
              </caption>
              <thead>
                <tr>
                  <th scope="col">Account</th>
                  <th scope="col">Return</th>
                  <th scope="col">
                    Final value
                    <br />
                    <small>USDT</small>
                  </th>
                  <th scope="col">
                    Max. drawdown
                    <br />
                    <small>Hourly marks</small>
                  </th>
                  <th scope="col">Buys / sells</th>
                  <th scope="col">
                    Turnover
                    <br />
                    <small>× initial funding</small>
                  </th>
                  <th scope="col">
                    Attributed costs
                    <br />
                    <small>USDT</small>
                  </th>
                </tr>
              </thead>
              <tbody>
                {market.accounts.map((account) => (
                  <tr key={account.strategy}>
                    <th scope="row">{account.strategy}</th>
                    <td
                      className={
                        Number(account.returnPct) < 0
                          ? "negative"
                          : Number(account.returnPct) > 0
                            ? "positive"
                            : ""
                      }
                    >
                      {percent(account.returnPct)}
                    </td>
                    <td>{number(account.finalValue)}</td>
                    <td>{number(account.drawdownPct)}%</td>
                    <td>
                      {account.buys} / {account.sells}
                    </td>
                    <td>{number(account.turnover)}×</td>
                    <td>{number(account.costs)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
        <p className="small muted">
          Drawdown is the largest decline from a previous peak at observed
          hourly marks, including initial funding. Intraminute losses are
          unobserved. Turnover sums buy and sell notionals divided by initial
          funding; it is not halved.
        </p>
      </section>
    </>
  );
}

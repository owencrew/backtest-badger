import { reportUrl } from "@/lib/research";
export function RidgeExplainer() {
  return (
    <section
      className="section-block ridge-explainer"
      aria-labelledby="ridge-title"
    >
      <p className="eyebrow">Meet the model</p>
      <h2 id="ridge-title">What is Ridge actually predicting?</h2>
      <div className="ridge-intro">
        <p>
          Ridge regression is a linear model: it adds up weighted features to
          estimate a number. It penalises large squared weights, helping
          stabilise estimates when inputs overlap. The name comes from earlier
          “ridge analysis”, which traced paths of optimal values across a curved
          response surface. Applying that method to regression errors led to
          Ridge regression. It is a mathematical method, not a trading strategy
          by itself.{" "}
          <a
            className="text-link"
            href="https://doi.org/10.1080/00401706.2020.1742207"
          >
            History of the name ↗
          </a>
        </p>
        <p>
          Here, a separate model for each market predicts{" "}
          <strong>the next four-hour close-to-close log return</strong>: ln(next
          close / current close). Scaling and model weights were fitted on
          pre-2024 training data only, with a fixed penalty of 1. The historical
          run reused those retained forecasts; it did not refit the model.
        </p>
      </div>
      <h3>Five inputs, all from completed market candles</h3>
      <dl className="feature-grid">
        <div>
          <dt>4-hour return</dt>
          <dd>ln(C[t] / C[t−1]): the latest four-hour price change.</dd>
        </div>
        <div>
          <dt>12-hour return</dt>
          <dd>ln(C[t] / C[t−3]): the change over three candles.</dd>
        </div>
        <div>
          <dt>24-hour return</dt>
          <dd>ln(C[t] / C[t−6]): the change over six candles.</dd>
        </div>
        <div>
          <dt>24-hour realised volatility</dt>
          <dd>
            Square root of the sum of the last six squared four-hour log
            returns. A measure of recent movement, not an annualised figure.
          </dd>
        </div>
        <div>
          <dt>Relative base volume</dt>
          <dd>
            Current four-hour BTC or ETH volume divided by the mean of the
            preceding six candles’ volumes. The current candle is excluded from
            that mean.
          </dd>
        </div>
      </dl>
      <p className="small muted">
        C[t] means the source candle’s close. These inputs require seven
        consecutive four-hour candles; missing prices are not filled in.
      </p>
      <h3>From a forecast to a hypothetical fill</h3>
      <ol className="decision-flow" aria-label="Historical Ridge decision flow">
        <li>
          <span>01 · Observe</span>
          <strong>Candle closes at 12:00 UTC</strong>
          <p>Completed-candle boundary, not an issuance timestamp.</p>
        </li>
        <li>
          <span>02 · Wait</span>
          <strong>Assumed available at 12:01</strong>
          <p>
            Source opening + 4 hours + 60 seconds; historical latency
            assumption.
          </p>
        </li>
        <li>
          <span>03 · Decide</span>
          <strong>
            Forecast &gt; 1e-12 → long
            <br />
            Otherwise → cash
          </strong>
          <p>The frozen sign threshold is unchanged. No short selling.</p>
        </li>
        <li>
          <span>04 · Execute</span>
          <strong>Strictly next minute: 12:02</strong>
          <p>
            Hypothetical native-minute opening with fees, spread and slippage.
          </p>
        </li>
      </ol>
      <div className="overview-grid">
        <div className="overview-card">
          <h3>Ridge</h3>
          <p>
            Holds its long or cash position until the target changes. Continuous
            holding avoids a compulsory exit every four hours, but a fluctuating
            forecast can still cause frequent switches and high turnover.
          </p>
        </div>
        <div className="overview-card">
          <h3>Cash</h3>
          <p>
            An independent 10,000 USDT account that makes no trades and earns no
            interest. Its flat return is a benchmark, not a forecast.
          </p>
        </div>
        <div className="overview-card">
          <h3>Buy &amp; Hold</h3>
          <p>
            Buys once at the start of 2024 and holds. Entry costs apply; unsold
            assets remain marked at the final observation, with no invented
            liquidation fee.
          </p>
        </div>
      </div>
      <p>
        Timing changes the price at which a decision can be acted on. Every buy
        and sell assumes 10 basis points of fees, 1 basis point of half-spread
        and 2 basis points of adverse slippage. Repeated switches accumulate
        costs. Continuous holdings therefore do not guarantee low turnover.
      </p>
      <p>
        This result tests one fixed model and decision rule on one previously
        inspected year in two correlated markets, under assumed execution costs.
        Its losses are evidence against this particular implementation under
        these conditions; they do not establish that all predictive trading
        fails.
      </p>
      <a href={reportUrl} className="text-link">
        Read the authoritative E.5g report ↗
      </a>
      <details className="glossary">
        <summary>A short research glossary</summary>
        <dl>
          <dt>Drawdown</dt>
          <dd>
            The decline from a previous account-value peak. Here the maximum
            uses observed hourly marks, so intraminute losses are unobserved.
          </dd>
          <dt>Turnover</dt>
          <dd>
            Total buy and sell notionals divided by initial funding. Both sides
            count; the total is not halved.
          </dd>
          <dt>Basis point (bp)</dt>
          <dd>
            One hundredth of a percentage point: 1 bp = 0.01%; 10 bps = 0.10%.
          </dd>
          <dt>Slippage</dt>
          <dd>
            A worse fill price than the reference price. Here it is a frozen
            assumption, not measured historical execution.
          </dd>
          <dt>Sharpe ratio</dt>
          <dd>
            Mean excess return divided by its standard deviation, with a stated
            sampling period and annualisation convention. It is sensitive to
            those choices and does not prove an edge; no Sharpe figure is
            inferred here.
          </dd>
        </dl>
      </details>
    </section>
  );
}

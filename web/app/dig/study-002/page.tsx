import Link from "next/link";
import Image from "next/image";
import { pageMetadata } from "@/lib/seo";
import { Disclaimer, Status } from "@/components/ui";
import { Study002Results } from "@/components/study002-results";
import {
  study002,
  studyReportUrl,
  studyMethodUrl,
  studySourceRoot,
  strategyNames,
  studyNumber,
} from "@/lib/study002";

export const metadata = pageMetadata(
  "Can a Slower Trend Beat the Noise? — Study 002",
  "A verified 2024 daily 30-day trend simulation: about 95% lower costs than Ridge, positive returns, mixed drawdowns and a shortfall against Buy & Hold.",
  "/dig/study-002/",
);

function ResearchFigure({
  name,
  title,
  description,
}: {
  name: "equity" | "drawdown" | "exposure";
  title: string;
  description: string;
}) {
  return (
    <figure className="study-figure">
      <figcaption>
        <strong>{title}</strong>
        <p>{description}</p>
      </figcaption>
      <p className="small muted">
        Both markets · 2024 · UTC. On small screens, scroll the figure
        horizontally to read every label.
      </p>
      <div
        className="study-figure-scroll"
        tabIndex={0}
        role="region"
        aria-label={`${title}; scroll horizontally on small screens`}
      >
        {/* Display only the original plotting area. The source PNG is byte-identical;
          original review masthead/footer are replaced by accessible HTML context. */}
        <div className="study-figure-window">
          <Image
            src={`/research/study-002/${name}.png`}
            width={1800}
            height={1200}
            alt={description}
          />
        </div>
      </div>
      <p className="source-note">
        Retained hourly research figure · Final mark 31 December 2024, 23:00
        UTC.{" "}
        <a href={`${studySourceRoot}/study-002-assets/${name}.png`}>
          Inspect the original source figure
        </a>
        .
      </p>
    </figure>
  );
}

export default function Study002() {
  return (
    <article className="study002">
      <header className="page-intro study-intro">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Home</Link>
          <span>/</span>
          <Link href="/dig/">The Dig</Link>
          <span>/</span>
          <span aria-current="page">Study 002</span>
        </nav>
        <Status>Study 002 · Historical simulation</Status>
        <h1>
          Can a Slower Trend
          <br />
          Beat the Noise?
        </h1>
        <p className="lede">
          Our first study found that frequent trading was expensive. This time,
          we tested a simpler idea: follow the direction of the past 30 days,
          make one decision each day, and see what remains after trading costs.
        </p>
        <p className="study-byline">
          Binance Spot · BTCUSDT / ETHUSDT · Research run{" "}
          <time dateTime="2026-11-01">1 November 2026</time>
          <br />
          <a className="text-link" href={studyMethodUrl}>
            Read the full methodology
          </a>{" "}
          ·{" "}
          <Link className="text-link" href="/dig/#study-001">
            Compare with Study 001
          </Link>
        </p>
      </header>
      <aside className="study-verdict">
        <p className="eyebrow">The finding</p>
        <h2>
          A slower rule cut the trading bill.
          <br />
          It still missed much of the market’s gain.
        </h2>
        <p>
          Both markets beat Ridge and Cash after assumed costs. Both lagged Buy
          &amp; Hold. Bitcoin Trend also had a larger observed hourly drawdown
          than Bitcoin Buy &amp; Hold.
        </p>
        <p className="small">
          Exploratory retrospective simulation on one previously examined year.
          Not live trading, an untouched out-of-sample evaluation or evidence of
          durable profitability.
        </p>
      </aside>
      <nav className="study-contents" aria-label="Study sections">
        <a href="#rule">The rule</a>
        <a href="#results">Results</a>
        <a href="#equity">Equity</a>
        <a href="#risk">Risk</a>
        <a href="#exposure">Exposure</a>
        <a href="#costs">Costs</a>
        <a href="#monthly">Monthly returns</a>
        <a href="#methodology">Evidence</a>
      </nav>

      <section className="section-block" id="rule">
        <p className="eyebrow">01 / The fixed rule</p>
        <h2>One daily decision. Long or cash.</h2>
        <p className="study-section-lede">
          Exactly 30 calendar days. Positive trend means long; zero or negative
          trend means cash. Holdings continue between decisions.
        </p>
        <ol className="study-timeline">
          <li>
            <span className="mono">00:00 UTC</span>
            <h3>Observe completed prices</h3>
            <p>
              Compare the latest completed native four-hour candle close with
              the close exactly 30 days earlier.
            </p>
          </li>
          <li>
            <span className="mono">00:01 UTC</span>
            <h3>Set the target</h3>
            <p>
              If the latest price is higher, target long. Otherwise, target
              cash. Make this decision once a day.
            </p>
          </li>
          <li>
            <span className="mono">00:02 UTC</span>
            <h3>Trade only if needed</h3>
            <p>
              A changed position executes hypothetically at the strictly next
              native one-minute opening. Otherwise, keep holding.
            </p>
          </li>
        </ol>
        <p className="small muted">
          Each market has a separate 10,000 USDT account. No leverage, short
          selling, stop-loss, alternative thresholds or optimisation. Each side
          assumes a 10 bps fee, 1 bp half-spread and 2 bps adverse slippage.
          These are historical execution references, not actual exchange fills.
        </p>
      </section>

      <section className="section-block" id="results">
        <p className="eyebrow">02 / Results at a glance</p>
        <h2>Positive returns. A demanding benchmark.</h2>
        <p className="study-section-lede">
          Funding-relative returns include assumed transaction costs. All eight
          accounts are independent; Bitcoin and Ether are never pooled.
        </p>
        <Study002Results section="overview" />
        <p className="source-note">
          Display values rounded from{" "}
          <a href={studyReportUrl}>
            the verified report and its exact source-linked review data
          </a>
          . Final valuation: 31 December 2024, 23:00 UTC; the last day and month
          are partial. Buy &amp; Hold retains unsold assets with no terminal
          sale cost.
        </p>
      </section>

      <section className="section-block" id="equity">
        <p className="eyebrow">03 / Portfolio performance</p>
        <h2>The path matters as much as the finish.</h2>
        <ResearchFigure
          name="equity"
          title="Portfolio equity after assumed costs · USDT"
          description="Bitcoin and Ether shown separately, with 30-Day Trend, Ridge Sign, Cash and Buy & Hold. Trend finishes above its 10,000 USDT funding in both markets, below Buy & Hold; Ridge finishes below Cash."
        />
      </section>

      <section className="section-block" id="risk">
        <p className="eyebrow">04 / Risk and drawdown</p>
        <h2>A positive year can still hurt.</h2>
        <p className="study-section-lede">
          Bitcoin Trend’s 37.88% maximum observed hourly drawdown exceeded Buy
          &amp; Hold’s 32.31%. Ether Trend’s 34.67% was lower than Buy &amp;
          Hold’s 46.66%. Both improved on Ridge’s roughly 65%, but the result
          was mixed.
        </p>
        <ResearchFigure
          name="drawdown"
          title="Drawdown from funding or observed hourly peaks · %"
          description="Declines below prior observed peaks for all four accounts in each market. Bitcoin Trend falls further from its peak than Buy & Hold; Ether Trend falls less. Cash stays at zero."
        />
        <p className="small muted">
          Drawdown includes initial funding and hourly marks. Losses between
          observations are unobserved; this is not an intraminute worst-case
          measure. The exact comparison is in the results table above.
        </p>
      </section>

      <section className="section-block" id="exposure">
        <p className="eyebrow">05 / Exposure and trading behaviour</p>
        <h2>Less trading. More time invested than Ridge.</h2>
        <p className="study-section-lede">
          Trend held Bitcoin for 235 days and Ether for 190 days. Ridge was
          invested for fewer days in both markets; Buy &amp; Hold remained
          invested. These different exposures materially affect gains and
          losses.
        </p>
        <ResearchFigure
          name="exposure"
          title="30-Day Trend position at hourly marks · Long / Cash"
          description="The verified long/cash history for Bitcoin and Ether. Bitcoin Trend spent more time invested than Ether Trend; both alternate between continuous holdings and periods in cash."
        />
        <div
          className="table-wrap"
          tabIndex={0}
          role="region"
          aria-label="Exposure comparison; scroll horizontally"
        >
          <table className="comparison-table">
            <caption>Time invested · Actual hypothetical fill times</caption>
            <thead>
              <tr>
                <th scope="col">Market</th>
                <th scope="col">Account</th>
                <th scope="col">Invested days</th>
                <th scope="col">Cash days</th>
                <th scope="col">Executions</th>
              </tr>
            </thead>
            <tbody>
              {study002.accounts.map((a) => (
                <tr key={a.id}>
                  <th scope="row">{a.symbol}</th>
                  <td>{strategyNames[a.strategy]}</td>
                  <td>
                    {studyNumber(String(a.exposureSeconds), 2, 1n, 86400n)}
                  </td>
                  <td>
                    {studyNumber(
                      String(31622400 - a.exposureSeconds),
                      2,
                      1n,
                      86400n,
                    )}
                  </td>
                  <td>{a.buys + a.sells}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="small muted">
          Duration extends to 1 January 2025 only as a time boundary for open
          holdings; it is not a new price or valuation. Duration and the sampled
          hourly positions above are distinct measures. Both Trend accounts
          ended in cash through their own signals.
        </p>
      </section>

      <section className="section-block" id="costs">
        <p className="eyebrow">06 / The trading bill</p>
        <h2>About 95% lower costs than Ridge.</h2>
        <p className="study-section-lede">
          Trend made 38 Bitcoin executions and 32 Ether executions, compared
          with Ridge’s 1,140 and 998. Attributed costs fell by 94.5% and 95.4%,
          respectively.
        </p>
        <Study002Results section="costs" />
        <aside className="study-note">
          <strong>
            Trading less reduced costs substantially, but did not outperform the
            simpler Buy &amp; Hold benchmark.
          </strong>
          <p>
            Half-spread and slippage are already embedded in execution prices,
            not charged again as cash fees. Adding attributed costs back to
            final equity would not reconstruct a frictionless portfolio:
            quantities and the subsequent capital path would change. Rounded
            cost components may not sum exactly to the rounded total.
          </p>
        </aside>
      </section>

      <section className="section-block" id="monthly">
        <p className="eyebrow">07 / Every month, including the losses</p>
        <h2>The annual result hides rough stretches.</h2>
        <p className="study-section-lede">
          Bitcoin Trend had five positive and seven negative months. Ether had
          four positive, seven negative and one flat month. December is partial
          through 31 December at 23:00 UTC.
        </p>
        <Study002Results section="monthly" />
        <p className="small muted">
          These are mark-to-mark returns. Buy &amp; Hold’s January opening mark
          already includes its inception costs, so chaining monthly returns
          differs from its funding-relative annual return. Cash returns are zero
          in every month.
        </p>
      </section>

      <section className="finding-panel" id="findings">
        <p className="eyebrow">08 / What the results tell us</p>
        <h2>
          A smaller bill.
          <br />
          Still a costly lag.
        </h2>
        <div>
          <p>
            The fixed daily rule generated far fewer trades, paid substantially
            less and finished with positive returns. It still significantly
            underperformed Buy &amp; Hold in both markets, and the drawdown
            comparison was mixed.
          </p>
          <p>
            Bitcoin Trend lost 19.55% in August, versus Ridge’s 7.84% loss and
            Buy &amp; Hold’s 8.75% loss. It held through the 5 August daily
            decision, sold on the 6th, bought on the 7th, sold on the 8th and
            bought again on the 9th, each hypothetically at 00:02 UTC.
          </p>
          <p>
            On 8 August, Buy &amp; Hold gained 11.88%; Trend returned −0.05%. A
            slower signal can still exit before a rebound and cross its
            threshold on consecutive days.
          </p>
          <p>
            <strong>
              Lower turnover cannot be isolated as the cause of improved
              returns.
            </strong>{" "}
            The signal, time invested and trade prices all changed. These are
            descriptive observations, not tests of a better lookback.
          </p>
        </div>
      </section>

      <section className="section-block methodology-grid" id="methodology">
        <div>
          <p className="eyebrow">09 / Methodology and evidence</p>
          <h2>The assumptions are part of the result.</h2>
          <p>
            One genuine historical run. Six newly funded accounts independently
            verified. Two preserved Ridge references.
          </p>
          <p>
            <a className="text-link" href={studyReportUrl}>
              Full research report
            </a>
            <br />
            <a className="text-link" href={studyMethodUrl}>
              Frozen methodology
            </a>
            <br />
            <a
              className="text-link"
              href={`${studySourceRoot}/study-002-config.json`}
            >
              Frozen configuration
            </a>
            <br />
            <a
              className="text-link"
              href={`${studySourceRoot}/study-002-freeze.json`}
            >
              Pre-run freeze record
            </a>
          </p>
        </div>
        <div className="methodology-details">
          <details open>
            <summary>What data was used, and what is missing?</summary>
            <p>
              Native Binance Spot four-hour candles supply the daily trend. The
              pinned source export is globally incomplete, but every one of the
              2,371 required four-hour candles per market was present in the
              contiguous study and warm-up interval. No missing observation was
              repaired. The existing authenticated native-minute publication
              supplies execution openings and 8,784 hourly marks per account.
            </p>
            <p>
              Historical archives can reflect provider revisions. Retained
              authentication does not establish contemporaneous exchange
              availability. No measured latency, historical order book,
              quantity-specific liquidity, market impact or proof of fillability
              is available.
            </p>
          </details>
          <details>
            <summary>When was the rule frozen?</summary>
            <p>
              The methodology, configuration and implementation were frozen at
              21:09:59 UTC on 1 November 2026, before the single genuine run.
              The fixed rule uses exactly 30 calendar days and 366 once-daily
              decisions. The freeze predates this run; it does not mean the rule
              was chosen before 2024 history was known.
            </p>
          </details>
          <details>
            <summary>How are execution and accounting handled?</summary>
            <p>
              Assumed availability is midnight plus 60 seconds. A changed target
              uses the strictly next native-minute opening at 00:02. Buy and
              sell references are adjusted by ×1.0003 and ×0.9997; a 10 bps fee
              on adjusted notional is rounded upward to 0.00000001 USDT.
              Quantity steps are 0.000001 base units.
            </p>
            <p>
              Exact Decimal accounting records paired ledger postings, fee-aware
              affordable quantities, holdings and hourly valuations. All six new
              portfolios passed both the existing ledger verifier and
              independent serialized posting/mark reconciliation. No economic
              backtest was rerun to publish this page.
            </p>
          </details>
          <details>
            <summary>How are the benchmarks constructed?</summary>
            <p>
              Each account starts independently with 10,000 USDT. Cash earns no
              interest. Buy &amp; Hold buys once at 1 January 2024 00:00, two
              minutes before the first eligible Trend fill, and retains its
              assets. The new Cash and Buy &amp; Hold metrics equal the original
              benchmarks. Ridge Sign is the unchanged historical Study 001
              reference; no model refit or forecast regeneration occurred.
            </p>
          </details>
          <details>
            <summary>How are risk and period boundaries defined?</summary>
            <p>
              Final observation: 31 December 2024 at 23:00 UTC. The final day
              and month are partial; no 2025 price or terminal sale is invented.
              Drawdown is the largest decline from initial funding or an
              observed hourly equity peak. Complete-day statistics exclude the
              final 23-hour day.
            </p>
            <p>
              The zero-rate daily Sharpe uses the arithmetic mean and sample
              standard deviation of 365 complete daily mark returns, scaled by
              √365. It is descriptive; Cash’s zero variance makes its Sharpe
              undefined, not zero.
            </p>
            <div
              className="table-wrap"
              tabIndex={0}
              role="region"
              aria-label="Descriptive Sharpe values; scroll horizontally"
            >
              <table>
                <caption>Zero-rate daily Sharpe · Descriptive only</caption>
                <thead>
                  <tr>
                    <th scope="col">Market / account</th>
                    <th scope="col">Sharpe</th>
                  </tr>
                </thead>
                <tbody>
                  {study002.accounts.map((a) => (
                    <tr key={a.id}>
                      <th scope="row">
                        {a.symbol} / {strategyNames[a.strategy]}
                      </th>
                      <td>
                        {a.sharpe.value === null
                          ? "Undefined (zero variance)"
                          : studyNumber(a.sharpe.value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
          <details open>
            <summary>What can this study not establish?</summary>
            <p>
              2024 had already been inspected. This is exploratory retrospective
              research, not a clean untouched out-of-sample test, live
              performance or prospective paper trading. One year and two
              correlated markets do not establish durable profitability.
              Different signals and exposure prevent a causal frequency-only
              comparison. No optimisation or alternative strategy sweep was
              performed.
            </p>
          </details>
          <details>
            <summary>Trace the displayed values and chart identities</summary>
            <p>
              All source links use immutable research revision{" "}
              <code>{study002.sourceRevision}</code>. The narrow website data
              selection retains the original Decimal strings; displayed values
              are rounded. The three hourly figures preserve the original PNG
              bytes and plot areas; accessible HTML supplies the page’s titles
              and provenance in place of the original review masthead.
            </p>
            <p>
              <a
                className="text-link"
                href={`${studySourceRoot}/study-002-assets/review-data.json`}
              >
                Exact source-linked review data
              </a>
              <br />
              <a
                className="text-link"
                href={`${studySourceRoot}/study-002-assets/manifest.json`}
              >
                Original asset manifest
              </a>
            </p>
            <dl className="study-hashes">
              {Object.entries(study002.sourceHashes).map(([file, hash]) => (
                <div key={file}>
                  <dt>{file}</dt>
                  <dd>
                    <code>{hash}</code>
                  </dd>
                </div>
              ))}
            </dl>
          </details>
        </div>
      </section>
      <Disclaimer />
      <p className="study-back">
        <Link className="text-link" href="/dig/">
          Back to The Dig research library
        </Link>
      </p>
    </article>
  );
}

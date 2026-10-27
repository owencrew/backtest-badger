import { pageMetadata } from "@/lib/seo";
import Link from "next/link";
import { PageIntro, Arrow, Disclaimer, SourceNote } from "@/components/ui";
import { BadgerTrail } from "@/components/badger-trail";
import { repository } from "@/lib/research";
export const metadata = pageMetadata(
  "About — Methodology & principles",
  "How Backtest Badger studies markets: causal features, chronological evaluation, reproducible evidence and honest limits on historical and prospective results.",
  "/about/",
);
export default function About() {
  return (
    <>
      <PageIntro
        section="About & Methodology"
        title="Curiosity, with a paper trail."
      >
        Backtest Badger is an open-source quantitative research project by Owen
        Crew. It brings market-data engineering, machine learning and
        backtesting into one inspectable body of work.
      </PageIntro>
      <section className="about-statement">
        <p className="eyebrow">Our working principle</p>
        <h2>
          Profitability is a question.
          <br />
          <span>Not an assumption.</span>
        </h2>
        <p>
          A losing strategy can be a useful result. The aim is to build reliable
          software, ask careful questions and make the answers
          understandable—from the source data to the last simulated transaction.
        </p>
        <a className="button button-secondary" href={repository}>
          Explore the source on GitHub <Arrow />
        </a>
      </section>
      <section className="section-block">
        <h2>What makes the research inspectable?</h2>
        <div className="principles-grid">
          {[
            [
              "01",
              "Keep the evidence",
              "Retained source identities, versioned data and reproducible model recipes make inputs and changes traceable. A checksum identifies bytes; it does not establish economic truth.",
            ],
            [
              "02",
              "Respect the clock",
              "Causal features use eligible information. Training, validation and testing are chronological; preprocessing is fitted on training data only.",
            ],
            [
              "03",
              "Make execution explicit",
              "Signals precede hypothetical fills. Timing, fees, spread, slippage and independent account funding are disclosed alongside the results.",
            ],
            [
              "04",
              "Keep the negative findings",
              "Benchmarks and ledger checks remain visible when a strategy loses. Previously inspected history is labelled exploratory, not untouched out-of-sample evidence.",
            ],
          ].map(([n, title, copy]) => (
            <div key={n}>
              <span className="step-number mono">{n}</span>
              <h3>{title}</h3>
              <p>{copy}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="section-block">
        <h2>Four kinds of evidence. Four different meanings.</h2>
        <div className="evidence-list">
          {[
            [
              "Historical backtests",
              "Implemented",
              "Simulated decisions on past observations. The 2024 study is exploratory and includes assumed transaction costs.",
            ],
            [
              "Forward forecasts",
              "Implemented; public snapshot pending",
              "Timestamped predictions recorded before outcomes, then scored. Forecast accuracy is not a trading return.",
            ],
            [
              "Prospective paper trading",
              "Planned",
              "Future simulated orders, fills and portfolios as new evidence arrives. Accounting foundations exist; the complete service does not.",
            ],
            [
              "Real-money trading",
              "Not implemented",
              "Actual orders and capital at risk. No real trading results are presented on this website.",
            ],
          ].map(([title, status, copy]) => (
            <div key={title}>
              <div>
                <h3>{title}</h3>
                <span className="topic-status">{status}</span>
              </div>
              <p>{copy}</p>
            </div>
          ))}
        </div>
      </section>
      <SourceNote />
      <Disclaimer />
      <section className="section-block">
        <BadgerTrail />
      </section>
      <div className="article-end">
        <Link href="/dig/" className="text-link">
          Examine the historical evidence <Arrow />
        </Link>
        <Link href="/field-notes/" className="text-link">
          Read the research journal <Arrow />
        </Link>
      </div>
    </>
  );
}

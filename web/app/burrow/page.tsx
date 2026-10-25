import Link from "next/link";
import type { Metadata } from "next";
import { PageIntro, Status, EmptyState, Arrow } from "@/components/ui";
export const metadata: Metadata = { title: "The Burrow — Forward research" };
export default function Burrow() {
  return (
    <>
      <PageIntro section="The Burrow" title="A window into forward research.">
        Forecasts are recorded before their outcomes arrive. This is where we’ll
        examine what those predictions get right, what they miss and how much
        evidence we have.
      </PageIntro>
      <div className="preview-notice">
        <strong>Dashboard design preview</strong>
        <span>
          No approved public statistics export is connected. This page is not
          live. Structure reviewed as of 25 Oct 2026; no current system status
          is asserted.
        </span>
      </div>
      <section className="section-block">
        <div className="section-heading">
          <h2>The research landscape</h2>
          <Status muted>Awaiting reviewed snapshot</Status>
        </div>
        <div className="overview-grid">
          <div className="overview-card">
            <p className="eyebrow">Market coverage</p>
            <h3>Bitcoin & Ether</h3>
            <p className="mono">BTCUSDT / ETHUSDT</p>
            <p>Binance Spot. Native four-hour observations.</p>
          </div>
          <div className="overview-card">
            <p className="eyebrow">Predictive research</p>
            <h3>Fixed model recipes</h3>
            <p>
              Ridge, shallow boosting and no-skill reference forecasts. No
              current model ranking is published here.
            </p>
          </div>
          <div className="overview-card">
            <p className="eyebrow">Evidence type</p>
            <h3>Forecasts, then outcomes</h3>
            <p>
              Prediction errors describe forecasting accuracy. They are not
              portfolio or trading returns.
            </p>
          </div>
        </div>
      </section>
      <section className="section-block">
        <div className="section-heading">
          <h2>Forward forecast activity</h2>
          <Link href="/about/" className="text-link">
            How evidence is evaluated <Arrow />
          </Link>
        </div>
        <div className="metric-grid">
          {[
            ["Issued forecasts", "Timestamped predictions"],
            ["Scored observations", "Matched realised outcomes"],
            ["Pending observations", "Outcomes not yet available"],
            ["Forecast accuracy", "Errors on matched cohorts"],
          ].map(([title, desc]) => (
            <div className="metric-card" key={title}>
              <span>{title}</span>
              <strong className="metric-empty">Not published</strong>
              <p>{desc}</p>
            </div>
          ))}
        </div>
        <p className="small muted">
          Unavailable is not zero. Counts, error metrics and sample sizes will
          appear together after export review.
        </p>
      </section>
      <div className="burrow-panels">
        <section className="research-panel">
          <div className="panel-heading">
            <h2>Timely and late cohorts</h2>
          </div>
          <EmptyState title="Different timing. Separate evidence.">
            Timely automated and late manual observations must be reported
            separately, with matched sample counts, missing outcomes and
            preliminary-sample warnings.
          </EmptyState>
          <div className="cohort-labels">
            <span>Timely cohort · Not published</span>
            <span>Late cohort · Not published</span>
          </div>
        </section>
        <section className="research-panel">
          <div className="panel-heading">
            <h2>Research-system activity</h2>
          </div>
          <EmptyState title="Waiting for a dated activity export">
            A future reviewed snapshot can show issuance and scoring events with
            their actual timestamps. There is no live feed or synthetic activity
            log in this prototype.
          </EmptyState>
        </section>
      </div>
      <section className="guide-band">
        <div>
          <p className="eyebrow">Different questions, different evidence</p>
          <h2>
            Looking for
            <br />
            historical returns?
          </h2>
        </div>
        <div>
          <p>
            The 2024 strategy comparison is ready to explore in The Dig.
            Prospective paper portfolios are planned; real-money trading is not
            implemented.
          </p>
          <Link className="text-link" href="/dig/">
            Explore the historical study <Arrow />
          </Link>
        </div>
      </section>
    </>
  );
}

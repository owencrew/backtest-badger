import { pageMetadata } from "@/lib/seo";
import Link from "next/link";
import { RidgeExplainer } from "@/components/ridge-explainer";
import { DigExplorer } from "@/components/dig-explorer";
import {
  PageIntro,
  Status,
  Disclaimer,
  SourceNote,
  Arrow,
} from "@/components/ui";
import { readArticles } from "@/lib/content";
import { ArticleCard } from "@/components/editorial";
export const metadata = pageMetadata(
  "The Dig — Historical research",
  "Explore the 2024 Ridge crypto spot backtest against Cash and Buy & Hold, with independent accounts, explicit trading costs and research limitations.",
  "/dig/",
);
export default function Dig() {
  const notes = readArticles("fieldNotes")
    .filter((a) => /^(003|004)/.test(a.slug))
    .reverse();
  return (
    <>
      <PageIntro section="The Dig" title="Put the strategy to the test.">
        A good backtest doesn’t promise a winning strategy. It gives you a
        clearer view of the evidence, the costs and the alternatives.
      </PageIntro>
      <div className="study-header">
        <div>
          <Status>Historical simulation</Status>
          <h2>The 2024 Ridge sign study</h2>
          <p>
            Binance Spot · Native-minute execution · Continuous long / cash
            holdings
          </p>
        </div>
        <div className="study-stamp">
          <span className="eyebrow">Evidence recorded</span>
          <time dateTime="2026-10-24">24 OCT 2026</time>
        </div>
      </div>
      <DigExplorer />
      <SourceNote />
      <RidgeExplainer />
      <section className="finding-panel">
        <p className="eyebrow">What we learned</p>
        <h2>
          Frequent changes.
          <br />A considerable cost.
        </h2>
        <div>
          <p>
            Ridge underperformed Cash and Buy & Hold in both markets. Bitcoin’s
            570 buys and 570 sells incurred 9,932.12 USDT of attributed costs;
            Ether’s 499 buys and 499 sells incurred 9,239.49 USDT.
          </p>
          <p>
            That establishes a severe cost burden. Adding costs back to final
            equity would not produce a valid frictionless result: different
            costs would change quantities and the subsequent capital path.
          </p>
        </div>
      </section>
      <section className="section-block methodology-grid">
        <div>
          <p className="eyebrow">Read the small print</p>
          <h2>
            The assumptions
            <br />
            are part of the result.
          </h2>
          <Link className="text-link" href="/about/">
            Full methodology <Arrow />
          </Link>
        </div>
        <div className="methodology-details">
          <details open>
            <summary>How does a forecast become a trade?</summary>
            <p>
              The frozen Ridge policy targets long when its next-four-hour
              return forecast exceeds 1e-12; otherwise it targets cash. A candle
              ending at 12:00 is assumed available at 12:01. Execution uses the
              strictly next native minute opening: 12:02. No model fitting or
              tuning occurred for this run.
            </p>
          </details>
          <details open>
            <summary>What does each trade cost?</summary>
            <p>
              Per side: 10 basis points in fees, 1 basis point of half-spread
              and 2 basis points of adverse slippage. One basis point is 0.01%.
              Spread and slippage are already embedded in execution prices; they
              are attributed for reporting, not charged again as cash fees.
            </p>
          </details>
          <details>
            <summary>Are the accounts fairly funded?</summary>
            <p>
              All six accounts independently begin with 10,000 USDT. Cash earns
              no interest. Buy & Hold buys once at January 1 00:00 and retains
              its assets; Ridge’s earliest eligible fill is 00:02. These are
              separate accounts, not a combined portfolio.
            </p>
          </details>
          <details>
            <summary>What does the final value include?</summary>
            <p>
              Final marks are December 31, 2024 at 23:00 UTC. The final day and
              month are partial. Buy & Hold includes unsold assets with no
              invented terminal liquidation cost. Both Ridge accounts finish in
              cash.
            </p>
          </details>
          <details>
            <summary>What can’t this study tell us?</summary>
            <p>
              One previously inspected year and two correlated markets cannot
              establish future reliability. There is no measured latency,
              historical order book, quantity-specific liquidity or proof of
              fillability. This is not a controlled execution-frequency
              comparison with the earlier hourly study; the holding rules also
              changed.
            </p>
          </details>
        </div>
      </section>
      <Disclaimer />
      {notes.length > 0 && (
        <section className="section-block">
          <h2>Behind the numbers</h2>
          <div className="article-grid">
            {notes.map((a) => (
              <ArticleCard key={a.slug} article={a} />
            ))}
          </div>
        </section>
      )}
    </>
  );
}

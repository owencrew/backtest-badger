import { pageMetadata } from "@/lib/seo";
import Link from "next/link";
import { PageIntro, Arrow } from "@/components/ui";
import { MarketDashboard } from "@/components/market-dashboard";
import { ForwardDashboard } from "@/components/forward-dashboard";
export const metadata = pageMetadata(
  "The Burrow — Markets & forward research",
  "Follow genuine Binance Spot Bitcoin and Ether observations. Public forward forecasts remain unavailable; market prices are separate from strategy performance.",
  "/burrow/",
);
export default function Burrow() {
  return (
    <>
      <PageIntro section="The Burrow" title="Keep an eye on the market.">
        Genuine Binance Spot observations, with room for the next piece of
        evidence: forecasts recorded before their outcomes arrive.
      </PageIntro>
      <MarketDashboard />
      <ForwardDashboard />
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
            The 2024 strategy comparison is ready to explore in The Dig. Forward
            prediction accuracy is separate from historical backtests.
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

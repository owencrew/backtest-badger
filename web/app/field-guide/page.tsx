import { pageMetadata } from "@/lib/seo";
import { ArticleCard } from "@/components/editorial";
import { PageIntro, EmptyState } from "@/components/ui";
import { readArticles, isEditorialPreview } from "@/lib/content";
const topics = [
  [
    "01",
    "Backtesting fundamentals",
    "Historical simulation, leakage, overfitting and fair comparisons.",
  ],
  [
    "02",
    "Risk & performance",
    "Return, drawdown, volatility, turnover and the cost of trading.",
  ],
  [
    "03",
    "Predictive modelling & signals",
    "How a forecast differs from a strategy decision or a trade.",
  ],
  [
    "04",
    "Trading strategies",
    "Trend following, momentum, mean reversion and Buy & Hold.",
  ],
  [
    "05",
    "Asset classes & instruments",
    "Crypto, equities, ETFs, bonds, currencies and commodities; futures and options as instruments.",
  ],
  [
    "06",
    "Market data & execution",
    "Candles, missing observations, reference prices and actual fills.",
  ],
];
export const metadata = pageMetadata(
  "Field Guide — Learn the fundamentals",
  "Plain-language introductions to backtesting, performance metrics and the steps from forecasts to trades. Educational topics with clear evidence boundaries.",
  "/field-guide/",
);
export default function FieldGuide() {
  const guides = readArticles("guides").slice().reverse();
  return (
    <>
      <PageIntro section="Field Guide" title="Find your footing.">
        A small library for big questions. Plain-language introductions to
        markets, models and the things a performance chart can leave out.
      </PageIntro>
      <div className="preview-notice">
        <strong>Education, not a feature list</strong>
        <span>
          The platform’s implemented historical study covers crypto spot
          markets. Other asset classes, instruments and strategy families are
          learning topics or future research.
        </span>
      </div>
      {guides.length > 0 ? (
        <section className="section-block">
          <div className="section-heading">
            <h2>Start here</h2>
            <span className="small muted">
              {isEditorialPreview() &&
              guides.some((a) => a.status !== "Published")
                ? "Introductory drafts · Local editorial preview"
                : "Introductions to the research"}
            </span>
          </div>
          <div className="guide-card-grid">
            {guides.map((article) => (
              <ArticleCard
                key={article.slug}
                article={article}
                collection="guides"
              />
            ))}
          </div>
        </section>
      ) : (
        <EmptyState title="Introductory guides are being reviewed">
          Start with the methodology and verified historical study in The Dig.
          New introductions will appear here after editorial review.
        </EmptyState>
      )}
      <section className="section-block">
        <h2>Your learning map</h2>
        <div className="learning-map">
          {topics.map(([n, title, desc], i) => (
            <div key={n}>
              <span className="mono step-number">{n}</span>
              <div>
                <h3>{title}</h3>
                <p>{desc}</p>
              </div>
              <span className="topic-status">
                {guides.some((guide) => guide.slug.startsWith(`00${i + 1}-`))
                  ? guides.find((guide) => guide.slug.startsWith(`00${i + 1}-`))
                      ?.status !== "Published"
                    ? "Draft introduction above"
                    : "Introduction above"
                  : "Planned topic"}
              </span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

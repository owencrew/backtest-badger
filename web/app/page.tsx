import { pageMetadata } from "@/lib/seo";
import Link from "next/link";
import Image from "next/image";
import {
  Arrow,
  Disclaimer,
  SectionHeading,
  SourceNote,
  Status,
} from "@/components/ui";
import { PerformanceComparisonChart } from "@/components/performance-chart";
import { ArticleCard } from "@/components/editorial";
import { readArticles } from "@/lib/content";
import { markets } from "@/lib/research";

export const metadata = pageMetadata(
  "Dig into the evidence",
  "Open-source quantitative research: explore historical backtests, genuine crypto market observations and clear explanations of methods and limitations.",
  "/",
);
export default function Home() {
  const notes = readArticles("fieldNotes").slice(0, 2);
  const guides = readArticles("guides").slice().reverse().slice(0, 3);
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            Independent quantitative research
          </p>
          <h1>
            Dig into
            <br />
            the <span>evidence.</span>
          </h1>
          <p className="hero-tagline">A little badger. A lot of backtests.</p>
          <p className="hero-description">
            Markets are noisy. Good research shouldn’t be.
            <br className="desktop-break" /> Exploring data, testing ideas and
            sharing what
            <br className="desktop-break" /> we find. Even when the strategy
            loses.
          </p>
          <div className="hero-actions">
            <Link className="button" href="/dig/">
              Explore The Dig <Arrow />
            </Link>
            <Link
              className="button button-secondary"
              href={notes.length ? "/field-notes/" : "/burrow/"}
            >
              {notes.length ? "Read Field Notes" : "Observe the markets"}{" "}
              <Arrow />
            </Link>
          </div>
          <div className="hero-footnote">
            <span>Open source</span>
            <span>Reproducible research</span>
          </div>
        </div>
        <div className="hero-art">
          <div className="art-topline">
            <span>THE BACKTEST BADGER</span>
            <span>FIG. 001</span>
          </div>
          <div className="art-circle" aria-hidden="true" />
          <Image
            className="hero-badger"
            src="/brand/badger-mascot.webp"
            width={1254}
            height={1254}
            alt="An original black-and-white badger digging through soil with financial candlesticks."
            priority
          />
          <div className="art-bottomline">
            <span>
              A curious nature.
              <br />A rigorous method.
            </span>
            <span className="art-cross" aria-hidden="true">
              ✳
            </span>
          </div>
        </div>
      </section>
      <div className="evidence-strip">
        <span className="eyebrow">Built on evidence</span>
        <span>Real market data</span>
        <span>Explicit trading costs</span>
        <span>Independent benchmarks</span>
      </div>
      <section className="featured-research section-block">
        <div className="research-editorial">
          <Status>Historical simulation</Status>
          <p className="eyebrow">Latest research / 2024 study</p>
          <h2>
            A working pipeline.
            <br />A losing strategy.
          </h2>
          <p>
            Our Ridge strategy lost 60.69% on Bitcoin. Buy & Hold gained
            120.81%. The useful finding? A clear, auditable account of what
            didn’t work.
          </p>
          <Link href="/dig/" className="text-link">
            Look beneath the returns <Arrow />
          </Link>
          <span className="editorial-number" aria-hidden="true">
            01 /
          </span>
        </div>
        <div className="research-chart-card">
          <div className="panel-heading">
            <h3>Bitcoin: strategy vs. benchmarks</h3>
            <span className="small mono muted">BTCUSDT</span>
          </div>
          <PerformanceComparisonChart markets={[markets[0]]} compact />
          <p className="panel-footnote">
            10,000 USDT per independent account · After assumed costs
          </p>
        </div>
      </section>
      <SourceNote />
      <section className="section-block process-section">
        <SectionHeading
          eyebrow="The method behind the mascot"
          title="Good questions. Traceable answers."
        />
        <div className="process-grid">
          {[
            ["01", "Market data", "Keep the observations. Disclose the gaps."],
            [
              "02",
              "Predictive models",
              "Learn from the past, without seeing the future.",
            ],
            ["03", "Backtesting", "Simulate decisions with timing and costs."],
            [
              "04",
              "Evaluation",
              "Compare fairly. Keep the uncomfortable results.",
            ],
          ].map(([n, title, text]) => (
            <div className="process-step" key={n}>
              <span className="mono step-number">{n}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
        <p className="process-note">
          Two separate evidence streams: historical simulations look back;
          forward forecasts are recorded before outcomes arrive. Neither is real
          trading.
        </p>
      </section>
      <section className="section-block">
        <SectionHeading
          eyebrow="Find your way around"
          title="There’s more beneath the surface."
        />
        <div className="destination-grid">
          {[
            [
              "/burrow/",
              "01",
              "The Burrow",
              "Follow the research",
              "Forward forecasts, scoring and the evidence still to come.",
              "Public market data",
            ],
            [
              "/dig/",
              "02",
              "The Dig",
              "Interrogate the results",
              "Strategies, benchmarks and the assumptions between them.",
              "2024 backtest",
            ],
            [
              "/field-notes/",
              "03",
              "Field Notes",
              "Read the discoveries",
              "The decisions and surprises behind the research.",
              notes.length ? "Research journal" : "Articles in review",
            ],
            [
              "/field-guide/",
              "04",
              "Field Guide",
              "Get your bearings",
              "Clear explanations for a complicated subject.",
              "Learning library",
            ],
          ].map(([href, n, title, subtitle, copy, tag]) => (
            <Link href={href} className="destination-card" key={href}>
              <div className="destination-top">
                <span className="mono">{n}</span>
                <Arrow />
              </div>
              <h3>{title}</h3>
              <strong>{subtitle}</strong>
              <p>{copy}</p>
              <span className="destination-tag">{tag}</span>
            </Link>
          ))}
        </div>
      </section>
      {notes.length > 0 && (
        <section className="section-block">
          <SectionHeading
            eyebrow="Fresh from the notebook"
            title="The findings are the story."
          >
            <Link className="text-link" href="/field-notes/">
              All Field Notes <Arrow />
            </Link>
          </SectionHeading>
          <div className="article-grid">
            {notes.map((article, i) => (
              <ArticleCard
                key={article.slug}
                article={article}
                featured={i === 0}
              />
            ))}
          </div>
        </section>
      )}
      <section className="guide-band">
        <div>
          <p className="eyebrow">A field guide for curious minds</p>
          <h2>Understand the methods behind the numbers.</h2>
          <Link href="/field-guide/" className="text-link">
            Explore Field Guide <Arrow />
          </Link>
        </div>
        <div className="guide-links">
          {guides.length ? (
            guides.map((g, i) => (
              <Link key={g.slug} href={`/field-guide/${g.slug}/`}>
                <span className="mono">0{i + 1}</span>
                <span>
                  {g.title}
                  <small>
                    {g.status === "Published"
                      ? "Introduction"
                      : "Educational draft"}{" "}
                    · {g.minutes} min
                  </small>
                </span>
                <Arrow />
              </Link>
            ))
          ) : (
            <p>
              Introductory explanations are awaiting editorial approval. Explore
              the planned learning topics in Field Guide.
            </p>
          )}
        </div>
      </section>
      <Disclaimer />
    </>
  );
}

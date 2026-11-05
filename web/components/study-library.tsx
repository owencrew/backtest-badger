import Link from "next/link";

const studies = [
  {
    number: "001",
    title: "The 2024 Ridge Sign Study",
    href: "/dig/#study-001",
    description:
      "A machine-learning forecast becomes a trading decision. What happens when frequent position changes meet transaction costs?",
    rule: "Four-hour Ridge signals",
    date: "24 October 2026",
    dateLabel: "Evidence recorded",
    finding:
      "Frequent trading imposed a substantial cost burden and both accounts lost money.",
  },
  {
    number: "002",
    title: "Can a Slower Trend Beat the Noise?",
    href: "/dig/study-002/",
    description:
      "A simple 30-day trend rule makes one decision each day. Does slower decision-making translate into better results?",
    rule: "Daily 30-day trend",
    date: "1 November 2026",
    dateLabel: "Research run",
    finding:
      "About 95% lower trading costs than Ridge, but both markets still lagged Buy & Hold.",
  },
];
export function StudyLibrary() {
  return (
    <section className="study-library" aria-labelledby="study-library-title">
      <div className="section-heading">
        <h2 id="study-library-title">Two studies. One inspected year.</h2>
        <span className="small muted">The research library</span>
      </div>
      <div className="study-card-grid">
        {studies.map((study) => (
          <Link
            className="study-card"
            href={study.href}
            key={study.number}
            aria-current={study.number === "001" ? "location" : undefined}
          >
            <div className="study-card-top">
              <span className="eyebrow">Study {study.number}</span>
              <span className="small">
                {study.number === "001" ? "Open below" : "Explore study"}
              </span>
            </div>
            <h3>{study.title}</h3>
            <p>{study.description}</p>
            <p className="study-card-meta">
              Historical simulation · Binance Spot BTC/ETH · 2024
              <br />
              {study.rule}
              <br />
              {study.dateLabel} {study.date}
            </p>
            <p className="study-card-finding">{study.finding}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

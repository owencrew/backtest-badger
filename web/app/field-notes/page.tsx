import { pageMetadata } from "@/lib/seo";
import { ArticleCard } from "@/components/editorial";
import { PageIntro, EmptyState } from "@/components/ui";
import { readArticles, isEditorialPreview } from "@/lib/content";
export const metadata = pageMetadata(
  "Field Notes — The research journal",
  "Research discoveries from Backtest Badger: missing market data, trading costs, changing positions and the timing assumptions behind historical backtests.",
  "/field-notes/",
);
export default function FieldNotes() {
  const notes = readArticles("fieldNotes");
  const featured = notes[0];
  return (
    <>
      <PageIntro section="Field Notes" title="The discoveries along the way.">
        Research rarely follows a straight line. These are the questions,
        surprises and decisions worth writing down.
      </PageIntro>
      {isEditorialPreview() && notes.some((a) => a.status !== "Published") && (
        <div className="preview-notice">
          <strong>From the editor’s desk</strong>
          <span>
            Unpublished articles are shown here for local editorial review. Only
            explicitly approved source bytes appear in production.
          </span>
        </div>
      )}
      {featured ? (
        <>
          <div className="journal-feature">
            <div className="journal-art" aria-hidden="true">
              <span className="eyebrow">
                Field Note / {featured.slug.slice(0, 3)}
              </span>
              <div className="journal-illustration">
                <svg viewBox="0 0 280 160" fill="none">
                  <path
                    d="M25 130H255M55 120V92M110 120V62M165 120V32M220 120V12"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <circle cx="110" cy="62" r="10" fill="currentColor" />
                  <path
                    d="M120 62H165V32"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeDasharray="5 5"
                  />
                </svg>
                <strong>{featured.slug.slice(0, 3)}</strong>
              </div>
              <span>{featured.title}</span>
            </div>
            <ArticleCard article={featured} featured />
          </div>
          {notes.length > 1 && (
            <section className="section-block">
              <h2>More from the notebook</h2>
              <div className="article-grid">
                {notes
                  .filter((a) => a.slug !== featured.slug)
                  .map((article) => (
                    <ArticleCard key={article.slug} article={article} />
                  ))}
              </div>
            </section>
          )}
        </>
      ) : (
        <EmptyState title="The notebook is under review">
          Research articles will appear here after explicit editorial approval.
          The historical study and its source report remain available in The
          Dig.
        </EmptyState>
      )}
    </>
  );
}

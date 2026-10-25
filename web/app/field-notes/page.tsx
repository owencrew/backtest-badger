import type { Metadata } from "next";
import { ArticleCard } from "@/components/editorial";
import { PageIntro, EmptyState } from "@/components/ui";
import { readArticles, isEditorialPreview } from "@/lib/content";
export const metadata: Metadata = {
  title: "Field Notes — The research journal",
};
export default function FieldNotes() {
  const notes = readArticles("fieldNotes");
  const featured = notes.find((a) => a.slug.startsWith("003")) ?? notes[0];
  return (
    <>
      <PageIntro section="Field Notes" title="The discoveries along the way.">
        Research rarely follows a straight line. These are the questions,
        surprises and decisions worth writing down.
      </PageIntro>
      {isEditorialPreview() && (
        <div className="preview-notice">
          <strong>From the editor’s desk</strong>
          <span>
            All four articles are draft local previews. Their original research
            conclusions and Markdown sources are preserved.
          </span>
        </div>
      )}
      {featured ? (
        <>
          <div className="journal-feature">
            <div className="journal-art" aria-hidden="true">
              <span className="eyebrow">Field Note / 003</span>
              <div className="journal-bars">
                <i />
                <i />
                <i />
                <i />
                <i />
                <i />
                <i />
              </div>
              <span>THE COST OF CHANGING COURSE</span>
            </div>
            <ArticleCard article={featured} featured />
          </div>
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

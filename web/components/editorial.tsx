import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { type Article, type Collection, editorialHref } from "@/lib/content";
import { Arrow, Status } from "./ui";

export function ArticleCard({
  article,
  collection = "fieldNotes",
  featured = false,
}: {
  article: Article;
  collection?: Collection;
  featured?: boolean;
}) {
  const href = `/${collection === "fieldNotes" ? "field-notes" : "field-guide"}/${article.slug}/`;
  return (
    <article className={`article-card ${featured ? "featured-article" : ""}`}>
      <div className="article-meta">
        <span className="mono">{article.date}</span>
        <span>
          {article.status === "Published"
            ? "Published"
            : "Draft · Local preview"}
        </span>
      </div>
      <div>
        <p className="eyebrow">
          {collection === "fieldNotes"
            ? `Field Note ${article.slug.slice(0, 3)}`
            : "Field Guide"}
        </p>
        <h3>
          <Link href={href}>{article.title}</Link>
        </h3>
        <p className="article-excerpt">{article.excerpt}</p>
      </div>
      <Link href={href} className="text-link">
        {article.status === "Published" ? "Read article" : "Read the preview"}
        <Arrow />
      </Link>
      <span className="reading-time">{article.minutes} min read</span>
    </article>
  );
}
export function ArticleLayout({
  article,
  collection,
  related,
}: {
  article: Article;
  collection: Collection;
  related: Article[];
}) {
  const root = collection === "fieldNotes" ? "/field-notes/" : "/field-guide/";
  const label = collection === "fieldNotes" ? "Field Notes" : "Field Guide";
  return (
    <>
      <div className="article-header">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Home</Link>
          <span>/</span>
          <Link href={root}>{label}</Link>
          <span>/</span>
          <span>{article.slug.slice(0, 3)}</span>
        </nav>
        <Status muted>
          {article.status === "Published"
            ? "Published article"
            : "Draft · Local editorial preview"}
        </Status>
        <h1>{article.title}</h1>
        <p className="lede">{article.topic}</p>
        <div className="article-meta">
          <time dateTime={article.date}>{article.date}</time>
          <span>{article.minutes} min read</span>
          <span>
            {collection === "guides"
              ? "Educational explanation"
              : "Research journal"}
          </span>
        </div>
      </div>
      {article.status !== "Published" && (
        <aside className="preview-notice">
          Editorial preview only. This draft is excluded from production builds
          until its status and exact content are approved.
        </aside>
      )}
      <div className="article-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ href, children }) => (
              <a href={editorialHref(href ?? "", collection)}>{children}</a>
            ),
            table: ({ children }) => (
              <div
                className="table-wrap"
                tabIndex={0}
                role="region"
                aria-label="Article data table"
              >
                <table>{children}</table>
              </div>
            ),
          }}
        >
          {article.body}
        </ReactMarkdown>
      </div>
      <div className="article-end">
        <Link className="text-link" href="/about/">
          Understand the methodology <Arrow />
        </Link>
        <Link className="text-link" href={root}>
          Back to {label} <Arrow />
        </Link>
      </div>
      {related.length > 0 && (
        <section className="section-block">
          <h2>Keep digging</h2>
          <div className="article-grid">
            {related.map((a) => (
              <ArticleCard key={a.slug} article={a} collection={collection} />
            ))}
          </div>
        </section>
      )}
    </>
  );
}

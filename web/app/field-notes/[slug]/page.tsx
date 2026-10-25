import { notFound } from "next/navigation";
import { readArticles } from "@/lib/content";
import { ArticleLayout } from "@/components/editorial";
export const dynamicParams = false;
export function generateStaticParams() {
  const articles = readArticles("fieldNotes");
  // A reserved not-found path lets static export succeed when nothing is approved.
  return articles.length
    ? articles.map((a) => ({ slug: a.slug }))
    : [{ slug: "publication-pending" }];
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const article = readArticles("fieldNotes").find((a) => a.slug === slug);
  return { title: article?.title ?? "Article unavailable" };
}
export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const articles = readArticles("fieldNotes");
  const article = articles.find((a) => a.slug === slug);
  if (!article) notFound();
  return (
    <ArticleLayout
      article={article}
      collection="fieldNotes"
      related={articles.filter((a) => a.slug !== slug).slice(0, 2)}
    />
  );
}

import { articleMetadata } from "@/lib/seo";
import { notFound } from "next/navigation";
import { readArticles } from "@/lib/content";
import { ArticleLayout } from "@/components/editorial";
export const dynamicParams = false;
export function generateStaticParams() {
  const articles = readArticles("guides");
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
  const article = readArticles("guides").find((a) => a.slug === slug);
  if (!article) notFound();
  return articleMetadata(article, "guides");
}
export default async function GuidePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const articles = readArticles("guides");
  const article = articles.find((a) => a.slug === slug);
  if (!article) notFound();
  return (
    <ArticleLayout
      article={article}
      collection="guides"
      related={articles.filter((a) => a.slug !== slug).slice(0, 2)}
    />
  );
}

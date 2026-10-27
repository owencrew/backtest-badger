import type { Metadata } from "next";
import type { Article, Collection } from "./content";

export const siteOrigin = "https://www.backtestbadger.com";
export const publicPaths = [
  "/",
  "/burrow/",
  "/dig/",
  "/field-notes/",
  "/field-guide/",
  "/about/",
];

// Static export resolves this at build time. Article approval never enables it.
export function indexingEnabled(value = process.env.BADGER_SEARCH_INDEXING) {
  return value === "www-live-owner-approved";
}

export function pageMetadata(
  title: string,
  description: string,
  pathname: string,
  type: "website" | "article" = "website",
): Metadata {
  const url = `${siteOrigin}${pathname}`;
  const socialTitle = `${title} | Backtest Badger`;
  return {
    title: { absolute: socialTitle },
    description,
    alternates: { canonical: url },
    openGraph: {
      type,
      title: socialTitle,
      description,
      url,
      siteName: "Backtest Badger",
      locale: "en_GB",
    },
    // No promotional artwork until its distribution rights are resolved.
    twitter: { card: "summary", title: socialTitle, description },
  };
}

export function articleMetadata(article: Article, collection: Collection) {
  const section = collection === "fieldNotes" ? "field-notes" : "field-guide";
  return pageMetadata(
    article.title,
    `${article.topic}. ${collection === "fieldNotes" ? "A research Field Note" : "An introductory Field Guide"} from Backtest Badger.`,
    `/${section}/${article.slug}/`,
    "article",
  );
}

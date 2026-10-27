import type { MetadataRoute } from "next";
import { readArticles } from "../lib/content";
import { publicPaths, siteOrigin } from "../lib/seo";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const paths = [
    ...publicPaths,
    ...readArticles("fieldNotes", "production").map(
      (article) => `/field-notes/${article.slug}/`,
    ),
    ...readArticles("guides", "production").map(
      (article) => `/field-guide/${article.slug}/`,
    ),
  ];
  // Article dates are original writing dates, not deployment/last-modified dates.
  return paths.map((pathname) => ({ url: `${siteOrigin}${pathname}` }));
}

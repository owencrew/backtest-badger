import type { MetadataRoute } from "next";
import { indexingEnabled, siteOrigin } from "../lib/seo";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    // Crawlers must be able to read the HTML noindex directive on candidates.
    rules: { userAgent: "*", allow: "/" },
    ...(indexingEnabled() ? { sitemap: `${siteOrigin}/sitemap.xml` } : {}),
  };
}

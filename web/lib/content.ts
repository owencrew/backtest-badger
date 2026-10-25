import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import approvals from "../content/publication-approvals.json";
import { repository, sourceRevision } from "./research";

export type Collection = "fieldNotes" | "guides";
export type Article = {
  slug: string;
  title: string;
  date: string;
  topic: string;
  status: string;
  excerpt: string;
  body: string;
  minutes: number;
  sourceFile: string;
  sha256: string;
};
export type Approval = { slug: string; sha256: string };
export const isEditorialPreview = () => process.env.NODE_ENV === "development";

export function publicationAllowed(
  article: Article,
  environment: string | undefined,
  list: Approval[],
) {
  if (environment === "development") return true;
  return (
    article.status === "Published" &&
    list.some((a) => a.slug === article.slug && a.sha256 === article.sha256)
  );
}

export function readArticles(collection: Collection): Article[] {
  const directory =
    collection === "fieldNotes"
      ? path.join(process.cwd(), "..", "docs", "field-notes")
      : path.join(process.cwd(), "content", "guides");
  return fs
    .readdirSync(directory)
    .filter((f) => /^\d{3}-.+\.md$/.test(f))
    .map((file) => {
      const raw = fs.readFileSync(path.join(directory, file), "utf8");
      const title = raw.match(/^# (.+)$/m)?.[1] ?? file;
      const metadata = (key: string) =>
        raw.match(new RegExp(`^- \\*\\*${key}:\\*\\* (.+)$`, "m"))?.[1] ?? "";
      const status =
        metadata("Publication status") ||
        raw.match(/^Publication status: (.+)$/m)?.[1] ||
        "Draft";
      const body = raw
        .replace(/^Publication status: .+\n+/m, "")
        .replace(/^# .+\n+/m, "")
        .replace(/^- \*\*(Date|Stage|Topic|Publication status):\*\* .+\n/gm, "")
        .trim();
      const excerpt = body
        .split(/\n\s*\n/)[0]
        .replace(/\n/g, " ")
        .replace(/\*\*/g, "");
      return {
        slug: file.replace(/\.md$/, ""),
        title,
        date: metadata("Date"),
        topic: metadata("Topic"),
        status,
        excerpt,
        body,
        minutes: Math.max(1, Math.ceil(body.split(/\s+/).length / 220)),
        sourceFile: file,
        sha256: createHash("sha256").update(raw).digest("hex"),
      };
    })
    .filter((article) =>
      publicationAllowed(article, process.env.NODE_ENV, approvals[collection]),
    )
    .sort((a, b) => b.slug.localeCompare(a.slug));
}

export function editorialHref(href: string, collection: Collection) {
  if (/^\d{3}-.+\.md(?:#.*)?$/.test(href)) {
    return `/${collection === "fieldNotes" ? "field-notes" : "field-guide"}/${href.replace(/\.md(?=#|$)/, "/")}`;
  }
  if (href.startsWith("../") && href.includes(".md")) {
    return `${repository}/blob/${sourceRevision}/docs/${href.slice(3)}`;
  }
  return href;
}

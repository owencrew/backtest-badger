import Link from "next/link";
import Image from "next/image";
import type { ReactNode } from "react";
import { repository, reportUrl } from "@/lib/research";

export function Arrow() {
  return (
    <span className="link-arrow" aria-hidden="true">
      ↗
    </span>
  );
}
export function Status({
  children,
  muted = false,
}: {
  children: ReactNode;
  muted?: boolean;
}) {
  return (
    <span className={`status ${muted ? "status-muted" : ""}`}>
      <span aria-hidden="true" />
      {children}
    </span>
  );
}
export function PageIntro({
  section,
  title,
  children,
}: {
  section: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="page-intro">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link href="/">Home</Link>
        <span>/</span>
        <span>{section}</span>
      </nav>
      <p className="eyebrow">{section}</p>
      <h1>{title}</h1>
      <p className="lede">{children}</p>
    </div>
  );
}
export function SectionHeading({
  eyebrow,
  title,
  children,
}: {
  eyebrow?: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
      </div>
      {children}
    </div>
  );
}
export function Disclaimer() {
  return (
    <aside className="disclaimer">
      <span className="disclaimer-symbol" aria-hidden="true">
        ⓘ
      </span>
      <p>
        <strong>Historical simulation. Real limitations.</strong> 2024 was
        previously inspected. These results are exploratory, include assumed
        costs and do not establish future returns or actual fillability.
        Research only; not investment advice.
      </p>
    </aside>
  );
}
export function SourceNote() {
  return (
    <p className="source-note">
      Source:{" "}
      <a href={reportUrl}>
        Stage 4B.2E.5g research report <Arrow />
      </a>{" "}
      · Evidence recorded 24 Oct 2026 · Final mark 31 Dec 2024, 23:00 UTC.
      Display values are rounded.
    </p>
  );
}
export function EmptyState({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon" aria-hidden="true">
        ⊙
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-top">
        <div>
          <Link href="/" className="brand">
            <Image src="/brand/badger-mark.svg" width={32} height={32} alt="" />
            <span>
              backtest<span className="brand-light">badger.</span>
            </span>
          </Link>
          <p>A little badger. A lot of backtests.</p>
        </div>
        <div className="footer-links">
          <Link href="/about/">About & methodology</Link>
          <Link href="/field-guide/">Field Guide</Link>
          <a href={repository}>
            Source on GitHub <Arrow />
          </a>
        </div>
      </div>
      <div className="footer-bottom">
        <p>Independent research. Transparent methods. Honest results.</p>
        <p>Research only · No real-money trading</p>
      </div>
    </footer>
  );
}

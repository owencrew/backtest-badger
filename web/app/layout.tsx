import type { Metadata } from "next";
import "@fontsource-variable/manrope";
import "./globals.css";
import { SiteHeader } from "@/components/site-header";
import { SiteFooter } from "@/components/ui";

export const metadata: Metadata = {
  title: {
    default: "Backtest Badger — Dig into the evidence.",
    template: "%s | Backtest Badger",
  },
  description:
    "A little badger. A lot of backtests. Open-source quantitative research with transparent methods and honest results.",
  icons: { icon: "/brand/badger-mark.svg" },
  robots: { index: false, follow: false },
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <SiteHeader />
        <main id="main" className="page-container">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}

"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState } from "react";

const destinations = [
  ["/", "Home"],
  ["/burrow/", "The Burrow"],
  ["/dig/", "The Dig"],
  ["/field-notes/", "Field Notes"],
  ["/field-guide/", "The Field Guide"],
  ["/about/", "About"],
];
export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header
      className="site-header"
      onKeyDown={(e) => {
        if (e.key === "Escape" && open) {
          setOpen(false);
          document.querySelector<HTMLButtonElement>(".menu-toggle")?.focus();
        }
      }}
    >
      <div className="header-inner">
        <Link
          href="/"
          className="brand"
          aria-label="Backtest Badger home"
          onClick={() => setOpen(false)}
        >
          <Image src="/brand/badger-mark.svg" width={39} height={39} alt="" />
          <span>
            backtest<span className="brand-light">badger</span>
            <span className="brand-dot">.</span>
          </span>
        </Link>
        <button
          className="menu-toggle"
          aria-expanded={open}
          aria-controls="primary-navigation"
          onClick={() => setOpen(!open)}
        >
          {open ? "Close ×" : "Menu ☰"}
        </button>
        <nav
          id="primary-navigation"
          className={open ? "primary-nav is-open" : "primary-nav"}
          aria-label="Main navigation"
        >
          {destinations.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              aria-current={
                (
                  href === "/"
                    ? pathname === "/"
                    : pathname.startsWith(href.slice(0, -1))
                )
                  ? "page"
                  : undefined
              }
              onClick={() => setOpen(false)}
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

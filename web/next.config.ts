import type { NextConfig } from "next";

const config: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  poweredByHeader: false,
  devIndicators: false,
  agentRules: false,
  distDir: process.env.NODE_ENV === "development" ? ".next-dev" : ".next",
};
export default config;

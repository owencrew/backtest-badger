// Run from the repository root after the locked frontend install.
// esbuild is resolved from the pinned tsx dependency; no runtime npm install.
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import path from "node:path";

const output = process.argv[2];
if (!output)
  throw new Error(
    "Usage: node ops/public-feed/bundle-validator.mjs OUTPUT_DIR",
  );
mkdirSync(output, { recursive: true, mode: 0o700 });
const require = createRequire(import.meta.url);
const tsx = require.resolve("tsx/package.json", {
  paths: [path.resolve("web")],
});
const { buildSync } = require(require.resolve("esbuild", { paths: [tsx] }));
for (const [source, name] of [
  ["validate-forward", "validator"],
  ["check-forward-endpoint", "check-forward-endpoint"],
]) {
  buildSync({
    entryPoints: [`web/scripts/${source}.ts`],
    outfile: path.join(output, `${name}.cjs`),
    bundle: true,
    platform: "node",
    format: "cjs",
    target: "node24",
  });
}

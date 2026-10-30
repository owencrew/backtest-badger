// Build only isolated v2 helpers; existing v1 bundles remain untouched.
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import path from "node:path";
const output = process.argv[2];
if (!output) throw new Error("Expected private v2 bundle directory.");
mkdirSync(output, { recursive: true, mode: 0o700 });
const require = createRequire(import.meta.url);
const tsx = require.resolve("tsx/package.json", { paths: [path.resolve("web")] });
const { buildSync } = require(require.resolve("esbuild", { paths: [tsx] }));
for (const [source, name] of [
  ["validate-forward-v2", "validator-v2"],
  ["benchmark-forward-v2-validator", "benchmark-v2-validator"],
  ["check-forward-v2-endpoint", "check-forward-v2-endpoint"],
]) {
  buildSync({ entryPoints: [`web/scripts/${source}.ts`],
    outfile: path.join(output, `${name}.cjs`), bundle: true,
    platform: "node", format: "cjs", target: "node24" });
}

import { readFileSync } from "node:fs";
import { validateForecastV2 } from "../lib/forecast";

if (process.argv.length !== 3)
  throw new Error("Expected one private v2 candidate.");
const bytes = readFileSync(process.argv[2]);
if (!bytes.length || bytes.length > 65536)
  throw new Error("Invalid snapshot size.");
validateForecastV2(JSON.parse(bytes.toString("utf8")));
console.log("Public v2 contract valid. Nothing uploaded.");

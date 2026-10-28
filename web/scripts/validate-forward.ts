import { readFileSync } from "node:fs";
import { validateForecast } from "../lib/forecast";
if (process.argv.length !== 3)
  throw new Error(
    "Usage: node --import tsx scripts/validate-forward.ts candidate.json",
  );
validateForecast(JSON.parse(readFileSync(process.argv[2], "utf8")));
console.log("Public forward contract valid. Validation does not upload data.");

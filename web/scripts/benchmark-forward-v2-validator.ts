/** Read-only benchmark entry point: receive public projection over private stdin. */
import { readFileSync } from "node:fs";
import { validateForecastV2 } from "../lib/forecast";
const bytes = readFileSync(0);
if (!bytes.length || bytes.length > 65536) throw new Error("Invalid v2 size.");
validateForecastV2(JSON.parse(bytes.toString("utf8")));

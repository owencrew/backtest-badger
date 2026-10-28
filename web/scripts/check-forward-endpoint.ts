/** Independent public read: schema, clocks, coverage and response metadata. */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { validateForecast, forecastIsStale } from "../lib/forecast";

export async function checkEndpoint(url: string, expectedFile?: string) {
  const endpoint = new URL(url);
  if (
    endpoint.protocol !== "https:" ||
    endpoint.username ||
    endpoint.password ||
    endpoint.pathname !== "/forward-v1.json" ||
    endpoint.search ||
    endpoint.hash
  )
    throw new Error("Expected the approved HTTPS forward object URL.");
  const response = await fetch(endpoint, {
    signal: AbortSignal.timeout(15_000),
    redirect: "error",
    headers: { Origin: "https://www.backtestbadger.com" },
    cache: "no-store",
  });
  if (
    response.status !== 200 ||
    response.headers.get("content-type")?.split(";")[0] !==
      "application/json" ||
    response.headers.get("cache-control") !==
      "public, max-age=60, must-revalidate" ||
    response.headers.get("access-control-allow-origin") !==
      "https://www.backtestbadger.com"
  )
    throw new Error("Public HTTP metadata/CORS mismatch.");
  const reader = response.body!.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > 65536) throw new Error("Public response exceeds size budget.");
      chunks.push(value);
    }
  } finally {
    await reader.cancel();
  }
  const bytes = Buffer.concat(chunks);
  const snapshot = validateForecast(JSON.parse(bytes.toString("utf8")));
  if (snapshot.latest.length !== 2)
    throw new Error("Both BTC and ETH forecasts are required for activation.");
  if (expectedFile && !bytes.equals(readFileSync(expectedFile)))
    throw new Error("Public bytes differ from the validated publication.");
  if (forecastIsStale(snapshot, Date.now()))
    throw new Error("Published cutoff is stale.");
  // A fresh exporter clock cannot hide missed research issuance. Allow the
  // existing 16-minute issuance window after the most recent 4h boundary.
  const boundary = Math.floor(Date.now() / 14_400_000) * 14_400_000;
  const requiredSource =
    Date.now() >= boundary + 16 * 60_000 ? boundary : boundary - 14_400_000;
  if (
    snapshot.latest.some((f) => Date.parse(f.source_close_at) < requiredSource)
  )
    throw new Error("Publication succeeded but forecast issuance is stale.");
  console.log(
    JSON.stringify({
      status: "public-feed-healthy",
      sha256: createHash("sha256").update(bytes).digest("hex"),
      bytes: size,
      as_of: snapshot.as_of,
      generated_at: snapshot.generated_at,
    }),
  );
}

if (process.argv[1]?.match(/check-forward-endpoint\.(ts|cjs)$/)) {
  checkEndpoint(process.argv[2], process.argv[3]).catch(() => {
    console.error(
      "Public feed check failed: inspect HTTP, schema, publication age and issuance.",
    );
    process.exitCode = 1;
  });
}

/** Independent v2 HTTPS read. No credential access and no R2 write capability. */
import { createHash, randomUUID } from "node:crypto";
import {
  closeSync,
  existsSync,
  fsyncSync,
  openSync,
  readFileSync,
  renameSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { basename, dirname, join } from "node:path";
import { isDeepStrictEqual } from "node:util";
import {
  forecastIsStale,
  timestamp,
  validateForecastV2,
} from "../lib/forecast";

type Snapshot = ReturnType<typeof validateForecastV2>;
export const V2_URL = "https://data.backtestbadger.com/forward-v2.json";

export function checkProgress(previous: Snapshot, current: Snapshot) {
  if (
    ["as_of", "generated_at"].some(
      (k) =>
        timestamp(current[k as "as_of"]) < timestamp(previous[k as "as_of"]),
    )
  )
    throw new Error("V2 publication clocks regressed.");
  for (const old of previous.latest_scored) {
    const row = current.latest_scored.find((r) => r.symbol === old.symbol);
    if (
      !row ||
      timestamp(row.source_close_at) < timestamp(old.source_close_at) ||
      (timestamp(row.source_close_at) === timestamp(old.source_close_at) &&
        !isDeepStrictEqual(row, old))
    )
      throw new Error("V2 scored evidence regressed or changed.");
  }
  for (const old of previous.latest) {
    const row = current.latest.find((r) => r.symbol === old.symbol);
    if (!row || timestamp(row.source_close_at) < timestamp(old.source_close_at))
      throw new Error("V2 issuance regressed.");
    if (timestamp(row.source_close_at) === timestamp(old.source_close_at)) {
      if (
        (
          ["issued_at", "target_close_at", "recipe_sha256", "cohort"] as const
        ).some((k) => row[k] !== old[k]) ||
        Object.keys(old.models).some((m) => {
          const model = m as keyof typeof old.models;
          return (
            row.models[model].predicted_log_return_4h !==
            old.models[model].predicted_log_return_4h
          );
        }) ||
        (old.status === "scored" && !isDeepStrictEqual(row, old))
      )
        throw new Error("V2 original observation changed.");
    }
  }
  for (const old of previous.evaluations) {
    const row = current.evaluations.find(
      (r) => r.symbol === old.symbol && r.cohort === old.cohort,
    )!;
    if (
      row.genuine_predictions < old.genuine_predictions ||
      row.matched_count < old.matched_count
    )
      throw new Error("V2 evidence counts regressed.");
  }
}

function saveState(file: string, bytes: Buffer) {
  const temporary = join(dirname(file), `.v2-check-${randomUUID()}`);
  try {
    const fd = openSync(temporary, "wx", 0o600);
    try {
      writeFileSync(fd, bytes);
      fsyncSync(fd);
    } finally {
      closeSync(fd);
    }
    renameSync(temporary, file);
    const directory = openSync(dirname(file), "r");
    try {
      fsyncSync(directory);
    } finally {
      closeSync(directory);
    }
  } finally {
    if (existsSync(temporary)) unlinkSync(temporary);
  }
}

export async function checkV2Endpoint(
  url: string,
  expectedFile?: string,
  stateFile?: string,
) {
  // Exact allowlist also rejects alternate hosts, ports, credentials and redirects.
  if (url !== V2_URL) throw new Error("Expected the approved v2 HTTPS URL.");
  if (stateFile && basename(stateFile) !== "last-check-v2.json")
    throw new Error("Expected isolated v2 checker state.");
  const response = await fetch(url, {
    signal: AbortSignal.timeout(15_000),
    redirect: "error",
    cache: "no-store",
    headers: { Origin: "https://www.backtestbadger.com" },
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
    throw new Error("V2 HTTP metadata/CORS mismatch.");
  if (!response.body) throw new Error("Missing v2 response body.");
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > 65536) throw new Error("V2 response exceeds size budget.");
      chunks.push(value);
    }
  } finally {
    await reader.cancel();
  }
  const bytes = Buffer.concat(chunks);
  const now = Date.now();
  const snapshot = validateForecastV2(
    JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)),
    now,
  );
  if (snapshot.latest.length !== 2) throw new Error("Both markets required.");
  if (expectedFile && !bytes.equals(readFileSync(expectedFile)))
    throw new Error("V2 public bytes differ from validated publication.");
  if (forecastIsStale(snapshot, now))
    throw new Error("V2 publication is stale.");
  const boundary = Math.floor(now / 14_400_000) * 14_400_000;
  const requiredSource =
    now >= boundary + 16 * 60_000 ? boundary : boundary - 14_400_000;
  if (
    snapshot.latest.some((r) => timestamp(r.source_close_at) < requiredSource)
  )
    throw new Error("V2 forecast issuance is stale.");
  if (stateFile && existsSync(stateFile))
    checkProgress(
      validateForecastV2(JSON.parse(readFileSync(stateFile, "utf8")), now),
      snapshot,
    );
  // Failed fetch, schema, bytes, freshness or progression never advances state.
  if (stateFile) saveState(stateFile, bytes);
  const result = {
    status: "public-feed-v2-healthy",
    sha256: createHash("sha256").update(bytes).digest("hex"),
    bytes: size,
    as_of: snapshot.as_of,
    generated_at: snapshot.generated_at,
    latest_scored: snapshot.latest_scored.map(
      ({ symbol, source_close_at, scored_at }) => ({
        symbol,
        source_close_at,
        scored_at,
      }),
    ),
  };
  console.log(JSON.stringify(result));
  return result;
}

if (process.argv[1]?.match(/check-forward-v2-endpoint\.(ts|cjs)$/)) {
  checkV2Endpoint(process.argv[2], process.argv[3], process.argv[4]).catch(
    () => {
      console.error(
        "V2 HTTPS check failed: inspect HTTP, contract, bytes, clocks and evidence privately.",
      );
      process.exitCode = 1;
    },
  );
}

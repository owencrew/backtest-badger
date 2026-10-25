import { fetchJson, requireValue, symbols, type Symbol } from "./market";
export const models = [
  "zero",
  "training_mean",
  "ridge",
  "gradient_boosting",
] as const;
export type Model = (typeof models)[number];
export const cohorts = [
  "primary_timely_automated",
  "secondary_late_manual",
  "timely_unattributed",
] as const;
export type Cohort = (typeof cohorts)[number];
export const protocolHash =
  "9bb655a374af27ecf41b0f31947dfad4256eb40e8973d53caf278507084d4bed";
export type Forecast = {
  symbol: Symbol;
  source_close_at: string;
  issued_at: string;
  target_close_at: string;
  recipe_sha256: string;
  cohort: Cohort;
  status: "pending_not_settled" | "mature_unscored" | "scored";
  scored_at: string | null;
  actual_log_return_4h: number | null;
  models: Record<
    Model,
    {
      predicted_log_return_4h: number;
      signed_error: number | null;
      absolute_error: number | null;
      squared_error: number | null;
    }
  >;
};
export type Evaluation = {
  symbol: Symbol;
  cohort: Cohort;
  first_target_close_at: string | null;
  genuine_predictions: number;
  matched_count: number;
  pending_not_settled: number;
  mature_unscored: number;
  missing_predictions: number | null;
  models: Record<
    Model,
    {
      mae: number | null;
      rmse: number | null;
      forecast_bias: number | null;
      directional_correct: number;
      directional_denominator: number;
      directional_accuracy: number | null;
    }
  >;
};
export type ForecastSnapshot = {
  schema_version: 1;
  kind: "public_forward_research";
  data_source: "Binance Spot";
  protocol: "stage-3c-v1";
  protocol_sha256: string;
  generated_at: string;
  as_of: string;
  latest: Forecast[];
  evaluations: Evaluation[];
};
type Obj = Record<string, unknown>;
function object(value: unknown, keys: string[]): Obj {
  requireValue(
    typeof value === "object" && value !== null && !Array.isArray(value),
    "Invalid forecast object.",
  );
  const result = value as Obj;
  requireValue(
    Object.keys(result).length === keys.length &&
      keys.every((key) => Object.hasOwn(result, key)),
    "Unexpected public forecast fields.",
  );
  return result;
}
export function timestamp(value: unknown): number {
  requireValue(
    typeof value === "string" &&
      /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z$/.test(value),
    "Forecast timestamps must use UTC Z.",
  );
  const ms = Date.parse(value);
  requireValue(
    Number.isFinite(ms) &&
      new Date(ms).toISOString().slice(0, 19) === value.slice(0, 19),
    "Invalid forecast timestamp.",
  );
  return ms;
}
function numeric(value: unknown): number {
  requireValue(
    typeof value === "number" && Number.isFinite(value),
    "Non-finite forecast metric.",
  );
  return value;
}
function count(value: unknown): number {
  const n = numeric(value);
  requireValue(
    Number.isSafeInteger(n) && n >= 0,
    "Invalid forecast sample count.",
  );
  return n;
}
function same(a: number, b: number) {
  return Math.abs(a - b) <= 1e-12 * Math.max(1, Math.abs(a), Math.abs(b));
}
function identity(row: Obj) {
  requireValue(
    symbols.includes(row.symbol as Symbol) &&
      cohorts.includes(row.cohort as Cohort),
    "Unknown forecast market/cohort.",
  );
}
const hour4 = 14_400_000;
export const FORECAST_STALE_MS = 20 * 60_000; // Snapshot publication, not forecast frequency.
export function validateForecast(
  value: unknown,
  now = Date.now(),
): ForecastSnapshot {
  const root = object(value, [
    "schema_version",
    "kind",
    "data_source",
    "protocol",
    "protocol_sha256",
    "generated_at",
    "as_of",
    "latest",
    "evaluations",
  ]);
  requireValue(
    root.schema_version === 1 &&
      root.kind === "public_forward_research" &&
      root.data_source === "Binance Spot" &&
      root.protocol === "stage-3c-v1" &&
      root.protocol_sha256 === protocolHash,
    "Unsupported forecast contract/protocol.",
  );
  const generated = timestamp(root.generated_at),
    asOf = timestamp(root.as_of);
  requireValue(
    asOf <= generated &&
      generated <= now + 60_000 &&
      generated - asOf <= 300_000,
    "Inconsistent forecast snapshot clocks.",
  );
  requireValue(
    Array.isArray(root.latest) &&
      root.latest.length <= 2 &&
      Array.isArray(root.evaluations) &&
      root.evaluations.length === 6,
    "Expected separate BTC/ETH evaluations for all three cohorts.",
  );
  const seen = new Set<string>();
  for (const item of root.latest) {
    const r = object(item, [
      "symbol",
      "source_close_at",
      "issued_at",
      "target_close_at",
      "recipe_sha256",
      "cohort",
      "status",
      "scored_at",
      "actual_log_return_4h",
      "models",
    ]);
    identity(r);
    requireValue(
      !seen.has(String(r.symbol)),
      "Duplicate latest market forecast.",
    );
    seen.add(String(r.symbol));
    requireValue(
      typeof r.recipe_sha256 === "string" &&
        /^[a-f0-9]{64}$/.test(r.recipe_sha256),
      "Invalid recipe fingerprint.",
    );
    const source = timestamp(r.source_close_at),
      issued = timestamp(r.issued_at),
      target = timestamp(r.target_close_at);
    requireValue(
      source % hour4 === 0 &&
        source >= Date.parse("2026-10-14T04:00:00Z") &&
        target === source + hour4 &&
        issued >= source + 60_000 &&
        issued < target &&
        issued <= asOf,
      "Invalid forward horizon or issuance.",
    );
    requireValue(
      (r.cohort === "secondary_late_manual") === issued >= source + 16 * 60_000,
      "Forecast timing conflicts with cohort.",
    );
    const scored = r.status === "scored";
    requireValue(
      scored ||
        r.status ===
          (asOf < target + 60_000 ? "pending_not_settled" : "mature_unscored"),
      "Invalid outcome maturity state.",
    );
    if (scored) {
      const captured = timestamp(r.scored_at);
      requireValue(
        captured >= target + 60_000 && captured <= asOf,
        "Outcome was not mature at scoring.",
      );
      numeric(r.actual_log_return_4h);
    } else
      requireValue(
        r.scored_at === null && r.actual_log_return_4h === null,
        "Pending forecast contains an outcome.",
      );
    const predictions = object(r.models, [...models]);
    for (const model of models) {
      const m = object(predictions[model], [
        "predicted_log_return_4h",
        "signed_error",
        "absolute_error",
        "squared_error",
      ]);
      const prediction = numeric(m.predicted_log_return_4h);
      requireValue(
        model !== "zero" || prediction === 0,
        "Invalid zero baseline.",
      );
      if (scored) {
        const error = prediction - numeric(r.actual_log_return_4h);
        requireValue(
          same(numeric(m.signed_error), error) &&
            same(numeric(m.absolute_error), Math.abs(error)) &&
            same(numeric(m.squared_error), error * error) &&
            numeric(m.absolute_error) >= 0 &&
            numeric(m.squared_error) >= 0,
          "Inconsistent saved forecast errors.",
        );
      } else
        requireValue(
          m.signed_error === null &&
            m.absolute_error === null &&
            m.squared_error === null,
          "Pending forecast contains errors.",
        );
    }
  }
  seen.clear();
  for (const item of root.evaluations) {
    const r = object(item, [
      "symbol",
      "cohort",
      "first_target_close_at",
      "genuine_predictions",
      "matched_count",
      "pending_not_settled",
      "mature_unscored",
      "missing_predictions",
      "models",
    ]);
    identity(r);
    const key = `${r.symbol}/${r.cohort}`;
    requireValue(!seen.has(key), "Duplicate evaluation cohort.");
    seen.add(key);
    const n = count(r.matched_count),
      genuine = count(r.genuine_predictions);
    requireValue(
      n + count(r.pending_not_settled) + count(r.mature_unscored) === genuine,
      "Inconsistent matched sample counts.",
    );
    if (r.missing_predictions !== null) {
      count(r.missing_predictions);
      requireValue(
        r.cohort === cohorts[0],
        "Missing opportunity grid belongs to primary cohort only.",
      );
    }
    if (genuine === 0)
      requireValue(
        r.first_target_close_at === null,
        "Empty sample has an evaluation period.",
      );
    else {
      const first = timestamp(r.first_target_close_at);
      requireValue(
        first % hour4 === 0 &&
          first >= Date.parse("2026-10-14T08:00:00Z") &&
          first < asOf + hour4,
        "Invalid evaluation period.",
      );
    }
    const metrics = object(r.models, [...models]);
    for (const model of models) {
      const m = object(metrics[model], [
        "mae",
        "rmse",
        "forecast_bias",
        "directional_correct",
        "directional_denominator",
        "directional_accuracy",
      ]);
      const correct = count(m.directional_correct),
        denominator = count(m.directional_denominator);
      requireValue(
        correct <= denominator &&
          denominator <= n &&
          (model !== "zero" || denominator === 0),
        "Inconsistent directional counts.",
      );
      if (denominator === 0)
        requireValue(
          m.directional_accuracy === null,
          "Undefined accuracy must be null.",
        );
      else
        requireValue(
          same(numeric(m.directional_accuracy), correct / denominator),
          "Inconsistent directional accuracy.",
        );
      if (n === 0)
        requireValue(
          m.mae === null && m.rmse === null && m.forecast_bias === null,
          "Empty sample has metrics.",
        );
      else
        requireValue(
          numeric(m.mae) >= 0 &&
            numeric(m.rmse) + 1e-12 >= numeric(m.mae) &&
            Math.abs(numeric(m.forecast_bias)) <= numeric(m.mae) + 1e-12,
          "Inconsistent forecast error summary.",
        );
    }
  }
  const snapshot = value as ForecastSnapshot;
  for (const latest of snapshot.latest) {
    const evaluation = snapshot.evaluations.find(
      (e) => e.symbol === latest.symbol && e.cohort === latest.cohort,
    )!;
    requireValue(
      evaluation.genuine_predictions > 0 &&
        timestamp(evaluation.first_target_close_at) <=
          timestamp(latest.target_close_at) &&
        (latest.status === "scored"
          ? evaluation.matched_count > 0
          : evaluation[latest.status] > 0),
      "Latest forecast is absent from its evaluation cohort.",
    );
  }
  for (const symbol of symbols) {
    const hasEvidence = snapshot.evaluations.some(
      (e) => e.symbol === symbol && e.genuine_predictions > 0,
    );
    requireValue(
      hasEvidence === snapshot.latest.some((f) => f.symbol === symbol),
      "Latest forecast coverage conflicts with evaluation evidence.",
    );
  }
  return snapshot;
}
export async function fetchForecast(url: string, signal: AbortSignal) {
  requireValue(
    (url.startsWith("/") && !url.startsWith("//")) ||
      new URL(url).protocol === "https:",
    "Forecast URL must be same-origin or HTTPS.",
  );
  return validateForecast(await fetchJson(url, signal));
}

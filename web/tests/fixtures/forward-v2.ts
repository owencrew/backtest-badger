// SYNTHETIC TEST DATA ONLY. Never connect this fixture to a running website.
import {
  models,
  type ScoredForecast,
  type ForecastSnapshot,
} from "../../lib/forecast";
import { syntheticSnapshot } from "./forward";

export function syntheticV2(): ForecastSnapshot & { schema_version: 2 } {
  const base = syntheticSnapshot();
  const scored = structuredClone(base.latest[0]) as ScoredForecast;
  scored.actual_direction = 1;
  for (const model of models)
    scored.models[model].directional_correct = model === "zero" ? null : true;
  const eth = structuredClone(scored);
  eth.symbol = "ETHUSDT";
  eth.actual_log_return_4h = -0.002;
  eth.actual_direction = -1;
  for (const model of models) {
    const p = model === "zero" ? 0 : model === "ridge" ? 0.0000002 : -0.001;
    const error = p - eth.actual_log_return_4h;
    eth.models[model] = {
      predicted_log_return_4h: p,
      signed_error: error,
      absolute_error: Math.abs(error),
      squared_error: error * error,
      directional_correct: p === 0 ? null : p < 0,
    };
  }
  const latest = [scored, eth].map((f) => {
    const pending = structuredClone(base.latest[0]);
    Object.assign(pending, {
      symbol: f.symbol,
      source_close_at: "2026-10-15T12:00:00Z",
      issued_at: "2026-10-15T12:01:00Z",
      target_close_at: "2026-10-15T16:00:00Z",
      status: "pending_not_settled",
      scored_at: null,
      actual_log_return_4h: null,
    });
    for (const model of models)
      Object.assign(pending.models[model], {
        signed_error: null,
        absolute_error: null,
        squared_error: null,
      });
    return pending;
  });
  for (const f of [scored, eth]) {
    const e = base.evaluations.find(
      (e) => e.symbol === f.symbol && e.cohort === f.cohort,
    )!;
    Object.assign(e, {
      genuine_predictions: 2,
      matched_count: 1,
      pending_not_settled: 1,
      first_target_close_at: f.target_close_at,
    });
    for (const m of models) {
      const p = f.models[m];
      e.models[m] = {
        mae: p.absolute_error,
        rmse: p.absolute_error,
        forecast_bias: p.signed_error,
        directional_correct: p.directional_correct ? 1 : 0,
        directional_denominator: p.directional_correct === null ? 0 : 1,
        directional_accuracy:
          p.directional_correct === null ? null : p.directional_correct ? 1 : 0,
      };
    }
  }
  return { ...base, schema_version: 2, latest, latest_scored: [scored, eth] };
}

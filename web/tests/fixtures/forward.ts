// SYNTHETIC UNIT-TEST FIXTURE ONLY. Never imported by application code or published.
import {
  cohorts,
  models,
  protocolHash,
  type ForecastSnapshot,
  type Forecast,
  type Evaluation,
} from "../../lib/forecast";
import { symbols } from "../../lib/market";
export function syntheticSnapshot(): ForecastSnapshot {
  return {
    schema_version: 1,
    kind: "public_forward_research",
    data_source: "Binance Spot",
    protocol: "stage-3c-v1",
    protocol_sha256: protocolHash,
    generated_at: "2026-10-15T13:00:00Z",
    as_of: "2026-10-15T13:00:00Z",
    latest: [
      {
        symbol: "BTCUSDT",
        source_close_at: "2026-10-15T04:00:00Z",
        issued_at: "2026-10-15T04:01:00Z",
        target_close_at: "2026-10-15T08:00:00Z",
        recipe_sha256: "a".repeat(64),
        cohort: "primary_timely_automated",
        status: "scored",
        scored_at: "2026-10-15T08:02:00Z",
        actual_log_return_4h: 0.005,
        models: Object.fromEntries(
          models.map((m) => {
            const p = m === "zero" ? 0 : 0.01;
            return [
              m,
              {
                predicted_log_return_4h: p,
                signed_error: p - 0.005,
                absolute_error: 0.005,
                squared_error: 0.000025,
              },
            ];
          }),
        ) as Forecast["models"],
      },
    ],
    evaluations: symbols.flatMap((symbol) =>
      cohorts.map((cohort): Evaluation => {
        const n =
          symbol === "BTCUSDT" && cohort === "primary_timely_automated" ? 1 : 0;
        return {
          symbol,
          cohort,
          first_target_close_at: n ? "2026-10-15T08:00:00Z" : null,
          genuine_predictions: n,
          matched_count: n,
          pending_not_settled: 0,
          mature_unscored: 0,
          missing_predictions: null,
          models: Object.fromEntries(
            models.map((m) => [
              m,
              {
                mae: n ? 0.005 : null,
                rmse: n ? 0.005 : null,
                forecast_bias: n ? (m === "zero" ? -0.005 : 0.005) : null,
                directional_correct: m === "zero" ? 0 : n,
                directional_denominator: m === "zero" ? 0 : n,
                directional_accuracy: n && m !== "zero" ? 1 : null,
              },
            ]),
          ) as Evaluation["models"],
        };
      }),
    ),
  };
}

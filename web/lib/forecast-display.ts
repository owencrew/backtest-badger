import type { Evaluation, Model } from "./forecast";

export const modelNames: Record<Model, string> = {
  zero: "Zero",
  training_mean: "Training mean",
  ridge: "Ridge",
  gradient_boosting: "Gradient boosting",
};

// Presentation only: keep the validated snapshot and logarithmic units intact.
export function logReturnBps(value: number | null | undefined): string {
  if (value == null) return "N/A — no matched outcomes";
  if (value === 0) return "0.00 bps";
  const magnitude = Math.abs(value * 10_000);
  // Never round a small nonzero forecast to zero; retain three significant digits.
  const digits =
    magnitude < 0.01 ? magnitude.toExponential(2) : magnitude.toFixed(2);
  return `${value < 0 ? "−" : "+"}${digits} bps`;
}

export function directionAccuracy(
  model: Model,
  metrics: Evaluation["models"][Model],
): string {
  if (metrics.directional_accuracy == null)
    return model === "zero"
      ? "N/A — zero forecast"
      : "N/A — no eligible directions";
  return `${(metrics.directional_accuracy * 100).toFixed(1)}%`;
}

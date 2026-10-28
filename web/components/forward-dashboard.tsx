"use client";
import { useMemo } from "react";
import {
  createForecastLoader,
  forecastIsStale,
  forecastStatus,
  type ForecastSnapshot,
  models,
  type Cohort,
} from "@/lib/forecast";
import { utc } from "@/lib/market";
import { useFeed } from "./use-feed";
import { EmptyState } from "./ui";
const cohortNames: Record<Cohort, string> = {
  primary_timely_automated: "Timely automated",
  secondary_late_manual: "Late manual",
  timely_unattributed: "Timely · automation unattributed",
};
const metric = (value: number | null) =>
  value === null ? "Undefined" : value.toPrecision(5);
function ConnectedForecasts({ url }: { url: string }) {
  const loader = useMemo(() => createForecastLoader(url), [url]);
  const { data, error, loading, checkedAt, refresh } = useFeed(loader);
  const stale = data && (forecastIsStale(data, checkedAt) || !!error);
  return (
    <>
      <div className="section-heading">
        <h3>
          {loading
            ? "Checking published snapshot…"
            : stale
              ? "Snapshot stale · retained for reference"
              : "Published forward evidence"}
        </h3>
        <button
          className="button button-secondary"
          disabled={loading}
          onClick={refresh}
        >
          Refresh forecasts
        </button>
      </div>
      {error && (
        <p className="feed-error" role="alert">
          Forecast feed unavailable: {error}{" "}
          {data && "Retained values below have not been updated."}
        </p>
      )}
      {!data ? (
        <EmptyState title="No verified snapshot loaded">
          Forecasts and accuracy remain unavailable until a valid public export
          can be retrieved.
        </EmptyState>
      ) : (
        <ForecastEvidence data={data} checkedAt={checkedAt} />
      )}
    </>
  );
}

export function ForecastEvidence({
  data,
  checkedAt,
}: {
  data: ForecastSnapshot;
  checkedAt: number;
}) {
  return (
    <>
      <p className="small muted">
        Binance Spot · Evidence cutoff {utc(Date.parse(data.as_of))}
        <br />
        Latest published snapshot generated {utc(Date.parse(data.generated_at))}
        . Publication freshness is separate from the four-hour forecast cycle.
      </p>
      <div className="overview-grid">
        {data.latest.map((f) => (
          <article key={f.symbol} className="overview-card">
            <p className="eyebrow">
              {f.symbol} · {cohortNames[f.cohort]}
            </p>
            <h3>{forecastStatus(f, checkedAt)}</h3>
            <p className="small">
              Source close {utc(Date.parse(f.source_close_at))}
              <br />
              Issued {utc(Date.parse(f.issued_at))}
              <br />
              Target close {utc(Date.parse(f.target_close_at))}
            </p>
            <p className="small muted">
              Next four-hour predicted log return (dimensionless)
            </p>
            <dl className="forecast-values">
              {models.map((m) => (
                <div key={m}>
                  <dt>{m.replaceAll("_", " ")}</dt>
                  <dd>
                    {metric(f.models[m].predicted_log_return_4h)}{" "}
                    <span className="muted">log return</span>
                    {f.status === "scored" && (
                      <small>
                        Signed error {metric(f.models[m].signed_error)}
                      </small>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
            <p className="small">
              Realised log return:{" "}
              {f.actual_log_return_4h === null
                ? "Not scored"
                : metric(f.actual_log_return_4h)}
            </p>
            <details>
              <summary>Model recipe identity</summary>
              <p className="small hash-value">{f.recipe_sha256}</p>
              {f.scored_at && (
                <p className="small">Scored {utc(Date.parse(f.scored_at))}</p>
              )}
            </details>
          </article>
        ))}
      </div>
      {data.latest.length === 0 && <p>No forecast observations published.</p>}
      <h3 className="section-block">
        Historical prediction accuracy · forward observations
      </h3>
      {data.evaluations.map((e) => (
        <div key={`${e.symbol}/${e.cohort}`} className="evaluation-cohort">
          <h4>
            {e.symbol} · {cohortNames[e.cohort]}
          </h4>
          <p className="small">
            {e.matched_count < 100
              ? "Preliminary: fewer than 100 matched observations."
              : "Descriptive only; no statistical significance is implied."}{" "}
            All four models share {e.matched_count} matched observations.
          </p>
          <p className="small muted">
            {e.genuine_predictions} issued · {e.pending_not_settled} unsettled
            at cutoff · {e.mature_unscored} mature, unscored · Missing primary
            opportunities: {e.missing_predictions ?? "undefined"}.<br />
            First target close:{" "}
            {e.first_target_close_at
              ? utc(Date.parse(e.first_target_close_at))
              : "none"}{" "}
            · Cutoff: {utc(Date.parse(data.as_of))}
          </p>
          <div
            className="table-wrap"
            tabIndex={0}
            role="region"
            aria-label={`${e.symbol} ${cohortNames[e.cohort]} errors; scroll on small screens`}
          >
            <table className="comparison-table">
              <caption>
                Forecast errors in dimensionless log-return units; direction
                uses strict sign
              </caption>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>MAE</th>
                  <th>RMSE</th>
                  <th>Bias</th>
                  <th>Direction correct / eligible</th>
                  <th>Accuracy</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m}>
                    <th scope="row">{m.replaceAll("_", " ")}</th>
                    <td>{metric(e.models[m].mae)}</td>
                    <td>{metric(e.models[m].rmse)}</td>
                    <td>{metric(e.models[m].forecast_bias)}</td>
                    <td>
                      {e.models[m].directional_correct} /{" "}
                      {e.models[m].directional_denominator}
                    </td>
                    <td>
                      {e.models[m].directional_accuracy === null
                        ? "Undefined"
                        : `${(e.models[m].directional_accuracy! * 100).toFixed(1)}%`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </>
  );
}

export function ForwardDashboard() {
  const url = process.env.NEXT_PUBLIC_FORWARD_SNAPSHOT_URL;
  return (
    <section className="section-block forward-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">A separate stream of evidence</p>
          <h2>Forecasts, then outcomes</h2>
        </div>
      </div>
      <p>
        Forecasts estimate the next native four-hour candle’s close-to-close log
        return, ln(next close / source close). The reference interval starts
        before issuance. These are predictions, not observed prices, trade
        recommendations or portfolio returns.
      </p>
      {url ? (
        <ConnectedForecasts url={url} />
      ) : (
        <EmptyState title="Forward forecasts are not published yet">
          The Lightsail research system records forecasts and scores their
          outcomes. A reviewed public snapshot is not connected here, so current
          forecasts and accuracy are unavailable. Market prices above are
          independently fetched from Binance.
        </EmptyState>
      )}
      <div className="cohort-labels">
        <span>Timely automated</span>
        <span>Late manual</span>
        <span>Timely unattributed</span>
      </div>
      <p className="small muted">
        Cohorts remain separate. Late forecasts observe more of the target
        interval. Accuracy excludes unscored outcomes; missingness can bias
        comparisons. Zero forecasts abstain from directional accuracy.
        Evaluation pools retained recipe identities within each cohort; the
        latest recipe is shown above. No model ranking or claim of
        profitability.
      </p>
    </section>
  );
}

"use client";
import { useMemo } from "react";
import {
  createForecastLoader,
  forecastIsStale,
  forecastStatus,
  type ForecastSnapshot,
  type Evaluation,
  models,
  type Cohort,
} from "@/lib/forecast";
import {
  directionAccuracy,
  logReturnBps,
  modelNames,
} from "@/lib/forecast-display";
import { utc } from "@/lib/market";
import { useFeed } from "./use-feed";
import { EmptyState } from "./ui";
const cohortNames: Record<Cohort, string> = {
  primary_timely_automated: "Timely automated",
  secondary_late_manual: "Late manual",
  timely_unattributed: "Timely · automation unattributed",
};
function ConnectedForecasts({ url }: { url: string }) {
  const loader = useMemo(() => createForecastLoader(url), [url]);
  const feed = useFeed(loader);
  return <ForecastFeedView {...feed} />;
}

// Keep network state separate from evidence so retained snapshots stay inspectable.
export function ForecastFeedView({
  data,
  error,
  loading,
  checkedAt,
  refresh,
}: {
  data?: ForecastSnapshot;
  error?: string;
  loading: boolean;
  checkedAt: number;
  refresh: () => void;
}) {
  return (
    <>
      <div className="section-heading forecast-feed-heading">
        <h3 role="status">
          {loading
            ? "Checking published snapshot…"
            : error
              ? data
                ? "Request failed · last-good snapshot retained"
                : "Forecast feed unavailable"
              : data && forecastIsStale(data, checkedAt)
                ? "Snapshot stale · retained for reference"
                : data
                  ? "Fresh published snapshot"
                  : "No verified snapshot loaded"}
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
        <ForecastEvidence
          data={data}
          checkedAt={checkedAt}
          retained={!!error}
        />
      )}
    </>
  );
}

function EvaluationResults({ evaluation: e }: { evaluation: Evaluation }) {
  return (
    <section
      className="evaluation-cohort"
      aria-label={`${e.symbol} ${cohortNames[e.cohort]} evaluation`}
    >
      <h4>
        {e.symbol} <span className="muted">· {cohortNames[e.cohort]}</span>
      </h4>
      <p className="evaluation-count">
        <strong>{e.matched_count} matched</strong> / {e.genuine_predictions}{" "}
        issued observations
      </p>
      {e.matched_count === 0 ? (
        <div className="cohort-empty">
          <p>
            {e.genuine_predictions === 0
              ? "No observations recorded in this cohort."
              : "No matched outcomes recorded in this cohort."}
          </p>
          <p className="small muted">
            Evaluation metrics cannot be calculated without matched outcomes.
          </p>
        </div>
      ) : (
        <>
          <p className="small muted">
            {e.matched_count < 100
              ? "Preliminary: fewer than 100 matched observations. Percentages from small samples can change sharply with one outcome."
              : "Descriptive only; no statistical significance is implied."}
          </p>
          <p className="small muted table-scroll-hint">
            Scroll horizontally for all metrics. Keyboard: focus the table, then
            use the arrow keys.
          </p>
          <div
            className="table-wrap"
            tabIndex={0}
            role="region"
            aria-label={`${e.symbol} ${cohortNames[e.cohort]} errors; scroll on small screens`}
          >
            <table className="comparison-table">
              <caption>{e.symbol} forecast errors · log-return bps</caption>
              <thead>
                <tr>
                  <th scope="col">Model</th>
                  <th scope="col">MAE (bps)</th>
                  <th scope="col">RMSE (bps)</th>
                  <th scope="col">Forecast bias (bps)</th>
                  <th scope="col">Direction correct / eligible</th>
                  <th scope="col">Directional accuracy</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m}>
                    <th scope="row">{modelNames[m]}</th>
                    <td>{logReturnBps(e.models[m].mae)}</td>
                    <td>{logReturnBps(e.models[m].rmse)}</td>
                    <td>{logReturnBps(e.models[m].forecast_bias)}</td>
                    <td>
                      {e.models[m].directional_correct} /{" "}
                      {e.models[m].directional_denominator}
                    </td>
                    <td>{directionAccuracy(m, e.models[m])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

export function ForecastEvidence({
  data,
  checkedAt,
  retained = false,
}: {
  data: ForecastSnapshot;
  checkedAt: number;
  retained?: boolean;
}) {
  const primary = data.evaluations.filter(
    (e) => e.cohort === "primary_timely_automated",
  );
  const late = data.evaluations.filter(
    (e) => e.cohort === "secondary_late_manual",
  );
  const unattributed = data.evaluations.filter(
    (e) => e.cohort === "timely_unattributed",
  );
  const freshness = retained
    ? "Last-good snapshot · refresh failed"
    : forecastIsStale(data, checkedAt)
      ? "Stale published snapshot"
      : "Fresh published snapshot";
  return (
    <>
      <p className="small muted snapshot-clocks">
        Binance Spot · Evidence cutoff {utc(Date.parse(data.as_of))}
        <br />
        Snapshot generated {utc(Date.parse(data.generated_at))}. Publication
        freshness is separate from the four-hour forecast cycle.
      </p>
      <h3 className="forecast-section-title">Latest predictions</h3>
      <p className="small muted">
        One basis point corresponds to 0.0001 log-return units. Values below are
        log returns × 10,000, not simple percentage returns.
      </p>
      <div className="forecast-grid">
        {data.latest.map((f) => (
          <article
            key={f.symbol}
            className="forecast-card"
            aria-label={`${f.symbol} latest prediction`}
          >
            <div className="forecast-card-heading">
              <h4>{f.symbol}</h4>
              <span className="forecast-status">
                {forecastStatus(f, checkedAt)}
              </span>
            </div>
            <p className="small muted">
              {cohortNames[f.cohort]} · {freshness}
            </p>
            <dl className="forecast-times">
              <div>
                <dt>Target close</dt>
                <dd>{utc(Date.parse(f.target_close_at))}</dd>
              </div>
              <div>
                <dt>Source candle close</dt>
                <dd>{utc(Date.parse(f.source_close_at))}</dd>
              </div>
              <div>
                <dt>Forecast issued</dt>
                <dd>{utc(Date.parse(f.issued_at))}</dd>
              </div>
            </dl>
            <p className="forecast-unit">
              Four-hour predicted log return (bps)
            </p>
            <dl className="forecast-values">
              {models.map((m) => (
                <div key={m}>
                  <dt>{modelNames[m]}</dt>
                  <dd>
                    {logReturnBps(f.models[m].predicted_log_return_4h)}
                    {f.status === "scored" && (
                      <small>
                        Signed error {logReturnBps(f.models[m].signed_error)}
                      </small>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
            <p className="forecast-outcome">
              Realised log return{" "}
              <strong>
                {f.status === "scored"
                  ? logReturnBps(f.actual_log_return_4h)
                  : "Not scored"}
              </strong>
            </p>
            <details className="forecast-technical">
              <summary>Forecast technical details</summary>
              <p className="small">Model recipe identity (SHA-256)</p>
              <p className="small hash-value">{f.recipe_sha256}</p>
              {f.scored_at && (
                <p className="small">Scored {utc(Date.parse(f.scored_at))}</p>
              )}
              <p className="small muted">
                Original log-return values, saved errors and exact UTC
                timestamps. Squared error remains in squared log-return units.
              </p>
              <pre
                className="forecast-json"
                tabIndex={0}
                aria-label={`${f.symbol} original forecast values`}
              >
                {JSON.stringify(f, null, 2)}
              </pre>
            </details>
          </article>
        ))}
      </div>
      {data.latest.length === 0 && <p>No forecast observations published.</p>}
      <section
        className="primary-evaluation"
        aria-labelledby="primary-evaluation-title"
      >
        <p className="eyebrow">Primary evidence</p>
        <h3 id="primary-evaluation-title">Timely automated evaluation</h3>
        <p className="small muted">
          All four models use the same matched observations within each market
          and cohort. These descriptive results do not establish statistical
          significance or trading profitability.
        </p>
        <p className="small muted">
          Direction uses the frozen strict-sign protocol. The Zero model has no
          eligible directional predictions: its denominator is zero (0 / 0), so
          accuracy is N/A — zero forecast, never 0%.
        </p>
        {primary.map((e) => (
          <EvaluationResults key={e.symbol} evaluation={e} />
        ))}
      </section>
      <details className="forecast-disclosure">
        <summary>
          Late manual forecasts{" "}
          <span className="disclosure-count">
            {late
              .map(
                (e) =>
                  `${e.symbol}: ${e.matched_count} matched / ${e.genuine_predictions} issued`,
              )
              .join(" · ")}
          </span>
        </summary>
        <p className="small">
          Late forecasts are not directly comparable with timely automated
          predictions: additional information timing can benefit them because
          they observe more of the target interval. These observations are never
          pooled with primary forecasts.
        </p>
        {late.map((e) => (
          <EvaluationResults key={e.symbol} evaluation={e} />
        ))}
      </details>
      <details className="forecast-disclosure">
        <summary>Detailed forecast evaluation</summary>
        <h3>Methodology and evidence coverage</h3>
        <p className="small">
          Forecasts estimate ln(next close / source close) over the next native
          four-hour candle. The reference interval starts before issuance. MAE
          and RMSE measure error magnitude; forecast bias and signed error use
          prediction minus realised outcome. Displayed errors use log-return
          bps.
        </p>
        <p className="small">
          Accuracy excludes unscored outcomes; missingness can bias comparisons.
          Direction uses strict signs: zero predictions abstain. Nonzero
          predictions against a zero outcome remain eligible and count as
          incorrect. Each cohort remains separate. Evaluation pools retained
          recipe identities within each cohort; the latest recipe identity does
          not identify every historical model in that pool. No model ranking is
          implied.
        </p>
        <p className="small muted">
          Evidence cutoff {utc(Date.parse(data.as_of))} · Generated{" "}
          {utc(Date.parse(data.generated_at))}. A successful HTTP refresh does
          not issue a new forecast. Counts below describe the snapshot cutoff.
        </p>
        <p className="small muted table-scroll-hint">
          Scroll horizontally for all counts. Keyboard: focus the table, then
          use the arrow keys.
        </p>
        <div
          className="table-wrap"
          tabIndex={0}
          role="region"
          aria-label="All cohort observation counts; scroll on small screens"
        >
          <table className="comparison-table">
            <caption>All cohorts · observation accounting</caption>
            <thead>
              <tr>
                {[
                  "Market / cohort",
                  "Issued",
                  "Matched",
                  "Pending / unsettled",
                  "Mature unscored",
                  "Missing primary opportunities",
                  "Earliest target close (UTC)",
                ].map((label) => (
                  <th scope="col" key={label}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.evaluations.map((e) => (
                <tr key={`${e.symbol}/${e.cohort}`}>
                  <th scope="row">
                    {e.symbol} · {cohortNames[e.cohort]}
                  </th>
                  <td>{e.genuine_predictions}</td>
                  <td>{e.matched_count}</td>
                  <td>{e.pending_not_settled}</td>
                  <td>{e.mature_unscored}</td>
                  <td>
                    {e.missing_predictions ??
                      (e.cohort === "primary_timely_automated"
                        ? "Not available"
                        : "Not applicable")}
                  </td>
                  <td>
                    {e.first_target_close_at
                      ? utc(Date.parse(e.first_target_close_at))
                      : "None recorded"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h3>Timely unattributed evaluation</h3>
        <p className="small muted">
          Timely forecasts without attributed automation remain separate from
          the primary cohort.
        </p>
        {unattributed.map((e) => (
          <EvaluationResults key={e.symbol} evaluation={e} />
        ))}
        <details className="forecast-technical">
          <summary>Original snapshot values · all cohorts and models</summary>
          <p className="small muted">
            Validated public data in original decimal log-return units,
            including all metrics, model identities and exact timestamps. No
            presentation conversion is applied here.
          </p>
          <pre
            className="forecast-json"
            tabIndex={0}
            aria-label="Original validated public snapshot"
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        </details>
      </details>
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
        Four-hour forecasts, followed by observed outcomes. These are
        predictions, not observed prices, trade recommendations or portfolio
        returns.
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
    </section>
  );
}

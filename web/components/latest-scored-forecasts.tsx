import { models, type ForecastSnapshot } from "@/lib/forecast";
import {
  directionOutcome,
  logReturnBps,
  modelNames,
} from "@/lib/forecast-display";
import { symbols, utc } from "@/lib/market";

export function LatestScoredForecasts({ data }: { data: ForecastSnapshot }) {
  return (
    <section aria-labelledby="latest-scored-title">
      <h3 className="forecast-section-title" id="latest-scored-title">
        Latest scored forecasts
      </h3>
      <p className="small muted">
        The most recent completed timely automated forecast for each market.
        These can predate the latest predictions above. One outcome does not
        establish model superiority or profitability; forecast errors are not
        portfolio returns.
      </p>
      {data.schema_version === 1 ? (
        <p className="small muted">
          Latest scored forecasts are unavailable in this version-1 snapshot.
        </p>
      ) : (
        <div className="forecast-grid">
          {symbols.map((symbol) => {
            const f = data.latest_scored.find((row) => row.symbol === symbol);
            return (
              <article
                key={symbol}
                className="forecast-card"
                aria-label={`${symbol} latest scored forecast`}
              >
                <div className="forecast-card-heading">
                  <h4>{symbol}</h4>
                  <span className="forecast-status">
                    {f ? "Outcome scored" : "Awaiting completed evidence"}
                  </span>
                </div>
                {!f ? (
                  <p>No completed timely forecast available yet.</p>
                ) : (
                  <>
                    <p className="small muted">
                      Timely automated · Original prediction and saved outcome
                    </p>
                    <dl className="forecast-times">
                      {[
                        ["Target close", f.target_close_at],
                        ["Source candle close", f.source_close_at],
                        ["Forecast issued", f.issued_at],
                        ["Outcome scored", f.scored_at],
                      ].map(([label, time]) => (
                        <div key={label}>
                          <dt>{label}</dt>
                          <dd>{utc(Date.parse(time))}</dd>
                        </div>
                      ))}
                    </dl>
                    <p className="forecast-outcome scored-actual">
                      Observed four-hour log return{" "}
                      <strong>{logReturnBps(f.actual_log_return_4h)}</strong>
                    </p>
                    <p className="small muted">
                      All values in log-return bps. Signed error = predicted −
                      actual.
                    </p>
                    <div className="scored-models">
                      {models.map((model) => {
                        const p = f.models[model];
                        return (
                          <section
                            className="scored-model"
                            key={model}
                            aria-label={`${symbol} ${modelNames[model]} comparison`}
                          >
                            <div className="scored-model-heading">
                              <h5>{modelNames[model]}</h5>
                              <span className="small">
                                Direction:{" "}
                                <strong>
                                  {directionOutcome(p.directional_correct)}
                                </strong>
                              </span>
                            </div>
                            <dl className="scored-values">
                              <div>
                                <dt>Predicted</dt>
                                <dd>
                                  {logReturnBps(p.predicted_log_return_4h)}
                                </dd>
                              </div>
                              <div>
                                <dt>Signed error</dt>
                                <dd>{logReturnBps(p.signed_error)}</dd>
                              </div>
                              <div>
                                <dt>Absolute error</dt>
                                <dd>{logReturnBps(p.absolute_error)}</dd>
                              </div>
                            </dl>
                          </section>
                        );
                      })}
                    </div>
                    <p className="small muted">
                      N/A means the prediction was exactly zero and abstained.
                      Direction uses the saved strict-sign result.
                    </p>
                    <details className="forecast-technical">
                      <summary>Scored forecast technical details</summary>
                      <p className="small">Model recipe identity (SHA-256)</p>
                      <p className="small hash-value">{f.recipe_sha256}</p>
                      <p className="small muted">
                        Original decimal log returns, saved errors, direction
                        and exact UTC timestamps. Squared errors remain in
                        squared log-return units.
                      </p>
                      <pre
                        className="forecast-json"
                        tabIndex={0}
                        aria-label={`${symbol} original scored forecast values`}
                      >
                        {JSON.stringify(f, null, 2)}
                      </pre>
                    </details>
                  </>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

"use client";
import { useState } from "react";

export function BadgerTrail() {
  const [running, setRunning] = useState(false);
  return (
    <div className="trail-preview">
      <div>
        <p className="eyebrow">From the sketchbook · Motion study</p>
        <h3>Following the trail backward.</h3>
        <p>
          A little nod to a future backtest runner. This abstract path is
          decorative; no research is running.
        </p>
        <button
          className="button button-secondary"
          onClick={() => setRunning(!running)}
        >
          {running ? "Reset motion preview" : "Play motion preview"}
          <span aria-hidden="true">{running ? "↺" : "↖"}</span>
        </button>
        <p className="small muted">
          Reduced-motion preference keeps the badge still.
        </p>
      </div>
      <div className="trail-scene" aria-hidden="true">
        <svg viewBox="0 0 400 130">
          <path d="M25 100C80 110 90 40 150 70S230 130 270 55S340 20 375 35" />
          <g className={`trail-badger ${running ? "trail-running" : ""}`}>
            <image
              href="/brand/badger-mark.svg"
              width="36"
              height="36"
              x="-18"
              y="-18"
            />
          </g>
        </svg>
        <span className="trail-label">ABSTRACT PATH / DESIGN PREVIEW</span>
      </div>
    </div>
  );
}

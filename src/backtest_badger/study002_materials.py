"""Build unpublished review data/charts from verified retained evidence only.

Matplotlib is an optional authoring tool, not a research/runtime dependency.
Use a separate temporary installation as documented in the Study 002 report.
"""

import argparse
import html
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from backtest_badger import local_historical_backtest as local
from backtest_badger import study002 as study
from backtest_badger import study002_runner as runner

NAMES = {
    study.STRATEGY: "30-Day Trend",
    "ridge": "Ridge Sign",
    "cash": "Cash",
    "buy_and_hold": "Buy & Hold",
}
COLORS = {
    study.STRATEGY: "#315943",
    "ridge": "#b45d54",
    "cash": "#82908d",
    "buy_and_hold": "#b59a68",
}


def create(run_dir, reference_dir, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import numpy as np

    marker = runner.verify_output(run_dir)
    old = runner.reference(reference_dir)
    summary = json.loads((run_dir / "summary.json").read_bytes())
    evidence = json.loads((run_dir / "private/evidence.json").read_bytes())
    runner.validate_evidence(summary, evidence, old)
    old_evidence = json.loads((reference_dir / "private/evidence.json").read_bytes())
    output.mkdir(parents=True, exist_ok=False)
    source_hash = marker["files"]["private/evidence.json"]["sha256"]
    source = {
        "study002_run": run_dir.name,
        "study002_evidence_sha256": source_hash,
        "study002_summary_sha256": marker["files"]["summary.json"]["sha256"],
        "study001_evidence_sha256": runner.REFERENCE_FILES["private/evidence.json"][
            "sha256"
        ],
        "study001_summary_sha256": runner.REFERENCE_FILES["summary.json"]["sha256"],
        "methodology": "../study-002-methodology.md",
        "report": "../study-002-slower-trend-results.md",
    }
    accounts = {}
    details = {}
    for result in evidence["results"]:
        for account in result["accounts"]:
            accounts[(result["symbol"], account["label"])] = account
    for result in old_evidence["results"]:
        accounts[(result["symbol"], "ridge")] = result["accounts"][0]
    for r in evidence["reports"] + old_evidence["reports"]:
        k = r["summary"]["symbol"], r["summary"]["label"]
        if k not in details:
            details[k] = r["summary"]
    rows = list(summary["accounts"])
    for original in old["accounts"]:
        if original["label"] != "ridge":
            continue
        symbol = original["symbol"]
        account = accounts[(symbol, "ridge")]
        result = next(r for r in old_evidence["results"] if r["symbol"] == symbol)
        report = details[(symbol, "ridge")]
        costs = original["costs_by_side"]
        totals = {
            key: str(sum(Decimal(v[key]) for v in costs.values()))
            for key in (
                "notional",
                "fees",
                "hypothetical_half_spread",
                "hypothetical_slippage",
            )
        }
        totals["total_attributed_costs"] = str(
            sum(
                Decimal(totals[k])
                for k in ("fees", "hypothetical_half_spread", "hypothetical_slippage")
            )
        )
        totals["turnover_initial_funding"] = str(Decimal(totals["notional"]) / 10000)
        complete = [
            p
            for p in report["observations"]
            if p["period"] == "daily" and p["complete"]
        ]
        rows.append(
            {
                **original,
                "initial_funding": "10000",
                "historical_reference": True,
                "first_mark_equity": account["marks"][0]["equity"],
                "final_mark_equity": account["marks"][-1]["equity"],
                "final_cash": account["final"]["cash"],
                "final_quantity": account["final"]["quantity"],
                "final_basis": account["final"]["basis"],
                "realised": account["final"]["realised"],
                "unrealised": account["marks"][-1]["unrealised"],
                "totals": totals,
                "signal_evaluations": len(result["decisions"]),
                "position_changes": len(account["fills"]),
                "hold_count": sum(d["action"] == "HOLD" for d in result["decisions"]),
                "cash_noop_count": sum(
                    d["action"] == "CASH_NOOP" for d in result["decisions"]
                ),
                "best_complete_day": max(complete, key=lambda p: Decimal(p["return"]))[
                    "start"
                ],
                "worst_complete_day": min(complete, key=lambda p: Decimal(p["return"]))[
                    "start"
                ],
                "extreme_day_tie_policy": "earliest UTC day",
            }
        )
    monthly = []
    for (symbol, label), report in details.items():
        for p in report["observations"]:
            if p["period"] == "monthly":
                monthly.append(
                    {
                        "symbol": symbol,
                        "strategy": label,
                        "start": p["start"],
                        "end": p["end"],
                        "complete": p["complete"],
                        "return": p["return"],
                        "costs_by_side": p["costs_by_side"],
                    }
                )
    data = {
        "schema": "study-002-review-v1",
        "publication_status": "unapproved_draft",
        "classification": "exploratory_retrospective_historical_simulation",
        "source": source,
        "accounts": rows,
        "monthly": monthly,
        "units": {
            "money": "USDT",
            "returns": "dimensionless fraction",
            "base_quantity": "BTC or ETH",
            "exposure": "seconds",
        },
        "chart_files": [
            f"{n}.png"
            for n in ("equity", "drawdown", "exposure", "activity", "costs", "monthly")
        ],
    }
    (output / "review-data.json").write_bytes(local._bytes(data))
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.18,
            "figure.facecolor": "#f4f1ea",
            "axes.facecolor": "#f4f1ea",
        }
    )
    for kind in ("equity", "drawdown", "exposure", "activity", "costs", "monthly"):
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        title = {
            "equity": "Portfolio equity after costs",
            "drawdown": "Drawdown from funding / observed hourly peaks",
            "exposure": "Trend position at hourly marks",
            "activity": "Monthly hypothetical executions",
            "costs": "Attributed transaction costs",
            "monthly": "Monthly mark-to-mark returns",
        }[kind]
        for ax, symbol in zip(axes, study.minute.SYMBOLS, strict=True):
            ax.set_title(symbol, loc="left", fontweight="bold")
            labels = (study.STRATEGY, "ridge", "cash", "buy_and_hold")
            if kind in ("equity", "drawdown", "exposure"):
                for label in labels if kind != "exposure" else (study.STRATEGY,):
                    account = accounts[(symbol, label)]
                    dates = [
                        datetime.fromisoformat(m["reference"]["at"])
                        for m in account["marks"]
                    ]
                    values = np.array([float(m["equity"]) for m in account["marks"]])
                    if kind == "drawdown":
                        peaks = np.maximum.accumulate(np.r_[10000, values])[1:]
                        values = (values / peaks - 1) * 100
                    if kind == "exposure":
                        values = [
                            int(Decimal(m["quantity"]) > 0) for m in account["marks"]
                        ]
                        ax.step(
                            dates,
                            values,
                            where="post",
                            color=COLORS[label],
                            label=NAMES[label],
                            linewidth=1,
                        )
                        ax.set_yticks([0, 1], ["Cash", "Long"])
                    else:
                        ax.plot(
                            dates,
                            values,
                            color=COLORS[label],
                            label=NAMES[label],
                            linewidth=1,
                        )
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
                ax.set_ylabel(
                    "USDT"
                    if kind == "equity"
                    else "% below peak"
                    if kind == "drawdown"
                    else "Position"
                )
                ax.set_xlabel("2024 · UTC · final mark 31 Dec 23:00")
            elif kind in ("activity", "monthly"):
                xs = np.arange(12)
                plotted = (
                    (study.STRATEGY, "ridge")
                    if kind == "activity"
                    else (study.STRATEGY, "ridge", "buy_and_hold")
                )
                for i, label in enumerate(plotted):
                    months = [
                        p
                        for p in details[(symbol, label)]["observations"]
                        if p["period"] == "monthly"
                    ]
                    values = [
                        sum(v["count"] for v in p["costs_by_side"].values())
                        if kind == "activity"
                        else float(p["return"]) * 100
                        for p in months
                    ]
                    ax.bar(
                        xs + (i - (len(plotted) - 1) / 2) * 0.25,
                        values,
                        width=0.25,
                        color=COLORS[label],
                        label=NAMES[label],
                    )
                ax.set_xticks(
                    xs,
                    [
                        "Jan",
                        "Feb",
                        "Mar",
                        "Apr",
                        "May",
                        "Jun",
                        "Jul",
                        "Aug",
                        "Sep",
                        "Oct",
                        "Nov",
                        "Dec*",
                    ],
                )
                ax.set_ylabel(
                    "Buy + sell count" if kind == "activity" else "Return (%)"
                )
                ax.set_xlabel("2024 · UTC · *December marked through 31 Dec 23:00")
                if kind == "monthly":
                    ax.axhline(0, color="#82908d", linewidth=0.6)
            else:
                values = []
                for label in labels:
                    by_side = details[(symbol, label)]["costs_by_side"]
                    values.append(
                        sum(
                            float(v[k])
                            for v in by_side.values()
                            for k in (
                                "fees",
                                "hypothetical_half_spread",
                                "hypothetical_slippage",
                            )
                        )
                    )
                bars = ax.bar(
                    [NAMES[label] for label in labels],
                    values,
                    color=[COLORS[label] for label in labels],
                )
                ax.bar_label(bars, labels=[f"{v:,.2f}" for v in values], padding=3)
                ax.set_ylim(0, max(values) * 1.18)
                ax.set_ylabel("USDT · fees + spread + slippage")
            if kind != "costs":
                ax.legend(loc="best", ncol=4, frameon=False, fontsize=9)
        fig.suptitle(
            f"Study 002 — {title}\nHistorical simulation · UNAPPROVED REVIEW DRAFT",
            fontsize=14,
        )
        fig.text(
            0.02, 0.045, f"Study 002 evidence SHA-256: {source_hash}", fontsize=6.7
        )
        fig.text(
            0.02,
            0.028,
            f"Study 001 evidence SHA-256: {source['study001_evidence_sha256']}",
            fontsize=6.7,
        )
        fig.text(
            0.02,
            0.011,
            "Independent 10,000 USDT accounts. Fixed costs. Previously inspected year. "
            "No terminal sale. Charts use retained account evidence.",
            fontsize=7,
        )
        fig.tight_layout(rect=(0, 0.07, 1, 0.92))
        fig.savefig(output / f"{kind}.png", dpi=150)
        plt.close(fig)
    table = []
    for row in rows:
        perf = row["performance"]
        costs = perf["costs_by_side"]
        total = sum(
            Decimal(v[k])
            for v in costs.values()
            for k in ("fees", "half_spread", "slippage")
        )
        returned = Decimal(perf["funding_relative_marked_return"]) * 100
        drawdown = (
            Decimal(perf["maximum_observed_hourly_reference_mark_drawdown"]) * 100
        )
        trades = sum(v["count"] for v in costs.values())
        table.append(
            f"<tr><th>{row['symbol']}</th><td>{NAMES[row['label']]}</td>"
            f"<td>{returned:+.2f}%</td><td>{drawdown:.2f}%</td>"
            f"<td>{trades}</td><td>{total:,.2f}</td></tr>"
        )
    figures = "".join(
        f'<figure><img src="{name}.png" alt="{label}; historical simulation '
        f'from source-linked retained evidence"><figcaption>{label}. '
        "Exact source hashes appear on each chart.</figcaption></figure>"
        for name, label in (
            ("equity", "Account equity in USDT"),
            ("drawdown", "Observed hourly drawdown"),
            ("exposure", "Trend long/cash exposure"),
            ("activity", "Monthly trading activity"),
            ("costs", "Attributed cost comparison in USDT"),
            ("monthly", "Monthly mark-to-mark returns"),
        )
    )
    page = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Study 002 — private review draft</title>
<style>body{{font:17px/1.6 system-ui;
background:#f4f1ea;
color:#202820;
max-width:1100px;
margin:auto;
padding:24px}}.badge{{background:#315943;
color:white;
padding:8px 14px;
display:inline-block}}table{{border-collapse:collapse;
width:100%;
font-variant-numeric:tabular-nums}}th,td{{padding:10px;
text-align:left;
border-bottom:1px solid #82908d}}img{{width:100%;
height:auto}}figure{{margin:35px 0}}.scroll{{overflow:auto}}a{{color:#315943}}</style>
<p class="badge">UNAPPROVED · LOCAL REVIEW DRAFT · HISTORICAL SIMULATION</p>
<h1>Can a Slower Trend Beat the Noise?</h1>
<p>Study 001's frequent position changes incurred substantial costs. This study asks
whether a simpler rule changes the outcome: once daily, hold the asset when its
completed price is above its price exactly 30 days earlier;
 otherwise hold cash.</p>
<p>The table includes fixed trading costs. Each strategy and market has its own 10,000
USDT. This changes both the signal and its frequency, so it cannot isolate the effect
of trading less.</p>
<div class="scroll">
<table>
<thead>
<tr>
<th>Market</th>
<th>Strategy</th>
<th>Net return</th>
<th>Hourly drawdown</th>
<th>Executions</th>
<th>Costs (USDT)</th>
</tr>
</thead>
<tbody>{"".join(table)}</tbody>
</table>
</div>
<p>Read the <a href="../study-002-slower-trend-results.md">scientific report</a>, <a
href="../study-002-methodology.md">predeclared methodology</a> and <a
href="review-data.json">exact source-linked data</a>. December's mark-to-mark period
is partial;
funding-relative returns include inception costs.</p>
{figures}
<h2>What this cannot establish</h2>
<p>2024 was already inspected. This is exploratory retrospective research, not
untouched out-of-sample evidence, live trading or proof of a durable edge. Archive
openings and assumed costs do not establish fillability. BTC and ETH share market
conditions.</p>
<p>Run: {html.escape(run_dir.name)}.
No production route or sitemap entry exists for this draft.
Publication requires owner review.</p>
</html>"""
    (output / "review.html").write_text(page)
    manifest = {
        "source": source,
        "files": {
            p.name: local.preparation.identity(p.read_bytes())
            for p in sorted(output.iterdir())
        },
    }
    (output / "manifest.json").write_bytes(local._bytes(manifest))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(create(args.run_dir, args.reference_dir, args.output_dir))


if __name__ == "__main__":
    main()

"""Read-only economic postmortem of the pinned Stage 2C validation accounts."""

import csv
import io
import json
import platform
from dataclasses import asdict
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

from backtest_badger.backtest import (
    ACCOUNTING,
    ACCOUNTING_TOLERANCE,
    EQUITY_COLUMNS,
    LIMITATIONS,
    SCENARIOS,
    STARTING_CASH,
    TRADE_COLUMNS,
    _serialise,
)
from backtest_badger.execution_data import START, coverage, csv_bytes, json_bytes
from backtest_badger.forecast_data import (
    CSV_SHA256 as FORECAST_CSV_SHA256,
)
from backtest_badger.forecast_data import (
    MANIFEST_SHA256 as FORECAST_MANIFEST_SHA256,
)
from backtest_badger.forecast_data import MODELS, Signal, schedule, should_enter
from backtest_badger.frozen import STEP, SYMBOLS, utc_time
from backtest_badger.ingestion import _retain
from backtest_badger.model_data import sha256

D = Decimal
MANIFEST_SHA256 = "72a2bd94966a07a726d3d2876fbabd249211ecda2994f930258edb8c5007ada0"
EXECUTION_MANIFEST_SHA256 = (
    "1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d"
)
IDENTITY = ("symbol", "model", "scenario")
TOTALS = ("gross_pnl", "net_pnl", "total_fees", "spread_cost", "slippage_cost")
MONTHS = tuple(f"2024-{m:02d}" for m in range(1, 13))
ROUNDING_TOLERANCE_USDT = D("1e-15")
DEFINITIONS = {
    "units": "Money/notional in USDT; returns and ratios are fractions unless "
    "named pct (percent) or bps (1e-4). Null JSON/blank CSV means undefined.",
    "gross_pnl": "Sum of quantity * (exit_reference - entry_reference), using "
    "each scenario's actual quantities. Never combine with another scenario's costs.",
    "net_pnl": "Scenario gross minus fees, spread and slippage; equals ending "
    "minus starting equity. Frictionless account growth is separately compounded.",
    "trade_returns": "Gross/net trade P&L divided by that trade's cash_before; "
    "arithmetic averages, undefined at zero trades. Wins require net P&L > 0.",
    "exposure": "Executed trades / eligible windows; not continuous-time exposure.",
    "drawdown": "Maximum initial/endpoint realised equity peak-to-trough fraction; "
    "includes cash windows, excludes intratrade marks.",
    "month": "UTC exit execution timestamp assigns the whole round trip, both "
    "sides' costs and invested window to [month start, next month start). An exit "
    "at midnight on February 1 belongs to February even if entry was in January. "
    "Beginning/ending equity are carried realised endpoint balances, not marked "
    "NAV at calendar midnight; a boundary-spanning open trade remains unrecognised "
    "until exit. Cash windows use their endpoint timestamp. All 12 months retained.",
    "monthly_reconciliation": "Add money/counts across months; multiply "
    "(1 + monthly_net_return) to recover annual ending / starting equity.",
    "turnover": "two_sided_notional = sum(entry_notional + exit_notional); "
    "two_sided_turnover_on_start = this / starting equity. "
    "entry_turnover_on_current_equity = sum(entry_notional / cash_before), "
    "which remains informative when account equity shrinks.",
    "cost_ratios": "cost_to_starting_equity = total_costs / starting equity; "
    "cost_to_positive_gross = total_costs / gross_pnl only for positive gross; "
    "cost_per_trade is undefined at zero trades. Monetary ratios use one scenario.",
    "cost_budget": "R = product(exit_reference / entry_reference) on the unchanged "
    "trade schedule. g = sum(ln(exit_reference / entry_reference)) / N. Maximum "
    "nonnegative effective round-trip log cost budget = g * 10000 bps if g >= 0. "
    "If g < 0, no nonnegative budget exists (null, not zero). No trades: R=1, "
    "g and budget undefined. This is an analytical diagnostic, not fee optimisation.",
    "cost_drag": "k = (1-h-s)*(1-f)/((1+h+s)*(1+f)); per-side rates divide bps "
    "by 10000. Effective round-trip log cost drag = -ln(k)*10000 bps, distinct "
    "from flat-price loss (1-k)*10000 bps and from per-side fee bps. "
    "Cumulative cost multiplier = k**N; analytical ending equity = 10000*R*k**N.",
    "rounding": "Analytical growth ignores the audited 1e-24 asset quantity floor "
    "and retained residual cash. Compare against actual endpoints, requiring "
    "absolute differences <= 1e-15 USDT for this fixed artifact. Report actual "
    "differences; this tolerance is numerical, not exchange execution precision.",
    "benchmarks": "Retain zero cash and always-positive training_mean under the "
    "same scenarios and eligible three-hour windows. Return differences are "
    "descriptive, not risk/exposure-adjusted alpha. No buy-and-hold added; native "
    "hourly sources are linked through the pinned manifest, not reopened/replayed.",
}
INTERPRETATION = (
    "Repeated full-capital round trips multiply the cost haircut even when "
    "individual charges look small. Small four-hour predictive error improvements "
    "need not survive sign selection, delayed three-hour exposure and costs. "
    "Positive frictionless returns can reflect long market exposure: compare the "
    "always-positive training mean before crediting ML timing. Different turnover "
    "and exposure prevent raw return differences being interpreted as alpha. "
    "A frictionlessly losing sequence remains unviable at zero costs, so low "
    "costs alone cannot establish a useful signal. Monthly differences are "
    "descriptive; no market-regime or event attribution is inferred. One validation "
    "year and correlated BTC/ETH markets cannot establish independent replication "
    "or robustness across regimes. No significance tests or confidence intervals "
    "are claimed. Exchange lot sizes and minimum notionals could prevent later "
    "orders in depleted accounts and change precise balances, counts and costs."
)


def identity(row):
    return tuple(row[k] for k in IDENTITY)


def close(actual, expected, label, tolerance=ACCOUNTING_TOLERANCE):
    if expected is None or actual is None:
        if actual is not None or expected is not None:
            raise ValueError(f"Reconciliation failed: {label}.")
    elif not D(expected).is_finite() or abs(actual - D(expected)) > tolerance:
        raise ValueError(f"Reconciliation failed: {label}.")


def read_rows(body, columns, text_columns):
    reader = csv.DictReader(io.StringIO(body.decode(), newline=""), strict=True)
    if reader.fieldnames != list(columns):
        raise ValueError("Incompatible Stage 2C CSV schema.")
    rows = []
    for row in reader:
        if None in row or None in row.values():
            raise ValueError("Malformed Stage 2C CSV row.")
        for key in columns:
            if key not in text_columns:
                row[key] = D(row[key])
                if not row[key].is_finite():
                    raise ValueError("Nonfinite Stage 2C value.")
        rows.append(row)
    return rows


def load_evidence(directory, *, expected_manifest_sha256=MANIFEST_SHA256):
    """Alternate pin is for synthetic tests only; CLI always uses the audited pin."""
    body = (directory / "manifest.json").read_bytes()
    if sha256(body) != expected_manifest_sha256:
        raise ValueError("Stage 2C manifest SHA-256 mismatch.")
    try:
        manifest = json.loads(body)
        if not (
            manifest["backtest_version"] == "stage-2c-v1"
            and manifest["kind"] == "historical simulation"
            and manifest["partition"] == "2024 validation only"
            and D(manifest["starting_cash_usdt"]) == STARTING_CASH
            and manifest["scenarios"] == _serialise([asdict(c) for c in SCENARIOS])
            and manifest["forecast_hashes"]
            == {
                "manifest.json": FORECAST_MANIFEST_SHA256,
                "validation_predictions.csv": FORECAST_CSV_SHA256,
            }
            and manifest["execution"]["manifest_sha256"] == EXECUTION_MANIFEST_SHA256
            and manifest["execution"]["coverage"] == coverage()
        ):
            raise ValueError("Incompatible Stage 2C provenance or assumptions.")
        files = {}
        # Explicit names: never follow paths supplied in an input manifest.
        for name in ("trades.csv", "equity_curve.csv", "summary.md"):
            files[name] = (directory / name).read_bytes()
            if sha256(files[name]) != manifest["output_sha256"][name]:
                raise ValueError(f"Stage 2C {name} SHA-256 mismatch.")
        trades = read_rows(
            files["trades.csv"],
            TRADE_COLUMNS,
            (*IDENTITY, "open_time", "signal_time", "entry_time", "exit_time"),
        )
        equity = read_rows(
            files["equity_curve.csv"], EQUITY_COLUMNS, (*IDENTITY, "timestamp", "event")
        )
        keys = [(s, m, c.name) for s in SYMBOLS for m in MODELS for c in SCENARIOS]
        if [identity(a) for a in manifest["accounts"]] != keys:
            raise ValueError("Incompatible or duplicate account identities.")
        grouped = {key: ([], []) for key in keys}
        for rows, index in ((trades, 0), (equity, 1)):
            previous = -1
            for row in rows:
                key = identity(row)
                rank = keys.index(key)
                if rank < previous:
                    raise ValueError("Noncanonical account ordering.")
                previous = rank
                grouped[key][index].append(row)
        grid = [START + i * STEP for i in range(2196)]
        schedules = {}
        for key, (ts, es) in grouped.items():
            if [utc_time(e["timestamp"]) for e in es] != grid:
                raise ValueError("Incomplete or nonchronological 2024 equity grid.")
            exits = []
            signature = []
            for t in ts:
                signal = Signal(
                    key[0],
                    key[1],
                    utc_time(t["open_time"]),
                    utc_time(t["signal_time"]),
                    t["forecast"],
                )
                entry, exit_time = schedule(signal)
                if (
                    not should_enter(signal)
                    or utc_time(t["entry_time"]) != entry
                    or utc_time(t["exit_time"]) != exit_time
                    or min(t["entry_reference"], t["exit_reference"], t["quantity"])
                    <= 0
                ):
                    raise ValueError("Incompatible retained trade schedule or price.")
                exits.append(exit_time)
                signature.append(
                    tuple(
                        t[k]
                        for k in (
                            "open_time",
                            "signal_time",
                            "forecast",
                            "entry_time",
                            "exit_time",
                            "entry_reference",
                            "exit_reference",
                        )
                    )
                )
            if exits != sorted(set(exits)):
                raise ValueError("Duplicate or nonchronological trades.")
            if key[1] == "zero" and ts:
                raise ValueError("Zero benchmark must stay in cash.")
            if key[1] == "training_mean" and len(ts) != 2195:
                raise ValueError("Training-mean benchmark must invest every window.")
            if key[:2] in schedules and schedules[key[:2]] != signature:
                raise ValueError("Trade schedules differ between cost scenarios.")
            schedules[key[:2]] = signature
    except (KeyError, TypeError, IndexError, InvalidOperation, csv.Error) as error:
        raise ValueError("Malformed Stage 2C evidence.") from error
    hashes = {"manifest.json": sha256(body)}
    hashes.update({name: sha256(data) for name, data in files.items()})
    return manifest, hashes, grouped


def cost_budget(trades, costs):
    """Exact fixed-schedule multiplicative diagnostic, without quantity rounding."""
    with localcontext(ACCOUNTING):
        growth, log_growth = D(1), D(0)
        for t in trades:
            ratio = t["exit_reference"] / t["entry_reference"]
            growth *= ratio
            log_growth += ratio.ln()
        n = len(trades)
        average = log_growth / n if n else None
        f, h, s = (
            v / 10000
            for v in (
                costs.fee_bps,
                costs.half_spread_bps,
                costs.slippage_bps,
            )
        )
        k = (1 - h - s) * (1 - f) / ((1 + h + s) * (1 + f))
        drag = -k.ln() * 10000
        budget = average * 10000 if n and average >= 0 else None
        return {
            "frictionless_growth_factor": growth,
            "frictionless_return_pct": (growth - 1) * 100,
            "average_geometric_log_return_bps": average * 10000 if n else None,
            "max_nonnegative_round_trip_log_cost_bps": budget,
            "cost_budget_status": "no_trades"
            if not n
            else ("nonnegative_budget" if average >= 0 else "loses_without_costs"),
            "round_trip_cost_multiplier": k,
            "round_trip_log_cost_drag_bps": drag,
            "flat_round_trip_cost_bps": (1 - k) * 10000,
            "budget_minus_actual_log_drag_bps": budget - drag
            if budget is not None
            else None,
            "cumulative_cost_multiplier": k**n,
            "analytical_ending_equity": STARTING_CASH * growth * k**n,
        }


def analyse_account(trades, equity, expected, costs):
    """Aggregate retained cash flows; do not simulate decisions, fills or quantities."""
    with localcontext(ACCOUNTING):
        return _analyse_account(trades, equity, expected, costs)


def _analyse_account(trades, equity, expected, costs):
    prefix = {k: expected[k] for k in IDENTITY}
    if not equity or any(identity(r) != identity(expected) for r in trades + equity):
        raise ValueError("Missing equity or mixed accounts.")
    if equity[0]["event"] != "initial":
        raise ValueError("Missing initial equity.")
    by_exit = {t["exit_time"]: t for t in trades}
    if len(by_exit) != len(trades):
        raise ValueError("Duplicate trade exits.")
    cash = peak = STARTING_CASH
    drawdown = D(0)
    close(equity[0]["equity"], cash, "initial equity")
    months = {
        month: {
            **prefix,
            "month": month,
            "trades": 0,
            "invested_windows": 0,
            "eligible_windows": 0,
            **{k: D(0) for k in TOTALS},
        }
        for month in MONTHS
    }
    for e in equity:
        close(e["cash"], e["equity"], "flat cash equity")
        close(e["asset_quantity"], D(0), "flat position")
    for e in equity[1:]:
        month = months[utc_time(e["timestamp"]).strftime("%Y-%m")]
        month["eligible_windows"] += 1
        t = by_exit.pop(e["timestamp"], None)
        if t is not None:
            if e["event"] != "exit":
                raise ValueError("Trade missing matching equity exit.")
            close(t["cash_before"], cash, "trade starting cash")
            close(
                t["gross_pnl"],
                t["quantity"] * (t["exit_reference"] - t["entry_reference"]),
                "scenario gross P&L",
            )
            close(t["total_fees"], t["entry_fee"] + t["exit_fee"], "fees")
            close(
                t["net_pnl"],
                t["gross_pnl"]
                - t["total_fees"]
                - t["spread_cost"]
                - t["slippage_cost"],
                "trade net P&L",
            )
            close(t["net_trade_return"], t["net_pnl"] / cash, "trade return")
            cash += t["net_pnl"]
            close(t["cash_after_exit"], cash, "trade ending cash")
            for k in TOTALS:
                month[k] += t[k]
            month["trades"] += 1
            month["invested_windows"] += 1
        elif e["event"] != "cash_window":
            raise ValueError("Equity exit missing matching trade.")
        close(e["equity"], cash, "equity path")
        peak = max(peak, cash)
        drawdown = max(drawdown, (peak - cash) / peak)
    if by_exit:
        raise ValueError("Trades outside equity observations.")
    monthly, beginning, compounded = [], STARTING_CASH, D(1)
    for month in months.values():
        ending = beginning + month["net_pnl"]
        month.update(
            total_costs=sum((month[k] for k in TOTALS[2:]), D(0)),
            beginning_equity=beginning,
            ending_equity=ending,
            monthly_net_return=ending / beginning - 1,
        )
        close(month["gross_pnl"] - month["total_costs"], month["net_pnl"], "month P&L")
        compounded *= 1 + month["monthly_net_return"]
        beginning = ending
        monthly.append(month)
    n, windows = len(trades), len(equity) - 1
    totals = {k: sum((m[k] for m in monthly), D(0)) for k in TOTALS}
    annual = {
        **prefix,
        "trades": n,
        "eligible_windows": windows,
        "cash_signals": windows - n,
        "starting_equity": STARTING_CASH,
        "ending_equity": cash,
        **totals,
        "net_return_pct": (cash / STARTING_CASH - 1) * 100,
        "win_rate": D(sum(t["net_pnl"] > 0 for t in trades)) / n if n else None,
        "average_net_trade_return": sum((t["net_trade_return"] for t in trades), D(0))
        / n
        if n
        else None,
        "max_realised_equity_drawdown": drawdown,
        "fraction_windows_invested": D(n) / windows if windows else D(0),
        "holding_hours": n * 3,
    }
    for k, v in annual.items():
        if k not in IDENTITY:
            close(v, expected[k], k)
    close(totals["net_pnl"], cash - STARTING_CASH, "annual P&L")
    close(compounded, cash / STARTING_CASH, "monthly compounded return")
    close(beginning, cash, "monthly ending equity")
    total_costs = sum((totals[k] for k in TOTALS[2:]), D(0))
    notional = sum((t["entry_notional"] + t["exit_notional"] for t in trades), D(0))
    annual.update(
        total_costs=total_costs,
        average_gross_trade_return=sum(
            (t["gross_pnl"] / t["cash_before"] for t in trades), D(0)
        )
        / n
        if n
        else None,
        winning_trade_pct=annual["win_rate"] * 100 if n else None,
        two_sided_notional=notional,
        two_sided_turnover_on_start=notional / STARTING_CASH,
        entry_turnover_on_current_equity=sum(
            (t["entry_notional"] / t["cash_before"] for t in trades), D(0)
        ),
        cost_to_starting_equity=total_costs / STARTING_CASH,
        cost_to_positive_gross=total_costs / totals["gross_pnl"]
        if totals["gross_pnl"] > 0
        else None,
        cost_per_trade=total_costs / n if n else None,
        **cost_budget(trades, costs),
    )
    annual["quantity_rounding_difference_usdt"] = (
        cash - annual["analytical_ending_equity"]
    )
    close(
        cash,
        annual["analytical_ending_equity"],
        "analytical growth",
        ROUNDING_TOLERANCE_USDT,
    )
    annual["reconciled_to_stage_2c"] = True
    return annual, monthly


def summary(accounts, monthly):
    lines = [
        "# Stage 2D — economic diagnostics of fixed 2024 historical simulations",
        "",
        "Each account starts with 10,000 USDT. All monetary figures below are USDT. "
        "Gross uses scenario-specific quantities; frictionless growth is a separate "
        "account. No costs are subtracted across scenarios. Rounded tables are for "
        "reading; CSV/manifest retain calculation precision.",
        "",
        "| Market | Model | Scenario | Trades | Ending equity | Gross P&L | Fees | "
        "Spread | Slippage | Net P&L | Net % |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for a in accounts:
        values = [*(a[k] for k in IDENTITY), str(a["trades"])]
        values += [
            f"{a[k]:.4f}"
            for k in (
                "ending_equity",
                "gross_pnl",
                "total_fees",
                "spread_cost",
                "slippage_cost",
                "net_pnl",
                "net_return_pct",
            )
        ]
        lines.append("| " + " | ".join(values) + " |")
    lines += [
        "",
        "## Fixed-sequence cost budgets",
        "",
        "Effective round-trip **log-cost** basis points, not per-side fees. "
        "Undefined budgets distinguish cash accounts and frictionless losses.",
        "",
        "| Market | Model | Frictionless % | Mean log return bps | Budget bps | "
        "Status | Base drag bps | Stress drag bps |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for a in accounts:
        if a["scenario"] != "frictionless":
            continue
        peers = {
            v["scenario"]: v
            for v in accounts
            if (v["symbol"], v["model"]) == (a["symbol"], a["model"])
        }
        values = [a["symbol"], a["model"]]
        values += [
            "undefined" if a[k] is None else f"{a[k]:.4f}"
            for k in (
                "frictionless_return_pct",
                "average_geometric_log_return_bps",
                "max_nonnegative_round_trip_log_cost_bps",
            )
        ]
        values += [a["cost_budget_status"]]
        values += [
            f"{peers[s]['round_trip_log_cost_drag_bps']:.4f}"
            for s in ("base", "stress")
        ]
        lines.append("| " + " | ".join(values) + " |")
    lines += [
        "",
        "## Every calendar month",
        "",
        DEFINITIONS["month"],
        "",
        "Monthly return is 100 × (ending / beginning − 1). Money sums and "
        "return products reconcile to annual results for every account.",
        "",
        "| Market | Model | Scenario | Month | Trades/invested windows | "
        "Gross P&L | Costs | Net P&L | Beginning equity | Ending equity | Net % |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for m in monthly:
        values = [*(m[k] for k in IDENTITY), m["month"], str(m["trades"])]
        values += [
            f"{m[k]:.4f}"
            for k in (
                "gross_pnl",
                "total_costs",
                "net_pnl",
                "beginning_equity",
                "ending_equity",
            )
        ]
        values += [f"{100 * m['monthly_net_return']:.4f}"]
        lines.append("| " + " | ".join(values) + " |")
    lines += ["", "## Benchmark context and monthly variation", ""]
    for a in accounts:
        rows = [m for m in monthly if identity(m) == identity(a)]
        gross_positive = sum(m["gross_pnl"] > 0 for m in rows)
        net_positive = sum(m["net_pnl"] > 0 for m in rows)
        lo = min(m["monthly_net_return"] for m in rows) * 100
        hi = max(m["monthly_net_return"] for m in rows) * 100
        lines.append(
            f"- {a['symbol']} {a['model']} {a['scenario']}: "
            f"{gross_positive}/12 positive gross months, "
            f"{net_positive}/12 positive net months; net range {lo:.2f}% "
            f"to {hi:.2f}%; invested {a['fraction_windows_invested']:.2%} "
            f"of windows."
        )
        if a["model"] in ("ridge", "gradient_boosting"):
            baseline = next(
                b
                for b in accounts
                if b["symbol"] == a["symbol"]
                and b["scenario"] == a["scenario"]
                and b["model"] == "training_mean"
            )
            delta = a["net_return_pct"] - baseline["net_return_pct"]
            lines.append(
                f"  Return difference vs training mean: {delta:+.4f} "
                f"percentage points; {a['trades']} vs {baseline['trades']} "
                "round trips. This is not risk-adjusted alpha."
            )
    lines += ["", INTERPRETATION, "", "## Calculation definitions", ""]
    lines += [f"- **{key}**: {value}" for key, value in DEFINITIONS.items()]
    lines += ["", "## Scientific limitations", "", LIMITATIONS, ""]
    return "\n".join(lines)


def analyse_economics(backtest, destination, **checks):
    if destination.exists():
        raise FileExistsError(destination)
    source, hashes, grouped = load_evidence(backtest, **checks)
    accounts, monthly = [], []
    for expected in source["accounts"]:
        costs = next(c for c in SCENARIOS if c.name == expected["scenario"])
        annual, months = analyse_account(*grouped[identity(expected)], expected, costs)
        accounts.append(annual)
        monthly.extend(months)
    # All arithmetic, including report percentages, uses the same explicit context.
    with localcontext(ACCOUNTING):
        rendered_summary = summary(accounts, monthly).encode()
    report = _serialise(
        {
            "analysis_version": "stage-2d-v1",
            "kind": "read-only economic postmortem of historical simulation",
            "partition": "2024 validation only",
            "source": {
                "artifact": source["backtest_version"],
                "verified_sha256": hashes,
                "recorded_forecast_hashes": source["forecast_hashes"],
                "recorded_execution": source["execution"],
                "recorded_implementation_sha256": source["implementation_sha256"],
            },
            "scenarios": source["scenarios"],
            "policy": source["policy"],
            "accounting": source["accounting"],
            "starting_cash_usdt": STARTING_CASH,
            "markets": SYMBOLS,
            "models": MODELS,
            "definitions": DEFINITIONS,
            "interpretation": INTERPRETATION,
            "limitations": LIMITATIONS,
            "reconciliation": "All 24 accounts match retained Stage 2C annual metrics; "
            "all monthly money/count totals and compounded returns reconcile.",
            "quantity_rounding_tolerance_usdt": ROUNDING_TOLERANCE_USDT,
            "test_policy": "No research CSV, holdout labels, forecast files or model "
            "fitting accessed.",
            "reproducibility": "Identical bytes with identical inputs, implementation "
            "and runtime; no timestamps or absolute input/output paths embedded.",
            "runtime": {
                "python": platform.python_version(),
                "implementation": platform.python_implementation(),
            },
            "implementation_sha256": {
                name: sha256(Path(__file__).with_name(name).read_bytes())
                for name in (
                    "economics.py",
                    "backtest.py",
                    "forecast_data.py",
                    "execution_data.py",
                    "frozen.py",
                    "model_data.py",
                    "ingestion.py",
                )
            },
            "accounts": accounts,
        }
    )
    files = {
        "monthly_results.csv": csv_bytes(tuple(monthly[0]), monthly),
        "cost_diagnostics.csv": csv_bytes(tuple(accounts[0]), accounts),
        "summary.md": rendered_summary,
    }
    report["output_sha256"] = {name: sha256(body) for name, body in files.items()}
    files["manifest.json"] = json_bytes(report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    for name, body in files.items():
        _retain(destination / name, body)
    return report

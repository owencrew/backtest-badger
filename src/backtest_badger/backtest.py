"""Sequential long/cash historical simulation, with explicit Decimal accounting."""

from dataclasses import asdict, dataclass
from decimal import ROUND_DOWN, Context, Decimal, localcontext
from pathlib import Path

from backtest_badger.execution_data import (
    START,
    csv_bytes,
    json_bytes,
    load_execution_data,
)
from backtest_badger.forecast_data import load_forecasts, schedule, should_enter
from backtest_badger.ingestion import _retain
from backtest_badger.model_data import sha256

D = Decimal
STARTING_CASH = D("10000")
ACCOUNTING = Context(prec=80)
ACCOUNTING_TOLERANCE = D("1e-60")
QUANTITY_STEP = D("1e-24")


@dataclass(frozen=True)
class Costs:
    name: str
    fee_bps: Decimal
    half_spread_bps: Decimal
    slippage_bps: Decimal

    def __post_init__(self):
        values = (self.fee_bps, self.half_spread_bps, self.slippage_bps)
        if (
            not self.name
            or any(
                not isinstance(v, Decimal) or not v.is_finite() or v < 0 for v in values
            )
            or self.fee_bps >= 10000
            or self.half_spread_bps + self.slippage_bps >= 10000
        ):
            raise ValueError(
                "Costs must be finite nonnegative bps with positive sell proceeds."
            )


SCENARIOS = (
    Costs("frictionless", D(0), D(0), D(0)),
    Costs("base", D(10), D(1), D(2)),
    Costs("stress", D(10), D(3), D(10)),
)
LIMITATIONS = (
    "Historical simulation only, not actual or paper-traded performance. Native 1h "
    "opens are historical references, not guaranteed fills. The deliberate hourly "
    "boundary policy is not immediate market-order execution: 12:01 signals enter "
    "at 13:00 and exit at 16:00, changing the exposure from the model's four-hour "
    "close-to-close target to a three-hour holding return. Fees, half-spreads and "
    "slippage are fixed assumptions, not verified historical account fees or quotes. "
    "Regression improvement need not imply profitable sign decisions, and repeated "
    "costs can overwhelm weak signals. Retrospective candles cannot reconstruct "
    "historical publication delays, order books, market impact or available liquidity. "
    "No exchange lot/minimum-notional filters are modelled; quantities use only a "
    "numerical precision floor. Realised-equity drawdown omits intratrade excursions; "
    "no Sharpe ratio is reported. A profitable validation outcome would still need "
    "separate robustness and untouched-holdout research; it establishes no robust "
    "strategy. BTC and ETH are correlated, not independent confirmation; one fixed "
    "2024 period cannot establish performance in other regimes. No tuning, refitting, "
    "test-label access, model promotion, live trading or deployment occurs."
)
TRADE_COLUMNS = (
    "symbol",
    "model",
    "scenario",
    "open_time",
    "signal_time",
    "forecast",
    "entry_time",
    "exit_time",
    "entry_reference",
    "exit_reference",
    "entry_price",
    "exit_price",
    "quantity",
    "cash_before",
    "entry_notional",
    "entry_fee",
    "cash_after_entry",
    "exit_notional",
    "exit_fee",
    "spread_cost",
    "slippage_cost",
    "total_fees",
    "gross_pnl",
    "net_pnl",
    "net_trade_return",
    "cash_after_exit",
    "asset_after_exit",
    "reconciliation_error",
)
EQUITY_COLUMNS = (
    "symbol",
    "model",
    "scenario",
    "timestamp",
    "event",
    "equity",
    "cash",
    "asset_quantity",
)


def simulate_account(signals, prices, costs):
    """One isolated account. Plan every decision before looking up future fills."""
    if not signals:
        raise ValueError("An account requires at least one eligible signal.")
    identity = signals[0].symbol, signals[0].model
    plan, previous_exit = [], None
    for signal in signals:
        entry, exit_time = schedule(signal)
        if (signal.symbol, signal.model) != identity:
            raise ValueError("Mixed market/model account.")
        if previous_exit is not None and signal.signal_time <= previous_exit:
            raise ValueError("Nonchronological or overlapping signal windows.")
        previous_exit = exit_time
        plan.append((signal, entry, exit_time, should_enter(signal)))
    # No trading around gaps, even for cash decisions. Production additionally
    # verifies every hourly identity and exact archive correspondence before here.
    for _, entry, exit_time, _ in plan:
        for stamp in (entry, exit_time):
            value = prices.get((identity[0], stamp))
            if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
                raise ValueError(
                    "Missing or invalid matching hourly execution reference."
                )
    with localcontext(ACCOUNTING):
        return _simulate(plan, prices, costs, identity)


def _simulate(plan, prices, costs, identity):
    fee, spread, slip = (
        v / 10000 for v in (costs.fee_bps, costs.half_spread_bps, costs.slippage_bps)
    )
    cash = peak = STARTING_CASH
    drawdown = D(0)
    trades, equity = [], []
    totals = {
        k: D(0)
        for k in ("gross_pnl", "net_pnl", "total_fees", "spread_cost", "slippage_cost")
    }
    prefix = {"symbol": identity[0], "model": identity[1], "scenario": costs.name}

    def record(stamp, event):
        equity.append(
            {
                **prefix,
                "timestamp": stamp.isoformat(),
                "event": event,
                "equity": cash,
                "cash": cash,
                "asset_quantity": D(0),
            }
        )

    record(START, "initial")
    max_error = D(0)
    for signal, entry, exit_time, enter in plan:
        if enter:
            before = cash
            buy_ref, sell_ref = (
                prices[identity[0], entry],
                prices[identity[0], exit_time],
            )
            buy, sell = buy_ref * (1 + spread + slip), sell_ref * (1 - spread - slip)
            quantity = (cash / (buy * (1 + fee))).quantize(
                QUANTITY_STEP, rounding=ROUND_DOWN
            )
            if quantity <= 0:
                raise ValueError("Account cannot afford a positive numerical quantity.")
            entry_notional = quantity * buy
            entry_fee = entry_notional * fee
            residual = cash - entry_notional - entry_fee
            exit_notional = quantity * sell
            exit_fee = exit_notional * fee
            cash = residual + exit_notional - exit_fee
            gross = quantity * (sell_ref - buy_ref)
            spread_cost = quantity * (buy_ref + sell_ref) * spread
            slippage_cost = quantity * (buy_ref + sell_ref) * slip
            fees = entry_fee + exit_fee
            net = cash - before
            error = abs(net - (gross - spread_cost - slippage_cost - fees))
            if residual < 0 or cash < 0 or error > ACCOUNTING_TOLERANCE:
                raise ValueError(
                    "Cash conservation or gross/net reconciliation failed."
                )
            max_error = max(max_error, error)
            trade = {
                **prefix,
                "open_time": signal.open_time.isoformat(),
                "signal_time": signal.signal_time.isoformat(),
                "forecast": signal.forecast,
                "entry_time": entry.isoformat(),
                "exit_time": exit_time.isoformat(),
                "entry_reference": buy_ref,
                "exit_reference": sell_ref,
                "entry_price": buy,
                "exit_price": sell,
                "quantity": quantity,
                "cash_before": before,
                "entry_notional": entry_notional,
                "entry_fee": entry_fee,
                "cash_after_entry": residual,
                "exit_notional": exit_notional,
                "exit_fee": exit_fee,
                "spread_cost": spread_cost,
                "slippage_cost": slippage_cost,
                "total_fees": fees,
                "gross_pnl": gross,
                "net_pnl": net,
                "net_trade_return": net / before,
                "cash_after_exit": cash,
                "asset_after_exit": D(0),
                "reconciliation_error": error,
            }
            trades.append(trade)
            for key in totals:
                totals[key] += trade[key]
        peak = max(peak, cash)
        drawdown = max(drawdown, (peak - cash) / peak)
        record(exit_time, "exit" if enter else "cash_window")
    reconciliation = abs(
        (cash - STARTING_CASH)
        - (
            totals["gross_pnl"]
            - totals["total_fees"]
            - totals["spread_cost"]
            - totals["slippage_cost"]
        )
    )
    if (
        max(reconciliation, abs(totals["net_pnl"] - (cash - STARTING_CASH)))
        > ACCOUNTING_TOLERANCE
    ):
        raise ValueError("Account totals do not reconcile.")
    count = len(trades)
    metrics = {
        **prefix,
        "starting_equity": STARTING_CASH,
        "ending_equity": cash,
        **totals,
        "net_return_pct": (cash / STARTING_CASH - 1) * 100,
        "trades": count,
        "cash_signals": len(plan) - count,
        "eligible_windows": len(plan),
        "win_rate": D(sum(t["net_pnl"] > 0 for t in trades)) / count if count else None,
        "average_net_trade_return": sum((t["net_trade_return"] for t in trades), D(0))
        / count
        if count
        else None,
        "max_realised_equity_drawdown": drawdown,
        "fraction_windows_invested": D(count) / len(plan),
        "holding_hours": count * 3,
        "missing_references": 0,
        "rejected_references": 0,
        "ending_asset_quantity": D(0),
        "account_reconciliation_error": reconciliation,
        "max_trade_reconciliation_error": max_error,
    }
    return trades, equity, metrics


def summary(report):
    lines = [
        "# Stage 2C — historical validation simulation",
        "",
        "Each account starts at 10,000 USDT. Gross P&L uses the actual scenario's "
        "quantities at reference prices; it is not a separately compounded "
        "frictionless account. Net = gross − fees − spread − slippage.",
        "",
        "| Market | Model | Scenario | Trades | Gross P&L USDT | Net P&L USDT | "
        "Net % | Fees | Spread | Slippage |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for m in report["accounts"]:
        values = [m["symbol"], m["model"], m["scenario"], str(m["trades"])]
        values += [
            f"{D(m[k]):.2f}"
            for k in (
                "gross_pnl",
                "net_pnl",
                "net_return_pct",
                "total_fees",
                "spread_cost",
                "slippage_cost",
            )
        ]
        lines.append("| " + " | ".join(values) + " |")
    lines += [
        "",
        "Drawdown observes initial equity and each eligible window's exit boundary, "
        "including cash windows. All observations are flat realised equity, "
        "not intratrade marks. "
        "Win rate and mean trade return are undefined for zero trades. "
        "The manifest contains full-precision metrics, exposure "
        "and reconciliation checks.",
        "",
        LIMITATIONS,
        "",
    ]
    return "\n".join(lines)


def _serialise(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _serialise(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialise(v) for v in value]
    return value


def backtest_validation(forecasts, execution, destination, **forecast_checks):
    if destination.exists():
        raise FileExistsError(destination)
    forecast_hashes, accounts = load_forecasts(forecasts, **forecast_checks)
    execution_metadata, prices = load_execution_data(execution)
    report = {
        "backtest_version": "stage-2c-v1",
        "kind": "historical simulation",
        "partition": "2024 validation only",
        "forecast_hashes": forecast_hashes,
        "execution": execution_metadata,
        "scenarios": [asdict(c) for c in SCENARIOS],
        "starting_cash_usdt": STARTING_CASH,
        "policy": "Forecast > 1e-12: fully invested long; otherwise cash. Signal = "
        "candle open + 4h + 60s; entry = next hourly boundary; exit = open + 8h. "
        "Independent market/model/scenario accounts; no overlapping positions.",
        "accounting": "80 significant Decimal digits, ROUND_HALF_EVEN; quantities "
        "rounded down to 1e-24 asset units; residual cash retained. Fees apply to "
        "executed notional on both sides. Spread/slippage add adversely to reference "
        "prices. Gross uses actual quantities before all costs; "
        "not a counterfactual portfolio.",
        "accounting_absolute_tolerance_usdt": ACCOUNTING_TOLERANCE,
        "drawdown": "Initial equity plus every eligible window endpoint; realised "
        "flat equity including cash windows; intratrade drawdowns unobserved.",
        "return_convention": "Net trade return = net P&L / pre-entry account equity; "
        "win = strictly positive net P&L. Exposure = invested / eligible windows.",
        "test_policy": "No research CSV, labels, test forecasts "
        "or model fitting accessed.",
        "reproducibility": "Byte-identical outputs for identical frozen inputs "
        "and implementation.",
        "implementation_sha256": {
            name: sha256(Path(__file__).with_name(name).read_bytes())
            for name in (
                "backtest.py",
                "forecast_data.py",
                "execution_data.py",
                "archives.py",
                "candles.py",
            )
        },
        "limitations": LIMITATIONS,
        "accounts": [],
    }
    trades, equity = [], []
    for signals in accounts.values():
        for costs in SCENARIOS:
            t, e, m = simulate_account(signals, prices, costs)
            trades.extend(t)
            equity.extend(e)
            report["accounts"].append(m)
    report = _serialise(report)
    files = {
        "trades.csv": csv_bytes(TRADE_COLUMNS, trades),
        "equity_curve.csv": csv_bytes(EQUITY_COLUMNS, equity),
        "summary.md": summary(report).encode(),
    }
    report["output_sha256"] = {name: sha256(body) for name, body in files.items()}
    files["manifest.json"] = json_bytes(report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    for name, body in files.items():
        _retain(destination / name, body)
    return report

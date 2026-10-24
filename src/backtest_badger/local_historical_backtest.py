"""E.5e local operator: pinned publication -> existing replay -> verified reports.

No acquisition, model fitting, signing, network or database operations. The CLI
has no pin override. Tests replace the retained pins with invented identities.
"""

import argparse
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Inexact, localcontext
from pathlib import Path
from uuid import uuid4

from backtest_badger import genuine_backtest_preparation as preparation
from backtest_badger import genuine_minute_publication as publication
from backtest_badger import paper_accounting as accounting
from backtest_badger import paper_minute_historical as minute
from backtest_badger import paper_minute_reporting as reporting
from backtest_badger.paper_types import INITIAL_CASH, D, money_context, require

VERSION = "stage-04b2e5e-local-historical-v1"
LIMITATIONS = (
    "Previously inspected exploratory 2024 history; not untouched out-of-sample.",
    "Hypothetical Binance Spot backtest, not live or prospective paper trading.",
    "Archive opens and assumed forecast availability do not prove fillability.",
    "No measured latency, depth, liquidity or market impact; fixed model costs.",
    "Independent 10000 USDT accounts; no combined BTC/ETH portfolio.",
    "No terminal liquidation or 2025 price; last valuation is December 31 23:00 UTC.",
    "Final day and December are partial; complete-day statistics exclude that day.",
    "Daily mark returns exclude inception costs already charged before the first mark.",
    "Annualisation uses 365 days; daily sample volatility and zero-rate Sharpe are "
    "descriptive, assume square-root-of-time scaling, and are not alpha evidence.",
    "Retained publication/sign-off reconciliation is not a fresh source audit.",
)
OUTPUT_FILES = ("run.json", "summary.json", "summary.md", "private/evidence.json")


def _bytes(value):
    return minute.scientific_json(value).encode("ascii")


def _pins():
    return publication._PublicationPins(
        **{
            name: publication._Fingerprint(**pin)
            for name, pin in preparation.HISTORICAL_PINS.items()
        }
    )


def _check_method():
    """Check the frozen runtime constants; there are no scenario overrides."""
    require(
        preparation.identity(_bytes(preparation.METHOD))["sha256"]
        == "d38ff4eb51cfbec757c4592fb4ee08c38f43d04ebbb23f264a875d0ae24b1754"
        and minute.PROTOCOL_VERSION == preparation.PROTOCOL["version"]
        and minute.PROTOCOL_SHA256 == preparation.PROTOCOL["sha256"]
        and minute.START == preparation.START
        and minute.END == preparation.END
        and minute.SYMBOLS == ("BTCUSDT", "ETHUSDT")
        and minute.QUANTITY_STEP == D("0.000001")
        and minute.INITIAL_CASH == INITIAL_CASH == D("10000")
        and accounting.FEE_RATE == D("0.001")
        and accounting.FEE_QUANTUM == D("0.00000001")
        and money_context().prec == 160
        and money_context().traps[Inexact]
        and money_context(division=True).prec == 80,
        "Frozen execution methodology changed.",
    )


def preflight(paths):
    """Read only the four explicit paths, then reconcile without economic replay."""
    require(set(paths) == set(preparation.PIN_NAMES), "Four explicit paths required.")
    _check_method()
    pins = _pins()
    bodies = {}
    for name in preparation.PIN_NAMES:
        pin = getattr(pins, name)
        try:
            with Path(paths[name]).open("rb") as stream:
                require(
                    os.fstat(stream.fileno()).st_size == pin.bytes,
                    f"{name}: retained byte length mismatch.",
                )
                body = stream.read(pin.bytes + 1)
        except OSError as error:
            raise ValueError(f"{name}: cannot read explicit input: {error}") from error
        require(
            preparation.identity(body) == {"sha256": pin.sha256, "bytes": pin.bytes},
            f"{name}: retained SHA-256/size mismatch.",
        )
        bodies[name] = body
    # All four identities are checked BEFORE any parsing or monetary operation.
    parsed = publication._parse_verified_publication(
        **{name: bodies[name] for name in publication.FILES_KEYS},
        expected=pins,
        signoff_claim=pins.signoff,
    )
    return publication._validate_independent_signoff(
        signoff=bodies["signoff"],
        expected_signoff=pins.signoff,
        publication=parsed,
        expected=pins,
    )


def _descriptive_statistics(summary):
    """Supplemental ratios only, from verified marks; never change account money."""
    unavailable = {"value": None, "reason": "account_unavailable"}
    if summary["status"] != "available":
        return dict.fromkeys(
            ("annualised_return", "annualised_daily_volatility", "zero_rate_sharpe"),
            unavailable,
        )
    daily = [
        row["return"]
        for row in summary["observations"]
        if row["period"] == "daily" and row["complete"]
    ]
    elapsed = (summary["last_observed_mark"].reference.at - minute.START) // timedelta(
        seconds=1
    )
    equity = summary["last_observed_mark"].equity
    with localcontext(money_context()):
        total = sum(daily, D(0))
    with localcontext(money_context(division=True)):
        annual = (
            (equity / INITIAL_CASH) ** (D(365 * 86400) / elapsed) - 1
            if elapsed > 0 and equity > 0
            else None
        )
        mean = total / len(daily) if daily else None
        deviation = (
            (sum(((r - mean) ** 2 for r in daily), D(0)) / (len(daily) - 1)).sqrt()
            if len(daily) > 1
            else None
        )
        volatility = deviation * D(365).sqrt() if deviation is not None else None
        sharpe = mean / deviation * D(365).sqrt() if deviation else None
    return {
        "annualised_return": {
            "value": annual,
            "reason": None if annual is not None else "nonpositive_equity_or_duration",
        },
        "annualised_daily_volatility": {
            "value": volatility,
            "reason": None
            if volatility is not None
            else "fewer_than_two_complete_days",
        },
        "zero_rate_sharpe": {
            "value": sharpe,
            "reason": None
            if sharpe is not None
            else "insufficient_days_or_zero_variance",
        },
    }


def _account_report(account, fingerprint):
    summary = reporting.minute_reporting_summary(
        account, end_exclusive=minute.END, expected_fingerprint=fingerprint
    )
    native = minute.minute_account_summary(account, end_exclusive=minute.END)
    require(
        summary["performance"] == (native if account.status == "available" else None)
        and summary["account_id"] == account.initial.portfolio.key
        and summary["input_fingerprint"] == fingerprint
        and summary["initial_account"] == account.initial
        and summary["final_account"] == account.final
        and summary["last_observed_mark"]
        == (account.marks[-1] if account.marks else None),
        "Report/ledger inconsistency.",
    )
    if account.status == "available":
        for side, costs in native["costs_by_side"].items():
            for native_name, report_name in (
                ("count", "count"),
                ("notional", "notional"),
                ("fees", "fees"),
                ("half_spread", "hypothetical_half_spread"),
                ("slippage", "hypothetical_slippage"),
            ):
                require(
                    costs[native_name] == summary["costs_by_side"][side][report_name],
                    "Report/ledger cost inconsistency.",
                )
    ledger = minute.minute_ledger_records(account)
    concise = {
        key: summary[key]
        for key in (
            "account_id",
            "symbol",
            "label",
            "status",
            "reason",
            "performance",
            "costs_by_side",
            "complete_day_statistics",
        )
    }
    concise.update(
        {
            "account_fingerprint": fingerprint,
            "ledger_identity": preparation.identity(_bytes(ledger)),
            "ledger_verification": "passed",
            "end_holdings": {
                "cash_usdt": account.final.cash,
                "base_quantity": account.final.quantity,
                "cost_basis_usdt": account.final.basis,
            },
            "descriptive_statistics": _descriptive_statistics(summary),
        }
    )
    return concise, {"summary": summary, "ledger": ledger}


def _reports(results, pins):
    require(
        tuple(r.symbol for r in results) == minute.SYMBOLS,
        "Expected two ordered markets.",
    )
    accounts = []
    for result in results:
        require(
            result.source.publication == pins
            and result.source.symbol == result.symbol
            and result.kind == publication.KIND
            and result.protocol_version == preparation.PROTOCOL["version"]
            and result.protocol_sha256 == preparation.PROTOCOL["sha256"]
            and result.end_exclusive == minute.END
            and len(result.decisions) == 2195
            and tuple(a.label for a in result.accounts) == tuple(preparation.LABELS),
            "Replay market/account/protocol identity changed.",
        )
        for account in result.accounts:
            portfolio = account.initial.portfolio
            require(
                portfolio.key == f"{publication.KIND}:{result.symbol}:{account.label}"
                and portfolio.symbol == result.symbol
                and portfolio.venue == "binance"
                and portfolio.market_type == "spot"
                and portfolio.inception_at == minute.START
                and portfolio.protocol_sha256 == minute.PROTOCOL_SHA256
                and portfolio.model_recipe_sha256 == result.source.model_recipe_sha256
                and portfolio.strategy_id
                == (
                    "ridge_sign"
                    if account.label == "ridge"
                    else f"analytical_{account.label}"
                )
                and portfolio.strategy_version == "1"
                and account.initial.cash == INITIAL_CASH,
                "Independent account identity/funding changed.",
            )
            accounts.append(account)
    # Retain BEFORE the reporting handoff, using E.5b's verified fingerprint API.
    fingerprints = tuple(
        reporting.minute_reporting_fingerprint(a, end_exclusive=minute.END)
        for a in accounts
    )
    rows, detailed = [], []
    for account, fingerprint in zip(accounts, fingerprints, strict=True):
        row, detail = _account_report(account, fingerprint)
        rows.append(row)
        detailed.append(detail)
    comparisons = []
    with localcontext(money_context(division=True)):
        for offset, symbol in ((0, "BTCUSDT"), (3, "ETHUSDT")):
            ridge = rows[offset]["performance"]
            for benchmark in rows[offset + 1 : offset + 3]:
                performance = benchmark["performance"]
                comparisons.append(
                    {
                        "symbol": symbol,
                        "benchmark": benchmark["label"],
                        "funding_return_difference": (
                            ridge["funding_relative_marked_return"]
                            - performance["funding_relative_marked_return"]
                            if ridge is not None and performance is not None
                            else None
                        ),
                        "reason": None
                        if ridge and performance
                        else "account_unavailable",
                    }
                )
    return {"accounts": rows, "ridge_comparisons": comparisons}, detailed


def _execution_identity():
    # Ordinary reproducibility metadata, not runtime/OS attestation. Record the
    # loaded project sources, including uncommitted code, rather than a guessed HEAD.
    return {
        "version": VERSION,
        "python": sys.version,
        "source_files": {
            name: preparation.identity(Path(module.__file__).read_bytes())
            for name, module in sorted(sys.modules.items())
            if name.startswith("backtest_badger") and getattr(module, "__file__", None)
        }
        | {"runner": preparation.identity(Path(__file__).read_bytes())},
    }


def _write(path, body):
    """Install a complete file without replacing any existing destination."""
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)  # Atomic and no-clobber, on the same local filesystem.
    temporary.unlink()


def _markdown(summary):
    lines = [
        "# Backtest Badger — exploratory historical backtest",
        "",
        "2024 Binance Spot; Ridge Sign, Cash and Buy & Hold. "
        "Three independent 10,000 USDT accounts per market.",
        "",
        "Returns below are funding-relative through the last observed hourly mark.",
        "",
        "| Market | Account | Status | Return | Hourly drawdown | Trades |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in summary["accounts"]:
        p = row["performance"]
        with localcontext(money_context(division=True)):
            returned = (
                f"{p['funding_relative_marked_return'] * 100:.4f}%" if p else "N/A"
            )
            drawdown = (
                f"{p['maximum_observed_hourly_reference_mark_drawdown'] * 100:.4f}%"
                if p
                else "N/A"
            )
        trades = sum(v["count"] for v in p["costs_by_side"].values()) if p else "N/A"
        lines.append(
            f"| {row['symbol']} | {row['label']} | {row['status']} | "
            f"{returned} | {drawdown} | {trades} |"
        )
    lines += ["", "Exact metrics, holdings and comparisons: `summary.json`.", ""]
    lines += [f"- {line}" for line in LIMITATIONS]
    return ("\n".join(lines) + "\n").encode("utf-8")


def run(paths, output_dir, *, execute=False):
    """Explicit local consent; every invocation validates again and uses a new run."""
    require(execute is True, "Explicit --execute consent required before input access.")
    checked = preflight(paths)
    parsed = checked.publication
    started = datetime.now(UTC)
    run_id = started.strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex
    directory = Path(output_dir) / run_id
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    (directory / "private").mkdir(mode=0o700)
    metadata = {
        "schema": VERSION,
        "run_id": run_id,
        "started_at": started,
        "operator_consent": "explicit_local_execute",
        "input_identities": parsed.pins,
        "execution": _execution_identity(),
        "protocol": preparation.PROTOCOL,
        "method": preparation.METHOD,
        "limitations": LIMITATIONS,
    }
    metadata_body = _bytes(metadata)
    expected_files = {"run.json": preparation.identity(metadata_body)}
    _write(directory / "run.json", metadata_body)
    results = publication._replay_verified_publication(
        parsed, expected=parsed.pins, signoff_claim=parsed.pins.signoff
    )
    summary, detailed = _reports(results, parsed.pins)
    summary = {
        "schema": VERSION,
        "research_classification": preparation.METHOD["research_status"],
        "protocol": preparation.PROTOCOL,
        "method": preparation.METHOD,
        "limitations": LIMITATIONS,
        **summary,
    }
    # Original publication, model, approval and sign-off bodies are not exported.
    evidence = {
        "input_identities": parsed.pins,
        "results": results,
        "reports": detailed,
    }
    for name, body in (
        ("summary.json", _bytes(summary)),
        ("summary.md", _markdown(summary)),
        ("private/evidence.json", _bytes(evidence)),
    ):
        expected_files[name] = preparation.identity(body)
        _write(directory / name, body)
    for name, expected in expected_files.items():
        require(
            preparation.identity((directory / name).read_bytes()) == expected,
            f"Output readback mismatch: {name}.",
        )
    completion = {
        "schema": VERSION,
        "run_id": run_id,
        "completed_at": datetime.now(UTC),
        "complete": True,
        "files": expected_files,
    }
    _write(directory / "COMPLETE.json", _bytes(completion))
    verify_output(directory)
    return directory


def verify_output(directory):
    """No replay: require the final marker and every recorded file identity."""
    directory = Path(directory)
    try:
        marker = json.loads((directory / "COMPLETE.json").read_bytes())
        require(
            marker["schema"] == VERSION
            and marker["complete"] is True
            and marker["run_id"] == directory.name
            and set(marker["files"]) == set(OUTPUT_FILES),
            "Invalid completion marker.",
        )
        for name in OUTPUT_FILES:
            require(
                preparation.identity((directory / name).read_bytes())
                == marker["files"][name],
                f"Output identity mismatch: {name}.",
            )
        return marker
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("Incomplete or malformed local run output.") from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    for name in ("preflight", "run"):
        command = commands.add_parser(name)
        for pin_name in preparation.PIN_NAMES:
            command.add_argument("--" + pin_name.replace("_", "-"), required=True)
        if name == "run":
            command.add_argument("--output-dir", required=True)
            command.add_argument("--execute", action="store_true", required=True)
    commands.add_parser("verify-output").add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "verify-output":
            verify_output(args.run_dir)
            print("Complete output; all recorded file identities match.")
        else:
            paths = {name: getattr(args, name) for name in preparation.PIN_NAMES}
            if args.mode == "preflight":
                preflight(paths)
                print(
                    "Preflight passed: four retained pins, publication and sign-off; "
                    "no economic replay performed."
                )
            else:
                print(run(paths, args.output_dir, execute=args.execute))
    except (ValueError, OSError) as error:
        parser.exit(1, f"Local historical backtest failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

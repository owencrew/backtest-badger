"""Local-only Study 002 orchestration; one explicit attempt, retained diagnostics."""

import argparse
import json
from datetime import UTC, datetime
from decimal import localcontext
from pathlib import Path
from uuid import uuid4

from backtest_badger import frozen
from backtest_badger import local_historical_backtest as local
from backtest_badger import study002 as study
from backtest_badger.paper_types import D, money_context, require

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/studies"
VERSION = "study-002-local-v1"
FILES = ("run.json", "summary.json", "private/evidence.json", "verification.json")
REFERENCE_ID = "20261024T143549527999Z-85d1960cda514032ba3e4ac5f59b21d2"
REFERENCE_FILES = {
    "summary.json": {
        "bytes": 16433,
        "sha256": "5d0536ea8e1b7f80274fddd6b0f0840901231838f17877632b936d5c01905a9b",
    },
    "private/evidence.json": {
        "bytes": 66840604,
        "sha256": "d23caae7d49bad50a254495b5f1a5b973ba72f714ce6be83bce0368a95bc0368",
    },
    "run.json": {
        "bytes": 6985,
        "sha256": "9ccb356d538b3a3198fbc670b0adc5f42ea215f3eee3e4c84df1e3d766f75790",
    },
    "summary.md": {
        "bytes": 1614,
        "sha256": "47ff388881d6cbf1c05b9f18b762a205ae73894292e8620b9cd00c0d6ac4c5eb",
    },
}


def reference(directory):
    """Original retained evidence, independently anchored outside its marker."""
    directory = Path(directory)
    local.verify_output(directory)
    for name, pin in REFERENCE_FILES.items():
        require(
            local.preparation.identity((directory / name).read_bytes()) == pin,
            f"Original Study 001 identity mismatch: {name}",
        )
    return json.loads((directory / "summary.json").read_bytes())


def check_freeze():
    record = json.loads((DOCS / "study-002-freeze.json").read_bytes())
    require(record["schema"] == "study-002-freeze-v1", "Wrong freeze record.")
    require(
        datetime.fromisoformat(record["frozen_at"]) <= datetime.now(UTC),
        "Future freeze.",
    )
    for name, pin in record["files"].items():
        require(
            local.preparation.identity((ROOT / name).read_bytes()) == pin,
            f"Frozen file changed: {name}",
        )
    for required in (
        "docs/studies/study-002-config.json",
        "docs/studies/study-002-methodology.md",
        "src/backtest_badger/study002.py",
        "src/backtest_badger/study002_runner.py",
    ):
        require(required in record["files"], "Incomplete freeze record.")
    require(
        record["validation"]["synthetic_and_regressions_passed"] is True,
        "Required validation has not passed.",
    )
    return record


def preflight(paths, history, reference_dir):
    freeze = check_freeze()
    publication = local.preflight(paths).publication
    _, markets = frozen.load_frozen(Path(history), acknowledge_incomplete=True)
    closes = study.close_projection(markets)
    references = {}
    for symbol, refs in zip(
        study.minute.SYMBOLS, publication.inputs.references, strict=True
    ):
        # Validate availability only; do not calculate trend signs before run.
        first = study.minute.START - study.LOOKBACK - study.STEP
        stop = study.minute.END - study.DAY
        expected = tuple(
            first + i * study.STEP for i in range((stop - first) // study.STEP)
        )
        require(
            tuple(r.opened for r in closes[symbol]) == expected,
            "Incomplete warm-up/grid.",
        )
        needed = {
            study.minute.START + i * study.minute.HOUR
            for i in range((study.minute.END - study.minute.START) // study.minute.HOUR)
        } | {
            study.minute.START + i * study.DAY + 2 * study.minute.MINUTE
            for i in range((study.minute.END - study.minute.START) // study.DAY)
        }
        references[symbol] = tuple(r for r in refs if r.at in needed)
        require(
            [r.at for r in references[symbol]] == sorted(needed),
            "Missing daily minute source.",
        )
    old = reference(reference_dir)
    return freeze, publication, closes, references, old


def _dt(value):
    return datetime.fromisoformat(value)


def validate_evidence(summary, evidence, old):
    """Independent serialized-posting/mark arithmetic, without strategy replay.

    Uses explicit signed postings and raw opening references, not cached account
    balances or the reporting implementation's derived totals as its authority.
    """
    checked = []
    require(
        len(summary["accounts"]) == len(evidence["reports"]) == 6,
        "Wrong account count.",
    )
    accounts = [a for r in evidence["results"] for a in r["accounts"]]
    require(
        len({a["initial"]["portfolio"]["key"] for a in accounts}) == 6,
        "Shared funding identity.",
    )
    with localcontext(money_context(division=True)):
        for account, row, detail in zip(
            accounts, summary["accounts"], evidence["reports"], strict=True
        ):
            ledger = detail["ledger"]
            key = account["initial"]["portfolio"]["key"]
            require(row["account_id"] == key, "Summary account mismatch.")
            require(
                local.preparation.identity(local._bytes(ledger))
                == row["ledger_identity"],
                "Ledger hash mismatch.",
            )
            require(
                local.preparation.identity(local._bytes(account))
                == row["canonical_account_identity"],
                "Account hash mismatch.",
            )
            require(
                ledger[0]["event"] == "funding" and D(ledger[0]["amount"]) == D(10000),
                "Wrong funding.",
            )
            require(
                [x["sequence"] for x in ledger] == list(range(1, len(ledger) + 1)),
                "Non-atomic ledger sequence.",
            )
            require(
                all(x["account_id"] == key for x in ledger), "Shared ledger identity."
            )
            with localcontext(money_context()):
                cash = sum(
                    (D(x["amount"]) for x in ledger if x["asset"] == "USDT"), D(0)
                )
                base = sum(
                    (
                        D(x["amount"])
                        for x in ledger
                        if x["asset"] == account["initial"]["portfolio"]["symbol"][:-4]
                    ),
                    D(0),
                )
            require(
                cash == D(row["final_cash"]) == D(account["final"]["cash"])
                and base == D(row["final_quantity"]) == D(account["final"]["quantity"]),
                "Posting/final mismatch.",
            )
            require(cash >= 0 and base >= 0, "Negative holdings.")
            if account["status"] == "unavailable":
                require(
                    account["label"] == "buy_and_hold"
                    and not account["fills"]
                    and not account["marks"]
                    and row["performance"] is None,
                    "Invalid unavailable account.",
                )
                checked.append(key)
                continue
            totals = {
                k: D(0)
                for k in (
                    "notional",
                    "fees",
                    "hypothetical_half_spread",
                    "hypothetical_slippage",
                )
            }
            seconds, entered = 0, None
            for i, fill in enumerate(account["fills"]):
                t, ref = fill["trade"], fill["reference"]
                q, price, raw = D(t["quantity"]), D(t["price"]), D(ref["price"])
                buy = t["side"] == "BUY"
                require(
                    t["at"] == ref["at"]
                    and price == raw * (D("1.0003") if buy else D("0.9997")),
                    "Execution reference mismatch.",
                )
                require(q > 0 and q % D("0.000001") == 0, "Wrong quantity step.")
                fee = (q * price * D("0.001")).quantize(
                    D("0.00000001"), rounding="ROUND_UP"
                )
                require(
                    D(t["fee"]) == fee and D(t["notional"]) == q * price,
                    "Fee/notional mismatch.",
                )
                pair = ledger[1 + 2 * i : 3 + 2 * i]
                require(
                    len(pair) == 2
                    and [x["asset"] for x in pair]
                    == ["USDT", account["initial"]["portfolio"]["symbol"][:-4]],
                    "Broken paired postings.",
                )
                require(
                    D(pair[0]["amount"])
                    == (-(q * price + fee) if buy else q * price - fee)
                    and D(pair[1]["amount"]) == (q if buy else -q),
                    "Wrong signed postings.",
                )
                require(
                    all(
                        x["at"] == t["at"] and x["trade_id"] == t["identity"]
                        for x in pair
                    ),
                    "Posting/trade identity mismatch.",
                )
                totals["notional"] += q * price
                totals["fees"] += fee
                for name, rate, field in (
                    ("hypothetical_half_spread", "0.0001", "half_spread_cost"),
                    ("hypothetical_slippage", "0.0002", "slippage_cost"),
                ):
                    cost = q * raw * D(rate)
                    require(cost == D(fill[field]), "Attribution mismatch.")
                    totals[name] += cost
                if buy:
                    require(entered is None, "Double entry.")
                    entered = _dt(t["at"])
                else:
                    require(entered is not None, "Exit without entry.")
                    seconds += int((_dt(t["at"]) - entered).total_seconds())
                    entered = None
            if entered:
                seconds += int((study.minute.END - entered).total_seconds())
            totals["total_attributed_costs"] = (
                totals["fees"]
                + totals["hypothetical_half_spread"]
                + totals["hypothetical_slippage"]
            )
            totals["turnover_initial_funding"] = totals["notional"] / D(10000)
            require(
                all(D(row["totals"][k]) == v for k, v in totals.items()),
                "Summary totals mismatch.",
            )
            running_cash, running_base, cursor, peak, drawdown, invested = (
                D(0),
                D(0),
                0,
                D(10000),
                D(0),
                0,
            )
            require(len(account["marks"]) == 8784, "Incomplete hourly marks.")
            for i, m in enumerate(account["marks"]):
                at = study.minute.START + i * study.minute.HOUR
                require(_dt(m["reference"]["at"]) == at, "Mark order mismatch.")
                while cursor < len(ledger) and _dt(ledger[cursor]["at"]) <= at:
                    posting = ledger[cursor]
                    if posting["asset"] == "USDT":
                        running_cash += D(posting["amount"])
                    else:
                        running_base += D(posting["amount"])
                    cursor += 1
                equity = running_cash + running_base * D(m["reference"]["price"])
                require(
                    running_cash >= 0
                    and running_base >= 0
                    and D(m["cash"]) == running_cash
                    and D(m["quantity"]) == running_base
                    and D(m["equity"]) == equity
                    and m["ledger_seq"] == cursor,
                    "Hourly ledger-prefix mismatch.",
                )
                require(
                    D(m["realised"]) + D(m["unrealised"]) == equity - D(10000),
                    "Marked P&L mismatch.",
                )
                peak = max(peak, equity)
                drawdown = max(drawdown, (peak - equity) / peak)
                invested += running_base > 0
            perf = row["performance"]
            require(
                D(row["final_mark_equity"]) == equity
                and D(perf["funding_relative_marked_return"])
                == (equity - D(10000)) / D(10000),
                "Final summary mismatch.",
            )
            require(
                D(perf["maximum_observed_hourly_reference_mark_drawdown"]) == drawdown
                and perf["exposure_seconds"] == seconds
                and D(perf["invested_hourly_mark_fraction"]) == D(invested) / 8784,
                "Risk/exposure mismatch.",
            )
            month_product = D(1)
            marks = {m["reference"]["at"]: m for m in account["marks"]}
            monthly_count = 0
            for p in detail["summary"]["observations"]:
                expected_return = (
                    D(marks[p["end"]]["equity"]) / D(marks[p["start"]]["equity"]) - 1
                )
                require(
                    abs(D(p["return"]) - expected_return) < D("1e-75"),
                    "Period return mismatch.",
                )
                if p["period"] == "monthly":
                    month_product *= 1 + D(p["return"])
                    monthly_count += sum(
                        v["count"] for v in p["costs_by_side"].values()
                    )
            require(
                abs(month_product - equity / D(account["marks"][0]["equity"]))
                < D("1e-74")
                and monthly_count == len(account["fills"]),
                "Monthly/annual inconsistency.",
            )
            require(
                row["position_changes"] == len(account["fills"])
                and D(row["realised"]) == D(account["final"]["realised"])
                and D(row["final_basis"]) == D(account["final"]["basis"])
                and D(row["unrealised"]) == D(account["marks"][-1]["unrealised"]),
                "Position/P&L summary mismatch.",
            )
            if account["label"] != study.STRATEGY:
                original = next(
                    x
                    for x in old["accounts"]
                    if x["symbol"] == row["symbol"] and x["label"] == row["label"]
                )
                require(
                    row["performance"] == original["performance"]
                    and row["costs_by_side"] == original["costs_by_side"]
                    and row["descriptive_statistics"]
                    == original["descriptive_statistics"],
                    "Original benchmark mismatch.",
                )
            checked.append(key)
        for result in evidence["results"]:
            decisions = result["decisions"]
            require(len(decisions) == 366, "Daily evaluation count mismatch.")
            account = result["accounts"][0]
            row = next(
                r
                for r in summary["accounts"]
                if r["symbol"] == result["symbol"] and r["label"] == study.STRATEGY
            )
            require(
                row["signal_evaluations"] == len(decisions)
                and row["hold_count"] == sum(d["action"] == "HOLD" for d in decisions)
                and row["cash_noop_count"]
                == sum(d["action"] == "CASH_NOOP" for d in decisions),
                "Decision summary mismatch.",
            )
            fills = {f["decision_id"]: f for f in account["fills"]}
            held = False
            for i, d in enumerate(decisions):
                s = d["signal"]
                at = study.minute.START + i * study.DAY + study.minute.MINUTE
                require(
                    _dt(s["at"]) == at
                    and _dt(s["now"]["closed"]) == at - study.minute.MINUTE
                    and _dt(s["past"]["closed"])
                    == at - study.minute.MINUTE - study.LOOKBACK,
                    "Signal chronology mismatch.",
                )
                target = D(s["now"]["price"]) > D(s["past"]["price"])
                action = (
                    ("HOLD" if held else "BUY_REQUIRED")
                    if target
                    else ("EXIT_REQUIRED" if held else "CASH_NOOP")
                )
                require(
                    s["long"] == target and d["action"] == action,
                    "Signal/action mismatch.",
                )
                if held != target:
                    require(
                        d["identity"] in fills
                        and _dt(fills[d["identity"]]["trade"]["at"])
                        == at + study.minute.MINUTE,
                        "Not strictly next minute.",
                    )
                else:
                    require(d["identity"] not in fills, "Noop traded.")
                held = target
    return {
        "status": "passed",
        "accounts": checked,
        "independent_serialized_ledger_checks": True,
        "benchmarks_equal_study001": True,
    }


def run(paths, history, reference_dir, output_parent, *, execute=False):
    require(execute is True, "Explicit --execute required.")
    parent = Path(output_parent).resolve()
    require(
        parent.is_relative_to(ROOT / "artifacts"),
        "Results must remain under ignored artifacts/.",
    )
    started = datetime.now(UTC)
    directory = parent / (started.strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex)
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    (directory / "private").mkdir(mode=0o700)
    identities = {}

    def publish(name, value):
        body = local._bytes(value)
        identities[name] = local.preparation.identity(body)
        local._write(directory / name, body)

    publish("attempt.json", {"started_at": started, "study": VERSION, "execute": True})
    try:
        freeze, publication, closes, refs, old = preflight(
            paths, history, reference_dir
        )
        method = freeze["files"]["docs/studies/study-002-methodology.md"]
        config = freeze["files"]["docs/studies/study-002-config.json"]
        execution = local._execution_identity()
        execution["version"] = VERSION
        execution["source_files"]["runner"] = local.preparation.identity(
            Path(__file__).read_bytes()
        )
        metadata = {
            "schema": VERSION,
            "run_id": directory.name,
            "started_at": started,
            "freeze": freeze,
            "input_identities": publication.pins,
            "history": {"csv": frozen.CSV_SHA256, "manifest": frozen.MANIFEST_SHA256},
            "execution": execution,
            "reference_files": REFERENCE_FILES,
        }
        publish("run.json", metadata)
        results, rows, details = [], [], []
        for symbol in study.minute.SYMBOLS:
            result = study.replay(
                symbol,
                closes[symbol],
                refs[symbol],
                config_sha256=config["sha256"],
                method_sha256=method["sha256"],
            )
            concise, detail = study.reports(result)
            results.append(result)
            rows.extend(concise)
            details.extend(detail)
        summary = {
            "schema": VERSION,
            "classification": "exploratory_retrospective_previously_inspected_2024",
            "accounts": rows,
            "ridge_reference": old["accounts"],
            "publication_status": "unapproved_draft",
        }
        evidence = {"results": results, "reports": details}
        for name, value in (
            ("summary.json", summary),
            ("private/evidence.json", evidence),
        ):
            publish(name, value)
        # Validate the bytes read back, independently of mutable in-memory objects.
        verified = validate_evidence(
            json.loads((directory / "summary.json").read_bytes()),
            json.loads((directory / "private/evidence.json").read_bytes()),
            old,
        )
        preflight(
            paths, history, reference_dir
        )  # no economics; post-run input/freeze preservation
        publish("verification.json", verified)
        for name, expected in identities.items():
            require(
                local.preparation.identity((directory / name).read_bytes()) == expected,
                f"Output readback mismatch: {name}",
            )
        local._write(
            directory / "COMPLETE.json",
            local._bytes(
                {
                    "schema": VERSION,
                    "run_id": directory.name,
                    "complete": True,
                    "completed_at": datetime.now(UTC),
                    "files": identities,
                }
            ),
        )
        verify_output(directory)
    except Exception as error:
        local._write(
            directory / "FAILED.json",
            local._bytes(
                {
                    "status": "failed",
                    "exception": type(error).__name__,
                    "message": str(error),
                    "at": datetime.now(UTC),
                }
            ),
        )
        raise
    return directory


def verify_output(directory):
    directory = Path(directory)
    marker = json.loads((directory / "COMPLETE.json").read_bytes())
    require(not (directory / "FAILED.json").exists(), "Failed attempt is not complete.")
    require(
        marker["schema"] == VERSION
        and marker["complete"] is True
        and marker["run_id"] == directory.name
        and set(marker["files"]) == set((*FILES, "attempt.json")),
        "Invalid completion manifest.",
    )
    for name, pin in marker["files"].items():
        require(
            local.preparation.identity((directory / name).read_bytes()) == pin,
            f"Output mismatch: {name}",
        )
    return marker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "run", "verify-output"))
    for name in (
        *local.preparation.PIN_NAMES,
        "history",
        "reference-dir",
        "output-dir",
        "run-dir",
    ):
        parser.add_argument("--" + name.replace("_", "-"), type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.mode == "verify-output":
        verify_output(args.run_dir)
        print("Study 002 output identities verified.")
    else:
        paths = {n: getattr(args, n) for n in local.preparation.PIN_NAMES}
        if args.mode == "preflight":
            preflight(paths, args.history, args.reference_dir)
            print("Study 002 preflight passed; no economics.")
        else:
            print(
                run(
                    paths,
                    args.history,
                    args.reference_dir,
                    args.output_dir,
                    execute=args.execute,
                )
            )


if __name__ == "__main__":
    main()

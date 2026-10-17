"""Supplied-input historical evaluation. No source readers, CLI, clocks or services.

The adapter consumes unchanged loader return shapes plus separately supplied
manifest lineage. A snapshot digest detects mutation after verification; mocked
pins and metadata do NOT authenticate real source bytes.
"""

import calendar
import csv
import io
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from hashlib import sha256

from backtest_badger.paper_accounting import Account, apply_trade, fund_account, replay
from backtest_badger.paper_execution import affordable_quantity
from backtest_badger.paper_historical import (
    BASE_CONFIG,
    END,
    HOUR,
    KIND,
    START,
    HistoricalForecast,
    HistoricalMark,
    HourlyReference,
    calculate_historical_trade,
    historical_json,
    replay_historical,
    value_historical,
)
from backtest_badger.paper_types import (
    INITIAL_CASH,
    STEP,
    Action,
    D,
    Portfolio,
    Side,
    digest,
    money_context,
    number,
    require,
    utc,
)

SYMBOLS = ("BTCUSDT", "ETHUSDT")
MODELS = ("zero", "training_mean", "ridge", "gradient_boosting")
PROTOCOL_VERSION = "historical-validation-v1"
PROTOCOL_SHA256 = "b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b"
PROTOCOL_REVISION = "9af7a4573169b16bd049be34ed130c41c17a9d45"
FORECAST_SHA256 = "e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674"
RECIPE_SHA256 = "af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581"
HOURLY_SHA256 = "39a9b7c21e882ccbf45053067bfb813702be6f279779f77b1a184288b01f5e1a"
HOURLY_MANIFEST_SHA256 = (
    "1b905fe6e23b2d5a8d6b60fe0a801bb2e0e4d15fefe830b9ec591c118c19fc4d"
)
ACQUISITION_SHA256 = "926697a89eb7c018ca5913f1e3c4c1170715db5639d444a58a78012e92aec055"
RESEARCH_SHA256 = "04d9dc27593cd904829c1760fcf8b557e249b0d5ac160879d538337bef9558a8"
RESEARCH_MANIFEST_SHA256 = (
    "a97c192bb01cbbca515d2052e04655dad45d78a9afbe58c45f8216fd2e4a1b8e"
)
FEATURES = (
    "log_return_4h",
    "log_return_12h",
    "log_return_24h",
    "realised_volatility_24h",
    "relative_base_volume",
)
SOURCE_PATHS = {
    "forecast_manifest": "artifacts/experiments/stage-2b-v1/manifest.json",
    "predictions": "artifacts/experiments/stage-2b-v1/validation_predictions.csv",
    "hourly_manifest": "artifacts/execution/binance-1h-2024-v1/manifest.json",
    "hourly_opens": "artifacts/execution/binance-1h-2024-v1/hourly_opens.csv",
    "acquisition": "artifacts/execution/binance-1h-2024-v1/acquisition.json",
}
# Transcribed from the reviewed Stage 2C documentation, never read from artifacts.
MONTHLY_ZIP_SHA256 = {
    (
        "BTCUSDT",
        "2024-01",
    ): "cf873a185bd5b24b8e00034e49583fcb49928e0c3a45c6fc27a632a683655417",
    (
        "ETHUSDT",
        "2024-01",
    ): "1fdb3a8fa6b77ef30ef17ed4b71b184172ef1f812d83bd0f50bbd08e71a92057",
    (
        "BTCUSDT",
        "2024-02",
    ): "b83aa7319ef1d4baa7b923c0fe802b88dfaf241c7456af295f1f656a24379b33",
    (
        "ETHUSDT",
        "2024-02",
    ): "f080ff288b2f7e85e78c5370a8a3258b93f85531ff96b4131c1b7889649a8ba4",
    (
        "BTCUSDT",
        "2024-03",
    ): "b0851daf609d6ab82fdf8f1d1c4fbd974bc1b4e6530a832067516ac1c2be63a6",
    (
        "ETHUSDT",
        "2024-03",
    ): "4eb16ab0c5db15e5e0d77827f5c19c215c7ce601a5501d9563b75bda7602f46e",
    (
        "BTCUSDT",
        "2024-04",
    ): "e266707ad2ea3cd4680bf1ac5025f0c1bfeb38e703374a91f8dc193d1ec8d48f",
    (
        "ETHUSDT",
        "2024-04",
    ): "8b710fad720ae0bc75eaded37b3add95ca49122ae398f3f6e33e57e864da781e",
    (
        "BTCUSDT",
        "2024-05",
    ): "077c71eec71a8ecf2edb6e3a3927b600b8f358fd37066ce120c19fb5302a9ab8",
    (
        "ETHUSDT",
        "2024-05",
    ): "0307d64f0d9ae6ff4001442a014d7b02dcbc5a003dcc36ba139f1c9695996b51",
    (
        "BTCUSDT",
        "2024-06",
    ): "2e1f968fa34b9feabfb19cc6eec47a146e20d64a706f4b17d0babf4d2f475c39",
    (
        "ETHUSDT",
        "2024-06",
    ): "59ee6920bd72d93d1130c89711c93ea192bbfd5f82b548dcb0448f66450f6a06",
    (
        "BTCUSDT",
        "2024-07",
    ): "41fd58a70ae40bebb74682555cc5054709f8dde0f5c8193ae2103dac95274e5f",
    (
        "ETHUSDT",
        "2024-07",
    ): "83181cfcc1f1e32a542e2c220cbd58acd1c550cc64ad1e2c414e47088266aa7c",
    (
        "BTCUSDT",
        "2024-08",
    ): "88521a975ee7bfdd21f891d81f4243a01b90b977cf525d11747e27c66e3bad60",
    (
        "ETHUSDT",
        "2024-08",
    ): "d908255a48978f6acb769c4b856a3307c58a8c19dbf2b3b7f10067245d5e8b89",
    (
        "BTCUSDT",
        "2024-09",
    ): "123f402c6dbf19b9b72b4af7ad4d5325c73ba4833148cc398b803d7a34ac5c5f",
    (
        "ETHUSDT",
        "2024-09",
    ): "bfbdda97d03abac469199120ec3c2f1305e2d5947e9155ff84dbeafe33cd4a67",
    (
        "BTCUSDT",
        "2024-10",
    ): "393b18ad2634f0cd3b2fd54321c8286ea143419cf3129b4cc44e089681912b03",
    (
        "ETHUSDT",
        "2024-10",
    ): "cbb13664485b6c9a6365da7ae23299b722ab5926a6aed516add486ef501883bc",
    (
        "BTCUSDT",
        "2024-11",
    ): "7a51fe8811c754ff43a2be0ba10e53a6d4218521e27ac765fbc9a1ca0fc15bac",
    (
        "ETHUSDT",
        "2024-11",
    ): "29cd30419b86d5dff5467a7a81d43e492aaaeb3669db216ab8badaad5fe610ec",
    (
        "BTCUSDT",
        "2024-12",
    ): "dfec812f73a84257b195cbdaed34d020fa77e845625c061c13bd6a60e7ef9372",
    (
        "ETHUSDT",
        "2024-12",
    ): "84312b7dc2b5c903853c78d94f587ef1d24b7960d7bd95f5bfe3afc3db006203",
}

LIMITATIONS = (
    (
        "Synthetic fixtures cannot authenticate genuine 2024 files; a "
        "separate owner-approved real-run gate is mandatory."
    ),
    (
        "Historical simulation using archived hourly opening references, "
        "not actual trades or prospective paper trading."
    ),
    "Signal availability at source open +4h+60s is assumed, not actual issuance.",
    (
        "Retrospective acquisition timestamps are not provider-side quote "
        "timestamps or historical availability evidence."
    ),
    (
        "Order-book liquidity, exchange filters, market impact and "
        "warranted fillability are not evidenced/untested."
    ),
    (
        "Buy-and-hold buys at 00:00, before Ridge's earliest 01:00 trade; "
        "funds, exposure and cost timing differ."
    ),
    (
        "Comparisons are contextual, not causal alpha evidence. Ridge was "
        "chosen after prior 2024 analysis; positive results are not "
        "independent validation."
    ),
    (
        "BTC and ETH are correlated; one retrospective provider/year "
        "cannot establish profitability. No Sharpe, significance test or "
        "model promotion."
    ),
    (
        "Final holdings remain open at December 31 23:00; END is used "
        "solely for exposure duration, never an invented price or sale."
    ),
    (
        "Spread/slippage are already embedded in execution prices; "
        "reported decomposition is not subtracted twice."
    ),
)


def json_bytes(value):
    """Canonical scientific serialization, independent of locale and Decimal context."""

    def default(item):
        if is_dataclass(item):
            return asdict(item)
        if isinstance(item, (Decimal, datetime)):
            return str(item) if isinstance(item, Decimal) else item.isoformat()
        raise TypeError(f"Unsupported scientific value: {type(item).__name__}")

    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=default,
        )
        + "\n"
    ).encode()


def fingerprint(value):
    return sha256(json_bytes(value)).hexdigest()


def loader_snapshot_sha256(forecast_result, execution_result, lineage):
    """Bind already verified in-memory values; not a replacement source verifier.

    Mapping/container order is irrelevant here. The adapter separately rejects
    chronology changes inside each source stream. Call immediately at the trusted
    loader boundary; do not recompute this to bless mutated prices or metadata.
    """
    hashes, accounts = forecast_result
    metadata, prices = execution_result
    return fingerprint(
        {
            "forecast_hashes": hashes,
            "accounts": [[s, m, accounts[s, m]] for s, m in sorted(accounts)],
            "execution_metadata": {
                **metadata,
                "sources": sorted(
                    metadata["sources"], key=lambda r: (r["symbol"], r["month"])
                ),
            },
            "prices": [[s, at, prices[s, at]] for s, at in sorted(prices)],
            "lineage": lineage,
        }
    )


def _validate_lineage(lineage):
    require(
        lineage["experiment_version"] == "stage-2b-v1"
        and lineage["fit_partition"] == "train"
        and lineage["evaluation_partition"] == "validation"
        and tuple(lineage["feature_order"]) == FEATURES,
        "Wrong model recipe/feature order/partition.",
    )
    require(
        lineage["input"]["input_hashes"]
        == {
            "research.csv": RESEARCH_SHA256,
            "manifest.json": RESEARCH_MANIFEST_SHA256,
        }
        and lineage["input"]["settling_seconds"] == 60,
        "Wrong research lineage declarations.",
    )
    require(
        lineage["output_sha256"]["validation_predictions.csv"] == FORECAST_SHA256,
        "Wrong prediction lineage.",
    )
    require(set(lineage["markets"]) == set(SYMBOLS), "Wrong lineage markets.")
    for symbol, count in zip(SYMBOLS, (13782, 13783), strict=True):
        market = lineage["markets"][symbol]
        require(
            market["training_count"] == count and market["validation_count"] == 2195,
            "Wrong recipe training/validation counts.",
        )
        params = market["model_parameters"]
        require(
            params["ridge"]
            == {
                "alpha": 1.0,
                "copy_X": True,
                "fit_intercept": True,
                "max_iter": None,
                "positive": False,
                "random_state": None,
                "solver": "svd",
                "tol": 0.0001,
            }
            and params["ridge_scaler"]
            == {
                "copy": True,
                "with_mean": True,
                "with_std": True,
            },
            "Wrong fixed Ridge/scaler parameters.",
        )
        scaler = market["fitted_scaler"]
        require(scaler["n_samples_seen"] == count, "Scaler must be training-only.")
        for name in ("mean", "scale"):
            require(len(scaler[name]) == 5, "Wrong scaler feature count.")
            for value in scaler[name]:
                require(not isinstance(value, bool), "Invalid scaler value.")
                value = number(D(str(value)))
                require(name != "scale" or value > 0, "Invalid scaler scale.")


@dataclass(frozen=True)
class HistoricalBundle:
    forecasts: tuple[tuple[HistoricalForecast, ...], ...]
    references: tuple[tuple[HourlyReference, ...], ...]
    source_evidence_json: bytes


def adapt_inputs(forecast_result, execution_result, *, evidence):
    """Validate full two-market loader-shaped inputs, without invoking any loader.

    evidence holds status, protocol/version/revision, exact declared paths,
    recipe identity kind, Stage 2B manifest metadata and a loader snapshot digest.
    Only synthetic_test evidence is accepted in this stage. A future authorised
    wrapper must authenticate bytes before supplying any genuine loader results.
    """
    try:
        require(evidence["status"] == "synthetic_test", "Synthetic-only adapter gate.")
        require(
            (
                evidence["protocol_version"],
                evidence["protocol_sha256"],
                evidence["protocol_git_revision"],
            )
            == (PROTOCOL_VERSION, PROTOCOL_SHA256, PROTOCOL_REVISION),
            "Source/protocol mismatch.",
        )
        require(
            evidence["source_paths"] == SOURCE_PATHS,
            "Wrong declared original source paths.",
        )
        require(
            evidence["recipe_identity_kind"] == "stage2b_manifest_sha256"
            and evidence["model_recipe_sha256"] == RECIPE_SHA256,
            "Wrong manifest-anchored recipe identity.",
        )
        hashes, accounts = forecast_result
        metadata, prices = execution_result
        require(
            hashes
            == {
                "manifest.json": RECIPE_SHA256,
                "validation_predictions.csv": FORECAST_SHA256,
            },
            "Unpinned forecast hashes.",
        )
        require(
            metadata["manifest_sha256"] == HOURLY_MANIFEST_SHA256
            and metadata["output_sha256"]
            == {
                "hourly_opens.csv": HOURLY_SHA256,
                "acquisition.json": ACQUISITION_SHA256,
            },
            "Unpinned hourly/acquisition hashes.",
        )
        require(
            metadata["coverage"]
            == {
                "start": START.isoformat(),
                "end_exclusive": END.isoformat(),
                "interval_seconds": 3600,
                "row_counts": {s: 8784 for s in SYMBOLS},
                "missing": 0,
                "rejected": 0,
                "complete": True,
            },
            "Wrong hourly coverage.",
        )
        _validate_lineage(evidence["stage2b_manifest"])
        require(
            set(accounts) == {(s, m) for s in SYMBOLS for m in MODELS},
            "Expected exact two-market/four-model loader accounts.",
        )
        sources = {}
        for row in metadata["sources"]:
            key = row["symbol"], row["month"]
            require(
                key in MONTHLY_ZIP_SHA256 and key not in sources,
                "Missing/duplicate/wrong market-month source.",
            )
            symbol, month = key
            url = (
                "https://data.binance.vision/data/spot/monthly/klines/"
                f"{symbol}/1h/{symbol}-1h-{month}.zip"
            )
            require(
                row["sha256"] == MONTHLY_ZIP_SHA256[key]
                and row["interval"] == "1h"
                and row["url"] == url
                and row["checksum_url"] == url + ".CHECKSUM"
                and row["checksum_valid"] is True
                and row["complete"] is True
                and row["row_count"]
                == calendar.monthrange(2024, int(month[-2:]))[1] * 24,
                "Broken monthly ZIP/checksum association.",
            )
            digest(row["checksum_sha256"])
            observed = utc(datetime.fromisoformat(row["observed_at"]))
            require(observed >= END, "Expected retrospective acquisition timestamp.")
            sources[key] = row
        require(set(sources) == set(MONTHLY_ZIP_SHA256), "Incomplete monthly evidence.")
        require(
            len({r["checksum_sha256"] for r in sources.values()}) == 24,
            "Duplicate monthly checksum identity.",
        )
        forecasts, references = [], []
        require(len(prices) == 17568, "Wrong hourly mapping count.")
        require(all(s in SYMBOLS for s, _ in prices), "Unexpected price market.")
        for symbol in SYMBOLS:
            # Other models are validated for identity/grid only, never simulated.
            for model in MODELS:
                signals = accounts[symbol, model]
                require(len(signals) == 2195, "Wrong source horizon count.")
                for i, signal in enumerate(signals):
                    require(
                        signal.symbol == symbol
                        and signal.model == model
                        and signal.open_time == START - STEP + i * STEP
                        and signal.signal_time
                        == signal.open_time + STEP + timedelta(seconds=60),
                        "Wrong market/model or missing/duplicate/reordered horizon.",
                    )
                    number(signal.forecast)
            forecasts.append(
                tuple(
                    HistoricalForecast(
                        symbol,
                        f"binance:spot:{symbol}:14400:{s.open_time.isoformat()}:ridge",
                        s.open_time,
                        s.signal_time,
                        s.forecast,
                        FORECAST_SHA256,
                    )
                    for s in accounts[symbol, "ridge"]
                )
            )
            hours = [(at, price) for (s, at), price in prices.items() if s == symbol]
            require(len(hours) == 8784, "Wrong per-market hourly count.")
            refs = []
            for i, (at, price) in enumerate(hours):
                require(at == START + i * HOUR, "Missing/duplicate/reordered hour.")
                month = f"{at.year:04d}-{at.month:02d}"
                refs.append(
                    HourlyReference(
                        symbol,
                        f"binance:spot:{symbol}:3600:{at.isoformat()}",
                        at,
                        price,
                        HOURLY_SHA256,
                        sources[symbol, month]["sha256"],
                    )
                )
            references.append(tuple(refs))
        require(
            evidence["loader_snapshot_sha256"]
            == loader_snapshot_sha256(
                forecast_result, execution_result, evidence["stage2b_manifest"]
            ),
            "Supplied loader values/metadata changed after snapshot verification.",
        )
        retained = {
            **evidence,
            "adapted_records_sha256": fingerprint([forecasts, references]),
            "row_identity_locations": {
                "forecasts": "decisions.json: forecast.record_id and source_open",
                "references": "hourly_marks.json: reference.record_id and at",
                "forecast_format": (
                    "binance:spot:{symbol}:14400:{UTC source open}:ridge"
                ),
                "reference_format": "binance:spot:{symbol}:3600:{UTC hourly open}",
            },
            "forecast_hashes": hashes,
            "execution_metadata": {
                **metadata,
                "sources": [sources[k] for k in sorted(sources)],
            },
            "authentication": "mocked_identifiers_not_genuine_file_authentication",
        }
        return HistoricalBundle(
            tuple(forecasts), tuple(references), json_bytes(retained)
        )
    except (KeyError, TypeError, AttributeError, IndexError, ArithmeticError) as error:
        raise ValueError("Malformed historical loader evidence.") from error


@dataclass(frozen=True)
class AnalyticalAccount:
    label: str
    initial: Account
    final: Account
    trades: tuple
    marks: tuple[HistoricalMark, ...]
    status: str = "available"
    reason: str | None = None


def benchmark(symbol, label, references):
    """Independent funded cash/B&H; initial 00:00 reference only, no later retry."""
    require(label in ("cash", "buy_and_hold"), "Unknown analytical benchmark.")
    refs = tuple(references)
    require(bool(refs) and refs[0].at == START, "Missing benchmark inception.")
    require(
        all(
            r.symbol == symbol and r.at == START + i * HOUR for i, r in enumerate(refs)
        ),
        "Invalid benchmark hourly references.",
    )
    config_hash = sha256(historical_json(BASE_CONFIG).encode()).hexdigest()
    portfolio = Portfolio(
        f"{KIND}:{symbol}:analytical:{label}:{config_hash}",
        symbol,
        START,
        config_hash,
        PROTOCOL_SHA256,
        RECIPE_SHA256,
        strategy_id=f"analytical_{label}",
    )
    initial = account = fund_account(Account(portfolio), START)
    trades = ()
    if label == "buy_and_hold":
        with localcontext(money_context()):
            quantity = affordable_quantity(
                INITIAL_CASH, refs[0].price * D("1.0003"), BASE_CONFIG.quantity_step
            )
        if quantity == 0:
            return AnalyticalAccount(
                label,
                initial,
                initial,
                (),
                (),
                "unavailable",
                "initial_full_fee_affordable_buy_infeasible",
            )
        trade = calculate_historical_trade(
            account,
            Side.BUY,
            refs[0],
            at=START,
            identity=portfolio.key + ":initial_buy",
        )
        account = apply_trade(account, trade)
        trades = (trade,)
    require(replay(portfolio, trades) == account, "Benchmark replay mismatch.")
    marks = tuple(
        value_historical(account, r, ledger_seq=account.ledger_seq) for r in refs
    )
    return AnalyticalAccount(label, initial, account, trades, marks)


def ratio(numerator, denominator):
    """80-significant-digit HALF_EVEN quotient; exact operands remain in reports."""
    if not denominator:
        return None
    with localcontext(money_context(division=True)):
        return D(numerator) / D(denominator)


def _account_state(account, mark=None):
    return {
        "cash": account.cash,
        "asset_units": account.quantity,
        "remaining_cost_basis": account.basis,
        "weighted_average_cost": ratio(account.basis, account.quantity),
        "realised_pnl": account.realised,
        "fees": account.fees,
        "unrealised_pnl": mark.unrealised if mark else D(0),
        "reference_marked_equity": mark.equity if mark else INITIAL_CASH,
        "ledger_seq": account.ledger_seq,
    }


def cost_summary(trades, references):
    """Costs from this account's actual hypothetical quantity/path, by side."""
    by_time = {r.at: r for r in references} if trades else {}
    result = {}
    with localcontext(money_context()):
        for side in Side:
            selected = [t for t in trades if t.side == side]
            notional = sum((t.notional for t in selected), D(0))
            raw = sum((t.quantity * by_time[t.at].price for t in selected), D(0))
            result[side.value] = {
                "count": len(selected),
                "notional": notional,
                "turnover_initial_funding": notional / INITIAL_CASH,
                "fees": sum((t.fee for t in selected), D(0)),
                "hypothetical_half_spread": raw * D("0.0001"),
                "hypothetical_slippage": raw * D("0.0002"),
            }
    return result


def verify_account(initial, trades, marks, final):
    """Replay each ledger prefix once, then compare EVERY original hourly mark."""
    require(initial == replay(initial.portfolio, ()), "Invalid initial funding.")
    states = {1: initial}
    account = initial
    for trade in trades:
        account = apply_trade(account, trade)
        states[account.ledger_seq] = account
    require(
        account == final and replay(initial.portfolio, trades) == final,
        "Final shared-accounting replay mismatch.",
    )
    cursor = 0
    for i, mark in enumerate(marks):
        while cursor < len(trades) and trades[cursor].at <= mark.reference.at:
            cursor += 1
        require(
            mark.reference.at == START + i * HOUR and mark.ledger_seq == 1 + 2 * cursor,
            "Mark chronology/ledger-prefix mismatch.",
        )
        require(
            mark
            == value_historical(
                states[mark.ledger_seq], mark.reference, ledger_seq=mark.ledger_seq
            ),
            "Hourly mark replay mismatch.",
        )
    return {
        "funding_events": 1,
        "fill_count": len(trades),
        "signed_postings": 2 * len(trades),
        "last_ledger_seq": final.ledger_seq,
        "replayed_hourly_marks": len(marks),
        "reconciled": True,
    }


def period_observations(account_id, marks, trades):
    """Frozen hourly calendar returns, including final 23h day/partial December.

    Boundary marks are post-trade. B&H inception cost precedes its first mark;
    that cost remains in funding-relative total return, not the first daily return.
    Flow reporting uses actual fill dates (including inception) independently of
    mark-to-mark return attribution.
    """
    by_time = {m.reference.at: m for m in marks}
    references = tuple(m.reference for m in marks)
    rows = []
    if not marks:
        return rows
    last = marks[-1].reference.at
    with localcontext(money_context()):
        for period in ("daily", "monthly"):
            starts = [
                at
                for at in by_time
                if at.hour == 0 and (period == "daily" or at.day == 1)
            ]
            for start in starts:
                boundary = start + (
                    timedelta(days=1)
                    if period == "daily"
                    else timedelta(days=calendar.monthrange(start.year, start.month)[1])
                )
                end = min(boundary, last)
                if end <= start:
                    continue
                first, final = by_time[start], by_time[end]
                change = final.equity - first.equity
                flows = [t for t in trades if start <= t.at < boundary]
                costs = cost_summary(flows, references)
                rows.append(
                    {
                        "account_id": account_id,
                        "period": period,
                        "start": start,
                        "end": end,
                        "complete": end == boundary,
                        "observed_seconds": (end - start) // timedelta(seconds=1),
                        "missing_boundary_seconds": (boundary - end)
                        // timedelta(seconds=1),
                        "start_equity": first.equity,
                        "end_equity": final.equity,
                        "pnl": change,
                        "return": ratio(change, first.equity),
                        "buy_count": costs["BUY"]["count"],
                        "sell_count": costs["SELL"]["count"],
                        **{
                            f"{side.lower()}_{name}": costs[side][name]
                            for side in ("BUY", "SELL")
                            for name in (
                                "notional",
                                "fees",
                                "hypothetical_half_spread",
                                "hypothetical_slippage",
                            )
                        },
                    }
                )
    return rows


def summarize_account(initial, trades, marks, final, *, decisions=(), end=END):
    """Account summary; duration uses timestamps, never an assumed mark frequency."""
    checked = verify_account(initial, trades, marks, final)
    require(bool(marks), "Cannot summarize unavailable marks.")
    with localcontext(money_context()):
        peak, maximum = INITIAL_CASH, D(0)
        for mark in marks:
            peak = max(peak, mark.equity)
            maximum = max(maximum, ratio(peak - mark.equity, peak))
        invested_seconds, entered = 0, None
        for trade in trades:
            if trade.side == Side.BUY:
                entered = trade.at
            else:
                invested_seconds += (trade.at - entered) // timedelta(seconds=1)
                entered = None
        if entered is not None:
            invested_seconds += (end - entered) // timedelta(seconds=1)
        invested_marks = sum(m.account.quantity > 0 for m in marks)
        costs = cost_summary(trades, [m.reference for m in marks])
        periods = period_observations(initial.portfolio.key, marks, trades)
        complete = [
            r["return"] for r in periods if r["period"] == "daily" and r["complete"]
        ]
        counts = Counter(d.action.value for d in decisions)
        return {
            "account_id": initial.portfolio.key,
            "symbol": initial.portfolio.symbol,
            "initial_funding": _account_state(initial),
            "first_hourly_mark": _account_state(marks[0].account, marks[0]),
            "final": _account_state(final, marks[-1]),
            "pnl": marks[-1].equity - INITIAL_CASH,
            "total_return": (marks[-1].equity - INITIAL_CASH) / INITIAL_CASH,
            "decision_count": len(decisions),
            "decisions_by_action": {a.value: counts[a.value] for a in Action},
            "targets": {
                "long": sum(d.target == 1 for d in decisions),
                "cash": sum(d.target == 0 for d in decisions),
            },
            "costs_by_side": costs,
            "two_sided_turnover_initial_funding": (
                costs["BUY"]["notional"] + costs["SELL"]["notional"]
            )
            / INITIAL_CASH,
            "exposure_seconds": invested_seconds,
            "period_seconds": (end - START) // timedelta(seconds=1),
            "exposure_fraction": ratio(
                invested_seconds, (end - START) // timedelta(seconds=1)
            ),
            "invested_hourly_marks": invested_marks,
            "hourly_mark_count": len(marks),
            "invested_hourly_mark_fraction": ratio(invested_marks, len(marks)),
            "ending_exposed": final.quantity > 0,
            "maximum_observed_hourly_drawdown": maximum,
            "complete_day_count": len(complete),
            "complete_day_mean_return": ratio(sum(complete, D(0)), len(complete)),
            "complete_day_min_return": min(complete) if complete else None,
            "complete_day_max_return": max(complete) if complete else None,
            "reconciliation": checked,
        }, periods


def ledger_records(initial, trades):
    records = [
        {
            "sequence": 1,
            "at": START,
            "event": "funding",
            "asset": "USDT",
            "amount": INITIAL_CASH,
        }
    ]
    for trade in trades:
        records.extend(
            {
                "sequence": trade.ledger_seq_before + i + 1,
                "at": trade.at,
                "event": "hypothetical_fill",
                "trade_id": trade.identity,
                **asdict(posting),
            }
            for i, posting in enumerate(trade.postings)
        )
    return records


def policy():
    return {
        "kind": KIND,
        "protocol_version": PROTOCOL_VERSION,
        "protocol_sha256": PROTOCOL_SHA256,
        "protocol_git_revision": PROTOCOL_REVISION,
        "config": asdict(BASE_CONFIG),
        "config_sha256": sha256(historical_json(BASE_CONFIG).encode()).hexdigest(),
        "markets": SYMBOLS,
        "start": START,
        "end_exclusive": END,
        "source_count_per_market": 2195,
        "hourly_count_per_market": 8784,
        "source_start": START - STEP,
        "source_last": END - 3 * STEP,
        "last_mark": END - HOUR,
        "initial_funding_per_account": INITIAL_CASH,
        "strategy": (
            "ridge_sign_v1: prediction strictly > 1e-12 targets long; otherwise cash"
        ),
        "timing": (
            "source open +4h+60s assumed availability; strictly next hourly "
            "opening; trade before mark"
        ),
        "transitions": (
            "flat/long BUY; long/long HOLD; long/cash SELL ALL; flat/cash "
            "CASH_NOOP; new signal for re-entry"
        ),
        "missingness": (
            "abort on every missing/invalid source, including HOLD/cash "
            "hours; no synthetic misses in publication"
        ),
        "fees": "10 bps each side; USDT quantum 1e-8 ROUND_UP",
        "arithmetic": (
            "money: exact 160 digits, Inexact trapped; ratios/WAC: 80 "
            "significant digits HALF_EVEN; exact ratio operands retained"
        ),
        "valuation": (
            "historical-opening-reference-v1; original hourly open; no forced "
            "final sale"
        ),
        "daily": (
            "consecutive 00:00 UTC marks only; Dec 31 00:00 to 23:00 partial, "
            "excluded from complete-day statistics"
        ),
        "monthly": (
            "month-opening 00:00 marks; all 12 months; December partial by one hour"
        ),
        "flows": (
            "actual UTC fill date; [period start,next boundary); B&H "
            "inception costs precede first post-buy mark and remain in "
            "funding-relative return"
        ),
        "drawdown": "inception funding then observed hourly equity only, not intrabar",
        "exposure": (
            "transition timestamps through END for duration only; hourly "
            "invested fraction separate"
        ),
        "benchmarks": (
            "independent 10000-USDT cash and initial-00:00 max-affordable "
            "base-cost buy-and-hold; infeasible initial buy unavailable"
        ),
        "comparisons": (
            "matched marks; difference in funding-relative returns uses 10000 "
            "each; relative endpoint difference uses benchmark endpoint equity"
        ),
        "limitations": LIMITATIONS,
    }


def evaluate_bundle(bundle):
    """Run only the frozen base case, plus separately identified analytical accounts."""
    require(isinstance(bundle, HistoricalBundle), "Expected validated bundle.")
    # Reconstructing a bundle directly is not a substitute for adapt_inputs.
    source = json.loads(bundle.source_evidence_json)
    require(
        source["adapted_records_sha256"]
        == fingerprint([bundle.forecasts, bundle.references]),
        "Adapted records changed after source validation.",
    )
    require(
        len(bundle.forecasts) == len(bundle.references) == 2,
        "Expected exactly two markets.",
    )
    require(
        source["status"] == "synthetic_test"
        and source["protocol_sha256"] == PROTOCOL_SHA256,
        "Synthetic/protocol gate.",
    )
    outputs = {
        name: {} for name in ("decisions", "orders_trades", "ledger", "hourly_marks")
    }
    summary, periods = {}, []
    for index, symbol in enumerate(SYMBOLS):
        forecasts, refs = bundle.forecasts[index], bundle.references[index]
        require(len(forecasts) == 2195 and len(refs) == 8784, "Full grids required.")
        ridge = replay_historical(
            symbol,
            forecasts,
            refs,
            protocol_sha256=PROTOCOL_SHA256,
            model_recipe_sha256=RECIPE_SHA256,
        )
        accounts = [
            (
                "ridge",
                ridge.initial_account,
                ridge.final_account,
                tuple(f.trade for f in ridge.fills),
                ridge.marks,
                ridge.decisions,
                ridge.fills,
                "available",
                None,
            )
        ]
        for label in ("cash", "buy_and_hold"):
            b = benchmark(symbol, label, refs)
            accounts.append(
                (
                    label,
                    b.initial,
                    b.final,
                    b.trades,
                    b.marks,
                    (),
                    (),
                    b.status,
                    b.reason,
                )
            )
        summary[symbol] = {}
        for (
            label,
            initial,
            final,
            trades,
            marks,
            decisions,
            fills,
            status,
            reason,
        ) in accounts:
            key = initial.portfolio.key
            outputs["decisions"][key] = decisions
            outputs["orders_trades"][key] = {
                "label": label,
                "status": status,
                "reason": reason,
                "initial": initial,
                "final": final,
                "trades": trades,
                "ridge_order_fills": fills,
            }
            outputs["ledger"][key] = ledger_records(initial, trades)
            outputs["hourly_marks"][key] = marks
            if status == "unavailable":
                summary[symbol][label] = {
                    "account_id": key,
                    "status": status,
                    "reason": reason,
                    "pnl": None,
                    "total_return": None,
                    "reconciliation": verify_account(initial, trades, marks, final),
                }
                continue
            report, rows = summarize_account(
                initial, trades, marks, final, decisions=decisions
            )
            summary[symbol][label] = {"status": status, **report}
            periods.extend(rows)
        comparisons = {}
        with localcontext(money_context()):
            for label in ("cash", "buy_and_hold"):
                r, b = summary[symbol]["ridge"], summary[symbol][label]
                comparisons[label] = (
                    None
                    if b["status"] == "unavailable"
                    else {
                        "common_hourly_marks": 8784,
                        "equity_difference": r["final"]["reference_marked_equity"]
                        - b["final"]["reference_marked_equity"],
                        "return_difference_initial_funding": r["total_return"]
                        - b["total_return"],
                        "relative_endpoint_difference": ratio(
                            r["final"]["reference_marked_equity"]
                            - b["final"]["reference_marked_equity"],
                            b["final"]["reference_marked_equity"],
                        ),
                        "benchmark_endpoint_denominator": b["final"][
                            "reference_marked_equity"
                        ],
                        "initial_funding_denominator_each": INITIAL_CASH,
                    }
                )
        summary[symbol]["comparisons"] = comparisons
    return {
        "policy": policy(),
        "source_evidence": source,
        **outputs,
        "summary": {
            "kind": KIND,
            "status": "synthetic_test",
            "coverage": {
                "markets": SYMBOLS,
                "source_count_per_market": 2195,
                "hourly_count_per_market": 8784,
                "monthly_sources": 24,
                "missing": 0,
                "rejected": 0,
            },
            "limitations": LIMITATIONS,
            "markets": summary,
        },
        "daily_monthly": periods,
    }


def scientific_payloads(report):
    files = {
        f"{name}.json": json_bytes(report[name])
        for name in (
            "policy",
            "source_evidence",
            "decisions",
            "orders_trades",
            "ledger",
            "summary",
        )
    }
    # Account identity belongs to the enclosing key; the immutable trade history
    # is retained once in orders_trades/ledger. Never repeat a growing trade-ID
    # tuple at every hourly observation (quadratic serialization size).
    files["hourly_marks.json"] = json_bytes(
        {
            key: [
                {
                    "reference": mark.reference,
                    "ledger_seq": mark.ledger_seq,
                    "account": {
                        field: getattr(mark.account, field)
                        for field in (
                            "cash",
                            "quantity",
                            "basis",
                            "realised",
                            "fees",
                            "ledger_seq",
                            "at",
                        )
                    },
                    "equity": mark.equity,
                    "unrealised": mark.unrealised,
                    "kind": mark.kind,
                    "valuation_policy": mark.valuation_policy,
                }
                for mark in marks
            ]
            for key, marks in report["hourly_marks"].items()
        }
    )
    rows = json.loads(json_bytes(report["daily_monthly"]))
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    files["daily_monthly.csv"] = buffer.getvalue().encode()
    lines = [
        "# Synthetic historical simulation — not genuine 2024 results",
        "",
        *[f"- {text}" for text in LIMITATIONS],
        "",
        "Exact Decimal values below; ratios use the declared 80-digit convention.",
        (
            "Daily/monthly boundaries use post-trade marks. B&H inception "
            "cost is included in total return but precedes its first "
            "daily/monthly interval."
        ),
        "",
        "| Market | Account | Status | Final equity | P&L | Total return |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for symbol in SYMBOLS:
        for label in ("ridge", "cash", "buy_and_hold"):
            row = report["summary"]["markets"][symbol][label]
            final = row.get("final", {}).get("reference_marked_equity", "undefined")
            lines.append(
                f"| {symbol} | {label} | {row['status']} | {final} | "
                f"{row['pnl']} | {row['total_return']} |"
            )
    lines.extend(
        [
            "",
            "All calendar months (December is partial by one hour):",
            "",
            "| Account | Month | Complete | Mark-to-mark P&L | Return |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        if row["period"] == "monthly":
            lines.append(
                f"| {row['account_id']} | {row['start'][:7]} | {row['complete']} | "
                f"{row['pnl']} | {row['return']} |"
            )
    files["summary.md"] = ("\n".join(lines) + "\n").encode()
    return files

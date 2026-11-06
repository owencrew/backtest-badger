"""Mappings between revision 0002 rows and immutable Stage 4B.1 evidence."""

import json
from decimal import localcontext
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

from backtest_badger.paper_execution import Order
from backtest_badger.paper_strategy import evaluate_strategy
from backtest_badger.paper_types import (
    EXECUTION_POLICY,
    FEE_QUANTUM,
    FEE_RATE,
    SLIPPAGE,
    STEP,
    VALUATION_POLICY,
    Action,
    Balances,
    D,
    Decision,
    Filters,
    Forecast,
    Portfolio,
    Quote,
    identifier,
    money_context,
)


def identity(portfolio_id, kind, key):
    identifier(key)
    return uuid5(
        NAMESPACE_URL, json.dumps(["backtest-badger", str(portfolio_id), kind, key])
    )


def fingerprint(text):
    return sha256(text.encode("utf-8")).hexdigest()


def configuration(symbol, model_recipe_sha256, cohort):
    """Return the v1 configuration frozen for a market and inception cohort."""
    identifier(cohort)
    return dict(
        schema="stage-4a-v1",
        cohort=cohort,
        venue="binance",
        market_type="spot",
        symbol=symbol,
        strategy="ridge_sign",
        strategy_version="1",
        model="ridge",
        model_recipe_sha256=model_recipe_sha256,
        threshold="1e-12",
        target_weights=[0, 1],
        fee_rate=str(FEE_RATE),
        fee_quantum=str(FEE_QUANTUM),
        slippage=str(SLIPPAGE),
        execution=EXECUTION_POLICY,
        valuation=VALUATION_POLICY,
        cost_basis="weighted_average",
        filters="effective-market-filters-v1",
        filter_ttl_seconds=3600,
        order_ttl_seconds=30,
        quote_rtt_seconds=2,
        receipt_ttl_seconds=1,
        exit_retry_seconds=300,
        source_interval_seconds=14400,
        availability_seconds=60,
        deadline_seconds=960,
        risk_exit_misses=2,
        mark_offset_seconds=600,
        mark_window_seconds=300,
    )


def canonical(config):
    return json.dumps(
        config,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def portfolio(row):
    return Portfolio(
        row["portfolio_key"],
        row["base_asset"] + row["quote_asset"],
        row["inception_at"],
        row["strategy_config_sha256"],
        row["protocol_sha256"],
        row["model_recipe_sha256"],
        strategy_id=row["strategy_id"],
        strategy_version=row["strategy_version"],
    )


def decision_fields(pid, d, artifact_relpath, prediction_id):
    f = d.forecast
    exit_required = d.action == Action.EXIT_REQUIRED
    kind = "FORECAST" if f else ("RISK_EXIT" if exit_required else "MISSED_SIGNAL")
    return dict(
        portfolio_id=pid,
        decision_key=d.identity,
        kind=kind,
        source_open_time=d.source_open,
        target_close_boundary=d.source_open + 2 * STEP,
        forecast_record_id=f.record_id if f else None,
        prediction_id=prediction_id,
        artifact_relpath=artifact_relpath,
        forecast_file_sha256=f.file_sha256 if f else None,
        forecast_content_sha256=f.content_sha256 if f else None,
        forecast_issued_at=f.issued_at if f else None,
        forecast_observed_at=f.observed_at if f else None,
        model_forecast=f.prediction if f else None,
        model_recipe_sha256=f.model_recipe_sha256 if f else None,
        cohort=f.cohort if f else None,
        automation_sha256=f.automation_sha256 if f else None,
        target_exposure=evaluate_strategy(f.prediction) if f else None,
        decision_result=d.action.value,
        is_exit_obligation=exit_required,
        missed_streak=d.missed_streak,
        obligation_key=d.obligation_id,
        reason_code=d.reason,
        strategy_config_sha256=d.portfolio.config_sha256,
        decided_at=d.at,
        created_at=d.at,
    )


def decision(p, d):
    f = None
    if d["kind"] == "FORECAST":
        f = Forecast(
            p,
            d["forecast_record_id"],
            d["source_open_time"],
            d["forecast_issued_at"],
            d["forecast_observed_at"],
            d["model_forecast"],
            d["forecast_file_sha256"],
            d["forecast_content_sha256"],
            d["model_recipe_sha256"],
            d["automation_sha256"],
            d["cohort"],
        )
    return Decision(
        d["decision_key"],
        p,
        d["decided_at"],
        Action(d["decision_result"]),
        d["reason_code"],
        d["missed_streak"],
        d["source_open_time"],
        f,
        d["obligation_key"],
    )


def order(p, d, o):
    balances = Balances(
        p,
        o["budget_cash_snapshot"],
        o["base_qty_snapshot"],
        o["snapshot_seq"],
        o["snapshot_at"],
    )
    return Order(
        o["client_order_key"],
        decision(p, d),
        balances,
        o["run_id"],
        o["submitted_at"],
        o["expires_at"],
    )


def quote_fields(q):
    with localcontext(money_context()):
        latency = q.elapsed_seconds * 1000 if q.elapsed_seconds is not None else None
    return dict(
        quote_key=q.identity,
        run_id=q.run_id,
        request_started_at=q.request_started_at,
        response_received_at=q.response_received_at,
        latency_ms=latency,
        source_url=q.source_url,
        http_status=q.http_status,
        raw_body=q.raw_body,
        raw_body_sha256=q.payload_sha256,
        bid_price=q.bid,
        ask_price=q.ask,
        bid_qty=q.bid_quantity,
        ask_qty=q.ask_quantity,
    )


def quote(p, e):
    with localcontext(money_context()):
        elapsed = e["latency_ms"] / 1000 if e["latency_ms"] is not None else None
    return Quote(
        e["quote_key"],
        e["run_id"],
        p.symbol,
        e["request_started_at"],
        e["response_received_at"],
        e["bid_price"],
        e["ask_price"],
        e["bid_qty"],
        e["ask_qty"],
        e["raw_body_sha256"],
        e["raw_body"],
        e["source_url"],
        http_status=e["http_status"],
        elapsed_seconds=elapsed,
    )


LIMITS = ("step", "min_quantity", "max_quantity", "min_notional", "max_notional")


def filter_fields(f):
    rules = {
        key: str(getattr(f, key)) if getattr(f, key) is not None else None
        for key in LIMITS
    }
    return dict(
        filter_rules_json=rules | dict(symbol=f.symbol, version=f.version),
        filter_observed_at=f.observed_at,
        filter_raw_sha256=f.payload_sha256,
    )


def filters(e):
    rules = e["filter_rules_json"]
    return Filters(
        rules["symbol"],
        e["filter_observed_at"],
        e["filter_raw_sha256"],
        *(D(rules[k]) if rules[k] is not None else None for k in LIMITS),
        version=rules["version"],
    )

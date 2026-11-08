"""Private source archive. Database evidence names immutable SHA-256 objects."""

import json
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256

from backtest_badger import forward
from backtest_badger import forward_evaluation as evaluation
from backtest_badger import paper_persistence as store
from backtest_badger import paper_records as records
from backtest_badger.paper_artifacts import (
    directory,
    publish_once,
    read_original,
    retain_body,
)
from backtest_badger.paper_clock import Sample
from backtest_badger.paper_forward_adapter import EvidenceError, Observation, Original
from backtest_badger.paper_market_data import (
    LIMIT,
    QUOTE,
    Response,
    effective_filters,
    retained_filters,
)
from backtest_badger.paper_reconciliation import (
    IntegrityIssue,
    inspect_portfolio,
    transaction,
)
from backtest_badger.paper_recovery import boundary
from backtest_badger.paper_types import (
    EXECUTION_POLICY,
    VALUATION_POLICY,
    digest,
    require,
)


def original_bytes(root, pin, limit=1024 * 1024):
    digest(pin)
    with directory(root) as fd:
        body = read_original(fd, pin + ".json", limit)
    require(sha256(body).hexdigest() == pin, "Corrupt private source object.")
    return body


def retain(root, body):
    pin = sha256(body).hexdigest()
    retain_body(root, body, pin)
    return pin


def verify_forecast(root, decision, name, prediction_id):
    f = decision.forecast
    require(
        name == forward.record_id(f.portfolio.symbol, f.source_open) + ".json",
        "Forecast path or horizon mismatch.",
    )
    record_bytes = original_bytes(root, f.file_sha256, 256 * 1024)
    prediction = evaluation.load_prediction(Original(name, record_bytes))
    record = prediction["record"]
    exact = json.loads(record_bytes, parse_float=Decimal)
    ridge = next(p for p in exact["predictions"] if p["model_id"] == "ridge")
    require(
        record["record_id"] == f.record_id
        and record["model"]["model_recipe_sha256"]
        == f.model_recipe_sha256
        == f.portfolio.model_recipe_sha256
        and prediction["content_sha256"] == f.content_sha256
        and evaluation.utc_time(record["issued_at"])
        == f.issued_at
        <= f.observed_at
        <= decision.at
        and ridge["prediction_id"] == prediction_id
        and ridge["predicted_log_return_4h"] == f.prediction,
        "Original forecast disagrees with durable decision.",
    )
    evidence = None
    if f.automation_sha256:
        raw = original_bytes(root, f.automation_sha256, 128 * 1024)
        j = evaluation.parse_journal(raw)
        start = evaluation.utc_time(j["started_at"])
        evidence = dict(
            filename=f"{start:%Y%m%dT%H%M%S%fZ}-{j['run_id']}.json",
            json_utf8=raw.decode(),
            file_sha256=f.automation_sha256,
        )
    evaluation.validate_cohort(
        {"name": f.cohort, "automation_evidence": evidence}, prediction, f.observed_at
    )

    return Observation(f, prediction_id, name, evidence, record_bytes)


def recovery_reader(root, state, discover):
    """Use the committed snapshot on restart and detect conflicting live claims."""
    saved = {d.source_open: d for d in state.decisions if d.forecast}

    def read(p, opened, clock):
        d = saved.get(opened)
        if d is None:
            return discover(p, opened, clock)
        f = d.forecast
        require(f.portfolio == p, "Unexpected recovery market.")
        try:
            original = verify_forecast(
                root, d, f.record_id + ".json", f.record_id + ":ridge"
            )
        except (ValueError, OSError, TypeError, KeyError, ArithmeticError) as exc:
            raise EvidenceError("missing_archived_original", f.record_id) from exc
        try:
            live = discover(p, opened, clock)
        except EvidenceError as exc:
            if exc.code != "original_unavailable":
                raise
            live = None
        if live is not None:
            require(
                replace(
                    live.forecast,
                    observed_at=f.observed_at,
                    automation_sha256=f.automation_sha256,
                )
                == f
                and bool(live.journal) == bool(original.journal),
                "Conflicting original at restart.",
            )
            if original.journal:
                before, after = (
                    evaluation.parse_journal(o.journal["json_utf8"].encode())
                    for o in (original, live)
                )
                require(
                    before["run_id"] == after["run_id"]
                    and before["started_at"] == after["started_at"]
                    and before["markets"][p.symbol] == after["markets"][p.symbol],
                    "Conflicting journal publisher at restart.",
                )
        return original

    return read


def record_archived_decision(conn, pid, root, decision, observation=None):
    """No financial decision may precede durable, re-readable source objects."""
    if decision.forecast is None:
        require(observation is None, "Unexpected forecast for a missing horizon.")
        return store.record_decision(conn, pid, decision)
    f = decision.forecast
    require(
        observation is not None and f == observation.forecast,
        "Different forecast observation.",
    )
    retain_body(root, observation.raw_record, f.file_sha256)
    if f.automation_sha256:
        require(
            observation.journal
            and observation.journal["file_sha256"] == f.automation_sha256,
            "Missing qualifying journal snapshot.",
        )
        retain_body(
            root, observation.journal["json_utf8"].encode(), f.automation_sha256
        )
    recovered = verify_forecast(
        root, decision, observation.artifact_relpath, observation.prediction_id
    )
    require(recovered == observation, "Observation differs from archived originals.")
    require(
        f.cohort != "timely_unattributed" or decision.at >= f.deadline,
        "Wait for original automation evidence before the deadline.",
    )
    return store.record_decision(
        conn,
        pid,
        decision,
        artifact_relpath=observation.artifact_relpath,
        prediction_id=observation.prediction_id,
    )


def archive_filters(root, response, portfolio, at):
    rules = effective_filters(response, portfolio, at)
    retain_body(root, response.body, rules.payload_sha256)
    return rules


def intent_reference(pid, oid, run_id):
    return (
        str(records.identity(pid, "filter-reference", str(oid) + ":" + run_id)) + ".ref"
    )


def submit_archived_order(conn, pid, root, order, attempt, source):
    """Bind the exact pre-intent filter observation even if the order never fills."""
    p = order.balances.portfolio
    require(source.run_id == order.run_id, "Intent needs this invocation's filters.")
    rules = archive_filters(root, source, p, order.submitted_at)
    oid = records.identity(pid, "order", order.identity)
    manifest = dict(
        portfolio=str(pid),
        order=str(oid),
        run_id=order.run_id,
        url=source.url,
        raw=rules.payload_sha256,
        start=source.start.wall.isoformat(),
        end=source.end.wall.isoformat(),
        ticks=[
            source.start.before_ns,
            source.start.after_ns,
            source.end.before_ns,
            source.end.after_ns,
        ],
    )
    pin = retain(root, forward.canonical(manifest))
    publish_once(root, intent_reference(pid, oid, order.run_id), pin.encode())
    return store.submit_order(conn, pid, order, attempt)


def verify_intent(root, p, order):
    oid, run = order["order_id"], order["run_id"]
    with directory(root) as fd:
        pin = read_original(
            fd, intent_reference(order["portfolio_id"], oid, run), 64
        ).decode()
    binding = json.loads(original_bytes(root, pin))
    require(
        binding["portfolio"] == str(order["portfolio_id"])
        and binding["order"] == str(oid)
        and binding["run_id"] == run,
        "Conflicting intent filter binding.",
    )
    ticks = binding["ticks"]
    start = Sample(evaluation.utc_time(binding["start"]), *ticks[:2])
    end = Sample(evaluation.utc_time(binding["end"]), *ticks[2:])
    raw = binding["raw"]
    source = Response(
        binding["url"], 200, original_bytes(root, raw), raw, start, end, run
    )
    return effective_filters(source, p, order["submitted_at"])


def archive_quote(root, quote):
    retain_body(root, quote.raw_body, quote.payload_sha256)
    return quote


def audit_sources(cur, pid, root):
    """Audit ledger and original sources in the caller's snapshot."""
    try:
        snap = inspect_portfolio(cur, pid)
    except IntegrityIssue:
        raise
    except (KeyError, IndexError, ArithmeticError, ValueError, TypeError) as exc:
        raise IntegrityIssue("invalid_portfolio_evidence", pid) from exc
    p = snap.account.portfolio
    try:
        row = cur.execute(
            "SELECT * FROM paper_portfolio WHERE portfolio_id=%s", (pid,)
        ).fetchone()
        for field in (
            "protocol_sha256",
            "implementation_sha256",
            "strategy_config_sha256",
            "execution_policy_sha256",
            "valuation_policy_sha256",
            "model_recipe_sha256",
        ):
            original_bytes(root, row[field])
        manifest = json.loads(original_bytes(root, row["implementation_sha256"]))
        require(
            isinstance(manifest, dict) and manifest, "Empty implementation manifest."
        )
        for pin in manifest.values():
            original_bytes(root, pin)
        for d in cur.execute(
            "SELECT * FROM paper_decision WHERE portfolio_id=%s AND kind='FORECAST'",
            (pid,),
        ):
            verify_forecast(
                root, records.decision(p, d), d["artifact_relpath"], d["prediction_id"]
            )
        intent_filters = {
            o["order_id"]: verify_intent(root, p, o)
            for o in cur.execute(
                "SELECT * FROM paper_order WHERE portfolio_id=%s", (pid,)
            )
        }
        for e in cur.execute(
            "SELECT * FROM paper_market_event WHERE portfolio_id=%s", (pid,)
        ):
            if e["raw_body_sha256"]:
                require(
                    original_bytes(root, e["raw_body_sha256"], LIMIT[QUOTE])
                    == e["raw_body"],
                    "Archived quote differs from database original.",
                )
            if e["reason_code"] == "INCEPTION":
                binding = json.loads(original_bytes(root, e["quote_key"]))
                require(
                    binding["quote_sha256"] == e["raw_body_sha256"],
                    "Inception quote mismatch.",
                )
                source_at = evaluation.utc_time(binding["filter_at"])
                require(
                    source_at <= e["request_started_at"], "Inception filter chronology."
                )
                pin = binding["filter_sha256"]
                retained_filters(
                    original_bytes(root, pin), p, source_at, pin, e["event_at"]
                )
            if e["filter_raw_sha256"]:
                pin = e["filter_raw_sha256"]
                rules = retained_filters(
                    original_bytes(root, pin),
                    p,
                    e["filter_observed_at"],
                    pin,
                    e["event_at"],
                )
                require(
                    rules == records.filters(e) == intent_filters[e["order_id"]],
                    "Effective rules differ from original filters.",
                )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        StopIteration,
        ArithmeticError,
    ) as exc:
        raise IntegrityIssue("original_evidence_integrity", pid) from exc
    return snap


def verify_portfolio(conn, pid, root):
    with transaction(conn, readonly=True) as cur:
        return audit_sources(cur, pid, root)


def scheduled_inception(
    conn, root, portfolio, config, implementation_pin, clock, read_filters, read_quote
):
    """
    One operator transaction, with an actual opening timestamp and no carried
    positions.
    """
    for pin in (
        portfolio.protocol_sha256,
        portfolio.model_recipe_sha256,
        implementation_pin,
    ):
        original_bytes(root, pin)
    require(
        retain(root, records.canonical(config).encode()) == portfolio.config_sha256,
        "Unpinned configuration.",
    )
    for policy in (EXECUTION_POLICY, VALUATION_POLICY):
        retain(root, policy.encode())
    pid = records.identity("v1", "portfolio", portfolio.key)
    with transaction(conn) as cur:
        prior = cur.execute(
            "SELECT * FROM paper_portfolio WHERE portfolio_id=%s", (pid,)
        ).fetchone()
        if prior:
            actual = records.portfolio(prior)
            require(
                actual == replace(portfolio, inception_at=actual.inception_at)
                and prior["implementation_sha256"] == implementation_pin
                and prior["activated_at"] is not None,
                "Conflicting inception.",
            )
            audit_sources(cur, pid, root)
            return pid
        started = clock.now()
        slot = boundary(started) + timedelta(minutes=10)
        require(
            slot <= started < slot + timedelta(minutes=5), "Outside inception window."
        )
        p = replace(portfolio, inception_at=started)
        receipt = store._create(cur, p, config, implementation_pin, started)
        require(
            receipt.created, "Concurrent inception; recover the committed identity."
        )
        store._fund(cur, pid, store._locked_portfolio(cur, pid), started)
        source = read_filters(p, clock)
        rules = archive_filters(root, source, p, clock.now())
        q = archive_quote(root, read_quote(p, clock))
        require(
            q.run_id == source.run_id == clock.run_id
            and started <= source.start.wall <= source.end.wall <= q.request_started_at,
            "Invalid inception source chronology.",
        )
        # The immutable quote key also pins the counterfactual's original filters.
        binding = dict(
            quote_key=q.identity,
            quote_sha256=q.payload_sha256,
            filter_sha256=rules.payload_sha256,
            filter_at=rules.observed_at.isoformat(),
        )
        q = replace(q, identity=retain(root, forward.canonical(binding)))
        store._mark(
            cur,
            pid,
            store._locked_portfolio(cur, pid),
            slot,
            clock.now(),
            q,
            None,
            True,
        )
        audit_sources(cur, pid, root)
        return pid

"""Fabricated diagnostic classification, clock uncertainty and stable identities."""

from dataclasses import replace
from datetime import timedelta

import pytest

from backtest_badger import paper_fixture as fx
from backtest_badger.paper_accounting import Account, fund_account
from backtest_badger.paper_operations import (
    CRITICAL,
    MISSING,
    WARNING,
    ClockHealth,
    Incident,
    diagnostics,
    incident_counts,
)
from backtest_badger.paper_records import identity
from backtest_badger.paper_recovery import Recovery
from backtest_badger.paper_strategy import State
from backtest_badger.paper_worker import Plan

PID = identity("v1", "portfolio", fx.COHORT)


@pytest.mark.parametrize("code", sorted(MISSING | WARNING | CRITICAL))
def test_incident_identity_survives_restarts(code):
    incident = Incident(code, PID, fx.OPEN)
    first = incident.report(fx.ISSUED)
    later = incident.report(fx.ISSUED + timedelta(minutes=5))
    assert first["observed_at"] != later["observed_at"]
    assert incident_counts([first, later]) == {first["key"]: 2}
    assert first["severity"] == (
        "integrity"
        if code in CRITICAL
        else "warning"
        if code in WARNING
        else "missingness"
    )
    with pytest.raises(ValueError):
        incident.report(fx.ISSUED, credentials="sensitive")


@pytest.mark.parametrize(
    ("result", "reason", "status", "code"),
    [
        ("MARKET_UNAVAILABLE", "rate_limited", 418, "provider_throttled"),
        ("FILTER_REJECTED", "rate_limited", 429, "provider_throttled"),
        ("FILTER_REJECTED", "unsupported_filter", 200, "filters_unavailable"),
        ("MARKET_UNAVAILABLE", "timeout", None, "quote_unavailable"),
        ("SIGNAL_INELIGIBLE", "awaiting_automation_evidence", None, "journal_pending"),
        ("INTEGRITY_PAUSE", "Conflicting journal publisher", None, "journal_conflict"),
        ("INTEGRITY_PAUSE", "invalid_original:bad", None, "invalid_automation"),
        ("INTEGRITY_PAUSE", "missing_archived_original", None, "original_missing"),
    ],
)
def test_plan_diagnostics(result, reason, status, code):
    p = fx.portfolio()
    state = State(fund_account(Account(p), fx.INCEPTION), fx.OPEN, fx.INCEPTION)
    view = Recovery(state, "ACTIVE", fx.INCEPTION)
    plan = Plan("fabricated", result, reason=reason, http_status=status)
    incidents = diagnostics(plan, view, fx.ISSUED, 241)
    assert {r["code"] for r in incidents} == {"runtime_excessive", code}


def test_clock_admission_requires_recent_bounded_external_status():
    sample = ClockHealth(True, fx.ISSUED, timedelta(milliseconds=30))
    assert sample.trusted(fx.ISSUED)
    for health in (
        replace(sample, synchronised=False),
        replace(sample, uncertainty=timedelta(seconds=1)),
        replace(sample, sampled_at=fx.INCEPTION - timedelta(minutes=5)),
        replace(sample, sampled_at=fx.ISSUED + timedelta(seconds=1)),
    ):
        assert not health.trusted(fx.ISSUED)

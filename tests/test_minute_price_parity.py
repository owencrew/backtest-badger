"""Parity on fabricated, independently labelled native sources only."""

from dataclasses import replace
from datetime import timedelta

import pytest
from test_paper_minute_historical import digest, pins, reference
from test_paper_minute_historical import offline_boundary as offline_boundary  # noqa: F401

from backtest_badger import paper_minute_historical as minute
from backtest_badger.minute_price_parity import audit_minute_price_parity
from backtest_badger.paper_historical import END, HOUR, START
from backtest_badger.paper_types import D


def grids(hours=4):
    hourly, minutes = [], []
    for symbol in minute.SYMBOLS:
        for i in range(hours):
            at = START + i * HOUR
            hourly.append(reference(at, symbol=symbol, interval=3600))
            minutes.append(reference(at, symbol=symbol))
    return tuple(hourly), tuple(minutes)


def audit(hourly, minutes, hours=4, **kwargs):
    options = {
        "hourly_source": pins(hourly, 3600),
        "minute_source": pins(minutes),
        "end_exclusive": START + hours * HOUR,
    }
    options.update(kwargs)
    options.setdefault(
        "expected_hourly_source_sha256",
        minute.price_source_sha256(options["hourly_source"]),
    )
    options.setdefault(
        "expected_minute_source_sha256",
        minute.price_source_sha256(options["minute_source"]),
    )
    return audit_minute_price_parity(hourly, minutes, **options)


def test_exact_parity_preserves_distinct_sources_and_determinism():
    hourly, minutes = grids()
    result = audit(hourly, minutes)
    assert result.direct_timing_comparison_permitted
    assert len(result.matched_identities) == result.expected_count == 8
    assert result.hourly_source.file_sha256 != result.minute_source.file_sha256
    assert result.hourly_source.manifest_sha256 != result.minute_source.manifest_sha256
    assert result.hourly_source.monthly_sources != result.minute_source.monthly_sources
    assert minute.scientific_json(result) == minute.scientific_json(
        audit(hourly, minutes)
    )
    assert result.status == "synthetic_test"


def test_all_exact_discrepancies_with_no_tolerance_or_substitution():
    hourly, minutes = grids()
    minutes = list(minutes)
    minutes[0] = replace(minutes[0], price=D("100.000000000000000000000000000001"))
    minutes[-1] = replace(minutes[-1], price=D("99.75"))
    result = audit(hourly, minutes)
    assert not result.direct_timing_comparison_permitted
    assert len(result.matched_identities) == 6
    assert len(result.discrepancies) == 2
    assert result.discrepancies[0].minute_minus_hourly == D("1e-30")
    assert result.discrepancies[1].minute_minus_hourly == D("-0.25")
    assert result.discrepancies[1].absolute_difference == D("0.25")
    assert result.discrepancies[0].hourly == hourly[0]
    assert result.discrepancies[0].minute == minutes[0]
    assert hourly[0].price == D(100)


@pytest.mark.parametrize("which", ["hourly", "minute"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reorder", "extra"])
def test_complete_discrepancy_inventory_and_fail_closed(which, mutation):
    hourly, minutes = map(list, grids())
    rows = hourly if which == "hourly" else minutes
    first = rows[0]
    if mutation == "missing":
        rows.pop(0)
    elif mutation == "duplicate":
        rows.insert(0, first)
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    else:
        rows.insert(
            4, reference(START + 4 * HOUR, interval=3600 if which == "hourly" else 60)
        )
    report = audit(hourly, minutes)
    assert not report.direct_timing_comparison_permitted
    if mutation == "missing":
        assert getattr(report, f"missing_{which}") == (("BTCUSDT", START),)
    elif mutation == "duplicate":
        assert getattr(report, f"duplicated_{which}") == (first, first)
        assert ("BTCUSDT", START) not in report.matched_identities
    elif mutation == "reorder":
        assert getattr(report, f"reordered_{which}_indices") == (1,)
    else:
        assert len(getattr(report, f"extra_{which}")) == 1


def test_both_sources_missing_same_identity_still_fails():
    h, m = grids()
    report = audit(h[1:], m[1:])
    assert report.missing_hourly == report.missing_minute == (("BTCUSDT", START),)
    assert not report.direct_timing_comparison_permitted


def test_duplicated_conflicting_prices_retained_not_silently_deduplicated():
    h, m = grids()
    report = audit(h, (m[0], replace(m[0], price=D(99)), *m[1:]))
    assert len(report.duplicated_minute) == 2
    assert len(report.discrepancies) == 1
    assert report.discrepancies[0].minute_minus_hourly == -1
    assert not report.direct_timing_comparison_permitted


@pytest.mark.parametrize(
    "mutation",
    ["file", "zip", "record", "type", "interval", "status", "fingerprint", "off_hour"],
)
def test_invalid_or_tampered_provenance_raises(mutation):
    h, m = grids()
    source = pins(m)
    with pytest.raises(ValueError):
        if mutation == "file":
            m = (replace(m[0], file_sha256=digest("tamper")), *m[1:])
        elif mutation == "zip":
            m = (replace(m[0], source_sha256=digest("tamper")), *m[1:])
        elif mutation == "record":
            h = (replace(h[0], record_id="wrong"), *h[1:])
        elif mutation == "type":
            m = h
        elif mutation == "interval":
            source = replace(source, interval_seconds=3600)
        elif mutation == "status":
            source = replace(source, status="genuine")
        elif mutation == "fingerprint":
            m = (replace(m[0], price=D(99)), *m[1:])
        else:
            m = (reference(START + timedelta(minutes=1)), *m[1:])
            source = pins(m)
        audit(h, m, minute_source=source)


def test_full_fabricated_year_all_market_hour_identities_and_leap_day():
    h, m = grids(8784)
    report = audit(h, m, 8784)
    assert report.direct_timing_comparison_permitted
    assert report.expected_count == report.hourly_count == report.minute_count == 17568
    assert len(report.matched_identities) == 17568
    assert sum(at.month == 2 for _, at in report.matched_identities) == 1392
    assert report.matched_identities[-1] == ("ETHUSDT", END - HOUR)
    assert not report.discrepancies


def test_changed_manifest_pin_rejected_against_separately_retained_identity():
    h, m = grids()
    original = pins(m)
    with pytest.raises(ValueError, match="metadata changed"):
        audit(
            h,
            m,
            minute_source=replace(original, manifest_sha256=digest("tamper")),
            expected_minute_source_sha256=minute.price_source_sha256(original),
        )

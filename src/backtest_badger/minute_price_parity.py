"""Offline exact native-hourly/native-minute price parity on supplied fixtures.

No I/O or genuine-source mode. Different native sources retain different pins.
A valid projected fingerprint does not authenticate the complete minute release.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext

from backtest_badger.paper_historical import END, HOUR, START, HourlyReference
from backtest_badger.paper_minute_historical import (
    SYMBOLS,
    MinuteReference,
    SyntheticPriceSource,
    validate_price_projection,
)
from backtest_badger.paper_types import money_context, require, utc


@dataclass(frozen=True)
class PriceDiscrepancy:
    symbol: str
    at: datetime
    hourly: HourlyReference
    minute: MinuteReference
    minute_minus_hourly: Decimal
    absolute_difference: Decimal


@dataclass(frozen=True)
class ParityReport:
    hourly_source: SyntheticPriceSource
    minute_source: SyntheticPriceSource
    expected_count: int
    hourly_count: int
    minute_count: int
    matched_identities: tuple[tuple[str, datetime], ...]
    missing_hourly: tuple[tuple[str, datetime], ...]
    missing_minute: tuple[tuple[str, datetime], ...]
    extra_hourly: tuple[HourlyReference, ...]
    extra_minute: tuple[MinuteReference, ...]
    duplicated_hourly: tuple[HourlyReference, ...]
    duplicated_minute: tuple[MinuteReference, ...]
    reordered_hourly_indices: tuple[int, ...]
    reordered_minute_indices: tuple[int, ...]
    discrepancies: tuple[PriceDiscrepancy, ...]
    direct_timing_comparison_permitted: bool
    status: str = "synthetic_test"
    authentication: str = "supplied_projection_integrity_not_full_source_authentication"


def audit_minute_price_parity(
    hourly_references,
    minute_references,
    *,
    hourly_source,
    minute_source,
    expected_hourly_source_sha256,
    expected_minute_source_sha256,
    end_exclusive=END,
):
    """Report every coverage/order/price failure; malformed provenance raises.

    Both markets are mandatory. Full year expects 17,568 market/hour identities.
    Rows must be in (symbol, timestamp) order. Duplicates remain in the report,
    never silently deduplicated. Differing prices are compared exactly, without
    tolerance or reference substitution. Permission applies to this fixture only.
    """
    utc(end_exclusive)
    require(
        START < end_exclusive <= END
        and not (
            end_exclusive.minute or end_exclusive.second or end_exclusive.microsecond
        ),
        "Invalid parity observation period.",
    )
    hourly, minute = tuple(hourly_references), tuple(minute_references)
    validate_price_projection(
        hourly,
        hourly_source,
        interval_seconds=3600,
        expected_source_sha256=expected_hourly_source_sha256,
    )
    validate_price_projection(
        minute,
        minute_source,
        interval_seconds=60,
        expected_source_sha256=expected_minute_source_sha256,
    )
    require(
        all(r.at.minute == 0 for r in minute), "Minute parity samples must be HH:00."
    )
    expected = {
        (symbol, START + i * HOUR)
        for symbol in SYMBOLS
        for i in range((end_exclusive - START) // HOUR)
    }

    def inspect(rows):
        groups, reversed_indices = {}, []
        previous = None
        for i, ref in enumerate(rows):
            key = ref.symbol, ref.at
            if previous is not None and key < previous:
                reversed_indices.append(i)
            groups.setdefault(key, []).append(ref)
            previous = key
        extra = tuple(r for r in rows if (r.symbol, r.at) not in expected)
        duplicates = tuple(r for r in rows if len(groups[r.symbol, r.at]) > 1)
        return (
            groups,
            tuple(sorted(expected - groups.keys())),
            extra,
            duplicates,
            tuple(reversed_indices),
        )

    hours, missing_h, extra_h, duplicate_h, reordered_h = inspect(hourly)
    minutes, missing_m, extra_m, duplicate_m, reordered_m = inspect(minute)
    matched, discrepancies = [], []
    with localcontext(money_context()):
        for symbol, at in sorted(hours.keys() & minutes.keys()):
            left, right = hours[symbol, at], minutes[symbol, at]
            if (
                (symbol, at) in expected
                and len(left) == len(right) == 1
                and left[0].price == right[0].price
            ):
                matched.append((symbol, at))
            # Retain all conflicting observations even under duplicated identities.
            for h in left:
                for m in right:
                    if h.price != m.price:
                        difference = m.price - h.price
                        discrepancies.append(
                            PriceDiscrepancy(
                                symbol,
                                at,
                                h,
                                m,
                                difference,
                                abs(difference),
                            )
                        )
    permitted = not any(
        (
            missing_h,
            missing_m,
            extra_h,
            extra_m,
            duplicate_h,
            duplicate_m,
            reordered_h,
            reordered_m,
            discrepancies,
        )
    )
    return ParityReport(
        hourly_source,
        minute_source,
        len(expected),
        len(hourly),
        len(minute),
        tuple(matched),
        missing_h,
        missing_m,
        extra_h,
        extra_m,
        duplicate_h,
        duplicate_m,
        reordered_h,
        reordered_m,
        tuple(discrepancies),
        permitted,
    )

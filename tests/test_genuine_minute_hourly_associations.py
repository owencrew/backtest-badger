"""Fabricated-only checks for order-independent retained hourly associations."""

from copy import deepcopy
from hashlib import sha256

import pytest

from backtest_badger import genuine_minute_publication as publication


def invented_sources():
    declarations = []
    sources = []
    for symbol in ("BTCUSDT", "ETHUSDT"):
        for n in range(1, 13):
            month = f"2024-{n:02d}"
            digest = sha256(f"fixture:{symbol}:{month}".encode()).hexdigest()
            declarations.append([symbol, month, digest])
            sources.append(
                {
                    "symbol": symbol,
                    "month": month,
                    "sha256": digest,
                    "complete": True,
                    "checksum_valid": True,
                }
            )
    return sources, declarations


@pytest.mark.parametrize("order", ("original", "reversed", "rotated"))
def test_hourly_source_order_is_not_provenance(order):
    sources, declarations = invented_sources()
    if order == "reversed":
        sources.reverse()
    elif order == "rotated":
        sources[:] = sources[7:] + sources[:7]
    publication._verify_hourly_associations(sources, declarations)


@pytest.mark.parametrize(
    "mutation",
    (
        "missing",
        "duplicate",
        "wrong_month",
        "wrong_hash",
        "incomplete",
        "checksum_invalid",
        "malformed_key",
        "duplicate_declaration",
        "missing_declaration",
    ),
)
def test_hourly_source_missing_or_corrupt_association_rejected(mutation):
    sources, declarations = invented_sources()
    if mutation == "missing":
        sources.pop()
    elif mutation == "duplicate":
        sources[-1] = deepcopy(sources[0])
    elif mutation == "wrong_month":
        sources[0]["month"] = "2023-12"
    elif mutation == "wrong_hash":
        sources[0]["sha256"] = "0" * 64
    elif mutation == "incomplete":
        sources[0]["complete"] = False
    elif mutation == "checksum_invalid":
        sources[0]["checksum_valid"] = False
    elif mutation == "malformed_key":
        sources[0]["symbol"] = []
    elif mutation == "duplicate_declaration":
        declarations[-1] = list(declarations[0])
    elif mutation == "missing_declaration":
        declarations.pop()
    with pytest.raises((ValueError, AssertionError)):
        publication._verify_hourly_associations(sources, declarations)

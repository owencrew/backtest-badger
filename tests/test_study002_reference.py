"""Opt-in read-only pinned Study 001 regression; never part of synthetic tests."""

import json
import os
from pathlib import Path

import pytest

from backtest_badger import local_historical_backtest as local
from backtest_badger import study002_runner as study


@pytest.mark.skipif(
    os.environ.get("BADGER_STUDY001_REGRESSION") != "authorised_read_only",
    reason="Explicit opt-in required for original pinned Study 001 evidence",
)
def test_original_pinned_replay_byte_identity():
    root = Path(__file__).resolve().parents[1]
    p = root / "artifacts/audits/stage-04b2d3-minute-inputs-v1"
    paths = {
        n: p / (n + ".json") for n in ("manifest", "authenticated_inputs", "integrity")
    }
    paths["signoff"] = (
        Path.home()
        / "Documents/BacktestBadgerEvidence"
        / "stage-04b2d14-publication-signoff-94584dc.json"
    )
    directory = (
        root
        / "artifacts/paper-historical/stage-04b2e5e-local-runs"
        / study.REFERENCE_ID
    )
    old = study.reference(directory)
    checked = local.preflight(paths).publication
    result = local.publication._replay_verified_publication(
        checked, expected=checked.pins, signoff_claim=checked.pins.signoff
    )
    summary, details = local._reports(result, checked.pins)
    assert json.loads(local._bytes(summary["accounts"])) == old["accounts"]
    assert (
        json.loads(local._bytes(summary["ridge_comparisons"]))
        == old["ridge_comparisons"]
    )
    regenerated = {
        "input_identities": checked.pins,
        "results": result,
        "reports": details,
    }
    assert (
        local._bytes(regenerated) == (directory / "private/evidence.json").read_bytes()
    )
    assert (
        local._bytes(
            {
                "schema": local.VERSION,
                "research_classification": local.preparation.METHOD["research_status"],
                "protocol": local.preparation.PROTOCOL,
                "method": local.preparation.METHOD,
                "limitations": local.LIMITATIONS,
                **summary,
            }
        )
        == (directory / "summary.json").read_bytes()
    )

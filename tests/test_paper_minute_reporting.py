"""Invented evidence only. Direct execution installs a guard before imports.

python3.12 -I -S -B tests/test_paper_minute_reporting.py [--regressions]
The guard is procedural protection, not a security sandbox for hostile code.
"""

import builtins
import io
import json
import os
import socket
import sys
from dataclasses import replace
from datetime import UTC, datetime
from decimal import ROUND_DOWN, localcontext
from hashlib import sha256


def _run_guarded():
    # No repository discovery, site initialisation, conftest or plugin autoload.
    import sysconfig

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    runtime = (root + "/.venv/lib/python3.12/site-packages",) + tuple(
        dict.fromkeys(
            sysconfig.get_path(key)
            for key in ("stdlib", "platstdlib", "purelib", "platlib")
        )
    )
    test_names = (
        "test_paper_minute_reporting.py",
        "test_paper_minute_historical.py",
        "test_paper_minute_integration.py",
        "test_paper_historical_evaluation.py",
    )
    test_paths = {root + "/tests/" + name for name in test_names}
    source = root + "/src/backtest_badger"
    directories = {root, root + "/src", source, root + "/tests"}
    original_lstat = os.lstat

    def check(path, *, metadata=False):
        if type(path) is int:
            raise PermissionError("File-descriptor access denied")
        absolute = os.path.abspath(os.fsdecode(path))
        if any(
            part in absolute.split("/")
            for part in (
                "artifacts",
                "BacktestBadgerEvidence",
                "crypto-trading-platform",
                ".ssh",
                ".aws",
                ".env",
                ".codex",
            )
        ):
            raise PermissionError("Original/private evidence denied")
        allowed = (
            absolute == "/dev/null"
            or absolute in test_paths
            or (absolute.startswith(source + "/") and absolute.endswith(".py"))
            or any(absolute == p or absolute.startswith(p + "/") for p in runtime)
        )
        if metadata:
            allowed = (
                allowed
                or absolute == "/"
                or absolute in directories
                or root.startswith(absolute + "/")
            )
        if not allowed:
            raise PermissionError("Non-allowlisted path denied: " + absolute)
        if not metadata and absolute != "/dev/null":
            current = "/"
            for part in absolute.strip("/").split("/"):
                current = os.path.join(current, part)
                try:
                    mode = original_lstat(current).st_mode
                except FileNotFoundError:
                    break
                if mode & 0o170000 == 0o120000:
                    raise PermissionError("Symlink read denied")

    def audit(event, args):
        if event == "open":
            check(args[0])
            if args[2] & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            ):
                raise PermissionError("Writes denied")
        if event in ("os.listdir", "os.scandir"):
            path = os.path.abspath(os.fsdecode(args[0]))
            if path not in {root + "/src", source}:
                check(path)
        if event.startswith(("socket.", "subprocess.")) or event in (
            "os.system",
            "os.posix_spawn",
            "os.exec",
            "os.fork",
            "os.forkpty",
            "os.remove",
            "os.rename",
            "os.mkdir",
            "os.rmdir",
            "os.link",
            "os.symlink",
        ):
            raise PermissionError("Network/process/mutation denied")

    sys.dont_write_bytecode = True
    sys.addaudithook(audit)
    for name in ("stat", "lstat"):
        original = getattr(os, name)

        def guarded(path, *args, _original=original, **kwargs):
            check(path, metadata=True)
            return _original(path, *args, **kwargs)

        setattr(os, name, guarded)
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ.pop("BADGER_TEST_ADMIN_DSN", None)
    os.environ.pop("DATABASE_URL", None)
    sys.path.extend((root + "/src", *runtime))
    import pytest

    targets = [root + "/tests/" + test_names[0]]
    if sys.argv[1:] == ["--regressions"]:
        targets += [root + "/tests/" + name for name in test_names[1:3]]
        # Exact pure hourly regression nodes: no publication/writer calls.
        targets += [
            root + "/tests/" + test_names[3] + "::test_" + name
            for name in (
                "full_synthetic_accounts_counts_lifecycle_and_exact_replay",
                "cost_affordability_and_signed_postings",
                "all_calendar_periods_leap_day_loss_and_final_partial",
                "drawdown_duration_comparisons_and_benchmark_first_mark",
                "short_fixture_undefined_daily_and_benchmark_infeasible",
                "mark_and_ledger_tampering_detected",
                "source_container_order_and_decimal_context_determinism",
                "unavailable_full_year_benchmark_remains_explicit",
                "signed_posting_sums_independently_reproduce_every_prefix",
                "hourly_snapshots_reference_history_without_duplicating_it",
            )
        ]
    elif sys.argv[1:]:
        raise SystemExit("Only --regressions or no arguments supported")

    # Pytest's default Session collector scans ancestors even for exact file
    # arguments. Supply only these explicit modules; keep normal parametrization,
    # fixtures, test execution and reporting, without filesystem collection.
    import types
    from pathlib import Path

    selections = {}
    for target in targets:
        path, _, name = target.partition("::")
        selections.setdefault(path, set())
        if name:
            selections[path].add(name)

    class ExactModule(pytest.Module):
        def _getobj(self):
            module = types.ModuleType(self.path.stem)
            module.__file__ = str(self.path)
            sys.modules[module.__name__] = module
            with open(self.path, "rb") as stream:
                exec(compile(stream.read(), str(self.path), "exec"), module.__dict__)
            return module

        def collect(self):
            selected = selections[str(self.path)]
            items = list(super().collect())
            if selected:
                found = {item.originalname for item in items}
                if not selected <= found:
                    raise pytest.UsageError("Missing exact regression selector")
                items = [item for item in items if item.originalname in selected]
            return items

    class ExactFiles:
        def pytest_sessionstart(self, session):
            session.collect = lambda: (
                ExactModule.from_parent(session, path=Path(path)) for path in selections
            )

    raise SystemExit(
        pytest.main(
            [
                "-c",
                "/dev/null",
                "--rootdir=" + root,
                "--noconftest",
                "-p",
                "no:cacheprovider",
                "-p",
                "no:logging",
                "--assert=plain",
                "-s",
                "-q",
                *targets,
            ],
            plugins=[ExactFiles()],
        )
    )


if __name__ == "__main__":
    _run_guarded()

import pytest  # noqa: E402

from backtest_badger import paper_minute_historical as minute  # noqa: E402
from backtest_badger import paper_minute_reporting as reporting  # noqa: E402
from backtest_badger.paper_historical import (  # noqa: E402
    END,
    HOUR,
    START,
    HistoricalForecast,
    SyntheticMiss,
)
from backtest_badger.paper_types import STEP, D, Side, money_context  # noqa: E402


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Also deny evidence/network access when collected by ordinary CI pytest."""

    def forbidden(*args, **kwargs):
        raise PermissionError("Synthetic reporting tests forbid external access")

    def guard(original):
        def checked(path, *args, **kwargs):
            if isinstance(path, str | bytes | os.PathLike):
                parts = os.fsdecode(path).split("/")
                if any(
                    p in parts
                    for p in (
                        "artifacts",
                        "BacktestBadgerEvidence",
                        "crypto-trading-platform",
                        ".ssh",
                        ".aws",
                        ".env",
                        ".codex",
                    )
                ):
                    forbidden()
            return original(path, *args, **kwargs)

        return checked

    for module, name in (
        (builtins, "open"),
        (io, "open"),
        (os, "open"),
        (os, "stat"),
        (os, "lstat"),
        (os, "listdir"),
        (os, "scandir"),
    ):
        monkeypatch.setattr(module, name, guard(getattr(module, name)))
    for name in ("create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("connect", "connect_ex", "bind"):
        monkeypatch.setattr(socket.socket, name, forbidden)


def fake(label):
    return sha256(("E5b-invented:" + label).encode()).hexdigest()


def invented(*, hours=32, symbol="BTCUSDT", values=None, misses=(), inception="100"):
    count = min(2195, (hours + 3) // 4)
    omitted = {m.source_open for m in misses}
    forecasts = tuple(
        HistoricalForecast(
            symbol,
            f"binance:spot:{symbol}:14400:"
            f"{(START - STEP + i * STEP).isoformat()}:ridge",
            START - STEP + i * STEP,
            START + i * STEP + minute.MINUTE,
            D(values[i] if values is not None else str(i % 2)),
            fake("forecasts"),
        )
        for i in range(count)
        if START - STEP + i * STEP not in omitted
    )
    times = {START + i * HOUR for i in range(hours)}
    times.update(minute.next_minute_at(f.feature_available_at) for f in forecasts)
    times.update(minute.next_minute_at(m.discovered_at) for m in misses)
    with localcontext(money_context()):
        refs = tuple(
            minute.MinuteReference(
                symbol,
                minute.reference_identity(symbol, at, 60),
                at,
                D(inception)
                if at == START
                else D(100)
                + D(at.month) / 10
                + (D("7.12345678901234567890123456789") if at.minute else D(0)),
                fake("minute-file"),
                fake(f"minute-month:{at:%Y-%m}"),
            )
            for at in sorted(times)
        )
    source = minute.SyntheticPriceSource(
        60,
        fake("manifest"),
        fake("minute-file"),
        tuple(sorted({(symbol, f"{r.at:%Y-%m}", r.source_sha256) for r in refs})),
        minute.projection_sha256(refs),
    )
    return minute.replay_minute_historical(
        symbol,
        forecasts,
        refs,
        source=source,
        expected_source_sha256=minute.price_source_sha256(source),
        forecast_sha256=fake("forecasts"),
        model_recipe_sha256=fake("recipe"),
        end_exclusive=START + hours * HOUR,
        synthetic_misses=misses,
    )


def options(account, end):
    return {
        "end_exclusive": end,
        "expected_fingerprint": reporting.minute_reporting_fingerprint(
            account, end_exclusive=end
        ),
    }


@pytest.fixture(scope="module")
def short():
    return invented()


@pytest.fixture(scope="module", params=minute.SYMBOLS)
def annual(request):
    values = tuple(
        "1" if i >= 3 and (START + i * STEP).day != 1 else "0" for i in range(2195)
    )
    result = invented(hours=8784, symbol=request.param, values=values)
    summaries = tuple(
        reporting.minute_reporting_summary(a, **options(a, END))
        for a in result.accounts
    )
    return result, summaries


def test_off_hour_costs_use_fill_evidence_and_independent_funding(short):
    assert len({a.initial.portfolio.key for a in short.accounts}) == 3
    for account in short.accounts:
        minute.verify_minute_account(account, end_exclusive=short.end_exclusive)
        report = reporting.minute_reporting_summary(
            account, **options(account, short.end_exclusive)
        )
        assert report["initial_funding"] == D(10000)
        assert report["execution_interval_seconds"] == 60
        assert report["valuation_interval_seconds"] == 3600
        assert report["last_observed_mark"] is account.marks[-1]
        assert report["final_account"] is account.final
        assert report["performance"] == minute.minute_account_summary(
            account, end_exclusive=short.end_exclusive
        )
        for side in Side:
            fills = [f for f in account.fills if f.trade.side == side]
            costs = report["costs_by_side"][side.value]
            with localcontext(money_context()):
                assert costs["notional"] == sum((f.trade.notional for f in fills), D(0))
                assert costs["fees"] == sum((f.trade.fee for f in fills), D(0))
                assert costs["hypothetical_half_spread"] == sum(
                    (f.trade.quantity * f.reference.price * D("0.0001") for f in fills),
                    D(0),
                )
                assert costs["hypothetical_slippage"] == sum(
                    (f.trade.quantity * f.reference.price * D("0.0002") for f in fills),
                    D(0),
                )
            with localcontext(money_context(division=True)):
                assert costs["turnover_initial_funding"] == costs["notional"] / D(10000)
        if account.label == "ridge":
            assert all(f.trade.at.minute == 2 for f in account.fills)
            assert report["periods"][0]["fills"][0] is account.fills[0]
            assert report["periods"][0]["fills"][0].reference.at.minute == 2
            # Deliberately different prices make an HH:00 lookup detectably wrong.
            assert all(
                f.reference.price
                != account.marks[(f.trade.at - START) // HOUR].reference.price
                for f in account.fills
            )
        if account.label == "cash":
            assert not account.fills
            assert all(
                c["count"] == c["notional"] == c["fees"] == 0
                for c in report["costs_by_side"].values()
            )


def test_full_year_complete_leap_day_and_partial_december(annual):
    result, summaries = annual
    for account, report in zip(result.accounts, summaries, strict=True):
        daily = [r for r in report["observations"] if r["period"] == "daily"]
        monthly = [r for r in report["observations"] if r["period"] == "monthly"]
        assert len(daily) == 366 and len(monthly) == 12
        assert sum(r["complete"] for r in daily) == 365
        assert daily[59]["start"] == datetime(2024, 2, 29, tzinfo=UTC)
        assert daily[59]["complete"] and monthly[1]["observed_seconds"] == 29 * 86400
        assert daily[-1]["observed_seconds"] == 23 * 3600
        assert monthly[-1]["observed_seconds"] == 31 * 86400 - 3600
        for row in (daily[-1], monthly[-1]):
            assert not row["complete"] and row["flow_complete"]
            assert row["missing_boundary_seconds"] == 3600
            assert row["end"] == END - HOUR
            assert row["boundary"] == END
        assert all(m.reference.at < END for m in account.marks)
        assert account.marks[-1].reference.at == END - HOUR
        complete = [r["return"] for r in daily if r["complete"]]
        stats = report["complete_day_statistics"]
        assert stats["count"] == 365
        assert stats["min"] == min(complete) and stats["max"] == max(complete)
        with localcontext(money_context()):
            total = sum(complete, D(0))
        with localcontext(money_context(division=True)):
            assert stats["mean"] == total / 365


def test_month_day_flows_partition_every_fill_once(annual):
    result, summaries = annual
    for account, report in zip(result.accounts, summaries, strict=True):
        for period in ("daily", "monthly"):
            rows = [r for r in report["observations"] if r["period"] == period]
            assert tuple(f for r in rows for f in r["fills"]) == account.fills
            for row in rows:
                assert all(
                    row["start"] <= f.trade.at < row["boundary"] for f in row["fills"]
                )
                assert all(f.trade.at == f.reference.at for f in row["fills"])
                with localcontext(money_context()):
                    change = row["end_mark"].equity - row["start_mark"].equity
                assert row["pnl"] == change
                with localcontext(money_context(division=True)):
                    assert row["return"] == change / row["start_mark"].equity
            with localcontext(money_context()):
                for side in Side:
                    for key in (
                        "count",
                        "notional",
                        "fees",
                        "hypothetical_half_spread",
                        "hypothetical_slippage",
                    ):
                        assert (
                            sum(
                                (r["costs_by_side"][side.value][key] for r in rows),
                                D(0),
                            )
                            == report["costs_by_side"][side.value][key]
                        )
    ridge = summaries[0]
    feb = next(
        r
        for r in ridge["observations"]
        if r["period"] == "monthly" and r["start"].month == 2
    )
    assert feb["fills"][0].trade.at == datetime(2024, 2, 1, 0, 2, tzinfo=UTC)
    assert feb["fills"][-1].trade.at.month == 2
    assert result.accounts[0].final.quantity > 0  # no END liquidation


@pytest.mark.parametrize(
    "boundary",
    (
        datetime(2024, 1, 2, tzinfo=UTC),
        datetime(2024, 2, 1, tzinfo=UTC),
        datetime(2024, 3, 1, tzinfo=UTC),
    ),
)
def test_midnight_fill_belongs_only_to_new_day_and_post_trade_mark(boundary):
    discovery = boundary - minute.MINUTE
    steps = (boundary - START) // STEP
    misses = tuple(
        SyntheticMiss("BTCUSDT", START - STEP + i * STEP, discovery, "fabricated_gap")
        for i in (steps - 2, steps - 1)
    )
    result = invented(
        hours=(boundary - START) // HOUR + 4,
        values=("1",) * (steps + 1),
        misses=misses,
    )
    ridge = result.accounts[0]
    exit_fill = ridge.fills[1]
    assert exit_fill.trade.at == boundary
    report = reporting.minute_period_observations(
        ridge, **options(ridge, result.end_exclusive)
    )
    daily = [r for r in report["observations"] if r["period"] == "daily"]
    first, second = daily[-2:]
    assert exit_fill not in first["fills"] and exit_fill in second["fills"]
    assert first["end_mark"] is second["start_mark"]
    assert first["end_mark"].ledger_seq == exit_fill.trade.ledger_seq_before + 2
    assert first["costs_by_side"]["SELL"]["count"] == 0
    assert second["costs_by_side"]["SELL"]["count"] == 1
    if boundary.day == 1:
        monthly = [r for r in report["observations"] if r["period"] == "monthly"]
        assert exit_fill not in monthly[-2]["fills"]
        assert exit_fill in monthly[-1]["fills"]


def test_bh_inception_funding_return_and_drawdown_are_distinct(short):
    bh = short.accounts[2]
    report = reporting.minute_reporting_summary(bh, **options(bh, short.end_exclusive))
    first = report["observations"][0]
    assert first["fills"] == bh.fills and bh.fills[0].trade.at == START
    assert first["start_mark"].equity < D(10000)
    with localcontext(money_context()):
        change = bh.marks[24].equity - bh.marks[0].equity
        pnl = bh.marks[-1].equity - D(10000)
        initial_loss = D(10000) - bh.marks[0].equity
    with localcontext(money_context(division=True)):
        assert first["return"] == change / bh.marks[0].equity
        assert report["performance"]["funding_relative_marked_return"] == pnl / D(10000)
        assert report["performance"][
            "maximum_observed_hourly_reference_mark_drawdown"
        ] == initial_loss / D(10000)
    assert first["return"] != report["performance"]["funding_relative_marked_return"]
    assert not any("ratio" in k for k in report["performance"])


def test_unavailable_bh_and_zero_duration_short_period():
    result = invented(hours=1, values=("0",), inception="100000000000")
    bh = result.accounts[2]
    report = reporting.minute_reporting_summary(bh, **options(bh, result.end_exclusive))
    assert report["status"] == "unavailable"
    assert report["reason"] == "inception_full_fee_affordable_buy_infeasible"
    assert report["performance"] is report["last_observed_mark"] is None
    assert report["costs_by_side"] is None
    assert report["observations"] == report["periods"] == ()
    assert not bh.marks and not bh.fills
    cash = result.accounts[1]
    cash_report = reporting.minute_reporting_summary(
        cash, **options(cash, result.end_exclusive)
    )
    assert cash_report["observations"][0]["return"] is None
    assert cash_report["observations"][0]["observed_seconds"] == 0
    assert cash_report["complete_day_statistics"] == {
        "count": 0,
        "mean": None,
        "min": None,
        "max": None,
    }
    # No marks exist to infer the unavailable account's endpoint; the pin binds it.
    with pytest.raises(ValueError, match="fingerprint"):
        reporting.minute_reporting_summary(
            bh, **{**options(bh, result.end_exclusive), "end_exclusive": END}
        )


def test_after_last_mark_fill_is_flow_not_invented_valuation():
    result = invented(hours=1, values=("1",))
    ridge = result.accounts[0]
    report = reporting.minute_reporting_summary(
        ridge, **options(ridge, result.end_exclusive)
    )
    assert report["last_observed_mark"].quantity == 0
    assert report["final_account"].quantity > 0
    assert report["performance"]["last_mark_pnl"] == 0
    assert report["costs_by_side"]["BUY"]["count"] == 1
    assert report["observations"][0]["fills"] == ridge.fills
    assert report["observations"][0]["return"] is None


REPORTERS = (
    reporting.minute_cost_attribution,
    reporting.minute_period_observations,
    reporting.minute_reporting_summary,
)


@pytest.mark.parametrize("reporter", REPORTERS)
@pytest.mark.parametrize(
    "mutation",
    (
        "timestamp",
        "duplicate_fill",
        "source_hash",
        "file_hash",
        "price",
        "fee",
        "spread",
        "slippage",
        "ledger",
        "equity",
        "mark_price",
        "mark_identity",
        "fill_order",
        "mark_order",
        "missing_mark",
        "duplicate_mark",
        "market",
        "account",
        "end",
        "trade_identity",
        "label",
        "initial_funding",
        "final_state",
        "missing_fill",
        "mark_cash",
        "mark_quantity",
        "mark_basis",
        "mark_realised",
        "mark_fees",
        "mark_unrealised",
    ),
)
def test_tampered_evidence_fails_before_reporting(short, reporter, mutation):
    account = short.accounts[0]
    kwargs = options(account, short.end_exclusive)
    fill, mark = account.fills[0], account.marks[5]
    fills, marks = list(account.fills), list(account.marks)
    if mutation == "timestamp":
        fills[0] = replace(
            fill, trade=replace(fill.trade, at=fill.trade.at + minute.MINUTE)
        )
    elif mutation in ("source_hash", "file_hash", "price"):
        key, value = {
            "source_hash": ("source_sha256", fake("other")),
            "file_hash": ("file_sha256", fake("other")),
            "price": ("price", D(999)),
        }[mutation]
        fills[0] = replace(fill, reference=replace(fill.reference, **{key: value}))
    elif mutation == "fee":
        fills[0] = replace(fill, trade=replace(fill.trade, fee=D(0)))
    elif mutation in ("spread", "slippage"):
        fills[0] = replace(
            fill,
            **{"half_spread_cost" if mutation == "spread" else "slippage_cost": D(0)},
        )
    elif mutation == "duplicate_fill":
        fills.insert(0, fill)
    elif mutation == "missing_fill":
        fills.pop(0)
    elif mutation == "fill_order":
        fills.reverse()
    elif mutation == "mark_order":
        marks[0], marks[1] = marks[1], marks[0]
    elif mutation == "missing_mark":
        marks.pop()
    elif mutation == "duplicate_mark":
        marks[6] = mark
    elif mutation == "ledger":
        marks[5] = replace(mark, ledger_seq=1)
    elif mutation == "equity":
        marks[5] = replace(mark, equity=D(9))
    elif mutation.startswith("mark_") and mutation.removeprefix("mark_") in (
        "cash",
        "quantity",
        "basis",
        "realised",
        "fees",
        "unrealised",
    ):
        marks[5] = replace(mark, **{mutation.removeprefix("mark_"): D(9)})
    elif mutation == "mark_price":
        marks[5] = replace(mark, reference=replace(mark.reference, price=D(999)))
    elif mutation == "mark_identity":
        marks[5] = replace(
            mark, reference=replace(mark.reference, source_sha256=fake("changed"))
        )
    elif mutation == "market":
        ref = replace(
            fill.reference,
            symbol="ETHUSDT",
            record_id=minute.reference_identity("ETHUSDT", fill.reference.at, 60),
        )
        fills[0] = replace(fill, reference=ref)
    elif mutation == "account":
        account = short.accounts[1]
        fills, marks = list(account.fills), list(account.marks)
    elif mutation == "end":
        kwargs["end_exclusive"] += HOUR
    elif mutation == "trade_identity":
        fills[0] = replace(fill, trade=replace(fill.trade, identity="changed"))
    elif mutation == "initial_funding":
        account = replace(account, initial=replace(account.initial, cash=D(9999)))
    elif mutation == "final_state":
        account = replace(account, final=replace(account.final, cash=D(9999)))
    else:
        account = replace(account, label="cash")
    changed = replace(account, fills=tuple(fills), marks=tuple(marks))
    with pytest.raises(ValueError):
        reporter(changed, **kwargs)


def test_retained_pin_closes_source_metadata_gap(short):
    account = short.accounts[0]
    kwargs = options(account, short.end_exclusive)
    changed = replace(
        account,
        fills=(
            replace(
                account.fills[0],
                reference=replace(
                    account.fills[0].reference, source_sha256=fake("replacement")
                ),
            ),
            *account.fills[1:],
        ),
    )
    # Accounting consistency alone cannot authenticate a reference's provenance.
    minute.verify_minute_account(changed, end_exclusive=short.end_exclusive)
    with pytest.raises(ValueError, match="fingerprint"):
        reporting.minute_reporting_summary(changed, **kwargs)


@pytest.mark.parametrize("change", ("cash_mark_price", "portfolio_recipe"))
@pytest.mark.parametrize("reporter", REPORTERS)
def test_pin_binds_evidence_even_when_accounting_is_unchanged(short, reporter, change):
    cash = short.accounts[1]
    kwargs = options(cash, short.end_exclusive)
    if change == "cash_mark_price":
        mark = cash.marks[0]
        changed = replace(
            cash,
            marks=(
                replace(mark, reference=replace(mark.reference, price=D(999))),
                *cash.marks[1:],
            ),
        )
    else:
        portfolio = replace(cash.initial.portfolio, model_recipe_sha256=fake("other"))
        changed = replace(
            cash,
            initial=replace(cash.initial, portfolio=portfolio),
            final=replace(cash.final, portfolio=portfolio),
        )
    minute.verify_minute_account(changed, end_exclusive=short.end_exclusive)
    with pytest.raises(ValueError, match="fingerprint"):
        reporter(changed, **kwargs)


def test_public_views_and_exact_fingerprint_contract(short):
    for account in short.accounts:
        # Retained by the fixture owner before reporting handoff; the entire
        # dataclass (including source references and initial/final states) is bound.
        expected = sha256(
            minute.scientific_json(
                {
                    "schema": "native-minute-economic-reporting-v1",
                    "account": account,
                    "end_exclusive": short.end_exclusive,
                }
            ).encode()
        ).hexdigest()
        assert expected == reporting.minute_reporting_fingerprint(
            account, end_exclusive=short.end_exclusive
        )
        kwargs = {
            "end_exclusive": short.end_exclusive,
            "expected_fingerprint": expected,
        }
        costs = reporting.minute_cost_attribution(account, **kwargs)
        periods = reporting.minute_period_observations(account, **kwargs)
        summary = reporting.minute_reporting_summary(account, **kwargs)
        assert costs["costs_by_side"] == summary["costs_by_side"]
        assert costs["periods"] == summary["periods"]
        assert periods["observations"] == summary["observations"]


@pytest.mark.parametrize("reporter", REPORTERS)
def test_verifier_is_mandatory_and_no_unsafe_pin_default(short, reporter, monkeypatch):
    account = short.accounts[0]
    kwargs = options(account, short.end_exclusive)
    calls = []

    def reject(*args, **kw):
        calls.append((args, kw))
        raise ValueError("verification sentinel")

    monkeypatch.setattr(reporting, "verify_minute_account", reject)
    with pytest.raises(ValueError, match="verification sentinel"):
        reporter(account, **kwargs)
    assert len(calls) == 1
    with pytest.raises(TypeError):
        reporter(account, end_exclusive=short.end_exclusive)


def test_exact_serialization_and_ambient_decimal_independence(short):
    account = short.accounts[0]
    kwargs = options(account, short.end_exclusive)
    expected = reporting.minute_reporting_summary(account, **kwargs)
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = 6, ROUND_DOWN
        actual = reporting.minute_reporting_summary(account, **kwargs)
        assert (
            reporting.minute_reporting_fingerprint(
                account, end_exclusive=short.end_exclusive
            )
            == kwargs["expected_fingerprint"]
        )
    assert minute.scientific_json(actual) == minute.scientific_json(expected)
    parsed = json.loads(minute.scientific_json(actual))
    assert parsed["start_inclusive"] == "2024-01-01T00:00:00+00:00"
    assert parsed["last_observed_mark"]["equity"] == str(account.marks[-1].equity)
    assert parsed["costs_by_side"]["BUY"]["notional"] == str(
        actual["costs_by_side"]["BUY"]["notional"]
    )


def test_local_guard_denies_before_original_metadata_or_network():
    for operation in (os.stat, os.lstat, os.listdir, os.scandir, builtins.open):
        with pytest.raises(PermissionError):
            operation("artifacts/invented-never-accessed")
    with pytest.raises(PermissionError):
        socket.create_connection(("example.invalid", 443))

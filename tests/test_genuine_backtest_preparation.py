"""Invented records only. Execute through run_e5_guarded.py, never source loaders.

Ordinary discovery skips this class: the explicit launcher installs denial before
imports. Selected unchanged class/guard AST definitions are compiled in isolation
because their normal transitive imports are outside this stage's read allowlist.
This deliberately does not claim parser, monetary or normal-import integration.
"""

import ast
import copy
import dataclasses
import os
import socket
import sys
import types
import unittest
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_exact(name, relative):
    module = types.ModuleType(name)
    module.__file__ = ROOT + "/" + relative
    sys.modules[name] = module
    with open(module.__file__, "rb") as stream:
        exec(compile(stream.read(), module.__file__, "exec"), module.__dict__)
    return module


def definitions(relative, names, name, namespace):
    path = ROOT + "/" + relative
    with open(path, "rb") as stream:
        tree = ast.parse(stream.read(), filename=path)
    selected = [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef | ast.ClassDef) and n.name in names
    ]
    if {n.name for n in selected} != set(names):
        raise AssertionError("Named definitions changed/missing")
    # Deferred annotations avoid importing any unapproved dependency.
    future = ast.ImportFrom(
        module="__future__", names=[ast.alias(name="annotations")], level=0
    )
    isolated = ast.fix_missing_locations(
        ast.Module(body=[future, *selected], type_ignores=[])
    )
    module = types.ModuleType(name)
    module.__dict__.update(namespace)
    sys.modules[name] = module
    exec(compile(isolated, path, "exec"), module.__dict__)
    return module


def fake_hash(text):
    return sha256(("invented E5 only: " + text).encode()).hexdigest()


class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not globals().get("E5_GUARDED", False):
            raise unittest.SkipTest("Use python3.12 -I -S -B tests/run_e5_guarded.py")
        cls.p = load_exact(
            "e5_preparation", "src/backtest_badger/genuine_backtest_preparation.py"
        )
        p = cls.p
        namespace = {
            "dataclass": dataclasses.dataclass,
            "field": dataclasses.field,
            "KIND": p.KIND,
            "minute": types.SimpleNamespace(
                END=p.END,
                PROTOCOL_VERSION=p.PROTOCOL["version"],
                PROTOCOL_SHA256=p.PROTOCOL["sha256"],
            ),
        }
        cls.bridge = definitions(
            "src/backtest_badger/genuine_minute_publication.py",
            [
                "_Fingerprint",
                "_PublicationPins",
                "_PublicationMinuteSource",
                "_PublicationReplayResult",
            ],
            "backtest_badger.genuine_minute_publication",
            namespace,
        )
        cls.gate = definitions(
            "src/backtest_badger/genuine_minute_replay.py",
            ["replay_genuine_minute_historical"],
            "e5_isolated_gate",
            {},
        )
        contract = p.candidate_contract()
        contract["mode"] = p.TEST
        sources = {}
        for symbol in p.SYMBOLS:
            sources[symbol] = {
                "symbol": symbol,
                "forecast_sha256": fake_hash("forecasts"),
                "model_recipe_sha256": fake_hash("recipe"),
                "manifest_sha256": fake_hash("minute manifest"),
                "file_sha256": fake_hash("minute file"),
                "kind": p.KIND,
                "projected_sha256": fake_hash(symbol + " projection"),
                "monthly_sources": [
                    [symbol, f"2024-{m:02}", fake_hash(f"{symbol}-{m}")]
                    for m in range(1, 13)
                ],
            }
        cls.bodies = {
            key: p.encode({"provenance": p.TEST, "role": key}) for key in p.PIN_NAMES
        }
        cls.bodies["authenticated_inputs"] = p.encode(
            {"provenance": p.TEST, "sources": sources}
        )
        contract["historical"].update(
            {
                "pins": {k: p.identity(v) for k, v in cls.bodies.items()},
                "verification_commit": "a" * 40,
                "verification_ci_run": "123456",
                "identity_origin": p.TEST,
            }
        )
        implementation = contract["implementation"]
        implementation.update(
            {
                "checkout": "b" * 40,
                "ci": {"commit": "b" * 40, "run_id": "654321", "conclusion": "success"},
            }
        )
        for role, row in implementation["roles"].items():
            if row["symbol"] == p.OWNER:
                row["symbol"] = "TEST_ONLY:" + role
            row["file_identity"] = p.identity(
                ("invented code " + row["symbol"].split(":")[0]).encode()
            )
        for key in ("transitive_code_dependency_closure", "lockfile", "pyproject"):
            implementation[key] = p.identity(("invented " + key).encode())
        implementation["python"] = {
            "version": "3.12.13",
            "executable": p.identity(b"fake interpreter"),
            "dependencies": p.identity(b"fake installed dependency inventory"),
        }
        contract["paths"] = {k: "/TEST_ONLY/inputs/" + k + ".json" for k in p.PIN_NAMES}
        contract["output"]["directory"] = "/TEST_ONLY/fresh-output-unique"
        cls.contract = contract
        cls.body = p.encode(contract)
        cls.history = copy.deepcopy(contract["historical"])
        cls.implementation = copy.deepcopy(implementation)
        approval = {
            "schema": "stage-04b2e5-TEST-approval-v1",
            "purpose": "distinct_one_shot_historical_evaluation_TEST_ONLY",
            "contract": p.identity(cls.body),
            "pins": cls.history["pins"],
            "attempt_id": fake_hash("one attempt"),
            "not_before": "2030-01-01T00:00:00Z",
            "expires_at": "2030-01-02T00:00:00Z",
            "maximum_attempts": 1,
            **{k: contract[k] for k in ("paths", "implementation", "method", "output")},
        }
        cls.approval = p.encode(approval)
        cls.claim = {
            "kind": "fabricated_owner_validation_claim",
            "approval": p.identity(cls.approval),
            "signature": "TEST_ONLY:" + sha256(cls.approval).hexdigest(),
            "external_independence_proven": False,
        }
        cls.observed = {
            "implementation": implementation,
            "pins": cls.history["pins"],
            "output_exists": False,
            "attempt_state": "UNSTARTED",
        }
        pins = cls.bridge._PublicationPins(
            **{k: cls.bridge._Fingerprint(**v) for k, v in cls.history["pins"].items()}
        )
        results = []
        for symbol in p.SYMBOLS:
            source = dict(sources[symbol])
            source.pop("kind")
            source["monthly_sources"] = tuple(
                tuple(r) for r in source["monthly_sources"]
            )
            source = cls.bridge._PublicationMinuteSource(publication=pins, **source)
            decisions = []
            for i in range(2195):
                opened = p.START - timedelta(hours=4) + i * timedelta(hours=4)
                available = opened + timedelta(hours=4, seconds=60)
                forecast = {
                    "symbol": symbol,
                    "source_open": opened,
                    "feature_available_at": available,
                    "prediction": Decimal("-0.01"),
                    "file_sha256": source.forecast_sha256,
                    "record_id": (
                        f"binance:spot:{symbol}:14400:{opened.isoformat()}:ridge"
                    ),
                }
                decisions.append(
                    {
                        "identity": f"{p.KIND}:{symbol}:ridge:{opened.isoformat()}",
                        "symbol": symbol,
                        "source_open": opened,
                        "at": available,
                        "forecast": forecast,
                        "miss": None,
                        "action": "CASH_NOOP",
                        "target": 0,
                        "missed_streak": 0,
                        "reason": "ridge_nonpositive",
                    }
                )
            accounts = []
            for label in p.LABELS:
                account_id = f"{p.KIND}:{symbol}:{label}"
                # Deliberately invented unverified account states. No engine runs.
                initial = {
                    "portfolio": {"key": account_id, "symbol": symbol},
                    "cash": Decimal("10000"),
                    "quantity": Decimal(0),
                    "basis": Decimal(0),
                    "realised": Decimal(0),
                    "fees": Decimal(0),
                    "ledger_seq": 1,
                    "at": p.START,
                    "trade_ids": (),
                }
                marks = []
                if label != "buy_and_hold":
                    for i in range(8784):
                        at = p.START + timedelta(hours=i)
                        ref = {
                            "symbol": symbol,
                            "at": at,
                            "price": Decimal("100000000000"),
                            "file_sha256": source.file_sha256,
                            "source_sha256": source.monthly_sources[at.month - 1][2],
                            "record_id": (
                                f"binance:spot:{symbol}:60:{int(at.timestamp()) * 1000}"
                            ),
                            "interval_seconds": 60,
                            "venue": "binance",
                            "market_type": "spot",
                        }
                        marks.append(
                            {
                                "account_id": account_id,
                                "reference": ref,
                                "ledger_seq": 1,
                                "cash": Decimal("10000"),
                                "quantity": Decimal(0),
                                "basis": Decimal(0),
                                "realised": Decimal(0),
                                "fees": Decimal(0),
                                "equity": Decimal("10000"),
                                "unrealised": Decimal(0),
                                "kind": "hourly_valuation_from_native_minute_open",
                            }
                        )
                accounts.append(
                    {
                        "label": label,
                        "initial": initial,
                        "final": initial,
                        "fills": (),
                        "marks": tuple(marks),
                        "status": "unavailable"
                        if label == "buy_and_hold"
                        else "available",
                        "reason": "inception_full_fee_affordable_buy_infeasible"
                        if label == "buy_and_hold"
                        else None,
                    }
                )
            results.append(
                cls.bridge._PublicationReplayResult(
                    symbol, source, tuple(decisions), tuple(accounts)
                )
            )
        cls.results = tuple(results)
        cls.result_pin = p.result_identity(cls.results)

    def validate(self, contract):
        return self.p.validate_test_contract(
            self.p.encode(contract),
            expected_history=self.history,
            expected_implementation=self.implementation,
        )

    def preflight(self, **changes):
        args = dict(
            approval=self.approval,
            owner_claim=self.claim,
            observed=self.observed,
            now="2030-01-01T12:00:00Z",
            expected_history=self.history,
            expected_implementation=self.implementation,
        )
        args.update(changes)
        return self.p.test_preflight(self.body, **args)

    def export(self, results=None, *, repin=False, bodies=None):
        results = self.results if results is None else results
        return self.p.encode_test_evidence(
            results,
            contract=self.body,
            fabricated_bodies=self.bodies if bodies is None else bodies,
            expected_results=self.p.result_identity(results)
            if repin
            else self.result_pin,
            expected_history=self.history,
            expected_implementation=self.implementation,
        )

    def test_candidate_and_committed_template_agree(self):
        with open(ROOT + "/docs/stage-04b2e5-run-contract.json", "rb") as stream:
            body = stream.read()
        self.assertEqual(body, self.p.encode(self.p.candidate_contract()))
        self.assertFalse(self.p.validate_candidate(body)["execution_authorised"])
        self.assertIn(self.p.OWNER.encode(), body)

    def test_candidate_rejects_populated_execution_authority(self):
        with self.assertRaises(ValueError):
            self.p.validate_candidate(self.body)

    def test_valid_fabricated_contract(self):
        self.assertEqual(self.validate(self.contract), self.contract)

    def test_preflight_never_grants_authority(self):
        result = self.preflight()
        self.assertEqual(result["state"], "READY_MODEL_ONLY")
        self.assertFalse(result["execution_authorised"])
        self.assertFalse(result["external_independence_proven"])

    def test_public_gate_before_hostile_argument_inspection(self):
        class Hostile:
            def __getattribute__(self, name):
                raise AssertionError("Approval was inspected")

        with self.assertRaises(PermissionError):
            self.gate.replay_genuine_minute_historical(approval=Hostile())

    def test_full_year_test_only_roundtrip(self):
        body = self.export()
        value = self.p.decode_test_evidence(body, expected=self.p.identity(body))
        self.assertEqual(self.p.encode(value), body)
        self.assertEqual(value["results"], self.p._record(self.results))
        self.assertEqual(value["counts"]["BTCUSDT"]["accounts"]["ridge"]["marks"], 8784)
        self.assertEqual(
            value["results"][0]["accounts"][0]["marks"][-1]["reference"]["at"],
            "2024-12-31T23:00:00+00:00",
        )
        self.assertEqual(
            value["metrics"]["daily_monthly"], self.p.METRICS["daily_monthly"]
        )
        self.assertNotIn(b"/TEST_ONLY/", body)
        self.assertNotIn(b"signature", body)
        self.assertFalse(value["economic_publication"])
        self.assertEqual(
            value["accounting_validation"], "NOT_PERFORMED_transport_only_TEST"
        )

    def test_canonical_json_rejects_duplicate_nonfinite_and_float(self):
        for body in (
            b'{"a":1,"a":2}\n',
            b'{"a":NaN}\n',
            b'{"a":Infinity}\n',
            b'{"a":-Infinity}\n',
            b'{"a":1e999}\n',
            b'{"a":1.0}\n',
            b"{}",
            b'{"b":1,"a":2}\n',
            b"{}\n{}\n",
            b"\xef\xbb\xbf{}\n",
        ):
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.p.decode(body)

    def test_exact_decimal_encoding(self):
        self.assertEqual(self.p._record(Decimal("1.00000000")), "1.00000000")
        for value in (
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("1e1000"),
            float("nan"),
        ):
            with self.subTest(value=str(value)), self.assertRaises(ValueError):
                self.p._record(value)

    def test_fill_costs_and_postings_transport_without_economic_certification(self):
        results = copy.deepcopy(self.results)
        row = results[0]
        at = self.p.START + timedelta(minutes=2)
        ref = dict(row.accounts[0]["marks"][0]["reference"])
        ref.update(
            at=at, record_id=f"binance:spot:BTCUSDT:60:{int(at.timestamp()) * 1000}"
        )
        # Invented transport specimen, intentionally NOT an accounting-valid run.
        # No result of this helper may claim that ledger reconciliation passed.
        fill = {
            "reference": ref,
            "trade": {
                "identity": "TEST_ONLY:fill",
                "portfolio": row.accounts[0]["initial"]["portfolio"],
                "side": "BUY",
                "at": at,
                "quantity": Decimal("0.000001"),
                "price": Decimal("100030000000"),
                "notional": Decimal("100030"),
                "fee": Decimal("100.03000000"),
                "ledger_seq_before": 1,
                "postings": [
                    {"asset": "USDT", "amount": Decimal("-100130.03000000")},
                    {"asset": "BTC", "amount": Decimal("0.000001")},
                ],
                "policy": "stage-4a-execution-v1",
            },
            "decision_id": row.decisions[0]["identity"],
            "half_spread_cost": Decimal("10.000000"),
            "slippage_cost": Decimal("20.000000"),
            "kind": "hypothetical_native_minute_execution",
        }
        row.accounts[0]["fills"] = (fill,)
        body = self.export(results, repin=True)
        value = self.p.decode_test_evidence(body, expected=self.p.identity(body))
        self.assertEqual(
            value["results"][0]["accounts"][0]["fills"][0], self.p._record(fill)
        )
        self.assertEqual(
            value["accounting_validation"], "NOT_PERFORMED_transport_only_TEST"
        )
        fill["reference"]["source_sha256"] = fake_hash("swapped fill source")
        with self.assertRaisesRegex(ValueError, "Reference source/time swap"):
            self.export(results, repin=True)

    def test_counterfeit_export_claims_and_metrics(self):
        value = self.p.decode(self.export())
        for field, replacement in (
            ("metrics", {"sharpe": "99"}),
            ("external_independence_proven", True),
            ("execution_authorised", True),
            ("provenance", "genuine"),
            ("accounting_validation", "PASS"),
            ("economic_publication", True),
        ):
            with self.subTest(field=field):
                changed = dict(value)
                changed[field] = replacement
                body = self.p.encode(changed)
                with self.assertRaises(ValueError):
                    self.p.decode_test_evidence(body, expected=self.p.identity(body))

    def test_pin_schema_even_with_matching_claims(self):
        for bad in (True, 1.0, "100", -1, 0):
            with self.subTest(bad=bad):
                value = copy.deepcopy(self.contract)
                value["historical"]["pins"]["manifest"]["bytes"] = bad
                with self.assertRaises(ValueError):
                    self.p.validate_test_contract(
                        self.p.encode(value),
                        expected_history=value["historical"],
                        expected_implementation=self.implementation,
                    )

    def test_original_pins_never_accepted_even_with_matching_claims(self):
        value = copy.deepcopy(self.contract)
        value["historical"]["pins"] = copy.deepcopy(self.p.HISTORICAL_PINS)
        with self.assertRaisesRegex(ValueError, "Genuine pin forbidden"):
            self.p.validate_test_contract(
                self.p.encode(value),
                expected_history=value["historical"],
                expected_implementation=self.implementation,
            )

    def test_future_no_retry_state_model(self):
        p = self.p
        self.assertFalse(
            p.attempt_transition("UNSTARTED", "refuse_preflight")[
                "authority_consumed_or_uncertain"
            ]
        )
        for event in ("crash", "complete", "status_unknown"):
            result = p.attempt_transition("CONSUMED_STARTED", event)
            self.assertTrue(result["authority_consumed_or_uncertain"])
            for retry in (
                "consume_before_start",
                "accept_test_preflight",
                "resume",
                "retry",
            ):
                with (
                    self.subTest(event=event, retry=retry),
                    self.assertRaises(ValueError),
                ):
                    p.attempt_transition(result["state"], retry)
        self.assertTrue(
            p.attempt_transition("READY_MODEL_ONLY", "consume_uncertain")[
                "authority_consumed_or_uncertain"
            ]
        )

    def test_fixture_wrapper_cannot_become_publication_result(self):
        impostor = dataclasses.make_dataclass(
            "_FixtureReplayResult",
            [(f.name, object) for f in dataclasses.fields(self.results[0])],
        )
        fake = impostor(
            **{
                f.name: getattr(self.results[0], f.name)
                for f in dataclasses.fields(self.results[0])
            }
        )
        with self.assertRaisesRegex(ValueError, "fixture relabelling"):
            self.export((fake, self.results[1]), repin=True)

    def test_guard_denies_protected_paths_without_access(self):
        for path in (
            ROOT + "/artifacts/TEST_ONLY_DO_NOT_OPEN",
            "/TEST_ONLY/BacktestBadgerEvidence/no",
            ROOT + "/src/backtest_badger/UNNAMED.py",
            "/TEST_ONLY/.ssh/no",
            "/TEST_ONLY/.aws/no",
        ):
            with self.subTest(path=path):
                with self.assertRaises(PermissionError):
                    open(path, "rb")
                with self.assertRaises(PermissionError):
                    os.stat(path)

    def test_guard_denies_network_before_socket_creation(self):
        with self.assertRaises(PermissionError):
            socket.socket()

    def test_guard_roots_are_lexical_on_macos_and_linux(self):
        for relative in (
            "tests/run_e5_guarded.py",
            "tests/test_genuine_backtest_preparation.py",
        ):
            with open(ROOT + "/" + relative, "rb") as stream:
                tree = ast.parse(stream.read())
            assignments = [
                node
                for node in tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "ROOT"
                    for target in node.targets
                )
            ]
            self.assertEqual(len(assignments), 1)
            code = compile(
                ast.Module(body=assignments, type_ignores=[]), relative, "exec"
            )
            for checkout in (
                "/Users/TEST_ONLY/Code/backtest-badger",
                "/home/runner/work/TEST_ONLY/TEST_ONLY",
            ):
                with self.subTest(relative=relative, checkout=checkout):
                    namespace = {"os": os, "__file__": checkout + "/" + relative}
                    exec(code, namespace)
                    self.assertEqual(namespace["ROOT"], checkout)
        self.assertEqual(ROOT, globals()["E5_CHECK_PATH"].__globals__["ROOT"])

    def test_guard_protected_paths_precede_metadata_in_portable_checkouts(self):
        check = globals()["E5_CHECK_PATH"]
        namespace = check.__globals__
        original = namespace["ORIGINAL_LSTAT"]

        def no_metadata(path):
            raise AssertionError("Rejected path reached filesystem metadata")

        namespace["ORIGINAL_LSTAT"] = no_metadata
        try:
            for checkout in (
                "/Users/TEST_ONLY/Code/backtest-badger",
                "/home/runner/work/TEST_ONLY/TEST_ONLY",
            ):
                for component in (
                    "artifacts",
                    "BacktestBadgerEvidence",
                    "crypto-trading-platform",
                    ".ssh",
                    ".aws",
                    ".env",
                    ".codex",
                ):
                    for metadata in (False, True):
                        with (
                            self.subTest(checkout=checkout, component=component),
                            self.assertRaisesRegex(PermissionError, "Protected path"),
                        ):
                            check(
                                checkout + "/" + component + "/TEST_ONLY",
                                metadata=metadata,
                            )
                with self.assertRaisesRegex(PermissionError, "Non-allowlisted path"):
                    check(checkout + "/tests/test_genuine_backtest_preparation.py")
            with self.assertRaisesRegex(PermissionError, "Non-allowlisted path"):
                check(ROOT + "/tests/TEST_ONLY_UNLISTED.py")
        finally:
            namespace["ORIGINAL_LSTAT"] = original

    def test_guard_suite_requires_every_case_without_skips_or_failures(self):
        succeeded = globals()["E5_SUITE_SUCCEEDED"]
        for count, successful, skipped, expected in (
            (87, True, [], True),
            (0, True, [], False),
            (84, True, [], False),
            (86, True, [], False),
            (88, True, [], False),
            (87, False, [], False),
            (87, True, [("TEST_ONLY", "skipped")], False),
        ):
            with self.subTest(count=count, successful=successful, skipped=skipped):
                result = types.SimpleNamespace(
                    testsRun=count,
                    skipped=skipped,
                    wasSuccessful=lambda successful=successful: successful,
                )
                self.assertEqual(succeeded(result), expected)

    def test_guard_denies_discovery_and_writes(self):
        with self.assertRaises(PermissionError):
            os.listdir(ROOT)
        with self.assertRaises(PermissionError):
            open(ROOT + "/docs/stage-04b2e5-run-contract.json", "wb")

    def test_guard_rejects_mocked_symlink_without_following_it(self):
        check = globals()["E5_CHECK_PATH"]
        namespace = check.__globals__
        original = namespace["ORIGINAL_LSTAT"]
        target = ROOT + "/docs/stage-04b2e5-run-contract.json"

        def fake_lstat(path):
            if path == target:
                return types.SimpleNamespace(st_mode=0o120000)
            return original(path)

        namespace["ORIGINAL_LSTAT"] = fake_lstat
        try:
            with self.assertRaisesRegex(PermissionError, "Symlink denied"):
                check(target)
        finally:
            namespace["ORIGINAL_LSTAT"] = original

    def test_pure_module_has_no_operational_import_or_call(self):
        path = ROOT + "/src/backtest_badger/genuine_backtest_preparation.py"
        with open(path, "rb") as stream:
            tree = ast.parse(stream.read())
        allowed = {
            "json",
            "re",
            "dataclasses",
            "datetime",
            "decimal",
            "enum",
            "hashlib",
            "pathlib",
        }
        banned = {"open", "exec", "eval", "__import__", "compile", "getattr", "setattr"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(n.name in allowed for n in node.names))
            if isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, allowed)
                if node.module == "pathlib":
                    self.assertEqual([n.name for n in node.names], ["PurePosixPath"])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                # getattr is used only for lossless dataclass field transport.
                self.assertNotIn(node.func.id, banned - {"getattr"})


def contract_case(path, bad):
    def test(self):
        value = copy.deepcopy(self.contract)
        target = value
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = bad
        with self.assertRaises((ValueError, TypeError)):
            self.validate(value)

    return test


for _name, _path, _bad in (
    ("authority", ["execution_authorised"], True),
    ("genuine_mode", ["mode"], "genuine"),
    ("market", ["method", "markets"], ["BTCUSDT", "SOLUSDT"]),
    ("date", ["method", "end_exclusive"], "2026-01-01T00:00:00Z"),
    ("fee", ["method", "fee_bps"], 11),
    ("bool_fee", ["method", "fee_bps"], True),
    ("spread", ["method", "half_spread_bps"], 0),
    ("slippage", ["method", "adverse_slippage_bps"], 0),
    ("quantity", ["method", "quantity_step"], "0.001"),
    ("liquidation", ["method", "forced_final_liquidation"], True),
    ("aggregation", ["method", "independent_portfolios"], False),
    ("threshold", ["method", "threshold"], "0"),
    ("timing", ["method", "execution"], "same_minute"),
    ("marks", ["method", "hourly_marks_per_available_account"], 8785),
    ("refit", ["method", "refit_reforecast_search"], True),
    ("metric", ["metrics", "future_summary"], "sharpe_best_trial"),
    ("historical_commit", ["historical", "verification_commit"], "c" * 40),
    ("historical_ci", ["historical", "verification_ci_run"], "999999"),
    ("hash_length_mixup", ["historical", "pins", "manifest", "bytes"], "a" * 64),
    ("bool_length", ["historical", "pins", "manifest", "bytes"], True),
    ("pin_swap", ["historical", "pins", "manifest", "sha256"], "c" * 64),
    ("current_commit", ["implementation", "checkout"], "c" * 40),
    ("current_ci", ["implementation", "ci", "run_id"], "999999"),
    ("failed_ci", ["implementation", "ci", "conclusion"], "failure"),
    (
        "guard_pin",
        ["implementation", "roles", "public_guard", "file_identity", "sha256"],
        "c" * 64,
    ),
    ("lock_pin", ["implementation", "lockfile", "sha256"], "c" * 64),
    ("runtime", ["implementation", "python", "version"], "3.13.0"),
    ("relative_path", ["paths", "manifest"], "relative.json"),
    ("parent_path", ["paths", "manifest"], "/TEST_ONLY/../private.json"),
    ("live_path", ["paths", "manifest"], "/some/real/place/manifest.json"),
    ("output_overlap", ["output", "directory"], "/TEST_ONLY/inputs/subdir"),
    ("output_parent", ["output", "directory"], "/TEST_ONLY"),
    (
        "historical_output",
        ["output", "directory"],
        "/TEST_ONLY/artifacts/audits/stage-04b2d3-minute-inputs-v1",
    ),
    ("overwrite", ["output", "policy"], "overwrite"),
    ("retries", ["attempt", "retry"], True),
    ("two_attempts", ["attempt", "maximum"], 2),
):
    setattr(
        PreparationTests, "test_contract_rejects_" + _name, contract_case(_path, _bad)
    )


def approval_case(kind):
    def test(self):
        approval = self.p.decode(self.approval)
        claim, observed = copy.deepcopy(self.claim), copy.deepcopy(self.observed)
        now = "2030-01-01T12:00:00Z"
        if kind == "missing_owner":
            claim = {}
        elif kind == "historical_approval":
            approval["purpose"] = "verification_only"
        elif kind == "reused_signoff":
            approval["schema"] = "stage-04b2d14-publication-signoff-v1"
        elif kind == "signature_payload":
            claim["signature"] = "TEST_ONLY:" + "a" * 64
        elif kind == "independence":
            claim["external_independence_proven"] = True
        elif kind == "consumed":
            observed["attempt_state"] = "CONSUMED_STARTED"
        elif kind == "uncertain":
            observed["attempt_state"] = "UNCERTAIN_TERMINAL"
        elif kind == "output_reuse":
            observed["output_exists"] = True
        elif kind == "output_unknown":
            observed["output_exists"] = None
        elif kind == "stale_checkout":
            observed["implementation"]["checkout"] = "c" * 40
        elif kind == "stale_ci":
            observed["implementation"]["ci"]["run_id"] = "999999"
        elif kind == "expired":
            now = "2030-01-02T00:00:00Z"
        elif kind == "not_yet_valid":
            now = "2029-12-31T23:59:59Z"
        elif kind == "path_scope":
            approval["paths"]["manifest"] = "/TEST_ONLY/other.json"
        elif kind == "date_scope":
            approval["method"]["start_inclusive"] = "2024-02-01T00:00:00Z"
        elif kind == "output_scope":
            approval["output"]["directory"] = "/TEST_ONLY/other"
        elif kind == "pins_scope":
            approval["pins"]["manifest"]["bytes"] += 1
        elif kind == "contract_scope":
            approval["contract"]["sha256"] = "c" * 64
        with self.assertRaises(ValueError):
            self.preflight(
                approval=self.p.encode(approval),
                owner_claim=claim,
                observed=observed,
                now=now,
            )

    return test


for _name in (
    "missing_owner",
    "historical_approval",
    "reused_signoff",
    "signature_payload",
    "independence",
    "consumed",
    "uncertain",
    "output_reuse",
    "output_unknown",
    "stale_checkout",
    "stale_ci",
    "expired",
    "not_yet_valid",
    "path_scope",
    "date_scope",
    "output_scope",
    "pins_scope",
    "contract_scope",
):
    setattr(PreparationTests, "test_approval_rejects_" + _name, approval_case(_name))


def result_case(kind):
    def test(self):
        results = copy.deepcopy(self.results)
        row = results[0]
        if kind == "source_swap":
            row = dataclasses.replace(
                row,
                source=dataclasses.replace(row.source, file_sha256=fake_hash("swap")),
            )
        elif kind == "missing_decision":
            row = dataclasses.replace(row, decisions=row.decisions[:-1])
        elif kind == "duplicate_decision":
            row = dataclasses.replace(
                row, decisions=(row.decisions[0], *row.decisions[:-1])
            )
        elif kind == "missing_mark":
            row.accounts[0]["marks"] = row.accounts[0]["marks"][:-1]
        elif kind == "duplicate_mark":
            row.accounts[0]["marks"] = (
                row.accounts[0]["marks"][0],
                *row.accounts[0]["marks"][:-1],
            )
        elif kind == "forecast_source":
            row.decisions[0]["forecast"]["file_sha256"] = fake_hash("swapped forecast")
        elif kind == "mark_source":
            row.accounts[0]["marks"][0]["reference"]["source_sha256"] = fake_hash(
                "wrong month"
            )
        elif kind == "synthetic_source":
            source = self.p._record(row.source)
            source["kind"] = "synthetic_historical_minute_simulation"
            row = dataclasses.replace(row, source=source)
        elif kind == "publication_pin":
            source = self.p._record(row.source)
            source["publication"]["manifest"]["sha256"] = fake_hash("wrong publication")
            row = dataclasses.replace(row, source=source)
        elif kind == "genuine_wrapper":
            object.__setattr__(row, "authority", "genuine_owner_approved")
        elif kind == "result_pin":
            row.accounts[0]["initial"]["cash"] = Decimal("9999")
        with self.assertRaises(ValueError):
            self.export((row, results[1]), repin=kind != "result_pin")

    return test


for _name in (
    "source_swap",
    "missing_decision",
    "duplicate_decision",
    "missing_mark",
    "duplicate_mark",
    "forecast_source",
    "mark_source",
    "synthetic_source",
    "publication_pin",
    "genuine_wrapper",
    "result_pin",
):
    setattr(PreparationTests, "test_export_rejects_" + _name, result_case(_name))

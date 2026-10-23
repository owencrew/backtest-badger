"""Fabricated-only supervisor/worker protocol for the approved E.5d custody design.

The supervisor alone owns state and publication. The pipe worker has no custody
paths in its request. Ordinary CI uses a separate process with MOCKED principals;
only a later OS rehearsal can demonstrate denied access by a different UID.
"""

import json
import os
import re
import select
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path

from backtest_badger import genuine_backtest_custody as custody
from backtest_badger import genuine_backtest_reporting_integration as integration
from backtest_badger.paper_types import require

SCHEMA = "stage-04b2e5d-fabricated-publication-v1"
LIMIT = 128 << 20


def output_schema():
    """Static fabricated allowlist, loaded and bound before calculation.

    This deliberately covers the full-year fabricated available-account fixture.
    Unsupported variants fail closed; it is not the future genuine output schema.
    """
    path = Path(__file__).with_name("genuine_backtest_output_schema.json")
    with custody.directory(path.parent) as parent:
        body, _ = custody.read_file(parent, path.name, 1 << 20)
    return json.loads(body), custody.identity(body)


def validate_output(value, schema):
    """Closed recursive keys, builtin scalar types, enums and constrained strings.

    No source metadata adapters or candidate-derived expected schema. Relative
    provenance keys are literal allowlisted names, never arbitrary private roots.
    """
    patterns = {k: re.compile(v) for k, v in schema["patterns"].items()}
    pending = [(value, schema["root"], 0)]
    count = 0
    while pending:
        item, reference, depth = pending.pop()
        count += 1
        require(depth <= 32 and count <= 8_000_000, "Output traversal bound.")
        spec = schema["definitions"][reference]
        kind = type(item)
        if kind is dict:
            shape = next(
                (s for s in spec.get("objects", []) if s.keys() == item.keys()), None
            )
            require(shape is not None, "Unknown output fields.")
            pending.extend((v, shape[k], depth + 1) for k, v in item.items())
        elif kind is list:
            require("items" in spec and len(item) <= 100_000, "Output list schema.")
            require(spec["items"] != "empty" or not item, "Expected empty sequence.")
            pending.extend((v, spec["items"], depth + 1) for v in item)
        elif kind is str:
            require(
                len(item) <= 4096
                and (
                    item in spec.get("literals", [])
                    or any(
                        patterns[p].fullmatch(item) for p in spec.get("patterns", [])
                    )
                ),
                "Unreviewed output string.",
            )
        else:
            require(
                kind in (int, bool, type(None)) and spec.get(kind.__name__) is True,
                "Output scalar type.",
            )
            require(kind is not int or abs(item) < 2**63, "Output integer bound.")


def science(value):
    return integration._bounded_json(value)


def decode(body):
    require(type(body) is bytes and 0 < len(body) <= LIMIT, "Frame bound.")
    value = json.loads(body)
    require(science(value) == body, "Canonical scientific JSON required.")
    return value


def retain_replay(body):
    """Hash the complete received replay and independently derive six account pins.

    The hash construction is exactly the native reporter's existing construction.
    This is custody of what the worker produced, not independent economic replay.
    """
    value = decode(body)
    custody.fields(
        value,
        {
            "publication_pins",
            "publication_claims",
            "signoff_claims",
            "source_identities",
            "forecasts",
            "references",
            "projection_sha256",
            "results",
        },
    )
    require(len(value["results"]) == 2, "Two markets required.")
    accounts = []
    for symbol, result in zip(
        integration.minute.SYMBOLS, value["results"], strict=True
    ):
        require(
            result["symbol"] == symbol and len(result["accounts"]) == 3,
            "Market/account order changed.",
        )
        for label, account in zip(integration._LABELS, result["accounts"], strict=True):
            account_id = f"{integration.preparation.KIND}:{symbol}:{label}"
            require(
                account["label"] == label
                and account["initial"]["portfolio"]["key"] == account_id,
                "Account identity changed.",
            )
            accounts.append(
                {
                    "account_id": account_id,
                    "fingerprint": sha256(
                        science(
                            {
                                "schema": integration.reporting.SCHEMA,
                                "account": account,
                                "end_exclusive": integration.minute.END,
                            }
                        )
                    ).hexdigest(),
                }
            )
    return {"replay_sha256": sha256(body).hexdigest(), "accounts": accounts}


def reconcile_report(body, *, replay, retained, schema=None):
    value = decode(body)
    validate_output(value, output_schema()[0] if schema is None else schema)
    custody.fields(
        value,
        {
            "schema",
            "fabricated_only",
            "execution_authorised",
            "economic_publication",
            "source_authentication_proven",
            "external_independence_proven",
            "accounting_status",
            "handoff_pins",
            "protocol",
            "method",
            "evidence",
            "reports",
            "limitations",
        },
    )
    require(
        value["schema"] == integration._SCHEMA
        and value["fabricated_only"] is True
        and all(
            value[n] is False
            for n in (
                "execution_authorised",
                "economic_publication",
                "source_authentication_proven",
                "external_independence_proven",
            )
        ),
        "Fabricated-only report flags.",
    )
    require(
        value["handoff_pins"] == retained and science(value["evidence"]) == replay,
        "Report differs from protected replay retention.",
    )
    require(
        value["method"] == integration.preparation.METHOD
        and value["protocol"] == integration.preparation.PROTOCOL
        and value["limitations"] == list(integration._LIMITATIONS)
        and value["accounting_status"] == "verified_fabricated_records_only",
        "Report contract changed.",
    )
    require(
        type(value["reports"]) is list and len(value["reports"]) == 6,
        "Six reports required.",
    )
    identities = []
    for row, pin in zip(value["reports"], retained["accounts"], strict=True):
        custody.fields(
            row,
            {
                "account_id",
                "account_fingerprint",
                "replay_fingerprint",
                "ledger_verification",
                "fingerprint_status",
                "signed_ledger",
                "summary",
                "report_id",
            },
        )
        require(
            row["account_id"] == pin["account_id"]
            and row["account_fingerprint"] == pin["fingerprint"]
            and row["replay_fingerprint"] == retained["replay_sha256"]
            and row["summary"]["input_fingerprint"] == pin["fingerprint"]
            and row["summary"]["account_id"] == pin["account_id"],
            "Report association changed.",
        )
        account = value["evidence"]["results"][len(identities) // 3]["accounts"][
            len(identities) % 3
        ]
        require(
            row["summary"]["initial_account"] == account["initial"]
            and row["summary"]["final_account"] == account["final"]
            and row["summary"]["last_observed_mark"]
            == (account["marks"][-1] if account["marks"] else None),
            "Report account boundary changed.",
        )
        content = {k: v for k, v in row.items() if k != "report_id"}
        require(
            sha256(science(content)).hexdigest() == row["report_id"],
            "Report identity mismatch.",
        )
        identities.append(
            {"account_id": pin["account_id"], "report_id": row["report_id"]}
        )
    return identities


def _read_frame(stream):
    header = stream.read(8)
    require(len(header) == 8, "Incomplete worker frame.")
    length = int.from_bytes(header, "big")
    require(0 < length <= LIMIT, "Worker frame bound.")
    body = stream.read(length)
    require(len(body) == length, "Incomplete worker frame.")
    return body


def _write_frame(stream, body):
    require(0 < len(body) <= LIMIT, "Worker frame bound.")
    stream.write(len(body).to_bytes(8, "big"))
    stream.write(body)
    stream.flush()


def worker_stdio():
    """No path-opening commands; real frozen parser, replay and reporting.

    Input bodies can contain historical operational metadata. They never include
    the supervisor execution approval or its custody/publication locations.

    The launcher must deny source/network I/O before importing this module. There
    is deliberately no automatic retry or reporting without a retention ACK.
    """
    incoming, outgoing = sys.stdin.buffer, sys.stdout.buffer
    bodies = {name: _read_frame(incoming) for name in custody.INPUT_LIMITS}
    pins = integration.publication._PublicationPins(
        *(
            integration.publication._Fingerprint(**custody.identity(bodies[name]))
            for name in custody.INPUT_LIMITS
        )
    )
    produced = integration._prepare_fabricated_replay(
        **bodies,
        expected=pins,
        fabricated_only=True,
    )
    replay = science(integration._replay_evidence(produced))
    _write_frame(outgoing, replay)
    receipt = decode(_read_frame(incoming))
    custody.fields(receipt, {"replay_sha256", "accounts"})
    expected = integration._HandoffPins(
        receipt["replay_sha256"],
        tuple(integration._AccountPin(**item) for item in receipt["accounts"]),
    )
    report = integration._report_fabricated_replay(produced, expected=expected)
    _write_frame(outgoing, integration._encode_test_report(report))


class PipeWorker:
    """Bounded anonymous-pipe transport; no shell, inherited state FDs or secrets.

    mocked=True is only for fabricated CI. A real installation must launch with
    different uid/gid, immutable command/runtime and OS deny policies. The genuine
    entry point is closed regardless of this transport option.
    """

    def __init__(self, command, *, uid, gid, seconds, maximum, mocked=False):
        self.deadline = time.monotonic() + seconds
        self.maximum = maximum
        require(mocked or uid != os.getuid(), "Separate worker principal required.")
        privileges = {} if mocked else {"user": uid, "group": gid, "extra_groups": []}
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            close_fds=True,
            cwd="/",
            env={
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1",
            },
            start_new_session=True,
            **privileges,
        )
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def _transfer(self, value, *, writing):
        stream = self.process.stdin if writing else self.process.stdout
        fd = stream.fileno()
        remaining = memoryview(value) if writing else value
        chunks = []
        while len(remaining) if writing else remaining:
            timeout = self.deadline - time.monotonic()
            require(timeout > 0, "Worker deadline expired.")
            ready = select.select(
                [] if writing else [fd], [fd] if writing else [], [], timeout
            )
            require(ready[0] or ready[1], "Worker deadline expired.")
            if writing:
                count = os.write(fd, remaining[: 1 << 20])
                require(count > 0, "Worker pipe closed.")
                remaining = remaining[count:]
            else:
                chunk = os.read(fd, min(remaining, 1 << 20))
                require(bool(chunk), "Worker pipe closed.")
                chunks.append(chunk)
                remaining -= len(chunk)
        return b"".join(chunks)

    def send(self, body):
        require(0 < len(body) <= self.maximum, "Worker frame limit.")
        self._transfer(len(body).to_bytes(8, "big"), writing=True)
        self._transfer(body, writing=True)

    def receive(self):
        length = int.from_bytes(self._transfer(8, writing=False), "big")
        require(0 < length <= self.maximum, "Worker frame limit.")
        return self._transfer(length, writing=False)

    def finish(self):
        self.process.stdin.close()
        timeout = self.deadline - time.monotonic()
        require(timeout > 0, "Worker deadline expired.")
        # No extra/duplicate report frames and no successful output after a crash.
        require(self.process.wait(timeout=timeout) == 0, "Worker failed.")
        require(
            os.read(self.process.stdout.fileno(), 1) == b"", "Unexpected worker output."
        )

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        for stream in (self.process.stdin, self.process.stdout):
            if not stream.closed:
                stream.close()


def _run_fabricated(
    *,
    document,
    reviewed,
    inventory,
    public_key,
    launch,
    clock=lambda: int(time.time()),
    fault=lambda _: None,
    mocked_principals=False,
):
    """Supervisor state machine. Injectable seams are TEST-only, not capabilities.

    All genuine data identities are rejected before source I/O. Callers in CI
    control their own temporary roots and intentionally mocked privilege policy.
    This function never enrols an attempt or reconstructs missing custody state.
    """
    approved = custody.verify_approval(
        document, now=clock(), expected=reviewed, public_key=public_key
    )
    schema, schema_pin = output_schema()
    require(schema_pin == approved["output_schema_identity"], "Output schema changed.")
    require(
        mocked_principals or approved["custody"]["supervisor_uid"] == os.getuid(),
        "Wrong supervisor principal.",
    )
    closure = custody.verify_closure(
        inventory,
        supervisor_uid=approved["custody"]["supervisor_uid"],
        mocked=mocked_principals,
    )
    require(closure == approved["implementation"]["closure"], "Wrong runtime closure.")
    bodies, before = custody.read_inputs(approved)
    # Parsing/sign-off validation precedes consumption, but NO economic calculation.
    pins = integration.publication._PublicationPins(
        *(
            integration.publication._Fingerprint(**approved["inputs"][name]["identity"])
            for name in custody.INPUT_LIMITS
        )
    )
    parsed = integration.publication._parse_verified_publication(
        **{
            name: bodies[name]
            for name in ("manifest", "authenticated_inputs", "integrity")
        },
        expected=pins,
        signoff_claim=pins.signoff,
    )
    integration.publication._validate_independent_signoff(
        signoff=bodies["signoff"],
        expected_signoff=pins.signoff,
        publication=parsed,
        expected=pins,
    )
    recipe = json.loads(parsed.inputs.source_evidence_json)["forecast_manifest"]
    require(
        recipe["test_policy"] == "fabricated metadata only"
        and recipe["limitations"] == "fabricated full-year test",
        "Explicit fabricated recipe required before consumption.",
    )
    output = Path(approved["output"])
    store_path = Path(approved["custody"]["store"])
    forbidden = [Path(item["path"]).parent for item in approved["inputs"].values()]
    forbidden += [store_path, *(Path(p) for p in inventory["roots"])]
    require(
        not any(
            output.is_relative_to(p) or p.is_relative_to(output) for p in forbidden
        ),
        "Output overlaps protected/source trees.",
    )
    with (
        custody.directory(output.parent) as parent,
        custody.directory(store_path) as store,
    ):
        custody.check_private(parent, os.getuid())
        custody.check_private(store, os.getuid())
        try:
            os.stat(output.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("Output already exists.")
        # Recheck clock, source snapshots and closure immediately before consumption.
        custody.verify_approval(
            document, now=clock(), expected=reviewed, public_key=public_key
        )
        again, after = custody.read_inputs(approved)
        require(before == after and bodies == again, "Inputs changed during preflight.")
        require(
            custody.verify_closure(
                inventory,
                supervisor_uid=approved["custody"]["supervisor_uid"],
                mocked=mocked_principals,
            )
            == closure,
            "Closure changed.",
        )
        custody.verify_approval(
            document, now=clock(), expected=reviewed, public_key=public_key
        )
        slot = custody.consume(store, approved, fault=fault)
        worker = None
        try:
            # Everything after consume is terminal on failure; no cleanup/resume.
            custody.write_once(slot, "inputs.json", custody.canonical(before), fault)
            os.mkdir(output.name, mode=0o700, dir_fd=parent)
            fault("output:created")
            custody.sync(parent)
            fault("output:directory_synced")
            worker = launch(approved)
            for body in bodies.values():
                worker.send(body)
            replay = worker.receive()
            require(len(replay) <= approved["limits"]["frame_bytes"], "Replay limit.")
            retained = retain_replay(replay)
            custody.write_once(slot, "replay.json", replay, fault)
            binding = {
                "approval": custody.identity(custody.canonical(approved)),
                "attempt_id": approved["attempt_id"],
                "closure": closure,
                "method": custody.identity(custody.canonical(approved["method"])),
                "output_schema": schema_pin,
                "signer_key_id": json.loads(document)["key_id"],
                "pins": retained,
            }
            custody.write_once(slot, "handoff.json", custody.canonical(binding), fault)
            # ACK only after both the replay AND all six pins are durably retained.
            worker.send(science(retained))
            fault("handoff:acknowledged")
            report = worker.receive()
            require(len(report) <= approved["limits"]["frame_bytes"], "Report limit.")
            report_ids = reconcile_report(
                report, replay=replay, retained=retained, schema=schema
            )
            worker.finish()
            _, after = custody.read_inputs(approved)
            require(after == before, "Inputs changed during worker execution.")
            custody.write_once(
                slot, "inputs-after.json", custody.canonical(after), fault
            )
            receipt = binding | {
                "reports": report_ids,
                "evidence": custody.identity(report),
            }
            custody.write_once(slot, "reports.json", custody.canonical(receipt), fault)
            manifest = custody.canonical(
                {
                    "schema": SCHEMA,
                    "fabricated_only": True,
                    "genuine_execution_authorised": False,
                    "complete": True,
                    "approval": binding["approval"],
                    "attempt_id": approved["attempt_id"],
                    "evidence": custody.identity(report),
                    "integrity": custody.identity(custody.canonical(receipt)),
                    "external_os_isolation_demonstrated": False,
                }
            )
            files = {
                "evidence.json": report,
                "integrity.json": custody.canonical(receipt),
                "manifest.json": manifest,
            }
            require(
                sum(map(len, files.values()))
                <= approved["limits"]["total_output_bytes"],
                "Total publication limit.",
            )
            with custody.directory(output) as out:
                for name, body in files.items():
                    custody.write_once(out, name, body, fault)
                # Marker exists, but completion still requires exact readback and
                # an additional protected durable receipt. Neither is resumable.
                for name, body in files.items():
                    readback, _ = custody.read_file(out, name, len(body))
                    require(readback == body, "Publication readback mismatch.")
                fault("publication:readback")
                custody.write_once(
                    slot,
                    "completed.json",
                    custody.canonical(
                        {
                            "manifest": custody.identity(manifest),
                            "receipt": custody.identity(files["integrity.json"]),
                        }
                    ),
                    fault,
                )
            return receipt
        finally:
            if worker is not None:
                worker.close()
            os.close(slot)


def _read_completed_fabricated(approved):
    """Read-only confirmation against protected receipts; never repair or promote.

    A manifest alone is insufficient. Missing, partial, changed or unconfirmed
    state fails closed. This performs no replay, reporting, writes or resumption.
    """
    require(
        approved["schema"] == custody.SCHEMA and approved["fabricated_only"] is True,
        "Fabricated readback only.",
    )
    store_path = Path(approved["custody"]["store"])
    with custody.directory(store_path) as store:
        custody.check_private(store, os.getuid())
        installation, _ = custody.read_file(store, "installation.json", 4096)
        require(
            installation
            == custody.canonical({"installation": approved["custody"]["installation"]}),
            "Lost custody history.",
        )
        slot = os.open(
            custody.attempt_key(approved),
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=store,
        )
        try:
            custody.check_private(slot, os.getuid())
            consumed, _ = custody.read_file(slot, "consumed.json", 4096)
            require(
                consumed
                == custody.canonical(
                    {
                        "approval": custody.identity(custody.canonical(approved)),
                        "attempt_id": approved["attempt_id"],
                    }
                ),
                "Consumption mismatch.",
            )
            complete, _ = custody.read_file(slot, "completed.json", 4096)
            completion = json.loads(complete)
            custody.fields(completion, {"manifest", "receipt"})
            require(custody.canonical(completion) == complete, "Damaged completion.")
            retained, _ = custody.read_file(slot, "reports.json", 1 << 20)
            receipt = json.loads(retained)
            require(
                custody.identity(retained) == completion["receipt"]
                and receipt["approval"] == custody.identity(custody.canonical(approved))
                and receipt["attempt_id"] == approved["attempt_id"],
                "Protected report receipt mismatch.",
            )
            with custody.directory(approved["output"]) as out:
                custody.check_private(out, os.getuid())
                expected = {
                    "evidence.json": receipt["evidence"],
                    "integrity.json": completion["receipt"],
                    "manifest.json": completion["manifest"],
                }
                for name, pin in expected.items():
                    custody.pin(pin)
                    require(pin["bytes"] <= LIMIT, "Readback bound.")
                    body, _ = custody.read_file(out, name, pin["bytes"])
                    require(custody.identity(body) == pin, "Completed output changed.")
            return receipt
        finally:
            os.close(slot)

# Stage 4B.2E.5c — fabricated replay/reporting integration

**FABRICATED TEST RECORDS ONLY. No genuine evaluation, real profits, execution
authority or economic publication.** Prepared on 2026-10-23. The locally verified
baseline is `d60babe62ee674055bddfa2e116ed1e9e0b0262a`. CI run `39985126993`
(2,795 ordinary passes, 88 expected skips, and 87 mandatory guarded passes) is an
owner-supplied baseline claim, not a network observation in this task. E.4's prior
original-byte compatibility PASS is not reread or rerun here.

## Implementation and handoff

The new private module is
`src/backtest_badger/genuine_backtest_reporting_integration.py`. It does not change
the parser, sign-off contract, replay, monetary core, reporting adapter, E.5 raw
transport, frozen strategy, protocol or public gate. Its only input is in-memory
records; it has no file reader/writer, source loader, CLI, network, signing,
database, attempt consumer or authority switch.

The intended test sequence is:

1. The test author creates entirely invented canonical publication/sign-off bytes
   and retains their `_PublicationPins` separately before presenting candidates.
2. `_prepare_fabricated_replay(..., expected=pins, fabricated_only=True)` calls the
   real `_parse_verified_publication`, `_validate_independent_signoff` and
   `_replay_verified_publication`. The latter invokes the unchanged minute core.
   No AST-extracted definition or stub supplies this acceptance path.
3. At the producer boundary, `_retain_fabricated_handoff(produced)` verifies and
   retains the complete replay fingerprint and six ordered reporting account
   fingerprints in `_HandoffPins`. The test author keeps these before any mutation
   or reporting receipt. This function is explicitly a producer operation.
4. `_report_fabricated_replay(received, expected=retained)` requires those pins;
   it never manufactures expected account pins from received accounts. It
   reconciles the retained publication/sign-off again rather than trusting injected
   parsed dataclasses, checks the complete replay handoff, verifies each account,
   and invokes `minute_reporting_summary` with its separately retained fingerprint.
   It checks parity with `minute_account_summary` including every side's fill
   count, notional, fees, half-spread and slippage. No numeric return formula is
   introduced by the integration.
5. `_encode_test_report(report)` returns immutable in-memory canonical bytes.
   The test author retains their SHA-256 separately. `_decode_test_report` requires
   both that hash and the **retained checked report context**. It rejects candidate
   substitution before parsing and requires canonical byte-for-byte agreement.

Frozen dataclasses, private names and same-process handoffs are structural tools,
not security capabilities. Retention independence is a caller obligation, not a
proven fact. An attacker replacing both expected pins and their retained context
defeats those integrity checks. The decoder does not accept arbitrary standalone
JSON as certified accounting, reconstruct accounts from untrusted dictionaries,
or run a second replay. Its context requirement enforces all nested field names,
types and exact operands by equality to the retained checked report; top-level
schema, declarations and false authority flags are also checked explicitly.

Known historical publication hashes and declared historical data hashes are
rejected. The recipe must carry the existing fabricated fixture's explicit
`fabricated metadata only` and `fabricated full-year test` markers. These are
misuse guards, not a way to prove that arbitrary bytes are invented. Existing
upstream genuine-shaped claims remain unmodified inside the fabricated context;
synthetic sources/results cannot be relabelled into the private publication type.
`replay_genuine_minute_historical(*, approval)` remains unconditionally closed.

## Evidence contract

`stage-04b2e5c-fabricated-economic-evidence-v1` is separate from
`stage-04b2e5-fabricated-evidence-v1`. The frozen replay/report envelopes carry
`fabricated_only=true`, `execution_authorised=false`, `economic_publication=false`
and `source_authentication_proven=false`. The wire document additionally states
`external_independence_proven=false` and
`accounting_status=verified_fabricated_records_only`.

The deterministic scientific encoding includes:

- Exact publication/sign-off fingerprints and parser-reconciled upstream claims,
  explicitly fabricated rather than authenticated historical observations.
- Complete source inventory identities and implementation hashes; all forecast
  records, ordered native-minute references, projection fingerprints and replay
  results. Source and model-recipe lineage remain bound to their upstream hashes.
- All six full accounts, ordered fills, signed postings, ledger prefixes and
  hourly marks. No lossy summary replaces account evidence.
- The unchanged reviewed protocol/method declarations, separately supplied handoff
  pins, unique ordered account identities and content-derived report identities.
- Each existing native-minute report: exact Decimal strings, fill-side totals,
  daily/monthly half-open cost flows, observed mark-to-mark returns, completeness
  flags and complete-day statistics. Explicit signed-ledger records accompany it.
- Honest ledger/fingerprint status labels and fixed limitations.

Only parser-checked source identity fields are projected into this contract.
Approval payloads/signatures, absolute private roots, environment snapshots,
credentials and arbitrary recipe metadata are excluded. Relative upstream
publication/source labels are claims, never paths to open.

The serializer bounds nesting to 32, visited nodes to 8,000,000, sequence lengths
to 100,000, individual strings to 1 MiB, integers to signed 63-bit magnitude, and
encoded output to 128 MiB. Shared `scientific_json` preserves Decimal operands,
UTC strings and sequence order without binary floats. Cycles/deep values are
rejected by a bounded iterative prewalk before recursive encoding. Decoding checks
byte size and the independent digest before JSON parsing. No economic output file
is created by tests or implementation.

The E.5 transport is unchanged: its `NOT_PERFORMED_transport_only_TEST` accounting
label remains mandatory. Its small fabricated source envelope is not the parser's
publication schema. There is no implicit promotion or relaxed conversion between
them; any future mapping needs its own explicit review and tests.

## Frozen scientific behavior

BTCUSDT then ETHUSDT remain separate, with 2,195 decisions and 10,979 minute
references each. Each market has independent 10,000-USDT Ridge, cash and B&H
portfolios and 8,784 hourly marks for each available account. The unavailable B&H
representation is retained with no fills/marks and no invented performance.

Endpoints remain `[2024-01-01T00:00Z, 2025-01-01T00:00Z)`, with last valuation at
December 31 23:00. Positive Ridge means prediction strictly greater than `1e-12`;
assumed availability is source open +4h+60s and strict next-minute execution maps
12:01 to 12:02. B&H starts January 1 00:00. Separate 10-bps fees, 1-bp half-spread,
2-bps slippage and `0.000001` quantity steps are unchanged. Sticky exits, retained
terminal holdings, leap day and partial last-day/month returns remain intact.
There is no 2025 price, automatic liquidation, forecast regeneration, tuning or
combined-market portfolio. Costs come from each actual fabricated minute fill.

## Offline validation and access boundary

The first repository read was the exact `AGENTS.md`, followed by exact HEAD and
scoped tracked diffs. Named dependencies were read only after explicit permission;
the owner subsequently permitted necessary source-code reads. No original archive,
publication/sign-off, signed owner approval, private key, credentials or ignored
evidence folder was opened, listed, statted, hashed or modified. No network,
database, source-loader call, deployment, signing, genuine backtest, commit or push
was performed. Preservation checks apply to explicitly named tracked files; they
do not claim observation or rehashing of forbidden evidence.

`tests/run_e5c_guarded.py` installs denials before project imports. A custom exact
source finder imports the real allowlisted modules without repository directory
enumeration. Pytest collects only exact test modules, with no conftest, plugin
autoload, bytecode writes or caches. Only standard-library and installed runtime
package directories permit import discovery; project paths are enumerated in the
launcher. Protected paths are rejected before metadata calls, reads check lexical
components for symlinks, writes/processes/network are rejected, and test fixtures
also block loaders, publishers and database connections. Pytest may restore the
known repository root at shutdown; directory changes elsewhere remain denied.
These are procedural Python guards, not an OS sandbox against hostile native code.

Commands:

```sh
python3.12 -I -S -B tests/run_e5c_guarded.py --small
python3.12 -I -S -B tests/run_e5c_guarded.py --regressions
python3.12 -I -S -B tests/run_e5_guarded.py
.venv/bin/ruff check --isolated --no-cache --no-respect-gitignore --select E,F,I,UP,B --target-version py312 src/backtest_badger/genuine_backtest_reporting_integration.py tests/test_genuine_backtest_reporting_integration.py tests/run_e5c_guarded.py
.venv/bin/ruff format --check --isolated --no-cache --no-respect-gitignore --target-version py312 src/backtest_badger/genuine_backtest_reporting_integration.py tests/test_genuine_backtest_reporting_integration.py tests/run_e5c_guarded.py
```

The regression selector includes the new integration, publication/parser, private
replay, reporting and synthetic minute historical tests. Imported source fixture
modules are helpers only: their loader/writer/signing test suites are not collected.
The E.5 launcher runs separately and still requires exactly 87 executions and zero
skips. The new launcher rejects incomplete integration collection or skipped calls.

CI keeps its existing ordinary checks and the mandatory 87-test E.5 step unchanged,
then adds a mandatory exact-file guarded E.5c step. Ordinary pytest also collects
the new tests; neither CI route authorises genuine inputs or economic publication.
No CI run was triggered or queried here. Repository-wide tests, database tests,
source-loader/signing tests and original E.4 verification are deliberately not run
locally. Local Ruff is the installed `0.17.0`, matching the approved lockfile;
no dependency sync/download is performed.

Final test counts and preservation results are recorded below after completion.

## Remaining execution-authority work

Current E.5d status: [operator review stopped at the custody boundary](stage-04b2e5d-operator-review.md).
Independent retention and protected one-attempt state are unresolved; no E.5d
operator is complete and E.5e is not ready for authorisation. The E.5c implementation
and its fabricated-only guarantees below remain unchanged.

2026-10-24 continuation: the [E.5d report](stage-04b2e5d-operator-review.md) now
records a fabricated supervisor/worker custody implementation and validation. The
preceding five-line status is preserved as the earlier checkpoint; actual macOS
isolation, installation/runtime closure and genuine authorisation remain gated.

Owner review, separately authorised commit/push and CI on that resulting commit
remain outstanding. A future genuine runner still requires an independently
reviewed implementation/runtime closure, exact authorised original input reads,
independently controlled producer/account fingerprint retention, explicit
single-attempt economic execution authority and separately approved immutable
publication handling. None is supplied by this TEST bridge or by the historical
verification/sign-off. No genuine performance result is produced by this stage.

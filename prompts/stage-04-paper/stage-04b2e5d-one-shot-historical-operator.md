# Backtest Badger — Stage 4B.2E.5d request archive

Received 2026-10-23 (Europe/London). Substantive owner request transcribed below;
headings and paragraph spacing normalised. This archive grants no further authority.

## One-shot historical evaluation operator (FABRICATED EXECUTION ONLY)

### First action and reviewed baseline

You are working in ~/Code/backtest-badger at reviewed baseline commit
09af01225d752cc3b02c08752e42587c353710f8 (CI 39993266953, successful). Before any
other repository commands, read the exact root AGENTS.md by its specified path.
Do not begin with pwd, unrestricted git status, rg --files, recursive discovery,
environment dumps, or attachment/session metadata. Thereafter use exact named
paths and scoped checks. If the checkout has moved, stop and report the discrepancy
rather than proceeding against an assumed baseline.

Review the existing frozen contracts and code by exact path, starting with:

- docs/stage-04b2e5-one-shot-backtest-preparation.md,
  docs/stage-04b2e5-run-contract.json
- docs/stage-04b2e5b-minute-economic-reporting.md,
  docs/stage-04b2e5c-fabricated-reporting-integration.md
- docs/stage-04b2c-minute-execution-protocol.md
- src/backtest_badger/genuine_backtest_preparation.py,
  genuine_backtest_reporting_integration.py, genuine_minute_publication.py,
  genuine_minute_replay.py, genuine_minute_signed_approval.py,
  genuine_minute_verification_operator.py, paper_minute_historical.py,
  paper_minute_reporting.py
- tests/run_e5_guarded.py, tests/run_e5c_guarded.py,
  tests/test_genuine_backtest_reporting_integration.py, .github/workflows/ci.yml,
  pyproject.toml, uv.lock.

You have permission to read/import further repository source code and synthetic
test dependencies only as necessary, provided they are identified in your final
report. This does not allow accessing original evidence, artifacts/, private keys,
credentials, .env, AWS, provider endpoints, real trading, database mutation, or
production infrastructure. Reading a module is not permission to invoke its I/O
or protected operations.

### Objective

Complete the implementation and fabricated validation of a single-use local
historical research execution operator so that the owner can subsequently review
a precise, short, independently authorised procedure for one genuine 2024
BTCUSDT/ETHUSDT evaluation. Consolidate existing components; do not rebuild the
monetary engine, invent a second signal engine, or create a generic execution
framework. This stage must not run against the four original publication/sign-off
files and must not produce any genuine economic results.

Build the smallest auditable one-shot implementation and accompanying owner
runbook, with these requirements:

1. **Distinct approval and trust** — New versioned exact-payload owner approval,
   separate from D-series verification consent and E.4 compatibility consent.
   Bind approval to four absolute original input locations and independently
   retained byte lengths/SHA-256, frozen 2024 method, two markets and six separate
   portfolios, full reviewed code/dependency/runtime identities, exact Git commit
   plus successful CI, unique attempt ID, validity window, output directory,
   publication contract and maximum_attempts=1. Reuse independently enrolled
   owner-verification primitives where safe, but never treat old signatures,
   historical sign-off, same-process hashes, a CLI argument or an environment
   variable as execution authority. Distinguish signer identity from historical
   evidence provenance. Any genuine route remains unconditionally closed in this
   stage, including the previously closed public replay_genuine_minute_historical
   API.
2. **One-attempt durable consumption** — Validate preflight before consumption;
   atomically reserve/consume exactly one attempt before any economic calculation.
   Concurrency, crash, interrupted write and ambiguous state must be fail-closed.
   A reserved/started/uncertain attempt cannot be retried, resumed or replaced
   without a new owner review. No read-only preflight should silently consume an
   attempt. Model the state machine with deterministic fault-injection tests.
   Avoid relying solely on same-process mutable memory or a writable untrusted
   JSON claim as a security boundary.
3. **Exact input and run closure** — A reviewed runner must use bounded, no-follow
   reads of only the four specifically approved publication/sign-off files, with
   descriptor/stat identity checks and pre/post immutable fingerprints, and the
   E.3 pure parser and independent sign-off reconciliation. Never rerun the
   historical D-series acquisition/verification or read minute ZIP/CSV, original
   model files, private signing material, database, provider API, or any other
   source. Validate complete checkout/runtime/dependency closure and protocol
   identities before calculation; fail if it is not possible to establish them
   accurately.
4. **One unchanged evaluation** — Call only the already reviewed private
   publication-to-replay pipeline and existing monetary/ledger reconciliation,
   then the reviewed native-minute reporting adapter. Preserve Ridge/cash/B&H,
   10,000 USDT each per market, 12:01 to 12:02, costs, exact Decimals, HH:00 marks,
   partial final periods and no terminal liquidation. Do not alter any strategy,
   thresholds, forecasts, prices, cost policies, frozen code, or analytical
   interpretation. The six account/report fingerprints must be bound to the whole
   replay evidence with a truly independent retained boundary; don't claim
   same-process rehashes prove external independence. If the retention mechanism
   cannot honestly establish the promised property, stop and document it instead
   of weakening it.
5. **Immutable, non-public research publication** — Agree and version the complete
   output schema before computation. Use a fresh explicitly owner-approved
   directory, not within any original source/evidence tree, with exclusive
   creation, no symlink traversal, bounded private files, fsync, integrity record
   and final manifest-last commit marker, followed by exact readback. Output
   includes every ledger, reference, exact metric, provenance and uncertainty
   statement, plus the identities of the run and owner approval (but never private
   signature material, path secrets, keys or credential content). Partial/crashed
   outputs remain preserved as incomplete, never silently overwritten or promoted.
   Do not publish to the public website or claim positive returns/alpha.
6. **Scientific limitations and privacy** — 2024 was already inspected: any
   resulting evaluation is exploratory, not untouched OOS, live/paper performance
   or evidence of tradable alpha. Historical native minute opens are reference
   assumptions, not real fill/latency/liquidity observations. Ensure private raw
   metadata, source path roots and signing material cannot escape through
   recursively serialised evidence; document a reviewed projection/allowlist.
7. **Tests, review and CI** — Use fabricated inputs and test identities only;
   tests must cover success, six-portfolio reconciliation, ledger and report
   fingerprints, missing/altered files, wrong approvals, stale commit/CI, wrong
   dependency closure, output reuse/symlinks, concurrent attempts, crash/fault
   injection at every durable point, no-retry terminal states, incomplete
   manifest/readback, secret redaction and inability to reach genuine execution.
   Add a mandatory separate guarded CI step if needed, without weakening existing
   87 E.5 and 55 E.5c mandatory steps. Run scoped Ruff and preservation checks and
   the widest suitable synthetic regression tests. Clearly distinguish pass claims
   from tests not run.

### Deliverables and stop gate

Implement narrowly scoped new module(s), fabricated-only test(s), an exact-file
guarded launcher if warranted, an operator review/activation runbook under docs/,
and a substantive archived request under prompts/stage-04-paper/. Update the
immediate stage-status documentation only; do not undertake repository-wide doc
cleanup, Lightsail changes, website work or architectural refactoring in this stage.

Do not access the genuine four historical files, create a genuine output directory,
execute a genuine backtest, sign a real approval, enrol/reveal private keys, access
remote systems, deploy, commit or push. For the user's review, report the
implementation diff, exact tests/results, approved provenance claims versus
demonstrated facts, memory/runtime limits, unresolved gates, and the complete later
owner authorisation payload. If any material property cannot be implemented within
the reviewed boundary, report that precise blocker rather than introducing a
bypass or claiming completion.

The next stage, E.5e, will consist only of a separately reviewed, specifically
authorised one-time original-data evaluation and readback. This prompt gives no
such permission.

## Approved custody-design continuation and validation follow-up

The owner subsequently approved implementation and fabricated testing of a minimal
one-shot local supervisor protected from an unprivileged worker by separate macOS
OS principals. The supervisor owns approval checks, durable attempt consumption,
complete replay/six-account fingerprint retention, report retention and exclusive
publication. Consumption precedes economics; uncertain acknowledgements, crashes
and partial outputs are terminal without automatic retry. Worker reporting waits
for retained replay fingerprints. The owner allowed the existing enrolled public
key only in a separately reviewed execution signature domain and forbade reading
private signing material. Complete relevant code/runtime identity must be frozen
and fabricated full-year resource requirements measured before real limits.

The threat model excludes the trusted Mac administrator, administrative rollback
and physical compromise. Ordinary CI may mock privilege boundaries only with honest
limitations, with a separate OS rehearsal specified. Necessary repository source,
synthetic tests and configuration reads are authorised; original evidence, private
files, credentials, network, production, sudo, real account creation, protected
installation, genuine replay, historical verification reruns, deployment, commit
and push are not authorised. Existing scientific code, protocol, public genuine
guard, prior tests and every uncommitted change must be preserved.

On 2026-10-24 the owner asked to continue the existing implementation, first read
the exact AGENTS.md, inspect scoped changes/logs, and finish fabricated full-year,
concurrency, crash/fault, duplicate, lost-ACK, readback and publication validation.
They requested the 87-case E.5 gate, 55-case E.5c gate, relevant regressions and
scoped lint/format, actual results and complete changed-file inventory, with mocked
isolation clearly distinguished from enforced macOS security. This continuation
gives no genuine execution or installation authority.

# Stage 4B.2E.5 — One-shot historical backtest preparation

Prepared 2026-10-23 (Europe/London). **Inert candidate and fabricated tests only.**
This is an uncommitted owner-review deliverable, not an executable evaluation
operator or a completed economic reporting integration.

The fresh authorisation is archived in
[019-one-shot-genuine-backtest-preparation.md](../prompts/stage-04-paper/019-one-shot-genuine-backtest-preparation.md).
No attachment or session metadata was used. The first repository read was the
exact repository `AGENTS.md`. HEAD was narrowly verified as
`f92203492e1c8ebf4fb337d60222fb50fe67de83`. The owner reports successful CI run
`39939328553` (2,681 passed, one skipped); this was not queried or independently
verified and is not CI for these changes. This preparatory baseline is never an
execution-authority substitute.

## Deliverables and hard boundary

- `src/backtest_badger/genuine_backtest_preparation.py`: standard-library-only
  candidate, pure validators, model transition table, TEST-only lossless evidence
  encoding and integrity roundtrip. No filesystem, network, environment, clock,
  signature verification, strategy execution or publication operations.
- `docs/stage-04b2e5-run-contract.json`: canonical machine-readable candidate,
  version `stage-04b2e5-one-shot-candidate-v1`. It contains declarations and
  explicit `OWNER_FILL_AFTER_SEPARATE_REVIEW` placeholders, not live paths.
- `tests/test_genuine_backtest_preparation.py` and `tests/run_e5_guarded.py`:
  fabricated cases and an exact-file, offline launcher.
- This report and the substantive request archive.

Existing code, tests and documents are not edited. In particular, the original
verification, E.3 parser/sign-off reconciliation, public gate, shared planner,
`_replay_minute_core`, accounting, frozen protocol and lockfile remain unchanged.
The historical verification at
`94584dc4b08f06441cff3bcd7983bba1ca0afe8d` must never be rerun. No genuine strategy
execution, original-file access, economic publication, signing, deployment,
commit or push is performed or authorised by this work.

## Three distinct identities

The candidate preserves the following **externally retained declarations** from
the E.2/E.3 guides. These files were not opened, statted or rehashed.

| Historical file role | Bytes | SHA-256 |
| --- | ---: | --- |
| Manifest | 560 | `3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea` |
| Authenticated inputs | 15,272,413 | `2581482b4b8a60fa1a53f7710ed080be7de25d50a76fcae35c8aaf64f2cb2168` |
| Integrity | 74,200 | `23c3d17b2e5b67de701d9a0dd22d6135a907057b9acaeb16bcbdb4cb9c613a8b` |
| Independent D.14 sign-off | 2,020 | `21b04470e861a039750bf7b665b993d332bf998fcc5b9fea47dc2c8b80f334b4` |

The historical verification commit is pinned separately. Its exact original CI
run ID is not supplied in the named E.2/E.3 guides; it deliberately remains an
owner-filled field. Do not substitute the E.5 baseline CI. Original published
`genuine_execution_authorised` and `economic_results` remain false. The reported
E.4 compatibility PASS is historical context only; no E.4 script was read or run.

The future implementation identity must bind the reviewed execution checkout,
successful CI for exactly that checkout, protocol version/hash, exact Python
3.12 patch runtime and executable identity, installed dependency inventory,
lockfile and project configuration. The role inventory identifies the public
guard, private parser, sign-off validator, private replay, planner, monetary
core, ledger checker, minute summary, accounting, types, strategy, affordability,
historical types, authentication/intent/integrity dependencies, preparation
module, future runner and future reporter. Each role requires a file hash/length.
The complete transitive code/dependency inventory and its identity remain
explicitly unresolved: completing it would require reads beyond this stage's
allowlist. Neither placeholders nor a matching role list prove closure.

The third identity is a **new exact-payload one-shot owner approval**, independent
of original verification consent, compatibility consent and historical sign-off.
The future approval must bind all four exact absolute input paths and pins,
strategy, markets, full frozen method, implementation/runtime/CI, output policy,
unique attempt identifier, not-before time, expiry, and maximum attempts of one.
Its envelope must be owner-signed or independently owner-validated over the exact
canonical payload. How that trust is established is a separate review decision.
There is no live verifier or usable signature format in this stage.

## Pure contract validation and model states

`candidate_contract()` returns a detached canonical value. `validate_candidate`
accepts only the unchanged inert template. `validate_test_contract` accepts only
a separately pinned fabricated specimen with explicit TEST provenance, invented
paths under `/TEST_ONLY/`, unrelated file identities and a fake implementation.
It rejects actual retained publication pins. No populated genuine run-contract
validator or public execution switch has been introduced.

The TEST approval schema is `stage-04b2e5-TEST-approval-v1`; its exact fields are
`schema`, `purpose`, `contract`, `paths`, `pins`, `implementation`, `method`,
`output`, `attempt_id`, `not_before`, `expires_at` and `maximum_attempts`.
The fabricated owner claim contains only `kind`, `approval` (hash/length),
`signature` (a visibly TEST-only string) and `external_independence_proven=false`.
`test_preflight` compares all fields with separately supplied expected historical
and implementation claims and simulated observations. It refuses output reuse,
unknown freshness, stale checkout/CI, missing approval and consumed/uncertain
attempts. It reads no path and never reports external independence or authority.
Caller-invented expected values cannot establish owner consent or authenticity.

`attempt_transition` is an inert finite table:

| From | Event | To | Authority consumption model |
| --- | --- | --- | --- |
| UNSTARTED | refuse preflight | REFUSED_NOT_ATTEMPTED | Not consumed |
| UNSTARTED | accept TEST preflight | READY_MODEL_ONLY | Not consumed |
| READY_MODEL_ONLY | approval expired | REFUSED_NOT_ATTEMPTED | Not consumed |
| READY_MODEL_ONLY | consume before start | CONSUMED_STARTED | Consumed |
| READY_MODEL_ONLY | consumption uncertain | UNCERTAIN_TERMINAL | Treat as consumed |
| CONSUMED_STARTED | complete | COMPLETED_TERMINAL | Consumed |
| CONSUMED_STARTED | crash | CRASHED_TERMINAL | Consumed |
| CONSUMED_STARTED | status unknown | UNCERTAIN_TERMINAL | Treat as consumed |

All other transitions fail, including retry, resume and restarting any terminal
state. These return values are not capabilities. A future runner must recheck
approval validity at durable consumption, atomically record consumption before
the first calculation, and make it impossible for concurrent processes to spend
the same approval. Missing/ambiguous crash records must fail closed. Durable
storage, locking/CAS, time source, audit record format, resource/time limits and
failure handling are unresolved; **there is no persistence here**. A refused
preflight is recorded separately from attempted computation. No automatic retry
or new attempt follows either refusal or failure; owner review is required.

## Frozen study and evidence transport

The fixed study is `[2024-01-01T00:00:00Z, 2025-01-01T00:00:00Z)`, previously
inspected exploratory validation, not untouched out-of-sample data. Each market,
BTCUSDT and ETHUSDT, has separate 10,000-USDT Ridge Sign, cash and inception B&H
accounts. No combined portfolio is defined. Ridge uses the unchanged strict
`prediction > 1e-12` threshold; no reforecasting, fitting, trial selection or
scenario changes are allowed.

Availability remains source-open +4h+60s, execution strictly next native minute
(12:01 to 12:02), and B&H inception 00:00. Native minute references supply HH:00
marks, with trade-before-mark ordering and final holdings retained. Costs remain
10-bps fees rounded UP to 1e-8 USDT, 1-bp half-spread, 2-bps adverse slippage and
0.000001 quantity step. Exact 160-digit Decimal money, 80-digit HALF_EVEN ratios
and WAC, sticky exits and ledger-prefix reconciliation are preserved requirements.
No monetary engine is called by this stage's tests or new code.

The in-memory export schema is `stage-04b2e5-fabricated-evidence-v1`:

| Field group | Meaning |
| --- | --- |
| Schema/provenance/flags | Mandatory TEST provenance; execution, economic publication and external-independence claims all false |
| Contract identity | Exact candidate specimen hash and byte count, without its input/output paths or approval envelope |
| Original file claims | Four fabricated pins, historical commit/CI and false flags, explicitly fabricated |
| Implementation claims/protocol | Fake reviewed closure/runtime/CI plus unchanged protocol version/hash |
| Method/metrics/warnings | Exact frozen definitions and explicit unresolved-reporting markers |
| Results identity | Separately supplied exact canonical result hash/length |
| Results | Two `_PublicationReplayResult` field trees, preserving decisions, sources, independent account states, fills, signed postings, mark states and all supplied costs |
| Counts | Decisions by market and fills/marks/status by independent account |
| Accounting validation | Always `NOT_PERFORMED_transport_only_TEST` |
| Approval/private paths | Always `intentionally_excluded` |

Decimals are finite bounded strings with their original scale preserved;
timestamps retain aware UTC ISO representations. Canonical JSON has sorted keys,
compact separators, ASCII escapes and one final newline. Duplicate keys, floats,
NaN, infinities, overflow encodings and noncanonical encodings are refused.
Exact types prevent bool-as-byte-length confusion. Decode checks a separately
retained export identity; this is integrity checking, not authentication.

The adapter consumes existing publication-result class **shapes**, fabricated
in-memory file envelopes and separately retained result pins. Source and monthly
identities, two-market ordering, full 2,195-decision grids and 8,784-hourly-mark
grids per available account are checked. Fills retain decision/time and source
links, exact ledger postings, fees, spread and slippage; cash cannot have fills
and B&H fills must be at inception. Missing/duplicate decisions and missing,
duplicate or reordered marks are rejected. Unavailable inception B&H retains its
explicit reason and no invented later buy.

This is a transport candidate, **not a certified economic export**. It does not
recompute prices, account balances, sticky exits, strategy actions or ledger
prefixes. Full ledger/accounting verification must later reuse the unchanged
`verify_minute_account` before reporting. The tests even include an intentionally
inconsistent fill specimen to verify exact transport without falsely reporting
accounting PASS. Class names, private dataclasses and supplied hashes cannot
prove authenticity against a malicious in-process caller. Fixture/synthetic
wrappers are refused by the normal shape checks, and neither a forged wrapper
nor any caller flag can produce a genuine-result schema through this API.

The outer evidence never contains the approval signature, its four absolute
paths or the output directory. No real signing material or private path was
supplied. A future economic exporter still needs a reviewed allowlist/redaction
policy for nested source evidence; arbitrary caller data is not safe publication
content. There is no economic publication implementation here.

## Reporting decision deliberately left open

The named `paper_minute_historical.py` already provides `minute_account_summary`:
last-mark P&L, funding-relative marked return, observed hourly reference-mark
drawdown, exact costs by side, exposure durations and invested-mark fraction.
Future reporting must use that unchanged primitive, retain its exact operands,
and retain cash, quantity, basis, realised P&L, unrealised P&L and equity directly
from the existing account/mark records. This stage computes none of those metrics
and adds no new realised/unrealised return ratio or risk statistic.

Inspection of `paper_historical_evaluation.period_observations` and `cost_summary`
found an integration blocker: they look up trade costs against the supplied
hour-boundary reference set, whereas minute trades can occur at HH:02. Reusing
that hourly reporter unchanged would be incorrect. A later reviewed pure adapter
must attribute costs from each existing minute fill/reference, retain all daily
and monthly periods and use the unchanged observation conventions. That adapter
and its economic reconciliation tests are not silently invented here.

Freeze these endpoint semantics now: complete daily returns use consecutive UTC
midnight marks; December 31 is 00:00 to 23:00, a 23-hour incomplete observation
excluded from complete-day statistics. December is partial by one hour. There
is no 2025-01-01 00:00 price. Calendar flow buckets use actual minute-fill times
in `[start, next boundary)`. B&H inception costs precede its first post-buy mark
and remain included in funding-relative return/drawdown. END is a duration
boundary for open holdings only. Drawdown is observed hourly, not intrabar.

## Prospective publication plan — no implementation

The owner must later select a new absolute directory and explicitly approve the
output policy. It must not be an input directory, a parent/child alias of one,
the original `artifacts/audits/stage-04b2d3-minute-inputs-v1/`, the historical
sign-off location or any existing historical/validation result directory.
No destination has been selected or probed here.

The proposed minimum bundle is a versioned evidence data payload, integrity
record and manifest commit marker. A future writer must create a fresh directory
exclusively without following symlinks, write each data file exclusively, flush
and sync, then write/sync integrity with exact data identities, then publish the
manifest **last** with exact identities of both data and integrity. The manifest
must not hash itself. Readers accept only a complete validated bundle with its
final manifest. Partial output after failure is retained as incomplete evidence,
never overwritten, resumed or used as permission to repeat computation.

Atomic visibility and durability must be reviewed for the selected filesystem:
staging plus a no-replace atomic final-manifest operation and directory fsync are
requirements, not an implemented portability claim. The attempt-consumption
record must survive a crash independently of economic publication. Approval
bytes/signatures/private paths belong in a separate owner-controlled audit record;
economic output may carry their non-sensitive digest and scope identifiers only.
Output size limits, file partitioning, filenames and the final reporting schema
must be approved before any computation, never chosen after seeing results.

## Validation and preservation

The launcher installs exact repository-path, private/original-source, filesystem
write, process and network denial **before project imports**. It permits the
interpreter's concrete standard-library directory for imports; Python import
machinery may enumerate those package directories. Repository enumeration,
unlisted repository reads, symlink traversal and all test-time file writes are
denied. No pytest plugins, conftest or historical test fixtures are imported.
These are Python/procedural guards, not an OS-enforced sandbox.

Because normal imports of the named bridge and replay tests transitively read
unlisted repository files, tests compile only the unchanged named result class
definitions and public guard from their ASTs in an isolated namespace. No import,
parser, verifier or monetary-loop body from those modules is executed. Fabricated
envelopes have explicit TEST provenance and do not imitate a valid authenticated
E.2 publication. Thus **full E.2/E.3 parser-to-core-to-export integration remains
unverified** under this restricted read scope. Ordinary pytest discovery skips
this new test class; the explicit guarded command is required.

```sh
python3.12 -I -S -B tests/run_e5_guarded.py
```

The final launcher uses `-I -S -B`: isolated import paths, disabled site startup
and disabled bytecode writes. Python 3.12.13 is the installed test runtime; no
dependencies were installed, synchronised or fetched. This standard-library
transport test does not validate the project's locked dependency environment.

The guarded suite passed **84 tests**, no failures or skips. It covers strict
encoding, exact source and approval bindings, cost/date/instrument mutations,
missing/duplicate grids, false independence claims, source/fill swaps, fake
wrapper injection, hostile public-gate arguments, consumed/expired approvals,
output reuse/uncertainty, no-retry states, protected paths, network denial,
simulated symlink denial and static absence of operational imports/calls.

Ruff **0.12.0**, available locally, passed lint for all three added Python files.
Format checking passed for all **12 explicitly named Python files** (nine existing,
three new). The broader scoped lint command found **three existing UP038 warnings**
in unchanged `paper_historical_evaluation.py:227` and
`paper_minute_historical.py:75,78`. Those files were preserved. `uv.lock` specifies
Ruff **0.17.0**; validation with that locked tool remains outstanding. No download
or environment synchronisation was attempted. Lint used the project's explicit
E/F/I/UP/B rule selection and Python 3.12 target, with config/ignore discovery and
caching disabled. The full suite and exact locked-runtime CI were not run.

Scoped Git comparison against HEAD passed for all 19 named existing paths,
including the public guard, bridge/parser/sign-off module, shared minute core,
accounting, frozen protocol, existing tests, project configuration and lockfile.
Only the six new deliverable paths appear in the scoped status check. New-file
whitespace checks pass. HEAD remains the original requested baseline.

The initial guard refused imports before collection until the concrete standard
library path and its import-directory enumeration were allowed. No denied file
was read. Initial lint issues were corrected. No pass count is attributed to
those aborted launches.

Repository-wide `ruff format --check .` would violate the prohibition on recursive
discovery and reads outside the named paths. Validation therefore uses explicit
file arguments with `--isolated`, `--no-cache` and no Git-ignore discovery. Python
fences in this report are absent; its sole command fence is shell. The archived
request contains no executable Python fence. The machine-readable contract is
checked byte-for-byte against the pure candidate generator by a guarded test.

Preservation checks are scoped tracked Git comparisons, not original evidence
readback. Ignored original files, E.4, CI and unnamed source/dependency files are
not inspected. No claim is made that their bytes were independently audited.
No unrelated existing document was changed merely to announce this candidate.

## Future owner-authorisation template and review gates

This template is descriptive and intentionally incomplete. It grants nothing:

> I separately approve the exact one-shot historical evaluation payload
> SHA-256 [fill] / byte length [fill], attempt ID [fill], valid from [UTC] until
> [UTC]. I approve execution checkout [SHA], successful CI [run ID tied to SHA],
> exact runtime/dependency/code closure [identity], frozen minute protocol
> [version/hash], BTCUSDT and ETHUSDT independent Ridge/cash/B&H portfolios over
> the frozen 2024 interval, and no other strategy, scenario, source or period.
> I authorise bounded no-follow read-only access to exactly [four absolute paths
> with their four independent hashes and lengths]. I separately approve the
> fresh output directory [absolute path], final reporting schema [identity] and
> exclusive-create atomic publication policy [identity]. I validate this exact
> payload independently or sign it through the separately reviewed mechanism
> [identify]. Historical verification consent, D.14 sign-off and compatibility
> consent are not this approval. One durably consumed computation attempt only;
> no retry, resume or replacement run after start or uncertain status. Preserve
> all original evidence and retain all incomplete/crash records for review.

Outstanding gates: complete and verify original historical CI declaration;
review/fill execution checkout/green CI and precise transitive closure; implement
and test the minute reporting adapter; establish independent exact-payload owner
validation; review the no-follow four-file runner, durable single-use/crash model,
resource bounds and output destination/publication mechanism; then separately
authorise original-file access and exactly one evaluation. The public genuine
gate remains unconditionally closed throughout E.5.

Retrospective archive prices are neither contemporaneous quotes nor actual
fill/latency/liquidity evidence. These hypothetical results could not establish
profitability or tradable alpha even after a later authorised evaluation.

FABRICATED TESTS ONLY · NO ORIGINAL EVIDENCE ACCESS · NO GENUINE REPLAY ·
NO ECONOMIC PUBLICATION · NO COMMIT OR PUSH.

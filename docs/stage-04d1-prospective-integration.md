# Stage 4D.1 — Prospective forecast and market-data integration

Work started on clean main at `6ddaf54631b163f29812f44897be7188ec31b271`.
GitHub CI and Frontend had both succeeded. The implementation connects the
Stage 3 originals, Stage 4B.1 policy and Stage 4C recovery reader in a
single-cycle **proposal planner**. Only fabricated tests write financial events.
The published research, website, forward collectors, scorers and feeds use
their existing entry points. The approval boundary for inception is Stage 4D.3.

## Local commands

Use the repository's locked Python 3.12 environment.

```sh
python -m backtest_badger.paper_worker
python -m backtest_badger.paper_worker dry-run
python -m backtest_badger.paper_worker market-smoke
```

The first two commands read only packaged fabricated records and journals.
They emit one JSON proposal to stdout. Forecast observation, decision, hypothetical
submission and the need for a subsequent quote appear separately. The account
and original files stay unchanged. There is no database client configuration,
scheduler, financial writer or order transport behind either command. A module
entry point avoids changing the existing CLI and dependency files fingerprinted
by the forward model recipe and the Study 002 freeze.

Only the third command opens a network connection. It reports availability,
validation, hashes, UTC observations and latency. A nonzero exit denotes a failed
check. An optional `--filter-archive PATH` saves original exchangeInfo bytes under
their SHA-256 in an explicitly selected, existing owner-only directory. Publication
uses a private staging file, exclusive link and byte comparison on replay. The
default smoke invocation retains source bytes in memory for validation and writes
only its diagnostic output. Use the offline tests to reproduce failures.

## Original evidence and eligibility

`read_forecast(portfolio, opened, records, operations, clock)` searches for the
exact Stage 3 filename in explicit evidence directories. Descriptor-relative opens
refuse symlinks along the path and enforce regular-file limits of 256 KiB per
forecast and 128 KiB per journal. A missing record in readable directories is a
grid observation. A missing directory, a journal referencing a missing record or
a corrupt original has a distinct error path.

The Stage 3 `load_prediction` verifier reads the pinned bytes. It checks the
published canonical encoding, content checksum, exact market, source grid, seven
input candles, causal features, four unique model/prediction identities, recipe,
target boundaries and issuance chronology. The portfolio's configured recipe
hash must match. A second parse of those same canonical bytes reads the original
Ridge JSON number into Decimal. The fixed sign decision uses strict
`prediction > Decimal("1e-12")`. This preserves the published number's precision.

The reader checks journal run and filename identities, paths, original file and
content hashes, and issuance times. It calls the existing Stage 3
`parse_journal`, `matches_automation`, `classify` and `validate_cohort`.
Only one publisher can claim a horizon. A later `already-recorded` check cannot
establish authorship. Unsafe or contradictory evidence stops the affected cycle.
The observation retains the original record bytes, safe relative filename, Ridge
prediction ID, journal bytes and both source hashes. The configured directories
and recipe pin form a trust boundary. These checks authenticate consistency with
the collector's retained evidence. A party able to replace both originals and
their trusted configuration could fabricate a self-consistent pair.

For a source opening at t the window is [t + 4h + 60s, t + 4h + 16min).
Issuance must also follow actual portfolio activation. Discovery and decision
have their own current timestamps. Late discovery preserves the Stage 3 cohort
and prevents entry. An unattributed record during publication is reported as
ineligible while the worker waits for the journal. This avoids consuming revision
0002's unique forecast key during the gap between the two Stage 3 publications.
A later incompatible claim against an already committed original pauses planning.
No outcome files, target candles or model fitting enter this path.

A read-only check on the local archive recognised the BTC source opening
2026-10-14 12:00 UTC as `primary_timely_automated` and ineligible at discovery
on 7 November. Its file SHA-256 was
`9383fb565c08a469f4fe2c38a7f6276f28e4b1d3944fe62c1e2ada0d73ed21c9` and its
journal SHA-256 was
`148a2f15c9aa519ca79caaa43dafb23ed1d6f659fff3205b94f000c111cd231d`.
All 114 local collector journals passed Stage 3 parsing. This inspection created
no financial or Stage 3 records.

## Public market evidence and time

Only BTCUSDT and ETHUSDT on the fixed HTTPS host `data-api.binance.vision` are
accepted. Each GET uses a constructed symbol-specific path, a two-second socket
timeout, a foreground POSIX elapsed-time guard, bounded reads and no redirects,
environment proxies, credentials or retries. HTTP 418/429 stops the entire smoke
action, with bounded numeric Retry-After information when supplied.

* `/api/v3/ticker/bookTicker` retains up to 4,096 original bytes, SHA-256, URL,
  HTTP status, request start, receipt, monotonic duration, invocation and unique
  quote identity. The strict five-field parser checks Decimal strings and calls
  `validate_quote`. Zero displayed quantity can be a valid observation. It cannot
  support a positive simulated fill on that side. A quote lacks an exchange-side
  timestamp. Client latency cannot establish executable depth or an available price.
  [Binance order book ticker](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market)
* `/api/v3/exchangeInfo` gets a separate 65,536-byte bound for the single-symbol
  response. The immutable response holds the original JSON, identity, time and
  hash. Sizing requires the correct spot symbol, currencies, trading status and
  MARKET capability. LOT_SIZE and MARKET_LOT_SIZE intersect on their common
  step, computed with an exact integer least common multiple. Enabled quantity
  minima take the larger value and maxima take the smaller. The resulting grid
  must contain a positive size. Zero disables the corresponding component.
  [Binance exchange information](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/general)
* MIN_NOTIONAL and NOTIONAL combine according to their market flags. Missing
  required fields, unknown material rules, incompatible increments or an
  unrepresentable upper quantity bound reject the proposal. Price ticks and
  reference-price metadata remain in the original body. The v1 simulation checks
  modelled notional. Binance can use a different reference price for admission.
  Stage 4C takes the effective version, hash, observation time and Decimal
  constraints. The complete original response stays outside the quote column.
  [Binance filters](https://developers.binance.com/en/docs/products/spot/filters)

`Clock` brackets each UTC sample with independent monotonic nanoseconds. It
rejects reversed timestamps and wall deltas outside the sampled monotonic
interval, allowing only UTC microsecond representation error. Each invocation
owns a new UUID and can run one worker cycle. Absolute UTC accuracy still depends
on the host. Bracketing two local clocks cannot prove external synchronisation.
The limits remain 2 seconds for quote receipt, 1 second from receipt to use,
30 seconds for an intent, and 1 hour for filters acquired before submission.
A buy must also finish before the exclusive forecast deadline and target close.

### Bounded public feasibility observation

Four public responses on 7 November 2026 each returned HTTP 200. Both ticker
payloads passed quote validation and both exchangeInfo payloads yielded effective
filters at observation time. The following times are UTC. No server-time request,
repeat request or account request was made.

| Market | Endpoint | Request start | Receipt | Monotonic seconds |
| --- | --- | --- | --- | ---: |
| BTCUSDT | bookTicker | 15:34:16.261718 | 15:34:17.285531 | 1.023813250 |
| BTCUSDT | exchangeInfo | 15:34:17.290019 | 15:34:18.513212 | 1.223199125 |
| ETHUSDT | bookTicker | 15:34:18.517671 | 15:34:19.488692 | 0.971026458 |
| ETHUSDT | exchangeInfo | 15:34:19.493047 | 15:34:20.516389 | 1.023345333 |

The check used in-memory retention. Subsequent hardening of the total HTTP time
bound, archive option and unknown-field handling was tested with fabricated
responses. The original smoke bodies were discarded, so the live validation count
above applies to the checks in place at observation time.

## Recovery and transition matrix

`recover(conn, pid)` uses one read-only REPEATABLE READ transaction. The Stage 4C
audit replays paired postings, fills, marks and exit satisfaction. The planner reads
activation, the latest evidence time, attempts, scheduled slots and the expected
source grid in the same snapshot. It checks the missed streak against the
sequence of decisions. `cycle` receives this reader, a forward reader, filter and
quote adapters, an invocation clock and an output sink. The sink receives one
plan. Stable decision and attempt keys express idempotency across fresh run IDs.

| Input or durable state | Proposed transition |
| --- | --- |
| Eligible positive, flat / long | BUY_REQUIRED / HOLD. A buy needs a current filter snapshot and fresh post-submission quote. |
| Eligible nonpositive, long / flat | EXIT_REQUIRED / CASH_NOOP. The original exit decision owns all subsequent attempts. |
| Late, stale or unattributed original | Report original cohort and actual discovery. No model-driven entry or exit. |
| Missing expected original | Wait through the deadline. After it, register the actual discovery time for each elapsed horizon. One miss while long yields SIGNAL_STALE. A second consecutive miss while long creates one risk exit. An eligible horizon resets the streak. |
| Pending exit, later positive | IGNORED_EXIT_PENDING. Continue planning against the original exit, including after its deadline. A source outage leaves a known obligation actionable. Conflicting evidence pauses the cycle. |
| Rejected/expired exit | Wait until the previous submission is at least five minutes old. Propose one new attempt and a fresh post-intent observation. |
| Rejected/expired buy | Preserve the terminal reason and wait for a new eligible forecast. A previous buy signal cannot authorise re-entry after its exit was satisfied. |
| Committed decision without intent | Recheck original buy evidence and current eligibility before proposing the stable intent. |
| Submitted intent interrupted, with or without quote | Propose rejection or expiry at discovery. A prior process's quote cannot become a restarted fill. |
| Committed fill and postings | Reconcile the complete pair. A repeated cycle adds no postings. |
| Stale or unsupported filters / changing snapshot | Reject the hypothetical attempt / request a new plan from coherent state. |
| Inactive, blocked dust or integrity incident | Report the state and block economic action. A dust pause retains its original exit. |
| Scheduled mark | Use +10 minutes on the four-hour grid and a five-minute capture window. Check a fresh bid against a re-read account prefix, including its posting time. Report a gap for an elapsed unmarked slot. Prior marks are immutable. |

The planner makes no financial database writes. A mark is a proposal for a
particular observed quote and ledger prefix. A future writer must pin that prefix
under the portfolio lock. A hypothetical order contains an immutable balance
snapshot and an expiry. Only the isolated test harness subsequently commits an
intent, requests its synthetic quote and invokes Stage 4C's atomic fill writer.

## Fabricated acceptance and reproducibility

The fixture portfolio key is `fabricated-stage-4d1`, UUID
`fa927ef9-a99b-5731-8e01-a95bfa0d9ddc`. The Ridge recipe pin is
`c83e3f41ebb0059e4d4173c871e26979918462600eaa3b0e9554dcd3419b169c`.
Both sources and their journals are packaged test data. Their paths and identities
use the Stage 3 publication format. No scientific model was trained for this fixture.

| BTC source open, 14 Oct 2026 UTC | Ridge | Original file SHA-256 | Journal SHA-256 |
| --- | ---: | --- | --- |
| 08:00 | 0.001 | `f756c02c9092fe5feae3fda8feade79513940557fa0844e9a7e240a57f83d0de` | `88a33e1e1102cd1f1a103b47dd66adfc02c3493c4fae986d32f1c4a90065a7c3` |
| 12:00 | -0.001 | `afad6a0fd3ab78e3d96eabaa6b6c65a1ff85169f38fc11281f85e738526fdf3b` | `9bf7ed3f46c8e211db0998b1f017c583c6f47204460c973d221039fb5e742892` |

The PostgreSQL acceptance case activates its fabricated fixture at 12:10 UTC
in a newly created revision 0002 database. At 12:11 the flat account proposes
BUY_REQUIRED. After saving the decision, a restart reproduces the same intent
key. The harness submits once, observes its synthetic quote 250 ms later and
commits a simulated buy. Recovery finds 99.88 BTC, 0.01240240 USDT and ledger
sequence 3. At 16:11 a negative original creates a sticky exit. A failed quote
and rejection leave holdings unchanged. A restarted cycle at 16:16 proposes exit
attempt 2 and a gap for the uncaptured 16:10 mark. After the harness supplies a new
order-linked quote, liquidation reconciles at sequence 5 with zero BTC, zero basis
and 10973.63043976 USDT. These numbers are deterministic accounting fixtures.

Separate cases restart after intent commit and after quote receipt, expire the
buy at its real discovery time, recover two missed horizons without postings,
retain blocked dust and detect deliberate original funding-time corruption.
Every database planning call in the rehearsal compares financial rows before and
after. The earlier Stage 4C suite additionally exercises eight rollback points,
separate-connection races and dump/restore via a dedicated PostgreSQL 17 container.

## Local verification

The baseline suite ran in parallel with implementation. The completed local
regression and acceptance runs cover all 3,362 tests collected at handoff.

| Check | Executed result |
| --- | --- |
| Baseline root pytest, private macOS scratch, loopback PostgreSQL 17 | 3,140 passed, 88 skipped in 19m 59.88s |
| New adapter, clock and planner unit cases | 128 passed |
| New PostgreSQL worker cases | 6 cases, all executed as part of the final focused run |
| All integration tests plus Stage 3 forward and paper primitives, records and new units | 860 passed in 34.10s, including all 234 PostgreSQL integration cases |
| Guarded E.5 / E.5c / E.5d runners, Python 3.12 with `-I -S -B` | 87 / 55 / 153 passed |
| Ruff lint, formatting, wheel build, wheel-only fixture launch, Git whitespace checks | Passed |
| Study 001 and 002 | Both original summary/detailed evidence pairs matched their published SHA-256s. All 57 Study 002 frozen files matched. |

The root suite's 87 E.5 skips require the separate guarded invocation above. Its
one further skip is the explicit genuine Study 001 replay. We verified retained
bytes without rerunning historical economics. A first corruption injection was
rejected by a database CHECK before reaching the reader. The final test alters a
funding timestamp inside its disposable database and verifies an integrity pause.

On this macOS host, 100 warm offline fixture proposals took a median 1.389 ms
and maximum 2.319 ms. Process high-water RSS was 141,574,144 bytes, including
Python and the Stage 3 scientific imports. This measurement covers a two-record
fixture. The implementation scans original collector journals and replays
portfolio history, so these figures do not estimate production cost.

To reproduce, use the [Stage 4C PostgreSQL 17 setup](stage-04c-paper-trading-persistence.md)
and its private scratch-directory instructions. Supply the explicit loopback
test DSN and disposable container identity for the restore tests. Use distinct
`--basetemp` directories for independent pytest invocations.

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -o tmp_path_retention_policy=none
uv run --locked pytest -qs tests/integration/test_paper_worker.py
uv run --locked --no-sync python -I -S -B tests/run_e5_guarded.py
uv run --locked --no-sync python -I -S -B tests/run_e5c_guarded.py
uv run --locked --no-sync python -I -S -B tests/run_e5d_guarded.py
uv build --wheel
git diff --check
```

## Stage 4D.2 handoff

1. Benchmark full reconciliation under the portfolio lock on representative
   history. Measure forecast archive scan time, ledger and mark replay, peak
   memory, lock waits and simultaneous mark/order work on both markets.
2. Rehearse separate migration owner, inception, non-owner worker and read-only
   reporting roles. Verify exact grants on all five tables and guard functions.
3. Rehearse migration 0002 from an isolated copy of 0001. Exercise both an empty
   downgrade and forward recovery after funded evidence exists. Revision 0002
   requires inception in a scheduled slot's capture window. Off-slot inception
   cannot be represented by this schema. Resolve the activation procedure before
   scheduling an inception.
4. Extend the operational fingerprint and encrypted backup to all five paper
   tables. Restore into a fresh isolated database, compare original rows, guards,
   ledger prefixes, exit obligations, marks and simulated balances.
5. Preserve as one recoverable set the original forecast bytes, the exact journal
   snapshot used for classification, quote bytes, private filter sources, version
   pins and database references. A running Stage 3 journal can be atomically
   replaced by a later snapshot. A reference to a lost hash cannot authenticate
   the earlier snapshot. Rehearse the decision-commit/intent boundary with
   independently retained originals and explicit handling of conflicted identities.
6. Isolate the worker process, credentials, network destinations and file roots.
   Establish CPU, memory, runtime and storage limits from the rehearsal.
7. Monitor host UTC synchronisation, suspension, sampled clock reversals, source
   latency, quote/filter freshness, rate limits and missed journal publications.
   Local durations alone cannot establish external clock accuracy.
8. Exercise alerts for overdue horizons, mark gaps, unresolved exits, blocked
   dust, database integrity, interrupted attempts and unavailable source archives.
   Rehearse terminalisation and restore at actual discovery times.
9. Rehearse the five-minute cadence in isolated staging. Verify that overlapping
   invocations cannot spend twice and that marks pin the locked prefix. Keep all
   rehearsal portfolios and original evidence distinguishable from genuine cohorts.
10. Obtain owner approval for production roles, migration, backup coverage and
    deployment, then separate Stage 4D.3 approval for each genuine BTC/ETH
    portfolio, funding time and first mark. Public reporting has its own gate.

## Changed-file inventory

| Files | Purpose |
| --- | --- |
| `src/backtest_badger/paper_artifacts.py`, `paper_forward_adapter.py` | Safe local original-byte access, private content-addressed retention, Stage 3 provenance and exact forecast conversion |
| `src/backtest_badger/paper_clock.py`, `paper_market_data.py` | Invocation identity and clocks, bounded public transport, quote/filter interpretation and smoke diagnostics |
| `src/backtest_badger/paper_recovery.py`, `paper_worker.py` | Read-only Stage 4C reconstruction, single-cycle planning, marks and local module CLI |
| `src/backtest_badger/paper_fixture.py`, `paper_fixtures/records/` (two JSON files), `paper_fixtures/operations/` (two JSON files) | Packaged fabricated cases identified above |
| `tests/test_paper_forward_adapter.py`, `test_paper_market_data.py`, `test_paper_clock.py`, `test_paper_worker.py`, `tests/integration/test_paper_worker.py` | Original-format authentication, adversarial source handling, causal planning and disposable recovery |
| `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/development-handoff.md`, this report | Current capabilities, verification, remaining gates |
| `prompts/README.md`, `prompts/stage-04-paper/stage-04d1-prospective-integration.md` | Request index and verbatim brief |

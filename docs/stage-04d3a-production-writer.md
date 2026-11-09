# Stage 4D.3A — Prospective simulated writer

Stage 4D.3A ran on local disposable PostgreSQL 17 databases. Every price, forecast, starting balance and economic outcome in this rehearsal is fabricated. This stage installed no service and activated no prospective portfolio.

## Release identification

Work started on clean main at `12ad7c50a5a7f6354d931c16bd2469cfe02151b9`. Both exact-SHA workflows succeeded. [Starting CI](https://github.com/owencrew/backtest-badger/actions/runs/42500120908) · [Starting Frontend](https://github.com/owencrew/backtest-badger/actions/runs/42500120916)

The release commit is the commit that introduced this report, titled `feat(paper): implement prospective simulated writer`. Resolve its full SHA even after main advances with `git log -1 --diff-filter=A --format=%H -- docs/stage-04d3a-production-writer.md`. Match the SHA to both Actions runs before a deployment review. Stage 4A economics, migration bytes and the Stage 3 publication process retain their previous identities.

## Writer interface and process boundary

`Writer(conn, config, clock, health, acquire).run()` runs one portfolio cycle on a dedicated autocommit session. Configuration pins a UUID, symbol, strategy config hash, original records and journals, private archive, and private operational directory. Each invocation claims a new clock/run identity. The transport returns original response bytes with bracketed UTC and monotonic samples. Operational use calls the existing unsigned HTTPS GET adapter on `data-api.binance.vision` for symbol-specific exchangeInfo and bookTicker. The proposal CLI still defaults to its offline fabricated demonstration.

The separate local entry point is `python -m backtest_badger.paper_writer_cli staging-once --config /absolute/private/config.json`. It requires an owner-only regular JSON file with exactly the following fields.

| Field | Required value |
| --- | --- |
| `mode` | `staging-once` |
| `dsn` | Explicit host, port, database, user and password for a loopback `badger_test_<32 hex>` database. Use the restricted worker login. The program rejects libpq environment overrides. |
| `portfolio_id`, `symbol`, `config_sha256` | Existing fabricated cohort UUID, BTCUSDT or ETHUSDT, and its canonical configuration hash. |
| `records`, `journals` | Separate absolute Stage 3 read-only roots. |
| `archive`, `runtime` | Separate owner-only directories outside the checkout and release. Both market workers share the provider runtime directory. |
| `clock_observation` | Absolute path to an external root-owned measurement. All ancestors must be root-owned and protected from group/other writes. The non-root worker reads UTC `sampled_at`, Boolean `synchronised` and numeric `uncertainty_ms`. |

The writer samples current UTC, checks wall/monotonic agreement and requires a synchronisation observation at most five minutes old with uncertainty at most 100 ms. A local monotonic clock alone cannot establish UTC accuracy. Tests injected fabricated clock observations. Production needs a separately reviewed synchronisation observer and a known relationship between the database and worker clocks.

The CLI emits JSON with run and order identities, result, reason, timings and incidents. Exit 0 means the cycle ran to an operational outcome, including ordinary missingness or a terminal rejected order. Exit 1 covers stopped, invalid configuration or integrity outcomes. Exit 2 reports controlled interruption. SIGTERM and the 240-second watchdog unwind transactions and release session locks. The provider gate serialises both markets' public requests and retains cooldown across processes. HTTP 418/429 sets the longer of five minutes and a numeric Retry-After. The operating system and trusted administrators control the private directories.

## From original forecast to settlement

1. Take the session advisory lock for the authorised portfolio. Recover and independently audit all financial rows, holdings, intent bindings, archived forecast/journal bytes, market evidence and pinned policies in one repeatable-read snapshot. Verify the configured market and canonical config. An integrity incident halts that portfolio and retains its incident identity in the private runtime directory.
2. From the durable horizon cursor, use the Stage 4D.1 reader and planner to authenticate each original record, publication identity, Ridge recipe, value and automation claim. Record discovery and decision at actual UTC. Archive exact bytes and admit through `record_archived_decision`. Recheck the live deadline after archival and database locking. Catch-up commits one horizon at a time. A pending risk exit can take priority over scanning more overdue horizons.
3. Apply the frozen Ridge Sign v1 threshold of `1e-12`. A timely positive signal buys only when flat. When long it holds. A timely nonpositive signal while long creates a sticky sell obligation. While flat it records a cash decision. One miss preserves exposure, two consecutive misses create a risk exit when exposed. A later positive signal cannot clear it.
4. Retrieve and validate effective market filters, publish the original bytes and their per-run reference, and reopen the binding. The writer samples actual submission time under the portfolio lock and rechecks filter and entry eligibility. Stage 4C checks exact balances, high-water sequence, prior attempts and the required obligation. Commit the unique SUBMITTED order, expiring in 30 seconds.
5. Begin a fresh bookTicker request only after the submission commit returns. Check source URL, market, payload hash, exact prices and displayed sizes, process identity, request chronology and the two-second RTT limit. Retain the bytes privately and commit QUOTE_OBSERVED. A failed response can retain the original envelope and bytes even when it cannot qualify as a quote.
6. Lock portfolio and order, check ACTIVE, SUBMITTED, current run and ledger sequence, and reread the exact order and observed quote. Sample actual use time and call the existing simulation. A buy pays ask × 1.0002, a sale receives bid × 0.9998, and the 10 bps per-side fee rounds upward to 1e-8 USDT. The approved size, depth, notional, cash and filter-age checks apply to the entire quantity. Simulated fills convey no guarantee of Binance execution.
7. A single transaction writes FILL, the paired USDT/base movements, the new ledger high-water, FILLED status, and EXIT_SATISFIED on liquidation. Execute the Stage 4C deferred constraints before final admission. PostgreSQL checks the tightest eligible deadline and commits in the same protocol message. A late guard aborts all provisional changes. A separate terminal transaction records rejection or expiry at discovery. The worker independently audits the resulting portfolio before reporting success.

### Perishable quotation timing

The critical path reads the current order, its decision, the quote and the portfolio row. Full source discovery, archived forecast replay and portfolio-wide independent reconciliation are outside that path. Commit-time validation still checks the authoritative ledger prefix in PostgreSQL.

The backend samples its own clock after the deferred guards. The client then measures the remaining UTC and monotonic lifetime. It anchors that remaining interval to the earlier server sample, conservatively charging the return trip to the budget. One SQL message samples the backend again, checks the deadline, and commits. A stale admission aborts the message before COMMIT. The same mechanism guards scheduled marks. The client separately reports exact monotonic receipt-to-simulation and receipt-to-commit-acknowledgement intervals. The reported backend admission interval is a conservative upper bound across the two clocks. An acknowledgement can arrive after an already admitted commit. Recovery reads the durable identity after a disconnect.

## Recovery and missingness

| Boundary or failure | Durable effect and next cycle |
| --- | --- |
| Crash before decision or while archiving | No dependent intent or trade. Private unreferenced objects can remain. Recheck actual eligibility. |
| Decision committed, intent absent | Recover the immutable decision. A resumed buy requires reauthentication and an open entry window. |
| Intent committed, no response | Terminalise at discovery. Before expiry record rejection, after expiry record EXPIRED. |
| Response received, publication interrupted | Only committed observations are recoverable. A new process never fills using an interrupted process's response. |
| QUOTE_OBSERVED committed, then interrupted | Preserve the observation and terminalise the unfilled attempt. |
| Crash during provisional postings or mark | PostgreSQL rolls back the transaction. The ledger prefix and earlier marks survive. |
| Lost commit acknowledgement | Reconcile the existing FILL and its exact two postings before scheduling another action. Deterministic order keys and unique quote/fill identities prevent reposting. |
| Failed buy | The consumed forecast cannot initiate another buy. |
| Failed or expired sell | Retain the original obligation. Allow one distinct attempt per eligible cycle, at least five minutes after the previous actual submission. A different timely forecast issued after successful liquidation is required for re-entry. |
| Blocked dust | Retain the position and obligation with original filter and quote evidence. Revision 0002 marks the portfolio paused. |
| Overlap or database timeout | Emit an operational warning. A still-submitted order is recovered on the next run. |
| Corrupt/missing required original or invalid account | Stop economic processing. Preserve the database, archive and per-portfolio halt record for investigation. |
| Provider failure or throttle | Record available failure evidence. Respect the shared cooldown. Preserve cash and base quantity. |
| Missing slot | Record MARK_MISSING after the five-minute capture window, at the actual check time. No retrospective price substitution. |

Valuations use UTC slots at 00:10, 04:10, 08:10, 12:10, 16:10 and 20:10. An observed mark requests its own quote and pins the original bid, quote identity, policy and exact locked ledger prefix. An intervening posting newer than the quote makes that mark unavailable. A failed observation inside the window leaves the slot open until the window closes. The mark/settlement race in the writer suite committed the mark at sequence 1 and the fill at sequence 3. Independent replay reproduced the mark after the fill.

Diagnostics reuse the Stage 4D.2 severity classes. Missing horizons and marks carry the actual discovery time. Provider throttling, contention, overlap, interrupted runs, expiry and repeated rejections produce operational warnings. Original conflicts, reconciliation failures, blocked dust and failed backup or restore are integrity incidents. Keys derive from the category, portfolio and affected horizon, order or obligation. A private log processor can aggregate the same key across invocations. Backup and restore incidents belong to the checkpoint monitor. Investigate a portfolio halt against its last good checkpoint before clearing it.

## Fabricated lifecycle and backup

Both markets began in separate restricted-role operator transactions with 10,000 simulated USDT and a valid inception mark. They entered, held, rejected a sell, preserved the obligation across a later positive forecast, liquidated on retry, stayed flat on a negative forecast, then re-entered on a new positive one. After two misses, the risk exit survived a rejection and subsequently liquidated. Both accounts finished flat at ledger sequence 9, each with eight mark slots including two explicitly missing.

The independent cluster restored two portfolios, 16 decisions, 14 orders, 48 events and 18 ledger rows. Each account had fabricated cash of 9,952.11520000 USDT, zero base units and realised P&L of −47.88480000 USDT. Those numbers are reproducibility checks on the synthetic price path. The restored worker role, archive objects, schema, ACLs, row fingerprints and historical prefixes were reverified. The Stage 4D.2 backup-failure and damaged-source drills still run independently. Keep the separate runtime incident/cooldown state with operational backups when moving hosts.

## Verification

### Local timing gate

PostgreSQL 17.11 ran in two disposable loopback clusters with separate temporary data volumes. The benchmark machine was an Apple M4 Pro with 14 logical CPUs and 24 GiB RAM, running arm64 macOS 26.5.2 and Python 3.12.13. The history generator, both worker sessions and timing observers used fabricated market data. All writer measurements used the restricted worker login.

| Scenario | Samples | Receipt to simulation use, ms | Receipt to backend admission upper bound, ms | Receipt to commit acknowledgement, ms | Whole cycle, s |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uncontended original forecast | 1 | 7.08 | 13.25 | 13.28 | 0.069 |
| 30-day histories, simultaneous BTC/ETH exit retries | 2 | 11.73–12.13 | 21.49–21.79 | 21.92–22.24 | 0.802 |
| One-year histories, simultaneous exit retries | 2 | 11.22–11.51 | 20.09–20.33 | 20.14–20.61 | 9.32–9.33 |
| Three new horizons after one year, simultaneous BTC/ETH | 6 | 10.75–13.77 | 19.05–23.17 | 19.06–24.46 | 20.65–22.34 |
| Competing observed valuation | 1 | 67.77 | 74.24 | 74.27 | 0.136 |
| Duplicate invocation, winning process | 1 | 6.97 | 12.98 | 13.01 | 0.074 |

The year contained 4,380 initial decisions and 105,120 collector journals before discovery of the three new horizons. In those six fresh-forecast cycles the scans took 11.11–12.59 s, combined initial and final independent audits took 8.62–8.82 s, order preparation took 426–456 ms and filter archival plus submission commit took 10–19 ms. Locked settlement took 1.90–2.55 ms to acquire and check the rows. Synthetic quote request/receipt sampling took 2.75–3.38 µs. The peak resident size for the shared benchmark process, including history generation, was 262.4 MiB. There were zero rejected quotes in the ten measured history cycles.

| Forced delay | Result at actual discovery |
| --- | --- |
| Held portfolio row lock | The lock phase took 1.054 s. At 1.062 s after quote receipt the writer rejected without postings. |
| Slow database response after provisional fill DML | At 1.069 s the writer rolled back the provisional fill and recorded a rejection. |
| Stall between final clock sample and commit dispatch | The backend guard rejected the transaction. Receipt to rejection was 1.070 s. |
| Row lock held beyond the three-second database timeout | The cycle stopped in 3.055 s with the intent still submitted. Restart expired it with the ledger at sequence 1. |
| Concurrent mark | The fill waited 56.1 ms in its lock phase. The mark retained sequence 1 after the fill advanced the account to 3. |
| Duplicate process | The active invocation completed one fill. The competing invocation reported the stable overlap incident and wrote no trade. |

All three deliberately stale quote cases rejected. The eleven process-kill cases inspected the actual committed state. On these short histories the first recovering cycle reconstructed state in 13.49–15.52 ms. The cycle following death immediately after fill commit took 30.9 ms and found the existing trade. At year end the initial audited recovery phase of the two sticky retries took 4.71–4.72 s.

These are observed ranges from a small warm local sample. Actual Binance HTTP latency, cold disk/WAL latency, production clock behaviour, filesystem access and competing Lightsail services still require on-host measurement. The one-second gate stays enabled under those conditions.

### Executed checks

| Check | Observed outcome |
| --- | --- |
| Full pytest suite with PG17 and private macOS scratch | 3,351 passed and 88 skipped in 21m 08s. The run included 3,080 passing non-integration tests. Three subsequent integration regressions covered the post-commit request, backlog progress and clock revocation. |
| Final complete PostgreSQL integration suite | 274 passed in 66.39 s, including restricted grants, original admission, corruption, expiry, concurrent settlement, backup and independent restore. |
| Paper-specific regression selection | 959 passed, including Stage 4B.1 arithmetic, Stage 4C transactions, Stage 4D.1 planner/authentication and Stage 4D.2 readiness. The narrower final CLI/writer selection also passed. These counts overlap the full suite. |
| Timed workload and controlled contention | 8 passed in 369.12 s. A separate timed repetition of all 11 process-death cases passed. |
| Isolated guarded historical runners E.5 / E.5c / E.5d | 87 / 55 / 153 passed. The full suite skips the 87 cases requiring the E.5 entry point and one opt-in genuine Study 001 replay. That replay remained skipped. |
| Scientific evidence | All 57 Study 002 freeze pins, four Study 001 result files and five Study 002 result files matched recorded sizes and SHA-256. Both Stage 4A protocol files and migration revisions matched the starting checkout. |
| Static and package verification | Repository Ruff lint and formatting, Git whitespace checks, offline wheel build, seven wheel-only imports and the packaged dry-run proposal passed. |

An early lifecycle assertion attempted the retry at the nominal five-minute tick. The recorded submission was slightly later, so the writer correctly returned EXIT_RETRY_WAIT. The test now advances beyond the actual boundary. A development run also mixed an older imported writer with an edited CLI. The final fresh-process integration suite exercised both together.

To reproduce, use the Stage 4D.2 two-cluster fixture, full Docker container IDs, explicit loopback test DSNs and private macOS scratch with separate pytest basetemps. Run the full root suite, the guarded runners and the explicitly named timing workload. The workload is opt-in. [Environment and runner setup](stage-04d2-production-readiness.md)

```sh
.venv/bin/pytest -o tmp_path_retention_policy=none
.venv/bin/pytest tests/integration
.venv/bin/pytest -s tests/integration/benchmark_paper_writer.py
.venv/bin/python -I -S -B tests/run_e5_guarded.py
.venv/bin/python -I -S -B tests/run_e5c_guarded.py
.venv/bin/python -I -S -B tests/run_e5d_guarded.py
```

## Release inventory

| Files | Change |
| --- | --- |
| `src/backtest_badger/paper_writer.py`, `paper_writer_cli.py`, `paper_admission.py` | Financial orchestration, explicit staging runtime, and deadline-guarded PostgreSQL admission. |
| `paper_worker.py`, `paper_recovery.py` | Share horizon, order and valuation scheduling logic and reconstruct planner state from the audited snapshot. |
| `paper_persistence.py`, `paper_reconciliation.py` | Share transaction settings, stored execution inputs, terminal events and atomic posting operations. |
| `paper_evidence.py`, `paper_market_data.py`, `paper_operations.py` | Archive admission under lock, reread original intent/quote evidence, retain rejected response envelopes and classify writer incidents. |
| `tests/test_paper_writer_cli.py`, `tests/integration/{paper_writer_harness,test_paper_writer,test_paper_readiness,benchmark_paper_writer}.py` | Reviewed CLI, fabricated transport, child-process failure injection, concurrent admission, backup/restore and long-history benchmark. |
| `README.md`, `docs/{architecture,roadmap,development-handoff,stage-04d3a-production-writer}.md`, `prompts/README.md`, `prompts/stage-04-paper/stage-04d3a-production-writer.md` | Current handoff, evidence, and verbatim archived stage request. |

## Separate Stage 4D.3B review

1. Obtain authority for host inspection. Record the actual Lightsail release SHA, service UIDs, timers, mounts, PostgreSQL version and Alembic revision. The dated October infrastructure snapshot is a comparison point. Establish which release and database are actually in use. [Production infrastructure](deployment/production-infrastructure.md)
2. Verify the release SHA, both exact-SHA workflows, wheel and frozen hashes. Rehearse the reviewed migration and role SQL on a restored copy. Establish an encrypted baseline backup, trusted receipt, independent restore, measured RPO/RTO and approved recovery owner. Test existing collector and scorer access.
3. Review a dedicated non-root paper identity, read-only Stage 3 roots, private archive and runtime directories, worker-only DB login and separate inception and reporting roles. Pin the public host, DNS/TLS/egress policy and clock observer. Exclude deployment, exchange, Cloudflare and backup credentials from the worker environment.
4. Measure cold-start memory, CPU, storage, archive growth and receipt-to-use/admission/acknowledgement on the inspected host with existing collection, scoring, backup and valuation load. Inspect clock agreement and file permissions. Verify monitoring for repeated incident keys, missing marks, ageing exits, worker silence, backup failure and failed restore. Establish storage and retention for private operational records.
5. Review the production entry point and systemd sandbox separately. Keep the five-minute oneshot disabled until the service configuration, kill switch and on-host rehearsal have been accepted. To stop execution, disable the paper timer and service, stop the worker, and revoke the runtime login and terminate its active sessions if needed. Preserve all rows, originals and halt records. Reconcile and checkpoint before separately approved forward recovery. [Migration and activation checklist](deployment/paper-migration-activation-checklist.md)
6. Obtain independent BTCUSDT and ETHUSDT inception approvals. At the approved slot verify the original first quote and filters, funding, opening mark and pinned release in one transaction. Document the actual start or the failed window. Public reporting is separately gated.

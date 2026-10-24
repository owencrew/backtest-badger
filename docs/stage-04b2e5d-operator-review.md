# Stage 4B.2E.5d — fixed-bootstrap / macOS rehearsal preparation

2026-10-24, Europe/London. **Preparation only; real OS rehearsal BLOCKED. No
installed executable bootstrap, genuine execution, original-input authority or
E.5e activation is provided.** The earlier implementation and initial blocker
records below remain historical records; their HEAD/test statements are not
claims about this continuation.

## Baseline and scope

Local `git rev-parse HEAD` returned
`48794dd2a32a7acf6561a7fd082f05cb66b52124`; the starting worktree was clean. The
owner reports GitHub Actions **40040696312** green for that commit: 2,967 ordinary
passes, E.5 **87/87**, E.5c **55/55**, E.5d **117/117**. These are the current
owner-supplied verified CI references, not a remote attestation performed here.
Historical verification remains commit
`94584dc4b08f06441cff3bcd7983bba1ca0afe8d`, run **39668530849**, green. Neither
original verification nor genuine 2024 economics was rerun. This uncommitted
continuation has no new CI run.

The substantive request is archived verbatim at
[`stage-04b2e5d-fixed-bootstrap-macos-rehearsal-preparation.md`](../prompts/stage-04-paper/stage-04b2e5d-fixed-bootstrap-macos-rehearsal-preparation.md).
There was one procedural deviation: a filename-only repository search and status
check ran before reading root `AGENTS.md`. It returned repository filenames,
including deployment filenames, but none of those deployment files was opened.
The exact root guidance was then read; subsequent source access was scoped.

## Review findings and direct fixes

| Boundary | Finding / disposition |
| --- | --- |
| Signature and intent | The execution domain signs canonical schema/key/payload, rejects verification domains and schemas, requires literal `fabricated_only=True`, one attempt, no resume, protected-review equality, and rejects original four-file identities before input I/O. Added tests use a valid ephemeral test signature AND matching review for each historical pin, so mismatch with the review cannot mask this lockout. |
| Consumption | A pre-enrolled installation/slot/eligibility record is required; `O_EXCL` consumption is file/directory synced before worker launch. Empty/partial consumption blocks reuse. No runtime enrolment, reset or retry path was added. |
| Retention / reporting | Supervisor derives replay and six ordered account fingerprints, retains replay/handoff before ACK, reconciles six report IDs and persists them before publication. It authenticates retained producer bytes, not economic truth independently of a malicious worker. |
| Completion | Evidence and integrity precede manifest; exact readback precedes protected completed receipt. Readback needs protected consumption/completion/report receipts and output hashes, performs no writes or replay, and never repairs partial output. |
| Worker FDs | **Fixed:** fd 2 previously inherited a supervisor capability despite `close_fds=True`. Worker stderr now goes to `/dev/null`; stdin/stdout are anonymous protocol pipes. A launch-options regression covers supplementary group removal, fixed environment and absence of extra passed FDs. OS observation is still required. |
| Runtime ancestry | **Fixed:** non-mocked closure checks now reject non-root/non-supervisor ownership and group/other-write permission on every ancestor, including the root. Symlinks remain rejected. This is a POSIX prerequisite, not an ACL/MAC or mount attestation. |
| Runtime exactness | **Fixed:** the existing closure verifier now rejects unlisted empty directories. Previously its file-only comparison silently accepted them. |
| Output schema | **Fixed:** exact typed boolean constants now lock TEST/authority flags, including nested publication/sign-off flags. Previously the recursive schema allowed either boolean, although report reconciliation already rejected top-level authority claims. Existing recursive literal/pattern/key restrictions reject private paths; no arbitrary path field was introduced. The allowlist has 135 definitions now. Its hash changes, so any fresh approval must bind the new bytes. |
| Genuine routes | Both public `run_genuine_historical_operator` and `replay_genuine_minute_historical` still refuse unconditionally, before argument inspection. No bootstrap, signing fixture, environment variable or command option activates either. |

The four inputs remain bounded, pinned and opened with no-follow descriptor walks;
preflight and pre-consumption rechecks precede replay. Frozen strategy, parser,
sign-off, monetary core and reporting are unchanged. Known genuine pins and
fabricated recipe markers are defense in depth, **not a permission system for
arbitrary paths**: the internal test callback API must never be exposed as a
privileged service accepting user paths. A future fixed installation must bind
its exact four newly fabricated input locations before any input open. Fabricated
markers alone do not establish provenance.

## Stop condition and fixed-bootstrap contract

There is no reviewed installed MAC/network/process policy for this Mac in the
available evidence. Local read-only host observations were **macOS 26.5.2 build
25F84, Darwin 25.5.0, arm64**, with **CPython 3.12.13**, build string
`main, Mar 3 2026, 12:39:30`, compiler
`Clang 21.0.0 (clang-2100.0.123.102)`. These are observations of this preparation
host, not a selected immutable runtime or attestation. No installed policy,
entitlements, accounts, service configuration or private directories were probed.

The local `/usr/share/man/man1/sandbox-exec.1` explicitly labels the command
**DEPRECATED** and directs developers to App Sandbox. The local
`/usr/share/man/man7/sandbox.7` describes inheritance and acquisition-time checks,
including the fact that previously opened descriptors remain usable. No sandbox
command was executed. A deprecated profile command, chmod, a separate PID, a
same-UID child, Python hooks or a worker-reported success flag cannot close this
review gate.

**Do not install or run the supervisor on the basis of this preparation.** A fixed
executable bootstrap is intentionally not implemented around an unproved policy.
There is no `--run`, `--install`, key/path override, mock-policy switch or success
marker that bypasses the blocker. The existing `_run_fabricated(launch=...)` and
test guard remain test harness seams only. The new preparation tool never calls
them, consumes a slot, reads an approval/input or starts a worker.

The separately reviewed bootstrap must satisfy all of the following before it
can replace that stop condition:

1. An administrator installs a reviewed, immutable runtime and minimal native
   entry executable beneath a fixed root-owned path, with every ancestor protected
   against worker replacement/rename and ACL grants, on a reviewed mount. The
   service definition is also protected. The user checkout and Homebrew/venv
   symlinks are not installation trust roots. Administrator compromise/rollback
   remains outside the stated threat model.
2. The service invokes one absolute executable/launcher with a fixed argument
   vector, sanitized environment, working directory `/`, no inherited private
   descriptors, no restart and no user-controlled Python startup/import hooks.
   OS policy must apply before loading Python or any untrusted worker code.
   Runtime code cannot self-certify the interpreter that already loaded it.
3. Literal reviewed source identities bind project commit plus successful CI,
   CPython executable/build/patch, machine/OS build, inventory bytes, fixed
   supervisor and worker launchers, output-schema bytes, and a protected review
   identity. This binding is installed independently of the worker and approval
   transport. Do not accept an arbitrary caller-supplied expected hash as authority.
4. At a fixed protected review location, load only a fresh fabricated review and
   ephemeral rehearsal **public** key bound by the administrator's review. Reject
   all other input roots, known genuine pins and genuine schemas before I/O.
   Fixed code selects the command, principal IDs, four fabricated inputs, schema,
   inventory and review; CLI/env/worker fields cannot select them. The separately
   approved operator creates/signs the synthetic intent outside the worker. No
   real owner private key or original input is needed for this rehearsal.
5. Exact protected contents and metadata must be rechecked before consumption;
   OS protection must bridge the last check to launch. A second snapshot alone
   does not remove the race. Only then can the unchanged one-shot state machine
   run with real principals and a fixed transport, without a callback exposed to
   users. Any uncertain consumption is terminal and quarantined.

In that **proposed** installation, denying the worker write/delete/rename rights
on the service, launcher, runtime, protected review and every ancestor prevents
it substituting the bootstrap or its expectations; MAC and descriptor/process
isolation must prevent alternate routes. This is a conditional argument, **not
an enforced fact on this host**. Real negative probes are the remaining evidence.

## Read-only preparation tool and exact inventory

`ops/e5d_rehearsal_preflight.py` uses only the standard library. Default invocation
prints the blocked plan and exits **2**, without installation/path reads or
process launch. `--preflight` is a separate manual action after installation
approval; it only examines the fixed fabricated staging location:

`/Library/Application Support/BacktestBadger/E5dRehearsal/v1`

It accepts no path, environment, worker command, approval or key override. The
root-controlled expected snapshot is always `review/runtime-snapshot.json`, and
the observed tree is always `runtime/`. It never scans original evidence, home,
credentials or the repository. Only deliberately staged runtime code/config may
be placed there. Its forbidden-name checks are additional guards, not a substitute
for the administrator's exact staging review.

The reusable `snapshot_tree` utility streams SHA-256 of every regular file and
records the exact directory set, owner/group, mode and BSD flags. Empty package
files/directories are represented explicitly. It rejects symlinks (including
ancestors), hardlinked/nonregular files, unknown/writable ancestors, unexpected
private names, within-read replacement/change and directory-set changes. Bounds
are 50,000 entries, 512 MiB/file and 4 GiB total. These are preparation bounds,
not genuine runtime limits. Snapshot ordering is deterministic; inode/timestamps
are used for within-read stability, not retained as reproducible content identity.

Preflight compares the complete snapshot to the fixed canonical reviewed file,
requires all seven role directories, and compares a second observation. Missing,
extra or changed bytes/metadata refuse. It can report actual UID/EUID/GID/groups,
PID/parent, import paths and loaded Python file paths, plus `ls -lde` observations
of the installation ancestors. ACL text is **not interpreted as proof**; internal
runtime ACLs and process/native images still require separate review. Even a
matching snapshot returns **BLOCKED / exit 2**, never installation success.

The installer/reviewer must stage and pin actual content for these roles:

| Role | Required actual content / independent binding |
| --- | --- |
| `python/` | Real CPython 3.12 executable and libpython, exact patch/build/compiler, executable hash, architecture; no venv interpreter symlink shortcut. |
| `stdlib/` | Full selected stdlib including encodings/import machinery, lib-dynload and any zip payload. Disable uncontrolled user/site startup hooks. |
| `packages/` | Actual wheel-installed package bytes and dist-info/RECORD; reject editable installs and unreviewed `.pth`/startup hooks. RECORD/version lists alone do not attest contents. |
| `native/` | Non-system extensions and transitive shared libraries; observe real loaded-image paths after imports and full fabricated work, not merely names from a self-reported list. |
| `project/` | Exact transitive source closure of the frozen replay/reporter and supervisor; no original data, private configuration or evidence directories. |
| `launcher/` | Fixed native policy launcher and fixed Python entry sources, reviewed together with service definition and public trust roots. |
| `config/` | Exact lockfile, project configuration, output schema and non-secret installed configuration. |

External trust roots include macOS kernel/build and architecture, boot/security
configuration, mounts/APFS, dyld and its shared cache, code-signing/entitlement
policy, launchd service/environment, ACL semantics, system libraries and their
loaded images, clock, and administrator-controlled installation. They are not
covered by a hash of copied runtime files. CPython version, inventory roles,
stdlib/package filenames and loaded modules printed by the running interpreter
are observations, not trusted host attestation. No complete installed runtime was
inventoried here.

**Integration gap:** this richer snapshot is intentionally not accepted as an
execution approval's existing `closure` object. That older format requires
positive-size files, omits empty directories, uses bounded 1 MiB canonical JSON,
and does not bind executing-host identities. Converting it by dropping empty
files/directories or collapsing trust roots would be unsafe. A reviewed format
and bootstrap integration (with real runtime size measurements) remain necessary;
this preparation does not declare closure complete because role names match.

## Separately approved real-principal rehearsal

The owner must first authorise a disposable installation and the specific probe
plan. A macOS security reviewer must select and validate a supported policy. An
App Sandbox native launcher/bundle with reviewed entitlements is a candidate
suggested by the local manual; compatibility with this Python/native runtime,
network denial, process/debug restrictions and policy inheritance is **unverified**.
It is not a drop-in wrapper implemented here. Do not fall back to sandbox-exec.
If the supported Mac policy cannot meet every boundary, stop. A safer alternative
for separate review is a disposable worker VM with no network device, no host
shared directories/clipboard/credentials, immutable runtime disk, and only a
bounded serial-style IPC channel to independently protected custody. Its exact
hypervisor, host-custodian boundary and guest MAC/process controls also need review;
a VM product name alone is not approval.

| Actor | Manual responsibility after separate owner approval |
| --- | --- |
| Owner | Approve exact disposable host, threat model, policy, runtime/public-key identities, fabricated inputs, resource envelope and fresh attempt; no genuine pins. |
| Administrator | Create dedicated non-login worker UID/GID (no admin/supplementary groups); install protected fixed runtime/service/review and separate private custody/publication roots; remove inherited capabilities; configure policy/watchdog with no restart. No such action occurred here. |
| Independent reviewer/operator | Review byte inventories, ancestors/ACLs/mounts and policy; generate a fresh ephemeral TEST approval outside worker control; exclusively pre-enrol installation/attempt with durable history; independently retain identities and observations. Never reconstruct spent/missing history. |
| Worker principal, observed by administrator | Run the specific negative probes below against disposable fabricated sentinels only. Record numeric identity, all results/errno, before/after hashes, process/FD/network observations. Any unexpected success stops the rehearsal. |
| Operator | Only after every denial passes, run one fixed fabricated supervisor publication. Check durable ordering and read-only completion; retain logs outside worker control. Each fault scenario needs a new reviewed attempt. |

No attack probe is bundled as an executable automatic script. The print-only
preparation tool deliberately cannot perform destructive probes. A separately
reviewed probe harness must record the following actual results; **none has been
executed in this continuation**:

| Probe target / operation | Required denial or observation |
| --- | --- |
| Fabricated private-original stand-ins, source tree and custody | As real worker UID: traverse, read-open, write-open, truncate, rename, unlink, replace and hardlink fail; test each ancestor as well as leaves. Use harmless sentinels, never real original directories. Include fabricated outside-root source paths. |
| Fixed bootstrap/runtime/review/service and prior receipts | Write/chmod/ACL alteration/rename/unlink/link or parent replacement fail; hashes and ACLs unchanged. Runtime read/execute is allowed only as required by the selected policy. Retained receipts must not become worker-owned. |
| Supervisor process | Signal probes (including permission-only signal 0, then approved termination probes on a sacrificial supervisor), debugger/task-port attachment and process-memory access fail. Different UID is only one prerequisite; validate privileged-helper/debug entitlement routes. |
| Network | Raw IPv4/IPv6, TCP/UDP, loopback, DNS and relevant local socket/IPC routes are denied by the chosen policy. Use administrator-controlled disposable endpoints after approval, never external services. A connection error without policy evidence is not proof of denial. |
| Inherited FDs | Supervisor starts with a fabricated private sentinel open; administrator observes worker FD types/targets and demonstrates no private descriptor is accessible. Only protocol stdin/stdout and `/dev/null` stderr are allowed. Include child-process inheritance. |
| Process context / imports | Record real/effective IDs, groups, parent/session, flags, ACLs and parent directories, actual Python import origins and loaded native images throughout the run. Snapshot and policy evidence are retained independently of worker reports. |

Record the same tests on an explicitly disposable same-UID control to show why
ordinary fixtures cannot prove independent custody. Do not weaken a prohibition
because the real worker cannot reproduce a same-UID test helper.

## Resources, interruption and retention envelope

Keep the earlier measured baseline below: parent lifetime peak **992,854,016 B**,
child peak **716,652,544 B**, publication **60,157,542 B**, slot **53,890,719 B**.
These are independent lifetime high-water observations with test overhead; their
sum is not a simultaneous RSS measurement. Current test ceilings remain **128
MiB/frame, 256 MiB publication, 600 s IPC**. They are not genuine limits.

For the first separately approved sparse fabricated OS measurement, plan **one
attempt at a time**, at least **4 GiB available memory**, **2 GiB free disposable
output/custody space beyond the installed runtime**, and **two CPU cores**. Keep
BLAS/OMP at one thread. Reserve additional space for all retained interrupted
attempts and administrator logs; never rely on cleanup of prior receipts or
original publications. These are provisional scheduling/headroom recommendations,
not enforced budgets or evidence of worst-case sufficiency. Measure concurrent
supervisor+worker memory, actual per-stage CPU/wall/disk, native thread counts,
higher-turnover fabricated cases and resource-denial behavior before selecting
hard limits. A provisional outside-supervisor **900 s wall watchdog** may be
reviewed for that first run; timeout must terminate the entire worker process
tree, quarantine the consumed attempt and never restart it. The current Python
transport's direct-child kill is not such an OS process-tree watchdog.

Fresh-attempt scenario matrix: (1) concurrent launch into one enrolled slot, one
winner; (2) worker and supervisor death before/after consumption-file creation,
file sync and directory sync; (3) lost retention ACK before/after six-account
receipt; (4) crash at each replay/report/output write and sync; (5) injected fsync
failure and real disposable-volume exhaustion; (6) partial manifest and missing
completed receipt; (7) completed readback after process restart, with execution
still refused; (8) planned OS reboot at reviewed durable boundaries and readback
only afterwards. Keep every resulting receipt/output in place. No retry or slot
repair after uncertainty, even if an unsynced entry vanishes. Real reboot/storage
observations do not establish universal power-loss guarantees; mocked exceptions
establish ordering/refusal only. Physical power-loss tests require separate scope.

## This continuation's validation and file inventory

Current local commands/results (all fabricated, offline; CPython 3.12.13):

| Executed command/check | Result |
| --- | --- |
| `python3.12 -I -S -B tests/run_e5d_guarded.py` | **153 passed**, zero skips, **711.48 s**; confirmed from the owner-supplied completed local log after Codex usage ended. |
| `python3.12 -I -S -B tests/run_e5d_guarded.py --preparation` | **27 passed**, zero skips, **0.15 s** final rerun (initial run: 27 passed in 0.18 s). |
| `python3.12 -I -S -B tests/run_e5_guarded.py` | **87 passed**, zero skips, **34.207 s**. |
| `python3.12 -I -S -B tests/run_e5c_guarded.py` | **55 passed**, zero skips, **128.71 s**. |
| `python3.12 -I -S -B ops/e5d_rehearsal_preflight.py` | Printed **BLOCKED**, exit **2**, as designed; no installed-tree preflight or probe executed. |
| Scoped Ruff check / format check | **Passed**, all six changed/new Python files; 6 already formatted. An initial lint run found one long string, corrected before the passing checks. |
| Preservation, schema and archive checks | **Passed:** 45 exact frozen source/config/test paths unchanged; earlier review preserved as byte-exact suffix; archived request byte-exact; all 135 schema definitions/references resolve. |
| `git diff --check` | **Passed**. |

Lint uses the existing installed `.venv/bin/ruff` with `--isolated --no-cache
--no-respect-gitignore --select E,F,I,UP,B --target-version py312`; format check
uses the same isolation flags and target. Exact file arguments were the custody
and operator modules, the E.5d guard and operator tests, the new preparation test
module, and the preparation utility. No package installation, full ordinary/DB
suite, historical verification or remote CI was run. The required CI gate must
still run on a future reviewed commit.

The successful complete-supervisor case within the current E.5d run observed
29.814 s supervisor wall, 1,046,855,680 B parent lifetime peak, 680,591,360 B child
peak and 37.255 s combined child CPU (both workers). Publication/slot sizes remain
60,157,542 / 53,890,719 B. Its fixture worker took 24.921 s. These include test
harness overhead and overlap with other fabricated regression commands; they
are not isolated worst-case or simultaneous-memory measurements. The earlier
baseline numbers remain preserved above/below.

Changed/new files relative to `48794dd2a32a7acf6561a7fd082f05cb66b52124`:

- `src/backtest_badger/genuine_backtest_custody.py` — ancestor prerequisites and empty-directory rejection.
- `src/backtest_badger/genuine_backtest_operator.py` — exact schema constants and closed stderr.
- `src/backtest_badger/genuine_backtest_output_schema.json` — TEST boolean constants.
- `ops/e5d_rehearsal_preflight.py` — new blocked, read-only preparation/inventory utility.
- `tests/test_genuine_backtest_operator.py` — nine additional signature/schema cases.
- `tests/test_e5d_rehearsal_preparation.py` — 27 new nonprivileged preparation cases.
- `tests/run_e5d_guarded.py` — exact source allowlist extended by two files, mandatory **153** cases (126 custody + 27 preparation); `--preparation` focuses the 27 cases and is not the CI command. Skips, incomplete collection and failed calls fail the gate.
- `.github/workflows/ci.yml` — E.5d label updated to 153; same required no-argument command. E.5 87 and E.5c 55 gates unchanged.
- `docs/stage-04b2e5d-operator-review.md` — this continuation prepended; history preserved.
- `prompts/stage-04-paper/stage-04b2e5d-fixed-bootstrap-macos-rehearsal-preparation.md` — verbatim request archive.

Source access: exact files named by the request, root AGENTS, pyproject,
`tests/run_e5c_guarded.py`, `tests/run_e5_guarded.py`, and direct signature,
fabricated integration and public-replay dependencies. Guarded tests import the
33 exact source modules and seven test/helper modules declared in
`run_e5c_guarded.py`, plus the E.5d source/test/schema files and this preparation
utility. No repository discovery is allowed inside those guards. OS-only reads
were kernel/version facts and the two named local manual files. No original
evidence contents, credentials/private signing keys, deployment config, production, remote
systems or sibling repository was read. No account creation, sudo, OS install,
service/ACL change, network, migrations, live signing, commit or push occurred.
Only ephemeral in-memory fabricated test keys were generated.

---

## Preserved earlier E.5d implementation and initial blocker records

# Stage 4B.2E.5d — fabricated custody implementation review

Updated 2026-10-24, Europe/London. **Fabricated implementation only. Genuine
execution remains closed; E.5e is not ready for authorisation.** The initial
custody-blocker report is preserved verbatim below as the historical review
record. Its statements that no implementation/tests exist describe that earlier
checkpoint, not the current working tree.

Both continuations first read the exact root `AGENTS.md`. HEAD remains
`09af01225d752cc3b02c08752e42587c353710f8`. Existing uncommitted documents, the
inert owner-payload draft and the five E.5c status lines were preserved. No reset,
revert, commit, push, deployment, account creation, privilege installation, sudo,
original evidence access or genuine historical calculation was performed.

## What is implemented

The owner approved a separately controlled local supervisor and unprivileged
worker for **fabricated implementation/testing**, with the trusted administrator,
administrative rollback and physical compromise outside the threat model.

- `genuine_backtest_custody.py` provides an execution-specific Ed25519 signature
  domain, exact fabricated intent validation, enrolled-public-key default,
  protected-review comparison, descriptor-relative no-follow reads, runtime
  inventory checking, exclusive durable writes and pre-enrolled attempt consumption.
- `genuine_backtest_operator.py` coordinates preflight, consumption, worker pipes,
  independent receipt derivation within the supervisor, retention before ACK,
  report reconciliation, private publication and protected completion readback.
  The worker calls the unchanged E.5c adapter, E.3 parser/sign-off validator,
  frozen replay, account verifier and native-minute reporter. It does not own
  custody or publication. There is no second monetary or strategy engine.
- `genuine_backtest_output_schema.json` is a static recursive **fabricated-report**
  allowlist, established from the invented full-year available-account fixture.
  It has 133 shared definitions covering exact object key sets, builtin types,
  enumerated labels and constrained identity/decimal/time strings. Its byte
  identity is bound in the fabricated approval before calculation. Arbitrary
  source metadata and private paths are rejected. This is deliberately narrower
  than a reviewed genuine exporter; unsupported variants fail closed.
- `test_genuine_backtest_operator.py` exercises real frozen full-year calculations
  in a separate subprocess and the complete supervisor path, plus focused fault,
  concurrency, state, privacy, transport and readback cases. Repeated durable-point
  tests reuse previously generated fabricated worker bytes to test the supervisor
  state machine without inventing another engine.
- `run_e5d_guarded.py` denies original/private paths and network operations, limits
  repository reads to exact files, and permits only disposable fabricated scratch
  writes and the exact worker subprocess. No-argument CI requires exactly 117
  passed test calls and zero skips. `--measure` selects the one complete supervisor
  test for resource measurement; it does not change the mandatory CI mode.
- CI adds a separate required E.5d step. The original 87- and 55-case steps remain
  unchanged. No remote CI was queried or run for this uncommitted working tree.

## Authority, order and completion semantics

The accepted execution-test schema is
`stage-04b2e5d-fabricated-supervisor-intent-v1`, in envelope
`stage-04b2e5d-one-shot-owner-signature-v1`, signed over canonical
`{schema,key_id,payload}` under
`BACKTEST_BADGER_ONE_SHOT_HISTORICAL_EXECUTION_V1\n`. Historical verification
signatures and schemas are rejected. The existing enrolled owner **public** key
is reused as the default verification anchor; synthetic tests use newly generated
in-memory test keys. No private signing material is read. There is no key
substitution path that enables genuine execution.

The exact fabricated payload binds the four absolute paths and byte identities,
method/protocol and six independent accounts, commit/successful CI claims,
closure inventory identity, attempt ID/window, supervisor/worker UID declarations,
installation identity/store, output directory, recursive schema identity and test
frame/output/wall limits. Canonical equality with the separately supplied protected
review rejects stale commit/CI/closure approvals. CI claims are internally checked
owner/test declarations, not independently observed GitHub attestations.

1. Validate signature, exact protected review, clock, closure and output schema.
   Read the four pinned bounded regular files through no-follow directory/file
   descriptors. Reject hardlinks, aliases, symlinks (including ancestors), oversized
   or changing descriptors. Parse/reconcile with the unchanged E.3 code. Require
   explicit fabricated recipe markers before consumption. Preflight does not run
   replay or economics.
2. Check the fresh output parent and source/custody/runtime disjointness. Recheck
   four inputs/metadata, closure and finally the clock. Open only a previously
   enrolled slot named `<approval-sha256>-<attempt-id>` in the protected store.
   Missing installation, slot or eligibility history is a refusal, never automatic
   creation of an unspent approval.
3. Create `consumed.json` with `O_EXCL`, write completely, fsync the file (plus
   macOS `F_FULLFSYNC` where provided), then fsync its directory. Only after those
   operations return does the supervisor start the worker. Even an empty or partial
   consumed file blocks another attempt. There is no reset/retry/resume operation.
4. Send only the four pinned byte sequences over anonymous framed pipes. Receive
   the complete canonical replay. The supervisor derives the whole replay hash and
   six ordered native-reporter-compatible account fingerprints itself; worker-supplied
   expected pins are not accepted. Persist `replay.json` and `handoff.json`, bound
   to approval, attempt, method, closure, schema and signer, **before** sending ACK.
   The worker waits for this ACK before invoking reporting.
5. Reconcile the report's evidence byte-for-byte with retained replay and each
   report/account association with retained pins, enforce the recursive allowlist,
   check report identities and account boundaries, and require successful worker
   exit. Re-read the four inputs, rejecting changes, and retain `inputs-after.json`.
   Persist all six report IDs and the complete report's hash/length in `reports.json`
   before output publication. Custody authenticates retained producer evidence;
   it does not independently recalculate strategy results or prove a malicious
   producer economically truthful.
6. Exclusively write private `evidence.json`, `integrity.json`, then
   `manifest.json`, syncing each file and directory. Exact readback must succeed
   before `completed.json` is written in protected custody. The manifest's
   `complete=true` means files were assembled; it is **not** standalone confirmation
   of completion. `_read_completed_fabricated` additionally requires the protected
   consumption/completion/report receipts and all exact output hashes. It never
   repairs, promotes partial evidence, calculates or writes anything.

A lost ACK, child failure, storage failure, timeout or incomplete output leaves
whatever was written in place. Consumed attempts remain terminal even when a
caller did not receive a success response. A later valid readback can confirm
already completed bytes; it cannot resume computation. After an uncertain
reservation acknowledgement, do not automatically relaunch even if crash recovery
loses an unsynced directory entry: quarantine the installation/attempt for review.
Before successful consumption fsync there has been no calculation. Process-death
and injected fsync errors establish ordering and local refusal, **not power-loss
persistence or administrative rollback resistance**.

## Validation record

All final fabricated validation passed; no test pass is a macOS isolation or
genuine-execution authorisation. Python was **3.12.13**, installed Ruff **0.17.0**.

| Executed command/check | Actual result |
| --- | --- |
| `python3.12 -I -S -B tests/run_e5d_guarded.py` | **117 passed**, zero skipped, **708.24 s** |
| `python3.12 -I -S -B tests/run_e5_guarded.py` | **87 passed**, zero skipped, **35.793 s** |
| `python3.12 -I -S -B tests/run_e5c_guarded.py` | **55 passed**, zero skipped, **131.23 s** |
| `python3.12 -I -S -B tests/run_e5c_guarded.py --regressions` | Earlier saved run inspected: **603 passed**, zero skipped, **564.95 s**; covered code remains unchanged |
| `python3.12 -I -S -B tests/run_e5d_guarded.py --measure` | **1 passed**, zero skipped, **63.40 s**; final full-supervisor measurement and durable-before-launch assertion |
| Scoped installed Ruff 0.17.0 lint | **Passed**, all four new Python files |
| Scoped installed Ruff 0.17.0 format check | **Passed**, all four files formatted |
| Baseline preservation and JSON checks | **Passed**, 50 exact existing tracked paths unchanged; schema references and inert draft checked |
| Tracked diff and added-file whitespace | **Passed** |

The measurement command followed the final telemetry/barrier assertion additions;
the mandatory 117-case count and behaviour were retained. The pre-existing broad
603-case suite was not needlessly rerun after changes confined to the new modules,
tests, CI and immediate documentation. No regression result is a fresh original
historical verification.

Lint used `.venv/bin/ruff check --isolated --no-cache --no-respect-gitignore
--select E,F,I,UP,B --target-version py312`; format used `.venv/bin/ruff format
--check --isolated --no-cache --no-respect-gitignore --target-version py312`.
Both received exactly `src/backtest_badger/genuine_backtest_custody.py`,
`src/backtest_badger/genuine_backtest_operator.py`, `tests/run_e5d_guarded.py`,
and `tests/test_genuine_backtest_operator.py`. Initial development-harness failures
were corrected before the successful final runs; they were not counted as passes.

The pre-continuation logs were inspected: the initial 92-case E.5d suite passed in
535.89 seconds, E.5 passed 87/87 in 35.786 seconds, and E.5c `--regressions` passed
603/603 in 564.95 seconds, including all 55 mandatory E.5c cases. These remain
actual earlier runs; the final focused run below covers the subsequent schema,
readback and fault-test additions. The 603 unchanged regression cases cover
publication/sign-off, private replay, native-minute reporting and minute-accounting.
No complete repository/DB integration suite was run locally.

The new cases include approval/domain/key/schema/window failures; changed method,
commit/CI/closure; all four input reads; missing/altered/symlink/hardlink/FIFO inputs;
runtime missing/extra/changed/writable files; lost/damaged/mispermissioned custody;
16 concurrent attempts with exactly one winner; process death at four consumption
points; all 40 downstream durable/ACK/readback fault points; partial/zero writes,
file/directory sync failure; worker launch/EOF/exit/lost-ACK failures; changed inputs
during the worker; incomplete/oversized frames and worker timeout; nested privacy
and type rejection; completion receipt/output tampering; consumed-attempt refusal;
and both old/new public genuine gates rejecting before argument inspection.

## Resource observations and limits

The focused `python3.12 -I -S -B tests/run_e5d_guarded.py --measure` run passed
1/1 in **63.40 seconds**, with the exact final complete supervisor test and its
real subprocesses. It explicitly observed the consumption-directory sync event
before worker launch. Actual measured values:

| Measurement | Observed value |
| --- | ---: |
| Supervisor call wall time (includes input/closure checks, worker, retention, output/readback) | 30.639 s |
| Supervisor process lifetime peak RSS | 992,854,016 bytes |
| Maximum child process lifetime peak RSS | 716,652,544 bytes |
| Combined CPU of both fabricated child runs used by the test | 38.994 s |
| Complete three-file publication | 60,157,542 bytes |
| Protected slot contents including replay and receipts | 53,890,719 bytes |
| Pipe-worker fixture exchange wall time in this measurement run | 26.132 s |

The parent retains an earlier fixture's replay/report bytes during the supervised
run; its peak includes test harness overhead. Child peaks are maxima, not a
simultaneous combined-memory measurement. Summing parent/child high-water values
would not measure actual concurrent RSS. These measurements support further
budget/rehearsal review, not a genuine resource-limit approval.

The initial pipe-worker run measured 14,812,916 input bytes, 53,884,354 replay bytes
and 60,154,355 report bytes; one observed worker lifetime peak RSS was 676,102,144
bytes and elapsed wall time 25.117 seconds. A subsequent guarded run observed
719,536,128 child peak RSS and 24.245 seconds. These are invented full-year fixtures,
not observations of original evidence or worst-case trading turnover. The worker
measurement includes exchange, supervisor hashing/schema validation and scheduling.
CPU/RSS observations are process lifetime high-water measurements, not per-stage
allocation accounting. Some regression jobs ran concurrently, so elapsed times
are not isolated performance guarantees.

Current test-only ceilings are 128 MiB/frame, 256 MiB total output and 600 seconds
for worker IPC/exit. They are experimental harness bounds, **not proposed genuine
limits**. The supervisor's total CPU/RSS/disk/wall time is not hard-limited by this
prototype. A complete frozen OS runtime, high-turnover fabricated workload,
supervisor-plus-worker peaks, storage headroom and interrupted-publication retention
must be measured before choosing and enforcing real budgets. The earlier 128 MiB
encoding cap is not a 128 MiB RSS promise.

## Precise proposed installation and separate OS rehearsal

This is a review procedure, not permission or an activation command. No part was
installed. Administrator steps require a separate, explicit authorisation.

1. Freeze one reviewed commit with successful CI for that exact commit, all added
   files including the allowlist, a fixed noninteractive supervisor bootstrap and
   a fixed worker command. The current callback seams and test launcher are for
   fabricated tests; an installed bootstrap must derive its launch command and
   protected review from administrator-controlled configuration, never worker or
   CLI/environment-supplied authority. Keep the genuine entry points closed.
2. On a disposable local Mac, an authorised administrator selects one new
   installation ID, records the actual numeric identities, and creates a dedicated
   non-login unprivileged worker account/group. A one-shot root-owned supervisor
   service runs only the fixed reviewed bootstrap and drops supplementary groups,
   GID and UID for the worker. No worker account belongs to admin or shares the
   supervisor's authority. The administrator remains trusted.
3. Proposed layout: a root-owned immutable runtime tree under
   `/Library/Application Support/BacktestBadger/E5dRuntime/<installation-id>`;
   a separate root-owned `0700` custody store under
   `/Library/Application Support/BacktestBadger/E5dCustody/<installation-id>`;
   a distinct root-owned `0700` publication parent under
   `/Library/Application Support/BacktestBadger/E5dPublications/<installation-id>`.
   All ancestors must be root-controlled and non-worker-writable, without symlinks
   or ACL grants to the worker. Code/runtime may be readable/executable by the
   worker but cannot be replaced. Credentials, original evidence and output/custody
   must not be readable/writable by the worker. No live paths are selected here.
4. Inventory the exact runtime closure: bootstrap and worker launcher, all project
   sources/config/lockfile, exact CPython executable/patch/build, stdlib, installed
   dependency bytes/metadata, native extensions and transitive loaded shared
   libraries, including the selected macOS system/dyld cache identity. Record
   architecture/OS, loaded-image paths and effective import paths. The inventory
   verifier compares every named root's exact file set and contents but cannot
   discover omitted external dependencies. A version list or seven synthetic role
   files is insufficient. Review external native images, ACLs, debugger rights,
   user-site/startup/import hooks and actual process environment separately.
5. Install OS policies denying worker network, private/source reads, writes to
   supervisor/runtime/state/output, process inspection/signalling of the supervisor,
   and inherited capabilities beyond its stdio pipes. Pin a supported macOS policy
   and launcher after review; this prototype does not claim a Python audit hook
   provides that isolation. Hard resource limits and whole-supervisor watchdog
   behaviour must be chosen from rehearsal measurements. No restart policy.
6. Populate **only fabricated** inputs in an administrator-controlled fixture tree,
   and a protected fabricated review with a short validity window, fresh attempt ID,
   exact output destination, frozen inventories and actual principal IDs. Use a
   separately controlled ephemeral rehearsal key. Create `installation.json`, then
   the exact digest/attempt slot and `eligible.json`, with exclusive creation,
   private modes and file/parent sync. Record installation/eligibility identities
   independently. Never reconstruct a missing production history from output.
7. Run as the real worker UID a negative-access probe against supervisor code,
   every runtime/state ancestor, eligibility/consumption/retention/output, and
   supervisor process. Probe open, write, truncate, unlink, rename, replace,
   symlink/hardlink, chmod, ACL change, signal and debugger attachment; every
   prohibited operation must fail. Demonstrate that same-UID fixtures would not
   provide this protection. Confirm there are no inherited private FDs or supervisor approval/custody/
   destination paths in the worker request/environment, and that network/source
   opens are denied. Historical operational metadata inside the four approved
   input bodies stays private and is excluded by the output projection.
8. Run the one complete invented full-year supervisor/worker publication. Observe
   durable consumption before launch, durable replay/six-account retention before
   reporting ACK, and six report IDs before publication. Record real UIDs/GIDs,
   mode/ACL/import/runtime observations, receipt hashes, exact output readback and
   resource measurements outside worker control. Repeat only with **fresh reviewed
   fabricated approvals and slots** for concurrency, lost ACK, worker/supervisor
   termination at each durability boundary, storage exhaustion and incomplete
   publication. Reusing any consumed slot must refuse before worker launch.
9. Reboot/process-kill and filesystem fault rehearsals must explicitly distinguish
   observed crash durability from untested power-loss guarantees. If storage or
   acknowledgement is uncertain, stop and quarantine; never enable an automatic
   service retry or attempt-store repair. Independently retain the rehearsal report
   and review all failures before selecting any genuine limits or authorisation.

## Remaining gates before genuine authorisation

- Review this uncommitted implementation and its fabricated-only recursive schema;
  authorise commit/push separately and obtain successful CI for the final exact
  reviewed commit. Baseline CI `39993266953` remains an owner-supplied claim.
- Review and implement/freeze the installed fixed bootstrap, OS policy and complete
  actual runtime closure. Carry out the separate two-principal Mac rehearsal above.
  Mode/UID mocks, a separate same-UID subprocess and POSIX file tests do not prove
  macOS ACL, code injection, process isolation or crash/power-loss properties.
- Measure and enforce approved genuine CPU/RSS/disk/time bounds. Test fixture output
  sizes and successful sparse-turnover full-year runs are not worst-case guarantees.
- Complete a separate exact genuine execution payload/schema and validate all its
  provenance, four original locations/pins, original historical CI, execution CI,
  installation, clock, closure, destination, budgets and receipt contracts. The
  existing owner-payload JSON remains preserved and inert with unresolved fields;
  it is not accepted by the fabricated verifier and must not be signed as-is.
- Freeze/review the complete genuine output projection, including unavailable
  benchmark variants and explicit exploratory/previously inspected-year limitations.
  The new allowlist is bounded to the fabricated available-account fixture and is
  not a general genuine exporter certification. Retained custody is integrity,
  not independent economic correctness or historical-source authenticity.
- Review any future activation code separately. Both
  `replay_genuine_minute_historical` and `run_genuine_historical_operator` still
  unconditionally refuse. A new approval, CLI flag, valid test signature or restored
  output marker cannot open them. No genuine reader/replay may run under this stage.

The 2024 interval remains previously inspected, exploratory research, not untouched
OOS, live trading, prospective paper performance, tradable alpha or profitability
evidence. Native minute opens are hypothetical references, not observed fills,
latency, liquidity, depth or market impact. No forced liquidation, forecast/model
change, cost change, new metric or public website publication was introduced.

## Changed-file inventory and preservation

Ten changed/untracked files relative to the requested baseline:

| File | Working-tree change |
| --- | --- |
| `.github/workflows/ci.yml` | Two added lines for the separate 117-case gate |
| `docs/stage-04b2e5c-fabricated-reporting-integration.md` | Existing five status lines preserved; continuation appended |
| `docs/stage-04b2e5d-operator-review.md` | Prior untracked report preserved verbatim below this new review |
| `docs/stage-04b2e5d-owner-payload-draft.json` | Prior untracked inert draft preserved without editing |
| `prompts/stage-04-paper/stage-04b2e5d-one-shot-historical-operator.md` | Prior untracked request preserved; authorisation/follow-up appended |
| `src/backtest_badger/genuine_backtest_custody.py` | New custody/approval/filesystem primitives |
| `src/backtest_badger/genuine_backtest_operator.py` | New fabricated supervisor, worker, reconciliation/readback |
| `src/backtest_badger/genuine_backtest_output_schema.json` | New static fabricated recursive allowlist |
| `tests/run_e5d_guarded.py` | New exact-file guarded CI/measurement/worker launcher |
| `tests/test_genuine_backtest_operator.py` | New focused fabricated tests |

The preservation check compared **50 exact tracked paths** against baseline:
33 E.5c source modules, its seven test/helper files, both previous launchers,
preparation tests, root AGENTS, project config/lockfile, and four frozen
preparation/contract/reporting/protocol documents. The diff was empty. More broadly,
`git diff --name-only <baseline> -- src tests pyproject.toml uv.lock AGENTS.md`
was empty: no existing tracked source or test was changed. The only tracked
changes are the CI addition and immediate E.5c status continuation. Both old CI
gates remain intact. Schema JSON references resolved, the owner draft parsed and
remained unauthorised, and `git diff --check` passed. HEAD remained the baseline.

Additional necessary source/test access is the existing E.5c exact-file import
inventory, plus the two new modules, their static schema and new test/guard. Source
imports do not authorise protected operations. Synthetic fixture helpers were
used; original evidence, `artifacts/`, private key files, credentials, `.env`, AWS,
providers, databases, production and the historical sibling repository were not
accessed. Fabricated test files were written only to newly created temporary
scratch directories; incomplete outputs were preserved there by the operator.

---

## Preserved initial E.5d custody-blocker review

# Stage 4B.2E.5d — operator review stopped at the custody boundary

2026-10-23, Europe/London. **BLOCKED: operator implementation is not complete.
E.5e is not ready for authorisation. No genuine evaluation was performed.**

The first repository command read the exact root `AGENTS.md`. Local HEAD matched
`09af01225d752cc3b02c08752e42587c353710f8`; the initial scoped tracked-file check
was clean. Successful CI `39993266953` is the owner's supplied baseline claim,
not independently queried and not CI for these changes.

The [archived request](../prompts/stage-04-paper/stage-04b2e5d-one-shot-historical-operator.md)
requires stopping if independent retention cannot honestly be established. This
report invokes that gate. No new runner, approval verifier, attempt store,
publisher, tests or CI step was added. Both existing mandatory CI gates remain.

## Precise blocker

| Reviewed component | Existing responsibility | Missing E.5d property |
| --- | --- | --- |
| `genuine_backtest_preparation.attempt_transition` | Pure transition table | Durable, protected consumption history |
| `genuine_minute_verification_operator._operate_verified` | Exclusive output reservation and verification publication | Attempt authority independent of the executor-controlled output directory |
| `genuine_backtest_reporting_integration._retain_fabricated_handoff` | Whole-replay hash and six account fingerprints | Independently controlled retention; expected pins are returned to the same process |
| `genuine_backtest_reporting_integration._decode_test_report` | Equality to retained report bytes and hash | Independently retained report receipt; caller controls both expected inputs |
| `genuine_minute_signed_approval` | Enrolled public key and verification-specific signature domain | Execution-specific approval and a protected spent-attempt record |
| `genuine_minute_verification_runtime._read_environment` | Git, module paths and dependency versions | Complete immutable runtime/dependency content closure |

A caller able to replace both results and expected pins defeats their integrity
check. A second process with the same filesystem authority, an executor-owned
`0600` file, owner-reversible `chmod`, or `O_EXCL` in a deletable/recreatable
directory does not establish independent custody. An owner signature on pre-run
intent cannot attest to not-yet-produced account/report bytes. A writable JSON
claim that an attempt is unspent is not protected consumption history.

The reviewed contracts specify no separately controlled custodian, protected
monotonic attempt store, isolation policy or immutable runtime image. This is a
missing trust/deployment design, not a claim that such a design is impossible.
Presuming a privileged boundary, adding a same-process callback returning
`independent=True`, or treating mocked permissions as enforcement would weaken
requirements 2 and 4. Consequently no operator was wired around those assumptions.
The existing public `replay_genuine_minute_historical` remains unconditionally
closed. Existing synthetic regression calculations are not an E.5d attempt.

## Design decision needed before implementation resumes

Review one concrete local custody arrangement. One possible design is a narrowly
scoped, separately controlled supervisor with protected append-only attempt state
and an immutable runtime, running an unprivileged worker. This is a proposal, not
an installed service or a new generic framework. Review must establish:

1. Custodian/executor principals and actual isolation. The executor cannot replace
   custodian code, trust anchors, retained records, parent directories or runtime.
   Same-UID process separation alone is insufficient. Define the threat model,
   including administrative rollback and loss of custody history.
2. One protected namespace keyed by approval digest and attempt ID, independent
   of output path. Missing, damaged or uncertain history is terminal, never
   permission to reconstruct an unspent approval. Read-only preflight cannot
   consume. Atomic reservation and file/parent-directory durability must finish
   before any calculation; uncertain acknowledgement consumes the attempt.
3. Complete canonical replay bytes transferred to the custodian before reporting.
   It independently computes and retains the whole-replay and six ordered account
   identities bound to run, approval, method and implementation. After reporting,
   it retains six report identities associated with those accounts and replay.
   Receipts must authenticate independently of executor-controlled candidate
   fields. This demonstrates retention, not correctness of a malicious producer.
4. One uninterrupted evaluation. Crash, timeout, lost receipt, uncertain reservation
   or incomplete publication cannot permit retry/resume. Later readback cannot
   resume computation or promote partial evidence. A replacement needs fresh review.
5. Specific filesystem/OS durability semantics. Test concurrent launch, process
   death, storage errors and lost acknowledgement at every durable point, including
   parent fsync and final-marker publication. Catchable exception injection alone
   cannot demonstrate power-loss durability or rollback resistance.
6. Accurately measured immutable closure: code, launcher, CPython patch/executable,
   stdlib, dependency bytes, native extensions/shared libraries, lockfile and project
   config. Versions/lockfile alone are insufficient. Review clock and resource limits.

The enrolled owner key may be reused as signer identity only after review of a new
domain/schema. Historical verification, D.14 sign-off and E.4 consent are separate.
Any custody signing key needs an explicit trust design; none is created/enrolled
here. Human independent retention is another possible design, but bounded waiting
and interruption/no-resume semantics must be specified first.

## Conditional owner runbook — no activation command

These steps are not runnable authorisation. E.5d must be completed before E.5e;
E.5e cannot silently become a further implementation stage.

1. Review the custody design and implement it with fabricated identities only.
   Complete the new approval verifier, closure checks, four-file reader, durable
   state machine and publisher. Test failures at each durable point and genuine
   route denial. Do not invoke D-series acquisition/verification.
2. Freeze the full output schema, privacy projection and limits before calculation.
   Obtain green CI for the exact subsequently reviewed execution commit, including
   the existing mandatory 87/55-case gates and a new guarded operator step.
3. Independently complete the private owner payload below. Select a fresh output
   outside every original evidence/source tree and establish trusted unused custody
   state. No live path is selected, probed or approved by this report.
4. Only after separate authorisation, verify signature, window, commit/CI evidence,
   complete closure, custody and destination. Read exactly four approved inputs
   with bounded descriptor-relative no-follow operations; reject symlink ancestors,
   nonregular files, aliases and descriptor/stat identity changes. Retain pre/post
   hashes, lengths and metadata. Use unchanged E.3 parsing and D.14 reconciliation.
5. Recheck preflight at reservation. Durably consume one attempt before calling
   the private publication replay once. Reuse the existing monetary core, ledger
   verifier and native-minute reporting adapter, with independent custody receipts.
6. Exclusively create bounded private files, fsync data/directories, write integrity,
   and commit manifest last without replacement. Exact readback must match the
   independently retained receipt. A marker alone cannot certify later readback:
   protected state must distinguish committed-but-unconfirmed from completed.
   Preserve incomplete/uncertain output; never silently clean up, retry or promote.

## Later owner payload

[stage-04b2e5d-owner-payload-draft.json](stage-04b2e5d-owner-payload-draft.json)
contains the complete **proposed field inventory**, including unchanged method
and retained four-file pins. It is an inert draft, not an implemented schema,
signature envelope or usable approval. No future verifier may accept `UNRESOLVED`.
A complete usable exact payload cannot honestly be supplied yet: execution commit
and CI, original absolute paths, custody, complete closure, output schema and
resource budgets remain unresolved. These are explicit stop gates, not defaults.

The draft binds four absolute paths/hash/lengths; historical provenance separately
from signer identity; frozen method/protocol and six portfolios; reviewed code,
dependency/runtime closure and successful exact-commit CI; attempt ID/window;
protected custody/publication contracts; output path/limits; maximum attempts one.
The historical lengths/hashes/commit are transcribed E.5 declarations, not observed
original bytes. Original historical CI remains unresolved. The enrolled public key
ID is observed in source code; it does not establish a signature in this stage.

After final review, sign canonical exact payload bytes under a new execution-specific
domain, privately retaining payload length/digest and envelope independently. Never
reuse the D-series domain or permit test-key injection on a genuine route. No
signature, private key or outer self-hash is included in this draft. Economic output
may carry safe run/approval/custody identities, never private payloads or roots.

## Scientific and privacy contract still requiring exporter review

Preserve BTCUSDT/ETHUSDT and separate Ridge/cash/B&H portfolios with 10,000 USDT
each; the 2024 interval, 2,195 forecasts per market, strict `prediction > 1e-12`,
+4h+60s availability and 12:01 to 12:02 execution. Preserve 10/1/2-bps costs,
0.000001 quantity step, exact Decimals, HH:00 marks, sticky exits, partial final
periods and retained final holdings. No new engine, metric, tuning or liquidation.

E.5c projects `pins`, `original_files`, `code_sha256`, publication/sign-off claims,
typed forecasts/references and replay/account data, excluding raw operational
integrity and recipe free text. A new exporter still needs a frozen recursive
field/type/value allowlist, including nested portfolio IDs, decision reasons and
provenance labels. Reject unknown fields and path-bearing/private free text before
export. Do not recursively serialise arbitrary source evidence/dataclasses as a
shortcut. Preserve ledgers, references, exact metrics and safe lineage; bind omitted
private metadata by approved digests. Existing TEST projection is not certification
of a genuine exporter.

Every later result must state: 2024 was already inspected and is exploratory, not
untouched OOS, live trading, prospective paper performance or evidence of tradable
alpha. Native minute opens are reference assumptions, not real fill, latency,
liquidity, depth or market-impact observations. No public website publication.

## Validation, resource limits and preservation

Executed results are recorded below. No existing test pass constitutes E.5d
operator validation. New approvals, concurrency, durable consumption/crash,
independent custody, original reads, complete closure, output symlinks/reuse,
immutable publication and post-crash readback remain unimplemented/untested for
E.5d. No full repository test suite or remote CI is run.

Existing parser bounds: manifest 4,096 bytes, authenticated inputs 32 MiB,
integrity/sign-off 1 MiB each. E.5c encoding bounds: 128 MiB, depth 32, 8,000,000
nodes, 100,000 entries per sequence/mapping and 1 MiB per string. These are not
RSS, wall-time, disk-space or power-loss guarantees. Retained objects, encoding
and decoded copies can use substantially more memory. No genuine resource budget
or peak RSS was measured; these must be approved before execution.

## Additional repository access inventory

Besides user-named files, the guarded launcher permits these exact dependencies
under `src/backtest_badger/` (each has suffix `.py`):

`__init__`, `genuine_minute_inputs`, `genuine_minute_verification_runtime`,
`genuine_minute_verification_wiring`, `genuine_minute_price_parity`,
`paper_minute_integration`, `paper_historical_evaluation`, `paper_historical`,
`paper_accounting`, `paper_execution`, `paper_strategy`, `paper_types`,
`forecast_data`, `minute_execution_data`, `execution_data`, `model_data`,
`archives`, `frozen`, `ingestion`, `features`, `candles`, `research`, `db`,
`config`, `history`.

Additional synthetic dependencies under `tests/`: `test_genuine_backtest_preparation.py`,
`test_genuine_minute_publication.py`, `test_genuine_minute_replay.py`,
`test_genuine_minute_inputs.py`, `test_genuine_minute_signed_approval.py`,
`test_paper_minute_reporting.py`, `test_paper_minute_historical.py`.
The input/signature suites are not collected; their helpers support fabricated
publication construction. The runtime module was also read directly for closure
review. Reading/importing these modules did not invoke their protected operations.
This bounded import/read scope is not a certified execution/runtime closure.

The guards install before project imports, deny original/private paths, writes,
processes and network, and constrain repository reads to exact files. Installed
stdlib/virtualenv dependencies are used without sync/download. Python guards are
procedural safeguards, not independent OS custody. No attachment metadata,
original evidence, `artifacts/`, private keys, credentials, `.env`, AWS, provider,
database or production infrastructure was accessed. No genuine output directory,
real signature, commit, push or deployment was created.

## Executed validation record

| Check | Actual local result |
| --- | --- |
| `python3.12 -I -S -B tests/run_e5_guarded.py` | 87 passed, zero skipped; 33.699 seconds |
| `python3.12 -I -S -B tests/run_e5c_guarded.py --regressions` | 603 passed, zero skipped; 529.60 seconds; includes all 55 mandatory E.5c cases |
| Scoped Ruff lint, installed 0.17.0 | Passed for the 11 Python files listed below |
| Scoped Ruff format check, installed 0.17.0 | All 11 files already formatted |
| Preservation against requested baseline | Empty diff for 51 exact tracked paths; HEAD unchanged |
| Draft/document checks | JSON parsed; unchanged four pins/method/protocol, six portfolios, single attempt and closed draft authority confirmed; new-file whitespace checks passed |

Local Python was 3.12.13; this version observation is not a complete runtime closure.
The two guarded suites ran concurrently in separate processes. Counts are baseline
regression results, not newly implemented E.5d coverage; the 603-case run includes
integration, publication/sign-off, private replay, native-minute reporting and
minute-accounting cases. Its unchanged launcher enforces exactly 55 collected
E.5c cases, no skips and a passed call for every collected test. The standalone
55-case command was not separately rerun. All data and identities used in these
calculations were fabricated. No economic result files were written.

Lint used `ruff check --isolated --no-cache --no-respect-gitignore --select E,F,I,UP,B
--target-version py312`; formatting used `ruff format --check --isolated --no-cache
--no-respect-gitignore --target-version py312`. Both supplied these exact arguments
under `src/backtest_badger/`: `genuine_backtest_preparation.py`,
`genuine_backtest_reporting_integration.py`, `genuine_minute_publication.py`,
`genuine_minute_replay.py`, `genuine_minute_signed_approval.py`,
`genuine_minute_verification_operator.py`, `paper_minute_historical.py`,
`paper_minute_reporting.py`; and under `tests/`: `run_e5_guarded.py`,
`run_e5c_guarded.py`, `test_genuine_backtest_reporting_integration.py`.

The 51-path preservation set is the unchanged E.5c launcher's 33 `SOURCES` and
seven `TESTS`, both launchers, `test_genuine_backtest_preparation.py`, root
`AGENTS.md`, `.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`, and the four
unchanged preparation/contract/reporting/protocol documents. It excludes the
intentionally updated E.5c status document. This is a tracked-code preservation
check, not observation of original evidence or complete checkout/runtime closure.

Diff: three new review artifacts (this report, inert payload draft, request archive)
and five status lines in the immediate E.5c document. No executable code or frozen
contract changed. No new fault-injection/custody tests exist; no acceptance claim
is made for the blocked operator. Required next work is the concrete independent
custody design and its implementation/validation within E.5d, before any E.5e request.

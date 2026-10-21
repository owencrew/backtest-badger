# Stage 4B.2D.6 — Activation blocked; fail-closed review proposal

Prepared 2026-10-21 (Europe/London). **Genuine activation is not implemented.**
This delivers the owner's explicitly permitted fail-closed alternative, with
additional refusal tests and revalidation of existing fabricated mechanics.
No approval record, trust anchor, signing key, authority reader, CLI or genuine
invocation script has been created. Both public gates remain unconditional
refusals before argument inspection or I/O. Stop for owner design review.

## Baseline and reason for the fallback

Initial clean `main` and final HEAD:
`94c0f08cd73e4cbe298ddf1baeec6fe08248cea9`,
`feat(research): prepare genuine minute verification wiring`.
Branch, HEAD, status and Git/index blob identities were checked locally.
The owner reports baseline Actions run `39515297944` passed at this SHA
(2,039 passed, 1 skipped). This is owner-supplied context, **not independently
verified CI evidence**. Existing tracked Stage 4B.2D.5 documentation records its
earlier starting SHA and local results, not independent confirmation of this new
CI run. No GitHub query was made; baseline CI cannot approve new work.

The [substantive owner request](../prompts/stage-04-paper/012-genuine-verification-activation.md)
explicitly requires:

> If this independent-anchor requirement cannot be implemented without another
> owner decision, leave the public genuine entry point closed and report the
> precise blocker rather than invent a signing key, an authority source, or a fallback.

**Precise blocker:** no owner-selected, independently retained approval anchor
or reviewed mechanism for obtaining it is designated in the request or existing
operator/wiring contract. A caller's digest, signature/public-key pair, CI string,
boolean consent field or matching current checkout cannot supply that missing
authority. The fixture `environment_reader` is test injection, not independent
owner/CI observation. Selecting a trust store or embedding an arbitrary approval
digest would invent authority. Even a seemingly complete candidate must refuse.

Consequently no production validator, loader binding or shared production core
was added. This is not a dormant genuine implementation that can be enabled by
filling fields. A later separately reviewed source change is still necessary.

## Concrete review proposal and future gates

Before implementation can activate a genuine path, the owner must designate
**where the independently approved manifest/digest is retained, how it is observed
through a distinct trusted mechanism, who can change it, and how its exact scope
and one-attempt permission are reviewed and revoked**. This document selects none
of those mechanisms and contains no accepted digest or invocation payload.

The proposed future contract is:

1. The distinct reviewed mechanism supplies the independently retained approval
   identity and offline CI evidence for the exact reviewed implementation SHA.
   It cannot take its anchor from the candidate, its sources, current runtime,
   filesystem metadata, current Git hashes, readiness records or environment
   overrides. A missing/untrusted observation rejects before original source or
   destination metadata access. Consent remains an owner-controlled procedural
   trust boundary; a digest binds bytes, not human consent.
2. A strict complete approval manifest is bound by that identity. Its reviewed
   encoding and digest coverage must include every field: full Git SHA, matching
   independently reviewed CI run/status/conclusion, exact Python/dependency
   versions, complete transitive code/document/config hashes and lengths, exact
   absolute roots/destination, 57 source identities, all ordered monthly evidence,
   original research/forecast declarations, hourly hashes, historical audit code,
   source kind, one-attempt permission and strict flags. Reject unknown/extra/
   missing fields and malicious objects; do not auto-fill evidence.
3. After approval, perform local exact clean-code/runtime/import identity checks
   and expressly authorised path preflight. No network, database or provider
   operation is permitted. Reserve the sole absent destination exclusively before
   opening the first source file. Existing files, symlinks, failed/partial prior
   attempts and races refuse, with no new path, retry, repair or resume.
4. Bind unchanged default-pinned `forecast_data.load_forecasts`, unchanged
   `paper_historical_evaluation._validate_lineage`, and unchanged
   `minute_execution_data.load_minute_execution_data` with the literal original
   minute-manifest pin. Reuse full bounded projection and prior five-file parity
   validators. Do not dynamically dispatch the Stage 4B.2D.5 symbolic strings.
5. Recheck sources, code, imported identities and environment around verification
   and publication. Keep genuine and fabricated front doors/types/validation
   separate. Exclusively publish deterministic `authenticated_inputs.json`, then
   separate operational `integrity.json`, with fsync and canonical byte/hash/size/
   crosslink readback. Publish `manifest.json` last, only after preservation checks,
   then read back all three files and recheck final preservation/inventory.
6. Genuine scientific and publication evidence must retain the distinct genuine
   source kind, `kind=source_authentication_only`, `economic_results=false` and
   `genuine_execution_authorised=false`. Failures preserve forensic partials,
   invalidate only an owned success-marker inode and best-effort publish a safe
   category/phase without exception text, source data, secrets or paths.

Future strict flags remain `verification_only=True`, `single_attempt=True`,
`resume=False`, `strategy_authorised=False`,
`economic_publication_authorised=False`. Readiness/plan objects and dictionary
copies remain `NOT_APPROVED / NOT_READY / NO_SOURCE_ACCESS` documentation.

After the mechanism decision: complete implementation and fabricated review;
owner-authorised commit and independently checked green CI for that exact code;
independently retain all evidence; then a distinct explicit permission for one
genuine verification invocation. Genuine replay/economic computation and economic
publication each require subsequent separate approvals and reviewed code.
Reviewing or committing this proposal does not open either public API.

## Declared identities and unresolved evidence

All real source identities here are **declarations only**, never newly measured.
The complete declarations remain in the unchanged
[Stage 4B.2D.5 guide](stage-04b2d5-genuine-verification-wiring.md#known-declarations-and-exact-future-inventory)
and frozen [minute source tables](stage-04b2c-minute-source-pins.md).

| Declaration | SHA-256 | Declared bytes |
| --- | --- | ---: |
| Forecast manifest | `af89bcdcd5a40b0ad0d011e09ee49d60b6f26dc24d5db5b9f08de8fa1d1a0581` | **Unknown** |
| Forecast CSV | `e6b8b2df739de361f80fa731c9901635b7fc3071daa75205b06c8c536e839674` | **Unknown** |
| Minute manifest | `673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127` | 19,749 |
| Minute CSV | `37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233` | 107,002,277 |
| Frozen minute source document | `967159d9f7e94a05695187adb5413edc6a1914e6cac8aec6b286e6800f58836c` | Tracked document; not a source file |
| Prior parity manifest | `53913fcc8b951d6171761e0f2f7bec14ca98320e4786893f3839fcdbfd9b424d` | 740 |

There are 57 declared source hashes but only 55 declared source lengths: two
named forecast files, 50 minute files (manifest, CSV, 24 ZIPs and 24 sidecars),
and five prior parity files. Both forecast lengths require separately authorised
independent evidence acquisition/retention. They cannot be learned during the
verification being approved. The complete original auditor implementation map
also requires independently retained historical evidence; hashing today's code
is not a substitute. Its declared auditor hash alone is insufficient.

The 24 ordered minute associations must preserve immutable URLs, ZIP/sidecar and
expanded CSV identities, month counts including leap February and retrospective
receipts. Retain the original full Stage 2B/research declarations and all 24
hourly month hashes without opening research/labels or original hourly sources.
The original five-file parity raw identities/inventory/provenance must be checked;
the 17,568-pair audit must not be rerun. Source-release status is not permission.

The three proposed roots remain `artifacts/experiments/stage-2b-v1/`,
`artifacts/execution/binance-1m-2024-v1/` and
`artifacts/audits/stage-04b2d1-native-parity-v1/`. The sole proposed destination
remains `artifacts/audits/stage-04b2d3-minute-inputs-v1/`. Their existence, ignore
state, contents and symlink state were not inspected. The complete future
absolute paths and permission for preflight remain unresolved.

Exact future enabled-code commit/CI/runtime identities and independently retained
hashes/lengths for the Stage 4B.2D.5 transitive allowlist plus any new imported files
are unresolved. The current preservation inventory below grants no authority.

## APIs, fabricated boundaries and scientific limits

**No public or private API change.** These remain unchanged:

```python
run_genuine_minute_verification(*, approval) -> AuthenticatedMinuteInputs
authenticate_minute_inputs(*, approval) -> AuthenticatedMinuteInputs
_run_fixture_verification(
    *, fixture_root, approval, forecast_loader, minute_loader,
    lineage_validator, environment_reader, native_loader_evidence,
) -> AuthenticatedMinuteInputs
```

Both public calls reject before inspecting approval; omitted required arguments
and additional override keywords fail Python argument binding. The private
fixture front door still requires isolated temporary roots and invented pins;
genuine pins/kinds cannot be accepted as fixture authority. Nothing manufactures
a genuine result from test bytes. No production success path exists to test.

Existing fabricated tests exercise eight accounts × 2,195 exact Decimal forecasts,
five-feature Ridge/scaler train-only lineage, full 1,054,080 native rows and
21,958 retained references (10,979 per market). Availability remains source open
+4h+60s with strictly next-minute references, e.g. 12:01 to 12:02; last reference
is 2024-12-31 16:02. No late signal/2025 prices or historical issuance is invented.
The independently bounded projector still has its 32-MiB allocation regression.
Authenticated inputs retain false execution authority and cannot enter either
synthetic replay public route. Archived opening equality proves neither
fillability, contemporaneous quote availability nor profitability.

The publisher's descriptor anchoring/exclusive creation and before/after checks
detect observed replacement and preserve alien files; they are not a transaction
against hostile concurrent code. Hard kills, storage failures and coordinated
replace/restore races can defeat cleanup or observation. Success requires complete
readback/inventory and preservation, not merely a manifest's presence. Python
records, test monkeypatches and audit hooks are not a hostile-process sandbox.

## Validation and preservation record

The new focused module tests 22 untrusted claims against both public gates,
omitted/extra parameters, and a fresh-process cold import. It asserts zero I/O or
fixture dispatch on rejection. Claims include self-computed approval digests,
unreviewed anchors, malicious/nested objects, readiness/plan copies, wrong/missing
files, unknown lengths, wrong code/document/source/runtime/commit/CI and source
kinds. These demonstrate unconditional refusal, **not production schema validation**.

The cold child installs the existing process audit/stat guards before project
imports by extracting only their definitions from the unchanged test source.
It exercises 23 forbidden operations (Path.stat/lstat, os.open/listdir, DNS,
network and PostgreSQL) before any underlying forbidden access, then confirms
unrelated temporary-root I/O works. The validation runner uses the same approach
before pytest collection. No guard or old assertion was weakened.

Existing operator/authentication/integration/parity regressions provide fabricated
full-native ZIP reconstruction, actual auditor-schema checks, root-independent
science, malformed/header/nonfinite/month/hour/manifest failures, source/code/
environment mutations, symlink/root swaps, reservation races, partial/collision/
fsync/link/readback failures, manifest-after-link interruption, inode-checked
invalidation and alien-file preservation. Their shared expensive fixtures remain
unchanged; the new tests create no additional full-year datasets. No success test
is claimed for genuine activation or an independent approval observer.

Validation uses `uv run --locked --offline --no-sync`, a writable isolated cache,
fresh user-owned temporary bases, explicit `tests/` collection and process guards.
Database environment configuration is removed by the runner. PostgreSQL tests
requiring a disposable DSN are skips, not passes. Results are recorded only after
normal process completion, including pytest cleanup.

| Check | Executed result |
| --- | --- |
| New refusal module | 47 passed in 0.19s; exit 0 |
| Focused regression selection | 533 passed in 213.96s (0:03:33); exit 0, no cleanup errors |
| Complete offline suite | 1,904 passed, 183 skipped in 386.86s (0:06:26); exit 0, no cleanup errors |
| Whole Python inventory Ruff lint/format | Both passed for all 91 explicit Python files; exit 0 |
| Tracked/staged and new-file whitespace | Both Git diff checks and all three new-file whitespace/final-newline checks passed |
| Protected-file comparison | All 185 protected files match SHA-256/length, HEAD and index bytes |

Local validation runner: `/private/tmp/badger-4b2d6-offline-tests.py`.
It installs the unchanged guard before importing pytest or project code, using
an AST extraction of just `forbidden`, `check_path` and `install_offline_audit`.
The new child-process test independently exercises this exact guard sequence.
The commands use `UV_CACHE_DIR=/private/tmp/badger-4b2d6-uv-cache`:

```sh
uv run --locked --offline --no-sync python /private/tmp/badger-4b2d6-offline-tests.py tests/test_genuine_minute_verification_activation.py
uv run --locked --offline --no-sync python /private/tmp/badger-4b2d6-offline-tests.py tests/test_genuine_minute_verification_activation.py tests/test_genuine_minute_verification_operator.py tests/test_genuine_minute_verification_wiring.py tests/test_genuine_minute_inputs.py tests/test_paper_minute_integration.py tests/test_genuine_minute_price_parity.py tests/test_minute_price_parity.py
uv run --locked --offline --no-sync python /private/tmp/badger-4b2d6-offline-tests.py tests
```

Focused/full logs are retained locally at `/private/tmp/badger-4b2d6-focused.log`
and `/private/tmp/badger-4b2d6-full.log`. These are local test records, not CI
or genuine invocation approvals. Temporary files are not permanent repository
artifacts; the recorded results and guard test remain in the repository.

The focused and full logs both end with `PYTEST_EXIT=0`; their enclosing
processes also returned exit 0. All 183 full-suite skips require disposable
PostgreSQL access and were not executed. No failed validation run occurred in
this stage. Final review found no additional change needed in the refusal tests;
all test code was final before both combined runs. Only documentation changed
after the full run started. No CI for these changes was queried or triggered.

Reviewed new refusal-test SHA-256:
`09e298336ab403c4bbdc5c4fc70c83b58e6904318a02b58657a7dc2ac713de3c`.
Substantive prompt archive SHA-256:
`bf60f07caae701c1f036995f57ba6b7cf7384756e9ce309d556ef11a5ab6a5f1`.
These are local review identities, not invocation approval anchors.

Before edits, all 188 tracked files were snapshotted from HEAD and index blob
bytes only. The complete local inventory is
`/private/tmp/badger-4b2d6-baseline.json`, SHA-256
`24e4809c91c6dcd33f28361549c08ceeaf2fcaf9069ad7f22c07bf99a8cf4e60`.
Only architecture, roadmap and handoff overviews are excluded from the protected
set; all 185 other pre-existing tracked files must remain byte-identical. No
protected historical file needs changing for this fallback. Key baseline hashes:

| Protected implementation | SHA-256 | Bytes |
| --- | --- | ---: |
| `genuine_minute_verification_operator.py` | `c693d5e11648619719402a62ab2fe94d69c547e04463877c0dfd9a8b3442f70e` | 22,704 |
| `genuine_minute_inputs.py` | `415c5e381dadc176a35c32f373fb4c25668e8c46b28fd2ce4d79952534a856e0` | 34,385 |
| `genuine_minute_verification_wiring.py` | `6bbb1cefef585a6dd5f4ee2fb01170cb2c5d8a72007020d9d0019be6e3bfffb6` | 13,705 |
| `forecast_data.py` | `d9ba8b84e4846d1d12dc208e4de9164e58ef418fc5381a27eef10322b9b180aa` | 5,650 |
| `minute_execution_data.py` | `84cb5f7a8c3fcfcc6b7b488cdaf22bd6e3fb8c369fdf8cf12c1435fc2da256c2` | 20,797 |
| `paper_historical_evaluation.py` | `df46fd26f857e834bd0559caa25ee525868b8de08ccbe3abb7388e9c6db193aa` | 41,830 |
| `genuine_minute_price_parity.py` | `d4b3fb3f9f06b553fce0f1303a61bc4483feb2d90840573c9c33ac9e5523d092` | 27,734 |

Changed files are this guide, the new refusal test module, substantive prompt
archive and the three overview documents. All production code, old tests,
protocols, source pins, replay/accounting modules, dependencies and lockfile remain
unchanged. The archived prompt excludes unrelated browser/session material.

**NO GENUINE SOURCE READ/STAT/INVENTORY. NO GENUINE VERIFICATION INVOCATION.
NO ECONOMIC CALCULATION on genuine data. NO COMMIT/PUSH/DEPLOY.**
Synthetic regression suites still exercise their existing synthetic calculations.

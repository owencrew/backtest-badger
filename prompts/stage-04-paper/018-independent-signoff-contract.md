# Stage 4B.2E.3 — Original substantive owner request

**IMPORTANT — BEFORE ANY TOOL CALL**
Read this entire message and apply its repository-access restrictions before taking any action.
Do not run `pwd`, `rg --files`, unrestricted `git status`, directory discovery, or generic environment inspection before processing the restrictions.
The instructions below are the complete task. There are no attachments to inspect.
No original market data, authentication publication, private keys, signed approvals, external evidence files or credentials may be accessed.
Implement Stage 4B.2E.3 using only the explicitly permitted repository files and fabricated tests. Do not commit, push or execute genuine historical replay.

Backtest Badger — Stage 4B.2E.3: Independent Sign-Off Contract Reconciliation (FABRICATED TESTS ONLY)
Owner request / stop gate. Implement and review the smallest pure, private sign-off reconciliation step needed between the independently retained Stage 4B.2D.14 sign-off and the Stage 4B.2E.2 authenticated publication bridge. This is NOT authorisation to read original publication/sign-off files, perform a genuine backtest, publish economics, or open the public replay gate. Stop with an uncommitted diff and review report.

## 0. Restriction applies BEFORE YOUR FIRST TOOL CALL

Read this entire prompt, including this boundary, BEFORE any tools or shell commands. Do not run rg --files, unrestricted git status --short, directory inventory, recursive discovery or generic environmental probes. Prior Codex runs breached this rule by performing automatic discovery before processing the prompt. If that happens again, immediately stop and disclose it; do not claim the procedural boundary was honoured.
Allowed repository source reads are strictly named paths, and only those actually necessary:

* AGENTS.md
* src/backtest_badger/genuine_minute_publication.py
* src/backtest_badger/genuine_minute_replay.py
* src/backtest_badger/genuine_minute_inputs.py
* src/backtest_badger/genuine_minute_signed_approval.py
* src/backtest_badger/genuine_minute_verification_operator.py
* src/backtest_badger/paper_minute_historical.py
* tests/test_genuine_minute_publication.py
* docs/stage-04b2e2-publication-replay-bridge.md
* docs/stage-04b2e1-genuine-replay-integration.md
* docs/architecture.md, docs/roadmap.md, docs/development-handoff.md
* pyproject.toml, uv.lock, and the explicit existing relevant test file(s) only as required for protected regression.

Do not inspect artifacts/ (including any list/stat/open of its original verification publication), ~/Documents/BacktestBadgerEvidence/, ~/Downloads/, the owner's keys, any signed approval, original model forecasts, native minute/raw/hourly/parity files, sibling repositories, secrets, environment credentials, remote services, production infrastructure, provider APIs, databases or websites. Do not use network access. Do not open the user's actual independent sign-off. Its writer-produced JSON contract is specified in this request and is the sole allowed template; don't discover it from the original file.
Use targeted exact-path Git diff commands only where needed. Do not git add/commit/push. Do not deploy. No new dependencies or changes to frozen cost, timing, strategy, minute accounting, protected protocol/source-pin documents or other existing source modules. Avoid Ruff/python/pytest caches and bytecode in the repository and original artifact paths; use RUFF_CACHE_DIR/UV_CACHE_DIR under a fresh temporary location, PYTHONDONTWRITEBYTECODE=1, -p no:cacheprovider, bounded pytest --basetemp and offline test guards established by the earlier E.2 guide. If you cannot meet a restriction, stop and report instead of working around it.

## 1. Verified baseline declarations (not authority to access originals)

Latest owner-pushed main commit as observed independently: 27a4d4e6967fa8a986678f1622e4509cffa16b4b with message feat(research): bridge authenticated publication to genuine replay. GitHub Actions run 39833360153 completed success, reporting 2,485 passed and 1 skipped. These facts are review context, not an instruction to contact GitHub; use the checked-out commit if it matches, otherwise stop before implementation.
Stage 4B.2E.2's private _parse_verified_publication currently matches three supplied publication bodies to four independently supplied fingerprints, but only checks the sign-off fingerprint claim's equality; it does not inspect or validate the sign-off's JSON. Stage 4B.2D.14 owner-run sign-off was produced by a separate read-only Python script and retained externally. The sign-off schema is KNOWN from that script (quoted below); no live access is needed to develop a strict pure parser.
Externally retained owner-observed identities (do not recompute them from candidate bytes to create authority):

| File | Exact bytes | SHA-256 |
| --- | ---: | --- |
| manifest.json | 560 | 3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea |
| authenticated_inputs.json | 15,272,413 | 2581482b4b8a60fa1a53f7710ed080be7de25d50a76fcae35c8aaf64f2cb2168 |
| integrity.json | 74,200 | 23c3d17b2e5b67de701d9a0dd22d6135a907057b9acaeb16bcbdb4cb9c613a8b |
| Independent stage-04b2d14-publication-signoff-94584dc.json | 2,020 | 21b04470e861a039750bf7b665b993d332bf998fcc5b9fea47dc2c8b80f334b4 |

The original verification commit was 94584dc4b08f06441cff3bcd7983bba1ca0afe8d, with successful CI claim 39668530849. This is distinct from the present reviewed implementation commit and any future genuine simulation commit.

## 2. Exact original D.14 sign-off writer contract (no source file lookup)

The D.14 readback script creates an record mapping, serialized with json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", UTF-8, no float special values. Fields EXACTLY:

```python
{
  "schema": "stage-04b2d14-publication-signoff-v1",
  "status": "PASS",
  "original_execution_commit": "94584dc4b08f06441cff3bcd7983bba1ca0afe8d",
  "reviewed_ci_run_id": "39668530849",
  "publication": "artifacts/audits/stage-04b2d3-minute-inputs-v1",
  "independent_manifest_sha256": "3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea",
  "published_file_identities": {
    "authenticated_inputs.json": {"bytes": 15272413, "sha256": "2581482b4b8a60fa1a53f7710ed080be7de25d50a76fcae35c8aaf64f2cb2168"},
    "integrity.json": {"bytes": 74200, "sha256": "23c3d17b2e5b67de701d9a0dd22d6135a907057b9acaeb16bcbdb4cb9c613a8b"},
    "manifest.json": {"bytes": 560, "sha256": "3d58852c3b837f2853beb6def5350932a25d52dc1373a9fc9d8db5b0d9f31eea"}
  },
  "publication_kind": "source_authentication_only",
  "source_kind": "genuine_retained_stage2b_native_minute_prior_parity",
  "verification_flags": {
    "verification_only": True, "single_attempt": True, "resume": False,
    "strategy_authorised": False, "economic_publication_authorised": False
  },
  "genuine_execution_authorised": False,
  "economic_results": False,
  "scientific_counts": {
    "forecast_accounts": 8, "forecasts": 17560, "reference_markets": 2,
    "references": 21958, "native_minute_rows_authenticated": 1054080
  },
  "checks": [
    "Exact no-follow publication path; exactly three existing files",
    "Independently retained manifest SHA-256 before parsing",
    "All manifest-declared companion hashes and byte lengths",
    "Strict canonical JSON, scientific and operational crosschecks",
    "Original 57 source, 45 implementation, and 22 historical audit identities",
    "Second exact-file byte/hash/metadata readback"
  ],
  "limitations": [
    "Read-only post-publication readback, not genuine verification rerun",
    "No original data sources, signed approval, private signing key or strategy engine read",
    "CI success was previously independently checked, not re-queried by this script",
    "Observed file preservation does not exclude hostile replace/restore races",
    "Procedure restricts inputs by exact paths; no OS-enforced sandbox",
    "No economic or replay authority is conferred by this sign-off"
  ]
}
```

This dictionary is a schema declaration copied from the D.14 sign-off writer, NOT the actual original sign-off bytes. That output exists only on the owner's Mac, has never been read during E.1/E.2, and remains outside this task. Tests must construct unrelated FABRICATED sign-off and publication identities, not claim this dictionary's serialization is a verified original sign-off or self-signing authority.

## 3. Implementation scope

Implement a private pure, no-I/O sign-off validation seam in src/backtest_badger/genuine_minute_publication.py (and matching tests/test_genuine_minute_publication.py) that:

1. Accepts exact in-memory bytes for the D.14 sign-off, independently retained sign-off fingerprint, and a previously independently parsed _VerifiedPublication plus its external pins. Require the bytes to match the external sign-off SHA/length BEFORE parsing. No paths, loaders, network, callbacks, sign-off writer, environment flags, permissions switches or public CLI. Keep original _parse_verified_publication behaviour stable unless changing it is essential to avoid a bypass; document any signature changes.
2. Rejects duplicate JSON keys, noncanonical/no-newline JSON, unexpected keys, incorrect scalar types (especially bool/int confusion), NaN/Infinity/overflow, extra/missing/inconsistent files, wrong status/flags/kind/source, altered scientific counts and inconsistent old commit/CI claims. Use exact external publication identities; never derive trusted pins from candidate data. Check all three published file identities against BOTH the supplied external fingerprints and the publication manifest.
3. Reconcile original_execution_commit/reviewed_ci_run_id to the original verification integrity.json approval, not to the new E.2 implementation commit. Confirm both the upstream manifest and retained sign-off say verification-only and economics false. Bind the sign-off's publication to the one frozen relative identifier, without opening that path. Treat checks and limitations as descriptive attestation statements from the fixed D.14 writer, not authority to perform those actions. Their required entries can be validated as a strict frozen declaration; no fuzzy acceptance of substitute strings.
4. Distinguish fingerprint continuity from validated sign-off content. A caller-supplied matching fingerprint is insufficient if the sign-off body was not independently checked. The existing closed public route replay_genuine_minute_historical(*, approval) MUST continue to raise PermissionError before inspecting its argument or touching any path. Neither validated sign-off nor a verified record grants strategy permission.
5. Avoid re-validating original native source archives or performing any simulated trades as part of sign-off parsing. Do not call _replay_minute_core from the new sign-off validator. The existing private pure replay is unchanged and remains separately un-authorised. If necessary, add a private wrapper type that carries the validated sign-off and original publication evidence; its construction must NOT grant authority.
6. Keep code minimal and maintainable, prefer existing strict parsers/identity utilities without weakening their bounds. Never introduce a second monetary engine, a new open allow_genuine flag, or fixture relabelling. Preserve parity/integrity limitations: this validates a historical sign-off document, not source bytes again, not signatures anew, not fresh CI, and not profitability.

## 4. Fabricated tests and preservation

Add focused tests for the complete schema, canonical roundtrip, exact byte/length/hash verification, original-commit-versus-new-commit separation, the three companion identities, false flags, scientific counts, and sign-off/manifest/integrity agreement. Negative tests for every altered required field, omitted/extra keys, wrong lists, reordered/duplicate keys, bool in place of integer, nonfinite numbers, mismatched fingerprints, caller self-hashed fake records, and injected pre-parsed objects. Keep existing E.2 pure full-year parity and synthetic-only gate tests passing. All test records must be deliberately fabricated and not derived by reading originals.
Before tests or lint, install offline access guards as in the existing E.2 guide; no cache writes to the repository, original artifacts, home evidence, or outside designated test temporaries. Run focused, scoped and full regression as feasible, report exact commands and real observed counts. Check Ruff lint and format. Use only scoped status/diff inspection. Do not change the frozen accounting core or anything unrelated. If an assumed schema detail cannot be implemented without inspecting the real file, stop and state what needs independent owner permission instead of inventing it or opening the file.

## 5. Deliverables and final report

* Minimal code + tests, optionally update docs/stage-04b2e2-publication-replay-bridge.md, architecture, roadmap, handoff.
* Add docs/stage-04b2e3-independent-signoff-contract.md recording the exact pure contract, accepted evidence, negative tests, preserved restrictions, results, and outstanding owner-controlled execution steps.
* Archive this substantive request (excluding any unrelated session text) in prompts/stage-04-paper/018-independent-signoff-contract.md.
* Produce an explicit summary: HEAD, files touched, tests/CI distinction, preservation check, procedural deviations, and what remains closed.
* Stop without commit, push, original sign-off read, economic runner, execution, output publication, or access to original data. Any next step involving reading the four original files or running 2024 economics requires a separate owner decision and pinning of the new implementation/CI.

FABRICATED TESTS ONLY · ORIGINAL SIGN-OFF/PUBLICATION UNREAD · GENUINE REPLAY NOT EXECUTED · ECONOMIC PUBLICATION NOT AUTHORISED.

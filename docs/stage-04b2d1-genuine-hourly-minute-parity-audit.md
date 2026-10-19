# Stage 4B.2D.1 — Authorised source-access gate

The owner authorised implementation and synthetic testing of a separate genuine
native-hourly/native-minute opening-price auditor, followed by **one** intentional
local audit only after all implementation, review and preflight gates pass.
The substantive instruction is archived in
[the scoped prompt](../prompts/stage-04-paper/007-genuine-native-hourly-minute-parity-audit.md).
Unrelated browser/session material trailing the attachment is excluded.

Starting `main` was clean at `38a27902542f94d47c620e3516cfff53b32be058`:
`git rev-parse HEAD` matched and `git status --porcelain=v1 --untracked-files=all`
returned no entries. Baseline CI run `39133544586` (1,575 passed, 1 skipped) was
supplied by the owner; it is not CI evidence for these uncommitted changes.

Phase A must not open genuine artifacts. Use fabricated evidence, forbid genuine
artifact reads and network/database connections, preserve protected files, and
pass focused tests, the locked full offline suite, Ruff and whitespace checks.
Review code, pin its bytes, and freeze the worktree throughout Phase B.
PostgreSQL tests skipped without a disposable test DSN are **not passes**.

Only these two existing directories may be opened during Phase B:

- `artifacts/execution/binance-1h-2024-v1/`
- `artifacts/execution/binance-1m-2024-v1/`

The sole output is the exclusively created, previously absent ignored directory
`artifacts/audits/stage-04b2d1-native-parity-v1/`. Existing directories, symlinks,
wrong paths, incomplete releases, changed code, changed protocols or wrong pins
block the audit. No replacement release, repair, download, overwrite, resume or
alternate output is permitted. Preflight failures before reservation leave no
new audit directory; later failures retain incomplete evidence and no final
manifest. Exceptions propagate to the operator.

The [implementation/report guide](stage-04b2d1-genuine-price-parity-audit.md)
records the explicit API, predeclared comparison, authoritative identities,
operator invocation, validation and eventual genuine outcome. Price discrepancies
are valid negative findings and must never be hidden by changing tolerances or
inputs. Source-validation failure leaves genuine parity indeterminate.

This authorisation excludes forecasts, other artifacts or holdouts, strategies,
accounts, returns/P&L, economic publication, databases, providers and deployment.
The next gate is separate owner approval to design and test a genuine
forecast/minute replay adapter, followed later by explicit approval for actual
strategy calculation and immutable economic publication. Parity permits neither.

Completed gate: Phase A passed (72 focused; full suite 1,465 passed and 183
PostgreSQL skips). The single authorised genuine invocation completed with zero
exact mismatches across 17,568 pairs; both full source releases authenticated.
See the report guide for externally retained output hashes and preservation
evidence. No genuine economic calculation or follow-on integration occurred.

# CI temporary-storage exhaustion

## Diagnosis

The working tree was clean before this repair. Both Actions job logs were read:
[40191098358](https://github.com/owencrew/backtest-badger/actions/runs/40191098358)
and [40216243848](https://github.com/owencrew/backtest-badger/actions/runs/40216243848).
Both collected 3,134 tests and ended with **91 failed, 2,797 passed, 88 skipped,
158 errors** after approximately 38 minutes. Installation and Ruff passed;
E.5/E.5c/E.5d were skipped after pytest failed. The two website commits did not
change the existing scientific tests.

The logs confirm `OSError: [Errno 122] Disk quota exceeded` under
`/tmp/pytest-of-runner/pytest-0`. The first reported setup error is
`test_full_native_signed_test_route`, writing the synthetic minute CSV in
`test_genuine_minute_verification_operator.source_fixture`, imported by the
runtime tests. Subsequent failures include assertions, missing failure reports
and fixture errors; they must be assessed by rerunning, not dismissed by type.

Accumulation of successful tests' temporary outputs is a contributing mechanism.
Pytest defaults to retaining all function directories and three sessions. These
failures occurred in **pytest-0**, so retaining previous sessions is not required
to explain the problem. Exact exhausted byte/inode/project quota and available
space at failure were not logged. GitHub documents 14 GB of storage for standard
[Linux hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners);
this is not a measurement of free `/tmp` capacity in these jobs. The failed logs
identify Ubuntu 26.04. Ubuntu's [release notes](https://documentation.ubuntu.com/release-notes/26.04/summary-for-lts-users/)
confirm that `/tmp` is now tmpfs by default. A directly measured
[runner-image issue](https://github.com/actions/runner-images/issues/14777)
reports approximately 7.8 GB, `usrquota`, and the same EDQUOT error on 26.04,
while 24.04 uses the root disk. This is strong evidence of the mechanism here,
not a retrospective measurement of either failed job's quota. New diagnostics
record block/inode availability and the `/tmp` mount on the next run.

## Change

Only `.github/workflows/ci.yml` changes execution:

- Pin the standard free runner to `ubuntu-24.04`, avoiding 26.04's RAM-backed
  `/tmp`. Guarded launchers explicitly use `/tmp`, so setting `TMPDIR` alone
  cannot cover the full suite. Reassess this pin before a future OS upgrade.
- Run `uv run --locked pytest -o tmp_path_retention_policy=none`.
- Record `df -h`, `df -i` and `findmnt -T /tmp` before pytest.
- Always record block/inode availability and largest temporary directories after
  pytest. This diagnostic-only step is best effort because system-owned `/tmp`
  directories may be unreadable. Test failures still fail the job.

The locked pytest **9.1.1** implementation and a two-test probe show that
`none` cleans up at session exit, rather than between tests. This preserves
fixture lifetime but does **not** bound peak storage within one session; the
runner pin avoids the tmpfs ceiling. See the actual
[9.1.1 implementation](https://github.com/pytest-dev/pytest/blob/9.1.1/src/_pytest/tmpdir.py).

The alternative `failed` was tested and rejected. It deletes passing `tmp_path`
directories during teardown, while some scientific I/O guards are still active.
For example, `test_genuine_minute_price_parity.offline_boundary` interprets
`shutil.rmtree`'s relative `os.open("artifacts", dir_fd=...)` as a protected
checkout path. The exploratory full run produced 86 teardown errors. Switching
to session-end cleanup preserves those guards without modifying frozen tests.
There is no dependency change or custom cleanup hook. Splitting tests into jobs
is unnecessary if the pinned runner's disk capacity is confirmed sufficient.

The override is CI-only. Module/session `tmp_path_factory` directories remain
available throughout the session. No test selection, scientific assertion,
production code, frozen evidence, PostgreSQL service/environment or guarded
launcher changes. All **3,134** collected cases remain included. The baseline
88 skips are 87 E.5 cases intentionally executed by the mandatory isolated
launcher and one existing Docker dump/restore test requiring
`BADGER_D2A_TEST_CONTAINER`; this repair introduces no skips. E.5 (87), E.5c (55)
and E.5d (153) remain required sequential steps with no optional failure handling.

## Storage consumers

Ten-second `du` samples in the final Linux run reached **7.22 GiB** total `/tmp`
and **2.84 GiB** in the pytest tree. Sampling can miss brief peaks. Session-end
cleanup removed the pytest tree; direct operator fixtures retained **4.38 GiB**.
The separately validated E.5d launcher retained another **4.38 GiB**. In CI's
sequential execution, those two trees alone would occupy approximately
**8.76 GiB**: retention alone cannot reliably fit the reported 26.04 tmpfs limit.
Sizes below are sampled allocated sizes; hard-link attribution depends on
traversal order, and per-directory maxima must not be summed as a peak.

- `test_genuine_minute_inputs.fabricated` (about 99 MiB): a complete 2024 minute
  grid for both symbols (1,054,080 rows); `test_full_stream_end_validation` copies it for excess
  and truncation cases.
- `test_genuine_minute_price_parity.full_minute_csv` (about 95 MiB): another
  full minute grid;
  `test_stream_final_hash_size_and_eof[extra]` copies it.
- `test_genuine_minute_verification_operator.source_fixture` (about 141 MiB per
  sampled source tree): full synthetic monthly ZIP/checksum archives plus native minute CSV; reused/imported by runtime
  tests, with module-scoped source directories. Case copies use hard links, so
  summing apparent file sizes would overstate their physical storage.
- `test_minute_execution_data.published` (about 275 MiB): two full synthetic
  publications, each
  with 24 ZIP/checksum pairs and the processed minute CSV.
- `test_local_historical_backtest.full` and
  `test_paper_historical_evaluation.published`: full-year fabricated replay and
  reporting outputs retained in module fixture directories (about 87 MiB and
  37 MiB respectively).
- `test_genuine_backtest_operator.scratch` and
  `test_e5d_rehearsal_preparation.scratch`: direct `tempfile.mkdtemp()` directories,
  outside pytest retention; operator scratch directories total 4.38 GiB and are
  the largest consumer. The E.5d launcher owns its separate 4.38 GiB tree.
  This fix does not delete those directories early or change their guards.
- `test_economics` retains a roughly 105 MiB deterministic-artifact test output
  and repeated roughly 14 MiB provenance-validation copies.
- PostgreSQL integration fixtures create uniquely named disposable databases and
  drop them in `finally`; the final check found zero generated databases left
  and only about 55 MiB in the disposable PostgreSQL data directory.

## Validation and limits

Validation used disposable local Ubuntu 24.04 ARM64 and PostgreSQL 17 containers,
CPython 3.12.3, uv 0.13.0 and the locked dependencies (pytest 9.1.1). The database
DSN matched CI's localhost maintenance-database contract. Docker Compose 2.40.3
was installed for offline configuration validation, without exposing a Docker
socket to the test container. This differs from GitHub's x86-64 VM and quota.

- Ruff lint and formatting passed locally and in Linux.
- `actionlint` 1.7.12 accepted the modified workflow.
- The two-test retention probe confirmed session-end cleanup with `none`.
- A focused Linux check passed the previously failing teardown-guard case and
  both offline Compose configuration tests after the environment was corrected.
- Final full suite: **3,134 collected; 3,045 passed, 88 existing skips, one
  failure** in 1,184.71 seconds. No disk-quota or teardown errors. All 249 unique
  failed/erroring cases from each original CI log passed in this run.
- **E.5: 87/87; E.5c: 55/55; E.5d: 153/153 passed, zero skips.** These launchers
  ran with the locked virtual environment's Python and unchanged `-I -S -B`
  flags in a separate disposable Ubuntu 24.04 container while the main suite
  finished. CI still invokes the original uv commands sequentially. The local
  run therefore does not constitute a green sequential CI job.
- `git diff --check` passed. No scientific source or test files changed.

An unrelated local timestamp-sensitive test was investigated rather than
classified as a storage failure: `test_symlink_traversal_and_replace_races`.
Immediate same-length writes sometimes have identical mtime/ctime on the Docker
filesystem. Repeated checks failed 4/5 times with default `all` and 3/5 with
`failed`; a macOS check passed. It failed again in the final `none` run
at line 912 (expected changed-file
rejection did not occur), despite abundant storage. It was not among the
original CI failures. No assertion was weakened to hide this sensitivity.
The exploratory run's other two call failures were missing Docker Compose,
subsequently installed and retested. Its 86 cleanup errors caused `failed` to be
rejected. Final validation is a fresh full run with `none`, without concurrent
pytest processes sharing its temporary root.

A GitHub-hosted run after owner review and push is still required to establish
actual runner headroom and green CI. A local container does not reproduce the
hosted runner's storage quota or image. No commit, push, deployment, Lightsail or
production database access was performed.

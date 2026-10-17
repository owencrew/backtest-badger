# Stage 4B.2C — Isolated minute source engineering

Implemented for review on 2026-10-17. **Synthetic ZIP/CSV fixtures only. No genuine
2024 one-minute acquisition, source authentication/freeze, historical artifact
access, minute simulation or economic report.** The separate
[minute protocol is DRAFT](stage-04b2c-minute-execution-protocol-DRAFT.md), not
approved. Stage 4B.2B synthetic integration is accepted; its hourly contracts and
genuine-data gates remain unchanged.

## Verified checkout and scope

Starting `main` was clean at `fe6035f4bda09a1bbeb59afd8b0d1899463ae4f4`.
Expected `31fb40fc88d93a9eeed578412342359fe222def5` is its parent. The only intervening
change is `fix(ci): fetch full history for protocol revision checks`, two lines in
`.github/workflows/ci.yml`. No pull, reset, rebase, commit, push or deploy occurred.
No remote-current-state claim is made.

Read the repository/prompt guidance, architecture/roadmap/handoff, Stage 2C and
Stage 4B.2/2A/2B guides, source validators/loaders, historical engine/evaluation/
publication and relevant tests. Existing archive limits (744 rows, 2 MiB ZIP,
8 MiB CSV), native 1h/4h candle validation and hourly replay remain unchanged.
The new standard-library module imports no research, database or hourly modules.
No dependencies, schema, framework, CLI or worker were added.

## Source evidence, identities and trust

The [official Binance public archive documentation](https://github.com/binance/binance-public-data)
was read on 2026-10-17 via GitHub only. It documents monthly Spot klines, 12 native
columns, `.CHECKSUM` sidecars, later archive replacements and the Spot timestamp
change to microseconds from January 2025. Its sample download structure supports
the fixed URLs below. No `data.binance.vision` request or genuine checksum lookup
was made, and documentation is not proof that the intended 24 archives are
currently accessible or conform to these limits.

For BTCUSDT and ETHUSDT, each month January–December 2024:

```text
https://data.binance.vision/data/spot/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-2024-{MM}.zip
https://data.binance.vision/data/spot/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-2024-{MM}.zip.CHECKSUM
```

Exactly 24 archive/sidecar pairs, ordered by symbol then month. There is no
symbol discovery, arbitrary date range, alternative frequency or gap option.
Source identity comes from the fixed request, exact sidecar filename and exact
ZIP member filename; native CSV itself has no symbol column. This establishes
consistency of supplied evidence, not a cryptographic proof of market identity.

A sidecar must contain one 64-hex SHA-256, GNU text/binary checksum separator and
exact ZIP basename, with optional LF/CRLF. Preserve original sidecar bytes, hash
them separately, and compare the actual ZIP SHA-256 before parsing. Sidecars are
not signed attestations; coordinated forgery of all local evidence is outside
this trust boundary. An independently retained manifest hash prevents silently
accepting a different self-consistent local release. A later provider ZIP **or
checksum-body** change requires review/new version, never automatic replacement.

## Native validation and bounds

2024 timestamps must be 13-digit **milliseconds**, with open equal to the exact
expected UTC identity and inclusive close equal to open +59,999 ms. The half-open
year ends at 2025-01-01 00:00, but that endpoint is never a source row. Counts:

| Calendar month | Rows per market |
| --- | ---: |
| January, March, May, July, August, October, December | 44,640 each |
| April, June, September, November | 43,200 each |
| February (leap year) | 41,760 |
| Full 2024 | 527,040 |
| Both markets | 1,054,080 |

All twelve fields are validated: open time, O/H/L/C, base volume, inclusive close
time, quote volume, trade count, taker base/quote volumes and numeric ignore field.
ASCII fixed-point unsigned decimals of at most 80 characters are parsed exactly
as Decimal; OHLC must be positive with low ≤ open/close ≤ high. Volumes are
nonnegative, taker volumes cannot exceed totals, and trades are unsigned integer
≤ 2^63−1. The ignore field is validated as a nonnegative decimal but not used.
No exponent syntax, signs, whitespace, underscores, NaN/Infinity, BOM, invalid
encoding, timestamp overflow, header, malformed/multiline row or partial month.
ASCII is the numeric-only subset of UTF-8 expected here. Unsupported source
formatting fails for review rather than being normalised permissively.

Duplicate, missing, unordered, off-grid, market/month-crossing, extra and
nonstandard identities fail, including at leap-day/year boundaries. No REST,
daily archives, interpolation, gap dropping, later-opening substitution, hourly
aggregation or synthetic replacement of genuine gaps is supported.

| Resource | Independent minute limit |
| --- | --- |
| ZIP body | 16 MiB |
| Expanded CSV | 32 MiB, checked in header and while streaming |
| Sidecar | 1 KiB |
| Manifest read | 128 KiB |
| CSV physical line | 2,048 bytes |
| Native rows | Exact month count, maximum 44,640 |
| Expansion ratio | At most 200:1 |
| ZIP directory | One entry; central directory at most 4 KiB |
| Decimal field | 80 characters, fixed point only |

These conservative engineering caps accommodate roughly 45,000 native rows, but
have **not** been calibrated on genuine 2024 data. A legitimate source exceeding
any cap stops for review; never silently increase a limit during acquisition.
ZIP32 only, stored/deflated compression, regular expected CSV at archive offset
zero. Reject multiple/duplicate/nested/path-traversal entries, symlinks, encryption,
unsupported compression, multi-disk/ZIP64, archive comments/trailers, CRC mismatch,
truncation and decompression errors. Inspect the fixed-size terminal directory
record before `ZipFile` allocates entry metadata. Never extract archive members.

The parser streams bounded physical lines and creates only one row's OHLCV
values at a time. It returns a compact opening-only fragment for one fully
validated month (at most 7,499,520 bytes), then releases that month after retention.
Publisher and loader never hold all ZIPs, full-year OHLCV rows or a million
Python record objects together. Peak payload memory is bounded by one ZIP,
one opening fragment and bounded parser/read buffers (with transient byte copies),
not the year length. The output is streamed to disk; its maximum is 177,085,440
bytes plus the header under the field limits. All full native validation fields
remain available in retained raw ZIPs, not in future signal inputs.

## Callable APIs and authorisation boundary

In `src/backtest_badger/minute_execution_data.py`:

```python
MinuteRequest(symbol, month)  # only fixed 2024 BTCUSDT/ETHUSDT identities
minute_requests() -> tuple[MinuteRequest, ...]
coverage() -> dict
verify_minute_archive(request, zip_bytes, checksum_bytes, observed_at)
    # -> (opening_only_csv_fragment: bytes, source_metadata: dict)
prepare_minute_execution_data(destination, *, downloader) -> str
    # external manifest SHA-256; downloader is REQUIRED
load_minute_execution_data(directory, *, expected_manifest_sha256) -> dict
    # independent offline replay; metadata only, no price-object collection
download_minute_archive(request) -> (zip_bytes, checksum_bytes, observed_at)
    # FUTURE AUTHORISATION ONLY; never used with real HTTP in this stage
```

The publisher accepts a downloader returning supplied bytes and an aware UTC
full-ZIP acquisition timestamp at/after month end. It does not assume timestamp
authenticity. `observed_at` is retrospective archive receipt, not price publication,
forecast issuance, bid/ask observation or fill time. Opening-only fragments contain
no acquisition wall clock; metadata retains it explicitly.

No default downloader or CLI exists. The optional future HTTP utility accepts
only exact fixed-plan URLs, with matching byte limits, no query strings, proxies,
credentials, cookies or redirects (including same-host redirects). HTTPS status
must be 200 with the exact requested response URL; enforce declared and streamed
lengths and reject truncated bodies. At most three attempts, 15-second socket
timeout, 60-second monotonic read deadline per attempt, 1/2-second retry sleeps;
retry only transport failures and HTTP 500/502/503/504. All errors omit raw HTTP
exception text. Blocking operations can exceed the deadline by the socket timeout;
DNS/OS scheduling are not a certified hard process deadline. There are at most
48 successful retrievals, 144 attempts, no recursive retry/discovery. HTTP tests
use mocked responses only; transport accessibility is untested.

For synthetic verification, execute only:

```sh
env -u BADGER_TEST_ADMIN_DSN uv --cache-dir /tmp/badger-4b2c-uv-cache run \
  --locked --offline --no-sync pytest -q tests/test_minute_execution_data.py \
  -p no:cacheprovider
```

The tests' `synthetic_download` fabricates complete native-shaped monthly rows,
ZIPs and matching sidecars. Pytest temporary destinations exercise both publisher
and loader. Do not substitute `download_minute_archive` into that example without
a separately authorised acquisition task.

## Manifest, publication and independent replay

Dataset contract: `binance-1m-2024-v1`; processed format: `minute-opens-csv-v1`.
Future proposed genuine path: `artifacts/execution/binance-1m-2024-v1/`.
That path was neither created nor inspected. Only pytest temporary outputs exist.

```text
raw/{SYMBOL}-1m-2024-{MM}.zip
raw/{SYMBOL}-1m-2024-{MM}.zip.CHECKSUM
minute_opens.csv
manifest.json                 # last, only after retained-source replay
failure.json                  # best effort on failure, never a valid release
*.partial                     # possible interrupted exclusive writes
```

Processed CSV is ASCII/LF with header
`symbol,open_time_ms,open,source_sha256`, ordered symbol/month/minute. The opening
string preserves source precision/trailing zeros, without Decimal-context rounding.
Each row links to its month's source hash; the manifest maps that hash to URL,
market/month and exact raw evidence. There is no high/low/close/volume field.

Canonical sorted-key, indented JSON manifest records version, status
`validated_source_structure_not_approved_for_evaluation`, checksum-attestation
limitation, exact full coverage, archive count 24, source records, output
name/size/SHA-256 and this isolated implementation's SHA-256. Each source includes
symbol/month/1m, ZIP and sidecar URLs/hashes/sizes, expanded CSV size, exact count,
UTC observed time, retrospective observation kind and complete-validation status.
The external manifest digest is returned to the caller, not recursively embedded.
No authentic release pin is declared in this repository.

Reserve a new destination using exclusive `mkdir`, with an existing parent;
refuse files, symlinks and directories even if empty. Raw evidence uses exclusive
partial creation, fsync and atomic hard links. Stream processed output similarly.
Re-read all retained evidence, reverify checksums/CSV and compare every reproduced
opening byte directly to the processed file before publishing the manifest last.
The offline loader repeats those checks with the required external manifest pin,
canonical manifest schema, unchanged implementation hash and bounded reads.
Even a rehashed processed price fails against the raw archive reconstruction.
No missing source, malformed metadata, source swap, failed directory or symlinked
file can become a completed release.

Same source bytes/code produce identical processed bytes across fresh destinations.
Identical observed metadata also produces identical manifests; changed acquisition
times change the manifest hash but not the scientific opening data. This is an
explicit separation of source content from retrospective receipt metadata.

Failures retain available raw/partial files and a best-effort safe `failure.json`
with current source/download hashes/time and validated source metadata. No final
manifest survives a handled failure, including an error just after manifest
linking. A hard kill or disk failure may prevent failure recording; absence of a
manifest still means incomplete. Investigate and use a **new destination**;
there is no resume/overwrite or repair-in-place. Exclusive creation is accidental
overwrite protection, not adversarial concurrent-filesystem security, backup or
power-loss certification. Filesystem hard-link support is required.

## Checks, preservation and next gate

Tests exercise complete synthetic January, leap-February and December; two
full-year publications; exact source/sidecar lineage; 13-digit timestamp/close
arithmetic; malformed numerics/encoding/rows; missing/extra/reordered identities;
ZIP directory/name/type/CRC/DEFLATE/ratio/byte limits; mocked HTTP retries,
redirects, size/deadline failures and exact URL allowlisting; exclusive retention,
manifest-last ordering after full replay, interrupted writes/downloads and fresh
recovery. Rehashed price or source metadata changes still fail independent replay;
canonical JSON comparisons also reject float counts masquerading as integers.

Two new destinations preserve identical raw and processed source bytes. Their
different supplied acquisition clocks change only metadata; normalising that
clock reproduces the exact manifest bytes. Tests forbid genuine network/database
connections and artifact opens; no strategy or economic calculation is added.
The unchanged full suite includes the hourly/4h source, replay and reporting
regressions. No isolated PostgreSQL server or remote CI was run; skips are not
passes. No existing real artifact was inventoried, opened or hashed.

**Final focused verification:** 157 tests passed in 64.84 seconds. Ruff lint
passed; all 137 Python files passed formatter checking. Tracked and new-file
whitespace checks are clean. The final complete locked suite passed **1,305 tests
with 183 isolated-PostgreSQL tests skipped** in 146.60 seconds. The baseline
1,148 passing cases remain passing, with 157 new minute-source cases.
`BADGER_TEST_ADMIN_DSN` was unset explicitly; no database or remote CI execution
is claimed.

Executed commands (installed tools, locked dependencies, offline/no sync):

```sh
uv --cache-dir /tmp/badger-4b2c-uv-cache run --locked --offline --no-sync ruff check . --no-cache
uv --cache-dir /tmp/badger-4b2c-uv-cache run --locked --offline --no-sync ruff format --check . --no-cache
env -u BADGER_TEST_ADMIN_DSN uv --cache-dir /tmp/badger-4b2c-uv-cache run --locked --offline --no-sync pytest -q tests/test_minute_execution_data.py -p no:cacheprovider
env -u BADGER_TEST_ADMIN_DSN uv --cache-dir /tmp/badger-4b2c-uv-cache run --locked --offline --no-sync pytest -q -p no:cacheprovider
git diff --check
```

Before/after SHA-256 checks cover 127 pre-existing tracked implementation, test,
document, prompt and dependency files. **124 remain byte-identical**; only the
three authorised status documents changed. This includes unchanged archive/candle
limits, hourly loader/replay/evaluation/publication, all old tests, earlier prompt
archives, `uv.lock` and `pyproject.toml`. Frozen protocol hashes remain:

| Protected document | Unchanged SHA-256 |
| --- | --- |
| Historical validation protocol | `b781ddef6d3d26f1dc6d0dcf0336b2bce7ba314b062b87e85fdaff7271839a2b` |
| Stage 4A technical specification | `25412bf4f0e83f848adb09d42d16f39e0c46a55a339d525fd576f1fa85dff399` |
| Stage 4A prospective protocol | `f4561da8db29a180b9abc7b131a6455cefca3c6c44318b268ad5428769273cd9` |

This is code/document preservation evidence, not an audit of real source bytes.
All Stage 4B.2C changes remain local and uncommitted.

The exact substantive prompt is archived at
[`005-minute-execution-design-and-source-engineering.md`](../prompts/stage-04-paper/005-minute-execution-design-and-source-engineering.md).
Unrelated browser/session material following its final sentence in the pasted
attachment was excluded; only the substantive request was preserved.

Before any real download, the owner must finalise the separate protocol and
approve the reviewed implementation/limits, then **separately authorise** exactly
these 24 monthly ZIP/sidecar pairs, the code revision and a named fresh destination.
Only a later successful acquisition/offline replay can supply exact pins for
owner review and freeze. Source publication is not approval for replay or economic
evaluation. Minute replay, parity-audit access to old inputs, original forecast
loading and real evaluation each remain subject to the draft's separate gates.
No Stage 4B.2D, holdout, genuine Stage 3, production or public-dashboard work.

# Stage 4B.2C.3 — Frozen historical minute source pins

**Status: verified source release.** Source identities frozen on 2026-10-18 under the owner’s explicit metadata-only review authorisation. No discrepancy was found. Any subsequent discrepancy blocks use and requires final owner review; never replace data or update pins merely to make a check pass.

This document records the independently verified local release `binance-1m-2024-v1`. It does not approve historical evaluation. The unchanged local manifest retains status `validated_source_structure_not_approved_for_evaluation`.

## Protocol, code and acquisition evidence

- Approved protocol: [minute execution protocol](stage-04b2c-minute-execution-protocol.md), version `historical-minute-execution-v1`, owner-approved 2026-10-17.
- Protocol SHA-256: `c8e2d3134f4e475da5bdb589e3344550bf08a8d17fdb2e7a18457f3b91ed898b`.
- Protocol Git blob SHA-1: `006a23948027ce7cf30ac8553cc6438316a63b29`.
- Acquisition and verification checkout: branch `main`, revision `f6e726482d770827c80d72330dfe217fd4261e95`.
- Reviewed implementation origin: `98a99bde7380cbfdc0efa819abb68d37f87e7e16`. Successful CI run `39055403823` is recorded in the approved protocol and acquisition signoff; remote CI was not queried or rerun here.
- Implementation: `src/backtest_badger/minute_execution_data.py`.
- Implementation SHA-256: `84cb5f7a8c3fcfcc6b7b488cdaf22bd6e3fb8c369fdf8cf12c1435fc2da256c2`.
- Implementation Git blob SHA-1: `499ada2582ccaed71de64aa14537a0ff1de50a8b`.
- Acquisition completed 2026-10-18. Existing signoff: `binance-1m-2024-v1-acquisition-signoff.md`, stored outside the repository in the acquisition chat’s visualization directory, chat ID `01a14d6f-41b9-7780-963c-5af754611c82` (“Acquire Binance 2024 minute data”).
- Reviewed signoff SHA-256: `6e2d214d720f4e146b0f731b3a3ca13c173f52685242de752b6392e4516d6d19`.
- Independent verification completed at `2026-10-18T05:45:38.056945+00:00` (UTC).

The protocol and engineering guide preserve their earlier approval-stage statements. This later source-freeze record reflects the separately authorised acquisition and verification, without editing those frozen documents.

## External release identities

Local directory: `artifacts/execution/binance-1m-2024-v1/`.

| File | Exact bytes | SHA-256 |
| --- | ---: | --- |
| `manifest.json` | 19749 | `673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127` |
| `minute_opens.csv` | 107002277 | `37878071a8d5b40685ef2b9951290f480eeba63aec60f410a55cca8d54168233` |

The manifest pin above was supplied externally by the owner, matches the acquisition signoff, and was passed literally to the existing offline loader. It was not derived from an untrusted replacement manifest and then accepted. Processed format: `minute-opens-csv-v1`; header: `symbol,open_time_ms,open,source_sha256`.

| Market | Native minute references | Missing timestamps | Duplicated timestamps |
| --- | ---: | ---: | ---: |
| BTCUSDT | 527040 | 0 | 0 |
| ETHUSDT | 527040 | 0 | 0 |

Coverage is exactly `[2024-01-01T00:00:00Z, 2025-01-01T00:00:00Z)` at 60-second intervals: 1,054,080 rows total, plus one CSV header. The first opening is `1704067200000` ms; the last is `1735689540000` ms. Each processed row’s source SHA-256 matches its market/month archive. Monthly counts are 44,640 for 31-day months, 43,200 for 30-day months and 41,760 for leap-February.

## Retained source identities

Exactly 24 ZIPs and 24 original sidecar bodies, plus the two files above (50 files). ZIP bytes total 49,948,389; sidecar bytes total 2,112. All sizes below are bytes. CSV size is the expanded native ZIP member size. Local names are `raw/{SYMBOL}-1m-{YYYY-MM}.zip` and the same name plus `.CHECKSUM`; the sole ZIP member is `{SYMBOL}-1m-{YYYY-MM}.csv`.

Each row below was compared field by field against the acquisition signoff and pinned manifest, with both local file hashes and sizes independently recomputed. Original URLs are recorded associations; no new provider request was made. Receipt times are retained acquisition metadata, not independently authenticated clocks.

| Market | Month | ZIP SHA-256 | Sidecar-body SHA-256 | ZIP bytes | Sidecar bytes | Native CSV bytes | Rows |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| BTCUSDT | 2024-01 | `40b78258091a468f8756843f207f5913eafc1d6e756c40a78711320d93fa5e75` | `58937db8d3f1d6aa0f5d8e7b8d091bb3db240b8198416f7527ba7590510bf760` | 2169570 | 88 | 6699071 | 44640 |
| BTCUSDT | 2024-02 | `431132e0db8b9fe6e5c93c8e9ba3ae37dbcfa0edcdd57618b1b78ac18d14be79` | `e91c7f4bfca6258f4cd4fb637d3af87438f97be8866ec6d12ca46b6336c2e69e` | 2013843 | 88 | 6267653 | 41760 |
| BTCUSDT | 2024-03 | `a9af86295eae839f1d072643c67eed7fcc47bb1d82c12ef312d041eec9511e7b` | `15b6a2de2d2455b2541ef8fe60c4130c11a032e7b1175f4e76621415f7e229d0` | 2221094 | 88 | 6755631 | 44640 |
| BTCUSDT | 2024-04 | `753040cbfaa72bf9b1fdc6253a3b521a9a174a664dfd0929a556be327b016bc6` | `b4c9a93eb29100151d112262aa16d98e3a76e4b1df82a6816750978cfa9704db` | 2120723 | 88 | 6493578 | 43200 |
| BTCUSDT | 2024-05 | `0f709143f66a09acc430d24a5f27f9accd52689c23ce10f2c0b6ea26997bfa8a` | `20af4b32e12ce08e075bebd03c9f43785210ef365d52f8f41c271566cfdf4bcf` | 2144250 | 88 | 6673369 | 44640 |
| BTCUSDT | 2024-06 | `90f4fc3f55918787848c71f4cd0f2f1a5851bbffaf6392e76e9ab555b7479d2b` | `ac279400992d5b462e365b4b2a446fe1875828236dfc9a5baaf4b94e6c5e265f` | 2018857 | 88 | 6436366 | 43200 |
| BTCUSDT | 2024-07 | `9cfd749fd2027a0c6f261bed607b49dd1256369fb41b784934544a3676f8162e` | `469a5311cc7501550dcf8be19171f4497a29ea05c68aa0663719e2ca496c125a` | 2141506 | 88 | 6677266 | 44640 |
| BTCUSDT | 2024-08 | `6a1cac2a5482132dc5a030534aa028e2becc560877f2b93b7add90194f576c42` | `11bf30d52752d4379c59936d2def177a3e3a4177d992baea8eab357afe904275` | 2164472 | 88 | 6680748 | 44640 |
| BTCUSDT | 2024-09 | `1e30f6091b05eeb7b0449735d749354b81ab429ab1449bae82a21e316db8eac3` | `c5b1dd7d721d16e8553793f36d2e739452a94fa337d862cd02bf782ad50dc13c` | 2049758 | 88 | 6454310 | 43200 |
| BTCUSDT | 2024-10 | `13f7f9f9bed652fd152422246cfbcaefa6223692c5c37fb3ca4e72f45501e607` | `6033dcdca22fe73c764c7794d2f42ef5e55230bee26f4ed7d8c7fef0149e744d` | 2121607 | 88 | 6677091 | 44640 |
| BTCUSDT | 2024-11 | `c30a63bd0e8a77f2d18a2a019272b907f29a84fd5378796cf9333b041edcb12b` | `f6cd2b7576d32f2775b620c241fb300c7f5c3b306c572447ce87f6489b8b3c89` | 2146495 | 88 | 6536845 | 43200 |
| BTCUSDT | 2024-12 | `58fef0b7c7abce7a0201efd04ed3732f236f607f3fcecf228fb8384cad1ae2c1` | `4beffd1c8c2ba68a487b26bf67e155fb5b01ce68944aa488b91a27f1105ab28c` | 2218893 | 88 | 6781290 | 44640 |
| ETHUSDT | 2024-01 | `2fb2c9b77365183f77e185de3578de2f3be5fefe433d7c0564f033f968d5e23c` | `0e694378724960bd240d1cba76ec9206358ea88879cdac57a9fa793805992632` | 2050101 | 88 | 6571961 | 44640 |
| ETHUSDT | 2024-02 | `ede3c9d4d47a5e9fdbc2e37b7086d97d4bcceec54316dd345fe0a1f8e648c443` | `e92038d1be6b863769910b057faeb7d61dfb132740fa6cd76d50b7c882fb820c` | 1922719 | 88 | 6154706 | 41760 |
| ETHUSDT | 2024-03 | `b63d885ef49b4e0f2a654ab02c5dcb502fb8abeb7300f3ebff4a33aadd3d4a82` | `dfba15085019d17ad6f462a3c2302943b06967f5ab2c10c3fc28d61aba727c30` | 2118386 | 88 | 6628255 | 44640 |
| ETHUSDT | 2024-04 | `9c6ef16ea4e0593ac4547d2f6c64c272d8f39806871473c4877885af47a67b88` | `71c070ea31e5b3c2eacd1bc4fb64bd96cd761ca3b3cee7bf127b32387b540ad2` | 2016825 | 88 | 6373889 | 43200 |
| ETHUSDT | 2024-05 | `4e09e26b7a2b352d24c25f6fc6cdd531d167d460a48226e4a8080413e0bb5e66` | `5953d3f43f44cb29fa1e01d0ff6de6b20320e24640bd4b934fbbf9ff21ef96e8` | 2054099 | 88 | 6559735 | 44640 |
| ETHUSDT | 2024-06 | `27040862f050687c6da296108dfcfb29e0500e0f9c8dd73669146e9e68a128c0` | `6e01734adca1f5ae7b232d445cfb5983e0095b0b71f87e548758df2ecd8b38b8` | 1945704 | 88 | 6319911 | 43200 |
| ETHUSDT | 2024-07 | `bda530d17235096c0e619edff1bef56154923b980d7a73406ea66114966ba0d2` | `02403cb8d029ec8e22e1c9a91758df9dc5c7d960454c6fa62cbeedddf5946db0` | 2050486 | 88 | 6547742 | 44640 |
| ETHUSDT | 2024-08 | `de64ff8c0e9bd0ff9ca7fc4015948fac94087c7293915a2a7f7bb47780e98e60` | `46ac08021a3d697bd50737a271b639a5d847c34a028c01d5995b0bdc2e9982c6` | 2065075 | 88 | 6562118 | 44640 |
| ETHUSDT | 2024-09 | `cb2ef3750b2608a871dcc6db479382e33b7d341f89ea17ed58b9fd44db88a793` | `77b9d6cefcd006a63bac9edea10e23bd7a9db4cffb47510807828731c40cb57a` | 1965720 | 88 | 6329447 | 43200 |
| ETHUSDT | 2024-10 | `99b11df1d79a2408d639cf512f1cfc6a4df4687de9146bd6271f9489ba15a8ba` | `4a06ff028ad303c2a70decdd0b672f00b9c8123358518bc5960a42fec53e917d` | 2039885 | 88 | 6556586 | 44640 |
| ETHUSDT | 2024-11 | `2c3e15ae6458707b07d2d8b51ad6634756153bc65f9bbb44d5ddb7ecdbccd0c6` | `a768f17f8ae610960f78ad1c2e5637957091fa99863c5b68dc4ddf4409fefeac` | 2062193 | 88 | 6436869 | 43200 |
| ETHUSDT | 2024-12 | `76e33a1db36f036c1e5866de2ebc54ab825522c801e1f9c487a85be781af4716` | `719aacd285c7e731fb53556ff5056e6b21f1d86fd8b95ae7ee3fd69d385389d5` | 2126128 | 88 | 6640453 | 44640 |

### Original URLs and retrospective receipt times

| Market | Month | ZIP URL | Sidecar URL | Observed at (UTC) |
| --- | --- | --- | --- | --- |
| BTCUSDT | 2024-01 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip.CHECKSUM) | 2026-10-18T05:17:44.911276+00:00 |
| BTCUSDT | 2024-02 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-02.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-02.zip.CHECKSUM) | 2026-10-18T05:17:48.416282+00:00 |
| BTCUSDT | 2024-03 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-03.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-03.zip.CHECKSUM) | 2026-10-18T05:17:50.298353+00:00 |
| BTCUSDT | 2024-04 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-04.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-04.zip.CHECKSUM) | 2026-10-18T05:17:53.810750+00:00 |
| BTCUSDT | 2024-05 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-05.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-05.zip.CHECKSUM) | 2026-10-18T05:17:56.825828+00:00 |
| BTCUSDT | 2024-06 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-06.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-06.zip.CHECKSUM) | 2026-10-18T05:17:59.894864+00:00 |
| BTCUSDT | 2024-07 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-07.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-07.zip.CHECKSUM) | 2026-10-18T05:18:02.476149+00:00 |
| BTCUSDT | 2024-08 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-08.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-08.zip.CHECKSUM) | 2026-10-18T05:18:05.526990+00:00 |
| BTCUSDT | 2024-09 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-09.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-09.zip.CHECKSUM) | 2026-10-18T05:18:09.011506+00:00 |
| BTCUSDT | 2024-10 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-10.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-10.zip.CHECKSUM) | 2026-10-18T05:18:12.063020+00:00 |
| BTCUSDT | 2024-11 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-11.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-11.zip.CHECKSUM) | 2026-10-18T05:18:15.137809+00:00 |
| BTCUSDT | 2024-12 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-12.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-12.zip.CHECKSUM) | 2026-10-18T05:18:18.651606+00:00 |
| ETHUSDT | 2024-01 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-01.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-01.zip.CHECKSUM) | 2026-10-18T05:18:20.947303+00:00 |
| ETHUSDT | 2024-02 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-02.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-02.zip.CHECKSUM) | 2026-10-18T05:18:24.515379+00:00 |
| ETHUSDT | 2024-03 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-03.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-03.zip.CHECKSUM) | 2026-10-18T05:18:27.568536+00:00 |
| ETHUSDT | 2024-04 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-04.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-04.zip.CHECKSUM) | 2026-10-18T05:18:30.646754+00:00 |
| ETHUSDT | 2024-05 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-05.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-05.zip.CHECKSUM) | 2026-10-18T05:18:34.179173+00:00 |
| ETHUSDT | 2024-06 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-06.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-06.zip.CHECKSUM) | 2026-10-18T05:18:37.676253+00:00 |
| ETHUSDT | 2024-07 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-07.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-07.zip.CHECKSUM) | 2026-10-18T05:18:41.210821+00:00 |
| ETHUSDT | 2024-08 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-08.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-08.zip.CHECKSUM) | 2026-10-18T05:18:44.261762+00:00 |
| ETHUSDT | 2024-09 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-09.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-09.zip.CHECKSUM) | 2026-10-18T05:18:47.662723+00:00 |
| ETHUSDT | 2024-10 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-10.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-10.zip.CHECKSUM) | 2026-10-18T05:18:51.194318+00:00 |
| ETHUSDT | 2024-11 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-11.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-11.zip.CHECKSUM) | 2026-10-18T05:18:54.778232+00:00 |
| ETHUSDT | 2024-12 | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-12.zip) | [CHECKSUM](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2024-12.zip.CHECKSUM) | 2026-10-18T05:18:58.275398+00:00 |

## Independent verification record

1. Confirmed empty `git status --porcelain=v1 --untracked-files=all`, expected branch/revision, and exact protocol/implementation SHA-256 and Git blob identities before writing this document. Read `AGENTS.md`, the approved protocol, engineering guide, loader implementation and existing acquisition signoff.
2. Rehashed all 50 local files using streamed SHA-256. Compared all 24 signoff rows against the manifest, including ZIP/sidecar hashes, sizes, native CSV sizes, counts, URLs and receipt timestamps. Verified exact expected file inventory and regular non-symlink evidence, with no failure record, partial or extra file.
3. Independently constructed the fixed two-market/twelve-month URL plan and calendar row counts. Parsed each sidecar’s checksum/filename association, compared its declared checksum to the actual ZIP digest, and checked the sole ZIP member name and expanded size.
4. Re-ran the unchanged `load_minute_execution_data` with the external pin below. It passed all native 12-field, ZIP/CRC, checksum, month-grid, resource-bound and canonical-manifest checks, and reconstructed every processed opening byte from retained ZIPs for exact comparison. This is a new verification run of the reviewed implementation, not an independently implemented native parser.
5. Separately streamed the processed CSV with the standard-library CSV reader. Compared every market/timestamp in order with the independently generated complete 2024 60-second grid; verified every row’s monthly source hash, exact monthly counts, header and EOF. This independently establishes zero missing, duplicated, extra or reordered processed timestamps.
6. Rehashed all 50 evidence files after verification and compared every pre-existing tracked file against its initial SHA-256 snapshot. All remained byte-identical.

Loader call executed in the locked environment, with bytecode writes disabled and no dependency installation:

```python
from backtest_badger.minute_execution_data import load_minute_execution_data

verified = load_minute_execution_data(
    "artifacts/execution/binance-1m-2024-v1",
    expected_manifest_sha256=(
        "673a60a2ea3a5c02b7f2e2543f70c27d6121b0ca81d8e24ebfbb84555011a127"
    ),
)
```

The temporary verification script used `uv --cache-dir /tmp/badger-4b2c3-uv-cache run --locked --offline --no-sync python -u`; it imported only the isolated minute source module and standard-library helpers. No downloader was invoked. Verification exited successfully.

## Limitations and remaining gates

Checks establish consistency with the externally pinned acquisition evidence, native source structure and processed-byte reproducibility. Sidecars are unsigned and are not signed Binance provider attestations. Local file/URL/ZIP-member consistency cannot independently prove market identity or protect against coordinated forgery of the original acquisition evidence. No fresh network-origin verification occurred.

Retrospective archive receipt is not contemporaneous publication, forecast availability or executable-price evidence. Provider archives can be corrected or replaced later; these pins identify only the acquired bytes. A later ZIP or sidecar-body change requires review and a new release, never silent replacement. Archived minute openings provide no quotes, order-book depth, latency, fillability or market-impact evidence. No independent authentication of acquisition timestamps or original publication ordering is claimed.

2024 was previously inspected in research; any future analysis remains exploratory, not independent out-of-sample validation. Source verification makes no profitability or real-trading claim.

The existing `artifacts/` ignore rule is preserved. Only this metadata document is added to Git; raw archives, sidecars, processed prices and the local manifest remain ignored. No source code, protocol, tests or scientific data were modified. No commit or push was made.

No historical backtest, performance calculation, hourly/minute parity audit, research forecast or holdout access, Stage 4B.2D, Stage 3 evidence, database, production access or deployment occurred. Parity-audit scope, original forecast loading, minute-replay implementation and real evaluation retain their separate owner-authorisation gates.

## Validation checks for this freeze

- Fresh focused synthetic suite: **157 passed in 100.30 seconds**. Command: `env -u BADGER_TEST_ADMIN_DSN PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never uv --cache-dir /tmp/badger-4b2c3-uv-cache run --locked --offline --no-sync pytest -q tests/test_minute_execution_data.py -p no:cacheprovider`.
- Focused lint passed: `uv --cache-dir /tmp/badger-4b2c3-uv-cache run --locked --offline --no-sync ruff check src/backtest_badger/minute_execution_data.py tests/test_minute_execution_data.py --no-cache`.
- Metadata table and URL/count/hash transcription checked against the verified manifest and acquisition signoff.
- `git diff --check` and `git diff --cached --check` passed after adding only this document to the index. The pre-existing tracked files and all 50 dataset files remained byte-identical in the final preservation check.
- No full test suite, remote CI, database tests or economic evaluation was run for this metadata-only change. No discrepancies or unresolved source-validation issues were found.

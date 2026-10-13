# When Market Data Isn't Complete

- **Date:** 2026-10-13
- **Stage:** 1B.3 — Historical market data
- **Topic:** Data quality, historical gaps and research validity
- **Publication status:** Draft

The archive downloaded successfully. Its checksum matched. The ingestion pipeline
stopped anyway.

Backtest Badger was collecting Binance Spot's native four-hour candles for BTCUSDT
and ETHUSDT, covering August 2017 through September 2026. Each candle records an
interval's opening, highest, lowest and closing prices, alongside trading volumes
and a trade count. The aim was to build a reproducible foundation for later
research, with genuine provider observations and explicit limits on what they
could tell us.

The first full backfill stopped at BTCUSDT's September 2017 monthly archive. It
contained 179 observations where the calendar grid expected 180. The September 6
candle opening at 12:00 UTC reported a close time of 16:00:00.000, one millisecond
beyond the expected inclusive boundary of 15:59:59.999. The next candle, opening at
16:00, was absent.

A matching checksum establishes that downloaded bytes match the provider's
published checksum. It cannot establish that those bytes contain complete
intervals, correct timestamps or economically accurate observations. File
integrity and research validity need separate checks.

We compared the monthly archive with Binance's daily four-hour archive, historical
public REST response and native hourly candles. Daily and REST data agreed
with the 12:00 candle's prices, volumes and trade count, but gave it the normal
closing boundary. The four hourly observations from 12:00 through 15:00 also
reproduced its economic values exactly.

Daily and REST data did return a 16:00 identity. However, it had zero trades and
zero volumes, and its close timestamp equalled its opening timestamp. Its presence
did not supply a valid complete four-hour replacement. Hourly observations from
17:00 through 22:00 were absent. The native 20:00 four-hour candle had a normal
boundary, yet its economic values matched the sole returned hour within that
interval: 23:00. Even a normally bounded candle did not establish uninterrupted
trading throughout its interval.

These observations are consistent with a trading interruption. The project
investigation also records a Binance repository contributor's explanation that
some historical gaps reflect maintenance. Neither establishes the cause or exact
duration of this particular gap. Historical export differences around an
interruption are a plausible explanation for the monthly-only boundary mismatch;
the provider's internal history remains unverified.

A second bounded comparison, for June 26, 2018, found a shortened four-hour candle
and two absent four-hour intervals across monthly, daily and REST sources. This
supported a general policy for handling disclosed gaps rather than a correction
specific to September 2017. The [detailed Stage 1B.3 investigation](../stage-01b3-full-history.md#bounded-official-source-investigation)
records the exact identities, timestamps and source comparisons.

The engineering decision was conservative: keep strict ingestion as the default,
and offer an explicit mode that imports valid observations while retaining gap
diagnostics. Irregular-close rows were excluded, including September's
corroborated 12:00 row. No timestamps were silently corrected, no prices were
forward-filled and no synthetic zero-volume candles were created. Checksums,
economic validation, identity checks and transactional conflict handling remained
strict. Original archives and diagnostic manifests preserved the evidence.

That separation allowed acquisition to finish without pretending the gaps had
disappeared. The [verified final results](../stage-01b3-full-history.md#final-live-results-and-verification)
were identical in count for both markets:

| Result | BTCUSDT | ETHUSDT |
| --- | ---: | ---: |
| Monthly archives acquired and inspected | 110 | 110 |
| Expected four-hour identities in the verified range | 19,991 | 19,991 |
| Accepted stored candles | 19,955 | 19,955 |
| Absent monthly-source identities | 17 | 17 |
| Excluded irregular-close observations | 19 | 19 |
| Remaining stored gaps | 36 | 36 |

The verified range begins on August 17, 2017 at 04:00 UTC and ends on October 1,
2026, exclusively; August is a partial initial month. All requested monthly
archives were acquired, but market coverage is not continuous. The default
complete export was correctly refused. An explicitly incomplete export must carry
the gap manifest and its incomplete status.

That distinction matters before any model is trained. A rolling indicator over
adjacent stored rows could silently span missing periods: row adjacency does not
guarantee four-hour adjacency. Future feature and target construction must reject
or explicitly handle windows crossing gaps, so a nominal prediction horizon does
not quietly change its duration. Chronological training splits and train-only
preprocessing remain necessary; they cannot repair missing observations.

Backtests likewise need an explicit policy for affected windows. Missing prices
cannot establish available fills, and absent observations do not justify assumed
zero returns. Regular candle boundaries alone cannot resolve trading
interruptions within a bar. These are requirements for future research, not
claims about experiments already performed: this investigation implemented no ML
or backtesting. The usable result is genuine stored history accompanied by an
honest account of where that history is incomplete.

# One Minute Can Change a Backtest

- **Date:** 2026-10-24
- **Stage:** 4B.2C–4B.2D.1 — Native-minute sources and price parity
- **Topic:** Causal execution timing, source verification and evidence limits
- **Publication status:** Published

A price can be recorded correctly and still be the wrong price for a backtest.
If the signal was not available when that price occurred, assigning it to a trade
gives the simulation information from the future.

Consider a four-hour candle ending at 12:00 UTC. Backtest Badger assumes its
information becomes usable after a 60-second settling delay, at **12:01**. The
12:00 close precedes that signal. So does the opening event at 12:01 under the
project's strict ordering rule: a decision available exactly on a minute boundary
must wait for the next one. The hypothetical execution reference is **12:02**.

This is the convention frozen in the [Stage 4B.2C minute protocol](../stage-04b2c-minute-execution-protocol.md).
It is an explicit assumption, not a measurement of how quickly a model or exchange
would respond. Waiting one minute gives the simulation a clear causal order; it
does not establish that an actual order could fill at that opening price.

## Three clocks, three roles

A candle summarises an interval's prices and activity. “Native” means it comes
from the provider at that interval, rather than being reconstructed locally from
another series. This research uses different intervals for different purposes:

| Data | Role in the research |
| --- | --- |
| Native four-hour candles | Completed observations for features and the model's next-four-hour close-to-close forecast target |
| Independently acquired native hourly candles | Reference prices for earlier hourly research and a separate comparison source for the parity audit |
| Native one-minute candles | Next-minute execution references and the HH:00 openings used for hourly portfolio valuations in the minute scenario |

Minute execution does not make this a minute forecasting model. Nor does it mean
there is a portfolio valuation for every minute. The minute protocol keeps **8,784
hourly marks per account** through December 31 23:00 UTC, while the source
validation requires all **527,040 minutes per market** in leap-year 2024. A complete
source grid includes periods with no trade; missing rows cannot quietly become
zero returns or be replaced by a later opening.

Offline source validation can inspect complete candles. A strategy decision must
still use only its eligible forecast, never the future high, low, close or volume
of the minute used for execution.

## Did the two sources agree at the hour?

The project acquired hourly and minute archives separately. They could disagree:
a provider can revise one archive independently of another. If hourly valuation
prices change between studies, a supposed timing comparison might also contain a
hidden data change.

The protocol therefore specified an exact comparison before economic use. The
[Stage 4B.2D.1 audit](../stage-04b2d1-genuine-price-parity-audit.md), completed on
19 October 2026, authenticated both retained releases and compared every native
hourly opening with the native minute opening at the same **HH:00** identity.
It found:

| Market | Hourly/minute pairs | Exact price mismatches |
| --- | ---: | ---: |
| BTCUSDT | 8,784 | 0 |
| ETHUSDT | 8,784 | 0 |
| Total | 17,568 | 0 |

The comparison used exact decimal prices, with no chosen tolerance or rounding
away of differences. Every monthly bucket had zero discrepancies; leap February
contributed 696 matched hours per market. Missing, duplicate and off-grid
observations were also absent. These are the findings of the earlier audit,
**not new tests performed for this article**.

This establishes agreement at the compared hour boundaries for those exact
retained releases. It does not compare each intervening minute to an hourly
price, prove that the prices were accessible in real time, or make different
trading policies equivalent. In particular, the earlier Stage 2C round trips and
the later continuous-holding minute strategy still differ in holding rules.

## What makes the evidence reusable?

The [source-engineering guide](../stage-04b2c-minute-data-engineering.md) separates
several checks. A ZIP checksum tests whether the file matches its retained
checksum evidence. Parsing tests fields and prices. Grid checks test whether
observations have the expected market, order and timestamps. For a 2024 native
minute, the inclusive close timestamp must be exactly **59,999 milliseconds**
after its opening; a plausible-looking row is insufficient.

The later genuine parity audit validated the complete source releases before
comparing their hourly projections. It retained source identities, comparison
results and output hashes. Before-and-after checks found all **101 source files**
unchanged. A manifest written after verification binds the report files together.
These practices help a future reader distinguish the evidence originally used
from a new download or a silently replaced result.

“Authenticated” has a bounded meaning here: the supplied files matched the
independently retained hashes and the source contracts passed validation. The
provider's checksum sidecars are unsigned; they are not signed attestations of
economic truth. Hashes identify bytes, not whether those bytes capture every
market event accurately. Retaining the originals makes revisions inspectable;
it does not prevent the provider from publishing different data later.

## What one minute cannot establish

A minute's opening price is a historical reference, not an order book. The audit
observed neither bid/ask depth nor the quantity available to a trader. It measured
no computation, network or order-submission latency, and supplied no proof of
market impact, exchange-filter compliance or actual fills. The first trade in a
minute need not occur at its nominal zero-second boundary.

The audit deliberately accessed no forecasts and calculated no strategy returns.
Its successful result cleared a source-price consistency condition; it did not
establish a trading advantage. The later genuine economic findings are described
separately in [The Price of Changing Your Mind](003-the-price-of-changing-your-mind.md).

Reliable research needs both questions kept visible: **was this the evidence we
intended to use, and could the decision have preceded the assumed execution?**
Source checks answer part of the first. Explicit signal and execution clocks
address part of the second. Neither should be mistaken for proof of fillability.

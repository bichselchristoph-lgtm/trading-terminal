---
id: 021
title: keepUpToDate at the open, five streams, full session
status: DONE
type: investigation
owner: claude-code
ran: 2026-08-13 09:12:57 → 16:05:00 ET (412.05 min, live regular session)
symbols: AMZN NVDA INTC TSLA SOFI
---

**Status** RUNNING

# 021 — `keepUpToDate` at five streams, for a full session

**Five streams cost nothing. The measured ratio is 1.0×.**

All five accepted, and in the regular session every one of them held a median cadence of
**5.00 s against 008b's one-stream baseline of 5.002 s**. Not 25 s, not 2×, not a
detectable penalty of any kind. The 09:30–10:00 bucket — the one the task named as
mattering — reads 4.982–5.000 s across the five. **`session_vwap_refresh_mode:
keep_up_to_date` survives contact with a five-symbol console on cadence grounds.**

**And it should still not be shipped as-is, for a reason the task did not anticipate.**

**At 15:22:15 ET all five streams stopped delivering, simultaneously, and never resumed.**
The run continued to 16:05:00 with the API socket up, `ib.isConnected()` returning `True`
throughout, and **the probe's own summary reporting `survived_window: True`**. Forty-two
minutes and forty-five seconds of a session that cannot be re-recorded went unmeasured
while every health signal available said fine.

That is the finding. The cadence question is answered and the answer is good; **the
survival question is answered and the answer is that this mechanism fails silently.**

---

## The six answers

### 1. Do all five accept? **Yes. The cap does not bind at five.**

Issued in order 09:12:57 → 09:13:02, one `reqHistoricalData` each, no re-request:

```
#1 AMZN  ACCEPTED=True  313 bars, earliest 2026-08-13 04:00:00-04:00
#2 NVDA  ACCEPTED=True  313 bars, earliest 2026-08-13 04:00:00-04:00
#3 INTC  ACCEPTED=True  313 bars, earliest 2026-08-13 04:00:00-04:00
#4 TSLA  ACCEPTED=True  313 bars, earliest 2026-08-13 04:00:00-04:00
#5 SOFI  ACCEPTED=True  313 bars, earliest 2026-08-13 04:00:00-04:00
```

No rejection, no ordinal failure, no error at request time. **There is nothing to record
under "which ordinal request failed" because none did.** Five is not the limit; this run
establishes only that five works, not where the limit is.

### 2. Cadence per stream, by period

Median / p95 / max, in seconds. **p95 and max are quoted beside the median because the
median hides bursts** — AMZN medianed 14.88 s pre-open while going 59.999 s dark.

| symbol | pre-09:25 | 09:25–09:30 | **09:30–10:00** | 10:00–12:00 | 12:00–15:30 | 15:30–16:00 | 16:00+ |
|---|---|---|---|---|---|---|---|
| AMZN | 14.88 / 60.00 / 60.00 | 5.76 / 29.97 / 29.99 | **5.00 / 5.78 / 6.12** | 5.00 / 5.82 / 10.22 | 5.00 / 5.90 / 51.79 | — | — |
| NVDA | 5.00 / 10.00 / 20.00 | 5.00 / 5.91 / 10.00 | **5.00 / 5.35 / 6.12** | 5.00 / 5.65 / 6.51 | 4.99 / 5.83 / 51.79 | — | — |
| INTC | 5.01 / 20.00 / 30.23 | 5.13 / 10.20 / 20.03 | **5.00 / 5.32 / 14.60** | 5.00 / 5.58 / 6.34 | 5.00 / 5.84 / 51.79 | — | — |
| TSLA | 5.55 / 19.45 / 25.01 | 5.01 / 14.79 / 20.00 | **5.00 / 5.50 / 6.03** | 4.99 / 5.73 / 6.38 | 5.00 / 5.83 / 51.79 | — | — |
| SOFI | 9.86 / 24.72 / 30.00 | 5.21 / 20.20 / 25.01 | **4.98 / 5.80 / 19.63** | 5.02 / 5.80 / 10.17 | 5.01 / 6.04 / 51.77 | — | — |

**The two empty columns are the finding, not a formatting gap.** Nothing was delivered
after 15:22:15, so the 15:30–16:00 bucket has no data and the 16:00 boundary was never
observed.

Update totals over the run: **AMZN 4,248 · NVDA 4,400 · INTC 4,353 · TSLA 4,346 ·
SOFI 4,244.** Every stream recorded **exactly 369 `APPEND_NEW_BAR`** events — one per
minute boundary from 09:13 to 15:22, **none missed** — and **zero anomalous
classifications** across 21,591 callbacks.

### 3. Five streams against one — **1.0×. This is the headline.**

| | 008b, one stream | 021, five streams | ratio |
|---|---:|---:|---:|
| median cadence, regular session | 5.002 s | **4.982 – 5.022 s** | **1.00× (worst 1.004×)** |

**There is no degradation to report.** The task set 2× as the threshold at which
`keep_up_to_date` stands and 30 s as the point where the decision reopens. The measurement
is 1.0×, over six hours and five symbols, and it is not close to either boundary.

**008b's single-stream figure was not an artifact.** Its own note flagged that as the one
claim resting on an untested limit; it is now tested.

### 4. Does cadence track print rate? **No, in the regular session — and this is now answered, not suggestive.**

008b saw the ~5 s beat hold across a **6×** volume swing and explicitly declined to
generalise. This run supplies a far larger swing and settles it:

| symbol | RTH minutes | vol/min median | vol/min range | **swing** | updates/min median | updates/min max |
|---|---:|---:|---|---:|---:|---:|
| AMZN | 352 | 32,357 | 9,177 – 625,098 | **68×** | 12 | 12 |
| INTC | 352 | 130,702 | 26,303 – 1,473,931 | **56×** | 12 | 12 |
| NVDA | 352 | 106,591 | 29,050 – 2,176,697 | **75×** | 12 | 13 |
| SOFI | 352 | 83,444 | 6,995 – 549,708 | **79×** | 12 | 12 |
| TSLA | 352 | 47,116 | 12,124 – 280,266 | **23×** | 12 | 12 |

**Volume moved by up to 79× and updates per minute did not move at all.** Rank correlation
between the two is 0.10–0.29 (Pearson 0.05–0.17) — and the weakness is the point: there is
almost no variance in the update count to correlate against.

**The mechanism, which explains both this and 008b:** the beat is a **fixed ~5-second grid**,
twelve ticks to the minute. Gaps land on multiples of 5 s — with `1×` dominating utterly
(NVDA 4,354 of 4,385 gaps; AMZN 4,151 of 4,238) and skips of 2×, 3×, up to 12× making up the
rest. A stream does **not slow down** when a symbol is quiet; **it skips grid ticks.**

In the regular session all five symbols print enough to fill every tick, so all five saturate
at 12/minute and volume is irrelevant. Pre-market, quiet symbols skip: AMZN medianed 14.88 s
(three ticks) and SOFI 9.86 s (two), while heavily-printed NVDA sat at 5.00 s (one) all
morning. **That is the same phenomenon at both ends, and "cadence tracks print rate" is the
wrong description of it — cadence is constant and coverage is what varies.**

### 5. Survival — **the connection survived six hours. The data stopped after six hours and nine minutes.**

**No spontaneous disconnect, at any point.** `spontaneous_connection_events: []`, and the
single `disconnected` record in the log is the probe's own teardown at 16:05:00.762 — the
distinction 008b's note flagged, handled here by snapshotting the event list before teardown.

**And it does not matter, because delivery stopped anyway.** Reconstructed from the error log:

```
15:22:09.076-.077  all five streams: a 51.8 s gap ends       <- the precursor
15:22:14.728       last update, every stream, simultaneously
15:22:19.915  2105 HMDS data farm connection is broken:ushmds
15:22:19.917 10182 Failed to request live updates (disconnected).   x5, one per stream
15:22:22.801  2106 HMDS data farm connection is OK:ushmds    <- recovered in 2.9 s
   ...
16:05:00       run ends. Nothing further was ever delivered.
```

**The farm blip lasted 2.9 seconds. The outage it caused lasted 42 minutes 45 seconds and
was still going when the probe stopped.** `keepUpToDate` subscriptions are killed by error
10182 and **do not re-establish themselves when the farm returns.** No retry, no error after
the fact, no change in connection state.

The 51.8 s gap ending 15:22:09 hit **all five streams within 1 ms of each other**, which is
the signature of a connection-level event rather than five coincidental quiet symbols. It is
the largest regular-session silence in the run — **10.4× the 008b beat** — and in hindsight it
was the farm already failing.

> **The worst silence observed in RTH: 51.8 s, on all five streams simultaneously, ending
> 15:22:09 ET — immediately before the streams died for good.**

**35 API error records in total.** All but the 15:22 cluster are routine farm connectivity
notices (2103/2104/2105/2106/2108 — `afarm`, `hfarm`, `jfarm`, `usfarm`, `usfuture`, `usopt`,
`ushmds`), the sort TWS emits all day. **Eight earlier farm break/restore pairs occurred
without killing anything** — 14:11, 14:20, 14:27, 14:35, 14:36, 15:08, 15:21. Only the
`ushmds` break at 15:22 was fatal, and `ushmds` is the historical-data farm, which is exactly
what a `reqHistoricalData` subscription rides on.

### 6. Does the 04:00 anchor hold? **Yes — for the 6 h 09 m it was alive.**

`anchor_held: True` on all five. Earliest bar was `2026-08-13 04:00:00-04:00` in the initial
payload and still `04:00:00-04:00` in the final one, for every symbol. The window extends
forward and keeps its anchor; it does not slide. **No seam, so no join, so no join bug** —
008b's conclusion holds at five streams.

**The honest qualification:** the last update was 15:22:14, so this confirms the anchor over
**09:12→15:22**, not to 16:00. Six hours and nine minutes, not six hours and fifty-two.

---

## Environment

| item | value |
|---|---|
| Application | **TWS, live**, `127.0.0.1:7496` |
| Server version | **178** |
| `clientId` | **121** (distinct, so this run is separable on the connection) |
| Window | **2026-08-13 09:12:57 → 16:05:00 ET**, 412.05 min |
| Started before the 09:25 deadline | **Yes** — requests issued 09:12:57–09:13:02 |
| Symbols | **AMZN, NVDA, INTC, TSLA, SOFI**, all `SMART`/`USD` |
| Request | `durationStr="1 D"`, `barSizeSetting="1 min"`, `whatToShow="TRADES"`, `useRTH=False`, `formatDate=1`, `keepUpToDate=True`, `endDateTime=""` |
| Requests issued | **5** (plus five contract qualifications). No re-request, no polling. |
| Connection | `readonly=True`, no `tws_order` import, no `reqExecutions` |
| Market data | Not enumerable via the API. Five streams ran 6 h with live prints, so the US equity entitlement is active. |
| Raw logs | `records/probes/021/021_<SYM>_events.jsonl` (21,591 update records), `021_run.jsonl` (409 heartbeats, 35 errors), `021_summary.json`, `021_analysis.json` |
| Scripts | `tools/probe_keepuptodate_scale.py`, `tools/analyse_keepuptodate_scale.py`, `tests/test_keepuptodate_scale.py` (49 tests) |

**Cost: none.** IBKR historical requests are covered by the existing subscription. No metered
vendor, no Databento, no orders.

---

## What I could not do

**This section is not empty, and two of the five entries are consequences of the 15:22 death.**

1. **The 16:00 boundary under `useRTH=False` was never observed.** This was record item 5's
   second half and the reason the task specified holding to 16:05. The streams were dead from
   15:22, so **whether the stream continues into post-market, stops, or errors at 16:00 remains
   exactly as unknown as before this run.** It needs another session.

2. **The 15:30–16:00 cadence bucket is empty**, for the same reason. The task named five
   buckets and this run measured four.

3. **No large pre-market gapper was available.** The method asked for at least one, so a
   heavily-printing name could be contrasted against a quiet one. I scanned twelve liquid
   candidates at 09:07 ET; the largest absolute gap was **SOFI at +0.67%**, with PLTR +0.66%
   and TSLA −0.63%. **This morning could not supply the contrast**, so I selected for print-rate
   spread instead — NVDA and INTC carried the heaviest pre-market volume (1.12 M and 1.62 M
   shares), AMZN the lightest of the five. That substitution turned out to answer question 4
   anyway, because pre-market supplied the low-print-rate regime the gap was wanted for. Scan
   output is in the done-note's raw form only; it was a throwaway script, not adopted.

4. **The limit on simultaneous `keepUpToDate` requests was not located.** Five accept. Whether
   six, ten or fifty do is untested — the task asked what happens at five, and going higher
   would have risked the measurement it asked for.

5. **`live/` was not exercised.** This probed the API directly, as 008b did. The standing
   caveat that `live/` has import coverage only is untouched.

---

## A defect in my own instrumentation, stated rather than buried

**`021_summary.json` records `survived_window: true` and `still_connected_at_end: true` for a
run in which every stream had been dead for 42.8 minutes.** Both fields are literally correct
— the socket did survive — and both are worthless as evidence that the mechanism worked.

008b's note contains a passage warning about precisely this class of mistake in its own
summary line, and I read it before writing this probe. **I still built a summary that reports
connection health and calls it survival**, because the question I encoded was "did the socket
drop" and the question that mattered was "did data keep arriving".

The analysis now separates them. `tools/analyse_keepuptodate_scale.py` computes a per-stream
silent tail and prints:

```
  AMZN   *** DEAD *** last update 15:22:14.728, then silent 2565.3s (42.8 min)
  ... x5
  !! 5/5 streams STOPPED DELIVERING before the run ended
  !! and the run summary says survived_window=True, still_connected_at_end=True.
  !! The socket survived. The data did not.
```

`test_a_connected_socket_is_not_a_delivering_stream` pins it. **The recorded summary for this
run has deliberately not been rewritten** — it is the record of what the probe actually
reported, and correcting it would erase the defect rather than the confusion.

---

## Proposed config entries

**Not written to `config/`** — same reason as 008a and 008b: they land with slice 008's config
loader so its rules apply from the first commit.

```yaml
session_vwap_refresh_mode:
  value: keep_up_to_date
  source: measurement
  note: >
    VERIFIED AT FIVE CONCURRENT STREAMS, which 008b listed as its one untested claim.
    2026-08-13, AMZN/NVDA/INTC/TSLA/SOFI, 09:12:57-16:05 ET, 412 min, one open request each.
    All five accepted; 21,591 updates; 369 appends per stream with none missed; zero anomalous
    classifications. Regular-session median cadence 4.982-5.022 s against 008b's one-stream
    5.002 s -- a ratio of 1.00x, so the per-stream beat does NOT divide across streams.
    09:30-10:00, the bucket the ORB playbooks trade, measured 4.982-5.000 s.
    MUST NOT BE ENABLED WITHOUT A LIVENESS WATCHDOG -- see keepuptodate_stream_watchdog_s.
    The 16:00 boundary under useRTH=False is STILL UNTESTED: the streams died at 15:22.

keepuptodate_stream_watchdog_s:
  value: 180
  role: REQUIRED companion to keep_up_to_date, not an optimisation
  source: measurement
  note: >
    A keepUpToDate subscription can die silently and permanently. On 2026-08-13 the ushmds
    historical-data farm broke for 2.9 s at 15:22:19; TWS answered all five subscriptions with
    error 10182 "Failed to request live updates (disconnected)"; the farm recovered at
    15:22:22.801 and NO STREAM EVER RESUMED. 42 min 45 s of the session went unrecorded with
    the API socket up and ib.isConnected() returning True throughout.
    ib.isConnected() IS NOT A LIVENESS SIGNAL FOR THIS MECHANISM. The console must track time
    since last update PER STREAM and re-request on breach. 180 s is chosen as 3x the widest
    legitimate silence observed anywhere in the run (59.999 s, pre-market, quietest symbol)
    and far below the 42-minute outage it must catch. Eight EARLIER farm break/restore pairs
    the same afternoon did not kill anything -- only ushmds did -- so the watchdog cannot key
    on error codes, only on silence.

streaming_bar_update_cadence_s:
  value: 5
  role: observed constant, not a tunable
  source: measurement
  note: >
    The update beat is a fixed ~5 s grid, 12 ticks per minute, and a stream with no new prints
    SKIPS TICKS rather than slowing down. Gaps land on multiples of 5 s with 1x dominating
    (NVDA 4,354 of 4,385). Measured 2026-08-13 across five symbols.
    SETTLES 008b's open question: cadence does NOT track print rate in the regular session.
    Per-minute volume swung 23x-79x (NVDA 29,050 to 2,176,697 shares) while updates per minute
    stayed at a median of 12 for every symbol; rank correlation 0.10-0.29, weak because there
    is no variance left to correlate. 008b saw a 6x swing and called this suggestive; at 79x it
    is established. Re-measure under another broker or TWS version -- this is a property of
    TWS 178, not of the concept.

cum_refresh_s:
  value: 120
  role: fallback
  source: constraint:ibkr
  note: >
    Unchanged from 008b, and its role is now stronger rather than weaker. The staleness
    advantage of keep_up_to_date is confirmed at five streams (5 s against 120 s, 24x), but
    keep_up_to_date has a silent-death mode that a periodic re-request does not: a re-request
    that fails fails loudly and is retried on the next cycle, whereas a dead keepUpToDate
    subscription is indistinguishable from a quiet market. Retain as the documented fallback
    the watchdog falls back TO.
```

---

## For whoever picks up §6b.1b

1. **Cadence is settled and it is good.** Five streams, 1.0×, six hours. Do not re-litigate it
   and do not carry 008b's single-stream number forward as though it were still the only
   evidence — quote this one.
2. **Build the watchdog before the feature.** A stream that dies silently while the connection
   reports healthy is worse than a slower refresh that fails loudly, because session VWAP is a
   stop level and a frozen one looks exactly like a calm market.
3. **Do not use `ib.isConnected()` as a health check for anything riding on `keepUpToDate`.**
   It was `True` for the entire 42-minute outage.
4. **The 16:00 boundary is still owed.** It was the reason for holding to 16:05 and this run
   did not reach it alive.
5. **The replace-not-accumulate rule from 008b is reconfirmed** at scale: 21,222 of 21,591
   updates were `REVISE_IN_PLACE`. At a median of 12 revisions per minute, a consumer that
   added rather than replaced would overstate volume by roughly 12×, not 6× — the exposure
   grows with the beat, and RVOL remains the thing that breaks.

---

**This note must be pasted to chat.** It lands in a repo the design session cannot see, and
on 2026-08-11 two correct done-notes never reached it. **The headline to carry is the pair:
five streams cost nothing, and the mechanism died silently at 15:22 with every health signal
green.** The first result clears `keep_up_to_date`; the second gates it.

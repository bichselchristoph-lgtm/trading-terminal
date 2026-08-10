---
id: 008b
title: Does keepUpToDate hold a session-length window open?
status: DONE
type: investigation
owner: claude-code
ran: 2026-08-10 12:34:30 → 13:06:32 ET (32.03 min, live regular session)
symbol: AMZN
---

# 008b — `keepUpToDate=True` over a session-length window

**It works, and it lands on the task's first interpretation branch:** it accepts
`useRTH=False`, the initial payload reaches back to **exactly 04:00**, the window does not
narrow or slide, and it ran 32 minutes with **zero API errors and no dropped connection**.
So `keepUpToDate` can replace the 120 s re-request cadence, and §6b.1b's pacing arithmetic
stops binding for session VWAP.

**But the headline is question 5, and the measured answer is not the one the task
anticipated.** The last bar *is* revised in place — 344 times in 32 minutes — so a naive
"add each update's contribution" is a real defect. Measured, however, its damage is almost
entirely in **volume, not price**:

| | correct (replace) | naive (add) | error |
|---|---:|---:|---:|
| window VWAP | 277.451666 | 277.453806 | **+0.214 cents** |
| window volume | 796,911 | 4,730,374 | **5.94× — 3,933,463 phantom shares** |

The task predicted "a silent few-cent error on a stop level". On VWAP that is **0.2 cents**,
because the repeated counts land at nearly the same price and largely cancel. **The severe
consequence is RVOL**, whose denominator would be overstated roughly sixfold. Anything
consuming volume from a `keepUpToDate` stream — RVOL above all — must replace, not
accumulate. VWAP would survive the bug; RVOL would not.

Script: **`tools/probe_keepuptodate.py`**. One symbol, one open request, no loop, no
re-request — the only repeated call is `ib.sleep()`, which pumps the event loop and issues
nothing. `readonly=True`, `__main__` guard, timeout-guarded, no `tws_order` import.

---

## The five answers

### 1. Does it accept `useRTH=False` at all? **Yes.**

Accepted immediately, no error, no warning. **Zero API errors across the whole 32 minutes.**
There is nothing to record under "exact error code and message" because nothing failed.

### 2. Does the initial payload reach back to 04:00? **Yes — exactly 04:00, and it stays.**

```
[12:34:31] ACCEPTED=True  initial payload = 515 bars
[12:34:31] earliest = 2026-08-10 04:00:00-04:00   latest = 2026-08-10 12:34:00-04:00
```

515 bars spanning 04:00 → 12:34 is 514 completed minutes plus the forming one — **every
minute present, no gaps**. `keepUpToDate` does not silently narrow the window, which was the
documented unknown.

It also does not *slide* it. At the end of 32 minutes the payload had grown to **547 bars
and its earliest bar was still `04:00:00-04:00`** — the window extends forward and keeps its
anchor rather than rolling. **No seam exists, so the "combine two requests" branch of the
task's interpretation does not apply and no join needs recording.**

### 3. Update cadence — **~5 s, not once per minute on bar close.**

376 updates in 32.03 minutes:

| statistic | seconds |
|---|---:|
| min | 4.196 |
| median | 5.002 |
| mean | 5.106 |
| max | 14.477 |

Roughly **11.4 updates per minute** (min 6, max 12). So the forming bar is revised
continuously at about a 5-second beat, and a new bar is appended once at each minute
boundary. This is materially better than the thing it replaces: **~5 s staleness against the
120 s cadence, a 24× improvement**, and it lands exactly where the task said it matters —
the first thirty minutes, where session VWAP moves fastest and the ORB playbooks trade.

The 14.477 s outlier is a single gap, not a pattern; the median and mean sitting within
0.1 s of each other says the distribution is tight.

### 4. Does it survive 30 minutes? **Yes — 32.03 minutes, no drop, no reconnect.**

`still_connected_at_end: True`. `api_errors: []`. 32 appends over 32 minutes — exactly one
new bar per minute boundary, with none missed.

**One correction to my own instrumentation, because the raw log misreports this.** The
stdout summary printed `survived without disconnect: False` and the log shows a
`!!! DISCONNECTED` line at `13:06:32.043`. That is **the probe's own teardown**, not a
dropped session: the observation deadline fell at `13:06:31`, the loop exited, and the
disconnect event is `ib.disconnect()` firing 1.0 s later, with the summary printing 2 ms
after that. The summary field `still_connected_at_end` — sampled *before* teardown — reads
`True`, which is the trustworthy one.

I have fixed the script so a future run cannot make this mistake: it now snapshots the
connection-event list before teardown and reports `survived_window` from spontaneous drops
only. **The finding is that the connection held**; had I trusted my own summary line I would
have filed the opposite conclusion.

### 5. Is the last bar revised in place? **Yes. 344 times. This is the one with a consequence.**

Of 376 updates: **344 `REVISE_IN_PLACE`, 32 `APPEND_NEW_BAR`, 0 no-change, 0 anomalous.**
Every update either revised the forming minute or closed it and started the next — nothing
unclassifiable.

**Fields revised in place: `average`, `barCount`, `close`, `high`, `low`, `volume`.**
Note `open` is absent, as it should be — a forming bar's open is fixed at its first print,
and every other field moves.

`average` is `Bar.WAP`, which task 008a settled as the VWAP price source. **So both terms of
`Σ(WAP × volume)` are mutated by every update.** Recomputing session VWAP means replacing
the forming minute's contribution wholesale, not adding to it.

A worked excerpt — one minute forming, then closing:

```
#   1 REVISE_IN_PLACE   bar=12:34:00  +4.94s  c=277.99  v=9684   n=515
#   2 REVISE_IN_PLACE   bar=12:34:00  +5.00s  c=278.0   v=10014  n=515
#   3 REVISE_IN_PLACE   bar=12:34:00  +4.48s  c=278.0   v=15317  n=515
#   4 REVISE_IN_PLACE   bar=12:34:00  +5.50s  c=277.94  v=20225  n=515
#   5 REVISE_IN_PLACE   bar=12:34:00  +4.46s  c=278.04  v=24597  n=515
#   6 REVISE_IN_PLACE   bar=12:34:00  +5.59s  c=278.02  v=25182  n=515
#   7 APPEND_NEW_BAR    bar=12:35:00  +4.76s  c=278.04  v=2828   n=516
#   8 REVISE_IN_PLACE   bar=12:35:00  +5.20s  c=278.01  v=3909   n=516
```

Read the `v` column: `9684 → 10014 → 15317 → 20225 → 24597 → 25182` is **one minute's
cumulative volume restated six times**, not six increments totalling 105,019. Then `n`
steps 515 → 516 and `v` resets to 2,828 for the new minute. A consumer that added these
would book 105,019 shares for a minute that traded 25,182.

**Quantified over the full window** (33 bars, 12:34 → 13:06), correct = last snapshot per
minute, naive = every update treated as an increment:

| | correct | naive | error |
|---|---:|---:|---:|
| VWAP | 277.451666 | 277.453806 | **+0.214 ¢** |
| volume | 796,911 | 4,730,374 | **5.94×** |
| updates per minute | — | — | mean 11.4 (min 6, max 12) |

The 5.94× is close to the mean updates-per-minute figure, as it should be — each minute gets
counted about as many times as it is revised. **The price error nearly cancels; the volume
error does not.** That asymmetry is the finding, and it is why this note leads with RVOL
rather than with stop levels.

---

## Environment

| item | value |
|---|---|
| Application | **TWS, live**, `127.0.0.1:7496` |
| Server version | **178** |
| Window | **2026-08-10 12:34:30 → 13:06:32 ET**, 32.03 min |
| Session context | **live regular session**, ~3.5 h before the close |
| Connection | `readonly=True`, `clientId=79` |
| Symbol | **AMZN**, `SMART`/`USD` |
| Request | `durationStr="1 D"`, `barSizeSetting="1 min"`, `whatToShow="TRADES"`, `useRTH=False`, `formatDate=1`, `keepUpToDate=True`, `endDateTime=""` |
| Requests issued | **1** (plus one contract qualification). No re-request. |
| Market data | Not enumerable via the API. The stream ran 32 min with zero errors, so the live US equity entitlement is active. |
| Raw logs | `kutd_AMZN_events.jsonl` (376 update records, every callback), `kutd_AMZN_summary.json` |

---

## Deviations from the method, and what I could not do

1. **The window did not span 10:00 ET.** The task asked for that ideally, so a quiet and an
   active stretch would both be covered. 008b arrived at 18:23 local — **12:23 ET, already
   past 10:00** — so the choice was a mid-session window today or waiting a day. I ran
   12:34–13:06. **The opening half-hour's cadence is therefore unmeasured**, and it is the
   stretch where update frequency would most plausibly differ, since it carries the heaviest
   print rate. The ~5 s beat held steady across a 6× swing in per-minute volume within my
   window (2,374 to 74,846 shares), which is *suggestive* that cadence is not volume-driven
   — but the open was not observed and I am not extrapolating into it.

2. **32 minutes, not a full session.** The task asked for at least 30. Whether the request
   survives six hours, or across the 16:00 boundary with `useRTH=False`, is untested. The
   evidence here is 32 clean minutes.

3. **One symbol, one process.** The pacing claim that follows — that `keepUpToDate` removes
   the per-account 60-per-10-minutes arithmetic — **rests on it being one open request
   rather than repeated ones, which is verified. What is not verified is how five concurrent
   `keepUpToDate` streams behave on one account.** IBKR limits simultaneous open historical
   requests separately from the request-rate budget, and that limit was not probed. Before
   this replaces the cadence in a five-symbol console, that needs its own test.

4. **No behaviour of `live/` was exercised.** This probed the API directly. The standing
   caveat that `live/` has import coverage only is untouched.

---

## Proposed config entries

Not written to `config/` — same reason as 008a: they land with slice 008's config loader so
its rules apply from the first commit.

```yaml
session_vwap_refresh_mode:
  value: keep_up_to_date
  source: measurement
  note: >
    reqHistoricalData(keepUpToDate=True) accepted useRTH=False, returned a 04:00-anchored
    515-bar payload, and ran 32.03 min (12:34-13:06 ET, AMZN, 2026-08-10) with 376 updates,
    zero API errors and no dropped connection. Update cadence was ~5s (median 5.002,
    mean 5.106, min 4.196, max 14.477) versus the 120s re-request cadence it replaces --
    a 24x reduction in staleness on a value used as a stop level. Keep cum_refresh_s as a
    documented fallback, not as the default. NOT YET VERIFIED for five concurrent streams
    on one account -- see cum_refresh_s note.

cum_refresh_s:
  value: 120
  role: fallback
  source: constraint:ibkr
  note: >
    No longer the default path for session VWAP; retained for when keepUpToDate is
    unavailable. The 120s figure exists because IBKR's 60-requests-per-10-minutes budget is
    PER ACCOUNT, so symbol processes divide it rather than multiplying it: five processes at
    30s would be 100 requests per ten minutes against a budget of 60. That arithmetic stops
    binding under keepUpToDate, which holds ONE request open per symbol -- but IBKR limits
    simultaneous open historical requests separately, and that limit is untested here.
    Under a broker without a per-account request budget this whole key becomes unnecessary.

streaming_bar_update_semantics:
  value: revise_in_place
  source: constraint:ibkr
  note: >
    The last bar is REVISED, not appended: 344 of 376 updates restated the forming minute,
    32 appended a new one. Mutated fields are average(WAP), barCount, close, high, low,
    volume -- open is not. Any accumulator MUST replace the forming minute's contribution,
    never add to it. Measured cost of getting this wrong over 33 bars: VWAP off by only
    +0.214 cents (the repeated counts sit at nearly the same price and cancel), but volume
    overstated 5.94x -- 4,730,374 against a true 796,911. The exposure is RVOL, whose
    denominator would be ~6x too large, far more than session VWAP. Under another broker,
    re-measure: append-only streaming would invert this rule entirely.
```

---

## For whoever picks up §6b.1b

1. **Build the replace path, not an accumulate path.** The forming minute is restated ~11
   times a minute. Adding is wrong, and it will look almost right on VWAP (0.2¢) while being
   6× wrong on volume — the worst possible failure signature, since the number you would
   sanity-check is the one that stays plausible.
2. **The 04:00 anchor needs no seam.** The initial payload already reaches 04:00 and keeps
   that anchor as it grows. No join, so no join bug.
3. **Test five concurrent streams before removing the cadence.** That is the one claim in
   this note resting on an untested limit.

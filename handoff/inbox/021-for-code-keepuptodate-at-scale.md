---
id: 021
title: keepUpToDate at the open, five streams, full session
status: READY
blocks: [S010-attach-a-symbol-and-the-context-block]
type: investigation
owner: claude-code
requires: a full regular session, started by 09:25 ET
---

# 021 — `keepUpToDate` at the open, at five streams, for a full session

**One run closes all three of 008b's deviations.** They were listed separately but they
share a window: five symbols, started at 09:25, held to the close. Running them apart would
cost three mornings and would still not answer the interaction below.

| 008b deviation | What it left open |
|---|---|
| 1 — window did not span the open | Cadence at the heaviest print rate of the day is unmeasured |
| 2 — 32 minutes, not a session | Six hours, and the 16:00 boundary under `useRTH=False`, untested |
| 3 — one symbol, one process | **Five concurrent streams on one account untested** |

**And it answers something none of them could separately: whether cadence degrades when
five streams share one account.** 008b measured a median of **5.002 s on one stream**. If
five streams median 25 s, the ~5 s figure was a single-stream artifact and
`session_vwap_refresh_mode: keep_up_to_date` needs revisiting before it reaches a
five-symbol console. **That number is the point of this task.**

---

## Standing constraints

- **Read-only, `readonly=True`.** No `tws_order` import, no `reqExecutions`, no orders.
- **`ib_async` only.** `__main__` guard. Timeout-guarded calls.
- **Five open requests, issued once.** No re-request, no polling, no loop that calls the
  API. The only repeated call is `ib.sleep()`, which pumps the loop and issues nothing.
- **Use a distinct `clientId`** so this is separable from anything else on the connection.
- **Write to disk continuously**, not at the end. A six-hour run that buffers in memory and
  dies at 15:50 loses six hours. Append each callback to JSONL as it arrives, and flush.
- **This holds five open historical requests against the documented 50-simultaneous cap.**
  It consumes no tick-by-tick slots, so it does not compete with the 5-slot T&S budget — but
  if you are trading that morning, know it is running.

---

## Method

**Start by 09:25 ET.** The pre-open window is deliberate: it is when the terminal would
attach for a 1-minute ORB, so it is the window that must be measured.

Five liquid US equities, ideally including **at least one with a large pre-market gap** —
the interesting cadence question is whether a name printing heavily behaves differently from
a quiet one, and a normal morning will not supply that contrast on its own.

```python
for contract in five:
    ib.reqHistoricalData(contract, endDateTime="", durationStr="1 D",
                         barSizeSetting="1 min", whatToShow="TRADES",
                         useRTH=False, formatDate=1, keepUpToDate=True)
```

Hold to **16:05 ET** — five minutes past the close, so the boundary behaviour is observed
rather than inferred.

**Log per callback, per symbol**: wall-clock received, bar timestamp, update kind
(`REVISE_IN_PLACE` / `APPEND_NEW_BAR`), and the bar's `volume` and `average`.

---

## Record — six things

1. **Do all five accept?** If any is rejected, the exact error code, the symbol, and
   **which ordinal request failed** — the fifth failing means a lower cap than documented.

2. **Cadence per stream, bucketed by period.** Median, mean, min, max for each of:
   **09:25–09:30 · 09:30–10:00 · 10:00–12:00 · 12:00–15:30 · 15:30–16:00.**
   **The 09:30–10:00 bucket is the one that matters** — it is when the ORB playbooks trade
   and when session VWAP moves fastest.

3. **Cadence at five streams against 008b's one-stream baseline of median 5.002 s.**
   State the ratio plainly. **This is the headline.**

4. **Does cadence track print rate?** For each symbol, per minute, record updates received
   alongside that minute's volume, and **say whether they correlate.** 008b saw the ~5 s beat
   hold across a 6× volume swing and called that *suggestive, not established.* The open
   provides a far larger swing. **Answer it or say it remains unanswered — do not repeat
   "suggestive."**

5. **Survival.** Any drop, per stream, with its wall-clock time and whether the series
   resumed or restarted. **And what happens at 16:00 under `useRTH=False`** — does the
   stream continue into post-market, stop, or error?

6. **Does the 04:00 anchor hold for six hours?** 008b saw it hold for 32 minutes without
   sliding. Confirm the earliest bar is still `04:00` at 16:00, per stream.

---

## Interpretation, decided in advance

- **Five accept, cadence in 09:30–10:00 stays within ~2× of 5 s** ⇒ `keep_up_to_date` stands
  as the default for a five-symbol console. Record the measured figure; **do not carry
  008b's single-stream number forward as though it applied.**
- **Cadence degrades materially** — say, median beyond 30 s at five streams ⇒ the staleness
  advantage over `cum_refresh_s: 120` shrinks from 24× to under 4×, **and the decision
  reopens.** Record the numbers and leave the config as it is; the change is a design
  decision, not a probe's to make.
- **Any stream rejected or dropping repeatedly** ⇒ the simultaneous-request limit binds
  below five. **Record the number that works**, because it caps how many symbols a console
  can carry, which is a design constraint rather than a tuning value.

---

## Deliverable

`handoff/done/021-for-code-keepuptodate-at-scale.md`, readable cold:

1. **The six answers with their actual numbers**, and the cadence table by period and symbol.
2. **The five-stream vs one-stream comparison stated as a ratio**, up front. It is the reason
   the task exists.
3. **Environment**: TWS or Gateway, version, `clientId`, symbols, exact window, subscriptions.
4. **What you could not do**, and why. An empty section here is suspicious.
5. **Proposed config changes** — key, value, `source:`, `note:` — for anything that resolves.
   **Do not write them into `config/`**; they land with the config loader slice so its rules apply
   from the first commit.

**If the run dies mid-session, file what you have and say when it died.** Four hours of
measured cadence is a result. **A silent gap presented as a completed run is not.**

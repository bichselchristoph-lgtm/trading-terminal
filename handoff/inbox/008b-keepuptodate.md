---
id: 008b
title: Does keepUpToDate hold a session-length window open?
status: READY
blocks: []
type: investigation
owner: claude-code
requires: live regular-session hours
---

# 008b — `keepUpToDate=True` over a session-length window

**Split out of 008a because it must run during a live session.** The other tests work on
completed data at any hour; this one observes updates arriving, so **running it after the
close would show nothing and could be misread as "does not work."**

**It blocks nothing.** `SPEC.md` §6b.1b builds the periodic re-request first, because that
is known to work. This decides whether that path is replaced or kept.

---

## Why it matters

Session VWAP currently refreshes by **re-requesting on a cadence, defaulted to 120 s** —
because IBKR's 60-requests-per-10-minutes budget is **per account**, so symbol processes
divide it rather than multiplying it. Five processes at 30 s would be 100 requests per ten
minutes against a budget of 60.

**`reqHistoricalData(keepUpToDate=True)` holds the request open and pushes bar updates as
they form.** If that works over a session-length window it removes two things at once: the
pacing arithmetic, and **the two-minute staleness on a value used as a stop level** — whose
rate of change is highest in the first thirty minutes, exactly when the ORB playbooks trade.

Documented restriction: `endDateTime` must be empty. **Whether it tolerates a 04:00-anchored
`useRTH=False` window across six hours is stated nowhere.**

---

## Standing constraints

- **Read-only, `readonly=True`.** No `tws_order` import, no `reqExecutions`, no orders.
- **`ib_async` only.** Guard synchronous calls with a timeout — the default is wait-forever.
- `__main__` guard on the module. No connection at import.
- One symbol. One open request. **Do not loop or re-request.**

---

## Method

Run during regular hours, at least 30 minutes, ideally spanning 10:00 so a quiet and an
active stretch are both covered.

```python
bars = ib.reqHistoricalData(contract, endDateTime="", durationStr="1 D",
                            barSizeSetting="1 min", whatToShow="TRADES",
                            useRTH=False, formatDate=1, keepUpToDate=True)
```

Log **every** update callback: wall-clock time received, the bar's own timestamp, and
whether the update **appended a new bar or revised the existing last one**.

---

## Record — five things

1. **Does it accept `useRTH=False` at all?** Exact error code and message if not.
2. **Does the initial payload reach back to 04:00**, or does `keepUpToDate` silently narrow
   the window? Give the earliest bar timestamp.
3. **Update cadence** — roughly once a minute on bar close, or more often as the forming
   bar revises?
4. **Does it survive 30 minutes without disconnecting?** Note any reconnect, and whether
   the series resumed or restarted.
5. **Is the last bar revised in place?** This is the one with a consequence: **if it is,
   recomputing session VWAP means replacing the forming minute's contribution, not adding
   to it. Adding would double-count that minute** — a silent few-cent error on a stop level,
   which is precisely the class of defect this project exists to prevent.

---

## Interpretation, decided in advance

- **Works, reaches 04:00, survives 30 minutes** ⇒ it replaces the cadence. `cum_refresh_s`
  becomes a fallback rather than the default, and §6b.1b's pacing arithmetic stops binding.
- **Works but narrows the window** ⇒ combine: one historical request for 04:00 → now, then
  `keepUpToDate` from there. **Record exactly where the seam falls** — it is a join, and
  joins are where double-counting lives.
- **Fails or drops** ⇒ the 120 s cadence stands. **Record the failure mode**, so nobody
  tries this again from memory in six months.

---

## Deliverable

`handoff/done/008b-keepuptodate.md` — the five answers with the actual log excerpts, the
environment (TWS or Gateway, version, subscriptions, symbol, wall-clock window), and a
proposed config entry if it resolves. **If it could not be run — wrong hours, no
subscription — record it as unrun with the reason.** An unrun test is a known gap; a
guessed answer is a well-formed value answering a different question.

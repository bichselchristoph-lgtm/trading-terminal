---
id: 084
title: The reduced RVOL curve is cached in memory for the trading day
type: task
class: product
story: S034
epic: 4
owner: claude-code
depends: 083
touches: the RVOL curve fetch and reduction path
mockup: ATTACHED mockup — the context block and its states
uat: c045
bugs:
  - id: B-138
    action: mitigate
---

**Status** WRITTEN

# 084 — cache the curve, not the bars

**Do not start until 083 is done.** The cache key includes the anchor, and the
anchor does not exist until 083 lands.

---

## 0. Is this task for you

**If `handoff/inbox/084-for-code-task-rvol-curve-cache.md` exists in your tree,
`handoff/done/083-*.md` does exist, and no file beginning `084-` exists in
`handoff/done/`, this task is for you. Otherwise stop reading and ignore this
message.**

---

## 1. Why

**Christoph switches between the same few tickers repeatedly through a session.**
Today every attach of AMZN re-fetches 20 sessions of one-minute bars and
re-reduces them — the same computation, from the same window, minutes apart.

**Task 082 measured that request at 15 to over 60 seconds with a 60% timeout
rate on AMZN under concurrent dispatch.** Caching does not fix the contention;
it removes the request entirely on every attach after the first. **RVOL then
lands with `ADR% used` in about two seconds instead of fifteen to sixty.**

---

## 2. Part 0 — read first

1. **`warm()`, `_warmed()`, `_ROLES` and `call_many()` in `live/attach/ibkr.py`
   are still in the tree, unused by the live dispatch path since task 080.**
   Read them. **If a usable caching primitive already exists there, say so and
   reuse it rather than building a second one.** A second cache alongside a
   dormant first one is a second store.
2. **How the session date is currently determined**, if it is anywhere. The
   cache is scoped to a trading day and needs one definition of that, not a new
   one.

---

## 3. Part 1 — what is cached

**The reduced curve. Not the raw bars.**

About 390 medians per symbol, not 19,200 bars. **The raw bars are already
discarded after reduction today and that does not change** — caching them would
multiply the memory cost by fifty for no benefit.

**Key: symbol + anchor + session date.** All three.

- **Symbol** — obvious.
- **Anchor** — 083's `rvol_anchor`. **Serving an RTH curve to an ETH numerator
  is exactly B-049**, arriving through a new door.
- **Session date** — the cache is a trading-day cache. On a new session date
  every entry is stale and must not be served.

**In memory only. Nothing is written to disk.**

**Say plainly why, because it is the part most likely to be revisited:**
historical bar data is retroactively rewritten by corporate actions. A split
rescales volume across the entire history, so a curve cached yesterday is
silently wrong today **for exactly the names most likely to be worth trading**
— and a wrong denominator does not refuse, it renders a plausible number. The
20-session window also shifts every day, so a cross-day cache saves one request
per symbol per day while carrying that risk. **The intra-day win is the whole
value and memory delivers all of it.**

---

## 4. Part 2 — how it behaves

**A hit skips the request entirely.** No wire call, no pacing-guard
consultation needed because no request is made.

**A miss behaves exactly as today.** Fetch, reduce, store, render.

**The sector curve is cached on the same terms**, keyed on the ETF symbol.
**Two symbols mapping to the same sector share one entry** — that is a real
saving and it must not be defeated by keying on the attached symbol instead of
the ETF.

**Cancel-on-switch does not evict.** Attaching away from AMZN and back is the
case this exists for.

**Bounded.** A session cannot attach unboundedly many symbols, but the cache
must not be able to grow without limit — **state the bound you chose and why.**

---

## 5. What you may NOT do

**No disk. No file. No database.** §3 says why.

**Do not cache anything else** — not `rth_dailies`, not the sector mapping, not
the price stream. Only the reduced curve. **Not this task's.**

**Do not change what RVOL computes.** Only where the curve comes from.

**Do not fix the forming-bar sawtooth.** Separate, ruled, not this task's.

**Do not touch `request_timeout_s`.**

---

## 6. Exit tests

**Seen red against real pre-fix code before accepted green.**

**Green.** Second attach of the same symbol in the same session issues no curve
request and renders the same values as the first.

**Identity — the important one.** **A cached curve is identical to a freshly
computed one**, value by value. Same shape as S035's two-attach-times seam test,
which asserts identity to the cent rather than approximate agreement. **A cache
that returns nearly the right curve is worse than no cache**, because the error
is invisible and permanent for the session.

**Key isolation, three tests, each red for a different reason:**
- Changing the anchor must miss, not hit.
- Changing the session date must miss, not hit.
- Two symbols sharing a sector ETF must **hit** on the sector curve.

**Refusal.** A failed fetch must not populate the cache with a partial or empty
curve. **A cached refusal would make one bad attach poison the whole session** —
and it would look exactly like a fast, correct one.

**Fixture.** No test may read a state the shared fixture guarantees — B-136.

**UAT.** `christoph/open/045`. Not yours to perform or mark.

---

## 7. What the done-note must state

Whether an existing primitive was reused or a new one built, and why. The bound
you chose. **Measured wall time for a second attach of the same symbol against
the first** — that number is the whole point of the task. Which tests were seen
red and against what.

`verify.ps1` runs as the last action. Do not paste or summarise it.

---

## 8. The prompt

```
Do inbox 084
```

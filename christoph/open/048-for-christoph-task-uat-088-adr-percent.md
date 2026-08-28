---
id: c048
title: UAT for 088 — ADR% used across the day boundary
type: task
class: product
uat_for: 088
depends: 088
---

# c048 — UAT for 088

**Needs two attaches at different times of day, so it spans a session rather
than taking twenty minutes.** Nothing here is hard; the waiting is the cost.

---

## A. The pre-session attach — the one that produced the defect

1. **Attach a symbol at or shortly after 04:00 ET.**
2. **Read `ADR% used`.**

**It must not report a full day's range.** Last time it read `106.8% of $12.26
ADR20 RTH` fifty seconds into the session.

3. **What does it say now?** Copy the row verbatim, including the basis tail.
4. **If it refuses, does the refusal say why** — and is it distinguishable from
   a failed fetch? **Three states must be tellable apart: a computed value, a
   session that has not started, and a request that failed.**

## B. The mid-session attach

5. **Attach the same symbol again after 10:00 ET.**
6. **Read `ADR% used`.** Does the percentage look like the range so far today,
   measured against your chart?

**This is the one place your own chart is the reference.** A number that looks
plausible and is wrong is the failure mode this indicator has already had once.

## C. The boundary itself

7. **If you happen to be at the terminal near 04:00**, attach a minute before
   and a minute after. **Does the row change from one state to the other
   cleanly, or does it show a full day's range on either side?**

**Optional.** Skip it if the timing does not suit — 088 is required to have a
test at the rollover, so this is confirmation rather than the only check.

## D. The basis

8. **Does the row still read `of $X ADR20 RTH`?**
9. **If 088 found that ADR%'s basis is configurable rather than fixed**, the
   label may now name the basis differently. **Whatever it says, does the
   numerator and the denominator being on the same footing read clearly to
   you?**

---

## What is NOT being checked

**The freshness age, the flicker, or the dead stream.** Those are 087 and
c047.

**RVOL.** Its `– (no bars today)` at an early attach is correct behaviour for an
RTH anchor, not a defect.

**Whether ADR20 itself is right.** The twenty-session average is ruled and is
not in question here — only what the percentage of it is measured over.

Write your answers into this file's copy and retire it the usual way.

---
id: c043
title: UAT for 080 — the two-stage attach and the live panel
type: task
class: product
uat_for: 080
depends: 080
---

# c043 — UAT for 080

**Live, during market hours. Twenty minutes. Do not run before 080 lands.**

**c041 is a separate UAT for task 078 and still stands.** Run that one first if
you have not; it checks a different thing.

## What you are checking

**Four questions, and only the first is about speed.**

---

## A. Is the terminal usable before the context arrives

1. Attach **AMZN**. **Start counting when you press enter.**
2. **How long until the symbol and a price are on screen?** A rough count is
   fine — the number that matters is whether it is *about a second* or *about
   a minute*.
3. **Could you have sized and staged an order at that moment**, from your own
   chart levels, without waiting for anything else?

**If the answer to 3 is no, the whole task has missed**, whatever the timings
say.

## B. Do the rows arrive separately, and is that comfortable

4. On the same attach, watch the rows fill. **Expect `ADR% used` and `VWAP`
   within a couple of seconds and `RVOL` to say `pending` for up to a minute.**
5. **Is one row sitting on `pending` while the others are filled comfortable,
   or does it read as broken?**

**This is the question only you can answer**, and it is the one the design
reversed a previous ruling to reach. If it reads as broken, say so plainly —
that is a real finding, not a complaint.

## C. Does the freshness age behave

6. **Read the number in the header.** It should tick — 3s, 5s, 4s. **A ticking
   number is the panel proving its own check is running.**
7. **Does it ever go amber during ordinary trading?** It should not. Amber past
   20 seconds means the stream stalled. **If amber appears several times an
   hour with no obvious cause, 20 seconds is too low and the threshold needs
   refitting — that is a finding, not a fault.**
8. **Does it ever go blank?** A blank header means the freshness check itself
   is broken. **Report it immediately if you see it.**

## D. The sector reading

9. **Does `1.4x vs XLC` name the right ETF for the symbol you attached?**
10. **If the sector reading ever goes amber on its own** while `0.86x own`
    stays normal, note when and what you were attached to.
11. **Honest question, and the answer may be no:** across this session, **did
    you look at the sector-relative number at all?** If not, it is worth
    knowing — dropping it would remove a whole second stream and everything
    built on it.

---

## What is NOT being checked

**Whether the numbers are right.** That is c013's outstanding check against
your own charts and it is still owed separately.

**Total time to a complete panel.** It will still be fifteen to sixty seconds
before `RVOL` lands. **That is expected and is not what this task set out to
change** — the change is that you are not waiting on it to trade.

Write your answers into this file's copy and retire it the usual way.

---
id: 021
title: Does a 52-week high disagree with your chart, in the right direction
status: OPEN
type: EXTERNAL
owner: christoph
closes: 041's UAT row
---

**Status** OPEN

# c021 — the disagreement is the test

**`041` anchored thirteen levels to RTH, including `52wH`, `52wL` and `ATH`.** You trade with ETH
charts enabled, so **on some names the terminal and your chart will now disagree — and that is the
ruling working, not a defect.**

**This UAT checks that the disagreement points the right way.** A terminal value *above* the ETH
chart's 52-week high would be impossible and would mean the ruling did not land.

---

## Find a name where the extreme printed outside regular hours

**Most names will agree, which proves nothing.** You need one whose 52-week high or low was made in
pre-market or after-hours — typically a gap-up on news, an earnings reaction, or a small cap that
ran overnight.

**If you cannot find one quickly, say so and stop.** An unfound case is a result. Do not spend more
than a few minutes hunting.

---

## The check

| | |
|---|---|
| Symbol | |
| Terminal `52wH` | `$___.__` |
| TradingView, **ETH** chart | `___` |
| Did they differ? | yes / no |
| **If yes: is the terminal's value LOWER?** | yes / no |

**The terminal's value must be lower or equal, never higher.** RTH is a subset of ETH, so the
regular-session high cannot exceed the all-hours high. **A terminal value above the chart's is a
defect, and the most likely cause is that the level did not actually move to RTH.**

Repeat for `52wL` if convenient — the same logic inverts: **the terminal's low must be higher or
equal.**

---

## What this does not test

**It does not test whether RTH is the right choice.** That was a ruling, made on the composition
argument: `52wH` must be the maximum of the months, which must be the maximum of the weeks, which
must be the maximum of the days — and `PDH` is RTH.

**This only confirms the ruling reached the code.**

---

## What to do with this

Save into `christoph/done/021-52-week-basis.md` — the filled-in file. Then tell chat.

**If every name you try agrees, record that.** It means the check found nothing, which is different
from the check passing.

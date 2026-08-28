---
id: c047
title: UAT for 087 — the age, the flicker, and the dead stream
type: task
class: product
uat_for: 087
depends: 087
---

# c047 — UAT for 087

**Two sittings. About twenty minutes of attention, but one part needs the
terminal left running for an hour.** Market hours preferred; a closed market
still works for everything except question B.

**You found all three of these yourself.** This checks whether they are gone,
not whether they exist.

---

## A. The age — does it move while everything is healthy

1. Attach a symbol with TWS live.
2. **Watch the number at the right of the ATTACHED header for one minute.**

**It should move: 1s, 2s, 3s, 4s, back to 0s or 1s as a push lands, and round
again.**

3. **Does it sit on `0s`?** That is the old defect and it is the one that
   matters most — **a frozen `0s` looks exactly like a working panel.**
4. **Does it move smoothly, or jump?**

## B. The dead stream — does anything say so

5. **Leave the terminal running for an hour**, attached, and come back.
6. **Read HEALTH's two stream rows.** If either has stopped updating,
   **is it marked?** Last time both rendered in identical plain text while one
   had been dead for a hundred minutes.
7. **Read the RVOL row on ATTACHED.** If a stream is dead, **does the row still
   say `pending`, or has it become a refusal naming what did not arrive?**

**A `pending` that never resolves is the thing being fixed.** If it is still
sitting there after an hour, this fails regardless of anything else.

## C. The flicker

8. Attach one symbol. **Watch the whole screen for two minutes.** Any flicker?
9. **Switch between three or four symbols as you normally would**, then watch
   again for two minutes.
10. **If there is still flicker, roughly how often — and does it get worse the
    more you attach?** That difference is the diagnosis, so it is worth timing
    roughly rather than describing.

## D. Judgment

11. **Reading the panel as a trader: do you now believe the freshness number?**
    The whole argument for putting it there was that a moving number proves the
    check is running. **If it moves but you still find yourself not trusting
    it, say so** — that is a design finding, not a bug.

---

## What is NOT being checked

**`ADR% used`.** That is 088 and its own UAT. **If it still reads oddly at an
early attach, that is expected here** — do not report it as a failure of this
task.

**Whether RVOL's numbers are right.** Still c013, still owed separately.

Write your answers into this file's copy and retire it the usual way.

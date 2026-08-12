# 011 · UAT — shrink it, grow it back

**Task** 018
**Status** RUNNING · **Owner** Christoph only · **Blocks** 018 reaching DONE
**Written** 2026-08-12 by the design session

---

## 1. What changed

**UAT `009` found that the too-small refusal fires only at launch.** Start narrow and it refuses
correctly; shrink the window afterwards and panels truncate to `WATCHLIS...` instead. You said
it didn't bother you — you know to upsize. **The rule is *never a silently clipped panel*, and a
rule that holds only at launch is not the rule**, so it was fixed.

Two things came out of building it that are worth knowing before you look:

**The first fix silently did nothing.** The resize handler was attached to the app, and Textual
delivers resize events to widgets, not to the app — so it looked right and never ran once. It
was caught only because a test failed. **Had the test been weaker, this UAT would have found
nothing wrong and the defect would have shipped twice.**

**Rows 5 and 8 now have names**, and **row 9 says deferred rather than unassigned.**

---

## 2. What to do

```powershell
cd D:\Dev\momentum
C:\venvs\trading\Scripts\python.exe -m live.tui.app
```

**Three states, in this order:**

**A · At 209 × 54**, your normal size.

**B · Drag it narrow**, under about 75 columns.

**C · Drag it back** to 209 × 54.

---

## 3. The one question

> **Did the screen ever show me a panel I could not read?**

Not whether it looked right. Not whether the transition was smooth. **Whether at any moment —
including mid-drag — there was a panel on screen you could not make sense of.**

---

## 4. Record your answer here

**A · Shrinking below ~75 columns: did the refusal appear, with zero panels?**

- [ ] yes
- [ ] no — panels still rendered

**B · Growing back to 209 × 54: did the panels come back?**

- [ ] yes
- [ ] no — the screen stayed refused

**C · Did the refusal message show the size you were actually at?**
Shrink to two different narrow sizes and check the numbers change. **A message naming the size
you launched at rather than the size you are at is the defect this whole task is about, wearing
a different hat.**

- [ ] yes — the numbers tracked the window
- [ ] no — it showed: `________________`

**D · At any point, including mid-drag, was there a panel you could not read?**

- [ ] no
- [ ] yes — describe it: `________________________________`

**E · Row 9 now reads `[ NOT BUILT ] (deferred - not core, revisit later)`.**
Rows 5 and 8 read `select` and `submit`. **Is that what you meant?**

- [ ] yes
- [ ] no: `________________________________`

**F · Anything unexpected.** Free text:

`________________________________________________`

---

Signed `________________` Date/time `________________`

*Once signed, copy this file to `christoph/done/`, verify it is byte-identical, then remove it
from `christoph/open/`.*

---

## 5. One limit, stated rather than hidden

**`deferred` and `slice not assigned` differ only in words, not in shape.**

Every other refusal in this terminal is distinguishable without reading — a bracketed badge
means *the machinery does not exist*, an em-dash and a parenthesis means *the input is missing*.
**These two are both `[ NOT BUILT ]` with different text inside the parentheses.**

Claude Code declined to invent a `[ DEFERRED ]` badge because `SPEC.md` §4's vocabulary is
closed and adding to it is a spec change, not a code change. **That was the right call.** The
design session's recommendation is to leave it — the distinction matters to the two of us, not
to a glance.

**If you disagree, say so in F.** It is a §4 amendment, and it is yours.

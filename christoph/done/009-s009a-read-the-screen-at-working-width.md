# 009 · UAT — read the screen at the width you actually trade at

**Slice** S009a
**Status** RUNNING · **Owner** Christoph only · **Blocks** S009a reaching DONE
**Written** 2026-08-12 by the design session

> **This is not a pre-registration.** S009a's results are already reported, so asking you to
> predict anything now would be theatre. The question here is comprehension, and it can only be
> answered after looking.

---

## 1. What S009 got wrong, in one number

Your terminal is **209 × 54**. Three tiles across 209 columns, minus padding, gives each panel
**67 columns. The panel was built at 71.**

**Four columns.** That is the entire caption-wrap defect. The test suite checked 80, 120 and
240 — **80 and 240 straddled 209 without ever covering it.** Nothing was subtly wrong; every
panel was four columns too wide, every time.

S009a fixes the cause rather than the symptom: **nothing renders at a width it was not measured
against.** 209 × 54 is now the primary snapshot width.

---

## 2. What to do

**Run the app twice.**

**A · At your normal working size**, maximised, 209 × 54.

**B · At a size small enough to break it.** Drag the window narrow — under about 75 columns.
You should get **one stated message and zero panels**, never a clipped or wrapped one.

---

## 3. What you are judging

**Not whether it looks nice.** The criterion is one question, applied to every line on screen:

> **Can I tell what this means without asking anyone?**

Four things specifically:

**3a · The captions.** Every panel's top border carries a provenance stamp. At 209 nothing
should truncate. **If anything wraps onto a second line, the fix did not hold.**

**3b · `[ NOT BUILT · S010 ]` versus `— (no account snapshot)`.** These say different things:
*the machinery does not exist* against *the machinery exists and the input is missing*. **They
are distinguished by shape, not colour** — a bracketed badge against an em-dash and a
parenthesis. **Can you tell them apart at a glance, without being told the rule?**

**3c · The PIPELINE panel.** Twelve stages, one row each. It exists because you asked whether
there should be an indicator section — and nothing on screen could say *not yet* as opposed to
*not in the design*. **Does it now answer that question by itself?**

**3d · The too-small message.** It should name **which tile ran out and by how much**, not just
the window. **Does it tell you what to do — make the window wider — or only that something is
wrong?**

---

## 4. Two things to look at specifically

**`manage` renders `[ NOT BUILT ] (slice not assigned)`.** You have since decided it is
**deferred, not core**. Those are different statements and the screen currently makes the
weaker one. **Confirm the wording you want**; the change rides in the next task.

**At 80 columns the PIPELINE panel truncates to `[ NOT …` on every row.** It is honest — the
truncation renders — but it cannot say which slice fills which stage. **This does not arise at
209.** Worth knowing it exists rather than discovering it on a laptop.

---

## 5. Record your answer here

**A · At 209 × 54, did any line wrap or overrun?**

- [x ] no — nothing wrapped
- [ ] yes — and here is which panel: `________________`

**B · Below ~75 columns, did you get one message and zero panels?**

- [ ] yes
- [ x] no — panels still rendered

**C · Was every refusal understandable without asking what it meant?**
If not, **name the exact string**, because a refusal nobody can read is worse than a blank:
refusal only appears if console is below ~75 colums. Resizing at a later point does not work.
`________________________________________________`

**D · Did the PIPELINE panel answer the indicator-section question by itself?**

- [ x] yes with some feature names missing. 
- [ ] no

**E · Anything on screen you did not expect.** Free text — this is the part most likely to find
something nobody thought to test:

`________________________________________________`

---

Signed `_Christoph_______________` Date/time `_____August 12, 2026 2:23pm___________`

*Once signed, copy this file to `christoph/done/`, verify it is byte-identical, then remove it
from `christoph/open/`.*

---

## 6. What this UAT does not cover

**The depth-ordering finding.** S009a observed that ARCA's book came back out of price order —
the best bid at index 6, not index 0 — and `012` captured 2.1 million ARCA depth records.
**That is not a screen question and is not yours to answer here.** It is recorded separately.

**Post-session depth availability.** S009a's probe ran pre-market and could not answer it.
Still open.

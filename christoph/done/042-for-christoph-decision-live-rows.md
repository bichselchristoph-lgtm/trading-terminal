---
id: c042
title: Live rows raise three questions the frozen panel never had
type: decision
spec: ATTACHED, LEVELS, UI
raises: S039
---

# c042 — three rulings that follow from making the rows live

**Your call. Three, each with a recommendation. All three exist only because
the rows now move.**

Mockup v0.2 draws all three my way so you can see them rather than imagine
them. It is marked PROPOSED and nothing builds from it until these are ruled.

---

## Ruling 1 — who owns price

**Recommendation: ATTACHED owns it. LEVELS reads it.**

S033 has the LEVELS rail rendering price between its above and below halves —
that is the rail's geometry and it is already ruled. Adding `Last $` to
ATTACHED puts one number on two panels.

**That is B-006 and B-004 again**, and worse than either: those were a static
address and a clock, whereas **two panels refreshing one price on independent
paths can visibly disagree mid-session.** A trader reading $712.97 on one panel
and $713.04 on the other has no way to know which is current.

**Why ATTACHED rather than LEVELS:** the price is the attached symbol's
headline fact and it must exist in stage 1, before any level has been computed.
The rail can position itself around a price it reads without owning it.

**What it rules out:** two independently-refreshed prices, under any argument
about panel independence.

Yes, as recommended. Signed-off by Christoph, Aug 24, 2026	

## Ruling 2 — does the attach time leave the panel

**Recommendation: yes. One clock, and it is the as-of.**

While every value was frozen at attach, **the attach time was the as-of** — one
number doing both jobs, correctly. **Live rows split those two facts**, and
rendering both puts two clocks on one panel whose relationship is documented
nowhere. That is exactly B-004, which mockup v1.2 closed by removing
`since HH:MM`.

**The as-of is the one that has to be there.** SPEC.md is explicit: VWAP's rate
of change is highest in the first thirty minutes, which is when the ORB
playbooks trade, so **a VWAP-based stop staged at 09:34 against a value
computed at 09:32 should show both times.**

**Cost, stated:** you lose "when did I attach this" from the screen. It stays in
the record. If you want it on the panel, say so — but then the two clocks need
a stated relationship, and that sentence is the work.
No.

Attached panel has the atttached time of a symbols such  as QQQ  attached 03:28:51. Changes when symbol changes.
Healht panel has attached for the terminal. At what time did the terminal connect for the first time. independent from a sybmmol. Does not change when symbol changes. 


Signed-off by Christoph, Aug 24, 2026	

## Ruling 3 — what makes a stream dead

**Recommendation: three consecutive missed updates, unfitted and labelled so.**

Task 008b measured median 5.002s, mean 5.106, min 4.196, **max 14.477** across
376 updates. **A single missed beat is normal; the max already ran to three
beats.** Three consecutive misses is roughly 15 seconds of silence, which is
long enough not to fire on ordinary jitter and short enough to matter on a stop
level.

**It is a threshold, so it is yours, and it has not been fitted** — one
32-minute session on one symbol is not a distribution. **It should render as
unfitted wherever its provenance is shown, like the ATR 2x multiplier.**

Yes, Signed-off by Christoph, Aug 24, 2026	---

## What follows on a yes to all three

ATTACHED and UI change; LEVELS gains a sentence saying it reads price rather
than owning it; **story S039 for the live-refresh mechanism itself**, which is
separate from S038's two-stage split and could ship before it.

## The thing I have not checked, said plainly

**Whether the current build refreshes anything after attach is unread.** Task
075 instrumented the attach only. `SPEC.md` specifies `keepUpToDate=True` as
the default with a 120-second cadence as fallback — **that is what the spec
says, not what I have seen the code do.** A task should establish it by reading
before S039 is written, or S039 will be specified against a build nobody
looked at.

**One word per ruling is all this needs back.**
Signed-off by Christoph, Aug 24, 2026	
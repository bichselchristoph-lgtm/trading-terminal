---
id: c044
title: UAT for 083 — the RVOL anchor renders and both halves agree
type: task
class: product
uat_for: 083
depends: 083
---

# c044 — UAT for 083

**Ten minutes. Can be run with the market closed** — this checks a label and a
basis, not live behaviour.

## What changed

The RVOL row now says which session its ratio is measured over, and the anchor
is a config setting rather than a fixed constant. Default RTH.

```
 RVOL rth    0.86x own · 1.4x vs XLC
```

## Steps

1. Attach any symbol. **Does the row read `RVOL rth`?**
2. **Set `rvol_anchor: eth` in config, restart, attach the same symbol.**
   Does the row read `RVOL eth`?
3. **Do the numbers change between the two?** They should — a different session
   basis is a different measurement. **If both anchors produce identical
   numbers, that is a defect**, not a reassurance: it means one half of the
   ratio is ignoring the setting.
4. Set it back to `rth`.

## The questions

**A.** Does the anchor render on every state of the row — value, `pending`, and
`unavailable`?

Yes. Signed-off by Christoph, Aug 24, 2026	


**B.** With `rth`, does the RVOL row land noticeably sooner than it did before?
The curve request should be about 59% smaller. **Rough impression is enough;
the measured version is in the done-note.**
Yes. Signed-off by Christoph, Aug 24, 2026	

**C.** Reading the panel as a trader rather than as a tester: **does `RVOL rth`
tell you something you wanted to know, or is it noise on a row you already
understood?** Say so plainly if it is the latter — the label was added on the
argument that every other row declares its basis, and that argument can be
wrong in practice.
Yes. Signed-off by Christoph, Aug 24, 2026	
## What is NOT being checked

**Whether RVOL's numbers are right.** That is c013 and it is still owed
separately.

**The one-minute sawtooth.** RVOL is understated at the top of each minute
because the numerator includes a forming bar. **Known, ruled, and not this
task's** — do not report it as a finding here.

Write your answers into this file's copy and retire it the usual way.

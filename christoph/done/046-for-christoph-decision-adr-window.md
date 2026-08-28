---
id: c046
title: The level rail windows to one ADR and truncates at five
type: decision
spec: LEVELS, UI
raises: S040
---

# c046 — the ADR window

**Your filter, with four amendments. Each is a sub-ruling and each has a
recommendation.**

## What you ruled

Filter the level set to those within one ADR above or below last price. If more
than five survive, sort nearest to furthest and truncate at five.

**It makes the thirteen missing levels affordable.** Twenty-three computed,
five rendered — the rail stops being a wall of numbers and the cost of building
the missing thirteen stops being a display problem.

---

## Amendment 1 — truncate per side, not globally

**Recommendation: nearest five above and nearest five below, each side
truncated independently.**

S033 has the rail rendering price between an above half and a below half.
**A global "closest five" can return five levels above price and none below.**
On a panel whose job is stops, that is exactly the wrong five — the level you
are stopping against is on one side, and it is the side that can vanish.

Yes. Signed-off by Christoph, Aug 24, 2026	

## Amendment 2 — the rail says what it is hiding

**Recommendation: `5 of 23 · 18 outside 1 ADR` on the rail.**

*It measures and sorts; nothing is removed.* The window is a view, not a
deletion — but **a panel showing five of twenty-three without saying so is
making a claim about relevance silently.** One line keeps that honest, and the
count self-clears as price moves.
Yes. Signed-off by Christoph, Aug 24, 2026	
## Amendment 3 — the boundary will flicker without hysteresis

**Recommendation: enters at 1.00 ADR, leaves at 1.10.**

Price refreshes every five seconds. **A level sitting near the boundary enters
and leaves the set repeatedly — rows appearing and disappearing while you are
reading them.** Same family as the RVOL sawtooth: a threshold evaluated against
a moving number, with no memory.

**The asymmetry is the whole mechanism.** Equal in and out thresholds do not
fix it; they relocate it.
Yes. Signed-off by Christoph, Aug 24, 2026	
## Amendment 4 — what happens when ADR is not there

**Recommendation: render every level, with the filter marked off.**

`ADR% used` can be `pending` for the first seconds of an attach and
`unavailable` after a failed fetch. **The window has no basis without it.**

**Never five levels chosen by an ADR that is missing or stale** — that is a
well-formed rail answering a different question, and it would look exactly like
a correct one. The unfiltered rail is long and obviously unfiltered; a wrongly
filtered rail is short and looks right.
Yes. Signed-off by Christoph, Aug 24, 2026	
---

## Noted, not recommended

**Late in the day, room left is what is reachable — not a full ADR.** At 80% of
the ADR consumed, a one-ADR window is roughly four times wider than the range
price can still cover, so the rail fills with levels today cannot reach.

**Not proposed as a change.** It needs your judgement in use before it is worth
specifying, and a window that changes width through the session is harder to
read than one that does not. **Worth revisiting after a week of use.**

---

## What follows on a yes

LEVELS and UI both change; a mockup for the windowed rail; **story S040**; and
**h067's scope is re-cut** — thirteen new levels computed, five rendered per
side, rather than thirteen new rows added to a rail that already renders ten.

**One word per amendment is all this needs back.**
Yes. Signed-off by Christoph, Aug 24, 2026	
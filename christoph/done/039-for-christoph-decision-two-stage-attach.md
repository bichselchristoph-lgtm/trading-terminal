---
id: c039
title: Attach splits into two stages — order-ready first, context second
type: decision
spec: ATTACHED, UI
raises: S038
supersedes: nothing
---

# c039 — two-stage attach

**Your call. Five sub-rulings below, each with a recommendation.**

## What this rests on

Task 075 measured twelve real attaches against live TWS. Two numbers decide this:

- **`reqContractDetails`: 0.23–0.25s, all twelve runs, no meaningful variance.**
- **The 20-session 1-minute intraday pull (the RVOL reference): 15.1s to 60s+, and AMZN pays it twice because its sector ETF pays it too.** Total attach ranged 15.8s to 143.4s.

The slow thing is not slow because of anything this codebase does. It is IBKR's historical-data service, and which end of that range you get is not ours to choose. **So the recommendation is not to make it faster. It is to stop waiting for it.**

**This also overturns 058.** 058 optimised the 1-year daily request. Measured, that request is the fastest wire call in every single run — 0.7 to 1.9s, no exceptions. It was never the bottleneck, and the design session said it was.

---

## Ruling 1 — does attach split into two stages at all?

**Recommendation: yes.**

Stage 1 resolves the contract and nothing else, and the terminal is order-ready. Stage 2 fills levels, RVOL, sector, tape — everything that needs history.

**What a yes commits you to:** the panel is deliberately incomplete for the first ten to sixty seconds after every attach, visibly and by design. That is the trade. Nothing arrives sooner overall; what changes is that the order path stops waiting behind the context path.

**What it rules out:** *(the field that stops this being re-proposed)* — optimising the 20D pull as the primary move. It stays available as a later, separate improvement to stage 2, but it is not the answer to "the switch is too slow", because its floor is not ours to set.

Signed-off by Christoph, Aug 24, 2026	

## Ruling 2 — what does stage 1 fetch?

**Recommendation: contract details only. Nothing historical, nothing streaming.**


Measured cost 0.24s. Anything added here is added to the number you actually feel.
Signed-off by Christoph, Aug 24, 2026	
## Ruling 3 — what do stage-2 fields show while pending?

**Recommendation: a designed pending state, distinct from refused, distinct from zero, and carrying no verdict colour.**

*A panel that renders a value with nothing behind it is worse than a panel that renders nothing* — this is exactly that case, and pending is a third state, not a variant of refused. "Not here yet" and "asked, came back empty" must not look alike on screen.
Signed-off by Christoph, Aug 24, 2026	
**This needs a mockup before it is built.**
Signed-off by Christoph, Aug 24, 2026	
## Ruling 4 — does stage 2 start automatically, or on a keypress?

**Recommendation: automatically, immediately after stage 1, in the background.**

You should never have to ask for context you always want.
Signed-off by Christoph, Aug 24, 2026	
## Ruling 5 — can a stage-2 failure ever block the order path?

**Recommendation: no. Never, for any reason.**
Signed-off by Christoph, Aug 24, 2026	
If stage 2 times out, the order path is unaffected and the pending fields become refused. This is the whole point of the split; without this ruling the split buys nothing.

---

## The gap you should know about before ruling

**There is no live price in this slice.** `open_tick_stream` unconditionally raises — S010 never built tape components into core. Read from the code, not inferred.

So stage 1 gives you the contract, and sizing has to take its price from you rather than from the terminal. **If you expect stage 1 to size against a live quote, that is a separate mechanism that does not exist yet**, and it should be its own story rather than a hidden assumption inside this one.

## What happens on a yes

ATTACHED and UI both change; a mockup for the pending state; story S038 authored; the two 075 defects folded in as part of the same work rather than patched separately.

**One word — the ruling — is all this needs back.**
Signed-off by Christoph, Aug 24, 2026	
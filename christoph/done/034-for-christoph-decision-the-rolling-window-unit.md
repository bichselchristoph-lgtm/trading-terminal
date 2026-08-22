---
id: 034
title: The rolling tape window — a duration or a count of prints
type: decision
bug: B-057
spec: TAPE-SPEC §17.1
relates: h050 (the tape window), h049 (validate the owned corpus)
blocks: every tape reading, since all of them are computed over this window
---

**Status** OPEN

# 034 — the rolling window unit

## What is on the screen today

**60 seconds, stepped 5 seconds. Neither number was fitted.** Both were chosen when the
tape component was first written and have never been measured against a real corpus.

Every tape reading — buyers, sellers, imbalance, absorption — is computed over this window.
**The unit is not a detail of the tape; it is the definition of what every tape number means.**

## The two candidates

| | **Duration — `last 60 seconds`** | **Count — `last 200 prints`** |
|---|---|---|
| Denominator | Seconds | Prints |
| On a heavily traded name | Thousands of prints. Stable | Reaches back a fraction of a second. Very twitchy |
| On a thin name | May hold too few prints to compute at all | Always computes — it waits until it has 200 |
| What the reading claims | *In the last minute* — always true | *In the last 200 prints* — **does not say how long ago that was** |

**The honest cost of the count window is that second row.** `buyers 340k in the last 200
prints` on a dead tape may reach back twenty minutes, which is a different claim from the one
the row appears to be making. **A duration never lies about its own recency.**

**The honest cost of the duration window is refusal.** On a thin name at 11:40, 60 seconds may
contain four prints, and a two-sided comparison over four prints is not a reading. That is a
refusal state, not an error — but it is a refusal that will fire regularly.

## The trap, and it only bites the count window

**IBKR historical tick data is filtered where the live stream is not.** This is already the
reason the tape baseline cannot be seeded from history: a baseline built from filtered history
and measured against unfiltered live prints compares two bases.

**A duration window is immune.** Its denominator is seconds, and filtering cannot change how
many seconds there are in a minute.

**A count window is not.** Its denominator *is* the print count — so filtering does not add
noise to it, **it rescales the entire instrument.** Odd lots were 64% of US trades and 83% of
trades above $250. If historical drops them, `last 200 prints` in replay and `last 200 prints`
live are two different windows wearing one name.

**That is the §7 archetype exactly: a well-formed value answering a different question.**

## What would settle it, and what it costs

**`h050` is the task that measures this** — print-count distributions per symbol and per
half-hour bucket, the per-symbol floor below which a window cannot compute, and the historical-
versus-live filter ratio.

**It is not cheap right now.** `h050` depends on `h049`, and `h049`'s corpus (`selection/phase3/`,
about 1.3 GB) is recorded as living only in the archived `momentum-harness` tree. **So this
question is currently gated behind an archive move that is yours, not a measurement that is
Claude Code's.**

## Already ruled out

- **Fitting the window on historical ticks alone.** Filtered history against unfiltered live is
  two bases; the fit would not transfer (tenet 6).
- **Changing the unit and the step in the same pass.** Two unfitted numbers moved together
  produce a result nobody can attribute.

## My recommendation

**Rule the duration window as current, with a stated print floor. Keep the count question open
and unruled, pending `h050`.**

Concretely, three lines:

1. **The rolling window is 60 seconds, stepped 5 seconds, and both numbers are recorded in
   `TAPE-SPEC` as unfitted** — stated as such, not silently.
2. **Below a stated minimum print count, the window refuses** rather than reporting a one-sided
   comparison. The floor is a number `h050` would produce; until then, a refusal that fires is
   better than a reading that is one-sided and looks two-sided.
3. **The count-based window is not rejected**, and this file records why it is attractive so it
   is not re-proposed from scratch: it is ready when it is ready, which is the right property on
   a thin name.

**Why not simply rule count-based now:** it is the option the filter trap makes unsafe to adopt
without measurement, and adopting it would silently change the meaning of every replay-derived
number against every live-derived one.

**Why not simply wait:** the terminal renders tape readings over the 60-second window today,
unfitted and unlabelled. Recording it as *current and unfitted, with a refusal floor* costs
nothing and stops the number claiming more than it can.

## To answer

**One of:**

- *"Duration stands, with the floor — count stays open."* (the recommendation)
- *"Count-based, and here is why the filter risk is acceptable."*
- *"Neither until `h050` runs — and here is what I will do about the archived corpus."*

**Copy this file to `christoph/done/` with your ruling and the date.**

`TAPE-SPEC §17.1` is then rewritten from the ruling, and `B-057` moves with the ruling in its
summary.
christoph's ruling aug 22 2026: Duration stands, with the floor — count stays open.
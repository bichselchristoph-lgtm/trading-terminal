---
id: 088
title: ADR% used reads 106.8% at an 04:00 attach — establish what its numerator is drawn from
type: task
class: product
story: S036
epic: 4
owner: claude-code
depends: none
touches: the ADR% computation and the request behind it
mockup: ATTACHED mockup — the context block and its states
uat: c048
bugs:
  - id: B-142
    action: fix
---

**Status** WRITTEN

# 088 — what day is ADR% measuring

**Read first. The fix depends on which of two causes is real, and they need
different fixes.**

---

## 0. Is this task for you

**If `handoff/inbox/088-for-code-task-adr-percent-day-boundary.md` exists in
your tree and no file beginning `088-` exists in `handoff/done/`, this task is
for you. Otherwise stop reading and ignore this message.**

---

## 1. What was observed

Christoph, live screen, 2026-08-24. **TSLA attached 04:00:50.**

```
 ADR% used   106.8% ▓▓▓▓▓▓▓▓▓▓▓▓▓ of $12.26 ADR20 RTH
 RVOL rth    – (no bars today) · pending
```

**A full average daily range consumed fifty seconds into the session is not a
plausible reading**, and 106.8% is close enough to exactly one whole day to be
a clue rather than noise.

**The row below it is the tell.** `RVOL rth` correctly reports *no bars today* —
the terminal knows there are no RTH bars yet. **One row knows the session has
not started while the row above it reports a complete day's range.**

---

## 2. Part 0 — the read that decides everything

**Read what the ADR% numerator's high and low are drawn from.** Specifically:

1. **Which request supplies them**, and **what window that request actually
   returned** at an 04:00 attach — not what it was asked for.
2. **Whether that window is today's session in progress, or the last completed
   session.**
3. **Which basis the numerator uses**, against a denominator labelled
   `ADR20 RTH`.

**Report all three as read. Do not fix before reporting.**

---

## 3. The two candidates, neither of them a finding

**Candidate A — the day boundary has not rolled.** At 04:00 ET a `1 D` request
may return **yesterday's completed session**. A whole day's range over a
20-day average lands near 100% by construction, which fits 106.8%.

**Candidate B — a basis mismatch.** The numerator drawn from extended-hours
bars while the denominator is `ADR20 RTH`. **This is B-049's shape in a
different indicator** — and ADR% was excluded from task 083's scope on the
grounds that its basis is *fixed by arithmetic*. **That assumption was inherited,
not verified, and this task is where it gets read.**

**They are not exclusive and both may hold.** The reading decides; argument
cannot.

---

## 4. Part 1 — the fix, once the cause is read

**If Candidate A: the row refuses rather than computing over a closed session.**
A range measured over a window that has already ended is a well-formed number
answering a different question. **`ADR% used — (session not started)` or the
equivalent in the existing refusal vocabulary** — the same shape `RVOL rth`
already uses one row below, which is the precedent to follow rather than a new
one to invent.

**If Candidate B: the numerator and the denominator take the same basis**, and
**the row's label states it** — as the RVOL row now does after 083.
**One key read by both halves, not two that agree**, and a test asserting they
are the same object rather than equal values. 083's divergence test is the
pattern; do not build a second shape.

**If both: fix both, and say in the done-note which one produced the 106.8%.**

---

## 5. What you may NOT do

**Do not touch the repaint path, the streams, or HEALTH.** That is 087. **Not
this task's.**

**Do not change `ADR20`'s own definition** — the twenty-session average is
ruled and is not in question. **Only the numerator and its basis are.**

**Do not add a config key unless Candidate B is what you find**, and if you do,
**one key read by both halves.**

**Do not change `request_timeout_s`** — B-132.

**Do not fix the forming-bar sawtooth.**

---

## 6. Exit tests

**Seen red against real pre-fix code before accepted green.**

**Green.** At a simulated 04:00 attach, the row does not report a full day's
range. **Assert the specific rendered text**, not that a substring appears —
B-126.

**Green.** At a mid-session attach, the row reports the range of the session in
progress, and the numerator's basis matches the denominator's.

**Refusal.** Whatever state a pre-session attach produces, **it is
distinguishable from a computed value and from a failed fetch.** Three states,
not two.

**Boundary.** **A test at the rollover itself** — the last minute before and
the first minute after. This is the case that produced the defect and it must
have a test, not an assumption.

**Divergence, if Candidate B holds.** Same shape as 083's: object identity, not
equal values.

**Fixture — B-136.**

**UAT.** `christoph/open/048`. Not yours to perform or mark.

---

## 7. What the done-note must state

The three reads from Part 0. **Which candidate produced the 106.8%**, stated as
what was read rather than what fits. Whether ADR%'s basis turned out to be
fixed by arithmetic as assumed, **or configurable like RVOL's** — because if it
is the latter, project instructions §8's classification is wrong in a second
place and that is worth more than the fix.

`verify.ps1` runs as the last action. Do not paste or summarise it.

---

## 8. The prompt

```
Do inbox 088
```

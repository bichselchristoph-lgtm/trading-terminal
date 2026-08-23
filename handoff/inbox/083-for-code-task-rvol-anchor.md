---
id: 083
title: RVOL's anchor becomes a configured choice, defaults to RTH, and renders
type: task
class: product
story: S034
epic: 4
owner: claude-code
depends: none
touches: the RVOL computation, its config, and the ATTACHED row that renders it
mockup: ATTACHED mockup — the context block and its states
uat: c044
bugs:
  - id: B-049
    action: guard
---

**Status** WRITTEN

# 083 — one anchor, read by both halves, rendered

**Read the mockup carrying `- LATEST` in the Trading Terminal Mockups folder
before writing anything.** No version is named here deliberately — a task that
pins a version points at an archived file the moment the drawing is revised.

---

## 0. Is this task for you

**If `handoff/inbox/083-for-code-task-rvol-anchor.md` exists in your tree and no
file beginning `083-` exists in `handoff/done/`, this task is for you.
Otherwise stop reading and ignore this message.**

---

## 1. Part 0 — read and report first

**Three reads, reported as read, not inferred.**

1. **What basis does each half of RVOL currently use?** The numerator is
   today's cumulative volume off the price stream; the denominator is the
   20-session per-minute median curve. **Name the constant each one reads and
   say whether they are the same object or two objects that happen to agree.**
2. **Does the numerator include the forming, not-yet-closed minute?** See §5 —
   this is a separate defect and this task does not fix it, but the answer must
   be recorded before anyone acts on it.
3. **What does "open" currently mean in "cumulative volume from open to t"** —
   04:00 or 09:30? Task 080's note says both halves were built on the
   extended-hours basis. **Confirm or contradict it by reading.**

**If any read contradicts this file, say so and name the line.**

---

## 2. Part 1 — one key, both halves

**`rvol_anchor` in config. Values `rth` and `eth`. Default `rth`.**

**Both halves of the ratio read that one key.** Not two settings that agree
today — **one object, read twice.** The numerator's basis and the curve's basis
must be the same value by construction, not by coincidence.

**This is the correction of a rule, not an exception to one.** Project
instructions §8 says *a basis is a constant beside the indicator's definition,
never config*. **That rule is wrong as written and is being corrected**; the
instructions will be re-issued. It was drawn from indicators whose basis is
fixed by arithmetic — `ADR%` on daily bars, where extended hours cannot alter
the bar; the opening range, which excludes them by definition. **RVOL is not
one of those.** `SPEC.md` already says `use_rth` is per-indicator and that RVOL
*only has to match itself*.

**What survives the correction, and it is the part that matters: a basis is
always declared and always rendered.** B-049 was never about configurability —
it was two halves of one ratio answering differently with nothing saying so.

**Do not touch any other indicator's basis.** `ADR%`, `ATR14`, the opening
range and VWAP's anchor are all out of scope. Not this task's.

---

## 3. Part 2 — the row renders its anchor

Per the mockup: `RVOL rth    0.86x own · 1.4x vs XLC`.

**The label is derived from the value actually used, never written as a
literal.** A hardcoded `rth` is a well-formed label answering a different
question, and it will eventually be wrong while looking right.

**The label field stays twelve columns**, so `RVOL rth` and `RVOL eth` both
align and nothing on the panel shifts when the anchor changes.

**The anchor renders even while the row is pending**, because it is a fact
about the row rather than about the value, and it is known at attach.

---

## 4. Part 3 — the request shrinks, and that is the point

Under `rth` the 20-session curve is built from **20 × 390 bars rather than
20 × 960** — about 59% fewer. Task 082 measured this request at 15 to over 60
seconds with a 60% timeout rate on AMZN under concurrent dispatch.

**Report the measured wall time and bar count for the curve request under both
anchors**, per B-033: bars received against bars expected. **One live run each
is enough; this is a size check, not a study.**

**Do not change anything else about the request** — not its duration string
beyond what the anchor implies, not its bar size, not `request_timeout_s`.

---

## 5. What you may NOT do

**Do not fix the forming-bar sawtooth.** The numerator includes a partial
minute while every bar in the denominator is complete, so RVOL is understated
at the top of each minute by up to a full minute of volume — worst at 09:31,
where that is nearly the whole denominator. **It is a real defect, it is ruled,
and it is a separate task.** Record what you read in Part 0 item 2 and stop.

**Do not add caching.** That is task 084 and it depends on this one.

**Do not touch `request_timeout_s`** — B-132, a threshold, Christoph's.

**Do not change any other indicator's basis or add a config key for one.**

---

## 6. Exit tests

**Seen red against real pre-fix code before accepted green.**

**Green.** With `rvol_anchor: rth`, the curve request uses the RTH basis and
the row renders `RVOL rth`. With `eth`, both change together. **Assert the
specific rendered text**, not that a substring appears somewhere — B-126.

**Divergence.** **A test that goes red if the numerator's basis and the curve's
basis are ever different values.** This is the B-049 guard and it is the most
important test in this task. It must fail if someone later introduces a second
key, so **assert they are the same object or read from the same place**, not
merely that they are equal in the fixture.

**Derived label.** A test that goes red if the rendered label is a literal
rather than derived from the value used — set the anchor to `eth` and assert
the row reads `RVOL eth`.

**Refusal.** The anchor still renders when the row is `pending` and when it is
`unavailable`. One reading refusing never blanks the other — B-117.

**Fixture.** No test may read a state the shared fixture guarantees rather than
one your change produced — B-136.

**UAT.** `christoph/open/044`. Not yours to perform or mark.

---

## 7. What the done-note must state

Part 0's three reads. The measured curve request wall time and bar count under
both anchors. Which tests were seen red and against what. **And whether the two
halves were previously the same object or two that happened to agree** — that
answer determines whether B-049 was closed or merely quiet.

`verify.ps1` runs as the last action. Do not paste or summarise it.

**Anything needing a decision that is not yours goes into a question file and
that session ends. It does not wait.**

---

## 8. The prompt

```
Do inbox 083
```

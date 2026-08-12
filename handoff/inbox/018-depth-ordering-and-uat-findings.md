# 018 — the depth-ordering question, three UAT findings, and a rule for findings

**Status** WRITTEN · **Date** 2026-08-12 · **Type** correction + investigation · **Tree** `D:\Dev\momentum`

> **Number not confirmed.** The design session cannot see the inbox. **If `018` is taken, say so
> and this file is re-issued under the correct number** — it is not renamed in place.
>
> **Part 1 is the highest-stakes item in this task and should run first.** Everything else is
> a screen fix.

---

## Part 1 — is the ARCA depth capture reconstructable?

**Observed, `S009a` part 4.** A live ARCA depth probe returned rows **out of price order.** The
best bid by price was `723.04` at **index 6**; index 0 was `723.03`. Asks likewise — `723.09` at
index 7 beat `723.12` at index 0. **`domBids[0]` was not the best bid at that instant.**

**Inference, not established:** positional DOM rows updating in place would explain it. IBKR's
depth API delivers row *positions* that mutate, and a consumer reading the array as a sorted
book would be wrong.

**Why it matters more than anything else in this task.** `012` captured **2,149,968 ARCA depth
records** in a session that cannot be re-recorded and is Row 14's basis. If position was not
recorded alongside price, **the book's true ordering at each instant may be unreconstructable**,
and every future consumer of that tape inherits the problem silently.

### What to do

**Read `tools/capture_tape.py` and determine, from the code, exactly what each depth record
carries.** Specifically whether the row `position` field from the depth callback is written, and
whether anything is sorted, reordered, or normalised on the way to disk.

**Then read enough of the tape to confirm it against reality** — the first few depth lines are
sufficient. **`records/` is read-only for this task: read it, never write, move, rename,
compress or delete anything in it.**

Report, in this order and clearly separated:

1. **The fields each depth record actually carries.** Quoted from the code.
2. **A verbatim sample** of two or three depth lines from the capture.
3. **Whether ordering is reconstructable**, as a yes/no with the reasoning shown.
4. **If no** — what is lost, precisely. Not "the data may be wrong": which question can no
   longer be answered from this file.

**Do not fix anything, and do not rewrite the capture tool.** This part establishes what is
true. **What follows from it is a decision that needs the answer first**, and inventing a repair
before the diagnosis is the pattern this project keeps paying for.

---

## Part 2 — the too-small guard is evaluated once

**Observed, UAT `009` answers B and C.** Launched below the per-tile minimum, the refusal renders
correctly: one stated message, zero panels, naming the starved tile. **Shrink the window after
launch and it never fires** — panels truncate to `WATCHLIS...` and `(no wat...` instead.

**Diagnosed cause:** the guard runs in `compose()`, which fires once at startup. `on_resize`
re-renders panel bodies but does not re-evaluate the guard.

**Decision, Christoph's, taken 2026-08-12: the terminal refuses.** The rule is *never a
silently clipped panel*, and a rule that holds only at launch is not the rule. Truncation at 24
columns is technically honest and functionally unreadable — **a panel you cannot read is not a
degraded panel, it is a different one.**

### What to do

Re-evaluate the per-tile check on resize, and switch between the refusal state and the panels in
both directions — **shrinking below the minimum must refuse, and growing back above it must
restore the panels.** A one-way transition would be worse than the current behaviour.

**The refusal message must recompute**, not reuse the startup values. It names the actual
window size and the actual shortfall; a stale message naming the launch size is precisely the
well-formed-value-answering-a-different-question defect.

**Test both directions**, and test that the message reflects the current size rather than the
first one.

---

## Part 3 — two pipeline rows have no name

**Observed, UAT `009` answer D** and visible in the screenshot: rows 5 and 8 render with an empty
name column.

```
   5      your decision - correctly not a slice
   8      your decision - correctly not a slice
```

**Cause:** both are declared `name: "[HUMAN]"` in `config/layout.yaml`, and the value cell
already says *your decision*, so the name reads as a gap rather than a stage.

**Fix: name them.** Row 5 is **`select`** — after rank, before size, choosing what to trade. Row
8 is **`submit`** — after stage, before manage, deciding whether to send. Both are real stage
names from `SPEC.md`'s twelve, both fit the column, and **neither implies a slice**, which the
value cell continues to make explicit.

**Do not remove the `human: true` flag or change what the value cell says.** The distinction
between *a stage the system does not perform* and *one it has not performed yet* is load-bearing
and currently correct.

---

## Part 4 — `manage` is deferred, not unassigned

**Observed:** row 9 renders `[ NOT BUILT ] (slice not assigned)`.

**Decision, Christoph's, 2026-08-12: `manage` is deferred — not core, considered later.**

Those are different statements. *Nobody decided* and *decided to postpone* carry different
weight, and the screen is currently making the weaker one.

**Fix:** render it as deferred, with wording that does not imply a slice exists. **The
`slice not assigned` state must remain reachable** for a genuine gap — this is a new state for a
stage that has been ruled on, not a replacement for the one that means nobody has.

**`BUILD-PLAN.md` still contains no slice building position management, and that remains true.**
Record it in the ledger if it is not already there; do not invent a slice number.

---

## Part 5 — the UAT-to-work rule

**The gap:** `docs/observations/OBSERVATIONS.md` has a trigger that goes red. **A signed UAT
sitting in `christoph/done/` has none.** Findings written into a retired UAT reach work only
because the design session happened to be in the conversation. **Three of this task's four parts
exist for exactly that reason, and nothing would have caught their absence.**

### What to do

**A finding recorded in a retired UAT must land where something fails if it is ignored** — a
Part in a task file, or a ledger row.

Build the check on the shape of `test_uat_has_a_file.py`, which is the mirror of this problem:
that test asserts a named UAT has a file; this asserts **a completed UAT's findings have a
destination.**

**The hard part is detecting a finding, and it is a real design problem — do not paper over it.**
A free-text answer box is not machine-readable in general. Two candidate shapes, neither
mandated:

- **Structural** — a retired UAT declares a `**Findings**` section listing ledger ids or task
  numbers, and the test asserts each resolves. Requires the design session to author the section
  into every UAT; **cheap to check, and it fails loudly when absent.**
- **Positional** — a non-empty answer in a designated free-text field must be matched by a
  ledger row citing that UAT as its source.

**Choose one, defend it, and state its limit** the way part 3 of `016` did. **If neither can be
made to work honestly, say so and build nothing** — a check that passes vacuously is worse than
no check, and this project has a fixture that proved it.

**Seed it with the three findings above**, whichever shape is chosen, so `009` is covered
retrospectively and the mechanism has been exercised at least once.

---

## Part 6 — three things flagged, not fixed

Report on each; act on none.

**6a · `handoff/accepted/012b-uat-basis-correction.md` accepts a `christoph/` item.**
`accepted/` is defined as a byte-identical copy of a **done-note**, and `012b` has no
`handoff/done/` counterpart. **Christoph's file, possibly intended.** Confirm whether it is
byte-identical to `christoph/done/012b-uat-basis-correction.md` and report.

**6b · `test_a_too_small_window_says_so_rather_than_clipping` calls `too_small_message(40, 10,
60, 16)` directly.** The fixed `60×16` no longer comes from anywhere in the app. The test is not
wrong — it checks the message — but **the numbers in it now read as a live minimum and are not
one.** Report whether part 2's change makes it misleading enough to warrant rewriting. **Do not
weaken it.**

**6c · The 80-column floor now has one column of slack.** `WATCHLIST` needs 23 and a tile gets
24. **Any panel title longer than `WATCHLIST` pushes the requirement past the inherited floor.**
Report whether any planned panel title in `BUILD-PLAN.md` would.

---

## Part 7 — commit and push

Commit in **separate, subject-coherent commits**, following `014`'s reasoning.

**Push if `017` has landed and the remote exists.** If it has not, **do not create a remote and
do not push** — `017` owns that and its checks run before the first push. **State which case
applied.**

---

## Do not

- **Do not write to, or remove from, `christoph/open/` or `christoph/done/`.** `016` part 7
  instructed otherwise and was wrong. A file needing correction there is authored by the design
  session and placed by Christoph.
- **Do not write, move, rename, compress or delete anything in `records/`.** Part 1 reads it.
- Do not modify any file recorded in `EVIDENCE-CARRY.md`, or re-record any hash.
- Do not reword any done-note's UAT exit row. **Christoph's decision, still open.**
- Do not open a TWS connection.
- Do not modify `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` or `HANDOFF-PROTOCOL.md`.
- Do not weaken a test to make it pass. **Report and stop** — that is what produced Resolution D.
- Do not invent a slice number for `manage`.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full suite, count before and after as measured numbers. Name any new failure. |
| **Refusal A** | Claude Code | Resize below the minimum after launch: refusal renders, zero panels, **message reflects the current size not the launch size.** Then resize back above: panels restore. |
| **Refusal B** | Claude Code | Part 5's check, deliberately violated — a retired UAT with a finding and no destination. Confirm red, and that the message names the UAT. Revert. |
| **Refusal C** | Claude Code | Confirm `slice not assigned` is still reachable and still distinct from `deferred`, at character-class level, **without colour.** |
| **UAT** | Christoph | Run the terminal at 209×54, shrink it below ~75 columns, then grow it back. **The criterion is whether the screen ever shows a panel you cannot read.** Write the record to `christoph/open/`. |

## Done-note must state

- **Part 1's four answers**, with the code quoted and the tape sample verbatim. **This is the
  part that matters most; do not compress it.**
- Which shape part 5 used, why, and its stated limit — or why nothing was built.
- The commit split, one line each, and whether a push happened.
- **Anything in this task that was wrong on contact.** Every task this week has had divergences
  and every one of them mattered.

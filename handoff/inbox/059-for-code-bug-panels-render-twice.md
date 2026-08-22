---
task: 059
class: product
depends: none
touches: live/render.py
---

# 059 — B-001: every panel renders twice

**If `handoff/inbox/059-for-code-bug-panels-render-twice.md` exists in your tree and `handoff/done/059-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. The defect

`B-001`, priority 1, open since `c015` where it reproduced three separate times.

**Observed:** every panel appears duplicated. The row records it after a redraw, after a reconnect, and after a restart.

**Expected:** one set of panels. A redraw replaces the previous frame rather than adding to it.

---

## 1. Fresh evidence, 2026-08-22 — two screenshots, and what they rule out

Christoph captured the empty first frame and then the frame after attaching QQQ. **Three readings, and they narrow the search before any code is read:**

1. **Attach alone reproduces it. No resize was involved.** The window was not resized between the two captures. **Do not spend any time on a resize path** — it is not a trigger, and chasing it is a fourth path that does not exist.

2. **Both copies are post-attach.** The duplicate carries `QQQ attached 11:44` with the same ADR%, ADR%avail, ATR and ext values as the first. **It is not a stale pre-attach frame left behind** — a leftover would read `(nothing attached)`. Both were painted after the attach completed.

3. **A scrollbar is present in both captures.** This is the strongest signal in the set. **An application holding the alternate screen buffer produces no scrollback at all.** Scrollback exists here, in the empty frame as well as the attached one — which is consistent with the app **appending each repaint to the buffer rather than redrawing in place**, and inconsistent with the product's own definition: *a Python TUI redrawing in place in Windows Terminal.*

**Reading 3 is an inference, not an observation.** It is the leading hypothesis and it must still be confirmed in Part 2 rather than assumed. **A scrollbar is an observation about the terminal, not about the widget tree.**

---

## 2. Part 1 — settle the cause, and the stated cause is not it

**The bug row says *"Missing CLS"*. Treat that as an inference from before the Textual port. Do not fix it by adding a screen clear** — a clear fights the framework and would hide whichever cause is real.

**Two candidates, and one cheap discriminator:**

| | Candidate | What it would mean |
|---|---|---|
| **A** | **Widgets are mounted again rather than updated.** The attach path mounts a fresh panel set instead of refreshing the existing one. | The duplication is **inside the app's own render tree** |
| **B** | **Each repaint is appended to the terminal buffer.** No alternate screen buffer, so a new frame lands below the previous one instead of replacing it. | The render tree is **correct** and nothing in the widget code is wrong |

**Discriminator one — the snapshot.** Take a `pytest-textual-snapshot` after an attach.

- **Two sets of panels in the snapshot → A.** Fix is in the mount/refresh path.
- **One set in the snapshot, two on screen → B.** Fix is in how the app takes the screen.

**Discriminator two — count the copies.** Attach a third and a fourth time and count.

- **The count keeps climbing → B.** Every repaint appends.
- **It stays at exactly two → A.** One extra widget set exists and is being re-rendered alongside the real one.

**Run both. They are independent, and agreeing is worth more than either alone.** **Report which candidate the evidence lands on before fixing anything.** If the two discriminators disagree, or if it will not reproduce under test at all, **write a question file rather than guessing** — a redraw defect that vanishes under test is a finding in its own right.

---

## 3. Part 2 — the fix, wherever Part 1 lands it

**`touches:` names `live/render.py` because that is the known render module. The fix may not live there.** Locate it by reading. **The done-note states which file actually carried the defect** — if the frontmatter was wrong, say so plainly rather than amending the task file. `handoff/` is copy-and-keep and nothing in it is edited.

**Three observed paths, all of which must be covered: attach, reconnect, restart.** A fix covering only attach leaves the other two, and the row records all three. **If one turns out to have a different cause, that is a second row — not a silent extension of this one.**

---

## 4. The test, and it must be seen red

**A test asserts that after an attach the app renders exactly one instance of each panel.**

**Assert the rule, not the current output.** `B-029` is precisely this failure — the `038` units test asserted whatever the code happened to produce, defect included, and three rows broke silently later. **Count panel instances against the expected set. Do not snapshot-match a frame you just generated and call it correct.**

**Demonstrate red before accepting green.** Revert the fix, watch it fail, restore it, watch it pass. **A test that has never failed is not known to work.**

**If the cause is B**, the test must be able to see it — an in-process snapshot may show one clean frame while the terminal shows three. **Say so in the done-note if the assertion has to reach past the widget tree to catch it**, because that is a real limit on what the suite can protect.

---

## 5. Snapshot width

The suite runs at 80×24, 120×40 and 240×70. **Christoph's terminal is 209×54 and is not among them** — that is `B-012`, **not this task's to fix**.

**Run the repro at 209×54 by hand as well.** A defect present only at the working size passes a green suite. If it reproduces at 209×54 and not at the pinned widths, **that is an `OBSERVATIONS.md` entry and it strengthens `B-012`.**

---

## 6. Exit tests

**Green.**
- Attach produces one set of panels. Attaching repeatedly does not increase the count.
- The same holds after a reconnect and after a restart.
- The new test was **seen red** before being accepted green.
- The existing snapshot suite stays green at all three pinned widths.

**Refusal.**
- **Attach a bad symbol and redraw.** The panels render their refusals **once**. A duplicated refusal is the same defect wearing different content, and refusals are the state this terminal is judged on.
- **Start with no data at all** — `BUILD-PLAN` slice 009's canonical empty frame. Every panel renders a named refusal, one instance each, no blanks and no zeros. **The empty frame in Christoph's own capture already carries a scrollbar, so this case is load-bearing rather than ceremonial.**

**UAT — Christoph.**
- Attach QQQ at 209×54 and confirm one set of panels. **Attach twice more and confirm the count does not climb.**
- Then reconnect and restart and confirm the same.

---

## 7. Not in this task

- **Resize.** Ruled out by the evidence above. Do not build a path for it.
- **`B-002` — bad symbol fails silently.** Tempting, since a bad symbol appears in the original repro. **It stays open.** If this fix incidentally changes what a bad symbol does, say so in the done-note.
- **`B-012` — 209×54 is not a snapshot width.** Named above, deliberately not fixed here.
- **`B-091` — ATR renders n=14 against a ruled n=20.** Visible in the same screenshot. Not this task's.
- **`B-005`, `B-009`, `B-010`, `B-011`.** Other UI rows. Untouched.

---

## 8. Closing

**Scratch in `$env:TEMP`, never the repo.**

**The closing sequence, from the main checkout: sync, work, verify, export, push.** `verify.ps1` runs as the last action and **is not pasted or summarised.** The done-note states that it ran and when, and **quotes no test count.**

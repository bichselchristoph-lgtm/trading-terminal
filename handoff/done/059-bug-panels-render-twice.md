---
id: 059
title: B-001 — candidate A ruled out, candidate B blocked on one fact only Christoph has
type: task
class: product
owner: claude-code
bugs:
  - id: B-001
    action: correct
    status: open
---

**Status** RUNNING

# 059 — Part 1 half-done, Part 2 and 3 blocked, nothing shipped as a fix

**`059` asked to settle the cause before fixing anything. One of its two discriminators
is conclusive and rules out candidate A. The other cannot be run from this environment,
and `059` §2's own instruction for that case — write a question file rather than guess —
is what I did. No screen clear was added, and nothing in `live/tui/app.py` was changed.**

`handoff/questions/059-panel-duplication-cause.md` holds the fork. It needs to be pasted
to chat.

---

## What was done

**New file: `live/tests/test_panels_render_once.py`, four tests, all green.** Drives
`MomentumApp` through Textual's real pilot at 209×54 (the `013`/`059` UAT size) and
counts `app.query(Panel)` against the seven titles `render_panels` always places:

- mount → exactly one of each
- three consecutive real key-press attaches → still exactly one of each, never climbing
- three direct calls to `_rerender()` (the call the attach path and any future reconnect
  path share) → still exactly one of each
- a refused (bad-symbol) attach → exactly one of each, and the refusal string appears
  once in the ATTACHED body, not twice

**This rules out candidate A** — nothing in the mount/refresh path in `app.py` creates a
second widget set, under any of the three trigger shapes `059` names (attach, reconnect,
restart — modelled as attach and a bare `_rerender()`).

**Candidate B — "each repaint is appended to the terminal buffer, render tree correct" —
could not be independently confirmed or refuted.** `059` §2's second discriminator (attach
repeatedly and count the copies **on screen**) is a real-terminal observation; Textual's
`run_test()` pilot drives the compositor's internal model, not a live console screen
buffer, and this session has no interactive Windows Terminal / GUI session reachable
through its shell tools to watch a real repaint happen.

---

## What points at B without proving it

1. The render-tree check above.
2. `059`'s own fresh evidence: a scrollbar in the pre-attach, empty first frame — flagged
   in the task itself as the strongest signal, and as an inference rather than a settled
   fact.
3. `christoph/done/015 for christoph attach qqq.md` — Christoph's own UAT, predating the
   Textual port, reproducing the identical "all panels displayed twice" symptom twice:
   once on a second attach, once after **restarting the terminal**. The same symptom
   under two unrelated renderers is the strongest single reason to believe the cause is
   outside `live/tui/`'s widget code.

Full detail, and the one fact that would turn this into a buildable fix (does the
duplication depend on reusing the same terminal tab across runs, and how does the app
normally get stopped — its own quit, `Ctrl+C`, `Ctrl+Break`, or the window closed) is in
the question file. **I did not act on my own leading hypothesis** (an abrupt-termination
console-cleanup gap) because it is one of several live candidates and building it without
confirmation would be exactly the guessing `059` §2 forbids.

---

## Not done, and why

- **Part 2 (the fix)** — blocked. There is no code change I can defend as addressing a
  cause I have not been able to confirm.
- **Part 3 (the red/green test)** — blocked for the same reason, and `059` §4 anticipated
  this: *"if the cause is B, the test must be able to see it... an in-process snapshot may
  show one clean frame while the terminal shows three."* `test_panels_render_once.py` is
  real, kept coverage, but it is not that test.
- **Section 5 (209×54 hand repro), section 6 exit tests, the UAT** — not run. They come
  after Part 2.

---

## Verify and export

`verify.ps1` was run as the closing action; not pasted or summarised here, per convention.
`export-handoff.ps1` ran after the commit. **This done-note, the new test file and the
question file all need to reach chat** — the question blocks the rest of `059`.

---
id: 059-q1
title: B-001 reproduces only on a real terminal — what closes the terminal between runs?
status: OPEN
raised_by: claude-code
task: 059
---

**Status** RUNNING
**Raised by** 059
**Blocks** yes — 059 Part 2 (the fix) and Part 3 (its red/green test)

# `059` Part 1 rules out candidate A. Candidate B needs one fact only Christoph has.

**I did not fix anything. Guessing at a fix for a defect I cannot reproduce is exactly
what `059` §2 forbids.**

---

## What `059` asked for

Two candidates, one cheap discriminator each, settle the cause before touching code:

| | Candidate | What it would mean |
|---|---|---|
| **A** | Widgets are mounted again rather than updated | duplication is **inside** the render tree |
| **B** | Each repaint is appended to the terminal buffer | render tree is **correct**, nothing in the widget code is wrong |

---

## Discriminator one — run, and conclusive

`live/tests/test_panels_render_once.py` (new, four tests, all green) drives the real
app through Textual's pilot at 209×54 — the size the `013` UAT and the fresh `059`
evidence both use — and counts `app.query(Panel)` against the seven known titles:

- On mount: exactly one of each.
- After three consecutive attaches: still exactly one of each, never climbing.
- After three direct calls to `_rerender()` — the call attach and any future reconnect
  path share: still exactly one of each.
- After a refused (bad-symbol) attach: exactly one of each, and the refusal string
  appears **once** in the ATTACHED panel body, not twice.

**Candidate A is ruled out.** Nothing in `app.py`'s mount/refresh path creates a second
widget set, under any of the three named trigger paths this task lists (attach,
reconnect, restart — modelled here as attach and a bare `_rerender()`).

## Discriminator two — cannot be run from this environment

`059` §2's second discriminator asks to attach a third and fourth time and **count the
copies** — on the actual screen. That is a real-terminal observation, and Textual's
`run_test()` pilot doesn't produce one: it drives the compositor's internal model, not
a live console's screen buffer. There is no interactive Windows Terminal session
reachable from this session's shell tools to watch a real repaint happen. **I could not
independently run this half**, and `059` §2 says exactly what to do when that happens:
*"if it will not reproduce under test at all, write a question file rather than
guessing."*

---

## Why I believe this anyway lands on B, and why that is not enough to fix it

Three things converge on B without proving the mechanism:

1. **Discriminator one, above** — the render tree is provably clean.
2. **The fresh `059` evidence itself** — a scrollbar in the *pre-attach, empty* frame,
   which `059` §1 reading 3 calls "the strongest signal in the set" while correctly
   flagging it as an inference, not a settled fact.
3. **`christoph/done/015 for christoph attach qqq.md`** — Christoph's own UAT, which
   **predates the Textual port** (`059` §2 calls the bug row's "Missing CLS" an
   inference from before that port). It reproduces the identical symptom twice, under a
   completely different renderer:
   - §3: after a second `a` → `QQQ` → enter, *"All panels are displayed twice."*
   - §6, DISPLAY ISSUES: *"started terminal again after bringing up TWS, now all panels
     displayed twice again. Each disconnect, switching of symbols need a CLS."*

**The same visible symptom across two unrelated render implementations is strong
evidence the cause sits outside `live/tui/`'s widget code entirely** — most likely in
how the terminal session is left after the process exits, and how the next process
picks that state back up. But "most likely" is a hypothesis, not a diagnosis, and I have
no way to test it here.

**My leading hypothesis, offered as a question, not acted on:** Christoph's §6 note says
*"started terminal again"* — i.e. the app was re-run **in the same terminal tab** that
had shown a previous run. If that previous run ended by the window being closed, or by
Ctrl+Break, rather than by the app's own quit path, Textual's cleanup
(`driver.stop_application_mode()` — restore console mode, exit the alternate screen)
never runs, because Windows delivers those as an abrupt-termination signal that a plain
Python `try/finally` does not reliably survive. The next launch in that same tab would
then be starting from an already-dirty console/alt-screen state. If true, the fix is a
Windows console control handler (`SetConsoleCtrlHandler`) in `live/tui/app.py`'s `main()`
that restores the terminal on *any* termination path, not just a clean one — narrowly
scoped, testable (the handler's registration and its restore sequence), and not a screen
clear on redraw, which `059` §2 already forbids.

**This is not the only candidate.** It could as easily be a ConPTY/Windows Terminal
quirk with no code-side fix at all, in which case the right answer might be a documented
launch/exit habit rather than a code change.

---

## The one fact that would settle it

**When the duplication has shown up — on attach, on reconnect, or (per `christoph/done/015`)
on restart — was the app running in the *same* terminal tab/window that had shown a
previous run of it, or a freshly opened one each time? And when it stops, how does it
stop — the app's own quit, `Ctrl+C`, `Ctrl+Break`, or closing the window?**

That answer decides which of three very different things gets built: a console-cleanup
fix inside this repo, a documented workaround with no code change, or a continued search
if the answer rules out the terminal-reuse theory entirely.

---

**This needs to be pasted to chat.** `059` Part 2 (the fix) and Part 3 (its red/green
test) are blocked on it — the render-tree-only coverage in
`live/tests/test_panels_render_once.py` is real protective work but cannot, by its own
nature, be the test `059` §4 asks for if the cause is B.

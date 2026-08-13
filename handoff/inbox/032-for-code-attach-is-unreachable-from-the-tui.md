---
id: 032
title: attach() exists and the TUI cannot reach it — the third green-suite-unreachable-feature
type: correction
owner: claude-code
depends: S010, 029
---

**Status** WRITTEN

# 032 — There is no way to attach a symbol

**Christoph launched the terminal for the first time on 2026-08-13 and asked how to attach
QQQ.** There is no answer. **That question is the finding.**

---

## Part 1 — The observation, read from the tree

`live/tui/app.py`:

- imports exactly three local modules — `.day_record`, `.grammar`, `.layout`. **`live.attach`
  is not among them.**
- `BINDINGS = [("ctrl+tab", "focus_next", "Next panel")]` — **one binding, and it moves focus.**
- **zero `def action_` methods**, no `Provider`, no `SystemCommand`, no command registration.
- the ATTACHED panel reads `record.attached` and nothing else.

`live/attach/attach.py` exposes `attach(symbol, md, *, origin="typed") -> AttachResult`, with
`live/tests/test_attach.py` at 18,449 bytes exercising it.

**Inference, and it follows from the imports alone:** there is no code path from a running TUI
to `attach()`. The panel can render an attachment; nothing in the application can create one.

**A second observation, which is its own defect.** `app.py`'s docstring states *"`Ctrl+P` is the
palette for the long tail."* **No palette is registered.** Ctrl+P opens Textual's built-in
palette carrying theme and quit. **A mechanism named in prose with no implementation** — §7,
in the file whose docstring names it.

---

## Part 2 — Why the suite is green, and this is the part that matters

**`live/tests/test_attach.py` calls `attach()` directly.** `live/tests/test_tui_*.py` drive the
app through Textual's pilot and assert on rendered panels built from a `DayRecord` **handed to
them**. Neither ever asks *"can a person reach this from the running program."*

**This is the third instance of one shape:**

| | Built | Unreachable because |
|---|---|---|
| `live/` | the app | no entry point — `029` |
| `S010` | `attach()` | nothing in the app calls it — this task |
| `S009` | the palette | it was written in a docstring |

**Every one of them shipped green.** The suite tests the pieces as libraries; the UAT tests the
program. **They are different questions and the repo still cannot tell them apart** — `029`
added a launch test, which proves the program *starts* and nothing about what it can *do*.

---

## Part 3 — Give it a way in. The smallest one.

**Do not design a command system.** One way to attach, chosen for being the least code:

**A key binding that opens a single-line input, and on submit calls `attach()`.** `a` is the
obvious key. The docstring's `Ctrl+P` claim is either implemented or deleted — **do not leave a
third state where it is half-true.**

**Three constraints, all standing:**

1. **The binding calls `live.attach.attach()`. It does not reimplement any of it.** A second
   attach path would be two implementations of one fact, which is the defect the whole project
   is named for.
2. **`SPEC.md` §4.2 — surfaced, not refused.** A failed attach renders its reason in the panel.
   It does not raise, does not exit, does not clear the frame. **`AttachResult` already carries
   the failure; render it.**
3. **`SPEC.md` §4.4 — no setting acquires a default here.** If the binding key is configurable
   it is declared in `config/`, once. If it is not configurable, it is a constant with a comment
   saying so. **Not a literal in two places.**

**`origin="typed"` already exists in `attach()`'s signature** — a typed attach was anticipated
by `S010`. Use it rather than inventing a new origin value; §8.2a's four populations depend on
that field meaning one thing.

**Detaching is out of scope. Say so in the done-note if it turns out to be one line anyway.**

---

## Part 4 — The test that would have caught it, and it is not another pilot test

**A pilot test that constructs the app and calls its attach action is not this test.** It would
pass against a binding that no key reaches.

**Drive it by key press.** Textual's `Pilot.press()` against a headless app: press the key, type
a symbol, submit, assert the ATTACHED panel renders that symbol. **A fake `MarketData` — no
IBKR, no network.** The test asserts *reachability*, not correctness of the data.

**Demonstrate it red before accepting green**, against the current `app.py`. It will fail
because no key does anything, which is the point.

**And one row in `docs/observations/OBSERVATIONS.md`, phrased so it covers the class:**

> **Three features have shipped complete, tested and unreachable** — the app with no entry
> point (`029`), `attach()` with nothing calling it (`032`), the palette that existed only in a
> docstring. **The suite tests every piece as a library; only a UAT has ever tested the
> program.** Every slice that adds something a person must reach needs a test that reaches it
> the way a person would — **a key press, not a method call.**

---

## Part 5 — `christoph/open/013` is unperformable, not failed

**Do not touch `christoph/`.** Recorded here so the state is attributed: `013` asks Christoph to
check the context block against his own charts. **He cannot produce a context block**, so the
UAT cannot be performed at all. That is a different fact from a UAT that ran and failed, and the
register should not record them alike.

**Christoph updates the file himself.** This task asserts nothing about it — rule 12.

---

## Done when

- A key press attaches a symbol in a running TUI, and the ATTACHED panel shows it.
- The reachability test exists and **has been seen red** against the pre-fix `app.py`.
- A failed attach renders its reason and the app stays up. Demonstrate with a bad symbol.
- The `Ctrl+P` docstring claim is true or gone.
- The OBSERVATIONS row exists.

---

## Deliverable

`handoff/done/032-for-code-attach-is-unreachable-from-the-tui.md`:

1. The key, and the exact sequence a person types to attach QQQ.
2. **The reachability test red, then green**, with the red output quoted.
3. The bad-symbol refusal, quoted as rendered.
4. What you did with the `Ctrl+P` claim, and why.
5. **Whether anything else in `live/` is reachable only from a test.** Look before answering —
   this task exists because nobody had.
6. **What you could not do**, and why. Empty is suspicious.
7. `verify.ps1` run at `<time>`. Do not quote its output — HANDOFF-PROTOCOL v1.2.

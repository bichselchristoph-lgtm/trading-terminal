---
id: 029
title: The TUI has no entry point — 236 tests pass and the app cannot be started
type: correction
owner: claude-code
depends: S010
---

**Status** WRITTEN

# 029 — `python -m live.tui.app` exits silently, and the suite is green

**Observation.** Christoph ran the `013` UAT and reported:

```
PS D:\Dev\momentum> C:\venvs\trading\Scripts\python.exe -m live.tui.app
PS D:\Dev\momentum>
```

No output, no traceback, no error. Prompt returns.

**Observation, from reading `live/tui/app.py` through the device bridge.** The file is 25,158
bytes, defines `class MomentumApp(App)` at line 424, and contains **no `if __name__ ==
"__main__"` block, no `main()`, and no `MomentumApp().run()` call anywhere.** There is no
`live/tui/__main__.py` either.

**Inference, and it follows directly.** `python -m live.tui.app` imports the module, executes
its class and function definitions, reaches the end, and exits 0. **The observed behaviour is
exactly what that produces.** Nothing is broken. **Nothing was ever built to start.**

---

## Why the suite did not catch this, and it is the more important half

**`live/tests/` drives the app through Textual's `run_test()` pilot**, which constructs
`MomentumApp` directly and never needs a process entry point. Every panel, every refusal, every
tile measurement is genuinely tested. **236 tests pass. The application cannot be launched by a
human being.**

*§7: a test that passes is not a test that works.* The suite tests the app **as a library**
while the UAT tests it **as a program**, and nothing in the repo knew those were different
questions. **The test and the UAT were asking about different objects that share a name** — the
project's first pattern, arriving at the boundary between the harness and the world.

**This is the third time a green suite has covered a broken `live/`.** Record it as such.

---

## Part 1 — Give it an entry point

Add `live/tui/__main__.py` so `python -m live.tui` starts the app, **and** an `if __name__ ==
"__main__"` block in `app.py` so the command Christoph actually typed also works. **Both**, not
one — he has the failing command in his history and will type it again.

`SPEC.md` §4.4 applies: **no setting acquires a default here.** The entry point reads config
through the existing loader and passes it in. **Do not let a launcher become a second place
where configuration lives.**

**If the app cannot start without a live TWS connection, that is a finding, not a design.**
`SPEC.md` §4.2's *surfaced, not refused* means a terminal with no broker renders panels that say
why they are empty. **A launcher that exits when TWS is absent is a refusal the user cannot
read**, which is the same defect in a new place. State which behaviour you implemented.

---

## Part 2 — The test that would have caught it, and it must be seen red

**A test that imports `__main__` and asserts it exists is not this test.** It would pass against
an entry point that raises on the first line.

**Launch it as a subprocess.** `subprocess.run([sys.executable, "-m", "live.tui", ...])` against
a non-interactive terminal, asserting the process **reaches the point of rendering** rather than
merely exiting 0 — **exit 0 is precisely the failure mode being fixed.** Textual's headless
driver or `TEXTUAL=headless` with a short timeout is the mechanism; use whichever the installed
version supports and say which.

**Demonstrate it red against the current `app.py` before accepting green.** A test never seen
failing is a test whose green means nothing, and this is the exact class of defect that has now
shipped three times.

---

## Part 3 — One row in the ledger

`docs/observations/OBSERVATIONS.md`:

> **The suite tests `live/` as a library; the UAT tests it as a program.** 236 tests passed
> while `python -m live.tui.app` exited silently, because the pilot constructs `MomentumApp`
> directly and never needs a process entry point. Third green-suite-over-broken-`live/`.
> **Every slice that adds a user-facing command needs a launch test, not only a pilot test.**

**Do not generalise the fix beyond the ledger row.** There is one command today.

---

## Done when

- `python -m live.tui` **and** `python -m live.tui.app` both start the app.
- The subprocess launch test exists and **has been seen red** against the pre-fix `app.py`.
- The ledger row exists.
- **Christoph can run the `013` UAT.** *(He performs it. This task does not, and must not,
  assert on his behalf — rule 12.)*

---

## Deliverable

`handoff/done/029-for-code-the-app-has-no-entry-point.md`:

1. The exact command that now works, and what it renders on a 209 × 54 terminal.
2. **The launch test red, then green**, with the red output quoted.
3. Whether the app starts with TWS absent, and what it renders if so.
4. **What you could not do**, and why. Empty is suspicious.
5. `verify.ps1` run at `<time>`. Do not quote its output — HANDOFF-PROTOCOL v1.2.

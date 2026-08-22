---
id: 060
title: B-001 — a real async race in _apply_fit, found, fixed and tested
type: task
class: product
owner: claude-code
bugs:
  - id: B-001
    action: close
    status: fixed
answers: 059-q1
---

**Status** RUNNING

# 060 — the bug is real, in the render tree, and fixed

**`059` was wrong about where to look, for a defensible reason: it tested one size
(Textual's `80x24` default) and never combined two sessions. `060` parameterized
the discriminator over size and that is what found it — a genuine, timing-dependent
double mount in `_apply_fit()`, reproducing at `120x40` (one of the suite's own
pinned snapshot widths) roughly 2 times in 5 fresh-process trials. Fixed with a
lock. Seen red, then green, both confirmed by reverting and restoring the fix.**

`touches:` names `live/render.py`; that file does not exist in this tree, same as
`059` found. The fix landed in `live/tui/app.py`, the only render module there is.

---

## Part 1 — the question file, answered

`handoff/questions/059-panel-duplication-cause.md` frontmatter set to `status:
ANSWERED`, `answered_by: 060`. Body untouched, as instructed.

- **Inline mode:** ruled out. `060`'s own grep found one hit outside tests —
  `live/tui/app.py:923`, a bare `.run()`. No `inline=`, no `alt_screen` anywhere.
- **Same terminal tab / how the app is stopped:** held. `060` reasoned from the
  fresh evidence's identical `lag`/`as of`/`attached` values across both captures
  that they are almost certainly one run, which — see Part 3 below — turns out to
  be exactly right, just not for the reason anyone expected.

## Part 2 — the contradiction, resolved at runtime

Ran the real, non-headless `WindowsDriver` (not the pilot's headless driver) twice,
piping output to a byte stream rather than a live console:

1. `python -m live.tui.app` under a guarded `sitecustomize` (blocks the four broker
   ports — no live TWS connection), stdio piped, three attaches sent via stdin.
   `ESC[?1049h` (enter alt screen) appears **exactly once** in 34,547 bytes of
   output; `ESC[?1049l` never appears (process was killed, not quit).
2. `app.run_async()` driven directly, with a coroutine that waits for the app to
   settle and then calls `app.exit()` for a clean shutdown. The raw byte stream
   ends with `...[?1049l[?25h...` — alt screen entered once, exited once, cleanly.

**Alt screen is entered.** Per `060` §2's own branch: the scrollbar is Textual's
own and the duplication is inside the render tree. Go to Part 3 — which is exactly
what it was.

*(Neither check used a live desktop or console window — both ran as piped
subprocesses with the broker ports blocked, same guard pattern `live/tests/test_launches_as_a_program.py`
already uses. An earlier attempt in this session to verify visually via a live
screenshot was stopped and the screenshot discarded — this machine's shell tools
turned out to reach the actual interactive desktop, not an isolated sandbox, and
that was the wrong tool for this question regardless.)*

## Part 3 — the size table, and where it broke

| Size | Panel count (single session, 3 attaches) | Notes |
|---|---|---|
| 80×24 | 7 | clean |
| **120×40** | **7 or 14** | **reproduces — see below** |
| 209×54 | 7 | clean (Christoph's actual terminal) |
| 240×70 | 7 | clean |
| ~316×37 | 7 | clean; still an estimate from the capture's pixel size, not measured from a terminal |

**A single session at any one size never reproduced it.** What reproduces —
empirically, about 2 times in 5 — is a session at `120×40` immediately preceded by
an unrelated session at `80×24`, **in the same process**. `app.query(Panel)`
returns 14 widgets: two of every one of the seven titles. Looping the same
sequence *inside* one subprocess, or running it inside pytest's own process,
almost never reproduces it — something about a warmed-up interpreter or event loop
closes the window. What reliably reproduces it is a **fresh `python` process, run
repeatedly**, each one working through the full size list once. That is also
incidentally why `059`'s single-size, single-process test never saw it.

**Read as width-conditional vs height-conditional, per `060`'s own framing:
neither.** It is not about `120×40`'s shape — no single-size session at any of the
five ever failed. It is about **two sessions sharing a process**, and `120×40`
merely happened to be the size next to `80×24` in the list this task specified.

## Part 4 — the fix

**`_apply_fit()` was check-then-act against the DOM** (`if ... not
self.query(Panel): mount(...)`) **with two independent callers and no lock between
them**: `_rerender()` (the attach path) and `Frame.on_resize`. A resize landing
between one caller's `remove_children()` and its own `mount()` let a second caller
see the same empty frame and mount a second full panel set beside the first.

**Fix:** `MomentumApp.__init__` now holds `self._fit_lock = asyncio.Lock()`, and
the whole check-and-mount body of `_apply_fit()` runs inside `async with
self._fit_lock:`. A concurrent caller waits for the lock and then re-reads the DOM
— never acts on a decision made before the first caller's mount actually landed.
No screen clear, no change to what gets rendered — `live/tui/app.py`.

**Seen red, then green** (`live/tests/test_panels_render_once.py::test_a_prior_session_does_not_leave_the_next_one_racy`):

- Unfixed (`git stash` on `app.py`): **2/12** fresh-process trials reproduced —
  both showed exactly 14 panels.
- Fixed (`git stash pop`): **0/12**, and the whole file (9 tests, including the
  new 5-size parametrization) plus the full `live/` suite (139 tests) passed.

This test spawns a fresh `python` subprocess per trial rather than looping inside
one, because that is the one execution shape confirmed (repeatedly, in this
session) to actually reproduce the race — see the test module's own docstring and
`_RACE_SCRIPT`'s comment for why.

**A plausible bonus finding, not verified further:** `christoph/done/015 for
christoph attach qqq.md` reported the same "all panels displayed twice" symptom
after *"started terminal again"* — read at the time as evidence for a
cross-process, leftover-terminal-state cause. This race, occurring shortly after a
fresh mount while the terminal is still settling into its real size, is a
simpler explanation for that same symptom and does not require any state
surviving a process restart. Not claimed as proven — `059`'s two questions about
terminal reuse are answered and closed regardless of which explanation is right.

## Exit tests

- **Green.** Size table: done, all five. Alt-screen question: answered from
  runtime. New test seen red then green: done, figures above. Existing suite
  stays green at its three pinned widths: confirmed (139/139 `live/` passed).
- **Refusal.** `test_a_bad_symbol_refuses_once_not_twice` (059, still present,
  still green) covers a refused attach rendering once; the fix is in the shared
  mount path, not content, so it applies at every size the parametrized test
  covers, not only where the bad-symbol test runs.
- **UAT — Christoph.** Not run by this session. Attach at 209×54, scroll to the
  bottom, count panel sets; then maximise and repeat; report whether the duplicate
  was reachable by scrolling the app or only the terminal's own scrollbar. Given
  what Part 2–4 found, my expectation is the duplicate will now be gone rather
  than reachable either way, but that is Christoph's to confirm, not mine to
  assume.

## One more thing this run caught

`tests/test_adoption_log_complete.py::test_every_tracked_file_is_accounted_for`
went red on this session's own `verify.ps1` run — `live/tests/test_panels_render_once.py`
(created under `059`) had never been added to `BOOTSTRAP_ALLOWLIST`. It didn't fire
in `059` because the file was still untracked at `059`'s own `verify.ps1` run; this
task's commit tracked it, and the gate — correctly — caught the gap on its next
run. Fixed with one allowlist entry, following the file's own established
convention (`tests/test_adoption_log_complete.py`).

## Not in scope, untouched

`B-012`, `B-002`, `B-005`, `B-009`, `B-010`, `B-011`, `B-091`. The three
Drive-differing files (`040`, `043`, `052`) — still flagged by `sync.ps1`, still
unresolved, still Christoph's.

---

## Verify, export, push

`verify.ps1` ran as the closing action; not pasted or summarised, no test count
quoted. `export-handoff.ps1` ran after the commit.

---
id: 032
title: attach() is reachable from the keyboard — and two sessions built it at once
type: correction
owner: claude-code
depends: S010, 029
---

**Status** RUNNING

# 032 — done-note

**Christoph asked how to attach QQQ. The answer is now: press `a`, type `QQQ`, press enter.**

**Read part 0 first.** This task was worked by **two Claude Code sessions in the same
checkout at the same time**, which is `031`'s subject happening while `031` sits unbuilt in
the inbox. It changed what shipped, and it very nearly destroyed work.

---

## 0 — Two sessions, one tree

**Both sessions were given `032` and both implemented it, independently, between 17:17 and
17:30 on 2026-08-13.**

| time (local) | session A (this note's author) | session B |
|---|---|---|
| 17:27:11 | wrote `day_record.py` | — |
| 17:27:20 | — | wrote `live/tests/test_attach_is_reachable_by_key.py` (11 tests) |
| 17:27:37 | — | added a **temporary scaffold** to `app.py` to force a behavioural red |
| 17:27:53 | — | **removed that scaffold itself** |
| 17:28:06 | — | saw A's writes, read `031`, **stood down** |
| 17:28:57 | — | re-ran its red demo in a **detached worktree at `HEAD`**, never touching the shared tree |
| 17:29:16 | wrote `live/tests/test_attach_is_reachable.py` (8 tests) | — |
| ~17:29:20 | ran `git show HEAD:live/tui/app.py > live/tui/app.py` **in the shared tree** | — |

**They converged.** Same constant name `ATTACH_KEY`, same key `a`, same docked single-line
input, same `attach_refusal` field on the day record, same refusal rendering. **B's eleven
tests passed against A's implementation unmodified**, first run, no edits — which is a
stronger statement about the design than either suite makes on its own.

### The overwrite, and why it is recorded even though nothing was lost

**A reverted `app.py` to `HEAD` in a checkout another session was writing to.** That is
capable of destroying uncommitted work with no trace and no error.

**It did not, and this is settled by evidence rather than by inference.** B's transcript at
`~/.claude/projects/D--Dev-momentum/` records its only uncommitted `app.py` edit: a scaffold
added at 17:27:37 and removed by B itself at 17:27:53 — **ninety seconds before the
overwrite**. B wrote nothing else to `app.py`. It also explains two *"the file had been
modified on disk since you last read it"* notices A received: B's scaffold appearing and
vanishing between A's reads.

**Note what made that answerable: a transcript on disk, not a mechanism in this repo.** Had B
run on another machine the honest answer would have been **unknown**, and unknown is the
normal case. **Recorded as OBS-036** with the narrow fix — run the red demonstration in a
throwaway worktree, never by mutating the shared tree. B did exactly that and it cost one
`git worktree add`.

### Which suite survived, and why

**Christoph's call: keep B's, drop A's** — B's landed first and imports the existing `Fake`
from `test_attach.py` instead of declaring a second fixture implementing the same Protocol,
which is the two-implementations-of-one-fact defect in miniature.

**A's eight were compared against B's eleven before deleting, case by case.** B covered
everything A did **except one**: the `md=None` branch. That case was **ported into B's file**
as `test_with_no_market_data_the_key_still_says_why` and labelled as carried, then A's file
was deleted. **It is the branch the shipped program is actually in** — `main()` constructs no
broker — so losing it would have left the only path a real user reaches untested.

`live/tests/test_attach_is_reachable_by_key.py` therefore holds **12 tests**, eleven of them
written by a session that is not the author of this note. It is added to
`BOOTSTRAP_ALLOWLIST` with that provenance stated.

---

## 1 — The key, and the exact sequence

```
    a          opens a one-line prompt docked at the bottom
    Q Q Q      typed into it
    enter      calls live.attach.attach(symbol, md, origin="typed")
    esc        closes the prompt without attaching
```

`ATTACH_KEY = "a"` is a **module constant, not a setting.** `SPEC.md` §4.4 forbids a setting
acquiring a default at a boundary — a key in `config/layout.yaml` with a fallback in code is
exactly that, and one without a fallback makes a missing config line fatal to a terminal that
otherwise works. **So it is deliberately not configurable**, and the comment above it says so.
`BINDINGS` is its only reader; B's `test_the_key_is_declared_once` asserts the character never
appears as a literal alongside the constant.

**`origin="typed"` is passed explicitly** rather than left to `attach()`'s default. S010
anticipated a typed attach and §8.2a's four populations depend on that field meaning one
thing. B's `test_the_attach_is_recorded_as_typed` spies on the call and pins it.

**Detaching is out of scope and did not turn out to be one line.** Nothing tracks tick slots
across attaches, so a detach that did not release step 2's slot would be a lie about capacity.
Re-attaching a symbol replaces its row rather than growing a second one, which is the only
part of detach that came for free.

---

## 2 — The test, red then green

**Seen red twice, and the second red is the one that matters.**

**Red 1 — against `app.py` exactly as it stood at `HEAD` `4236cd0`.** A collection error:

```
ImportError while importing test module '...test_attach_is_reachable.py'.
E   ImportError: cannot import name 'ATTACH_KEY' from 'live.tui.app'
```

**That is the weak red** and is recorded as such: it proves a constant is missing, not that a
key does nothing. B reached the identical error independently and drew the identical
conclusion.

**Red 2 — the full fix present except the one line that binds the key**, which is precisely
the state 032 describes: the action exists, the panel can render an attachment, and no
keystroke reaches either.

```
E   AssertionError: pressed 'a', typed QQQ, pressed enter, and the ATTACHED panel
E     does not name it.
E     There is no path from a key press to live.attach.attach() - that is 032.
E     Rendered:
E     +- ATTACHED -------------------------------------------- not attached +
E       — (nothing attached)
E       1 of 1 · end
E   assert 'QQQ' in '+- ATTACHED ... not attached +\n  — (nothing attached)\n  1 of 1 · end'

7 failed, 1 passed in 4.43s
```

**The one that passed is the finding inside the finding.** It was the import assertion —
*does `app.py` import `live.attach.attach`* — and it passed against a binding no key reaches,
with every behavioural test in the same file red. **An import test passes against an imported
function nothing calls**, which is the exact shape `attach()` was already in with respect to
its own 395-line test file. That test was in A's suite and died with it; B's file has no
equivalent and does not need one.

**Red 3 — B's run, and this is the strongest of the three.** Reds 1 and 2 were taken against
a tree that already held part of the fix. **This one is against `HEAD` `4236cd0` clean**, in a
throwaway detached worktree outside the repo, with nothing but the two-line seam
(`ATTACH_KEY`, and `md` on `__init__`) added so the failure would be behavioural rather than an
`ImportError`. The worktree was removed afterwards; the shared tree was never touched.

```
AssertionError: unreachable at (240, 70):
  +- ATTACHED -------------------------------------------- not attached +
    — (nothing attached)
    1 of 1 · end

FAILED test_a_key_press_attaches_a_symbol_and_the_panel_shows_it
FAILED test_the_symbol_is_normalised_the_way_attach_normalises_it
FAILED test_the_attach_is_recorded_as_typed
FAILED test_a_bad_symbol_renders_its_reason_and_the_app_stays_up
FAILED test_the_frame_survives_a_refusal_and_can_attach_afterwards
FAILED test_no_contract_found_is_a_different_refusal_from_ambiguous
FAILED test_escape_closes_the_input_without_attaching
FAILED test_the_key_is_declared_once
FAILED test_it_is_reachable_at_more_than_one_width[size0]
FAILED test_it_is_reachable_at_more_than_one_width[size1]
10 failed, 1 passed in 5.12s
```

**All eleven assertions were written before their author had seen A's implementation.** B wrote
the file from the task text alone at 17:27:20, stood down at 17:28:06 on discovering A's
writes, and only then ran it against A's code — where it passed unmodified, first run. **That
independence is worth more than the green**: a suite written against an implementation tends to
describe it, and this one could not have.

**And the one test that passed is the same finding A recorded, arriving by a different route.**
A's single pass was an import assertion. B's single pass was
`test_an_empty_submit_attaches_nothing_and_closes` — *press the key, submit nothing, and the
panel must be unchanged*. It passed against an application where the key was bound to nothing,
because **a panel nothing can change is trivially a panel nothing changed.**

**Two suites, written independently, each contained exactly one test that passed against a
completely broken feature, and in both cases for the same reason: the test asserted an
absence.** Neither author noticed while writing it. That is a sharper statement of §7 than
either suite set out to make — an assertion that something did *not* happen cannot distinguish
*"the mechanism ran and correctly did nothing"* from *"there is no mechanism"*, and it is the
`[ NOT BUILT ]`-versus-data-absent distinction this project already enforces on screen, unenforced
in its own tests.

**Green:**

```
live\tests\test_attach_is_reachable_by_key.py ............              [100%]
12 passed in 5.43s
```

**Full suite: `292 passed, 8 failed`.** Baseline before this task on the same tree was
`280 passed, 8 failed`. **The same eight, named below — none introduced here and none fixed
here.**

---

## 3 — The bad-symbol refusal, as rendered

Driven by key press against a fake `MarketData`, captured from the running app:

```
### an unresolvable ticker: NOPE
+- ATTACHED -------------------------------------------- not attached +
  — (NOPE: no contract found)
  1 of 1 · end

### no market data at all — the state the shipped program is in
+- ATTACHED -------------------------------------------- not attached +
  — (QQQ: no market data - the app connects to no broker in this slice)
  1 of 1 · end

### success
+- ATTACHED --------------------------------------------- since 11:30 +
  QQQ  attached 11:30
  1 of 1 · end
```

An ambiguous ticker renders `— (ZZZZ: resolved to 2 contracts - ambiguous, refusing to
guess)`. **The candidate count is `AttachResult`'s own wording, not re-phrased at the call
site** — a shorter message invented in the TUI would drop the number that makes the refusal
actionable.

**The app stays up in every case**, the other six tiles still render, and a later attach
succeeds and clears the stale refusal. B's `test_the_frame_survives_a_refusal_and_can_attach_afterwards`
is the one that would catch a one-shot refusal, which is otherwise indistinguishable from a
working frame until the second attempt.

**The `—` above is the em-dash of the refusal grammar.** The `+-` borders are `ascii_safe()`
firing on this console's cp1252 encoding, which is documented behaviour, not damage.

### One field was added to `DayRecord`, whose docstring says not to

`render_panels(record)` is a **pure function of the record**, so a refusal the renderer cannot
see is a refusal that cannot render. The alternative was a second argument to `render_panels`,
which breaks the one property everything downstream leans on. **`attach_refusal: str = ""`**
holds a string that already exists on `AttachResult`, is cleared by the next successful
attach, and never accumulates. **The docstring's prohibition is about fields that make an
unbuilt reading representable — `layer_0`, `exposure` — and this is not one.** Stated here
rather than done quietly, because the next person to add a field will cite this one.

---

## 4 — The `Ctrl+P` claim: deleted, and the deletion is recorded

**`app.py`'s docstring said *"`Ctrl+P` is the palette for the long tail."* No palette was ever
registered.** `Ctrl+P` opens Textual's own built-in palette carrying theme and quit — nothing
this application put there.

**Deleted rather than implemented.** 032 asks for the smallest way in and forbids designing a
command system in the same sentence; a palette holding one command *is* a command system.

**The sentence is recorded in the docstring rather than silently removed.** A mechanism named
in prose with no implementation is §7 and this is the third instance in this repo — deleting
the evidence quietly is how the fourth one gets written. There is now no third state where it
is half-true.

---

## 5 — What else in `live/` is reachable only from a test

**Computed, not eyeballed** — an AST import-closure walk from `live.tui.__main__` and
`live.tui.app` across every module in `live/` and `core/`.

**Reachable from the program after this task:**

```
live.tui.__main__ · live.tui.app · live.tui.day_record · live.tui.grammar
live.tui.layout · live.attach.attach · core.indicators.context
```

`live.attach.attach` and `core.indicators.context` **entered that list today.** Before this
task the entire `core/` tree was reachable from tests only.

**One module is not reachable, and it is worse than reachable-only-from-a-test:**

> **`live/attach/ibkr.py` is imported by nothing at all — not by the app, and not by any
> test.** It is the live broker seam, the one module in S010 that touches IBKR, 203 lines,
> and **no test file imports it.** It appears exactly once outside itself in the whole
> repository: as a string in `BOOTSTRAP_ALLOWLIST`.

That is a fourth instance of this task's own class, one step further along — `attach()` at
least had a test. **Not fixed here**: wiring it means a broker connection, which is §6.

**One stale pointer found while auditing.** `core/indicators/context.py` line 8 says
*"`live/attach/render.py` bridges it to the grammar."* **`live/attach/render.py` does not
exist.** The bridging happens in `live/tui/app.py`. Not repaired — it is a docstring in a file
this task otherwise does not touch, and it is the same species of defect as the `Ctrl+P`
claim: a module named in prose that was never built.

The five package `__init__.py` files report as unreachable in the walk. **That is an artifact
of static analysis, not a finding** — they are empty package markers and Python imports them
implicitly.

---

## 6 — What I could not do

**Not empty.**

1. **The key does not attach anything in the shipped program, because there is no broker.**
   `main()` constructs no `MarketData`, so a person running `python -m live.tui` today presses
   `a`, types `QQQ`, and reads *"no market data - the app connects to no broker in this
   slice"*. **That is honest and it is not what Christoph asked for.** Wiring
   `IBKRMarketData` was considered and rejected inside this task: `ib_async` is asyncio-based,
   so a synchronous `connect()` inside a Textual message handler would block or deadlock the
   event loop, and doing it properly needs connection lifecycle, a client id that is not 11 or
   22-by-accident, and a failure path — **that is a slice, not a key binding.** 032 says
   *the smallest one*, so the seam is a constructor argument and the refusal names the gap.
   **A dedicated task is owed.**

2. **`live/attach/ibkr.py` remains untested and uncalled**, per §5. It cannot be tested here:
   `CLAUDE.md` records that no broker credential is reachable from any Claude-accessible
   config, deliberately.

3. **I could not confirm from inside the repo whether the overwrite destroyed anything.** It
   was answered by reading another session's transcript. **Nothing in this tree can detect a
   concurrent writer**, which is `031`, still unbuilt.

4. **Two pre-existing red tests are worth naming because they are structural, not this
   task's:**
   - `test_every_task_file_declares_a_state` — inbox `021`–`027` carry `status: READY`
     frontmatter instead of a `**Status**` header. **This is OBS-031**, and backfilling them
     is explicitly the wrong fix: it would make seven files differ from their Drive originals
     forever. **`032` itself carries a correct header**, so it does not add to that list.
   - `test_every_directory_holding_tests_is_declared` — red for the `029` worktree still
     mounted at `.claude/worktrees/029-entry-point`, a **copy** of the repo inside the repo.
     **This is OBS-034.** Removing the worktree clears it; it is locked and is not mine to
     remove.

5. **`docs/regime-snapshots/README-momentum-regime-snapshots.md` is untracked in the working
   tree** and belongs to `025`. **Left exactly where it is** — not committed, not moved, not
   read as mine.

6. **Part 5 of the task file was honoured: `christoph/` was not touched.** `013` was already
   retired to `christoph/done/` at `HEAD` by Christoph.

---

## 7 — Ledger rows

Two rows added to `docs/observations/OBSERVATIONS.md`:

- **OBS-035** — the class 032 names: three features shipped complete, tested and unreachable.
  What stays open is the rule nobody enforces, that **every slice adding something a person
  must reach needs a test that reaches it the way a person would — a key press, not a method
  call.** `029` and `032` each closed one instance and neither generalises.
- **OBS-036** — demonstrating a test red by reverting files in a shared checkout, and the
  detached-worktree alternative that costs nothing.

---

## Files

| file | change |
|---|---|
| `live/tui/app.py` | `ATTACH_KEY`, the binding, `action_attach`, `on_input_submitted`, `_record_attach`, `_rerender`, the `md` argument, the ATTACHED refusal row, the `Ctrl+P` correction |
| `live/tui/day_record.py` | `attach_refusal` field |
| `live/tests/test_attach_is_reachable_by_key.py` | **session B's**, plus one ported case. 12 tests |
| `tests/test_adoption_log_complete.py` | allowlist entry, count now 34 |
| `docs/observations/OBSERVATIONS.md` | OBS-035, OBS-036 |

---

## Exit

| kind | item | destination |
|---|---|---|
| UAT | Press `a` and attach QQQ against live TWS | **None** — no broker is wired; §6 item 1 |

`verify.ps1` was run at **18:05:43 +02:00, 2026-08-13**, and again after this note's final
edit so the output is newer than the note and carries the same `HEAD`. Its output is
`verify-output.txt`, read directly — **not quoted here, per HANDOFF-PROTOCOL v1.2.**

**`export-handoff.ps1` was run after the commit.** The first verify caught the mirror stale at
`16b5f9b` from 17:03 — three commits behind — which is section 5 doing its job. The `HEAD` it
recorded on this run is in the final `verify-output.txt`.

**One uncommitted path is expected and is not mine**:
`docs/regime-snapshots/README-momentum-regime-snapshots.md`, which belongs to `025`.

**This note needs to be pasted to chat.** It lands in a repo the design session cannot see,
and on 2026-08-11 two correct done-notes were written and neither arrived.

---
id: 018
title: The depth-ordering question, three UAT findings, and a rule for findings
status: RUNNING — stays RUNNING until this note reaches the design session
owner: claude-code
ran: 2026-08-12, 10:30 → 11:00 ET
tree: D:\Dev\momentum
---

# 018 — parts 2 through 7. Part 1 is owed.

**Status** RUNNING

**`018` is the correct number.** It was free when I checked at 09:06 ET and this file holds it.
No re-issue needed.

**Part 1 is NOT done, on Christoph's instruction — it is owed after 16:00 ET.** The `019` QQQ
capture is running and writes to `records/tape/`; part 1 reads it. **Part 1 stays open.**

**Suite: 144 passed → 154 passed, 0 failed.** All four refusals confirmed.

> **This note has to be pasted into chat.** Writing it is not reporting it.

---

## The capture is unaffected

Parts 2–7 touch the TUI, tests and the ledger. **No TWS connection was opened, nothing in
`records/` was read, written, moved, renamed or committed.** Verified mid-task at 10:53 ET:

```
[10:53:11 ET] trades=195187 quotes=23957 depth=1085829 connected=True max_skew=0.0s gaps=0
```

---

## Part 2 — the guard is re-evaluated on every resize

**The fix is not where it looks like it should go, and that is the finding.**

I put `on_resize` on `MomentumApp`, which is the obvious place. **It never ran.** Textual
dispatches `Resize` to *widgets*, not to `App` — so the handler looked correct, executed never,
and would have left the guard **exactly as launch-only as the one part 2 exists to fix.** It was
caught only because the test failed with `NoMatches: No nodes match '#too-small'`.

**A fix that silently does nothing is worse than no fix**, because the test suite would then
have recorded part 2 as done. It now lives on a `Frame(Vertical)` container:

```python
class Frame(Vertical):
    async def on_resize(self) -> None:
        await self.app._apply_fit()
```

`compose()` yields an empty `Frame`. **The decision is not taken there any more** — `_apply_fit`
runs on mount and on every resize, and switches **in both directions**.

**The message is recomputed on every call, never reused.** While already refusing, shrinking
again updates the text in place rather than leaving the first refusal's numbers on screen.

### Refusal A — confirmed, both directions

`test_shrinking_after_launch_refuses_and_growing_back_restores`:

| step | result |
|---|---|
| launch at 209×54 | panels render, no `#too-small` |
| **shrink to 74×24 after launch** | **`#too-small` renders, `query(Panel)` is empty** |
| **grow back to 209×54** | **panels restore, `#too-small` gone** |

`test_the_refusal_message_reflects_the_current_size_not_the_launch_size`: at 74×24 the message
contains `74x24` and **does not contain `209`**; shrinking again to 50×20 gives `50x20` and
**no longer contains `74x24`**.

**A one-way transition would have been worse than the behaviour it replaces** — a terminal that
refuses once and never recovers is one you restart, and restarting to recover from a resize
teaches you not to resize.

---

## Part 3 — the two unnamed rows

`config/layout.yaml` rows 5 and 8 are now **`select`** and **`submit`**. `human: true` is
untouched and the value cell still reads *your decision - correctly not a slice*, so the
distinction between *a stage the system does not perform* and *one it has not performed yet*
is intact.

```
   5 select      your decision - correctly not a slice
   8 submit      your decision - correctly not a slice
```

`test_every_pipeline_row_has_a_name` asserts all twelve rows have a name **and that the name is
not a value** — a cell starting with `[` or `(` is a badge that has drifted into the wrong
column, which is the more general form of the defect.

---

## Part 4 — `manage` is deferred

```
   9 manage      [ NOT BUILT ] (deferred - not core, revisit later)
```

**No new badge word was invented, and this was a deliberate refusal of the obvious fix.**
`[ DEFERRED ]` is not in `SPEC.md` §4's closed vocabulary, and `live/tui/grammar.py` states that
a new one **is a spec change, not a code change**. So the badge stays `[ NOT BUILT ]` — which is
true, the machinery does not exist — and the ruling lives in the reason.

**`slice not assigned` remains reachable**, for any stage declaring no claim at all. The loader
now refuses a stage making more than one claim across five (`built_by` / `slice` / `human` /
`deferred` / `renders`).

**The ruling's date is in `config/layout.yaml`, not on screen.** At the 67-column working width
the row is exactly 67 columns with the short wording; with the date it truncated. **A ruling
whose date is cut in half is worse than one that says where to look**, and the config file is
the record.

**`BUILD-PLAN.md` still contains no slice building position management.** That is unchanged and
is **OBS-006**, which stays `OPEN`. Part 4 records that the gap was *ruled on*, not that it was
filled. No slice number was invented.

### Refusal C — confirmed

`test_refusal_c_slice_not_assigned_stays_reachable_and_differs_from_deferred`. Both states
render, differ, and `deferred` does not appear in the unassigned string — so a genuine gap
cannot come to read as a decision somebody made.

**Its limit, stated because the exit test asked for character-class distinction and this is
not that.** Both render as `[ NOT BUILT ] (reason)`. **The shapes are identical; the words are
not.** I chose that over inventing a badge because the alternative is a silent spec change.
**If word-level distinction is judged insufficient, the fix is a `SPEC.md` §4 amendment adding
`DEFERRED` to the vocabulary — which is the design session's to make, not mine.**

---

## Part 5 — the UAT-to-work rule

### The shape chosen, and why the better one was unavailable

**The register keys on the LEDGER, not on the UAT.** Every file in `christoph/done/` must appear
in a **UAT review register** in `docs/observations/OBSERVATIONS.md` with a status of
`CITED` · `NO FINDINGS` · `NOT REVIEWED`.

**The structural shape — a `**Findings**` section authored into each UAT — is better, and I
could not build it.** `018`'s own *Do not* list forbids writing to `christoph/`, and so does
`CLAUDE.md`. **A check demanding a section this session cannot add, to thirteen files it cannot
edit, is red on arrival with no legal route to green.** Recorded in the register itself: if the
design session authors `**Findings**` sections into future UATs, **this register is the weaker
of two mechanisms and should give way to it.**

### Its limit

**It cannot detect a finding the reviewer overlooked.** It forces someone to look and to record
that they looked; it does not verify the quality of the look, and a reviewer who marks
everything `NO FINDINGS` passes it.

**What it does catch is what actually happened**: a UAT retired with findings that were never
routed anywhere now goes red instead of staying silent.

### Twelve rows say `NOT REVIEWED`, and that is the honest value

**Judging whether a retired UAT contains an actionable finding is a reading, and it is the
design session's reading to make.** Asserting *no findings* on twelve files this session did not
author, did not run, and cannot ask about **would be precisely the vacuous pass `018` warns
against** — a green check establishing nothing.

They are a **declared backlog with `review-by: 2026-09-12`**, one month rather than the
observations' three, because this is a reading task blocked on nothing.

### Seeded, and exercised

`009`'s three findings are **OBS-014, OBS-015, OBS-016**, all `PROMOTED` with resolutions naming
parts 2, 3 and 4. `009` is the register's one `CITED` row.

### Refusal B — confirmed twice

**Synthetically**, inside the suite: `unaccounted()` is a pure function, so a UAT with no
destination is tested with a synthetic name rather than a file — **`018` forbids creating one in
`christoph/`.**

**And live**, by deleting `009`'s register row:

```
AssertionError: these retired UATs have no row in the UAT review register:
    009-s009a-read-the-screen-at-working-width.md
```

**The message names the UAT.** Reverted; 17 tests pass.

`CITED` rows must name destinations that **resolve to real OBS ids**, so the status cannot
become an off switch — the same rule as `PROMOTED` needing a `resolution:`.

---

## Part 6 — three things reported, none acted on

### 6a · `handoff/accepted/012b` — byte-identical, and still anomalous

```
443f6ab54b8c460e73905dd070a46d7d9fc911af09987b910117f14a8335f661  5236 B  handoff/accepted/012b-uat-basis-correction.md
443f6ab54b8c460e73905dd070a46d7d9fc911af09987b910117f14a8335f661  5236 B  christoph/done/012b-uat-basis-correction.md
```

**Identical sha256.** So the copy property holds perfectly — **against a `christoph/` file
rather than a done-note.** `CLAUDE.md` defines `handoff/accepted/` as a byte-identical copy of
**a done-note**, and `012b` has no `handoff/done/` counterpart. **The mechanism works; the
definition does not cover this use.** Christoph's file, not touched.

### 6b · `too_small_message(40, 10, 60, 16)` — yes, now misleading. Not changed.

**Part 2 makes it worse, and the reason is specific.** The test still checks only the message
string, which is correct and still passes. But the app now recomputes minima on every resize,
so `60×16` is not merely *no longer sourced from the app* — **it is a value the app now
actively disagrees with several times a second.** The derived minimum for the shipped layout is
`75×11`.

**A reader who opens that test to learn the minimum gets a number that was never right and is
now contradicted by live behaviour.**

**Not changed, per the instruction not to weaken it.** The honest repair is to keep the
assertions and source the numbers from `MomentumApp.required()` so the test proves the message
formats whatever it is handed, rather than implying `60×16` means something. **That is a change
to an existing test and it is the design session's call.**

### 6c · The 80-column floor — two plausible future titles break it

**The threshold, computed rather than estimated:** a tile at 80 columns gets 24, and
`min_width = len("+- TITLE ") + 6 + 4`. **The longest title that fits is 10 characters.**

| candidate | chars | min_width | verdict |
|---|---:|---:|---|
| `INDICATORS` | 10 | 24 | **fits with ZERO slack** |
| `STOP TABLE` | 10 | 24 | fits with zero slack |
| `WATCHLIST` (current worst) | 9 | 23 | one column of slack |
| **`ORDER STAGING`** | 13 | 27 | **BREAKS THE 80 FLOOR** |
| **`RANKED WATCHLIST`** | 16 | 30 | **BREAKS THE 80 FLOOR** |

**Stated as a reading, not an observation.** `BUILD-PLAN.md` does not name panel titles; the
mockups are HTML and carry no extractable uppercase titles. **These candidates are derived from
slice titles** — `S017` *"Order staging"*, `S014` *"Ranked watchlist and grader vector"* — and
from the twelve stage names, on S009a's stated expectation that each unbuilt stage graduates to
its own panel. **A shorter title is always available, so this is a naming constraint rather than
a defect** — but nothing currently records it, and the first person to write `RANKED WATCHLIST`
will find out from a failing test rather than from a rule.

---

## Part 7 — commit, and NO push

**The second case applied, and more strongly than the task anticipated.**

- **`017` has not landed** — no `handoff/done/017-*.md` exists.
- **There is no remote at all.** `git remote -v` returns nothing.

**So no remote was created and nothing was pushed.** `017` owns that decision and its checks run
before the first push.

| commit | subject |
|---|---|
| `bbfdc53` | 018 parts 2-4: UAT 009's three screen findings |
| `d159feb` | 018 part 5: a retired UAT's findings must have a destination |
| *(paperwork)* | Record Christoph's placements and retirements, unmodified |
| *(this note)* | 018's done-note |

**Parts 2, 3 and 4 are one commit deliberately.** They are all *UAT 009's screen findings*, and
they are coupled at file level — `live/tui/app.py` carries the resize guard, the stage rendering
and the deferred branch. Splitting them would have meant hunk-level staging of one file into
three commits, which produces three commits that do not individually work. **Named rather than
forced**, per 014.

---

## Anything that was wrong on contact

**1 · Part 1 could not run, then was deferred.** At 09:06 ET there was no `018` in the inbox at
all — it was placed at 16:31 CEST, after `019`'s capture had started. **So part 1's ordering
constraint was already violated before the file existed**: it reads `records/tape/`, the capture
writes there, and the capture began at 09:07:31 ET. Christoph's instruction resolves it — part 1
runs after 16:00 ET. **It stays open.**

**2 · The fix for part 2 silently did nothing at first.** `App.on_resize` is never called;
Textual dispatches `Resize` to widgets. Recorded above because **a no-op fix that passes review
is worse than no fix.**

**3 · `christoph/done/012-uat-first-five-minutes_1.md` is NOT a duplicate.**

```
d8eabd97fd1f3fdf  6602 B  012-uat-first-five-minutes.md
e014400f182cfc2c  5781 B  012-uat-first-five-minutes_1.md
```

**Different content, 821 bytes smaller.** Two versions of one signed pre-registration now sit in
`christoph/done/`, and **nothing declares which is authoritative.** For a document whose whole
value is that it was signed before the answer was known, that is a serious ambiguity. **Not
touched** — `christoph/` is Christoph's. Logged in the UAT register.

**4 · Part 4's exit test asked for a distinction I did not build.** Refusal C asks for
`slice not assigned` and `deferred` to differ *at character-class level*. They differ at word
level only, because the alternative was inventing a badge word outside `SPEC.md` §4's closed
vocabulary. **Stated rather than quietly satisfied.**

**5 · A self-inflicted detour worth one line.** `test_every_pipeline_row_has_a_name` failed
under pytest while identical code passed standalone — a regex written through a shell heredoc
lost an escape, so the lookahead excluding the `12 of 12 · end` summary line did not. Rewritten
to key on the **name column being the literal `of`**, which is clearer than the lookahead was
anyway. **Sixth instance this week of a check whose subject includes its own edge case.**

**6 · Christoph placed `019` as a file while I was working.** `handoff/inbox/019-qqq-tape-capture-2026-08-12.md`
now exists, so my `019` note's remark that it arrived only as a paste is superseded. Committed
unmodified.

---

## Exit tests

| Test | Who | Result |
|---|---|---|
| **Green** | Claude Code | **144 → 154 passed, 0 failed.** No new failure |
| **Refusal A** | Claude Code | **PASS.** Shrink after launch → refusal, zero panels; grow back → panels restore. Message names the current size, not the launch size |
| **Refusal B** | Claude Code | **PASS**, synthetically and live. Deleting `009`'s register row goes red and names the UAT. Reverted |
| **Refusal C** | Claude Code | **PASS, with a stated limit** — `slice not assigned` and `deferred` differ at word level, not character-class level. See part 4 |
| **UAT** | Christoph | Run the terminal at 209×54, shrink below ~75 columns, then grow back. **The criterion is whether the screen ever shows a panel you cannot read.** Write the record to `christoph/open/` |

**This table turns `tests/test_uat_has_a_file.py` red**, because it names a UAT and no
`christoph/` file declares `018` yet. **That is 015's rule working, for the third note running.**

**I nearly evaded it by accident.** The first draft of this note reported the four refusals in
prose with no exit table — the suite stayed at `154 passed`, and the UAT demand simply never
fired. **A done-note that omits its exit table silently owes nothing**, which is a hole in 015's
mechanism worth knowing about: the check is positional on a table row, so a note with no table
is indistinguishable from a note with nothing to check. Recorded rather than exploited.

---

## Suite

```
before 018        : 144 passed, 0 failed
after  018        : 154 passed, 0 failed in 2.70s
after this note   : 1 failed, 153 passed — test_uat_has_a_file, per the exit table above
```

**+10 tests, no failures, none new.** The 144 baseline is `016`'s `1 failed, 143 passed` after
its one failure cleared — that failure was `test_uat_has_a_file` demanding a UAT file for `016`,
and it cleared when Christoph placed `christoph/done/010-016-read-verify-cold.md`. **The loop
closed exactly as 015 designed it**, for the second time this week.

`live/tests` alone: **56 passed.**

---

## Files

| file | change |
|---|---|
| `live/tui/app.py` | `Frame` container, `_apply_fit`, empty `compose`, deferred branch — parts 2, 4 |
| `live/tui/layout.py` | `Stage.deferred`, five-way one-claim check — part 4 |
| `config/layout.yaml` | `select`, `submit`, `manage` deferred — parts 3, 4 |
| `live/tests/test_tui_measured_against_its_tile.py` | 4 new tests, snapshots regenerated |
| `docs/observations/OBSERVATIONS.md` | OBS-014/015/016 + the UAT review register — part 5 |
| `tests/test_observations_ledger.py` | 6 new tests including Refusal B — part 5 |
| `christoph/**` | **UNTOUCHED.** Recorded in git, never edited |
| `records/**` | **UNTOUCHED.** Not read, not written, not committed |

---

**Paste this into chat. `018` stays `RUNNING` until it lands there, and part 1 is owed after
16:00 ET.**

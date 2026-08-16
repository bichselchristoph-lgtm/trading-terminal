---
id: 055
title: The checkpoint — establish a clean, merged, verified baseline before any product task
type: task
class: admin
task_version_executed: 1.0
owner: claude-code
tree: D:\Dev\momentum
branch: none — read-only on main, per instruction
bugs:
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: 'tools/now.py mis-parses the literal frontmatter value depends: none'
    spec: PROCESS-SPEC
    summary: >-
      depends_on() (tools/now.py:87-93) correctly treats an ABSENT depends:
      key as no dependencies, but does not special-case the literal string
      "none" written as a VALUE. "depends: none" parses to raw="none", which
      is non-empty, so the task gets a phantom dependency on a task literally
      named "none" that can never appear in done/superseded.
    actual: >-
      049 and 051 both write "depends: none" (the project's own established
      convention — 5 files use it) and both render as blocked ("needs none")
      in NOW.md when they are actually ready. This affects exactly the two
      tasks named next after this checkpoint.
    expected: >-
      depends_on() should treat the literal string "none" the same as an
      absent key. Not fixed here — 055 is read-only except NOW.md, and this
      is a tools/now.py code change, not a stale-derivation refresh.
  - id: NEW
    action: raise
    status: NEW
    priority: 2
    title: 049's frontmatter names the wrong tree for the phase3 corpus
    spec: PROCESS-SPEC
    summary: >-
      049 Part 0 depends on selection/phase3/, which exists only in
      D:\Dev\momentum-harness (archived, read-only). 049's frontmatter
      declares "tree: D:\Dev\momentum".
    actual: >-
      Confirmed: selection/phase3/ is 1.3 GB, present under momentum-harness,
      absent under momentum. Flagged by Christoph mid-session; independently
      confirmed here as part of item 12.
    expected: 049's problem to correct when it runs — not this task's to fix.
  - id: NEW
    action: raise
    status: NEW
    priority: 3
    title: Three retired UATs have no row in the UAT review register
    spec: PROCESS-SPEC
    summary: >-
      013-s010-check-against-your-charts.md, 014-for-christoph-account-parameters.md,
      015 for christoph attach qqq.md are retired but unregistered in
      OBSERVATIONS.md's UAT review register.
    actual: >-
      tests/test_observations_ledger.py::test_every_retired_uat_has_a_register_row
      and ::test_refusal_b_a_retired_uat_with_no_destination_is_red both red on
      this same underlying gap. Pre-existing, not caused by this session.
    expected: >-
      A CITED / NO FINDINGS / NOT REVIEWED row per file, per the test's own
      message. Not this session's to write — it may not write to christoph/.
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: test_inbound_run_record_has_no_conflicts is false-green on a plain re-run
    spec: PROCESS-SPEC
    summary: >-
      tools/sync_from_drive.py prints two different shapes for the same
      condition (files refused): "0 new - N REFUSED" when nothing new copied
      alongside the refusal, "N differing" when something new copied in the
      same run as a refusal. The test I wrote in 053 only matches "differing".
    actual: >-
      Discovered live, during this checkpoint's own item 9 and item 6: the
      sync ran with the same standing 040/043/052 refusals as always, printed
      "0 new - 3 REFUSED", and the test that exists specifically to catch this
      reported green. It caught the condition only by accident, while 053's
      own new file happened to land in the same run.
    expected: >-
      Match both shapes. Not fixed here - 055 is read-only. Flagged as the
      single most load-bearing finding in this report: a guard that stops
      guarding the moment its one observed shape changes is this project's
      most-repeated defect, and this is a new instance of it, in my own prior
      work, found by the checkpoint that exists to catch exactly this.
---

**Status** REVIEWED

# 055 — the checkpoint

**Read this cold.** One page, per instruction. Gate condition checked first: `handoff/done/054-*.md`
exists on `main`, and `main` contains both `053` and `054` (confirmed by `git merge-base
--is-ancestor`). Proceeded.

## 1. Twelve items, answered plainly

1. **`git status` on `main`: NOT clean.** 1 tracked file modified (`sync-run-record.md`, from a
   routine sync run) + 11 untracked files (10 new `christoph/open/` decision files, 1 new
   `handoff/inbox/055-*.md`) — all arrived via sync, none committed. Not fixed — this task does not
   commit anything but `NOW.md`.
2. **`main` contains `053` and `054`: yes, via ONE merge commit, not two.** `1413c34` "Merge branch
   '054-unblock-the-queue'" — because `053` was merged into `054`'s branch before it was pushed, so
   no separate `053`→`main` merge exists. Worth naming precisely since the task asked for "the merge
   commits" (plural).
3. **`git log origin/main..main`: empty.** Nothing unpushed.
4. **Worktrees: NOT zero.** Two beyond the main checkout — `wt-052` (`C:\...\Temp\wt-052`, branch
   `task-052`, already merged into `main`, clean, 0 days old) and `wt-probe`
   (`D:\Dev\_worktrees\wt-probe`, detached HEAD, clean, 0 days old). Same-day, not `OBS-034`'s
   multi-day pattern, but still extra registrations that should be removed.
5. **`verify.ps1` ran on `main`, from the main checkout.** Exit 0. `513 passed, 8 failed`.
6. **The red set: does NOT match the expected set, and the mismatch itself is a finding.** The
   suite now shows **7 failed** (it will show 8 once `test_inbound_run_record_has_no_conflicts` is
   fixed — see below), and only **1** was actually on `055`'s expected list. **The second
   expected-red item never fired**: `test_inbound_run_record_has_no_conflicts` passed even though
   the sync ran with the same standing `040`/`043`/`052` refusals it always has — because the test
   only matches one of two wording shapes the script can print for the same condition
   (`"N REFUSED"` vs `"N differing"`), a gap in my own `053` work, surfaced here rather than by
   the test itself. See bugs block, priority 1. The rest of the 6 unexpected reds, named with what
   each asserts:
   - `test_handoff_state_declared` — task files missing a `**Status**` header, old range (`021`–`038`).
   - `test_observations_ledger` ×2 — same underlying gap: 3 retired UATs (`013`, `014`, `015`) with
     no register row (see bugs block).
   - `test_regime_prompt_invariants` ×2 — a bare `6/9` figure in `REGIME-PROMPT.md`/`RE-SUPPLY.md`.
   - `test_regime_snapshot_could_not_do::test_the_format_still_lacks_a_key` — **this one is not a
     defect.** Its own message: *"This test failing is the GOOD outcome"* — a deliberate tripwire
     that fires once `REGIME-PROMPT.md` documents an `id` key, signalling the rule-15 grouping is now
     buildable. Correctly red, correctly not on the expected list (it's a trigger, not weather).
   - `test_uat_has_a_file` — UATs named in old done-notes (`017`–`042`) with no file authored.

   None of these were introduced or touched by `053`/`054`. Exact "last passed" dates were not
   established — that needs a bisect this checkpoint did not run, stated rather than guessed.
7. **The export ran** from the main checkout, HEAD `1413c34`, exit 0.
8. **`verify-output.md` in the manifest — confirmed by reading it directly:**
   `MANIFEST-momentum-code-handoff.md:158`, hash `B06484...`, 8856 bytes.
9. **Inbound sync's own status, captured correctly** (not through a pipe — `$?` immediately after the
   single `powershell.exe` invocation): **exit 1.** Refusal list unchanged: `040`, `043`, `052`
   (`DIFFERS, NOT OVERWRITTEN`), plus `035a` off-convention-but-copied. Matches `055`'s prediction
   exactly.
10. **`NOW.md` regenerated** (as a side effect of item 5's `verify.ps1` run — the one write this task
    is permitted). Four numbers: **ready 8** (`006 007 025 031 033 040 048 055`) · **blocked 3**
    (`049`, `050`, `051` — but see the bug on `049`/`051` below) · **on christoph 14** · **admin:product
    this stretch 14:5.**
11. **`records/tape/` inventory: 2 sessions, QQQ only, 3.9 GB total** — `2026-08-11` (1.93 GB) and
    `2026-08-12` (1.93 GB), flat files (`depth`/`quotes`/`summary`/`trades`/`provenance`), not
    subfoldered. **Close to but not exactly the ~4.1 GB this task's own text cites** — measured now,
    precisely, rather than repeated.
12. **`selection/phase3/`: `D:\Dev\momentum-harness\selection\phase3\`, 1.3 GB.** Contains
    `capture.parquet`, `holdout.parquet`, `training.parquet`, `venue_map.parquet`,
    `records/phase3_records.parquet`, plus `cache/`, `probe/`, `statistics/`, `ticks/` and several
    logs. Read only, confirmed. **`049`'s frontmatter says `tree: D:\Dev\momentum` — the wrong
    tree** (bugs block).

## 2. Not on the list — the most valuable line

**`NOW.md` shows `049` and `051` as `blocked — needs none`, and they are actually ready.**
`tools/now.py`'s `depends_on()` (lines 87–93) treats an absent `depends:` key as "nothing" but does
not special-case the literal string `"none"` written as a value. `049` and `051` both write
`depends: none` — the project's own established convention, used in 5 files — which parses to a
phantom dependency on a task literally named `"none"` that can never be satisfied. **This affects
exactly the two tasks named as next**, after `051` runs first. Not fixed here (`055` is read-only
except `NOW.md`, and this is a code defect, not a stale derivation); raised in the bugs block.

## 3. Bugs

See frontmatter `bugs:` — three entries: the `depends: none` parsing defect, `049`'s wrong `tree:`
(independently confirmed, not merely repeated from Christoph), and the three unregistered retired
UATs.

## 4. What could not be established

**Exact "last passed" commit for the 6 unexpected-red tests** — would need a bisect this checkpoint
did not run. Stated as unknown rather than guessed.

## After this

Per `055`: **`051` next, then `049`, then `050`** — each on its own branch in the main checkout, no
worktrees. `049`'s wrong-tree frontmatter and the `depends: none` misparse are both worth carrying
into `049`'s and `051`'s launch, even though `NOW.md` currently shows them blocked.

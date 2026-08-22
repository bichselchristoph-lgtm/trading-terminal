---
id: 055
title: The checkpoint — establish a clean, merged, verified baseline before any product task
type: task
class: admin
version: 1.0
originates: Christoph, 2026-08-16 — "check everything in cleanly before starting a product task"
unblocks: 051, 049 and 050. Nothing else in this task changes the terminal, and it is the last admin task before product work.
depends: 054
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 055 — the checkpoint

**Type: task. Class: admin.** **Changes nothing. Establishes what is true.**

**This task produces no commits except `NOW.md` if it is stale.** If it wants to change anything else,
**that is a finding and it stops.**

---

## Addressing

**If `handoff/inbox/055-for-code-task-the-checkpoint.md` exists in your tree and
`handoff/done/055-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Second condition, and it is the real gate: `handoff/done/054-*.md` must exist, and `main` must
contain the `053` and `054` branches.** **If either is untrue, stop and say which** — the checkpoint
is meaningless on an unmerged tree.

**Work in the main checkout, on `main`, read-only except `NOW.md`.**

---

## Why this exists

**Three product tasks follow. Every defect this session found was invisible because something looked
fine from the wrong vantage point** — a green run in a worktree that said nothing about `main`, an
`EXIT=0` that was `tail`'s, a copier refusal indistinguishable from a straggler.

**A baseline is worth having only if it is read once, deliberately, from the place the work will
actually run.**

---

## The standard

**Not "everything green."** The suite contains tests that are **knowingly red about defects that are
reported rather than fixed**, and that is correct.

**The standard is: the red set is exactly the expected red set, named.**

**Expected red, and why each:**

| Test | Red because |
|---|---|
| **inbound conflicts (`053` test 5)** | 040, 043 and 052 differ between Drive and the tree. **Records of what ran; not to be overwritten** |
| **any test asserting `verify-output` reachability, if `054` Part 4 did not complete** | Report it rather than assuming |

**Anything else red is a finding, not weather.** **A test permanently red has stopped carrying
information** — so any red outside that list gets named, with what it asserts and when it last passed.

**Do not add an allowlist.** The expected set lives in this report, not in the suite.

---

## What to establish

**Read each, report each. Do not fix anything.**

1. **`git status` is clean on `main`.** No uncommitted changes, no untracked files that should be
   tracked.
2. **`main` contains `053` and `054`.** Name the merge commits.
3. **`git log origin/main..main` is empty** — nothing unpushed.
4. **Zero worktrees.** `git worktree list` shows only the main checkout. **If any exist, they are
   orphans and this is exactly `OBS-034`** — name them and their age.
5. **`verify.ps1` runs on `main`, from the main checkout.** **A green run in a branch or a worktree
   says nothing about `main`, which is why this runs here and nowhere else.**
6. **The suite's red set, by name**, against the table above.
7. **The export ran and the manifest is current at this HEAD.**
8. **`verify-output.md` is present in the export manifest** — read the manifest, do not reason about
   the config.
9. **The inbound sync's refusal list, by name** — not the exit code, and **not through a pipe.**
   Capture the script's own status.
10. **`NOW.md` regenerated**, and its four admin-tax numbers reported as they stand.
11. **`records/tape/` inventory** — sessions, dates, symbols, size on disk. **Both `CLAUDE.md` files
    describe one session at ~2 GB; you measured two at ~4.1 GB.** `050` reads this data and **an
    inventory taken now is worth more than one taken while a task is running.**
12. **`selection/phase3/` location and contents**, in `D:\Dev\momentum-harness`. **Read only. That tree
    is ARCHIVED — build nothing there.** `049` Part 0 depends on it and its frontmatter names the
    wrong tree.

---

## The one thing this task may change

**`NOW.md`, because it is derived and regenerating it is not a decision.**

**Everything else: report and stop.**

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. **Then run the export.**

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | **No new tests.** This task asserts nothing it did not already assert — **a checkpoint that adds its own test is measuring its own arrival** |
| **Refusal** | Claude Code | **If `054`'s done-note is absent or the branches are unmerged, the task refuses and names which.** A checkpoint on an unmerged tree is a well-formed value answering a different question |
| **UAT** | Christoph | None. **The merge is his and it happens before this runs, not after** |

---

## Report

**One page. This is the document a design session reads before releasing three product tasks.**

1. **Clean or not**, with the twelve items above answered plainly.
2. **The red set, named**, and whether it matches the expected set exactly.
3. **The four `NOW.md` numbers.**
4. **The tape and corpus inventories.**
5. **Anything you found that is not on the list.** **That is the most valuable line in the report** —
   the list was written by the party that has been wrong about this tree four times today.
6. **Your `bugs:` block**, or `bugs: []`.

---

## After this

**`051`, then `049`, then `050`.** Each on its own branch in the main checkout. **No worktrees.**

**`051` first because it is the only one of the three that asks whether numbers already on screen are
wrong.**

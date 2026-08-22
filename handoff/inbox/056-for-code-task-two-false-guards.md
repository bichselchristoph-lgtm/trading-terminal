---
id: 056
title: Two false guards — a test that stopped guarding, and a ledger that reads a word as a dependency
type: task
class: admin
task_version: 1.0
owner: claude-code
tree: D:\Dev\momentum
branch: 056-two-false-guards — a branch in the main checkout, no worktree
depends: none
touches: tools/now.py, tools/sync_from_drive.py, sync-run-record.md, tests/
unblocks: NOTHING

  Stated honestly. Nothing Christoph sees on screen changes because of this
  task. What it buys is that the next green suite means something, and that
  NOW.md stops lying about which tasks are ready. Rule 16: this counts in the
  admin column and not in the second number.
---

**Status** WRITTEN

# 056 — two false guards

## 0. The gate

**If `handoff/inbox/056-for-code-task-two-false-guards.md` exists in your tree and
`handoff/done/056-*.md` does not, this task is for you. Otherwise stop reading and
ignore this message.**

## 1. Why this task exists

`055` was a read-only checkpoint. It found four things and fixed none, by design.
Two of them are priority 1, and both are the same shape: **a guard that reports
green while the condition it exists to catch is actually present.**

This task fixes those two and nothing else. The other two `055` findings are not
yours — one is Christoph's, one belongs to `049`'s replacement.

> §7 of the project instructions: *a test that passes is not a test that works.*
> Both parts below require you to **demonstrate red before accepting green.** A
> fix committed without having seen the test fail first has not been shown to fix
> anything.

## 2. Part A — the sync guard that matches a word instead of a condition

### What is wrong

`tools/sync_from_drive.py` describes the same condition — *files were refused,
because they differ and were not overwritten* — in two different wordings,
depending on whether anything else copied in the same run:

- `0 new · 3 REFUSED` — when nothing new copied alongside the refusal
- `N differing` — when something new copied in the same run as a refusal

`tests/test_inbound_run_record_has_no_conflicts` matches only the second wording.
On 16 Aug it reported **green** while `040`, `043` and `052` were all being
refused. It has only ever caught the condition by accident — on a run where a new
file happened to land beside the refusal.

### The ruling: match the condition, not the prose

**Do not fix this by adding the second wording to the test's pattern.** That
leaves the same defect one rewording away, and the rewording will happen, because
the outcome line is prose written for a human reader.

**The run record gains a machine-readable field, and the test reads that field.**

1. `sync-run-record.md` gains a structured refusal count per pair — a count, not a
   sentence. Name it plainly; `refused: N` is fine. Zero is written explicitly as
   `refused: 0`; **an absent field is not zero** (tenet 2), and the test must treat
   absence as a failure to report, not as a clean run.
2. The human-readable outcome line stays exactly as it is. It is for Christoph and
   for `verify.ps1` section 6, and rule 18's *silence must be meaningful* still
   governs it — `0 new · up to date` and `0 new · 3 REFUSED` must keep reading
   differently.
3. `test_inbound_run_record_has_no_conflicts` reads the structured field and
   ignores the prose entirely.

### Demonstrate red

Before the fix, and recorded in the done-note as an observation:

- Construct a run record fixture carrying the `0 new · N REFUSED` wording with no
  structured field, and show the **current** test green against it. That green is
  the defect, reproduced deliberately.
- After the change, show the new test **red** against a fixture with `refused: 3`,
  and red again against a fixture with the field absent altogether.
- Then green against `refused: 0`.

Fixtures live in the test tree. **Any scratch directory or throwaway file this
work needs goes to `$env:TEMP`, never into the repo** (rule 20).

## 3. Part B — `depends: none` parsed as a dependency

### What is wrong

`tools/now.py`, `depends_on()`, lines 87–93 as of `20058f9`. An **absent**
`depends:` key is correctly read as no dependencies. The **literal string** `none`
written as a value is not special-cased: it parses to `raw="none"`, which is
non-empty, so the task acquires a phantom dependency on a task named `none` that
can never appear in `done` or `superseded`.

`049` and `051` both write `depends: none`. Five files in the tree use that
convention. Both render as `blocked — needs none` in `NOW.md` while being
genuinely ready — and they are the two tasks named next after the checkpoint.

### The fix

`depends_on()` treats the literal values `none`, `None`, `NONE` and the empty
string identically to an absent key. Whitespace is stripped before the comparison.

**Do not fix this by editing the five task files.** `handoff/` is copy-and-keep;
nothing in it is edited, and a convention used in five files is the convention.
The parser is what is wrong.

### Demonstrate red

- A test asserting that a task file carrying `depends: none` renders as **ready**,
  not blocked. Show it red against the current parser.
- A second test asserting that a task carrying a real, unmet dependency still
  renders as **blocked**, so the fix has not simply disabled dependency checking.
  This one should be green before and after — say so, and say that you checked.
- Regenerate `NOW.md` through `verify.ps1`, never by hand. `049` and `051` should
  move out of `blocked`.

## 4. Part C — commit what is sitting on `main`

`main` was dirty at the checkpoint: `sync-run-record.md` modified, plus eleven
untracked files that arrived through the inbound sync — ten `christoph/open/`
decision files and `055`'s own task file. They are legitimate tree contents that
were never committed.

Commit them. One commit, message naming what they are and how they arrived.

**Do not touch the worktrees.** Two are registered (`wt-052`, `wt-probe`) and
three inert directories sit under `.claude/worktrees`. Removing them is deletion,
deletion is Christoph's alone (rule 19), and `git worktree remove` is denied by
policy in any case. `verify.ps1` section 7 already reports them. Leave them
reported.

## 5. Bugs

Raise a row for each of Part A and Part B in the frontmatter `bugs:` block, and
close both in the same block once the exit tests pass. `spec: PROCESS-SPEC` for
both.

Do **not** raise rows for the other two `055` findings. The three unregistered
retired UATs are Christoph's — he is the only party who can say `CITED` or
`NO FINDINGS` or `NOT REVIEWED` about his own UAT. `049`'s wrong `tree:`
frontmatter is a defect in a task file that cannot be edited in place; its
replacement is the design session's to author.

## 6. Exit tests

**Green** — the full suite runs. The two new tests pass. The previously-red set
drops by one: `test_inbound_run_record_has_no_conflicts` becomes a test that can
actually go red, and the five remaining reds from the checkpoint are untouched by
this task. **Do not quote a test count in the done-note** — state that
`verify.ps1` ran, and when.

**Refusal** — with a run record showing `refused: 3`, the sync test is red. With
the field absent, it is red. Both demonstrated, both named in the done-note.

**UAT** — none. This task changes nothing Christoph can look at. Stated rather
than invented; a UAT written to satisfy the shape of a task file is worse than
no UAT, because it retires and then owes a register row.

## 7. The done-note

`handoff/done/056-two-false-guards.md`.

- **Status: complete.** Not `REVIEWED`. `REVIEWED` is the design session's to set
  after reading the note and `verify-output.md` together — `055` set its own and
  should not have.
- Report the deliberate green in Part A as an observation. It is the most useful
  single line in this task: the shape of the failure, reproduced on demand.
- If anything blocks you that is a decision rather than a defect, write a question
  file and end the session. Do not wait.
- Anything found that is not in this task and not a bug goes to `OBSERVATIONS.md`
  with a `PROMOTED` or `DROPPED` resolution owed.

Closing sequence per `CLAUDE.md`.

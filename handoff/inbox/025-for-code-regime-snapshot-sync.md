---
id: 025
title: Copy the daily regime snapshots from the sync folder into the repo
status: READY
blocks: []
type: pipeline
owner: claude-code
---

# 025 — Copy the daily regime snapshots into `docs/regime-snapshots/`

**The scheduled task is the source of truth for the daily regime read.** It publishes to a
Drive-sync folder. **This task copies from there into the repo, one way, daily.**

| Location | Role |
|---|---|
| The scheduled task | **Authors.** Source of truth |
| `D:\claude-googledrive-sync\momentum-regime-snapshots-from scheduled\` | **Publishes.** Written by the task, owned by Drive sync |
| `D:\Dev\momentum\docs\regime-snapshots\` | **Consumes.** This task's destination. Committed |

**Note the source folder name contains a space** — `...-from scheduled`. Quote it everywhere.
An unquoted path here fails in a way that looks like an empty folder rather than an error.

**Why the repo needs a copy at all.** The sync folder is outside the tree, machine-local, and
not under version control. **The join that eventually answers *"did regime separate
outcomes"* runs against the trade log, which is in the repo** — and a join across a folder
Drive can re-sync, reorder or partially populate is not a join anyone can reproduce.
**Committing the snapshot is what makes the answer checkable a year later.**

---

## Standing constraints

- **One way. Never write to the sync folder, never delete from it, never rename in it.** It
  is owned by Drive sync and by the scheduled task. **A file that appears there because this
  task put it there would be indistinguishable from an authored snapshot.**
- **Copy, never move.** The source must remain intact after the run.
- **Idempotent.** Running twice changes nothing the second time. It will be run daily and
  will usually have nothing to do.
- **Never create a file to fill a gap.** Not an empty one, not a placeholder, not a stub.

---

## Part 1 — The copy, and the one rule that matters

For each file in the source folder:

| Case | Action |
|---|---|
| Not in the repo | **Copy it.** |
| In the repo, **byte-identical** | **Do nothing.** This is the normal case on a re-run |
| In the repo, **differs** | **Do not overwrite. Report it and stop.** |

**That third row is the point of this task.** A snapshot carries `frozen_at`, written once
and never updated — **it describes a moment that has passed.** So a source file differing
from the repo copy means one of two things, and **both matter more than getting today's file
copied**:

- the scheduled task re-ran and produced something different for a day it had already
  answered, or
- something edited a record that is supposed to be immutable.

**Report both versions' `frozen_at` and their hashes, name the file, and leave the repo
untouched.** Do not diff-and-merge, do not take the newer, do not take the larger.
**Silently replacing it would destroy the only evidence that it changed.**

**Compare on content, not on modification time.** Drive sync rewrites mtimes on files whose
bytes never changed — a copy, a re-sync or a client reinstall is enough. **An mtime-based
comparison would report a change every time Drive touched the folder**, and the real changes
would be lost in the noise. Hash the bytes.

---

## Part 2 — Gaps are states, not errors

**A missing day is a fact about the world**, not a failure of this task. The market closes;
the task may not fire.

**Do not create anything for a missing day.** Report what is absent between the earliest and
latest snapshot present, and **distinguish weekdays from weekends and holidays** using
`core/session.py` — the existing calendar, not a fresh one. **A gap on a trading day is worth
noticing; a gap on Thanksgiving is not, and a report that cannot tell them apart will be
ignored within a week.**

---

## Part 3 — Commit them, and prove they are tracked

The snapshots are the record. **Commit them.**

**Then assert with `git check-ignore` in a test that `docs/regime-snapshots/` is *not*
ignored.** `.gitignore` in this repo has swallowed an intended path before, and the negation
blocks are load-bearing. **A snapshot silently untracked looks present locally and is absent
in history — the worst available outcome for a record whose entire purpose is to be joined
against trades later.**

---

## Part 4 — Run it daily, and make its silence meaningful

Wire it to run once a day. **The normal outcome is that it copies one file pair and says so
in one line.**

**It must report even when it does nothing**, and the report must distinguish:

- `0 new · 0 differing · up to date` — the healthy no-op
- `0 new · source folder empty or unreachable` — **a different fact entirely**, and the one
  that means the pipeline is broken rather than idle

**A task that prints nothing when it succeeds prints nothing when it fails.** These two
states look identical from outside and must not read identically.

---

## Done when

- New snapshots appear in `docs/regime-snapshots/` and are committed.
- A re-run copies nothing and says so.
- **A deliberately-modified repo copy causes a report and no overwrite** — demonstrate this,
  do not assert it.
- The `git check-ignore` test exists and passes.
- The source folder is byte-for-byte unchanged after a run.

---

## Deliverable

`handoff/done/025-for-code-regime-snapshot-sync.md`:

1. How many files were copied on the first run, and the date range covered.
2. **The differing-file case demonstrated** — modify a repo copy, run, quote the report,
   confirm nothing was overwritten.
3. The `git check-ignore` assertion, quoted.
4. Any gaps found, split into trading days and non-trading days.
5. **What you could not do**, and why. Empty is suspicious.
6. `verify.ps1` run at `<time>`.

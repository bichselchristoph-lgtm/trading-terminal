---
id: 043
title: A third Drive pair, and two instruments that watch nothing
type: task
class: admin
version: 1.1
unblocks: S011 and S012 — their UAT files reach christoph/open/ by hand today, and a UAT that never arrives is a slice that cannot exit
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 043 — three things nobody is watching

**Type: task. Class: admin.** Three parts, one theme: **an instrument that reports on everything
except itself.**

**Part 1 is a rule change Christoph made on 2026-08-15.** Parts 2 and 3 close `OBS-044` and
`OBS-046`, both of which earlier tasks correctly refused to fix in passing.

**v1.1 corrects the Drive folder name.** v1.0 said `momentum-inbox-christoph`. **The folder
Christoph created is `momentum-christoph-open`**, and it exists. v1.0 was never copied into the tree.

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/043-for-code-task-third-pair-and-two-instruments.md` exists in your tree and
`handoff/done/043-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes — `OBS-046`, which this task also fixes.

---

## Part 1 — a third Drive pair, for `christoph/open/` only

**The rule that no Claude writes to `christoph/` by any channel is amended, narrowly.**

| Folder | Before | Now |
|---|---|---|
| `christoph/open/` | placed by hand | **arrives via Drive, like `handoff/inbox/`** |
| `christoph/done/` | Christoph only | **Christoph only. Unchanged. Locked.** |

**Why the rule changes.** `christoph/open/` files are **authored by the design session** — they are
its task files for Christoph. There was never an authorship conflict there, only a placement
convention, and the convention cost a manual copy on every UAT. **The rule existed because of a
limit, and the limit has lifted** — the same reasoning that retired the download-and-copy step for
`handoff/`.

**Why `christoph/done/` does not change.** That half is Christoph's answers. It is copy-verify-retire
and he performs it. **Nothing writes into it, by any channel, ever.** A task that appears to require
writing there is defective — stop and report.

### The change

**`config/sync.yaml` gains a third pair. There is still one copier.**

| # | Drive folder | Destination | Direction |
|---|---|---|---|
| 1 | `momentum-regime-snapshots-from scheduled` | `docs/regime-snapshots/` | in |
| 2 | `momentum-inbox-handoff` | `handoff/inbox/` | in |
| **3** | **`momentum-christoph-open`** | **`christoph/open/`** | **in** |

**The folder exists** — created 2026-08-15, alongside `momentum-christoph-done`.

**A naming inconsistency worth recording, not fixing.** The inbound pairs so far carry `inbox` in
the name (`momentum-inbox-handoff`); the outbound ones carry the repo folder
(`momentum-code-handoff`, `momentum-christoph-done`). **`momentum-christoph-open` reads outbound by
that convention and is inbound.** Christoph named it for symmetry with `momentum-christoph-done`,
which is a defensible reading — the two folders are the two halves of one exchange. **Record it in
`OBSERVATIONS.md` so the ambiguity is on the ledger. Do not rename anything.**

**Same rules as pair 2, unchanged:** not present ⇒ copy and name it · present and byte-identical ⇒
do nothing · **present and differing ⇒ do not overwrite, report, stop.** Compare on content, never
on modification time.

**No new script. No second copier.** If the existing one cannot take a third pair without being
duplicated, **stop and report** — `SPEC.md` §4.4 and §4a: a copier is configured, never duplicated.

**A test must assert that no configured pair has `christoph/done/` as a destination.** Positional,
scoped to `config/sync.yaml`. **Seen red by adding one.** The lock has to be a mechanism, not a
sentence in a document — and where it cannot be a missing tool, it should at least be a red test.

---

## Part 2 — the inbound copier leaves no record at all

**`OBS-044`.** `037` gave the outbound export a run record on every attempt. **`tools/sync_from_drive.py`
has the same defect and is worse off: three stdout lines and nothing on disk.** `037` said *"say so
and stop"*, and it did. This is the follow-through.

**Give it the same treatment, reusing `037`'s mechanism rather than a parallel one:**

- **A run record written before the attempt and again after**, so a run killed mid-copy leaves
  `last_attempt` moved and `last_success` stale — the signature to look for.
- **At the repository root, outside every sync source and destination.** A record that only exists
  where the copy lands cannot report a failure to reach there.
- **Four distinct outcomes on stdout**, none of them the same sentence: `N new · <names>` ·
  `0 new · up to date` · `0 new · source unreachable` · `0 new · destination unreachable`. **Both
  failures exit non-zero and still write the record.**
- **A refused file is its own outcome** and must not read as `up to date`. The `035` collision made
  the copier exit 1 on every run for two days.

**`037` reintroduced its own bug inside its own fix** — the record's fields were indented into a
markdown code block, so `^last_success` never matched and every failed run silently reset it to
`never`. **Found by executing the refusal, not by reading the code.** Do the same: **run both failure
paths and read the record afterwards.**

**Whether the two copiers share one record file or keep two is your call.** State which you chose
and why. **One file with three sections is probably right** — `verify.ps1` then has one thing to
read — but a shared file is a shared failure mode, and that trade is yours to judge from the code.

---

## Part 3 — `verify.ps1` reports worktree count and age

**`OBS-046`.** Two worktrees from 2026-08-13 outlived their tasks by three days and kept
`test_pytest_collection` red the whole time. **`OBS-034` predicted the breakage was transient.
Measured three days later it was not, because nobody removed them.**

**The tasks were accepted and merged. The worktrees stayed. Nothing said so.** Same shape as the
export: an instrument that runs after every task, reporting on everything except the thing that
outlives tasks.

**Add to `verify.ps1`:**

```
  worktrees         2 — 024-subagent-roster (3d), 029-entry-point (3d)
```

**Name, and age in days.** No verdict, no threshold — `verify.ps1` states facts and draws no
conclusions, and this section is no exception.

**Do not have `verify.ps1` remove anything.** It is read-only, and a verification script with a side
effect cannot be run to find out whether something happened. **`OBS-036`.**

**Christoph has confirmed the `024` and `029` worktrees are clean, merged and safe to remove.**
Remove those two as part of this task. **Check `git status --porcelain` in each before removing, and
if either is dirty, stop and report** — the confirmation was given about a state that may have moved.
**Never remove a worktree that is not one of those two.**

---

## Not in scope

No panel work. No spec amendments — `038`, `041` and `042` cover those. **No changes to
`christoph/done/`, by any means.** No renaming of Drive folders. No new scheduler and no daemon:
`037` established that the export runs as a final action alongside `verify.ps1`, and pair 3 changes
nothing about that.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export**, from the main checkout — not from a worktree (`OBS-045`).

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran. The `christoph/done/` guard test seen red by adding a forbidden pair; the inbound record tests seen red by removing the record |
| **Refusal** | Claude Code | Pair 3's Drive source pointed at a path that does not exist ⇒ `source unreachable` on stdout, exit non-zero, **run record still written.** And a differing file in `christoph/open/` ⇒ reported, not overwritten |
| **UAT** | Christoph | `c023` — drop a file into `momentum-christoph-open`, run the sync, confirm it lands in `christoph/open/` and that `christoph/done/` is untouched |

---

## Report

1. **Whether one copier took a third pair without duplication**, or what stopped it.
2. Which outcomes `sync_from_drive.py` could emit **before** — measured, not read off the source.
3. Whether you chose one run record or two, and why.
4. **Both inbound failure paths executed, and the record read afterwards.** Quote it.
5. Whether `024` and `029` were clean when you checked, and that only those two were removed.
6. **What `verify.ps1`'s worktree line reads now.**
7. The reds, quoted.
8. **What you could not do**, and why. Empty is suspicious.

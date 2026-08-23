---
task: 064
class: admin
unblocks: NOTHING
depends: none
touches: verify.ps1 sync.ps1 export-handoff.ps1 tests/test_task_file_shape.py
supersedes: 063
---

# 064 — five instruments, four disjoint files, one commit

**If `handoff/inbox/064-for-code-task-instrument-batch.md` exists in your tree and `handoff/done/064-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. Shape, and why it is one task

**Five defects, all in the machinery, all cheap, none blocking each other.** Batching them is worth it only because **the four files below do not overlap** — that is the property that makes parallel work safe here, and it is the only reason this is one task rather than five.

| Part | Owns, exclusively | Fixes |
|---|---|---|
| **A** | `verify.ps1` | PowerShell 5.1 parse · `NOW.md` four numbers |
| **B** | `sync.ps1` | `last_success` pinned 8 days · retired items re-copied · the three divergences |
| **C** | `export-handoff.ps1` | Manifests written from a dirty tree |
| **D** | `tests/test_task_file_shape.py` | One bad YAML file blinds the guard for thirteen |

**Run A–D as four subagents, in parallel.** Each is given exactly one file and must not write outside it.

**No subagent commits, stages, or runs the closing sequence.** The parent session does that once, after all four report. **This is a convention stated in a task file, not a control** — nothing prevents a subagent staging something. **It is weaker than a missing tool and you should treat it as weaker.** The mitigation that is real: the file sets are disjoint, so a mistake shows as an unexpected path in `git status` rather than as lost work.

**If any part cannot be done, that part refuses and the other three still land.** A part that refuses does not block the commit.

---

## 1. Part 0 — close `063` first, before the subagents start

**`063` refused correctly and left no done-note**, so it will read `ready` forever and refuse on every future run. **Its precondition was unsatisfiable and that is the task author's defect, not yours:** the scheduled sync writes `sync-run-record.md` and `export-run-record.md` — both tracked — every fifteen minutes, so `git status --porcelain` is empty only by luck.

**Write `handoff/done/063-quiet-tree-reverify.md`** recording: it refused per its own §1, the refusal was correct, the precondition was unsatisfiable by construction, `064` supersedes it, and no `verify.ps1` run occurred. **Do not re-run `063`. Do not delete it.**

---

## 2. Part A — `verify.ps1`

### A1. It does not parse under Windows PowerShell 5.1

**`062` observed this and did not diagnose it.** A BOM-less UTF-8 file misread under the 5.1 system codepage is **a plausible cause that nobody has tested.**

**Test it before fixing it.** Copy the file to `$env:TEMP`, add a UTF-8 BOM to the copy, invoke `powershell.exe -File` against both. **Report what you observed.** If the BOM fixes it, apply it to the real file. **If it does not, say so and stop there — do not try a second theory and report it as the cause.**

### A2. Which interpreter the scheduled tasks actually name

**This is why A1 matters and it is read-only.** Report the `Execute` and `Argument` values of every scheduled task that invokes anything in `D:\Dev\momentum`. **If any names `powershell.exe` rather than `pwsh`, that task has been failing to parse and its run record has been lying by omission.**

**Do not change a scheduled task.** Report it; changing one is outside the repo.

### A3. `NOW.md` emits one number where the rule requires four

Currently `admin:product this stretch 17:8`. **Required, as four separate lines:**

```
admin tasks this stretch      17
  naming a product task        4
product tasks this stretch      8
days since last product task    3
```

**The second line is the one that carries the signal** — it counts admin task files whose `unblocks:` names a *product* task, not `NOTHING` and not another admin task. **The gap between the first and second lines is what makes an admin chain visible in arithmetic instead of needing a prohibition. Collapsing the four into a ratio deleted exactly that.**

**`days since last product task` is derived from the commit date of the most recent `handoff/done/` note whose task file carried `class: product`.** If none exists in the window, render the count and say what it is counted from — **never `0`, which reads as *one landed today*.**

---

## 3. Part B — `sync.ps1`

### B1. `last_success` has been pinned for eight days and the pin is the bug

**Observed: last attempt 2026-08-23, last success 2026-08-15 — 188 hours.** Cause is visible in the same record: `handoff_inbox: 0 new · 3 REFUSED · 30 unchanged`, every run, since the 15th.

**A refusal is a designed outcome, not a failure of the run.** The copier did exactly what it is specified to do. **But by counting it as "not a success", the one signal that would report a broken channel has been saturated for eight days and can no longer report anything.**

**Split the two facts:**

- **`last_success`** advances when a run completes as designed, refusals included.
- **`refused`** becomes its own count in the record, with the offending filenames. **It goes to zero exactly when the problem is gone** — the self-clearing property the clock never had.

**Do not make refusals stop being reported.** Make them stop hiding a different fact.

### B2. Report the three divergences; resolve none of them

`040`, `043`, `052` differ between Drive and the tree. **For each: which side is newer, how many lines differ, and the first differing line.**

**Do not overwrite either copy. Do not pick a winner.** A handed-off task file that differs means one of the two is not the task that was run, **and which one wins is a decision about work already done, not a sync defect.** Report and stop — that part of the existing behaviour is correct.

### B3. A retired `christoph/open/` item is copied back in

**Present in `christoph/done/` and absent from `christoph/open/` means retired, not missing.** The copier currently reads the absence as *not in the destination* and restores it.

**A file whose basename exists in `christoph/done/` is never copied into `christoph/open/`.** Report each one skipped, by name — **silence here would make a retirement indistinguishable from a sync that never ran.**

**This does not clear the Drive source folder** and must not try to. It stops the tree from resurrecting what was retired.

---

## 4. Part C — `export-handoff.ps1`

**Observed: all three manifests carry `tree at export DIRTY -- 3 uncommitted paths`.** A manifest names a HEAD, but the bytes exported were the working tree's. **So the manifest describes a state that never existed as a commit, and its HEAD is a claim it cannot support.**

**The export still runs** — refusing would strand every done-note behind an unrelated dirty file.

**But the manifest must state, at the top and by name, every path that differed from HEAD at export time.** Not a count. **A reader must be able to tell whether the dirt was in a file this export actually carried.**

**And the HEAD line must say so:** `HEAD 8be92f8 + 3 uncommitted paths (listed below)` rather than a bare hash. **A bare hash beside dirty bytes is the same defect as a value rendered with nothing behind it.**

---

## 5. Part D — `tests/test_task_file_shape.py`

**Observed: three tests in this file fail with a traceback.** `handoff/inbox/056-*.md` has an unquoted colon inside prose in its frontmatter; `yaml.safe_load` raises; the loop has no per-file handling and aborts **before any other file is checked.**

**So `class`, `unblocks` and the destination rule have gone unverified on every task file from `049` onward — thirteen of them, including this one.** OBS-080.

**Fix the guard, not `056`.** `handoff/` is copy-and-keep: **editing a file there puts the tree and Drive out of byte-sync, which is precisely the `040`/`043`/`052` condition Part B is reporting on.** A correction to a task file arrives as a new task, never as an edit.

**Required:** each file parsed inside its own try/except. **A file that fails to parse is a named violation attributed to that file — not a traceback, and never a reason to stop checking the rest.**

**Demonstrate red properly.** Two scratch files under `$env:TEMP`: one with malformed frontmatter, one clean and violating a rule. **The test must report both, in one run.** A run that reports only the first is the bug you are fixing.

**Expect new failures once it works.** Twelve task files have never been checked. **Report every violation it now finds and fix none of them** — they are other tasks' files, and fixing them from inside this task is how a task acquires work nobody scoped.

---

## 6. Not in this task

- **`056`'s frontmatter.** §5.
- **Resolving `040` / `043` / `052`.** §3, B2.
- **Any scheduled task's configuration.** Outside the repo.
- **The worktrees, the orphan directories, the Drive `momentum-christoph-open` folder.** All deletions — Christoph's alone.
- **`.claude/settings.json`.** You cannot write it and must not route around that.
- **Anything product.** No panel, no level, no basis, no threshold.

---

## 7. Exit tests

**Green.**
- Each of A–D lands or refuses with a stated reason. A refusal in one does not block the others.
- **D was seen reporting two violations from two scratch files in one run**, having been seen red as a single abort first.
- **B's run record shows a `refused` count separate from `last_success`**, demonstrated against the current three.
- **C's manifest names the dirty paths individually** — verified by exporting from a deliberately dirty tree.
- **A1 states what was observed, not what was assumed.** If the BOM theory failed, that is a legitimate result.
- `handoff/done/063-*.md` exists.

**Refusal.**
- **A subagent that would need to write outside its one file stops and says which file and why.** It does not take the write.
- **A1 with no confirmed cause is a pass** — reported as unexplained, with the observations, and no cause named.

**UAT (Christoph).**
- Read the four `NOW.md` numbers. **The second one is the one to look at.**

---

## 8. The closing sequence

**Parent session only, after all four parts report.** Per `CLAUDE.md`, from the main checkout. **One commit containing all parts that landed.**

**`verify.ps1` runs last and is the version this task just modified** — say so in the note. **A run of an instrument the same commit changed is not independent evidence about that instrument**, and the note should not present it as such.

---

**This note needs to be pasted to chat.**

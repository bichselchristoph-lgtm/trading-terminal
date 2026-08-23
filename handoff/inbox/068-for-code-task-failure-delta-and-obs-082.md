---
task: 068
class: admin
unblocks: NOTHING
depends: 064
touches: verify.ps1 docs/ADOPTION-LOG.md tests/test_donenote_bugs_block.py
---

# 068 — the failure set stops being something a note has to quote

**If `handoff/inbox/068-for-code-task-failure-delta-and-obs-082.md` exists in your tree and `handoff/done/068-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. Why this exists, and what it is not

**Three notes in a row quoted a test count, and the verification gate says they must not.** *A note never quotes a test count. It states that `verify.ps1` ran, and when.* The rule is written down and it has been broken three times.

**The reporting was not the defect.** `065`'s comparison against `064` was correct and the reconciliation held: `14 + 545` became `14 + 546`, one test added, failing set byte-identical. **What failed is that "the same as before" had no referent anywhere except a reader's memory of a different task's note.**

**So this does not add a fourth wording of the rule. It removes the need to quote anything** — rule 14, and the same move as taking away the delete operation.

**Two of `OBS-082`'s failures ride along** because they are cheap and in the same neighbourhood. **The third thing that was going in here has been struck:** `test_attaching_state.py` and `test_pacing_guard.py` are tracked and present at HEAD under `02d4083`. **The design session was wrong about that and the check was worth running anyway.**

---

## 1. Run after `064`, not beside it

**`064` Part A also writes `verify.ps1`.** One file, two tasks, so they serialise. **`068` starts after `064`'s commit lands.**

**Within `068`, the three parts are disjoint** — `verify.ps1`, `docs/ADOPTION-LOG.md`, `tests/test_donenote_bugs_block.py` — **and run as three subagents.** Confirm the file sets before starting; if `064` moved something, say so rather than working around it.

**No subagent commits. The parent commits once.** A convention, not a control.

---

## 2. Part A — `verify.ps1` §1 reports the delta

**Today §1 prints the summary line and the named failures. It says nothing about whether that set changed.**

**Required, three lines beside the existing output:**

```
  unchanged  14
  new         0
  fixed       0
```

**And when any of `new` or `fixed` is non-zero, name the tests individually.** A count of two new failures cannot be acted on; two names can.

### **Where the previous set is stored, and why it is gitignored**

**At the repository root, beside the run records.** **Gitignored — not tracked.**

**This matters and it is not a preference.** `sync-run-record.md` and `export-run-record.md` are tracked, so the 15-minute scheduled sync dirties the tree every quarter hour. **That is the whole reason `063`'s precondition was unsatisfiable.** Adding a third tracked file written on every run would make it worse for exactly the same reason.

### **The first run, and any run where the file is absent**

**Report `no previous run recorded`. Never `new 0`.**

**Absence is not zero, and it applies to your own instruments.** A missing state file and a run that fixed nothing must not read alike.

### **Order of operations, stated because getting it backwards is silent**

**Read the previous set → compute the delta → print it → then overwrite the file with the current set.** Writing first makes every run report zero change, and it would look exactly like a stable suite.

---

## 3. Part B — the two `ADOPTION-LOG.md` rows

**`test_adoption_log_complete.py::test_every_tracked_file_is_accounted_for` has been red since `064`.** `live/tests/test_attaching_state.py` and `live/tests/test_pacing_guard.py` are tracked with no row.

**Add both**, in the format the `053`/`054`/`061`-era *authored in this tree; not imported* rows use. **Read one of those first and match it rather than inventing a shape.**

**Provenance paperwork on files that exist.** Nothing about the guard 058 built is missing.

---

## 4. Part C — a guard that cannot be satisfied has to yield

**`test_donenote_bugs_block.py` is red because `058`'s done-note has no `bugs:` key.**

**And it cannot be fixed the way it is asking to be fixed.** `handoff/` is copy-and-keep: **nothing there is edited, because a done-note is exported and an edit puts the tree and Drive out of byte-sync on bytes** — which is the `040`/`043`/`052` condition the inbound copier has been refusing on since 15 August. **`061` could add `bugs: []` to its own note only because that note had not been committed yet. `058`'s has.**

**So two rules collide: a permanently red test has stopped carrying information, and nothing in `handoff/` is edited.**

**The guard yields. The archive does not.** The guard's job is notes still being written; **an already-exported note is a record of what was true, and records are not corrected.**

### **What to build**

**A note that has been exported is out of scope for failure and is reported instead.**

- **Exported is read from the export manifest**, not inferred from a number or a date. **Do not raise the `FROM_TASK` floor to step over `058`** — pinning the scope to whatever currently passes is `B-029` exactly, and the guard would stop protecting the next note the same way.
- **Every skipped note is printed by name with its reason.** A skip nobody sees is the guard silently shrinking.
- **`verify.ps1` §1 surfaces the count**, so it is a content signal that goes to zero when the last such note ages out rather than a warning in a file nobody opens.

**If the manifest cannot be read, the test refuses by name rather than skipping everything** — a scope check that fails open is worse than no scope check.

---

## 5. Not in this task

- **The other twelve failures.** Nine predate all of this; three are `test_task_file_shape.py` and belong to `064` Part D.
- **`058`'s done-note.** Not edited. §4 is the whole answer.
- **Any scheduled task's configuration.** Outside the repo.
- **`065`'s phrasing.** A correction arrives as a new task, and this is it.

---

## 6. Exit tests

**Green.**
- **§1 prints `unchanged` / `new` / `fixed`, and names anything in the last two.**
- **Seen against a deliberately-broken scratch state file**: one test removed from the previous set reports `fixed 1` by name; one added reports `new 1` by name. **Not a synthetic stand-in for the parser — the real §1 path.**
- **With the state file deleted, it reports `no previous run recorded`.**
- **`test_adoption_log_complete` green.**
- **`test_donenote_bugs_block` green, with `058`'s note named as skipped and its reason stated.**

**Refusal.**
- **Export manifest unreadable → the scope check refuses by name.** It does not skip every note and pass.
- **State file present but unparseable → reported as unreadable, not as an empty previous set.** Same reason as the missing-file case.

**UAT (Christoph).**
- Read §1 once. **`unchanged 12 · new 0 · fixed 2` should be legible without reference to any earlier note.** That is the whole point of the task.

---

## 7. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**`verify.ps1` runs last and is the file this task changed** — say so. **A run of an instrument the same commit modified is not independent evidence about that instrument**, and the note should not offer it as such.

---

**This note needs to be pasted to chat.**

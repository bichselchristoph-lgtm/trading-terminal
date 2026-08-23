---
task: 063
class: admin
unblocks: NOTHING
depends: none
touches: none
---

# 063 — re-verify 061 from a quiet tree

**If `handoff/inbox/063-for-code-task-quiet-tree-reverify.md` exists in your tree and `handoff/done/063-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. Why this exists

`061`'s done-note §8 records that while it ran, **another session held uncommitted changes in the same checkout — including to `verify.ps1` itself.** So the green run `061` reports was produced by an instrument that was being edited while it measured.

**Nothing is alleged to be wrong with it.** It is simply not verified, and the verification gate says a note's claims are unverified until raw output is read. `061` handled the situation correctly — it left the other session's work alone and committed only its own index. **This task is the missing measurement, not a correction.**

**It does not re-do `061`'s work.** It re-runs the instrument over the same tree once the tree is quiet, so `REVIEWED` has something to stand on.

---

## 1. Precondition — this task must not start on a dirty tree

First action, before anything else: `git status --porcelain`.

| Result | Action |
|---|---|
| **Nothing reported** | Proceed to §2 |
| **Tracked files modified or staged that this session did not write** | **Stop.** §3 |

**If it is dirty: stop.** Write a question file naming **every path reported, individually** — not a count. Then end the session.

**Do not stash. Do not check out. Do not clean. Do not commit on another session's behalf.** Another session's uncommitted work is never discarded on instruction; its author commits it. **The refusal is the correct outcome, not a failure of this task.**

**A count is not a report here.** "3 files dirty" cannot be acted on by the reader; the three paths can.

---

## 2. Run

Tree clean, so:

1. **`verify.ps1`.** Do not paste or summarise its output in the note.
2. **Write the done-note**, commit it, `export-handoff.ps1`, push.

**`sync.ps1` is not run by this task.** It changes the tree, which defeats the one property this task exists to establish. If files are waiting in Drive, `verify.ps1` will say so as a content signal — that is the right place for it.

---

## 3. What the note must state

- **The HEAD `verify.ps1` reported**, and whether it equals the HEAD recorded in `061`'s note.
- **Whether the suite result matches `061`'s** — the same 12 pre-existing failures, `tests/test_permission_policy.py` green 8/8.
- **Whether `verify.ps1` itself changed between the two runs.** `git log --oneline` on that path since `061`'s commit, plus whether it is dirty now. **If it changed, the two runs are not comparable and the honest answer to this task is "still unverified"** — which is a legitimate result and must be stated as one, not worked around.
- **If any number differs from `061`'s, say so and stop there.** Do not re-run until the numbers agree. **A difference is the finding; a re-run that produces agreement has destroyed it.**

---

## 4. Not in this task

- **Any change to `verify.ps1`.** `062` holds uncommitted work on that file — **touching it here is precisely the collision this exercise exists to end.**
- **`062` itself.**
- **The `056` YAML defect / `OBS-080`.** Its own task.
- **`040` / `043` / `052` sync divergence.** Its own task.
- **`B-001`, `059`, `060`.** Untouched.

---

## 5. Exit tests

**Green.**
- `verify.ps1` ran on a tree that `git status --porcelain` reported clean at start.
- The note records HEAD, the comparison to `061`, and whether `verify.ps1` changed between runs.

**Refusal.**
- Tree not clean at start → **no run happened**, a question file exists naming every dirty path individually, and the session ended. **This is a pass.**

**UAT (Christoph).**
- Paste `verify-output` to the design session.

---

## 6. The closing sequence

Per `CLAUDE.md`, from the main checkout, with `sync.ps1` omitted for the reason in §2.

---

**This note needs to be pasted to chat.**

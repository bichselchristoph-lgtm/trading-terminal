# 013a — Where did the done-notes go?

**Status** DONE · **Date** 2026-08-11 · **Type** read-only inventory
**Runs in** `D:\Dev\momentum`. No writes, no network, no TWS. **Safe alongside `012`/`012a` capture and `013`.**

> Read this cold. The session that wrote it cannot answer questions.
> **This task writes nothing.** If you find yourself about to create a folder, move a file, or fix a naming inconsistency — stop. Report it instead. The fix is a later task and depends on what this one finds.

---

## Why

The design session assumed completed task files move to `handoff/done/`. That folder holds **one item**, while six tasks — H8, H9, H9a, M001, H10, H11 — have completed. The assumption is wrong somewhere, and `013` is currently backfilling state headers on the strength of it.

Separately: **no done-note has ever been stored on disk.** They have been written to chat, pasted to Christoph, and pasted to the design session. `HANDOFF-PROTOCOL.md` defines five states but names no location for the note that closes them. The record of what each task actually did exists only in conversation — the same shape as the snapshot-delivery problem, where a correct artifact is produced into a channel that does not retain it.

Fixing this before knowing the actual convention would be inventing one on top of another. Hence a read first.

---

## What to report

**1. The handoff tree as it stands.** Every file and folder under `D:\Dev\momentum\handoff\`, recursively, with paths and modification times. Include the single item in `done/` — name it and say what it is.

**2. Where the completed task files actually are.** For each of H8, H9, H9a, M001, H10, H11: locate the task file if it exists anywhere in the repo, and give its path. **If a task file does not exist on disk at all, say so plainly.** That is a finding, not a gap to fill — several of these were pasted as chat prompts and may never have been written to a file.

**3. Whether the done-notes exist anywhere.** Search the repo for the text of any done-note — distinctive strings like adoption-log rows, commit hashes `e7d3a14`, `66994a8`, `f9c18c6`, `aa8bb43`, `1afcecf`. Report where such text lives: `ADOPTION-LOG.md`, commit messages, `docs/observations/`, or nowhere.

**4. What the git history says about the convention.** Has anything ever been committed into `handoff/done/`? Has anything ever been moved there from `handoff/inbox/`? `git log --diff-filter=A -- handoff/` and `git log --diff-filter=R -- handoff/` answer this. **If the answer is that the convention has never once been exercised, say that** — an unexercised convention and a violated one are different problems with different fixes.

**5. What `CLAUDE.md` and the specs claim.** Quote every line in `CLAUDE.md`, `HANDOFF-PROTOCOL.md`, or any spec that says where task files or done-notes belong. **Quote, do not summarise.** If the specs are silent, say they are silent.

---

## Do not

- Do not create `handoff/notes/` or any folder.
- Do not move, rename, or delete anything.
- Do not modify `HANDOFF-PROTOCOL.md`, even though this task will likely show it incomplete.
- Do not commit.
- Do not touch `records/`, the capture, or anything belonging to `012`.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | All five items reported. `git status` shows the working tree exactly as it was before this task ran — **prove it, do not assert it.** |
| **Refusal** | Claude Code | For every item that does not exist, the report says it does not exist. **An absent file is reported as absent, never as an empty result folded into a summary.** Absence is not zero. |
| **UAT** | Christoph | Read item 2. You know which of these tasks you ran as pasted chat prompts rather than files — confirm the list matches your memory, and say where it does not. |

## Done-note must state

- The full handoff tree, and what the one item in `done/` is.
- For each of the six completed tasks: path on disk, or explicitly absent.
- Where done-note text survives, if anywhere.
- Whether `handoff/done/` has ever been written to in git history.
- Every quoted line from `CLAUDE.md` and the specs about task-file and note location — or a statement that there are none.
- **Whether `013` was running concurrently**, since it backfills headers in this same tree and may have changed it mid-read.

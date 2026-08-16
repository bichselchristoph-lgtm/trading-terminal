---
id: 054
title: Unblock the queue — the isolation ruling, the two parts that never arrived, and verify-output's last hop
type: task
class: admin
version: 1.0
originates: 052 v4.0 (never reached the tree) · 040 v1.2 Part 0 · 043 v1.2 Part 2 · 053 done-note
closes: B-034
unblocks: 049, 050 and 051 — all three are held only by the isolation ruling, which lives in a version of 052 the tree never received.
depends: none
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 054 — unblock the queue

**Type: task. Class: admin.** **Written once. Any correction gets a new number.**

**Everything here exists because a file was refused by the copier and the refusal looked like a
straggler.** Two of these parts have been sitting unexecuted since `045`.

---

## Addressing

**If `handoff/inbox/054-for-code-task-unblock-the-queue.md` exists in your tree and
`handoff/done/054-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in the main checkout, on a branch. Do not create a worktree** — see Part 1.
**Scratch in `$env:TEMP`, never the repo.**

---

## Part 1 — the isolation ruling, for all remaining tasks

**Work in the main checkout, on a task branch. Push the branch. Never commit to `main`.**

**Do not create a worktree, by any route.**

**The reasoning, so it is not relitigated.** `EnterWorktree` only creates under
`.claude/worktrees/`, which `.claude/settings.json` denies writes to — you probed it and it binds.
**And `git worktree remove` is denied, so any worktree created outlives the task permanently.** That
is `OBS-034` exactly: two orphans sat three days keeping a test red. **An orphan that cannot be
cleaned is worse than not isolating.**

**An earlier ruling said register worktrees outside `.claude/worktrees/`. That is withdrawn** — it was
made before the removal denial was established, and it produces a permanent orphan by design.

**What still protects against a second writer:** *one terminal at a time*, and the branch. **The
weaker guard is retired knowingly, not forgotten** — record it as such.

**Do not edit `.claude/settings.json`.** It is a security control and rule 19 puts it on Christoph.

---

## Part 2 — 040's Part 0, which never reached the tree

**`040` v1.2 in Drive carries a Part 0 that the tree's v1.1 does not. It was refused by the copier
and has never run.**

**It is the fix for `B-034`: the socket guard in `tests/test_keepuptodate_scale.py` does not stop an
asyncio client, so a test can reach live TWS.**

**Read Part 0 from the Drive copy and execute it here.** Do not renumber it, do not overwrite the
tree's `040`, and do not mark `040` done — **`040`'s own scope is unchanged; only this part was
stranded.**

**The guard must be seen to fail before it is accepted.** A guard that has never been observed
blocking anything is a guard whose green means nothing — **and this one was measured not to bind.**

---

## Part 3 — 043's Part 2, which never reached the tree

**`043` v1.2 in Drive carries a Part 2 — the questions channel — that the tree's v1.1 does not.**

**Read it from the Drive copy and execute it.** Same conditions as Part 2: do not renumber, do not
overwrite, do not mark `043` done.

**If any of it is already present** — `handoff/questions/` exists and `044-q1` was answered there —
**report what was already true and implement only the remainder.** **Do not assume it is all missing
because the file was refused.**

---

## Part 4 — `verify-output` still cannot reach Drive

**You moved it to `handoff/` and then found the exporter filters to `.md` only. Correct finding, and
correct to raise it rather than widen the filter.**

**Fix it at the filename, not the copier: `verify.ps1` writes `handoff/verify-output.md`.**

**Why this way.** Widening the filter changes what every future export carries, for one file. **A
copier is configured, never duplicated — and it is also not widened for a single case.** The content
is plain text either way.

**Retire the old path properly.** The root-level `verify-output.txt` and the `handoff/verify-output.txt`
you created must not both linger — **two files claiming to be the verification record is the
byte-indistinguishable defect in a new place.**

**Then confirm by reading the export manifest**, not by reasoning about the config. **`REVIEWED` is
unreachable until a design session can open that file from Drive.**

---

## Part 5 — two corrections from 052 v4.0

**Neither reached the tree. Both are live documents.**

### 5a — `SPEC.md:187` contradicts the naming convention

**It reads:** *"Mockup mapping (files keep their historical numbers)."*

**Replace with:**

```
Mockup mapping. TWO SETS EXIST AND THEY DO NOT MIX.

  docs/specs/mockups/     LOCAL, first generation, numbered 01-07.
                          Referenced by tests and by HTML cross-links.
                          These filenames are pointers and do not change.

  Trading Terminal/Mockups/ (Google Drive)
                          Second generation, numbered within type and named
                          for the spec they serve. Current, and what a product
                          spec cites.

A first-generation mockup predates Textual, the TRADE consolidation, the
deletion of the conviction dial and the deletion of the regime surface.
Citing one in a live instruction is a staleness finding, not a rename.
```

**The local filenames do not change.** Two tests reference them —
`test_resupplied_docs_are_repaired.py:58` and `test_regime_prompt_invariants.py` — **and renaming
them would break working code to satisfy a naming rule.**

### 5b — `handoff/inbox/006` and `007` cite a first-generation mockup

**No done-notes, so they are live. Add under the frontmatter of each:**

```
**STALENESS FINDING, 2026-08-16.** The mockup this task cites is first
generation — it predates Textual, the TRADE consolidation, the deletion of the
conviction dial and the deletion of the regime surface. Do not run this task
until Christoph rules whether its visual contract still stands.
```

**A refusal, not a rename.** **A task whose picture of the screen is two design generations old is
stale in more than its filename.**

---

## Part 6 — `verify.ps1` does not run under the default shell

**You reported working around `OBS-068`: a PowerShell 5.1 parse failure, requiring `pwsh`.**

**Report only, do not fix in this task:** what fails, whether `pwsh` is guaranteed present, and
whether anything invokes `verify.ps1` without it.

**Why it matters more than a workaround suggests.** **`verify.ps1` is the verification instrument, and
nothing reports on `verify.ps1`.** An instrument that fails to start on the default shell **fails
silently for anyone who does not know the workaround** — and its absence and its success look
identical from Drive.

---

## Not in this task

**Nothing about 049, 050 or 051.** Part 1 unblocks them; they run on their own numbers.

**No resolution of the 040, 043 or 052 conflicts.** The tree copies are records of what ran. **The
correction is this task, which is the rule the design session broke to create the problem.**

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. **Then run the export, from the main checkout.**

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | The socket guard **seen failing to block before the fix, and blocking after.** The declared-outputs test from `053` **goes green for `verify-output.md`**, having been red for the `.txt` |
| **Refusal** | Claude Code | **A worktree is not created by any route, and the task says so in the done-note rather than silently not doing it.** And **an output declared but unexported still fails loudly** |
| **UAT** | Christoph | None |

---

## Report

1. **Which branch, and confirmation `main` was not committed to.**
2. **040 Part 0: what it asked for, what you did, and the guard seen failing before and blocking
   after.**
3. **043 Part 2: what was already true, and what remained.**
4. **Whether `verify-output.md` appeared in the export manifest** — read, not reasoned.
5. **That only one verification-record file remains on disk.**
6. **`SPEC.md:187` before and after.**
7. **Which tasks received the staleness line.**
8. **`OBS-068`: what fails under 5.1, whether `pwsh` is guaranteed, what invokes `verify.ps1`
   blindly.**
9. **Your `bugs:` block.** At minimum: **the copier's refusal hid two unexecuted task parts for days**
   · **the exporter's `.md` filter** · **`verify.ps1` unrunnable on the default shell** · **the
   ledger holds four duplicated ids and `OBS-062` said so before the design session ruled on three.**
10. **What you could not do**, and why. Empty is suspicious.

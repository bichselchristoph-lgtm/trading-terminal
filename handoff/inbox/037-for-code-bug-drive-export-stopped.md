---
id: 037
title: The repo-to-Drive export stopped and nothing said so
type: bug
class: admin
unblocks: 038 — the session taxonomy cannot be settled against c013's chart comparison while the done-note is unreadable to the design session
owner: claude-code
tree: D:\Dev\momentum
---

# 037 — the export stopped, and nothing said so

**Type: bug. Class: admin.**

**Unblocks `038`** — the session-basis and level-taxonomy slice. `c013`'s UAT compared the
terminal's levels against Christoph's own charts. It is the only externally-checked evidence this
project has, and **the design session cannot read it**: the export last ran 2026-08-13 20:12 and
`christoph/done/` on Drive holds nothing past `c014`. `038` would be written blind to the exact
measurements it exists to correct.

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/037-for-code-bug-drive-export-stopped.md` exists in your tree and
`handoff/done/037-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

*(The previous addressing gate used `git status --porcelain` being empty. That condition is never
satisfied in Christoph's tree — his own `christoph/` files are untracked — so it disqualified the
message it was attached to. Do not reuse it.)*

**Work in a worktree, not `D:\Dev\momentum`.** Remove it when the task completes.

---

## The symptom

`020` exports `handoff/` and `christoph/done/` from the repo to
`D:\claude-googledrive-sync\momentum-code-handoff` and `...\momentum-christoph-done`.

**It worked on 2026-08-13 and has not run successfully since 20:12 that day.** Files created in
the tree after that time — `c013`'s close, `c015`, `036` — are absent from Drive.

**Nobody noticed for about fifteen hours.** That is the actual defect. The copy failing is a
fault; the failure being invisible is the bug.

---

## Part 0 — diagnose and report before fixing

**Do not repair first and describe the repair afterwards. The present state is the finding.**

Establish and report:

1. **How is the export triggered?** Windows Scheduled Task, manual invocation, a hook, something
   else. **Name the actual mechanism, not the intended one.**
2. **When did it last attempt to run**, as distinct from when it last succeeded?
3. **What was the failure?** Exit code, stderr, exception, or silent no-op. **If it never
   attempted, say that** — a trigger that stopped firing and a copier that started failing are
   different bugs with different fixes.
4. **Did it report anything anywhere?** A log, a console line, an exit code nobody read.

**If the cause turns out to be a Google outage or a credential expiry rather than the code, say
so and do not invent a code defect to fix.**

---

## Part 1 — fix the immediate break

Repair whatever Part 0 found, and run the export. **Report which files moved.**

---

## Part 2 — the structural fix

**The requirement, in Christoph's words: the sync always works, excluding Google outages.** Since
outages cannot be excluded in fact, the requirement is really: **a sync that is not working says
so, loudly, somewhere that gets read.**

### 2a — Every run leaves a record, including failures

The copier writes a run record on **every** invocation — success, partial, and failure alike:

```
last_attempt : 2026-08-14 11:42:03
last_success : 2026-08-14 11:42:07
outcome      : 3 new · 013, 015, 036
```

or

```
last_attempt : 2026-08-14 11:42:03
last_success : 2026-08-13 20:12:41
outcome      : FAILED — <reason>
```

**A failure that leaves no record is the bug repeating itself.** Write the record before
attempting the copy and update it after, so a crash mid-run still leaves `last_attempt` moved and
`last_success` stale — which is exactly the signature to detect.

**Where it lives is your call, but it must not be inside a synced folder.** A run record that
only exists in the destination cannot report that it failed to reach the destination.

### 2b — `verify.ps1` reports the age of the last success

**`verify.ps1` runs as the last action of every task that changes the tree.** Adding one line to
its output means the staleness surfaces every time anything at all happens, with no scheduler, no
daemon, and no new machinery:

```
drive export : last success 2026-08-13 20:12 (15h 30m ago)
```

**This is the whole structural answer.** It reuses the one instrument that already runs
constantly and is already read.

### 2c — A test that goes red when the record is absent or malformed

**Not a time-based test** — one that fails at 3am on a Sunday because nothing ran is a test that
gets ignored, and this project already carries eight of those.

Assert instead that **the run record exists, parses, and carries both timestamps.** That catches
the copier being changed in a way that stops it recording, which is the failure mode that would
undo 2a.

**Scope the test positionally**, to the run-record file only. A test that searches the repo for
timestamp-shaped strings will match its own fixture — the self-reference trap, which has fired
five times in one session in this project.

### 2d — Make the trigger deterministic

Whatever Part 0 found, **the export should not depend on someone remembering.**

**The recommendation, and say plainly if you disagree:** Claude Code runs the export as a final
action alongside `verify.ps1` on any task that adds to `handoff/done/`. Then it can never drift
by more than one task, and 2b's line becomes a backstop rather than the primary mechanism.

**Do not add a second scheduler.** `SPEC` §4.4 and §4a: one copier, configured, never duplicated.

---

## Part 3 — the three silences must not read alike

`§4a` already requires this and it is worth confirming it actually holds:

| Output | Means |
|---|---|
| `3 new · 013, 015, 036` | Files moved |
| `0 new · up to date` | Nothing to do — the normal case |
| `0 new · source unreachable` | **Broken** |
| `0 new · destination unreachable` | **Broken, differently** |

**Report which of these the copier can currently emit.** If `source unreachable` and `up to date`
produce the same line today, that alone explains fifteen silent hours.

---

## Not in scope

**Do not touch `026`** — the inbound Drive-to-inbox copier. Same config, different pair, and it
is working. If the fix genuinely must be shared between them, **say so and stop** rather than
changing a working path inside a bug fix.

No changes to what is exported. No new folder pairs.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise its output. Do not quote a test count.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran with 2c included, seen red first by removing the run record |
| **Refusal** | Claude Code | Point the destination at a path that does not exist ⇒ the copier reports `destination unreachable`, exits non-zero, and **still writes the run record** |
| **UAT** | Christoph | `c017` — open `D:\claude-googledrive-sync\momentum-christoph-done` and confirm `013` is there |

---

## Report

In `handoff/done/037-drive-export-stopped.md`:

- **Part 0's four answers**, before any fix
- What the fix was
- Where the run record lives and why that location survives a failure to reach Drive
- The red output from 2c
- **Which of Part 3's four lines the copier could emit before, and which it can emit now**
- Whether you agree with 2d's trigger recommendation, and why if not

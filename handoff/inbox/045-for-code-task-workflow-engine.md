---
id: 045
title: The workflow engine — trigger, dependencies, and who may decide
type: task
class: admin
version: 1.1
unblocks: S011 and S012 — every slice exits through a UAT, and four UAT files have sat in Drive unable to reach christoph/open/ since this morning
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 045 — the workflow engine

**Type: bug and rule change. Class: admin.**

**Run this first, before `044`.** Everything queued depends on files arriving.

**Five parts. Parts 1 and 2 unblock today. Parts 3, 4 and 5 stop it recurring.**

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/045-for-code-task-workflow-engine.md` exists in your tree and
`handoff/done/045-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes.

---

## The defect

**`tools/sync_from_drive.py` has no trigger of its own.** It runs when a task runs, because a task
running is what makes someone invoke it.

**That is exactly backwards for pair 3.** `handoff/inbox/` files arrive by the same run that
consumes them, so the missing trigger was invisible. **`christoph/open/` files arrive *between*
tasks** — that is what a UAT is — **and between tasks nothing runs.**

**Measured, 2026-08-15.** Four UAT files placed in `momentum-christoph-open`. `christoph/open/`
holds one `.gitkeep`.

**And Christoph cannot invoke it.** Running things is his by design, but **no document states the
command.** He was the one party who could have unblocked this and nothing told him how.

---

## Part 1 — Christoph must be able to run it, and it must be written down

1. **Establish the exact invocation** — interpreter, path, arguments, working directory. **Run it
   and confirm the four waiting files land in `christoph/open/`.**
2. **If it needs arguments, a specific working directory, or an activated environment, that is
   itself a finding.** A tool only its author can invoke is a tool with one user.
3. **Wrap it as `sync.ps1` at the repository root** — one word, beside `verify.ps1`, which already
   works that way. **Do not make Christoph remember a shape.**
4. **Write it into `CLAUDE.md`** as a copy-pasteable line, in a section he reads. **Bump the version
   and add a history row.** `037` flagged the bump as owed at v1.7 and correctly did not do it
   unasked. **This task asks.**

---

## Part 2 — a scheduled run, and this overturns `037`

**`037` ruled out a daemon:** *"a missed export is visible in `verify.ps1`; a background process
that fails quietly is not."*

**That reasoning was sound and is no longer true.** `043` gave the inbound copier a run record. **A
scheduled run that dies leaves `last_attempt` moved and `last_success` stale — the exact signature.
The objection was to silence, and the silence is gone.**

**And `verify.ps1` alone cannot carry this**, because it runs at the end of a task — **the same
broken clock the trigger was meant to fix.** An instrument pointed at the thing it is meant to
detect the absence of.

### The scheduled task

- **Every 15 minutes**, Windows Scheduled Task, **inbound sync only**.
- **Writes the run record on every attempt**, success and failure alike. `043`'s mechanism, unchanged.
- **Never touches the export.** `037` settled that: it runs as a task's last action, after the
  commit, and a scheduled export would race a session mid-commit.
- **Never writes to `christoph/done/`.** `043`'s guard test must still pass.
- **Logs to a file, not to a console nobody is watching.**

**Christoph creates or approves the scheduled task if Windows requires it** — say what he must do,
in one line.

**If a scheduled run collides with a session running the sync by hand, the copier's existing
behaviour governs: byte-identical is a no-op, differing is a refusal.** Confirm that holds under
concurrent invocation, or report what does not.

---

## Part 3 — `NOW.md`, computed from the tree

**Specified in the project instructions §4 and never built.** Nothing today shows what is runnable,
what is blocked, or on whom.

**It cannot depend on memory** — three sessions write to this tree and each sees a snapshot. **So
derive it.**

### `depends:` in frontmatter

Every task file gains an optional list of task ids. **`045` depends on nothing. `044` depends on
`045`.**

**A task file already in the tree without `depends:` is treated as depending on nothing.** Do not
edit files under `handoff/` to add it — copy-and-keep.

### The file

`claude/NOW.md`, **rewritten from the tree on every `verify.ps1` run**, never edited by hand:

```
ready now    045
blocked      044 — needs 045
             040 — needs Christoph present
running      —
on christoph c018 c019 c021 c023 c025
done         037 038 039 041 042 043
admin:product this stretch   9:2
```

**Derivation, entirely mechanical:**

- **done** — a file exists in `handoff/done/`
- **ready** — in `handoff/inbox/`, not in `handoff/done/`, and every `depends:` is done
- **blocked** — in `handoff/inbox/`, not done, with an unmet dependency **named**
- **on christoph** — in `christoph/open/`, not in `christoph/done/`
- **admin:product** — counted from `class:` in frontmatter, per rule 16

**No state is stored.** Anything that cannot be derived from the tree does not go in it.

**This replaces the design session handing Christoph prompts one at a time.** He reads what is
runnable and picks.

---

## Part 4 — who decides: the product/admin line, applied a second time

**Rule 16 already draws this line to count the admin tax. It now also governs who may decide.**

> **Product** — changes what the terminal renders, computes, or does for Christoph.
> **Admin** — everything else. Pipelines, protocols, tests, git, workflow, ledgers, syncs.

| | Gated on Christoph |
|---|---|
| **Product** — what a panel shows, what a number means, a spec change, a threshold, a UAT, an architectural choice | **Yes. Always.** |
| **Admin** — a failing test, a git conflict, a broken guard, a sync defect, a worktree, a duplicate ledger id | **No.** Proceed. |

### What changes

**Claude Code may author its own task file — for admin only — and act on it in the same session.**

Today only the design session may author task files, which is why a broken test guard waits for a
file to be written and a prompt to be relayed. **The file still gets written; it exists for the
record and the review, not for permission.**

### Four guardrails, all already in force

1. **`class: admin` only.** A self-authored file carrying `spec` or `product` is defective.
   **Anything touching what Christoph sees, or what a number means, is a question file** and the
   gate stands.
2. **Rule 16 still binds.** It must name the product task it unblocks, and **admin unblocking admin
   remains forbidden.** That is what stops this becoming a machine for generating work.
3. **The tax is still counted.** Self-authored tasks appear in `NOW.md`'s ratio like any other.
   **Autonomy buys no exemption from the count.**
4. **Review moves after, not before.** The design session reads the done-note and may reject.

**Numbering: read the inbox, never infer.** A self-authored file takes the next free number by the
same rule as any other, and **a collision is a stop** — five duplicate ledger ids and two `035`s
already say why.

**Write this into `CLAUDE.md`** with Part 1's command, in the same version bump.

**The risk, stated so it is watched:** rule 16 exists to *discourage* admin, and this makes admin
cheaper to produce. **If six self-authored admin tasks land in a day, that is the same failure with
a new author**, and `NOW.md`'s ratio is where it will show.

---

## Part 5 — make the staleness visible where Christoph already looks

**`043` gave the inbound copier a run record. Confirm `verify.ps1` reports its age**; if it does
not, that is a finding.

**Add a line that is not a clock:**

```
  drive inbound     last success 2026-08-15T09:12:04+02:00  (2h 19m ago)
                    waiting in Drive  4 — momentum-christoph-open: 018-…, 019-…, 021-…, 023-…
```

**`waiting in Drive` is the point.** *"Last success two hours ago"* is unalarming. **"Four files are
in Drive that are not in the tree"** means the same thing on a Sunday and a Thursday, and goes to
zero exactly when the problem is gone.

**Count per pair, name the files, cap the list, say `… and N more`. An unreachable source is its own
line and must never read as `0 waiting`.**

---

## The tests

**None time-based.** A test that goes red because nothing ran on a Sunday gets ignored — there were
eight of those in this repo a week ago.

1. **The inbound run record exists, parses, carries both timestamps.** Extend `043`'s tests.
2. **`verify.ps1` emits a `waiting in Drive` count — behavioural**, run against a temp Drive root
   holding one file the destination lacks. **A static check would pass forever against a
   `verify.ps1` that had stopped counting**, which is this defect exactly.
3. **`NOW.md` is derived, not stored** — regenerate it twice from an unchanged tree and assert the
   output is identical. **Then change one thing in the tree and assert it moved.**
4. **`depends:` cycles are refused**, naming the cycle. Two tasks depending on each other must not
   render as `blocked` forever with no explanation.

**Seen red: record removed · a file waiting the count misses · a hand-edit to `NOW.md` surviving a
run · a two-task cycle.**

---

## Not in scope

No panel work. No new folder pairs. **No scheduled export** — `037` settled it. No edits to anything
under `handoff/`. **No retro-fitting `depends:`** into task files already in the tree.

---

## Last action

**Run the inbound sync first** — this task's own subject — **then `verify.ps1`, then the export**,
from the main checkout, not a worktree.

**Do not paste or summarise `verify.ps1`. Do not quote a test count.**

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran with all four tests, each seen red first |
| **Refusal** | Claude Code | Drive source unreachable ⇒ its own line, **never `0 waiting`**; and a `depends:` cycle refused by name |
| **UAT** | Christoph | `c025` — run the documented command from a cold terminal without asking anyone, confirm the four UAT files land, and read `NOW.md`. **If he has to ask how, Part 1 failed** |

---

## Report

1. **The exact invocation**, and whether it needed a wrapper.
2. Whether the four waiting UAT files landed.
3. What `CLAUDE.md` said before, its new version, and what Christoph must do for the scheduled task.
4. Whether `verify.ps1` already reported the inbound record's age, or `043` left that half undone.
5. **What `waiting in Drive` read on the first run.** The present state is the finding.
6. **What `NOW.md` reads now**, in full.
7. The four reds, quoted.
8. **What you could not do**, and why. Empty is suspicious.

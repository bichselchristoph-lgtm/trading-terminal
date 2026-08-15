---
id: 048
title: The ask audit — every rule that is always-yes or always-no leaves ask
type: task
class: admin
version: 1.0
unblocks: NOTHING, and rule 16's guardrail does not apply — this task was requested by Christoph, not self-authored. See "Rule 16" below
owner: claude-code
author: Christoph (instruction relayed 2026-08-15), written up by claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 048 — the ask audit

**Type: rule change. Class: admin.**

> **Read this cold. The session that wrote it cannot answer questions.**
>
> **DO NOT RUN THIS IN THE SESSION THAT WROTE IT.** It was deliberately deferred.

---

## Addressing

**If `handoff/inbox/048-for-code-task-the-ask-audit.md` exists in your tree and
`handoff/done/048-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

---

## The instruction, in Christoph's words

> *"Anything I would always say yes to belongs in `allow`, anything I would always say no to
> belongs in `deny`. `ask` should hold only commands where the answer genuinely depends on the
> case."*

**That is the whole rule and it is not a heuristic — it is a definition of what `ask` is for.**

---

## Why `ask` is not a safe parking space

**Two measurements, both already in the tree, and they point the same way.**

1. **`ask` does not bind in auto mode.** `OBS-065`, measured with three probes under `046`:
   a `deny` on a path blocked, a `deny` on a shell blocked, **an `ask` on a shell ran
   unprompted.** Shell commands route through the classifier, which approves what `ask` would
   have prompted for. **A rule parked in `ask` is not a weak protection. In auto mode it is
   none.**
2. **`ask` overrides a more specific `allow`.** `047`: the exact-string entry
   `Bash(git push origin main)` sat in `allow` beside `Bash(git push:*)` in `ask`, and **could
   never fire.** The narrow rule was reviewed once as though it were doing something.

**So the cost of a wrong classification is asymmetric.** Something that belongs in `deny` and sits
in `ask` is unprotected. Something that belongs in `allow` and sits in `ask` costs a prompt — or,
worse, silently shadows a narrower `allow` that someone wrote on purpose.

---

## What was already decided, so it is not re-litigated

**`047` is done and is not part of this audit.** `Bash(git push:*)` and its PowerShell twin moved
to `allow`; the three force variants stay in `deny` under both tools. **`047` has no task file:
it was a one-line instruction from the person who holds the decision, executed in the same
session.** A task file exists to route a decision to whoever may take it, and he took it.

---

## Deletion cannot be scoped by path — MEASURED — so the fix is upstream

**The obvious way to settle half this audit is to stop classifying `rm` and `Remove-Item` by
command and start scoping them by path: deny deletion under `records/`, `.claude/worktrees/`,
`christoph/` and outside `D:\Dev\momentum`, allow it everywhere else in the repo. That is the
right shape and the settings format cannot express it.**

**Two probes, 2026-08-15, against the live session:**

| rule placed in `deny` | command run | result |
|---|---|---|
| `Bash(rm -f D:/Dev/momentum/.probe-deny/a.txt)` — **exact command string** | that exact command | **BLOCKED**, file survived |
| `Bash(rm //d/Dev/momentum/.probe-deny/**)` — **path glob** | `rm -f D:/Dev/momentum/.probe-deny/b.txt` | **RAN. File deleted.** |

**Both rules were in the same `deny` array, in the same well-formed file, in the same session.
One blocked and one matched nothing.** A `Bash(...)` specifier is a **command-string prefix**;
only the file tools — `Read`, `Edit`, `Write` — take **path patterns**. A path written inside a
`Bash(...)` rule is read as literal command text, so it matches a command that begins with those
characters and nothing else.

**This is `OBS-067`'s shape a third time: the rule reads as a protection and is absent.** It
would sit in the policy looking exactly like the rule beside it that works.

**And three further reasons it could not work even if the syntax existed**, worth stating so
nobody re-attempts it: a relative path defeats it, `cd` first defeats it, and **`allow` already
contains a general-purpose interpreter** — `Bash(C:/venvs/trading/Scripts/python.exe:*)` — which
can delete anything on the disk and which no command-string rule can see into.

### So the fix is not a rule. It is to stop creating the paths.

**Most `Remove-Item` prompts today are for temp directories created inside `D:\Dev\momentum`.**
The prompt is not protecting anything — it is the cost of scratch having been put somewhere it
should never have been, and every one of those prompts trains the habit of approving a deletion
inside the repo.

> **Tools and probes write scratch to `$env:TEMP`. Never into the repository.**

**Applies to `tools/*.py`, every test that materialises a directory, every ad-hoc probe, and this
audit's own probes.** If nothing creates a temp path inside the tree, deletion inside the tree
stops being routine — and the `ask` prompts that remain are about real files, which is the only
state in which a prompt carries information.

**The session that wrote this task demonstrated the anti-pattern while measuring it**, creating
`.probe-deny/` inside the repo rather than under `$env:TEMP`. That is the evidence, not an
apology: the wrong location is the path of least resistance even for someone writing the rule
against it.

**What to do in the audit:** leave `rm`, `rmdir`, `mv`, `Remove-Item`, `Move-Item` and the
aliases in `ask` — that is the fallback and it is already in place — **and check the tree for
tools and tests that create scratch inside it.** Anything found is the real finding.

---

## The work

**Go through `.claude/settings.json`'s `ask` list entry by entry.** For each, answer one question
— *would Christoph always say yes, always say no, or does it genuinely depend?* — and move it, or
leave it, on that answer.

**Three rules on how to do it:**

1. **Move both shell twins together, always.** `tests/test_permission_policy_is_shell_symmetric.py`
   asserts every `git` rule in `ask` and `deny` exists under both tools, and `046` part 2 is the
   record of what a one-shell rule is worth: **a `Bash`-only deny is one environment variable from
   no deny at all** (`OBS-067`).
2. **Watch for prefix subsumption in both directions.** A broad `ask` prefix kills a narrow
   `allow` (`047`'s defect). A broad `allow` prefix does *not* kill a narrow `deny` — `deny`
   outranks `allow` — **but do not take that on trust from this file; it is the kind of
   precedence claim `58b0926` asserted and `f35bd3a` disproved.** Probe it.
3. **A rule that stays in `ask` must be able to say why in one sentence**, naming the case that
   goes one way and the case that goes the other. **If no such sentence exists, it is not
   case-dependent and it is in the wrong list.**

### The entries where the answer is not obvious, flagged so they get thought rather than a default

**These are the ones this task exists for. They are not pre-decided here.**

| entry | why it is not a straight call |
|---|---|
| `git reset:*`, `git checkout:*` | **`OBS-066` lives here.** Plain `reset` unstages and plain `checkout` switches branch — both harmless. But `git reset HEAD~1 --hard` reorders the flag past the `deny` prefix, and `git checkout <file>` discards without the `--`. **Moving these to `allow` re-opens both gaps** wherever `classifyAllShell` is not in force |
| `git branch:*` | creating and listing are always-yes; `git branch -D` can orphan commits. **Prefix matching cannot express "everything except `-D`"** |
| `git rm:*` | `git rm --cached` is the documented fix for an accidentally-tracked config — `test_no_secrets.py`'s own failure message recommends it — while `git rm <file>` deletes from disk |
| `find:*` | in `ask` only because `-delete` and `-exec rm` exist. Plain `find` is read-only and constant |
| `schtasks /create`, `/delete`, `tools/register-sync-task.ps1` | **`045` recorded that registering the scheduled task is Christoph's**, because it writes outside the repository. If that is an always-no for Claude Code, these are `deny` — **and `deny` has no escape hatch**, which is the thing to weigh |
| `[Environment]::SetEnvironmentVariable`, `Set-ItemProperty`, `New-ItemProperty`, `Remove-ItemProperty` | machine and registry writes. Same question as above, same lack of an escape hatch. **Note that `CLAUDE_CODE_USE_POWERSHELL_TOOL` — the variable behind `046` part 2 — is set through exactly this surface** |
| `Edit`/`Write` on `.gitignore` and `.claude/settings.json` | **the archetypal `ask`, and the likely answer is "leave it".** Both are load-bearing guards, `046` legitimately edited both, and a session editing its own permission policy unprompted is the one case where a prompt is the whole point |

**Do not treat the table as a set of answers. It is a list of the places where a default would be
wrong.**

---

## Rule 16

**This task names no product task it unblocks, and none should be invented.**

**Guardrail 2 does not apply, because this is not a self-authored task.** `CLAUDE.md` v1.7's
guardrails govern a task file Claude Code writes for itself; **this one was requested by Christoph
in a session on 2026-08-15 and written up on his instruction.** He holds the product/admin
decision line, and directing admin work is his to do.

**Say this again in the done-note.** `046` was the first self-authored admin task and it could
not name a product task either — **two consecutive admin tasks unblocking no product is the
pattern `045` Part 4 asked to have watched**, and `NOW.md`'s ratio is where it shows. The
difference in authorship is the material fact and it must not be blurred.

---

## Not in scope

**No change to `deny`'s existing entries.** No change to the `.gitignore` guard. No change to
`spend_guard.py` or its patterns. **No new permission rules for commands that are not already in
`ask`** — this is a re-classification, not an expansion.

---

## The tests

1. **The symmetry test must stay green**, and its required-denies list must still name every entry
   it names today.
2. **A new assertion: no rule can be dead.** For each tool, **no `allow` entry may be subsumed by
   an `ask` or `deny` prefix for the same tool.** That is `047`'s defect stated structurally, and
   it is the one thing in this whole area that nothing currently checks. **Seen red against the
   state at `480fdb1`**, which had `Bash(git push origin main)` in `allow` under `Bash(git push:*)`
   in `ask`.
3. **Anything moved to `deny` is probed**, not assumed — the same three-probe shape as `OBS-065`.
   **`deny` is the only class measured to bind, and that measurement was taken in one session in
   one mode.**

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | full suite, **not a targeted run** — `046` §5 is why |
| **Refusal** | Claude Code | the dead-rule assertion seen red against `480fdb1`'s policy |
| **Measured** | Claude Code | every entry moved to `deny`, probed |
| **UAT** | Christoph | **None.** The policy renders nothing; a UAT here would be re-running a probe |

---

## Report

1. **The final `ask` list, entry by entry, each with its one-sentence reason for staying.**
2. Everything that moved, and to which list.
3. **Whether `deny` really does outrank a broader `allow`** — measured, not assumed.
4. What you left in `ask` that you were tempted to move, and what stopped you.
5. **The rule-16 position**, restated as above.
6. What you could not do. Empty is suspicious.
